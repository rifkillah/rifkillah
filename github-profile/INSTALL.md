# Cara memasang profile README ini

Paket ini berisi README profil GitHub dengan sistem visual **Liquid Glass** — semua banner, header, rail teknologi, kartu proyek, badge sosial, dan footer adalah SVG animasi buatan sendiri.

---

## 1 · Yang kamu butuhkan

- Akun GitHub: **`rifkillah`**
- Repositori khusus profil: **`rifkillah/rifkillah`** (nama repo harus sama dengan username)
- Tidak perlu server, build tool, atau npm. GitHub merender SVG langsung.

Kalau repo `rifkillah/rifkillah` belum ada: buat repo **Public** dengan nama `rifkillah`, lalu centang *Add a README file*.

---

## 2 · Struktur paket

```text
github-profile/
├── README.md                 ← profil utama (timpa README lama)
├── INSTALL.md                ← file ini
├── preview.html              ← buka di browser untuk melihat semua aset
├── assets/
│   ├── hero.svg              ← banner desktop
│   ├── hero-mobile.svg       ← banner iPhone / layar sempit
│   ├── marquee.svg           ← rail kata berjalan
│   ├── sec-about.svg         ← header bagian About
│   ├── sec-journey.svg       ← header bagian Journey
│   ├── sec-stack.svg         ← header bagian Stack
│   ├── sec-work.svg          ← header bagian Work
│   ├── sec-lab.svg           ← header bagian GitHub Lab
│   ├── sec-beyond.svg        ← header bagian Beyond Code
│   ├── sec-connect.svg       ← header bagian Connect
│   ├── stack.svg             ← 30 ikon teknologi, 3 baris animasi
│   ├── featured-matfess.svg  ← studi kasus Matfess + mockup HP
│   ├── hobby-*.svg           ← 4 kartu hobi
│   ├── github-stats.svg      ← kartu statistik (dibuat sendiri, auto-refresh)
│   ├── github-stats-mobile.svg ← varian iPhone
│   ├── github-stats.json     ← cache angka terakhir
│   ├── footer.svg            ← penutup
│   ├── social/*.svg          ← 10 badge kontak
│   └── src/                  ← foto & ikon sumber (untuk rebuild)
├── .github/workflows/
│   └── profile-stats.yml     ← refresh kartu statistik tiap hari
└── tools/
    ├── build_assets.py       ← generator semua SVG
    └── build_stats.py        ← pengambil data GitHub + kartu statistik
```

> **Penting:** pertahankan huruf besar/kecil nama folder dan file. GitHub Pages/raw bersifat *case-sensitive*.

---

## 3 · Cara upload (pilih salah satu)

### A · Lewat browser (paling mudah)

1. Buka `https://github.com/rifkillah/rifkillah`.
2. Klik **Add file → Upload files**.
3. Drag semua isi folder `github-profile/` (README.md, assets/, tools/, preview.html).
4. Commit message: `feat: liquid glass profile`.
5. Buka halaman profil `https://github.com/rifkillah` — README langsung tampil.

> **Catatan:** folder `.github/` (berisi workflow) diawali titik sehingga bisa tersembunyi di Windows/macOS. Kalau tidak ikut ter-upload, buka tab **Actions** di GitHub → **New workflow** → **set up a workflow yourself**, lalu tempel isi `profile-stats.yml`. Workflow hanya mengurus pembaruan otomatis; README tetap tampil tanpanya.

Untuk mengganti README lama: upload `README.md` baru → GitHub otomatis menimpa setelah commit.

### B · Lewat Git

```bash
git clone https://github.com/rifkillah/rifkillah.git
cd rifkillah

# salin isi paket ini ke folder repo
# (README.md, assets/, tools/, preview.html, INSTALL.md)

git add .
git commit -m "feat: liquid glass profile"
git push origin main
```

---

## 4 · Checklist setelah upload

- [ ] Banner tampil di desktop **dan** versi mobile berganti otomatis (lebar ≤ 640px).
- [ ] Animasi berjalan: cincin avatar, chip mengambang, marquee, rail ikon, sheen kartu.
- [ ] Semua badge sosial mengarah ke akun yang benar.
- [ ] Kartu **GitHub Signal** tampil dan angkanya masuk akal.

Kartu statistik sudah ikut di dalam paket (`assets/github-stats.svg`), jadi tidak bergantung pada layanan pihak ketiga. Untuk memperbarui angkanya otomatis:

1. Buka tab **Actions** → **Refresh GitHub signal** → **Run workflow**.
2. Workflow memakai `GITHUB_TOKEN` bawaan repo (tidak perlu bikin token manual) dan melakukan commit otomatis setiap hari pukul 03:17 UTC.
3. Kalau ingin memperbarui secara lokal: `python tools/build_stats.py` (butuh koneksi) atau `python tools/build_stats.py --offline` (pakai cache).

Kalau ada gambar yang tidak muncul:

1. Pastikan file benar-benar ter-upload di `assets/…`.
2. Buka URL mentahnya, misal `https://raw.githubusercontent.com/rifkillah/rifkillah/main/assets/hero.svg`.
3. Tunggu 1–2 menit — cache gambar GitHub (camo) kadang perlu waktu.

---

## 5 · Kustomisasi

### Ganti foto profil di banner

```bash
# ganti file ini dengan fotomu (disarankan persegi, minimal 600×600)
assets/src/avatar.png

python tools/build_assets.py
```

Generator akan menanam foto sebagai base64 ke `hero.svg` dan `hero-mobile.svg`, jadi tidak ada request eksternal saat README dibuka.

### Ganti palet warna

Buka `tools/build_assets.py`, ubah bagian atas:

```python
BLUE   = "#6EA8FF"
MINT   = "#6EE7B7"
VIOLET = "#A78BFA"
CYAN   = "#67E8F9"
ROSE   = "#FDA4AF"
AMBER  = "#FCD34D"
```

lalu jalankan `python tools/build_assets.py` lagi.

### Ganti teks

Semua teks di banner/header ada di `tools/build_assets.py` (cari `RIFKILLAH`, `About`, `Matfess`, dst).
Teks paragraf ada di `README.md`.

### Ganti screenshot Matfess

```bash
# timpa dengan screenshot baru (rasio potret)
assets/src/matfess-card.jpg

python tools/build_assets.py
```

### Menyesuaikan tautan sosial

Edit blok **CONNECT** di `README.md`. Label dan handle di badge diatur di `tools/build_assets.py` pada list `SOCIALS`.

---

## 6 · Catatan teknis

- **Kenapa SVG?** GitHub menghapus `<style>`, `<script>`, dan atribut `style` dari Markdown. Satu-satunya cara mendapatkan glass, gradien, dan animasi adalah dengan menaruhnya di dalam file gambar (SVG), lalu memanggilnya lewat `<img>`.
- **Tema terang/gelap:** setiap kartu membawa kanvas gelapnya sendiri, jadi tampilan tetap konsisten di tema GitHub apa pun. Tidak ada gambar yang "hilang" di mode terang.
- **Aksesibilitas:** semua gambar punya `alt`, animasi dimatikan otomatis saat pengguna mengaktifkan `prefers-reduced-motion`.
- **Privasi:** tidak ada script, tracker, atau cookie. Semua gambar berasal dari repo ini sendiri — tidak ada request ke layanan pihak ketiga.
- **Kartu statistik** dibuat oleh `tools/build_stats.py` dari GitHub REST API + contribution calendar publik, lalu dirender menjadi SVG statis. Tidak ada layanan pihak ketiga yang bisa down — kalau API sedang rate-limited, workflow memakai cache terakhir.
- **Ukuran:** total aset ± 1,3 MB; setiap SVG di bawah 150 KB, aman untuk batas cache gambar GitHub.

---

## 7 · Kredit

- Bahasa visual **Liquid Glass** terinspirasi dari [zakisheriff/Liquid-Glass](https://github.com/zakisheriff/Liquid-Glass) (MIT). Di sini diimplementasikan ulang dengan SVG murni, bukan memakai paket React-nya.
- Ikon teknologi & brand: [Simple Icons](https://simpleicons.org/) (CC0 1.0).
- Kartu statistik: dibuat sendiri dengan Python + SVG, memakai [GitHub REST API](https://docs.github.com/rest) dan [github-contributions-api](https://github.com/grubersjewish/github-contributions-api) untuk kalender kontribusi.

---

Dibuat untuk **Rifkillah Muliya Al-Faris** · 2026.
