async function loadComponent(path, targetId) {
  const res = await fetch(path);
  const html = await res.text();
  document.getElementById(targetId).innerHTML = html;
}

document.addEventListener("DOMContentLoaded", async () => {

  await loadComponent("/components/navbar.html", "navbar-container");
  await loadComponent("/components/app-drawer.html", "drawer-container");
  await loadComponent("/components/footer.html", "footer-container");

});