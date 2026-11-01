/* The plan progress string, site side. Same format as addon/RoadToForever/Progress.lua (read its header):
     R2FP1:<base64( "v=1\n" + plan + RS + level + RS + ids joined by US )>
   Works in the browser (window.R2FProgress) and in node (module.exports) so the addon tests can run both
   sides against each other. No character name, realm or guild is ever put in the string. */
(function (root) {
  "use strict";
  var PREFIX = "R2FP1:", MAX_LEN = 2048, MAX_ID = 40, RS = "\x1e", US = "\x1f";

  // ids: array of step ids. Returns the string, or null when the result would pass the 2 KB cap.
  function encode(plan, level, ids) {
    level = Math.floor(Number(level) || 0);
    if (level < 0 || level > 60) level = 0;
    var text = "v=1\n" + plan + RS + level + RS + ids.join(US);
    var out = PREFIX + root.btoa(text);
    return out.length > MAX_LEN ? null : out;
  }

  // Returns { plan, level, ids: [..] } or { error: "..." }. Ids that are malformed are dropped.
  function decode(input) {
    var s = String(input == null ? "" : input).replace(/\s+/g, "");
    if (!s) return { error: "Paste a progress string first." };
    if (s.length > MAX_LEN) return { error: "That string is too long to be a progress string." };
    var ver = /^R2FP(\d+):/.exec(s);
    if (!ver) return { error: "That is not a Road to Forever progress string." };
    if (Number(ver[1]) !== 1) return { error: "That string is from a newer version. Reload the page, or update the addon." };
    var text;
    try { text = root.atob(s.slice(PREFIX.length)); } catch (e) { return { error: "That is not a Road to Forever progress string." }; }
    var m = /^v=1\n([^\x1e]*)\x1e([^\x1e]*)\x1e([^\x1e]*)$/.exec(text);
    if (!m) return { error: "That is not a Road to Forever progress string." };
    var level = Number(m[2]);
    if (m[2] === "" || !(level >= 0 && level <= 60) || Math.floor(level) !== level) return { error: "That is not a Road to Forever progress string." };
    var seen = {}, ids = [];
    (m[3] === "" ? [] : m[3].split(US)).forEach(function (id) {
      if (id && id.length <= MAX_ID && /^[\w-]+$/.test(id) && !seen[id]) { seen[id] = true; ids.push(id); }
    });
    return { plan: m[1], level: level, ids: ids };
  }

  var api = { encode: encode, decode: decode, MAX_LEN: MAX_LEN };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.R2FProgress = api;
})(typeof window !== "undefined" ? window : globalThis);
