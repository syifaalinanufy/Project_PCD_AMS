"""
Perhitungan histogram dan statistik citra.

Histogram dihitung untuk 4 kanal sekaligus (keabuan, R, G, B) supaya
pengguna bisa berganti kanal di halaman tanpa meminta data ulang ke server.
"""
import numpy as np


def hitung_histogram(img):
    """Mengembalikan (histogram, statistik) dari citra RGB Pillow."""
    a = np.asarray(img)

    # Keabuan memakai rumus luminance, lalu dibulatkan ke 0-255
    abu = np.rint(0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])
    abu = abu.astype(np.uint8)

    def hitung(kanal):
        # bincount menghitung berapa piksel untuk tiap nilai 0..255
        return np.bincount(kanal.ravel(), minlength=256).tolist()

    histogram = {
        "gray": hitung(abu),
        "r": hitung(a[..., 0]),
        "g": hitung(a[..., 1]),
        "b": hitung(a[..., 2]),
    }

    statistik = {
        "min": int(abu.min()),
        "max": int(abu.max()),
        "rata": round(float(abu.mean()), 2),
        "median": int(np.median(abu)),
        "std": round(float(abu.std()), 2),
        "piksel": int(abu.size),
    }
    return histogram, statistik
