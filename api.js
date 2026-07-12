/*
  api.js
  ------
  Tiny wrapper around fetch() so every screen talks to the Flask backend
  the same way. Because app.py serves the frontend AND the API from the
  same origin, we don't need to hardcode http://127.0.0.1:5000 - relative
  URLs like "/api/assets" just work, and the session cookie is sent
  automatically (credentials: 'include').
*/
const api = {
  async _request(method, path, body) {
    const opts = {
      method,
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    };
    if (body !== undefined) opts.body = JSON.stringify(body);

    const res = await fetch(path, opts);
    let data = null;
    try { data = await res.json(); } catch (e) { /* no body */ }

    if (!res.ok) {
      const message = (data && data.error) ? data.error : `Request failed (${res.status})`;
      throw new Error(message);
    }
    return data;
  },
  get(path) { return this._request("GET", path); },
  post(path, body) { return this._request("POST", path, body); },
  patch(path, body) { return this._request("PATCH", path, body); },
};

/* Small toast helper used across screens for success/error feedback */
function toast(message, kind = "info") {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    el.style.cssText = `
      position:fixed; bottom:22px; right:22px; z-index:999;
      padding:12px 18px; border-radius:8px; font-size:0.85rem; font-weight:600;
      box-shadow:0 8px 24px rgba(0,0,0,0.4); transition:opacity .2s; opacity:0;
    `;
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.style.background = kind === "error" ? "#F1706B" : "#34D3B8";
  el.style.color = "#0B0F1A";
  el.style.opacity = "1";
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.style.opacity = "0"; }, 2600);
}
