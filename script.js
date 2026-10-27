// ============================================================
// PORTAL PUISI
// Vanilla JavaScript + localStorage
// Tidak membutuhkan backend atau MySQL
// ============================================================

// ================= DOM ELEMENTS =================

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


// ================= LOCAL STORAGE =================

const STORAGE_USERS = "portal_puisi_users";
const STORAGE_POEMS = "portal_puisi_poems";
const STORAGE_SESSION = "portal_puisi_session";


// Mengambil data dari localStorage
function getStorage(key, defaultValue = []) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : defaultValue;
    } catch (error) {
        console.error(`Gagal membaca ${key}:`, error);
        return defaultValue;
    }
}


// Menyimpan data ke localStorage
function saveStorage(key, data) {
    localStorage.setItem(key, JSON.stringify(data));
}


// ================= TANGGAL =================

function setDefaultSubmitDate() {
    if (!puisiTglSubmit) return;

    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());

    puisiTglSubmit.value = now.toISOString().slice(0, 16);
}


// ================= NOTIFIKASI =================

function showAlert(message, type = "info", durationMs = 4500) {
    if (!alertBox) return;

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
    if (alertBox) {
        alertBox.classList.add("hidden");
    }
}


// ================= KEAMANAN TAMPILAN =================

function escapeHtml(text) {
    if (text === null || text === undefined) {
        return "";
    }

    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ================= MANAJEMEN SESI =================

function getCurrentUser() {
    return getStorage(STORAGE_SESSION, null);
}


function setAuthenticatedState(user) {
    if (!user) return;

    authSection.classList.add("hidden");
    dashboardSection.classList.remove("hidden");
    userProfileBar.classList.remove("hidden");

    userDisplayName.textContent = user.nama || user.username;

    loadDaftarPuisi();
}


function setUnauthenticatedState() {
    authSection.classList.remove("hidden");
    dashboardSection.classList.add("hidden");
    userProfileBar.classList.add("hidden");

    userDisplayName.textContent = "-";

    if (puisiTbody) {
        puisiTbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    Silakan masuk untuk melihat daftar karya puisi.
                </td>
            </tr>
        `;
    }
}


// Memeriksa sesi yang tersimpan di browser
function checkSession() {
    const user = getCurrentUser();

    if (user) {
        setAuthenticatedState(user);
    } else {
        setUnauthenticatedState();
    }
}


// ================= TAB LOGIN DAN REGISTER =================

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


// ================= REGISTRASI =================

formRegister.addEventListener("submit", (e) => {
    e.preventDefault();
    hideAlert();

    const username = document
        .getElementById("reg-username")
        .value.trim();

    const nama = document
        .getElementById("reg-nama")
        .value.trim();

    const no_id = document
        .getElementById("reg-noid")
        .value.trim();

    const password = document
        .getElementById("reg-password")
        .value;

    // Validasi input
    if (!username || !nama || !no_id || !password) {
        showAlert("Semua kolom registrasi wajib diisi.", "error");
        return;
    }

    const users = getStorage(STORAGE_USERS);

    // Memeriksa apakah username sudah digunakan
    const usernameExists = users.some(
        user => user.username.toLowerCase() === username.toLowerCase()
    );

    if (usernameExists) {
        showAlert("Username sudah digunakan.", "error");
        return;
    }

    // Memeriksa apakah nomor identitas sudah digunakan
    const idExists = users.some(
        user => user.no_id === no_id
    );

    if (idExists) {
        showAlert("Nomor identitas sudah terdaftar.", "error");
        return;
    }

    // Menyimpan pengguna baru
    const newUser = {
        id: Date.now(),
        username: username,
        nama: nama,
        no_id: no_id,
        password: password
    };

    users.push(newUser);
    saveStorage(STORAGE_USERS, users);

    showAlert("Registrasi berhasil. Silakan login.", "success");

    formRegister.reset();

    // Kembali ke tab login
    tabLogin.click();

    document.getElementById("login-username").value = username;
    document.getElementById("login-password").focus();
});


// ================= LOGIN =================

formLogin.addEventListener("submit", (e) => {
    e.preventDefault();
    hideAlert();

    const username = document
        .getElementById("login-username")
        .value.trim();

    const password = document
        .getElementById("login-password")
        .value;

    const users = getStorage(STORAGE_USERS);

    // Mencari pengguna berdasarkan username dan password
    const user = users.find(
        item =>
            item.username.toLowerCase() === username.toLowerCase() &&
            item.password === password
    );

    if (!user) {
        showAlert(
            "Username atau password salah.",
            "error"
        );
        return;
    }

    // Menyimpan sesi login
    const session = {
        id: user.id,
        username: user.username,
        nama: user.nama,
        no_id: user.no_id
    };

    saveStorage(STORAGE_SESSION, session);

    showAlert("Login berhasil. Selamat datang!", "success");

    formLogin.reset();

    setAuthenticatedState(session);
});


// ================= SUBMIT PUISI =================

formPuisi.addEventListener("submit", (e) => {
    e.preventDefault();
    hideAlert();

    const user = getCurrentUser();

    if (!user) {
        showAlert("Silakan login terlebih dahulu.", "error");
        setUnauthenticatedState();
        return;
    }

    const judul = document
        .getElementById("puisi-judul")
        .value.trim();

    const kategori = document
        .getElementById("puisi-kategori")
        .value;

    const keyword = document
        .getElementById("puisi-keyword")
        .value.trim();

    const isi = document
        .getElementById("puisi-isi")
        .value.trim();

    const tgl_submit = puisiTglSubmit.value;

    // Validasi data puisi
    if (!judul || !kategori || !keyword || !isi || !tgl_submit) {
        showAlert("Semua kolom puisi wajib diisi.", "error");
        return;
    }

    // Mengambil data puisi sebelumnya
    const poems = getStorage(STORAGE_POEMS);

    // Menyiapkan data puisi baru
    const newPoem = {
        id: Date.now(),
        user_id: user.id,
        judul: judul,
        kategori: kategori,
        keyword: keyword,
        isi: isi,
        tgl_submit: tgl_submit,
        penulis: user.nama || user.username
    };

    // Menyimpan puisi
    poems.push(newPoem);
    saveStorage(STORAGE_POEMS, poems);

    showAlert("Puisi berhasil disimpan.", "success");

    formPuisi.reset();
    setDefaultSubmitDate();

    loadDaftarPuisi();
});


// ================= DAFTAR PUISI =================

function loadDaftarPuisi() {
    const user = getCurrentUser();

    if (!user) {
        setUnauthenticatedState();
        return;
    }

    if (!puisiTbody) return;

    const poems = getStorage(STORAGE_POEMS);

    // Menampilkan puisi milik pengguna yang sedang login
    const userPoems = poems.filter(
        poem => poem.user_id === user.id
    );

    // Mengurutkan berdasarkan tanggal terbaru
    userPoems.sort(
        (a, b) => new Date(b.tgl_submit) - new Date(a.tgl_submit)
    );

    if (userPoems.length === 0) {
        puisiTbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    Belum ada karya puisi. Mulailah menulis di atas!
                </td>
            </tr>
        `;
        return;
    }

    puisiTbody.innerHTML = userPoems.map((item, index) => `
        <tr>
            <td><strong>${index + 1}</strong></td>

            <td>
                <small>${escapeHtml(item.tgl_submit)}</small>
            </td>

            <td>
                <strong>${escapeHtml(item.judul)}</strong>
            </td>

            <td>
                ${escapeHtml(item.penulis || "-")}
            </td>

            <td>
                <span class="badge">
                    ${escapeHtml(item.kategori)}
                </span>
            </td>

            <td>
                <code>${escapeHtml(item.keyword)}</code>
            </td>

            <td>
                <div class="poem-content-preview">
                    ${escapeHtml(item.isi)}
                </div>
            </td>
        </tr>
    `).join("");
}


// ================= LOGOUT =================

function handleLogout() {
    localStorage.removeItem(STORAGE_SESSION);

    showAlert("Anda berhasil keluar dari sistem.", "info");

    setUnauthenticatedState();
}


btnLogout.addEventListener("click", handleLogout);


// ================= REFRESH DAFTAR PUISI =================

btnRefreshPuisi.addEventListener("click", loadDaftarPuisi);


// ================= INISIALISASI =================

document.addEventListener("DOMContentLoaded", () => {
    setDefaultSubmitDate();
    checkSession();
});