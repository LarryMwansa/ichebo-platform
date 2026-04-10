document.addEventListener("DOMContentLoaded", () => {
  setTimeout(initAppDrawer, 100);
});

function initAppDrawer() {
  const appBtn = document.getElementById("appBtn");
  if (!appBtn) return;

 // =========================
// ROUTER Logout Helper
// =========================
const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    ICSRouter.Navigation.logout();
  });
}
}