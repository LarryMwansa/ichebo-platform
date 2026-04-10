document.addEventListener("DOMContentLoaded", () => {
  setTimeout(initAppDrawer, 100);
});

function initAppDrawer() {
  const appBtn = document.getElementById("appBtn");
  if (!appBtn) return;

  // your logic here...
  const apps = [
  { name: "Bible", icon: "📖", link: "/pages/bible.html" },
  { name: "Activity", icon: "✅", link: "/pages/activity.html" },
  { name: "Records", icon: "📝", link: "/pages/records.html" },
  { name: "Learn", icon: "🏫", link: "/pages/learn.html" },
  { name: "Live", icon: "🎬", link: "/pages/live.html" },
  { name: "Community", icon: "👥", link: "#" },
];

function renderApps() {
  const grid = document.getElementById("appGrid");
  if (!grid) return;

  grid.innerHTML = "";

  apps.forEach(app => {
    const el = document.createElement("a");
    el.href = app.link;
    el.className = "app";

    el.innerHTML = `
      <div class="app-icon">${app.icon}</div>
      <div class="app-label">${app.name}</div>
    `;

    grid.appendChild(el);
  });
}
}