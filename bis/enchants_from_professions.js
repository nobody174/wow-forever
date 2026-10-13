// Prints professions.html's BiS enchant list (DATA) as JSON, for bis/build_bis.py.
// The page's own script is evaluated (from `var FC =` to the end of `var DATA = [...]`), so the
// professions page stays the one place enchants are edited.
// Usage: node bis/enchants_from_professions.js [path/to/professions.html]
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const file = process.argv[2] || path.join(__dirname, "..", "professions.html");
const html = fs.readFileSync(file, "utf8");
const start = html.indexOf("var FC = ");
const data = html.indexOf("var DATA = [", start);
const end = html.indexOf("\n  ];", data);
if (start < 0 || data < 0 || end < 0) {
  console.error("professions.html: could not find `var FC =` / `var DATA = [` ... `];`");
  process.exit(1);
}
const ctx = {};
vm.createContext(ctx);
vm.runInContext(html.slice(start, end + 5) + "\nthis.DATA = DATA;", ctx);
const out = ctx.DATA.map((x) => ({
  name: x.name, prof: x.prof, skill: x.skill, slot: x.slot, eff: x.eff, specs: x.specs,
}));
process.stdout.write(JSON.stringify(out) + "\n");
