"""Fungsi bantu bersama untuk Enhancement, Noise, Edge Detection, Segmentation.

Semua memakai NumPy murni (tanpa OpenCV) supaya mudah dibaca dan dijelaskan.
"""
import numpy as np


def _pad(a, ry, rx):
    """Tambah tepi dengan cara memantulkan piksel (reflect), bekerja untuk 2D/3D."""
    tambah = [(ry, ry), (rx, rx)] + [(0, 0)] * (a.ndim - 2)
    mode = "reflect" if min(a.shape[0], a.shape[1]) > max(ry, rx) else "edge"
    return np.pad(a, tambah, mode=mode)


def konvolusi(a, kernel):
    """Konvolusi 2D dengan kernel kecil (korelasi; kernel simetris/anti-simetris
    sudah ditangani pemanggil). a: 2D atau 3D float."""
    kernel = np.asarray(kernel, dtype=np.float32)
    kh, kw = kernel.shape
    ry, rx = kh // 2, kw // 2
    p = _pad(a.astype(np.float32), ry, rx)
    h, w = a.shape[:2]
    hasil = np.zeros(a.shape, dtype=np.float32)
    for i in range(kh):
        for j in range(kw):
            k = kernel[i, j]
            if k != 0:
                hasil += k * p[i:i + h, j:j + w]
    return hasil


def konvolusi_pisah(a, k1d):
    """Konvolusi terpisah: kernel 1D diterapkan ke baris lalu kolom (cepat)."""
    k1d = np.asarray(k1d, dtype=np.float32)
    r = len(k1d) // 2
    p = _pad(a.astype(np.float32), r, r)
    h, w = a.shape[:2]
    tengah = np.zeros((h + 2 * r, w) + a.shape[2:], dtype=np.float32)
    for j, k in enumerate(k1d):
        tengah += k * p[:, j:j + w]
    hasil = np.zeros(a.shape, dtype=np.float32)
    for i, k in enumerate(k1d):
        hasil += k * tengah[i:i + h]
    return hasil


def kernel_gauss_1d(ukuran, sigma):
    r = ukuran // 2
    x = np.arange(-r, r + 1, dtype=np.float32)
    k = np.exp(-(x ** 2) / (2 * max(sigma, 1e-3) ** 2))
    return k / k.sum()


def blur_gauss(a, sigma):
    ukuran = max(3, int(2 * np.ceil(3 * sigma) + 1))
    return konvolusi_pisah(a, kernel_gauss_1d(ukuran, sigma))


def blur_rata(a, ukuran):
    return konvolusi_pisah(a, np.ones(ukuran, dtype=np.float32) / ukuran)


def normalisasi(a):
    """Skalakan array ke 0..255 (untuk menampilkan magnitudo tepi)."""
    mx = float(a.max())
    return a * (255.0 / mx) if mx > 0 else a


# ---------- filter domain frekuensi ----------

def jarak_frekuensi(h, w):
    """Jarak tiap titik spektrum (sudah di-shift ke tengah) dari pusat."""
    v = np.arange(h, dtype=np.float32) - h // 2
    u = np.arange(w, dtype=np.float32) - w // 2
    return np.sqrt(v[:, None] ** 2 + u[None, :] ** 2)


def filter_frekuensi(a, mask_fn):
    """Terapkan filter H(D) pada tiap kanal lewat FFT. mask_fn menerima D."""
    h, w = a.shape[:2]
    H = mask_fn(jarak_frekuensi(h, w)).astype(np.float32)
    kanal = [a] if a.ndim == 2 else [a[..., c] for c in range(a.shape[2])]
    hasil = []
    for k in kanal:
        F = np.fft.fftshift(np.fft.fft2(k))
        hasil.append(np.real(np.fft.ifft2(np.fft.ifftshift(F * H))))
    return hasil[0] if a.ndim == 2 else np.stack(hasil, axis=-1)
