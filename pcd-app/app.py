import base64
import io

from flask import Flask, jsonify, render_template, request
from PIL import Image, ImageOps, UnidentifiedImageError

import operations 

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024      # batas upload 16 MB


@app.route("/")
def landing():
    return render_template("landingpage.html")


@app.route("/app")
def editor():
    return render_template("index.html")


def baca_gambar(berkas): #fungsi untuk membaca file gambar
    if berkas is None:
        return None
    try:
        img = Image.open(berkas.stream)
        img = ImageOps.exif_transpose(img)       
        return img.convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise ValueError("File bukan gambar yang valid.")


def ke_data_url(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


@app.route("/api/operasi/<grup>")
def daftar_operasi(grup):
    """Definisi parameter tiap operasi, dipakai browser untuk membuat slider/pilihan."""
    return jsonify(operations.metadata(grup))


@app.route("/api/process", methods=["POST"])
def process():
    try:
        grup = request.form.get("group", "")
        nama = request.form.get("op", "")

        img = baca_gambar(request.files.get("image"))
        if img is None:
            return jsonify(error="Buka gambar dulu lewat File > Open."), 400
        citra_b = baca_gambar(request.files.get("imageB"))

        try:
            hasil, info = operations.jalankan(grup, nama, img, request.form, citra_b)
        except KeyError:
            return jsonify(error=f"Operasi '{nama}' belum tersedia."), 501

        histogram, statistik = operations.hitung_histogram(hasil)
        return jsonify(image=ke_data_url(hasil), histogram=histogram,
                       statistik=statistik, info=info)
    except ValueError as e:                               #kesalahan input pengguna
        return jsonify(error=str(e)), 400
    except Exception as e:                                #kesalahan tak terduga
        app.logger.exception("Gagal memproses gambar")
        return jsonify(error=f"Gagal memproses: {e}"), 500


if __name__ == "__main__":
    app.run(debug=True)