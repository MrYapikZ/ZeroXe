# Login & Authentication

**Kategori:** Authentication
**Modul:** ZerØXe → Login Dialog

---

## Deskripsi

Fitur **Login & Authentication** menangani autentikasi pengguna ke server **Kitsu** menggunakan email dan password. Setelah login berhasil, sesi pengguna disimpan secara terenkripsi di komputer lokal sehingga pengguna tidak perlu login ulang setiap kali aplikasi dibuka.

Fitur utama:
- Login via email & password ke Kitsu API
- Session disimpan terenkripsi menggunakan **Fernet encryption**
- **Auto-login** jika session sebelumnya masih valid
- Tampilan avatar pengguna setelah login
- Logout dengan penghapusan session lokal

> **Catatan:** Konfigurasi `FERNET_KEY` di file `.env` wajib diisi sebelum dapat menggunakan aplikasi.

---

## Prasyarat

Sebelum menggunakan fitur ini, pastikan:

- File `.env` sudah dikonfigurasi dengan `FERNET_KEY` yang valid (untuk saat ini `FERNET_KEY` hardcoded di config.py)
- Server Kitsu dapat diakses melalui jaringan
- Akun pengguna sudah terdaftar di Kitsu

---

## Cara Penggunaan

### Langkah 1 — Buka Aplikasi

Jalankan ZerØXe. Jika belum ada session tersimpan, dialog **Login** akan muncul secara otomatis.

---

### Langkah 2 — Masukkan Kredensial

Isi field **Email** dan **Password** dengan akun Kitsu yang valid, lalu klik tombol **"Login"**.

---

### Langkah 3 — Login Berhasil

Setelah login berhasil, aplikasi akan menutup dialog login dan menampilkan **main window** dengan avatar dan nama pengguna di header.

Session pengguna akan tersimpan secara otomatis. Pada pembukaan berikutnya, aplikasi akan langsung masuk tanpa perlu login ulang.

---

### Logout

Untuk keluar dari session aktif, klik tombol **Logout** di header aplikasi. Session lokal akan dihapus dan dialog login akan muncul kembali.

---

## Perilaku & Batasan

| Aspek | Detail |
|---|---|
| Protokol autentikasi | Kitsu API (Gazu client) |
| Penyimpanan session | File terenkripsi Fernet di direktori config OS |
| Auto-login | Aktif jika session file valid dan belum expired |
| Avatar | Diunduh dari server Kitsu dan di-cache secara lokal |
| Fallback URL | Jika primary API URL gagal, mencoba `KITSU_ALT_API_URL` |

---

## Troubleshooting

**Dialog login tidak muncul dan aplikasi langsung crash?**
Pastikan `FERNET_KEY` sudah diisi di file `.env`. Tanpa key ini, aplikasi tidak dapat menginisialisasi enkripsi session.

**Error "Connection refused" atau tidak bisa login?**
Periksa koneksi jaringan ke server Kitsu. Pastikan URL di `config.py` (`KITSU_API_URL`) sudah benar dan server aktif.

**Auto-login tidak berfungsi?**
Session mungkin sudah expired atau file session rusak. Hapus file session di direktori config (`user_data.dat`) dan login ulang.

**Avatar tidak tampil?**
Pastikan koneksi ke server Kitsu aktif. Avatar diunduh dari server saat pertama kali login.
