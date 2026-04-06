# Version Management

**Kategori:** Blender Launcher
**Modul:** ZerØXe → BLauncher → Versioning

---

## Deskripsi

Fitur **Version Management** mengelola sistem versioning file Blender di dalam pipeline produksi. Setiap kali seniman ingin menyimpan progress kerja, mereka dapat membuat versi baru yang tersimpan di folder `progress/` dengan penamaan otomatis (`v001`, `v002`, dst.). Versi terbaik dapat dipromosikan ke **master file**.

Fitur utama:
- Buat versi baru dari file Blender yang sedang aktif
- Upload/promosi versi ke **master file** produksi
- Tampilkan riwayat versi lengkap dengan metadata (author, tanggal, status)
- **Lock/Unlock** file untuk mencegah edit bersamaan
- **Replace file** — ganti file di path tertentu dengan file lain
- Versi disimpan di subfolder `progress/` relatif terhadap path shot/asset

> **Catatan:** Versioning dilakukan melalui script Python yang dijalankan langsung di dalam Blender yang sedang terbuka.

---

## Prasyarat

Sebelum menggunakan fitur ini, pastikan:

- File Blender sudah disimpan di path yang benar sesuai struktur project
- Shot atau asset sudah dipilih di panel BLauncher
- Blender sedang terbuka dengan file yang ingin di-versioning

---

## Cara Penggunaan

### Langkah 1 — Pilih Shot/Asset di BLauncher

Navigasikan ke shot atau asset yang filenya ingin di-versioning. Daftar versi yang ada akan tampil di panel versi.

---

### Langkah 2 — Buat Versi Baru

Klik tombol **"Up Version"** untuk membuat versi baru. ZerØXe akan mengirimkan script ke Blender yang sedang terbuka untuk:

1. Menyimpan file saat ini
2. Menduplikasi file ke folder `progress/` dengan nomor versi baru (misal: `v003.blend`)
3. Mencatat metadata versi (author, tanggal, status) ke log `.zeroxe`

---

### Langkah 3 — Upload ke Master (Opsional)

Jika versi sudah siap untuk produksi, klik tombol **"Up Master"** untuk mempromosikan file versi aktif ke master file. Master file adalah file utama yang digunakan oleh departemen lain.

---

### Langkah 4 — Lock File (Opsional)

Klik tombol **"Lock"** untuk mengunci file agar tidak diedit oleh pengguna lain. File yang terkunci akan ditandai di metadata dengan informasi siapa yang mengunci.

Klik **"Unlock"** untuk melepas kunci.

---

## Struktur Folder Versioning

```
<shot_folder>/
├── <shot_name>.blend          # Master file
└── progress/                  # Folder versi
    ├── v001.blend
    ├── v002.blend
    ├── v003.blend
    └── .zeroxe/               # Log metadata versi
        └── version_log.json
```

---

## Perilaku & Batasan

| Aspek | Detail |
|---|---|
| Folder versi | `progress/` relatif terhadap path master file |
| Penamaan versi | Format: `v001`, `v002`, dst. (prefix `v`, 3 digit) |
| Log metadata | Disimpan di `progress/.zeroxe/version_log.json` |
| Eksekusi versioning | Script Python dikirim ke Blender yang sedang terbuka |
| Master file | File utama di root folder shot/asset |
| Lock state | Dicatat di metadata versi, bukan file-lock OS |

---

## Troubleshooting

**Tombol "Up Version" tidak berfungsi?**
Pastikan Blender sedang terbuka dan file yang aktif sudah disimpan terlebih dahulu. Script versioning dikirim ke proses Blender yang aktif.

**Nomor versi tidak urut atau ada gap?**
Versi diurutkan berdasarkan nama file di folder `progress/`. Jika ada file yang dihapus manual, gap akan terjadi — ini normal dan tidak mempengaruhi fungsionalitas.

**Error saat "Up Master"?**
Pastikan path master file valid dan pengguna memiliki permission write ke folder tersebut.

**File terkunci oleh pengguna lain?**
Koordinasikan dengan pemilik lock untuk unlock file, atau hubungi supervisor produksi.
