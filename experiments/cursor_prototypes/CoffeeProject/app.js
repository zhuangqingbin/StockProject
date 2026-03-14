function $(id) {
  return document.getElementById(id);
}

function showToast(title, msg) {
  const toast = $("toast");
  const t = $("toastTitle");
  const m = $("toastMsg");
  t.textContent = title;
  m.textContent = msg;
  toast.hidden = false;
  window.setTimeout(() => {
    toast.hidden = true;
  }, 3500);
}

function setCtaHint(isSixMonth) {
  const hint = $("ctaHint");
  hint.textContent = isSixMonth ? "and continue your 6‑month journey" : "and manage your monthly plan";
}

document.addEventListener("DOMContentLoaded", () => {
  const form = $("loginForm");
  const togglePw = $("togglePw");
  const pw = $("password");
  const sixMonth = $("sixMonth");

  setCtaHint(sixMonth.checked);

  togglePw.addEventListener("click", () => {
    const isPw = pw.type === "password";
    pw.type = isPw ? "text" : "password";
    togglePw.textContent = isPw ? "Hide" : "Show";
    togglePw.setAttribute("aria-label", isPw ? "Hide password" : "Show password");
  });

  sixMonth.addEventListener("change", () => {
    setCtaHint(sixMonth.checked);
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const email = form.email.value.trim();
    const password = form.password.value;

    // Minimal front-end validation (demo).
    if (!email || !email.includes("@")) {
      showToast("Check your email", "Please enter a valid email address.");
      form.email.focus();
      return;
    }
    if (!password || password.length < 8) {
      showToast("Password too short", "Use at least 8 characters.");
      form.password.focus();
      return;
    }

    const plan = sixMonth.checked ? "6‑month" : "monthly";
    showToast("Signed in", `Welcome back. Loading your ${plan} dashboard…`);
  });
});

