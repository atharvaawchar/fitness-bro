/* ═══════════════════════════════════════════════════════════════
   Fitness Bro — Main JavaScript
   Theme toggle, sidebar toggle, global utilities
═══════════════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {

  // ─── Dark Mode ────────────────────────────────────────────────
  const html       = document.documentElement;
  const themeBtn   = document.getElementById("themeToggle");
  const themeIcon  = document.getElementById("themeIcon");
  const savedTheme = localStorage.getItem("fb-theme") || "dark";

  function applyTheme(theme) {
    html.setAttribute("data-theme", theme);
    localStorage.setItem("fb-theme", theme);
    if (themeIcon) {
      themeIcon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-fill";
    }
  }

  applyTheme(savedTheme);

  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const current = html.getAttribute("data-theme");
      applyTheme(current === "dark" ? "light" : "dark");
    });
  }

  // ─── Sidebar Toggle (mobile) ──────────────────────────────────
  const sidebar  = document.getElementById("sidebar");
  const overlay  = document.getElementById("sidebarOverlay");
  const toggleBtn = document.getElementById("sidebarToggle");

  function openSidebar() {
    sidebar?.classList.add("open");
    overlay?.classList.add("show");
    document.body.style.overflow = "hidden";
  }

  function closeSidebar() {
    sidebar?.classList.remove("open");
    overlay?.classList.remove("show");
    document.body.style.overflow = "";
  }

  toggleBtn?.addEventListener("click", () => {
    sidebar?.classList.contains("open") ? closeSidebar() : openSidebar();
  });

  overlay?.addEventListener("click", closeSidebar);

  // Close sidebar on nav link click (mobile)
  document.querySelectorAll(".nav-item").forEach(link => {
    link.addEventListener("click", () => {
      if (window.innerWidth <= 768) closeSidebar();
    });
  });

  // ─── Active Nav Highlight ─────────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll(".nav-item").forEach(item => {
    const href = item.getAttribute("href");
    if (href === currentPath || (href !== "/" && currentPath.startsWith(href))) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // ─── Staggered Fade-in Animations ────────────────────────────
  const fadeEls = document.querySelectorAll(".fade-in-up");
  fadeEls.forEach((el, i) => {
    el.style.animationDelay = `${i * 0.08}s`;
  });

  // ─── Health Check & Status ────────────────────────────────────
  fetch("/api/health")
    .then(r => r.json())
    .then(data => {
      const badge = document.getElementById("ibmBadge");
      if (!badge) return;
      if (data.ibm_watsonx_connected) {
        badge.innerHTML = `<div class="ibm-badge-dot" style="background:var(--green);box-shadow:0 0 8px var(--green)"></div><span>IBM Granite <strong style="color:var(--green)">Connected</strong></span>`;
      } else if (data.ibm_watsonx_configured) {
        const err = (data.ibm_watsonx_error || "Init failed").substring(0, 60);
        badge.innerHTML = `<div class="ibm-badge-dot" style="background:var(--orange)"></div><span style="color:var(--orange);font-size:11px">${err}</span>`;
      } else {
        badge.innerHTML = `<div class="ibm-badge-dot" style="background:var(--text-dim)"></div><span>Powered by <strong>IBM Watsonx</strong></span>`;
      }
    })
    .catch(() => {});

  // ─── Utility: Format Numbers ──────────────────────────────────
  window.formatNumber = (n) => {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
    if (n >= 1000)    return (n / 1000).toFixed(1) + "K";
    return String(n);
  };

  // ─── Utility: Show Toast Notification ─────────────────────────
  window.showToast = (message, type = "success") => {
    const existing = document.querySelector(".fb-toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.className = "fb-toast";
    toast.style.cssText = `
      position: fixed; bottom: 24px; right: 24px; z-index: 9999;
      background: ${type === "success" ? "var(--success)" : type === "error" ? "var(--danger)" : "var(--accent)"};
      color: #fff; padding: 12px 20px; border-radius: 12px;
      font-weight: 600; font-size: 14px; box-shadow: var(--shadow-md);
      animation: slideToast 0.3s ease;
      display: flex; align-items: center; gap: 8px;
    `;
    const icons = { success: "✅", error: "❌", info: "ℹ️" };
    toast.innerHTML = `${icons[type] || "✅"} ${message}`;
    document.body.appendChild(toast);

    const style = document.createElement("style");
    style.textContent = "@keyframes slideToast{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}";
    document.head.appendChild(style);

    setTimeout(() => toast.remove(), 3500);
  };

  // ─── Utility: Download text file ─────────────────────────────
  window.downloadTxt = (content, filename) => {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

});
