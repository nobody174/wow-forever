// Snapshot of what the launch plan shows: every step of every phase, resolved for every plan (race x class, plus the
// presets), using the page's own allowed() / override() / resolve(). Used to prove that moving PHASES out of
// launch-plan.html into launch-plan-steps.json changed nothing, and to compare any two versions of the plan data.
//
//   node tools/plan_snapshot.js [--html launch-plan.html] [--steps launch-plan-steps.json] > snapshot.json
//   node tools/plan_snapshot.js ... --check snapshot.json     exit 1 and name the first difference
//
// --html   the page to read RACES, CLASSES, PRESETS and the functions from (default: ./launch-plan.html; use
//          `git show <commit>:launch-plan.html > old.html` to snapshot an older version)
// --steps  the steps file; without it the page's inline `var PHASES = {...};` is used (the old layout)

const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const args = process.argv.slice(2);
function opt(name) { const i = args.indexOf(name); return i === -1 ? null : args[i + 1]; }

const html = fs.readFileSync(path.resolve(opt("--html") || path.join(root, "launch-plan.html")), "utf8");
function grab(re, what) {
  const m = html.match(re);
  if (!m) throw new Error("plan_snapshot: could not find " + what + " in the page");
  return m[0];
}

const stepsFile = opt("--steps");
const parts = [
  grab(/^  var CLASS_ORDER = .*;$/m, "CLASS_ORDER"),
  grab(/^  var CLASSES = \{[\s\S]*?^  \};$/m, "CLASSES"),
  grab(/^  var RACE_ORDER = .*;$/m, "RACE_ORDER"),
  grab(/^  var RACES = \{[\s\S]*?^  \};$/m, "RACES"),
  grab(/^  var PRESETS = \{[\s\S]*?^  \};$/m, "PRESETS"),
  grab(/^  function planId\(sel\) .*$/m, "planId()"),
  grab(/^  function parsePlan\(id\) \{[\s\S]*?^  \}$/m, "parsePlan()"),
  grab(/^  function allPlans\(\) \{[\s\S]*?^  \}$/m, "allPlans()"),
  stepsFile ? "var PHASES = JSON.parse(" + JSON.stringify(fs.readFileSync(path.resolve(stepsFile), "utf8")) + ");"
            : grab(/^  var PHASES = \{[\s\S]*?^  \};$/m, "PHASES"),
  grab(/^  function allowed\(item, sel\) \{[\s\S]*?^  \}$/m, "allowed()"),
  grab(/^  function override\(item, sel\) \{[\s\S]*?^  \}$/m, "override()"),
  grab(/^  function resolve\(item, sel\) \{[\s\S]*?^  \}$/m, "resolve()"),
];
const site = new Function(parts.join("\n") + "\nreturn { PHASES, allPlans, parsePlan, resolve };")();

function snapshot() {
  const out = { phases: Object.keys(site.PHASES), plans: {} };
  for (const id of site.allPlans()) {
    const sel = site.parsePlan(id);
    out.plans[id] = {};
    for (const ph of Object.keys(site.PHASES)) {
      out.plans[id][ph] = [];
      for (const item of site.PHASES[ph]) {
        const r = site.resolve(item, sel);
        if (r) out.plans[id][ph].push(Object.assign({}, r, { only: item.only }));
      }
    }
  }
  // The raw data too (the overrides are what the resolved views cannot show for plans nobody has).
  out.raw = site.PHASES;
  return out;
}

// Key order does not matter for objects; array order does.
function canon(v) {
  if (Array.isArray(v)) return v.map(canon);
  if (v && typeof v === "object") {
    const o = {};
    for (const k of Object.keys(v).sort()) if (v[k] !== undefined) o[k] = canon(v[k]);
    return o;
  }
  return v;
}

function firstDiff(a, b, where) {
  if (JSON.stringify(a) === JSON.stringify(b)) return null;
  if (Array.isArray(a) && Array.isArray(b)) {
    for (let i = 0; i < Math.max(a.length, b.length); i++) {
      const d = firstDiff(a[i], b[i], where + "[" + i + "]");
      if (d) return d;
    }
  } else if (a && b && typeof a === "object" && typeof b === "object") {
    for (const k of new Set(Object.keys(a).concat(Object.keys(b)))) {
      const d = firstDiff(a[k], b[k], where + "." + k);
      if (d) return d;
    }
  }
  return where + ": " + JSON.stringify(a) + " != " + JSON.stringify(b);
}

const snap = canon(snapshot());
const checkFile = opt("--check");
if (checkFile) {
  const base = canon(JSON.parse(fs.readFileSync(path.resolve(checkFile), "utf8")));
  const d = firstDiff(base, snap, "snapshot");
  if (d) { console.error("plan differs from the baseline at " + d); process.exit(1); }
  const plans = Object.keys(snap.plans).length;
  const steps = Object.values(snap.plans).reduce((n, p) => n + Object.values(p).reduce((m, l) => m + l.length, 0), 0);
  console.log("plan identical to the baseline: " + plans + " plans, " + steps + " resolved steps, " + snap.phases.length + " phases");
} else {
  process.stdout.write(JSON.stringify(snap));
}
