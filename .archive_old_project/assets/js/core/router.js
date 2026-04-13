// =========================
// ICS PLATFORM ROUTER
// =========================

// Define route rules
const ROUTES = {
  public: [
    "index.html",
    "login.html",
    "register.html"
  ],
  protected: [
    "dashboard.html",
    "bible.html",
    "records.html",
    "activity.html",
    "live.html",
    "learn.html",
    "profile.html",
    "settings.html"
  ],
  defaultAuth: "/pages/dashboard.html",
  defaultPublic: "/pages/login.html"
};

const ROUTE_COMPETENCE_MIN = {
  "governance.html": 4,
  "handbook.html": 5
}



// =========================
// ROUTER CORE
// =========================
const Router = {

  // Get current page filename
  currentPage() {
    const path = window.location.pathname;
    return path.substring(path.lastIndexOf("/") + 1);
  },

  // Check if route is protected
  isProtected(page) {
    return ROUTES.protected.includes(page);
  },

  // Check if route is public
  isPublic(page) {
    return ROUTES.public.includes(page);
  },

  // Redirect helper
  goTo(path) {
    window.location.href = path;
  },

  // Main guard logic
  async guard() {
    const page = this.currentPage();
    const isAuth = !!localStorage.getItem('ics_token');

    // If user NOT logged in and tries protected page
    if (!isAuth && this.isProtected(page)) {
      this.goTo(ROUTES.defaultPublic);
      return;
    }

    // If user IS logged in and tries public page
    if (isAuth && this.isPublic(page)) {
      this.goTo(ROUTES.defaultAuth);
      return;
    }

    if (isAuth && this.isProtected(page) && window.ICSIdentity?.getCurrentUser) {
      const user = await window.ICSIdentity.getCurrentUser()
      if (!user) {
        localStorage.removeItem('ics_token')
        localStorage.removeItem('ics_user')
        this.goTo(ROUTES.defaultPublic)
        return
      }

      const min = ROUTE_COMPETENCE_MIN[page]
      if (typeof min === 'number') {
        const level = Number(user.competence_level ?? 0)
        if (Number.isFinite(level) && level < min) {
          this.goTo(ROUTES.defaultAuth)
          return
        }
      }
    }
  }

};



// =========================
// NAVIGATION API
// =========================
const Navigation = {

  go(page) {
    Router.goTo(`/pages/${page}`);
  },

  logout() {
    localStorage.removeItem('ics_token');
    localStorage.removeItem('ics_user');
    Router.goTo("/pages/login.html");
  }

};



// =========================
// INITIALIZE ROUTER
// =========================
function initRouter() {
  Router.guard().catch(() => {
    Router.goTo(ROUTES.defaultPublic)
  })
}



// =========================
// EXPORT GLOBAL
// =========================
window.ICSRouter = {
  Router,
  Navigation,
  initRouter
};
