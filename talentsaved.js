/* =============================================================================
   Saved builds sidebar (talents.html + builds.html). Load after talentcalc.js.

   Two lists in one right-hand drawer:
     - My builds:   saved in this browser (localStorage "wf-talent-builds-v1").
                    Save from any calculator's "Save build" button, or import a
                    talents.html link a friend pasted in chat.
     - Group picks: group-builds.json in the repo, so everyone sees the same list.
                    Only the site owner can change it: "Owner login" takes a GitHub
                    fine-grained token (this repo only, Contents read/write), checks
                    it with GitHub, and then "Publish to group" / Edit / Remove commit
                    group-builds.json through the GitHub API. The token is kept only
                    in the owner's own browser; it is never in the repo.

   group-builds.json: { "picks": [ { id, name, by, note, code: "<class>/<t1>-<t2>-<t3>", ts } ] }

   API: TalentSaved.open(tab?)  TalentSaved.openSave(calcInstance, defaultName?)
   ============================================================================= */
(function () {
  "use strict";

  var REPO = "nobody174/wow-forever-macros", BRANCH = "main", FILE = "group-builds.json";
  var API = "https://api.github.com";
  var KEY = "wf-talent-builds-v1", TAB_KEY = "wf-talent-builds-tab", ACTIVE_KEY = "wf-talent-builds-active", OWNER_KEY = "wf-owner-gh";
  var TC = window.TalentCalc;
  if (!TC) return;

  function load(k, d) { try { var v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } }
  function sGet(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } }
  function sSet(k, v) { try { if (v) sessionStorage.setItem(k, v); else sessionStorage.removeItem(k); } catch (e) { /* blocked */ } }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function uid(p) { return (p || "b") + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }
  function link(code) { return new URL("talents.html#" + code, location.href).href; }
  function clsOf(code) { return TC.classById(String(code).split("/")[0]); }

  var builds = load(KEY, []);
  if (!Array.isArray(builds)) builds = [];
  var tab = load(TAB_KEY, "mine") === "group" ? "group" : "mine";
  var pending = null, editing = null, flash = null, lastFocus = null;
  var picks = null, picksErr = false, busy = false, notice = null, loginOpen = false;

  // --- Owner session (GitHub token kept in this browser only) -------------------------
  function readOwner() {
    var raw = sGet(OWNER_KEY);
    if (!raw) try { raw = localStorage.getItem(OWNER_KEY); } catch (e) { raw = null; }
    try { var o = JSON.parse(raw); return o && o.token && o.login ? o : null; } catch (e) { return null; }
  }
  var owner = readOwner();
  function storeOwner(o, remember) {
    try { localStorage.removeItem(OWNER_KEY); } catch (e) { /* blocked */ }
    sSet(OWNER_KEY, "");
    if (!o) return;
    if (remember) { try { localStorage.setItem(OWNER_KEY, JSON.stringify(o)); } catch (e) { sSet(OWNER_KEY, JSON.stringify(o)); } }
    else sSet(OWNER_KEY, JSON.stringify(o));
  }
  function gh(path, opts, token) {
    opts = opts || {};
    var headers = { "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" };
    if (token || owner) headers.Authorization = "Bearer " + (token || owner.token);
    if (opts.body) headers["Content-Type"] = "application/json";
    return fetch(API + path, { method: opts.method || "GET", headers: headers, body: opts.body, cache: "no-store" }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) {
        if (!r.ok) { var e = new Error(j.message || ("GitHub said " + r.status)); e.status = r.status; throw e; }
        return j;
      });
    });
  }
  function b64encode(s) { return btoa(unescape(encodeURIComponent(s))); }
  function b64decode(s) { return decodeURIComponent(escape(atob(String(s).replace(/\s/g, "")))); }

  // --- Group picks: read (everyone) and write (owner) -----------------------------------
  function normPicks(j) {
    var list = j && Array.isArray(j.picks) ? j.picks : [];
    return list.filter(function (p) { return p && p.code && clsOf(p.code); });
  }
  function loadPicks() {
    var p = owner
      ? gh("/repos/" + REPO + "/contents/" + FILE + "?ref=" + BRANCH).then(function (f) { return JSON.parse(b64decode(f.content)); })
      : fetch(FILE + "?t=" + Date.now(), { cache: "no-store" }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
    return p.then(function (j) { picks = normPicks(j); picksErr = false; }, function () { if (!picks) picksErr = true; })
      .then(function () { if (isOpen()) render(); });
  }
  // Read the latest file + sha, apply change(list), commit. One retry on a sha conflict.
  function commit(change, message, tries) {
    busy = true; notice = { kind: "info", text: "Saving to GitHub…" }; render();
    return gh("/repos/" + REPO + "/contents/" + FILE + "?ref=" + BRANCH).then(function (f) {
      var list = normPicks(JSON.parse(b64decode(f.content)));
      list = change(list);
      var text = JSON.stringify({ picks: list }, null, 2) + "\n";
      return gh("/repos/" + REPO + "/contents/" + FILE, { method: "PUT", body: JSON.stringify({
        message: message, content: b64encode(text), sha: f.sha, branch: BRANCH
      }) }).then(function () { return list; });
    }).then(function (list) {
      picks = list; busy = false;
      notice = { kind: "ok", text: "Saved. The rest of the group sees it in about a minute (when GitHub Pages updates)." };
      render();
      return true;
    }, function (e) {
      if ((e.status === 409 || e.status === 422) && !(tries > 0)) return commit(change, message, 1);
      busy = false;
      if (e.status === 401) { owner = null; storeOwner(null); }
      notice = { kind: "err", text: e.status === 401 ? "GitHub rejected the token (expired or revoked). Log in again."
        : e.status === 403 || e.status === 404 ? "This token can't write to the repo. It needs Contents: Read and write on " + REPO + "."
        : "Couldn't save: " + e.message };
      render();
      return false;
    });
  }

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
  fab.innerHTML = 'Saved builds <span class="ts-count"></span>';
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
    '<div class="ts-body"></div>';
  document.body.appendChild(fab);
  document.body.appendChild(overlay);
  document.body.appendChild(drawer);
  var body = drawer.querySelector(".ts-body");
  function isOpen() { return document.body.classList.contains("ts-open"); }

  // Sit just under the sticky top bar, like the Buyable quests button.
  function placeFab() {
    var bar = document.querySelector(".topbar");
    if (bar) document.documentElement.style.setProperty("--topbar-h", bar.offsetHeight + "px");
  }
  placeFab();
  window.addEventListener("resize", placeFab);

  // --- Rendering -----------------------------------------------------------------
  function editHTML(b) {
    return '<label class="ts-lbl">Name<input type="text" maxlength="80" data-f="name" value="' + esc(b.name) + '"></label>' +
      '<label class="ts-lbl">Note<textarea rows="3" maxlength="600" data-f="note" placeholder="Why this build, when to use it…">' + esc(b.note) + "</textarea></label>";
  }
  function cardHTML(b, kind) {
    var cls = clsOf(b.code) || { name: "?", color: "#9AA0B8", id: "" };
    var dis = busy ? " disabled" : "";
    var head = '<div class="ts-card-top"><img class="ts-icon" src="' + TC.ICON + "classicon_" + cls.id + '.jpg" alt="" loading="lazy">' +
      '<div><div class="ts-name">' + esc(b.name) + "</div>" + '<div class="ts-meta">' + metaLine(b.code) +
      (kind === "group" && b.by ? " · " + esc(b.by) : "") + "</div></div></div>";
    var attrs = ' style="--c:' + cls.color + '" data-id="' + esc(b.id) + '" data-kind="' + kind + '"';
    if (editing === kind + ":" + b.id) {
      return '<div class="ts-card ts-editing"' + attrs + ">" + head + editHTML(b) +
        '<div class="ts-acts"><button type="button" class="ts-btn ts-primary" data-act="edit-ok"' + dis + ">Save</button>" +
        '<button type="button" class="ts-btn" data-act="edit-cancel">Cancel</button></div></div>';
    }
    var acts = '<a class="ts-btn ts-primary" data-act="open" href="talents.html#' + esc(b.code) + '">Open</a>' +
      '<button type="button" class="ts-btn" data-act="copy">Copy link</button>';
    if (kind === "mine") {
      acts += '<button type="button" class="ts-btn" data-act="edit">Edit</button><button type="button" class="ts-btn ts-danger" data-act="del">Delete</button>';
      if (owner) acts += '<button type="button" class="ts-btn ts-owner" data-act="publish"' + dis + ">Publish to group</button>";
    } else if (owner) {
      acts += '<button type="button" class="ts-btn ts-owner" data-act="edit"' + dis + '>Edit</button><button type="button" class="ts-btn ts-danger" data-act="del"' + dis + ">Remove</button>";
    }
    return '<div class="ts-card' + (flash === b.id ? " ts-flash" : "") + '"' + attrs + ">" + head +
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
  function noticeHTML() {
    return notice ? '<p class="ts-notice ts-' + notice.kind + '" role="status">' + esc(notice.text) + "</p>" : "";
  }
  function ownerHTML() {
    if (owner) {
      return '<div class="ts-ownerbar">Signed in as <b>' + esc(owner.login) + '</b> — you can publish, edit and remove group picks. ' +
        '<button type="button" class="ts-link" data-act="logout">Sign out</button></div>';
    }
    if (!loginOpen) return '<p class="ts-foot">Group picks are published by the site owner. <button type="button" class="ts-link" data-act="login-open">Owner login</button></p>';
    return '<form class="ts-login"><div class="ts-save-h">Owner login</div>' +
      '<p class="ts-meta">Paste a GitHub fine-grained token. It stays in this browser only and is checked with GitHub. ' +
      '<a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">Create one</a>: ' +
      'Repository access → Only select repositories → <b>' + esc(REPO.split("/")[1]) + '</b>; Permissions → Contents → <b>Read and write</b>; pick an expiry.</p>' +
      '<label class="ts-lbl">Token<input type="password" name="token" autocomplete="off" spellcheck="false" required placeholder="github_pat_…"></label>' +
      '<label class="ts-check"><input type="checkbox" name="remember"> Remember on this device</label>' +
      '<div class="ts-acts"><button type="submit" class="ts-btn ts-primary"' + (busy ? " disabled" : "") + '>Sign in</button>' +
      '<button type="button" class="ts-btn" data-act="login-cancel">Cancel</button></div></form>';
  }
  function render() {
    drawer.querySelectorAll("[data-tab]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.tab === tab)); });
    drawer.querySelector('[data-n="mine"]').textContent = builds.length;
    drawer.querySelector('[data-n="group"]').textContent = picks ? picks.length : "";
    fab.querySelector(".ts-count").textContent = builds.length;
    var html = noticeHTML();
    if (tab === "mine") {
      if (pending) html += saveFormHTML();
      html += '<div class="ts-tools"><form class="ts-import"><input type="url" name="url" placeholder="Paste a talent calc link to add it" aria-label="Talent calc link">' +
        '<button type="submit" class="ts-btn">Add</button></form>' +
        (builds.length ? '<button type="button" class="ts-btn ts-ghost" data-act="copy-all">Copy all as links</button>' : "") + "</div>";
      html += builds.length ? grouped(builds, "mine")
        : '<p class="ts-empty">Nothing saved yet. Build something in the calculator and press <b>Save build</b>, or paste a link a friend sent you above.</p>';
      html += '<p class="ts-foot">Saved in this browser only. To share, use <b>Copy link</b> (or <b>Copy all as links</b>) and paste it in the group chat — whoever opens it can add it to their own list.' +
        (owner ? " <b>Publish to group</b> puts a build in Group picks for everyone." : "") + "</p>";
    } else {
      if (picks) html += picks.length ? grouped(picks, "group") : '<p class="ts-empty">No group picks yet.</p>';
      else html += '<p class="ts-empty">' + (picksErr ? "Couldn't load the group picks right now." : "Loading group picks…") + "</p>";
      html += ownerHTML();
    }
    body.innerHTML = html;
    flash = null;
  }

  // --- Open / close ----------------------------------------------------------------
  function open(t) {
    if (t) { tab = t; save(TAB_KEY, tab); }
    if (!isOpen()) { lastFocus = document.activeElement; if (!busy) notice = null; }
    render();
    document.body.classList.add("ts-open");
    drawer.setAttribute("aria-hidden", "false");
    var first = body.querySelector(".ts-save input[name=name]");
    (first || drawer.querySelector(".ts-close")).focus();
    if (first) first.select();
    if (tab === "group") loadPicks();
  }
  function close() {
    document.body.classList.remove("ts-open");
    drawer.setAttribute("aria-hidden", "true");
    pending = null; editing = null; loginOpen = false;
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function copy(text, btn) {
    var done = function () { if (!btn) return; var t = btn.textContent; btn.textContent = "Copied!"; setTimeout(function () { btn.textContent = t; }, 1500); };
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

  function signIn(f) {
    var token = f.token.value.trim(), remember = f.remember.checked;
    if (!token) return;
    busy = true; notice = { kind: "info", text: "Checking the token with GitHub…" }; render();
    var login;
    gh("/user", {}, token).then(function (u) {
      login = u.login;
      return gh("/repos/" + REPO, {}, token);
    }).then(function (repo) {
      var p = repo.permissions || {};
      if (!(p.push || p.admin || p.maintain)) throw Object.assign(new Error("no access"), { status: 403 });
      owner = { token: token, login: login };
      storeOwner(owner, remember);
      busy = false; loginOpen = false;
      notice = { kind: "ok", text: "Signed in as " + login + "." };
      return loadPicks();
    }).catch(function (e) {
      busy = false;
      notice = { kind: "err", text: e.status === 401 ? "GitHub doesn't accept that token." : e.status === 403 || e.status === 404
        ? "That token doesn't have access to " + REPO + "." : "Couldn't reach GitHub: " + e.message };
      render();
    });
  }

  // --- Events -------------------------------------------------------------------------
  fab.addEventListener("click", function () { open(); });
  overlay.addEventListener("click", close);
  drawer.querySelector(".ts-close").addEventListener("click", close);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && isOpen()) close(); });
  drawer.querySelector(".ts-tabs").addEventListener("click", function (e) {
    var b = e.target.closest("[data-tab]");
    if (b) { editing = null; if (!busy) notice = null; open(b.dataset.tab); }
  });
  body.addEventListener("submit", function (e) {
    e.preventDefault();
    var f = e.target;
    if (f.classList.contains("ts-login")) { signIn(f); return; }
    if (f.classList.contains("ts-import")) {
      var code = parseCode(f.url.value);
      if (!code) { f.url.setCustomValidity("That isn't a talent calc link (it should end in #class/digits)."); f.url.reportValidity(); return; }
      var cls = clsOf(code), sp = splitOf(code);
      var b = { id: uid(), code: code, name: cls.name + " — " + treeName(cls, sp) + " " + sp.join("/"), note: "", ts: Date.now() };
      builds.unshift(b); persist(); editing = "mine:" + b.id; render();
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
    if (!a || a.disabled) return;
    var card = a.closest(".ts-card"), id = card && card.dataset.id, kind = card && card.dataset.kind;
    var list = kind === "group" ? (picks || []) : builds;
    var b = card ? list.filter(function (x) { return x.id === id; })[0] : null;
    switch (a.dataset.act) {
      case "open":
        sSet(ACTIVE_KEY, kind === "mine" && b ? b.id : "");
        close();            // let the link navigate (same page: hashchange reloads the calc)
        return;
      case "copy": copy(link(b.code), a); break;
      case "copy-all":
        copy(builds.map(function (x) { return x.name + ": " + link(x.code); }).join("\n"), a); break;
      case "edit": editing = kind + ":" + id; render(); break;
      case "edit-cancel": editing = null; render(); break;
      case "edit-ok":
        var nm = card.querySelector('[data-f="name"]').value.trim() || b.name, nt = card.querySelector('[data-f="note"]').value.trim();
        editing = null;
        if (kind === "mine") { b.name = nm; b.note = nt; persist(); flash = b.id; render(); }
        else commit(function (l) { l.forEach(function (p) { if (p.id === id) { p.name = nm; p.note = nt; } }); return l; }, "Group picks: edit " + nm);
        break;
      case "del":
        if (!window.confirm((kind === "mine" ? "Delete" : "Remove from Group picks") + ' "' + b.name + '"?')) break;
        if (kind === "mine") { builds = builds.filter(function (x) { return x.id !== id; }); persist(); render(); }
        else commit(function (l) { return l.filter(function (p) { return p.id !== id; }); }, "Group picks: remove " + b.name);
        break;
      case "publish":
        var pick = { id: uid("g"), name: b.name, by: owner.login, note: b.note || "", code: b.code, ts: Date.now() };
        commit(function (l) { return [pick].concat(l); }, "Group picks: add " + b.name).then(function (ok) { if (!ok) return; flash = pick.id; tab = "group"; save(TAB_KEY, tab); render(); });
        break;
      case "save-cancel": pending = null; render(); break;
      case "login-open": loginOpen = true; notice = null; render(); var t = body.querySelector(".ts-login input[name=token]"); if (t) t.focus(); break;
      case "login-cancel": loginOpen = false; render(); break;
      case "logout": owner = null; storeOwner(null); notice = { kind: "info", text: "Signed out. The token was removed from this browser." }; render(); break;
    }
  });

  render();
  loadPicks();

  window.TalentSaved = {
    open: open,
    openSave: function (inst, name) { pending = { inst: inst, name: name || "" }; editing = null; notice = null; open("mine"); }
  };
  if (location.hash === "#saved") open();
})();
