#!/usr/bin/env python3
"""
================================================================================
Aplikasi Web Monolitik Stateful - Single-Path Routing Backend
Sesuai Spesifikasi: Python Native dengan driver MySQL Connector
Fitur:
  - Single-Path Routing via query parameter (?aksi=...)
  - Server-Side Local Session (In-Memory Session Store + Cookie HTTP)
  - Database MySQL dengan relasi Foreign Key (ON DELETE CASCADE)
  - Static File Server (HTML, CSS, JS)
================================================================================
"""

import http.server
import socketserver
import urllib.parse
from http import cookies
import json
import mysql.connector
from mysql.connector import IntegrityError
import hashlib
import uuid
import os
import mimetypes
import threading
import webbrowser
from datetime import datetime

# ================= Konfigurasi Global =================
PORT = 8080
HOST = "0.0.0.0"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "db_puisi")

# In-Memory Server-Side Session Store
# Format: { "session_id_uuid": { "user_id": 1, "username": "admin", "nama": "Admin", "login_at": "..." } }
SESSIONS = {}


# ================= Helper Database =================
def get_db_connection():
    """Membuka koneksi ke database MySQL aplikasi."""
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def init_database():
    """Inisialisasi database, tabel, dan data awal MySQL."""
    print("[DATABASE] Memeriksa inisialisasi basis data MySQL...")
    server_conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    server_cursor = server_conn.cursor()
    server_cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    server_conn.commit()
    server_cursor.close()
    server_conn.close()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Buat tabel jika belum ada
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        nama VARCHAR(100) NOT NULL,
        no_id VARCHAR(50) NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS puisi (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        judul VARCHAR(150) NOT NULL,
        tgl_submit DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        isi TEXT NOT NULL,
        kategori VARCHAR(50) NOT NULL,
        keyword VARCHAR(100) NOT NULL,
        CONSTRAINT fk_puisi_users FOREIGN KEY (user_id) 
            REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
    );
    """)

    # Masukkan data dummy jika tabel users masih kosong
    cursor.execute("SELECT COUNT(*) as count FROM users;")
    if cursor.fetchone()["count"] == 0:
        default_pwd = hashlib.sha256("password123".encode("utf-8")).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password, nama, no_id) VALUES (%s, %s, %s, %s)",
            ("chairil_anwar", default_pwd, "Chairil Anwar", "ID-001")
        )
        cursor.execute(
            "INSERT INTO users (username, password, nama, no_id) VALUES (%s, %s, %s, %s)",
            ("sapardi_djoko", default_pwd, "Sapardi Djoko Damono", "ID-002")
        )
        cursor.execute(
            "INSERT INTO puisi (user_id, judul, isi, kategori, keyword) VALUES (%s, %s, %s, %s, %s)",
            (1, "Aku", "Kalau sampai waktuku\nKu mau tak seorang kan merayu\nTidak juga kau\n\nTak perlu sedu sedan itu\n\nAku ini binatang jalang\nDari kumpulannya terbuang...", "Puisi Bebas", "perjuangan, semangat, eksistensial")
        )
        cursor.execute(
            "INSERT INTO puisi (user_id, judul, isi, kategori, keyword) VALUES (%s, %s, %s, %s, %s)",
            (2, "Hujan Bulan Juni", "Tak ada yang lebih tabah\ndari hujan bulan juni\ndirahasiakannya rintik rindunya\nkepada pohon berbunga itu...", "Romansa & Alam", "rindu, ketabahan, hujan")
        )
        print("[DATABASE] Data awal dummy berhasil diisikan.")

    conn.commit()
    conn.close()
    print("[DATABASE] Inisialisasi basis data selesai.")


def hash_password(password: str) -> str:
    """Mengamankan password menggunakan hashing SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ================= Request Handler =================
class StatefulAppHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        """Kustomisasi format log request di terminal."""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {self.address_string()} - {format % args}")

    # --------- Helper Sesi Server-Side & Cookie ---------
    def get_session(self):
        """Membaca cookie session_id dari request dan mencocokkan ke Server-Side SESSIONS."""
        cookie_header = self.headers.get("Cookie")
        if not cookie_header:
            return None, None
        
        cookie = cookies.SimpleCookie()
        try:
            cookie.load(cookie_header)
        except Exception:
            return None, None

        if "session_id" in cookie:
            sid = cookie["session_id"].value
            if sid in SESSIONS:
                return sid, SESSIONS[sid]
        return None, None

    def send_json_response(self, data, status_code=200, set_cookie_sid=None, clear_cookie=False):
        """Mengirim response JSON beserta header Session Cookie jika ada."""
        json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(json_bytes)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        
        # Pengaturan Cookie Sesi
        if set_cookie_sid:
            # HttpOnly untuk keamanan, Path=/ agar berlaku di seluruh halaman
            self.send_header("Set-Cookie", f"session_id={set_cookie_sid}; Path=/; HttpOnly; SameSite=Lax")
        elif clear_cookie:
            self.send_header("Set-Cookie", "session_id=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; HttpOnly")
            
        self.end_headers()
        self.wfile.write(json_bytes)

    def read_request_body(self):
        """Membaca dan mem-parsing body request (JSON atau Form URL Encoded)."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        
        body_raw = self.rfile.read(content_length).decode("utf-8")
        content_type = self.headers.get("Content-Type", "")

        if "application/json" in content_type:
            try:
                return json.loads(body_raw)
            except json.JSONDecodeError:
                return {}
        else:
            # Parse form urlencoded
            parsed = urllib.parse.parse_qs(body_raw)
            return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}

    # --------- Static File Serving ---------
    def serve_static_file(self, filepath):
        """Melayani file statis HTML, CSS, JS dari direktori proyek."""
        # Hilangkan query string dan normalize path
        clean_path = filepath.split("?")[0].lstrip("/")
        if clean_path == "" or clean_path == "index.html":
            clean_path = "index.html"

        full_path = os.path.join(BASE_DIR, clean_path)

        # Keamanan: cegah directory traversal
        if not os.path.abspath(full_path).startswith(BASE_DIR):
            self.send_error(403, "Akses Ditolak")
            return

        if not os.path.isfile(full_path):
            self.send_error(404, "File Tidak Ditemukan")
            return

        mime_type, _ = mimetypes.guess_type(full_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(full_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Gagal membaca file: {str(e)}")

    # --------- Router Utama (Single-Path Routing) ---------
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        aksi = query_params.get("aksi", [None])[0]

        # 1. Routing API berdasarkan ?aksi=...
        if aksi or parsed_url.path.endswith("app.py") or parsed_url.path.endswith("server.php"):
            self.handle_api_get(aksi)
            return

        # 2. Routing File Statis (index.html, style.css, script.js)
        self.serve_static_file(parsed_url.path)

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        aksi = query_params.get("aksi", [None])[0]

        self.handle_api_post(aksi)

    # --------- Handler Aksi GET ---------
    def handle_api_get(self, aksi):
        sid, session_data = self.get_session()

        # Aksi 1: Cek Status Sesi Aktif
        if aksi == "check_session":
            if session_data:
                self.send_json_response({
                    "status": "success",
                    "authenticated": True,
                    "user": {
                        "id": session_data["user_id"],
                        "username": session_data["username"],
                        "nama": session_data["nama"]
                    }
                })
            else:
                self.send_json_response({
                    "status": "error",
                    "authenticated": False,
                    "message": "Sesi tidak ditemukan atau telah kedaluwarsa"
                })
            return

        # Aksi 2: Ambil Daftar Puisi
        elif aksi == "daftar_puisi":
            if not session_data:
                self.send_json_response({
                    "status": "error",
                    "message": "Akses ditolak: Anda harus login terlebih dahulu"
                }, status_code=401)
                return

            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT p.id, p.user_id, p.judul, p.tgl_submit, p.isi, p.kategori, p.keyword, u.nama AS penulis
                    FROM puisi p
                    JOIN users u ON p.user_id = u.id
                    ORDER BY p.id DESC;
                """)
                rows = cursor.fetchall()
                puisi_list = []
                for row in rows:
                    puisi = dict(row)
                    if isinstance(puisi.get("tgl_submit"), datetime):
                        puisi["tgl_submit"] = puisi["tgl_submit"].strftime("%Y-%m-%d %H:%M:%S")
                    puisi_list.append(puisi)
                conn.close()

                self.send_json_response({
                    "status": "success",
                    "data": puisi_list
                })
            except Exception as e:
                self.send_json_response({"status": "error", "message": f"Database error: {str(e)}"}, status_code=500)
            return

        # Aksi 3: Logout via GET
        elif aksi == "logout":
            if sid and sid in SESSIONS:
                del SESSIONS[sid]
            self.send_json_response({"status": "success", "message": "Logout berhasil"}, clear_cookie=True)
            return

        else:
            self.send_json_response({
                "status": "error",
                "message": f"Aksi GET '{aksi}' tidak dikenali"
            }, status_code=400)

    # --------- Handler Aksi POST ---------
    def handle_api_post(self, aksi):
        body = self.read_request_body()
        sid, session_data = self.get_session()

        # Aksi 1: Registrasi User Baru
        if aksi == "register":
            username = str(body.get("username", "")).strip()
            password = str(body.get("password", "")).strip()
            nama = str(body.get("nama", "")).strip()
            no_id = str(body.get("no_id", "")).strip()

            if not username or not password or not nama or not no_id:
                self.send_json_response({
                    "status": "error",
                    "message": "Semua field (username, password, nama, no_id) wajib diisi!"
                }, status_code=400)
                return

            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                pwd_hashed = hash_password(password)

                cursor.execute(
                    "INSERT INTO users (username, password, nama, no_id) VALUES (%s, %s, %s, %s)",
                    (username, pwd_hashed, nama, no_id)
                )
                conn.commit()
                conn.close()

                self.send_json_response({
                    "status": "success",
                    "message": "Registrasi berhasil! Silakan masuk dengan akun Anda."
                }, status_code=201)
            except IntegrityError:
                self.send_json_response({
                    "status": "error",
                    "message": f"Username '{username}' sudah terdaftar. Gunakan username lain."
                }, status_code=409)
            except Exception as e:
                self.send_json_response({"status": "error", "message": f"Server error: {str(e)}"}, status_code=500)
            return

        # Aksi 2: Login User & Inisialisasi Sesi Server-Side
        elif aksi == "login":
            username = str(body.get("username", "")).strip()
            password = str(body.get("password", "")).strip()

            if not username or not password:
                self.send_json_response({
                    "status": "error",
                    "message": "Username dan password wajib diisi!"
                }, status_code=400)
                return

            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                pwd_hashed = hash_password(password)

                cursor.execute(
                    "SELECT id, username, nama, no_id FROM users WHERE username = %s AND password = %s",
                    (username, pwd_hashed)
                )
                user = cursor.fetchone()
                conn.close()

                if user:
                    # Buat UUID untuk Session ID
                    new_session_id = str(uuid.uuid4())
                    # Simpan data user ke RAM server
                    SESSIONS[new_session_id] = {
                        "user_id": user["id"],
                        "username": user["username"],
                        "nama": user["nama"],
                        "no_id": user["no_id"],
                        "login_at": datetime.now().isoformat()
                    }

                    print(f"[SESSION] Sesi aktif baru dibuat untuk user: {user['username']} (SID: {new_session_id})")

                    self.send_json_response({
                        "status": "success",
                        "message": f"Selamat datang kembali, {user['nama']}!",
                        "user": {
                            "id": user["id"],
                            "username": user["username"],
                            "nama": user["nama"]
                        }
                    }, set_cookie_sid=new_session_id)
                else:
                    self.send_json_response({
                        "status": "error",
                        "message": "Kombinasi username atau password salah!"
                    }, status_code=401)
            except Exception as e:
                self.send_json_response({"status": "error", "message": f"Server error: {str(e)}"}, status_code=500)
            return

        # Aksi 3: Submit Puisi Baru (Terproteksi Sesi)
        elif aksi == "submit_puisi":
            if not session_data:
                self.send_json_response({
                    "status": "error",
                    "message": "Akses ditolak: Silakan login terlebih dahulu untuk mengirim puisi."
                }, status_code=401)
                return

            judul = str(body.get("judul", "")).strip()
            isi = str(body.get("isi", "")).strip()
            kategori = str(body.get("kategori", "")).strip()
            keyword = str(body.get("keyword", "")).strip()
            tgl_submit = str(body.get("tgl_submit", "")).strip()

            if not judul or not isi or not kategori or not keyword or not tgl_submit:
                self.send_json_response({
                    "status": "error",
                    "message": "Semua kolom puisi (judul, isi, tgl submit, kategori, keyword) wajib diisi!"
                }, status_code=400)
                return

            try:
                tgl_submit = datetime.fromisoformat(tgl_submit).strftime("%Y-%m-%d %H:%M:%S")
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "INSERT INTO puisi (user_id, judul, tgl_submit, isi, kategori, keyword) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (session_data["user_id"], judul, tgl_submit, isi, kategori, keyword)
                )
                conn.commit()
                new_id = cursor.lastrowid
                conn.close()

                print(f"[PUISI] Puisi baru ID={new_id} berhasil dibuat oleh user_id={session_data['user_id']}")

                self.send_json_response({
                    "status": "success",
                    "message": "Karya puisi berhasil disimpan!",
                    "id": new_id
                }, status_code=201)
            except ValueError:
                self.send_json_response({
                    "status": "error",
                    "message": "Format tanggal submit tidak valid."
                }, status_code=400)
            except Exception as e:
                self.send_json_response({"status": "error", "message": f"Database error: {str(e)}"}, status_code=500)
            return

        # Aksi 4: Logout (POST)
        elif aksi == "logout":
            if sid and sid in SESSIONS:
                print(f"[SESSION] Menghapus sesi {sid} untuk user: {SESSIONS[sid].get('username')}")
                del SESSIONS[sid]
            self.send_json_response({"status": "success", "message": "Logout berhasil"}, clear_cookie=True)
            return

        else:
            self.send_json_response({
                "status": "error",
                "message": f"Aksi POST '{aksi}' tidak dikenali"
            }, status_code=400)


# ================= Server Runner =================
if __name__ == "__main__":
    init_database()
    
    # Memastikan socket reuse address agar tidak error 'Address already in use' saat restart cepat
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer((HOST, PORT), StatefulAppHandler) as httpd:
        print("=" * 65)
        print("[SERVER] SERVER MONOLITIK STATEFUL BERJALAN")
        print(f"[SERVER] Akses Lokal : http://localhost:{PORT}")
        print(f"[SERVER] Single-Path : http://localhost:{PORT}/app.py?aksi=...")
        print(f"[SERVER] Database    : MySQL {DB_NAME}@{DB_HOST}:{DB_PORT}")
        print("[SERVER] Tekan CTRL + C untuk menghentikan server")
        print("=" * 65)
        # Membuka aplikasi di browser setelah server aktif
        threading.Timer(
            1.0,
            lambda: webbrowser.open(f"http://localhost:{PORT}", new=2)
        ).start()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[SERVER] Server dihentikan oleh pengguna.")
            httpd.server_close()
