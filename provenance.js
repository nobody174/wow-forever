/* Shared data-provenance strip: "Client 1.60.x · updated <date> · beta data" (plus plan step counts on the launch plan).
   Content comes from data-version.json, which build.py writes; nothing here is typed by hand.
   Put <div id="provenance"></div> (add data-plan on the launch plan) where the strip should go and load this file with `defer`. */
(function () {
  "use strict";
  var host = document.getElementById("provenance");
  if (!host) return;
  var css = ".prov{display:flex;flex-wrap:wrap;gap:4px 14px;align-items:center;margin:0 0 16px;padding:8px 12px;border:1px solid var(--edge);border-radius:6px;background:var(--panel);font:13px/1.4 var(--sans);color:var(--muted)}" +
    ".prov b{color:var(--text);font-weight:600}.prov .beta{color:var(--warn);font-weight:600;text-transform:uppercase;letter-spacing:.04em;font-size:12px}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  fetch("data-version.json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (v) {
    if (!v) return;
    function part(html) { var s = document.createElement("span"); s.innerHTML = html; return s; }
    var strip = document.createElement("div");
    strip.className = "prov";
    strip.setAttribute("role", "note");
    strip.appendChild(part("Client <b>" + v.client + "</b>"));
    strip.appendChild(part("updated <b>" + v.updated + "</b>"));
    if (host.hasAttribute("data-plan") && v.plan) {
      var ok = v.plan.steps - v.plan.unverified;
      strip.appendChild(part("<b>" + ok + "</b> verified / <b>" + v.plan.unverified + "</b> unverified (across all races and classes)"));
    }
    if (v.state) strip.appendChild(part('<span class="beta">' + v.state + "</span>"));
    host.appendChild(strip);
  }).catch(function () { /* the pages work without the strip */ });
})();
