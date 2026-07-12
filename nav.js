/*
  nav.js
  ------
  1. renderSidebar(activePage) - injects the same sidebar markup into every
     screen so it's visually identical everywhere (edit it once here, it
     changes on all screens).
  2. requireAuth() - called at the top of every screen's own <script>. If
     there's no logged-in user (GET /api/auth/me fails) it bounces back to
     the login screen. This is what makes screens 2-10 "protected".
*/

const NAV_ITEMS = [
  { href: "dashboard.html", icon: "◆", label: "Dashboard", key: "dashboard" },
  { href: "xfactor.html", icon: "✺", label: "AI Insights", key: "xfactor" },
  { href: "org-setup.html", icon: "⚙", label: "Organization setup", key: "org" },
  { href: "assets.html", icon: "▣", label: "Assets", key: "assets" },
  { href: "allocation.html", icon: "⇄", label: "Allocation & Transfer", key: "allocation" },
  { href: "ot.html", icon: "⏱", label: "Overtime Control", key: "ot" },
  { href: "booking.html", icon: "▤", label: "Resource Booking", key: "booking" },
  { href: "maintenance.html", icon: "✦", label: "Maintenance", key: "maintenance" },
  { href: "audit.html", icon: "☑", label: "Audit", key: "audit" },
  { href: "reports.html", icon: "▲", label: "Reports", key: "reports" },
  { href: "activity.html", icon: "◷", label: "Activity & Notifications", key: "activity" },
];

function renderSidebar(activeKey) {
  const links = NAV_ITEMS.map(item => `
    <a class="nav-link ${item.key === activeKey ? "active" : ""}" href="${item.href}">
      <span class="ic">${item.icon}</span>${item.label}
    </a>`).join("");

  return `
    <aside class="sidebar" id="sidebar">
      <div class="brand"><span class="mark">AF</span> AssetFlow</div>
      <div class="nav-group-label">Workspace</div>
      ${links}
      <div class="sidebar-footer">
        <span id="sidebar-user">...</span>
        <span class="logout-btn" onclick="doLogout()">Log out</span>
      </div>
    </aside>`;
}

async function requireAuth() {
  try {
    const user = await api.get("/api/auth/me");
    const el = document.getElementById("sidebar-user");
    if (el) el.textContent = user.name.split(" ")[0];
    const avatar = document.getElementById("topbar-avatar");
    if (avatar) avatar.textContent = user.name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase();
    return user;
  } catch (e) {
    window.location.href = "index.html";
    return null;
  }
}

async function doLogout() {
  await api.post("/api/auth/logout");
  window.location.href = "index.html";
}