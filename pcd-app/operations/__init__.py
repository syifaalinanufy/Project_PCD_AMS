from .basic_ops import OPERASI as _BASIC_OPS
from .dua_citra import DUA_CITRA
from .edge import OPERASI as _EDGE
from .enhancement import OPERASI as _ENH
from .noise import OPERASI as _NOISE
from .segmentation import OPERASI as _SEG
from .histogram import hitung_histogram  

# Basic Ops: operasi dengan dua citra berbeda (Add, AND, dst.)
OPS = {**_BASIC_OPS, **DUA_CITRA}

GRUP = {
    "ops": OPS,
    "enh": _ENH,
    "noise": _NOISE,
    "edge": _EDGE,
    "seg": _SEG,
}

# Teks tombol di ribbon
ALIAS = {
    "Add (+)": "Add",
    "Subtract (-)": "Subtract",
    "Multiply (x)": "Multiply",
    "Divide (÷)": "Divide",
}


def cari(grup, nama):
    daftar = GRUP.get(grup, {})
    return daftar.get(ALIAS.get(nama, nama))


def metadata(grup):
    
    hasil = {}
    for nama in list(GRUP.get(grup, {})) + list(ALIAS):
        d = cari(grup, nama)
        if d:
            hasil[nama] = {"params": d["params"], "dua_citra": d.get("dua_citra")}
    return hasil


def _konversi(definisi, form):
    
    argumen = {}
    for p in definisi:
        mentah = form.get(p["kunci"])
        if mentah in (None, ""):
            argumen[p["kunci"]] = p["default"]
        elif p["tipe"] == "slider":
            try:
                v = float(mentah)
            except ValueError:
                raise ValueError(f"Nilai '{p['label']}' tidak valid.")
            v = min(max(v, p["min"]), p["max"])
            argumen[p["kunci"]] = int(round(v)) if isinstance(p["langkah"], int) else v
        else:
            if mentah not in p["opsi"]:
                raise ValueError(f"Pilihan '{p['label']}' tidak valid.")
            argumen[p["kunci"]] = mentah
    return argumen


def jalankan(grup, nama, img, form, citra_b=None):

    d = cari(grup, nama)
    if d is None:
        raise KeyError(nama)
    argumen = _konversi(d["params"], form)
    mode = d.get("dua_citra")
    if mode == "wajib" or (mode == "opsional" and form.get("mode") == "image"):
        if citra_b is None:
            raise ValueError("Pilih Gambar B terlebih dahulu.")
        argumen["citra_b"] = citra_b
    hasil = d["fungsi"](img, **argumen)
    # fungsi boleh mengembalikan (citra, info); info = teks notifikasi
    return hasil if isinstance(hasil, tuple) else (hasil, "")
