"""
Operasi menu Noise: menambahkan derau (noise) buatan ke citra.

Tiap fungsi punya parameter 'seed' agar hasil bisa diulang (seed 0 = acak
setiap kali). 'Mode' menentukan noise yang sama untuk semua kanal warna
(Keabuan) atau berbeda per kanal (Per kanal RGB).
"""
import numpy as np

from .basic_ops import ke_array, ke_citra, pilihan, slider

MODE = pilihan("mode", "Mode warna", ["Per kanal RGB", "Keabuan"])
SEED = slider("seed", "Seed (0 = acak)", 0, 999, 0)


def _tambah(img, sampel, mode, seed):
    """sampel(rng, bentuk) -> derau. Derau ditambahkan ke citra."""
    rng = np.random.default_rng(None if seed == 0 else seed)
    a = ke_array(img)
    h, w = a.shape[:2]
    if mode == "Keabuan":
        n = sampel(rng, (h, w))[..., None]
    else:
        n = sampel(rng, (h, w, 3))
    return ke_citra(a + n)


def gaussian_noise(img, mean=0, sigma=25, mode="Per kanal RGB", seed=0):
    """Derau berdistribusi normal (bell curve), mirip noise sensor kamera."""
    return _tambah(img, lambda r, s: r.normal(mean, sigma, s), mode, seed)


def rayleigh_noise(img, skala=25, mode="Per kanal RGB", seed=0):
    """Derau Rayleigh: selalu positif, miring ke kanan (radar/ultrasonik)."""
    return _tambah(img, lambda r, s: r.rayleigh(skala, s), mode, seed)


def erlang_noise(img, bentuk=2, skala=15, mode="Per kanal RGB", seed=0):
    """Derau Erlang/Gamma: jumlah 'bentuk' derau eksponensial."""
    return _tambah(img, lambda r, s: r.gamma(bentuk, skala, s), mode, seed)


def exponential_noise(img, skala=25, mode="Per kanal RGB", seed=0):
    """Derau eksponensial: kasus khusus Erlang dengan bentuk = 1."""
    return _tambah(img, lambda r, s: r.exponential(skala, s), mode, seed)


def uniform_noise(img, minimum=-40, maksimum=40, mode="Per kanal RGB", seed=0):
    """Derau seragam: nilai acak merata di antara minimum dan maksimum."""
    lo, hi = min(minimum, maksimum), max(minimum, maksimum)
    return _tambah(img, lambda r, s: r.uniform(lo, hi, s), mode, seed)


def impulse_noise(img, jumlah=5, rasio_garam=50, mode="Per kanal RGB", seed=0):
    """Salt & pepper: sebagian piksel menjadi putih (garam) atau hitam (merica)."""
    rng = np.random.default_rng(None if seed == 0 else seed)
    a = ke_array(img).copy()
    h, w = a.shape[:2]
    bentuk = (h, w) if mode == "Keabuan" else (h, w, 3)
    kena = rng.random(bentuk) < jumlah / 100
    garam = rng.random(bentuk) < rasio_garam / 100
    if mode == "Keabuan":
        kena, garam = kena[..., None], garam[..., None]
    a = np.where(kena & garam, 255, a)
    a = np.where(kena & ~garam, 0, a)
    return ke_citra(a)


OPERASI = {
    "Gaussian Noise": {"fungsi": gaussian_noise, "params": [
        slider("mean", "Mean", -100, 100, 0), slider("sigma", "Sigma", 1, 100, 25), MODE, SEED]},
    "Rayleigh Noise": {"fungsi": rayleigh_noise, "params": [
        slider("skala", "Skala", 1, 100, 25), MODE, SEED]},
    "Erlang (Gamma) Noise": {"fungsi": erlang_noise, "params": [
        slider("bentuk", "Bentuk (k)", 1, 10, 2), slider("skala", "Skala", 1, 50, 15), MODE, SEED]},
    "Exponential Noise": {"fungsi": exponential_noise, "params": [
        slider("skala", "Skala", 1, 100, 25), MODE, SEED]},
    "Uniform Noise": {"fungsi": uniform_noise, "params": [
        slider("minimum", "Minimum", -100, 100, -40), slider("maksimum", "Maksimum", -100, 100, 40),
        MODE, SEED]},
    "Impulse Noise": {"fungsi": impulse_noise, "params": [
        slider("jumlah", "Jumlah piksel kena", 1, 50, 5, satuan="%"),
        slider("rasio_garam", "Porsi garam (putih)", 0, 100, 50, satuan="%"), MODE, SEED]},
}
