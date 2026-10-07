/* Shared site footer: What's new (with a "new" dot), Coming next, and the Discord ideas channel.
   Content comes from news.json; load this file with `defer` on every page. */
(function () {
  "use strict";
  var SEEN_KEY = "wf-news-seen";
  var DISCORD = "https://discord.gg/Yh2sTMZksq";
  var css = ".site-foot{border-top:1px solid var(--edge);background:var(--panel);padding:18px 16px 22px;text-align:center;font:14px/1.5 var(--sans);color:var(--muted)}" +
    ".site-foot nav{display:flex;flex-wrap:wrap;justify-content:center;gap:6px 22px;margin-bottom:6px}" +
    ".site-foot a{color:var(--gold);text-decoration:none}.site-foot a:hover{text-decoration:underline}" +
    ".site-foot .dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#E5382B;margin-left:6px;vertical-align:2px;box-shadow:0 0 6px rgba(229,56,43,.7)}" +
    ".site-foot small{font-size:12px}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  var f = document.createElement("footer");
  f.className = "site-foot";
  f.innerHTML = '<nav aria-label="Site news"><a href="news.html" id="foot-news">What’s new</a><a href="news.html#next">Coming next</a>' +
    '<a href="' + DISCORD + '" target="_blank" rel="noopener" id="foot-idea">Send an idea or report a bug (Discord)</a></nav>' +
    "<small>Road to Forever is a fan site for WoW Forever, not made by or affiliated with Blizzard.</small>";
  document.body.appendChild(f);
  // Pages with a fixed bottom tray (Addons downloads, Macros export): keep the footer above it.
  function clearTrays() {
    var h = 0;
    document.querySelectorAll(".tray, .xtray").forEach(function (t) {
      var cs = getComputedStyle(t), r = t.getBoundingClientRect();
      if (cs.position === "fixed" && cs.visibility !== "hidden" && r.top < innerHeight) h = Math.max(h, innerHeight - r.top);
    });
    f.style.marginBottom = h ? h + "px" : "";
  }
  clearTrays();
  window.addEventListener("resize", clearTrays);
  document.addEventListener("click", function () { setTimeout(clearTrays, 350); });
  fetch("news.json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
    if (!j) return;
    if (j.discord) document.getElementById("foot-idea").href = j.discord;
    var latest = j.news && j.news[0] && j.news[0].date, seen = null;
    try { seen = localStorage.getItem(SEEN_KEY); } catch (e) { /* blocked */ }
    if (latest && seen !== latest && !/news\.html$/.test(location.pathname)) {
      var a = document.getElementById("foot-news");
      a.insertAdjacentHTML("beforeend", '<span class="dot" title="New since your last visit"></span>');
      a.setAttribute("aria-label", "What’s new (new since your last visit)");
    }
  }).catch(function () { /* footer still works without the dot */ });
})();
