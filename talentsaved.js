/* =============================================================================
   Saved builds sidebar (talents.html + builds.html). Load after talentcalc.js.

   Two lists in one right-hand drawer:
     - My builds:   saved in this browser (localStorage "wf-talent-builds-v1").
                    Save from any calculator's "Save build" button, or import a
                    talents.html link a friend pasted in chat.
     - Group picks: the GROUP_PICKS array below, shipped with the site so the
                    whole group sees the same suggestions. Each entry has a
                    share `code` ("hunter/0502...") or a `preset` by talent name
                    (resolved against Wowhead's data at runtime). "Copy as group
                    pick" on a saved build produces a ready-to-paste entry.

   API: TalentSaved.open(tab?)  TalentSaved.openSave(calcInstance, defaultName?)
   ============================================================================= */
(function () {
  "use strict";

  // --- Group picks (edit here) ------------------------------------------------
  // { cls, name, by, note, code: "<class>/<t1>-<t2>-<t3>" }  or  { ..., preset: [[talentName, rank], ...] }
  var GROUP_PICKS = [
    { cls: "hunter", name: "Hunter — Beast Mastery (level 20)", by: "Builds page",
      note: "Leveling start for all our Hunters (2 Hunters · Warrior · Druid and 3 Hunters · Druid plans).",
      preset: [["Deadly Aspects", 5], ["Focused Fire", 2], ["Pathfinding", 2], ["Improved Revive Pet", 1], ["Bestial Swiftness", 1]] },
    { cls: "warrior", name: "Warrior — Tank (level 20)", by: "Builds page",
      note: "Tank start for the 2 Hunters · Warrior · Druid plan. Pre-Shield Slam, Rend-centric.",
      preset: [["Improved Rend", 3], ["Deflection", 2], ["Improved Tactical Mastery", 5], ["Anger Management", 1]] }
  ];

  var KEY = "wf-talent-builds-v1", TAB_KEY = "wf-talent-builds-tab", ACTIVE_KEY = "wf-talent-builds-active";
  var TC = window.TalentCalc;
  if (!TC) return;

  function load(k, d) { try { var v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } }
  function sGet(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } }
  function sSet(k, v) { try { if (v) sessionStorage.setItem(k, v); else sessionStorage.removeItem(k); } catch (e) { /* blocked */ } }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function uid() { return "b" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }
  function link(code) { return new URL("talents.html#" + code, location.href).href; }
  function clsOf(code) { return TC.classById(String(code).split("/")[0]); }

  var builds = load(KEY, []);
  if (!Array.isArray(builds)) builds = [];
  var tab = load(TAB_KEY, "mine") === "group" ? "group" : "mine";
  var raw = null, pending = null, editing = null, flash = null, lastFocus = null;

  // A share code's points per tree, without Wowhead data ("0502-05" -> [7,5,0]).
  function splitOf(code) {
    var parts = String(code).split("/")[1] || "";
    return [0, 1, 2].map(function (i) { return (parts.split("-")[i] || "").split("").reduce(function (a, d) { return a + (+d || 0); }, 0); });
  }
  function treeName(cls, split) { var m = 0; split.forEach(function (n, i) { if (n > split[m]) m = i; }); return split[m] ? cls.trees[m][1] : "Empty"; }
  function metaLine(code) {
    var cls = clsOf(code), sp = splitOf(code), n = sp[0] + sp[1] + sp[2];
    if (!cls) return "";
    return esc(treeName(cls, sp)) + " · " + sp.join("/") + (n ? " · level " + (n + 9) : "");
  }

  // --- DOM -----------------------------------------------------------------------
  var fab = document.createElement("button");
  fab.type = "button";
  fab.className = "ts-fab";
  fab.setAttribute("aria-haspopup", "dialog");
  fab.setAttribute("aria-controls", "ts-drawer");
  fab.innerHTML = 'Saved builds <span class="ts-count" id="ts-count"></span>';
  var overlay = document.createElement("div");
  overlay.className = "ts-overlay";
  var drawer = document.createElement("aside");
  drawer.className = "ts-drawer";
  drawer.id = "ts-drawer";
  drawer.setAttribute("role", "dialog");
  drawer.setAttribute("aria-modal", "true");
  drawer.setAttribute("aria-labelledby", "ts-title");
  drawer.setAttribute("aria-hidden", "true");
  drawer.innerHTML =
    '<div class="ts-head"><div class="ts-row"><h3 id="ts-title">Saved builds</h3>' +
    '<button class="ts-close" type="button" aria-label="Close">&times;</button></div>' +
    '<p>Keep your own talent builds here, and look up the builds we suggest for the group.</p>' +
    '<div class="ts-tabs" role="group" aria-label="List"><button type="button" data-tab="mine">My builds <span data-n="mine"></span></button>' +
    '<button type="button" data-tab="group">Group picks <span data-n="group"></span></button></div></div>' +
    '<div class="ts-body" id="ts-body"></div>';
  document.body.appendChild(fab);
  document.body.appendChild(overlay);
  document.body.appendChild(drawer);
  var body = drawer.querySelector("#ts-body");

  // Sit just under the sticky top bar, like the Buyable quests button.
  function placeFab() {
    var bar = document.querySelector(".topbar");
    if (bar) document.documentElement.style.setProperty("--topbar-h", bar.offsetHeight + "px");
  }
  placeFab();
  window.addEventListener("resize", placeFab);

  // --- Rendering -----------------------------------------------------------------
  function cardHTML(b, kind) {
    var cls = clsOf(b.code) || { name: "?", color: "#9AA0B8", id: "" };
    var head = '<div class="ts-card-top"><img class="ts-icon" src="' + TC.ICON + "classicon_" + cls.id + '.jpg" alt="" loading="lazy">' +
      '<div><div class="ts-name">' + esc(b.name) + "</div>" + '<div class="ts-meta">' + metaLine(b.code) +
      (kind === "group" && b.by ? " · " + esc(b.by) : "") + "</div></div></div>";
    if (kind === "mine" && editing === b.id) {
      return '<div class="ts-card ts-editing" style="--c:' + cls.color + '" data-id="' + b.id + '">' + head +
        '<label class="ts-lbl">Name<input type="text" maxlength="80" data-f="name" value="' + esc(b.name) + '"></label>' +
        '<label class="ts-lbl">Note<textarea rows="3" maxlength="600" data-f="note" placeholder="Why this build, when to use it…">' + esc(b.note) + "</textarea></label>" +
        '<div class="ts-acts"><button type="button" class="ts-btn ts-primary" data-act="edit-ok">Save</button>' +
        '<button type="button" class="ts-btn" data-act="edit-cancel">Cancel</button>' +
        '<button type="button" class="ts-btn" data-act="group-copy" title="Copy a GROUP_PICKS entry to paste into talentsaved.js">Copy as group pick</button></div></div>';
    }
    var acts = '<a class="ts-btn ts-primary" data-act="open" href="talents.html#' + esc(b.code) + '">Open</a>' +
      '<button type="button" class="ts-btn" data-act="copy">Copy link</button>' +
      (kind === "mine" ? '<button type="button" class="ts-btn" data-act="edit">Edit</button><button type="button" class="ts-btn ts-danger" data-act="del">Delete</button>' : "");
    return '<div class="ts-card' + (flash === b.id ? " ts-flash" : "") + '" style="--c:' + cls.color + '" data-id="' + esc(b.id) + '" data-kind="' + kind + '">' + head +
      (b.note ? '<p class="ts-note">' + esc(b.note) + "</p>" : "") + '<div class="ts-acts">' + acts + "</div></div>";
  }
  function grouped(list, kind) {
    var html = "";
    TC.CLASSES.forEach(function (c) {
      var mine = list.filter(function (b) { var bc = clsOf(b.code); return bc && bc.id === c.id; });
      if (!mine.length) return;
      html += '<div class="ts-group" style="--c:' + c.color + '">' + c.name + "</div>" + mine.map(function (b) { return cardHTML(b, kind); }).join("");
    });
    return html;
  }
  function saveFormHTML() {
    var inst = pending.inst, code = inst.encode(), active = sGet(ACTIVE_KEY);
    var cur = builds.filter(function (b) { return b.id === active && clsOf(b.code) && clsOf(b.code).id === inst.cls.id; })[0];
    var sp = inst.split();
    var name = pending.name || (inst.cls.name + " — " + (inst.mainTree() || "Empty") + " " + sp.join("/"));
    if (cur && !pending.name) name = cur.name;
    return '<form class="ts-save" style="--c:' + inst.cls.color + '"><div class="ts-save-h">Save this build</div>' +
      '<div class="ts-meta">' + metaLine(code) + "</div>" +
      (inst.total() ? "" : '<p class="ts-warn">No points spent yet — this saves an empty tree.</p>') +
      '<label class="ts-lbl">Name<input type="text" maxlength="80" name="name" value="' + esc(name) + '" required></label>' +
      '<label class="ts-lbl">Note <span>(optional)</span><textarea rows="3" maxlength="600" name="note" placeholder="Why this build, when to use it…">' + esc(cur ? cur.note : "") + "</textarea></label>" +
      '<div class="ts-acts">' +
      (cur ? '<button type="submit" class="ts-btn ts-primary" data-mode="update">Update “' + esc(cur.name) + '”</button><button type="submit" class="ts-btn" data-mode="new">Save as new</button>'
           : '<button type="submit" class="ts-btn ts-primary" data-mode="new">Save</button>') +
      '<button type="button" class="ts-btn" data-act="save-cancel">Cancel</button></div></form>';
  }
  function render() {
    drawer.querySelectorAll("[data-tab]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.tab === tab)); });
    drawer.querySelector('[data-n="mine"]').textContent = builds.length;
    drawer.querySelector('[data-n="group"]').textContent = GROUP_PICKS.length;
    fab.querySelector(".ts-count").textContent = builds.length;
    var html = "";
    if (tab === "mine") {
      if (pending) html += saveFormHTML();
      html += '<div class="ts-tools"><form class="ts-import"><input type="url" name="url" placeholder="Paste a talent calc link to add it" aria-label="Talent calc link">' +
        '<button type="submit" class="ts-btn">Add</button></form>' +
        (builds.length ? '<button type="button" class="ts-btn ts-ghost" data-act="copy-all">Copy all as links</button>' : "") + "</div>";
      html += builds.length ? grouped(builds, "mine")
        : '<p class="ts-empty">Nothing saved yet. Build something in the calculator and press <b>Save build</b>, or paste a link a friend sent you above.</p>';
      html += '<p class="ts-foot">Saved in this browser only. To share, use <b>Copy link</b> (or <b>Copy all as links</b>) and paste it in the group chat — whoever opens it can add it to their own list.</p>';
    } else {
      if (!raw) html += '<p class="ts-empty">Loading the talent data…</p>';
      else {
        var picks = GROUP_PICKS.map(function (p, i) {
          var code = p.code || (p.preset ? TC.presetCode(raw, p.cls, p.preset) : "");
          return code ? { id: "g" + i, name: p.name, by: p.by, note: p.note, code: code } : null;
        }).filter(Boolean);
        html += picks.length ? grouped(picks, "group") : '<p class="ts-empty">No group picks yet.</p>';
      }
      html += '<p class="ts-foot">Suggestions we agreed on (or want to talk about). To suggest one: save it under <b>My builds</b>, press <b>Edit → Copy as group pick</b>, and send the result to whoever updates the site.</p>';
    }
    body.innerHTML = html;
    flash = null;
  }

  // --- Open / close ----------------------------------------------------------------
  function open(t) {
    if (t) { tab = t; save(TAB_KEY, tab); }
    if (!document.body.classList.contains("ts-open")) lastFocus = document.activeElement;
    render();
    document.body.classList.add("ts-open");
    drawer.setAttribute("aria-hidden", "false");
    var first = body.querySelector(".ts-save input[name=name]");
    (first || drawer.querySelector(".ts-close")).focus();
    if (first) first.select();
  }
  function close() {
    document.body.classList.remove("ts-open");
    drawer.setAttribute("aria-hidden", "true");
    pending = null; editing = null;
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function copy(text, btn, label) {
    var done = function () { if (!btn) return; var t = btn.textContent; btn.textContent = label || "Copied!"; setTimeout(function () { btn.textContent = t; }, 1500); };
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, function () { window.prompt("Copy this:", text); });
    else window.prompt("Copy this:", text);
  }
  function persist() { if (!save(KEY, builds)) alert("Couldn't save — this browser is blocking local storage (private window?)."); }

  // Accepts "https://…/talents.html#hunter/05-…", "#hunter/05", or "hunter/05".
  function parseCode(s) {
    s = String(s || "").trim();
    var h = s.indexOf("#");
    if (h !== -1) s = s.slice(h + 1);
    try { s = decodeURIComponent(s); } catch (e) { /* keep as is */ }
    var m = /^([a-z]+)(\/[0-9]*(-[0-9]*){0,2})?$/.exec(s);
    return m && TC.classById(m[1]) ? s : "";
  }

  // --- Events -------------------------------------------------------------------------
  fab.addEventListener("click", function () { open(); });
  overlay.addEventListener("click", close);
  drawer.querySelector(".ts-close").addEventListener("click", close);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && document.body.classList.contains("ts-open")) close(); });
  drawer.querySelector(".ts-tabs").addEventListener("click", function (e) {
    var b = e.target.closest("[data-tab]");
    if (b) { editing = null; open(b.dataset.tab); }
  });
  body.addEventListener("submit", function (e) {
    e.preventDefault();
    var f = e.target;
    if (f.classList.contains("ts-import")) {
      var code = parseCode(f.url.value);
      if (!code) { f.url.setCustomValidity("That isn't a talent calc link (it should end in #class/digits)."); f.url.reportValidity(); return; }
      var cls = clsOf(code), sp = splitOf(code);
      var b = { id: uid(), code: code, name: cls.name + " — " + treeName(cls, sp) + " " + sp.join("/"), note: "", ts: Date.now() };
      builds.unshift(b); persist(); editing = b.id; render();
      var inp = body.querySelector('.ts-editing input[data-f="name"]'); if (inp) { inp.focus(); inp.select(); }
      return;
    }
    if (f.classList.contains("ts-save") && pending) {
      var mode = (e.submitter && e.submitter.dataset.mode) || "new";
      var name = f.name.value.trim() || "Untitled build", note = f.note.value.trim(), c = pending.inst.encode();
      var active = sGet(ACTIVE_KEY), cur = builds.filter(function (x) { return x.id === active; })[0];
      if (mode === "update" && cur) { cur.code = c; cur.name = name; cur.note = note; cur.ts = Date.now(); flash = cur.id; }
      else { var nb = { id: uid(), code: c, name: name, note: note, ts: Date.now() }; builds.unshift(nb); flash = nb.id; sSet(ACTIVE_KEY, nb.id); }
      persist(); pending = null; render();
    }
  });
  body.addEventListener("input", function (e) { if (e.target.setCustomValidity) e.target.setCustomValidity(""); });
  body.addEventListener("click", function (e) {
    var a = e.target.closest("[data-act]");
    if (!a) return;
    var card = a.closest(".ts-card"), id = card && card.dataset.id;
    var list = card && card.dataset.kind === "group" ? null : builds;
    var b = list ? list.filter(function (x) { return x.id === id; })[0] : null;
    var code = b ? b.code : (card ? card.querySelector("[data-act=open]").getAttribute("href").split("#")[1] : "");
    switch (a.dataset.act) {
      case "open":
        sSet(ACTIVE_KEY, b ? b.id : "");
        close();            // let the link navigate (same page: hashchange reloads the calc)
        return;
      case "copy": copy(link(code), a); break;
      case "copy-all":
        copy(builds.map(function (x) { return x.name + ": " + link(x.code); }).join("\n"), a); break;
      case "edit": editing = id; render(); break;
      case "edit-cancel": editing = null; render(); break;
      case "edit-ok":
        b.name = card.querySelector('[data-f="name"]').value.trim() || b.name;
        b.note = card.querySelector('[data-f="note"]').value.trim();
        persist(); editing = null; flash = b.id; render(); break;
      case "del":
        if (window.confirm('Delete "' + b.name + '"?')) { builds = builds.filter(function (x) { return x.id !== id; }); persist(); render(); }
        break;
      case "group-copy":
        var nm = card.querySelector('[data-f="name"]').value.trim() || b.name, nt = card.querySelector('[data-f="note"]').value.trim();
        copy("    { cls: " + JSON.stringify(code.split("/")[0]) + ", name: " + JSON.stringify(nm) + ", by: \"\",\n      note: " + JSON.stringify(nt) + ",\n      code: " + JSON.stringify(code) + " },", a);
        break;
      case "save-cancel": pending = null; render(); break;
    }
  });

  TC.load().then(function (d) { raw = d; if (tab === "group" && document.body.classList.contains("ts-open")) render(); }, function () { /* group picks stay "loading" */ });
  render();

  window.TalentSaved = {
    GROUP_PICKS: GROUP_PICKS,
    open: open,
    openSave: function (inst, name) { pending = { inst: inst, name: name || "" }; editing = null; open("mine"); }
  };
  if (location.hash === "#saved") open();
})();
