// Reads the launch plan page's inline WAYPOINTS and prints a JSON list of problems with the "/bizway <zone> <x> <y> <label>" line
// each location button copies (zone words, two coordinates between 0 and 100, a label). Run by run_tests.py.
const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "..", "launch-plan.html"), "utf8");
const m = html.match(/^  var WAYPOINTS = \{[\s\S]*?^  \};$/m);
if (!m) { console.log(JSON.stringify({ error: "no WAYPOINTS block" })); process.exit(0); }
const WAYPOINTS = new Function(m[0] + "\nreturn WAYPOINTS;")();
// The pattern Nav.WayCommand uses: words, then two numbers, then the label.
const pat = /^(.+?)[\s,]+([\d.]+)[\s,]+([\d.]+)\s*(.*)$/;
const problems = [];
let n = 0;
for (const [id, w] of Object.entries(WAYPOINTS)) {
  (w.wp || []).forEach((p, i) => {
    n++;
    const line = p[0] + " " + p[1] + " " + p[2] + " " + p[3];
    const r = pat.exec(line);
    const x = r && Number(r[2]), y = r && Number(r[3]);
    if (!r || r[1].trim() === "" || !(x >= 0 && x <= 100) || !(y >= 0 && y <= 100) || r[1] !== p[0])
      problems.push(id + "[" + i + "]: " + line);
    if (typeof p[3] !== "string" || p[3].trim() === "") problems.push(id + "[" + i + "]: empty label");
  });
}
console.log(JSON.stringify({ count: n, problems }));
