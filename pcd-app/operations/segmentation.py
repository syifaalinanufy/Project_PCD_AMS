from collections import deque

import numpy as np
from PIL import Image

from .basic_ops import _ambang_otsu, ke_array, ke_citra, keabuan, pilihan, slider

BATAS_RG = 400      


def region_growing(img, seed_x=50, seed_y=50, toleransi=20, konektivitas="8 tetangga",
                   tampilan="Wilayah disorot"):
    """Dari titik awal (seed), wilayah melebar ke piksel tetangga yang nilai
    keabuannya beda <= toleransi dari rata-rata wilayah."""
    asli = img
    W0, H0 = img.size
    skala = min(1.0, BATAS_RG / max(W0, H0))
    kecil = img.resize((max(1, round(W0 * skala)), max(1, round(H0 * skala))), Image.BILINEAR) \
        if skala < 1 else img
    g = keabuan(kecil)
    h, w = g.shape
    sx = min(w - 1, int(seed_x / 100 * (w - 1)))
    sy = min(h - 1, int(seed_y / 100 * (h - 1)))
    langkah = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if konektivitas.startswith("8"):
        langkah += [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    masuk = np.zeros((h, w), dtype=bool)
    masuk[sy, sx] = True
    jumlah, total = 1, float(g[sy, sx])
    antrean = deque([(sy, sx)])
    while antrean:
        y, x = antrean.popleft()
        rata = total / jumlah
        for dy, dx in langkah:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not masuk[ny, nx] \
                    and abs(g[ny, nx] - rata) <= toleransi:
                masuk[ny, nx] = True
                jumlah += 1
                total += float(g[ny, nx])
                antrean.append((ny, nx))

    mask = np.asarray(Image.fromarray((masuk * 255).astype(np.uint8)).resize((W0, H0), Image.NEAREST)) > 127
    a = ke_array(asli)
    if tampilan == "Mask hitam-putih":
        hasil = np.where(mask[..., None], 255, 0) * np.ones((1, 1, 3))
    elif tampilan == "Hanya wilayah":
        hasil = np.where(mask[..., None], a, 0)
    else:
        warna = np.array([255, 60, 60], dtype=np.float32)
        hasil = np.where(mask[..., None], 0.35 * a + 0.65 * warna, a)
    persen = 100 * masuk.mean()
    return ke_citra(hasil), f"Wilayah mencakup {persen:.1f}% piksel."


def kmeans(img, k=3, warna="RGB", iterasi=20, tampilan="Warna pusat klaster"):
    """K-Means: piksel dikelompokkan ke k klaster berdasarkan kemiripan nilai;
    tiap piksel diganti warna pusat klasternya. Inisialisasi k-means++ dengan
    seed tetap sehingga hasil konsisten."""
    a = ke_array(img)
    h, w = a.shape[:2]
    data = a.reshape(-1, 3) if warna == "RGB" else keabuan(img).reshape(-1, 1)
    n = len(data)
    k = int(min(k, n))
    rng = np.random.default_rng(42)
    # k-means++: pusat awal menyebar
    pusat = [data[rng.integers(n)]]
    for _ in range(1, k):
        d2 = np.min([((data - c) ** 2).sum(1) for c in pusat], axis=0)
        if d2.sum() == 0:
            pusat.append(data[rng.integers(n)])
        else:
            pusat.append(data[rng.choice(n, p=d2 / d2.sum())])
    pusat = np.array(pusat, dtype=np.float32)
    label = np.zeros(n, dtype=int)
    for _ in range(iterasi):
        jarak = np.stack([((data - c) ** 2).sum(1) for c in pusat], axis=1)
        baru = jarak.argmin(1)
        if _ > 0 and (baru == label).all():
            break
        label = baru
        for j in range(k):
            anggota = data[label == j]
            if len(anggota):
                pusat[j] = anggota.mean(0)
    if tampilan == "Label (abu-abu)":
        urut = np.argsort(pusat.mean(1))
        peringkat = np.empty(k, dtype=int)
        peringkat[urut] = np.arange(k)
        nilai = peringkat[label] * (255 / max(k - 1, 1))
        hasil = nilai.reshape(h, w)
    else:
        hasil = pusat[label].reshape(h, w, -1)
        if hasil.shape[2] == 1:
            hasil = hasil[..., 0]
    return ke_citra(hasil)


def otsu(img, tampilan="Biner"):
    """Otsu: ambang otomatis yang memisahkan latar dan objek dengan
    memaksimalkan varians antar kelas."""
    g = keabuan(img)
    t = _ambang_otsu(g)
    if tampilan == "Biner":
        hasil = np.where(g > t, 255, 0)
    elif tampilan == "Biner terbalik":
        hasil = np.where(g > t, 0, 255)
    else:
        hasil = np.where((g > t)[..., None], ke_array(img), 0)
    return ke_citra(hasil), f"Ambang Otsu = {int(round(float(t)))}"


BATAS_KONTUR = 700      
WARNA_KONTUR = {"Hijau": (0, 255, 0), "Merah": (255, 0, 0), "Biru": (0, 120, 255),
                "Kuning": (255, 220, 0), "Putih": (255, 255, 255)}


def _label(mask, delapan=True):
    """Memberi nomor tiap kelompok piksel True yang saling bersentuhan
    (connected component). Mengembalikan (label, jumlah)."""
    h, w = mask.shape
    label = np.zeros((h, w), dtype=np.int32)
    langkah = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if delapan:
        langkah += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    jumlah = 0
    for y0, x0 in zip(*np.nonzero(mask)):
        if label[y0, x0]:
            continue
        jumlah += 1
        label[y0, x0] = jumlah
        tumpukan = [(y0, x0)]
        while tumpukan:
            y, x = tumpukan.pop()
            for dy, dx in langkah:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not label[ny, nx]:
                    label[ny, nx] = jumlah
                    tumpukan.append((ny, nx))
    return label, jumlah


def _geser_or(m, radius):
    """Menebalkan mask True sebesar radius piksel (dilasi kotak)."""
    if radius <= 0:
        return m
    p = np.pad(m, radius)
    h, w = m.shape
    hasil = np.zeros_like(m)
    for dy in range(2 * radius + 1):
        for dx in range(2 * radius + 1):
            hasil |= p[dy:dy + h, dx:dx + w]
    return hasil


def contour_detection(img, ambang=0, objek="Terang", luas_min=0.1, tebal=2, warna="Hijau"):
    """Deteksi kontur luar (seperti RETR_EXTERNAL): biner -> cari tiap objek ->
    ambil tepi terluarnya -> gambar di atas citra asli. Lubang di dalam objek
    tidak dihitung sebagai objek lain."""
    W0, H0 = img.size
    skala = min(1.0, BATAS_KONTUR / max(W0, H0))
    kecil = img.resize((max(1, round(W0 * skala)), max(1, round(H0 * skala))),
                       Image.BILINEAR) if skala < 1 else img
    g = keabuan(kecil)
    t = _ambang_otsu(g) if ambang == 0 else ambang
    biner = (g > t) if objek == "Terang" else (g <= t)

    latar, _ = _label(~biner, delapan=False)
    tepi_citra = np.unique(np.concatenate([latar[0], latar[-1], latar[:, 0], latar[:, -1]]))
    terisi = ~np.isin(latar, tepi_citra[tepi_citra > 0]) | biner

    label, jumlah = _label(terisi, delapan=True)
    luas = np.bincount(label.ravel(), minlength=jumlah + 1)
    batas = luas_min / 100 * terisi.size
    benar = [i for i in range(1, jumlah + 1) if luas[i] >= batas]
    objek_ok = np.isin(label, benar)

    p = np.pad(objek_ok, 1)
    h, w = objek_ok.shape
    dalam = p[:h, 1:w + 1] & p[2:, 1:w + 1] & p[1:h + 1, :w] & p[1:h + 1, 2:]
    garis = objek_ok & ~dalam

    garis_penuh = np.asarray(Image.fromarray((garis * 255).astype(np.uint8))
                             .resize((W0, H0), Image.NEAREST)) > 127
    garis_penuh = _geser_or(garis_penuh, max(0, int(tebal) // 2 + (1 if skala < 1 else 0) - 1)
                            if tebal > 1 else (1 if skala < 1 else 0))
    hasil = ke_array(img).copy()
    hasil[garis_penuh] = WARNA_KONTUR[warna]
    return ke_citra(hasil), f"Jumlah kontur/objek terdeteksi: {len(benar)}"


OPERASI = {
    "Region Growing": {"fungsi": region_growing, "params": [
        slider("seed_x", "Seed X", 0, 100, 50, satuan="%"),
        slider("seed_y", "Seed Y", 0, 100, 50, satuan="%"),
        slider("toleransi", "Toleransi", 1, 100, 20),
        pilihan("konektivitas", "Konektivitas", ["8 tetangga", "4 tetangga"]),
        pilihan("tampilan", "Tampilan", ["Wilayah disorot", "Hanya wilayah", "Mask hitam-putih"])]},
    "K-Means Clustering": {"fungsi": kmeans, "params": [
        slider("k", "Jumlah klaster (K)", 2, 10, 3),
        pilihan("warna", "Ruang warna", ["RGB", "Keabuan"]),
        pilihan("tampilan", "Tampilan", ["Warna pusat klaster", "Label (abu-abu)"])]},
    "Contour Detection": {"fungsi": contour_detection, "params": [
        slider("ambang", "Ambang (0 = Otsu otomatis)", 0, 255, 0),
        pilihan("objek", "Objek berwarna", ["Terang", "Gelap"]),
        slider("luas_min", "Luas minimum objek", 0, 5, 0.1, 0.1, "%"),
        slider("tebal", "Tebal garis", 1, 6, 2),
        pilihan("warna", "Warna garis", list(WARNA_KONTUR))]},
    "Otsu Thresholding": {"fungsi": otsu, "params": [
        pilihan("tampilan", "Tampilan", ["Biner", "Biner terbalik", "Objek berwarna"])]},
}
