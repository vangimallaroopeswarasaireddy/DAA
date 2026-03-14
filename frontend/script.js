const API_BASE = "http://127.0.0.1:8000";

const showLoginBtn = document.getElementById("showLoginBtn");
const showRegisterBtn = document.getElementById("showRegisterBtn");
const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const messageBox = document.getElementById("messageBox");

function showMessage(text, type = "success") {
  messageBox.textContent = text;
  messageBox.className = `message ${type}`;
  messageBox.classList.remove("hidden");
}

function switchToLogin() {
  loginForm.classList.remove("hidden");
  registerForm.classList.add("hidden");
  showLoginBtn.classList.add("active");
  showRegisterBtn.classList.remove("active");
  messageBox.classList.add("hidden");
}

function switchToRegister() {
  registerForm.classList.remove("hidden");
  loginForm.classList.add("hidden");
  showRegisterBtn.classList.add("active");
  showLoginBtn.classList.remove("active");
  messageBox.classList.add("hidden");
}

showLoginBtn.addEventListener("click", switchToLogin);
showRegisterBtn.addEventListener("click", switchToRegister);

registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    username: document.getElementById("registerUsername").value.trim(),
    email: document.getElementById("registerEmail").value.trim(),
    password: document.getElementById("registerPassword").value
  };

  try {
    const res = await fetch(`${API_BASE}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
      showMessage(data.detail || "Registration failed", "error");
      return;
    }

    showMessage("Registration successful. Please login.", "success");
    registerForm.reset();
    switchToLogin();
  } catch (error) {
    showMessage("Cannot connect to backend", "error");
  }
});

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    username: document.getElementById("loginUsername").value.trim(),
    password: document.getElementById("loginPassword").value
  };

  try {
    const res = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
      showMessage(data.detail || "Login failed", "error");
      return;
    }

    localStorage.setItem("token", data.access_token);
    window.location.href = "dashboard.html";
  } catch (error) {
    showMessage("Cannot connect to backend", "error");
  }
});