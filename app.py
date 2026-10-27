from __future__ import annotations

import base64
import os
import re
import secrets
from datetime import datetime, timedelta
from pathlib import Path

import mysql.connector
from flask import Flask, jsonify, make_response, request, send_from_directory
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash


# ============================================================
# PORTAL PUISI - MONOLITHIC BACKEND
# Flask + MySQL + Stateless Signed Cookie
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=None)

APP_SECRET = os.getenv("APP_SECRET", "ubah-secret-key-portal-puisi")
TOKEN_MAX_AGE = int(os.getenv("TOKEN_MAX_AGE", str(60 * 60 * 24)))

DB_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "portal_puisi")

serializer = URLSafeTimedSerializer(APP_SECRET, salt="portal-puisi-auth")


def db_server_connection():
    """Koneksi ke MySQL server tanpa memilih database terlebih dahulu."""
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def db_connection():
    """Koneksi ke database aplikasi."""
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def init_database():
    """Membuat database dan tabel jika belum ada."""
    conn = db_server_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cursor.close()
    conn.close()

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            nama VARCHAR(150) NOT NULL,
            no_id VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS puisi (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            judul VARCHAR(255) NOT NULL,
            kategori VARCHAR(100) NOT NULL,
            keyword VARCHAR(255) NOT NULL,
            isi TEXT NOT NULL,
            kutipan TEXT NOT NULL,
            template VARCHAR(50) NOT NULL,
            tgl_submit DATETIME NOT NULL,
            image_filename VARCHAR(255) NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_puisi_user
                FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    # Akun demo agar halaman yang sudah menyediakan hint demo langsung dapat dipakai.
    cursor.execute(
        "SELECT id FROM users WHERE username = %s LIMIT 1",
        ("chairil_anwar",),
    )
    if cursor.fetchone() is None:
        cursor.execute(
            """
            INSERT INTO users (username, nama, no_id, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (
                "chairil_anwar",
                "Chairil Anwar",
                "DEMO-001",
                generate_password_hash("password123"),
            ),
        )

    conn.commit()
    cursor.close()
    conn.close()


def json_error(message: str, status: int = 400):
    return jsonify({"status": "error", "message": message}), status


def get_json_body() -> dict:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def create_auth_token(user: dict) -> str:
    # Token berisi identitas minimal user dan ditandatangani.
    # Server tidak perlu menyimpan session state.
    payload = {
        "user_id": user["id"],
        "username": user["username"],
        "nama": user["nama"],
        "exp": int((datetime.utcnow() + timedelta(seconds=TOKEN_MAX_AGE)).timestamp()),
    }
    return serializer.dumps(payload)


def get_current_user():
    token = request.cookies.get("auth_token")
    if not token:
        return None

    try:
        payload = serializer.loads(token, max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    conn = db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, username, nama, no_id FROM users WHERE id = %s LIMIT 1",
        (user_id,),
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def set_auth_cookie(response, user: dict):
    response.set_cookie(
        "auth_token",
        create_auth_token(user),
        httponly=True,
        secure=False,  # Ubah menjadi True saat memakai HTTPS.
        samesite="Lax",
        max_age=TOKEN_MAX_AGE,
        path="/",
    )
    return response


def validate_required(data: dict, fields: list[str]):
    missing = [field for field in fields if not str(data.get(field, "")).strip()]
    return missing


def safe_filename(filename: str) -> str:
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    return filename[:180] or "puisi.png"


def save_canvas_image(image_data: str | None) -> str | None:
    """Menyimpan data URL PNG dari canvas sebagai file lokal dan mengembalikan nama file."""
    if not image_data:
        return None

    if not isinstance(image_data, str) or not image_data.startswith("data:image/png;base64,"):
        raise ValueError("Format gambar harus berupa PNG data URL.")

    encoded = image_data.split(",", 1)[1]
    raw = base64.b64decode(encoded, validate=True)

    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("Ukuran gambar terlalu besar. Maksimum 5 MB.")

    filename = safe_filename(f"puisi_{secrets.token_hex(12)}.png")
    (UPLOAD_DIR / filename).write_bytes(raw)
    return filename


# ============================================================
# FRONTEND
# ============================================================

@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/script.js")
def script_js():
    return send_from_directory(BASE_DIR, "script.js")


@app.get("/style.css")
def style_css():
    return send_from_directory(BASE_DIR, "style.css")


@app.get("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ============================================================
# SINGLE-PATH API
# Tetap mempertahankan pola app.py?aksi=...
# ============================================================

@app.route("/app.py", methods=["GET", "POST"])
def api():
    aksi = request.args.get("aksi", "").strip().lower()

    if aksi == "check_session" and request.method == "GET":
        user = get_current_user()
        if not user:
            return jsonify({"authenticated": False})

        return jsonify({"authenticated": True, "user": user})

    if aksi == "register" and request.method == "POST":
        data = get_json_body()
        missing = validate_required(data, ["username", "nama", "no_id", "password"])
        if missing:
            return json_error("Semua data registrasi wajib diisi.")

        username = str(data["username"]).strip()
        nama = str(data["nama"]).strip()
        no_id = str(data["no_id"]).strip()
        password = str(data["password"])

        if len(username) < 3:
            return json_error("Username minimal 3 karakter.")
        if len(password) < 6:
            return json_error("Password minimal 6 karakter.")

        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE username = %s OR no_id = %s LIMIT 1",
            (username, no_id),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.close()
            conn.close()
            return json_error("Username atau nomor identitas sudah terdaftar.", 409)

        cursor.execute(
            """
            INSERT INTO users (username, nama, no_id, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (username, nama, no_id, generate_password_hash(password)),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Registrasi berhasil. Silakan login.",
        }), 201

    if aksi == "login" and request.method == "POST":
        data = get_json_body()
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", ""))

        if not username or not password:
            return json_error("Username dan password wajib diisi.")

        conn = db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, username, nama, no_id, password_hash
            FROM users
            WHERE username = %s
            LIMIT 1
            """,
            (username,),
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or not check_password_hash(user["password_hash"], password):
            return json_error("Username atau password salah.", 401)

        public_user = {
            "id": user["id"],
            "username": user["username"],
            "nama": user["nama"],
            "no_id": user["no_id"],
        }

        response = make_response(jsonify({
            "status": "success",
            "message": "Login berhasil.",
            "user": public_user,
        }))
        return set_auth_cookie(response, public_user)

    if aksi == "logout" and request.method == "POST":
        response = make_response(jsonify({
            "status": "success",
            "message": "Logout berhasil.",
        }))
        response.delete_cookie("auth_token", path="/")
        return response

    if aksi == "submit_puisi" and request.method == "POST":
        user = get_current_user()
        if not user:
            return json_error("Sesi tidak valid. Silakan login kembali.", 401)

        data = get_json_body()
        required = [
            "judul",
            "kategori",
            "keyword",
            "isi",
            "tgl_submit",
            "kutipan",
            "template",
        ]
        missing = validate_required(data, required)
        if missing:
            return json_error("Semua kolom puisi wajib diisi.")

        judul = str(data["judul"]).strip()
        kategori = str(data["kategori"]).strip()
        keyword = str(data["keyword"]).strip()
        isi = str(data["isi"]).strip()
        kutipan = str(data["kutipan"]).strip()
        template = str(data["template"]).strip()
        tgl_submit_raw = str(data["tgl_submit"]).strip()

        try:
            tgl_submit = datetime.fromisoformat(tgl_submit_raw)
        except ValueError:
            return json_error("Format tanggal submit tidak valid.")

        try:
            image_filename = save_canvas_image(data.get("image_data"))
        except (ValueError, base64.binascii.Error):
            return json_error("Gambar preview tidak valid atau terlalu besar.")

        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO puisi
                (user_id, judul, kategori, keyword, isi, kutipan, template,
                 tgl_submit, image_filename)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user["id"],
                judul,
                kategori,
                keyword,
                isi,
                kutipan,
                template,
                tgl_submit.strftime("%Y-%m-%d %H:%M:%S"),
                image_filename,
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Puisi berhasil disimpan ke database.",
        }), 201

    if aksi == "daftar_puisi" and request.method == "GET":
        user = get_current_user()
        if not user:
            return json_error("Sesi tidak valid. Silakan login kembali.", 401)

        conn = db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                p.id,
                DATE_FORMAT(p.tgl_submit, '%Y-%m-%d %H:%i') AS tgl_submit,
                p.judul,
                u.nama AS penulis,
                p.kategori,
                p.keyword,
                p.isi,
                p.kutipan,
                p.template,
                p.image_filename
            FROM puisi p
            INNER JOIN users u ON u.id = p.user_id
            WHERE p.user_id = %s
            ORDER BY p.tgl_submit DESC, p.id DESC
            """,
            (user["id"],),
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        for row in rows:
            if row.get("image_filename"):
                row["gambar_url"] = f"/uploads/{row['image_filename']}"
            else:
                row["gambar_url"] = None

        return jsonify({
            "status": "success",
            "data": rows,
        })

    return json_error("Aksi tidak dikenal.", 404)


@app.errorhandler(mysql.connector.Error)
def handle_mysql_error(error):
    app.logger.exception("MySQL error")
    return jsonify({
        "status": "error",
        "message": "Terjadi masalah saat mengakses database MySQL.",
    }), 500


if __name__ == "__main__":
    init_database()
    print("============================================")
    print(" Portal Puisi - Monolithic Flask + MySQL")
    print(" http://127.0.0.1:5000")
    print("============================================")
    app.run(host="127.0.0.1", port=5000, debug=True)
