"""
Operasi Basic Ops yang bisa memakai citra kedua (Gambar B).

- Arithmetic (Add, Subtract, Multiply, Divide): OPSIONAL. Tanpa Gambar B
  memakai nilai skala dari basic_ops.py; dengan Gambar B dihitung per piksel.
- Boolean (AND, OR, XOR): WAJIB dua gambar.

File ini memakai ulang fungsi bantu dari basic_ops.py tanpa mengubahnya.
Pendaftaran di bawah menimpa versi lama di operations/__init__.py.
"""
import numpy as np
from PIL import Image

from . import basic_ops as dasar
from .basic_ops import ke_array, ke_citra


def _samakan(citra_b, img):
    """Ubah Gambar B ke RGB dan ukuran Gambar A agar bisa dihitung per piksel."""
    b = citra_b.convert("RGB")
    if b.size != img.size:
        b = b.resize(img.size, Image.Resampling.BICUBIC)
    return b


# ---------------------- Arithmetic ----------------------

def add(img, nilai=50, citra_b=None):
    if citra_b is None:
        return dasar.add(img, nilai)
    return ke_citra(ke_array(img) + ke_array(_samakan(citra_b, img)))


def subtract(img, nilai=50, citra_b=None):
    if citra_b is None:
        return dasar.subtract(img, nilai)
    return ke_citra(ke_array(img) - ke_array(_samakan(citra_b, img)))


def multiply(img, faktor=1.5, citra_b=None):
    if citra_b is None:
        return dasar.multiply(img, faktor)
    # dinormalisasi /255 supaya hasil tetap di rentang 0..255
    return ke_citra(ke_array(img) * ke_array(_samakan(citra_b, img)) / 255)


def divide(img, pembagi=1.5, citra_b=None):
    if citra_b is None:
        return dasar.divide(img, pembagi)
    b = np.maximum(ke_array(_samakan(citra_b, img)), 1)      # hindari bagi nol
    return ke_citra(ke_array(img) / b * 128)                 # A = B -> abu-abu tengah


# ---------------------- Boolean ----------------------

def _boolean(img, citra_b, fungsi):
    if citra_b is None:
        raise ValueError("Pilih Gambar B terlebih dahulu.")
    a = np.asarray(img.convert("RGB"), dtype=np.uint8)
    b = np.asarray(_samakan(citra_b, img), dtype=np.uint8)
    return Image.fromarray(fungsi(a, b))


def bool_and(img, citra_b=None):
    return _boolean(img, citra_b, np.bitwise_and)


def bool_or(img, citra_b=None):
    return _boolean(img, citra_b, np.bitwise_or)


def bool_xor(img, citra_b=None):
    return _boolean(img, citra_b, np.bitwise_xor)


# ---------------------- pendaftaran ----------------------
# "dua_citra": "opsional" = Gambar B boleh dipakai | "wajib" = harus ada Gambar B
_P = dasar.OPERASI

DUA_CITRA = {
    "Add": {"fungsi": add, "params": _P["Add"]["params"], "dua_citra": "opsional"},
    "Subtract": {"fungsi": subtract, "params": _P["Subtract"]["params"], "dua_citra": "opsional"},
    "Multiply": {"fungsi": multiply, "params": _P["Multiply"]["params"], "dua_citra": "opsional"},
    "Divide": {"fungsi": divide, "params": _P["Divide"]["params"], "dua_citra": "opsional"},
    "AND": {"fungsi": bool_and, "params": [], "dua_citra": "wajib"},
    "OR": {"fungsi": bool_or, "params": [], "dua_citra": "wajib"},
    "XOR": {"fungsi": bool_xor, "params": [], "dua_citra": "wajib"},
}
