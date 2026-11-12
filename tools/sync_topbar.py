#!/usr/bin/env python3
"""Keeps the shared top bar CSS identical on every page (CLAUDE.md hard rule 3).

The CSS lives once, in CSS below. Every page carries a copy between the markers
`/* topbar:begin */` and `/* topbar:end */`; this script rewrites those copies.

  python tools/sync_topbar.py           rewrite the copies that differ
  python tools/sync_topbar.py --check   exit 1 if any copy differs (CI runs this), or if the nav links differ

The first run on a page that has no markers yet replaces everything from `.topbar{` up to the page's
`@media (prefers-reduced-motion:reduce){.topbar nav a` line. Page-specific topbar rules (the Home page's sound
buttons, the launch plan's progress bars) stay OUTSIDE the markers, in the page's own CSS.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["addons", "bis", "builds", "hunter", "index", "launch-plan", "library-books", "news", "professions", "auction-house", "talents",
         "template", "macros"]  # macros.html is generated from template.html; kept in step here so a stale build shows up
BEGIN, END = "/* topbar:begin */", "/* topbar:end */"

CSS = BEGIN + r"""
.topbar{position:sticky;top:0;z-index:20;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:12px;padding:14px 20px;background:var(--panel);border-bottom:1px solid var(--edge)}
.topbar .site-title{display:flex;align-items:center;min-height:24px;font:400 20px/1.1 var(--serif);color:var(--gold);text-decoration:none;letter-spacing:.01em;justify-self:start}
.topbar nav{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;justify-self:center}
@media (max-width:1180px){
  .topbar{grid-template-columns:1fr;justify-items:center;text-align:center}
  .topbar .site-title{justify-self:center}
}
.topbar nav a{
  font:600 13px/1 var(--sans);text-transform:uppercase;letter-spacing:.04em;
  color:var(--gold);text-decoration:none;padding:10px 16px;border-radius:6px;
  background:linear-gradient(180deg,#2A335A 0%,#161E38 55%,#10152C 100%);
  border:1px solid var(--edge);border-top-color:#4A5688;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.08), 0 2px 4px rgba(0,0,0,.35);
  transition:transform .08s ease, box-shadow .08s ease, border-color .08s ease;
}
.topbar nav a:hover{
  border-color:var(--gold);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.12), 0 0 10px rgba(255,209,0,.35), 0 2px 4px rgba(0,0,0,.35);
  transform:translateY(-1px);
}
.topbar nav a:active{transform:translateY(0);box-shadow:inset 0 1px 4px rgba(0,0,0,.5)}
.topbar nav a[aria-current="page"]{
  color:#0E1428;background:linear-gradient(180deg,#FFE566 0%,var(--gold) 55%,#C79C00 100%);
  border-color:#FFE566;box-shadow:inset 0 1px 0 rgba(255,255,255,.5), 0 0 10px rgba(255,209,0,.5);
}
/* Phones: one row, the links scroll sideways under an edge fade (footer.js scrolls the current page into view). */
@media (max-width:700px){
  .topbar{display:flex;align-items:center;justify-items:initial;text-align:left;gap:10px;padding:8px 12px}
  .topbar .site-title{flex:none;font-size:16px}
  .topbar nav{flex:1 1 auto;min-width:0;flex-wrap:nowrap;justify-content:flex-start;gap:6px;overflow-x:auto;overscroll-behavior-x:contain;scrollbar-width:none;
    -webkit-mask-image:linear-gradient(90deg,#000 calc(100% - 28px),transparent);mask-image:linear-gradient(90deg,#000 calc(100% - 28px),transparent)}
  .topbar nav::-webkit-scrollbar{display:none}
  .topbar nav::after{content:"";flex:none;width:22px}
  .topbar nav a{flex:none;white-space:nowrap;padding:8px 12px}
}
""" + END + "\n"


def nav_links(html):
    m = re.search(r'<div class="topbar">.*?<nav[^>]*>(.*?)</nav>', html, re.S)
    return re.findall(r'<a href="([^"]+)"[^>]*>([^<]*)</a>', m.group(1)) if m else None


def synced(html):
    """The page text with its topbar CSS replaced by CSS (LF line endings)."""
    if BEGIN in html:
        a, b = html.index(BEGIN), html.index(END) + len(END)
        return html[:a] + CSS.rstrip("\n") + html[b:]
    a = html.index(".topbar{")
    m = re.search(r"^@media \(prefers-reduced-motion:reduce\)\{\.topbar nav a", html[a:], re.M)
    if not m:
        raise SystemExit("no reduced-motion line after .topbar{ to anchor on")
    return html[:a] + CSS + html[a + m.start():]


def main():
    check = "--check" in sys.argv
    bad, links = [], {}
    for page in PAGES:
        path = os.path.join(ROOT, page + ".html")
        raw = open(path, encoding="utf-8", newline="").read()
        crlf = "\r\n" in raw
        html = raw.replace("\r\n", "\n")
        new = synced(html)
        links[page] = nav_links(html)
        if new != html:
            bad.append(page)
            if not check:
                open(path, "w", encoding="utf-8", newline="").write(new.replace("\n", "\r\n") if crlf else new)
    ref = links["bis"]
    for page, l in links.items():
        if l != ref:
            bad.append(page + " (nav links differ)")
    if check:
        if bad:
            print("top bar drift: " + ", ".join(bad) + "\nrun: python tools/sync_topbar.py (and python build.py for macros.html)")
            sys.exit(1)
        print("top bar identical on all pages")
    else:
        print("rewrote: " + (", ".join(bad) if bad else "nothing, already in sync"))


if __name__ == "__main__":
    main()
