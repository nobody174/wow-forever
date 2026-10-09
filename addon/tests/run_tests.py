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
import tempfile

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


def new_runtime(templates=True, before_load=None):
    """Fresh Lua 5.1 state with the WoW stubs and the addon loaded in TOC order.
    before_load: optional Lua source run after the stubs but before any addon
    file, for scenarios that need an API gone before addon code captures it
    as a local (same reason templates=False works the way it does below)."""
    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    assert lua.eval("_VERSION") == "Lua 5.1", lua.eval("_VERSION")
    stubs = os.path.join(HERE, "wow_stubs.lua").replace("\\", "/")
    lua.execute('assert(loadfile("%s"))()' % stubs)
    if before_load:
        lua.execute(before_load)
    if not templates:
        lua.execute("TEST.templates.PortraitFrameTemplate = nil; TEST.templates.ButtonFrameTemplate = nil;"
                    "TEST.templates.InputScrollFrameTemplate = nil; TEST.templates.UICheckButtonTemplate = nil;"
                    "TEST.templates.UIRadioButtonTemplate = nil;"
                    # Step 6 fallbacks: no tab template, no PanelTemplates helpers, no MenuUtil.
                    "TEST.templates.CharacterFrameTabButtonTemplate = nil; PanelTemplates_SetTab = nil;"
                    "PanelTemplates_SetNumTabs = nil; PanelTemplates_TabResize = nil; MenuUtil = nil;"
                    # Step 9 fallbacks: plain link box, no GameTooltip:SetTalent.
                    "TEST.templates.InputBoxTemplate = nil; GameTooltip.SetTalent = nil;"
                    # Step 10 fallbacks: no AnimationGroup (steady glow), no
                    # PanelTemplates_GetSelectedTab (reads .selectedTab).
                    "TEST.frameMethods.CreateAnimationGroup = nil; PanelTemplates_GetSelectedTab = nil")
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
    lua.execute('local r = R2F.Library.db.library["WARRIOR/Ham"]; r.body = r.body .. "\\n/say hi"')
    d = diff(wu, lib.db.library, "WARRIOR")
    check((d.updated, d.unchanged) == (1, n - 1), "edited library entry shows as updated")
    check(d.status["WARRIOR/Ham"] == "updated", "status per id")
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

    check(M.Ensure("WARRIOR/Ham") is True, "Ensure creates a new macro")
    check(T.cursor == "Ham", "new macro is on the cursor")
    check(lua.eval("#TEST.macros.char") == 1 and lua.eval("#TEST.macros.acc") == 0, "goes to character slots first")
    check(lua.eval('TEST.macros.char[1].icon') == "INV_MISC_QUESTIONMARK", "#showtooltip macro created with question mark icon")
    check(lua.eval('R2FCharDB.created["WARRIOR/Ham"].hash == R2F.Library.Hash(TEST.bodyOf("Ham"))'), "created record stores body hash")

    T.cursor = None
    check(M.Ensure("WARRIOR/Ham") is True and T.cursor == "Ham" and lua.eval("#TEST.macros.char") == 1,
          "Ensure on an existing own macro just picks it up")

    # Icon macro (no #showtooltip) keeps its icon.
    icon_id = next(r["id"] for r in fx["warriorUniversal"]["records"] if r["icon"] and not r["body"].startswith("#showtooltip"))
    icon_rec = next(r for r in fx["warriorUniversal"]["records"] if r["id"] == icon_id)
    M.Ensure(icon_id)
    check(lua.eval("(select(2, GetMacroInfo(GetMacroIndexByName(%r))))" % icon_rec["short"]) == icon_rec["icon"],
          "icon macro created with its icon (%s)" % icon_id)

    # Player edits our macro -> popup; Replace restores it.
    T.setBody("Ham", "/say mine")
    T.cursor = None
    check(M.Ensure("WARRIOR/Ham") is False and lua.eval("#CONFIRMS") == 1, "edited own macro asks Replace/Keep mine")
    check('"Ham"' in lua.eval("CONFIRMS[1].text"), "popup names the macro")
    check(T.cursor is None, "nothing picked up before an answer")
    lua.execute("CONFIRMS[1].fn()")
    check(T.bodyOf("Ham") == lua.eval('R2F.Library.db.library["WARRIOR/Ham"].body') and T.cursor == "Ham",
          "Replace restores the library body and picks it up")

    # Foreign macro with same name, different body: Keep mine = untouched.
    T.addMacro("OP", "/cast Heroic Strike", False)
    check(M.Ensure("WARRIOR/OP") is False and lua.eval("#CONFIRMS") == 2, "foreign macro with our name asks first")
    check(T.bodyOf("OP") == "/cast Heroic Strike", "Keep mine (no accept) leaves it alone")
    # Foreign macro with identical body -> adopted silently.
    sunder_body = lua.eval('R2F.Library.db.library["WARRIOR/Disarm"].body')
    T.addMacro("Disarm", sunder_body, False)
    check(M.Ensure("WARRIOR/Disarm") is True and lua.eval("#CONFIRMS") == 2 and lua.eval('R2FDB.createdAccount["WARRIOR/Disarm"] ~= nil'),
          "identical foreign macro is adopted without a popup (recorded as account)")

    # Combat: refused, nothing written (the fake errors on protected calls).
    T.combat = True
    T.errors = lua.table()
    check(M.Ensure("WARRIOR/Mock") is False, "Ensure refused in combat")
    check(lua.eval("TEST.errors[1]") == lua.eval("R2F.L.ERR_COMBAT"), "combat error text")
    check(lua.eval('GetMacroIndexByName("Mock")') == 0, "no macro created in combat")
    T.combat = False

    # Slots: fill character slots -> account; all full -> error.
    lua.execute("for i = 1, 30 - #TEST.macros.char do TEST.addMacro('c' .. i, 'x', true) end")
    M.Ensure("WARRIOR/Mock")
    check(lua.eval('GetMacroIndexByName("Mock") <= 120 and GetMacroIndexByName("Mock") > 0'), "full character slots -> account slot")
    check(lua.eval('R2FDB.createdAccount["WARRIOR/Mock"].account == true'), "account macro recorded in createdAccount")
    lua.execute("for i = 1, 120 - #TEST.macros.acc do TEST.addMacro('a' .. i, 'x', false) end TEST.errors = {}")
    check(M.Ensure("WARRIOR/Slam") is False and lua.eval("TEST.errors[1]") == lua.eval("R2F.L.ERR_NO_SLOTS"), "no free slots error")
    counts = M.Counts()
    check(tuple(counts) == (120, 120, 30, 30), "Counts() = acc, maxAcc, char, maxChar")

    # slotsFirst = account
    lua.execute("TEST.reset() R2FCharDB.created = {} R2FDB.createdAccount = {} R2FDB.settings.slotsFirst = 'account'")
    M.Ensure("WARRIOR/Ham")
    check(lua.eval("#TEST.macros.acc") == 1, "slotsFirst=account uses account slots")
    lua.execute("R2FDB.settings.slotsFirst = 'character'")

    # Tidy up: three ours; one on a bar, one edited, one free -> only the free one.
    lua.execute("TEST.reset() R2FCharDB.created = {} R2FDB.createdAccount = {}")
    for i in ("WARRIOR/Ham", "WARRIOR/OP", "WARRIOR/Mock", "WARRIOR/Slam"):
        M.Ensure(i)
    lua.execute('TEST.actions[1] = "Ham" TEST.setBody("OP", "/say edited")')
    T.addMacro("Mine", "/dance", True)
    cands = M.TidyCandidates()
    names = sorted(cands[i].name for i in range(1, len(cands) + 1))
    check(names == ["Mock", "Slam"], "tidy candidates = unedited, not on bars, ours only: %s" % names)
    check(M.Tidy(cands) == 2, "Tidy deletes both (indices re-looked-up after each delete)")
    check(T.bodyOf("Mock") is None and T.bodyOf("Slam") is None and T.bodyOf("Ham") and T.bodyOf("OP") and T.bodyOf("Mine"),
          "only the candidates were deleted")
    check(lua.eval('R2FCharDB.created["WARRIOR/Mock"] == nil'), "deleted macro's record removed")
    # Player deleted one of ours by hand -> record forgotten.
    lua.execute('DeleteMacro(GetMacroIndexByName("Ham"))')
    M.TidyCandidates()
    check(lua.eval('R2FCharDB.created["WARRIOR/Ham"] == nil'), "stale record dropped when the macro is gone")
    # Tidy in combat writes nothing.
    T.combat = True
    check(M.Tidy(cands) == 0, "Tidy refused in combat")
    T.combat = False

    # On-your-bars marker.
    M.Ensure("WARRIOR/Ham")
    lua.execute('TEST.actions[5] = "Ham"')
    check(M.OnBars("WARRIOR/Ham", M.NamesOnBars()) is True and M.OnBars("WARRIOR/OP", M.NamesOnBars()) is False, "OnBars marker")

    # Update (step 4 uses it): unedited -> edited in place; edited -> left alone; combat -> queued.
    lua.execute('R2F.Library.db.library["WARRIOR/Ham"].body = "#showtooltip Victory Rush\\n/cast Victory Rush"')
    check(M.Update("WARRIOR/Ham") == "updated" and T.bodyOf("Ham") == "#showtooltip Victory Rush\n/cast Victory Rush", "Update edits an unedited macro")
    check(M.Update("WARRIOR/Ham") == "unchanged", "Update on an up-to-date macro reports unchanged")
    check(M.Update("WARRIOR/OP") == "edited" and T.bodyOf("OP") == "/say edited", "Update leaves an edited macro alone")
    check(M.Update("WARRIOR/Slam") == "none", "Update with no real macro reports none")
    lua.execute('R2F.Library.db.library["WARRIOR/Ham"].body = "#showtooltip Victory Rush\\n/cast [harm] Victory Rush"')
    T.combat = True
    check(M.Update("WARRIOR/Ham") == "queued" and M.QueueSize() == 1, "Update in combat is queued")
    T.combat = False
    M.RunQueue()
    check(T.bodyOf("Ham").endswith("/cast [harm] Victory Rush") and M.QueueSize() == 0, "queued write runs after combat")

    # Icons / Learn later.
    ts = M.TooltipSpell
    check(ts("#showtooltip Victory Rush\n/cast [harm] Victory Rush") == "Victory Rush", "TooltipSpell: explicit")
    check(ts("#showtooltip\n/cast [harm] Rend") == "Rend", "TooltipSpell: from /cast")
    check(ts("#showtooltip\n/castsequence reset=3 Rend, Slam") == "Rend", "TooltipSpell: castsequence")
    check(ts("#showtooltip\n/cast !Auto Shot") == "Auto Shot", "TooltipSpell: strips !")
    check(ts("#showtooltip [mod:shift] Cleave; Heroic Strike") == "Cleave", "TooltipSpell: first clause")
    check(ts("/petattack [harm]") is None, "TooltipSpell: no #showtooltip -> nil")
    tex, later = M.DisplayIcon(lua.eval('R2F.Library.db.library["WARRIOR/OP"]'))
    check(tex == "Interface\\Icons\\Ability_Rogue_Ambush" and later is False, "known spell -> spell icon")
    tex, later = M.DisplayIcon(lua.eval('R2F.Library.db.library["WARRIOR/Mock"]'))
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
    for i in ("WARRIOR/Ham", "WARRIOR/OP", "WARRIOR/Mock", "WARRIOR/Slam"):
        M.Ensure(i)
    lua.execute('TEST.actions[1] = "Ham" TEST.actions[2] = "OP" TEST.actions[3] = "Slam"')
    T.setBody("OP", "/say my own HS")

    lib_body = lambda i: lua.eval('R2F.Library.db.library[%r].body' % i)
    new = {
        "WARRIOR/Ham": {"body": "#showtooltip Victory Rush\n/cast [harm] Victory Rush\n/say v2"},
        "WARRIOR/OP": {"body": "#showtooltip Heroic Strike\n/cast [harm] Heroic Strike\n/say v2"},
        "WARRIOR/Mock": {"body": "#showtooltip Rend\n/cast [harm] Rend\n/say v2"},
        "WARRIOR/Slam": {"note": "Only the note changed."},
    }
    res, _ = parse(import_string(modified(recs, new)))
    d = diff(res, Lib.db.library, "WARRIOR")
    check(d.updated == 4, "diff: 4 updated records (got %s)" % d.updated)
    check(lua_table_to_list(d.plan.update) == ["WARRIOR/Ham", "WARRIOR/Mock"],
          "plan: unedited real macros with a new body are updated, note-only change is not (%s)" % lua_table_to_list(d.plan.update))
    check(lua_table_to_list(d.plan.edited) == ["WARRIOR/OP"], "plan: the hand-edited macro is reported as kept")
    text = preview(d)
    check(text.split("\n")[0] == "%d macros: 0 new, 4 updated, %d unchanged." % (len(recs), len(recs) - 4),
          "preview first line keeps the 5.6 wording: " + text.split("\n")[0])
    check(text.endswith("\n" + Ltxt.IMPORT_WILL_UPDATE.replace("%d", "2") + " " + Ltxt.IMPORT_WILL_KEEP_ONE),
          "preview second line: will update 2, keep 1 edited: %r" % text)
    check(T.bodyOf("Ham") != new["WARRIOR/Ham"]["body"], "preview/diff writes nothing")

    T.calls = lua.table()
    T.chat = lua.table()
    d = commit(res, "WARRIOR", 2)
    calls = lua_table_to_list(T.calls)
    check(calls == ["edit:Ham", "edit:Mock"], "re-import EditMacro'd exactly the unedited changed macros: %s" % calls)
    check(T.bodyOf("Ham") == new["WARRIOR/Ham"]["body"] and T.bodyOf("Mock") == new["WARRIOR/Mock"]["body"],
          "re-import pushed the new bodies to the real macros")
    check(lua.eval('R2FCharDB.created["WARRIOR/Ham"].hash == R2F.Library.Hash(TEST.bodyOf("Ham"))'),
          "stored hash follows the update (so the macro still counts as unedited)")
    check(T.bodyOf("OP") == "/say my own HS", "hand-edited real macro left untouched")
    check(lib_body("WARRIOR/OP") == new["WARRIOR/OP"]["body"], "library still takes the new version of the edited macro")
    check(d.applied == "now", "updates ran right away out of combat")
    chat = chat_lines(lua)
    check(any("updated 2 of your macros to the new version." in c for c in chat), "chat: updated 2")
    check(any("kept your edits to OP." in c for c in chat), "chat: kept the edited one, by name: %s" % chat)
    check(lua.eval('R2FCharDB.changed["WARRIOR/Ham"]') == "updated", "Changed flag set for an updated macro on a bar")
    check(lua.eval('R2FCharDB.changed["WARRIOR/OP"]') == "edited", "Changed flag (edited kind) for the kept macro on a bar")
    check(lua.eval('R2FCharDB.changed["WARRIOR/Mock"]') is None, "no Changed flag for an updated macro not on any bar")
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
    v3["WARRIOR/Ham"] = {"body": "#showtooltip Victory Rush\n/cast [harm] Victory Rush\n/say v3"}
    v3["WARRIOR/Mock"] = {"body": "#showtooltip Rend\n/cast [harm] Rend\n/say v3"}
    res3, _ = parse(import_string(modified(recs, v3)))
    lua.execute('R2FCharDB.changed = {}')
    T.calls = lua.table()
    T.chat = lua.table()
    T.combat = True
    d = commit(res3, "WARRIOR", 4)  # the fake client raises if EditMacro runs in combat
    check(d.applied == "queued" and M.QueueSize() == 1, "import in combat queues ONE update job")
    check(len(T.calls) == 0 and T.bodyOf("Ham").endswith("v2"), "nothing written in combat")
    check(lib_body("WARRIOR/Ham").endswith("v3"), "library updated even in combat (SavedVariables only)")
    check(any(Ltxt.UPDATED_QUEUED.replace("%d", "2") in c for c in chat_lines(lua)), "chat says it will update after combat")
    check(lua.eval('R2FCharDB.changed["WARRIOR/Ham"]') == "updated", "queued update shows its Changed marker right away")
    # The player edits Rend before combat ends: the queued job must re-check and leave it.
    T.setBody("Mock", "/say edited in combat")
    T.combat = False
    M.RunQueue()
    check(T.bodyOf("Ham").endswith("v3") and M.QueueSize() == 0, "queued EditMacro runs on PLAYER_REGEN_ENABLED")
    check(T.bodyOf("Mock") == "/say edited in combat", "queued update re-checks: macro edited meanwhile is left alone")
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
    lua.execute('R2F.Library.db.library["WARRIOR/Ham"].body = "#showtooltip Victory Rush\\n/cast Victory Rush"')
    T.cursor = None
    check(M.Ensure("WARRIOR/Ham") is True and T.cursor == "Ham" and T.bodyOf("Ham") == "#showtooltip Victory Rush\n/cast Victory Rush"
          and lua.eval("#CONFIRMS") == 0, "Ensure updates a stale unedited macro, then picks it up (no popup)")

    # Login sync (library changed by an import on another character).
    lua.execute('R2F.Library.db.library["WARRIOR/Ham"].body = "#showtooltip Victory Rush\\n/cast [harm] Victory Rush\\n/say alt"')
    lua.execute('R2FCharDB.changed = { ["PALADIN/HL"] = "updated", ["WARRIOR/Gone"] = "updated" }')
    T.chat = lua.table()
    check(M.SyncOnLogin() == 1 and T.bodyOf("Ham").endswith("/say alt"), "login sync updates this character's stale unedited macro")
    check(T.bodyOf("Mock") == "/say edited in combat", "login sync leaves edited macros alone")
    check(any("to the version in your library" in c for c in chat_lines(lua)), "login sync says so in chat")
    check(lua.eval('R2FCharDB.changed["PALADIN/HL"] == nil and R2FCharDB.changed["WARRIOR/Gone"] == nil'),
          "login drops Changed flags that could never be hovered")
    check(lua.eval('R2FCharDB.changed["WARRIOR/Ham"]') == "updated", "login sync marks the updated macro on a bar")
    T.combat = True
    lua.execute('R2F.Library.db.library["WARRIOR/Ham"].body = "#showtooltip Victory Rush\\n/say reload in combat"')
    check(M.SyncOnLogin() == 1 and M.QueueSize() == 1 and not T.bodyOf("Ham").endswith("combat"), "login sync in combat is queued")
    T.combat = False
    M.RunQueue()
    check(T.bodyOf("Ham").endswith("reload in combat"), "queued login sync runs after combat")

    # Flags go away with the library entry or the real macro.
    lua.execute('R2F.Library.SetChanged("WARRIOR/Ham", "updated") R2F.Library.Remove("WARRIOR/Ham")')
    check(lua.eval('R2FCharDB.changed["WARRIOR/Ham"]') is None, "Remove from library clears the Changed flag")
    lua.execute('R2F.Library.SetChanged("WARRIOR/Slam", "updated") R2F.Library.SetCreated("WARRIOR/Slam", nil)')
    check(lua.eval('R2FCharDB.changed["WARRIOR/Slam"]') is None, "forgetting the real macro clears the Changed flag")
    # Replace answers an "edited" Changed note.
    lua.execute('R2F.Library.SetChanged("WARRIOR/OP", "edited")')
    M.Ensure("WARRIOR/OP")
    lua.execute("CONFIRMS[#CONFIRMS].fn()")
    check(T.bodyOf("OP") == lib_body("WARRIOR/OP") and lua.eval('R2FCharDB.changed["WARRIOR/OP"]') is None,
          "Replace on an edited macro installs the new version and clears its flag")


def test_stance():
    """Warrior stance icon: shown per stance, lock, scale, slash commands, non-warriors."""
    lua = new_runtime()
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    check(lua.eval("R2FStanceFrame ~= nil"), "stance: frame built for a Warrior")
    st = "R2FDB.stance"
    check(lua.eval(st + ".shown") is True and lua.eval(st + ".scale") == 1, "stance: defaults")
    lua.execute("TEST.stanceIndex = 3 R2F.Stance.Update()")
    check(lua.eval("R2FStanceFrame.border ~= nil"), "stance: border texture exists")
    lua.execute('SlashCmdList.R2F("stance lock")')
    check(lua.eval(st + ".lock") is True, "stance: /r2f stance lock locks")
    lua.execute('SlashCmdList.R2F("stance")')
    check(lua.eval(st + ".shown") is False, "stance: /r2f stance hides")
    lua.execute("R2F.Stance.SetScale(9)")
    check(lua.eval(st + ".scale") == 3, "stance: scale clamped to 3")
    lua.execute("R2F.Stance.SetScale(0.1)")
    check(lua.eval(st + ".scale") == 0.5, "stance: scale clamped to 0.5")
    lua.execute("R2F.Settings.Show()")
    check(lua.eval("R2FStanceScale ~= nil"), "stance: Settings has the size slider")
    lua.execute('SlashCmdList.R2F("help")')
    # Non-warrior: no frame, no Settings section, command only prints.
    lua = new_runtime()
    T = lua.eval("TEST")
    T.classToken = "PRIEST"
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    check(lua.eval("R2FStanceFrame == nil"), "stance: no frame for a Priest")
    lua.execute('SlashCmdList.R2F("stance")')
    lua.execute("R2F.Settings.Show()")
    check(lua.eval("R2FStanceScale == nil"), "stance: no Settings section for a Priest")


def import_string_k(records, keep=None):
    """import_string plus K records (ADDON_PLAN 15.1): keep = {CLASS: [every id on the site]}."""
    parts = ["\x1f".join(r[k] for k in FIELDS) for r in records]
    for cls, ids in (keep or {}).items():
        parts.append("\x1f".join(["K", cls, ",".join(ids)]))
    return "R2F1:" + base64.b64encode(("v=1\n" + "\x1e".join(parts)).encode("utf-8")).decode()


def test_import_replaces(fx):
    """ADDON_PLAN 15.1: the import string's K lines make an import remove what the site dropped."""
    recs = {r["id"]: r for r in fx["warriorUniversal"]["records"]}
    war = [i for i in recs if i.startswith("WARRIOR/")]
    anyc = [i for i in recs if i.startswith("ANY/")]
    HAM, SLAM, EXE, OP, KICK, DIS = ("WARRIOR/Ham", "WARRIOR/Slam", "WARRIOR/Exe",
                                     "WARRIOR/OP", "WARRIOR/Kick", "WARRIOR/Disarm")
    for i in (HAM, SLAM, EXE, OP, KICK, DIS):
        check(i in recs, "15.1 fixture has " + i)

    def fresh():
        lua = new_runtime()
        lua.execute("TEST.reset() R2FDB = nil R2FCharDB = nil R2F.Library.Init() R2F.playerClass = 'WARRIOR'")
        lua.globals().S = import_string_k([recs[i] for i in recs])  # whole library, no K
        lua.execute("R2F.Library.Apply(R2F.Import.Parse(S).records, 1)")
        return lua, lua.eval("TEST")

    def commit(lua, ids, keep, replace=False):
        lua.globals().S = import_string_k([recs[i] for i in ids], keep)
        lua.globals().REPLACE = replace
        lua.execute("PARSED = R2F.Import.Parse(S) D = R2F.Import.Commit(PARSED, 'WARRIOR', 2, { replace = REPLACE })")

    def has(lua, i):
        return lua.eval('R2F.Library.Get("%s") ~= nil' % i)

    def chat(lua):
        return "\n".join(lua.eval("TEST.chat[%d]" % n) for n in range(1, lua.eval("#TEST.chat") + 1))

    # --- Parse: K lines are read, not counted as skipped ---------------------
    lua = new_runtime()
    lua.globals().S = import_string_k([recs[HAM]], {"WARRIOR": [HAM, SLAM], "ANY": []})
    check(lua.eval("R2F.Import.Parse(S).skipped") == 0 and lua.eval("#R2F.Import.Parse(S).records") == 1,
          "15.1 parse: K lines are not records and not 'skipped'")
    check(lua.eval("R2F.Import.Parse(S).keep.WARRIOR['%s']" % SLAM) is True
          and lua.eval("R2F.Import.Parse(S).keep.WARRIOR['%s']" % OP) is None
          and lua.eval("next(R2F.Import.Parse(S).keep.ANY)") is None, "15.1 parse: keep sets (and an empty one)")
    lua.globals().S = import_string_k([recs[HAM]], {"NOPE": [HAM]})
    check(lua.eval("R2F.Import.Parse(S).skipped") == 1 and lua.eval("next(R2F.Import.Parse(S).keep)") is None,
          "15.1 parse: a K line for an unknown class is skipped as damaged")
    # The real site string carries K lines listing every id of each carried class.
    lua.globals().S = fx["warriorUniversal"]["string"]
    every = {c: {r["id"] for r in fx["everything"]["records"] if r["class"] == c} for c in ("WARRIOR", "ANY")}
    check(lua.eval("R2F.Import.Parse(S).skipped") == 0, "15.1 site string: nothing skipped")
    for c, ids in every.items():
        n = lua.eval("(function() local n = 0 for _ in pairs(R2F.Import.Parse(S).keep.%s) do n = n + 1 end return n end)()" % c)
        check(n == len(ids), "15.1 site string: K %s lists all %d ids on the site (%d)" % (c, len(ids), n))

    # --- Old string (no K lines): add-only, as before --------------------------
    lua, T = fresh()
    before = lua.eval("R2F.Library.Count()")
    commit(lua, [HAM], None)
    check(lua.eval("R2F.Library.Count()") == before and lua.eval("#D.gone") == 0
          and "removed from the site" not in lua.eval("R2F.Import.PreviewText(D)"),
          "15.1 old string without K: nothing removed, no removal line")

    # --- Removed id leaves; unpicked id stays; other classes untouched ------------
    lua, T = fresh()
    keep_war = [i for i in war if i != SLAM]          # the site dropped Slam
    commit(lua, [HAM], {"WARRIOR": keep_war})
    check(not has(lua, SLAM), "15.1 an id missing from K leaves the library")
    check(has(lua, HAM) and has(lua, EXE) and has(lua, OP), "15.1 macros the player didn't pick (still in K) stay")
    check(all(has(lua, i) for i in anyc), "15.1 a class without a K line is not touched (Universal)")
    check(lua.eval("#D.gone") == 1, "15.1 diff lists exactly the one removed id")
    pv = lua.eval("R2F.Import.PreviewText(D)")
    check("1 macro was removed from the site and leaves your library." in pv, "15.1 preview line (one): %r" % pv)
    check(lua.eval("R2F.Library.Count()") == len(recs) - 1, "15.1 library count after")

    # Plural wording + 'exist as game macros' count in the preview (before commit).
    lua, T = fresh()
    for i in (SLAM, EXE):
        lua.execute('R2F.Macros.Ensure("%s")' % i)
    lua.globals().S = import_string_k([recs[HAM]], {"WARRIOR": [i for i in war if i not in (SLAM, EXE, OP)]})
    lua.execute("PARSED = R2F.Import.Parse(S) DD = R2F.Import.Diff(PARSED, R2F.Library.db.library, 'WARRIOR')")
    pv = lua.eval("R2F.Import.PreviewText(DD)")
    check("3 macros were removed from the site and leave your library. 2 of them exist as game macros." in pv,
          "15.1 preview line (plural + game macros): %r" % pv)

    # --- Game macros: unedited+unused deleted; on a bar / edited kept, listed ----
    lua, T = fresh()
    for i in (SLAM, EXE, OP, KICK, DIS):
        lua.execute('R2F.Macros.Ensure("%s")' % i)
    T.actions[5] = "Kick"                               # on a bar
    lua.execute('TEST.setBody("OP", "/say mine")')      # edited by the player
    T.addMacro("Mine", "/dance", True)                  # the player's own macro
    T.chat = lua.table()
    keep = [i for i in war if i not in (SLAM, EXE, OP, KICK, DIS)]
    commit(lua, [HAM], {"WARRIOR": keep})
    check(T.bodyOf("Slam") is None and T.bodyOf("Exe") is None and T.bodyOf("Disarm") is None,
          "15.1 unedited, unused game macros of removed entries are deleted")
    check(T.bodyOf("Kick") is not None and T.bodyOf("OP") == "/say mine" and T.bodyOf("Mine") == "/dance",
          "15.1 on-bar and edited game macros (and the player's own) are kept")
    txt = chat(lua)
    check("deleted 3 game macros" in txt, "15.1 chat: deleted count: %r" % txt)
    check("kept, still on your bars: Kick" in txt and "kept, edited by you: OP" in txt, "15.1 chat lists the kept ones")
    check(not any(has(lua, i) for i in (SLAM, EXE, OP, KICK, DIS)), "15.1 all five left the library")
    check(lua.eval('R2F.Library.Created("WARRIOR/Kick") ~= nil') and lua.eval('R2F.Library.Created("WARRIOR/Slam") == nil'),
          "15.1 kept macros stay tracked (Tidy up can take them later); deleted ones are forgotten")
    T.actions[5] = None   # Kick leaves the bar: Tidy up now offers it
    check("Kick" in names_of(lua.eval("R2F.Macros.TidyCandidates()")), "15.1 a kept macro is Tidy-able once off the bars")

    # --- Still on the site but changed: updates in place, not removed -------------
    lua, T = fresh()
    lua.execute('R2F.Macros.Ensure("%s")' % HAM)
    T.actions[1] = "Ham"
    changed = dict(recs[HAM])
    changed["body"] = "#showtooltip\n/cast Hamstring (new)"
    lua.globals().S = import_string_k([changed], {"WARRIOR": war})
    lua.execute("PARSED = R2F.Import.Parse(S) D = R2F.Import.Commit(PARSED, 'WARRIOR', 2)")
    check(has(lua, HAM) and T.bodyOf("Ham") == changed["body"] and lua.eval("#D.gone") == 0,
          "15.1 changed-but-still-on-site macro updates in place and stays")

    # --- Combat: library change now, game macro deletion queued -------------------
    lua, T = fresh()
    lua.execute('R2F.Macros.Ensure("%s")' % SLAM)
    T.combat = True
    T.calls = lua.table()
    T.chat = lua.table()
    commit(lua, [HAM], {"WARRIOR": [i for i in war if i != SLAM]})
    check(not has(lua, SLAM) and T.bodyOf("Slam") is not None and lua.eval("R2F.Macros.QueueSize()") == 1,
          "15.1 combat: library entry gone at once, game macro delete queued")
    check("when combat ends" in chat(lua), "15.1 combat: queued message")
    T.combat = False
    lua.execute("R2F.Macros.RunQueue()")
    check(T.bodyOf("Slam") is None and lua.eval("R2F.Macros.QueueSize()") == 0, "15.1 combat: deleted after combat")
    # Combat with nothing to delete (only kept macros): no queue, lists printed.
    lua, T = fresh()
    lua.execute('R2F.Macros.Ensure("%s")' % KICK)
    T.actions[3] = "Kick"
    T.combat = True
    T.chat = lua.table()
    commit(lua, [HAM], {"WARRIOR": [i for i in war if i != KICK]})
    check(lua.eval("R2F.Macros.QueueSize()") == 0 and T.bodyOf("Kick") is not None
          and "kept, still on your bars: Kick" in chat(lua), "15.1 combat: nothing to delete -> nothing queued, kept listed")
    T.combat = False

    # --- Replace checkbox: everything of the carried classes not in the string -----
    lua, T = fresh()
    lua.execute('R2F.Macros.Ensure("%s")' % EXE)
    lua.globals().S = import_string_k([recs[HAM]], None)          # old-style string, one macro
    lua.execute("PARSED = R2F.Import.Parse(S) DD = R2F.Import.Diff(PARSED, R2F.Library.db.library, 'WARRIOR', { replace = true })")
    check(lua.eval("#DD.gone") == len(war) - 1, "15.1 replace: diff = all other Warrior macros")
    check("are not in this string and leave your library" in lua.eval("R2F.Import.PreviewText(DD)"), "15.1 replace: preview wording")
    commit(lua, [HAM], None, replace=True)
    check(has(lua, HAM) and not any(has(lua, i) for i in war if i != HAM), "15.1 replace: only the string's macros remain for the class")
    check(all(has(lua, i) for i in anyc), "15.1 replace: classes the string doesn't carry are untouched")
    check(T.bodyOf("Exe") is None, "15.1 replace: unedited unused game macro deleted too")
    lua, T = fresh()
    commit(lua, [HAM, SLAM], {"WARRIOR": war}, replace=True)
    check(lua.eval("R2F.Library.Count()") == 2 + len(anyc), "15.1 replace with a K string: unpicked Warrior macros go too")


def test_settings_tab(templates, fx):
    """ADDON_PLAN 15.2: Settings tab, Home as 'what's next', tree names, checked-glow fix."""
    lua = new_runtime(templates)
    tag = "templates" if templates else "fallbacks"
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    L = lua.eval("R2F.L")
    R2F_L_STANCE_SHOW = lua.eval("R2F.L.SETTINGS_STANCE_SHOW")
    MW = lua.eval("R2F.MainWindow")
    res = lua.eval("function(s) local a, b = R2F.Import.Parse(s) return a, b end")(fx["warriorUniversal"]["string"])[0]
    lua.eval("R2F.Library.Apply")(res.records, 1)

    # --- Fourth tab, slash command, title -----------------------------------------
    lua.execute('SlashCmdList.R2F("settings")')
    check(MW.IsShown() is True and MW.CurrentTab() == "settings", "%s: /r2f settings opens the Settings tab" % tag)
    win = "R2FMain" if templates else "R2FMainPlain"
    title = lua.eval("%s.__title" % win) if templates else lua.eval("%s.r2fTitle.__text" % win)
    check(title == "Road to Forever: Settings", "%s: Settings title: %r" % (tag, title))
    check(lua.eval("R2FDB.settings.lastTab") == "settings", "Settings can be the remembered last tab")
    lua.execute("R2F.MainWindow.SelectTab('macros')")
    check(lua.eval("R2F.Settings.IsShown()") is False, "Settings.IsShown() false on another tab")

    # --- Home is a short 'what's next' list; Quick settings are not on it -----------
    lua.execute("R2F.MainWindow.SelectTab('home')")
    find_frames(lua, "f.__kind == 'Button' and f.tab ~= nil and f.sub ~= nil", "HOME")
    check(lua.eval("#HOME") == 3, "%s: Home has three entries" % tag)
    check(font_text(lua, "^What's next$") == "What's next", "Home heading")
    acc_n, acc_max, char_n, char_max = lua.eval("R2F.Macros.Counts()")
    check(lua.eval("HOME[3].sub.__text") == "%d of %d character slots, %d of %d account slots used" % (char_n, char_max, acc_n, acc_max),
          "Home slot line: %r" % lua.eval("HOME[3].sub.__text"))
    lua.execute('TEST.addMacro("Mine", "/dance", true) R2F.Home.Refresh()')
    check(lua.eval("HOME[3].sub.__text").startswith("%d of %d character slots" % (char_n + 1, char_max)),
          "Home slot line follows the live macro count")
    find_frames(lua, "f.qsItem ~= nil", "QSB")
    check(lua.eval("#QSB") == 3 and lua.eval("QSB[1]:IsVisible()") is False,
          "Quick settings boxes exist but are not on the Home page")

    # --- Settings page content ----------------------------------------------------
    lua.execute("R2F.MainWindow.SelectTab('settings')")
    for key in ("SETTINGS_MACROS", "SETTINGS_MINIMAP", "QS_TITLE"):
        check(font_text(lua, "^" + lua.eval("R2F.L.%s" % key) + "$") is not None, "Settings tab has the %s heading" % key)
    check(lua.eval("QSB[1]:IsVisible()") is True, "%s: Quick settings boxes visible on the Settings tab" % tag)
    find_frames(lua, "f.__kind == 'Button' and f.__text == R2F.L.BTN_REMOVE_ALL", "RM")
    check(lua.eval("#RM") == 1 and lua.eval("RM[1]:IsVisible()") is True, "Remove all is on the Settings tab")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel", "CBS")
    labels = {lua.eval("CBS[%d].r2fLabel.__text" % i) for i in range(1, lua.eval("#CBS") + 1)}
    for key in ("SETTINGS_SLOTS_CHAR", "SETTINGS_SLOTS_ACC", "SETTINGS_MINIMAP_SHOW", "SETTINGS_MINIMAP_LOCK",
                "QS_ZOOM", "QS_GUILD", "QS_PVP", "BAGS_MOVABLE", "BAGS_LOCK"):
        check(lua.eval("R2F.L.%s" % key) in labels, "Settings tab has the %s control" % key)
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.SETTINGS_STANCE_SHOW", "SSB")
    check(lua.eval("R2FStanceScale ~= nil and R2FStanceScale:IsVisible()") is False
          and lua.eval("#SSB == 0 or not SSB[1]:IsVisible()") is True, "stance options are not on the Settings tab any more (15.4)")
    # Combat greys Remove all and the Quick settings boxes through the tab.
    T.combat = True
    T.fire("PLAYER_REGEN_DISABLED")
    check(lua.eval("RM[1]:IsEnabled()") is False and lua.eval("QSB[1]:IsEnabled()") is False, "combat greys Remove all + Quick settings")
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")
    check(lua.eval("RM[1]:IsEnabled()") is True and lua.eval("QSB[1]:IsEnabled()") is True, "after combat both are enabled again")
    # The old floating panel and its button are gone.
    check(lua.eval("R2FSettings == nil"), "no floating Settings panel")
    check("R2FSettings" not in lua_table_to_list(lua.eval("UISpecialFrames")), "R2FSettings not in UISpecialFrames")

    # --- Black squares: checked glow + icon fallback --------------------------------
    lua.execute("R2F.MainWindow.SelectTab('macros') R2F.MacroBook.Refresh()")
    check(lua.eval("R2F.UI.FALLBACK_ICON") == "Interface\\Icons\\INV_Misc_QuestionMark", "fallback icon is a standard icon")
    lua.execute("""
      GLOWS, BADGLOWS = 0, 0
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'CheckButton' and f.__checked_tex_marker == nil then
          local c = f.GetCheckedTexture and f:GetCheckedTexture()
          if c and c.__tex ~= 'Interface\\\\Buttons\\\\UI-CheckBox-Check' then
            GLOWS = GLOWS + 1
            if c.__blend ~= 'ADD' or c.__tex ~= 'Interface\\\\Buttons\\\\ButtonHilight-Square' then BADGLOWS = BADGLOWS + 1 end
          end
        end
      end""")
    check(lua.eval("GLOWS") >= 3 and lua.eval("BADGLOWS") == 0,
          "%s: every class circle and side tab draws its selected state as an ADD-blended glow (%s, %s bad)"
          % (tag, lua.eval("GLOWS"), lua.eval("BADGLOWS")))
    check(lua.eval("""(function()
        for _, f in ipairs(TEST.allFrames) do
          if f.__kind == 'CheckButton' and f.GetCheckedTexture and f:GetCheckedTexture() then
            if f:GetCheckedTexture().__tex == 'Interface\\\\Buttons\\\\CheckButtonHilight' then return false end
          end
        end
        return true end)()"""), "the black-square texture (CheckButtonHilight) is no longer used for checked states")
    lua.execute("""
      local b = CreateFrame('CheckButton', nil, UIParent)
      R2F.UI.SetNormalIcon(b, nil)
      NORM1 = b:GetNormalTexture().__tex
      R2F.UI.SetNormalIcon(b, 'Interface\\\\Icons\\\\INV_Misc_Book_09')
      NORM2 = b:GetNormalTexture().__tex""")
    check(lua.eval("NORM1") == "Interface\\Icons\\INV_Misc_QuestionMark" and lua.eval("NORM2") == "Interface\\Icons\\INV_Misc_Book_09",
          "SetNormalIcon falls back to the question mark for an empty path")


def test_tree_names():
    """15.2: the Talents tab's tree names = talentcalc.js CLASSES (same names, same order)."""
    js = open(os.path.join(ROOT, "talentcalc.js"), encoding="utf-8").read()
    classes = re.findall(r'\{ id: "(\w+)",\s+name: "\w+",\s+color: "#\w+", trees: \[\[\d+, "([^"]+)"\], \[\d+, "([^"]+)"\], \[\d+, "([^"]+)"\]\] \}', js)
    check(len(classes) == 9, "15.2 talentcalc.js CLASSES parsed: %d classes" % len(classes))
    lua = new_runtime()
    lua.execute("GetTalentTabInfo = nil")
    for cid, a, b, c in classes:
        got = [lua.eval("R2F.Talents.TreeName(%d, %r)" % (i, cid.upper())) for i in (1, 2, 3)]
        check(got == [a, b, c], "15.2 tree names for %s: %s" % (cid, got))
    check(lua.eval("(function() local n = 0 for _ in pairs(R2F.Talents.TREE_NAMES) do n = n + 1 end return n end)()") == 9,
          "15.2 TREE_NAMES has exactly the nine classes")


BAG_FRAMES_LUA = """
  local function mk(name, id)
    local f = CreateFrame('Frame', name, UIParent)
    f:SetID(id)
    f.__shown = false
    return f
  end
  NUM_CONTAINER_FRAMES = 3
  STYLE_CLASSIC, STYLE_COMBINED = %s, %s
  if STYLE_CLASSIC then
    mk('ContainerFrame1', 0) mk('ContainerFrame2', 1) mk('ContainerFrame3', 2)
  end
  if STYLE_COMBINED then mk('ContainerFrameCombinedBags', 0) end
  -- The game's own stacking: every open window sits at its default spot.
  ANCHOR_CALLS = 0
  function UpdateContainerFrameAnchors()
    ANCHOR_CALLS = ANCHOR_CALLS + 1
    for _, name in ipairs({ 'ContainerFrame1', 'ContainerFrame2', 'ContainerFrame3', 'ContainerFrameCombinedBags' }) do
      local f = _G[name]
      if f and f:IsShown() then
        f:ClearAllPoints()
        f:SetPoint('BOTTOMRIGHT', UIParent, 'BOTTOMRIGHT', -10, 100)
      end
    end
  end
  MOVES = 0
  for _, name in ipairs({ 'ContainerFrame1', 'ContainerFrame2', 'ContainerFrame3', 'ContainerFrameCombinedBags' }) do
    local f = _G[name]
    if f then f.StartMoving = function() MOVES = MOVES + 1 end end
  end
"""


def bag_runtime(classic, combined, saved=None):
    lua = new_runtime()
    lua.execute("TEST.reset()")
    lua.execute(BAG_FRAMES_LUA % ("true" if classic else "false", "true" if combined else "false"))
    if saved:
        lua.execute("R2FCharDB = %s" % saved)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    return lua, T


def bag_point(lua, name):
    return lua.eval("(function() local p = %s.__point return p and table.concat({ tostring(p[1]), tostring(p[2] == UIParent and 'UIParent' or p[2]), "
                    "tostring(p[3]), tostring(p[4]), tostring(p[5]) }, ',') end)()" % name)


def bag_drag(lua, name, point, x, y):
    """Simulate a drag: the game reports `point` for the frame after StopMovingOrSizing."""
    lua.execute("%s.GetPoint = function() return %r, UIParent, %r, %d, %d end" % (name, point, point, x, y))
    lua.execute("%s:Fire('OnDragStart') %s:Fire('OnDragStop')" % (name, name))


def test_bags():
    """ADDON_PLAN 15.3: movable bags for classic ContainerFrameN and the combined bag."""
    # --- Detection at run time ----------------------------------------------------
    for classic, combined, want in ((True, False, "classic"), (False, True, "combined"), (True, True, "both"), (False, False, None)):
        lua, T = bag_runtime(classic, combined)
        check(lua.eval("R2F.Bags.Style()") == want, "15.3 detects the bag style: %s" % want)
        check(lua.eval("R2F.Bags.Available()") is (want is not None), "15.3 Available() for %s" % want)
    lua, T = bag_runtime(False, False)
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("bags")')
    check(any("no bag windows found" in c for c in lua_table_to_list(lua.eval("TEST.chat"))), "15.3 /r2f bags says when nothing is found")
    check(lua.eval("R2F.Bags.SetMovable(true)") is True and lua.eval("R2FCharDB.bags.movable") is True,
          "15.3 enabling with no bag windows is harmless")
    lua, T = bag_runtime(True, True)
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("bags")')
    check(any("bag windows found: both" in c for c in lua_table_to_list(lua.eval("TEST.chat"))), "15.3 /r2f bags reports both styles")

    # --- Defaults: off, per character, nothing touched ---------------------------------
    lua, T = bag_runtime(True, False)
    check(lua.eval("R2FCharDB.bags.movable") is False and lua.eval("R2FCharDB.bags.lock") is False
          and lua.eval("R2FDB.bags == nil"), "15.3 off by default, stored per character (R2FCharDB.bags)")
    lua.execute("ContainerFrame1:Show() UpdateContainerFrameAnchors()")
    bag_drag(lua, "ContainerFrame1", "BOTTOMLEFT", 300, 400)
    check(lua.eval("MOVES") == 0 and lua.eval("R2FCharDB.bags.bags[0] == nil"), "15.3 not movable: dragging does nothing and saves nothing")
    check(bag_point(lua, "ContainerFrame1") == "BOTTOMRIGHT,UIParent,BOTTOMRIGHT,-10,100", "15.3 not movable: the game's position stays")

    # --- Classic windows: drag, save, re-apply after the game re-anchors ------------------
    lua.execute("R2F.Bags.SetMovable(true)")
    check(lua.eval("R2F.Bags.IsMovable()") is True, "15.3 Movable bags on")
    bag_drag(lua, "ContainerFrame1", "BOTTOMLEFT", 300, 400)
    check(lua.eval("MOVES") == 1, "15.3 unlocked + movable: a drag starts moving the backpack window")
    check(lua.eval("R2FCharDB.bags.bags[0][1]") == "BOTTOMLEFT" and lua.eval("R2FCharDB.bags.bags[0][3]") == 300
          and lua.eval("R2FCharDB.bags.bags[0][4]") == 400, "15.3 position saved under bag id 0 (the backpack)")
    lua.execute("UpdateContainerFrameAnchors()")
    check(bag_point(lua, "ContainerFrame1") == "BOTTOMLEFT,UIParent,BOTTOMLEFT,300,400",
          "15.3 re-applied right after the game re-anchors: %s" % bag_point(lua, "ContainerFrame1"))
    lua.execute("ContainerFrame1:Hide() ContainerFrame1:Show()")
    check(bag_point(lua, "ContainerFrame1") == "BOTTOMLEFT,UIParent,BOTTOMLEFT,300,400", "15.3 re-applied when the window is shown again")
    # Another bag keeps the game's spot until it is dragged; keyed by bag id, not stack order.
    lua.execute("ContainerFrame2:Show() UpdateContainerFrameAnchors()")
    check(bag_point(lua, "ContainerFrame2") == "BOTTOMRIGHT,UIParent,BOTTOMRIGHT,-10,100",
          "15.3 a bag that was never moved keeps the game's position")
    bag_drag(lua, "ContainerFrame2", "TOPLEFT", 50, -60)
    lua.execute("UpdateContainerFrameAnchors()")
    check(bag_point(lua, "ContainerFrame2") == "TOPLEFT,UIParent,TOPLEFT,50,-60" and
          bag_point(lua, "ContainerFrame1") == "BOTTOMLEFT,UIParent,BOTTOMLEFT,300,400", "15.3 each bag has its own saved spot")

    # --- Lock: position kept, dragging refused ----------------------------------------------
    lua.execute("MOVES = 0 R2F.Bags.SetLock(true)")
    bag_drag(lua, "ContainerFrame1", "CENTER", 1, 2)
    check(lua.eval("MOVES") == 0 and lua.eval("R2FCharDB.bags.bags[0][3]") == 300, "15.3 locked: no drag, saved position unchanged")
    lua.execute("UpdateContainerFrameAnchors()")
    check(bag_point(lua, "ContainerFrame1") == "BOTTOMLEFT,UIParent,BOTTOMLEFT,300,400", "15.3 locked bags still sit at the saved spot")
    lua.execute("R2F.Bags.SetLock(false)")
    bag_drag(lua, "ContainerFrame1", "CENTER", 1, 2)
    check(lua.eval("MOVES") == 1, "15.3 unlocking allows dragging again")

    # --- Combat: nothing moves, hooks wait, applied afterwards -------------------------------------
    lua, T = bag_runtime(True, False)
    lua.execute("R2F.Bags.SetMovable(true) ContainerFrame1:Show() UpdateContainerFrameAnchors()")
    bag_drag(lua, "ContainerFrame1", "BOTTOMLEFT", 300, 400)
    lua.execute("MOVES = 0")
    T.combat = True
    bag_drag(lua, "ContainerFrame1", "CENTER", 9, 9)
    check(lua.eval("MOVES") == 0 and lua.eval("R2FCharDB.bags.bags[0][3]") == 300, "15.3 combat: a drag does not start and saves nothing")
    lua.execute("UpdateContainerFrameAnchors()")
    check(bag_point(lua, "ContainerFrame1") == "BOTTOMRIGHT,UIParent,BOTTOMRIGHT,-10,100",
          "15.3 combat: the game's re-anchor is not overridden (no SetPoint from us)")
    lua.execute("ContainerFrame1:Hide() ContainerFrame1:Show()")
    check(bag_point(lua, "ContainerFrame1") == "BOTTOMRIGHT,UIParent,BOTTOMRIGHT,-10,100", "15.3 combat: OnShow does not move the bag either")
    T.errors = lua.table()
    check(lua.eval("R2F.Bags.SetMovable(false)") is False and lua.eval("R2F.Bags.IsMovable()") is True
          and lua.eval("TEST.errors[1]") == lua.eval("R2F.L.QS_COMBAT"), "15.3 combat: the Movable setting cannot be changed")
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")
    check(bag_point(lua, "ContainerFrame1") == "BOTTOMLEFT,UIParent,BOTTOMLEFT,300,400", "15.3 after combat the saved position is applied")

    # --- Turning it off hands the bags back to the game, saved spots are kept --------------------------
    anchors = lua.eval("ANCHOR_CALLS")
    lua.execute("R2F.Bags.SetMovable(false)")
    check(lua.eval("ANCHOR_CALLS") == anchors + 1 and bag_point(lua, "ContainerFrame1") == "BOTTOMRIGHT,UIParent,BOTTOMRIGHT,-10,100",
          "15.3 Movable off: the game re-stacks the bags")
    lua.execute("MOVES = 0")
    bag_drag(lua, "ContainerFrame1", "CENTER", 5, 5)
    lua.execute("UpdateContainerFrameAnchors()")
    check(lua.eval("MOVES") == 0 and bag_point(lua, "ContainerFrame1") == "BOTTOMRIGHT,UIParent,BOTTOMRIGHT,-10,100"
          and lua.eval("R2FCharDB.bags.bags[0][3]") == 300, "15.3 Movable off: hooks are inert, saved spot kept")
    lua.execute("R2F.Bags.SetMovable(true) UpdateContainerFrameAnchors()")
    check(bag_point(lua, "ContainerFrame1") == "BOTTOMLEFT,UIParent,BOTTOMLEFT,300,400", "15.3 switching it on again restores the saved spot")

    # --- Relog: saved position comes back from R2FCharDB ----------------------------------------------------
    saved = "{ bags = { movable = true, lock = false, bags = { [0] = { 'TOPRIGHT', 'TOPRIGHT', -40, -80 } } } }"
    lua, T = bag_runtime(True, False, saved)
    lua.execute("ContainerFrame1:Show()")
    check(bag_point(lua, "ContainerFrame1") == "TOPRIGHT,UIParent,TOPRIGHT,-40,-80", "15.3 relog: saved position applied when the bag opens")
    check(lua.eval("R2FCharDB.bags.movable") is True, "15.3 relog: setting persisted")

    # --- Combined bag ---------------------------------------------------------------------------------------------
    lua, T = bag_runtime(False, True)
    lua.execute("R2F.Bags.SetMovable(true) ContainerFrameCombinedBags:Show() UpdateContainerFrameAnchors()")
    bag_drag(lua, "ContainerFrameCombinedBags", "CENTER", 12, 34)
    check(lua.eval("MOVES") == 1 and lua.eval("R2FCharDB.bags.combined[3]") == 12 and lua.eval("R2FCharDB.bags.combined[4]") == 34,
          "15.3 combined bag: dragged and saved under 'combined'")
    lua.execute("UpdateContainerFrameAnchors()")
    check(bag_point(lua, "ContainerFrameCombinedBags") == "CENTER,UIParent,CENTER,12,34", "15.3 combined bag: re-applied after the game re-anchors")
    T.combat = True
    lua.execute("UpdateContainerFrameAnchors()")
    check(bag_point(lua, "ContainerFrameCombinedBags") == "BOTTOMRIGHT,UIParent,BOTTOMRIGHT,-10,100", "15.3 combined bag: combat blocks it too")
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")
    check(bag_point(lua, "ContainerFrameCombinedBags") == "CENTER,UIParent,CENTER,12,34", "15.3 combined bag: applied after combat")

    # --- Both styles at once ------------------------------------------------------------------------------------
    lua, T = bag_runtime(True, True)
    lua.execute("R2F.Bags.SetMovable(true) ContainerFrame1:Show() ContainerFrameCombinedBags:Show()")
    bag_drag(lua, "ContainerFrame1", "LEFT", 1, 2)
    bag_drag(lua, "ContainerFrameCombinedBags", "RIGHT", 3, 4)
    lua.execute("UpdateContainerFrameAnchors()")
    check(bag_point(lua, "ContainerFrame1") == "LEFT,UIParent,LEFT,1,2" and bag_point(lua, "ContainerFrameCombinedBags") == "RIGHT,UIParent,RIGHT,3,4",
          "15.3 both styles present: each keeps its own spot")

    # --- A bag anchored to another frame is saved as an absolute spot --------------------------------------------
    lua, T = bag_runtime(True, False)
    lua.execute("R2F.Bags.SetMovable(true) ContainerFrame1:Show()")
    lua.execute("ContainerFrame1.GetPoint = function() return 'TOPRIGHT', ContainerFrame2, 'TOPLEFT', 0, 0 end"
                " ContainerFrame1.GetLeft = function() return 111 end ContainerFrame1.GetBottom = function() return 222 end"
                " ContainerFrame1:Fire('OnDragStart') ContainerFrame1:Fire('OnDragStop')")
    check(lua.eval("R2FCharDB.bags.bags[0][1]") == "BOTTOMLEFT" and lua.eval("R2FCharDB.bags.bags[0][3]") == 111
          and lua.eval("R2FCharDB.bags.bags[0][4]") == 222, "15.3 relative anchor -> saved as absolute BOTTOMLEFT")

    # --- Settings tab boxes ----------------------------------------------------------------------------------------
    lua, T = bag_runtime(True, False)
    lua.execute("R2F.MainWindow.Show('settings')")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.BAGS_MOVABLE", "BM")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.BAGS_LOCK", "BL")
    check(lua.eval("#BM") == 1 and lua.eval("#BL") == 1 and lua.eval("BM[1]:IsVisible()") is True,
          "15.3 Settings tab has Movable bags + Lock bags")
    lua.execute("BM[1]:Click()")
    check(lua.eval("R2FCharDB.bags.movable") is True and lua.eval("BM[1]:GetChecked()") is True, "15.3 clicking Movable bags turns it on")
    lua.execute("BL[1]:Click()")
    check(lua.eval("R2FCharDB.bags.lock") is True and lua.eval("BL[1]:GetChecked()") is True, "15.3 clicking Lock bags locks")
    T.combat = True
    T.fire("PLAYER_REGEN_DISABLED")
    check(lua.eval("BM[1]:IsEnabled()") is False and lua.eval("BL[1]:IsEnabled()") is False, "15.3 the two boxes grey out in combat")
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")
    check(lua.eval("BM[1]:IsEnabled()") is True, "15.3 and come back after combat")
    lua, T = bag_runtime(False, False)
    lua.execute("R2F.MainWindow.Show('settings')")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.BAGS_MOVABLE", "BM")
    check(lua.eval("BM[1]:IsEnabled()") is False, "15.3 no bag windows found: the boxes are greyed out")


def reminder_runtime(token, preset=None):
    """Fresh runtime logged in as class `token` (WARRIOR / HUNTER / PRIEST), optional R2FDB preset."""
    lua = new_runtime()
    lua.execute("TEST.reset()")
    lua.execute("TEST.classToken = %r" % token)
    if preset:
        lua.execute("R2FDB = %s" % preset)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    return lua, T


def border_of(lua, frame):
    return lua.eval("(function() local c = %s.border.__ctex return c and table.concat({ c[1], c[2], c[3] }, ',') end)()" % frame)


def test_reminders():
    """ADDON_PLAN 15.4: Reminders tab, stance moved out of Settings, Hunter ammo low."""
    RED = "0.9,0.1,0.1"
    # --- Tabs and class filter ------------------------------------------------------
    lua, T = reminder_runtime("WARRIOR")
    MW = lua.eval("R2F.MainWindow")
    keys = [lua.eval("R2F.MainWindow.TABS[%d]" % i) for i in range(1, 6)]
    check(keys == ["home", "macros", "talents", "reminders", "settings"], "15.4 tab order: %s" % keys)
    lua.execute('SlashCmdList.R2F("reminders")')
    check(MW.CurrentTab() == "reminders", "15.4 /r2f reminders opens the Reminders tab")
    title = lua.eval("R2FMain.__title")
    check(title == "Road to Forever: Reminders", "15.4 Reminders title: %r" % title)
    check(lua.eval("R2FStanceFrame ~= nil") and lua.eval("R2FAmmoFrame == nil") and lua.eval("R2FAmmoScale == nil"),
          "15.4 Warrior: stance frame only, no ammo frame or ammo controls")
    check(lua.eval("R2FStanceScale ~= nil and R2FStanceScale:IsVisible()") is True, "15.4 stance size slider is on the Reminders tab")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.SETTINGS_STANCE_SHOW", "SS")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.SETTINGS_STANCE_LOCK", "SL")
    check(lua.eval("#SS") == 1 and lua.eval("#SL") == 1 and lua.eval("SS[1]:IsVisible()") is True, "15.4 stance Show / Lock boxes on the Reminders tab")
    lua.execute("SL[1]:Click()")
    check(lua.eval("R2FDB.stance.lock") is True and lua.eval("SL[1]:GetChecked()") is True, "15.4 stance Lock works from the new tab")
    lua.execute("SL[1]:Click() SS[1]:Click()")
    check(lua.eval("R2FDB.stance.shown") is False, "15.4 stance Show works from the new tab")
    lua.execute("SS[1]:Click() R2FStanceScale:Fire('OnValueChanged', 150)")
    check(lua.eval("R2FDB.stance.scale") == 1.5, "15.4 stance size slider works from the new tab")
    lua.execute("R2F.MainWindow.SelectTab('settings')")
    check(lua.eval("SS[1]:IsVisible()") is False and lua.eval("R2FStanceScale:IsVisible()") is False,
          "15.4 the stance options are no longer on the Settings tab")
    # Controls only write SavedVariables: still usable in combat.
    lua.execute("R2F.MainWindow.SelectTab('reminders')")
    T.combat = True
    T.fire("PLAYER_REGEN_DISABLED")
    check(lua.eval("SS[1]:IsEnabled()") is True and lua.eval("SL[1]:IsEnabled()") is True, "15.4 Reminders controls stay enabled in combat")
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")

    lua, T = reminder_runtime("HUNTER")
    check(lua.eval("R2FAmmoFrame ~= nil") and lua.eval("R2FStanceFrame == nil") and lua.eval("R2FStanceScale == nil"),
          "15.4 Hunter: ammo frame only")
    lua.execute("R2F.MainWindow.Show('reminders')")
    check(lua.eval("R2FAmmoScale:IsVisible() and R2FAmmoThreshold:IsVisible()") is True, "15.4 Hunter sees the ammo size + threshold sliders")
    lua, T = reminder_runtime("PRIEST")
    check(lua.eval("R2FAmmoFrame == nil and R2FStanceFrame == nil and R2FAmmoScale == nil and R2FStanceScale == nil"),
          "15.4 Priest: no reminder frames or controls")
    lua.execute("R2F.MainWindow.Show('reminders')")
    check(font_text(lua, "^No reminders for your class") is not None, "15.4 a class without reminders sees the 'none yet' line")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("ammo")')
    check(any("Hunters only" in c for c in lua_table_to_list(lua.eval("TEST.chat"))), "15.4 /r2f ammo on a Priest explains")

    # --- Ammo counting ----------------------------------------------------------------
    lua, T = reminder_runtime("HUNTER")
    check(lua.eval("(R2F.Ammo.Count())") == 0, "15.4 no ammo equipped counts as 0")
    lua.execute("TEST.ammoItem = 11285 TEST.ammoCount = 1500")
    check(lua.eval("(R2F.Ammo.Count())") == 1500, "15.4 equipped ammo: the slot's total count")
    lua.execute("TEST.ammoCount = 37")
    check(lua.eval("(R2F.Ammo.Count())") == 37, "15.4 count follows the item")
    lua.execute("local old = GetInventoryItemCount GetInventoryItemCount = function() error('boom') end "
                "COUNT_ERR = R2F.Ammo.Count() GetInventoryItemCount = old")
    check(lua.eval("COUNT_ERR") == 0, "15.4 a failing count API is caught (0, no error)")

    # --- Threshold, hide when fine, colours ---------------------------------------------------
    lua, T = reminder_runtime("HUNTER")
    check(lua.eval("R2FDB.ammo.threshold") == 200 and lua.eval("R2FDB.ammo.shown") is True, "15.4 ammo defaults: on, threshold 200")
    lua.execute("TEST.ammoItem = 11285 TEST.ammoCount = 1500 R2F.Ammo.SetLock(true)")
    check(lua.eval("R2FAmmoFrame:IsShown()") is False, "15.4 locked and ammo fine: hidden")
    lua.execute("TEST.ammoCount = 200 R2F.Ammo.Update()")
    check(lua.eval("R2FAmmoFrame:IsShown()") is False, "15.4 exactly at the threshold is still fine")
    lua.execute("TEST.ammoCount = 199 R2F.Ammo.Update()")
    check(lua.eval("R2FAmmoFrame:IsShown()") is True and border_of(lua, "R2FAmmoFrame") == RED, "15.4 under the threshold: shown with a red border")
    check(lua.eval("R2FAmmoFrame.count.__text") == "199", "15.4 the icon shows the count: %r" % lua.eval("R2FAmmoFrame.count.__text"))
    check(lua.eval("R2FAmmoFrame.count.__color[1]") == 1 and lua.eval("R2FAmmoFrame.count.__color[2]") < 0.5, "15.4 the count text turns red")
    check(lua.eval("R2FAmmoFrame.icon.__tex") == "Interface\\Icons\\INV_Ammo_Arrow_03", "15.4 icon is the equipped ammo's")
    lua.execute("TEST.ammoItem = nil TEST.ammoCount = nil R2F.Ammo.Update()")
    check(lua.eval("R2FAmmoFrame:IsShown()") is True and lua.eval("R2FAmmoFrame.count.__text") == "0"
          and lua.eval("R2FAmmoFrame.icon.__tex") == "Interface\\Icons\\INV_Ammo_Arrow_02", "15.4 no ammo at all: red 0 with the fallback icon")
    lua.execute("TEST.ammoItem = 11285 TEST.ammoCount = 1500 R2F.Ammo.SetLock(false)")
    check(lua.eval("R2FAmmoFrame:IsShown()") is True and border_of(lua, "R2FAmmoFrame") != RED,
          "15.4 unlocked and ammo fine: shown (grey) so it can be moved")
    lua.execute("R2F.Ammo.SetLock(true) R2F.Ammo.SetShown(false) TEST.ammoCount = 5 R2F.Ammo.Update()")
    check(lua.eval("R2FAmmoFrame:IsShown()") is False, "15.4 switched off: hidden even when ammo is low")
    lua.execute("R2F.Ammo.SetShown(true)")
    check(lua.eval("R2FAmmoFrame:IsShown()") is True, "15.4 switched on again: low ammo shows")
    # Threshold setting: steps of 50, clamped, and it changes what is low.
    lua.execute("TEST.ammoCount = 400 R2F.Ammo.Update()")
    check(lua.eval("R2FAmmoFrame:IsShown()") is False, "15.4 400 ammo with threshold 200: fine")
    lua.execute("R2F.Ammo.SetThreshold(500)")
    check(lua.eval("R2FDB.ammo.threshold") == 500 and lua.eval("R2FAmmoFrame:IsShown()") is True, "15.4 threshold 500: 400 ammo is low now")
    lua.execute("R2F.Ammo.SetThreshold(275)")
    check(lua.eval("R2FDB.ammo.threshold") == 300, "15.4 threshold rounds to the step (275 -> 300)")
    lua.execute("R2F.Ammo.SetThreshold(5)")
    check(lua.eval("R2FDB.ammo.threshold") == 50, "15.4 threshold minimum 50")
    lua.execute("R2F.Ammo.SetThreshold(99999)")
    check(lua.eval("R2FDB.ammo.threshold") == 1000, "15.4 threshold maximum 1000")
    lua.execute("R2F.MainWindow.Show('reminders') R2FAmmoThreshold:Fire('OnValueChanged', 650)")
    check(lua.eval("R2FDB.ammo.threshold") == 650, "15.4 the threshold slider sets it")
    check(font_text(lua, "^Turn red when under: 650$") is not None, "15.4 the slider label shows the value")

    # --- Events and combat -------------------------------------------------------------------------
    lua, T = reminder_runtime("HUNTER")
    lua.execute("TEST.ammoItem = 11285 TEST.ammoCount = 1500 R2F.Ammo.SetLock(true)")
    for event in ("BAG_UPDATE", "UNIT_INVENTORY_CHANGED", "PLAYER_EQUIPMENT_CHANGED"):
        lua.execute("TEST.ammoCount = 1500 R2F.Ammo.Update()")
        lua.execute("TEST.ammoCount = 10")
        T.fire(event, "player")
        check(lua.eval("R2FAmmoFrame:IsShown()") is True, "15.4 %s updates the icon" % event)
    T.combat = True
    T.errors = lua.table()
    lua.execute("TEST.ammoCount = 1500")
    T.fire("BAG_UPDATE")
    check(lua.eval("R2FAmmoFrame:IsShown()") is False and lua_table_to_list(lua.eval("TEST.errors")) == [],
          "15.4 works in combat: updates with no errors")
    lua.execute("TEST.ammoCount = 20")
    T.fire("BAG_UPDATE")
    check(lua.eval("R2FAmmoFrame:IsShown()") is True, "15.4 shows in combat when ammo runs low")
    T.combat = False

    # --- Slash commands -----------------------------------------------------------------------------
    lua, T = reminder_runtime("HUNTER")
    lua.execute('SlashCmdList.R2F("ammo lock")')
    check(lua.eval("R2FDB.ammo.lock") is True, "15.4 /r2f ammo lock locks")
    lua.execute('SlashCmdList.R2F("ammo")')
    check(lua.eval("R2FDB.ammo.shown") is False, "15.4 /r2f ammo hides")
    lua.execute('SlashCmdList.R2F("ammo")')
    check(lua.eval("R2FDB.ammo.shown") is True, "15.4 /r2f ammo shows again")

    # --- Saved positions and size ---------------------------------------------------------------------------
    lua, T = reminder_runtime("HUNTER")
    lua.execute("R2FAmmoFrame.__cx, R2FAmmoFrame.__cy = 111, -222 R2FAmmoFrame:Fire('OnDragStart') R2FAmmoFrame:Fire('OnDragStop')")
    check(lua.eval("R2FDB.ammo.x") == 111 and lua.eval("R2FDB.ammo.y") == -222, "15.4 dropping the ammo icon saves its position")
    lua.execute("MV = nil R2FAmmoFrame.StartMoving = function() MV = true end R2F.Ammo.SetLock(true) R2FAmmoFrame:Fire('OnDragStart')")
    check(lua.eval("MV") is None, "15.4 locked: a drag does not start")
    lua.execute("R2F.Ammo.SetLock(false) R2FAmmoFrame:Fire('OnDragStart')")
    check(lua.eval("MV") is True, "15.4 unlocked: a drag starts")
    lua.execute("R2FDB.ammo.x, R2FDB.ammo.y = 111, -222 R2F.Ammo.SetScale(2)")
    check(lua.eval("R2FDB.ammo.scale") == 2 and lua.eval("R2FAmmoFrame.__scale") == 2, "15.4 size applies to the frame")
    lua.execute("R2F.Ammo.SetScale(99)")
    check(lua.eval("R2FDB.ammo.scale") == 3, "15.4 size clamped to 300%")
    lua.execute("R2F.Ammo.SetScale(0.01)")
    check(lua.eval("R2FDB.ammo.scale") == 0.5, "15.4 size clamped to 50%")
    # Independent from the stance icon: a Warrior's position is untouched by this.
    lua, T = reminder_runtime("WARRIOR")
    lua.execute("R2FStanceFrame.__cx, R2FStanceFrame.__cy = 33, 44 R2FStanceFrame:Fire('OnDragStart') R2FStanceFrame:Fire('OnDragStop')")
    check(lua.eval("R2FDB.stance.x") == 33 and lua.eval("R2FDB.stance.y") == 44 and lua.eval("R2FDB.ammo.x") == 0,
          "15.4 each reminder keeps its own position")
    # Relog: saved settings come back.
    preset = "{ ammo = { shown = true, lock = true, scale = 1.5, x = 70, y = -80, threshold = 350 } }"
    lua, T = reminder_runtime("HUNTER", preset)
    check(lua.eval("R2FDB.ammo.threshold") == 350 and lua.eval("R2FDB.ammo.scale") == 1.5 and lua.eval("R2FDB.ammo.x") == 70,
          "15.4 relog: ammo settings persisted")
    pt = lua.eval("R2FAmmoFrame.__point")
    check(pt[1] == "CENTER" and pt[4] == 70 / 1.5 and pt[5] == -80 / 1.5, "15.4 relog: the icon is placed at the saved spot (%s, %s)" % (pt[4], pt[5]))
    # Bad saved values are repaired, not trusted.
    lua, T = reminder_runtime("HUNTER", "{ ammo = { threshold = 5, scale = 9, shown = 'yes' } }")
    check(lua.eval("R2FDB.ammo.threshold") == 200 and lua.eval("R2FDB.ammo.scale") == 1 and lua.eval("R2FDB.ammo.shown") is True,
          "15.4 invalid saved ammo values fall back to the defaults")


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
        if f.__kind == 'Button' and f.__scripts.OnDragStart and f ~= R2FMinimapButton then table.insert(SLOTS, f) end
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
    # Step 6: /r2f opens the main window on its last tab (Home the first
    # time); /r2f macros shows the Macro Book inside it.
    lua.execute('SlashCmdList.R2F("")')
    check(lua.eval("R2F.MainWindow.IsShown()") is True and lua.eval("R2F.MainWindow.CurrentTab()") == "home",
          "/r2f opens the main window on Home the first time")
    check(lua.eval("R2F.MacroBook.IsShown()") is False, "the book is not visible while Home is showing")
    lua.execute('SlashCmdList.R2F("macros")')
    check(lua.eval("R2F.MacroBook.IsShown()") is True, "/r2f macros shows the Macro Book")
    tag = "templates" if templates else "fallbacks"
    check(lua.eval("R2FMain ~= nil") if templates else lua.eval("R2FMainPlain ~= nil"),
          "%s: main window created via %s" % (tag, "PortraitFrameTemplate" if templates else "fallback"))

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
        if f.__kind == 'Button' and f.__scripts.OnDragStart and f ~= R2FMinimapButton then table.insert(SLOTS, f) end
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
    # v0.10.0: Remove from library asks first (ADDON_PLAN 5.10).
    check(lua.eval("R2F.Library.Count()") == before and lua.eval("R2FConfirm:IsShown()") is True,
          "right-click > Remove from library opens a confirm popup first")
    lua.execute("R2FConfirm.yes:Click()")
    check(lua.eval("R2F.Library.Count()") == before - 1, "right-click > Remove from library (confirmed)")

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
    check("R2FImport" in special and any(s.startswith("R2FMain") for s in special), "windows close with Esc: %s" % special)
    new_globals = lua.eval("""(function()
      local out = {}
      for k in pairs(_G) do if not BEFORE[k] then table.insert(out, k) end end
      table.sort(out) return table.concat(out, ",") end)()""").split(",")
    allowed_exact = {"R2F", "R2FDB", "R2FCharDB", "SLASH_R2F1", "SLASH_R2FT1"} | BINDING_GLOBALS
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
    ids = ["WARRIOR/Ham", "WARRIOR/OP", "WARRIOR/Mock", "WARRIOR/Slam", "WARRIOR/Disarm", "WARRIOR/Exe"]
    for i in ids:
        M.Ensure(i)
    # VR on slot 1, Rend on the last standard slot (120), Sunder on a
    # stance/bonus-bar slot (73); HS edited by the player; Slam + Exe unused.
    lua.execute('TEST.actions[1] = "Ham" TEST.actions[120] = "Mock" TEST.actions[73] = "Disarm" TEST.setBody("OP", "/say mine")')
    T.addMacro("Mine", "/dance", True)
    T.actions[2] = "Mine"
    cands = M.TidyCandidates()
    check(names_of(cands) == ["Exe", "Slam"],
          "tidy: only unedited AND unused macros of ours (slots 1, 73, 120 seen as in use): %s" % names_of(cands))
    # Run-time re-check: the player puts Slam on a bar after the popup was built.
    T.actions[40] = "Slam"
    check(M.Tidy(cands) == 1 and T.bodyOf("Slam") is not None and T.bodyOf("Exe") is None,
          "tidy re-checks the bars when it runs: Slam (now on a bar) kept, Exe deleted")
    check(T.bodyOf("OP") == "/say mine" and T.bodyOf("Mine") == "/dance" and T.bodyOf("Ham") and T.bodyOf("Mock"),
          "tidy leaves edited, in-use and the player's own macros alone")
    T.actions[40] = None

    # Tidy up confirmed in combat -> queued (6.7 pattern), runs after combat.
    lua.execute('TEST.actions[73] = nil')  # Sunder now unused
    T.combat = True
    T.calls = lua.table()
    lua.execute("R2F.Macros.RunOrQueue(function() TIDIED = R2F.Macros.Tidy(R2F.Macros.TidyCandidates()) end)")
    check(M.QueueSize() == 1 and len(T.calls) == 0 and T.bodyOf("Disarm") is not None,
          "tidy accepted in combat is queued, nothing deleted in combat")
    T.combat = False
    M.RunQueue()
    check(lua.eval("TIDIED") == 2 and T.bodyOf("Disarm") is None and T.bodyOf("Slam") is None
          and T.bodyOf("Ham") and T.bodyOf("Mock") and M.QueueSize() == 0,
          "queued tidy runs after combat and deletes the now-unused macros (Sunder, Slam) only")
    T.errors = lua.table()
    T.combat = True
    check(M.Tidy(lua.eval('{ { id = "WARRIOR/Mock", name = "Mock" } }')) == 0 and T.bodyOf("Mock") is not None
          and lua.eval("TEST.errors[1]") == lua.eval("R2F.L.ERR_COMBAT"), "Tidy called directly in combat refuses (no write)")
    T.combat = False

    # --- slotsFirst decides CreateMacro's perCharacter ----------------------
    lua.execute("TEST.reset() R2FCharDB.created = {} R2FDB.createdAccount = {} R2FDB.settings.slotsFirst = 'account'")
    M.Ensure("WARRIOR/Ham")
    check(lua.eval("#TEST.macros.acc") == 1 and lua.eval("#TEST.macros.char") == 0
          and lua.eval('R2FDB.createdAccount["WARRIOR/Ham"] ~= nil'), "slotsFirst=account: CreateMacro goes to account slots")
    lua.execute("R2FDB.settings.slotsFirst = 'character'")
    M.Ensure("WARRIOR/OP")
    check(lua.eval("#TEST.macros.char") == 1 and lua.eval('R2FCharDB.created["WARRIOR/OP"] ~= nil'),
          "slotsFirst=character: the next CreateMacro goes to character slots")
    check(lua.eval('GetMacroIndexByName("Ham") <= 120'), "changing the setting does not move an existing macro")
    lua.execute("for i = 1, 120 do TEST.addMacro('a' .. i, 'x', false) end R2FDB.settings.slotsFirst = 'account'")
    M.Ensure("WARRIOR/Mock")
    check(lua.eval('GetMacroIndexByName("Mock") > 120'), "slotsFirst=account falls back to character slots when account is full")

    # --- Remove all ------------------------------------------------------------
    lua.execute("TEST.reset() R2FCharDB.created = {} R2FDB.createdAccount = {} R2FDB.settings.slotsFirst = 'character'")
    for i in ("WARRIOR/Ham", "WARRIOR/OP", "WARRIOR/Mock"):
        M.Ensure(i)                      # character slots
    lua.execute("R2FDB.settings.slotsFirst = 'account'")
    for i in ("WARRIOR/Slam", "WARRIOR/Exe"):
        M.Ensure(i)                      # account slots
    lua.execute("R2FDB.settings.slotsFirst = 'character'")
    lua.execute('TEST.actions[1] = "Ham" TEST.actions[2] = "Exe" TEST.setBody("OP", "/say my HS")')
    T.addMacro("Mine", "/dance", False)
    lua.execute('R2FCharDB.created["WARRIOR/Gone"] = { name = "Gone", hash = "0" }')  # macro deleted by hand
    lua.execute('R2F.Library.SetChanged("WARRIOR/Ham", "updated")')
    check(lua.eval("#TEST.macros.char") == 3 and lua.eval("#TEST.macros.acc") == 3, "setup: 3 character + 2 account + 1 own macro")
    plan = M.RemoveAllPlan()
    check(names_of(plan.delete) == ["Exe", "Ham", "Mock", "Slam"] and names_of(plan.keep) == ["OP"],
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
    check(lua.eval('R2FCharDB.created["WARRIOR/Ham"] ~= nil and R2FDB.createdAccount["WARRIOR/Slam"] ~= nil'),
          "RemoveAll in combat keeps the tracking")
    lua.execute("R2F.Macros.RunOrQueue(function() RA_DEL, RA_KEPT = R2F.Macros.RemoveAll() end)")
    check(M.QueueSize() == 1 and len(T.calls) == 0, "remove all accepted in combat is queued")
    T.combat = False
    M.RunQueue()
    check((lua.eval("RA_DEL"), lua.eval("RA_KEPT")) == (4, 1), "queued remove all ran after combat: 4 deleted, 1 kept")
    check(all(T.bodyOf(n) is None for n in ("Ham", "Mock", "Slam", "Exe")),
          "remove all deleted the unedited macros, including ones on bars and in account slots")
    check(T.bodyOf("OP") == "/say my HS" and T.bodyOf("Mine") == "/dance", "remove all kept the edited macro and the player's own")
    check(lua.eval("next(R2FCharDB.created) == nil and next(R2FDB.createdAccount) == nil"),
          "remove all cleared character AND account tracking (incl. the edited and stale records)")
    check(lua.eval("next(R2FCharDB.changed) == nil"), "remove all cleared the Changed flags")
    check(lua.eval("R2F.Library.Count()") == lib_count and lua.eval('R2F.Library.db.library["WARRIOR/Ham"] ~= nil'),
          "remove all leaves R2FDB.library untouched")
    check(M.Ensure("WARRIOR/Ham") is True and T.cursor == "Ham", "after remove all the macro can be dragged out again")
    # HS is no longer ours: dragging it from the book asks first (it's the player's macro now).
    n_confirms = lua.eval("#CONFIRMS")
    check(M.Ensure("WARRIOR/OP") is False and lua.eval("#CONFIRMS") == n_confirms + 1,
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

    # Key bindings (repointed in step 6, ADDON_PLAN 6.9 / 6.10): Toggle = main
    # window on its last tab, Open Macros / Open Talents = that tab (toggling).
    lua.execute("R2F.Bindings.Toggle()")
    check(lua.eval("R2F.MainWindow.IsShown()") is True and lua.eval("R2F.MainWindow.CurrentTab()") == "home",
          "%s: binding Toggle opens the main window on its last tab (Home at first)" % tag)
    lua.execute("R2F.Bindings.Toggle()")
    check(lua.eval("R2F.MainWindow.IsShown()") is False, "binding Toggle closes it again")
    lua.execute("R2F.Bindings.OpenMacros()")
    check(lua.eval("R2F.MacroBook.IsShown()") is True, "binding Open Macros opens the Macro Book tab")
    lua.execute("R2F.Bindings.OpenTalents()")
    check(lua.eval("R2F.MainWindow.CurrentTab()") == "talents" and lua.eval("R2F.MacroBook.IsShown()") is False,
          "binding Open Talents switches to the Talents tab")
    lua.execute("R2F.Bindings.OpenTalents()")
    check(lua.eval("R2F.MainWindow.IsShown()") is False, "binding Open Talents on the Talents tab closes the window")
    lua.execute("R2F.Bindings.OpenMacros()")
    for g in BINDING_GLOBALS:
        check(isinstance(lua.eval(g), str) and lua.eval(g) != "", "binding label global %s is set" % g)

    # 15.2: the Macro Book has no Settings button any more; Settings is the 4th tab.
    lua.execute("""
      SETBTN = nil
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'Button' and f.__text == R2F.L.BTN_SETTINGS and not f.r2fKey then SETBTN = f end
      end""")
    check(lua.eval("SETBTN == nil"), "%s: no Settings button in the Macro Book (15.2)" % tag)
    lua.execute("R2F.Settings.Show()")
    check(lua.eval("R2F.MainWindow.CurrentTab()") == "settings" and lua.eval("R2F.Settings.IsShown()") is True
          and lua.eval("R2FSettings == nil"), "%s: Settings opens as a tab of the main window" % tag)
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
    lua.execute('R2F.Macros.Ensure("WARRIOR/Ham")')
    check(lua.eval("#TEST.macros.acc") == 1 and lua.eval("#TEST.macros.char") == 0,
          "%s: after choosing Account first in Settings, a dragged macro is created in an account slot" % tag)
    lua.execute(rb("SETTINGS_SLOTS_CHAR") + ":Click()")
    lua.execute('R2F.Macros.Ensure("WARRIOR/OP")')
    check(lua.eval("#TEST.macros.char") == 1 and lua.eval('GetMacroIndexByName("Ham") <= 120'),
          "back to Character first: next macro in a character slot, VR stays in its account slot")

    # Minimap checkboxes: stored in R2FDB.minimap (step 6 reads them).
    check(lua.eval(rb("SETTINGS_MINIMAP_SHOW") + ":GetChecked()") is True and lua.eval(rb("SETTINGS_MINIMAP_LOCK") + ":GetChecked()") is False,
          "Settings: minimap shown + unlocked by default")
    lua.execute("REAL_MM = R2F.Minimap APPLIED = 0 R2F.Minimap = { Apply = function() APPLIED = APPLIED + 1 end }")
    lua.execute(rb("SETTINGS_MINIMAP_SHOW") + ":Click() " + rb("SETTINGS_MINIMAP_LOCK") + ":Click()")
    check(lua.eval("R2FDB.minimap.hide") is True and lua.eval("R2FDB.minimap.lock") is True
          and lua.eval(rb("SETTINGS_MINIMAP_SHOW") + ":GetChecked()") is False and lua.eval(rb("SETTINGS_MINIMAP_LOCK") + ":GetChecked()") is True,
          "Settings: minimap checkboxes write R2FDB.minimap.hide / .lock")
    check(lua.eval("APPLIED") == 2, "Settings calls the step-6 hook R2F.Minimap.Apply after each minimap change")
    lua.execute(rb("SETTINGS_MINIMAP_SHOW") + ":Click() R2F.Minimap = REAL_MM")
    check(lua.eval("R2FDB.minimap.hide") is False, "Show minimap button toggles back")

    # Combat: Remove all greyed out, Settings button still usable.
    T.fire("PLAYER_REGEN_DISABLED")
    T.combat = True
    check(lua.eval("REMOVEALL.__enabled") is False, "combat greys out Remove all")
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")
    check(lua.eval("REMOVEALL.__enabled") is True, "combat end re-enables Remove all")

    # Remove all through the real confirm dialog; accepted in combat -> queued.
    lua.execute('TEST.actions[1] = "Ham"')
    lua.execute("REMOVEALL:Click()")
    check(lua.eval("R2FConfirm:IsShown()") is True, "Remove all asks first")
    text = lua.eval("R2FConfirm.text.__text")
    check(text.startswith("Delete 2 Road to Forever macros") and "Ham, OP" in text and "library stays" in text,
          "Remove all popup lists the macros and says the library stays: %r" % text)
    T.combat = True
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'Button' and f.__parent == R2FConfirm and f.__text == R2F.L.BTN_REMOVE then f:Click() end
      end""")
    check(T.bodyOf("Ham") is not None and lua.eval("R2F.Macros.QueueSize()") == 1, "%s: Remove all accepted in combat waits" % tag)
    T.combat = False
    T.chat = lua.table()
    T.fire("PLAYER_REGEN_ENABLED")
    check(T.bodyOf("Ham") is None and T.bodyOf("OP") is None, "%s: Remove all ran after combat" % tag)
    check(any("removed 2 Road to Forever macros." in c for c in chat_lines(lua)), "Remove all chat line")
    check(lua.eval("R2F.Library.Count()") == lib_count, "Remove all kept the library")
    T.chat = lua.table()
    lua.execute("REMOVEALL:Click()")
    check(any(lua.eval("R2F.L.REMOVE_ALL_NONE") in c for c in chat_lines(lua)), "Remove all with nothing to remove just says so")

    # Esc closes the panel; one-global audit with Settings built.
    check("R2FMain" in lua_table_to_list(lua.eval("UISpecialFrames")) or "R2FMainPlain" in lua_table_to_list(lua.eval("UISpecialFrames")),
          "Settings tab closes with Esc (it is part of the main window)")
    new_globals = lua.eval("""(function()
      local out = {}
      for k in pairs(_G) do if not BEFORE[k] then table.insert(out, k) end end
      table.sort(out) return table.concat(out, ",") end)()""").split(",")
    test_vars = {"SETBTN", "CHECKS", "REMOVEALL", "L", "APPLIED", "NS", "REAL_MM"}
    bad = [g for g in new_globals if g and g not in test_vars and g not in BINDING_GLOBALS
           and g not in ("SLASH_R2F1", "SLASH_R2FT1") and not g.startswith("R2F")]
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


def find_frames(lua, cond, var):
    """Collect TEST.allFrames entries matching a Lua condition on `f` into global `var`."""
    lua.execute("%s = {} for _, f in ipairs(TEST.allFrames) do if %s then table.insert(%s, f) end end" % (var, cond, var))
    return lua.eval("#" + var)


def test_step6_ui(templates, fx):
    """Step 6: main window + tabs, Home counts, reparented Macro Book, minimap button + menu, slash commands."""
    lua = new_runtime(templates)
    tag = "templates" if templates else "fallbacks"
    T = lua.eval("TEST")
    L = lua.eval("R2F.L")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    MW = lua.eval("R2F.MainWindow")
    win = "R2FMain" if templates else "R2FMainPlain"

    # ---- Minimap button: own backend, R2F.Minimap.Apply -------------------
    check(lua.eval("R2F.Minimap.backend") == "own", "%s: no LibDBIcon loaded -> own minimap button" % tag)
    check(lua.eval("R2FMinimapButton ~= nil and R2FMinimapButton.__parent == Minimap"), "minimap button is a child of Minimap")
    check(lua.eval("R2FMinimapButton.icon.__tex") == "Interface\\AddOns\\RoadToForever\\media\\logo64",
          "minimap icon = media/logo64")
    pt = lua_table_to_list(lua.eval("R2FMinimapButton.__point"))
    import math
    want = (75 * math.cos(math.radians(220)), 75 * math.sin(math.radians(220)))
    check(pt[0] == "CENTER" and abs(pt[3] - want[0]) < 1e-6 and abs(pt[4] - want[1]) < 1e-6,
          "default minimapPos 220 puts the button on the rim (round minimap): %s" % pt)
    lua.execute("R2FDB.minimap.hide = true R2F.Minimap.Apply()")
    check(lua.eval("R2FMinimapButton:IsShown()") is False, "Apply: hide = true hides the button")
    lua.execute("R2FDB.minimap.hide = false R2F.Minimap.Apply()")
    check(lua.eval("R2FMinimapButton:IsShown()") is True, "Apply: hide = false shows it again")
    lua.execute("R2FDB.minimap.minimapPos = 90 R2F.Minimap.Apply()")
    pt = lua_table_to_list(lua.eval("R2FMinimapButton.__point"))
    check(abs(pt[3]) < 1e-6 and abs(pt[4] - 75) < 1e-6, "Apply: minimapPos 90 = top of the minimap")
    lua.execute("function GetMinimapShape() return 'SQUARE' end")
    x, y = lua.eval("R2F.Minimap.Offset")(45)
    check(abs(x - 75) < 1e-6 and abs(y - 75) < 1e-6, "square minimap: 45 degrees = the corner (%s, %s)" % (x, y))
    x, y = lua.eval("R2F.Minimap.Offset")(30)
    check(abs(x - 75) < 1e-6 and 0 < y < 75, "square minimap: 30 degrees follows the right edge")
    lua.execute("GetMinimapShape = nil")

    # Drag: locked = nothing; unlocked = follows the cursor, saves minimapPos.
    lua.execute("R2FDB.minimap.lock = true R2F.Minimap.Apply() R2FMinimapButton:Fire('OnDragStart')")
    check(lua.eval("R2FMinimapButton.__scripts.OnUpdate") is None, "locked: dragging does nothing")
    lua.execute("R2FDB.minimap.lock = false R2FMinimapButton:Fire('OnDragStart')")
    check(lua.eval("R2FMinimapButton.__scripts.OnUpdate ~= nil"), "unlocked: drag starts an OnUpdate")
    T.cursorX, T.cursorY = 1000, 700          # straight above the centre (1000, 600)
    lua.execute("R2FMinimapButton:Fire('OnUpdate')")
    check(abs(lua.eval("R2FDB.minimap.minimapPos") - 90) < 1e-6, "drag: cursor above the minimap -> 90 degrees")
    T.cursorX, T.cursorY = 900, 600           # left of it
    lua.execute("R2FMinimapButton:Fire('OnUpdate') R2FMinimapButton:Fire('OnDragStop')")
    check(abs(lua.eval("R2FDB.minimap.minimapPos") - 180) < 1e-6 and lua.eval("R2FMinimapButton.__scripts.OnUpdate") is None,
          "drag stop saves 180 degrees and removes the OnUpdate")
    T.cursorX, T.cursorY = None, None

    # Tooltip (12.2).
    lua.execute("R2FMinimapButton:Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(lines == ["Road to Forever", "0 macros in your library", L.MM_LEFT, L.MM_RIGHT, L.MM_DRAG],
          "minimap tooltip lines: %s" % lines)
    T.talentPoints = 5
    lua.execute("R2FDB.minimap.lock = true R2FMinimapButton:Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check("5 free talent points" in lines and L.MM_DRAG not in lines,
          "tooltip: free talent points when > 0, no drag hint when locked: %s" % lines)
    lua.execute("R2FDB.minimap.lock = false")
    T.talentPoints = 0

    # Left-click toggles the main window on its last tab.
    lua.execute("R2FMinimapButton:Click('LeftButton')")
    check(MW.IsShown() is True and MW.CurrentTab() == "home", "minimap left-click opens the main window (Home first)")
    lua.execute("R2FMinimapButton:Click('LeftButton')")
    check(MW.IsShown() is False, "minimap left-click closes it again")

    # ---- Right-click menu (MenuUtil on the template run, own menu on fallbacks)
    lua.execute("R2FMinimapButton:Click('RightButton')")
    expected = [("title", "Road to Forever"), ("button", L.MENU_OPEN), ("button", L.MENU_MACROS),
                ("button", L.MENU_TALENTS), ("divider", None), ("check", L.MENU_LOCK), ("button", L.MENU_HIDE)]
    if templates:
        menu = lua.eval("TEST.menu")
        got = [(menu[i].kind, menu[i].text) for i in range(1, len(menu) + 1)]
        check(got == expected, "MenuUtil menu = 12.2's items in order: %s" % got)
        click = lambda i: lua.execute("TEST.menu[%d].func()" % i)
        checked = lambda: lua.eval("TEST.menu[6].isChecked()")
    else:
        check(lua.eval("R2FMenu ~= nil and R2FMenu:IsShown()") is True, "no MenuUtil -> own menu frame opens")
        rows = lua.eval("R2FMenu.rows")
        got = [(rows[i].item.kind, rows[i].item.text) for i in range(1, len(expected) + 1)]
        check(got == expected, "own menu rows = 12.2's items in order: %s" % got)
        check(lua.eval("R2FMenu.rows[1].__enabled") is False and lua.eval("R2FMenu.rows[5].__enabled") is False,
              "own menu: title and divider are not clickable")
        check(lua.eval("R2FMenu.rows[6].check.__tex") == "Interface\\Buttons\\UI-CheckBox-Up", "own menu: lock unchecked")
        check("R2FMenu" in lua_table_to_list(lua.eval("UISpecialFrames")), "own menu closes with Esc")

        def click(i):
            lua.execute("R2F.UI.ContextMenu(R2F.Minimap.MenuItems()) R2FMenu.rows[%d]:Click()" % i)
        checked = lambda: lua.eval("R2F.Minimap.MenuItems()[6].isChecked()")
    click(3)
    check(MW.IsShown() is True and MW.CurrentTab() == "macros", "%s: menu > Macros opens the Macros tab" % tag)
    click(4)
    check(MW.CurrentTab() == "talents", "menu > Talents opens the Talents tab")
    click(2)
    check(MW.CurrentTab() == "talents", "menu > Open Road to Forever keeps the last tab")
    lua.execute("R2F.Settings.Show()")
    click(6)
    check(lua.eval("R2FDB.minimap.lock") is True and checked() is True, "menu > Lock button position locks (check item)")
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.SETTINGS_MINIMAP_LOCK then LOCKBOX = f end
        if f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.SETTINGS_MINIMAP_SHOW then SHOWBOX = f end
      end""")
    check(lua.eval("LOCKBOX:GetChecked()") is True, "the open Settings panel follows the menu's lock")
    click(6)
    check(lua.eval("R2FDB.minimap.lock") is False, "Lock again unlocks")
    T.chat = lua.table()
    click(7)
    check(lua.eval("R2FDB.minimap.hide") is True and lua.eval("R2FMinimapButton:IsShown()") is False,
          "menu > Hide minimap button hides it")
    check(any("minimap button hidden. Type /r2f minimap to show it again." in c for c in chat_lines(lua)),
          "hiding prints how to get it back (12.2)")
    check(lua.eval("SHOWBOX:GetChecked()") is False, "Settings' Show box follows the hide")
    lua.execute("R2F.Settings.Toggle()")

    # ---- Slash commands (12.3) ---------------------------------------------
    slash = lambda m: lua.execute('SlashCmdList.R2F(%r)' % m)
    T.chat = lua.table()
    slash("minimap")
    check(lua.eval("R2FDB.minimap.hide") is False and lua.eval("R2FMinimapButton:IsShown()") is True
          and any(L.MM_SHOWN in c for c in chat_lines(lua)), "/r2f minimap shows the hidden button")
    slash("minimap")
    check(lua.eval("R2FDB.minimap.hide") is True and lua.eval("R2FMinimapButton:IsShown()") is False, "/r2f minimap toggles")
    slash("minimap")
    T.chat = lua.table()
    slash("help")
    help_lines = lua_table_to_list(L.HELP_LINES)
    chat = chat_lines(lua)
    check(len(chat) == len(help_lines) and all(c.endswith(h) for c, h in zip(chat, help_lines)), "/r2f help prints the list")
    for cmd in ("/r2f macros", "/r2ft", "/r2f talents", "/r2f minimap", "/r2f help"):
        check(any(h.startswith(cmd) or ("or " + cmd) in h for h in help_lines), "help lists " + cmd)
    lua.execute("R2F.MainWindow.Hide()")
    slash("  MACROS ")
    check(MW.IsShown() is True and MW.CurrentTab() == "macros" and lua.eval("R2F.MacroBook.IsShown()") is True,
          "/r2f macros (any case/spaces) opens the Macros tab")
    slash("macros")
    check(MW.IsShown() is True, "/r2f macros on the Macros tab keeps it open (opens, doesn't toggle)")
    lua.execute("SlashCmdList.R2FT('')")
    check(MW.CurrentTab() == "talents" and lua.eval("SLASH_R2FT1") == "/r2ft", "/r2ft opens the Talents tab")
    slash("home")
    check(any('unknown command "home"' in c for c in chat_lines(lua)), "unknown command says so")
    slash("")
    check(MW.IsShown() is False, "/r2f toggles the window closed")
    slash("")
    check(MW.CurrentTab() == "talents", "/r2f reopens on the last tab used")
    slash("talents")
    check(MW.CurrentTab() == "talents", "/r2f talents opens the Talents tab")
    slash("import")
    check(MW.CurrentTab() == "macros" and lua.eval("R2FImport:IsShown()") is True, "/r2f import still works (Macros + Import)")
    lua.execute("R2FImport:Hide()")

    # ---- Main window tabs ----------------------------------------------------
    n = find_frames(lua, "f.r2fKey ~= nil", "MTABS")
    check(n == 5, "five bottom tabs (15.4)")
    keys = [lua.eval("MTABS[%d].r2fKey" % i) for i in range(1, 6)]
    names = [lua.eval("MTABS[%d]:GetName()" % i) for i in range(1, 6)]
    labels = [lua.eval("MTABS[%d].__text" % i) for i in range(1, 6)]
    check(keys == ["home", "macros", "talents", "reminders", "settings"]
          and labels == ["Home", "Macros", "Talents", "Reminders", "Settings"]
          and names == [win + "Tab%d" % i for i in range(1, 6)], "tabs Home / Macros / Talents / Reminders / Settings, named %s" % names)
    tpl = lua.eval("MTABS[1].r2fTemplate")
    check(tpl == ("CharacterFrameTabButtonTemplate" if templates else "UIPanelButtonTemplate"),
          "%s: tab template chain picked %s" % (tag, tpl))
    lua.execute("MTABS[1]:Click()")
    check(MW.CurrentTab() == "home" and lua.eval("MTABS[1].__enabled") is False and lua.eval("MTABS[2].__enabled") is True,
          "clicking Home selects it (selected tab looks selected = disabled)")
    check(lua.eval("R2FDB.settings.lastTab") == "home", "last tab saved in R2FDB.settings.lastTab")
    title = lua.eval("%s.__title" % win) if templates else lua.eval("%s.r2fTitle.__text" % win)
    check(title == "Road to Forever", "Home title: %r" % title)
    lua.execute("MTABS[2]:Click()")
    title = lua.eval("%s.__title" % win) if templates else lua.eval("%s.r2fTitle.__text" % win)
    check(MW.CurrentTab() == "macros" and title == "Road to Forever: Macros", "Macros tab + title")
    check(lua.eval("R2FDB.settings.lastTab") == "macros", "switching tabs saves lastTab")
    lua.execute("MTABS[3]:Click()")
    check(MW.CurrentTab() == "talents" and lua.eval("R2F.MacroBook.IsShown()") is False, "Talents tab hides the book")
    # Step 9 replaced the placeholder with the real tab (tested in test_talent_preview).
    check(find_frames(lua, "f.__kind == 'Button' and f.__text == R2F.L.BTN_PREVIEW", "TT") == 1
          and lua.eval("R2F.L.TALENTS_TAB_LATER") is None, "Talents tab has its Preview button, no placeholder")
    if templates:
        check(lua.eval("R2FMain.PortraitContainer.portrait.__tex") == "Interface\\AddOns\\RoadToForever\\media\\logo128",
              "portrait = media/logo128")
    check(win in lua_table_to_list(lua.eval("UISpecialFrames")), "main window closes with Esc (UISpecialFrames)")
    check(lua.eval("R2FMacroBook == nil and R2FMacroBookPlain == nil"), "no separate Macro Book window any more")
    lua.execute("R2F.MainWindow.Hide() R2FDB.settings.lastTab = 'bogus' R2F.Library.Init()")
    check(lua.eval("R2FDB.settings.lastTab") == "home", "Init resets an unknown lastTab to home")

    # ---- Home counts -----------------------------------------------------------
    parse = lua.eval("function(s) local a, b = R2F.Import.Parse(s) return a, b end")
    res, _ = parse(fx["everything"]["string"])
    lua.eval("R2F.Library.Apply")(res.records, 1)
    total = len(fx["everything"]["records"])
    for i in ("WARRIOR/Ham", "WARRIOR/OP", "WARRIOR/Mock"):
        lua.execute('R2F.Macros.Ensure(%r)' % i)
    lua.execute('TEST.actions[1] = "Ham" TEST.actions[80] = "Mock" TEST.addMacro("Mine", "/dance", true) TEST.actions[2] = "Mine"')
    inlib, onbars = lua.eval("R2F.Home.Counts")()
    check((inlib, onbars) == (total, 2), "Home counts: whole library, our macros on bars only (%s, %s)" % (inlib, onbars))
    lua.execute("R2F.MainWindow.Show('home')")
    find_frames(lua, "f.__kind == 'Button' and f.tab ~= nil and f.sub ~= nil", "HOME")
    check(lua.eval("#HOME") == 3, "Home has three entries: Macro Book, Talents, macro slots (15.2)")
    check(lua.eval("HOME[1].sub.__text") == "%d macros in your library, 2 on your bars" % total,
          "Home Macro Book line: %r" % lua.eval("HOME[1].sub.__text"))
    # Step 9: 12.4's free-points line instead of the step-6 placeholder.
    check(lua.eval("HOME[2].sub.__text") == "No free talent points", "Home Talents line with no free points")
    T.talentPoints = 5
    lua.execute("R2F.Home.Refresh()")
    check(lua.eval("HOME[2].sub.__text") == "5 free talent points", "Home Talents line: 5 free talent points")
    T.talentPoints = 1
    T.fire("CHARACTER_POINTS_CHANGED")
    T.runTimers()
    check(lua.eval("HOME[2].sub.__text") == "1 free talent point", "Home Talents line follows CHARACTER_POINTS_CHANGED")
    T.talentPoints = 0
    T.fire("PLAYER_LEVEL_UP")
    T.runTimers()
    check(lua.eval("HOME[2].sub.__text") == "No free talent points", "Home Talents line follows PLAYER_LEVEL_UP")
    lua.execute('TEST.actions[80] = nil')
    T.fire("ACTIONBAR_SLOT_CHANGED")
    T.runTimers()
    check(lua.eval("HOME[1].sub.__text").endswith(", 1 on your bars"), "Home count follows ACTIONBAR_SLOT_CHANGED")
    lua.execute("R2F.Library.db.library = {} R2F.Library.Apply({ { id = 'ANY/Zoom', class = 'ANY', section = 'Universal',"
                " group = 'Misc / UI', name = 'Zoom', short = 'Zoom', body = '/x' } }, 1) R2F.Home.Refresh()")
    check(lua.eval("HOME[1].sub.__text").startswith("1 macro in your library"), "singular wording for 1 macro")
    lua.eval("R2F.Library.Apply")(res.records, 1)
    find_frames(lua, "f.__kind == 'Button' and f.__text == R2F.L.HOME_IMPORT", "HIMPORT")
    T.fire("PLAYER_REGEN_DISABLED")
    check(lua.eval("HIMPORT[1].__enabled") is False, "Home's Import macros is greyed out in combat")
    T.fire("PLAYER_REGEN_ENABLED")
    lua.execute("HIMPORT[1]:Click()")
    check(lua.eval("R2FImport:IsShown()") is True, "Home's Import macros opens the Import window")
    lua.execute("R2FImport:Hide() HOME[1]:Click()")
    check(MW.CurrentTab() == "macros", "clicking the Macro Book entry switches to the Macros tab")
    lua.execute("R2F.MainWindow.SelectTab('home') HOME[2]:Click()")
    check(MW.CurrentTab() == "talents", "clicking the Talents entry switches to the Talents tab")

    # ---- Home footer: version/author (12.4.2) ----------------------------------
    # The footer is built once with the page (same as every other Home widget),
    # so each metadata scenario needs its own fresh runtime, not a hide/show
    # cycle on this one. Matched by r2fFooterHit, not by text, since the window
    # title ("Road to Forever") would otherwise also match a loose text pattern.
    lua.execute("R2F.MainWindow.SelectTab('home')")
    find_frames(lua, "f.r2fFooterHit", "FOOTERHIT")
    check(lua.eval("#FOOTERHIT") == 1, "%s: footer has exactly one hover hit-frame" % tag)
    find_frames(lua, "f.__kind == 'FontString' and f.__text and f.__text:find('github.io/wow%-forever')", "FOOTER")
    check(lua.eval("#FOOTER") == 1 and lua.eval("FOOTER[1].__text") ==
          "Road to Forever v0.10.1 · by nobody174 · nobody174.github.io/wow-forever",
          "%s: footer reads the TOC's real version/author: %r" % (tag, lua.eval("FOOTER[1].__text")))
    lua.execute("FOOTERHIT[1]:Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(lines == [lua.eval("R2F.L.HOME_FOOTER_TIP")],
          "%s: hovering the footer shows the why-it-exists tooltip: %r" % (tag, lines))
    lua.execute("FOOTERHIT[1]:Fire('OnLeave')")
    check(lua.eval("GameTooltip:IsShown()") is False, "%s: leaving the footer hides the tooltip" % tag)

    # Neither metadata API exists on this client -> plain fallback line, no error.
    lua2 = new_runtime(templates)
    lua2.execute("C_AddOns = nil GetAddOnMetadata = nil")
    lua2.execute("TEST.fire('ADDON_LOADED', 'RoadToForever') TEST.fire('PLAYER_LOGIN') R2F.MainWindow.Show('home')")
    find_frames(lua2, "f.__kind == 'FontString' and f.__text and f.__text:find('github.io/wow%-forever')", "FOOTER2")
    check(lua2.eval("FOOTER2[1].__text") == "Road to Forever · nobody174.github.io/wow-forever",
          "%s: no metadata API -> plain fallback line, not an error: %r" % (tag, lua2.eval("FOOTER2[1].__text")))

    # Only the legacy global exists (an older client) -> still reads the real values.
    lua3 = new_runtime(templates)
    lua3.execute("C_AddOns = nil")
    lua3.execute("TEST.fire('ADDON_LOADED', 'RoadToForever') TEST.fire('PLAYER_LOGIN') R2F.MainWindow.Show('home')")
    find_frames(lua3, "f.__kind == 'FontString' and f.__text and f.__text:find('github.io/wow%-forever')", "FOOTER3")
    check(lua3.eval("FOOTER3[1].__text") ==
          "Road to Forever v0.10.1 · by nobody174 · nobody174.github.io/wow-forever",
          "%s: legacy-only GetAddOnMetadata still reads the real values: %r" % (tag, lua3.eval("FOOTER3[1].__text")))

    # ---- Macro Book reparented: refresh, tabs, drag, tooltip, paging, menu ------
    lua.execute("R2F.MainWindow.SelectTab('home') R2F.MacroBook.Refresh()")
    find_frames(lua, "f.__kind == 'Button' and f.__scripts.OnDragStart and f ~= R2FMinimapButton", "SLOTS")
    check(lua.eval("#SLOTS") == 12 and lua.eval("SLOTS[1].__parent.__parent:GetName()") == win,
          "the book's 12 slots live in a page of the main window")
    check(lua.eval("R2F.MacroBook.IsShown()") is False, "book not 'shown' while Home is the tab")
    lua.execute("R2F.MacroBook.ShowSection('WARRIOR', 'General')")
    check(MW.CurrentTab() == "macros" and lua.eval("R2F.MacroBook.IsShown()") is True, "ShowSection opens the Macros tab")
    general = [r for r in fx["everything"]["records"] if r["class"] == "WARRIOR" and r["section"] == "General"]
    check(lua.eval("SLOTS[1].entry.id") == general[0]["id"], "book shows the requested section after reparenting")
    lua.execute("SLOTS[1]:Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(lines[0] == general[0]["name"] and lines[-1] == "Drag to an action bar.", "slot tooltip still works")
    T.cursor = None
    lua.execute("SLOTS[2]:Fire('OnDragStart')")
    check(T.cursor == general[1]["short"], "dragging from the reparented book still creates + picks up")
    pages = -(-len(general) // 12)
    find_frames(lua, "f.__kind == 'FontString' and type(f.__text) == 'string' and f.__text:match('^Page ')", "PAGETEXT")
    find_frames(lua, "f.__normal and f.__normal.__tex == 'Interface\\\\Buttons\\\\UI-SpellbookIcon-NextPage-Up'", "NEXT")
    check(lua.eval("PAGETEXT[1].__text") == "Page 1 of %d" % pages, "paging text in the reparented book")
    if pages > 1:
        lua.execute("NEXT[1]:Click()")
        check(lua.eval("PAGETEXT[1].__text") == "Page 2 of %d" % pages and lua.eval("SLOTS[1].entry.id") == general[12]["id"],
              "next page works in the reparented book")
    lua.execute("SLOTS[1]:Click('RightButton')")
    find_frames(lua, "f.__kind == 'Button' and f.__text == R2F.L.MENU_REMOVE", "RM")
    menu_frame = "RM[1].__parent"
    check(lua.eval(menu_frame + ":IsShown()") is True, "slot right-click menu opens")
    lua.execute("R2F.MainWindow.Hide()")
    check(lua.eval(menu_frame + ":IsShown()") is False, "closing the main window closes the slot menu")
    check(lua.eval("R2F.MacroBook.IsShown()") is False, "book is not 'shown' with the window closed")
    lua.execute("R2F.MacroBook.Toggle()")
    check(lua.eval("R2F.MacroBook.IsShown()") is True and MW.CurrentTab() == "macros", "MacroBook.Toggle opens the Macros tab")
    lua.execute("R2F.MacroBook.Toggle()")
    check(MW.IsShown() is False, "MacroBook.Toggle on the Macros tab closes the window")
    # Refresh while hidden must not touch anything (no error, nothing shown).
    for ev in ("UPDATE_MACROS", "ACTIONBAR_SLOT_CHANGED", "LEARNED_SPELL_IN_TAB", "PLAYER_REGEN_DISABLED", "PLAYER_REGEN_ENABLED"):
        T.fire(ev)
    T.runTimers()
    check(MW.IsShown() is False, "events with the window closed don't open it")


def test_minimap_libdbicon(fx):
    """Step 6: when another addon has loaded LibDataBroker + LibDBIcon, use that copy (6.10)."""
    lua = new_runtime()
    T = lua.eval("TEST")
    lua.execute("""
      DBI = { calls = {} }
      LDB = { objects = {} }
      function LDB:NewDataObject(name, obj) self.objects[name] = obj return obj end
      for _, m in ipairs({ 'Register', 'Show', 'Hide', 'Lock', 'Unlock' }) do
        DBI[m] = function(self, name, a, b)
          table.insert(self.calls, m .. ':' .. name)
          if m == 'Register' then self.obj, self.db = a, b end
        end
      end
      LibStub = { GetLibrary = function(self, major, silent)
        if major == 'LibDataBroker-1.1' then return LDB end
        if major == 'LibDBIcon-1.0' then return DBI end
      end }""")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    check(lua.eval("R2F.Minimap.backend") == "libdbicon", "LibDBIcon from another addon -> used")
    check(lua.eval("DBI.calls[1]") == "Register:RoadToForever" and lua.eval("DBI.db == R2FDB.minimap"),
          "Register gets R2FDB.minimap as-is (6.3/6.9)")
    check(lua.eval("R2FMinimapButton") is None, "no second, own button")
    obj = lua.eval("LDB.objects.RoadToForever")
    check(obj.type == "launcher" and obj.icon == "Interface\\AddOns\\RoadToForever\\media\\logo64", "LDB launcher object")
    lua.execute("DBI.calls = {} R2FDB.minimap.hide = true R2FDB.minimap.lock = true R2F.Minimap.Apply()")
    check(lua_table_to_list(lua.eval("DBI.calls")) == ["Hide:RoadToForever", "Lock:RoadToForever"], "Apply -> Hide + Lock")
    lua.execute("DBI.calls = {} R2FDB.minimap.hide = false R2FDB.minimap.lock = false R2F.Minimap.Apply()")
    check(lua_table_to_list(lua.eval("DBI.calls")) == ["Show:RoadToForever", "Unlock:RoadToForever"], "Apply -> Show + Unlock")
    lua.execute("LDB.objects.RoadToForever.OnClick(UIParent, 'LeftButton')")
    check(lua.eval("R2F.MainWindow.IsShown()") is True, "LDB OnClick left = open the main window")
    lua.execute("LDB.objects.RoadToForever.OnClick(UIParent, 'RightButton')")
    check(lua.eval("TEST.menu ~= nil and #TEST.menu == 7"), "LDB OnClick right = the menu")
    lua.execute("GameTooltip:SetOwner() LDB.objects.RoadToForever.OnTooltipShow(GameTooltip)")
    check(lua_table_to_list(lua.eval("GameTooltip.lines"))[0] == "Road to Forever", "LDB tooltip filled by FillTooltip")

    # A broken copy (Register errors) -> our own button instead, no error.
    lua2 = new_runtime()
    lua2.execute("LibStub = { GetLibrary = function(_, major) return { NewDataObject = function() return {} end,"
                 " Register = function() error('old copy') end } end }")
    lua2.eval("TEST").fire("ADDON_LOADED", "RoadToForever")
    lua2.eval("TEST").fire("PLAYER_LOGIN")
    check(lua2.eval("R2F.Minimap.backend") == "own" and lua2.eval("R2FMinimapButton ~= nil"),
          "broken LibDBIcon copy -> falls back to our own button")
    # lastTab survives a reload: saved data from an earlier session decides /r2f's tab.
    lua4 = new_runtime()
    lua4.execute("R2FDB = { settings = { lastTab = 'talents', windowPos = { 'TOPLEFT', 'TOPLEFT', 30, -40 } } }")
    lua4.eval("TEST").fire("ADDON_LOADED", "RoadToForever")
    lua4.eval("TEST").fire("PLAYER_LOGIN")
    lua4.execute("SlashCmdList.R2F('')")
    check(lua4.eval("R2F.MainWindow.CurrentTab()") == "talents", "after a reload /r2f opens the saved last tab")
    pt = lua_table_to_list(lua4.eval("R2FMain.__point"))
    check(pt[0] == "TOPLEFT" and pt[3:] == [30, -40], "main window opens at the saved windowPos: %s" % pt)
    # No Minimap frame at all -> no button, no error.
    lua3 = new_runtime()
    lua3.execute("Minimap = nil")
    lua3.eval("TEST").fire("ADDON_LOADED", "RoadToForever")
    lua3.eval("TEST").fire("PLAYER_LOGIN")
    check(lua3.eval("R2F.Minimap.backend") == "none", "no Minimap frame -> no button, no error")
    lua3.execute("R2F.Minimap.Apply() SlashCmdList.R2F('minimap')")
    check(lua3.eval("R2FDB.minimap.hide") is True, "/r2f minimap still stores the setting without a button")


def test_media():
    """Step 6 logo (12.1): both TGAs exist, 32-bit with alpha, power-of-two, transparent outside the circle."""
    import struct
    check(os.path.exists(os.path.join(ROOT, "addon", "art", "logo.svg")), "addon/art/logo.svg exists")
    for size in (64, 128):
        path = os.path.join(ADDON, "media", "logo%d.tga" % size)
        check(os.path.exists(path), "media/logo%d.tga exists" % size)
        if not os.path.exists(path):
            continue
        data = open(path, "rb").read()
        id_len, cmap, kind = data[0], data[1], data[2]
        w, h = struct.unpack("<HH", data[12:16])
        bpp, desc = data[16], data[17]
        check(kind == 2 and cmap == 0, "logo%d: uncompressed true-color TGA" % size)
        check((w, h) == (size, size) and size & (size - 1) == 0, "logo%d: %dx%d, power of two" % (size, w, h))
        check(bpp == 32 and desc & 0x0F == 8, "logo%d: 32 bpp with 8 alpha bits" % size)
        px = data[18 + id_len:18 + id_len + w * h * 4]
        check(len(px) == w * h * 4, "logo%d: full pixel data" % size)
        alpha = lambda x, y: px[(y * w + x) * 4 + 3]   # BGRA; row order doesn't matter for these points
        check(all(alpha(x, y) == 0 for x, y in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))),
              "logo%d: transparent corners" % size)
        check(alpha(w // 2, h // 2) == 255, "logo%d: opaque centre" % size)
    check(not os.path.exists(os.path.join(ADDON, "libs")), "no libs folder shipped (6.10: nothing vendored)")


TALENT_FIXTURE = os.path.join(HERE, "talent_fixture.json")
SITE_TALENTS = "https://nobody174.github.io/wow-forever-macros/talents.html#"


def ref_talent_hash(text):
    """Third, independent implementation of the 13.3 hash (Python), on UTF-8 bytes."""
    h = 5381
    for b in text.encode("utf-8"):
        h = (h * 33 + b) % 2**32
    v, out = h % 36**4, ""
    for _ in range(4):
        out = "0123456789abcdefghijklmnopqrstuvwxyz"[v % 36] + out
        v //= 36
    return out


def talent_js(fixture_path=TALENT_FIXTURE):
    """Run the real talentcalc.js (Node) on a talent fixture."""
    out = subprocess.run(["node", os.path.join(HERE, "talent_link_check.js"), fixture_path],
                         capture_output=True, check=True, cwd=ROOT)
    return json.loads(out.stdout.decode("utf-8"))


def set_game_talents(lua, raw, tree_ids, ranks, order="name"):
    """Fill the fake client's talents (C_Traits view, wow_stubs.lua) from
    Wowhead-format data: one pane per tree id, talents in a client order that
    is NOT row/col (by name, or reversed). A tree with no talents can only be
    expressed with one trait tree per pane (an empty pane has no position to
    be found by in a single tree; a real tree never has one), so then the
    stub's "perPane" layout is used, otherwise the real single-tree one."""
    lua.execute("TEST.talentTabs = {}")
    empty = any(not (raw.get(str(tid)) or {}) for tid in tree_ids)
    lua.execute("TEST.traitLayout = %r" % ("perPane" if empty else "single"))
    add = lua.eval("function(t, n, tier, col, rank, mx, ptier, pcol) TEST.talentTabs[t] = TEST.talentTabs[t] or {}"
                   " table.insert(TEST.talentTabs[t], { name = n, tier = tier, column = col, rank = rank, maxRank = mx,"
                   " prereq = ptier and { ptier, pcol } or nil }) end")
    for t, tid in enumerate(tree_ids, start=1):
        lua.execute("TEST.talentTabs[%d] = {}" % t)
        tree = raw.get(str(tid)) or {}
        by_id = {x["id"]: x for x in tree.values()}
        talents = list(tree.values())
        talents.sort(key=lambda x: x["name"], reverse=(order == "reverse"))
        for x in talents:
            # Step 10: Wowhead's requires[{id}] -> the prerequisite's tier/column
            # (GetTalentPrereqs and the fake server's rule).
            req = by_id.get((x.get("requires") or [{}])[0].get("id"))
            add(t, x["name"], x["row"] + 1, x["col"] + 1, ranks.get(x["name"], 0), len(x["ranks"]),
                req and req["row"] + 1, req and req["col"] + 1)


def test_talents(templates):
    """Step 8: Talents.lua (read, encode, ~hash, Copy my build) cross-checked
    against the real talentcalc.js on the same fixture (ADDON_PLAN 13.3)."""
    tag = "templates" if templates else "fallbacks"
    fxt = json.load(open(TALENT_FIXTURE, encoding="utf-8"))
    raw = fxt["talents"]
    js = talent_js()
    lua = new_runtime(templates)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    TL = lua.eval("R2F.Talents")
    read = lua.eval("function() return R2F.Talents.ReadTrees() end")

    # ---- 13.10: talents come from C_Traits, nothing is loaded on demand ------
    # (13.9 force-loaded Blizzard_TalentUI; on WoW Forever that answers
    # false, "MISSING" and the Classic globals never appear.)
    set_game_talents(lua, raw, js["classes"]["warrior"], {})
    T.loadAddOnCalls = lua.table()
    trees = read()
    check(trees is not None and len(trees) == 3, "%s: ReadTrees() reads 3 panes from C_Traits on the first call" % tag)
    check(len(lua_table_to_list(T.loadAddOnCalls)) == 0, "%s: ReadTrees() never calls LoadAddOn" % tag)
    check(lua.eval("GetNumTalentTabs == nil and GetNumTalents == nil") is True,
          "%s: the fake client has no Classic tab API at all (like WoW Forever)" % tag)
    check(lua.eval("select(2, LoadAddOn('Blizzard_TalentUI'))") == "MISSING",
          "%s: the fake client answers Blizzard_TalentUI with MISSING, like the real one" % tag)
    # Config not ready yet (right after login): nil, then fine once it is.
    T.traitsReady = False
    check(read() is None, "%s: no combat config yet -> ReadTrees() nil, no error" % tag)
    T.traitsReady = True
    check(read() is not None, "%s: config ready -> ReadTrees() works" % tag)
    # Each missing / failing piece of the chain: nil, never a Lua error.
    for setup in ("C_Traits = nil", "C_SpecializationInfo = nil",
                  "C_SpecializationInfo.GetActiveSpecGroup = nil",
                  "C_SpecializationInfo.GetCombatConfigIDForSpecGroup = function() error('boom') end",
                  "C_Traits.GetConfigInfo = function() return nil end",
                  "C_Traits.GetConfigInfo = function() return { treeIDs = {} } end",
                  "C_Traits.GetTreeNodes = function() error('boom') end",
                  "C_Traits.GetNodeInfo = function() error('boom') end",
                  "C_Traits.GetDefinitionInfo = function() return nil end",
                  "C_Spell.GetSpellName = function() return nil end GetSpellInfo = nil"):
        lua_x = new_runtime(templates)
        lua_x.execute("TEST.fire('ADDON_LOADED', 'RoadToForever') TEST.fire('PLAYER_LOGIN')")
        set_game_talents(lua_x, raw, js["classes"]["warrior"], {})
        lua_x.execute(setup)
        check(lua_x.eval("R2F.Talents.ReadTrees()") is None, "%s: %s -> ReadTrees() nil, no error" % (tag, setup))
    # GetSpellInfo fallback when C_Spell has no GetSpellName.
    lua_x = new_runtime(templates)
    lua_x.execute("TEST.fire('ADDON_LOADED', 'RoadToForever') TEST.fire('PLAYER_LOGIN')")
    set_game_talents(lua_x, raw, js["classes"]["warrior"], {})
    lua_x.execute("C_Spell = nil GetSpellInfo = function(id) return TEST.spellNames[id] end")
    check(lua_x.eval("R2F.Talents.Hash(R2F.Talents.ReadTrees())") == js["hashes"]["warrior"],
          "%s: names via GetSpellInfo when C_Spell is missing" % tag)

    # ---- The hash: Lua == JS == Python, per class, on the same names -----------
    check(TL.HashText("") == ref_talent_hash("") == "045h", "%s: hash of '' = 5381 -> '045h'" % tag)
    for s in ("Deflection", "Ünbridled Wrath", "a,b;c", "x" * 300):
        check(TL.HashText(s) == ref_talent_hash(s), "%s: Lua HashText == Python reference for %r" % (tag, s[:20]))
    # A class with no data at all (Paladin isn't in the fixture): the site hashes
    # ";;"; the addon never makes a link from that (no talents -> can't read).
    check(TL.HashText(";;") == js["hashes"]["paladin"], "%s: empty-class hash agrees (';;')" % tag)
    for cls in ("warrior", "hunter"):
        set_game_talents(lua, raw, js["classes"][cls], {})
        lua_hash = TL.Hash(read())
        names = ";".join(",".join(x["name"] for x in sorted((raw.get(str(tid)) or {}).values(),
                                                             key=lambda x: (x["row"], x["col"])))
                         for tid in js["classes"][cls])
        check(lua_hash == js["hashes"][cls] == ref_talent_hash(names),
              "%s: %s ~hash identical in Talents.lua (%s), talentcalc.js (%s) and Python (%s)"
              % (tag, cls, lua_hash, js["hashes"][cls], ref_talent_hash(names)))
    # Client index order must not matter (the sort is what makes it link order).
    set_game_talents(lua, raw, js["classes"]["warrior"], {}, order="reverse")
    check(TL.Hash(read()) == js["hashes"]["warrior"], "%s: hash independent of GetTalentInfo index order" % tag)

    # ---- Reading: sorted by tier, then column -----------------------------------
    set_game_talents(lua, raw, js["classes"]["warrior"], {"Deflection": 5})
    trees = read()
    arms = [trees[1][i].name for i in range(1, len(trees[1]) + 1)]
    want = [x["name"] for x in sorted(raw["161"].values(), key=lambda x: (x["row"], x["col"]))]
    check(arms == want, "%s: ReadTrees sorts by tier then column: %s" % (tag, arms))
    check(len(trees) == 3 and trees[1][2].rank == 5 and trees[1][2].maxRank == 5, "%s: ranks and max ranks read" % tag)

    # ---- Encoder + full link, every scenario: hand-made == JS == Lua ------------
    for sc, jsc in zip(fxt["scenarios"], js["scenarios"]):
        lua.execute("TEST.classToken = %r" % sc["cls"].upper())
        set_game_talents(lua, raw, js["classes"][sc["cls"]], sc["ranks"])
        trees = read()
        code = TL.Encode(trees)
        body = TL.LinkBody(TL.ClassId(), trees)
        want_body = "%s/%s~%s" % (sc["cls"], sc["code"], js["hashes"][sc["cls"]])
        check(jsc["total"] == jsc["points"], "%s: %s: fixture build is valid on the site" % (tag, sc["name"]))
        check(code == sc["code"], "%s: %s: Lua code %r == hand-worked %r" % (tag, sc["name"], code, sc["code"]))
        check(body == jsc["link"] == want_body, "%s: %s: Lua link %r == talentcalc.js link %r" % (tag, sc["name"], body, jsc["link"]))
        check(jsc["reread"] == jsc["rereadBare"] == jsc["rereadSetCode"] == jsc["encode"],
              "%s: %s: site reads the link with and without ~hash to the same build" % (tag, sc["name"]))
        check(TL.MyBuildLink() == SITE_TALENTS + body, "%s: %s: full link = site URL + body" % (tag, sc["name"]))
    lua.execute("TEST.classToken = nil")
    check(TL.SITE_URL == SITE_TALENTS, "%s: SITE_URL" % tag)
    check(js["clean"] == {"05302": "05302", "05302~abcd": "05302", "--53041~0000": "--53041", "~abcd": "",
                          "": "", "3-0502~": "3-0502", "a~b~c": "a"}, "%s: cleanCode drops everything from ~" % tag)
    want_read = {"35~111": "warrior/35", "35~111-5": "warrior/35", "--53041~1z9k": "warrior/--53041", "3-0502~00": "warrior/3-0502"}
    for k, v in want_read.items():
        check(js["readHashed"][k] == [v, v], "%s: site reads %r as %r (got %s)" % (tag, k, v, js["readHashed"][k]))
    check(js["hashForBefore"] == "" and js["hashForAfterMount"] == js["hashes"]["warrior"]
          and js["hashForUnknownClass"] == "", "%s: hashFor only once data is loaded" % tag)

    # ---- The hash catches what it's for -------------------------------------------
    base = js["hashes"]["warrior"]
    def variant(mutate):
        r = json.loads(json.dumps(raw))
        mutate(r)
        set_game_talents(lua, r, js["classes"]["warrior"], {})
        return TL.Hash(read())
    check(variant(lambda r: r["161"]["3"].update(name="Deflectio")) != base, "%s: renamed talent -> different hash" % tag)
    check(variant(lambda r: r["163"].pop("33")) != base, "%s: missing talent (like Crusade) -> different hash" % tag)
    check(variant(lambda r: (r["161"]["9"].update(col=2), r["161"]["7"].update(col=0))) != base,
          "%s: two talents swapped -> different hash" % tag)
    set_game_talents(lua, raw, [163, 164, 161], {})
    check(TL.Hash(read()) != base, "%s: tabs in another order -> different hash" % tag)
    r2 = json.loads(json.dumps(raw))
    r2["163"]["33"]["row"] = 3   # Improved Bloodrage moves below Iron Will: same names, new link order
    set_game_talents(lua, r2, js["classes"]["warrior"], {})
    check(TL.Hash(read()) != base, "%s: talent moved to another tier -> different hash" % tag)

    # ---- Copy my build: /r2f copybuild, popup with the link selected ------------
    set_game_talents(lua, raw, js["classes"]["warrior"], fxt["scenarios"][1]["ranks"])
    link = SITE_TALENTS + "warrior/%s~%s" % (fxt["scenarios"][1]["code"], base)
    T.calls = lua.table()
    lua.execute("SlashCmdList.R2F('copybuild')")
    check(lua.eval("R2FCopy ~= nil and R2FCopy:IsShown()") is True, "%s: /r2f copybuild opens the copy box" % tag)
    check(lua.eval("R2FCopy.edit:GetText()") == link, "%s: copy box holds the link: %r" % (tag, lua.eval("R2FCopy.edit:GetText()")))
    check(lua.eval("R2FCopy.hint.__text") == lua.eval("R2F.L.TALENT_COPY_HINT")
          == "Press Ctrl+C, then paste it in your browser or Discord.", "%s: copy hint per 13.4" % tag)
    # Typing into the box puts the link back (the copy box's own rule).
    lua.execute("R2FCopy.edit.__text = 'x' R2FCopy.edit.__scripts.OnTextChanged(R2FCopy.edit, true)")
    check(lua.eval("R2FCopy.edit:GetText()") == link, "%s: typing can't change the link" % tag)
    # Read-only: works in combat, no macro or talent writes at all.
    lua.execute("R2FCopy:Hide()")
    T.combat = True
    T.fire("PLAYER_REGEN_DISABLED")
    got = lua.eval("R2F.Talents.CopyMyBuild()")
    check(got == link and lua.eval("R2FCopy:IsShown()") is True, "%s: Copy my build works in combat (read-only)" % tag)
    check(len(lua_table_to_list(T.calls)) == 0, "%s: Copy my build makes no macro API calls" % tag)
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")
    # The macro book's Copy text still gets its own hint afterwards.
    lua.execute("R2F.UI.ShowCopy('/cast x')")
    check(lua.eval("R2FCopy.hint.__text") == lua.eval("R2F.L.COPY_HINT"), "%s: default copy hint restored for Copy text" % tag)
    lua.execute("R2FCopy:Hide()")
    # No talent data yet / no talent API: a chat line, no popup, no error.
    lua.execute("TEST.talentTabs = {} TEST.chat = {}")
    check(lua.eval("R2F.Talents.CopyMyBuild()") is None and lua.eval("R2FCopy:IsShown()") is False
          and any(lua.eval("R2F.L.TALENT_READ_FAILED") in c for c in chat_lines(lua)),
          "%s: no talent tabs -> chat line, no popup" % tag)
    lua.execute("TEST.talentTabs = { {}, {}, {} }")
    check(lua.eval("R2F.Talents.CopyMyBuild()") is None and lua.eval("R2FCopy:IsShown()") is False,
          "%s: tabs without talents (data not loaded) -> no link" % tag)
    lua.execute("C_Traits = nil")
    check(lua.eval("R2F.Talents.CopyMyBuild()") is None, "%s: no talent API (C_Traits) -> nil, no error" % tag)
    help_lines = lua_table_to_list(lua.eval("R2F.L.HELP_LINES"))
    check(any(h.startswith("/r2f copybuild") for h in help_lines), "%s: help lists /r2f copybuild" % tag)


def lua_states(plan):
    """{talent name: (state, planned, now, later)} from a Talents.Plan result."""
    out = {}
    for t in range(1, len(plan.trees) + 1):
        tree = plan.trees[t]
        for k in range(1, len(tree.talents) + 1):
            e = tree.talents[k]
            out[e.name] = (e.state, e.planned, e.now, e.later)
    return out


def test_talent_preview(templates):
    """Step 9: link parsing (13.2), the ~hash check on import (13.3), sanity
    checks, the plan/summary (13.4) and the Talents tab UI. Links come from the
    REAL talentcalc.js (Node) on the step-8 fixture, so parsing is checked
    against what the site actually hands out, and the hash compared is step 8's
    unchanged Talents.Hash."""
    tag = "templates" if templates else "fallbacks"
    fxt = json.load(open(TALENT_FIXTURE, encoding="utf-8"))
    raw = fxt["talents"]
    js = talent_js()
    lua = new_runtime(templates)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    TL = lua.eval("R2F.Talents")
    L = lua.eval("R2F.L")
    parse = lua.eval("function(s) return R2F.Talents.ParseLink(s) end")
    prev = lua.eval("function(s) return R2F.Talents.Preview(s) end")
    W = js["classes"]["warrior"]
    wh = js["hashes"]["warrior"]
    lua.execute("TEST.tabNames = { 'Arms', 'Fury', 'Protection' }")

    def game(ranks, points, cls="warrior"):
        lua.execute("TEST.classToken = %r" % cls.upper())
        set_game_talents(lua, raw, js["classes"][cls], ranks)
        T.talentPoints = points

    # ---- 13.2: the four accepted forms (+ what a paste can add) -------------
    def parsed(s):
        r = parse(s)
        if r is None:
            return None
        return (r["class"], r.code, r.hash, lua_table_to_list(r.codes))
    forms = {
        SITE_TALENTS + "warrior/05302~" + wh: ("warrior", "05302", wh, ["05302"]),
        "talents.html#warrior/3-0502~" + wh: ("warrior", "3-0502", wh, ["3", "0502"]),
        "#warrior/--53041": ("warrior", "--53041", None, ["", "", "53041"]),
        "warrior/05302": ("warrior", "05302", None, ["05302"]),
        "  <%sWarrior/05302~%s>  " % (SITE_TALENTS, wh.upper()): ("warrior", "05302", wh, ["05302"]),
        "warrior/": ("warrior", "", None, [""]),
        "warrior/~" + wh: ("warrior", "", wh, [""]),
        "warrior/3-0502~": ("warrior", "3-0502", None, ["3", "0502"]),
        "druid/5": ("druid", "5", None, ["5"]),
    }
    for s, want in forms.items():
        check(parsed(s) == want, "%s: ParseLink(%r) = %s, want %s" % (tag, s, parsed(s), want))
    for s in ("", "   ", "hello", "warrior", "foo/123", "warrior/32a", "warrior/32~ab~c", "warrior/3 2",
              "https://nobody174.github.io/wow-forever-macros/talents.html", "https://github.io/x"):
        check(parse(s) is None, "%s: ParseLink(%r) refused" % (tag, s))
    check(parse(None) is None and lua.eval("R2F.Talents.ParseLink(42)") is None, "%s: non-string -> nil" % tag)
    # Every link the real site makes, bare and as a full URL, parses back to it.
    for jsc in js["scenarios"]:
        cls, rest = jsc["link"].split("/", 1)
        code, h = rest.split("~")
        for s in (jsc["link"], SITE_TALENTS + jsc["link"], "talents.html#" + jsc["link"], "#" + jsc["link"]):
            p = parsed(s)
            check(p is not None and p[:3] == (cls, code, h), "%s: site link %r parses to (%s, %s, %s): %s"
                  % (tag, s, cls, code, h, p))

    # ---- Class must match (13.2) -------------------------------------------------
    game({}, 10)
    r = prev("paladin/5~abcd")
    check(r.error == "This is a Paladin build. You're playing a Warrior." and r.plan is None,
          "%s: wrong class -> 13.2's message exactly: %r" % (tag, r.error))
    game({}, 10, cls="hunter")
    r = prev(SITE_TALENTS + "warrior/05302~" + wh)
    check(r.error == "This is a Warrior build. You're playing a Hunter.", "%s: wrong class (hunter): %r" % (tag, r.error))
    r = prev("not a link")
    check(r.error == L.TALENT_BAD_LINK and r.plan is None, "%s: junk -> bad-link message" % tag)

    # ---- Decoding == the site's encoding: each real site link previews as its build
    for sc, jsc in zip(fxt["scenarios"], js["scenarios"]):
        game({}, 51, cls=sc["cls"])
        r = prev(SITE_TALENTS + jsc["link"])
        got = {n: v[1] for n, v in lua_states(r.plan).items() if v[1]} if r.plan else None
        check(r.error is None and r.caution is None and got == sc["ranks"],
              "%s: %s: site link previews as exactly its build: %s (error %s)" % (tag, sc["name"], got, r.error))
        # The same character after learning it: nothing left to do.
        game(sc["ranks"], 0, cls=sc["cls"])
        r = prev(jsc["link"])
        want = L.TALENT_SUMMARY_EMPTY if not sc["ranks"] else L.TALENT_SUMMARY_DONE
        check(r.plan is not None and r.plan.summary == want and r.plan.learnable is False,
              "%s: %s: own build -> %r: %r" % (tag, sc["name"], want, r.plan and r.plan.summary))
    # Client index order doesn't matter (ReadTrees' sort is reused, not redone).
    lua.execute("TEST.classToken = 'WARRIOR'")
    set_game_talents(lua, raw, W, {}, order="reverse")
    T.talentPoints = 51
    r = prev("warrior/05302~" + wh)
    check({n: v[1] for n, v in lua_states(r.plan).items() if v[1]} == fxt["scenarios"][1]["ranks"],
          "%s: mapping independent of GetTalentInfo index order" % tag)

    # ---- 13.3: the ~hash on import -----------------------------------------------
    game({}, 10)
    r = prev("warrior/05302~" + wh)
    check(r.plan is not None and r.error is None and r.caution is None, "%s: matching hash -> preview, no warning" % tag)
    r = prev("warrior/05302~zzzz")
    want_mismatch = ("This link was made with different talent trees than your game has. Nothing was learned. "
                     "Make a new link on the site or wait for the site to update.")
    check(r.error == want_mismatch and r.plan is None, "%s: different hash -> stop, 13.3's text exactly" % tag)
    # The real case: the game is missing a talent the site has (like Crusade).
    r2 = json.loads(json.dumps(raw))
    r2["163"].pop("33")
    set_game_talents(lua, r2, W, {})
    r = prev("warrior/05302~" + wh)
    check(r.error == want_mismatch and r.plan is None, "%s: game missing a talent -> site's hash refused" % tag)
    game({}, 10)
    r = prev("warrior/05302")
    check(r.error is None and r.plan is not None and r.caution == "Older link: can't check it against your talent trees.",
          "%s: no hash -> allowed with 13.3's yellow line" % tag)
    T.locale = "deDE"
    r = prev("warrior/05302~zzzz")
    check(r.error is None and r.plan is not None and r.caution == L.TALENT_HASH_LOCALE,
          "%s: non-English client: mismatch -> 'can't check' caution, not a stop (13.6/13.7)" % tag)
    r = prev("warrior/05302~" + wh)
    check(r.caution is None, "%s: non-English client with a matching hash: no caution" % tag)
    T.locale = "enGB"
    check(prev("warrior/05302~zzzz").error == want_mismatch, "%s: enGB counts as English (strict)" % tag)
    T.locale = None
    lua.execute("local g = GetLocale GetLocale = nil R2F_T = R2F.Talents.Preview('warrior/05302~zzzz') GetLocale = g")
    check(lua.eval("R2F_T.error") == want_mismatch, "%s: no GetLocale -> strict" % tag)
    lua.execute("R2F_T = nil")

    # ---- Sanity checks (always, even with a matching hash) ------------------------
    r = prev("warrior/4~" + wh)
    st = lua_states(r.plan)
    check(r.plan.kind == "conflict" and st["Improved Heroic Strike"][0] == "overmax" and r.plan.learnable is False
          and r.plan.summary == "The link puts 4 points in Improved Heroic Strike, which has only 3 ranks in your game. "
          "Make a new link on the site or wait for the site to update.",
          "%s: rank above max -> red conflict: %r" % (tag, r.plan.summary))
    r = prev("warrior/-00001~" + wh)
    check(r.plan.kind == "conflict" and r.plan.conflicts[1].kind == "nospot" and "your Fury tree" in r.plan.summary,
          "%s: point past the tree's last talent -> conflict: %r" % (tag, r.plan.summary))
    r = prev("warrior/-00000~" + wh)
    check(r.plan.kind != "conflict" and len(r.plan.conflicts) == 0, "%s: zeros past the end are harmless" % tag)
    r = prev("warrior/--5-1~" + wh)
    check(r.plan.kind == "conflict" and r.plan.conflicts[1].kind == "notree", "%s: a 4th tree with points -> conflict" % tag)
    r = prev("warrior/--5--0")
    check(len(r.plan.conflicts) == 0, "%s: empty extra trees are harmless" % tag)

    # ---- The summary line (13.4), every variant ----------------------------------
    prot21 = "warrior/--55155~" + wh            # 5+5+1+5+5 = 21 in Protection
    game({}, 21)
    r = prev(prot21)
    check(r.plan.summary == "This build uses 21 points. You have 21 free. All 21 will be learned."
          and r.plan.kind == "all" and r.plan.learnable is True, "%s: summary 'all' = 13.4 exactly: %r" % (tag, r.plan.summary))
    game({}, 16)
    r = prev(prot21)
    check(r.plan.summary == "This build uses 21 points. You have 16 free: 16 will be learned now, 5 later."
          and r.plan.kind == "partial", "%s: summary 'partial' = 13.4 exactly: %r" % (tag, r.plan.summary))
    game({"Improved Rend": 2}, 21)
    r = prev(prot21)
    check(r.plan.summary == "You already have 2 points in Improved Rend, which this build doesn't use. "
          "Reset your talents at a trainer first." and r.plan.kind == "conflict" and r.plan.learnable is False,
          "%s: summary 'conflict' = 13.4 exactly: %r" % (tag, r.plan.summary))
    game({}, 0)
    r = prev(prot21)
    check(r.plan.summary == "No free talent points." and r.plan.learnable is False, "%s: summary 'no free points'" % tag)
    game({"Shield Specialization": 5}, 0)
    check(prev(prot21).plan.summary == "No free talent points.", "%s: no free points, part learned" % tag)
    game({"Deflection": 5}, 2)
    r = prev("warrior/03302~" + wh)
    check(r.plan.summary == "You have 5 points in Deflection, but this build only uses 3. Reset your talents at a trainer first.",
          "%s: conflict, fewer points than you have: %r" % (tag, r.plan.summary))
    game({"Deflection": 5}, 5)
    r = prev("warrior/05302~" + wh)
    check(r.plan.summary == "This build uses 10 points, 5 of them already learned. You have 5 free. All 5 will be learned.",
          "%s: part of the build already learned: %r" % (tag, r.plan.summary))
    game({"Deflection": 5}, 3)
    check(prev("warrior/05302~" + wh).plan.summary
          == "This build uses 10 points, 5 of them already learned. You have 3 free: 3 will be learned now, 2 later.",
          "%s: part learned + not enough points" % tag)
    game({}, 4)
    check(prev("warrior/1~" + wh).plan.summary == "This build uses 1 point. You have 4 free. It will be learned.",
          "%s: singular wording" % tag)
    check(prev("warrior/~" + wh).plan.summary == "This link has no talent points in it.", "%s: empty build" % tag)
    # Several conflicts: a link problem is named before your own extra points.
    game({"Deflection": 1}, 10)
    r = prev("warrior/4000000002~" + wh)   # IHS 4 > max 3, a 10th Arms talent, Deflection unused
    check(len(r.plan.conflicts) == 3 and r.plan.conflicts[1].kind == "overmax"
          and r.plan.conflicts[3].kind == "unused", "%s: link problems listed first" % tag)

    # ---- Per-talent states (the mini trees) -------------------------------------
    # Game: Improved Heroic Strike 2 (not in build), Deflection 5 (= build),
    # Improved Charge 1 (build 2). Build "05302" + Charge 2 + Fury Cruelty 5,
    # 4 free points: learning order = tier 1 (Arms Rend 3, Fury Cruelty...).
    game({"Improved Heroic Strike": 2, "Deflection": 5, "Improved Charge": 1}, 4)
    r = prev("warrior/05322-05~" + wh)
    st = lua_states(r.plan)
    check(st["Improved Heroic Strike"][0] == "conflict", "%s: points the build doesn't use -> conflict" % tag)
    check(st["Deflection"][0] == "learned", "%s: already learned -> learned" % tag)
    # Tier 1 first: Rend (Arms, col 3) 3, then Cruelty (Fury, col 3) gets 1 of 5.
    check(st["Improved Rend"][:4] == ("now", 3, 3, 0), "%s: Improved Rend all now: %s" % (tag, st["Improved Rend"]))
    check(st["Cruelty"][:4] == ("now", 5, 1, 4), "%s: Cruelty part now, part later: %s" % (tag, st["Cruelty"]))
    check(st["Improved Charge"][:4] == ("later", 2, 0, 1) and st["Tactical Mastery"][:4] == ("later", 2, 0, 2),
          "%s: tier 2 waits (no points left): %s %s" % (tag, st["Improved Charge"], st["Tactical Mastery"]))
    check(st["Booming Voice"][0] == "off" and st["Iron Will"][0] == "off", "%s: not in build -> off" % tag)
    check((r.plan.trees[1].current, r.plan.trees[1].planned, r.plan.trees[2].planned) == (8, 12, 5),
          "%s: tree current -> planned counts" % tag)
    order = lua.eval("function(p) local o = {} for i, e in ipairs(R2F.Talents.LearnOrder(p)) do o[i] = e.name end return o end")
    check(lua_table_to_list(order(r.plan)) == ["Improved Rend", "Cruelty", "Improved Charge", "Tactical Mastery"],
          "%s: learning order tier, then tree, then column (13.5)" % tag)

    # ---- Tree names (GetTalentTabInfo's shapes) -----------------------------------
    names = lambda: [lua.eval("R2F.Talents.TreeName(%d)" % i) for i in (1, 2, 3)]
    check(names() == ["Arms", "Fury", "Protection"], "%s: tree names, Classic shape" % tag)
    T.tabInfoShape = "new"
    check(names() == ["Arms", "Fury", "Protection"], "%s: tree names, id-first shape" % tag)
    T.tabInfoShape = "error"
    check(names() == ["Arms", "Fury", "Protection"], "%s: GetTalentTabInfo error -> our own tree names (15.2)" % tag)
    T.tabInfoShape = None
    lua.execute("R2F_G = GetTalentTabInfo GetTalentTabInfo = nil")
    check(names() == ["Arms", "Fury", "Protection"], "%s: no GetTalentTabInfo -> our own tree names (15.2)" % tag)
    check(lua.eval("R2F.Talents.TreeName(1, 'NOPE')") == "Tree 1", "%s: unknown class -> Tree N" % tag)
    lua.execute("GetTalentTabInfo = R2F_G R2F_G = nil")

    # ---- The Talents tab ------------------------------------------------------------
    T.calls = lua.table()
    T.talentWrites = 0
    game({"Improved Heroic Strike": 2, "Deflection": 5, "Improved Charge": 1}, 4)
    lua.execute("R2F.MainWindow.Show('talents')")
    P = lua.eval("R2F.TalentPanel")
    edit = "R2FTalentLink" if templates else "R2FTalentLinkPlain"
    check(lua.eval("%s ~= nil" % edit) is True, "%s: link box %s (template chain)" % (tag, edit))
    find_frames(lua, "f.__kind == 'Button' and f.__text ~= nil and f.__text ~= ''", "TBTN")
    btn = {}
    for i in range(1, lua.eval("#TBTN") + 1):
        btn[lua.eval("TBTN[%d].__text" % i)] = "TBTN[%d]" % i
    for label in ("Preview", "Copy my build", "Learn talents", "Cancel"):
        check(label in btn, "%s: Talents tab has %r" % (tag, label))
    find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.TALENT_LINK_PLACEHOLDER:format('warrior')", "PH")
    check(lua.eval("#PH") == 1 and lua.eval("PH[1].__shown") is True, "%s: placeholder talents.html#warrior/... shown" % tag)
    check(lua.eval(btn["Learn talents"] + ".__enabled") is False and lua.eval(btn["Cancel"] + ".__enabled") is False,
          "%s: no preview yet: Learn and Cancel disabled" % tag)
    # Before a preview: the character's own trees, rank badges, no build.
    c = lambda t, row, col: "R2F.TalentPanel.Cell(%d, %d, %d)" % (t, row, col)
    check(lua.eval(c(1, 1, 2) + ".rank.__text") == "5" and lua.eval(c(1, 1, 2) + ".__shown") is True,
          "%s: own trees drawn before any preview (Deflection rank 5)" % tag)
    check(lua.eval(c(2, 3, 1) + ".__shown") is False, "%s: empty grid cells hidden" % tag)
    # Paste + Preview.
    lua.execute("%s:SetText(%r)" % (edit, "talents.html#warrior/05322-05~" + wh))
    check(lua.eval("PH[1].__shown") is False, "%s: placeholder hides once there's text" % tag)
    lua.execute(btn["Preview"] + ":Click()")
    summary = find_frames(lua, "f.__kind == 'FontString' and type(f.__text) == 'string' and f.__text:find('^You already have 2 points')", "SUM")
    check(summary == 1, "%s: Preview shows the summary line" % tag)
    check(lua.eval("SUM[1].__color[1]") == 1 and lua.eval("SUM[1].__color[2]") < 0.2, "%s: conflict summary is red" % tag)
    check(lua.eval("R2FCharDB.lastTalentLink") == "talents.html#warrior/05322-05~" + wh, "%s: link remembered per character" % tag)
    # Cells: Arms row 1 = IHS (conflict), Deflection (learned), Rend (now +3);
    # Fury row 1 col 3 = Cruelty (now +1); Arms row 2 col 1 = Charge (later).
    check(lua.eval(c(1, 1, 1) + ".slot.__vertex[1]") == 1 and lua.eval(c(1, 1, 1) + ".slot.__vertex[2]") < 0.2
          and lua.eval(c(1, 1, 1) + ".rank.__text") == "2", "%s: conflict cell: red ring, rank 2" % tag)
    check(lua.eval(c(1, 1, 2) + ".rank.__text") == "5" and lua.eval(c(1, 1, 2) + ".glow.__shown") is False
          and lua.eval(c(1, 1, 2) + ".icon.__desat") is False, "%s: learned cell: rank 5, normal icon" % tag)
    check(lua.eval(c(1, 1, 3) + ".rank.__text") == "+3" and lua.eval(c(1, 1, 3) + ".glow.__shown") is True
          and lua.eval(c(1, 1, 3) + ".rank.__color[3]") == 0, "%s: now cell: gold +3 and glow" % tag)
    # 13.10: columns are ranks of the pane's own distinct posX, and the
    # fixture's (truncated) Fury tree has nothing in Wowhead's column 0, so
    # Cruelty (Wowhead col 2) is drawn in column 2 here, not 3. Cosmetic only:
    # link order / hash / learning order depend on the relative order alone.
    check(lua.eval(c(2, 1, 2) + ".rank.__text") == "+1", "%s: Cruelty now +1" % tag)
    check(lua.eval(c(1, 2, 1) + ".later.__shown") is True and lua.eval(c(1, 2, 1) + ".rank.__text") == "1"
          and lua.eval(c(1, 2, 1) + ".icon.__vertex[1]") < 1, "%s: later cell: 'later', dim, current rank 1" % tag)
    check(lua.eval(c(3, 1, 1) + ".icon.__desat") is True and lua.eval(c(3, 1, 1) + ".badge.__shown") is False,
          "%s: not-in-build cell desaturated, no badge" % tag)
    find_frames(lua, "f.__kind == 'FontString' and f.__text == '8 -> 12'", "HEAD")
    check(lua.eval("#HEAD") == 1, "%s: Arms header '8 -> 12'" % tag)
    find_frames(lua, "f.__kind == 'FontString' and f.__text == 'Arms'", "HN")
    check(lua.eval("#HN") >= 1, "%s: tree name header from GetTalentTabInfo" % tag)
    check(lua.eval(btn["Learn talents"] + ".__enabled") is False and lua.eval(btn["Cancel"] + ".__enabled") is True,
          "%s: conflict: Learn disabled, Cancel enabled" % tag)
    # Hover: the game's tooltip + "Build: x / y". 13.10: talents carry their
    # spell id from C_Traits, so it's SetSpellByID(spellID), never
    # SetTalent(tab, index) (our index isn't Classic's any more).
    lua.execute("GameTooltip.talentArgs = nil " + c(1, 1, 2) + ":Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    sid = lua.eval(c(1, 1, 2) + ".entry.spellID")
    args = lua_table_to_list(lua.eval("GameTooltip.spellArgs"))
    check(sid is not None and args == [sid] and lines[0] == "Deflection",
          "%s: SetSpellByID(spell id %s): %s" % (tag, sid, args))
    check(lua.eval("GameTooltip.talentArgs") is None, "%s: SetTalent not used for C_Traits talents" % tag)
    check("Build: 5 / 5" in lines, "%s: tooltip 'Build: 5 / 5': %s" % (tag, lines))
    lua.execute(c(1, 1, 3) + ":Fire('OnEnter')")
    check("Learned now: +3" in lua_table_to_list(lua.eval("GameTooltip.lines")), "%s: tooltip says +3 now" % tag)
    lua.execute("GameTooltip.SetSpellByID = function() error('other signature') end " + c(1, 1, 2) + ":Fire('OnEnter')")
    check(lua_table_to_list(lua.eval("GameTooltip.lines"))[0] == "Deflection", "%s: SetSpellByID error -> name line" % tag)
    lua.execute("GameTooltip.SetSpellByID = nil " + c(1, 1, 2) + ":Fire('OnEnter')")
    check(lua_table_to_list(lua.eval("GameTooltip.lines"))[0] == "Deflection", "%s: no SetSpellByID -> name line" % tag)
    lua.execute("GameTooltip.SetTalent = nil")
    # A learnable build: since step 10 Learn talents is enabled (13.8).
    game({}, 21)
    lua.execute("%s:SetText(%r) %s.__scripts.OnEnterPressed(%s)" % (edit, prot21, edit, edit))
    res = P.Result()
    check(res.plan.learnable is True and lua.eval(btn["Learn talents"] + ".__enabled") is True,
          "%s: learnable build -> Learn talents enabled (step 10)" % tag)
    find_frames(lua, "f.__kind == 'FontString' and f.__text == 'This build uses 21 points. You have 21 free. All 21 will be learned.'", "S21")
    check(lua.eval("#S21") == 1 and lua.eval("S21[1].__color[1]") == 1 and lua.eval("S21[1].__color[2]") == 1,
          "%s: Enter previews too; non-conflict summary white" % tag)
    lua.execute(btn["Learn talents"] + ".__scripts.OnEnter(%s)" % btn["Learn talents"])
    check(lua_table_to_list(lua.eval("GameTooltip.lines")) == [L.TALENT_LEARN_TIP], "%s: Learn tooltip explains it" % tag)
    # Points spent elsewhere: the preview follows CHARACTER_POINTS_CHANGED.
    game({"Shield Specialization": 5}, 16)
    T.fire("CHARACTER_POINTS_CHANGED")
    T.runTimers()
    check(P.Result().plan.summary == "This build uses 21 points, 5 of them already learned. You have 16 free. All 16 will be learned.",
          "%s: preview re-read on CHARACTER_POINTS_CHANGED: %r" % (tag, P.Result().plan.summary))
    # Caution line (old link) in yellow; stop messages in red with the own trees.
    lua.execute("%s:SetText('warrior/--55155') %s:Click()" % (edit, btn["Preview"]))
    find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.TALENT_NO_HASH", "CAU")
    check(lua.eval("#CAU") == 1 and lua.eval("CAU[1].__color[2]") == 0.82, "%s: old link: yellow caution line" % tag)
    lua.execute("%s:SetText('warrior/--55155~zzzz') %s:Click()" % (edit, btn["Preview"]))
    find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.TALENT_HASH_MISMATCH", "ERR")
    check(lua.eval("#ERR") == 1 and lua.eval("ERR[1].__color[2]") < 0.2 and P.Result().plan is None,
          "%s: hash mismatch: red stop line, no plan" % tag)
    check(lua.eval(c(3, 1, 1) + ".rank.__text") == "5" and lua.eval(c(3, 1, 1) + ".glow.__shown") is False,
          "%s: behind a stop: own trees, no build" % tag)
    check(lua.eval("S21[1].__text") == "", "%s: no summary behind a stop" % tag)
    lua.execute("%s:SetText('paladin/5') %s:Click()" % (edit, btn["Preview"]))
    find_frames(lua, "f.__kind == 'FontString' and f.__text == \"This is a Paladin build. You're playing a Warrior.\"", "WC")
    check(lua.eval("#WC") == 1, "%s: wrong class shown on the tab" % tag)
    check(lua.eval("R2FCharDB.lastTalentLink") == "paladin/5", "%s: parsable link remembered even if refused" % tag)
    lua.execute("%s:SetText('garbage') %s:Click()" % (edit, btn["Preview"]))
    check(lua.eval("R2FCharDB.lastTalentLink") == "paladin/5", "%s: junk isn't remembered" % tag)
    # Cancel: back to the own trees, box and memory cleared.
    lua.execute(btn["Cancel"] + ":Click()")
    check(lua.eval(edit + ":GetText()") == "" and lua.eval("R2FCharDB.lastTalentLink") is None
          and P.Result() is None and lua.eval(btn["Cancel"] + ".__enabled") is False, "%s: Cancel clears" % tag)
    # Empty Preview = Cancel.
    lua.execute("%s:SetText('   ') %s:Click()" % (edit, btn["Preview"]))
    check(P.Result() is None, "%s: Preview with an empty box clears" % tag)
    # Copy my build button (step 8's function).
    lua.execute(btn["Copy my build"] + ":Click()")
    check(lua.eval("R2FCopy:IsShown()") is True and lua.eval("R2FCopy.edit:GetText()").startswith(SITE_TALENTS + "warrior/--5~"),
          "%s: Copy my build button opens the copy box with the link" % tag)
    lua.execute("R2FCopy:Hide()")

    # ---- Read-only, combat ---------------------------------------------------------
    T.combat = True
    T.fire("PLAYER_REGEN_DISABLED")
    game({}, 21)
    T.combat = True
    lua.execute("%s:SetText(%r)" % (edit, prot21))
    check(lua.eval(btn["Preview"] + ".__enabled") is True, "%s: Preview not greyed out in combat (read-only)" % tag)
    lua.execute(btn["Preview"] + ":Click()")
    check(P.Result() is not None and P.Result().plan is not None, "%s: Preview works in combat" % tag)
    lua.execute(btn["Copy my build"] + ":Click() R2FCopy:Hide()")
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")
    check(lua.eval("TEST.talentWrites") == 0, "%s: Preview / Cancel / Copy never call LearnTalent or the preview API" % tag)
    check(len(lua_table_to_list(T.calls)) == 0, "%s: no macro API writes from the Talents tab" % tag)
    # Tab switch lets go of the keyboard.
    lua.execute("R2F.MainWindow.SelectTab('home')")
    check(lua.eval("R2F.MainWindow.CurrentTab()") == "home", "%s: leaving the Talents tab works" % tag)

    # ---- Globals ---------------------------------------------------------------------
    new_globals = lua.eval("""(function()
      local out = {}
      for k in pairs(_G) do if not BEFORE[k] then table.insert(out, k) end end
      table.sort(out) return table.concat(out, ",") end)()""").split(",")
    test_vars = {"NS", "TBTN", "PH", "SUM", "HEAD", "HN", "S21", "CAU", "ERR", "WC"}
    bad = [g for g in new_globals if g and g not in test_vars and g not in BINDING_GLOBALS
           and g not in ("SLASH_R2F1", "SLASH_R2FT1") and not g.startswith("R2F")]
    check(not bad, "%s: step 9 adds no globals besides R2F* frames: %s" % (tag, bad))

    # ---- The last link comes back in a new session (6.3 lastTalentLink) ---------------
    lua2 = new_runtime(templates)
    lua2.execute("R2FCharDB = { lastTalentLink = %r }" % prot21)
    T2 = lua2.eval("TEST")
    T2.fire("ADDON_LOADED", "RoadToForever")
    T2.fire("PLAYER_LOGIN")
    lua2.execute("TEST.tabNames = { 'Arms', 'Fury', 'Protection' }")
    set_game_talents(lua2, raw, W, {})
    T2.talentPoints = 21
    lua2.execute("R2F.MainWindow.Show('talents')")
    check(lua2.eval(edit + ":GetText()") == prot21
          and lua2.eval("R2F.TalentPanel.Result().plan.summary") == "This build uses 21 points. You have 21 free. All 21 will be learned.",
          "%s: last link restored and previewed after a reload" % tag)
    lua2.execute("R2FCharDB.lastTalentLink = 42 R2F.Library.Init()")
    check(lua2.eval("R2FCharDB.lastTalentLink") is None, "%s: Init drops a non-string lastTalentLink" % tag)


class LearnCtx:
    """One fresh client + the Talents tab, for the step-10 learning tests."""

    def __init__(self, templates, ranks, points, link, raw, warrior, setup=None):
        self.lua = lua = new_runtime(templates)
        if setup:
            lua.execute(setup)
        self.T = T = lua.eval("TEST")
        T.fire("ADDON_LOADED", "RoadToForever")
        T.fire("PLAYER_LOGIN")
        lua.execute("TEST.tabNames = { 'Arms', 'Fury', 'Protection' }")
        set_game_talents(lua, raw, warrior, ranks)
        T.talentPoints = points
        lua.execute("R2F.MainWindow.Show('talents')")
        self.edit = "R2FTalentLink" if templates else "R2FTalentLinkPlain"
        find_frames(lua, "f.__kind == 'Button' and f.__text ~= nil and f.__text ~= ''", "LBTN")
        self.btn = {}
        for i in range(1, lua.eval("#LBTN") + 1):
            self.btn.setdefault(lua.eval("LBTN[%d].__text" % i), "LBTN[%d]" % i)
        self.learn, self.cancel = self.btn["Learn talents"], self.btn["Cancel"]
        self.previewb, self.copy = self.btn["Preview"], self.btn["Copy my build"]
        find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.TALENT_TAB_HINT", "LHINT")
        if link:
            self.preview(link)

    def preview(self, link):
        self.lua.execute("%s:SetText(%r) %s:Click()" % (self.edit, link, self.previewb))

    def ev(self, expr):
        return self.lua.eval(expr)

    def enabled(self, b):
        return self.ev(b + ".__enabled")

    def text(self, b):
        return self.ev(b + ".__text")

    def click(self, b):
        self.lua.execute(b + ":Click()")

    def popup(self):
        """Text of the confirm dialog if it's showing, else None."""
        if self.ev("R2FConfirm ~= nil and R2FConfirm:IsShown()"):
            return self.ev("R2FConfirm.text.__text")
        return None

    def accept(self):
        self.lua.execute("R2FConfirm.yes:Click()")

    def status(self):
        return self.ev("R2F.Talents.LearnStatus()")

    def calls(self):
        return [self.ev("(function() local t, i = TEST.learnCalls[%d]:match('(%%d+):(%%d+)')"
                        " return TEST.talentTabs[tonumber(t)][tonumber(i)].name end)()" % k)
                for k in range(1, self.ev("#TEST.learnCalls") + 1)]

    def rank(self, name):
        return self.ev("(function() for _, l in ipairs(TEST.talentTabs) do for _, x in ipairs(l) do "
                       "if x.name == %r then return x.rank end end end end)()" % name)

    def index_of(self, name):
        return self.ev("(function() for t, l in ipairs(TEST.talentTabs) do for i, x in ipairs(l) do "
                       "if x.name == %r then return i end end end end)()" % name)

    def chat(self):
        return chat_lines(self.lua)

    def said(self, text):
        return any(c.endswith(text) for c in self.chat())

    def status_line(self):
        n = find_frames(self.lua, "f.__kind == 'FontString' and f.__color ~= nil and type(f.__text) == 'string'"
                        " and (f.__text:find('^Stopped') or f.__text:find('^Learned') or f.__text:find('^The point')"
                        " or f.__text:find('^added'))", "LST")
        return [self.ev("LST[%d].__text" % i) for i in range(1, n + 1)]

    def combat(self, on):
        self.T.combat = on
        self.T.fire("PLAYER_REGEN_DISABLED" if on else "PLAYER_REGEN_ENABLED")


def test_talent_learning(templates):
    """Step 10: the learning engine (13.5) driven through the real Talents tab
    against a fake server (wow_stubs.lua: LearnTalent only sends; T.server()
    answers with Classic's rules and fires CHARACTER_POINTS_CHANGED)."""
    tag = "templates" if templates else "fallbacks"
    fxt = json.load(open(TALENT_FIXTURE, encoding="utf-8"))
    raw = fxt["talents"]
    js = talent_js()
    W = js["classes"]["warrior"]
    wh = js["hashes"]["warrior"]
    deep = fxt["scenarios"][5]                 # Deflection 5, TM 5, AM 1, BV 5, SS 1 = 17
    link = "%swarrior/%s~%s" % (SITE_TALENTS, deep["code"], wh)
    order17 = (["Deflection"] * 5 + ["Booming Voice"] * 5 + ["Shield Specialization"]
               + ["Tactical Mastery"] * 5 + ["Anger Management"])
    ctx = lambda ranks, pts, lnk=link, setup=None: LearnCtx(templates, ranks, pts, lnk, raw, W, setup)
    STOP_COMBAT = "Stopped: you entered combat. %d of %d learned. Click Learn talents to continue."

    # ---- Order: exactly step 9's LearnOrder, expanded per point ---------------------
    c = ctx({}, 17)
    lp = c.ev("(function() local o = {} for i, p in ipairs(R2F.Talents.LearnPoints(R2F.TalentPanel.Result().plan))"
              " do o[i] = p.name .. '>' .. p.target end return o end)()")
    names = [s.split(">")[0] for s in lua_table_to_list(lp)]
    check(names == order17, "%s: learn points = tier, then tree, then column, one per point: %s" % (tag, names))
    via9 = c.ev("(function() local o = {} for _, e in ipairs(R2F.Talents.LearnOrder(R2F.TalentPanel.Result().plan))"
                " do for _ = 1, e.now do o[#o + 1] = e.name end end return o end)()")
    check(lua_table_to_list(via9) == names, "%s: the same list step 9's preview hands 'now' points from" % tag)
    # Independent Python derivation from the fixture (tier, then tab, then column).
    py = []
    for t, tid in enumerate(W, start=1):
        for x in raw[str(tid)].values():
            py += [(x["row"], t, x["col"], x["name"])] * deep["ranks"].get(x["name"], 0)
    check([p[3] for p in sorted(py)] == names, "%s: order matches an independent Python sort" % tag)
    check([s.split(">")[1] for s in lua_table_to_list(lp)][:5] == ["1", "2", "3", "4", "5"],
          "%s: targets count up per talent" % tag)

    # ---- Popup: the 13.4 text; Cancel learns nothing ----------------------------------
    check(c.enabled(c.learn) is True and c.text(c.learn) == "Learn talents", "%s: learnable -> Learn enabled" % tag)
    c.click(c.learn)
    check(c.popup() == "Learn 17 talent points? Only a trainer reset can undo this.",
          "%s: confirm popup text = 13.4: %r" % (tag, c.popup()))
    check(c.ev("R2FConfirm.yes.__text") == "Learn" and c.ev("R2FConfirm.no.__text") == "Cancel", "%s: [Learn] [Cancel]" % tag)
    c.lua.execute("R2FConfirm.no:Click()")
    check(c.ev("TEST.talentWrites") == 0 and c.status().phase == "idle", "%s: popup Cancel learns nothing" % tag)

    # ---- A full run, point by point --------------------------------------------------
    c.T.calls = c.lua.table()
    c.click(c.learn)
    c.accept()
    check(c.calls() == ["Deflection"] and c.status().phase == "learning", "%s: Learn -> exactly one point sent" % tag)
    check(c.text(c.learn) == "Learning 1 / 17" and c.enabled(c.learn) is False, "%s: label 'Learning 1 / 17'" % tag)
    check(c.enabled(c.previewb) is False and c.enabled(c.copy) is False and c.ev(c.edit + ".__enabled") is False,
          "%s: link box, Preview, Copy my build locked while learning" % tag)
    check(c.text(c.cancel) == "Stop" and c.enabled(c.cancel) is True, "%s: Cancel turns into Stop" % tag)
    first = c.ev("TEST.learnCalls[1]")
    check(first == "1:%d" % c.index_of("Deflection"), "%s: LearnTalent(tab, CLIENT index): %s" % (tag, first))
    c.T.server(1)
    check(c.calls() == ["Deflection"] * 2 and c.text(c.learn) == "Learning 2 / 17",
          "%s: next point only after the server's answer: %s" % (tag, c.text(c.learn)))
    labels = []
    while c.ev("#TEST.learnQueue") > 0:
        c.T.server(1)
        labels.append(c.text(c.learn))
    check(c.calls() == order17, "%s: the whole run sends the plan's points in order" % tag)
    check(labels[:3] == ["Learning 3 / 17", "Learning 4 / 17", "Learning 5 / 17"] and labels[-1] == "Learn talents",
          "%s: label counts up, back to 'Learn talents' at the end: %s" % (tag, labels[-3:]))
    check(all(c.rank(n) == v for n, v in deep["ranks"].items()) and c.ev("TEST.talentPoints") == 0,
          "%s: the game now has exactly the build" % tag)
    check(c.said("Learned 17 talent points.") and c.status().phase == "done", "%s: 'Learned 17 talent points.' in chat" % tag)
    check("Learned 17 talent points." in c.status_line(), "%s: done line on the tab" % tag)
    check(c.ev("R2F.TalentPanel.Cell(1, 3, 2).rank.__text") == "1", "%s: trees refreshed (Anger Management rank 1)" % tag)
    check(c.ev("R2F.TalentPanel.Result().plan.summary") == "You already have this whole build."
          and c.enabled(c.learn) is False, "%s: afterwards: whole build, Learn disabled" % tag)
    check(c.enabled(c.previewb) is True and c.ev(c.edit + ".__enabled") is True and c.text(c.cancel) == "Cancel",
          "%s: tab unlocked after the run" % tag)
    nchat = len(c.chat())
    c.T.runTimers()
    check(len(c.chat()) == nchat and c.status().phase == "done", "%s: stale timeouts after success do nothing" % tag)
    check(len(lua_table_to_list(c.T.calls)) == 0, "%s: no macro API calls while learning talents" % tag)

    # ---- Fewer free points: only the 'now' points, then 'No free talent points.' ----------
    c = ctx({}, 12)
    c.click(c.learn)
    check(c.popup() == "Learn 12 talent points? Only a trainer reset can undo this.", "%s: popup counts the 'now' points" % tag)
    c.accept()
    c.T.server()
    check(c.calls() == order17[:12] and c.said("Learned 12 talent points."), "%s: partial build: first 12 in order" % tag)
    check(c.ev("R2F.TalentPanel.Result().plan.summary") == "No free talent points.", "%s: then no free points" % tag)
    # A level-up later: Learn again picks up the rest (new popup, new run).
    c.T.talentPoints = 5
    c.T.fire("PLAYER_LEVEL_UP")
    c.T.runTimers()
    check(c.enabled(c.learn) is True, "%s: level-up -> Learn enabled for the rest" % tag)
    c.click(c.learn)
    check(c.popup() == "Learn 5 talent points? Only a trainer reset can undo this.", "%s: second popup for the rest" % tag)
    c.accept()
    c.T.server()
    check(c.calls() == order17 and c.said("Learned 5 talent points."), "%s: the rest learned in order" % tag)
    c = ctx({}, 1, "warrior/1~" + wh)
    c.click(c.learn)
    check(c.popup() == "Learn 1 talent point? Only a trainer reset can undo this.", "%s: singular popup" % tag)
    c.accept()
    c.T.server()
    check(c.said("Learned 1 talent point."), "%s: singular done line" % tag)

    # ---- Learn only enabled with zero conflicts ---------------------------------------
    cases = [
        ({"Improved Rend": 2}, 17, link, False),                    # points the build doesn't use
        ({}, 17, "warrior/4~" + wh, False),                          # over max rank
        ({}, 17, "warrior/-00001~" + wh, False),                     # no such talent
        ({}, 17, "warrior/--5-1~" + wh, False),                      # no such tree
        ({}, 0, link, False),                                        # no free points
        (deep["ranks"], 3, link, False),                             # whole build already learned
        ({}, 17, "warrior/~" + wh, False),                           # empty link
        ({}, 17, "warrior/05005001-5-1~zzzz", False),                # hash mismatch (stop, no plan)
        ({}, 17, link, True),
        ({"Deflection": 5}, 2, link, True),                          # part learned, part free
        ({}, 17, "warrior/05005001-5-1", True),                      # old link (caution) still learnable
    ]
    for ranks, pts, lnk, want in cases:
        c = ctx(ranks, pts, lnk)
        res = c.ev("R2F.TalentPanel.Result()")
        plan = res.plan
        zero = plan is not None and len(plan.conflicts) == 0
        check(c.enabled(c.learn) is want and (not want or zero),
              "%s: Learn enabled=%s for %s / %s free (conflicts: %s)" % (tag, want, lnk, pts, None if plan is None else len(plan.conflicts)))
        if not want:
            c.lua.execute("R2F.TalentPanel.Learn()")       # even called directly
            check(c.popup() is None and c.ev("TEST.talentWrites") == 0, "%s: no popup, no write for %s" % (tag, lnk))

    # ---- A refused point: stop at once, the exact message, nothing after it ----------
    c = ctx({}, 17)
    c.click(c.learn)
    c.accept()
    c.T.server(3)
    c.T.serverRejects = True
    c.T.server()
    c.T.runTimers()
    want = "Stopped at Deflection: the game didn't accept the point. 3 of 17 learned."
    check(c.status().phase == "stopped" and c.said(want), "%s: refused point -> 13.5's message: %s" % (tag, c.chat()[-1:]))
    check(want in c.status_line(), "%s: stop line on the tab (red)" % tag)
    check(len(c.calls()) == 4, "%s: nothing sent past the refused point" % tag)
    c.T.fire("CHARACTER_POINTS_CHANGED")
    c.T.runTimers()
    check(len(c.calls()) == 4, "%s: stays stopped on later events / timers" % tag)
    check(c.ev("R2F.Talents.LearnMode()") == "direct", "%s: LearnTalent worked earlier -> no guided mode" % tag)
    check(c.text(c.learn) == "Learn talents" and c.enabled(c.learn) is True and c.enabled(c.previewb) is True,
          "%s: stopped: tab unlocked, Learn enabled" % tag)
    check(c.ev("R2F.Talents.CanResume(%r)" % link) is True and c.ev("R2F.Talents.CanResume('warrior/05~%s')" % wh) is False,
          "%s: a stopped run only resumes for its own link" % tag)
    c.T.serverRejects = False
    c.click(c.learn)
    check(c.popup() is None and c.text(c.learn) == "Learning 4 / 17", "%s: Learn continues the stopped run, no popup" % tag)
    check(len(c.calls()) == 4, "%s: the refused point isn't re-sent before its wait is over" % tag)
    c.T.runTimersOnce()
    check(len(c.calls()) == 5, "%s: ... then sent again once" % tag)
    c.T.server()
    check(c.calls() == order17[:3] + ["Deflection"] + order17[3:] and c.said("Learned 17 talent points."),
          "%s: resumed run finishes: 17 of 17" % tag)
    # LearnTalent raising (an error inside the client call) = refused too.
    c = ctx({}, 17)
    c.T.learnError = "some client error"
    c.click(c.learn)
    c.accept()
    check(c.said("Stopped at Deflection: the game didn't accept the point. 0 of 17 learned. "
                 + c.ev("R2F.L.TALENT_BLOCKED_HINT")), "%s: LearnTalent error -> refused, guided hint" % tag)

    # ---- Combat mid-run: stop at once, count the point in flight, resume ----------------
    c = ctx({}, 17)
    c.click(c.learn)
    c.accept()
    c.T.server(5)                                  # 5 landed, the 6th is on its way
    writes = c.ev("TEST.talentWrites")
    c.combat(True)
    check(c.said(STOP_COMBAT % (5, 17)) and c.status().phase == "stopped",
          "%s: combat -> 13.5's message at once: %s" % (tag, c.chat()[-1:]))
    check(c.enabled(c.learn) is False, "%s: Learn greyed out in combat" % tag)
    c.lua.execute("%s.__scripts.OnEnter(%s)" % (c.learn, c.learn))
    check(lua_table_to_list(c.ev("GameTooltip.lines")) == [c.ev("R2F.L.TALENT_LEARN_COMBAT")], "%s: combat tooltip" % tag)
    c.T.server()                                   # the 6th lands after all
    check(c.said(STOP_COMBAT % (6, 17)), "%s: the point in flight is counted when it lands" % tag)
    c.T.runTimers()
    c.lua.execute("R2F.TalentPanel.Learn()")
    check(c.ev("TEST.talentWrites") == writes and c.popup() is None, "%s: nothing sent in combat, Learn() refuses" % tag)
    c.combat(False)
    check(c.enabled(c.learn) is True, "%s: Learn back after combat" % tag)
    c.click(c.learn)
    check(c.popup() is None and c.text(c.learn) == "Learning 7 / 17", "%s: resume after combat from 7 / 17" % tag)
    c.T.server()
    check(c.calls() == order17 and c.said("Learned 17 talent points."), "%s: resumed run completes in order" % tag)
    # Combat starting between the answer and the next send: R2F.inCombat is set
    # before the event reaches us, and the stub raises if LearnTalent runs in combat.
    c = ctx({}, 17)
    c.click(c.learn)
    c.accept()
    c.lua.execute("R2F.inCombat = true")
    c.T.server(1)
    check(c.said(STOP_COMBAT % (1, 17)) and len(c.calls()) == 1, "%s: combat flag checked before every send" % tag)

    # ---- Popup accepted in combat: queued (RunOrQueue), starts after combat -----------
    c = ctx({}, 17)
    c.click(c.learn)
    c.combat(True)
    c.accept()
    check(c.ev("TEST.talentWrites") == 0 and c.status().phase == "queued" and c.said(c.ev("R2F.L.TALENT_LEARN_QUEUED")),
          "%s: accepted in combat -> queued, nothing sent" % tag)
    check(c.text(c.learn) == "After combat" and c.text(c.cancel) == "Stop", "%s: queued label" % tag)
    c.combat(False)
    check(c.calls() == ["Deflection"] and c.status().phase == "learning", "%s: starts on PLAYER_REGEN_ENABLED" % tag)
    c.T.server()
    check(c.said("Learned 17 talent points."), "%s: queued run completes" % tag)
    c = ctx({}, 17)
    c.click(c.learn)
    c.combat(True)
    c.accept()
    c.click(c.cancel)                              # Stop while queued
    c.combat(False)
    check(c.ev("TEST.talentWrites") == 0 and c.status().phase == "idle", "%s: Stop while queued -> nothing after combat" % tag)

    # ---- Stop button mid-run; late answer; resume -----------------------------------------
    c = ctx({}, 17)
    c.click(c.learn)
    c.accept()
    c.T.server(2)
    c.click(c.cancel)
    check(c.said("Stopped. 2 of 17 learned. Click Learn talents to continue."), "%s: Stop -> message" % tag)
    c.T.server()
    check(c.said("Stopped. 3 of 17 learned. Click Learn talents to continue.") and len(c.calls()) == 3,
          "%s: the point already sent is counted, nothing new sent" % tag)
    c.click(c.learn)
    c.T.server()
    check(c.calls() == order17 and c.said("Learned 17 talent points."), "%s: resume after Stop" % tag)
    # Stop with a point in flight, Learn clicked AT ONCE: the point must not be
    # sent twice (both could land: a rank more than the build, irreversible).
    # Shield Specialization is a 1-point talent in this build: a double send
    # would make it 2 / 1.
    c = ctx({}, 17)
    c.click(c.learn)
    c.accept()
    c.T.server(10)                                 # Shield Specialization (11th) is in flight
    check(c.calls()[-1] == "Shield Specialization", "%s: (setup) Shield Specialization in flight" % tag)
    c.click(c.cancel)
    c.click(c.learn)
    check(c.calls().count("Shield Specialization") == 1 and c.status().phase == "learning",
          "%s: resume right after Stop waits for the point in flight, doesn't resend it" % tag)
    c.T.server()                                   # it lands, then the rest follows
    c.T.runTimers()
    check(c.calls() == order17 and c.rank("Shield Specialization") == 1
          and all(c.rank(n) == v for n, v in deep["ranks"].items()) and c.said("Learned 17 talent points."),
          "%s: no double send: exactly the build, Shield Specialization 1 / 1" % tag)
    # Same, but the point really was lost: resent once after the wait.
    c = ctx({}, 17)
    c.click(c.learn)
    c.accept()
    c.T.server(10)
    c.click(c.cancel)
    c.lua.execute("TEST.learnQueue = {}")          # the request never reached the server
    c.click(c.learn)
    c.T.runTimersOnce()
    check(c.calls().count("Shield Specialization") == 2, "%s: a lost point is sent again after the wait" % tag)
    c.T.server()
    check(c.calls().count("Shield Specialization") == 2 and c.said("Learned 17 talent points.")
          and c.rank("Shield Specialization") == 1, "%s: ... and the run completes with the exact build" % tag)
    # Window closed mid-run: the run doesn't depend on the tab.
    c = ctx({}, 17)
    c.click(c.learn)
    c.accept()
    c.lua.execute("R2F.MainWindow.Hide()")
    c.T.server()
    check(c.said("Learned 17 talent points."), "%s: run finishes with the window closed" % tag)
    # Another link after a stop: the old run is dropped, Learn asks again.
    c = ctx({}, 17)
    c.click(c.learn)
    c.accept()
    c.T.server(2)
    c.click(c.cancel)
    c.T.server()
    c.preview("warrior/05~" + wh)
    check(c.status().phase == "idle" and c.status_line() == [], "%s: new link -> stopped run and its line dropped" % tag)
    c.click(c.learn)
    check(c.popup() == "Learn 2 talent points? Only a trainer reset can undo this.", "%s: new link -> new popup" % tag)
    c.lua.execute("R2FConfirm.no:Click()")
    c.lua.execute(c.cancel + ":Click()")
    check(c.status().phase == "idle", "%s: Cancel resets" % tag)
    # Popup open, link changed before accepting: nothing happens.
    c = ctx({}, 17)
    c.click(c.learn)
    c.preview("warrior/05~" + wh)
    c.accept()
    check(c.ev("TEST.talentWrites") == 0 and c.status().phase == "idle", "%s: link changed under the popup -> nothing" % tag)

    # ---- Re-verification before each point --------------------------------------------
    # Prerequisite not maxed (a link the site wouldn't make): stopped BEFORE the write.
    c = ctx({"Improved Heroic Strike": 2, "Deflection": 5, "Improved Rend": 3}, 1, "warrior/25300001~" + wh)
    check(c.enabled(c.learn) is True, "%s: AM without Tactical Mastery: plan itself is 'learnable'" % tag)
    c.click(c.learn)
    c.accept()
    check(c.said("Stopped at Anger Management: its tier or prerequisite isn't met in your game. 0 of 1 learned.")
          and c.ev("TEST.talentWrites") == 0, "%s: GetTalentPrereqs re-check stops before LearnTalent" % tag)
    c.click(c.learn)
    check(c.popup() is not None, "%s: a tier/prerequisite stop isn't resumable (new popup)" % tag)
    c.lua.execute("R2FConfirm.no:Click()")
    # Same without GetTalentPrereqs: the server refuses, the rank re-read stops it.
    c = ctx({"Improved Heroic Strike": 2, "Deflection": 5, "Improved Rend": 3}, 1, "warrior/25300001~" + wh,
            setup="GetTalentPrereqs = nil")
    c.click(c.learn)
    c.accept()
    c.T.server()
    c.T.runTimers()
    check(len(c.calls()) == 1 and c.said("Stopped at Anger Management: the game didn't accept the point. 0 of 1 learned. "
                                         + c.ev("R2F.L.TALENT_BLOCKED_HINT")),
          "%s: no GetTalentPrereqs -> server refusal caught by the rank re-read" % tag)
    # Tier requirement (Improved Charge, tier 2, no prerequisite, 0 points in Arms).
    c = ctx({}, 1, "warrior/0001~" + wh)
    c.click(c.learn)
    c.accept()
    check(c.said("Stopped at Improved Charge: its tier or prerequisite isn't met in your game. 0 of 1 learned.")
          and c.ev("TEST.talentWrites") == 0, "%s: tier re-check stops before LearnTalent" % tag)
    c = ctx({}, 1, "warrior/00000001~" + wh)
    c.click(c.learn)
    c.accept()
    check(c.said("Stopped at Anger Management: its tier or prerequisite isn't met in your game. 0 of 1 learned.")
          and c.ev("TEST.talentWrites") == 0, "%s: tier 3 + missing prerequisite stops before LearnTalent" % tag)
    # A prerequisite that changes MID-run (live GetTalentPrereqs, not the plan).
    c = ctx({}, 17)
    c.click(c.learn)
    c.accept()
    c.T.server(10)
    c.lua.execute("for _, x in ipairs(TEST.talentTabs[1]) do if x.name == 'Anger Management' then x.prereq = { 1, 1 } end end")
    c.T.server()
    check(c.said("Stopped at Anger Management: its tier or prerequisite isn't met in your game. 16 of 17 learned.")
          and len(c.calls()) == 16, "%s: prerequisite unmet mid-run -> stop before that point, no error" % tag)
    # Player spends a point elsewhere mid-run -> conflict -> stop.
    c = ctx({}, 17)
    c.click(c.learn)
    c.accept()
    c.T.server(3)
    c.T.playerLearn(1, c.index_of("Improved Heroic Strike"))
    c.T.server()
    check(c.said("Stopped: your talents changed while learning. 4 of 17 learned. Check the preview, then click Learn talents again."),
          "%s: a point outside the build mid-run -> stop: %s" % (tag, c.chat()[-1:]))
    check(c.enabled(c.learn) is False, "%s: ... and the conflict keeps Learn disabled" % tag)
    # Player spends a build point in Blizzard's window mid-run -> skipped, still 17.
    c = ctx({}, 17)
    c.click(c.learn)
    c.accept()
    c.T.server(3)
    c.T.playerLearn(3, c.index_of("Shield Specialization"))
    c.T.server()
    check(c.said("Learned 17 talent points.") and c.rank("Shield Specialization") == 1
          and len(c.calls()) == 16, "%s: a build point spent elsewhere is skipped, not learned twice" % tag)
    # Free points gone mid-run.
    c = ctx({}, 17)
    c.click(c.learn)
    c.accept()
    c.T.server(2)
    c.T.talentPoints = 1                           # e.g. spent elsewhere; the point in flight uses the last one
    c.T.server()
    check(c.said("Stopped: no free talent points left. 3 of 17 learned."), "%s: no free points left -> stop: %s" % (tag, c.chat()[-1:]))

    # ---- Timing: the 0.5 s timeout, a late answer, no C_Timer --------------------------
    c = ctx({}, 17)
    check(c.ev("R2F.Talents.LEARN_TIMEOUT") == 0.5, "%s: timeout 0.5 s (13.5)" % tag)
    c.click(c.learn)
    c.accept()
    c.T.fire("CHARACTER_POINTS_CHANGED")           # e.g. a level-up: rank unchanged
    check(c.status().phase == "learning", "%s: an unrelated CHARACTER_POINTS_CHANGED doesn't stop the run" % tag)
    c.T.runTimers()                                # timeout before the answer
    check(c.ev("R2F.Talents.LearnMode()") == "guided", "%s: first point refused, never worked -> guided suspected" % tag)
    c.T.server()                                   # the answer was only slow
    check(c.said("The point in Deflection arrived late after all. 1 of 17 learned. Click Learn talents to continue.")
          and c.ev("R2F.Talents.LearnMode()") == "direct", "%s: late answer -> counted, back to direct mode" % tag)
    c.click(c.learn)
    c.T.server()
    check(c.said("Learned 17 talent points.") and len(c.calls()) == 17, "%s: resumes after the late answer" % tag)
    c = ctx({}, 17, setup="C_Timer = nil")
    c.click(c.learn)
    c.accept()
    c.T.server()
    check(c.said("Learned 17 talent points."), "%s: no C_Timer: event-driven run still completes" % tag)
    c = ctx({}, 17, setup="C_Timer = nil")
    c.click(c.learn)
    c.accept()
    c.T.serverRejects = True
    c.T.server()
    check(c.status().phase == "learning" and c.enabled(c.cancel) is True, "%s: no C_Timer, no answer: waiting, Stop available" % tag)
    c.T.fire("CHARACTER_POINTS_CHANGED")
    check(c.status().phase == "stopped" and c.said("Stopped at Deflection: the game didn't accept the point. 0 of 17 learned. "
                                                   + c.ev("R2F.L.TALENT_BLOCKED_HINT")),
          "%s: no C_Timer: the next event without the rank is final" % tag)

    # ---- Guided mode ------------------------------------------------------------------
    def glow(cx):
        return {"shown": cx.ev("R2F.TalentGuide.Glow() ~= nil and R2F.TalentGuide.Glow():IsShown()"),
                "anchor": cx.ev("R2F.TalentGuide.Glow() and R2F.TalentGuide.Glow().anchor and R2F.TalentGuide.Glow().anchor:GetName()"),
                "label": cx.ev("R2F.TalentGuide.Glow() and R2F.TalentGuide.Glow().label.__text")}
    def tick(cx):
        cx.lua.execute("R2F.TalentGuide.Host():Fire('OnUpdate', 0.3)")
    c = ctx({}, 17, setup="LearnTalent = nil")
    check(c.ev("R2F.Talents.LearnMode()") == "guided", "%s: no LearnTalent -> guided mode" % tag)
    c.click(c.learn)
    check(c.popup() == "Learn 17 talent points? Only a trainer reset can undo this.\n\n" + c.ev("R2F.L.TALENT_CONFIRM_GUIDED"),
          "%s: guided popup says what will happen" % tag)
    c.accept()
    defl = c.index_of("Deflection")
    g = glow(c)
    check(c.ev("TalentFrame:IsShown()") is True and c.ev("TEST.toggles") == 1, "%s: Blizzard's talent window opened" % tag)
    check(g["shown"] is True and g["anchor"] == "TalentFrameTalent%d" % defl and g["label"] == "Click Deflection (1 of 17)",
          "%s: glow on Deflection's button (client index %d): %s" % (tag, defl, g))
    check(c.said("Click Deflection (1 of 17)") and c.said(c.ev("R2F.L.TALENT_GUIDE_START")), "%s: chat says what to click" % tag)
    check(c.text(c.learn) == "Learning 1 / 17" and c.text(c.cancel) == "Stop", "%s: guided label" % tag)
    check(c.ev("LHINT ~= nil") and find_frames(c.lua, "f.__kind == 'FontString' and f.__text == 'Click Deflection (1 of 17)'", "NOTE") >= 2,
          "%s: the tab's note line shows it too" % tag)
    check(c.ev("R2F.TalentGuide.Glow().__parent == UIParent and R2F.TalentGuide.Glow().__name == nil"),
          "%s: glow parented to UIParent" % tag)
    pulse = c.ev("R2F.TalentGuide.Glow().pulse ~= nil and R2F.TalentGuide.Glow().pulse.playing")
    check(pulse is (True if templates else False), "%s: pulse animation %s" % (tag, "plays" if templates else "absent (steady glow)"))
    c.T.playerLearn(1, defl)
    check(glow(c)["label"] == "Click Deflection (2 of 17)" and c.text(c.learn) == "Learning 2 / 17",
          "%s: glow advances on CHARACTER_POINTS_CHANGED" % tag)
    for _ in range(4):
        c.T.playerLearn(1, defl)
    g = glow(c)
    check(g["anchor"] == "TalentFrameTab2" and g["label"] == "Open the Fury tab, then click Booming Voice (6 of 17)",
          "%s: other tree -> glow on its tab: %s" % (tag, g))
    c.lua.execute("TalentFrame.selectedTab = 2")
    tick(c)
    g = glow(c)
    check(g["anchor"] == "TalentFrameTalent%d" % c.index_of("Booming Voice") and g["label"] == "Click Booming Voice (6 of 17)",
          "%s: tab switched -> glow on the talent (throttled refresh): %s" % (tag, g))
    c.lua.execute("TalentFrame:Hide()")
    tick(c)
    check(glow(c)["shown"] is False, "%s: talent window closed -> glow hidden" % tag)
    c.lua.execute("TalentFrame:Show()")
    tick(c)
    check(glow(c)["shown"] is True, "%s: reopened -> glow back" % tag)
    # Combat stops guided mode too; resume continues it.
    c.combat(True)
    check(c.said(STOP_COMBAT % (5, 17)) and glow(c)["shown"] is False, "%s: guided: combat stops, glow hidden" % tag)
    c.combat(False)
    c.click(c.learn)
    check(c.popup() is None and glow(c)["label"] == "Click Booming Voice (6 of 17)", "%s: guided resumes after combat" % tag)
    # Click through the rest in the right tabs.
    for n in order17[5:]:
        t = 2 if n == "Booming Voice" else 3 if n == "Shield Specialization" else 1
        c.lua.execute("TalentFrame.selectedTab = %d" % t)
        c.T.playerLearn(t, c.index_of(n))
    check(c.said("Learned 17 talent points.") and glow(c)["shown"] is False and c.ev("R2F.TalentGuide.Host():IsShown()") is False,
          "%s: guided run completes, glow and its refresh gone" % tag)
    check(c.ev("TEST.talentWrites") == 0, "%s: guided mode never calls a talent write" % tag)
    bliz = find_frames(c.lua, "f.__name and f.__name:find('^TalentFrame') and next(f.__scripts) ~= nil", "BZ")
    check(bliz == 0, "%s: no script set on any Blizzard talent frame" % tag)
    # A wrong click (talent not in the build) stops guided mode.
    c = ctx({}, 17, setup="LearnTalent = nil")
    c.click(c.learn)
    c.accept()
    c.T.playerLearn(1, c.index_of("Improved Heroic Strike"))
    check(c.said("Stopped: your talents changed while learning. 0 of 17 learned. Check the preview, then click Learn talents again.")
          and glow(c)["shown"] is False, "%s: guided: wrong talent clicked -> stop" % tag)
    # Stop button in guided mode.
    c = ctx({}, 17, setup="LearnTalent = nil")
    c.click(c.learn)
    c.accept()
    c.click(c.cancel)
    check(c.said("Stopped. 0 of 17 learned. Click Learn talents to continue.") and glow(c)["shown"] is False,
          "%s: guided: Stop" % tag)
    # Newer frame name; window already open is not toggled shut.
    c = ctx({}, 17, setup="LearnTalent = nil TEST.talentFrameName = 'PlayerTalentFrame'")
    c.lua.execute("ToggleTalentFrame()")
    c.click(c.learn)
    c.accept()
    check(c.ev("PlayerTalentFrame:IsShown()") is True and c.ev("TEST.toggles") == 1
          and glow(c)["anchor"] == "PlayerTalentFrameTalent%d" % c.index_of("Deflection"),
          "%s: PlayerTalentFrame names; an open window stays open" % tag)
    # No ToggleTalentFrame: text only until the player opens the window.
    c = ctx({}, 17, setup="LearnTalent = nil ToggleTalentFrame = nil")
    c.click(c.learn)
    c.accept()
    check(c.said(c.ev("R2F.L.TALENT_GUIDE_OPEN")) and c.said("Click Deflection (1 of 17)") and glow(c)["shown"] is False,
          "%s: no ToggleTalentFrame -> 'open your talent window', no glow yet" % tag)
    c.lua.execute("TEST.makeTalentFrame('TalentFrame'):Show()")
    tick(c)
    check(glow(c)["shown"] is True, "%s: glow appears once the player opens it" % tag)
    # Detection: first point refused -> hint -> Learn continues in guided mode.
    c = ctx({}, 17, setup="TEST.learnBlocked = true")
    c.click(c.learn)
    c.accept()
    c.T.runTimers()
    check(c.said("Stopped at Deflection: the game didn't accept the point. 0 of 17 learned. " + c.ev("R2F.L.TALENT_BLOCKED_HINT")),
          "%s: blocked LearnTalent -> 13.5's stop + guided hint" % tag)
    c.click(c.learn)
    check(c.popup() is None and c.status().mode == "guided" and glow(c)["label"] == "Click Deflection (1 of 17)",
          "%s: next Learn -> guided mode on the same run" % tag)
    # ADDON_ACTION_FORBIDDEN for LearnTalent: stops at once, no timer needed.
    c = ctx({}, 17, setup="TEST.learnBlocked = true TEST.forbiddenEvent = true")
    c.click(c.learn)
    c.accept()
    check(c.status().phase == "stopped" and c.ev("R2F.Talents.LearnMode()") == "guided",
          "%s: ADDON_ACTION_FORBIDDEN -> stop and guided mode at once" % tag)
    c.T.fire("ADDON_ACTION_FORBIDDEN", "OtherAddon", "LearnTalent()")
    c.T.fire("ADDON_ACTION_BLOCKED", "RoadToForever", "CastSpellByName()")
    check(c.ev("R2F.Talents.LearnMode()") == "guided", "%s: other addons' / other functions' events ignored" % tag)

    # ---- Blizzard's preview API (Wrath-style), when switched on --------------------------
    setup = ("GetCVarBool = function(n) return n == 'previewTalents' end "
             "PREV = {} AddPreviewTalentPoints = function(t, i, n) table.insert(PREV, t .. ':' .. i .. 'x' .. n) end")
    c = ctx({}, 17, setup=setup)
    check(c.ev("R2F.Talents.LearnMode()") == "preview", "%s: preview API + CVar on -> preview mode" % tag)
    c.click(c.learn)
    prev_calls = lua_table_to_list(c.ev("PREV"))
    want_prev = ["1:%dx5" % c.index_of("Deflection"), "2:%dx5" % c.index_of("Booming Voice"),
                 "3:%dx1" % c.index_of("Shield Specialization"), "1:%dx5" % c.index_of("Tactical Mastery"),
                 "1:%dx1" % c.index_of("Anger Management")]
    check(prev_calls == want_prev and c.popup() is None and c.ev("TEST.talentWrites") == 0,
          "%s: fills Blizzard's preview in learning order, no popup, no LearnTalent / commit: %s" % (tag, prev_calls))
    check(c.said(c.ev("R2F.L.TALENT_PREVIEW_FILLED").replace("%d", "17")) and c.ev("TalentFrame:IsShown()") is True,
          "%s: talent window opened for Blizzard's Learn button" % tag)
    c = ctx({}, 17, setup="GetCVarBool = function() return false end")
    check(c.ev("R2F.Talents.LearnMode()") == "direct", "%s: preview functions present but CVar off -> direct" % tag)

    # ---- Globals ------------------------------------------------------------------------
    new_globals = c.ev("""(function()
      local out = {}
      for k in pairs(_G) do if not BEFORE[k] then table.insert(out, k) end end
      table.sort(out) return table.concat(out, ",") end)()""").split(",")
    # TalentFrame* = the stub's fake Blizzard window; PREV / GetCVarBool = this test's setup.
    bad = [g for g in new_globals if g and g not in ("NS", "LBTN", "LHINT", "LST", "NOTE", "BZ", "PREV", "GetCVarBool")
           and not g.startswith("TalentFrame")
           and g not in BINDING_GLOBALS
           and g not in ("SLASH_R2F1", "SLASH_R2FT1") and not g.startswith("R2F")]
    check(not bad, "%s: step 10 adds no globals of its own: %s" % (tag, bad))


# The 8 Paladin Holy nodes dumped from a real WoW Forever client (tree 1100,
# /tdump, 2026-10-02; still in the user's saved chat log), with Wowhead's own
# row/col (0-based) for the same node ids. ADDON_PLAN 13.10.
#   node id: (posX, posY, name, maxRank, wowhead row, wowhead col)
REAL_HOLY_NODES = {
    105320: (1620, 5730, "Light's Vigil", 1, 6, 1),
    105321: (2220, 5130, "Holy Power", 5, 5, 2),
    105323: (1620, 4530, "Holy Shock", 1, 4, 1),
    105324: (1020, 4530, "Divine Precision", 3, 4, 0),
    105325: (2220, 3930, "Divine Favor", 1, 3, 2),
    105327: (2220, 3330, "Purifying Power", 2, 2, 2),
    105329: (1620, 3930, "Illumination", 5, 3, 1),
    105330: (1020, 3330, "Voice of Truth", 1, 2, 0),
}


def trait_tree_lua(tree_ids, trees):
    """Lua source for TEST.traitTree from {tree id: [(id, posX, posY, name, rank, maxRank)]}."""
    parts = []
    for tid in tree_ids:
        nodes = ", ".join("{ id = %d, posX = %s, posY = %s, name = %s, rank = %d, maxRank = %d, spellID = %d }"
                          % (i, x, y, lua_literal(n), r, m, 300000 + i) for i, x, y, n, r, m in trees[tid])
        parts.append("[%d] = { %s }" % (tid, nodes))
    return "TEST.traitTree = { treeIDs = { %s }, trees = { %s } }" % (", ".join(str(t) for t in tree_ids), ", ".join(parts))


def paladin_like_tree(transform=lambda x, y: (x, y)):
    """One tree (1100) = the 8 REAL Holy nodes + SYNTHESIZED filler: Holy's rows
    0/1 and column 3 (which the dump didn't print; their positions follow the
    verified 600-step grid) and Protection / Retribution panes at the
    screenshot-read pane offset. Only the 8 real nodes are asserted on."""
    nodes = [(i, x, y, n, 0, m) for i, (x, y, n, m, _, _) in REAL_HOLY_NODES.items()]
    synth = [(1, 1, 0), (1, 2, 0), (1, 0, 1), (1, 1, 1), (1, 2, 1), (1, 3, 1), (1, 3, 3)]
    for p in (2, 3):
        synth += [(p, c, r) for r in range(7) for c in range(4) if (r + c + p) % 2 == 0]
    for k, (p, c, r) in enumerate(synth):
        nodes.append((900000 + k, 1020 + (p - 1) * 3930 + c * 600, 2130 + r * 600, "Synth %d" % k, 0, 1))
    nodes = [(i, *transform(x, y), n, r, m) for i, x, y, n, r, m in nodes]
    return trait_tree_lua([1100], {1100: nodes})


def test_talent_traits(templates):
    """13.10: reading talents through C_Traits. The position -> row/column
    conversion is checked against REAL dumped node data, the pane split and its
    refusals, and the realistic WoW Forever client (no Classic talent API at
    all: reading works, learning is guided and writes nothing)."""
    tag = "templates" if templates else "fallbacks"
    fxt = json.load(open(TALENT_FIXTURE, encoding="utf-8"))
    raw = fxt["talents"]
    js = talent_js()
    lua = new_runtime(templates)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    TL = lua.eval("R2F.Talents")
    read = lua.eval("function() return R2F.Talents.ReadTrees() end")

    def by_node(trees):
        out = {}
        for t in range(1, len(trees) + 1):
            for k in range(1, len(trees[t]) + 1):
                e = trees[t][k]
                out[e.nodeID] = (t, e.tier, e.column, e.name, k)
        return out

    # ---- Real data, nothing synthesized: the rank conversion alone ---------
    # Ranks of the 8 real nodes' distinct posX / posY, compared with Wowhead's
    # row/col for the same node ids. Only Wowhead rows 2..6 and cols 0..2 are
    # in the dump, so absolute values need an offset here; what this proves
    # from real data alone is the DIRECTION and the strict order of both axes
    # (posY grows with the row, posX with the column), i.e. exactly the
    # (row, column) sort that the link digits, the hash and the learn order use.
    lua.execute("REALN = { %s }" % ", ".join("{ posX = %d, posY = %d }" % (v[0], v[1]) for v in REAL_HOLY_NODES.values()))
    colr = lua.eval("(R2F.Talents.GridRanks(REALN, 'posX'))")
    rowr = lua.eval("(R2F.Talents.GridRanks(REALN, 'posY'))")
    min_row = min(v[4] for v in REAL_HOLY_NODES.values())
    min_col = min(v[5] for v in REAL_HOLY_NODES.values())
    for nid, (x, y, name, _, row, col) in REAL_HOLY_NODES.items():
        check(rowr[y] - 1 == row - min_row and colr[x] - 1 == col - min_col,
              "%s: real node %d %s: ranks (%d, %d) == Wowhead (row %d, col %d) minus the dump's offset"
              % (tag, nid, name, rowr[y], colr[x], row, col))
    ours = sorted(REAL_HOLY_NODES, key=lambda n: (rowr[REAL_HOLY_NODES[n][1]], colr[REAL_HOLY_NODES[n][0]]))
    wh = sorted(REAL_HOLY_NODES, key=lambda n: (REAL_HOLY_NODES[n][4], REAL_HOLY_NODES[n][5]))
    check(ours == wh, "%s: real nodes sorted by our (tier, column) == Wowhead (row, col) order: %s" % (tag, ours))
    rev = sorted(REAL_HOLY_NODES, key=lambda n: (-REAL_HOLY_NODES[n][1], REAL_HOLY_NODES[n][0]))
    check(rev != wh, "%s: sanity: treating posY as decreasing with the row would NOT match Wowhead" % tag)

    # ---- Real nodes inside a full tree: absolute tier/column -----------------
    lua.execute(paladin_like_tree())
    trees = read()
    check(trees is not None and len(trees) == 3, "%s: Paladin-like single tree (1100) splits into 3 panes" % tag)
    got = by_node(trees)
    for nid, (x, y, name, _, row, col) in REAL_HOLY_NODES.items():
        t, tier, column, nm, _ = got.get(nid, (None,) * 5)
        check(t == 1 and tier == row + 1 and column == col + 1 and nm == name,
              "%s: real node %d %s -> pane %s tier %s column %s (Wowhead row %d col %d, +1)"
              % (tag, nid, name, t, tier, column, row, col))
    check(len(trees[1]) == 15 and len(trees[2]) == 14 and len(trees[3]) == 14,
          "%s: every node lands in its own pane (15/14/14)" % tag)
    # Scale and offset of the coordinates don't matter (ranks, not arithmetic).
    base = {k: v[:3] for k, v in got.items()}
    lua.execute(paladin_like_tree(lambda x, y: (x * 0.5 + 77, y * 2 - 13)))
    check({k: v[:3] for k, v in by_node(read()).items()} == base, "%s: scaled/offset coordinates -> same result" % tag)
    lua.execute(paladin_like_tree(lambda x, y: (x / 10.0, y / 10.0)))
    check({k: v[:3] for k, v in by_node(read()).items()} == base, "%s: posX/10 (UI units) -> same result" % tag)

    # ---- Refusals: nil rather than a wrong mapping ---------------------------
    lua.execute("TEST.traitTree = nil")
    set_game_talents(lua, raw, js["classes"]["warrior"], {})
    lua.execute("TEST.traitLayout = 'single' table.remove(TEST.talentTabs[3], 1)")
    check(read() is not None, "%s: sanity: warrior single tree reads" % tag)
    lua.execute("TEST.talentTabs[3] = {}")
    check(read() is None, "%s: single tree with an empty pane -> nil (2 groups can't be 3 panes)" % tag)
    set_game_talents(lua, raw, js["classes"]["warrior"], {})
    T.traitPaneOffset = 1800          # panes touching: every gap is one grid step, no clear split
    check(read() is None, "%s: pane gutter no wider than a column gap -> nil" % tag)
    T.traitPaneOffset = 3930
    lua.execute("for k = 1, 8 do TEST.talentTabs[1][k].tier = k end")
    check(read() is None, "%s: more than 7 distinct rows -> nil" % tag)
    set_game_talents(lua, raw, js["classes"]["warrior"], {})
    lua.execute(trait_tree_lua([1100], {1100: [(1 + i, 1020 + i * 600, 2130, "C%d" % i, 0, 1) for i in range(5)]
                                         + [(10, 9000, 2130, "P2", 0, 1), (11, 15000, 2130, "P3", 0, 1)]}))
    check(read() is None, "%s: more than 4 columns in a pane -> nil" % tag)
    lua.execute("TEST.traitTree = nil")
    # Two-tree configs: neither 1 (observed) nor 3 (one per pane) -> nil.
    lua.execute(trait_tree_lua([1, 2], {1: [(1, 0, 0, "A", 0, 1)], 2: [(2, 0, 0, "B", 0, 1)]}))
    check(read() is None, "%s: a 2-tree config -> nil" % tag)
    lua.execute("TEST.traitTree = nil")

    # ---- One tree per pane (never seen; supported) == single tree ----------
    for sc in fxt["scenarios"][:3]:
        lua.execute("TEST.classToken = %r" % sc["cls"].upper())
        set_game_talents(lua, raw, js["classes"][sc["cls"]], sc["ranks"])
        single = TL.LinkBody(TL.ClassId(), read()) if lua.eval("TEST.traitLayout") == "single" else None
        lua.execute("TEST.traitLayout = 'perPane'")
        per = TL.LinkBody(TL.ClassId(), read())
        want = "%s/%s~%s" % (sc["cls"], sc["code"], js["hashes"][sc["cls"]])
        check(per == want and single in (None, want), "%s: %s: per-pane layout link %r == site %r" % (tag, sc["name"], per, want))
    lua.execute("TEST.classToken = nil")

    # ---- Live ranks: a point learned shows up on the next read --------------
    set_game_talents(lua, raw, js["classes"]["warrior"], {})
    lua.execute("for _, x in ipairs(TEST.talentTabs[1]) do if x.name == 'Deflection' then x.rank = 3 end end")
    check(any(e.name == "Deflection" and e.rank == 3 for e in (read()[1][k] for k in range(1, len(read()[1]) + 1))),
          "%s: activeRank read live" % tag)

    # ---- TRAIT_CONFIG_UPDATED drives the same refresh as CHARACTER_POINTS_CHANGED
    check(lua.eval("(function() for _, f in ipairs(TEST.allFrames) do if f.__events and f.__events.TRAIT_CONFIG_UPDATED"
                   " and f.__events.CHARACTER_POINTS_CHANGED then return true end end return false end)()") is True,
          "%s: Core registers TRAIT_CONFIG_UPDATED next to CHARACTER_POINTS_CHANGED" % tag)

    # ---- The realistic WoW Forever client: no Classic talent API at all -----
    fv = new_runtime(templates, before_load="GetTalentInfo = nil LearnTalent = nil GetTalentPrereqs = nil "
                     "GetTalentTabInfo = nil AddPreviewTalentPoints = nil LearnPreviewTalents = nil")
    F = fv.eval("TEST")
    F.fire("ADDON_LOADED", "RoadToForever")
    F.fire("PLAYER_LOGIN")
    sc = fxt["scenarios"][1]
    fv.execute("TEST.classToken = %r" % sc["cls"].upper())
    set_game_talents(fv, raw, js["classes"][sc["cls"]], sc["ranks"])
    want = "%s/%s~%s" % (sc["cls"], sc["code"], js["hashes"][sc["cls"]])
    check(fv.eval("R2F.Talents.MyBuildLink()") == SITE_TALENTS + want,
          "%s: Forever client: Copy my build link == talentcalc.js's (%s)" % (tag, want))
    # A learnable build on that client.
    set_game_talents(fv, raw, js["classes"]["warrior"], {})
    fv.execute("TEST.classToken = 'WARRIOR'")
    F.talentPoints = 10
    link = "warrior/05~" + js["hashes"]["warrior"]
    res = fv.eval("R2F.Talents.Preview(%s)" % lua_literal(link))
    check(res.plan is not None and res.plan.learnable is True and res.error is None,
          "%s: Forever client: Preview works and the plan is learnable" % tag)
    check(fv.eval("R2F.Talents.TreeName(1)") == "Arms",
          "%s: Forever client: no GetTalentTabInfo -> our own tree name (15.2)" % tag)
    check(fv.eval("R2F.Talents.LearnMode()") == "guided",
          "%s: Forever client without C_Traits writes (13.12 adds them): learning is guided" % tag)
    # Even if a LearnTalent (and a switched-on preview API) existed there: no
    # Classic GetTalentInfo = no way to confirm a (tab, index) address -> guided.
    fv.execute("LearnTalent = function() error('must not be called') end "
               "AddPreviewTalentPoints = LearnTalent LearnPreviewTalents = LearnTalent "
               "GetCVarBool = function() return true end")
    check(fv.eval("R2F.Talents.LearnMode()") == "guided",
          "%s: Forever client with a stray LearnTalent / preview API: still guided" % tag)
    fv.execute("LearnTalent = nil AddPreviewTalentPoints = nil LearnPreviewTalents = nil GetCVarBool = nil")
    fv.execute("R2F.Talents.StartLearn(%s, R2F.Talents.LearnPoints(R2F.Talents.Preview(%s).plan))"
               % (lua_literal(link), lua_literal(link)))
    F.runTimers()
    st = fv.eval("R2F.Talents.LearnStatus()")
    check(st.phase == "guided" and st.point.name == "Deflection", "%s: Forever client: guided run points at Deflection" % tag)
    check(fv.eval("R2F.TalentGuide.Glow() == nil or not R2F.TalentGuide.Glow():IsShown()") is True,
          "%s: Forever client: no glow on a Blizzard button it can't confirm" % tag)
    check(F.talentWrites == 0, "%s: Forever client: nothing written" % tag)
    # The player applies the points in Blizzard's window (fires TRAIT_CONFIG_UPDATED):
    # the guided run follows.
    for _ in range(5):
        fv.execute("for _, x in ipairs(TEST.talentTabs[1]) do if x.name == 'Deflection' then x.rank = (x.rank or 0) + 1 end end"
                   " TEST.talentPoints = TEST.talentPoints - 1")
        F.fire("TRAIT_CONFIG_UPDATED", 7001)
    check(fv.eval("R2F.Talents.LearnStatus().phase") == "done" and F.talentWrites == 0,
          "%s: Forever client: guided run finishes on TRAIT_CONFIG_UPDATED, still nothing written" % tag)

    # ---- A Classic-API client whose address names another talent: no write --
    set_game_talents(lua, raw, js["classes"]["warrior"], {})
    lua.execute("TEST.classToken = 'WARRIOR' R2F.Talents.ResetSession()")
    T.talentPoints = 10
    lua.execute("REAL_GTI = GetTalentInfo GetTalentInfo = function(tab, i) local n, a, b, c, d, e = REAL_GTI(tab, i)"
                " return n and ('Not ' .. n), a, b, c, d, e end")
    T.learnCalls = lua.table()
    check(lua.eval("R2F.Talents.LearnMode()") == "direct", "%s: sanity: Classic API present -> direct mode" % tag)
    lua.execute("R2F.Talents.StartLearn(%s, R2F.Talents.LearnPoints(R2F.Talents.Preview(%s).plan))"
                % (lua_literal(link), lua_literal(link)))
    T.runTimers()
    check(len(lua_table_to_list(T.learnCalls)) == 0 and lua.eval("R2F.Talents.LearnStatus().phase") == "stopped",
          "%s: Classic address doesn't name the talent -> stopped before LearnTalent, nothing sent" % tag)
    lua.execute("GetTalentInfo = REAL_GTI")


# 13.11: the 13 distinct posX values of Paladin's WHOLE trait tree 1100 (all
# 50 nodes), from the live /tdump of 2026-10-03. Real data. Protection's first
# column comes as both 5020 and 5030 (Blizzard's own jitter; the gap list is
# 600 600 600 | 2200 | 10 590 600 600 | 2260 | 600 600 600).
REAL_PALADIN_X = [1020, 1620, 2220, 2820, 5020, 5030, 5620, 6220, 6820, 9080, 9680, 10280, 10880]
PALADIN_PANE_X = [[1020, 1620, 2220, 2820], [5020, 5620, 6220, 6820], [9080, 9680, 10280, 10880]]
PALADIN_JITTER_X = 5030
# Paladin's cell layout per pane (Wowhead's Forever data, site tree order Holy
# 382 / Protection 383 / Retribution 381): (node id, row, col, max rank). Only
# the SHAPE is kept here (Wowhead's talent data isn't stored in the repo, 13.10);
# names are placeholders except the 8 real Holy nodes already above. posY is
# 2130 + row * 600, the grid verified on the real Holy nodes (Protection's and
# Retribution's posY were not in the 13-value report: synthesized on that grid).
PALADIN_LAYOUT = [
    [(105639, 0, 1, 5), (105332, 0, 2, 5), (105333, 1, 0, 3), (105335, 1, 1, 2), (105334, 1, 2, 3),
     (105331, 1, 3, 2), (105330, 2, 0, 1), (110871, 2, 1, 3), (105327, 2, 2, 2), (110873, 3, 0, 2),
     (105329, 3, 1, 5), (105325, 3, 2, 1), (105324, 4, 0, 3), (105323, 4, 1, 1), (110872, 4, 2, 2),
     (105321, 5, 2, 5), (105320, 6, 1, 1)],
    [(105630, 0, 1, 5), (105626, 0, 2, 5), (105638, 1, 0, 3), (105637, 1, 1, 2), (105636, 1, 3, 5),
     (110875, 2, 0, 1), (105634, 2, 1, 3), (110874, 2, 2, 3), (105632, 2, 3, 2), (110878, 3, 0, 1),
     (105629, 3, 1, 3), (105633, 3, 2, 3), (105625, 4, 1, 1), (105627, 4, 2, 5), (110879, 5, 2, 5),
     (105628, 6, 1, 1)],
    [(105707, 0, 1, 5), (105706, 0, 2, 5), (105705, 1, 0, 2), (105704, 1, 1, 2), (105703, 1, 2, 5),
     (105702, 2, 0, 3), (105701, 2, 1, 3), (105696, 2, 2, 1), (105699, 2, 3, 2), (105698, 3, 0, 2),
     (105700, 3, 2, 1), (105697, 4, 0, 3), (105693, 4, 1, 3), (105694, 4, 2, 1), (110882, 5, 1, 3),
     (110880, 5, 2, 2), (105692, 6, 1, 1)],
]
PALADIN_TREES = (382, 383, 381)
PROT_COL0 = [i for i, r, c, m in PALADIN_LAYOUT[1] if c == 0]   # the 3 nodes that can carry 5030


def paladin_name(pane, nid, row, col):
    if nid in REAL_HOLY_NODES:
        return REAL_HOLY_NODES[nid][2]
    return "%s r%dc%d" % (("Holy", "Prot", "Ret")[pane], row, col)


def paladin_tree(jitter_ids=(PROT_COL0[0],), ranks=None, nudge=None, pane_x=None, transform=lambda x, y: (x, y)):
    """The 50-node Paladin tree 1100 on the REAL posX values. jitter_ids = the
    Protection column-0 nodes at 5030 (the rest at 5020; the report doesn't
    say which node had which, so tests try every choice). nudge = {id: (dx, dy)}
    synthetic extra jitter; pane_x = synthetic column X values per pane."""
    ranks, nudge, pane_x = ranks or {}, nudge or {}, pane_x or PALADIN_PANE_X
    nodes = []
    for p, layout in enumerate(PALADIN_LAYOUT):
        for nid, row, col, mx in layout:
            x = pane_x[p][col]
            if p == 1 and col == 0 and nid in jitter_ids:
                x = PALADIN_JITTER_X
            y = 2130 + row * 600
            dx, dy = nudge.get(nid, (0, 0))
            x, y = transform(x + dx, y + dy)
            name = paladin_name(p, nid, row, col)
            nodes.append((nid, x, y, name, ranks.get(name, 0), mx))
    # The client's order is not row/col order: interleave by id.
    nodes.sort(key=lambda n: (n[0] * 7919) % 1000)
    return trait_tree_lua([1100], {1100: nodes})


def paladin_wowhead_fixture(scenarios):
    """The same layout in Wowhead's format, for the real talentcalc.js."""
    talents = {}
    for p, layout in enumerate(PALADIN_LAYOUT):
        tree = {}
        for nid, row, col, mx in layout:
            tree[str(nid)] = {"id": nid, "row": row, "col": col, "icon": "inv_misc_questionmark",
                              "name": paladin_name(p, nid, row, col), "ranks": list(range(1, mx + 1))}
        talents[str(PALADIN_TREES[p])] = tree
    return {"talents": talents, "scenarios": scenarios}


def test_talent_grid_jitter(templates):
    """13.11: tolerance for Blizzard's few-unit jitter in node positions. The
    real 13 posX values of Paladin's whole tree must read as 4 / 4 / 4 columns
    (raw ranking saw 5 in Protection and refused), and the tolerance must be
    relative (any grid step), work on Y too, and NOT merge real columns."""
    tag = "templates" if templates else "fallbacks"
    lua = new_runtime(templates)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    TL = lua.eval("R2F.Talents")
    read = lua.eval("function() return R2F.Talents.ReadTrees() end")
    snap_lua = lua.eval("function(vals) local n = {} for i = 1, #vals do n[i] = { v = vals[i] } end"
                        " return R2F.Talents.GridSnap(n, 'v') end")

    def snap(vals):
        m = snap_lua(lua.table(*vals))
        return {v: m[v] for v in vals}

    def distinct_after(vals):
        return len(set(snap(vals).values()))

    def layout_of(trees):
        """{node id: (pane, tier, column)} from ReadTrees output."""
        out = {}
        for t in range(1, len(trees) + 1):
            for k in range(1, len(trees[t]) + 1):
                e = trees[t][k]
                out[e.nodeID] = (t, e.tier, e.column)
        return out

    want = {nid: (p + 1, row + 1, col + 1) for p, layout in enumerate(PALADIN_LAYOUT) for nid, row, col, _ in layout}

    def cols_per_pane(trees):
        return [len({trees[t][k].column for k in range(1, len(trees[t]) + 1)}) for t in (1, 2, 3)]

    # ---- The real values, re-derived -----------------------------------------
    gaps = [b - a for a, b in zip(REAL_PALADIN_X, REAL_PALADIN_X[1:])]
    check(gaps == [600, 600, 600, 2200, 10, 590, 600, 600, 2260, 600, 600, 600],
          "%s: real Paladin posX gaps re-derived: %s" % (tag, gaps))
    s = snap(REAL_PALADIN_X)
    check(s[5030] == 5020 and all(s[v] == v for v in REAL_PALADIN_X if v != 5030),
          "%s: real 13 X values: only 5030 snaps (onto 5020), every other value is its own grid line" % tag)
    xs = sorted(set(s.values()))
    sg = sorted(((b - a, i) for i, (a, b) in enumerate(zip(xs, xs[1:]))), reverse=True)
    check(len(xs) == 12 and [g for g, _ in sg[:3]] == [2260, 2200, 600]
          and sorted(i for _, i in sg[:2]) == [3, 7],
          "%s: gutters on the SNAPPED values: 2260 / 2200 after the 4th and 8th line, next gap 600 (clear split)" % tag)

    # ---- The bug, reproduced on the raw values -------------------------------
    lua.execute(paladin_tree())
    raw_prot = lua.eval("(function() local n = {} for _, v in ipairs({5020, 5030, 5620, 6220, 6820}) do"
                        " n[#n + 1] = { posX = v } end return select(2, R2F.Talents.GridRanks(n, 'posX')) end)()")
    check(raw_prot == 5, "%s: raw ranking counts 5 Protection columns (the bug)" % tag)
    FRACTION = TL.SNAP_FRACTION   # the shipped value; restored after each sanity flip
    TL.SNAP_FRACTION = 0
    check(read() is None, "%s: sanity: tolerance off -> the real tree reads nil (reproduces the live failure)" % tag)
    TL.SNAP_FRACTION = FRACTION

    # ---- The real tree, every possible placement of the jitter --------------
    variants = [(i,) for i in PROT_COL0] + [tuple(PROT_COL0[:k] + PROT_COL0[k + 1:]) for k in range(3)]
    for jit in variants:
        lua.execute(paladin_tree(jitter_ids=jit))
        trees = read()
        ok = trees is not None and len(trees) == 3
        check(ok, "%s: real Paladin tree, 5030 on %s: ReadTrees succeeds" % (tag, jit))
        if not ok:
            continue
        check([len(trees[t]) for t in (1, 2, 3)] == [17, 16, 17] and cols_per_pane(trees) == [4, 4, 4],
              "%s: 5030 on %s: 17/16/17 talents, 4/4/4 columns (got %s)" % (tag, jit, cols_per_pane(trees)))
        check(layout_of(trees) == want, "%s: 5030 on %s: all 50 nodes at Wowhead's pane/row/col" % (tag, jit))

    # ---- End to end: link + hash == the site's talentcalc.js ---------------
    jit_name = paladin_name(1, PROT_COL0[0], 1, 0)       # Protection row 1 col 0, at 5030
    scen = [{"name": "none", "cls": "paladin", "ranks": {}},
            {"name": "jittered node", "cls": "paladin",
             "ranks": {"Prot r0c1": 5, jit_name: 3, "Holy r0c2": 2, "Ret r0c1": 4}}]
    tmp = os.path.join(tempfile.mkdtemp(), "paladin_fixture.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(paladin_wowhead_fixture(scen), f)
    js = talent_js(tmp)
    lua.execute("TEST.classToken = 'PALADIN'")
    for sc, out in zip(scen, js["scenarios"]):
        lua.execute(paladin_tree(ranks=sc["ranks"]))
        check(out["points"] == out["total"], "%s: sanity: talentcalc.js took every preset point (%s)" % (tag, sc["name"]))
        link = TL.LinkBody(TL.ClassId(), read())
        check(link == out["link"], "%s: real Paladin tree, %s: link %r == talentcalc.js %r" % (tag, sc["name"], link, out["link"]))
        check(lua.eval("R2F.Talents.MyBuildLink()") == SITE_TALENTS + out["link"],
              "%s: %s: Copy my build link == the site's" % (tag, sc["name"]))
    check(js["scenarios"][1]["link"].startswith("paladin/02-503-4~"),
          "%s: sanity: the jittered node's 3 points are Protection's digit 3 (row 1 col 0, after row 0's two)" % tag)
    lua.execute("TEST.classToken = nil")

    # ---- Holy unchanged: no jitter -> snapping is a no-op -------------------
    lua.execute(paladin_like_tree())
    lua.execute("NOJIT = {} for _, t in ipairs(TEST.traitTree.trees[1100]) do NOJIT[#NOJIT + 1] = t end")
    check(lua.eval("(function() for _, key in ipairs({'posX', 'posY'}) do local m = R2F.Talents.GridSnap(NOJIT, key)"
                   " for v, s in pairs(m) do if v ~= s then return false end end end return true end)()") is True,
          "%s: no jitter (the 13.10 tree with the 8 real Holy nodes): every value snaps to itself (no-op)" % tag)
    real8 = [v[0] for v in REAL_HOLY_NODES.values()] + [v[1] for v in REAL_HOLY_NODES.values()]
    check(all(k == v for k, v in snap(real8).items()), "%s: the 8 real Holy nodes' X/Y: no-op" % tag)

    # ---- Synthetic: jitter in Y (never seen; defensive) ----------------------
    nudge_y = {105698: (0, 7), 105694: (0, -9)}            # Ret row 3 down 7, Ret row 4 up 9
    lua.execute(paladin_tree(nudge=nudge_y))
    trees = read()
    check(trees is not None and layout_of(trees) == want,
          "%s: synthetic Y jitter (+7 / -9 on two rows): still 7 tiers, every node in place" % tag)
    TL.SNAP_FRACTION = 0
    check(read() is None, "%s: sanity: that Y jitter without tolerance = 9 tiers -> nil" % tag)
    TL.SNAP_FRACTION = FRACTION

    # ---- Synthetic: several jitter pairs, both directions, both axes --------
    nudge_multi = {105327: (-6, 0), 105699: (12, 0), 105705: (0, 4), 105625: (-3, -3)}
    lua.execute(paladin_tree(jitter_ids=(PROT_COL0[1],), nudge=nudge_multi))
    trees = read()
    check(trees is not None and layout_of(trees) == want and cols_per_pane(trees) == [4, 4, 4],
          "%s: synthetic: 5 jitter pairs (X and Y, + and -, all three panes): 4/4/4, every node in place" % tag)

    # ---- Synthetic: other grid steps (the tolerance is relative) ------------
    for k, desc in ((0.1, "step 60 (a fixed 100-unit threshold would merge real columns)"),
                    (10, "step 6000, jitter 100 (a fixed small threshold would miss it)"),
                    (0.37, "step 222, odd offset")):
        lua.execute(paladin_tree(transform=lambda x, y, k=k: (x * k + 13, y * k - 5)))
        trees = read()
        check(trees is not None and layout_of(trees) == want, "%s: synthetic %s: every node in place" % (tag, desc))
    check(snap([0, 300, 6000, 12000, 18000])[300] == 0, "%s: step 6000: jitter of 300 (5%%) snaps" % tag)
    check(distinct_after([0, 60, 120, 180, 1]) == 4, "%s: step 60: jitter of 1 snaps, the 4 columns stay" % tag)

    # ---- Not too aggressive: real columns closer than usual stay apart ------
    # A pane whose columns 2 and 3 are only a third of a step apart (200 vs
    # 600). Intentional layout, NOT jitter: it must read as 4 columns. This
    # fails if the tolerance were raised to a third of a step or more.
    tight = [PALADIN_PANE_X[0], PALADIN_PANE_X[1], [9080, 9680, 9880, 10480]]
    lua.execute(paladin_tree(pane_x=tight))
    trees = read()
    check(trees is not None and layout_of(trees) == want and cols_per_pane(trees) == [4, 4, 4],
          "%s: real columns 200 apart (1/3 step) are NOT merged: Retribution keeps 4 columns" % tag)
    check(distinct_after([0, 600, 800, 1400, 2000]) == 5, "%s: GridSnap keeps a 1/3-step gap" % tag)
    check(distinct_after([0, 600, 750, 1350, 1950]) == 5, "%s: GridSnap keeps a 1/4-step gap" % tag)
    TL.SNAP_FRACTION = 0.4
    t2 = read()
    check(t2 is None or layout_of(t2) != want,
          "%s: sanity: with a too-aggressive tolerance (0.4) the tight tree no longer reads right" % tag)
    TL.SNAP_FRACTION = FRACTION

    # ---- Fail-safe: jitter on most gaps -> nothing merges -> nil, not a guess
    check(distinct_after([0, 10, 600, 610, 1200, 1210, 1800, 1810]) == 8,
          "%s: jitter on every column (median gap = jitter): nothing snaps" % tag)
    # Every column split in two (odd rows +10): exactly half the X gaps (11 of
    # 22) are jitter. The UPPER median still lands on a real step: reads right.
    half = {nid: (10, 0) for layout in PALADIN_LAYOUT for nid, r, _, _ in layout if r % 2 == 1}
    lua.execute(paladin_tree(nudge=half))
    t3 = read()
    check(t3 is not None and layout_of(t3) == want, "%s: half the X gaps are jitter: upper median, still right" % tag)
    # Every column split in three (+0 / +10 / +20 by row): jitter is the
    # majority, the median is a jitter gap, nothing snaps -> more than 4
    # columns -> refused.
    most = {nid: (10 * (r % 3), 0) for layout in PALADIN_LAYOUT for nid, r, _, _ in layout}
    lua.execute(paladin_tree(nudge=most))
    check(read() is None, "%s: jitter on most X gaps: refused (nil), not guessed" % tag)
    # Chaining: small gaps in a row don't pull separate lines into one cluster.
    check(distinct_after([0, 600, 1200, 1800, 2400, 3000, 50, 100, 150]) == 7,
          "%s: a run of 50-unit steps is measured from the cluster's first value (no chaining)" % tag)
    lua.execute("TEST.traitTree = nil")


# 13.12: the realistic WoW Forever client for the "traits" learning tests: no
# Classic talent API at all, plus the C_Traits write stubs in the given model.
def forever_setup(model="staged", extra=""):
    return ("GetTalentInfo = nil LearnTalent = nil GetTalentPrereqs = nil AddPreviewTalentPoints = nil "
            "LearnPreviewTalents = nil TEST.installTraitWrites(%r) %s" % (model, extra))


def trait_calls(c):
    return lua_table_to_list(c.ev("TEST.traitCalls"))


def purchases(c):
    return [x[len("purchase:"):] for x in trait_calls(c) if x.startswith("purchase:")]


def commits(c):
    return trait_calls(c).count("commit")


def staged_of(c, name):
    return c.ev("(function() for _, l in ipairs(TEST.talentTabs) do for _, x in ipairs(l) do "
                "if x.name == %r then return x.staged or 0 end end end end)()" % name)


def test_talent_traits_learning(templates):
    """13.12: the "traits" learning mode (C_Traits.PurchaseRank + CommitConfig,
    one point at a time, two-way read-back, guided fallback) driven through the
    real Talents tab on a WoW Forever-like client, against fake trait servers
    (wow_stubs.lua T.installTraitWrites): staged + commit, immediate, async,
    staged without a commit, and every failure switch."""
    tag = "templates" if templates else "fallbacks"
    fxt = json.load(open(TALENT_FIXTURE, encoding="utf-8"))
    raw = fxt["talents"]
    js = talent_js()
    W = js["classes"]["warrior"]
    wh = js["hashes"]["warrior"]
    deep = fxt["scenarios"][5]                 # 17 points, the step-10 build
    link = "%swarrior/%s~%s" % (SITE_TALENTS, deep["code"], wh)
    order17 = (["Deflection"] * 5 + ["Booming Voice"] * 5 + ["Shield Specialization"]
               + ["Tactical Mastery"] * 5 + ["Anger Management"])
    STOP_COMBAT = "Stopped: you entered combat. %d of %d learned. Click Learn talents to continue."
    HINT = None

    def ctx(model="staged", ranks=None, pts=17, lnk=link, extra=""):
        return LearnCtx(templates, ranks or {}, pts, lnk, raw, W, forever_setup(model, extra))

    def drain(c):
        while c.ev("#TEST.traitQueue") > 0:
            c.T.traitServer(1)

    def exact_build(c):
        return all(c.rank(n) == v for n, v in deep["ranks"].items())

    # ---- Mode detection ------------------------------------------------------------
    c = ctx()
    HINT = c.ev("R2F.L.TALENT_BLOCKED_HINT")
    check(c.ev("R2F.Talents.LearnMode()") == "traits", "%s: Forever client + C_Traits.PurchaseRank -> 'traits' mode" % tag)
    d = LearnCtx(templates, {}, 17, link, raw, W, "TEST.installTraitWrites('staged')")
    check(d.ev("R2F.Talents.LearnMode()") == "direct",
          "%s: Classic API present too -> still 'direct' (Classic path unchanged, traits only as its alternative)" % tag)
    d = ctx(extra="C_Traits.GetNodeInfo = nil")
    check(d.ev("R2F.Talents.LearnMode()") == "guided", "%s: C_Traits without GetNodeInfo -> guided" % tag)
    d = ctx(extra="C_Traits.PurchaseRank = 'not a function'")
    check(d.ev("R2F.Talents.LearnMode()") == "guided", "%s: PurchaseRank not a function -> guided" % tag)

    # ---- Order: the shared plan, untouched; points carry their node id --------------
    lp = c.ev("(function() local o = {} for i, p in ipairs(R2F.Talents.LearnPoints(R2F.TalentPanel.Result().plan))"
              " do o[i] = p.name .. '>' .. p.target .. '>' .. tostring(p.nodeID) end return o end)()")
    lp = lua_table_to_list(lp)
    check([s.split(">")[0] for s in lp] == order17, "%s: traits mode learns in the same tier/tree/column order" % tag)
    check(all(s.split(">")[2] != "nil" for s in lp), "%s: every point carries its trait node id" % tag)
    nid = c.ev("(function() for _, t in ipairs(R2F.Talents.ReadTrees()) do for _, x in ipairs(t) do"
               " if x.name == 'Deflection' then return x.nodeID end end end end)()")
    check(lp[0].split(">")[2] == str(nid), "%s: the node id is the reader's own (ReadTrees) for that talent" % tag)

    # ---- Popup; Cancel writes nothing -------------------------------------------------
    check(c.enabled(c.learn) is True, "%s: traits: learnable -> Learn enabled" % tag)
    c.click(c.learn)
    check(c.popup() == "Learn 17 talent points? Only a trainer reset can undo this.", "%s: traits: same 13.4 popup" % tag)
    c.lua.execute("R2FConfirm.no:Click()")
    check(c.ev("TEST.talentWrites") == 0 and trait_calls(c) == [] and c.status().phase == "idle",
          "%s: traits: popup Cancel writes nothing" % tag)

    # ---- Full run, staged model (retail-like): purchase, commit, wait, verify -------
    c.T.calls = c.lua.table()
    c.click(c.learn)
    c.accept()
    check(trait_calls(c) == ["purchase:Deflection", "commit"] and c.status().phase == "learning"
          and c.status().mode == "traits", "%s: Learn -> one purchase + one commit, then waits: %s" % (tag, trait_calls(c)))
    check(staged_of(c, "Deflection") == 1 and c.rank("Deflection") == 0,
          "%s: (stub) the point is staged, not applied, until the server answers" % tag)
    check(c.text(c.learn) == "Learning 1 / 17" and c.enabled(c.learn) is False and c.text(c.cancel) == "Stop"
          and c.enabled(c.previewb) is False and c.ev(c.edit + ".__enabled") is False,
          "%s: traits: 'Learning 1 / 17', tab locked, Stop" % tag)
    c.T.fire("TRAIT_TREE_CURRENCY_INFO_UPDATED", 1100)
    c.T.fire("CHARACTER_POINTS_CHANGED")
    check(len(purchases(c)) == 1 and c.status().phase == "learning",
          "%s: events without the applied point don't advance or stop the run" % tag)
    c.T.traitServer(1)
    check(purchases(c) == ["Deflection"] * 2 and commits(c) == 2 and c.text(c.learn) == "Learning 2 / 17",
          "%s: next point only after TRAIT_CONFIG_UPDATED + read-back: %s" % (tag, c.text(c.learn)))
    labels = []
    while c.ev("#TEST.traitQueue") > 0:
        c.T.traitServer(1)
        labels.append(c.text(c.learn))
    check(purchases(c) == order17 and commits(c) == 17, "%s: whole run: 17 purchases in order, 17 commits" % tag)
    check(labels[:2] == ["Learning 3 / 17", "Learning 4 / 17"] and labels[-1] == "Learn talents",
          "%s: traits: label counts up, back to 'Learn talents'" % tag)
    check(exact_build(c) and c.ev("TEST.talentPoints") == 0 and all(staged_of(c, n) == 0 for n in deep["ranks"]),
          "%s: traits: the game has exactly the build, nothing left staged" % tag)
    check(c.said("Learned 17 talent points.") and c.status().phase == "done" and "Learned 17 talent points." in c.status_line(),
          "%s: traits: 'Learned 17 talent points.' in chat and on the tab" % tag)
    check(c.ev("TEST.talentWrites") == 34, "%s: traits: exactly 34 writes (17 x purchase + commit)" % tag)
    nchat = len(c.chat())
    c.T.runTimers()
    check(len(c.chat()) == nchat and c.status().phase == "done" and len(purchases(c)) == 17,
          "%s: traits: stale timeouts after success do nothing" % tag)
    check(len(lua_table_to_list(c.T.calls)) == 0, "%s: traits: no macro API calls" % tag)
    check(c.ev("R2F.TalentPanel.Result().plan.summary") == "You already have this whole build.",
          "%s: traits: afterwards the preview shows the whole build" % tag)
    # Fewer points: only the 'now' points; singular.
    c = ctx(pts=12)
    c.click(c.learn)
    check(c.popup() == "Learn 12 talent points? Only a trainer reset can undo this.", "%s: traits: popup counts 'now' points" % tag)
    c.accept()
    drain(c)
    check(purchases(c) == order17[:12] and c.said("Learned 12 talent points."), "%s: traits: partial build, first 12 in order" % tag)
    c = ctx(pts=1, lnk="warrior/1~" + wh)
    c.click(c.learn)
    c.accept()
    drain(c)
    check(c.said("Learned 1 talent point.") and purchases(c) == ["Improved Heroic Strike"], "%s: traits: single point" % tag)

    # ---- Immediate model (no commit): event-driven, and timeout-only ----------------
    c = ctx("immediate")
    c.click(c.learn)
    c.accept()
    check(trait_calls(c) == ["purchase:Deflection"], "%s: immediate: no CommitConfig on this client -> purchase only" % tag)
    drain(c)
    check(purchases(c) == order17 and exact_build(c) and c.said("Learned 17 talent points."),
          "%s: immediate: full run on TRAIT_CONFIG_UPDATED" % tag)
    c = ctx("immediate")
    c.click(c.learn)
    c.accept()
    c.lua.execute("TEST.traitQueue = {}")      # never any event: only the timeouts' read-backs
    for _ in range(17):
        c.T.runTimersOnce()
        c.lua.execute("TEST.traitQueue = {}")
    check(purchases(c) == order17 and exact_build(c) and c.said("Learned 17 talent points."),
          "%s: immediate: no events at all -> each timeout's read-back confirms (rank AND free points)" % tag)

    # ---- Async model (delayed TRAIT_CONFIG_UPDATED, server applies later) --------------
    c = ctx("async")
    c.click(c.learn)
    c.accept()
    check(c.rank("Deflection") == 0 and c.status().phase == "learning", "%s: async: sent, nothing applied yet" % tag)
    drain(c)
    check(purchases(c) == order17 and exact_build(c) and c.said("Learned 17 talent points.")
          and c.ev("R2F.Talents.LearnMode()") == "traits", "%s: async: full run, stays in traits mode" % tag)

    # ---- A rejected purchase mid-run: stop, guided fallback, nothing more fired --------
    c = ctx()
    c.click(c.learn)
    c.accept()
    c.T.traitServer(3)                          # 3 applied; the 4th is in flight
    c.T.purchaseRejects = True
    c.T.traitServer(1)                          # 4th applied -> 5th purchase refused
    want = "Stopped at Deflection: the game didn't accept the point. 4 of 17 learned. " + HINT
    check(c.status().phase == "stopped" and c.said(want), "%s: refused purchase -> stop + guided hint: %s" % (tag, c.chat()[-1:]))
    check(want in c.status_line(), "%s: refused purchase: red line on the tab" % tag)
    check(purchases(c) == ["Deflection"] * 5 and commits(c) == 4, "%s: the refused purchase isn't committed" % tag)
    check(c.ev("R2F.Talents.LearnMode()") == "guided", "%s: anything unexpected -> guided for the session" % tag)
    writes = c.ev("TEST.talentWrites")
    c.T.purchaseRejects = False
    c.T.fire("TRAIT_CONFIG_UPDATED", 7001)
    c.T.runTimers()
    check(c.ev("TEST.talentWrites") == writes, "%s: stays stopped on later events / timers" % tag)
    c.click(c.learn)
    check(c.popup() is None and c.status().mode == "guided" and c.said("Click Deflection (5 of 17)"),
          "%s: Learn continues the SAME run in guided mode (5 of 17), no popup" % tag)
    for n in order17[4:]:
        c.T.playerLearn({"Booming Voice": 2, "Shield Specialization": 3}.get(n, 1), c.index_of(n))
    check(c.said("Learned 17 talent points.") and exact_build(c) and c.ev("TEST.talentWrites") == writes,
          "%s: guided fallback finishes the build; no C_Traits write after the fallback" % tag)
    c.lua.execute("R2F.Talents.ResetSession()")
    check(c.ev("R2F.Talents.LearnMode()") == "traits", "%s: a new session (/reload) tries traits again" % tag)
    # PurchaseRank raising.
    c = ctx(extra="TEST.purchaseError = 'some client error'")
    c.click(c.learn)
    c.accept()
    check(c.said("Stopped at Deflection: the game didn't accept the point. 0 of 17 learned. " + HINT)
          and commits(c) == 0 and c.ev("R2F.Talents.LearnMode()") == "guided", "%s: PurchaseRank error -> refused, guided" % tag)
    # CanEditConfig says no: nothing purchased at all.
    c = ctx(extra="C_Traits.CanEditConfig = function() return false, 'nope' end")
    c.click(c.learn)
    c.accept()
    check(c.ev("TEST.talentWrites") == 0 and c.status().phase == "stopped" and c.ev("R2F.Talents.LearnMode()") == "guided",
          "%s: CanEditConfig false -> stopped before any purchase, guided" % tag)
    # The node's own canPurchaseRank = false: tier/prerequisite stop, nothing sent.
    c = ctx(extra="TEST.canPurchaseRank = false")
    c.click(c.learn)
    c.accept()
    check(c.said("Stopped at Deflection: its tier or prerequisite isn't met in your game. 0 of 17 learned.")
          and c.ev("TEST.talentWrites") == 0, "%s: canPurchaseRank false -> 'locked' stop, nothing sent" % tag)
    # Shared re-verification still runs first (tier rule on live ranks).
    c = ctx(pts=1, lnk="warrior/0001~" + wh)
    c.click(c.learn)
    c.accept()
    check(c.said("Stopped at Improved Charge: its tier or prerequisite isn't met in your game. 0 of 1 learned.")
          and c.ev("TEST.talentWrites") == 0, "%s: traits: tier re-check stops before PurchaseRank" % tag)
    # ADDON_ACTION_FORBIDDEN for PurchaseRank: stopped at once.
    c = ctx(extra="TEST.purchaseForbidden = true")
    c.click(c.learn)
    c.accept()
    check(c.status().phase == "stopped" and commits(c) == 0 and c.ev("R2F.Talents.LearnMode()") == "guided"
          and c.said("Stopped at Deflection: the game didn't accept the point. 0 of 17 learned. " + HINT),
          "%s: ADDON_ACTION_FORBIDDEN on PurchaseRank -> stop, no commit, guided" % tag)
    c = ctx()
    c.T.fire("ADDON_ACTION_FORBIDDEN", "OtherAddon", "C_Traits.PurchaseRank()")
    c.T.fire("ADDON_ACTION_BLOCKED", "RoadToForever", "CastSpellByName()")
    check(c.ev("R2F.Talents.LearnMode()") == "traits", "%s: other addons' / other functions' events ignored" % tag)
    c.T.fire("ADDON_ACTION_BLOCKED", "RoadToForever", "LearnTalent()")
    check(c.ev("R2F.Talents.LearnMode()") == "traits", "%s: a LearnTalent block says nothing about C_Traits" % tag)

    # ---- Read-back catches a false success ------------------------------------------
    c = ctx(extra="TEST.purchaseLies = true")
    c.click(c.learn)
    c.accept()
    check(trait_calls(c) == ["purchase:Deflection"] and c.status().phase == "learning",
          "%s: 'true' that changed nothing: nothing to commit, waiting" % tag)
    c.T.fire("TRAIT_CONFIG_UPDATED", 7001)
    check(c.status().phase == "learning", "%s: an event alone proves nothing" % tag)
    c.T.runTimers()
    check(c.said("Stopped at Deflection: the game didn't accept the point. 0 of 17 learned. " + HINT)
          and c.rank("Deflection") == 0 and len(purchases(c)) == 1 and c.ev("R2F.Talents.LearnMode()") == "guided",
          "%s: false success caught by the read-back at the timeout; guided" % tag)
    # activeRank that counts STAGED ranks (field semantics differ) + no commit
    # function: the rank alone would say "learned"; the free points don't.
    c = ctx("stagedNoCommit", extra="TEST.activeIncludesStaged = true")
    c.click(c.learn)
    c.accept()
    c.T.fire("TRAIT_TREE_CURRENCY_INFO_UPDATED", 1100)
    check(c.status().phase == "learning", "%s: activeRank includes staged: rank says yes, free points say no -> still waiting" % tag)
    c.T.runTimers()
    staged_msg = ("Stopped at Deflection: the point is waiting in Blizzard's talent window but wasn't applied. "
                  "Click Apply Changes there to keep it, or undo it there. 0 of 17 learned. " + HINT)
    check(c.said(staged_msg) and c.status().done == 0 and len(purchases(c)) == 1,
          "%s: ... never counted as learned; 'waiting in Blizzard's window' stop: %s" % (tag, c.chat()[-1:]))
    c.T.playerApply()
    check(c.said("The point in Deflection arrived late after all. 1 of 17 learned. Click Learn talents to continue.")
          and c.ev("R2F.Talents.LearnMode()") == "guided",
          "%s: player's Apply Changes -> counted late; the session stays guided" % tag)
    # The same semantics WITH CommitConfig: committed, then really confirmed.
    c = ctx(extra="TEST.activeIncludesStaged = true")
    c.click(c.learn)
    c.accept()
    drain(c)
    check(c.said("Learned 17 talent points.") and exact_build(c) and commits(c) == 17,
          "%s: activeRank-includes-staged client with CommitConfig: every point committed and confirmed" % tag)
    # Staged, no CommitConfig (normal fields): handed to the player's Apply Changes.
    c = ctx("stagedNoCommit")
    c.click(c.learn)
    c.accept()
    check(staged_of(c, "Deflection") == 1 and commits(c) == 0, "%s: no CommitConfig: the point stays staged" % tag)
    c.T.runTimers()
    check(c.said(staged_msg) and c.ev("R2F.Talents.LearnMode()") == "guided", "%s: no CommitConfig -> 'Apply Changes' stop, guided" % tag)
    c.click(c.learn)
    check(c.status().mode == "guided" and c.ev("TEST.talentWrites") == 1, "%s: ... Learn continues guided, nothing more written" % tag)

    # ---- Commit failures --------------------------------------------------------------
    c = ctx(extra="TEST.commitRejects = true")
    c.click(c.learn)
    c.accept()
    check(c.said(staged_msg) and c.status().phase == "stopped" and c.ev("R2F.Talents.LearnMode()") == "guided",
          "%s: CommitConfig returns false -> stop at once ('waiting in Blizzard's window'), guided" % tag)
    c = ctx(extra="TEST.commitError = 'boom'")
    c.click(c.learn)
    c.accept()
    check(c.said(staged_msg), "%s: CommitConfig raising -> same stop" % tag)
    c = ctx(extra="TEST.commitServerFails = true")
    c.click(c.learn)
    c.accept()
    c.T.fire("CONFIG_COMMIT_FAILED", 9999)
    check(c.status().phase == "learning", "%s: CONFIG_COMMIT_FAILED for another config is ignored" % tag)
    c.T.traitServer()
    check(c.said(staged_msg) and c.status().phase == "stopped" and len(lua_table_to_list(c.T.timers)) >= 1,
          "%s: CONFIG_COMMIT_FAILED -> stop at once, without waiting for the timeout" % tag)
    c = ctx(extra="TEST.serverRejects = true")
    c.click(c.learn)
    c.accept()
    c.T.traitServer()
    c.T.runTimers()
    check(c.said(staged_msg) and c.rank("Deflection") == 0, "%s: server silently applies nothing -> timeout stop" % tag)

    # ---- Combat mid-run ---------------------------------------------------------------
    c = ctx()
    c.click(c.learn)
    c.accept()
    c.T.traitServer(5)                          # 5 applied; the 6th purchased + committed
    writes = c.ev("TEST.talentWrites")
    c.combat(True)
    check(c.said(STOP_COMBAT % (5, 17)) and c.status().phase == "stopped", "%s: traits: combat -> stop at once" % tag)
    check(c.enabled(c.learn) is False, "%s: traits: Learn greyed out in combat" % tag)
    c.T.traitServer()                           # the commit in flight lands anyway
    check(c.said(STOP_COMBAT % (6, 17)), "%s: traits: the point in flight is counted when it lands" % tag)
    c.T.runTimers()
    c.lua.execute("R2F.TalentPanel.Learn()")
    check(c.ev("TEST.talentWrites") == writes and c.popup() is None, "%s: traits: nothing written in combat" % tag)
    c.combat(False)
    c.click(c.learn)
    check(c.popup() is None and c.text(c.learn) == "Learning 7 / 17" and c.status().mode == "traits",
          "%s: traits: resume after combat from 7 / 17, still traits" % tag)
    drain(c)
    check(purchases(c) == order17 and exact_build(c) and c.said("Learned 17 talent points."),
          "%s: traits: resumed run completes, exactly the build" % tag)
    c = ctx()
    c.click(c.learn)
    c.accept()
    c.lua.execute("R2F.inCombat = true")
    c.T.traitServer(1)
    check(c.said(STOP_COMBAT % (1, 17)) and len(purchases(c)) == 1, "%s: traits: combat flag checked before every purchase" % tag)
    # Popup accepted in combat: queued, starts after.
    c = ctx()
    c.click(c.learn)
    c.combat(True)
    c.accept()
    check(c.ev("TEST.talentWrites") == 0 and c.status().phase == "queued" and c.text(c.learn) == "After combat",
          "%s: traits: accepted in combat -> queued, nothing written" % tag)
    c.combat(False)
    check(purchases(c) == ["Deflection"] and c.status().mode == "traits", "%s: traits: starts on PLAYER_REGEN_ENABLED" % tag)
    drain(c)
    check(c.said("Learned 17 talent points."), "%s: traits: queued run completes" % tag)

    # ---- No double send ----------------------------------------------------------------
    c = ctx()
    c.click(c.learn)
    c.accept()
    c.T.traitServer(10)                         # Shield Specialization (11th, 1 rank) in flight
    check(purchases(c)[-1] == "Shield Specialization", "%s: (setup) Shield Specialization in flight" % tag)
    c.click(c.cancel)
    c.click(c.learn)
    check(purchases(c).count("Shield Specialization") == 1 and c.status().phase == "learning",
          "%s: traits: Stop + Learn at once waits for the point in flight" % tag)
    drain(c)
    c.T.runTimers()
    check(purchases(c) == order17 and c.rank("Shield Specialization") == 1 and exact_build(c)
          and c.said("Learned 17 talent points."), "%s: traits: no double send, Shield Specialization 1 / 1" % tag)
    # The commit got lost: in traits mode it is NEVER re-sent (a second purchase
    # could stack on an invisible one); it's reported, guided takes over.
    c = ctx()
    c.click(c.learn)
    c.accept()
    c.T.traitServer(10)
    c.click(c.cancel)
    c.lua.execute("TEST.traitQueue = {}")
    c.click(c.learn)
    c.T.runTimersOnce()
    check(purchases(c).count("Shield Specialization") == 1 and c.status().phase == "stopped"
          and c.said(staged_msg.replace("Deflection", "Shield Specialization").replace("0 of 17", "10 of 17")),
          "%s: traits: a lost commit is not re-sent; stop says it's waiting in Blizzard's window: %s" % (tag, c.chat()[-1:]))
    c.T.playerApply()
    check(c.rank("Shield Specialization") == 1 and c.said("The point in Shield Specialization arrived late after all. "
                                                          "11 of 17 learned. Click Learn talents to continue."),
          "%s: ... the player's Apply Changes lands it once, counted late" % tag)
    # Player's own un-applied changes in Blizzard's window: never committed by us.
    c = ctx()
    c.T.playerStage(1, c.index_of("Improved Heroic Strike"))
    c.click(c.learn)
    c.accept()
    pend = ("Stopped: Blizzard's talent window has changes that aren't applied yet. Apply or undo them there first. "
            "0 of 17 learned. Click Learn talents to continue.")
    check(c.said(pend) and c.ev("TEST.talentWrites") == 0, "%s: staged changes of the player's -> stop before any write" % tag)
    check(c.ev("R2F.Talents.LearnMode()") == "traits", "%s: ... no guided switch for that (nothing was sent)" % tag)
    c.lua.execute("for _, x in ipairs(TEST.talentTabs[1]) do x.staged = 0 end")    # player undoes it
    c.click(c.learn)
    check(c.popup() is None and purchases(c) == ["Deflection"], "%s: ... undone -> Learn continues, no popup" % tag)
    drain(c)
    check(c.said("Learned 17 talent points.") and c.rank("Improved Heroic Strike") == 0,
          "%s: ... and the run never applied the player's staged talent" % tag)
    # Same, on a client whose node fields can't show staging (activeRank counts
    # staged ranks): only the currency (with vs without staged) reveals it.
    # (A build talent, so the preview, which then sees it as applied, stays learnable.)
    c = ctx(extra="TEST.activeIncludesStaged = true")
    c.T.playerStage(1, c.index_of("Deflection"))
    c.preview(link)
    c.click(c.learn)
    c.accept()
    check(c.said(pend.replace("0 of 17", "0 of 16")) and c.ev("TEST.talentWrites") == 0,
          "%s: player's staged change invisible in node fields -> caught by the currency, nothing written" % tag)
    # Something staged appears between the purchase and the commit: no commit.
    c = ctx(extra="local P = C_Traits.PurchaseRank C_Traits.PurchaseRank = function(...) local r = P(...)"
                  " TEST.playerStage(1, 1) return r end")
    c.click(c.learn)
    c.accept()
    check(commits(c) == 0 and c.said(staged_msg), "%s: other staged changes right before the commit -> no commit" % tag)
    # Window closed mid-run; Stop + late answer.
    c = ctx()
    c.click(c.learn)
    c.accept()
    c.lua.execute("R2F.MainWindow.Hide()")
    drain(c)
    check(c.said("Learned 17 talent points."), "%s: traits: run finishes with the window closed" % tag)
    c = ctx()
    c.click(c.learn)
    c.accept()
    c.T.traitServer(2)
    c.click(c.cancel)
    check(c.said("Stopped. 2 of 17 learned. Click Learn talents to continue."), "%s: traits: Stop" % tag)
    c.T.traitServer()
    check(c.said("Stopped. 3 of 17 learned. Click Learn talents to continue.") and len(purchases(c)) == 3,
          "%s: traits: the point already sent is counted, nothing new sent" % tag)
    c.click(c.learn)
    drain(c)
    check(purchases(c) == order17 and c.said("Learned 17 talent points."), "%s: traits: resume after Stop" % tag)
    # A point spent elsewhere mid-run -> conflict -> stop (shared verify).
    c = ctx()
    c.click(c.learn)
    c.accept()
    c.T.traitServer(2)
    c.T.playerLearn(1, c.index_of("Improved Heroic Strike"))
    c.T.traitServer()
    check(c.said("Stopped: your talents changed while learning. 3 of 17 learned. Check the preview, then click Learn talents again."),
          "%s: traits: a point outside the build mid-run -> stop" % tag)

    # ---- Globals -----------------------------------------------------------------------
    new_globals = c.ev("""(function()
      local out = {}
      for k in pairs(_G) do if not BEFORE[k] then table.insert(out, k) end end
      table.sort(out) return table.concat(out, ",") end)()""").split(",")
    bad = [g for g in new_globals if g and g not in ("NS", "LBTN", "LHINT", "LST")
           and not g.startswith("TalentFrame") and g not in BINDING_GLOBALS
           and g not in ("SLASH_R2F1", "SLASH_R2FT1") and not g.startswith("R2F")]
    check(not bad, "%s: traits mode adds no globals: %s" % (tag, bad))


def test_free_points(templates):
    """13.12: unspent talent points. WoW Forever: C_Traits' tree currency (the
    real screenshot: 'Unspent Talents: 17' while the addon said 0). Classic:
    UnitCharacterPoints, unchanged. Neither: 'unknown', never a guessed 0."""
    tag = "templates" if templates else "fallbacks"
    fxt = json.load(open(TALENT_FIXTURE, encoding="utf-8"))
    raw = fxt["talents"]
    js = talent_js()
    W = js["classes"]["warrior"]
    wh = js["hashes"]["warrior"]
    deep = fxt["scenarios"][5]
    link = "%swarrior/%s~%s" % (SITE_TALENTS, deep["code"], wh)

    def home(lua):
        lua.execute("R2F.MainWindow.Show('home')")
        return lua.eval("R2F.Home.TalentLine()")

    # The screenshot's case: talents reset, 17 unspent; the legacy call says 0.
    c = LearnCtx(templates, {}, 17, link, raw, W, forever_setup("staged", "UnitCharacterPoints = function() return 0 end"))
    n, src = c.ev("R2F.Talents.FreePointsInfo()")
    check(n == 17 and src == "traits", "%s: Forever: 17 unspent from C_Traits' tree currency (legacy call says 0): %s %s" % (tag, n, src))
    check(c.ev("R2F.Minimap.FreeTalentPoints()") == 17 and c.ev("R2F.Talents.FreePoints()") == 17,
          "%s: Forever: minimap tooltip and the engine read the same 17" % tag)
    check(c.ev("R2F.TalentPanel.Result().plan.summary") == "This build uses 17 points. You have 17 free. All 17 will be learned."
          and c.enabled(c.learn) is True, "%s: Forever: the Talents tab sees the 17 points and Learn is enabled" % tag)
    check(home(c.lua) == "17 free talent points", "%s: Forever: Home says 17 free talent points" % tag)
    c.lua.execute("GameTooltip:SetOwner() R2F.Minimap.FillTooltip(GameTooltip)")
    check("17 free talent points" in lua_table_to_list(c.ev("GameTooltip.lines")), "%s: Forever: minimap tooltip line" % tag)
    # The applied amount: staged changes in Blizzard's window don't count yet.
    c.T.playerStage(1, c.index_of("Deflection"))
    check(c.ev("R2F.Talents.FreePoints()") == 17, "%s: staged (un-applied) changes don't lower the free points" % tag)
    args = c.ev("(function() local real = C_Traits.GetTreeCurrencyInfo local seen"
                " C_Traits.GetTreeCurrencyInfo = function(cfg, tree, ex) seen = { cfg, tree, tostring(ex) } return real(cfg, tree, ex) end"
                " R2F.Talents.FreePoints() C_Traits.GetTreeCurrencyInfo = real return seen end)()")
    check(lua_table_to_list(args) == [7001, 1100, "true"], "%s: called as (configID, treeID, excludeStagedChanges=true): %s"
          % (tag, lua_table_to_list(args)))
    # Odd answers -> unknown, never a guess.
    lua = c.lua
    lua.execute("REAL_TCI = C_Traits.GetTreeCurrencyInfo UnitCharacterPoints = nil")
    cases = [
        ("function() return { { traitCurrencyID = 1, quantity = 17 }, { traitCurrencyID = 2, quantity = 3 } } end", None),
        ("function() return { { traitCurrencyID = 1, quantity = 9 }, { traitCurrencyID = 2, quantity = 9 } } end", 9),
        ("function() return {} end", None),
        ("function() return { { traitCurrencyID = 1, quantity = -1 } } end", None),
        ("function() return { { traitCurrencyID = 1, quantity = 'x' } } end", None),
        ("function() return { { traitCurrencyID = 1 } } end", None),
        ("function() return nil end", None),
        ("function() error('boom') end", None),
        ("function() return { { quantity = 4 } } end", 4),
    ]
    for fn, want in cases:
        lua.execute("C_Traits.GetTreeCurrencyInfo = " + fn)
        check(lua.eval("(R2F.Talents.FreePointsInfo())") == want, "%s: currency answer %s -> %s" % (tag, fn, want))
    lua.execute("C_Traits.GetTreeCurrencyInfo = REAL_TCI")
    # One tree per pane sharing one currency: counted once, not three times.
    lua.execute("TEST.traitLayout = 'perPane'")
    check(lua.eval("(R2F.Talents.FreePointsInfo())") == 17, "%s: per-pane trees sharing a currency -> 17, not 51" % tag)
    lua.execute("TEST.traitLayout = 'single'")
    # No currency API on a trait client: the legacy call's 0 there is the bug
    # itself, so it's 'unknown'; a positive legacy answer is believed.
    lua.execute("C_Traits.GetTreeCurrencyInfo = nil UnitCharacterPoints = function() return 0 end")
    check(lua.eval("R2F.Talents.FreePointsInfo()") is None, "%s: trait client, no currency API, legacy 0 -> unknown" % tag)
    lua.execute("UnitCharacterPoints = function() return 4 end")
    n, src = lua.eval("R2F.Talents.FreePointsInfo()")
    check(n == 4 and src == "classic", "%s: trait client, no currency API, legacy 4 -> 4" % tag)
    # Neither works: unknown, said as such, Learn stays off.
    lua.execute("UnitCharacterPoints = nil")
    c.lua.execute("for _, l in ipairs(TEST.talentTabs) do for _, x in ipairs(l) do x.staged = 0 end end")
    c.lua.execute("R2F.MainWindow.Show('talents')")          # home() above switched tabs
    c.preview(link)
    plan = c.ev("R2F.TalentPanel.Result().plan")
    check(plan.freeKnown is False and plan.free == 0 and plan.learnable is False
          and plan.summary == c.ev("R2F.L.TALENT_SUMMARY_POINTS_UNKNOWN"),
          "%s: no usable answer -> 'couldn't read your free talent points', not 'No free talent points.'" % tag)
    check(c.enabled(c.learn) is False, "%s: unknown free points -> Learn disabled" % tag)
    c.lua.execute("R2F.TalentPanel.Learn()")
    check(c.popup() is None and c.ev("TEST.talentWrites") == 0, "%s: unknown free points -> Learn() refuses, nothing written" % tag)
    check(home(c.lua) == "Free talent points: couldn't read them", "%s: Home says it couldn't read them" % tag)
    check(c.ev("R2F.Minimap.FreeTalentPoints()") == 0, "%s: minimap: unknown counts as 0 (no tooltip line)" % tag)

    # Classic-era client (no trait config at all): UnitCharacterPoints, unchanged.
    cl = new_runtime(templates, before_load="C_Traits = nil C_SpecializationInfo = nil")
    T = cl.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    T.talentPoints = 5
    n, src = cl.eval("R2F.Talents.FreePointsInfo()")
    check(n == 5 and src == "classic" and cl.eval("R2F.Minimap.FreeTalentPoints()") == 5,
          "%s: Classic: UnitCharacterPoints('player') = 5 -> 5" % tag)
    check(home(cl) == "5 free talent points", "%s: Classic: Home line" % tag)
    T.talentPoints = 0
    n, src = cl.eval("R2F.Talents.FreePointsInfo()")
    check(n == 0 and src == "classic" and home(cl) == "No free talent points",
          "%s: Classic: a real 0 is still 'No free talent points'" % tag)
    cl.execute("UnitCharacterPoints = function() return nil end")
    check(cl.eval("R2F.Talents.FreePointsInfo()") is None, "%s: Classic: a non-number answer -> unknown" % tag)
    cl.execute("UnitCharacterPoints = nil")
    check(cl.eval("R2F.Talents.FreePointsInfo()") is None and cl.eval("R2F.Minimap.FreeTalentPoints()") == 0
          and home(cl) == "Free talent points: couldn't read them", "%s: no API at all -> unknown, no error" % tag)
    # Trait config not ready yet (right after login): the legacy call is used as on Classic.
    lua2 = new_runtime(templates)
    T2 = lua2.eval("TEST")
    T2.fire("ADDON_LOADED", "RoadToForever")
    T2.fire("PLAYER_LOGIN")
    T2.traitsReady = False
    T2.talentPoints = 3
    check(lua2.eval("(R2F.Talents.FreePointsInfo())") == 3, "%s: no trait config yet -> legacy call" % tag)


def test_talent_source_traits():
    """13.12's write discipline on the source: PurchaseRank and CommitConfig are
    called in exactly one function (purchasePoint, Talents.lua), after its
    combat check; the refund / reset / bulk C_Traits writes are never touched;
    the shared plan/order code is byte-identical to the last release."""
    calls = []
    for dirpath, _, names in os.walk(ADDON):
        for n in names:
            if n.endswith(".lua"):
                for i, line in enumerate(open(os.path.join(dirpath, n), encoding="utf-8"), 1):
                    code = line.split("--", 1)[0]
                    for api in ("PurchaseRank", "CommitConfig", "RefundRank", "RollbackConfig", "ResetTree",
                                "PurchaseAllRanks", "TryPurchaseAllRanks", "TryPurchaseToNode",
                                "CascadeRepurchaseRanks", "StageConfig"):
                        if re.search(r"\b%s\b" % api, code):
                            calls.append((n, api, code.strip()))
    used = sorted({(n, a) for n, a, _ in calls})
    check(used == [("Talents.lua", "CommitConfig"), ("Talents.lua", "PurchaseRank")],
          "only PurchaseRank and CommitConfig, only in Talents.lua; no refund/reset/bulk writes: %s" % used)
    src = open(os.path.join(ADDON, "Talents.lua"), encoding="utf-8").read().replace("\r\n", "\n")
    body = src[src.index("local function purchasePoint(r, p)"):]
    body = body[:body.index("\nend\n")]
    rest = src.replace(body, "")
    check(not re.search(r"C_Traits\.(PurchaseRank|CommitConfig)\s*,|C_Traits\.(PurchaseRank|CommitConfig)\s*\(",
                        "\n".join(l.split("--", 1)[0] for l in rest.splitlines())),
          "PurchaseRank / CommitConfig are only called inside purchasePoint")
    check(body.index("R2F.InCombat()") < body.index("C_Traits.PurchaseRank"), "purchasePoint checks combat before PurchaseRank")
    check(body.index("pendingElsewhere(configID, nil)") < body.index("C_Traits.PurchaseRank")
          and body.index("x.name ~= p.name") < body.index("C_Traits.PurchaseRank"),
          "purchasePoint checks the node's name and staged changes before PurchaseRank")
    check(body.count("pcall(C_Traits.PurchaseRank") == 1 and body.count("pcall(C_Traits.CommitConfig") == 1,
          "both writes are pcall-wrapped")
    # The shared plan / order code is untouched (byte for byte vs the v0.10.5 tag).
    try:
        old = subprocess.run(["git", "show", "r2f-v0.10.5:addon/RoadToForever/Talents.lua"], capture_output=True,
                             check=True, cwd=ROOT).stdout.decode("utf-8").replace("\r\n", "\n")
    except (subprocess.CalledProcessError, OSError):
        old = None
    if old is not None:
        def fn(text, head):
            t = text[text.index(head):]
            return t[:t.index("\nend\n")]
        for head in ("function Talents.LearnOrder(plan)", "local function verify(r, p)",
                     "function Talents.Encode(trees)", "function Talents.Hash(trees)"):
            check(fn(src, head) == fn(old, head), "unchanged since v0.10.5: %s" % head)
        lp_old, lp_new = fn(old, "function Talents.LearnPoints(plan)"), fn(src, "function Talents.LearnPoints(plan)")
        check(lp_new.replace(", nodeID = e.nodeID", "") == lp_old,
              "LearnPoints: only the nodeID field added")


def test_talent_source_writes():
    """Step 10's write discipline (ADDON_PLAN 13.8), on the source itself:
    LearnTalent is CALLED in exactly one place (learnPoint in Talents.lua, right
    after its combat check); AddPreviewTalentPoints only in FillPreview;
    LearnPreviewTalents (Blizzard's commit) is never called, only detected; no
    talent API in any other file; guided mode never writes to Blizzard frames."""
    calls, refs = [], []
    for dirpath, _, names in os.walk(ADDON):
        for n in names:
            if n.endswith(".lua"):
                for i, line in enumerate(open(os.path.join(dirpath, n), encoding="utf-8"), 1):
                    code = line.split("--", 1)[0]
                    for api in ("LearnTalent", "LearnPreviewTalents", "AddPreviewTalentPoints"):
                        if re.search(r"\b%s\b" % api, code):
                            refs.append((n, i, api, code.strip()))
                            if re.search(r"(\b%s\s*\(|pcall\(\s*%s\b)" % (api, api), code):
                                calls.append((n, api))
    check(calls == [("Talents.lua", "LearnTalent"), ("Talents.lua", "AddPreviewTalentPoints")],
          "LearnTalent called once and AddPreviewTalentPoints once, both in Talents.lua; "
          "LearnPreviewTalents never: %s" % calls)
    check(all(n == "Talents.lua" for n, _, _, _ in refs), "talent write API only referenced in Talents.lua: %s" % refs)
    src = open(os.path.join(ADDON, "Talents.lua"), encoding="utf-8").read()
    body = src[src.index("local function learnPoint(p)"):]
    body = body[:body.index("\nend\n")]
    check(body.index("R2F.InCombat()") < body.index("LearnTalent"), "learnPoint checks combat before LearnTalent")
    # 13.10: and confirms the Classic address names this very talent first.
    check(body.index("legacyMatches(") < body.index("LearnTalent"), "learnPoint checks the Classic address before LearnTalent")
    fill = src[src.index("function Talents.FillPreview(plan)"):]
    fill = fill[:fill.index("\nend\n")]
    check(fill.index("legacyMatches(") < fill.index("AddPreviewTalentPoints"),
          "FillPreview checks the Classic address before AddPreviewTalentPoints")
    code = "\n".join(l.split("--", 1)[0] for l in src.splitlines())
    check(not re.search(r"\b(GetNumTalentTabs|GetNumTalents|LoadAddOn|IsAddOnLoaded|Blizzard_TalentUI)\b", code),
          "Talents.lua no longer touches the Classic tab API or LoadAddOn (13.10)")
    guide =open(os.path.join(ADDON, "UI", "TalentGuide.lua"), encoding="utf-8").read()
    guide_code = "\n".join(l.split("--", 1)[0] for l in guide.splitlines())
    # Only our own frames (glow, host, label, texture) get written to.
    writes = re.findall(r"(\w+)[:.](SetScript|HookScript|SetPoint|SetParent|Show|Hide|SetSize|ClearAllPoints|Disable|Enable)\(",
                        guide_code)
    # ("TalentGuide" = our module's own function definitions, TalentGuide.Show etc.)
    check({w for w, _ in writes} <= {"glow", "host", "self", "label", "tex", "TalentGuide"},
          "TalentGuide only writes to its own frames: %s" % sorted({w for w, _ in writes}))
    check("CreateFrame(\"Frame\", nil, UIParent)" in guide_code and "_G[" in guide_code,
          "glow/host are unnamed frames on UIParent; Blizzard frames only looked up")
    toc = open(os.path.join(ADDON, "RoadToForever.toc"), encoding="utf-8").read()
    check("UI\\TalentPanel.lua" in toc and "UI\\TalentGuide.lua" in toc, "TalentPanel.lua and TalentGuide.lua in the TOC")
    check(re.search(r"^## Version: \d+\.\d+\.\d+$", toc, re.M) is not None, "TOC has a x.y.z version")


def test_quick_settings(templates, fx):
    """Quick settings (ADDON_PLAN 12.4.1): Home check boxes read GetCVar, write SetCVar
    (GetCVarDefault for the zoom's off value), refuse in combat, and the Macro Book
    hides exactly ANY/Zoom, ANY/HideGuild, ANY/HidePvP."""
    lua = new_runtime(templates)
    tag = "templates" if templates else "fallbacks"
    T = lua.eval("TEST")
    L = lua.eval("R2F.L")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    QS = lua.eval("R2F.QuickSettings")
    writes = lambda: lua_table_to_list(lua.eval("TEST.cvarWrites"))
    errors = lambda: lua_table_to_list(lua.eval("TEST.errors"))
    clear = lambda: lua.execute("TEST.cvarWrites = {} TEST.errors = {}")

    # ---- The three items match data.py's macros exactly (via macros.html) -----
    html = open(os.path.join(ROOT, "macros.html"), encoding="utf-8").read()
    data = json.loads(re.search(r"^const D = (.*);$", html, re.M).group(1))
    site = {"ANY/" + m["short"]: m for s in data["universal"]["sections"] for g in s["groups"] for m in g["macros"]
            if m.get("short")}
    items = [(lua.eval("R2F.QuickSettings.ITEMS[%d].macro" % i), lua.eval("R2F.QuickSettings.ITEMS[%d].cvar" % i),
              lua.eval("R2F.QuickSettings.ITEMS[%d].on" % i), lua.eval("R2F.QuickSettings.ITEMS[%d].off" % i))
             for i in range(1, lua.eval("#R2F.QuickSettings.ITEMS") + 1)]
    check([i[0] for i in items] == ["ANY/Zoom", "ANY/HideGuild", "ANY/HidePvP"], "exactly the three macro ids: %s" % items)
    for mid, cvar, on, _ in items:
        check(mid in site and site[mid]["code"] == "/console %s %s" % (cvar, on),
              "%s is data.py's '/console %s %s' macro" % (mid, cvar, on))
    check([(i[1], i[2], i[3]) for i in items] == [("cameraDistanceMaxZoomFactor", "4", None),
                                                  ("UnitNamePlayerGuild", "0", "1"), ("UnitNamePlayerPVPTitle", "0", "1")],
          "CVar values as BACKLOG specifies (zoom off = game default, not a constant)")
    zoom_ref = re.search(r"cameraDistanceMaxZoomFactor\", on = \"4\", off = nil", open(
        os.path.join(ADDON, "QuickSettings.lua"), encoding="utf-8").read())
    check(zoom_ref is not None, "zoom's off value is nil in the source (no hardcoded default)")

    # Import everything, as a player who picked every macro on the site would.
    parse = lua.eval("function(s) local a, b = R2F.Import.Parse(s) return a, b end")
    res, _ = parse(fx["everything"]["string"])
    lua.eval("R2F.Library.Apply")(res.records, 1)
    total = len(fx["everything"]["records"])

    # ---- Home opens: the boxes show the LIVE values ----------------------------
    # Set by "someone else" (a /console, another addon) before Home is opened.
    lua.execute("TEST.cvars.UnitNamePlayerGuild = '0' TEST.cvars.cameraDistanceMaxZoomFactor = '4.000000'")
    lua.execute('SlashCmdList.R2F("settings")')
    check(lua.eval("R2F.MainWindow.CurrentTab()") == "settings", "%s: /r2f settings opens the Settings tab" % tag)
    n = find_frames(lua, "f.qsItem ~= nil", "QSB")
    check(n == 3, "%s: three Quick settings boxes on the Settings tab (%d)" % (tag, n))
    check([lua.eval("QSB[%d].qsItem.key" % i) for i in (1, 2, 3)] == ["zoom", "guild", "pvp"], "boxes in item order")
    check([lua.eval("QSB[%d].r2fLabel.__text" % i) for i in (1, 2, 3)] == [L.QS_ZOOM, L.QS_GUILD, L.QS_PVP],
          "box labels: %s / %s / %s" % (L.QS_ZOOM, L.QS_GUILD, L.QS_PVP))
    check(lua.eval("QSB[1]:IsVisible() and QSB[3]:IsVisible()") is True, "boxes live on the visible Settings page")
    checked = lambda: [lua.eval("QSB[%d]:GetChecked()" % i) is True for i in (1, 2, 3)]
    enabled = lambda: [lua.eval("QSB[%d]:IsEnabled()" % i) is True for i in (1, 2, 3)]
    check(checked() == [True, True, False], "Settings open reads GetCVar: zoom 4.000000 + guild 0 set elsewhere -> ticked; "
          "pvp 1 -> unticked: %s" % checked())
    check(writes() == [], "opening Settings writes no CVar")
    check(enabled() == [True, True, True], "boxes enabled out of combat")
    check(find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.QS_TITLE", "QT") == 1 and
          find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.QS_NOTE", "QN") == 1,
          "Quick settings heading + note line on the Settings tab")

    # Changed elsewhere while Settings is showing: CVAR_UPDATE redraws (throttled).
    lua.execute("TEST.cvars.UnitNamePlayerPVPTitle = '0'")
    T.fire("CVAR_UPDATE", "UnitNamePlayerPVPTitle", "0")
    T.runTimers()
    check(checked() == [True, True, True], "CVAR_UPDATE from elsewhere ticks the pvp box")
    # Changed while another tab shows, no event: re-read when Home opens again.
    lua.execute("R2F.MainWindow.SelectTab('macros') TEST.cvars.UnitNamePlayerPVPTitle = '1' "
                "TEST.cvars.cameraDistanceMaxZoomFactor = '2.2' R2F.MainWindow.SelectTab('settings')")
    check(checked() == [False, True, False], "switching back to Settings re-reads every CVar (zoom 2.2 = not max)")

    # ---- Ticking / unticking writes exactly the right values -------------------
    clear()
    lua.execute("QSB[1]:Click()")
    check(writes() == ["cameraDistanceMaxZoomFactor=4"] and checked()[0], "tick zoom -> SetCVar(cameraDistanceMaxZoomFactor, 4)")
    clear()
    lua.execute("QSB[1]:Click()")
    check(writes() == ["cameraDistanceMaxZoomFactor=1.7"] and not checked()[0],
          "untick zoom -> the GetCVarDefault value (1.7): %s" % writes())
    # A different default in another client: still read, never assumed.
    lua.execute("TEST.cvarDefaults.cameraDistanceMaxZoomFactor = '2.6' TEST.cvars.cameraDistanceMaxZoomFactor = '4'"
                " R2F.Settings.Refresh()")
    clear()
    lua.execute("QSB[1]:Click()")
    check(writes() == ["cameraDistanceMaxZoomFactor=2.6"], "untick zoom follows GetCVarDefault (2.6): %s" % writes())
    clear()
    lua.execute("QSB[2]:Click()")
    check(writes() == ["UnitNamePlayerGuild=1"] and not checked()[1], "untick guild -> UnitNamePlayerGuild 1")
    clear()
    lua.execute("QSB[2]:Click()")
    check(writes() == ["UnitNamePlayerGuild=0"] and checked()[1], "tick guild -> UnitNamePlayerGuild 0")
    clear()
    lua.execute("QSB[3]:Click()")
    check(writes() == ["UnitNamePlayerPVPTitle=0"] and checked()[2], "tick pvp -> UnitNamePlayerPVPTitle 0")
    clear()
    lua.execute("QSB[3]:Click()")
    check(writes() == ["UnitNamePlayerPVPTitle=1"] and not checked()[2], "untick pvp -> UnitNamePlayerPVPTitle 1")
    check(errors() == [], "no errors on normal clicks: %s" % errors())
    # The flip is from the live value, not the button's own toggle.
    lua.execute("TEST.cvars.UnitNamePlayerPVPTitle = '0'")   # changed elsewhere, no event, box still unticked
    clear()
    lua.execute("QSB[3]:Click()")
    check(writes() == ["UnitNamePlayerPVPTitle=1"] and not checked()[2],
          "a click flips the LIVE value (0 -> 1), even when the box was stale")

    # No GetCVarDefault: zoom can't be unticked (no guessing); C_CVar fallback works.
    lua.execute("TEST.cvars.cameraDistanceMaxZoomFactor = '4' SAVED_DEF = GetCVarDefault GetCVarDefault = nil"
                " R2F.Settings.Refresh()")
    clear()
    lua.execute("QSB[1]:Click()")
    check(writes() == [] and errors() == [L.QS_NO_DEFAULT] and checked()[0],
          "no GetCVarDefault: untick refused with a message, nothing written, box stays ticked")
    check(lua.eval("R2F.QuickSettings.OffValue(R2F.QuickSettings.ITEMS[2])") == "1",
          "guild/pvp off value is the fixed 1 (no default needed)")
    lua.execute("C_CVar = { GetCVarDefault = function(n) return '1.9' end }")
    clear()
    lua.execute("QSB[1]:Click()")
    check(writes() == ["cameraDistanceMaxZoomFactor=1.9"], "C_CVar.GetCVarDefault used when the global is missing")
    lua.execute("GetCVarDefault = SAVED_DEF C_CVar = nil")

    # ---- Combat gate ------------------------------------------------------------
    T.fire("PLAYER_REGEN_DISABLED")       # flag set; InCombatLockdown() still false here
    check(enabled() == [False, False, False], "boxes greyed out in combat")
    check(lua.eval("QSB[1].r2fLabel.__color[1]") == 0.5, "labels grey while disabled")
    clear()
    lua.execute("QSB[2]:Fire('OnClick')")  # a click that lands anyway (between event and redraw)
    check(writes() == [] and errors() == [L.QS_COMBAT], "combat (event flag): click refused, nothing written: %s" % errors())
    T.combat = True
    clear()
    for i in (1, 2, 3):
        lua.execute("QSB[%d]:Fire('OnClick')" % i)
        check(lua.eval("R2F.QuickSettings.Set(R2F.QuickSettings.ITEMS[%d], true)" % i) is False,
              "Set refused in combat (item %d)" % i)
    check(writes() == [], "no SetCVar in combat at all (the stub would raise)")
    check(checked() == [False, True, False], "boxes still show the live values in combat")
    lua.execute("QSB[1]:Fire('OnEnter')")
    check(L.QS_TIP_COMBAT in lua_table_to_list(lua.eval("GameTooltip.lines")), "tooltip says why in combat")
    lua.execute("R2F.inCombat = false")    # lockdown only, no flag: still refused
    clear()
    lua.execute("R2F.QuickSettings.Toggle(R2F.QuickSettings.ITEMS[1])")
    check(writes() == [] and errors() == [L.QS_COMBAT], "InCombatLockdown alone also refuses")
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")
    check(enabled() == [True, True, True], "boxes enabled again after combat")
    clear()
    lua.execute("QSB[2]:Click()")
    check(writes() == ["UnitNamePlayerGuild=1"], "after combat a click works (nothing was queued meanwhile)")
    lua.execute("QSB[1]:Fire('OnEnter')")
    tip = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(tip[0] == L.QS_ZOOM and tip[1] == L.QS_ZOOM_TIP and L.QS_TIP_COMBAT not in tip, "tooltip out of combat: %s" % tip)

    # ---- The game refusing or clamping ------------------------------------------
    lua.execute("TEST.cvarClamp.cameraDistanceMaxZoomFactor = '3.4'")
    clear()
    lua.execute("QSB[1]:Click()")
    check(writes() == ["cameraDistanceMaxZoomFactor=4"] and errors() == [L.QS_NOT_ACCEPTED] and not checked()[0],
          "a clamped value is reported and the box shows the live 3.4 (unticked)")
    lua.execute("TEST.cvarClamp = {} TEST.cvarError = 'boom'")
    clear()
    lua.execute("QSB[3]:Click()")
    check(errors() == [L.QS_NOT_ACCEPTED], "SetCVar raising is caught (pcall) and reported")
    lua.execute("TEST.cvarError = nil")

    # ---- Macro Book: exactly the three ids hidden ------------------------------
    # A few look-alikes the filter must NOT catch (exact ids only).
    lua.execute("""R2F.Library.Apply({
      { id = 'ANY/ZoomIn', class = 'ANY', section = 'Universal', group = 'Misc / UI', name = 'Zoom in', short = 'ZoomIn',
        body = '/console cameraDistanceMaxZoomFactor 2' },
      { id = 'ANY/HideGuilds', class = 'ANY', section = 'Universal', group = 'Misc / UI', name = 'x', short = 'HideGuilds',
        body = '/console UnitNamePlayerGuild 0' },
      { id = 'WARRIOR/Zoom', class = 'WARRIOR', section = 'General', group = 'Class QoL', name = 'x', short = 'Zoom',
        body = '/console cameraDistanceMaxZoomFactor 4' },
    }, 2)""")
    for mid in ("ANY/ZoomIn", "ANY/HideGuilds", "WARRIOR/Zoom", "ANY/zoom", "ANY/Zoom ", "ANY/HidePvP2", "Zoom", ""):
        check(QS.HidesMacro(mid) is False, "look-alike id %r is not hidden" % mid)
    for mid in ("ANY/Zoom", "ANY/HideGuild", "ANY/HidePvP"):
        check(QS.HidesMacro(mid) is True, "%s hidden while its box works" % mid)

    def book_ids(section="Universal", cls="ANY"):
        lua.execute("R2F.MacroBook.ShowSection('%s', '%s')" % (cls, section))
        find_frames(lua, "f.__kind == 'Button' and f.__scripts.OnDragStart and f ~= R2FMinimapButton", "BS")
        find_frames(lua, "f.__kind == 'Button' and f.__normal and f.__normal.__tex and "
                    "f.__normal.__tex:find('NextPage%-Up')", "NEXTB")
        ids = []
        for _ in range(20):
            ids += [lua.eval("BS[%d].entry.id" % i) for i in range(1, 13) if lua.eval("BS[%d]:IsShown()" % i)]
            if not lua.eval("NEXTB[1]:IsEnabled()"):
                break
            lua.execute("NEXTB[1]:Click()")
        return ids

    universal = [r["id"] for r in fx["everything"]["records"] if r["class"] == "ANY"]
    for mid in ("ANY/Zoom", "ANY/HideGuild", "ANY/HidePvP"):
        check(mid in universal, "fixture (site import) contains %s" % mid)
    shown = book_ids()
    expected = [i for i in universal if i not in ("ANY/Zoom", "ANY/HideGuild", "ANY/HidePvP")]
    check(not {"ANY/Zoom", "ANY/HideGuild", "ANY/HidePvP"} & set(shown), "%s: Universal tab hides the three" % tag)
    check(set(expected) <= set(shown) and {"ANY/ZoomIn", "ANY/HideGuilds"} <= set(shown)
          and len(shown) == len(expected) + 2,
          "every other Universal macro (and both look-alikes) still shows: %d of %d" % (len(shown), len(expected) + 2))
    find_frames(lua, "f.__kind == 'CheckButton' and f.sec and f.__shown and f.sec.class == 'ANY'", "UT")
    lua.execute("UT[1]:Fire('OnEnter')")
    tip = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(tip[1] == "%d macros" % (len(expected) + 2), "Universal tab tooltip counts the visible macros: %s" % tip)
    check(find_frames(lua, "f.__kind == 'FontString' and type(f.__text) == 'string' and "
                      "f.__text:find(R2F.L.BOOK_QUICK_SETTINGS, 1, true)", "QNOTE") == 1,
          "Universal tab says where the three went")
    check("WARRIOR/Zoom" in book_ids("General", "WARRIOR"), "a class macro with short Zoom still shows (id differs)")
    check(lua.eval("R2F.Library.Get('ANY/Zoom') ~= nil and R2F.Library.Get('ANY/HidePvP') ~= nil"),
          "the three stay in the library (only the grid hides them)")
    lua.execute("R2F.MainWindow.SelectTab('home')")
    lua.execute("QHOME = nil for _, f in ipairs(TEST.allFrames) do if f.tab == 'macros' and not QHOME then QHOME = f end end")
    check(lua.eval("QHOME.sub.__text").startswith("%d macros in your library" % (total + 3)),
          "Home's library count still counts the whole library")

    # A box that can't work keeps its macro visible.
    lua.execute("R2F.MainWindow.SelectTab('settings') TEST.cvars.UnitNamePlayerPVPTitle = nil R2F.Settings.Refresh()")
    check(enabled() == [True, True, False] and checked()[2] is False, "unknown CVar: that box disabled + unticked")
    clear()
    lua.execute("QSB[3]:Fire('OnClick')")
    check(writes() == [] and errors() == [L.QS_UNAVAILABLE], "unknown CVar: click refused with a message")
    lua.execute("QSB[3]:Fire('OnEnter')")
    check(L.QS_UNAVAILABLE in lua_table_to_list(lua.eval("GameTooltip.lines")), "unknown CVar: tooltip says so")
    shown = book_ids()
    check("ANY/HidePvP" in shown and "ANY/Zoom" not in shown and "ANY/HideGuild" not in shown,
          "unknown CVar: only that macro comes back to the book")
    lua.execute("TEST.cvars.UnitNamePlayerPVPTitle = '1' SAVED_SET = SetCVar SetCVar = nil")
    shown = book_ids()
    check({"ANY/Zoom", "ANY/HideGuild", "ANY/HidePvP"} <= set(shown), "no SetCVar: all three macros show again")
    lua.execute("R2F.MainWindow.SelectTab('settings')")
    check(enabled() == [False, False, False], "no SetCVar: every box disabled")
    lua.execute("C_CVar = { SetCVar = SAVED_SET }")
    check(QS.HidesMacro("ANY/Zoom") is True, "C_CVar.SetCVar counts as available")
    lua.execute("SetCVar = SAVED_SET C_CVar = nil")

    # Library with only the hidden three: no Universal tab, but the note.
    lua.execute("R2F.Library.db.library = {}")
    lua.eval("R2F.Library.Apply")(lua.eval("""(function(recs)
      local out = {}
      for i = 1, #recs do local r = recs[i]
        if r.id == 'ANY/Zoom' or r.id == 'ANY/HideGuild' or r.id == 'ANY/HidePvP' then out[#out + 1] = r end
      end
      return out end)""")(res.records), 3)
    book_ids()
    check(find_frames(lua, "f.__kind == 'CheckButton' and f.sec and f.__shown", "VT") == 0,
          "only hidden macros: no tab")
    check(find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.EMPTY_CLASS", "EC") == 1 and
          find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.BOOK_QUICK_SETTINGS", "QN2") == 1,
          "only hidden macros: the empty-class text plus the Quick settings note")

    # ---- Nothing saved, no new globals, SetCVar only in QuickSettings.lua -------
    check(lua.eval("R2FDB.quick == nil and R2FDB.settings.quick == nil and R2FCharDB.quick == nil"),
          "Quick settings store nothing in SavedVariables")
    lua.execute("NEWG = {} for k in pairs(_G) do if not BEFORE[k] then NEWG[#NEWG + 1] = k end end")
    newg = set(lua_table_to_list(lua.eval("NEWG")))
    check(not any("Quick" in g or g.startswith("build") for g in newg), "%s: no Quick-settings globals: %s" % (tag, sorted(newg)))
    users = []
    for dirpath, _, names in os.walk(ADDON):
        for nm in names:
            if nm.endswith(".lua"):
                code = "\n".join(l.split("--", 1)[0] for l in open(os.path.join(dirpath, nm), encoding="utf-8"))
                if re.search(r"\b(SetCVar|GetCVar|GetCVarDefault)\b", code):
                    users.append(nm)
    check(users == ["QuickSettings.lua"], "CVar API only in QuickSettings.lua: %s" % users)
    src = open(os.path.join(ADDON, "QuickSettings.lua"), encoding="utf-8").read()
    body = src[src.index("function QuickSettings.Set("):]
    body = body[:body.index("\nend\n")]
    check(body.index("R2F.InCombat()") < body.index("pcall(set"), "Set checks combat before SetCVar")


def lua_literal(v):
    """Python view of a Lua value (lupa table / scalar) -> Lua source, to carry
    SavedVariables over into a fresh runtime (a simulated relog)."""
    if v is None:
        return "nil"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v)  # JSON string escapes are valid Lua for our ASCII/UTF-8 data
    items = ", ".join("[%s] = %s" % (lua_literal(k), lua_literal(v[k])) for k in list(v.keys()))
    return "{" + items + "}"


def login(templates, cls, saved=None):
    """Fresh client logged in as class token `cls`; `saved` = (R2FDB, R2FCharDB) source."""
    lua = new_runtime(templates)
    T = lua.eval("TEST")
    lua.execute("TEST.classToken = %r TEST.className = %r" % (cls, cls.capitalize()))
    if saved:
        lua.execute("R2FDB = %s R2FCharDB = %s" % saved)
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    return lua, T


def apply_classes(lua, fx, classes, now=1):
    """Store the site's records of the given classes (as an import would)."""
    lua.eval("""function(recs, keep, now)
      local out = {}
      for i = 1, #recs do if keep[recs[i].class] then out[#out + 1] = recs[i] end end
      R2F.Library.Apply(out, now) end""")(
        lua.eval("function(s) return (R2F.Import.Parse(s)).records end")(fx["everything"]["string"]),
        lua.table_from({c: True for c in classes}), now)


def book_state(lua):
    """Visible side tabs, picker buttons, slots and the bottom note of the Macro Book."""
    find_frames(lua, "f.__kind == 'CheckButton' and f.sec and f.__shown", "BTABS")
    find_frames(lua, "f.__kind == 'CheckButton' and f.cls and f.__shown", "PICKS")
    find_frames(lua, "f.__kind == 'Button' and f.__scripts.OnDragStart and f ~= R2FMinimapButton", "BSLOTS")
    tabs = [(lua.eval("BTABS[%d].sec.class" % i), lua.eval("BTABS[%d].sec.section" % i)) for i in range(1, lua.eval("#BTABS") + 1)]
    picks = [lua.eval("PICKS[%d].cls" % i) for i in range(1, lua.eval("#PICKS") + 1)]
    checked = [lua.eval("PICKS[%d]:GetChecked()" % i) is True for i in range(1, lua.eval("#PICKS") + 1)]
    return tabs, picks, checked


def font_text(lua, pattern):
    """Text of the first FontString whose text matches a Lua pattern (or None)."""
    lua.execute("FT = nil for _, f in ipairs(TEST.allFrames) do if f.__kind == 'FontString' and type(f.__text) == 'string'"
                " and f.__shown and f.__text:find(%s) then FT = f end end" % json.dumps(pattern))
    return lua.eval("FT and FT.__text")


def test_class_picker(templates, fx):
    """v0.10.0 (ADDON_PLAN 5.10): browse any class in the library from the Macro Book,
    read-only for classes other than your own; counters/checks stay this character's."""
    WARRIOR_N = sum(1 for r in fx["warriorUniversal"]["records"] if r["id"].startswith("WARRIOR/"))
    PALADIN_N = sum(1 for r in fx["everything"]["records"] if r["id"].startswith("PALADIN/"))
    tag = "templates" if templates else "fallbacks"
    lua, T = login(templates, "PALADIN")
    L = lua.eval("R2F.L")
    MB = lua.eval("R2F.MacroBook")
    errors = lambda: lua_table_to_list(lua.eval("TEST.errors"))
    calls = lambda: lua_table_to_list(lua.eval("TEST.calls"))
    check(lua.eval("R2F.playerClass") == "PALADIN", "%s: logged in as a Paladin" % tag)

    # ---- Only your own class + Universal: no picker, the book looks as before ----
    apply_classes(lua, fx, {"ANY", "PALADIN"})
    lua.execute("R2F.MacroBook.Show()")
    tabs, picks, _ = book_state(lua)
    check(picks == [], "%s: no other class in the library -> no picker at all: %s" % (tag, picks))
    check(tabs == [("ANY", "Universal"), ("PALADIN", "General"), ("PALADIN", "Tank"), ("PALADIN", "DPS"),
                   ("PALADIN", "Healer")], "own view: Universal + Paladin tabs: %s" % tabs)
    check(font_text(lua, "^Paladin %(") is None, "no picker label without a picker")

    # ---- The real-game report: import Warrior macros while on a Paladin ---------
    lua.execute('SlashCmdList.R2F("import")')
    lua.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'EditBox' and f.__scripts.OnTextChanged and f.__parent and
           (f.__parent == R2FImportScroll or f.__parent == R2FImportScrollPlain) then EDIT = f end
        if f.__kind == 'Button' and f.__text == 'Import' and f.__parent == R2FImport then IMPORTBTN = f end
      end""")
    lua.eval("EDIT.SetText")(lua.eval("EDIT"), fx["warriorUniversal"]["string"])
    T.runTimers()
    lua.execute("IMPORTBTN:Click()")
    check(lua.eval("R2F.Library.ClassCounts().WARRIOR") == WARRIOR_N, "the Warrior import landed in the library (%d)" % WARRIOR_N)
    check(MB.BrowsedClass() == "WARRIOR" and MB.IsShown() is True,
          "%s: after importing only Warrior macros the book opens on the Warrior preview" % tag)
    tabs, picks, checked = book_state(lua)
    check(tabs == [("ANY", "Universal"), ("WARRIOR", "General"), ("WARRIOR", "Tank"), ("WARRIOR", "DPS")],
          "%s: Warrior preview = Universal + Warrior tabs: %s" % (tag, tabs))
    check(picks == ["PALADIN", "WARRIOR"] and checked == [False, True],
          "picker lists your class first, then Warrior; Warrior selected: %s %s" % (picks, checked))
    check(font_text(lua, "^Warrior %(preview%)$") == "Warrior (preview)", "picker label says preview")
    check(lua.eval("BTABS[2]:GetChecked()") is True, "the preview opens on the class's first new section (General)")

    # ---- Read-only: drag / click never makes a real macro -----------------------
    warrior_general = [r for r in fx["warriorUniversal"]["records"] if r["section"] == "General"]
    check(lua.eval("BSLOTS[1].entry.id") == warrior_general[0]["id"], "grid shows the Warrior's General macros")
    lua.execute("TEST.errors = {} TEST.calls = {} TEST.cursor = nil")
    lua.execute("BSLOTS[1]:Fire('OnDragStart')")
    msg = lua.eval("R2F.L.OTHER_CLASS_USE:format('Warrior')")
    check(T.cursor is None and calls() == [] and errors() == [msg],
          "%s: dragging a Warrior macro on a Paladin is refused, nothing created: %s %s" % (tag, calls(), errors()))
    lua.execute("TEST.errors = {} BSLOTS[2]:Click('LeftButton')")
    check(T.cursor is None and calls() == [] and errors() == [msg], "left-click refused the same way")
    # The book refuses before Macros is even asked (two independent layers).
    lua.execute("ENSURES = 0 local orig = R2F.Macros.Ensure R2F.Macros.Ensure = function(...) ENSURES = ENSURES + 1"
                " return orig(...) end TEST.errors = {} BSLOTS[1]:Fire('OnDragStart') BSLOTS[1]:Click('LeftButton')"
                " R2F.Macros.Ensure = orig")
    check(lua.eval("ENSURES") == 0 and errors() == [msg, msg], "the book's own guard: Macros.Ensure never called for a preview")
    for fn in ("Ensure", "Create", "Replace"):
        lua.execute("TEST.errors = {}")
        check(lua.eval("R2F.Macros.%s(%r)" % (fn, warrior_general[0]["id"])) is False and errors() == [msg] and calls() == [],
              "Macros.%s refuses another class's macro on its own (the real gate)" % fn)
    # A Paladin macro called like the Warrior's: still no Replace popup for it.
    lua.execute("TEST.addMacro(%r, '/say mine', true) CONFIRMSHOWN = R2FConfirm and R2FConfirm:IsShown()"
                % warrior_general[0]["short"])
    lua.execute("TEST.errors = {}")
    lua.eval("R2F.Macros.Ensure")(warrior_general[0]["id"])
    check(lua.eval("not (R2FConfirm and R2FConfirm:IsShown())") is True and T.bodyOf(warrior_general[0]["short"]) == "/say mine",
          "no Replace popup for another class's macro, the player's own macro untouched")
    lua.execute("BSLOTS[1]:Fire('OnEnter')")
    tip = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(tip[-2:] == [msg, L.TIP_SHARE] and L.TIP_DRAG not in tip,
          "read-only tooltip: why + Shift-click hint, no drag hint: %s" % tip[-2:])
    shown = [i for i in range(1, 13) if lua.eval("BSLOTS[%d].__shown" % i)]
    subs = [lua.eval("BSLOTS[%d].sub.__text" % i) for i in shown]
    check(all(lua.eval("BSLOTS[%d].icon.__desat" % i) is True for i in shown) and L.LEARN_LATER not in subs
          and len(shown) == 12, "read-only icons are grey, subtext is the group (never Learn later): %s" % subs)
    # Same macros on a Warrior: some are "Learn later" (spell unknown), proving the check above means something.
    lua.execute("R2F.playerClass = 'WARRIOR' R2F.MacroBook.Refresh()")
    check(L.LEARN_LATER in [lua.eval("BSLOTS[%d].sub.__text" % i) for i in shown],
          "(control: the same page on a Warrior does show Learn later)")
    lua.execute("R2F.playerClass = 'PALADIN' R2F.MacroBook.Browse('WARRIOR')")
    check(lua.eval("BSLOTS[1].readOnly") is True, "back on the Paladin, previewing Warrior again")
    T.shift = True
    lua.execute("TEST.chatInsert = nil BSLOTS[1]:Click('LeftButton')")
    T.shift = False
    check(lua.eval("TEST.chatInsert") is not None and calls() == [], "Shift-click still shares a previewed macro in chat")

    # ---- Universal stays usable while previewing --------------------------------
    lua.execute("BTABS[1]:Click()")
    check(lua.eval("BSLOTS[1].entry.class") == "ANY" and lua.eval("BSLOTS[1].readOnly") is False,
          "Universal entries are not read-only in the Warrior preview")
    lua.execute("TEST.cursor = nil TEST.errors = {} BSLOTS[1]:Fire('OnDragStart')")
    check(T.cursor == lua.eval("BSLOTS[1].entry.short") and errors() == [], "dragging a Universal macro works while previewing")
    note = font_text(lua, "^Previewing ")
    check(note is not None and note.startswith(lua.eval("R2F.L.BROWSE_NOTE:format('Warrior')")),
          "Universal tab in preview: the read-only / this-character note: %r" % note)
    check(font_text(lua, "You also have macros for") is None, "5.7's line is left out while previewing")

    # ---- Counters and gold checks = the character you're playing ----------------
    check(font_text(lua, "^Character %d+ /") == "Character 1 / 30" and font_text(lua, "^Account %d+ /") == "Account 0 / 120",
          "slot counters count this character's real macros while previewing: %s / %s"
          % (font_text(lua, "^Character %d+ /"), font_text(lua, "^Account %d+ /")))
    # An account-slot macro made from a Warrior entry on another character, and on
    # THIS character's bar: the check shows (real state), the others don't.
    hs = warrior_general[1]
    lua.eval("""function(id, short, body)
      TEST.addMacro(short, body, false)
      R2F.Library.SetCreated(id, { name = short, hash = R2F.Library.Hash(body), account = true })
      TEST.actions[7] = short end""")(hs["id"], hs["short"], hs["body"])
    lua.execute("BTABS[2]:Click()")
    find_frames(lua, "f.__kind == 'Button' and f.__scripts.OnDragStart and f ~= R2FMinimapButton", "BSLOTS")
    check(lua.eval("BSLOTS[2].entry.id") == hs["id"] and lua.eval("BSLOTS[2].check.__shown") is True
          and lua.eval("BSLOTS[3].check.__shown") is False,
          "gold check in preview = on THIS character's bars (account macro on slot 7)")
    check(font_text(lua, "^Account %d+ /") == "Account 1 / 120", "account counter follows the live macro list")
    check(note is not None and font_text(lua, "^Previewing ") is not None, "class tab in preview carries the note too")
    lua.execute("TEST.actions[7] = nil")
    T.fire("ACTIONBAR_SLOT_CHANGED")
    T.runTimers()
    check(lua.eval("BSLOTS[2].check.__shown") is False, "taking it off the bar clears the check (live, while previewing)")
    lua.execute("BSLOTS[2]:Fire('OnEnter')")
    check(L.TIP_ON_BARS not in lua_table_to_list(lua.eval("GameTooltip.lines")), "no on-bars tooltip line once it's off")

    # ---- Back to your own class: full interaction --------------------------------
    lua.execute("PICKS[1]:Click()")
    tabs, picks, checked = book_state(lua)
    check(MB.BrowsedClass() == "PALADIN" and checked == [True, False] and tabs[1][0] == "PALADIN",
          "%s: clicking your class returns to the Paladin view: %s" % (tag, tabs))
    check(lua.eval("BTABS[2]:GetChecked()") is True, "picking a class opens its first section")
    check(font_text(lua, "^Paladin %(your class%)$") == "Paladin (your class)", "picker label marks your own class")
    check(font_text(lua, "^Previewing ") is None, "no preview note in your own view")
    lua.execute("TEST.cursor = nil TEST.errors = {} TEST.calls = {}")
    find_frames(lua, "f.__kind == 'Button' and f.__scripts.OnDragStart and f ~= R2FMinimapButton", "BSLOTS")
    lua.execute("BSLOTS[1]:Fire('OnDragStart')")
    check(T.cursor == lua.eval("BSLOTS[1].entry.short") and calls() == ["create:" + T.cursor] and errors() == [],
          "%s: dragging your own class's macro creates + picks it up as before" % tag)
    lua.execute("BTABS[1]:Click()")
    other = font_text(lua, "^You also have macros for")
    check(other is not None and other.split("\n")[0] == lua.eval("R2F.L.OTHER_CLASSES:format('Warrior (%d)')" % WARRIOR_N),
          "5.7's line in your own view: %r" % other)

    # Picker tooltips.
    lua.execute("PICKS[1]:Fire('OnEnter')")
    check(lua_table_to_list(lua.eval("GameTooltip.lines")) == ["Paladin", "%d macros" % PALADIN_N, L.PICKER_TIP_YOURS],
          "own class button tooltip")
    lua.execute("PICKS[2]:Fire('OnEnter')")
    check(lua_table_to_list(lua.eval("GameTooltip.lines")) == ["Warrior", "%d macros" % WARRIOR_N,
                                                               lua.eval("R2F.L.PICKER_TIP_OTHER:format('Warrior')")],
          "other class button tooltip says preview only")
    check(lua.eval("PICKS[1].__normal.__tex") == "Interface\\TargetingFrame\\UI-Classes-Circles",
          "class button = the class circle texture")

    # ---- Remembered for the session: close / reopen / other tabs ----------------
    lua.execute("PICKS[2]:Click()")
    lua.execute("R2F.MainWindow.Hide() R2F.MacroBook.Show()")
    check(MB.BrowsedClass() == "WARRIOR" and book_state(lua)[1:] == (["PALADIN", "WARRIOR"], [False, True]),
          "%s: closing and reopening the window keeps the browsed class" % tag)
    lua.execute("R2F.MainWindow.SelectTab('home') R2F.MainWindow.SelectTab('macros')")
    check(MB.BrowsedClass() == "WARRIOR", "switching to Home and back keeps it too")
    check(lua.eval("R2FDB.settings.browse == nil and R2FCharDB.browse == nil"), "the browsed class is not saved")
    saved = (lua_literal(lua.eval("R2FDB")), lua_literal(lua.eval("R2FCharDB")))
    check("WARRIOR" not in saved[1] and "browse" not in saved[0] + saved[1],
          "nothing about browsing in SavedVariables")

    # ---- A fresh login (relog / reload) starts on your own class -----------------
    lua2, T2 = login(templates, "PALADIN", saved)
    check(lua2.eval("R2F.Library.ClassCounts().WARRIOR") == WARRIOR_N, "relog: the library came back from SavedVariables")
    lua2.execute("R2F.MacroBook.Show()")
    tabs2, picks2, checked2 = book_state(lua2)
    check(lua2.eval("R2F.MacroBook.BrowsedClass()") == "PALADIN" and checked2 == [True, False]
          and tabs2[1][0] == "PALADIN", "%s: after a relog the book opens on your own class: %s" % (tag, tabs2))

    # ---- The browsed class emptied -> back to your own ---------------------------
    lua.execute("PICKS[2]:Click()")
    lua.execute("for id, e in pairs(R2F.Library.db.library) do if e.class == 'WARRIOR' then R2F.Library.Remove(id) end end"
                " R2F.MacroBook.Refresh()")
    tabs, picks, _ = book_state(lua)
    check(MB.BrowsedClass() == "PALADIN" and picks == [] and tabs[0] == ("ANY", "Universal")
          and all(c in ("ANY", "PALADIN") for c, _ in tabs) and len(tabs) == 5,
          "%s: removing every Warrior macro falls back to your class, picker gone" % tag)

    # ---- Every class: only classes with macros, roster order, own first -----------
    apply_classes(lua, fx, {"ANY", "PRIEST", "WARLOCK", "MAGE", "ROGUE", "SHAMAN", "HUNTER", "PALADIN", "WARRIOR"}, 2)
    lua.execute("R2F.MacroBook.Refresh()")
    tabs, picks, _ = book_state(lua)
    check(picks == ["PALADIN", "PRIEST", "WARLOCK", "MAGE", "ROGUE", "SHAMAN", "HUNTER", "WARRIOR"],
          "picker: your class, then every class with macros in roster order, no Druid: %s" % picks)
    check(lua.eval("PICKS[2].__normal.__tex") == "Interface\\Icons\\INV_Misc_QuestionMark",
          "a class without CLASS_ICON_TCOORDS gets the question mark, not a wrong slice")
    lua.execute("PICKS[2]:Click()")
    tabs, _, _ = book_state(lua)
    check(tabs == [("ANY", "Universal"), ("PRIEST", "Shared"), ("PRIEST", "Shadow"), ("PRIEST", "Holy"),
                   ("PRIEST", "Discipline")], "browsing Priest shows Universal + Priest tabs: %s" % tabs)

    # ---- Import lands on your own class when it brought something new for it ----
    lua.execute("R2F.Library.db.library = {}")
    apply_classes(lua, fx, {"ANY"})
    d = lua.eval("function(s) local p = R2F.Import.Parse(s) return R2F.Import.Diff(p, R2F.Library.db.library, 'PALADIN') end")(
        fx["everything"]["string"])
    check(d.firstNew["class"] == "PRIEST" and d.firstNewOwn["class"] == "PALADIN",
          "mixed import: firstNew is the Priest's, firstNewOwn the Paladin's (%s / %s)"
          % (d.firstNew["class"], d.firstNewOwn["class"]))
    apply_classes(lua, fx, {"ANY", "PRIEST", "PALADIN"}, 3)
    lua.execute("R2F.MacroBook.ShowSection(%r, %r)" % ("PRIEST", "Shared"))
    check(MB.BrowsedClass() == "PRIEST", "ShowSection on another class opens its preview")
    lua.execute("R2F.MacroBook.ShowSection('ANY', 'Universal')")
    check(MB.BrowsedClass() == "PALADIN", "ShowSection on Universal returns to your own view")

    # ---- A caster browsing a melee class: the DPS tab icon is the TAB's class ----
    lua3, T3 = login(templates, "MAGE")
    # Mixed import through the Import window (Universal already in the library,
    # so the first NEW record is a Priest's): the book opens on your own class.
    apply_classes(lua3, fx, {"ANY"})
    lua3.execute('SlashCmdList.R2F("import")')
    lua3.execute("""
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'EditBox' and f.__scripts.OnTextChanged and f.__parent and
           (f.__parent == R2FImportScroll or f.__parent == R2FImportScrollPlain) then EDIT = f end
        if f.__kind == 'Button' and f.__text == 'Import' and f.__parent == R2FImport then IMPORTBTN = f end
      end""")
    lua3.eval("EDIT.SetText")(lua3.eval("EDIT"), fx["everything"]["string"])
    T3.runTimers()
    lua3.execute("IMPORTBTN:Click()")
    check(lua3.eval("R2F.MacroBook.BrowsedClass()") == "MAGE"
          and lua3.eval("R2F.MacroBook.IsShown()") is True,
          "%s: an import with new macros for your class opens your own view, not the first class in it" % tag)
    lua3.execute("R2F.MacroBook.Browse('PALADIN')")
    find_frames(lua3, "f.__kind == 'CheckButton' and f.sec and f.__shown and f.sec.section == 'DPS'", "DPST")
    check(lua3.eval("DPST[1].__normal.__tex") == "Interface\\Icons\\Ability_DualWield",
          "a Mage browsing Paladin sees the melee DPS icon (tab's class, not the player's)")

    # ---- No new globals -----------------------------------------------------------
    lua.execute("NEWG = {} for k in pairs(_G) do if not BEFORE[k] then NEWG[#NEWG + 1] = k end end")
    test_vars = {"EDIT", "IMPORTBTN", "BTABS", "PICKS", "BSLOTS", "FT", "NS", "NEWG", "CONFIRMSHOWN", "ENSURES"}
    bad = [g for g in lua_table_to_list(lua.eval("NEWG")) if g not in test_vars and not g.startswith("R2F")
           and g not in ("SLASH_R2F1", "SLASH_R2FT1") and g not in BINDING_GLOBALS]
    check(not bad, "%s: the class picker adds no globals: %s" % (tag, bad))


def test_remove_from_library(templates, fx):
    """v0.10.0: right-click > Remove from library asks first, removes the library entry
    only (never the real macro), and a later import counts it as new again.
    Plus the Tidy up tooltip."""
    tag = "templates" if templates else "fallbacks"
    lua, T = login(templates, "PALADIN")
    L = lua.eval("R2F.L")
    calls = lambda: lua_table_to_list(lua.eval("TEST.calls"))
    apply_classes(lua, fx, {"ANY", "PALADIN"})
    lua.execute("R2F.MacroBook.ShowSection('PALADIN', 'General')")
    find_frames(lua, "f.__kind == 'Button' and f.__scripts.OnDragStart and f ~= R2FMinimapButton", "BSLOTS")
    rec = lua.eval("BSLOTS[1].entry")
    mid, short, name, body = rec.id, rec.short, rec.name, rec.body
    # A real macro made from it, on a bar.
    lua.execute("BSLOTS[1]:Fire('OnDragStart')")
    lua.execute("TEST.actions[3] = %r" % short)
    check(lua.eval("GetMacroIndexByName(%r)" % short) > 0, "real macro made from %s" % mid)
    lua.execute("TEST.calls = {}")

    def open_remove(slot=1):
        lua.execute("BSLOTS[%d]:Click('RightButton')" % slot)
        find_frames(lua, "f.__kind == 'Button' and f.__text == R2F.L.MENU_REMOVE", "RMB")
        lua.execute("RMB[1]:Click()")

    open_remove()
    check(lua.eval("R2FConfirm:IsShown()") is True and lua.eval("R2F.Library.Get(%r) ~= nil" % mid),
          "%s: Remove from library opens the confirm popup and removes nothing yet" % tag)
    text = lua.eval("R2FConfirm.text.__text")
    check(text == lua.eval("R2F.L.REMOVE_CONFIRM:format(%s, %s)" % (json.dumps(name), json.dumps(short))),
          "confirm names the macro and says the real macro stays: %r" % text)
    check(lua.eval("R2FConfirm.yes.__text") == L.BTN_REMOVE and lua.eval("R2FConfirm.no.__text") == L.BTN_CANCEL,
          "confirm buttons: Remove / Cancel")
    lua.execute("R2FConfirm.no:Click()")
    check(lua.eval("R2F.Library.Get(%r) ~= nil" % mid) and lua.eval("BSLOTS[1].entry.id") == mid,
          "Cancel keeps it in the library and the grid")
    open_remove()
    T.chat = lua.table()
    lua.execute("R2FConfirm.yes:Click()")
    check(lua.eval("R2F.Library.Get(%r) == nil" % mid), "%s: Remove confirmed: gone from the library" % tag)
    find_frames(lua, "f.__kind == 'Button' and f.__scripts.OnDragStart and f ~= R2FMinimapButton and f.__shown", "VIS")
    shown_ids = [lua.eval("VIS[%d].entry.id" % i) for i in range(1, lua.eval("#VIS") + 1)]
    check(mid not in shown_ids, "and gone from the grid")
    check(calls() == [] and T.bodyOf(short) == body and lua.eval("TEST.actions[3]") == short,
          "the real macro is untouched: no delete/edit, same body, still on the bar")
    check(lua.eval("R2F.Library.Created(%r) ~= nil" % mid), "its created record stays (Tidy up / Remove all still know it)")
    check(any(("removed %s from the library." % short) in c for c in chat_lines(lua)),
          "chat confirms the removal")
    lua.execute("TEST.actions[3] = nil")
    cands = [c.id for c in lua_table_to_list(lua.eval("R2F.Macros.TidyCandidates()"))]
    check(mid in cands, "Tidy up can still delete the real macro once it's off the bar")
    lua.execute("TEST.actions[3] = %r" % short)

    # Re-import: counted as new (not updated), and back in the book.
    d = lua.eval("function(s) local p = R2F.Import.Parse(s) return R2F.Import.Diff(p, R2F.Library.db.library, 'PALADIN') end")(
        fx["everything"]["string"])
    check(d.status[mid] == "new", "%s: re-importing a removed macro counts it as new (%s)" % (tag, d.status[mid]))
    other_status = d.status[lua.eval("BSLOTS[2].entry.id")]
    check(other_status == "unchanged", "the macros that stayed are unchanged (%s)" % other_status)
    lua.eval("function(s) R2F.Import.Commit(R2F.Import.Parse(s), 'PALADIN', 9) end")(fx["everything"]["string"])
    lua.execute("R2F.MacroBook.ShowSection('PALADIN', 'General')")
    check(lua.eval("BSLOTS[1].entry.id") == mid and lua.eval("BSLOTS[1].check.__shown") is True,
          "re-imported: back in the grid, and its real macro on the bar is recognised again")

    # Popup accepted after the entry already went away: nothing happens, no error.
    open_remove()
    lua.execute("R2F.Library.Remove(%r)" % mid)
    T.chat = lua.table()
    lua.execute("R2FConfirm.yes:Click()")
    check(chat_lines(lua) == [], "accepting after the entry is already gone does nothing")

    # Another class's macro while previewing: allowed (library only, no game macro).
    lua.execute("R2F.MacroBook.Browse('WARRIOR')")
    find_frames(lua, "f.__kind == 'Button' and f.__scripts.OnDragStart and f ~= R2FMinimapButton", "BSLOTS")
    wid = lua.eval("BSLOTS[1].entry.id")
    check(wid.startswith("WARRIOR/") and lua.eval("BSLOTS[1].readOnly") is True, "previewing Warrior")
    lua.execute("TEST.calls = {}")
    open_remove()
    check(lua.eval("R2FConfirm:IsShown()") is True, "%s: Remove from library is offered for a previewed class too" % tag)
    lua.execute("R2FConfirm.yes:Click()")
    check(lua.eval("R2F.Library.Get(%r) == nil" % wid) and calls() == [],
          "removing a previewed class's macro only touches the library")
    # Copy text works read-only too.
    lua.execute("BSLOTS[1]:Click('RightButton')")
    find_frames(lua, "f.__kind == 'Button' and f.__text == R2F.L.MENU_COPY", "CPB")
    lua.execute("CPB[1]:Click()")
    check(lua.eval("R2FCopy:IsShown()") is True and lua.eval("R2FCopy.text") == lua.eval("BSLOTS[1].entry.body"),
          "Copy text works on a previewed macro")

    # ---- Tidy up tooltip -----------------------------------------------------------
    find_frames(lua, "f.__kind == 'Button' and f.__text == R2F.L.BTN_TIDY", "TIDYB")
    lua.execute("TIDYB[1]:Fire('OnEnter')")
    tip = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(tip == [L.BTN_TIDY, L.TIDY_TIP, L.TIDY_TIP_LIBRARY], "%s: Tidy up tooltip: %s" % (tag, tip))
    check("aren't on any action bar" in L.TIDY_TIP and "haven't edited" in L.TIDY_TIP
          and "Remove from library" in L.TIDY_TIP_LIBRARY, "Tidy up tooltip explains it and contrasts Remove from library")
    T.fire("PLAYER_REGEN_DISABLED")
    lua.execute("TIDYB[1]:Fire('OnEnter')")
    tip = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(lua.eval("TIDYB[1].__enabled") is False and tip[-1] == L.TIDY_TIP_COMBAT,
          "in combat Tidy up is greyed out and its tooltip says why")
    T.fire("PLAYER_REGEN_ENABLED")


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
    test_stance()
    test_import_replaces(fx)
    test_settings_tab(True, fx)
    test_settings_tab(False, fx)
    test_tree_names()
    test_bags()
    test_reminders()
    test_ui_smoke(True, fx)
    test_ui_smoke(False, fx)
    test_step5_logic(new_runtime(), fx)
    test_step5_ui(True, fx)
    test_step5_ui(False, fx)
    test_bindings_xml(new_runtime())
    test_step6_ui(True, fx)
    test_step6_ui(False, fx)
    test_minimap_libdbicon(fx)
    test_media()
    test_talents(True)
    test_talents(False)
    test_talent_preview(True)
    test_talent_preview(False)
    test_talent_learning(True)
    test_talent_learning(False)
    test_talent_traits(True)
    test_talent_traits(False)
    test_talent_grid_jitter(True)
    test_talent_grid_jitter(False)
    test_talent_source_writes()
    test_talent_traits_learning(True)
    test_talent_traits_learning(False)
    test_free_points(True)
    test_free_points(False)
    test_talent_source_traits()
    test_quick_settings(True, fx)
    test_quick_settings(False, fx)
    test_class_picker(True, fx)
    test_class_picker(False, fx)
    test_remove_from_library(True, fx)
    test_remove_from_library(False, fx)
    print("%d checks passed, %d failed" % (PASSES, len(FAILS)))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
