// Builds test fixtures for the addon's Lua tests from the REAL site code.
//
// It pulls `const D = ...`, `ALL`, `byOrder`, the XINDEX loop and the
// importString() function out of the generated macros.html and runs them
// unchanged, so the strings the Lua importer is tested against are byte-for-
// byte what "Copy import string" puts on the clipboard.
//
// Usage: node addon/tests/make_fixtures.js   (prints one JSON object)

const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..", "..");
const html = fs.readFileSync(path.join(root, "macros.html"), "utf8");

function grab(re, what) {
  const m = html.match(re);
  if (!m) throw new Error("make_fixtures: could not find " + what + " in macros.html");
  return m[0];
}

const siteCode = [
  grab(/^const D = .*;$/m, "const D"),
  grab(/^const ALL = .*;$/m, "const ALL"),
  grab(/^const byOrder = .*;$/m, "const byOrder"),
  grab(/^const XINDEX = \[\];[\s\S]*?^}$/m, "XINDEX loop"),
  grab(/^function importString\(\)\{[\s\S]*?^}$/m, "importString()"),
].join("\n");

// `sel` is the page's selection Set; importString() reads it as a free variable.
const make = new Function("sel", siteCode + "\nreturn {XINDEX, importString, D};");

function build(filter) {
  const sel = new Set();
  const probe = make(sel);
  for (const e of probe.XINDEX) if (filter(e)) sel.add(e.m.id);
  const records = probe.XINDEX.filter(e => sel.has(e.m.id)).map(e => ({
    id: e.m.id,
    class: e.m.id.slice(0, e.m.id.indexOf("/")),
    section: e.section,
    group: e.group,
    name: e.m.name,
    short: e.m.short,
    icon: e.m.icon || "",
    body: e.m.code,
    note: e.m.note || "",
  }));
  return { string: probe.importString(), records };
}

// btoa(unescape(encodeURIComponent(text))) exactly as the site does it.
const enc = text => btoa(unescape(encodeURIComponent(text)));
const b64cases = [
  "", "a", "ab", "abc", "abcd", "v=1\n",
  "Weapon swap: 1H+offhand ↔ 2H",
  "Raptor Strike — GCD",
  "æøå ÆØÅ € 🐉",
  "line1\nline2\x1Efield\x1Fx",
].map(text => ({ text, b64: enc(text) }));

const out = {
  warriorUniversal: build(e => e.cls === "Warrior" || e.cls === "Universal"),
  everything: build(() => true),
  // Small set with the two UTF-8 names (↔) and one icon macro.
  utf8: build(e => /↔|—/.test(e.m.name) || e.m.id === "ANY/Zoom"),
  b64cases,
  order: make(new Set()).D.order,
};
process.stdout.write(JSON.stringify(out));
