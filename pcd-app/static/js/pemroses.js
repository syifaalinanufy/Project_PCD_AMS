(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  const GRUP = [
    { kunci: "ops", view: "opsView", tombol: "basicBtn" },
    { kunci: "enh", view: "enhView", tombol: "enhBtn" },
    { kunci: "noise", view: "noiseView", tombol: "noiseBtn" },
    { kunci: "edge", view: "edgeView", tombol: "edgeBtn" },
    { kunci: "seg", view: "segView", tombol: "segBtn" },
  ];
  const WARNA = { gray: "#565f3f", r: "#b5453a", g: "#4f8a4f", b: "#3d5f9e" };

  let fileA = null; /* gambar yang dibuka */
  let fileB = null; /* Gambar B (operasi dua gambar) */
  let sedangProses = false;
  const riwayat = []; /* hasil tiap Terapkan; dipakai semua menu */

  /* gaya kotak angka di samping slider (ditambahkan dari sini agar tidak perlu mengubah CSS) */
  const gaya = document.createElement("style");
  gaya.textContent =
    ".p-baris{display:flex;justify-content:space-between;align-items:center;gap:8px}" +
    ".p-angka-wrap{display:inline-flex;align-items:center;gap:4px;font-size:12px}" +
    ".p-angka{width:70px;padding:3px 6px;border:1px solid var(--pasir);border-radius:6px;" +
    "background:var(--krem);color:var(--teks);font:inherit;font-weight:600;text-align:right}";
  document.head.appendChild(gaya);

  /* ---------- bantu ---------- */
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => t.classList.remove("show"), 3200);
  }

  GRUP.forEach((g) => {
    g.el = $("#" + g.view);
    g.box = $(".p-box", g.el);
    g.meta = {}; /* definisi parameter dari server */
    g.nama = null; /* operasi yang sedang dipilih */
  });
  const grupAktif = () => GRUP.find((g) => !g.el.classList.contains("hidden"));

  /* ---------- pindah tampilan ---------- */
  const SEMUA_VIEW = ["homeView", "aboutView", ...GRUP.map((g) => g.view)];
  function showView(viewId, tombolId) {
    SEMUA_VIEW.forEach((v) => $("#" + v).classList.add("hidden"));
    $$(".sidebar > button").forEach((b) => b.classList.remove("active"));
    $("#" + viewId).classList.remove("hidden");
    if (tombolId) $("#" + tombolId).classList.add("active");
    gambarSemuaHistogram(); /* canvas baru punya ukuran setelah tampil */
  }
  GRUP.forEach((g) =>
    $("#" + g.tombol).addEventListener("click", () =>
      showView(g.view, g.tombol),
    ),
  );
  $("#aboutBtn").addEventListener("click", () =>
    showView("aboutView", "aboutBtn"),
  );

  /* ---------- menu File ---------- */
  const fileBtn = $("#fileBtn"),
    fileMenu = $("#fileMenu");
  const tutupMenu = () => {
    fileMenu.classList.remove("show");
    fileBtn.classList.remove("active");
  };
  fileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    fileMenu.classList.toggle("show");
    fileBtn.classList.toggle("active");
  });
  document.addEventListener("click", tutupMenu);

  const bukaDialog = () => $("#fileInput").click();
  $("#openBtn").addEventListener("click", bukaDialog);
  $("#openArea").addEventListener("click", () => {
    if (!fileA) bukaDialog();
  });

  function simpan(tanyaNama) {
    const hasil = riwayat[riwayat.length - 1];
    if (!hasil)
      return toast("Belum ada hasil untuk disimpan. Terapkan operasi dulu.");
    let nama = "picforge-hasil.png";
    if (tanyaNama) {
      const isian = window.prompt("Simpan sebagai:", nama);
      if (!isian) return;
      nama = /\.png$/i.test(isian) ? isian : isian + ".png";
    }
    const a = document.createElement("a");
    a.href = hasil.image;
    a.download = nama;
    a.click();
  }
  $("#saveBtn").addEventListener("click", () => simpan(false));
  $("#saveAsBtn").addEventListener("click", () => simpan(true));

  /* gambar baru: simpan file, tampilkan di semua menu, kosongkan riwayat */
  function aturRasio(url) {
    const tes = new Image();
    tes.onload = () => {
      const rasio = tes.naturalWidth + " / " + tes.naturalHeight;
      $$(".canvas").forEach((c) => {
        if ($("img", c)) c.style.setProperty("--ratio", rasio);
      });
    };
    tes.src = url;
  }
  $("#fileInput").addEventListener("change", (e) => {
    const f = e.target.files[0];
    if (!f) return;
    fileA = f;
    const url = URL.createObjectURL(f);
    $("#preview").src = url;
    $("#preview").style.display = "block";
    $("#placeholder").style.display = "none";
    $$(".img-asli").forEach((img) => {
      img.src = url;
      img.style.display = "block";
      const k = $(".kosong", img.parentElement);
      if (k) k.style.display = "none";
    });
    $("#fileInfo").textContent = f.name;
    aturRasio(url);
    riwayat.length = 0;
    tampilkan();
    e.target.value = ""; /* supaya file yang sama bisa dibuka lagi */
  });

  /* ---------- parameter otomatis ---------- */
  function buatParameter(g) {
    const m = g.meta[g.nama];
    $(".op-name", g.el).textContent = g.nama;
    g.box.innerHTML = "";
    if (!m) {
      g.box.innerHTML = '<span class="tanpa">Operasi belum tersedia.</span>';
      return;
    }
    if (!m.params.length) {
      g.box.innerHTML =
        '<span class="tanpa">Operasi ini tidak memerlukan parameter.</span>';
      return;
    }
    m.params.forEach((p) => {
      const id = g.kunci + "_" + p.kunci;
      const item = document.createElement("div");
      item.className = "p-item";
      if (p.tipe === "slider") {
        /* slider + kotak angka: keduanya saling mengikuti, jadi nilai bisa digeser atau diketik */
        item.innerHTML =
          `<div class="p-baris"><label for="${id}">${p.label}</label>` +
          `<span class="p-angka-wrap"><input type="number" class="p-angka" step="any" ` +
          `min="${p.min}" max="${p.max}" value="${p.default}" aria-label="${p.label}">` +
          (p.satuan ? `<i>${p.satuan}</i>` : "") +
          `</span></div>` +
          `<input type="range" data-kunci="${p.kunci}" id="${id}" ` +
          `min="${p.min}" max="${p.max}" step="${p.langkah}" value="${p.default}">`;
        const geser = $('input[type="range"]', item);
        const angka = $(".p-angka", item);
        geser.addEventListener("input", () => (angka.value = geser.value));
        angka.addEventListener("input", () => {
          const v = parseFloat(angka.value);
          if (!isNaN(v))
            geser.value = Math.min(
              Math.max(v, p.min),
              p.max,
            ); /* slider ikut, nilai dibatasi */
        });
        angka.addEventListener(
          "change",
          () => (angka.value = geser.value),
        ); /* rapikan setelah selesai mengetik */
        angka.addEventListener("keydown", (e) => {
          if (e.key === "Enter") {
            angka.value = geser.value;
            terapkan(g);
          }
        });
      } else {
        const opsi = p.opsi
          .map(
            (o) =>
              `<option value="${o}"${o === p.default ? " selected" : ""}>${o}</option>`,
          )
          .join("");
        item.innerHTML =
          `<label for="${id}">${p.label}</label>` +
          `<select data-kunci="${p.kunci}" id="${id}">${opsi}</select>`;
      }
      g.box.appendChild(item);
    });
  }

  /* ---------- Basic Ops: mode Skalar/Citra Lain dan Gambar B ---------- */
  const opsGrup = GRUP[0];
  const modeCitraLain = () => {
    const aktif = $("#opsModeToggle .mode-btn.active");
    return (
      !$("#opsModeToggle").classList.contains("hidden") &&
      aktif &&
      aktif.dataset.mode === "image"
    );
  };
  /* "wajib" bila Gambar B harus ada, null bila tidak dipakai */
  function aturanB() {
    const m = opsGrup.meta[opsGrup.nama];
    if (!m || !m.dua_citra) return null;
    if (m.dua_citra === "wajib") return "wajib";
    return modeCitraLain() ? "wajib" : null;
  }
  function aturTampilanOps() {
    const m = opsGrup.meta[opsGrup.nama];
    const opsional = m && m.dua_citra === "opsional";
    const perluB = aturanB() === "wajib";
    $("#opsModeToggle").classList.toggle("hidden", !opsional);
    $("#opsDualImage").classList.toggle("hidden", !perluB);
    $("#opsPanels").classList.toggle("dual-mode", perluB);
    opsGrup.box.classList.toggle("hidden", !!(opsional && modeCitraLain()));
  }
  $$("#opsModeToggle .mode-btn").forEach((b) =>
    b.addEventListener("click", () => {
      $$("#opsModeToggle .mode-btn").forEach((x) =>
        x.classList.toggle("active", x === b),
      );
      aturTampilanOps();
    }),
  );
  $("#opsImgBBtn").addEventListener("click", () => $("#opsImgBInput").click());
  $("#opsImgBInput").addEventListener("change", (e) => {
    const f = e.target.files[0];
    if (!f) return;
    fileB = f;
    $("#opsImgBName").textContent = f.name;
    const img = $("#opsImgBPreview");
    img.src = URL.createObjectURL(f);
    img.style.display = "block";
    aturRasio(img.src);
  });

  /* ---------- pilih operasi di ribbon ---------- */
  GRUP.forEach((g) => {
    $$(".ribbon button", g.el).forEach((b) =>
      b.addEventListener("click", () => {
        $$(".ribbon button", g.el).forEach((x) =>
          x.classList.toggle("sel", x === b),
        );
        g.nama = b.textContent.trim();
        if (g === opsGrup)
          $("#opsModeToggle .mode-btn[data-mode=scalar]").click();
        buatParameter(g);
        if (g === opsGrup) aturTampilanOps();
      }),
    );
    $(".histo .hist-kanal, .hist-kanal", g.el).addEventListener("change", () =>
      gambarHistogram(g),
    );
    $$(".p-actions button", g.el).forEach((b) =>
      b.addEventListener("click", () => {
        if (b.dataset.aksi === "apply") terapkan(g);
        else if (b.dataset.aksi === "undo") undo();
        else reset();
      }),
    );
  });

  /* ---------- tampilan hasil, histogram, statistik ---------- */
  function gambarHistogram(g) {
    const canvas = $(".hist-canvas", g.el);
    const w = (canvas.width = canvas.clientWidth);
    const h = (canvas.height = canvas.clientHeight);
    if (!w || !h) return; /* menu sedang tersembunyi */
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, w, h);
    const hasil = riwayat[riwayat.length - 1];
    if (!hasil) return;
    const kanal = $(".hist-kanal", g.el).value;
    const data = hasil.histogram[kanal];
    const maks = Math.max(...data) || 1;
    ctx.fillStyle = WARNA[kanal];
    const lebar = w / 256;
    data.forEach((v, i) => {
      const tinggi = (v / maks) * (h - 6);
      ctx.fillRect(i * lebar, h - tinggi, Math.max(lebar, 1), tinggi);
    });
  }
  const gambarSemuaHistogram = () => GRUP.forEach(gambarHistogram);

  function tampilkan() {
    const hasil = riwayat[riwayat.length - 1];
    GRUP.forEach((g) => {
      const img = $(".img-hasil", g.el);
      img.style.display = hasil ? "block" : "none";
      if (hasil) img.src = hasil.image;
      const k = $(".kosong", img.parentElement);
      if (k) k.style.display = hasil ? "none" : "";
      const s = hasil && hasil.statistik;
      $(".stats", g.el).innerHTML = s
        ? `<dt>Min</dt><dd>${s.min}</dd><dt>Max</dt><dd>${s.max}</dd>` +
          `<dt>Rata-rata</dt><dd>${s.rata}</dd><dt>Median</dt><dd>${s.median}</dd>` +
          `<dt>Std</dt><dd>${s.std}</dd><dt>Piksel</dt><dd>${s.piksel}</dd>`
        : "";
    });
    gambarSemuaHistogram();
  }

  /* ---------- Terapkan, Undo, Reset ---------- */
  async function terapkan(g) {
    if (sedangProses) return;
    if (!fileA) return toast("Buka gambar dulu lewat File > Open.");
    if (!g.nama) return toast("Pilih operasi terlebih dahulu.");
    const perluB = g === opsGrup && aturanB() === "wajib";
    if (perluB && !fileB) return toast("Pilih Gambar B terlebih dahulu.");

    const fd = new FormData();
    fd.append("group", g.kunci);
    fd.append("op", g.nama);
    if (g === opsGrup) fd.append("mode", modeCitraLain() ? "image" : "scalar");
    $$("[data-kunci]", g.box).forEach((el) =>
      fd.append(el.dataset.kunci, el.value),
    );

    sedangProses = true;
    const tombol = $('[data-aksi="apply"]', g.el);
    tombol.disabled = true;
    tombol.textContent = "Memproses...";
    try {
      /* hasil sebelumnya jadi masukan berikutnya (Undo membatalkan) */
      const terakhir = riwayat[riwayat.length - 1];
      const sumber = terakhir
        ? await (await fetch(terakhir.image)).blob()
        : fileA;
      fd.append("image", sumber, "a.png");
      if (perluB) fd.append("imageB", fileB);

      const res = await fetch("/api/process", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Terjadi kesalahan.");
      riwayat.push(data);
      tampilkan();
      if (data.info) toast(data.info);
    } catch (err) {
      toast(err.message);
    } finally {
      sedangProses = false;
      tombol.disabled = false;
      tombol.textContent = "Terapkan";
    }
  }
  function undo() {
    if (!riwayat.length) return toast("Tidak ada yang bisa di-undo.");
    riwayat.pop();
    tampilkan();
  }
  function reset() {
    riwayat.length = 0;
    tampilkan();
  }

  window.addEventListener("resize", gambarSemuaHistogram);

  /* ---------- muat daftar operasi dari server ---------- */
  GRUP.forEach((g) => {
    g.box.innerHTML =
      '<span class="tanpa">Pilih operasi untuk menampilkan parameter.</span>';
    fetch("/api/operasi/" + g.kunci)
      .then((r) => r.json())
      .then((d) => (g.meta = d))
      .catch(() => toast("Gagal memuat daftar operasi dari server."));
  });
  showView("homeView", null);
})();
