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
                    "TEST.templates.InputScrollFrameTemplate = nil")
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
    allowed_exact = {"R2F", "R2FDB", "R2FCharDB", "SLASH_R2F1"}
    test_vars = {"EDIT", "PREVIEW", "IMPORTBTN", "BADTEXT", "TABS", "SLOTS", "PAGETEXT", "TIDY", "BOOKIMPORT",
                 "COMBATTEXT", "OTHER", "NS"}
    bad = [g for g in new_globals if g and g not in allowed_exact and g not in test_vars and not g.startswith("R2F")]
    check(not bad, "%s: no globals besides R2F, saved vars, SLASH_R2F1 and R2F* frame names: %s" % (tag, bad))
    print("  %s: new globals = %s" % (tag, [g for g in new_globals if g not in test_vars]))


def main():
    fx = fixtures()
    lua = new_runtime()
    test_base64(lua, fx)
    test_import_parse(lua, fx)
    test_diff_and_library(lua, fx)
    test_site_cross_check(lua, fx)
    test_macros(new_runtime(), fx)
    test_ui_smoke(True, fx)
    test_ui_smoke(False, fx)
    print("%d checks passed, %d failed" % (PASSES, len(FAILS)))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
