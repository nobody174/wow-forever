#!/usr/bin/env python3
"""Link checker for the static site: every internal link, anchor, query value and referenced file must resolve.

    python tools/check_links.py             # offline checks (what CI runs); exit 1 on any problem
    python tools/check_links.py --external  # also asks every external URL once (slow, needs a network, warnings only)

What it checks, per page (*.html):
  * href / src / content / fetch() targets that are local files: the file exists (query strings ignored).
  * "#id" links: the id exists on that page, or the fragment is a route the page itself understands (bis.html#hunter/survival,
    professions.html#bis/hunter, talents.html#legacy ...); routes are validated against the data behind them.
  * launch-plan.html?plan= / ?race= / ?class= / ?level= values name a real plan, race, class and level.
  * duplicate ids within one page, and manifest.webmanifest icon files.
Standard library only.
"""
import glob
import json
import os
import re
import sys
from urllib.parse import unquote, urlsplit, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLASSES = ["priest", "warlock", "mage", "rogue", "druid", "shaman", "hunter", "paladin", "warrior"]


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


PAGES = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "*.html")))
SOURCES = {p: read(p) for p in PAGES}


def static_ids(html):
    """Ids written in the markup (not those a script creates later)."""
    body = re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)
    return re.findall(r'\sid="([^"]+)"', body)


IDS = {p: static_ids(s) for p, s in SOURCES.items()}


# --- what the pages understand in the URL ---------------------------------------------------------------------------------
def block_keys(src, var):
    """Top-level keys of `var NAME = { key: ..., key: ... }` in a page script."""
    m = re.search(r"var %s = \{(.*?)^  \};" % var, src, flags=re.S | re.M)
    if not m:
        return None
    return re.findall(r"^    (\w+):", m.group(1), flags=re.M)


LP = SOURCES["launch-plan.html"]
LP_RACES = block_keys(LP, "RACES") or []
LP_PRESETS = block_keys(LP, "PRESETS") or []
LP_CLASSES = [c.lower() for c in (block_keys(LP, "CLASSES") or [])]
BIS_SPECS = set(json.loads(read("bis-data.json"))["specs"])
PROF_VIEWS = re.search(r"var VIEWS = \[([^\]]*)\]", SOURCES["professions.html"])
PROF_VIEWS = re.findall(r'"([^"]+)"', PROF_VIEWS.group(1)) if PROF_VIEWS else []


def route_ok(page, frag):
    """True/False when the page has a hash route for this fragment, None when the page has none."""
    f = unquote(frag).lower()
    if page == "bis.html":
        return f in BIS_SPECS
    if page == "professions.html":
        parts = f.split("/")
        if parts[0] not in PROF_VIEWS and parts[0] != "list":
            return False
        return len(parts) < 2 or parts[0] != "bis" or parts[1] in CLASSES
    if page == "talents.html":
        parts = f.split("/")
        return parts[0] == "legacy" or parts[0] in CLASSES
    if page == "launch-plan.html" and f == "buyable":
        return True  # opens the buyable quests drawer
    return None


def check_query(page, q, where, problems):
    """Only launch-plan.html has query routes."""
    qs = parse_qs(q)
    for k in qs:
        if k not in ("plan", "race", "class", "level", "mode"):
            problems.append("%s: %s has an unknown query key '%s'" % (page, where, k))
    if "plan" in qs and qs["plan"][0] not in LP_PRESETS and ":" not in qs["plan"][0]:
        problems.append("%s: %s ?plan=%s is not a plan preset" % (page, where, qs["plan"][0]))
    if "race" in qs and qs["race"][0] not in LP_RACES:
        problems.append("%s: %s ?race=%s is not a race" % (page, where, qs["race"][0]))
    if "class" in qs:
        if qs["class"][0] not in LP_CLASSES:
            problems.append("%s: %s ?class=%s is not a class" % (page, where, qs["class"][0]))
        elif "race" in qs and qs["race"][0] in LP_RACES:
            allowed = [c.lower() for c in re.findall(r'"(\w+)"', re.search(
                r"%s:\s*\{[^}]*?classes:\s*\[([^\]]*)\]" % qs["race"][0], LP, flags=re.S).group(1))]
            if qs["class"][0] not in allowed:
                problems.append("%s: %s a %s cannot be a %s (the page would fall back to another class)" % (
                    page, where, qs["race"][0], qs["class"][0]))
    if "level" in qs and not (qs["level"][0].isdigit() and 0 <= int(qs["level"][0]) <= 60):
        problems.append("%s: %s ?level=%s is not 0-60" % (page, where, qs["level"][0]))
    if "mode" in qs and qs["mode"][0] != "night":
        problems.append("%s: %s ?mode=%s is not 'night'" % (page, where, qs["mode"][0]))


# --- collecting the links -------------------------------------------------------------------------------------------------
def local_refs(html):
    """(kind, url) for every reference the markup or its scripts make to something on this site or the web."""
    out = []
    for m in re.finditer(r'\b(href|src)="([^"]*)"', html):
        out.append((m.group(1), m.group(2)))
    for m in re.finditer(r'<meta[^>]+(?:property|name)="(?:og:image|twitter:image|og:url)"[^>]*content="([^"]*)"', html):
        out.append(("meta", m.group(1)))
    for m in re.finditer(r'fetch\(\s*"([^"]+)"', html):
        out.append(("fetch", m.group(1)))
    return out


def split_url(url):
    u = urlsplit(url.replace("&amp;", "&"))
    return u.scheme, u.netloc, u.path, u.query, u.fragment


def main():
    external = "--external" in sys.argv
    problems, warnings, ext_urls = [], [], {}
    checked = 0

    for page in PAGES:
        html = SOURCES[page]
        seen, dupes = set(), set()
        for i in IDS[page]:
            (dupes if i in seen else seen).add(i)
        for d in sorted(dupes):
            problems.append("%s: id '%s' is used more than once" % (page, d))

        for kind, url in local_refs(html):
            url = url.strip()
            if not url or url.startswith(("mailto:", "data:", "javascript:", "tel:")):
                continue
            scheme, host, path, query, frag = split_url(url)
            if scheme in ("http", "https"):
                if host.endswith("nobody174.github.io") and path.startswith("/wow-forever/"):
                    path, scheme = path[len("/wow-forever/"):], ""
                else:
                    ext_urls.setdefault(url, []).append(page)
                    continue
            # a JS template piece, not a whole link
            if "'" in url or "${" in url or "+" in url:
                continue
            checked += 1
            where = "'%s'" % url
            target = path or page
            if path == "/":
                target = "index.html"
            if path and not path.startswith("/"):
                if not os.path.exists(os.path.join(ROOT, path)):
                    problems.append("%s: %s points to a file that does not exist" % (page, where))
                    continue
            elif path.startswith("/"):
                problems.append("%s: %s is root-relative (it breaks under /wow-forever/)" % (page, where))
                continue
            if kind == "fetch" and (frag or query):
                continue
            if query and target.endswith(".html"):
                if target == "launch-plan.html":
                    check_query(page, query, where, problems)
                else:
                    problems.append("%s: %s has a query string but %s does not read one" % (page, where, target))
            if frag and target.endswith(".html"):
                if frag == "":
                    continue
                ok = route_ok(target, frag)
                if ok is None:
                    ok = frag in IDS[target]
                if not ok:
                    problems.append("%s: %s has no '#%s' on %s" % (page, where, frag, target))
            elif frag == "" and url.endswith("#"):
                pass  # a bare "#" (JS-driven button); allowed

    # the manifest's icons and the files it names
    try:
        man = json.loads(read("manifest.webmanifest"))
        for ic in man.get("icons", []):
            checked += 1
            if not os.path.exists(os.path.join(ROOT, ic["src"])):
                problems.append("manifest.webmanifest: icon '%s' does not exist" % ic["src"])
        for key in ("start_url",):
            if key in man and not os.path.exists(os.path.join(ROOT, man[key].split("?")[0].split("#")[0] or "index.html")):
                problems.append("manifest.webmanifest: %s '%s' does not exist" % (key, man[key]))
    except FileNotFoundError:
        warnings.append("no manifest.webmanifest")

    if external:
        import urllib.request
        for url, pages in sorted(ext_urls.items()):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "road-to-forever-link-check"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    code = r.status
            except Exception as e:  # network trouble is a warning, never a failure
                code = getattr(e, "code", None) or type(e).__name__
            if code != 200:
                warnings.append("external %s answered %s (on %s)" % (url, code, ", ".join(sorted(set(pages)))))

    print("%d pages, %d local references, %d external URLs%s" % (
        len(PAGES), checked, len(ext_urls), "" if external else " (not asked: add --external)"))
    for w in warnings:
        print("WARN  " + w)
    for p in problems:
        print("FAIL  " + p)
    if problems:
        print("%d problem(s)" % len(problems))
        return 1
    print("links ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
