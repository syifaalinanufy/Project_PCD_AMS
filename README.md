# PicForge — Aplikasi Pengolahan Citra Digital

PicForge adalah aplikasi web untuk mempelajari dan mencoba operasi pengolahan citra digital secara langsung. Pengguna cukup membuka gambar, memilih operasi, mengatur parameternya, lalu melihat hasilnya beserta **histogram** dan **statistik** citra (min, max, rata-rata, median, standar deviasi, jumlah piksel).

Aplikasi ini dibuat sebagai tugas besar mata kuliah **Pengolahan Citra Digital** oleh **Kelompok AMS, kelas TI B**.

| Nama | NIM | Peran |
| --- | --- | --- |
| Anggita Natarina | 2407113014 | Ketua kelompok |
| Syifa 'Alin Anufy | 2407134839 | Anggota |
| Marsha Harliani Azzahra | 2407112388 | Anggota |

---

## Fitur utama

- **54 operasi** pengolahan citra di dalam 5 menu: Basic Ops, Enhancement, Noise, Edge Detection, dan Segmentation.
- **Parameter** lewat slider dan pilihan untuk setiap operasi.
- **Operasi berantai**: hasil terakhir otomatis menjadi masukan operasi berikutnya.
- **Undo** dan **Reset** untuk kembali ke hasil sebelumnya atau ke citra asli.
- **Histogram** kanal Keabuan, Merah, Hijau, dan Biru, lengkap dengan statistik citra.
- **Operasi Boolean** (AND, OR, XOR) dengan citra pembanding berbentuk lingkaran, persegi, atau setengah kiri yang dibuat otomatis.
- Semua perhitungan memakai **NumPy** dan **Pillow**, tanpa OpenCV.

## Teknologi

| Bagian | Teknologi |
| --- | --- |
| Server | Python 3, Flask |
| Pengolahan citra | NumPy, Pillow |
| Tampilan | HTML, CSS, JavaScript |

---

## Struktur folder

```
Project_PCD_AMS/
├── README.md
├── requirements.txt
└── pcd-app/
    ├── app.py                  # server Flask dan endpoint API
    ├── operations/
    │   ├── __init__.py         # pusat pemanggil operasi
    │   ├── basic_ops.py        # menu Basic Ops
    │   ├── enhancement.py      # menu Enhancement
    │   ├── noise.py            # menu Noise
    │   ├── edge.py             # menu Edge Detection
    │   ├── segmentation.py     # menu Segmentation
    │   ├── helper.py           # fungsi bantu (konvolusi, blur, filter frekuensi)
    │   └── histogram.py        # histogram dan statistik
    ├── templates/
    │   ├── landingpage.html    # halaman depan
    │   └── index.html          # halaman aplikasi
    └── static/
        ├── css/style.css
        ├── js/pemroses.js      # logika tampilan, pengiriman data, histogram
        └── img/
```

---

## Cara menjalankan aplikasi

### 1. Persiapan

Pastikan **Python 3.10 atau lebih baru** sudah terpasang. Cek dengan:

```bash
python --version
```

### 2. Unduh proyek

```bash
git clone https://github.com/syifaalinanufy/Project_PCD_AMS.git
cd Project_PCD_AMS
```

Atau unduh ZIP dari GitHub (tombol **Code → Download ZIP**), lalu ekstrak.

### 3. Virtual environment

```bash
python -m venv venv
```

Aktifkan:

- **Windows:** `venv\Scripts\activate`
- **macOS / Linux:** `source venv/bin/activate`

### 4. Install Library yang dibutuhkan

```bash
pip install -r requirements.txt
```

### 5. Menjalankan server

```bash
cd pcd-app
python app.py
```

### 6. Buka di browser

| Alamat | Halaman |
| --- | --- |
| http://127.0.0.1:5000/ | Landing page |
| http://127.0.0.1:5000/app | Halaman aplikasi |

Untuk menghentikan server, tekan **Ctrl + C** di terminal.

---

## Cara memakai

1. Buka menu **File → Open**, lalu pilih gambar (JPG atau PNG).
2. Pilih salah satu menu di sidebar: **Basic Ops**, **Enhancement**, **Noise**, **Edge Detection**, atau **Segmentation**.
3. Pilih operasi, lalu atur parameternya lewat slider atau pilihan yang muncul.
4. Klik **Terapkan**. Hasilnya tampil di panel **Gambar Hasil**, lengkap dengan histogram dan statistiknya.
5. Untuk operasi berikutnya, klik **Terapkan** lagi pada operasi lain. Operasi akan diterapkan pada hasil terakhir.
6. Klik **Undo** untuk membatalkan operasi terakhir, atau **Reset** untuk kembali ke citra asli.
7. Untuk operasi **AND, OR, dan XOR**, pilih bentuk citra pembanding (Lingkaran, Persegi, atau Setengah kiri). Citra pembanding berupa bentuk putih di atas latar hitam yang dibuat otomatis seukuran gambar, sehingga AND dapat dipakai untuk memotong (*masking*) bagian gambar.
8. Gunakan dropdown di bawah histogram untuk melihat histogram kanal **Keabuan**, **Merah**, **Hijau**, atau **Biru**.

**Tips:**

- Batas ukuran unggahan adalah **16 MB**. Karena hasil setiap operasi dikirim ulang dalam format PNG, gunakan foto sekitar **1–2 megapiksel** (misalnya sisi terpanjang 1280–2000 piksel) agar operasi berantai tetap lancar dan cepat.
- Foto dari HP otomatis ditegakkan sesuai orientasinya.

---

## Daftar operasi

### Basic Ops (25 operasi)

| Kelompok | Operasi |
| --- | --- |
| Operasi titik | Negative, Thresholding (Binary, Binary Inverse, Truncate, To Zero), Binary (Otsu / ambang tetap) |
| Aritmetika | Add, Subtract (dengan nilai konstanta), Multiply, Divide (dengan faktor pengali/pembagi) |
| Boolean | NOT, AND, OR, XOR (AND, OR, XOR dengan citra pembanding berbentuk Lingkaran, Persegi, atau Setengah kiri) |
| Geometri | Translation, Rotation, Zooming, Flipping, Cropping |
| Warna | Grayscale (Luminance, Rata-rata, Lightness), RGB, HSV, CMY, YUV, YIQ, Pseudo color |
| Konvolusi dan frekuensi | Convolution (Blur, Gaussian, Sharpen, Emboss, Outline), Fourier Transform |

### Enhancement (12 operasi)

| Kelompok | Operasi |
| --- | --- |
| Kecerahan dan kontras | Brightness, Contrast (rumus Tengah 128 atau Y = αX), Hist. Equalization (Luminance atau per kanal RGB) |
| Geometri | Geometrics correction (distorsi lensa dan rotasi) |
| Filter spasial | Lowpass Filtering, Median Filtering, Highpass Filtering, Highboost Filtering |
| Filter frekuensi | ILPF, BLPF, IHPF, BHPF |

### Noise (6 operasi)

Gaussian Noise, Rayleigh Noise, Erlang (Gamma) Noise, Exponential Noise, Uniform Noise, Impulse Noise (salt and pepper).

Setiap noise dapat diterapkan per kanal RGB atau pada keabuan, dengan **seed** agar hasilnya bisa diulang.

### Edge Detection (7 operasi)

Sobel, Prewitt, Roberts, Laplacian, Laplacian of Gaussian, Canny, Compass (Kirsch).

### Segmentation (4 operasi)

Region Growing, K-Means Clustering, Contour Detection, Otsu Thresholding.

---

## Cara kerja singkat

1. Browser (`pemroses.js`) mengirim gambar dan parameter ke endpoint **`POST /api/process`**.
2. `app.py` membaca gambar, lalu `operations.jalankan()` memanggil fungsi operasi yang sesuai.
3. Fungsi operasi menghitung hasilnya dengan NumPy, lalu hasilnya dirapikan ke rentang 0–255.
4. Server menghitung histogram dan statistik, lalu mengirim balik gambar hasil (PNG base64), histogram, dan statistik dalam format JSON.
5. Browser menampilkan hasilnya dan menyimpannya di riwayat untuk fitur Undo.

---

© 2026 Kelompok AMS — Pengolahan Citra Digital, kelas TI B.