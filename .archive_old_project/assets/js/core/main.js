// =========================
// ICS FRONTEND UI - MAIN.JS
// State-driven UI Controller
// =========================

document.addEventListener("DOMContentLoaded", () => {
  // INIT ROUTER FIRST
  ICSRouter.initRouter();

  // =========================
  // ELEMENTS
  // =========================
  const drawerToggle = document.getElementById("drawerToggle");
  const drawer = document.getElementById("drawer");
  const overlay = document.getElementById("overlay");
  const closeBtn = document.getElementById("closeBtn");

  const profileBtn = document.getElementById("profileBtn");
  const profileMenu = document.getElementById("profileMenu");

  const optionsBtn = document.getElementById("optionsBtn");
  const optionsMenu = document.getElementById("optionsMenu");

  const themeToggle = document.getElementById("themeToggle");

  // FIX: Wire up logout button — was present in HTML but never bound
  const logoutBtn = document.getElementById("logoutBtn");

  if (!drawer || !overlay) {
    console.warn("Critical UI elements missing.");
    return;
  }

  // =========================
  // STATE
  // =========================
  const state = {
    drawerOpen: false,
    profileOpen: false,
    optionsOpen: false,
  };

  // =========================
  // HELPERS
  // =========================
  function closeAll() {
    setState({
      drawerOpen: false,
      profileOpen: false,
      optionsOpen: false,
    });
  }

  function isAnyOpen() {
    return state.drawerOpen || state.profileOpen || state.optionsOpen;
  }

  // =========================
  // STATE CONTROLLER
  // =========================
  function setState(nextState) {
    Object.assign(state, nextState);

    // Enforce exclusivity
    if (state.drawerOpen) {
      state.profileOpen = false;
      state.optionsOpen = false;
    }

    if (state.profileOpen) {
      state.drawerOpen = false;
      state.optionsOpen = false;
    }

    if (state.optionsOpen) {
      state.drawerOpen = false;
      state.profileOpen = false;
    }

    render();
  }

  // =========================
  // RENDER
  // =========================
  function render() {
    drawer.classList.toggle("active", state.drawerOpen);
    profileMenu?.classList.toggle("active", state.profileOpen);
    optionsMenu?.classList.toggle("active", state.optionsOpen);

    overlay.classList.toggle("active", isAnyOpen());

    document.body.style.overflow = state.drawerOpen ? "hidden" : "";
  }

  // =========================
  // THEME SYSTEM
  // =========================
  function applyTheme(theme) {
    const isDark = theme === "dark";
    document.body.classList.toggle("dark", isDark);

    if (themeToggle) {
      themeToggle.textContent = isDark ? "☀️" : "🌙";
    }
  }

  function initTheme() {
    const saved = localStorage.getItem("theme");

    if (saved) {
      applyTheme(saved);
    } else {
      const prefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)",
      ).matches;
      applyTheme(prefersDark ? "dark" : "light");
    }
  }

  initTheme();

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      flashThemeTransition();

      const isDark = document.body.classList.toggle("dark");
      const newTheme = isDark ? "dark" : "light";

      localStorage.setItem("theme", newTheme);
      applyTheme(newTheme);
    });
  }

  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", (e) => {
      if (!localStorage.getItem("theme")) {
        applyTheme(e.matches ? "dark" : "light");
      }
    });

  // =========================
  // EVENT HANDLERS
  // =========================

  drawerToggle?.addEventListener("click", (e) => {
    e.stopPropagation();
    setState({ drawerOpen: !state.drawerOpen });
  });

  closeBtn?.addEventListener("click", () => {
    setState({ drawerOpen: false });
  });

  profileBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    setState({ profileOpen: !state.profileOpen });
  });

  optionsBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    setState({ optionsOpen: !state.optionsOpen });
  });

  // FIX: Logout button now properly calls router logout (clears session + redirects)
  logoutBtn?.addEventListener("click", () => {
    ICSRouter.Navigation.logout();
  });

  overlay?.addEventListener("click", closeAll);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeAll();
  });

  drawer?.addEventListener("click", (e) => e.stopPropagation());

  // =========================
  // DRAG GESTURE (DRAWER)
  // =========================
  let startY = 0;
  let currentY = 0;
  let startTime = 0;
  let isDragging = false;

  const CLOSE_DISTANCE = 120;
  const VELOCITY_THRESHOLD = 0.5;

  function startDrag(y) {
    startY = y;
    currentY = y;
    startTime = Date.now();
    isDragging = true;

    drawer.style.transition = "none";
  }

  function moveDrag(y) {
    if (!isDragging) return;

    currentY = y;
    const diff = currentY - startY;

    if (diff > 0) {
      drawer.style.transform = `translateY(${diff * 0.6}px)`;
    }
  }

  function endDrag() {
    if (!isDragging) return;

    isDragging = false;

    const diff = currentY - startY;
    const time = Date.now() - startTime;
    const velocity = diff / time;

    drawer.style.transition = "0.35s cubic-bezier(0.22, 1, 0.36, 1)";

    if (diff > CLOSE_DISTANCE || velocity > VELOCITY_THRESHOLD) {
      setState({ drawerOpen: false });
    } else {
      drawer.style.transform = "translateY(0)";
    }
  }

  drawer?.addEventListener("touchstart", (e) =>
    startDrag(e.touches[0].clientY),
  );
  drawer?.addEventListener("touchmove", (e) => moveDrag(e.touches[0].clientY));
  drawer?.addEventListener("touchend", endDrag);

  drawer?.addEventListener("mousedown", (e) => startDrag(e.clientY));
  document.addEventListener("mousemove", (e) => moveDrag(e.clientY));
  document.addEventListener("mouseup", endDrag);

  // =========================
  // LOAD USER INTO UI
  // =========================
  // Populate navbar profile info from session
  ICSAuth.loadUserUI();

  // =========================
  // INITIAL RENDER
  // =========================
  render();
});

// =========================
// THEME TRANSITION EFFECT
// =========================
function flashThemeTransition() {
  const fade = document.createElement("div");
  fade.className = "theme-fade";
  document.body.appendChild(fade);

  requestAnimationFrame(() => fade.classList.add("active"));

  setTimeout(() => {
    fade.classList.remove("active");
    setTimeout(() => fade.remove(), 300);
  }, 150);
}
