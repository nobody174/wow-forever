"""Unit + smoke tests for the Road to Forever addon, run OUTSIDE the game.

Lua: real PUC Lua 5.1 (the language version WoW uses) through the `lupa`
Python package (`pip install --user lupa`; its wheel bundles lua51).
Fixtures: `node addon/tests/make_fixtures.js` runs the site's own
importString() code from macros.html, so the import strings tested here are
exactly what the site's "Copy import string" button produces.

Usage (repo root):  python addon/tests/run_tests.py
Exit code 0 = every check passed.
"""
import base64
import json
import os
import re
import subprocess
import sys

try:
    import lupa.lua51 as lua51
except ImportError:
    sys.exit("run_tests.py needs lupa with Lua 5.1: python -m pip install --user lupa")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
ADDON = os.path.join(ROOT, "addon", "RoadToForever")

FAILS = []
PASSES = 0


def check(cond, msg):
    global PASSES
    if cond:
        PASSES += 1
    else:
        FAILS.append(msg)
        print("FAIL:", msg)


def toc_files():
    files = []
    with open(os.path.join(ADDON, "RoadToForever.toc"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                files.append(line.replace("\\", "/"))
    return files


def fixtures():
    out = subprocess.run(["node", os.path.join(HERE, "make_fixtures.js")],
                         capture_output=True, check=True, cwd=ROOT)
    return json.loads(out.stdout.decode("utf-8"))


def new_runtime(templates=True):
    """Fresh Lua 5.1 state with the WoW stubs and the addon loaded in TOC order."""
    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    assert lua.eval("_VERSION") == "Lua 5.1", lua.eval("_VERSION")
    stubs = os.path.join(HERE, "wow_stubs.lua").replace("\\", "/")
    lua.execute('assert(loadfile("%s"))()' % stubs)
    if not templates:
        lua.execute("TEST.templates.PortraitFrameTemplate = nil; TEST.templates.ButtonFrameTemplate = nil;"
                    "TEST.templates.InputScrollFrameTemplate = nil; TEST.templates.UICheckButtonTemplate = nil;"
                    "TEST.templates.UIRadioButtonTemplate = nil")
    # Globals present before the addon loads, for the one-global audit.
    lua.execute("BEFORE = {} for k in pairs(_G) do BEFORE[k] = true end BEFORE.BEFORE = true")
    lua.execute("NS = {}")
    for rel in toc_files():
        path = os.path.join(ADDON, rel).replace("\\", "/")
        check(os.path.exists(path), "TOC file exists: " + rel)
        lua.execute('assert(loadfile("%s"))("RoadToForever", NS)' % path)
    return lua


def lua_table_to_list(t):
    return [t[i] for i in range(1, len(t) + 1)] if t is not None else []


# ---------------------------------------------------------------------------
def test_base64(lua, fx):
    dec = lua.eval("R2F.Base64.Decode")
    for case in fx["b64cases"]:
        check(dec(case["b64"]) == case["text"], "base64 decodes btoa output of %r" % case["text"])
    # Every byte value, cross-checked against Python's base64 (binary-safe
    # runtime: no UTF-8 conversion of Lua strings).
    raw = lua51.LuaRuntime(encoding=None)
    raw.execute(open(os.path.join(ADDON, "Base64.lua"), "rb").read().replace(b"local _, R2F = ...", b"local R2F = {} B64 = R2F"))
    for n in range(0, 8):
        data = bytes(range(256))[n:] + bytes([255, 0, 128])[:n % 3]
        check(raw.eval("B64.Base64.Decode")(base64.b64encode(data)) == data,
              "base64 binary round trip, %d bytes" % len(data))
    check(dec("YWJj\n ZA==") == "abcd", "base64 ignores whitespace")
    check(dec("YWJjZA") == "abcd", "base64 accepts missing padding")
    for bad in ["Y", "YW=J", "YW===", "@@@@", "YWJjZ", "Y W J j Z"]:
        check(dec(bad) is None, "base64 rejects %r" % bad)


def test_import_parse(lua, fx):
    parse = lua.eval("function(s) local a, b = R2F.Import.Parse(s) return a, b end")
    L = lua.eval("R2F.L")
    for key in ("warriorUniversal", "everything", "utf8"):
        fixture = fx[key]
        res, err = parse(fixture["string"])
        check(res is not None, "%s: parses (%s)" % (key, err))
        if res is None:
            continue
        recs = lua_table_to_list(res.records)
        check(len(recs) == len(fixture["records"]), "%s: record count %d == site %d" % (key, len(recs), len(fixture["records"])))
        check(res.skipped == 0, "%s: no skipped records" % key)
        for r, want in zip(recs, fixture["records"]):
            for field in ("id", "class", "section", "group", "name", "short", "body"):
                check(r[field] == want[field], "%s %s: field %s" % (key, want["id"], field))
            check((r.icon or "") == want["icon"], "%s %s: icon" % (key, want["id"]))
            check((r.note or "") == want["note"], "%s %s: note" % (key, want["id"]))

    def enc(text):
        return "R2F1:" + base64.b64encode(text.encode("utf-8")).decode()

    good = "ANY/Zoom\x1fANY\x1fUniversal\x1fMisc / UI\x1fZoom\x1fZoom\x1fAbility_Hunter_Pet_Bat\x1f/console x\x1f"
    cases = [
        ("garbage", L.IMPORT_BAD),
        ("R2F2:abcd", L.IMPORT_NEWER),
        ("R2F1:@@@", L.IMPORT_BAD),
        (enc("v=2\n" + good), L.IMPORT_NEWER),
        (enc("x=1\n" + good), L.IMPORT_BAD),
        (enc("v=1\n"), L.IMPORT_EMPTY),
        ("", L.IMPORT_BAD),
    ]
    for text, msg in cases:
        res, err = parse(text)
        check(res is None and err == msg, "bad string %r -> %r (got %r)" % (text[:20], msg, err))

    res, err = parse("\n  " + enc("v=1\n" + good) + "  \n")
    check(res is not None and len(res.records) == 1, "surrounding whitespace is ignored")
    rec = res.records[1]
    check(rec.icon == "Ability_Hunter_Pet_Bat" and rec.note is None, "empty note -> nil, icon kept")

    bad_records = [
        good.replace("\x1f/console x\x1f", "\x1f/console x"),                     # 8 fields
        good.replace("ANY/Zoom", "ANY/ThisIsSeventeen12").replace("\x1fZoom\x1fAbility", "\x1fThisIsSeventeen12\x1fAbility"),  # short 17
        good.replace("/console x", "x" * 256),                                    # body 256
        good.replace("ANY/Zoom\x1fANY", "FOO/Zoom\x1fFOO"),                         # unknown class
        good.replace("ANY/Zoom", "ANY/Other"),                                    # id != class/short
        good.replace("\x1fZoom\x1fZoom\x1f", "\x1fZoom\x1f\x1f"),                   # empty short
    ]
    payload = "v=1\n" + "\x1e".join([good] + bad_records + [good])
    res, err = parse(enc(payload))
    check(res is not None and len(res.records) == 1 and res.skipped == len(bad_records) + 1,
          "invalid + duplicate records are skipped and counted (got %s)" % str(res and (len(res.records), res.skipped)))
    ok16 = good.replace("ANY/Zoom", "ANY/Sixteen_chars_").replace("\x1fZoom\x1fAbility", "\x1fSixteen_chars_\x1fAbility")
    res, _ = parse(enc("v=1\n" + ok16.replace("Sixteen_chars_", "Sixteen_chars_16")))
    check(res is not None and len(res.records) == 1, "16-character short is accepted")
    res, _ = parse(enc("v=1\n" + good.replace("/console x", "y" * 255)))
    check(res is not None and len(res.records) == 1, "255-character body is accepted")
    res, _ = parse(enc("v=1\n" + good.replace("ANY/Zoom\x1fANY", "DRUID/Zoom\x1fDRUID")))
    check(res is not None and len(res.records) == 1, "DRUID is a known class token")
    utf8len = lua.eval("R2F.Import.utf8len")
    check(utf8len("1H\u21942H") == 5, "utf8len counts characters, not bytes")


def test_diff_and_library(lua, fx):
    lua.execute("R2F.Library.Init()")
    parse = lua.eval("function(s) local a, b = R2F.Import.Parse(s) return a, b end")
    diff = lua.eval("R2F.Import.Diff")
    lib = lua.eval("R2F.Library")
    preview = lua.eval("R2F.Import.PreviewText")

    wu, _ = parse(fx["warriorUniversal"]["string"])
    n = len(fx["warriorUniversal"]["records"])
    d = diff(wu, lib.db.library, "WARRIOR")
    check((d.total, d.new, d.updated, d.unchanged, d.otherClass) == (n, n, 0, 0, 0),
          "fresh library: all new (%s)" % [d.total, d.new, d.updated, d.unchanged, d.otherClass])
    check(preview(d) == "%d macros: %d new, 0 updated, 0 unchanged." % (n, n), "preview text: " + preview(d))
    lib.Apply(wu.records, 1000)
    check(lib.Count() == n, "library holds every imported macro")

    everything, _ = parse(fx["everything"]["string"])
    total = len(fx["everything"]["records"])
    d = diff(everything, lib.db.library, "WARRIOR")
    check((d.new, d.unchanged, d.updated) == (total - n, n, 0), "superset import: new/unchanged split")
    check(d.otherClass == total - n, "other-class count = everything except Warrior + Universal")
    check(" are for another class and will be kept for those characters." in preview(d), "preview mentions other classes")

    # One changed body -> updated.
    lua.execute('local r = R2F.Library.db.library["WARRIOR/VR"]; r.body = r.body .. "\\n/say hi"')
    d = diff(wu, lib.db.library, "WARRIOR")
    check((d.updated, d.unchanged) == (1, n - 1), "edited library entry shows as updated")
    check(d.status["WARRIOR/VR"] == "updated", "status per id")
    lib.Apply(wu.records, 1001)

    # Tab/section order vs the site's page order.
    secs = lib.Sections("WARRIOR")
    names = [secs[i].section for i in range(1, len(secs) + 1)]
    check(names == ["General", "Tank", "DPS"], "Warrior section order " + str(names))
    site_order = [r["id"] for r in fx["warriorUniversal"]["records"] if r["class"] == "WARRIOR"]
    lua_order = []
    for i in range(1, len(secs) + 1):
        es = secs[i].entries
        lua_order += [es[j].id for j in range(1, len(es) + 1)]
    check(lua_order == site_order, "Macro Book entry order == site page order")
    anys = lib.Sections("ANY")
    check(len(anys) == 1 and anys[1].section == "Universal", "Universal is one section")

    # Hash: stable 8 hex digits, differs on change.
    h = lua.eval("R2F.Library.Hash")
    check(re.fullmatch(r"[0-9a-f]{8}", h("abc")) is not None and h("abc") != h("abd"), "hash format")
    check(h("") == "00001505", "djb2 of empty string = 5381")
    # Python djb2 cross-check on a real body.
    body = fx["warriorUniversal"]["records"][0]["body"]
    hv = 5381
    for b in body.encode("utf-8"):
        hv = (hv * 33 + b) % 2**32
    check(h(body) == "%08x" % hv, "Lua hash == reference djb2")

    # Init keeps existing data and fills gaps.
    lua.execute('R2FDB = { library = { x = { class = "ANY" } }, settings = { slotsFirst = "bogus" } } R2FCharDB = nil R2F.Library.Init()')
    check(lua.eval('R2FDB.library.x ~= nil and R2FDB.version == 1 and R2FDB.settings.slotsFirst == "character" and type(R2FCharDB.created) == "table" and type(R2FDB.createdAccount) == "table"'),
          "Init migrates/fills without wiping")


def test_site_cross_check(lua, fx):
    """Ids/shorts/sections as build.py emits them (macros.html JSON) vs the addon's rules."""
    html = open(os.path.join(ROOT, "macros.html"), encoding="utf-8").read()
    data = json.loads(re.search(r"^const D = (.*);$", html, re.M).group(1))
    ids = []

    def walk(token, groups):
        for g in groups:
            for m in g["macros"]:
                if m["code"]:
                    ids.append(m["id"])
                    check(m["id"] == token + "/" + m["short"], "build.py id rule for " + m["id"])
                    check(len(m["short"]) <= 16, "short <= 16: " + m["id"])

    walk("ANY", [g for s in data["universal"]["sections"] for g in s["groups"]])
    order = lua.eval("R2F.Library.SECTION_ORDER")
    for c in data["classes"]:
        token = c["name"].upper().replace(" ", "")
        for s in c["sections"]:
            walk(token, s["groups"])
        lua_secs = lua_table_to_list(order[token])
        check(lua_secs == [s["spec"] for s in c["sections"]],
              "Library.SECTION_ORDER[%s] matches data.py %s" % (token, [s["spec"] for s in c["sections"]]))
        check(lua.eval("R2F.Library.KNOWN_CLASSES")[token] is True, "known class token " + token)
    check(lua_table_to_list(lua.eval("R2F.Library.GROUP_ORDER")) == data["order"], "GROUP_ORDER matches data.py ORDER")
    parse = lua.eval("function(s) local a, b = R2F.Import.Parse(s) return a, b end")
    res, _ = parse(fx["everything"]["string"])
    check(sorted(lua_table_to_list(res.records) and [res.records[i].id for i in range(1, len(res.records) + 1)]) == sorted(ids),
          "every build.py id survives the round trip into the addon")


def test_macros(lua, fx):
    lua.execute("TEST.reset() R2FDB = nil R2FCharDB = nil R2F.Library.Init() R2F.playerClass = 'WARRIOR'")
    parse = lua.eval("function(s) local a, b = R2F.Import.Parse(s) return a, b end")
    res, _ = parse(fx["warriorUniversal"]["string"])
    lua.eval("R2F.Library.Apply")(res.records, 1)
    M = lua.eval("R2F.Macros")
    T = lua.eval("TEST")
    # Capture the confirm popup instead of showing it.
    lua.execute("CONFIRMS = {} R2F.UI.Confirm = function(text, a, b, fn) table.insert(CONFIRMS, {text=text, fn=fn}) end")

    check(M.Ensure("WARRIOR/VR") is True, "Ensure creates a new macro")
    check(T.cursor == "VR", "new macro is on the cursor")
    check(lua.eval("#TEST.macros.char") == 1 and lua.eval("#TEST.macros.acc") == 0, "goes to character slots first")
    check(lua.eval('TEST.macros.char[1].icon') == "INV_MISC_QUESTIONMARK", "#showtooltip macro created with question mark icon")
    check(lua.eval('R2FCharDB.created["WARRIOR/VR"].hash == R2F.Library.Hash(TEST.bodyOf("VR"))'), "created record stores body hash")

    T.cursor = None
    check(M.Ensure("WARRIOR/VR") is True and T.cursor == "VR" and lua.eval("#TEST.macros.char") == 1,
          "Ensure on an existing own macro just picks it up")

    # Icon macro (no #showtooltip) keeps its icon.
    icon_id = next(r["id"] for r in fx["warriorUniversal"]["records"] if r["icon"] and not r["body"].startswith("#showtooltip"))
    icon_rec = next(r for r in fx["warriorUniversal"]["records"] if r["id"] == icon_id)
    M.Ensure(icon_id)
    check(lua.eval("(select(2, GetMacroInfo(GetMacroIndexByName(%r))))" % icon_rec["short"]) == icon_rec["icon"],
          "icon macro created with its icon (%s)" % icon_id)

    # Player edits our macro -> popup; Replace restores it.
    T.setBody("VR", "/say mine")
    T.cursor = None
    check(M.Ensure("WARRIOR/VR") is False and lua.eval("#CONFIRMS") == 1, "edited own macro asks Replace/Keep mine")
    check('"VR"' in lua.eval("CONFIRMS[1].text"), "popup names the macro")
    check(T.cursor is None, "nothing picked up before an answer")
    lua.execute("CONFIRMS[1].fn()")
    check(T.bodyOf("VR") == lua.eval('R2F.Library.db.library["WARRIOR/VR"].body') and T.cursor == "VR",
          "Replace restores the library body and picks it up")

    # Foreign macro with same name, different body: Keep mine = untouched.
    T.addMacro("HS", "/cast Heroic Strike", False)
    check(M.Ensure("WARRIOR/HS") is False and lua.eval("#CONFIRMS") == 2, "foreign macro with our name asks first")
    check(T.bodyOf("HS") == "/cast Heroic Strike", "Keep mine (no accept) leaves it alone")
    # Foreign macro with identical body -> adopted silently.
    sunder_body = lua.eval('R2F.Library.db.library["WARRIOR/Sunder"].body')
    T.addMacro("Sunder", sunder_body, False)
    check(M.Ensure("WARRIOR/Sunder") is True and lua.eval("#CONFIRMS") == 2 and lua.eval('R2FDB.createdAccount["WARRIOR/Sunder"] ~= nil'),
          "identical foreign macro is adopted without a popup (recorded as account)")

    # Combat: refused, nothing written (the fake errors on protected calls).
    T.combat = True
    T.errors = lua.table()
    check(M.Ensure("WARRIOR/Rend") is False, "Ensure refused in combat")
    check(lua.eval("TEST.errors[1]") == lua.eval("R2F.L.ERR_COMBAT"), "combat error text")
    check(lua.eval('GetMacroIndexByName("Rend")') == 0, "no macro created in combat")
    T.combat = False

    # Slots: fill character slots -> account; all full -> error.
    lua.execute("for i = 1, 18 - #TEST.macros.char do TEST.addMacro('c' .. i, 'x', true) end")
    M.Ensure("WARRIOR/Rend")
    check(lua.eval('GetMacroIndexByName("Rend") <= 120 and GetMacroIndexByName("Rend") > 0'), "full character slots -> account slot")
    check(lua.eval('R2FDB.createdAccount["WARRIOR/Rend"].account == true'), "account macro recorded in createdAccount")
    lua.execute("for i = 1, 120 - #TEST.macros.acc do TEST.addMacro('a' .. i, 'x', false) end TEST.errors = {}")
    check(M.Ensure("WARRIOR/Slam") is False and lua.eval("TEST.errors[1]") == lua.eval("R2F.L.ERR_NO_SLOTS"), "no free slots error")
    counts = M.Counts()
    check(tuple(counts) == (120, 120, 18, 18), "Counts() = acc, maxAcc, char, maxChar")

    # slotsFirst = account
    lua.execute("TEST.reset() R2FCharDB.created = {} R2FDB.createdAccount = {} R2FDB.settings.slotsFirst = 'account'")
    M.Ensure("WARRIOR/VR")
    check(lua.eval("#TEST.macros.acc") == 1, "slotsFirst=account uses account slots")
    lua.execute("R2FDB.settings.slotsFirst = 'character'")

    # Tidy up: three ours; one on a bar, one edited, one free -> only the free one.
    lua.execute("TEST.reset() R2FCharDB.created = {} R2FDB.createdAccount = {}")
    for i in ("WARRIOR/VR", "WARRIOR/HS", "WARRIOR/Rend", "WARRIOR/Slam"):
        M.Ensure(i)
    lua.execute('TEST.actions[1] = "VR" TEST.setBody("HS", "/say edited")')
    T.addMacro("Mine", "/dance", True)
    cands = M.TidyCandidates()
    names = sorted(cands[i].name for i in range(1, len(cands) + 1))
    check(names == ["Rend", "Slam"], "tidy candidates = unedited, not on bars, ours only: %s" % names)
    check(M.Tidy(cands) == 2, "Tidy deletes both (indices re-looked-up after each delete)")
    check(T.bodyOf("Rend") is None and T.bodyOf("Slam") is None and T.bodyOf("VR") and T.bodyOf("HS") and T.bodyOf("Mine"),
          "only the candidates were deleted")
    check(lua.eval('R2FCharDB.created["WARRIOR/Rend"] == nil'), "deleted macro's record removed")
    # Player deleted one of ours by hand -> record forgotten.
    lua.execute('DeleteMacro(GetMacroIndexByName("VR"))')
    M.TidyCandidates()
    check(lua.eval('R2FCharDB.created["WARRIOR/VR"] == nil'), "stale record dropped when the macro is gone")
    # Tidy in combat writes nothing.
    T.combat = True
    check(M.Tidy(cands) == 0, "Tidy refused in combat")
    T.combat = False

    # On-your-bars marker.
    M.Ensure("WARRIOR/VR")
    lua.execute('TEST.actions[5] = "VR"')
    check(M.OnBars("WARRIOR/VR", M.NamesOnBars()) is True and M.OnBars("WARRIOR/HS", M.NamesOnBars()) is False, "OnBars marker")

    # Update (step 4 uses it): unedited -> edited in place; edited -> left alone; combat -> queued.
    lua.execute('R2F.Library.db.library["WARRIOR/VR"].body = "#showtooltip Victory Rush\\n/cast Victory Rush"')
    check(M.Update("WARRIOR/VR") == "updated" and T.bodyOf("VR") == "#showtooltip Victory Rush\n/cast Victory Rush", "Update edits an unedited macro")
    check(M.Update("WARRIOR/VR") == "unchanged", "Update on an up-to-date macro reports unchanged")
    check(M.Update("WARRIOR/HS") == "edited" and T.bodyOf("HS") == "/say edited", "Update leaves an edited macro alone")
    check(M.Update("WARRIOR/Slam") == "none", "Update with no real macro reports none")
    lua.execute('R2F.Library.db.library["WARRIOR/VR"].body = "#showtooltip Victory Rush\\n/cast [harm] Victory Rush"')
    T.combat = True
    check(M.Update("WARRIOR/VR") == "queued" and M.QueueSize() == 1, "Update in combat is queued")
    T.combat = False
    M.RunQueue()
    check(T.bodyOf("VR").endswith("/cast [harm] Victory Rush") and M.QueueSize() == 0, "queued write runs after combat")

    # Icons / Learn later.
    ts = M.TooltipSpell
    check(ts("#showtooltip Victory Rush\n/cast [harm] Victory Rush") == "Victory Rush", "TooltipSpell: explicit")
    check(ts("#showtooltip\n/cast [harm] Rend") == "Rend", "TooltipSpell: from /cast")
    check(ts("#showtooltip\n/castsequence reset=3 Rend, Slam") == "Rend", "TooltipSpell: castsequence")
    check(ts("#showtooltip\n/cast !Auto Shot") == "Auto Shot", "TooltipSpell: strips !")
    check(ts("#showtooltip [mod:shift] Cleave; Heroic Strike") == "Cleave", "TooltipSpell: first clause")
    check(ts("/petattack [harm]") is None, "TooltipSpell: no #showtooltip -> nil")
    tex, later = M.DisplayIcon(lua.eval('R2F.Library.db.library["WARRIOR/HS"]'))
    check(tex == "Interface\\Icons\\Ability_Rogue_Ambush" and later is False, "known spell -> spell icon")
    tex, later = M.DisplayIcon(lua.eval('R2F.Library.db.library["WARRIOR/Rend"]'))
    check(tex == "Interface\\Icons\\INV_MISC_QUESTIONMARK" and later is True, "unknown spell -> question mark + Learn later")
    tex, later = M.DisplayIcon(lua.eval('{ body = "/petattack", icon = "Ability_GhoulFrenzy" }'))
    check(tex == "Interface\\Icons\\Ability_GhoulFrenzy" and later is False, "icon macro -> its icon")


FIELDS = ("id", "class", "section", "group", "name", "short", "icon", "body", "note")


def import_string(records):
    """Same format as the site's importString() (ADDON_PLAN 7)."""
    text = "v=1\n" + "\x1e".join("\x1f".join(r[k] for k in FIELDS) for r in records)
    return "R2F1:" + base64.b64encode(text.encode("utf-8")).decode()


def modified(records, changes):
    """Copy of the fixture records with {id: {field: value}} applied."""
    out = []
    for r in records:
        r = dict(r)
        r.update(changes.get(r["id"], {}))
        out.append(r)
    return out


def chat_lines(lua):
    c = lua.eval("TEST.chat")
    return [c[i] for i in range(1, len(c) + 1)]


def test_updates(lua, fx):
    """Step 4: re-import updates unedited macros, keeps edited ones, Changed flags, combat queue."""
    lua.execute("TEST.reset() R2FDB = nil R2FCharDB = nil R2F.Library.Init() R2F.playerClass = 'WARRIOR'")
    lua.execute("CONFIRMS = {} R2F.UI.Confirm = function(text, a, b, fn) table.insert(CONFIRMS, {text=text, fn=fn}) end")
    parse = lua.eval("function(s) local a, b = R2F.Import.Parse(s) return a, b end")
    commit = lua.eval("R2F.Import.Commit")
    preview = lua.eval("R2F.Import.PreviewText")
    diff = lua.eval("R2F.Import.Diff")
    M, T, Lib = lua.eval("R2F.Macros"), lua.eval("TEST"), lua.eval("R2F.Library")
    Ltxt = lua.eval("R2F.L")
    recs = fx["warriorUniversal"]["records"]

    res, _ = parse(import_string(recs))
    d = commit(res, "WARRIOR", 1)
    check(d.imported == len(recs) and len(d.plan.update) == 0 and len(d.plan.edited) == 0,
          "first import: nothing to update (no real macros yet)")
    for i in ("WARRIOR/VR", "WARRIOR/HS", "WARRIOR/Rend", "WARRIOR/Slam"):
        M.Ensure(i)
    lua.execute('TEST.actions[1] = "VR" TEST.actions[2] = "HS" TEST.actions[3] = "Slam"')
    T.setBody("HS", "/say my own HS")

    lib_body = lambda i: lua.eval('R2F.Library.db.library[%r].body' % i)
    new = {
        "WARRIOR/VR": {"body": "#showtooltip Victory Rush\n/cast [harm] Victory Rush\n/say v2"},
        "WARRIOR/HS": {"body": "#showtooltip Heroic Strike\n/cast [harm] Heroic Strike\n/say v2"},
        "WARRIOR/Rend": {"body": "#showtooltip Rend\n/cast [harm] Rend\n/say v2"},
        "WARRIOR/Slam": {"note": "Only the note changed."},
    }
    res, _ = parse(import_string(modified(recs, new)))
    d = diff(res, Lib.db.library, "WARRIOR")
    check(d.updated == 4, "diff: 4 updated records (got %s)" % d.updated)
    check(lua_table_to_list(d.plan.update) == ["WARRIOR/VR", "WARRIOR/Rend"],
          "plan: unedited real macros with a new body are updated, note-only change is not (%s)" % lua_table_to_list(d.plan.update))
    check(lua_table_to_list(d.plan.edited) == ["WARRIOR/HS"], "plan: the hand-edited macro is reported as kept")
    text = preview(d)
    check(text.split("\n")[0] == "%d macros: 0 new, 4 updated, %d unchanged." % (len(recs), len(recs) - 4),
          "preview first line keeps the 5.6 wording: " + text.split("\n")[0])
    check(text.endswith("\n" + Ltxt.IMPORT_WILL_UPDATE.replace("%d", "2") + " " + Ltxt.IMPORT_WILL_KEEP_ONE),
          "preview second line: will update 2, keep 1 edited: %r" % text)
    check(T.bodyOf("VR") != new["WARRIOR/VR"]["body"], "preview/diff writes nothing")

    T.calls = lua.table()
    T.chat = lua.table()
    d = commit(res, "WARRIOR", 2)
    calls = lua_table_to_list(T.calls)
    check(calls == ["edit:VR", "edit:Rend"], "re-import EditMacro'd exactly the unedited changed macros: %s" % calls)
    check(T.bodyOf("VR") == new["WARRIOR/VR"]["body"] and T.bodyOf("Rend") == new["WARRIOR/Rend"]["body"],
          "re-import pushed the new bodies to the real macros")
    check(lua.eval('R2FCharDB.created["WARRIOR/VR"].hash == R2F.Library.Hash(TEST.bodyOf("VR"))'),
          "stored hash follows the update (so the macro still counts as unedited)")
    check(T.bodyOf("HS") == "/say my own HS", "hand-edited real macro left untouched")
    check(lib_body("WARRIOR/HS") == new["WARRIOR/HS"]["body"], "library still takes the new version of the edited macro")
    check(d.applied == "now", "updates ran right away out of combat")
    chat = chat_lines(lua)
    check(any("updated 2 of your macros to the new version." in c for c in chat), "chat: updated 2")
    check(any("kept your edits to HS." in c for c in chat), "chat: kept the edited one, by name: %s" % chat)
    check(lua.eval('R2FCharDB.changed["WARRIOR/VR"]') == "updated", "Changed flag set for an updated macro on a bar")
    check(lua.eval('R2FCharDB.changed["WARRIOR/HS"]') == "edited", "Changed flag (edited kind) for the kept macro on a bar")
    check(lua.eval('R2FCharDB.changed["WARRIOR/Rend"]') is None, "no Changed flag for an updated macro not on any bar")
    check(lua.eval('R2FCharDB.changed["WARRIOR/Slam"]') is None, "no Changed flag for a note-only change")
    check(lua.eval('R2FDB.changed') is None, "Changed flags are per character, not in R2FDB")

    # Same string again: nothing written, the edited one isn't re-reported.
    T.calls = lua.table()
    T.chat = lua.table()
    d = commit(res, "WARRIOR", 3)
    check(len(T.calls) == 0 and len(d.plan.update) == 0 and len(d.plan.edited) == 0, "identical re-import writes nothing")
    check(not any("kept your edits" in c for c in chat_lines(lua)), "identical re-import doesn't repeat the kept-edit note")

    # Combat during an import: EditMacro is queued (one job), not skipped, not an error.
    v3 = dict(new)
    v3["WARRIOR/VR"] = {"body": "#showtooltip Victory Rush\n/cast [harm] Victory Rush\n/say v3"}
    v3["WARRIOR/Rend"] = {"body": "#showtooltip Rend\n/cast [harm] Rend\n/say v3"}
    res3, _ = parse(import_string(modified(recs, v3)))
    lua.execute('R2FCharDB.changed = {}')
    T.calls = lua.table()
    T.chat = lua.table()
    T.combat = True
    d = commit(res3, "WARRIOR", 4)  # the fake client raises if EditMacro runs in combat
    check(d.applied == "queued" and M.QueueSize() == 1, "import in combat queues ONE update job")
    check(len(T.calls) == 0 and T.bodyOf("VR").endswith("v2"), "nothing written in combat")
    check(lib_body("WARRIOR/VR").endswith("v3"), "library updated even in combat (SavedVariables only)")
    check(any(Ltxt.UPDATED_QUEUED.replace("%d", "2") in c for c in chat_lines(lua)), "chat says it will update after combat")
    check(lua.eval('R2FCharDB.changed["WARRIOR/VR"]') == "updated", "queued update shows its Changed marker right away")
    # The player edits Rend before combat ends: the queued job must re-check and leave it.
    T.setBody("Rend", "/say edited in combat")
    T.combat = False
    M.RunQueue()
    check(T.bodyOf("VR").endswith("v3") and M.QueueSize() == 0, "queued EditMacro runs on PLAYER_REGEN_ENABLED")
    check(T.bodyOf("Rend") == "/say edited in combat", "queued update re-checks: macro edited meanwhile is left alone")
    check(any("updated 1 of your macros to the new version." in c for c in chat_lines(lua)), "after-combat chat counts what was written")

    # Icon-only change on a macro without #showtooltip.
    icon_rec = next(r for r in recs if r["icon"] and not r["body"].startswith("#showtooltip"))
    M.Ensure(icon_rec["id"])
    res4, _ = parse(import_string(modified(recs, dict(v3, **{icon_rec["id"]: {"icon": "INV_Misc_Bomb_01"}}))))
    d = commit(res4, "WARRIOR", 5)
    check(lua_table_to_list(d.plan.update) == [icon_rec["id"]], "icon-only change is an update")
    check(lua.eval("(select(2, GetMacroInfo(GetMacroIndexByName(%r))))" % icon_rec["short"]) == "INV_Misc_Bomb_01",
          "new icon pushed to the real macro")

    # Ensure on a stale-but-unedited macro updates it before picking it up.
    lua.execute('R2F.Library.db.library["WARRIOR/VR"].body = "#showtooltip Victory Rush\\n/cast Victory Rush"')
    T.cursor = None
    check(M.Ensure("WARRIOR/VR") is True and T.cursor == "VR" and T.bodyOf("VR") == "#showtooltip Victory Rush\n/cast Victory Rush"
          and lua.eval("#CONFIRMS") == 0, "Ensure updates a stale unedited macro, then picks it up (no popup)")

    # Login sync (library changed by an import on another character).
    lua.execute('R2F.Library.db.library["WARRIOR/VR"].body = "#showtooltip Victory Rush\\n/cast [harm] Victory Rush\\n/say alt"')
    lua.execute('R2FCharDB.changed = { ["PALADIN/HL"] = "updated", ["WARRIOR/Gone"] = "updated" }')
    T.chat = lua.table()
    check(M.SyncOnLogin() == 1 and T.bodyOf("VR").endswith("/say alt"), "login sync updates this character's stale unedited macro")
    check(T.bodyOf("Rend") == "/say edited in combat", "login sync leaves edited macros alone")
    check(any("to the version in your library" in c for c in chat_lines(lua)), "login sync says so in chat")
    check(lua.eval('R2FCharDB.changed["PALADIN/HL"] == nil and R2FCharDB.changed["WARRIOR/Gone"] == nil'),
          "login drops Changed flags that could never be hovered")
    check(lua.eval('R2FCharDB.changed["WARRIOR/VR"]') == "updated", "login sync marks the updated macro on a bar")
    T.combat = True
    lua.execute('R2F.Library.db.library["WARRIOR/VR"].body = "#showtooltip Victory Rush\\n/say reload in combat"')
    check(M.SyncOnLogin() == 1 and M.QueueSize() == 1 and not T.bodyOf("VR").endswith("combat"), "login sync in combat is queued")
    T.combat = False
    M.RunQueue()
    check(T.bodyOf("VR").endswith("reload in combat"), "queued login sync runs after combat")

    # Flags go away with the library entry or the real macro.
    lua.execute('R2F.Library.SetChanged("WARRIOR/VR", "updated") R2F.Library.Remove("WARRIOR/VR")')
    check(lua.eval('R2FCharDB.changed["WARRIOR/VR"]') is None, "Remove from library clears the Changed flag")
    lua.execute('R2F.Library.SetChanged("WARRIOR/Slam", "updated") R2F.Library.SetCreated("WARRIOR/Slam", nil)')
    check(lua.eval('R2FCharDB.changed["WARRIOR/Slam"]') is None, "forgetting the real macro clears the Changed flag")
    # Replace answers an "edited" Changed note.
    lua.execute('R2F.Library.SetChanged("WARRIOR/HS", "edited")')
    M.Ensure("WARRIOR/HS")
    lua.execute("CONFIRMS[#CONFIRMS].fn()")
    check(T.bodyOf("HS") == lib_body("WARRIOR/HS") and lua.eval('R2FCharDB.changed["WARRIOR/HS"]') is None,
          "Replace on an edited macro installs the new version and clears its flag")


def test_ui_updates(fx):
    """Step 4 through the UI: preview line, green arrow on the slot, cleared by the first tooltip."""
    lua = new_runtime()
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    recs = fx["warriorUniversal"]["records"]
    lua.execute('SlashCmdList.R2F("import")')
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'EditBox' and f.__parent == R2FImportScroll then EDIT = f end
        if f.__kind == 'Button' and f.__text == 'Import' and f.__parent == R2FImport then IMPORTBTN = f end
      end""")
    lua.eval("EDIT.SetText")(lua.eval("EDIT"), import_string(recs))
    T.runTimers()
    lua.execute("IMPORTBTN:Click()")
    general = [r for r in recs if r["section"] == "General"]
    first = general[0]
    lua.execute("""
      TABS = {} SLOTS = {}
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'CheckButton' and f.sec and f.__shown then table.insert(TABS, f) end
        if f.__kind == 'Button' and f.__scripts.OnDragStart then table.insert(SLOTS, f) end
      end
      TABS[2]:Click()""")
    lua.execute("SLOTS[1]:Fire('OnDragStart')")
    check(T.cursor == first["short"], "UI: macro created from the book")
    T.actions[7] = first["short"]
    check(lua.eval("SLOTS[1].arrow.__shown") is False, "UI: no arrow before any update")

    new_body = first["body"] + "\n/say v2"
    lua.execute('SlashCmdList.R2F("import")')
    lua.eval("EDIT.SetText")(lua.eval("EDIT"), import_string(modified(recs, {first["id"]: {"body": new_body}})))
    T.runTimers()
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'FontString' and type(f.__text) == 'string' and f.__text:find(' new, ') then PREVIEW = f end
      end""")
    check(lua.eval("PREVIEW.__text").endswith("\n" + lua.eval("R2F.L.IMPORT_WILL_UPDATE_ONE")),
          "UI: preview says the macro in the game will be updated: %r" % lua.eval("PREVIEW.__text"))
    lua.execute("IMPORTBTN:Click()")
    check(T.bodyOf(first["short"]) == new_body, "UI: Import button updated the real macro")
    lua.execute("TABS[2]:Click()")
    check(lua.eval("SLOTS[1].entry.id") == first["id"] and lua.eval("SLOTS[1].arrow.__shown") is True,
          "UI: green Changed arrow shows on the updated macro")
    check(lua.eval("SLOTS[1].arrow.__vertex[2]") == 1 and lua.eval("SLOTS[2].arrow.__shown") is False,
          "UI: arrow is green and only on the changed slot")
    lua.execute("SLOTS[1]:Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(lua.eval("R2F.L.TIP_CHANGED") in lines, "UI: first tooltip explains the change")
    check(lua.eval("SLOTS[1].arrow.__shown") is False and lua.eval("R2FCharDB.changed[%r]" % first["id"]) is None,
          "UI: hovering clears the arrow and the stored flag")
    lua.execute("SLOTS[1]:Fire('OnLeave') TABS[2]:Click() SLOTS[1]:Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(lua.eval("R2F.L.TIP_CHANGED") not in lines and lua.eval("SLOTS[1].arrow.__shown") is False,
          "UI: stays cleared after a refresh and a second hover")

    # PLAYER_LOGIN runs the sync (an import on another character changed the shared library).
    alt_body = first["body"] + "\n/say from an alt"
    lua.execute('R2F.Library.db.library[%r].body = %r' % (first["id"], alt_body))
    T.fire("PLAYER_LOGIN")
    check(T.bodyOf(first["short"]) == alt_body, "UI: PLAYER_LOGIN brings an unedited macro up to the library")


def test_ui_smoke(templates, fx):
    """Load everything, fire the login events, drive the UI through a full import + drag."""
    lua = new_runtime(templates)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "SomeOtherAddon")
    check(lua.eval("R2FDB") is None, "other addons' ADDON_LOADED is ignored")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    check(lua.eval("R2F.playerClass") == "WARRIOR", "class read on PLAYER_LOGIN")
    lua.execute('SlashCmdList.R2F("")')
    check(lua.eval("R2F.MacroBook.IsShown()") is True, "/r2f opens the Macro Book")
    tag = "templates" if templates else "fallbacks"
    check(lua.eval("R2FMacroBook ~= nil") if templates else lua.eval("R2FMacroBookPlain ~= nil"),
          "%s: book frame created via %s" % (tag, "PortraitFrameTemplate" if templates else "fallback"))

    lua.execute('SlashCmdList.R2F("import")')
    check(lua.eval("R2FImport:IsShown()") is True, "import window opens")
    edit = lua.eval("R2FImport and (R2FImportScroll and R2FImportScroll.EditBox or nil)") if templates else None
    # Find the edit box whichever path built it.
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'EditBox' and f.__scripts.OnTextChanged and f.__parent and
           (f.__parent == R2FImportScroll or f.__parent == R2FImportScrollPlain) then EDIT = f end
      end""")
    check(lua.eval("EDIT ~= nil"), "%s: import edit box found" % tag)
    lua.eval("EDIT.SetText")(lua.eval("EDIT"), fx["warriorUniversal"]["string"])
    T.runTimers()
    n = len(fx["warriorUniversal"]["records"])
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'FontString' and type(f.__text) == 'string' and f.__text:find(' new, ') then PREVIEW = f end
        if f.__kind == 'Button' and f.__text == 'Import' and f.__parent == R2FImport then IMPORTBTN = f end
      end""")
    check(lua.eval("PREVIEW and PREVIEW.__text") == "%d macros: %d new, 0 updated, 0 unchanged." % (n, n), "%s: import preview line" % tag)
    check(lua.eval("IMPORTBTN.__enabled") is True, "Import button enabled for a valid string")
    lua.execute("IMPORTBTN:Click()")
    check(lua.eval("R2FImport:IsShown()") is False, "import window closes after import")
    check(lua.eval("R2F.Library.Count()") == n, "library filled")
    check(any("imported %d macros." % n in lua.eval("TEST.chat")[i] for i in range(1, len(lua.eval("TEST.chat")) + 1)), "chat confirms import")

    # Bad string shows the error and keeps Import disabled.
    lua.execute('SlashCmdList.R2F("import")')
    lua.eval("EDIT.SetText")(lua.eval("EDIT"), "nonsense")
    T.runTimers()
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'FontString' and f.__text == R2F.L.IMPORT_BAD then BADTEXT = f end
      end""")
    check(lua.eval("BADTEXT ~= nil") and lua.eval("IMPORTBTN.__enabled") is False, "bad string message, Import disabled")
    lua.execute("R2FImport:Hide()")

    # Tabs: Universal, General, Tank, DPS (Warrior + Universal import).
    lua.execute("""
      TABS = {} SLOTS = {}
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'CheckButton' and f.sec and f.__shown then table.insert(TABS, f) end
        if f.__kind == 'Button' and f.__scripts.OnDragStart then table.insert(SLOTS, f) end
      end""")
    secs = [lua.eval("TABS[%d].sec.section" % i) for i in range(1, lua.eval("#TABS") + 1)]
    check(secs == ["Universal", "General", "Tank", "DPS"], "%s: tabs %s" % (tag, secs))
    check(lua.eval("#SLOTS") == 12, "12 macro slots per page")
    check(lua.eval("TABS[1]:GetChecked()") is True, "import jumped to the first tab with new macros (Universal)")
    lua.execute("TABS[2]:Click()")
    check(lua.eval("TABS[2]:GetChecked()") is True, "clicking a tab selects it")
    general = [r for r in fx["warriorUniversal"]["records"] if r["section"] == "General"]
    check(lua.eval("SLOTS[1].entry.id") == general[0]["id"], "first slot = first General macro in site order")
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'FontString' and type(f.__text) == 'string' and f.__text:match('^Page ') then PAGETEXT = f end
      end""")
    pages = -(-len(general) // 12)
    check(lua.eval("PAGETEXT.__text") == "Page 1 of %d" % pages, "page text (%s)" % lua.eval("PAGETEXT.__text"))

    # Tooltip lines (5.4).
    lua.execute("SLOTS[1]:Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(lines[0] == general[0]["name"] and lines[1] == general[0]["short"] and lines[-1] == "Drag to an action bar.",
          "tooltip: name, short, ..., drag hint")

    # Drag creates + picks up; shift-click shares; right-click menu removes.
    lua.execute("SLOTS[1]:Fire('OnDragStart')")
    check(T.cursor == general[0]["short"], "%s: drag creates and picks up the macro" % tag)
    T.shift = True
    lua.execute("SLOTS[2]:Click('LeftButton')")
    check(lua.eval("TEST.chatInsert") is not None and "\n" not in lua.eval("TEST.chatInsert"), "shift-click puts a one-line body in chat")
    T.shift = False
    before = lua.eval("R2F.Library.Count()")
    lua.execute("""
      SLOTS[3]:Click('RightButton')
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'Button' and f.__text == R2F.L.MENU_REMOVE then f:Click() end
      end""")
    check(lua.eval("R2F.Library.Count()") == before - 1, "right-click > Remove from library")

    # Combat: Import/Tidy greyed out, In combat shown, drag refused.
    # Real event order: PLAYER_REGEN_DISABLED is handled while InCombatLockdown()
    # is still false; the UI must grey out anyway.
    T.combat = False
    T.fire("PLAYER_REGEN_DISABLED")
    T.combat = True
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'Button' and f.__text == 'Tidy up' then TIDY = f end
        if f.__kind == 'Button' and f.__text == 'Import' and f.__parent ~= R2FImport then BOOKIMPORT = f end
        if f.__kind == 'FontString' and f.__text == 'In combat' then COMBATTEXT = f end
      end""")
    check(lua.eval("TIDY.__enabled") is False and lua.eval("BOOKIMPORT.__enabled") is False and lua.eval("COMBATTEXT.__shown") is True,
          "combat greys out Import/Tidy up and shows In combat")
    T.cursor = None
    lua.execute("SLOTS[4]:Fire('OnDragStart')")
    check(T.cursor is None, "drag in combat does nothing")
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")
    check(lua.eval("TIDY.__enabled") is True and lua.eval("COMBATTEXT.__shown") is False, "combat end re-enables")

    # Tidy up through the UI: the dragged macro is not on a bar -> offered and deleted.
    lua.execute("TIDY:Click()")
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'Button' and f.__text == 'Delete' then f:Click() end
      end""")
    check(lua.eval("GetMacroIndexByName(%r)" % general[0]["short"]) == 0, "Tidy up via the book deletes the unused macro")

    # Events while open don't error.
    for ev in ("UPDATE_MACROS", "ACTIONBAR_SLOT_CHANGED", "LEARNED_SPELL_IN_TAB"):
        T.fire(ev)
    T.runTimers()
    check(lua.eval("R2F.MacroBook.IsShown()") is True, "refresh events while open")

    # 5.7 line: import a Paladin macro -> mentioned on the Universal tab.
    pal = next(r for r in fx["everything"]["records"] if r["class"] == "PALADIN")
    parse = lua.eval("function(s) local a, b = R2F.Import.Parse(s) return a, b end")
    res, _ = parse(fx["everything"]["string"])
    lua.eval("R2F.Library.Apply")(res.records, 5)
    lua.execute("TABS[1]:Click()")
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'FontString' and type(f.__text) == 'string' and f.__text:find('^You also have macros for') then OTHER = f end
      end""")
    other = lua.eval("OTHER and OTHER.__text")
    check(other is not None and "Paladin (" in other, "Universal tab lists other classes: %s" % other)

    # Esc support + the one-global audit.
    special = lua_table_to_list(lua.eval("UISpecialFrames"))
    check("R2FImport" in special and any(s.startswith("R2FMacroBook") for s in special), "windows close with Esc: %s" % special)
    new_globals = lua.eval("""(function()
      local out = {}
      for k in pairs(_G) do if not BEFORE[k] then table.insert(out, k) end end
      table.sort(out) return table.concat(out, ",") end)()""").split(",")
    allowed_exact = {"R2F", "R2FDB", "R2FCharDB", "SLASH_R2F1"} | BINDING_GLOBALS
    test_vars = {"EDIT", "PREVIEW", "IMPORTBTN", "BADTEXT", "TABS", "SLOTS", "PAGETEXT", "TIDY", "BOOKIMPORT",
                 "COMBATTEXT", "OTHER", "NS"}
    bad = [g for g in new_globals if g and g not in allowed_exact and g not in test_vars and not g.startswith("R2F")]
    check(not bad, "%s: no globals besides R2F, saved vars, SLASH_R2F1, binding labels and R2F* frame names: %s" % (tag, bad))
    print("  %s: new globals = %s" % (tag, [g for g in new_globals if g not in test_vars]))


BINDING_GLOBALS = {"BINDING_HEADER_ROADTOFOREVER", "BINDING_NAME_R2F_TOGGLE", "BINDING_NAME_R2F_MACROS",
                   "BINDING_NAME_R2F_TALENTS"}


def names_of(lua_list):
    return [lua_list[i].name for i in range(1, len(lua_list) + 1)]


def test_step5_logic(lua, fx):
    """Step 5: Tidy up rules across action slots, combat queueing, slotsFirst, Remove all."""
    lua.execute("TEST.reset() R2FDB = nil R2FCharDB = nil R2F.Library.Init() R2F.playerClass = 'WARRIOR'")
    lua.execute("CONFIRMS = {} R2F.UI.Confirm = function(text, a, b, fn) table.insert(CONFIRMS, {text=text, fn=fn}) end")
    parse = lua.eval("function(s) local a, b = R2F.Import.Parse(s) return a, b end")
    res, _ = parse(fx["warriorUniversal"]["string"])
    lua.eval("R2F.Library.Apply")(res.records, 1)
    M, T = lua.eval("R2F.Macros"), lua.eval("TEST")
    lib_count = lua.eval("R2F.Library.Count()")

    # --- Tidy up across a simulated set of action slots -------------------
    ids = ["WARRIOR/VR", "WARRIOR/HS", "WARRIOR/Rend", "WARRIOR/Slam", "WARRIOR/Sunder", "WARRIOR/Exe"]
    for i in ids:
        M.Ensure(i)
    # VR on slot 1, Rend on the last standard slot (120), Sunder on a
    # stance/bonus-bar slot (73); HS edited by the player; Slam + Exe unused.
    lua.execute('TEST.actions[1] = "VR" TEST.actions[120] = "Rend" TEST.actions[73] = "Sunder" TEST.setBody("HS", "/say mine")')
    T.addMacro("Mine", "/dance", True)
    T.actions[2] = "Mine"
    cands = M.TidyCandidates()
    check(names_of(cands) == ["Exe", "Slam"],
          "tidy: only unedited AND unused macros of ours (slots 1, 73, 120 seen as in use): %s" % names_of(cands))
    # Run-time re-check: the player puts Slam on a bar after the popup was built.
    T.actions[40] = "Slam"
    check(M.Tidy(cands) == 1 and T.bodyOf("Slam") is not None and T.bodyOf("Exe") is None,
          "tidy re-checks the bars when it runs: Slam (now on a bar) kept, Exe deleted")
    check(T.bodyOf("HS") == "/say mine" and T.bodyOf("Mine") == "/dance" and T.bodyOf("VR") and T.bodyOf("Rend"),
          "tidy leaves edited, in-use and the player's own macros alone")
    T.actions[40] = None

    # Tidy up confirmed in combat -> queued (6.7 pattern), runs after combat.
    lua.execute('TEST.actions[73] = nil')  # Sunder now unused
    T.combat = True
    T.calls = lua.table()
    lua.execute("R2F.Macros.RunOrQueue(function() TIDIED = R2F.Macros.Tidy(R2F.Macros.TidyCandidates()) end)")
    check(M.QueueSize() == 1 and len(T.calls) == 0 and T.bodyOf("Sunder") is not None,
          "tidy accepted in combat is queued, nothing deleted in combat")
    T.combat = False
    M.RunQueue()
    check(lua.eval("TIDIED") == 2 and T.bodyOf("Sunder") is None and T.bodyOf("Slam") is None
          and T.bodyOf("VR") and T.bodyOf("Rend") and M.QueueSize() == 0,
          "queued tidy runs after combat and deletes the now-unused macros (Sunder, Slam) only")
    T.errors = lua.table()
    T.combat = True
    check(M.Tidy(lua.eval('{ { id = "WARRIOR/Rend", name = "Rend" } }')) == 0 and T.bodyOf("Rend") is not None
          and lua.eval("TEST.errors[1]") == lua.eval("R2F.L.ERR_COMBAT"), "Tidy called directly in combat refuses (no write)")
    T.combat = False

    # --- slotsFirst decides CreateMacro's perCharacter ----------------------
    lua.execute("TEST.reset() R2FCharDB.created = {} R2FDB.createdAccount = {} R2FDB.settings.slotsFirst = 'account'")
    M.Ensure("WARRIOR/VR")
    check(lua.eval("#TEST.macros.acc") == 1 and lua.eval("#TEST.macros.char") == 0
          and lua.eval('R2FDB.createdAccount["WARRIOR/VR"] ~= nil'), "slotsFirst=account: CreateMacro goes to account slots")
    lua.execute("R2FDB.settings.slotsFirst = 'character'")
    M.Ensure("WARRIOR/HS")
    check(lua.eval("#TEST.macros.char") == 1 and lua.eval('R2FCharDB.created["WARRIOR/HS"] ~= nil'),
          "slotsFirst=character: the next CreateMacro goes to character slots")
    check(lua.eval('GetMacroIndexByName("VR") <= 120'), "changing the setting does not move an existing macro")
    lua.execute("for i = 1, 120 do TEST.addMacro('a' .. i, 'x', false) end R2FDB.settings.slotsFirst = 'account'")
    M.Ensure("WARRIOR/Rend")
    check(lua.eval('GetMacroIndexByName("Rend") > 120'), "slotsFirst=account falls back to character slots when account is full")

    # --- Remove all ------------------------------------------------------------
    lua.execute("TEST.reset() R2FCharDB.created = {} R2FDB.createdAccount = {} R2FDB.settings.slotsFirst = 'character'")
    for i in ("WARRIOR/VR", "WARRIOR/HS", "WARRIOR/Rend"):
        M.Ensure(i)                      # character slots
    lua.execute("R2FDB.settings.slotsFirst = 'account'")
    for i in ("WARRIOR/Slam", "WARRIOR/Exe"):
        M.Ensure(i)                      # account slots
    lua.execute("R2FDB.settings.slotsFirst = 'character'")
    lua.execute('TEST.actions[1] = "VR" TEST.actions[2] = "Exe" TEST.setBody("HS", "/say my HS")')
    T.addMacro("Mine", "/dance", False)
    lua.execute('R2FCharDB.created["WARRIOR/Gone"] = { name = "Gone", hash = "0" }')  # macro deleted by hand
    lua.execute('R2F.Library.SetChanged("WARRIOR/VR", "updated")')
    check(lua.eval("#TEST.macros.char") == 3 and lua.eval("#TEST.macros.acc") == 3, "setup: 3 character + 2 account + 1 own macro")
    plan = M.RemoveAllPlan()
    check(names_of(plan.delete) == ["Exe", "Rend", "Slam", "VR"] and names_of(plan.keep) == ["HS"],
          "remove-all plan: every unedited one (on bars too, both scopes), edited kept: %s / %s"
          % (names_of(plan.delete), names_of(plan.keep)))
    check(len(T.calls) == 5 and all(c.startswith("create:") for c in lua_table_to_list(T.calls)),
          "remove-all plan writes nothing")

    # In combat: refused directly, queued through the confirm path.
    T.combat = True
    T.calls = lua.table()
    T.errors = lua.table()
    deleted, kept = M.RemoveAll()
    check((deleted, kept) == (0, 0) and len(T.calls) == 0 and lua.eval("TEST.errors[1]") == lua.eval("R2F.L.ERR_COMBAT"),
          "RemoveAll in combat refuses, no DeleteMacro (the fake client would raise)")
    check(lua.eval('R2FCharDB.created["WARRIOR/VR"] ~= nil and R2FDB.createdAccount["WARRIOR/Slam"] ~= nil'),
          "RemoveAll in combat keeps the tracking")
    lua.execute("R2F.Macros.RunOrQueue(function() RA_DEL, RA_KEPT = R2F.Macros.RemoveAll() end)")
    check(M.QueueSize() == 1 and len(T.calls) == 0, "remove all accepted in combat is queued")
    T.combat = False
    M.RunQueue()
    check((lua.eval("RA_DEL"), lua.eval("RA_KEPT")) == (4, 1), "queued remove all ran after combat: 4 deleted, 1 kept")
    check(all(T.bodyOf(n) is None for n in ("VR", "Rend", "Slam", "Exe")),
          "remove all deleted the unedited macros, including ones on bars and in account slots")
    check(T.bodyOf("HS") == "/say my HS" and T.bodyOf("Mine") == "/dance", "remove all kept the edited macro and the player's own")
    check(lua.eval("next(R2FCharDB.created) == nil and next(R2FDB.createdAccount) == nil"),
          "remove all cleared character AND account tracking (incl. the edited and stale records)")
    check(lua.eval("next(R2FCharDB.changed) == nil"), "remove all cleared the Changed flags")
    check(lua.eval("R2F.Library.Count()") == lib_count and lua.eval('R2F.Library.db.library["WARRIOR/VR"] ~= nil'),
          "remove all leaves R2FDB.library untouched")
    check(M.Ensure("WARRIOR/VR") is True and T.cursor == "VR", "after remove all the macro can be dragged out again")
    # HS is no longer ours: dragging it from the book asks first (it's the player's macro now).
    n_confirms = lua.eval("#CONFIRMS")
    check(M.Ensure("WARRIOR/HS") is False and lua.eval("#CONFIRMS") == n_confirms + 1,
          "the kept edited macro is the player's now: Ensure asks Replace/Keep mine")

    # Name lists in popups are capped.
    nl = lua.eval("R2F.UI.NameList")
    check(nl(lua.eval("{'a','b','c'}")) == "a, b, c", "NameList joins names")
    check(nl(lua.eval("(function() local t = {} for i = 1, 25 do t[i] = 'm' .. i end return t end)()"), 3) == "m1, m2, m3 and 22 more",
          "NameList caps long lists")

    # Init fills a partial minimap table without touching set values.
    lua.execute("R2FDB.minimap = { hide = true } R2F.Library.Init()")
    check(lua.eval("R2FDB.minimap.hide == true and R2FDB.minimap.lock == false and R2FDB.minimap.minimapPos == 220"),
          "Init fills missing minimap fields (LibDBIcon format) and keeps hide")


def test_step5_ui(templates, fx):
    """Step 5 through the UI: Settings panel, Remove all popup, combat state, key bindings."""
    lua = new_runtime(templates)
    tag = "templates" if templates else "fallbacks"
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    parse = lua.eval("function(s) local a, b = R2F.Import.Parse(s) return a, b end")
    res, _ = parse(fx["warriorUniversal"]["string"])
    lua.eval("R2F.Library.Apply")(res.records, 1)
    lib_count = lua.eval("R2F.Library.Count()")

    # Key bindings: Toggle / Open Macros toggle the book, Open Talents is a stub.
    lua.execute("R2F.Bindings.Toggle()")
    check(lua.eval("R2F.MacroBook.IsShown()") is True, "%s: binding Toggle opens the Macro Book" % tag)
    lua.execute("R2F.Bindings.Toggle()")
    check(lua.eval("R2F.MacroBook.IsShown()") is False, "binding Toggle closes it again")
    lua.execute("R2F.Bindings.OpenMacros()")
    check(lua.eval("R2F.MacroBook.IsShown()") is True, "binding Open Macros opens the Macro Book")
    T.chat = lua.table()
    lua.execute("R2F.Bindings.OpenTalents()")
    check(any(lua.eval("R2F.L.TALENTS_LATER") in c for c in chat_lines(lua)), "binding Open Talents says it comes later")
    for g in BINDING_GLOBALS:
        check(isinstance(lua.eval(g), str) and lua.eval(g) != "", "binding label global %s is set" % g)

    # Settings button opens the panel (no longer disabled).
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'Button' and f.__text == R2F.L.BTN_SETTINGS then SETBTN = f end
      end""")
    check(lua.eval("SETBTN.__enabled") is True, "%s: Settings button is enabled" % tag)
    lua.execute("SETBTN:Click()")
    check(lua.eval("R2FSettings and R2FSettings:IsShown()") is True, "%s: Settings button opens the Settings panel" % tag)
    lua.execute("""
      CHECKS = {}
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'CheckButton' and f.r2fLabel then CHECKS[f.r2fLabel.__text] = f end
        if f.__kind == 'Button' and f.__text == R2F.L.BTN_REMOVE_ALL then REMOVEALL = f end
      end
      L = R2F.L""")
    rb = lambda key: "CHECKS[L.%s]" % key
    check(lua.eval(rb("SETTINGS_SLOTS_CHAR") + ":GetChecked()") is True and lua.eval(rb("SETTINGS_SLOTS_ACC") + ":GetChecked()") is False,
          "Settings: Character slots first is selected by default")

    # Account first through the panel -> the next CreateMacro goes to account slots.
    lua.execute(rb("SETTINGS_SLOTS_ACC") + ":Click()")
    check(lua.eval("R2FDB.settings.slotsFirst") == "account", "Settings radio writes R2FDB.settings.slotsFirst")
    check(lua.eval(rb("SETTINGS_SLOTS_ACC") + ":GetChecked()") is True and lua.eval(rb("SETTINGS_SLOTS_CHAR") + ":GetChecked()") is False,
          "Settings: radio pair has exactly one selected")
    lua.execute('R2F.Macros.Ensure("WARRIOR/VR")')
    check(lua.eval("#TEST.macros.acc") == 1 and lua.eval("#TEST.macros.char") == 0,
          "%s: after choosing Account first in Settings, a dragged macro is created in an account slot" % tag)
    lua.execute(rb("SETTINGS_SLOTS_CHAR") + ":Click()")
    lua.execute('R2F.Macros.Ensure("WARRIOR/HS")')
    check(lua.eval("#TEST.macros.char") == 1 and lua.eval('GetMacroIndexByName("VR") <= 120'),
          "back to Character first: next macro in a character slot, VR stays in its account slot")

    # Minimap checkboxes: stored in R2FDB.minimap (step 6 reads them).
    check(lua.eval(rb("SETTINGS_MINIMAP_SHOW") + ":GetChecked()") is True and lua.eval(rb("SETTINGS_MINIMAP_LOCK") + ":GetChecked()") is False,
          "Settings: minimap shown + unlocked by default")
    lua.execute("APPLIED = 0 R2F.Minimap = { Apply = function() APPLIED = APPLIED + 1 end }")
    lua.execute(rb("SETTINGS_MINIMAP_SHOW") + ":Click() " + rb("SETTINGS_MINIMAP_LOCK") + ":Click()")
    check(lua.eval("R2FDB.minimap.hide") is True and lua.eval("R2FDB.minimap.lock") is True
          and lua.eval(rb("SETTINGS_MINIMAP_SHOW") + ":GetChecked()") is False and lua.eval(rb("SETTINGS_MINIMAP_LOCK") + ":GetChecked()") is True,
          "Settings: minimap checkboxes write R2FDB.minimap.hide / .lock")
    check(lua.eval("APPLIED") == 2, "Settings calls the step-6 hook R2F.Minimap.Apply after each minimap change")
    lua.execute(rb("SETTINGS_MINIMAP_SHOW") + ":Click() R2F.Minimap = nil")
    check(lua.eval("R2FDB.minimap.hide") is False, "Show minimap button toggles back")

    # Combat: Remove all greyed out, Settings button still usable.
    T.fire("PLAYER_REGEN_DISABLED")
    T.combat = True
    check(lua.eval("REMOVEALL.__enabled") is False and lua.eval("SETBTN.__enabled") is True,
          "combat greys out Remove all (Settings button stays usable)")
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")
    check(lua.eval("REMOVEALL.__enabled") is True, "combat end re-enables Remove all")

    # Remove all through the real confirm dialog; accepted in combat -> queued.
    lua.execute('TEST.actions[1] = "VR"')
    lua.execute("REMOVEALL:Click()")
    check(lua.eval("R2FConfirm:IsShown()") is True, "Remove all asks first")
    text = lua.eval("R2FConfirm.text.__text")
    check(text.startswith("Delete 2 Road to Forever macros") and "HS, VR" in text and "library stays" in text,
          "Remove all popup lists the macros and says the library stays: %r" % text)
    T.combat = True
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'Button' and f.__parent == R2FConfirm and f.__text == R2F.L.BTN_REMOVE then f:Click() end
      end""")
    check(T.bodyOf("VR") is not None and lua.eval("R2F.Macros.QueueSize()") == 1, "%s: Remove all accepted in combat waits" % tag)
    T.combat = False
    T.chat = lua.table()
    T.fire("PLAYER_REGEN_ENABLED")
    check(T.bodyOf("VR") is None and T.bodyOf("HS") is None, "%s: Remove all ran after combat" % tag)
    check(any("removed 2 Road to Forever macros." in c for c in chat_lines(lua)), "Remove all chat line")
    check(lua.eval("R2F.Library.Count()") == lib_count, "Remove all kept the library")
    T.chat = lua.table()
    lua.execute("REMOVEALL:Click()")
    check(any(lua.eval("R2F.L.REMOVE_ALL_NONE") in c for c in chat_lines(lua)), "Remove all with nothing to remove just says so")

    # Esc closes the panel; one-global audit with Settings built.
    check("R2FSettings" in lua_table_to_list(lua.eval("UISpecialFrames")), "Settings panel closes with Esc")
    new_globals = lua.eval("""(function()
      local out = {}
      for k in pairs(_G) do if not BEFORE[k] then table.insert(out, k) end end
      table.sort(out) return table.concat(out, ",") end)()""").split(",")
    test_vars = {"SETBTN", "CHECKS", "REMOVEALL", "L", "APPLIED", "NS"}
    bad = [g for g in new_globals if g and g not in test_vars and g not in BINDING_GLOBALS
           and g not in ("SLASH_R2F1",) and not g.startswith("R2F")]
    check(not bad, "%s: step 5 adds no globals besides R2F* frames and the binding labels: %s" % (tag, bad))


def test_bindings_xml(lua):
    """Bindings.xml: valid XML, not in the TOC, every binding has a label and calls a real function."""
    import xml.etree.ElementTree as ET
    path = os.path.join(ADDON, "Bindings.xml")
    root = ET.parse(path).getroot()
    check(root.tag == "Bindings", "Bindings.xml root is <Bindings>")
    check("Bindings.xml" not in toc_files(), "Bindings.xml is not listed in the TOC (the client loads it by itself)")
    names = []
    for b in root.findall("Binding"):
        name = b.get("name")
        names.append(name)
        check(isinstance(lua.eval("BINDING_NAME_" + name), str), "label BINDING_NAME_%s exists" % name)
        body = (b.text or "").strip()
        m = re.fullmatch(r"R2F\.Bindings\.(\w+)\(\)", body)
        check(m is not None and lua.eval("type(R2F.Bindings.%s)" % m.group(1)) == "function",
              "binding %s calls an existing R2F.Bindings function (%r)" % (name, body))
        if b.get("header"):
            check(isinstance(lua.eval("BINDING_HEADER_" + b.get("header")), str), "header label BINDING_HEADER_%s exists" % b.get("header"))
    check(names == ["R2F_TOGGLE", "R2F_MACROS", "R2F_TALENTS"], "the three bindings of ADDON_PLAN 6.1: %s" % names)
    check(root.find("Binding").get("header") == "ROADTOFOREVER", "first binding carries the header")


def main():
    fx = fixtures()
    lua = new_runtime()
    test_base64(lua, fx)
    test_import_parse(lua, fx)
    test_diff_and_library(lua, fx)
    test_site_cross_check(lua, fx)
    test_macros(new_runtime(), fx)
    test_updates(new_runtime(), fx)
    test_ui_updates(fx)
    test_ui_smoke(True, fx)
    test_ui_smoke(False, fx)
    test_step5_logic(new_runtime(), fx)
    test_step5_ui(True, fx)
    test_step5_ui(False, fx)
    test_bindings_xml(new_runtime())
    print("%d checks passed, %d failed" % (PASSES, len(FAILS)))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
