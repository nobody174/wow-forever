#!/usr/bin/env python3
"""Refresh prices.json (the site's fallback prices for the Professions cost views) from AHledger's live API.

    python tools/refresh_prices.py            # dry run: prints what would change
    python tools/refresh_prices.py --write    # writes prices.json

Same rule as professions.html's loadLive(): cheapest listing (min buyout), the median when fewer than FEW_LISTED are listed, nothing
when the item is not on the auction house. A material the AH does not list, one in LIVE_OFF (AHledger's price is known wrong) and one
sold by a vendor (VENDOR_ITEM: the page takes the cheaper of vendor and AH on its own) keep their old price. Needs a network; AHledger's
terms ask for the "Prices from AHledger" link wherever its prices show (it is on the page).
"""
import datetime
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKET = "forever.normal.alliance.eu"
FEW_LISTED = 10


def main():
    page = open(os.path.join(ROOT, "professions.html"), encoding="utf-8").read()
    mats = re.findall(r'\["(\w+)", "[^"]*", "\w+", (?:null|\d+), (\d+)\]', page)
    code_of = {int(item): code for code, item in mats}
    live_off = set(re.findall(r"LIVE_OFF = \{ (\w+):", page))
    vendor = re.search(r"VENDOR_ITEM = \{(.*?)\};", page, re.S)
    vendor_ids = {int(x) for x in re.findall(r"(\d+)\s*:", vendor.group(1))} if vendor else set()
    path = os.path.join(ROOT, "prices.json")
    data = json.load(open(path, encoding="utf-8"))
    ids = sorted(code_of)
    req = urllib.request.Request("https://api.ahledger.com/v1/tooltip/%s?items=%s" % (MARKET, ",".join(str(i) for i in ids)),
                                 headers={"User-Agent": "RoadToForever-price-refresh (https://github.com/nobody174/wow-forever)"})
    items = json.loads(urllib.request.urlopen(req, timeout=40).read().decode("utf-8"))["items"]
    changed = 0
    for it in items:
        code = code_of.get(it["id"])
        if not code or code in live_off or it["id"] in vendor_ids:
            continue
        few = (it.get("quantity") or 0) < FEW_LISTED and it.get("median") is not None
        v = it["median"] if few else (it["minBuyout"] if it.get("minBuyout") is not None else it.get("median"))
        if not isinstance(v, (int, float)) or v <= 0 or it.get("quantity") == 0:
            continue
        v = int(round(v))
        if data["prices"].get(code) != v:
            print("%-8s %-28s %s -> %s (%s listed)" % (code, it.get("name", ""), data["prices"].get(code), v, it.get("quantity")))
            data["prices"][code] = v
            changed += 1
    print("%d price(s) changed" % changed)
    if "--write" in sys.argv and changed:
        data["updated"] = datetime.date.today().isoformat()
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("prices.json written")


if __name__ == "__main__":
    main()
