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

document.addEventListener("DOMContentLoaded", () => App.init());
