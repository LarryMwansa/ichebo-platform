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
  guard() {
    const page = this.currentPage();
    const isAuth = ICSStorage.Session.isAuthenticated();

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
    ICSStorage.Session.clear();
    Router.goTo("/pages/login.html");
  }

};



// =========================
// INITIALIZE ROUTER
// =========================
function initRouter() {
  Router.guard();
}



// =========================
// EXPORT GLOBAL
// =========================
window.ICSRouter = {
  Router,
  Navigation,
  initRouter
};