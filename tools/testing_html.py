"""Builds addon/dev/TESTING.html (a checklist page) from addon/dev/TESTING.md.

Each open test gets its number, title, the steps, a status (not tested / done / needs more testing / not working) and a comment box.
Answers are kept in the browser (localStorage) and "Copy my answers" puts them in the reply format TESTING.md asks for
(`5.87 done`, `5.41 not working: <what you saw>`), ready to paste to Claude. Open the file by double-clicking it.
Run again after TESTING.md changes (a changed list keeps the answers of numbers that still exist).

Usage (repo root):  python tools/testing_html.py
"""
import html
import os
import re

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(ROOT, "addon", "dev", "TESTING.md")
OUT = os.path.join(ROOT, "addon", "dev", "TESTING.html")


def inline(text):
    """Escape, then **bold** and `code`."""
    t = html.escape(text)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return t


def steps_of(body):
    """Split a test's text into sentences (one step each), keeping ':' lead-ins and abbreviations together."""
    parts = re.split(r"(?<=[.?!])\s+(?=[A-Z(\"`])", body.strip())
    return [p for p in parts if p]


def parse(md):
    meta, tests, rest = [], [], []
    section = None
    for line in md.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        m = re.match(r"^- \*\*(\d+\.\d+)\s+(.*?)\*\*\s*(.*)$", line)
        if section == "To test" and m:
            num, head, body = m.groups()
            # the title may end with ':' inside the bold part
            tests.append({"num": num, "title": head.rstrip(":"), "body": body})
        elif section and section.startswith("Cannot") and line.strip():
            rest.append(line.strip())
        elif section is None and line.strip():
            meta.append(line.strip())
    return meta, tests, rest


def card(t):
    steps = "".join("<li>%s</li>" % inline(s) for s in steps_of(t["body"]))
    n = t["num"]
    return (
        '<section class="test" data-num="%s" id="t%s">'
        '<header><span class="num">%s</span><h2>%s</h2></header>'
        '<ol>%s</ol>'
        '<div class="answer">'
        '<select aria-label="Status for %s"><option value="">Not tested</option><option value="done">Done, works</option>'
        '<option value="needs more testing">Needs more testing</option><option value="not working">Not working</option></select>'
        '<textarea placeholder="What you saw (optional, needed for Not working)" rows="2"></textarea>'
        '</div></section>'
    ) % (n, n.replace(".", "_"), n, inline(t["title"]), steps, n)


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Road to Forever: open tests</title>
<style>
:root{--bg:#f6f4ef;--card:#fff;--ink:#1f1d1a;--dim:#6b665e;--line:#ddd7cb;--accent:#8a5a00;--ok:#2e7d32;--warn:#b26a00;--bad:#c62828}
@media (prefers-color-scheme:dark){:root{--bg:#161412;--card:#201d1a;--ink:#ece7de;--dim:#a39c90;--line:#3a352f;--accent:#e0a63b;--ok:#6fbf73;--warn:#e0a63b;--bad:#ef7b7b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,sans-serif}
main{max-width:820px;margin:0 auto;padding:16px}h1{font-size:1.4rem;margin:.2em 0}
.meta{color:var(--dim);font-size:.9rem}.meta p{margin:.2em 0}
.bar{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);display:flex;gap:8px;align-items:center;flex-wrap:wrap;z-index:2}
.bar .count{margin-right:auto;color:var(--dim)}button{font:inherit;padding:6px 12px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;cursor:pointer}
button.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
.test{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--line);border-radius:8px;margin:12px 0;padding:10px 14px}
.test.s-done{border-left-color:var(--ok)}.test.s-needs{border-left-color:var(--warn)}.test.s-bad{border-left-color:var(--bad)}
header{display:flex;gap:10px;align-items:baseline}.num{font-weight:700;color:var(--accent);font-variant-numeric:tabular-nums}h2{font-size:1rem;margin:0}
ol{margin:.5em 0 .7em 1.3em;padding:0}li{margin:.25em 0}code{background:rgba(127,127,127,.15);padding:0 4px;border-radius:3px;font-size:.9em}
.answer{display:flex;gap:8px;flex-wrap:wrap}select,textarea{font:inherit;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);padding:5px 8px}
textarea{flex:1;min-width:220px;resize:vertical}.rest{margin-top:24px;color:var(--dim);font-size:.9rem}
.rest h2{color:var(--ink)}.rest p{margin:.3em 0}.toast{color:var(--ok)}
</style></head><body><main>
<h1>Road to Forever: open tests</h1>
<div class="meta">%(meta)s</div>
<div class="bar"><span class="count" id="count"></span><span class="toast" id="toast"></span>
<button id="hide">Hide finished</button><button id="clear">Clear all answers</button><button class="primary" id="copy">Copy my answers</button></div>
%(cards)s
<div class="rest"><h2>Cannot be tested yet</h2>%(rest)s</div>
</main>
<script>
(function(){
var KEY="r2f-testing-answers",data={},hide=false;
try{data=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){data={}}
function save(){try{localStorage.setItem(KEY,JSON.stringify(data))}catch(e){}}
function cls(v){return v==="done"?"s-done":v==="needs more testing"?"s-needs":v==="not working"?"s-bad":""}
var tests=[].slice.call(document.querySelectorAll(".test"));
function paint(){
  var n=0;
  tests.forEach(function(el){
    var d=data[el.dataset.num]||{},v=d.s||"";
    el.className="test "+cls(v);
    el.style.display=(hide&&v==="done")?"none":"";
    if(v==="done")n++;
  });
  document.getElementById("count").textContent=n+" of "+tests.length+" done";
}
tests.forEach(function(el){
  var sel=el.querySelector("select"),ta=el.querySelector("textarea"),d=data[el.dataset.num]||{};
  sel.value=d.s||"";ta.value=d.c||"";
  function upd(){data[el.dataset.num]={s:sel.value,c:ta.value};save();paint()}
  sel.addEventListener("change",upd);ta.addEventListener("input",upd);
});
function toast(t){var e=document.getElementById("toast");e.textContent=t;setTimeout(function(){e.textContent=""},2500)}
document.getElementById("hide").onclick=function(){hide=!hide;this.textContent=hide?"Show finished":"Hide finished";paint()};
document.getElementById("clear").onclick=function(){if(confirm("Clear every answer?")){data={};save();tests.forEach(function(el){el.querySelector("select").value="";el.querySelector("textarea").value=""});paint()}};
document.getElementById("copy").onclick=function(){
  var out=[];
  tests.forEach(function(el){
    var d=data[el.dataset.num];if(!d||(!d.s&&!d.c))return;
    var s=d.s||"comment",c=(d.c||"").replace(/\\s+/g," ").trim();
    out.push(el.dataset.num+" "+s+(c?(s==="not working"||s==="comment"?": ":" - ")+c:""));
  });
  var text=out.join("\\n")||"(no answers yet)";
  function done(){toast("Copied "+out.length+" line(s)")}
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(done,function(){prompt("Copy:",text)})}
  else prompt("Copy:",text);
};
paint();
})();
</script></body></html>
"""


def main():
    md = open(SRC, encoding="utf-8").read()
    meta, tests, rest = parse(md)
    page = PAGE
    page = page.replace("%(meta)s", "".join("<p>%s</p>" % inline(m) for m in meta[1:]))
    page = page.replace("%(cards)s", "\n".join(card(t) for t in sorted(tests, key=lambda t: [int(x) for x in t["num"].split(".")])))
    page = page.replace("%(rest)s", "".join("<p>%s</p>" % inline(r) for r in rest))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print("wrote %s (%d tests)" % (OUT, len(tests)))


main()
