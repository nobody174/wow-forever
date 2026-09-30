/* =============================================================================
   Shared WoW Forever talent calculator (talents.html + builds.html).

   Data: Wowhead publishes its Forever talent data as a script that calls
   WH.setPageData("wow.talentCalcClassic.classicplus.data", {...}). A plain
   <script> tag is not blocked by CORS, so we provide a tiny WH shim and let the
   script hand us the data. Format per tree id:
     { talentId: { id, row, col, icon, name, ranks[], descriptions{1..n},
                   requires[{id,qty}], requiredPoints } }

   API:
     TalentCalc.CLASSES            class list (id, name, color, trees)
     TalentCalc.load()             Promise -> raw data (loaded once, cached)
     TalentCalc.mount(el, opts)    render a calculator into el, returns an instance
       opts.cls        class id ("mage")
       opts.code       share code "<t1>-<t2>-<t3>" (digits per talent)
       opts.preset     [[talentName, rank], ...] (used when no code is given)
       opts.compact    true = tree tabs + one tree at a time (builds page)
       opts.onChange   function(instance) after every point change
     instance.encode() "<class>/<code>"   instance.reset()   instance.setCode(code)
   ============================================================================= */
(function () {
  "use strict";

  var DATA_URL = "https://nether.wowhead.com/forever/data/talents-classic";
  var ICON = "https://wow.zamimg.com/images/wow/icons/large/";
  var MAX_POINTS = 51;

  // Armor-type order like the rest of the site; tree ids in in-game tab order.
  var CLASSES = [
    { id: "priest",  name: "Priest",  color: "#E6E2D6", trees: [[201, "Discipline"], [202, "Holy"], [203, "Shadow"]] },
    { id: "warlock", name: "Warlock", color: "#9482C9", trees: [[302, "Affliction"], [303, "Demonology"], [301, "Destruction"]] },
    { id: "mage",    name: "Mage",    color: "#69CCF0", trees: [[81, "Arcane"], [41, "Fire"], [61, "Frost"]] },
    { id: "rogue",   name: "Rogue",   color: "#FFF569", trees: [[182, "Assassination"], [181, "Combat"], [183, "Subtlety"]] },
    { id: "druid",   name: "Druid",   color: "#FF7D0A", trees: [[283, "Balance"], [281, "Feral Combat"], [282, "Restoration"]] },
    { id: "shaman",  name: "Shaman",  color: "#4C8BFF", trees: [[261, "Elemental"], [263, "Enhancement"], [262, "Restoration"]] },
    { id: "hunter",  name: "Hunter",  color: "#ABD473", trees: [[361, "Beast Mastery"], [363, "Marksmanship"], [362, "Survival"]] },
    { id: "paladin", name: "Paladin", color: "#F58CBA", trees: [[382, "Holy"], [383, "Protection"], [381, "Retribution"]] },
    { id: "warrior", name: "Warrior", color: "#C79C6E", trees: [[161, "Arms"], [164, "Fury"], [163, "Protection"]] }
  ];
  function classById(id) { return CLASSES.filter(function (c) { return c.id === id; })[0] || null; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  // --- Data loading (once per page) -------------------------------------------
  var loading = null;
  function load() {
    if (loading) return loading;
    loading = new Promise(function (resolve, reject) {
      var raw = null;
      window.WH = window.WH || {};
      var prev = window.WH.setPageData;
      window.WH.setPageData = function (key, value) {
        if (/talentCalcClassic/.test(key) && value && value.talents) raw = value.talents;
        if (typeof prev === "function") try { prev.apply(this, arguments); } catch (e) { /* ignore */ }
      };
      var s = document.createElement("script");
      s.src = DATA_URL;
      s.async = true;
      s.onload = function () { if (raw) resolve(raw); else reject(new Error("no data")); };
      s.onerror = function () { reject(new Error("load failed")); };
      setTimeout(function () { if (!raw) reject(new Error("timeout")); }, 15000);
      document.head.appendChild(s);
    });
    return loading;
  }

  // --- Shared tooltip + pointer tracking -----------------------------------------
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
      var inst = tipState.inst, x = tipState.x;
      if (b.dataset.act === "plus") inst._add(x, false);
      else if (b.dataset.act === "minus") inst._remove(x, false);
      else hideTip();
    });
    // composedPath: the tooltip re-renders on +/-, so e.target may already be detached.
    document.addEventListener("click", function (e) {
      var path = e.composedPath ? e.composedPath() : [];
      if (tipState && tipState.touch && path.indexOf(tip) === -1 && !(e.target.closest && e.target.closest(".tc-cell"))) hideTip();
    });
    window.addEventListener("scroll", function () { if (tipState && !tipState.touch) hideTip(); }, { passive: true });
    return tip;
  }
  function hideTip() { if (tip) tip.hidden = true; tipState = null; }

  // --- One calculator instance ------------------------------------------------------
  function Calc(el, raw, opts) {
    var self = this;
    var cls = classById(opts.cls) || CLASSES[0];
    var compact = !!opts.compact;
    var trees = cls.trees.map(function (tr) {
      var src = raw[tr[0]] || {};
      var list = Object.keys(src).map(function (k) { return src[k]; });
      list.sort(function (a, b) { return a.row - b.row || a.col - b.col; });
      return { id: tr[0], name: tr[1], talents: list };
    });
    var byId = {}, byName = {}, ranks = {};
    trees.forEach(function (t, ti) {
      t.talents.forEach(function (x) { x._tree = ti; byId[x.id] = x; byName[x.name.toLowerCase()] = byName[x.name.toLowerCase()] || x; });
    });
    var active = 0;   // visible tree in compact mode

    // Rules
    function rank(x) { return ranks[x.id] || 0; }
    function treePoints(ti) { return trees[ti].talents.reduce(function (a, x) { return a + rank(x); }, 0); }
    function total() { var n = 0; for (var i = 0; i < trees.length; i++) n += treePoints(i); return n; }
    function need(x) { return x.requiredPoints || x.row * 5; }
    function pointsBelow(ti, row) { return trees[ti].talents.reduce(function (a, x) { return a + (x.row < row ? rank(x) : 0); }, 0); }
    function prereqsMet(x) { return (x.requires || []).every(function (q) { var p = byId[q.id]; return p && rank(p) >= q.qty; }); }
    function tierMet(x) { return pointsBelow(x._tree, x.row) >= need(x); }
    function canAdd(x) { return total() < MAX_POINTS && rank(x) < x.ranks.length && tierMet(x) && prereqsMet(x); }
    function canRemove(x) {
      var r = rank(x);
      if (!r) return false;
      var t = trees[x._tree].talents;
      for (var i = 0; i < t.length; i++) {
        var u = t[i];
        if (!rank(u)) continue;
        var q = (u.requires || []).filter(function (q) { return q.id === x.id; })[0];
        if (q && r - 1 < q.qty) return false;
        if (u.row > x.row && pointsBelow(x._tree, u.row) - 1 < need(u)) return false;
      }
      return true;
    }
    function valid() {
      if (total() > MAX_POINTS) return false;
      return trees.every(function (t) { return t.talents.every(function (x) {
        return rank(x) <= x.ranks.length && (!rank(x) || (tierMet(x) && prereqsMet(x)));
      }); });
    }

    // Share code: one digit per talent in row/col order, trees joined by "-".
    function code() {
      return trees.map(function (t) {
        return t.talents.map(function (x) { return rank(x); }).join("").replace(/0+$/, "");
      }).join("-").replace(/-+$/, "");
    }
    function applyCode(c) {
      ranks = {};
      var parts = String(c || "").split("-");
      trees.forEach(function (t, ti) {
        var s = parts[ti] || "";
        t.talents.forEach(function (x, i) { var n = parseInt(s.charAt(i), 10) || 0; if (n) ranks[x.id] = n; });
      });
      if (!valid()) ranks = {};
    }
    function applyPreset(list) {
      ranks = {};
      (list || []).forEach(function (p) { var x = byName[String(p[0]).toLowerCase()]; if (x) ranks[x.id] = parseInt(p[1], 10) || 0; });
      if (!valid()) ranks = {};
    }
    var initial = null;
    function captureInitial() { initial = JSON.stringify(ranks); }

    if (opts.code) applyCode(opts.code); else applyPreset(opts.preset);
    captureInitial();
    // Compact mode opens on the tree with the most points.
    trees.forEach(function (t, ti) { if (treePoints(ti) > treePoints(active)) active = ti; });

    // Rendering
    function cellBox(row, col) {
      var cs = getComputedStyle(el);
      var size = parseFloat(cs.getPropertyValue("--cell")) || 46, gap = parseFloat(cs.getPropertyValue("--gap")) || 14;
      return { x: col * (size + gap), y: row * (size + gap), s: size };
    }
    function arrowsHTML(t) {
      var html = "";
      t.talents.forEach(function (x) {
        (x.requires || []).forEach(function (q) {
          var p = byId[q.id];
          if (!p) return;
          var a = cellBox(p.row, p.col), b = cellBox(x.row, x.col), w = 4, key = ' data-from="' + p.id + '" data-qty="' + q.qty + '"';
          var bar = function (l, tp, wd, ht) { return '<span class="tc-arrow"' + key + ' style="left:' + l + "px;top:" + tp + "px;width:" + wd + "px;height:" + ht + 'px"></span>'; };
          var head = function (kind, l, tp) { return '<span class="tc-arrow tc-hd' + kind + '"' + key + ' style="left:' + l + "px;top:" + tp + 'px"></span>'; };
          if (p.row === x.row) {
            var midY = a.y + a.s / 2;
            if (p.col < x.col) { html += bar(a.x + a.s, midY - w / 2, b.x - a.x - a.s - 6, w) + head(" tc-r", b.x - 8, midY - 6); }
            else { html += bar(b.x + b.s + 6, midY - w / 2, a.x - b.x - b.s - 6, w) + head(" tc-l", b.x + b.s, midY - 6); }
          } else {
            var cx = b.x + b.s / 2 - w / 2, top = a.y + a.s;
            if (p.col !== x.col) {
              var fromX = p.col < x.col ? a.x + a.s : a.x, toX = cx + (p.col < x.col ? w : 0);
              html += bar(Math.min(fromX, toX), a.y + a.s / 2 - w / 2, Math.abs(toX - fromX), w);
              top = a.y + a.s / 2 - w / 2;
            }
            html += bar(cx, top, w, b.y - top - 6) + head("", b.x + b.s / 2 - 6, b.y - 8);
          }
        });
      });
      return html;
    }
    function render() {
      el.classList.add("tc");
      el.classList.toggle("tc-compact", compact);
      el.style.setProperty("--c", cls.color);
      var bar = compact
        ? '<div class="tc-bar"><span class="tc-stat">Points <b data-tc="spent">0</b> / 51</span><span class="tc-stat">Level <b data-tc="level">—</b></span>' +
          '<button type="button" class="tc-btn tc-danger" data-tc-act="reset">Reset to build</button>' +
          '<button type="button" class="tc-btn" data-tc-act="copy">Copy link</button>' +
          '<a class="tc-btn" data-tc="open" href="talents.html">Open in Talent Calc</a></div>' +
          '<div class="tc-tabs" role="tablist">' + trees.map(function (t, ti) {
            return '<button type="button" role="tab" data-tab="' + ti + '" aria-selected="' + (ti === active) + '">' + esc(t.name) + '<span class="tc-n" data-pts="' + ti + '">0</span></button>';
          }).join("") + "</div>"
        : '<div class="tc-bar"><span class="tc-stat tc-split">Build <b data-tc="split">0 / 0 / 0</b></span><span class="tc-stat">Spent <b data-tc="spent">0</b> / 51</span>' +
          '<span class="tc-stat tc-left">Left <b data-tc="left">51</b></span><span class="tc-stat">Level <b data-tc="level">—</b></span>' +
          '<button type="button" class="tc-btn" data-tc-act="copy">Copy link</button><button type="button" class="tc-btn tc-danger" data-tc-act="reset">Reset</button></div>' +
          '<p class="tc-hint">Click to add a point, right-click to remove, Shift-click to max. On a phone, tap a talent for + and − buttons.</p>';
      var html = trees.map(function (t, ti) {
        var cells = t.talents.map(function (x) {
          return '<button type="button" class="tc-cell" data-id="' + x.id + '" style="grid-row:' + (x.row + 1) + ";grid-column:" + (x.col + 1) +
            '" aria-label="' + esc(x.name) + '"><img src="' + ICON + x.icon + '.jpg" alt="" loading="lazy"><span class="tc-rk"></span></button>';
        }).join("");
        return '<section class="tc-tree" data-tree="' + ti + '"' + (compact && ti !== active ? " hidden" : "") + '><div class="tc-head"><h3>' + esc(t.name) +
          '</h3><span class="tc-pts" data-pts="' + ti + '">0</span><button type="button" class="tc-reset-tree" data-reset="' + ti +
          '" aria-label="Reset ' + esc(t.name) + '" title="Reset this tree">×</button></div><div class="tc-grid">' + arrowsHTML(t) + cells + "</div></section>";
      }).join("");
      el.innerHTML = bar + '<div class="tc-trees">' + html + "</div>";
      update(false);
    }
    function q(sel) { return el.querySelector(sel); }
    function update(changed) {
      var spent = total();
      el.querySelectorAll(".tc-cell").forEach(function (c) {
        var x = byId[c.dataset.id], r = rank(x), m = x.ranks.length;
        c.className = "tc-cell" + (r >= m ? " tc-max" : r ? " tc-some" : canAdd(x) ? " tc-avail" : "");
        c.querySelector(".tc-rk").textContent = r + "/" + m;
      });
      el.querySelectorAll(".tc-arrow").forEach(function (a) { a.classList.toggle("tc-on", rank(byId[a.dataset.from]) >= +a.dataset.qty); });
      el.querySelectorAll("[data-pts]").forEach(function (s) { s.textContent = treePoints(+s.dataset.pts); });
      var set = function (k, v) { var n = q('[data-tc="' + k + '"]'); if (n) n.textContent = v; };
      set("split", trees.map(function (t, ti) { return treePoints(ti); }).join(" / "));
      set("spent", spent);
      set("left", MAX_POINTS - spent);
      set("level", spent ? String(spent + 9) : "—");
      var open = q('[data-tc="open"]');
      if (open) open.href = "talents.html#" + self.encode();
      if (changed && typeof opts.onChange === "function") opts.onChange(self);
      if (tipState && tipState.inst === self) showTip(tipState.x, tipState.anchor, tipState.touch);
    }

    function add(x, max) { var ch = false; while (canAdd(x)) { ranks[x.id] = rank(x) + 1; ch = true; if (!max) break; } if (ch) update(true); }
    function remove(x, all) {
      var ch = false;
      while (canRemove(x)) { ranks[x.id] = rank(x) - 1; if (!ranks[x.id]) delete ranks[x.id]; ch = true; if (!all) break; }
      if (ch) update(true);
    }

    // Tooltip
    function descHTML(s) { return esc(s).replace(/\n/g, "<br>"); }
    function showTip(x, anchor, touch) {
      ensureTip();
      tipState = { inst: self, x: x, anchor: anchor, touch: touch };
      var r = rank(x), m = x.ranks.length, d = x.descriptions || {};
      var html = '<p class="tc-tn">' + esc(x.name) + '</p><p class="tc-tr">Rank ' + r + "/" + m + "</p>";
      html += '<p class="tc-td">' + descHTML(d[Math.max(r, 1)] || "") + "</p>";
      if (r && r < m && d[r + 1]) html += '<p class="tc-tl">Next rank</p><p class="tc-td">' + descHTML(d[r + 1]) + "</p>";
      if (!tierMet(x)) html += '<p class="tc-req">Requires ' + need(x) + " points in " + esc(trees[x._tree].name) + "</p>";
      (x.requires || []).forEach(function (rq) {
        var p = byId[rq.id];
        if (p && rank(p) < rq.qty) html += '<p class="tc-req">Requires ' + rq.qty + " point" + (rq.qty > 1 ? "s" : "") + " in " + esc(p.name) + "</p>";
      });
      html += '<p class="tc-how">Click: +1 · Right-click: −1 · Shift-click: max</p>';
      html += '<div class="tc-ctl"><button type="button" data-act="minus" aria-label="Remove a point">−</button><button type="button" data-act="plus" aria-label="Add a point">+</button><button type="button" class="tc-close" data-act="close">Close</button></div>';
      tip.innerHTML = html;
      tip.className = "tc-tip" + (touch ? " tc-touch" : "");
      tip.style.setProperty("--c", cls.color);
      tip.hidden = false;
      if (!touch) {
        var b = anchor.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
        var left = b.right + 12 + w > window.innerWidth ? Math.max(8, b.left - w - 12) : b.right + 12;
        tip.style.left = left + "px";
        tip.style.top = Math.min(Math.max(8, b.top), window.innerHeight - h - 8) + "px";
      }
    }

    // Events (delegated on the root)
    el.addEventListener("click", function (e) {
      var act = e.target.closest("[data-tc-act]");
      if (act) {
        if (act.dataset.tcAct === "reset") { ranks = compact ? JSON.parse(initial) : {}; update(true); }
        else if (act.dataset.tcAct === "copy") {
          var url = new URL("talents.html#" + self.encode(), location.href).href;
          var done = function () { act.textContent = "Copied!"; setTimeout(function () { act.textContent = "Copy link"; }, 1500); };
          if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, function () { window.prompt("Copy this link:", url); });
          else window.prompt("Copy this link:", url);
        }
        return;
      }
      var tab = e.target.closest("[data-tab]");
      if (tab) {
        active = +tab.dataset.tab;
        el.querySelectorAll("[data-tab]").forEach(function (b) { b.setAttribute("aria-selected", String(+b.dataset.tab === active)); });
        el.querySelectorAll(".tc-tree").forEach(function (t) { t.hidden = +t.dataset.tree !== active; });
        hideTip();
        return;
      }
      var reset = e.target.closest("[data-reset]");
      if (reset) { trees[+reset.dataset.reset].talents.forEach(function (x) { delete ranks[x.id]; }); update(true); return; }
      var c = e.target.closest(".tc-cell");
      if (!c) return;
      var x = byId[c.dataset.id];
      if (lastPointer === "touch" || lastPointer === "pen") { showTip(x, c, true); return; }
      add(x, e.shiftKey);
    });
    el.addEventListener("contextmenu", function (e) {
      var c = e.target.closest(".tc-cell");
      if (!c) return;
      e.preventDefault();
      remove(byId[c.dataset.id], e.shiftKey);
    });
    el.addEventListener("keydown", function (e) {
      var c = e.target.closest(".tc-cell");
      if (!c) return;
      var x = byId[c.dataset.id];
      if (e.key === "-" || e.key === "Backspace" || e.key === "Delete") { e.preventDefault(); remove(x, e.shiftKey); }
      else if (e.key === "+" || e.key === "=") { e.preventDefault(); add(x, e.shiftKey); }
    });
    el.addEventListener("mouseover", function (e) {
      var c = e.target.closest(".tc-cell");
      if (c && lastPointer === "mouse") showTip(byId[c.dataset.id], c, false);
    });
    el.addEventListener("mouseout", function (e) {
      var rel = e.relatedTarget;
      if (tipState && !tipState.touch && e.target.closest(".tc-cell") && !(rel && rel.closest && rel.closest(".tc-cell"))) hideTip();
    });
    el.addEventListener("focusin", function (e) {
      var c = e.target.closest(".tc-cell");
      if (c && lastPointer !== "touch") showTip(byId[c.dataset.id], c, false);
    });
    el.addEventListener("focusout", function () { if (tipState && !tipState.touch) hideTip(); });

    // Public API
    this.cls = cls;
    this.encode = function () { var c = code(); return cls.id + (c ? "/" + c : ""); };
    this.reset = function () { ranks = {}; captureInitial(); update(true); };
    this.setCode = function (c) { applyCode(c); update(false); };
    this._add = add;
    this._remove = remove;
    ensureTip();
    render();
  }

  window.TalentCalc = {
    CLASSES: CLASSES,
    ICON: ICON,
    DATA_URL: DATA_URL,
    classById: classById,
    load: load,
    mount: function (el, opts) { return load().then(function (raw) { return new Calc(el, raw, opts || {}); }); },
    mountSync: function (el, raw, opts) { return new Calc(el, raw, opts || {}); }
  };
})();
