/* Legacy calculator engine (talents.html, "Legacy" mode).
   Data is NOT stored in the repo: like talentcalc.js, we load Wowhead's public
   Forever data script, which calls
     WH.setPageData("wow.legacyCalculator.classicplus.calc", {build, cap, trees})
   so the calculator always shows Wowhead's newest Legacy perks.
   Data shape: { build, cap (max points, 16), trees: [{ id, name, art, blurb,
     nodes: [{ id, x, y, name, icon, maxRanks, locked, requiredSpent, castMs,
     cdMs, ranks: [text per rank] }], edges: [{ from, to }] }] }
   Rules (checked against Wowhead's own calculator, 2026-10-06):
   - At most `cap` points across all three trees.
   - A perk with requiredSpent R needs R points in that tree's perks whose own
     requiredSpent is lower than R (gates work like talent tiers).
   - An edge from A to B means B needs at least 1 rank in A.
   - A point can't be removed if that would break a perk that's already taken.
   - locked perks ("Unknown", not in the game yet) can't be taken.
   Share code: "legacy/<t1>-<t2>-<t3>", one digit per perk in grid order
   (top-to-bottom, left-to-right), locked perks included so codes don't shift
   when Blizzard fills them in. */
(function () {
  "use strict";
  var DATA_URL = "https://nether.wowhead.com/forever/data/legacy-calculator";
  var ICON = "https://wow.zamimg.com/images/wow/icons/large/";
  var ART = "https://wow.zamimg.com/images/tools/legacy-calculator/";

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function dur(ms) {
    var s = Math.round(ms / 1000);
    if (s < 60) return s + " sec";
    if (s < 3600) return Math.round(s / 60) + " min";
    return Math.round(s / 3600) + " hr";
  }

  // --- Data loading (once per page) ---------------------------------------------
  var loading = null;
  function load() {
    if (loading) return loading;
    loading = new Promise(function (resolve, reject) {
      var data = null;
      window.WH = window.WH || {};
      var prev = window.WH.setPageData;
      window.WH.setPageData = function (key, value) {
        if (/legacyCalculator/.test(key) && value && value.trees) data = value;
        if (typeof prev === "function") try { prev.apply(this, arguments); } catch (e) { /* ignore */ }
      };
      var s = document.createElement("script");
      s.src = DATA_URL;
      s.async = true;
      s.onload = function () { if (data) resolve(data); else reject(new Error("no data")); };
      s.onerror = function () { reject(new Error("load failed")); };
      setTimeout(function () { if (!data) reject(new Error("timeout")); }, 15000);
      document.head.appendChild(s);
    });
    return loading;
  }

  // --- Tooltip (reuses talentcalc.css's .tc-tip look) ----------------------------
  var tip = null, tipState = null, lastPointer = "mouse";
  function ensureTip() {
    if (tip) return tip;
    tip = document.createElement("div");
    tip.className = "tc-tip";
    tip.hidden = true;
    tip.setAttribute("role", "dialog");
    document.body.appendChild(tip);
    document.addEventListener("pointerdown", function (e) { lastPointer = e.pointerType || "mouse"; }, true);
    tip.addEventListener("click", function (e) {
      var b = e.target.closest("[data-act]");
      if (!b || !tipState) return;
      if (b.dataset.act === "plus") tipState.inst._add(tipState.n, false);
      else if (b.dataset.act === "minus") tipState.inst._remove(tipState.n, false);
      else hideTip();
    });
    document.addEventListener("click", function (e) {
      var path = e.composedPath ? e.composedPath() : [];
      if (tipState && tipState.touch && path.indexOf(tip) === -1 && !(e.target.closest && e.target.closest(".lc-cell"))) hideTip();
    });
    window.addEventListener("scroll", function () { if (tipState && !tipState.touch) hideTip(); }, { passive: true });
    return tip;
  }
  function hideTip() { if (tip) tip.hidden = true; tipState = null; }

  // --- One calculator ------------------------------------------------------------
  function Calc(el, data, opts) {
    opts = opts || {};
    var self = this;
    var cap = data.cap || 16;
    // Grid positions: Wowhead's x/y are canvas coordinates; turn the distinct
    // values into column/row numbers shared by all trees.
    var xs = [], ys = [];
    data.trees.forEach(function (t) { t.nodes.forEach(function (n) { if (xs.indexOf(n.x) === -1) xs.push(n.x); if (ys.indexOf(n.y) === -1) ys.push(n.y); }); });
    xs.sort(function (a, b) { return a - b; }); ys.sort(function (a, b) { return a - b; });
    var byId = {}, ranks = {};
    var trees = data.trees.map(function (t, ti) {
      var nodes = t.nodes.map(function (n) {
        var m = {
          id: n.id, name: n.name, icon: n.icon || "inv_misc_questionmark", max: n.maxRanks || (n.ranks || []).length || 1,
          locked: !!n.locked, need: n.requiredSpent || 0, castMs: n.castMs || 0, cdMs: n.cdMs || 0,
          ranks: n.ranks || [], col: xs.indexOf(n.x), row: ys.indexOf(n.y), tree: ti, req: []
        };
        byId[m.id] = m;
        return m;
      }).sort(function (a, b) { return a.row - b.row || a.col - b.col; });
      return { name: t.name, art: t.art, blurb: t.blurb || "", nodes: nodes, edges: (t.edges || []).slice() };
    });
    trees.forEach(function (t) { t.edges.forEach(function (e) { if (byId[e.to] && byId[e.from]) byId[e.to].req.push(byId[e.from]); }); });

    // Rules
    function rank(n) { return ranks[n.id] || 0; }
    function treePoints(ti) { return trees[ti].nodes.reduce(function (a, n) { return a + rank(n); }, 0); }
    function total() { var s = 0; for (var i = 0; i < trees.length; i++) s += treePoints(i); return s; }
    function below(n) { return trees[n.tree].nodes.reduce(function (a, o) { return a + (o.need < n.need ? rank(o) : 0); }, 0); }
    function gateMet(n) { return below(n) >= n.need; }
    function reqMet(n) { return n.req.every(function (p) { return rank(p) >= 1; }); }
    function ok(n) { return !rank(n) || (!n.locked && rank(n) <= n.max && gateMet(n) && reqMet(n)); }
    function valid() { return total() <= cap && trees.every(function (t) { return t.nodes.every(ok); }); }
    function canAdd(n) { return !n.locked && total() < cap && rank(n) < n.max && gateMet(n) && reqMet(n); }
    function canRemove(n) {
      if (!rank(n)) return false;
      ranks[n.id]--;
      var good = trees[n.tree].nodes.every(ok);
      ranks[n.id]++;
      return good;
    }

    // Share code
    function code() {
      return trees.map(function (t) { return t.nodes.map(rank).join("").replace(/0+$/, ""); }).join("-").replace(/-+$/, "");
    }
    function applyCode(c) {
      ranks = {};
      var parts = String(c || "").split("-");
      trees.forEach(function (t, ti) {
        var s = parts[ti] || "";
        t.nodes.forEach(function (n, i) { var v = parseInt(s.charAt(i), 10) || 0; if (v) ranks[n.id] = v; });
      });
      if (!valid()) ranks = {};
    }

    // Rendering
    function cellBox(row, col) {
      var cs = getComputedStyle(el);
      var size = parseFloat(cs.getPropertyValue("--cell")) || 48, gap = parseFloat(cs.getPropertyValue("--gap")) || 22;
      return { x: col * (size + gap), y: row * (size + gap), s: size };
    }
    function linksHTML(t) {
      return t.edges.map(function (e) {
        var a = byId[e.from], b = byId[e.to];
        if (!a || !b) return "";
        var A = cellBox(a.row, a.col), B = cellBox(b.row, b.col), w = 4, k = ' data-from="' + a.id + '"';
        if (a.row === b.row) {
          var l = Math.min(A.x, B.x) + A.s, wd = Math.abs(B.x - A.x) - A.s;
          return '<span class="lc-link"' + k + ' style="left:' + l + "px;top:" + (A.y + A.s / 2 - w / 2) + "px;width:" + wd + "px;height:" + w + 'px"></span>';
        }
        var cx = B.x + B.s / 2 - w / 2, html = "";
        if (a.col !== b.col) html += '<span class="lc-link"' + k + ' style="left:' + Math.min(A.x + A.s / 2, cx) + "px;top:" + (A.y + A.s / 2 - w / 2) + "px;width:" + Math.abs(cx - A.x - A.s / 2) + "px;height:" + w + 'px"></span>';
        var top = Math.min(A.y + A.s / 2, B.y), ht = Math.abs(B.y - A.y) - A.s / 2;
        return html + '<span class="lc-link"' + k + ' style="left:' + cx + "px;top:" + top + "px;width:" + w + "px;height:" + ht + 'px"></span>';
      }).join("");
    }
    function gates(t) {
      var g = [];
      t.nodes.forEach(function (n) { if (n.need && g.indexOf(n.need) === -1) g.push(n.need); });
      return g.sort(function (a, b) { return a - b; });
    }
    function render() {
      el.classList.add("tc", "lc");
      var cols = xs.length, rows = ys.length;
      el.style.setProperty("--cols", cols);
      el.style.setProperty("--rows", rows);
      var bar = '<div class="tc-bar"><span class="tc-stat">Spent <b data-lc="spent">0</b> / ' + cap + '</span>' +
        '<span class="tc-stat tc-left">Left <b data-lc="left">' + cap + '</b></span>' +
        '<button type="button" class="tc-btn" data-lc-act="copy">Copy link</button>' +
        '<button type="button" class="tc-btn tc-danger" data-lc-act="reset">Reset</button></div>' +
        '<p class="tc-hint">Legacy points are shared by your whole account. Click to add a point, right-click to remove, Shift-click to max. On a phone, tap a perk for + and − buttons.</p>';
      var html = trees.map(function (t, ti) {
        var cells = t.nodes.map(function (n) {
          return '<button type="button" class="lc-cell' + (n.locked ? " lc-locked" : "") + '" data-id="' + n.id + '" style="grid-row:' + (n.row + 1) + ";grid-column:" + (n.col + 1) +
            '" aria-label="' + esc(n.locked ? "Not in the game yet" : n.name) + '"><img src="' + ICON + n.icon + '.jpg" alt="" loading="lazy">' +
            (n.locked ? "" : '<span class="tc-rk"></span>') + "</button>";
        }).join("");
        var gt = gates(t).map(function (g) { return '<span class="lc-gate" data-gate="' + g + '" data-tree="' + ti + '">' + g + " pts</span>"; }).join("");
        return '<section class="tc-tree lc-tree" data-tree="' + ti + '" style="--art:url(\'' + ART + esc(t.art) + '.webp\')"><div class="tc-head"><h3>' + esc(t.name) +
          '</h3><span class="tc-pts"><span data-pts="' + ti + '">0</span> / ' + cap + '</span><button type="button" class="tc-reset-tree" data-reset="' + ti +
          '" aria-label="Reset ' + esc(t.name) + '" title="Reset this tree">×</button></div>' +
          '<div class="lc-sub"><span class="lc-blurb">' + esc(t.blurb) + "</span>" + gt + "</div>" +
          '<div class="lc-grid">' + linksHTML(t) + cells + "</div></section>";
      }).join("");
      el.innerHTML = bar + '<div class="tc-trees">' + html + "</div>";
      update(false);
    }
    function update(changed) {
      var spent = total();
      el.querySelectorAll(".lc-cell").forEach(function (c) {
        var n = byId[c.dataset.id], r = rank(n);
        if (n.locked) return;
        c.className = "lc-cell" + (r >= n.max ? " tc-max" : r ? " tc-some" : canAdd(n) ? " tc-avail" : "");
        c.querySelector(".tc-rk").textContent = r + "/" + n.max;
      });
      el.querySelectorAll(".lc-link").forEach(function (a) { a.classList.toggle("lc-on", rank(byId[a.dataset.from]) >= 1); });
      el.querySelectorAll("[data-pts]").forEach(function (s) { s.textContent = treePoints(+s.dataset.pts); });
      el.querySelectorAll(".lc-gate").forEach(function (g) { g.classList.toggle("lc-on", treePoints(+g.dataset.tree) >= +g.dataset.gate); });
      var set = function (k, v) { var x = el.querySelector('[data-lc="' + k + '"]'); if (x) x.textContent = v; };
      set("spent", spent);
      set("left", cap - spent);
      if (changed && typeof opts.onChange === "function") opts.onChange(self);
      if (tipState && tipState.inst === self) showTip(tipState.n, tipState.anchor, tipState.touch);
    }
    function add(n, max) { var ch = false; while (canAdd(n)) { ranks[n.id] = rank(n) + 1; ch = true; if (!max) break; } if (ch) update(true); }
    function remove(n, all) {
      var ch = false;
      while (canRemove(n)) { ranks[n.id] = rank(n) - 1; if (!ranks[n.id]) delete ranks[n.id]; ch = true; if (!all) break; }
      if (ch) update(true);
    }

    function showTip(n, anchor, touch) {
      ensureTip();
      tipState = { inst: self, n: n, anchor: anchor, touch: touch };
      var html;
      if (n.locked) {
        html = '<p class="tc-tn">Not in the game yet</p><p class="tc-td">' + esc(n.ranks[0] || "To be added in a future update.") + "</p>" +
          '<div class="tc-ctl"><button type="button" class="tc-close" data-act="close">Close</button></div>';
      } else {
        var r = rank(n);
        html = '<p class="tc-tn">' + esc(n.name) + '</p><p class="tc-tr">Rank ' + r + "/" + n.max + "</p>";
        if (n.castMs || n.cdMs) html += '<p class="tc-tr">' + (n.castMs ? dur(n.castMs) + " cast" : "Instant") + (n.cdMs ? " · " + dur(n.cdMs) + " cooldown" : "") + "</p>";
        html += '<p class="tc-td">' + esc(n.ranks[Math.max(r, 1) - 1] || "") + "</p>";
        if (r && r < n.max && n.ranks[r]) html += '<p class="tc-tl">Next rank</p><p class="tc-td">' + esc(n.ranks[r]) + "</p>";
        if (!gateMet(n)) html += '<p class="tc-req">Requires ' + n.need + " points spent in " + esc(trees[n.tree].name) + "</p>";
        n.req.forEach(function (p) { if (!rank(p)) html += '<p class="tc-req">Requires a rank in ' + esc(p.name) + "</p>"; });
        if (!r && total() >= cap) html += '<p class="tc-req">All ' + cap + " Legacy points are spent</p>";
        html += '<p class="tc-how">Click: +1 · Right-click: −1 · Shift-click: max</p>';
        html += '<div class="tc-ctl"><button type="button" data-act="minus" aria-label="Remove a point">−</button><button type="button" data-act="plus" aria-label="Add a point">+</button><button type="button" class="tc-close" data-act="close">Close</button></div>';
      }
      tip.innerHTML = html;
      tip.className = "tc-tip" + (touch ? " tc-touch" : "");
      tip.hidden = false;
      if (!touch) {
        var b = anchor.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
        tip.style.left = (b.right + 12 + w > window.innerWidth ? Math.max(8, b.left - w - 12) : b.right + 12) + "px";
        tip.style.top = Math.min(Math.max(8, b.top), window.innerHeight - h - 8) + "px";
      }
    }

    el.addEventListener("click", function (e) {
      var act = e.target.closest("[data-lc-act]");
      if (act) {
        if (act.dataset.lcAct === "reset") { ranks = {}; update(true); }
        else {
          var url = new URL("talents.html#" + self.link(), location.href).href;
          var done = function () { act.textContent = "Copied!"; setTimeout(function () { act.textContent = "Copy link"; }, 1500); };
          if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, function () { window.prompt("Copy this link:", url); });
          else window.prompt("Copy this link:", url);
        }
        return;
      }
      var reset = e.target.closest("[data-reset]");
      if (reset) { trees[+reset.dataset.reset].nodes.forEach(function (n) { delete ranks[n.id]; }); update(true); return; }
      var c = e.target.closest(".lc-cell");
      if (!c) return;
      var n = byId[c.dataset.id];
      if (lastPointer === "touch" || lastPointer === "pen") { showTip(n, c, true); return; }
      add(n, e.shiftKey);
    });
    el.addEventListener("contextmenu", function (e) {
      var c = e.target.closest(".lc-cell");
      if (!c) return;
      e.preventDefault();
      remove(byId[c.dataset.id], e.shiftKey);
    });
    el.addEventListener("keydown", function (e) {
      var c = e.target.closest(".lc-cell");
      if (!c) return;
      var n = byId[c.dataset.id];
      if (e.key === "-" || e.key === "Backspace" || e.key === "Delete") { e.preventDefault(); remove(n, e.shiftKey); }
      else if (e.key === "+" || e.key === "=") { e.preventDefault(); add(n, e.shiftKey); }
    });
    el.addEventListener("mouseover", function (e) {
      var c = e.target.closest(".lc-cell");
      if (c && lastPointer === "mouse") showTip(byId[c.dataset.id], c, false);
    });
    el.addEventListener("mouseout", function (e) {
      var rel = e.relatedTarget;
      if (tipState && !tipState.touch && e.target.closest(".lc-cell") && !(rel && rel.closest && rel.closest(".lc-cell"))) hideTip();
    });
    el.addEventListener("focusin", function (e) {
      var c = e.target.closest(".lc-cell");
      if (c && lastPointer !== "touch") showTip(byId[c.dataset.id], c, false);
    });
    el.addEventListener("focusout", function () { if (tipState && !tipState.touch) hideTip(); });

    this.build = data.build || "";
    this.link = function () { var c = code(); return "legacy" + (c ? "/" + c : ""); };
    this.total = total;
    this.setCode = function (c) { applyCode(c); update(false); };
    this._add = add;
    this._remove = remove;
    applyCode(opts.code);
    ensureTip();
    render();
  }

  window.LegacyCalc = {
    DATA_URL: DATA_URL,
    load: load,
    hideTip: hideTip,
    mountSync: function (el, data, opts) { return new Calc(el, data, opts); }
  };
})();
