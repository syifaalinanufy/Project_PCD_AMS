import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


# ====================== fungsi bantu ======================

def ke_array(img):
    """Citra Pillow -> array float (tinggi x lebar x 3)."""
    return np.asarray(img, dtype=np.float32)


def ke_citra(arr):
    """Array -> citra RGB. Nilai dibulatkan dan dipotong ke 0..255.
    Array 2D (keabuan) otomatis dijadikan RGB agar semua hasil seragam."""
    arr = np.clip(np.rint(arr), 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    return img if img.mode == "RGB" else img.convert("RGB")


def keabuan(img):
    """Citra RGB -> array 2D keabuan dengan rumus luminance."""
    a = ke_array(img)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def hsv_ke_rgb(h, s, v):
    """Konversi HSV (semua 0..1) ke RGB (0..255) untuk satu array penuh."""
    i = np.floor(h * 6).astype(int) % 6
    f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=-1) * 255


# ====================== Basic Ops ======================

def negative(img):
    """Membalik nilai tiap piksel: hasil = 255 - nilai."""
    return ke_citra(255 - ke_array(img))


def thresholding(img, ambang=128, jenis="Binary"):
    """Memisahkan piksel berdasarkan ambang batas pada citra keabuan."""
    g = keabuan(img)
    if jenis == "Binary":
        hasil = np.where(g > ambang, 255, 0)
    elif jenis == "Binary Inverse":
        hasil = np.where(g > ambang, 0, 255)
    elif jenis == "Truncate":
        hasil = np.minimum(g, ambang)        # nilai di atas ambang dipotong
    else:                                    # To Zero
        hasil = np.where(g > ambang, g, 0)   # nilai di bawah ambang jadi 0
    return ke_citra(hasil)


# Kernel konvolusi: (ukuran, isi kernel, pembagi/scale, offset)
KERNEL = {
    "Blur 3x3": ((3, 3), [1] * 9, 9, 0),
    "Gaussian 5x5": ((5, 5), [a * b for a in (1, 4, 6, 4, 1) for b in (1, 4, 6, 4, 1)], 256, 0),
    "Sharpen": ((3, 3), [0, -1, 0, -1, 5, -1, 0, -1, 0], 1, 0),
    "Emboss": ((3, 3), [-2, -1, 0, -1, 1, 1, 0, 1, 2], 1, 128),
    "Outline": ((3, 3), [-1, -1, -1, -1, 8, -1, -1, -1, -1], 1, 0),
}


def convolution(img, kernel="Blur 3x3", ulangi=1):
    """Konvolusi dengan kernel pilihan; bisa diulang beberapa kali."""
    ukuran, isi, skala, offset = KERNEL[kernel]
    filt = ImageFilter.Kernel(ukuran, isi, scale=skala, offset=offset)
    hasil = img
    for _ in range(int(ulangi)):
        hasil = hasil.filter(filt)
    return hasil


def fourier_transform(img, tampilan="Spektrum magnitudo"):
    """Transformasi Fourier 2D, ditampilkan sebagai spektrum frekuensi."""
    g = keabuan(img)
    # fftshift memindahkan frekuensi rendah ke tengah gambar
    F = np.fft.fftshift(np.fft.fft2(g))
    if tampilan == "Spektrum magnitudo":
        m = np.log1p(np.abs(F))              # log supaya detailnya terlihat
        hasil = m / m.max() * 255
    else:
        hasil = (np.angle(F) + np.pi) / (2 * np.pi) * 255
    return ke_citra(hasil)


# ---------------------- Arithmetic ----------------------

def add(img, nilai=50):
    return ke_citra(ke_array(img) + nilai)


def subtract(img, nilai=50):
    return ke_citra(ke_array(img) - nilai)


def multiply(img, faktor=1.5):
    return ke_citra(ke_array(img) * faktor)


def divide(img, pembagi=1.5):
    return ke_citra(ke_array(img) / max(pembagi, 0.1))   # hindari bagi nol


# ---------------------- Boolean ----------------------

def _citra_kedua(img, bentuk):
    """Citra pembanding untuk AND/OR/XOR: bentuk putih di atas latar hitam."""
    w, h = img.size
    kedua = Image.new("RGB", (w, h), (0, 0, 0))
    gambar = ImageDraw.Draw(kedua)
    putih = (255, 255, 255)
    if bentuk == "Lingkaran":
        r = min(w, h) * 0.4
        gambar.ellipse([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r], fill=putih)
    elif bentuk == "Persegi":
        s = min(w, h) * 0.35
        gambar.rectangle([w / 2 - s, h / 2 - s, w / 2 + s, h / 2 + s], fill=putih)
    else:                                      # Setengah kiri
        gambar.rectangle([0, 0, w // 2, h], fill=putih)
    return np.asarray(kedua, dtype=np.uint8)


def _boolean(img, fungsi, bentuk):
    a = np.asarray(img, dtype=np.uint8)
    return Image.fromarray(fungsi(a, _citra_kedua(img, bentuk)))


def bool_not(img):
    return Image.fromarray(np.bitwise_not(np.asarray(img, dtype=np.uint8)))


def bool_and(img, bentuk="Lingkaran"):
    return _boolean(img, np.bitwise_and, bentuk)


def bool_or(img, bentuk="Lingkaran"):
    return _boolean(img, np.bitwise_or, bentuk)


def bool_xor(img, bentuk="Lingkaran"):
    return _boolean(img, np.bitwise_xor, bentuk)


# ---------------------- Geometrics ----------------------

def translation(img, geser_x=10, geser_y=5):
    """Menggeser citra; geser dalam persen dari lebar/tinggi."""
    w, h = img.size
    dx, dy = w * geser_x / 100, h * geser_y / 100
    # transform memetakan koordinat hasil ke sumber, jadi tandanya dibalik
    return img.transform(img.size, Image.Transform.AFFINE,
                         (1, 0, -dx, 0, 1, -dy),
                         resample=Image.Resampling.BILINEAR, fillcolor=(0, 0, 0))


def rotation(img, sudut=30):
    """Memutar citra berlawanan arah jarum jam; sudut kosong diisi hitam."""
    return img.rotate(sudut, resample=Image.Resampling.BICUBIC, fillcolor=(0, 0, 0))


def zooming(img, skala=150):
    """Memperbesar/memperkecil terhadap titik tengah, ukuran gambar tetap."""
    w, h = img.size
    s = skala / 100
    besar = img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.Resampling.BICUBIC)
    kanvas = Image.new("RGB", (w, h), (0, 0, 0))
    # tempel di tengah; bagian yang keluar bingkai terpotong otomatis
    kanvas.paste(besar, ((w - besar.width) // 2, (h - besar.height) // 2))
    return kanvas


def flipping(img, arah="Horizontal"):
    if arah == "Horizontal":
        return ImageOps.mirror(img)
    if arah == "Vertikal":
        return ImageOps.flip(img)
    return img.rotate(180)                    # horizontal + vertikal


def cropping(img, ukuran=60, posisi_x=50, posisi_y=50):
    """Memotong sebagian citra. Ukuran dalam persen, posisi 0-100 persen."""
    w, h = img.size
    cw, ch = max(1, int(w * ukuran / 100)), max(1, int(h * ukuran / 100))
    kiri = int((w - cw) * posisi_x / 100)
    atas = int((h - ch) * posisi_y / 100)
    return img.crop((kiri, atas, kiri + cw, atas + ch))


# ---------------------- Colouring ----------------------

def binary(img, metode="Otsu (otomatis)", ambang=128):
    """Citra biner: ambang tetap atau dihitung otomatis dengan metode Otsu."""
    g = keabuan(img)
    if metode.startswith("Otsu"):
        ambang = _ambang_otsu(g)
    return ke_citra(np.where(g > ambang, 255, 0))


def _ambang_otsu(g):
    """Mencari ambang yang memaksimalkan selisih antar-kelas (metode Otsu)."""
    hist = np.bincount(np.clip(g, 0, 255).astype(np.uint8).ravel(), minlength=256)
    total = hist.sum()
    jumlah = np.dot(np.arange(256), hist)
    bobot_b, jumlah_b, terbaik, ambang = 0, 0.0, -1.0, 128
    for t in range(256):
        bobot_b += hist[t]
        if bobot_b == 0:
            continue
        bobot_f = total - bobot_b
        if bobot_f == 0:
            break
        jumlah_b += t * hist[t]
        selisih = jumlah_b / bobot_b - (jumlah - jumlah_b) / bobot_f
        antar_kelas = bobot_b * bobot_f * selisih ** 2
        if antar_kelas > terbaik:
            terbaik, ambang = antar_kelas, t
    return ambang


def grayscale(img, metode="Luminance"):
    a = ke_array(img)
    if metode == "Luminance":
        g = keabuan(img)
    elif metode == "Rata-rata RGB":
        g = a.mean(axis=2)
    else:                                      # Lightness
        g = (a.max(axis=2) + a.min(axis=2)) / 2
    return ke_citra(g)


def rgb(img, kanal="Merah", tampilan="Berwarna"):
    """Menampilkan satu kanal R/G/B, berwarna atau sebagai skala abu-abu."""
    a = ke_array(img)
    idx = ["Merah", "Hijau", "Biru"].index(kanal)
    if tampilan == "Skala abu-abu":
        return ke_citra(a[..., idx])
    hasil = np.zeros_like(a)
    hasil[..., idx] = a[..., idx]
    return ke_citra(hasil)


def _pilih_kanal(kanal3, pilihan, daftar):
    """Bantu HSV/CMY/YUV/YIQ: 'Gabungan' = 3 kanal sebagai RGB, selain itu
    satu kanal ditampilkan sebagai skala abu-abu."""
    if pilihan == "Gabungan":
        return ke_citra(kanal3)
    return ke_citra(kanal3[..., daftar.index(pilihan)])


def hsv(img, kanal="Gabungan"):
    a = np.asarray(img.convert("HSV"), dtype=np.float32)   # H, S, V (0..255)
    return _pilih_kanal(a, kanal, ["Hue", "Saturation", "Value"])


def cmy(img, kanal="Gabungan"):
    a = 255 - ke_array(img)                    # C = 255-R, M = 255-G, Y = 255-B
    return _pilih_kanal(a, kanal, ["Cyan", "Magenta", "Yellow"])


def yuv(img, kanal="Gabungan"):
    a = ke_array(img)
    y = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    u = 0.492 * (a[..., 2] - y) + 128          # +128 agar nilai negatif terlihat
    v = 0.877 * (a[..., 0] - y) + 128
    return _pilih_kanal(np.stack([y, u, v], axis=-1), kanal, ["Y", "U", "V"])


def yiq(img, kanal="Gabungan"):
    a = ke_array(img)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    i = 0.596 * r - 0.274 * g - 0.322 * b + 128
    q = 0.211 * r - 0.523 * g + 0.312 * b + 128
    return _pilih_kanal(np.stack([y, i, q], axis=-1), kanal, ["Y", "I", "Q"])


def pseudo(img, peta="Pelangi"):
    """Pseudo-color: tiap tingkat keabuan diberi warna dari peta warna."""
    g = keabuan(img) / 255
    if peta == "Pelangi":                       # biru (gelap) -> merah (terang)
        return ke_citra(hsv_ke_rgb((1 - g) * 0.7, np.ones_like(g), np.ones_like(g)))
    if peta == "Panas":                         # hitam -> merah -> kuning -> putih
        r = np.clip(3 * g, 0, 1)
        gr = np.clip(3 * g - 1, 0, 1)
        b = np.clip(3 * g - 2, 0, 1)
    else:                                       # Dingin: biru -> cyan -> putih
        r = np.clip(2 * g - 1, 0, 1)
        gr = np.clip(2 * g, 0, 1)
        b = np.ones_like(g)
    return ke_citra(np.stack([r, gr, b], axis=-1) * 255)


# ====================== pendaftaran operasi ======================
# slider(): parameter berupa angka  |  pilihan(): parameter berupa daftar.
# "kunci" harus sama dengan nama argumen fungsi di atas.

def slider(kunci, label, minimum, maksimum, default, langkah=1, satuan=""):
    return {"kunci": kunci, "label": label, "tipe": "slider", "min": minimum,
            "max": maksimum, "default": default, "langkah": langkah, "satuan": satuan}


def pilihan(kunci, label, opsi, default=None):
    return {"kunci": kunci, "label": label, "tipe": "pilihan", "opsi": opsi,
            "default": default or opsi[0]}


BENTUK = pilihan("bentuk", "Bentuk citra ke-2", ["Lingkaran", "Persegi", "Setengah kiri"])
GABUNGAN = lambda *kanal: pilihan("kanal", "Tampilkan", ["Gabungan", *kanal])

OPERASI = {
    "Negative": {"fungsi": negative, "params": []},
    "Thresholding": {"fungsi": thresholding, "params": [
        slider("ambang", "Ambang batas", 0, 255, 128),
        pilihan("jenis", "Jenis", ["Binary", "Binary Inverse", "Truncate", "To Zero"])]},
    "Convolution": {"fungsi": convolution, "params": [
        pilihan("kernel", "Kernel", list(KERNEL)),
        slider("ulangi", "Pengulangan", 1, 5, 1, satuan="x")]},
    "Fourier Transform": {"fungsi": fourier_transform, "params": [
        pilihan("tampilan", "Tampilan", ["Spektrum magnitudo", "Spektrum fase"])]},

    "Add": {"fungsi": add, "params": [slider("nilai", "Nilai Konstanta", 0, 255, 50)]},
    "Subtract": {"fungsi": subtract, "params": [slider("nilai", "Nilai Konstanta", 0, 255, 50)]},
    "Multiply": {"fungsi": multiply, "params": [slider("faktor", "Faktor pengali", 0.1, 5, 1.5, 0.1, "x")]},
    "Divide": {"fungsi": divide, "params": [slider("pembagi", "Faktor pembagi", 0.2, 5, 1.5, 0.1, "x")]},

    "NOT": {"fungsi": bool_not, "params": []},
    "AND": {"fungsi": bool_and, "params": [BENTUK]},
    "OR": {"fungsi": bool_or, "params": [BENTUK]},
    "XOR": {"fungsi": bool_xor, "params": [BENTUK]},

    "Translation": {"fungsi": translation, "params": [
        slider("geser_x", "Geser horizontal", -100, 100, 10, satuan="%"),
        slider("geser_y", "Geser vertikal", -100, 100, 5, satuan="%")]},
    "Rotation": {"fungsi": rotation, "params": [slider("sudut", "Sudut", -180, 180, 30, satuan="°")]},
    "Zooming": {"fungsi": zooming, "params": [slider("skala", "Skala", 25, 300, 150, satuan="%")]},
    "Flipping": {"fungsi": flipping, "params": [
        pilihan("arah", "Arah", ["Horizontal", "Vertikal", "Horizontal + Vertikal"])]},
    "Cropping": {"fungsi": cropping, "params": [
        slider("ukuran", "Ukuran area", 10, 95, 60, satuan="%"),
        slider("posisi_x", "Posisi horizontal", 0, 100, 50, satuan="%"),
        slider("posisi_y", "Posisi vertikal", 0, 100, 50, satuan="%")]},

    "Binary": {"fungsi": binary, "params": [
        pilihan("metode", "Metode", ["Otsu (otomatis)", "Ambang tetap"]),
        slider("ambang", "Ambang (untuk ambang tetap)", 0, 255, 128)]},
    "Grayscale": {"fungsi": grayscale, "params": [
        pilihan("metode", "Metode", ["Luminance", "Rata-rata RGB", "Lightness"])]},
    "RGB": {"fungsi": rgb, "params": [
        pilihan("kanal", "Kanal", ["Merah", "Hijau", "Biru"]),
        pilihan("tampilan", "Tampilan", ["Berwarna", "Skala abu-abu"])]},
    "HSV": {"fungsi": hsv, "params": [GABUNGAN("Hue", "Saturation", "Value")]},
    "CMY": {"fungsi": cmy, "params": [GABUNGAN("Cyan", "Magenta", "Yellow")]},
    "YUV": {"fungsi": yuv, "params": [GABUNGAN("Y", "U", "V")]},
    "YIQ": {"fungsi": yiq, "params": [GABUNGAN("Y", "I", "Q")]},
    "Pseudo": {"fungsi": pseudo, "params": [pilihan("peta", "Peta warna", ["Pelangi", "Panas", "Dingin"])]},
}