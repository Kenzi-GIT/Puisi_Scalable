/**
 * ==========================================================================
 * Logika Frontend (Vanilla JavaScript / Pure Fetch API)
 * Menangani Single-Path Routing Backend & Otomatisasi Session Cookie
 * ==========================================================================
 */

// Target Endpoint Single-Path Routing
const BACKEND_URL = "app.py";

// Elemen DOM
const alertBox = document.getElementById("alert-box");
const authSection = document.getElementById("auth-section");
const dashboardSection = document.getElementById("dashboard-section");
const userProfileBar = document.getElementById("user-profile-bar");
const userDisplayName = document.getElementById("user-display-name");

const tabLogin = document.getElementById("tab-login");
const tabRegister = document.getElementById("tab-register");
const formLogin = document.getElementById("form-login");
const formRegister = document.getElementById("form-register");
const formPuisi = document.getElementById("form-puisi");
const puisiTbody = document.getElementById("puisi-tbody");

const btnLogout = document.getElementById("btn-logout");
const btnRefreshPuisi = document.getElementById("btn-refresh-puisi");
const puisiTglSubmit = document.getElementById("puisi-tgl-submit");

// Isi tanggal submit dengan waktu lokal saat form pertama kali dibuka.
function setDefaultSubmitDate() {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    puisiTglSubmit.value = now.toISOString().slice(0, 16);
}

setDefaultSubmitDate();

// ================= Helper Notifikasi =================
function showAlert(message, type = "info", durationMs = 4500) {
    alertBox.className = `alert-box alert-${type}`;
    alertBox.textContent = message;
    alertBox.classList.remove("hidden");

    if (durationMs > 0) {
        setTimeout(() => {
            alertBox.classList.add("hidden");
        }, durationMs);
    }
}

function hideAlert() {
    alertBox.classList.add("hidden");
}

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ================= Manajemen Tampilan Sesi =================
function setAuthenticatedState(user) {
    authSection.classList.add("hidden");
    dashboardSection.classList.remove("hidden");
    userProfileBar.classList.remove("hidden");
    userDisplayName.textContent = user.nama || user.username;
    
    // Muat daftar puisi setelah login sukses
    loadDaftarPuisi();
}

function setUnauthenticatedState() {
    authSection.classList.remove("hidden");
    dashboardSection.classList.add("hidden");
    userProfileBar.classList.add("hidden");
    userDisplayName.textContent = "-";
    puisiTbody.innerHTML = '<tr><td colspan="7" class="text-center">Silakan masuk untuk melihat daftar karya puisi.</td></tr>';
}

// ================= Tab Navigasi Auth =================
tabLogin.addEventListener("click", () => {
    tabLogin.classList.add("active");
    tabRegister.classList.remove("active");
    formLogin.classList.remove("hidden");
    formRegister.classList.add("hidden");
    hideAlert();
});

tabRegister.addEventListener("click", () => {
    tabRegister.classList.add("active");
    tabLogin.classList.remove("active");
    formRegister.classList.remove("hidden");
    formLogin.classList.add("hidden");
    hideAlert();
});

// ================= API Calls (Fetch API Native) =================

/**
 * 1. Cek Sesi saat halaman pertama kali dibuka
 */
async function checkSession() {
    try {
        const response = await fetch(`${BACKEND_URL}?aksi=check_session`, {
            method: "GET",
            credentials: "include" // Mengirim dan menerima cookie sesi browser
        });

        const result = await response.json();
        if (result.authenticated && result.user) {
            setAuthenticatedState(result.user);
        } else {
            setUnauthenticatedState();
        }
    } catch (err) {
        console.error("Gagal memeriksa sesi:", err);
        setUnauthenticatedState();
    }
}

/**
 * 2. Aksi: Login Pengguna
 */
formLogin.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert();

    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;

    try {
        const response = await fetch(`${BACKEND_URL}?aksi=login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ username, password })
        });

        const result = await response.json();

        if (response.ok && result.status === "success") {
            showAlert(result.message, "success");
            formLogin.reset();
            setAuthenticatedState(result.user);
        } else {
            showAlert(result.message || "Gagal masuk. Periksa kembali akun Anda.", "error");
        }
    } catch (err) {
        showAlert("Terjadi kesalahan koneksi ke server.", "error");
        console.error("Login error:", err);
    }
});

/**
 * 3. Aksi: Registrasi Pengguna Baru
 */
formRegister.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert();

    const username = document.getElementById("reg-username").value.trim();
    const nama = document.getElementById("reg-nama").value.trim();
    const no_id = document.getElementById("reg-noid").value.trim();
    const password = document.getElementById("reg-password").value;

    try {
        const response = await fetch(`${BACKEND_URL}?aksi=register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ username, nama, no_id, password })
        });

        const result = await response.json();

        if (response.ok && result.status === "success") {
            showAlert(result.message, "success");
            formRegister.reset();
            // Pindahkan tab ke login dan isi username otomatis
            tabLogin.click();
            document.getElementById("login-username").value = username;
            document.getElementById("login-password").focus();
        } else {
            showAlert(result.message || "Gagal melakukan registrasi.", "error");
        }
    } catch (err) {
        showAlert("Terjadi kesalahan koneksi saat registrasi.", "error");
        console.error("Register error:", err);
    }
});

/**
 * 4. Aksi: Submit Puisi Baru
 */
formPuisi.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert();

    const judul = document.getElementById("puisi-judul").value.trim();
    const kategori = document.getElementById("puisi-kategori").value;
    const keyword = document.getElementById("puisi-keyword").value.trim();
    const isi = document.getElementById("puisi-isi").value.trim();
    const tgl_submit = document.getElementById("puisi-tgl-submit").value;

    try {
        const response = await fetch(`${BACKEND_URL}?aksi=submit_puisi`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ judul, kategori, keyword, isi, tgl_submit })
        });

        const result = await response.json();

        if (response.ok && result.status === "success") {
            showAlert(result.message, "success");
            formPuisi.reset();
            setDefaultSubmitDate();
            loadDaftarPuisi();
        } else {
            showAlert(result.message || "Gagal menyimpan karya puisi.", "error");
            if (response.status === 401) {
                setUnauthenticatedState();
            }
        }
    } catch (err) {
        showAlert("Terjadi kesalahan saat menyimpan puisi.", "error");
        console.error("Submit puisi error:", err);
    }
});

/**
 * 5. Aksi: Ambil Daftar Puisi
 */
async function loadDaftarPuisi() {
    puisiTbody.innerHTML = '<tr><td colspan="7" class="text-center">Memuat karya puisi terbaru...</td></tr>';

    try {
        const response = await fetch(`${BACKEND_URL}?aksi=daftar_puisi`, {
            method: "GET",
            credentials: "include"
        });

        if (response.status === 401) {
            setUnauthenticatedState();
            showAlert("Sesi telah habis. Silakan login kembali.", "error");
            return;
        }

        const result = await response.json();

        if (response.ok && result.status === "success" && Array.isArray(result.data)) {
            if (result.data.length === 0) {
                puisiTbody.innerHTML = '<tr><td colspan="7" class="text-center">Belum ada karya puisi. Mulailah menulis di atas!</td></tr>';
                return;
            }

            puisiTbody.innerHTML = result.data.map((item, index) => `
                <tr>
                    <td><strong>${index + 1}</strong></td>
                    <td><small>${escapeHtml(item.tgl_submit)}</small></td>
                    <td><strong>${escapeHtml(item.judul)}</strong></td>
                    <td>${escapeHtml(item.penulis || "-")}</td>
                    <td><span class="badge">${escapeHtml(item.kategori)}</span></td>
                    <td><code>${escapeHtml(item.keyword)}</code></td>
                    <td><div class="poem-content-preview">${escapeHtml(item.isi)}</div></td>
                </tr>
            `).join("");
        } else {
            puisiTbody.innerHTML = `<tr><td colspan="7" class="text-center error-text">${escapeHtml(result.message || "Gagal memuat data")}</td></tr>`;
        }
    } catch (err) {
        console.error("Load puisi error:", err);
        puisiTbody.innerHTML = '<tr><td colspan="7" class="text-center">Gagal memuat data puisi. Silakan klik muat ulang.</td></tr>';
    }
}

/**
 * 6. Aksi: Logout Pengguna
 */
async function handleLogout() {
    try {
        await fetch(`${BACKEND_URL}?aksi=logout`, {
            method: "POST",
            credentials: "include"
        });
    } catch (err) {
        console.warn("Logout request warning:", err);
    } finally {
        showAlert("Anda berhasil keluar dari sistem.", "info");
        setUnauthenticatedState();
    }
}

btnLogout.addEventListener("click", handleLogout);
btnRefreshPuisi.addEventListener("click", loadDaftarPuisi);

// ================= Inisialisasi Saat Halaman Dimuat =================
document.addEventListener("DOMContentLoaded", () => {
    checkSession();
});
