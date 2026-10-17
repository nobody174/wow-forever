"""Does the Classic source data (classic_sources.py) agree with ForeverDB's source sentences for its picks?
Only the "Drops from <creature>, N%" sentences have a number to compare; the rest are counted by coverage."""
import collections
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S = json.load(open(ROOT / "bis" / "own" / "cache" / "classic_sources.json"))
picks = {}
for f in glob.glob(str(ROOT / "bis" / "raw" / "*.json")):
    for s in json.load(open(f))["slots"]:
        b = s.get("best")
        if b:
            picks[b["id"]] = b
cnt, bad = collections.Counter(), []
for i, b in picks.items():
    cnt[(b.get("conf"), str(i) in S)] += 1
    m = re.match(r"Drops from (.+?)(?: in .+?)?, ([\d.]+)%", b.get("src") or "")
    if m and str(i) in S:
        name, p = m.group(1), float(m.group(2))
        recs = [r for r in S[str(i)] if r["t"] == "drop" and r["n"] == name]
        ok = any(abs((r.get("p") or 0) - p) < max(0.6, 0.05 * p) for r in recs)
        cnt["drop chance agrees" if ok else "drop chance differs"] += 1
        if not ok and len(bad) < 10:
            bad.append((i, b["name"], b["src"], sorted({(r["n"], r.get("p")) for r in S[str(i)] if r["t"] == "drop"})[:3]))
for k, v in sorted(cnt.items(), key=str):
    print(k, v)
for b in bad:
    print(b)
