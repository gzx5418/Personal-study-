const App = {
  modules: {},
  current: null,
  _rendered: {},

  register(name, module) {
    this.modules[name] = module;
  },

  init() {
    window.addEventListener("hashchange", () => this.route());
    if (!window.location.hash) window.location.hash = "#dashboard";
    this.route();
  },

  route() {
    const hash = window.location.hash.slice(1) || "dashboard";
    const mod = this.modules[hash];
    if (!mod) return;
    if (this.current === hash) return;

    // 切换模块前取消所有进行中的请求，避免无效响应触发已卸载模块的回调
    if (typeof Api !== "undefined" && typeof Api.cancelAll === "function") {
      try { Api.cancelAll(); } catch (e) { console.warn("cancelAll failed:", e); }
    }

    $$("[data-nav]").forEach((el) => {
      el.classList.toggle("is-active", el.dataset.nav === hash);
    });

    $$(".module").forEach((el) => {
      el.classList.remove("is-visible");
    });

    this.current = hash;
    document.title = `${mod.title} - 智学助手`;

    const container = $(`#module-${hash}`);
    if (container) {
      if (!this._rendered[hash]) {
        container.innerHTML = mod.render();
        mod.bind(container);
        this._rendered[hash] = true;
      }
      container.classList.add("is-visible");
    }
  },
};

document.addEventListener("DOMContentLoaded", () => {
  App.init();

  const menuToggle = document.getElementById("menuToggle");
  const headerNav = document.getElementById("headerNav");
  const navOverlay = document.getElementById("navOverlay");

  function closeMobileNav() {
    if (headerNav) headerNav.classList.remove("is-open");
    if (navOverlay) navOverlay.classList.remove("is-visible");
    if (menuToggle) menuToggle.setAttribute("aria-expanded", "false");
  }

  function toggleMobileNav() {
    const isOpen = headerNav && headerNav.classList.contains("is-open");
    if (isOpen) {
      closeMobileNav();
    } else {
      if (headerNav) headerNav.classList.add("is-open");
      if (navOverlay) navOverlay.classList.add("is-visible");
      if (menuToggle) menuToggle.setAttribute("aria-expanded", "true");
    }
  }

  if (menuToggle) {
    menuToggle.addEventListener("click", toggleMobileNav);
  }

  if (navOverlay) {
    navOverlay.addEventListener("click", closeMobileNav);
  }

  if (headerNav) {
    headerNav.addEventListener("click", (e) => {
      if (e.target.closest(".nav-link")) {
        closeMobileNav();
      }
    });
  }
});
