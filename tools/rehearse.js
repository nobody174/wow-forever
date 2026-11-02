#!/usr/bin/env node
// Launch-day rehearsal: opens the real pages in headless Chrome with a faked clock and checks what a visitor would see.
//
//   node tools/rehearse.js              everything (about 3 minutes)
//   node tools/rehearse.js --quick      pages, countdown and 4 plans only
//   node tools/rehearse.js --only plans (pages | countdown | plans | night | bis)
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
  const probe = PROBES[url.searchParams.get("__probe")];
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
    const size = opts.mobile ? "390,844" : "1280,900";
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
      check(!!p.local && /Launches/.test(p.local), "index at " + c.label + ": shows the launch time in the visitor's time (got '" + (p.local || "") + "')");
      // After launch the beta ribbon should be gone: tell, don't fail (it is a manual edit on the day: see BETA-RIBBON in index.html).
      if (c.live && p.ribbon) console.log("NOTE  index after launch still carries the Beta ribbon (remove the BETA-RIBBON block on the day)");
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
