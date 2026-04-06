# Blender Launcher

**Kategori:** Blender Launcher
**Modul:** ZerØXe → BLauncher

---

## Deskripsi

Fitur **Blender Launcher** memungkinkan pengguna untuk membuka file Blender (`.blend`) langsung dari ZerØXe dengan navigasi berbasis project management Kitsu. Pengguna cukup memilih Department → Project → Entity → Shot/Asset, lalu launcher akan membuka file Blender yang sesuai.

Fitur utama:
- Navigasi bertingkat: **Department → Project → Entity Type → Episode → Shot/Asset**
- Membuka file Blender langsung dari path yang dikonfigurasi di Kitsu
- Menampilkan daftar versi yang tersedia untuk shot atau asset terpilih
- Menampilkan metadata file: nama, status, tipe, lock state, tanggal, dan author

> **Catatan:** File Blender harus tersedia di path yang sesuai dengan struktur folder project.

---

## Prasyarat

Sebelum menggunakan fitur ini, pastikan:

- Sudah login ke Kitsu via ZerØXe
- File Blender tersedia di path yang sesuai
- Blender executable sudah dikonfigurasi atau tersedia di sistem

---

## Cara Penggunaan

### Langkah 1 — Buka Tab BLauncher

Setelah login, pilih tab **BLauncher** di main window ZerØXe.

---

### Langkah 2 — Pilih Department

Pada dropdown **Department**, pilih department yang sesuai (misal: `Animation`, `Lighting`, `Asset`).

---

### Langkah 3 — Pilih Project

Setelah department dipilih, dropdown **Project** akan terisi dengan daftar project yang tersedia. Pilih project yang diinginkan.

---

### Langkah 4 — Pilih Entity Type

Pilih tipe entity yang akan dibuka: **Asset** atau **Shot**.

---

### Langkah 5 — Navigasi ke Shot/Asset

- Untuk **Shot**: pilih **Episode** → **Sequence** → **Shot**
- Untuk **Asset**: pilih **Asset Type** → **Asset**

---

### Langkah 6 — Buka File Blender

Setelah shot atau asset terpilih, daftar versi akan muncul di panel versi. Pilih versi yang ingin dibuka, lalu klik tombol **"Open in Blender"**.

---

## Perilaku & Batasan

| Aspek | Detail |
|---|---|
| Sumber data | Kitsu API (Gazu client) |
| Format file | Blender `.blend` |
| Navigasi shot | Department → Project → Entity → Episode → Sequence → Shot |
| Navigasi asset | Department → Project → Entity → Asset Type → Asset |
| Metadata | Nama file, status, tipe, lock state, tanggal modifikasi, author |

---

## Troubleshooting

**Dropdown Project kosong setelah pilih Department?**
Department yang dipilih mungkin tidak memiliki project terdaftar di Kitsu. Coba pilih department lain atau periksa konfigurasi project di Kitsu.

**File Blender tidak terbuka setelah klik "Open"?**
Pastikan path file Blender valid dan dapat diakses dari komputer ini. Periksa juga apakah Blender executable sudah terpasang.

**Daftar versi kosong?**
Folder `progress/` mungkin belum ada atau kosong untuk shot/asset tersebut. Buat versi pertama terlebih dahulu menggunakan fitur [Version Management](./version-management.md).

**Shot/Asset tidak muncul di list?**
Data diambil dari Kitsu. Pastikan shot atau asset sudah terdaftar dan aktif di project management Kitsu.
