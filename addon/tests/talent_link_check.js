// Runs the REAL talentcalc.js (the site's talent calculator engine) in Node on
// a talent fixture and prints what it produces, so run_tests.py can compare it
// with Talents.lua on the same input (ADDON_PLAN.md 13.3: the ~hash must be
// identical on both sides, and Copy my build must encode like the site).
//
// talentcalc.js is a browser script; a tiny fake DOM (just the calls a
// calculator instance makes while rendering into a detached element) is
// enough to build real instances with TalentCalc.mountSync.
//
// Usage: node addon/tests/talent_link_check.js <fixture.json>   (prints JSON)
//   fixture = { talents: <Wowhead-format raw data>, scenarios: [{cls, ranks}] }

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..", "..");
const fixture = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const src = fs.readFileSync(path.join(root, "talentcalc.js"), "utf8");

function fakeEl() {
  return {
    classList: { add() {}, toggle() {} },
    style: { setProperty() {} },
    dataset: {},
    set innerHTML(_) {},
    get innerHTML() { return ""; },
    querySelectorAll() { return []; },
    querySelector() { return null; },
    addEventListener() {},
    appendChild() {},
    setAttribute() {},
  };
}
const window = { addEventListener() {}, innerWidth: 1200, innerHeight: 800 };
const sandbox = {
  window,
  document: { createElement: fakeEl, body: fakeEl(), head: fakeEl(), addEventListener() {} },
  getComputedStyle: () => ({ getPropertyValue: () => "" }),
  setTimeout,
};
vm.runInNewContext(src, sandbox, { filename: "talentcalc.js" });
const TC = window.TalentCalc;
const raw = fixture.talents;

const out = { hashes: {}, scenarios: [], clean: {} };
out.hashForBefore = TC.hashFor("warrior");   // no data seen yet -> ""
out.classes = {};
for (const c of TC.CLASSES) {
  out.hashes[c.id] = TC.treeHash(raw, c.id);
  out.classes[c.id] = c.trees.map(t => t[0]);   // tree ids in in-game tab order
}

for (const s of fixture.scenarios) {
  const preset = Object.entries(s.ranks || {});
  const inst = TC.mountSync(fakeEl(), raw, { cls: s.cls, preset });
  const link = inst.link();
  // Reading side: the link (with ~hash) and the bare old-style code must both
  // load the same build back.
  const body = link.slice(link.indexOf("/") + 1);
  const fromLink = TC.mountSync(fakeEl(), raw, { cls: s.cls, code: body });
  const bare = TC.cleanCode(body);
  const fromBare = TC.mountSync(fakeEl(), raw, { cls: s.cls, code: bare });
  // setCode (talents.html hashchange path) with a hash appended.
  const viaSet = TC.mountSync(fakeEl(), raw, { cls: s.cls });
  viaSet.setCode(body);
  out.scenarios.push({
    name: s.name, cls: s.cls, total: inst.total(), points: preset.reduce((a, p) => a + p[1], 0),
    encode: inst.encode(), link,
    reread: fromLink.encode(), rereadBare: fromBare.encode(), rereadSetCode: viaSet.encode(),
  });
}

// cleanCode on its own, including inputs a pasted link can have.
for (const s of ["05302", "05302~abcd", "--53041~0000", "~abcd", "", "3-0502~", "a~b~c"]) {
  out.clean[s] = TC.cleanCode(s);
}
// Reading a hashed link whose check has DIGITS where the tree still has
// talents: without the "ignore from ~" rule, "35~111" would read as
// 3,5,0,1,1,1 (a valid but wrong build). Both the mount path (opts.code) and
// setCode (talents.html's hashchange) must give exactly the digits before "~".
out.readHashed = {};
for (const code of ["35~111", "35~111-5", "--53041~1z9k", "3-0502~00"]) {
  const a = TC.mountSync(fakeEl(), raw, { cls: "warrior", code }).encode();
  const b = TC.mountSync(fakeEl(), raw, { cls: "warrior" });
  b.setCode(code);
  out.readHashed[code] = [a, b.encode()];
}
// hashFor once a calculator has seen the data (talentsaved.js's links).
out.hashForAfterMount = TC.hashFor("warrior");
out.hashForUnknownClass = TC.hashFor("deathknight");
process.stdout.write(JSON.stringify(out));
