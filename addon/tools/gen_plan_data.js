// Generates addon/RoadToForever/PlanData.lua (ADDON_PLAN 15.5) from the site's own
// launch-plan.html (RACES, CLASSES, PRESETS and the allowed()/override()/resolve() functions), the steps in
// launch-plan-steps.json (PHASES) and
// launch-plan-waypoints.json. build.py runs it; run_tests.py checks the checked-in file is
// up to date and compares the addon's plan filtering against the site's resolve().
//
// Usage:
//   node addon/tools/gen_plan_data.js            write addon/RoadToForever/PlanData.lua
//   node addon/tools/gen_plan_data.js --check    exit 1 if the file differs from a fresh generation
//   node addon/tools/gen_plan_data.js --validate  check launch-plan-steps.json (exit 1 and list every problem)
//   node addon/tools/gen_plan_data.js --stats   print JSON: plan step counts for data-version.json (build.py)
//   node addon/tools/gen_plan_data.js --expected print JSON: per plan id ("skyborne:HUNTER", "hunter", ...), the ids
//                                                + texts the SITE shows (its resolve()), for the tests

const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..", "..");
const OUT = path.join(root, "addon", "RoadToForever", "PlanData.lua");
const html = fs.readFileSync(path.join(root, "launch-plan.html"), "utf8");
const stepsText = fs.readFileSync(process.env.R2F_STEPS_FILE || path.join(root, "launch-plan-steps.json"), "utf8")  // R2F_STEPS_FILE: tests only;
const wpJson = JSON.parse(fs.readFileSync(path.join(root, "launch-plan-waypoints.json"), "utf8"));

// Only the launch-day phases (owner, 2026-10-09): not "before" (done before launch) or "beta".
const LAUNCH_PHASES = ["night", "p1", "p2", "p3"];

function grab(re, what) {
  const m = html.match(re);
  if (!m) throw new Error("gen_plan_data: could not find " + what + " in launch-plan.html");
  return m[0];
}

const siteCode = [
  grab(/^  var CLASS_ORDER = .*;$/m, "CLASS_ORDER"),
  grab(/^  var CLASSES = \{[\s\S]*?^  \};$/m, "CLASSES"),
  grab(/^  var RACE_ORDER = .*;$/m, "RACE_ORDER"),
  grab(/^  var RACES = \{[\s\S]*?^  \};$/m, "RACES"),
  grab(/^  var PRESETS = \{[\s\S]*?^  \};$/m, "PRESETS"),
  grab(/^  function planId\(sel\) .*$/m, "planId()"),
  grab(/^  function parsePlan\(id\) \{[\s\S]*?^  \}$/m, "parsePlan()"),
  grab(/^  function allPlans\(\) \{[\s\S]*?^  \}$/m, "allPlans()"),
  "var PHASES = JSON.parse(" + JSON.stringify(stepsText) + ");",
  grab(/^  function allowed\(item, sel\) \{[\s\S]*?^  \}$/m, "allowed()"),
  grab(/^  function override\(item, sel\) \{[\s\S]*?^  \}$/m, "override()"),
  grab(/^  function resolve\(item, sel\) \{[\s\S]*?^  \}$/m, "resolve()"),
].join("\n");
const site = new Function(siteCode + "\nreturn { CLASS_ORDER, CLASSES, RACE_ORDER, RACES, PRESETS, PHASES, allPlans, parsePlan, planId, resolve, override };")();

// ---------------------------------------------------------------------------------------------------------------
// Validation of launch-plan-steps.json (rules in launch-plan-steps.schema.json, plus what a schema cannot say:
// ids unique across every phase, race / class / preset names exist, every phase has a section on the page).
// `node addon/tools/gen_plan_data.js --validate` (build.py and CI run it) prints every problem and exits 1.
// ---------------------------------------------------------------------------------------------------------------
function validateSteps(steps) {
  const errs = [];
  const races = Object.keys(site.RACES), classes = Object.keys(site.CLASSES), presets = Object.keys(site.PRESETS);
  const ITEM_KEYS = ["id", "lvl", "t", "n", "tags", "only", "race", "cls", "preset", "quests", "reach"];
  const LAYER_KEYS = ["lvl", "t", "n", "tags", "quests", "reach"];
  const TAG_KINDS = ["dng", "unv", "opt"];
  const isObj = v => v !== null && typeof v === "object" && !Array.isArray(v);
  const nonEmpty = v => typeof v === "string" && v.trim() !== "";

  if (!isObj(steps)) return ["the steps file must be an object of phase -> list of steps"];
  const pagePhases = [...html.matchAll(/data-phase="([a-z0-9]+)"/g)].map(m => m[1]);
  for (const ph of pagePhases) if (!Array.isArray(steps[ph])) errs.push("phase '" + ph + "' has a section on the page but no list in the steps file");
  for (const ph of Object.keys(steps)) if (pagePhases.indexOf(ph) === -1) errs.push("phase '" + ph + "' has no <div class=\"phase\" data-phase> on the page");

  const seen = {};
  function tagsOk(tags, where) {
    if (!Array.isArray(tags)) return errs.push(where + ": tags must be a list");
    tags.forEach((t, i) => {
      if (!Array.isArray(t) || t.length !== 2 || TAG_KINDS.indexOf(t[0]) === -1 || !nonEmpty(t[1]))
        errs.push(where + ": tags[" + i + "] must be [" + TAG_KINDS.join(" | ") + ", text]");
    });
  }
  function fieldsOk(o, allowed, where) {
    for (const k of Object.keys(o)) if (allowed.indexOf(k) === -1) errs.push(where + ": unknown field '" + k + "'");
    if ("lvl" in o && !nonEmpty(o.lvl)) errs.push(where + ": lvl must be a non-empty string");
    if ("t" in o && !nonEmpty(o.t)) errs.push(where + ": t must be a non-empty string");
    if ("n" in o && typeof o.n !== "string") errs.push(where + ": n must be a string");
    if ("tags" in o) tagsOk(o.tags, where);
    if ("quests" in o && !(Array.isArray(o.quests) && o.quests.every(q => Number.isInteger(q) && q > 0))) errs.push(where + ": quests must be a list of quest ids");
    if ("reach" in o && !(Number.isInteger(o.reach) && o.reach >= 1 && o.reach <= 60)) errs.push(where + ": reach must be a level from 1 to 60");
  }
  function namesOk(map, known, kind, where) {
    if (!isObj(map)) return errs.push(where + ": '" + kind + "' must be an object");
    for (const key of Object.keys(map)) {
      const names = key.split(" ");
      for (const n of names) if (known.indexOf(n) === -1) errs.push(where + ": '" + kind + "' names unknown '" + n + "'");
      const v = map[key];
      if (v === false) continue;
      if (!isObj(v)) errs.push(where + ": " + kind + "." + key + " must be false or an object");
      else fieldsOk(v, LAYER_KEYS, where + " " + kind + "." + key);
    }
  }
  for (const ph of Object.keys(steps)) {
    if (!Array.isArray(steps[ph])) { errs.push("phase '" + ph + "' must be a list"); continue; }
    steps[ph].forEach((item, i) => {
      const where = ph + "[" + i + "]" + (isObj(item) && typeof item.id === "string" ? " (" + item.id + ")" : "");
      if (!isObj(item)) return errs.push(where + ": a step must be an object");
      if (!nonEmpty(item.id) || !/^[a-z0-9][a-z0-9-]*$/.test(item.id)) errs.push(where + ": id must be lowercase letters, digits and dashes");
      else if (seen[item.id]) errs.push(where + ": duplicate id (also in " + seen[item.id] + ")");
      else seen[item.id] = ph + "[" + i + "]";
      if (!("lvl" in item)) errs.push(where + ": missing lvl");
      if (!("t" in item)) errs.push(where + ": missing t (the title)");
      fieldsOk(item, ITEM_KEYS, where);
      if ("only" in item) {
        if (!isObj(item.only)) errs.push(where + ": only must be an object");
        else {
          for (const k of Object.keys(item.only)) {
            if (k !== "race" && k !== "cls") { errs.push(where + ": only.'" + k + "' is not race or cls"); continue; }
            const list = item.only[k], known = k === "race" ? races : classes;
            if (!Array.isArray(list) || list.length === 0) errs.push(where + ": only." + k + " must be a non-empty list");
            else for (const n of list) if (known.indexOf(n) === -1) errs.push(where + ": only." + k + " names unknown '" + n + "'");
          }
          if (Object.keys(item.only).length === 0) errs.push(where + ": only is empty");
        }
      }
      if ("race" in item) namesOk(item.race, races, "race", where);
      if ("cls" in item) namesOk(item.cls, classes, "cls", where);
      if ("preset" in item) namesOk(item.preset, presets, "preset", where);
    });
  }
  return errs;
}

// The site's "Buyable quests" list (second script block): QUESTS and its own PHASES array.
const buy = new Function([
  grab(/^  var QUESTS = \[[\s\S]*?^  \];$/m, "QUESTS"),
  grab(/^  var PHASES = \[[\s\S]*?^  \];$/m, "buy PHASES"),
].join("\n") + "\nreturn { QUESTS, PHASES };")();

// Phase headings: the page's own <h2 id="p1">Phase 1 — 12 → 20</h2>.
function heading(id) {
  const m = html.match(new RegExp('<h2 id="' + id + '">([\\s\\S]*?)</h2>'));
  if (!m) throw new Error("gen_plan_data: no heading for " + id);
  return plain(m[1]);
}

// HTML (links, strong, em, entities) -> plain text for the game's font strings.
function plain(s) {
  s = String(s == null ? "" : s)
    .replace(/<br\s*\/?>/gi, " ")
    .replace(/<a\s[^>]*>([\s\S]*?)<\/a>/gi, "$1")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/g, " ").replace(/&times;/g, "x").replace(/&rarr;/g, "->")
    .replace(/&quot;/g, '"').replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&")
    .replace(/\s+/g, " ").trim();
  if (s.indexOf("|") !== -1) throw new Error("gen_plan_data: '|' in plan text (game escape char): " + s);
  return s;
}

function lstr(s) {
  return '"' + String(s).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n").replace(/\r/g, "")
    .replace(/[\x00-\x08\x0b-\x1f]/g, c => "\\" + String(c.charCodeAt(0)).padStart(3, "0")) + '"';
}
function lnum(n) { return String(n); }

function tagsLua(tags) {
  return "{ " + (tags || []).map(t => "{ " + lstr(t[0]) + ", " + lstr(plain(t[1])) + " }").join(", ") + " }";
}

function fieldsLua(o, keys) {
  const parts = [];
  for (const k of keys) {
    if (!(k in o)) continue;
    if (k === "tags") parts.push("tags = " + tagsLua(o.tags));
    else if (k === "quests") parts.push("quests = { " + o.quests.map(q => lnum(Number(q))).join(", ") + " }");
    else if (k === "reach") parts.push("reach = " + lnum(Number(o.reach)));
    else parts.push(k + " = " + lstr(plain(o[k])));
  }
  return parts.join(", ");
}

// quests = quest ids that must all be turned in, reach = a level that counts as done (both: "Follow the plan").
const FIELDS = ["lvl", "t", "n", "tags", "quests", "reach"];

function layerLua(o) { return o === false ? "false" : "{ " + fieldsLua(o, FIELDS) + " }"; }

// One override map ({ "dwarf gnome": {...}, nightelf: false }) -> Lua, one entry per name (a key may list several).
function mapLua(map, names, what, id) {
  const seen = {};
  const parts = [];
  for (const key of Object.keys(map)) {
    for (const name of key.split(" ")) {
      if (names.indexOf(name) === -1) throw new Error("gen_plan_data: unknown " + what + " '" + name + "' in step " + id);
      if (seen[name]) throw new Error("gen_plan_data: " + what + " '" + name + "' is overridden twice in step " + id);
      seen[name] = true;
      parts.push(name + " = " + layerLua(map[key]));
    }
  }
  return parts.join(", ");
}

function listLua(a) { return "{ " + a.map(lstr).join(", ") + " }"; }

function itemLua(item) {
  let s = "      { id = " + lstr(item.id);
  const base = fieldsLua(item, FIELDS);
  if (base) s += ", " + base;
  if (item.only) {
    const o = [];
    if (item.only.race) o.push("race = " + listLua(item.only.race));
    if (item.only.cls) o.push("cls = " + listLua(item.only.cls));
    s += ",\n        only = { " + o.join(", ") + " }";
  }
  const ov = [];
  if (item.race) ov.push("race = { " + mapLua(item.race, site.RACE_ORDER, "race", item.id) + " }");
  if (item.cls) ov.push("cls = { " + mapLua(item.cls, site.CLASS_ORDER, "class", item.id) + " }");
  if (item.preset) ov.push("preset = { " + mapLua(item.preset, Object.keys(site.PRESETS), "preset", item.id) + " }");
  if (ov.length) s += ",\n        ov = { " + ov.join(", ") + " }";
  return s + " },";
}

function pointLua(p) {
  let s = "{ zone = " + lstr(p.zone);
  if (p.mapHint != null) s += ", mapHint = " + lnum(p.mapHint);
  if (p.x != null) s += ", x = " + lnum(p.x) + ", y = " + lnum(p.y);
  s += ", label = " + lstr(p.label);
  if (p.dungeon) s += ", dungeon = " + lstr(p.dungeon);
  s += ", conf = " + lstr(p.conf) + " }";
  return s;
}

function generate() {
  const ids = new Set();
  const out = [];
  out.push("-- PlanData.lua: the Launch Plan for the Plan tab.");
  out.push("-- GENERATED by addon/tools/gen_plan_data.js (run by build.py) from launch-plan.html (RACES, CLASSES, PHASES)");
  out.push("-- and launch-plan-waypoints.json. Do not edit by hand: change the site data and rebuild.");
  out.push("-- Only the launch-day phases are here: " + LAUNCH_PHASES.join(", ") + ".");
  out.push("-- Item rules (same as the site): `only` = shown to those races / classes only; then the layers of `ov` apply in");
  out.push("-- order race, class, preset: a table replaces the fields it names, `false` hides the step for good.");
  out.push("-- A plan id is \"race:CLASS\" (\"skyborne:HUNTER\") or a preset id (\"hunter\" = Skyborne Hunter + duo tips).");
  out.push("");
  out.push("local _, R2F = ...");
  out.push("");
  out.push("R2F.PlanData = {");
  out.push("  classOrder = " + listLua(site.CLASS_ORDER) + ",");
  out.push("  classes = {");
  for (const c of site.CLASS_ORDER) out.push("    " + c + " = { label = " + lstr(site.CLASSES[c].label) + " },");
  out.push("  },");
  out.push("  raceOrder = " + listLua(site.RACE_ORDER) + ",");
  out.push("  races = {");
  for (const r of site.RACE_ORDER) {
    const d = site.RACES[r];
    out.push("    " + r + " = { label = " + lstr(plain(d.label)) + ", start = " + lstr(plain(d.start)) + ", draft = " + (d.draft ? "true" : "false") +
      ", classes = " + listLua(d.classes) + " },");
  }
  out.push("  },");
  out.push("  presets = {");
  for (const id of Object.keys(site.PRESETS)) {
    const p = site.PRESETS[id];
    out.push("    " + id + " = { label = " + lstr(plain(p.label)) + ", race = " + lstr(p.race) + ", cls = " + lstr(p.cls) + ", extra = " + lstr(plain(p.extra)) + " },");
  }
  out.push("  },");
  out.push("  phases = {");
  for (const ph of LAUNCH_PHASES) {
    out.push("    { id = " + lstr(ph) + ", title = " + lstr(heading(ph)) + ", items = {");
    for (const item of site.PHASES[ph]) {
      if (ids.has(item.id)) throw new Error("gen_plan_data: duplicate step id " + item.id);
      ids.add(item.id);
      out.push(itemLua(item));
    }
    out.push("    } },");
  }
  out.push("  },");
  // The "Buyable quests" list of the site (quests whose objectives can be bought instead of farmed).
  out.push("  quests = {");
  out.push("    phases = { " + buy.PHASES.map(p => "{ id = " + lstr(p[0]) + ", title = " + lstr(plain(p[1])) + " }").join(", ") + " },");
  out.push("    list = {");
  const qids = new Set();
  for (const q of buy.QUESTS) {
    if (qids.has(q.id)) throw new Error("gen_plan_data: duplicate quest id " + q.id);
    qids.add(q.id);
    let line = "      { id = " + lstr(q.id) + ", name = " + lstr(plain(q.name)) + ", zone = " + lstr(plain(q.zone)) +
      ", q = " + lnum(q.q) + ", phase = " + lstr(q.phase) + ", st = " + lstr(q.st) +
      ", items = { " + q.items.map(it => "{ " + lstr(plain(it[0])) + ", " + lnum(it[1]) + " }").join(", ") + " }";
    if (q.note) line += ", note = " + lstr(plain(q.note));
    if (q.xp) line += ", xp = " + lstr(plain(q.xp));
    out.push(line + " },");
  }
  out.push("    },");
  out.push("  },");
  // Waypoints: step id -> { default = {points}, <race> = {points} }.
  out.push("  waypoints = {");
  for (const id of Object.keys(wpJson.steps).sort()) {
    if (!ids.has(id)) throw new Error("gen_plan_data: waypoints for unknown or non-launch step " + id);
    const lists = wpJson.steps[id];
    const parts = [];
    for (const key of ["default"].concat(site.RACE_ORDER)) {
      if (!lists[key]) continue;
      parts.push(key + " = { " + lists[key].map(pointLua).join(", ") + " }");
    }
    for (const key of Object.keys(lists)) {
      if (key !== "default" && site.RACE_ORDER.indexOf(key) === -1) throw new Error("gen_plan_data: unknown race key " + key + " for " + id);
    }
    out.push("    [" + lstr(id) + "] = { " + parts.join(", ") + " },");
  }
  out.push("  },");
  out.push("}");
  return out.join("\n") + "\n";
}

// What the site shows per plan (its own resolve()): ids and plain texts, in order.
function expected() {
  const res = {};
  for (const id of site.allPlans()) {
    const sel = site.parsePlan(id);
    res[id] = [];
    for (const ph of LAUNCH_PHASES) {
      for (const item of site.PHASES[ph]) {
        const r = site.resolve(item, sel);
        if (!r) continue;
        res[id].push({ phase: ph, id: r.id, lvl: plain(r.lvl), t: plain(r.t), n: plain(r.n || ""),
          tags: (r.tags || []).map(t => [t[0], plain(t[1])]) });
      }
    }
  }
  const classes = {};
  for (const r of site.RACE_ORDER) classes[r] = site.RACES[r].classes;
  return { plans: res, phases: LAUNCH_PHASES, waypointSteps: Object.keys(wpJson.steps), raceClasses: classes,
           quests: buy.QUESTS.map(q => ({ id: q.id, name: plain(q.name), items: q.items.map(it => plain(it[0]) + ":" + it[1]), phase: q.phase })) };
}

// Step counts for the provenance strip: distinct step ids any race/class/preset shows, and how many of those
// carry the "unv" (unverified) tag in at least one plan. The page's "Verified only" toggle hides exactly these.
function stats() {
  const all = new Set(), unv = new Set();
  for (const id of site.allPlans()) {
    const sel = site.parsePlan(id);
    for (const ph of Object.keys(site.PHASES)) {
      for (const item of site.PHASES[ph]) {
        const r = site.resolve(item, sel);
        if (!r) continue;
        all.add(r.id);
        if ((r.tags || []).some(t => t[0] === "unv")) unv.add(r.id);
      }
    }
  }
  return { steps: all.size, unverified: unv.size };
}

const arg = process.argv[2];
if (arg !== "--stats" && arg !== "--expected") {
  const problems = validateSteps(site.PHASES);
  if (problems.length) {
    console.error("launch-plan-steps.json has " + problems.length + " problem(s):\n  " + problems.join("\n  "));
    process.exit(1);
  }
}
if (arg === "--validate") {
  console.log("launch-plan-steps.json is valid");
} else if (arg === "--stats") {
  process.stdout.write(JSON.stringify(stats()));
} else if (arg === "--expected") {
  process.stdout.write(JSON.stringify(expected()));
} else if (arg === "--check") {
  const fresh = generate();
  const cur = fs.existsSync(OUT) ? fs.readFileSync(OUT, "utf8").replace(/\r\n/g, "\n") : "";
  if (cur !== fresh) { console.error("PlanData.lua is out of date: run python build.py"); process.exit(1); }
} else {
  fs.writeFileSync(OUT, generate(), "utf8");
  console.log("PlanData.lua written");
}
