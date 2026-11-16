import numpy as np

from .basic_ops import ke_citra, keabuan, pilihan, slider
from .helper import blur_gauss, konvolusi, normalisasi

AMBANG = slider("ambang", "Ambang (0 = tanpa)", 0, 255, 0)


def _tampil(mag, ambang):
    """Normalisasi magnitudo ke 0..255 lalu (opsional) jadikan biner."""
    mag = normalisasi(mag)
    if ambang > 0:
        mag = np.where(mag >= ambang, 255, 0)
    return ke_citra(mag)


def _gradien(img, kx, ky, ambang):
    g = keabuan(img)
    gx, gy = konvolusi(g, kx), konvolusi(g, ky)
    return _tampil(np.hypot(gx, gy), ambang)


def sobel(img, ambang=0):
    """Sobel: gradien dengan bobot lebih besar di tengah, tahan noise."""
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    return _gradien(img, kx, kx.T, ambang)


def prewitt(img, ambang=0):
    """Prewitt: seperti Sobel tetapi semua bobot sama."""
    kx = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
    return _gradien(img, kx, kx.T, ambang)


def roberts(img, ambang=0):
    """Roberts: kernel 2x2 diagonal, cepat tetapi sensitif noise."""
    kx = np.array([[1, 0], [0, -1]], dtype=np.float32)
    ky = np.array([[0, 1], [-1, 0]], dtype=np.float32)
    g = keabuan(img)
    p = np.pad(g, ((0, 1), (0, 1)), mode="edge")
    h, w = g.shape
    gx = p[:h, :w] - p[1:h + 1, 1:w + 1]
    gy = p[:h, 1:w + 1] - p[1:h + 1, :w]
    return _tampil(np.hypot(gx, gy), ambang)


KERNEL_LAPLACIAN = {
    "4 tetangga": [[0, 1, 0], [1, -4, 1], [0, 1, 0]],
    "8 tetangga": [[1, 1, 1], [1, -8, 1], [1, 1, 1]],
}


def laplacian(img, kernel="4 tetangga", ambang=0):
    """Laplacian: turunan kedua, tepi ada di titik perubahan tanda."""
    g = keabuan(img)
    return _tampil(np.abs(konvolusi(g, np.array(KERNEL_LAPLACIAN[kernel]))), ambang)


def log_edge(img, sigma=1.5, ambang=0):
    """Laplacian of Gaussian: haluskan dengan Gaussian dulu, lalu Laplacian."""
    g = blur_gauss(keabuan(img), sigma)
    lap = konvolusi(g, np.array(KERNEL_LAPLACIAN["8 tetangga"]))
    return _tampil(np.abs(lap), ambang)


def canny(img, rendah=50, tinggi=120, sigma=1.4):
    """Canny: Gaussian -> gradien Sobel -> non-maximum suppression -> hysteresis."""
    if rendah > tinggi:
        rendah, tinggi = tinggi, rendah
    g = blur_gauss(keabuan(img), sigma)
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    gx, gy = konvolusi(g, kx), konvolusi(g, kx.T)
    mag = np.hypot(gx, gy)
    mag = mag * (255.0 / mag.max()) if mag.max() > 0 else mag
    sudut = (np.rad2deg(np.arctan2(gy, gx)) + 180) % 180

    # non-maximum suppression: pertahankan hanya puncak lokal searah gradien
    p = np.pad(mag, 1, mode="edge")
    h, w = mag.shape
    def n(dy, dx):
        return p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
    a1 = np.where(((sudut < 22.5) | (sudut >= 157.5)), np.maximum(n(0, 1), n(0, -1)), 0)
    a2 = np.where((sudut >= 22.5) & (sudut < 67.5), np.maximum(n(-1, 1), n(1, -1)), 0)
    a3 = np.where((sudut >= 67.5) & (sudut < 112.5), np.maximum(n(1, 0), n(-1, 0)), 0)
    a4 = np.where((sudut >= 112.5) & (sudut < 157.5), np.maximum(n(-1, -1), n(1, 1)), 0)
    tetangga_maks = a1 + a2 + a3 + a4
    tipis = np.where(mag >= tetangga_maks, mag, 0)

    # hysteresis: tepi kuat + tepi lemah yang terhubung ke tepi kuat
    kuat = tipis >= tinggi
    lemah = (tipis >= rendah) & ~kuat
    tepi = kuat.copy()
    for _ in range(100):                      # perluas sampai tak ada perubahan
        pk = np.pad(tepi, 1)
        tetangga = np.zeros_like(tepi)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                tetangga |= pk[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        baru = tepi | (lemah & tetangga)
        if (baru == tepi).all():
            break
        tepi = baru
    return ke_citra(np.where(tepi, 255, 0))


def _kirsch_kernel():
    """8 kernel Kirsch dibuat dengan memutar bobot [5,5,5,-3,-3,-3,-3,-3]
    mengelilingi sel tengah."""
    posisi = [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (1, 0)]
    dasar = [5, 5, 5, -3, -3, -3, -3, -3]
    hasil = []
    for geser in range(8):
        k = np.zeros((3, 3), dtype=np.float32)
        for i, (r, c) in enumerate(posisi):
            k[r, c] = dasar[(i - geser) % 8]
        hasil.append(k)
    return hasil


ARAH = ["Utara", "Timur Laut", "Timur", "Tenggara", "Selatan", "Barat Daya", "Barat", "Barat Laut"]


def compass_kirsch(img, arah="Semua arah", ambang=0):
    """Compass (Kirsch): 8 kernel arah, diambil respon terbesar."""
    g = keabuan(img)
    kernel = _kirsch_kernel()
    if arah == "Semua arah":
        respon = np.max([konvolusi(g, k) for k in kernel], axis=0)
    else:
        respon = konvolusi(g, kernel[ARAH.index(arah)])
    return _tampil(np.maximum(respon, 0), ambang)


OPERASI = {
    "Sobel": {"fungsi": sobel, "params": [AMBANG]},
    "Prewitt": {"fungsi": prewitt, "params": [AMBANG]},
    "Roberts": {"fungsi": roberts, "params": [AMBANG]},
    "Laplacian": {"fungsi": laplacian, "params": [
        pilihan("kernel", "Kernel", list(KERNEL_LAPLACIAN)), AMBANG]},
    "Laplacian of Gaussian": {"fungsi": log_edge, "params": [
        slider("sigma", "Sigma", 0.5, 5.0, 1.5, 0.1), AMBANG]},
    "Canny": {"fungsi": canny, "params": [
        slider("rendah", "Ambang rendah", 0, 255, 50), slider("tinggi", "Ambang tinggi", 0, 255, 120),
        slider("sigma", "Sigma", 0.5, 4.0, 1.4, 0.1)]},
    "Compass (Kirsch)": {"fungsi": compass_kirsch, "params": [
        pilihan("arah", "Arah", ["Semua arah"] + ARAH), AMBANG]},
}
