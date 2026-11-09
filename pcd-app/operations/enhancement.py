import numpy as np
from PIL import ImageFilter

from .basic_ops import ke_array, ke_citra, pilihan, slider
from .helper import (blur_gauss, blur_rata, filter_frekuensi, konvolusi)


def brightness(img, nilai=30):
    """Menambah/mengurangi kecerahan: hasil = piksel + nilai."""
    return ke_citra(ke_array(img) + nilai)


def contrast(img, faktor=1.5, titik="Tengah 128"):
    """Mengubah kontras (gain α).
    Tengah 128: hasil = (piksel-128)*α + 128  (terang dan gelap sama-sama menjauhi 128).
    Nol (Y = αX): hasil = α * piksel, sesuai rumus Y = αX + β bila dilanjutkan
    dengan Brightness β."""
    a = ke_array(img)
    if titik == "Nol (Y = αX)":
        return ke_citra(a * faktor)
    return ke_citra((a - 128) * faktor + 128)


def hist_equalization(img, mode="Luminance"):
    """Pemerataan histogram dengan CDF.
    Luminance: hanya kecerahan yang diratakan, warna terjaga.
    Per kanal RGB: tiap kanal diratakan sendiri."""
    def ratakan(k):
        k = np.clip(k, 0, 255).astype(np.uint8)
        hist = np.bincount(k.ravel(), minlength=256)
        cdf = hist.cumsum()
        cdf_min = cdf[np.nonzero(cdf)[0][0]]
        total = cdf[-1]
        if total == cdf_min:                  # citra satu warna, tak ada yang diratakan
            return k.astype(np.float32)
        tabel = np.rint((cdf - cdf_min) / (total - cdf_min) * 255)
        return np.clip(tabel, 0, 255)[k].astype(np.float32)

    a = ke_array(img)
    if mode == "Per kanal RGB":
        return ke_citra(np.stack([ratakan(a[..., c]) for c in range(3)], axis=-1))
    y = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    y2 = ratakan(y)
    # skala ketiga kanal dengan rasio kecerahan baru/lama agar warna tetap
    rasio = (y2 + 1) / (y + 1)
    return ke_citra(a * rasio[..., None])


def _sampel(a, ys, xs, interpolasi):
    h, w = a.shape[:2]
    if interpolasi == "Nearest":
        yi = np.clip(np.rint(ys).astype(int), 0, h - 1)
        xi = np.clip(np.rint(xs).astype(int), 0, w - 1)
        return a[yi, xi]
    ys = np.clip(ys, 0, h - 1)
    xs = np.clip(xs, 0, w - 1)
    y0, x0 = np.floor(ys).astype(int), np.floor(xs).astype(int)
    y1, x1 = np.minimum(y0 + 1, h - 1), np.minimum(x0 + 1, w - 1)
    fy, fx = (ys - y0)[..., None], (xs - x0)[..., None]
    return (a[y0, x0] * (1 - fy) * (1 - fx) + a[y0, x1] * (1 - fy) * fx +
            a[y1, x0] * fy * (1 - fx) + a[y1, x1] * fy * fx)


def geometrics_correction(img, distorsi=0.2, rotasi=0, interpolasi="Bilinear"):
    """Koreksi geometri: memperbaiki distorsi lensa (barrel/pincushion) dan
    memutar citra. Pemetaan balik: tiap piksel hasil mengambil nilai dari
    posisi asalnya, supaya tidak ada lubang."""
    a = ke_array(img)
    h, w = a.shape[:2]
    cy, cx = (h - 1) / 2, (w - 1) / 2
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # rotasi (berlawanan arah jarum jam) terhadap pusat
    t = np.deg2rad(rotasi)
    dx, dy = xx - cx, yy - cy
    xr = np.cos(t) * dx - np.sin(t) * dy
    yr = np.sin(t) * dx + np.cos(t) * dy
    # distorsi radial: r' = r (1 + k r^2), r dinormalisasi oleh setengah diagonal
    norm = max(np.hypot(cx, cy), 1.0)
    r2 = (xr ** 2 + yr ** 2) / norm ** 2
    f = 1 + distorsi * r2
    xs, ys = cx + xr * f, cy + yr * f
    hasil = _sampel(a, ys, xs, interpolasi)
    # area di luar citra asli dibuat hitam
    di_luar = (xs < 0) | (xs > w - 1) | (ys < 0) | (ys > h - 1)
    hasil[di_luar] = 0
    return ke_citra(hasil)


def lowpass(img, jenis="Gaussian", ukuran=5):
    """Lowpass spasial: menghaluskan citra / mengurangi noise."""
    a = ke_array(img)
    if jenis == "Rata-rata":
        return ke_citra(blur_rata(a, ukuran))
    return ke_citra(blur_gauss(a, ukuran / 3))


def median(img, ukuran=3):
    """Median filter: nilai tengah tetangga, bagus untuk noise garam-merica."""
    ukuran = max(3, int(ukuran) | 1)          # harus ganjil
    return img.filter(ImageFilter.MedianFilter(size=ukuran))


def highpass(img, jenis="Detail", ukuran=5):
    """Highpass spasial: memunculkan tepi/detail.
    Detail: citra - blur (+128 agar terlihat). Sharpen: citra + detail."""
    a = ke_array(img)
    detail = a - blur_gauss(a, ukuran / 3)
    if jenis == "Sharpen":
        return ke_citra(a + detail)
    return ke_citra(detail + 128)


def highboost(img, k=2.0, ukuran=5):
    """Highboost: hasil = A + k * (A - blur(A)). k=1 sama dengan unsharp masking."""
    a = ke_array(img)
    return ke_citra(a + k * (a - blur_gauss(a, ukuran / 3)))


# ----- filter domain frekuensi (ideal dan Butterworth) -----

def _lp_ideal(r):
    return lambda D: (D <= r).astype(np.float32)


def _lp_butter(r, n):
    return lambda D: 1.0 / (1.0 + (D / max(r, 1e-3)) ** (2 * n))


def ilpf(img, radius=30):
    """Ideal Lowpass: memotong semua frekuensi di luar radius."""
    return ke_citra(filter_frekuensi(ke_array(img), _lp_ideal(radius)))


def blpf(img, radius=30, orde=2):
    """Butterworth Lowpass: pemotongan halus, orde makin besar makin tajam."""
    return ke_citra(filter_frekuensi(ke_array(img), _lp_butter(radius, orde)))


def ihpf(img, radius=30):
    """Ideal Highpass: membuang frekuensi di dalam radius."""
    return ke_citra(filter_frekuensi(ke_array(img), lambda D: 1 - _lp_ideal(radius)(D)))


def bhpf(img, radius=30, orde=2):
    """Butterworth Highpass."""
    return ke_citra(filter_frekuensi(ke_array(img), lambda D: 1 - _lp_butter(radius, orde)(D)))


OPERASI = {
    "Brightness": {"fungsi": brightness,
                   "params": [slider("nilai", "Nilai", -255, 255, 30)]},
    "Contrast": {"fungsi": contrast,
                 "params": [slider("faktor", "Faktor (α)", 0.0, 3.0, 1.5, 0.1),
                            pilihan("titik", "Rumus", ["Tengah 128", "Nol (Y = αX)"])]},
    "Hist. Equalization": {"fungsi": hist_equalization,
                           "params": [pilihan("mode", "Mode", ["Luminance", "Per kanal RGB"])]},
    "Geometrics correction": {"fungsi": geometrics_correction,
                              "params": [slider("distorsi", "Distorsi lensa", -0.5, 0.5, 0.2, 0.05),
                                         slider("rotasi", "Rotasi", -180, 180, 0, 1, "°"),
                                         pilihan("interpolasi", "Interpolasi", ["Bilinear", "Nearest"])]},
    "Lowpass Filtering": {"fungsi": lowpass,
                          "params": [pilihan("jenis", "Jenis", ["Gaussian", "Rata-rata"]),
                                     slider("ukuran", "Ukuran kernel", 3, 25, 5, 2)]},
    "Median Filtering": {"fungsi": median,
                         "params": [slider("ukuran", "Ukuran kernel", 3, 11, 3, 2)]},
    "ILPF": {"fungsi": ilpf, "params": [slider("radius", "Radius", 1, 300, 30)]},
    "BLPF": {"fungsi": blpf, "params": [slider("radius", "Radius", 1, 300, 30),
                                        slider("orde", "Orde", 1, 10, 2)]},
    "Highpass Filtering": {"fungsi": highpass,
                           "params": [pilihan("jenis", "Jenis", ["Detail", "Sharpen"]),
                                      slider("ukuran", "Ukuran kernel", 3, 25, 5, 2)]},
    "Highboost Filtering": {"fungsi": highboost,
                            "params": [slider("k", "Faktor k", 0.5, 5.0, 2.0, 0.1),
                                       slider("ukuran", "Ukuran kernel", 3, 25, 5, 2)]},
    "IHPF": {"fungsi": ihpf, "params": [slider("radius", "Radius", 1, 300, 30)]},
    "BHPF": {"fungsi": bhpf, "params": [slider("radius", "Radius", 1, 300, 30),
                                        slider("orde", "Orde", 1, 10, 2)]},
}