-- 1. Inisialisasi Database
CREATE DATABASE IF NOT EXISTS db_puisi 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE db_puisi;

-- 2. Tabel `users`
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    nama VARCHAR(100) NOT NULL,
    no_id VARCHAR(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Tabel `puisi` dengan Foreign Key ON DELETE CASCADE
CREATE TABLE IF NOT EXISTS puisi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    judul VARCHAR(150) NOT NULL,
    tgl_submit DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    isi TEXT NOT NULL,
    kategori VARCHAR(50) NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    CONSTRAINT fk_puisi_users
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Data Dummy Awal (Password hash default: 'password123')
INSERT INTO users (id, username, password, nama, no_id) VALUES
(1, 'chairil_anwar', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Chairil Anwar', 'ID-001'),
(2, 'sapardi_djoko', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Sapardi Djoko Damono', 'ID-002')
ON DUPLICATE KEY UPDATE username=VALUES(username);

INSERT INTO puisi (id, user_id, judul, isi, kategori, keyword) VALUES
(1, 1, 'Aku', 'Kalau sampai waktuku\nKu mau tak seorang kan merayu\nTidak juga kau\n\nTak perlu sedu sedan itu\n\nAku ini binatang jalang\nDari kumpulannya terbuang...', 'Puisi Bebas', 'perjuangan, semangat, eksistensial'),
(2, 2, 'Hujan Bulan Juni', 'Tak ada yang lebih tabah\ndari hujan bulan juni\ndirahasiakannya rintik rindunya\nkepada pohon berbunga itu...', 'Romansa & Alam', 'rindu, ketabahan, hujan')
ON DUPLICATE KEY UPDATE judul=VALUES(judul);
