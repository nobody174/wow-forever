#!/usr/bin/env node
// Launch-day rehearsal: opens the real pages in headless Chrome with a faked clock and checks what a visitor would see.
//
//   node tools/rehearse.js              everything (about 3 minutes)
//   node tools/rehearse.js --quick      pages, countdown and 4 plans only
//   node tools/rehearse.js --only plans (pages | countdown | plans | night | bis | home | a11y)
//   CHROME=/path/to/chrome node tools/rehearse.js     when Chrome is not found in the usual places
//
// How: a tiny local server serves this folder and, for HTML pages only, injects a script before the page's own scripts. The
// script (1) moves the clock when the URL has __now=<ISO time>, (2) records script errors, failed resource loads and failed
// fetches, (3) runs a small read-only probe (named by __probe=...) and leaves the answer on <html data-r2f-probe>. Chrome
// prints the final DOM (--dump-dom) and this file reads those two attributes. Nothing in the pages is changed on disk.
//
// Checks (each names the page / plan that failed):
//   pages      every page loads, no script error, has a title, and the same top bar links
//   countdown  index.html at T-2d3h4m5s, T-1s, T+0 and T+1h shows the right tiles and then "live"; launch-plan shows the date
//   plans      all 29 launch-plan plans: each phase draws exactly the step ids tools/plan_snapshot.js resolves, no load error
//   night      launch night mode (?mode=night): only the night phase shows, with its steps
//   bis        Mr.BiZ: every one of the 27 specs draws rows and the new panels
//   home       Home: the start-here steps, the saved-plan link (also with broken storage), no overlap from 800px to 1920px
//   a11y       accessibility audit of every page on desktop and phone (names, labels, alt, contrast, tap size, landmarks);
//              add --report to list every finding instead of failing on them
// Exit code 1 when anything failed. External resources (YouTube, Wowhead ...) are ignored: only this site's own files count.

const fs = require("fs");
const os = require("os");
const path = require("path");
const http = require("http");
const { spawn, execFileSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const args = process.argv.slice(2);
const QUICK = args.includes("--quick");
const ONLY = args.includes("--only") ? args[args.indexOf("--only") + 1] : null;
const TARGET = Date.parse("2026-11-04T23:00:00Z");
const CONCURRENCY = Math.max(1, Math.min(6, os.cpus().length - 1));

function findChrome() {
  const cands = [process.env.CHROME,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser"];
  for (const c of cands) if (c && fs.existsSync(c)) return c;
  throw new Error("Chrome not found: set CHROME=/path/to/chrome");
}

// --- the probes: small read-only functions run inside the page ---------------------------------------------------------------
const PROBES = {
  basic: `function () {
    var nav = Array.prototype.map.call(document.querySelectorAll(".topbar nav a"), function (a) { return a.getAttribute("href"); });
    var h1 = document.querySelector("h1");
    var st = document.getElementById("status");
    return { title: document.title, h1: h1 ? h1.textContent.trim() : "", nav: nav, textLen: document.body.innerText.length,
      dataNote: st && /Couldn.t load/.test(st.textContent) ? st.textContent.trim().slice(0, 80) : "" };
  }`,
  countdown: `function () {
    var tiles = Array.prototype.map.call(document.querySelectorAll("#countdown .tile .num"), function (n) { return n.textContent; });
    var live = document.querySelector("#countdown .live-msg");
    var ribbon = !!document.querySelector(".beta-ribbon");
    return { tiles: tiles, live: live ? live.textContent.trim() : "", ribbon: ribbon, local: document.getElementById("local-time").textContent };
  }`,
  home: `function () {
    var hc = document.querySelector(".hero-content").getBoundingClientRect(), sl = document.querySelector(".side-links").getBoundingClientRect();
    var st = document.querySelector(".start"), steps = Array.prototype.map.call(document.querySelectorAll(".start ol a"), function (a) { return a.getAttribute("href"); });
    var cont = document.getElementById("start-continue");
    var overlap = !(hc.right <= sl.left || hc.left >= sl.right || hc.bottom <= sl.top || hc.top >= sl.bottom);
    var cr = document.querySelector(".start").getBoundingClientRect();
    return { w: innerWidth, steps: steps, startVisible: !!st && st.getBoundingClientRect().height > 0,
      contHidden: cont.hidden, contBox: cont.getBoundingClientRect().width, contText: cont.textContent, overlap: overlap, heroTop: hc.top, sideTop: sl.top, heroLeft: hc.left, heroRight: hc.right,
      sideRight: sl.right, startRight: cr.right, vw: innerWidth, hScroll: document.documentElement.scrollWidth > innerWidth + 1 };
  }`,
  launchplan: `function () {
    var out = {};
    document.querySelectorAll(".phase[data-phase]").forEach(function (p) {
      out[p.getAttribute("data-phase")] = Array.prototype.map.call(p.querySelectorAll("ul.check input[data-id]"), function (i) { return i.getAttribute("data-id"); });
    });
    var failed = /could not be loaded/.test(document.body.innerText);
    var visible = 0;
    document.querySelectorAll("ul.check input[data-id]").forEach(function (i) { if (i.offsetParent !== null) visible++; });
    var lvl = document.getElementById("pick-level");
    var prov = document.getElementById("provenance");
    return { phases: out, failed: failed, night: document.body.classList.contains("night"), visible: visible,
      level: !!lvl, prov: prov ? prov.textContent.trim() : "", chip: (document.getElementById("launch-chip") || {}).textContent || "",
      nowbar: !!document.getElementById("now-bar") };
  }`,
  a11y: `function () {
    var out = { vw: innerWidth, noName: [], noAlt: [], noLabel: [], contrast: [], small: [], misc: [] };
    function vis(e) { var r = e.getBoundingClientRect(); var cs = getComputedStyle(e); return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none"; }
    function sel(e) { var s = e.tagName.toLowerCase(); if (e.id) s += "#" + e.id; else if (e.className && typeof e.className === "string") s += "." + e.className.trim().split(/\\s+/).slice(0, 2).join("."); return s; }
    function text(e) { return (e.getAttribute("aria-label") || e.getAttribute("title") || e.textContent || "").trim().replace(/\\s+/g, " "); }
    // accessible name of a control: aria-label / aria-labelledby / text / title / alt of an inner image
    function name(e) {
      var n = e.getAttribute("aria-label"); if (n && n.trim()) return n;
      var by = e.getAttribute("aria-labelledby"); if (by) { var t = by.split(" ").map(function (i) { var x = document.getElementById(i); return x ? x.textContent : ""; }).join(" ").trim(); if (t) return t; }
      var t2 = (e.textContent || "").trim(); if (t2) return t2;
      var img = e.querySelector("img[alt]"); if (img && img.alt.trim()) return img.alt;
      var svg = e.querySelector("svg title"); if (svg && svg.textContent.trim()) return svg.textContent;
      return (e.getAttribute("title") || "").trim();
    }
    document.querySelectorAll("a[href], button, [role=button], summary").forEach(function (e) {
      if (!vis(e)) return;
      if (!name(e)) out.noName.push(sel(e) + " " + (e.getAttribute("href") || ""));
    });
    document.querySelectorAll("img").forEach(function (e) { if (!e.hasAttribute("alt")) out.noAlt.push(sel(e) + " " + (e.getAttribute("src") || "").slice(0, 50)); });
    document.querySelectorAll("input:not([type=hidden]), select, textarea").forEach(function (e) {
      if (!vis(e) && e.type !== "checkbox" && e.type !== "radio") return;
      var lab = e.getAttribute("aria-label") || e.getAttribute("aria-labelledby") || e.getAttribute("title") || (e.id && document.querySelector('label[for="' + e.id + '"]')) || e.closest("label") || e.getAttribute("placeholder");
      if (!lab) out.noLabel.push(sel(e));
    });
    // contrast of text on a flat background (gradients / images are skipped: unknown)
    function rgba(c) { var m = c.match(/rgba?\\(([^)]+)\\)/); if (!m) return null; var p = m[1].split(/[ ,\\/]+/).filter(Boolean).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; }
    function lum(c) { function f(v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); } return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); }
    function bgOf(e) {
      var layers = [], er = e.getBoundingClientRect();
      for (var n = e; n && n.nodeType === 1; n = n.parentElement) {
        var nr = n.getBoundingClientRect();
        if (n !== e && (er.left < nr.left - 1 || er.right > nr.right + 1 || er.top < nr.top - 1 || er.bottom > nr.bottom + 1)) continue; // hangs outside this box
        var cs = getComputedStyle(n);
        if (cs.backgroundImage !== "none") return null;
        var c = rgba(cs.backgroundColor);
        if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; }
      }
      var base = { r: 11, g: 15, b: 30, a: 1 };
      var bg = layers.length && layers[layers.length - 1].a >= 1 ? layers.pop() : (rgba(getComputedStyle(document.body).backgroundColor) || base);
      if (bg.a < 1) bg = { r: 11, g: 15, b: 30, a: 1 };
      while (layers.length) { var t = layers.pop(); bg = { r: t.r * t.a + bg.r * (1 - t.a), g: t.g * t.a + bg.g * (1 - t.a), b: t.b * t.a + bg.b * (1 - t.a), a: 1 }; }
      return bg;
    }
    var seen = {};
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    var node;
    while ((node = walker.nextNode())) {
      var tx = node.nodeValue.trim(); if (tx.length < 2) continue;
      var el = node.parentElement; if (!el || /^(SCRIPT|STYLE|NOSCRIPT)$/.test(el.tagName) || !vis(el)) continue;
      if (el.closest("[disabled], [aria-disabled=true]")) continue; // inactive controls are exempt (WCAG 1.4.3)
      var cs = getComputedStyle(el), fg = rgba(cs.color), bg = bgOf(el);
      if (!fg || !bg) continue;
      var op = 1; for (var q = el; q && q.nodeType === 1; q = q.parentElement) op *= parseFloat(getComputedStyle(q).opacity);
      if (op < 0.99) { fg = { r: fg.r * fg.a * op + bg.r * (1 - fg.a * op), g: fg.g * fg.a * op + bg.g * (1 - fg.a * op), b: fg.b * fg.a * op + bg.b * (1 - fg.a * op), a: 1 }; }
      else if (fg.a < 1) fg = { r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a), b: fg.b * fg.a + bg.b * (1 - fg.a), a: 1 };
      var L1 = lum(fg), L2 = lum(bg), ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
      var size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight, 10) >= 700;
      var need = size >= 24 || (size >= 18.66 && bold) ? 3 : 4.5;
      if (ratio < need) { var key = sel(el) + "|" + cs.color + "|" + cs.backgroundColor; if (!seen[key]) { seen[key] = 1; out.contrast.push(ratio.toFixed(2) + " (<" + need + ") " + sel(el) + " '" + tx.slice(0, 28) + "' " + cs.color); } }
    }
    // controls smaller than 24 x 24 CSS px (WCAG 2.2 AA 2.5.8; links inside a sentence are exempt)
    document.querySelectorAll("button, [role=button], summary, input:not([type=hidden]), select, nav a, .topbar a, .site-foot nav a, a.btn, a.pill, a.chip").forEach(function (e) {
      if (!vis(e) || e.disabled || e.getAttribute("aria-disabled") === "true") return;
      var box = e;
      // a checkbox / radio inside a label is tapped through the whole label
      if ((e.type === "checkbox" || e.type === "radio") && e.closest("label")) box = e.closest("label");
      var r = box.getBoundingClientRect();
      if (r.width < 24 || r.height < 24) out.small.push(Math.round(r.width) + "x" + Math.round(r.height) + " " + sel(e) + " '" + text(box).slice(0, 20) + "'");
    });
    if (!document.documentElement.lang) out.misc.push("no <html lang>");
    if (!document.querySelector("main, [role=main]")) out.misc.push("no <main> landmark");
    var h1s = document.querySelectorAll("h1").length; if (h1s !== 1) out.misc.push(h1s + " <h1> elements");
    var prev = 0; document.querySelectorAll("h1,h2,h3,h4,h5,h6").forEach(function (h) { var l = +h.tagName[1]; if (prev && l > prev + 1 && vis(h)) out.misc.push("heading jumps h" + prev + " to h" + l + " '" + text(h).slice(0, 24) + "'"); prev = l; });
    if (!document.querySelector("meta[name=viewport]")) out.misc.push("no viewport meta");
    document.querySelectorAll("a[target=_blank]").forEach(function (a) { if (!/noopener/.test(a.rel)) out.misc.push("target=_blank without noopener: " + (a.getAttribute("href") || "").slice(0, 50)); });
    return out;
  }`,
  bis: `function () {
    var rows = document.querySelectorAll("#rows .row");
    var empty = document.querySelectorAll("#rows .row.empty").length;
    var w = document.getElementById("weights");
    var chips = w ? w.querySelectorAll(".chip, .wchip, span").length : 0;
    var title = (document.querySelector("#rows .row .nm") || {}).textContent || "";
    return { rows: rows.length, empty: empty, weightsHidden: w ? w.hidden : null, chips: chips, firstItem: title,
      sum: (document.getElementById("sum") || {}).textContent || "", provenance: !!document.getElementById("provenance") };
  }`,
};

function shimFor(url) {
  const now = url.searchParams.get("__now");
  // __js=<function source> runs an ad-hoc probe (for looking at one thing in a page; local server only)
  const probe = url.searchParams.get("__js") || PROBES[url.searchParams.get("__probe")];
  return `<script>(function(){
  var errs=[];
  function add(m){errs.push(String(m).slice(0,300));try{document.documentElement.setAttribute("data-r2f-errors",JSON.stringify(errs));}catch(e){}}
  window.addEventListener("error",function(e){
    var t=e.target;
    if(t&&t!==window&&(t.src||t.href)){ if((t.src||t.href).indexOf(location.origin)===0) add("load failed: "+(t.src||t.href)); }
    else if(e.message==="Script error."&&!e.filename){ /* a third-party script (Wowhead data): the browser hides the details */ }
    else add("error: "+e.message+" @"+(e.filename||"").replace(location.origin,"")+":"+e.lineno);
  },true);
  window.addEventListener("unhandledrejection",function(e){add("rejection: "+(e.reason&&e.reason.message||e.reason));});
  var ce=console.error;console.error=function(){add("console.error: "+Array.prototype.join.call(arguments," "));ce.apply(console,arguments);};
  var f=window.fetch;
  if(f)window.fetch=function(u){var s=String(u&&u.url||u);var own=s.indexOf("http")!==0||s.indexOf(location.origin)===0;
    return f.apply(this,arguments).then(function(r){if(own&&!r.ok)add("fetch "+r.status+": "+s);return r;},function(e){if(own)add("fetch failed: "+s);throw e;});};
  ${url.searchParams.get("__ls") ? `try{var seed=${url.searchParams.get("__ls")};Object.keys(seed).forEach(function(k){localStorage.setItem(k,seed[k]);});}catch(e){}` : ""}
  ${url.searchParams.get("__probe") === "a11y" ? `document.addEventListener("DOMContentLoaded",function(){var st=document.createElement("style");st.textContent="*,*::before,*::after{transition:none!important;animation:none!important}";document.head.appendChild(st);});` : ""}
  ${now ? `var RD=Date,off=${Date.parse(now)}-RD.now();
  window.Date=class extends RD{constructor(...a){if(a.length===0)super(RD.now()+off);else super(...a);}static now(){return RD.now()+off;}};` : ""}
  ${probe ? `setTimeout(function(){try{document.documentElement.setAttribute("data-r2f-probe",JSON.stringify((${probe})()));}catch(e){add("probe: "+e.message);}},4000);` : ""}
})();</script>`;
}

const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".json": "application/json", ".css": "text/css",
  ".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".webmanifest": "application/manifest+json",
  ".md": "text/plain; charset=utf-8", ".tga": "application/octet-stream", ".ico": "image/x-icon" };

function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const url = new URL(req.url, "http://localhost");
      let p = decodeURIComponent(url.pathname);
      if (p.endsWith("/")) p += "index.html";
      const file = path.join(ROOT, p);
      if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end("not found"); return; }
      const ext = path.extname(file).toLowerCase();
      res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream", "Cache-Control": "no-store" });
      if (ext === ".html") {
        const html = fs.readFileSync(file, "utf8");
        res.end(html.replace(/<head[^>]*>/i, (m) => m + shimFor(url)));
      } else fs.createReadStream(file).pipe(res);
    });
    srv.listen(0, "127.0.0.1", () => resolve(srv));
  });
}

// --- running one page in Chrome ---------------------------------------------------------------------------------------------
const CHROME = findChrome();
function unescapeAttr(s) { return s.replace(/&quot;/g, '"').replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&#39;/g, "'").replace(/&amp;/g, "&"); }

// Chrome sometimes starts slowly when six run at once and the probe fires before the page finished; run again (up to 3 tries)
// when a probe was asked for and did not come back. A page whose script is really broken still ends without a probe.
async function runPage(base, relUrl, opts) {
  let r;
  for (let tries = 0; tries < 3; tries++) {
    r = await runPageOnce(base, relUrl, opts);
    if (r.probe || relUrl.indexOf("__probe=") === -1) break;
  }
  if (relUrl.indexOf("__probe=") !== -1 && !r.probe) r.errors = (r.errors || []).concat(["no probe answer after 3 tries (the page did not finish drawing)"]);
  return r;
}

function runPageOnce(base, relUrl, opts) {
  opts = opts || {};
  return new Promise((resolve) => {
    const prof = fs.mkdtempSync(path.join(os.tmpdir(), "r2f-rehearse-"));
    const size = opts.width ? opts.width + ",900" : opts.mobile ? "390,844" : "1280,900";
    const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run", "--disable-extensions",
      "--user-data-dir=" + prof, "--window-size=" + size, "--virtual-time-budget=7000", "--dump-dom", base + relUrl],
      { stdio: ["ignore", "pipe", "pipe"] });
    let out = "";
    chrome.stdout.on("data", (d) => { out += d; });
    chrome.stderr.on("data", () => {});
    const timer = setTimeout(() => chrome.kill("SIGKILL"), 60000);
    chrome.on("close", () => {
      clearTimeout(timer);
      try { fs.rmSync(prof, { recursive: true, force: true }); } catch (e) { /* the profile folder can stay locked for a moment on Windows */ }
      const get = (name) => { const m = out.match(new RegExp(name + '="([^"]*)"')); return m ? JSON.parse(unescapeAttr(m[1])) : null; };
      resolve({ html: out, errors: get("data-r2f-errors") || [], probe: get("data-r2f-probe"), empty: out.length < 200 });
    });
  });
}

async function pool(tasks) {
  const results = new Array(tasks.length);
  let next = 0;
  async function worker() { while (next < tasks.length) { const i = next++; results[i] = await tasks[i](); } }
  await Promise.all(Array.from({ length: CONCURRENCY }, worker));
  return results;
}

// --- the checks -------------------------------------------------------------------------------------------------------------
let failures = 0, checks = 0;
function check(ok, msg) { checks++; if (!ok) { failures++; console.log("FAIL  " + msg); } }
function section(name) { console.log("\n== " + name); }
function want(name) { return !ONLY || ONLY === name; }
function noErrors(r, label) {
  check(!r.empty, label + ": the page rendered");
  (r.errors || []).forEach((e) => check(false, label + ": " + e));
  if (!(r.errors || []).length) check(true, label);
}

async function main() {
  const srv = await serve();
  const base = "http://127.0.0.1:" + srv.address().port + "/";
  console.log("Chrome: " + CHROME + " | " + CONCURRENCY + " at a time | server " + base);
  if (args.includes("--eval")) {
    // node tools/rehearse.js --eval "bis.html#hunter/survival" "function(){ return document.title; }" [--mobile]
    const i = args.indexOf("--eval"), target = args[i + 1], js = args[i + 2];
    const [pg, hash] = target.split("#");
    const r = await runPage(base, pg + (pg.includes("?") ? "&" : "?") + "__js=" + encodeURIComponent(js) + (hash ? "#" + hash : ""), { mobile: args.includes("--mobile") });
    console.log(JSON.stringify(r.probe, null, 1));
    if (r.errors.length) console.log("errors: " + r.errors.join(" | "));
    srv.close(); return;
  }
  const snap = JSON.parse(execFileSync("node", [path.join(ROOT, "tools", "plan_snapshot.js"), "--steps", path.join(ROOT, "launch-plan-steps.json")],
    { maxBuffer: 64 * 1024 * 1024 }).toString());
  const plans = Object.keys(snap.plans);

  if (want("pages")) {
    section("pages load without errors");
    const pages = fs.readdirSync(ROOT).filter((f) => f.endsWith(".html") && f !== "template.html").sort();
    const rs = await pool(pages.map((p) => () => runPage(base, p + "?__probe=basic")));
    let navRef = null;
    pages.forEach((p, i) => {
      const r = rs[i];
      noErrors(r, p);
      const b = r.probe || {};
      check(b.title && b.title.length > 3, p + ": has a title");
      check((b.textLen || 0) > 300, p + ": shows content (" + (b.textLen || 0) + " characters)");
      if (b.dataNote) console.log("NOTE  " + p + ": the live Wowhead data did not load here (needs a network): " + b.dataNote);
      if (b.nav) {
        const key = b.nav.join("|");
        if (navRef === null) navRef = key;
        check(key === navRef, p + ": top bar links match the other pages");
      }
    });
  }

  if (want("countdown")) {
    section("countdown around the launch");
    const at = (ms) => new Date(TARGET + ms).toISOString();
    const cases = [
      { ms: -(2 * 864e5 + 3 * 36e5 + 4 * 6e4 + 5e3), tiles: ["02", "03", "04", "05"], live: false, label: "T-2d 3h 4m 5s" },
      { ms: -36e5, tiles: ["00", "00", "59"], live: false, label: "T-1h" },
      { ms: -1000, tiles: [], live: true, label: "T-1s (the page is open for ~4s, so it flips to live by itself)" },
      { ms: 0, tiles: [], live: true, label: "T+0" },
      { ms: 36e5, tiles: [], live: true, label: "T+1h" },
    ];
    const rs = await pool(cases.map((c) => () => runPage(base, "index.html?__probe=countdown&__now=" + encodeURIComponent(at(c.ms)))));
    cases.forEach((c, i) => {
      const r = rs[i], p = r.probe || {};
      noErrors(r, "index at " + c.label);
      if (c.live) check(/live/i.test(p.live || ""), "index at " + c.label + ": shows the live message (got '" + (p.live || "") + "')");
      else {
        // the page ticks once per second and the probe runs ~4s in, so the seconds tile is not checked and minutes can be one lower than the start
        const t = p.tiles || [];
        check(t.length === 4, "index at " + c.label + ": four tiles (got " + t.length + ")");
        check(t.slice(0, 3).join() === c.tiles.slice(0, 3).join(), "index at " + c.label + ": days/hours/minutes " + c.tiles.slice(0, 3).join(":") + " (got " + t.join(":") + ")");
        check(!p.live, "index at " + c.label + ": not live yet");
      }
      // Before launch the page shows the launch time in the visitor's time; once live it clears that line (and hides the launch-night link).
      if (c.live) check(!p.local, "index at " + c.label + ": the launch-time line is cleared once live (got '" + (p.local || "") + "')");
      else check(!!p.local && /Launches/.test(p.local), "index at " + c.label + ": shows the launch time in the visitor's time (got '" + (p.local || "") + "')");
      check(!p.ribbon, "index at " + c.label + ": no Beta ribbon");
    });
    const lp = await runPage(base, "launch-plan.html?__probe=launchplan&__now=" + encodeURIComponent(at(0)));
    noErrors(lp, "launch-plan after launch");
    check(/Launch:/.test((lp.probe || {}).chip || ""), "launch-plan: the launch chip shows the date");
  }

  if (want("plans")) {
    section("launch plan: all " + plans.length + " plans draw what the data says");
    const list = QUICK ? plans.filter((_, i) => i % 8 === 0) : plans;
    const urlFor = (id) => id.includes(":") ? "race=" + id.split(":")[0] + "&class=" + id.split(":")[1].toLowerCase() : "plan=" + id;
    const rs = await pool(list.map((id) => () => runPage(base, "launch-plan.html?" + urlFor(id) + "&__probe=launchplan")));
    list.forEach((id, i) => {
      const r = rs[i], p = r.probe || {};
      noErrors(r, "plan " + id);
      check(p.failed === false, "plan " + id + ": the steps loaded");
      check(p.level && p.nowbar, "plan " + id + ": level box and Now/Next bar are there");
      let drawn = 0, bad = [];
      snap.phases.forEach((ph) => {
        const want = snap.plans[id][ph].map((s) => s.id), got = (p.phases || {})[ph] || [];
        drawn += got.length;
        if (want.join() !== got.join()) bad.push(ph + " (want " + want.length + ", drew " + got.length + ")");
      });
      check(bad.length === 0, "plan " + id + ": every phase draws its steps in order" + (bad.length ? " | " + bad.join(", ") : " (" + drawn + " steps)"));
      check(/across all races and classes|steps/i.test(p.prov || "") || (p.prov || "").length > 0, "plan " + id + ": data-as-of strip shows");
    });
  }

  if (want("night")) {
    section("launch night mode");
    for (const id of QUICK ? ["hunter"] : ["hunter", "human:PRIEST", "gnome:MAGE"]) {
      const q = id.includes(":") ? "race=" + id.split(":")[0] + "&class=" + id.split(":")[1].toLowerCase() : "plan=" + id;
      const r = await runPage(base, "launch-plan.html?" + q + "&mode=night&__probe=launchplan", { mobile: true });
      const p = r.probe || {};
      noErrors(r, "night " + id);
      check(p.night === true, "night " + id + ": body is in night mode");
      const nightSteps = ((snap.plans[id] || snap.plans["skyborne:HUNTER"]).night || []).length;
      check(p.visible === nightSteps || (id === "hunter" && p.visible > 0), "night " + id + ": only the night steps are visible (" + p.visible + " of " + nightSteps + ")");
    }
  }

  if (want("home")) {
    section("Home: start here, continue link, no overlap");
    const q = (ls) => "index.html?__probe=home" + (ls ? "&__ls=" + encodeURIComponent(JSON.stringify(ls)) : "");
    const fresh = await runPage(base, q(), { width: 1280 });
    noErrors(fresh, "home (fresh browser)");
    let p = fresh.probe || {};
    check(p.startVisible && p.steps.join() === "launch-plan.html,builds.html,addons.html", "home: the three steps show and point at the plan, builds and addons (" + (p.steps || []).join() + ")");
    check(p.contHidden === true && p.contBox === 0, "home: no continue link (and no empty box) in a fresh browser");
    const saved = await runPage(base, q({ "wf-launch-plan-sel": JSON.stringify("nightelf:DRUID"), "wf-launch-plan-level": "14" }), { width: 1280 });
    noErrors(saved, "home (saved plan)");
    p = saved.probe || {};
    check(p.contHidden === false && p.contText === "Continue your plan: Night Elf Druid, level 14 →", "home: continue link names the saved plan and level (got '" + p.contText + "')");
    const duo = await runPage(base, q({ "wf-launch-plan-sel": JSON.stringify("hunter") }), { width: 1280 });
    p = duo.probe || {};
    check(p.contHidden === false && p.contText === "Continue your plan: 2 Hunters →", "home: the 2 Hunters preset reads right (got '" + p.contText + "')");
    for (const junk of [{ "wf-launch-plan-sel": "{bad" }, { "wf-launch-plan-sel": JSON.stringify("elf:WIZARD") }, { "wf-launch-plan-sel": "null" }, { "wf-launch-plan-sel": JSON.stringify("human:MAGE"), "wf-launch-plan-level": "abc" }]) {
      const r = await runPage(base, q(junk), { width: 1280 });
      noErrors(r, "home (storage " + JSON.stringify(junk) + ")");
      p = r.probe || {};
      const okJunk = junk["wf-launch-plan-level"] ? p.contText === "Continue your plan: Human Mage →" : p.contHidden === true;
      check(okJunk, "home: odd saved values never break the page or show a wrong plan (" + JSON.stringify(junk) + " -> '" + p.contText + "')");
    }
    for (const w of [800, 1024, 1180, 1280, 1366, 1440, 1536, 1920]) {
      const r = await runPage(base, q(), { width: w });
      noErrors(r, "home at " + w + "px");
      p = r.probe || {};
      check(p.overlap === false, "home at " + w + "px: the title block does not touch the side panels");
      check(p.startRight <= p.vw + 1 && p.heroRight <= p.vw + 1, "home at " + w + "px: nothing runs off the right edge");
      check(p.hScroll === false, "home at " + w + "px: no sideways scrolling");
    }
    const ph = await runPage(base, q(), { width: 504 });
    p = ph.probe || {};
    check(p.heroTop < p.sideTop, "home on a phone: the title and countdown come before the link lists");
    check(p.hScroll === false, "home on a phone: no sideways scrolling");
  }

  if (want("a11y")) {
    section("accessibility audit (desktop and 390px phone)");
    const pages = fs.readdirSync(ROOT).filter((f) => f.endsWith(".html") && f !== "template.html").sort();
    const jobs = [];
    pages.forEach((pg) => [false, true].forEach((mobile) => jobs.push({ pg, mobile })));
    const rs = await pool(jobs.map((j) => () => runPage(base, j.pg + "?__probe=a11y", { mobile: j.mobile })));
    jobs.forEach((j, i) => {
      const r = rs[i], p = r.probe || {}, label = j.pg + (j.mobile ? " (phone)" : "");
      noErrors(r, label);
      if (j.mobile) check(p.vw <= 520, label + ": the phone viewport is narrow (" + p.vw + "px; Chrome's smallest headless window)");
      for (const k of ["noName", "noAlt", "noLabel", "misc", "contrast", "small"]) {
        const list = p[k] || [];
        if (args.includes("--report")) list.forEach((x) => console.log("      " + label + " " + k + ": " + x));
        else check(list.length === 0, label + ": " + k + " | " + list.slice(0, 4).join(" ; ") + (list.length > 4 ? " ... +" + (list.length - 4) : ""));
      }
    });
  }

  if (want("bis")) {
    section("Mr.BiZ: every spec");
    const specs = Object.keys(JSON.parse(fs.readFileSync(path.join(ROOT, "bis-data.json"), "utf8")).specs);
    const list = QUICK ? specs.slice(0, 3) : specs;
    const rs = await pool(list.map((s) => () => runPage(base, "bis.html?__probe=bis#" + s)));
    list.forEach((s, i) => {
      const r = rs[i], p = r.probe || {};
      noErrors(r, "bis " + s);
      check(p.rows >= 15, "bis " + s + ": draws the slot rows (" + p.rows + ")");
      check(p.weightsHidden === false && p.chips > 0, "bis " + s + ": stat weights panel shows");
      check(!!p.firstItem, "bis " + s + ": the first row names an item");
    });
  }

  srv.close();
  console.log("\n" + (failures ? failures + " FAILED of " : "all passed: ") + checks + " checks");
  process.exit(failures ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(2); });
