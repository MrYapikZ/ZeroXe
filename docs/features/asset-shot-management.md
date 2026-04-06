# Asset & Shot Management

**Kategori:** Asset & Shot Management
**Modul:** ZerØXe → BLauncher → Asset/Shot Browser

---

## Deskripsi

Fitur **Asset & Shot Management** menyediakan interface untuk menelusuri seluruh asset dan shot yang terdaftar di **Kitsu** berdasarkan hierarki project. Pengguna dapat memfilter berdasarkan department, project, episode, dan tipe entity untuk menemukan file yang dibutuhkan dengan cepat.

Struktur navigasi:
- **Shot:** Department → Project → Episodes → Sequences → Shots
- **Asset:** Department → Project → Asset Types → Assets

Setiap item menampilkan metadata dari Kitsu seperti nama, tipe, dan status task.

> **Catatan:** Data seluruhnya diambil dari server Kitsu secara real-time. Pastikan koneksi ke server Kitsu aktif.

---

## Prasyarat

Sebelum menggunakan fitur ini, pastikan:

- Sudah login ke Kitsu via ZerØXe
- Project, shot, dan asset sudah terdaftar di Kitsu
- Koneksi jaringan ke server Kitsu aktif

---

## Cara Penggunaan

### Langkah 1 — Pilih Department

Pada dropdown **Department**, pilih department yang ingin ditelusuri. Daftar department diambil langsung dari Kitsu.

---

### Langkah 2 — Pilih Project

Setelah department dipilih, dropdown **Project** akan terisi. Pilih project yang relevan.

---

### Langkah 3 — Pilih Tipe Entity

Pilih antara **Shot** atau **Asset** untuk menentukan jenis entity yang akan ditelusuri.

---

### Langkah 4A — Navigasi Shot

Jika memilih **Shot**:

1. Pilih **Episode** dari dropdown episode
2. Pilih **Sequence** dari dropdown sequence
3. Pilih **Shot** yang diinginkan dari daftar shot

---

### Langkah 4B — Navigasi Asset

Jika memilih **Asset**:

1. Pilih **Asset Type** (misal: `Character`, `Prop`, `Environment`)
2. Pilih **Asset** dari daftar asset yang tersedia

---

### Langkah 5 — Lihat Detail & Versi

Setelah shot atau asset dipilih, panel kanan akan menampilkan:
- Daftar versi file yang tersedia
- Metadata file: nama, status, tipe, lock state, tanggal, dan author

---

## Perilaku & Batasan

| Aspek | Detail |
|---|---|
| Sumber data | Kitsu API (Gazu client) — real-time |
| Hierarki shot | Department → Project → Episode → Sequence → Shot |
| Hierarki asset | Department → Project → Asset Type → Asset |
| Filter department | Berdasarkan department yang terdaftar di Kitsu |
| Data yang ditampilkan | Nama, tipe, status task dari Kitsu |
| Caching | Tidak ada — data selalu fresh dari server |

---

## Troubleshooting

**Dropdown Episode/Sequence kosong?**
Project mungkin tidak memiliki episode atau sequence yang terdaftar. Periksa struktur project di Kitsu.

**Asset Type tidak sesuai ekspektasi?**
Asset type dikelola di Kitsu. Koordinasikan dengan project manager untuk memastikan tipe asset sudah dikonfigurasi dengan benar.

**Data lama / tidak update?**
Data diambil saat dropdown diubah. Ubah pilihan di dropdown mana saja lalu kembali ke pilihan sebelumnya untuk memuat ulang data.

**Koneksi ke Kitsu lambat?**
Periksa kondisi jaringan dan server Kitsu. ZerØXe juga memiliki fallback URL alternatif yang dikonfigurasi di `config.py` (`KITSU_ALT_API_URL`).
