# 📖 Portal Puisi - Stateful Monolithic Web Application

Aplikasi web monolitik *stateful* berbasis Python Native & Pure Vanilla Web (HTML, CSS, JS) dengan *Single-Path Routing* dan *Server-Side Local Session Management*.

---

## 🏛️ Arsitektur Sistem

1. **Monolithic Stateful Architecture:**
   - Sesi pengguna disimpan pada memori (*RAM*) lokal server melalui *Session ID* acak (`UUID`).
   - Browser bertukar *Session ID* secara otomatis via header HTTP `Set-Cookie` (`session_id=...; HttpOnly; SameSite=Lax`).
   - **Tantangan Skalabilitas:** Arsitektur ini mendemonstrasikan batasan *horizontal scaling* tanpa *centralized session store* (seperti Redis) atau *sticky sessions*.
2. **Single-Path Routing:**
   - Seluruh *endpoint* API backend diarahkan ke satu file utama melalui query parameter:
     - `app.py?aksi=register` (POST)
     - `app.py?aksi=login` (POST)
     - `app.py?aksi=logout` (POST/GET)
     - `app.py?aksi=check_session` (GET)
     - `app.py?aksi=submit_puisi` (POST)
     - `app.py?aksi=daftar_puisi` (GET)
3. **Relational Database with Foreign Key:**
   - Tabel `puisi` berelasi dengan tabel `users` dengan aturan `ON DELETE CASCADE` dan `ON UPDATE CASCADE`.

---

## 📁 Struktur Direktori

```text
Scalable/
├── database/
│   └── schema_mysql.sql      # Skrip DDL & Seed untuk MySQL
├── index.html                # Antarmuka web (Pure HTML5)
├── style.css                 # Gaya antarmuka (Pure CSS3 Native)
├── script.js                 # Logika Fetch API & Session Handling (Vanilla JS)
├── app.py                    # Backend Server Stateful Monolitik
├── requirements.txt          # Dependensi Python MySQL
├── .gitignore                # Filter file temporary Git
└── README.md                 # Dokumentasi proyek & deployment
```

---

## 🚀 Panduan Menjalankan di Komputer Lokal

### 1. Prasyarat
- Python 3.8+
- MySQL Server 8.0+
- Driver Python MySQL Connector

Install dependensi Python:
```powershell
pip install -r requirements.txt
```

Sebelum menjalankan aplikasi, pastikan MySQL aktif. Secara default aplikasi
menggunakan host `localhost`, port `3306`, user `root`, password kosong, dan
database `db_puisi`. Konfigurasi dapat diubah melalui environment variable:

```powershell
$env:MYSQL_HOST = "localhost"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = "password_mysql"
$env:MYSQL_DATABASE = "db_puisi"
```

Aplikasi akan membuat database, tabel, dan data demo secara otomatis saat
pertama kali dijalankan. Skrip SQL manual tersedia di
`database/schema_mysql.sql`.

### 2. Jalankan Server
Buka terminal di dalam folder proyek, lalu jalankan:
```bash
python app.py
```

### 3. Akses Aplikasi
Buka peramban web (*browser*) dan kunjungi:
```text
http://localhost:8080
```

### 4. Akun Demo Awal
- **Username:** `chairil_anwar`
- **Password:** `password123`

---

## ☁️ Panduan Deployment ke AWS EC2

### 1. Buat Instance AWS EC2
- **AMI:** Ubuntu Server 22.04 LTS atau Amazon Linux 2023.
- **Instance Type:** `t2.micro` (Free Tier eligible).
- **Key Pair:** Unduh berkas `.pem` untuk akses SSH.

### 2. Konfigurasi Security Group
Tambahkan *Inbound Rules*:
| Type | Protocol | Port Range | Source |
| :--- | :--- | :--- | :--- |
| SSH | TCP | 22 | My IP / 0.0.0.0/0 |
| Custom TCP | TCP | 8080 | 0.0.0.0/0 |

### 3. Clone & Jalankan di Server EC2
Masuk ke instance EC2 via terminal SSH:
```bash
ssh -i "your-key.pem" ubuntu@<PUBLIC_IP_EC2>
```

Clone repositori GitHub dan jalankan aplikasi di latar belakang:
```bash
git clone https://github.com/USERNAME/Scalable.git
cd Scalable
pip3 install -r requirements.txt
python3 app.py
```
*(Atau gunakan `nohup python3 app.py > server.log 2>&1 &` atau `systemd` agar tetap berjalan saat terminal ditutup).*

Akses aplikasi di browser melalui:
```text
http://<PUBLIC_IP_EC2>:8080
```

### 4. Verifikasi Sesi dan Pengujian

1. Buka `http://<PUBLIC_IP_EC2>:8080` dari browser.
2. Daftar atau gunakan akun demo, lalu login.
3. Di DevTools browser buka tab **Network** dan pilih request `login`.
4. Pastikan response memiliki `Set-Cookie: session_id=...`.
5. Pilih request `daftar_puisi` atau `submit_puisi` dan pastikan request
   mengirim cookie `session_id`.
6. Uji seluruh aksi `register`, `login`, `submit_puisi`, dan `daftar_puisi`.

Simpan screenshot pengujian Network, halaman aplikasi melalui IP publik,
konfigurasi Security Group, dan status instance sebagai bukti laporan.

### 5. Deliverables

- Laporan singkat dalam format PDF.
- Tautan repositori GitHub di dalam laporan.
- IP publik EC2 yang aktif untuk demonstrasi.
