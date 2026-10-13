// Prints professions.html's BiS enchant list (DATA) as JSON, for bis/build_bis.py.
// The page's own script is evaluated (from `var FC =` to the end of `var LADDER = {...}`), so the
// professions page stays the one place enchants are edited.
// Each row carries `alts`: the 2nd and 3rd best stand-ins of the page's LADDER (LADDER[name].alts, found in ALT or
// DATA by name) with their effect, profession and skill, so Mr.BiZ can list them under the best one.
// `--names` prints every enchant name the page knows (DATA + ALT), for bis/tools/wago_enchant_ids.py.
// Usage: node bis/enchants_from_professions.js [--names] [path/to/professions.html]
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const args = process.argv.slice(2);
const namesOnly = args.includes("--names");
const file = args.filter((a) => !a.startsWith("--"))[0] || path.join(__dirname, "..", "professions.html");
const html = fs.readFileSync(file, "utf8");
const start = html.indexOf("var FC = ");
const data = html.indexOf("var DATA = [", start);
const ladder = html.indexOf("var LADDER = {", data);
const end = html.indexOf("\n  };", ladder);
if (start < 0 || data < 0 || ladder < 0 || end < 0) {
  console.error("professions.html: could not find `var FC =` / `var DATA = [` / `var LADDER = {` ... `};`");
  process.exit(1);
}
const ctx = {};
vm.createContext(ctx);
vm.runInContext(html.slice(start, end + 5) + "\nthis.DATA = DATA; this.ALT = ALT; this.LADDER = LADDER;", ctx);

const byName = {};
for (const a of ctx.ALT) byName[a.name] = a;
for (const d of ctx.DATA) byName[d.name] = byName[d.name] || d;

if (namesOnly) {
  process.stdout.write(JSON.stringify(Object.keys(byName).sort()) + "\n");
  process.exit(0);
}

const out = ctx.DATA.map((x) => {
  const row = { name: x.name, prof: x.prof, skill: x.skill, slot: x.slot, eff: x.eff, specs: x.specs };
  const lad = ctx.LADDER[x.name];
  const alts = ((lad && lad.alts) || []).slice(0, 2).map((n) => byName[n]).filter(Boolean)
    .map((a) => ({ name: a.name, eff: a.eff, prof: a.prof || x.prof, skill: a.skill }));
  if (alts.length) row.alts = alts;
  return row;
});
process.stdout.write(JSON.stringify(out) + "\n");
