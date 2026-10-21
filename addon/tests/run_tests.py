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
    # The bundled macro set would fill the library at login in every test; it is parked here and
    # restored by test_bundle (NS = the addon's namespace table).
    lua.execute("NS.MacroDataReal = NS.MacroData NS.MacroData = nil")
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
    check(lua.eval(st + ".shown") is True and lua.eval(st + ".scale") == 1.25 and lua.eval(st + ".lock") is True, "stance: defaults (owner's setup, locked)")
    lua.execute("TEST.stanceIndex = 3 R2F.Stance.Update()")
    check(lua.eval("R2FStanceFrame.border ~= nil"), "stance: border texture exists")
    lua.execute(st + ".lock = false")
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

    # --- /r2f settings opens Home (the Settings tab was folded into it) -------------
    lua.execute('SlashCmdList.R2F("settings")')
    check(MW.IsShown() is True and MW.CurrentTab() == "home", "%s: /r2f settings opens Home" % tag)
    title = lua.eval("R2F.MainWindow.Title()")
    check(title == "Road to Forever", "%s: Home title: %r" % (tag, title))
    check(lua.eval("R2FDB.settings.lastTab") == "home", "the retired settings tab is remembered as home")
    lua.execute("R2FDB.settings.lastTab = 'settings' R2F.Library.Init()")
    check(lua.eval("R2FDB.settings.lastTab") == "home", "a saved lastTab of 'settings' becomes home")
    lua.execute("R2F.MainWindow.SelectTab('macros')")
    check(lua.eval("R2F.Settings.IsShown()") is False, "Settings.IsShown() false on another tab")

    # --- Home: headline, the plan entry, the options, share card ---------------------
    lua.execute("R2F.MainWindow.SelectTab('home')")
    find_frames(lua, "f.__kind == 'Button' and f.tab ~= nil and f.sub ~= nil", "HOME")
    check(lua.eval("#HOME") == 1 and lua.eval("HOME[1].tab") == "plan", "%s: Home has the one plan entry" % tag)
    check(font_text(lua, "^Road to Forever$") == "Road to Forever" and font_text(lua, "^" + lua.eval("R2F.L.HOME_TAGLINE") + "$") is not None,
          "Home headline and tagline")
    acc_n, acc_max, char_n, char_max = lua.eval("R2F.Macros.Counts()")
    check(lua.eval("R2F.Home.SlotLine()") == "%d of %d character slots, %d of %d account slots used" % (char_n, char_max, acc_n, acc_max),
          "slot line helper: %r" % lua.eval("R2F.Home.SlotLine()"))
    find_frames(lua, "f.qsItem ~= nil", "QSB")
    check(lua.eval("#QSB") == 5 and lua.eval("QSB[1]:IsVisible()") is True,
          "%s: Quick settings switches are on the Home page" % tag)
    for key in ("QS_TITLE", "SETTINGS_MINIMAP", "HOME_SHARE"):
        check(font_text(lua, "^" + lua.eval("R2F.L.%s" % key) + "$") is not None, "Home has the %s heading" % key)
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel", "CBS")
    labels = {lua.eval("CBS[%d].r2fLabel.__text" % i) for i in range(1, lua.eval("#CBS") + 1)}
    for key in ("SETTINGS_MINIMAP_SHOW", "SETTINGS_MINIMAP_LOCK", "QS_ZOOM", "QS_GUILD", "QS_PVP"):
        check(lua.eval("R2F.L.%s" % key) in labels, "Home has the %s control" % key)
    find_frames(lua, "f.__kind == 'Button' and f.__text == R2F.L.HOME_PROFS and f.__shown", "PROFS")
    check(lua.eval("#PROFS") == 1, "Export professions is on Home")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.SETTINGS_STANCE_SHOW", "SSB")
    check(lua.eval("R2FStanceScale ~= nil and R2FStanceScale:IsVisible()") is False
          and lua.eval("#SSB == 0 or not SSB[1]:IsVisible()") is True, "stance options are not on Home (15.4)")
    # Combat greys the Quick settings switches.
    T.combat = True
    T.fire("PLAYER_REGEN_DISABLED")
    check(lua.eval("QSB[1]:IsEnabled()") is False, "combat greys the Quick settings switches")
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")
    check(lua.eval("QSB[1]:IsEnabled()") is True, "after combat they are enabled again")
    # The old floating panel and its button are gone.
    check(lua.eval("R2FSettings == nil"), "no floating Settings panel")
    check("R2FSettings" not in lua_table_to_list(lua.eval("UISpecialFrames")), "R2FSettings not in UISpecialFrames")

    # --- Macros page Options menu: where new macros go, Remove all ----------------------
    lua.execute("R2F.MainWindow.SelectTab('macros') R2F.MacroBook.OptionsMenu()")
    check(lua.eval("R2FMenu:IsShown()") is True and lua.eval("R2FMenu.rows[6].text.__text") == lua.eval("R2F.L.BTN_REMOVE_ALL"),
          "%s: Remove all is in the Macros Options menu" % tag)
    check(lua.eval("R2FMenu.rows[2].check.__tex") == "Interface\\Buttons\\UI-CheckBox-Check",
          "%s: Options menu: character slots first by default" % tag)
    lua.execute("R2FMenu.rows[3]:Click()")
    check(lua.eval("R2FDB.settings.slotsFirst") == "account", "%s: Options menu: account slots first" % tag)
    lua.execute("R2F.MacroBook.OptionsMenu() R2FMenu.rows[2]:Click()")
    check(lua.eval("R2FDB.settings.slotsFirst") == "character", "%s: Options menu: back to character slots" % tag)
    find_frames(lua, "f.__kind == 'Button' and f.__text == R2F.L.BTN_MACRO_OPTIONS and f.__shown", "OPTBTN")
    check(lua.eval("#OPTBTN") == 1, "%s: the Macros page has an Options button" % tag)

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


def test_talented_perk():
    """The Talented legacy perk: build level = points + 9 - 5 with it on; setting defaults off;
    talentcalc.js uses the same arithmetic."""
    lua = new_runtime()
    lua.execute("R2FDB = nil R2FCharDB = nil R2F.Library.Init()")
    check(lua.eval("R2F.Talents.LevelFor(21, false)") == 30, "perk: 21 points = level 30 without the perk")
    check(lua.eval("R2F.Talents.LevelFor(26, true)") == 30, "perk: 26 points = level 30 with the perk")
    check(lua.eval("R2F.Talents.LevelFor(26, false)") == 35, "perk: 26 points = level 35 without the perk")
    check(lua.eval("R2F.Talents.LevelFor(0, true)") == 0, "perk: no points = no level")
    check(lua.eval("R2F.Library.db.settings.talented") is True, "perk: setting defaults to on (owner's setup)")
    js = open(os.path.join(ROOT, "talentcalc.js"), encoding="utf-8").read()
    check("points + 9 - perkRank()" in js and "TALENTED_RANK = 5" in js,
          "perk: talentcalc.js uses points + 9 - 5, the same as Talents.LevelFor")


def test_bundle(fx):
    """The macros inside the addon (MacroData.lua): current with data.py, same as the site's export of
    everything, installed once per version at login."""
    r = subprocess.run([sys.executable, "build.py", "--check-macro-data"], cwd=ROOT, capture_output=True, text=True)
    check(r.returncode == 0, "MacroData.lua matches data.py (run python build.py)")
    lua = new_runtime()
    check(lua.eval("NS.MacroDataReal ~= nil and NS.MacroDataReal.string == nil") is False, "MacroData.lua defines the bundle")
    check(lua.eval("NS.MacroDataReal.string") == fx["everything"]["string"],
          "the bundled string is byte-identical to what the site's export tray writes for every macro")
    lua.execute("R2FDB = nil R2FCharDB = nil R2F.Library.Init() R2F.playerClass = 'WARRIOR'")
    check(lua.eval("R2F.Bundle.Pending()") is False, "no bundle in the runtime: nothing pending")
    lua.execute("R2F.MacroData = NS.MacroDataReal")
    check(lua.eval("R2F.Bundle.Pending()") is True, "fresh install: the bundle is pending")
    lua.execute("R2F.Bundle.Run()")
    total = len(fx["everything"]["records"])
    check(lua.eval("R2F.Library.Count()") == total, "bundle installs all %d macros" % total)
    check(lua.eval("R2FDB.bundleVersion") == lua.eval("R2F.MacroData.version") and lua.eval("R2F.Bundle.Pending()") is False,
          "the installed version is remembered")
    lua.execute("R2F.Library.Remove('ANY/Zoom')")
    lua.execute("R2F.Bundle.Run()")
    check(lua.eval("R2F.Library.Get('ANY/Zoom')") is None, "same version: login does not reinstall")
    lua.execute("R2FDB.bundleVersion = 'old' R2F.Bundle.Run()")
    check(lua.eval("R2F.Library.Get('ANY/Zoom') ~= nil"), "a new bundled version restores / updates the macros")


def test_planner():
    """0.37.0: loadouts and sharing over the addon channel (the build comes from the sandbox calculator)."""
    fxt = json.load(open(TALENT_FIXTURE, encoding="utf-8"))
    js = talent_js()
    lua = new_runtime()
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    use_fixture_data(lua, fxt["talents"], "warrior")
    set_game_talents(lua, fxt["talents"], js["classes"]["warrior"], {})
    lua.execute("TL = R2F.Talents")
    lua.execute("CX = R2F.TalentCalc.FromCode('warrior', '1') LINK = TL.SITE_URL .. R2F.TalentCalc.Body(CX)")
    lua.execute("P2 = TL.Preview(LINK).plan")
    check(lua.eval("P2 ~= nil and P2.total") == 1, "planner: a link built from the calculator previews with 1 point")
    # Loadouts
    lua.execute("R2FDB.loadouts = R2FDB.loadouts or {} ")
    lua.execute("LO = TL.SaveLoadout('Leveling', LINK)")
    check(lua.eval("LO ~= nil and LO.by == nil and #TL.Loadouts('warrior')") == 1, "planner: a loadout is saved")
    lua.execute("TL.SaveLoadout('Leveling', LINK)")
    check(lua.eval("#TL.Loadouts('warrior')") == 1, "planner: same name updates instead of duplicating")
    check(lua.eval("TL.SaveLoadout('', LINK)") is None and lua.eval("TL.SaveLoadout('x', 'junk')") is None,
          "planner: empty name / bad link are refused")
    # Sharing
    T.addonSent = lua.table()
    lua.execute("TEST.addonSent = {}")
    check(lua.eval("TL.ShareLoadout(LO, 'PARTY')") is True and lua.eval("#TEST.addonSent") == 1
          and lua.eval("TEST.addonSent[1][1]") == "R2FT" and lua.eval("TEST.addonSent[1][3]") == "PARTY",
          "planner: share sends one R2FT message to the channel")
    lua.execute("MSG = TEST.addonSent[1][2]")
    lua.execute("TL.DeleteLoadout(LO.id)")
    check(lua.eval("#TL.Loadouts('warrior')") == 0, "planner: delete removes it")
    lua.execute("TL.OnAddonMessage('R2FT', MSG, 'PARTY', 'Bob-Realm')")
    check(lua.eval("#TL.Loadouts('warrior')") == 1 and lua.eval("TL.Loadouts('warrior')[1].by") == "Bob",
          "planner: a received loadout is saved, marked with the sender")
    lua.execute("TL.OnAddonMessage('R2FT', 'L\\tBad\\tnonsense', 'PARTY', 'Eve-Realm')")
    lua.execute("TL.OnAddonMessage('R2FT', MSG, 'PARTY', UnitName('player') .. '-Realm')")
    lua.execute("TL.OnAddonMessage('XXXX', MSG, 'PARTY', 'Zed-Realm')")
    check(lua.eval("#TL.Loadouts('warrior')") == 1, "planner: bad body, own name and wrong prefix are ignored")


def test_talent_cache_and_clear():
    """The Talents tab's "couldn't read your talents": names not loaded yet must not fail the read once a good read
    exists, and the Clear button gives an empty board to build from."""
    fxt = json.load(open(TALENT_FIXTURE, encoding="utf-8"))
    js = talent_js()
    lua = new_runtime()
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    set_game_talents(lua, fxt["talents"], js["classes"]["warrior"], {})
    lua.execute("TL = R2F.Talents")
    lua.execute("GOOD = TL.ReadTrees() GOODHASH = TL.Hash(GOOD)")
    check(lua.eval("GOOD ~= nil and #GOOD") == 3, "talent cache: a normal read gives 3 panes")
    check(lua.eval("R2FCharDB.talentCache ~= nil and #R2FCharDB.talentCache.trees") == 3, "talent cache: the structure is saved per character")
    # Names not loaded yet (the spell data is missing): the live read cannot finish...
    lua.execute("""
      REAL_NAME, REAL_INFO = C_Spell.GetSpellName, GetSpellInfo
      C_Spell.GetSpellName = function() return nil end
      GetSpellInfo = nil
      C_Traits.GetNodeInfo_real = C_Traits.GetNodeInfo
    """)
    check(lua.eval("TL.ReadTrees() ~= nil and #TL.ReadTrees()") == 3, "talent cache: with names not loaded, the last good structure is used")
    check(lua.eval("TL.Hash(TL.ReadTrees())") == lua.eval("GOODHASH"), "talent cache: same names in the same order (same ~hash)")
    # ... but a config that is really unreadable is still nil, not a stale guess
    lua.execute("TEST.traitsReady = false")
    check(lua.eval("TL.ReadTrees()") is None, "talent cache: no config -> nil even with a cache")
    lua.execute("TEST.traitsReady = true C_Spell.GetSpellName = REAL_NAME GetSpellInfo = REAL_INFO")
    # Reset
    lua.execute("R2F.MainWindow.Show('talents')")
    lua.execute("R2F.TalentPanel.Clear()")
    check(lua.eval("R2F.TalentPanel.CurrentBody() ~= nil"), "talent clear: Reset leaves an empty board with a link")
    check(lua.eval("R2F.TalentCalc.Total(R2F.TalentPanel.Calc())") == 0, "talent clear: the reset board has no points")
    check(lua.eval("R2FCharDB.lastTalentLink ~= nil"), "talent clear: the board is remembered")


def test_dungeon_entrances():
    """A plan point with `dungeon` takes its position from the game's own map (the entrances Leatrix Maps draws)."""
    lua, T = plan_runtime(True, True, True)
    # Dun Morogh (1426) gets an entrance called "City of Dalaran", position as the game gives it (0..1 vector).
    lua.execute("""
      C_EncounterJournal = { GetDungeonEntrancesForMap = function(id)
        if id == 1426 then
          return { { areaPoiID = 1, name = 'City of Dalaran', position = { GetXY = function() return 0.25, 0.5 end } } }
        end
        return {}
      end }
      PT = { zone = 'Alterac Mountains', label = 'City of Dalaran (sewers)', dungeon = 'City of Dalaran', conf = 'check' }
    """)
    check(lua.eval("R2F.Plan.HasPosition(PT)") is True, "entrance: a dungeon point has a position once the game's map knows the entrance")
    check(lua.eval("R2F.Plan.EntranceFor('city of dalaran').mapID") == 1426 and lua.eval("R2F.Plan.EntranceFor('City of Dalaran').x") == 25,
          "entrance: the game's 0..1 position becomes map percent (25, 50)")
    check(lua.eval("R2F.Plan.EntranceFor('Dalaran').y") == 50, "entrance: a name that is part of the entrance's name still finds it")
    check(lua.eval("R2F.Plan.EntranceFor('Gnomeregan')") is None, "entrance: an unknown dungeon has none")
    lua.execute("R = R2F.Plan.Waypoint(PT, 'x')")
    check(lua.eval("R") == "arrow" and lua.eval("R2F.Nav.Target().x") == 25 and lua.eval("R2F.Nav.Target().label") == "City of Dalaran (sewers)",
          "entrance: the Waypoint button points the arrow at the entrance")
    # The generated plan data carries `dungeon` for the five unknown dungeons.
    n = lua.eval("(function() local c = 0 for _, st in pairs(R2F.PlanData.waypoints) do for _, pts in pairs(st) do for _, p in ipairs(pts) do if p.dungeon then c = c + 1 end end end end return c end)()")
    check(n == 5, "entrance: five plan dungeon points ask the game for their entrance: %s" % n)
    # No such API (a client without it): no position, no error.
    lua2, _ = plan_runtime(True, True, True)
    lua2.execute("C_EncounterJournal = nil PT = { zone = 'Alterac Mountains', label = 'x', dungeon = 'City of Dalaran', conf = 'check' }")
    check(lua2.eval("R2F.Plan.HasPosition(PT)") is False and lua2.eval("R2F.Plan.Waypoint(PT)") is None,
          "entrance: without the API the point stays 'position not known yet'")


def test_worn_enchant():
    """Mr.BiZ says which enchant you wear in a slot (from the item link) against the slot's list, and lists the 2nd / 3rd best."""
    lua = new_runtime()
    lua.execute("R2FDB = nil R2FCharDB = nil R2F.Library.Init()")
    lua.execute("BZ = R2F.BiZ ROWS = BZ.Enchants('hunter/beast-mastery', 'chest')")
    check(lua.eval("#ROWS") >= 1 and lua.eval("ROWS[1].ids ~= nil and #ROWS[1].ids") >= 1, "worn enchant: the best chest enchant carries its enchantment id")
    check(lua.eval("ROWS[1].alts ~= nil and #ROWS[1].alts") >= 1 and lua.eval("ROWS[1].alts[1].ids ~= nil"), "worn enchant: the 2nd best is listed with its id")
    lua.execute("BEST, ALT = ROWS[1].ids[1], ROWS[1].alts[1].ids[1]")
    check(lua.eval("(BZ.EnchantState(ROWS, BEST))") == "best", "worn enchant: the id of the best enchant = best")
    check(lua.eval("(select(3, BZ.EnchantState(ROWS, ALT)))") == 2 and lua.eval("(BZ.EnchantState(ROWS, ALT))") == "alt", "worn enchant: the 2nd best's id = #2")
    check(lua.eval("(BZ.EnchantState(ROWS, 99999))") == "other" and lua.eval("(BZ.EnchantState(ROWS, 0))") == "none" and lua.eval("(BZ.EnchantState(ROWS, nil))") is None,
          "worn enchant: another id = other, 0 = none, nothing worn = nil")
    lua.execute("""
      TEST.worn = {}
      GetInventoryItemLink = function(unit, slot) return TEST.worn[slot] end
    """)
    check(lua.eval("BZ.WornEnchant('chest')") is None, "worn enchant: an empty slot gives nil")
    lua.execute("TEST.worn[5] = '|cff1eff00|Hitem:1488:' .. BEST .. ':0:0:0:0:0:0:0:0|h[Avenger]|h|r'")
    check(lua.eval("BZ.WornEnchant('chest')") == lua.eval("BEST"), "worn enchant: the enchant id is read from the item link")
    lua.execute("TEST.worn[5] = '|Hitem:1488::0:0|h[Avenger]|h'")
    check(lua.eval("BZ.WornEnchant('chest')") == 0, "worn enchant: a link with no enchant = 0")
    check(lua.eval("BZ.WornEnchant('nonsense')") is None, "worn enchant: an unknown slot gives nil")
    # In the panel: the lines show up for the selected slot.
    lua.execute("BZ.SetSpec('hunter/beast-mastery') R2F.MainWindow.Show('bis') R2F.BiZTab.Refresh()")
    lua.execute("TEST.worn[5] = '|Hitem:1488:' .. ALT .. ':0:0|h[Avenger]|h'")
    lua.execute("for _, b in ipairs(DOLL or {}) do end")
    find_frames(lua, "f.__kind == 'Button' and f.slotKey == 'chest'", "CHESTBTN")
    lua.execute("CHESTBTN[1]:Click()")
    check(font_text(lua, "^Enchant: ") is not None, "worn enchant: the panel lists the best enchant")
    check(font_text(lua, "^#2: ") is not None, "worn enchant: and the 2nd best under it")
    check(font_text(lua, "^Your chest has the #2 enchant") is not None, "worn enchant: and says you wear the #2 enchant")
    lua.execute("TEST.worn[5] = '|Hitem:1488:' .. BEST .. ':0:0|h[Avenger]|h' R2F.BiZTab.Refresh()")
    check(font_text(lua, "^Your chest has the best enchant") is not None, "worn enchant: the best one is recognised")


def test_corpse_arrow():
    """On death the arrow points at the corpse; alive again, the arrow from before comes back."""
    lua, T = plan_runtime(True, True, True)
    lua.execute("""
      TEST.hereMap = 1426
      TEST.ghost = false
      UnitIsGhost = function() return TEST.ghost end
      TEST.corpse = { 0.3, 0.6 }
      C_DeathInfo = { GetCorpseMapPosition = function(id)
        if id == 1426 and TEST.corpse then return { GetXY = function() return TEST.corpse[1], TEST.corpse[2] end } end
      end }
      R2F.Library.db.gameplay.corpsearrow = true
      R2F.Nav.Clear()
      R2F.Nav.SetTarget(1426, 40, 50, 'Anvilmar', 'Dun Morogh')
    """)
    check(lua.eval("R2F.Gameplay.IsOn('corpsearrow')") is True, "corpse arrow: on by default for a new character")
    T.fire("PLAYER_DEAD")
    check(lua.eval("R2F.Nav.Target().label") == "Your corpse" and lua.eval("R2F.Nav.Target().x") == 30 and lua.eval("R2F.Nav.Target().y") == 60,
          "corpse arrow: dying points the arrow at the corpse (map percent 30, 60)")
    lua.execute("TEST.ghost = true")
    T.fire("PLAYER_ALIVE")
    check(lua.eval("R2F.Nav.Target().label") == "Your corpse", "corpse arrow: releasing (a ghost) keeps it on the corpse")
    lua.execute("TEST.ghost = false")
    T.fire("PLAYER_UNGHOST")
    check(lua.eval("R2F.Nav.Target().label") == "Anvilmar" and lua.eval("R2F.Nav.Target().x") == 40,
          "corpse arrow: alive again, the arrow from before is back")
    # Nothing was set before: alive again clears the arrow.
    lua.execute("R2F.Nav.Clear()")
    T.fire("PLAYER_DEAD")
    check(lua.eval("R2F.Nav.Target().label") == "Your corpse", "corpse arrow: works with no arrow set before")
    T.fire("PLAYER_ALIVE")
    check(lua.eval("R2F.Nav.Target()") is None, "corpse arrow: alive again with nothing before leaves no arrow")
    # A target you set while dead is left alone.
    lua.execute("R2F.Nav.Clear() R2F.Nav.SetTarget(1426, 40, 50, 'Anvilmar', 'Dun Morogh')")
    T.fire("PLAYER_DEAD")
    lua.execute("R2F.Nav.SetTarget(1426, 10, 10, 'Mine', 'Dun Morogh')")
    T.fire("PLAYER_UNGHOST")
    check(lua.eval("R2F.Nav.Target().label") == "Mine", "corpse arrow: an arrow you set yourself while dead stays")
    # No corpse position (not released yet / another map): no arrow, no error.
    lua.execute("R2F.Nav.Clear() TEST.corpse = nil")
    T.fire("PLAYER_DEAD")
    check(lua.eval("R2F.Nav.Target()") is None, "corpse arrow: no corpse position known -> no arrow")
    lua.execute("TEST.corpse = { 0.3, 0.6 } TEST.ghost = true")
    T.fire("PLAYER_ALIVE")
    check(lua.eval("R2F.Nav.Target().label") == "Your corpse", "corpse arrow: released later, the corpse position is found then")
    # A ghost wakes at a graveyard in another zone: only a map above the one it is on knows the corpse.
    lua.execute("""R2F.Nav.RestoreAfterCorpse() R2F.Nav.Clear() TEST.ghost = true
      OLD_INFO = C_Map.GetMapInfo
      C_Map.GetMapInfo = function(id) if id == 1426 then return { name = 'Dun Morogh', parentMapID = 1455 } end return OLD_INFO and OLD_INFO(id) end
      C_DeathInfo.GetCorpseMapPosition = function(id) if id == 1455 then return { x = 0.41, y = 0.52 } end end""")
    T.fire("PLAYER_ALIVE")
    check(lua.eval("R2F.Nav.Target().label") == "Your corpse" and lua.eval("R2F.Nav.Target().mapID") == 1455,
          "corpse arrow: the corpse is found on the parent map when the zone's own map does not have it")
    T.chat = lua.table()
    lua.execute("R2F.DEBUG.corpse()")
    check("map 1455" in chat_all(lua) and "Your corpse" in chat_all(lua), "corpse arrow: /r2f debug corpse lists the maps asked and the arrow")
    lua.execute("""C_Map.GetMapInfo = OLD_INFO
      C_DeathInfo.GetCorpseMapPosition = function(id)
        if id == 1426 and TEST.corpse then return { GetXY = function() return TEST.corpse[1], TEST.corpse[2] end } end
      end""")
    # Reload as a ghost.
    lua.execute("TEST.ghost = false R2F.Nav.RestoreAfterCorpse() R2F.Nav.Clear() TEST.ghost = true")
    T.fire("PLAYER_ENTERING_WORLD")
    check(lua.eval("R2F.Nav.Target().label") == "Your corpse", "corpse arrow: logging in as a ghost points at the corpse")
    # Switched off.
    lua.execute("TEST.ghost = false R2F.Nav.RestoreAfterCorpse() R2F.Nav.Clear() R2F.Library.db.gameplay.corpsearrow = false")
    T.fire("PLAYER_DEAD")
    check(lua.eval("R2F.Nav.Target()") is None, "corpse arrow: switched off, dying does nothing")


def test_arrow_3d():
    """The 3D arrow: a sprite sheet of 100 turn angles; the frame follows the turn angle, the flat dart is the switch-off."""
    import math
    lua, T = plan_runtime(True, True, True)
    check(lua.eval("R2F.Nav.FRAMES") == 100 and lua.eval("R2F.Nav.COLS") == 10, "3D arrow: 100 frames, 10 per row")
    check(lua.eval("R2F.Gameplay.IsOn('arrow3d')") is True, "3D arrow: on by default for a new character")
    for angle, frame in ((0, 0), (math.pi / 2, 25), (math.pi, 50), (-math.pi / 2, 75), (-0.01, 0), (0.0377, 1), (2 * math.pi + 0.0377, 1), (-math.pi, 50)):
        got = lua.eval("R2F.Nav.FrameFor(%r)" % angle)
        check(got == frame, "3D arrow: angle %.4f -> frame %d (got %s)" % (angle, frame, got))
    l, r, t, b = lua.eval("R2F.Nav.FrameCoords(0)")
    check(abs(l) < 1e-9 and abs(r - 102 / 1024) < 1e-9 and abs(t) < 1e-9 and abs(b - 102 / 1024) < 1e-9, "3D arrow: frame 0 is the top-left cell")
    l, r, t, b = lua.eval("R2F.Nav.FrameCoords(37)")
    check(abs(l - 7 * 102 / 1024) < 1e-9 and abs(t - 3 * 102 / 1024) < 1e-9 and abs(r - 8 * 102 / 1024) < 1e-9 and abs(b - 4 * 102 / 1024) < 1e-9,
          "3D arrow: frame 37 is column 7, row 3")
    # In the arrow frame: the 3D texture and a frame follow the target; the dart rotation stays 0.
    lua.execute("TEST.hereMap = 1426 TEST.herePos = { 0.5, 0.5 } TEST.facing = 0 R2F.Nav.SetTarget(1426, 60, 50, 'Spot', 'Dun Morogh')")
    lua.execute("R2FNavFrame:Fire('OnUpdate', 1)")
    tex = lua.eval("R2FNavFrame.arrow.__tex")
    check(tex is not None and tex.endswith("arrow3d_gilded"), "3D arrow: the sprite sheet is the texture: %r" % tex)
    check(lua.eval("R2FNavFrame.arrow.__texcoord ~= nil"), "3D arrow: a texture coordinate window is set")
    got = lua.eval("{ unpack(R2FNavFrame.arrow.__texcoord) }")
    want = lua.eval("{ R2F.Nav.FrameCoords(R2F.Nav.FrameFor(-math.pi / 2)) }")
    check(all(abs(got[i] - want[i]) < 1e-9 for i in range(1, 5)), "3D arrow: target east of a north-facing player -> frame 75 (pointing right)")
    check(abs(lua.eval("R2FNavFrame.arrow.__rotation or 0")) < 1e-9, "3D arrow: the picture is not rotated, the frame carries the angle")
    # Switching it off gives the flat dart back.
    lua.execute("R2F.Gameplay.SetOn('arrow3d', false)")
    tex = lua.eval("R2FNavFrame.arrow.__tex")
    check(tex is not None and tex.endswith("arrow") and not tex.endswith("arrow3d"), "3D arrow: switched off, the flat dart texture is back: %r" % tex)
    lua.execute("R2FNavFrame:Fire('OnUpdate', 1)")
    check(abs(lua.eval("R2FNavFrame.arrow.__rotation") + math.pi / 2) < 1e-9, "3D arrow: the flat dart turns by the angle again")
    lua.execute("R2F.Gameplay.SetOn('arrow3d', true)")
    check(lua.eval("string.sub(R2FNavFrame.arrow.__tex, -14)") == "arrow3d_gilded", "3D arrow: back to the sprite sheet")
    # Arrow looks (0.58.0): flat / gold dart / stone arrow, chosen with Nav.SetStyle (the Tweaks buttons).
    lua.execute("R2F.Nav.SetStyle('dart')")
    check(lua.eval("R2F.Nav.Style()") == "dart" and lua.eval("R2FNavFrame.arrow.__tex").endswith("arrow3d_dart"), "3D arrow: the gold dart look")
    lua.execute("R2F.Nav.SetStyle('flat')")
    tex = lua.eval("R2FNavFrame.arrow.__tex")
    check(lua.eval("R2F.Nav.Style()") == "flat" and tex.endswith("arrow") and not tex.endswith("arrow3d"), "3D arrow: the flat look: %s" % tex)
    lua.execute("R2F.Nav.SetStyle('arrow')")
    check(lua.eval("R2F.Nav.Style()") == "arrow" and lua.eval("R2FNavFrame.arrow.__tex").endswith("arrow3d"), "3D arrow: the stone arrow look")
    check(lua.eval("R2F.Nav.SetStyle('nonsense')") is False, "3D arrow: an unknown look is refused")
    for look in ("gilded", "plate", "slab"):
        # painted looks: rendered into sprite sheets like the modelled ones
        lua.execute("R2F.Nav.SetStyle('%s')" % look)
        lua.execute("R2FNavFrame:Fire('OnUpdate', 1)")
        check(lua.eval("R2F.Nav.Style()") == look and lua.eval("R2FNavFrame.arrow.__tex").endswith("arrow3d_" + look), "arrow look %s: its sprite sheet" % look)
    for look in ("block", "needle"):
        lua.execute("R2F.Nav.SetStyle('%s')" % look)
        check(lua.eval("R2F.Nav.Style()") == look and lua.eval("R2FNavFrame.arrow.__tex").endswith("arrow3d_" + look), "3D arrow: the %s look" % look)
    lua.execute("R2F.Nav.SetStyle('arrow')")
def test_quest_weapons():
    """Weapons along the route: quest rewards matched to plan steps by zone and level, class and faction, upgrades only."""
    lua, T = plan_runtime()
    lua.execute("QW = R2F.QuestWeapons")
    for text, want in (("12\u201314", [12, 14]), ("~5", [5, 5]), ("16", [16, 16]), ("29\u201331", [29, 31])):
        got = lua.eval("{ QW.LevelRange(%r) }" % text)
        check([got[1], got[2]] == want, "quest weapons: level range %r -> %s" % (text, want))
    check(lua.eval("QW.LevelRange('Early')") is None and lua.eval("QW.LevelRange('Thu\u2013Fri')") is None, "quest weapons: no level in the step -> nil")
    check(lua.eval("QW.ZoneInTitle('The Hall of Thanes', 'Hall of Thanes \u2014 one clear')") is True
          and lua.eval("QW.ZoneInTitle('Wetlands', 'Darkshore \u2014 quest against the flow')") is False,
          "quest weapons: a zone is matched in the step title (a leading 'The' is ignored)")
    check(lua.eval("QW.CanUse('HUNTER', 'bow')") is True and lua.eval("QW.CanUse('MAGE', 'bow')") is False
          and lua.eval("QW.CanUse('PRIEST', 'wand')") is True and lua.eval("QW.CanUse('WARRIOR', 'wand')") is False
          and lua.eval("QW.CanUse('DRUID', 'shield')") is False, "quest weapons: class weapon use")
    check(lua.eval("QW.CanUse('ROGUE', '1h axe')") is True and lua.eval("QW.CanUse('ROGUE', '2h axe')") is False,
          "quest weapons: Forever's table: a Rogue can use one-handed axes (not two-handed)")
    lua.execute("""
      R2F.QuestWeaponData = { items = {
        { 101, 'Ally Bow', 'bow', 5, 'Quest A', 'Zephras Isle', 1, 2 },
        { 102, 'Horde Bow', 'bow', 5, 'Quest H', 'Zephras Isle', 2, 2 },
        { 103, 'High Bow', 'bow', 30, 'Quest B', 'Zephras Isle', 0, 2 },
        { 104, 'Mace', '1h mace', 5, 'Quest C', 'Zephras Isle', 0, 2 },
        { 105, 'Elsewhere Bow', 'bow', 5, 'Quest D', 'Wetlands', 0, 2 },
        { 106, 'Dagger', 'dagger', 6, 'Quest E', 'Zephras Isle', 0, 2 },
        { 107, 'Staff', 'staff', 6, 'Quest F', 'Zephras Isle', 0, 3 },
        { 108, 'Thanes Gun', 'gun', 9, 'Old Incursion', 'The Hall of Thanes', 0, 3 },
      } }
      ZSTEP = { t = 'Zephras Isle together, share every quest', lvl = '1\u201312' }
    """)
    ids = lambda cls, side: sorted(c["id"] for c in lua.eval("QW.Candidates(ZSTEP, '%s', %d)" % (cls, side)).values())
    check(ids("HUNTER", 1) == [101, 106, 107], "quest weapons: Alliance Hunter at Zephras: its own faction, level and weapon types: %s" % ids("HUNTER", 1))
    check(ids("HUNTER", 2) == [102, 106, 107], "quest weapons: a Horde Hunter gets the Horde reward instead: %s" % ids("HUNTER", 2))
    check(ids("MAGE", 1) == [106, 107], "quest weapons: a Mage can use neither the bow nor the mace: %s" % ids("MAGE", 1))
    check(lua.eval("#QW.Candidates({ t = 'Tram to Ironforge, collect all Hall of Thanes quests', lvl = '12' }, 'HUNTER', 1)") == 0,
          "quest weapons: a step that only collects quests gets none")
    check(lua.eval("#QW.Candidates({ t = 'Hall of Thanes \u2014 one clear', lvl = '13\u201315' }, 'HUNTER', 1)") == 1,
          "quest weapons: the dungeon clear gets its quest reward")
    check(lua.eval("#QW.Candidates({ t = 'Hall of Thanes \u2014 one clear', lvl = '' }, 'HUNTER', 1)") == 0,
          "quest weapons: a step with no level range gets none")

    # Upgrades only, best per slot, from the live stats.
    install_item_stubs(lua)
    lua.execute("""
      UnitFactionGroup = function() return 'Alliance' end
      R2F.playerClass = 'HUNTER'
      TEST.gsItems['item:101'] = { stats = { ITEM_MOD_AGILITY_SHORT = 10, ITEM_MOD_INTELLECT_SHORT = 10 }, loc = 'INVTYPE_RANGEDRIGHT', cls = 2, sub = 2 }
      TEST.gsItems['item:106'] = { stats = { ITEM_MOD_AGILITY_SHORT = 4, ITEM_MOD_INTELLECT_SHORT = 4 }, loc = 'INVTYPE_WEAPON', cls = 2, sub = 15 }
      TEST.gsItems['item:107'] = { stats = { ITEM_MOD_AGILITY_SHORT = 8, ITEM_MOD_INTELLECT_SHORT = 8 }, loc = 'INVTYPE_2HWEAPON', cls = 2, sub = 10 }
      R2F.Plan.Select('hwd')
      ZID = nil
      for _, st in ipairs(R2F.Plan.Steps('hwd')) do if st.t:find('Zephras Isle together', 1, true) then ZID = st.id end end
    """)
    lua.execute("LINES = R2F.QuestWeapons.StepLines('hwd')[ZID] or {}")
    by_slot = {lua.eval("LINES[%d].slot" % i): lua.eval("LINES[%d].id" % i) for i in range(1, lua.eval("#LINES") + 1)}
    check(by_slot == {"ranged": 101, "mainhand": 107}, "quest weapons: one line per slot, the better main hand wins: %s" % by_slot)
    check("(quest: Quest A)" in lua.eval("LINES[1].text") or "(quest: Quest F)" in lua.eval("LINES[1].text"), "quest weapons: the line names the quest: %r" % lua.eval("LINES[1].text"))
    lua.execute("TEST.gsItems['item:900'] = { stats = { ITEM_MOD_AGILITY_SHORT = 50, ITEM_MOD_INTELLECT_SHORT = 50 }, loc = 'INVTYPE_2HWEAPON', cls = 2, sub = 10 } TEST.worn[16] = 'item:900' TEST.worn[17] = 'item:900'")
    lua.execute("LINES = R2F.QuestWeapons.StepLines('hwd')[ZID] or {}")
    check(lua.eval("#LINES") == 1 and lua.eval("LINES[1].slot") == "ranged", "quest weapons: nothing that beats the worn main hand shows, the ranged one still does")
    lua.execute("TEST.worn[16] = nil TEST.worn[17] = nil TEST.gsItems['item:101'].stats = nil TEST.requested = {}")
    check(lua.eval("#(R2F.QuestWeapons.StepLines('hwd')[ZID] or {})") == 1 and lua.eval("#TEST.requested") >= 1,
          "quest weapons: an item whose stats are not loaded yet shows no line and is asked for")
    lua.execute("TEST.gsItems['item:101'].stats = { ITEM_MOD_AGILITY_SHORT = 10, ITEM_MOD_INTELLECT_SHORT = 10 } R2F.playerClass = 'MAGE'")
    lua.execute("LINES = R2F.QuestWeapons.StepLines('hwd')[ZID] or {}")
    check(lua.eval("#LINES") == 1 and lua.eval("LINES[1].slot") == "mainhand", "quest weapons: a Mage gets no bow line (class weapon use)")
    # On the Plan tab
    lua.execute("R2F.playerClass = 'HUNTER' R2F.MainWindow.Show('plan') R2F.PlanTab.Refresh()")
    check(font_text(lua, "^Weapon: .*Ally Bow.* %(quest: Quest A%)") is not None, "quest weapons: the Plan tab shows 'Weapon: <item> (quest: <quest>)'")
    # Hover: the item tooltip, the score gain over what is worn, and where it comes from.
    find_frames(lua, "f.w ~= nil and f.w.id == 101 and f.__shown", "WTIP")
    check(lua.eval("#WTIP") == 1, "quest weapons: the Ally Bow line has a hover frame")
    lua.execute("WTIP[1]:Fire('OnEnter')")
    tip = " | ".join(str(x) for x in lua_table_to_list(lua.eval("GameTooltip.lines")))
    check("BiZ score +" in tip and "Reward of the quest Quest A (Zephras Isle)" in tip and "Compared with the item you wear" in tip,
          "quest weapons: the tooltip says the score gain and the quest: %s" % tip)
    lua.execute("WTIP[1]:Fire('OnLeave')")
    check(lua.eval("GameTooltip.__shown") is False, "quest weapons: leaving hides the tooltip")
    # The real data
    lua.execute("R2F.QuestWeaponData = nil")
    check(lua.eval("R2F.QuestWeaponData == nil"), "quest weapons: (data reset)")


def test_unknown_events():
    """Forever has no LEARNED_SPELL_IN_TAB (it is LEARNED_SPELL_IN_SKILL_LINE) and RegisterEvent errors on an
    unknown event: loading must not fail, and the new name must reach the same handlers."""
    before = """
      local realCreate = CreateFrame
      CreateFrame = function(...)
        local f = realCreate(...)
        local reg = f.RegisterEvent
        f.RegisterEvent = function(self, e)
          if e == 'LEARNED_SPELL_IN_TAB' then error('Attempt to register unknown event "' .. e .. '"', 2) end
          return reg(self, e)
        end
        return f
      end
    """
    lua = new_runtime(before_load=before)
    T = lua.eval("TEST")
    check(lua.eval("R2F ~= nil"), "unknown event: the addon loads although LEARNED_SPELL_IN_TAB is refused")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    lua.execute("R2FCharDB.training = R2FCharDB.training or {} CALLS_OK = 0")
    # The new event reaches the Ranks / refresh handler without an error.
    lua.execute("R2F.Ranks.OnLearned = function() CALLS_OK = CALLS_OK + 1 end")
    T.fire("LEARNED_SPELL_IN_SKILL_LINE", 101, 1, False)
    check(lua.eval("CALLS_OK") == 1, "unknown event: LEARNED_SPELL_IN_SKILL_LINE runs the learned-spell handler")


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


def bag_drag(lua, name, point, x, y, shift=True):
    """Simulate a Shift+drag (v0.20.0): the game reports `point` for the frame after StopMovingOrSizing."""
    lua.execute("%s.GetPoint = function() return %r, UIParent, %r, %d, %d end" % (name, point, point, x, y))
    lua.execute("TEST.shift = %s %s:Fire('OnDragStart') %s:Fire('OnDragStop') TEST.shift = false TEST.fire('MODIFIER_STATE_CHANGED')" % ("true" if shift else "false", name, name))
    lua.execute("%s.GetPoint = nil" % name)   # the game reports the point again (the fake keeps what SetPoint set)


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
    check(lua.eval("ANCHOR_CALLS") == anchors and bag_point(lua, "ContainerFrame1") == "BOTTOMRIGHT,UIParent,BOTTOMRIGHT,-10,100",
          "15.3 Movable off: the bags go back to where the game put them, WITHOUT calling the game's placement (it taints the bag code)")
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
                " TEST.shift = true ContainerFrame1:Fire('OnDragStart') ContainerFrame1:Fire('OnDragStop') TEST.shift = false")
    check(lua.eval("R2FCharDB.bags.bags[0][1]") == "BOTTOMLEFT" and lua.eval("R2FCharDB.bags.bags[0][3]") == 111
          and lua.eval("R2FCharDB.bags.bags[0][4]") == 222, "15.3 relative anchor -> saved as absolute BOTTOMLEFT")

    # --- v0.20.0: Shift+drag, grips, no game placement calls, ForeverPlus note ------------------------------------------
    lua, T = bag_runtime(True, True)
    lua.execute("R2F.Bags.SetMovable(true) ContainerFrame1:Show() ContainerFrameCombinedBags:Show() UpdateContainerFrameAnchors()")
    lua.execute("MOVES = 0")
    bag_drag(lua, "ContainerFrame1", "LEFT", 7, 8, shift=False)
    check(lua.eval("MOVES") == 0 and lua.eval("R2FCharDB.bags.bags[0] == nil"), "15.3 without Shift a drag on the bag window does nothing (the title stays the game's)")
    bag_drag(lua, "ContainerFrame1", "LEFT", 7, 8, shift=True)
    check(lua.eval("MOVES") == 1 and lua.eval("R2FCharDB.bags.bags[0][3]") == 7, "15.3 Shift+drag moves and saves it")
    # The grip over the title takes the mouse only while Shift is held.
    mouse = lambda: lua.eval("(function() local n = 0 for _, f in ipairs(TEST.allFrames) do if f.__mouse and f.__parent == ContainerFrame1 then n = n + 1 end end return n end)()")
    check(mouse() == 0, "15.3 no Shift: the grip over the title does not take the mouse")
    lua.execute("TEST.shift = true") ; T.fire("MODIFIER_STATE_CHANGED")
    check(mouse() == 1, "15.3 Shift held: the grip takes the mouse (the title bar becomes a handle)")
    lua.execute("TEST.shift = false") ; T.fire("MODIFIER_STATE_CHANGED")
    check(mouse() == 0, "15.3 Shift released: the grip lets go")
    lua.execute("R2F.Bags.SetLock(true) TEST.shift = true") ; T.fire("MODIFIER_STATE_CHANGED")
    check(mouse() == 0, "15.3 locked: Shift does not arm the grip")
    lua.execute("R2F.Bags.SetLock(false) TEST.shift = true") ; T.fire("MODIFIER_STATE_CHANGED")
    T.combat = True
    T.fire("MODIFIER_STATE_CHANGED")
    check(mouse() == 0, "15.3 combat: the grip is never armed")
    T.combat = False
    lua.execute("TEST.shift = false")
    # Grip's own drag handler starts the move too (the title bar drag).
    lua.execute("MOVES = 0 TEST.shift = true")
    for g in range(1):
        lua.execute("""for _, f in ipairs(TEST.allFrames) do if f.__parent == ContainerFrame1 and f.__scripts.OnDragStart then GRIP = f end end
          GRIP.__mouse = true GRIP:Fire('OnDragStart')""")
    check(lua.eval("MOVES") == 1, "15.3 dragging the title grip moves the window")
    lua.execute("GRIP:Fire('OnDragStop') TEST.shift = false")
    # Never run the game's placement code from our side.
    lua.execute("ANCHOR_CALLS = 0 R2F.Bags.SetMovable(false) R2F.Bags.SetMovable(true) R2F.Bags.SetLock(true) R2F.Bags.SetLock(false)")
    check(lua.eval("ANCHOR_CALLS") == 0, "15.3 switching settings never calls UpdateContainerFrameAnchors (ForeverPlus got 'blocked from an action' from that)")
    # ForeverPlus note.
    T.chat = lua.table()
    lua.execute("C_AddOns = { IsAddOnLoaded = function(name) return name == 'ForeverPlus' end }")
    lua.execute('SlashCmdList.R2F("bags")')
    check("ForeverPlus is loaded" in chat_all(lua), "15.3 /r2f bags warns when ForeverPlus (which also moves the bag window) is loaded")
    T.chat = lua.table()
    lua.execute("C_AddOns = { IsAddOnLoaded = function(name) return false end }")
    lua.execute('SlashCmdList.R2F("bags")')
    check("ForeverPlus" not in chat_all(lua), "15.3 no ForeverPlus warning when it is not loaded")

    # --- Settings tab boxes ----------------------------------------------------------------------------------------
    lua, T = bag_runtime(True, False)
    lua.execute("R2F.MainWindow.Show('gameplay') R2F.GameplayTab.ShowPage('bags')")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.BAGS_MOVABLE", "BM")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.BAGS_LOCK", "BL")
    check(lua.eval("#BM") == 1 and lua.eval("#BL") == 1 and lua.eval("BM[1]:IsVisible()") is True,
          "15.3 Tweaks > Bags page has Movable bags + Lock bags")
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
    lua.execute("R2F.MainWindow.Show('gameplay') R2F.GameplayTab.ShowPage('bags')")
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
    keys = [lua.eval("R2F.MainWindow.TABS[%d]" % i) for i in range(1, 7)]
    check(keys == ["home", "macros", "talents", "plan", "bis", "gameplay"], "15.4/15.5/19 tab order: %s" % keys)
    lua.execute('SlashCmdList.R2F("reminders")')
    lua.execute('R2F.GameplayTab.ShowPage("icons")')
    check(MW.CurrentTab() == "gameplay", "15.4 /r2f reminders (the old name) opens the Gameplay tab")
    title = lua.eval("R2F.MainWindow.Title()")
    check(title == "Road to Forever: Tweaks", "15.4 Reminders title: %r" % title)
    check(lua.eval("R2FStanceFrame ~= nil") and lua.eval("R2FAmmoFrame == nil") and lua.eval("R2FAmmoScale == nil"),
          "15.4 Warrior: stance frame only, no ammo frame or ammo controls")
    # Class icons page, two columns (0.63.2): repair / countdown / tracking on the left, the class ones on the right.
    check(lua.eval("R2F.RemindersTab.TotalHeight(1)") > 0 and lua.eval("R2F.RemindersTab.TotalHeight(2)") > 0,
          "class icons page: both columns have sections")
    check(lua.eval("R2FStanceScale ~= nil and R2FStanceScale:IsVisible()") is True, "15.4 stance size slider is on the Reminders tab")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.SETTINGS_STANCE_SHOW", "SS")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.SETTINGS_STANCE_LOCK", "SL")
    check(lua.eval("#SS") == 1 and lua.eval("#SL") == 1 and lua.eval("SS[1]:IsVisible()") is True, "15.4 stance Show / Lock boxes on the Reminders tab")
    lua.execute("SL[1]:Click()")   # the stance icon starts locked, so the click unlocks it
    check(lua.eval("R2FDB.stance.lock") is False and lua.eval("SL[1]:GetChecked()") is False, "15.4 stance Lock works from the new tab")
    lua.execute("SL[1]:Click() SS[1]:Click()")
    check(lua.eval("R2FDB.stance.shown") is False, "15.4 stance Show works from the new tab")
    lua.execute("SS[1]:Click() R2FStanceScale:Fire('OnValueChanged', 150)")
    check(lua.eval("R2FDB.stance.scale") == 1.5, "15.4 stance size slider works from the new tab")
    lua.execute("R2F.MainWindow.SelectTab('settings')")
    check(lua.eval("SS[1]:IsVisible()") is False and lua.eval("R2FStanceScale:IsVisible()") is False,
          "15.4 the stance options are no longer on the Settings tab")
    # Controls only write SavedVariables: still usable in combat.
    lua.execute("R2F.MainWindow.SelectTab('gameplay')")
    T.combat = True
    T.fire("PLAYER_REGEN_DISABLED")
    check(lua.eval("SS[1]:IsEnabled()") is True and lua.eval("SL[1]:IsEnabled()") is True, "15.4 Reminders controls stay enabled in combat")
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")

    lua, T = reminder_runtime("HUNTER")
    check(lua.eval("R2FAmmoFrame ~= nil") and lua.eval("R2FStanceFrame == nil") and lua.eval("R2FStanceScale == nil"),
          "15.4 Hunter: ammo frame only")
    lua.execute("R2F.MainWindow.Show('gameplay') R2F.GameplayTab.ShowPage('icons')")
    check(lua.eval("R2FAmmoScale:IsVisible() and R2FAmmoThreshold:IsVisible()") is True, "15.4 Hunter sees the ammo size + threshold sliders")
    # Rested XP (0.64.0): the bank as a percent of the level's bar; gold icon, hidden without rested XP once locked.
    lua.execute("TEST.bank = 450 TEST.need = 900 GetXPExhaustion = function() return TEST.bank end UnitXPMax = function() return TEST.need end")
    check(abs(lua.eval("R2F.Rested.Percent()") - 50) < 1e-9, "rested: 450 of a 900 bar = 50 percent")
    lua.execute("R2FDB.rested.shown = true R2F.Rested.SetLock(true)")
    check(lua.eval("R2FRestedFrame:IsShown()") is True and lua.eval("R2FRestedFrame.count.__text") == "50%", "rested: the icon says 50%")
    lua.execute("TEST.bank = nil R2F.Rested.Update()")
    check(lua.eval("R2FRestedFrame:IsShown()") is False, "rested: none left and locked: hidden")
    lua.execute("GetXPExhaustion = nil")
    check(lua.eval("R2F.Rested.Percent()") is None, "rested: no experience API: nothing")
    # Buff countdown (0.63.0): Walk on Air shows the seconds left on the buff, big, and nothing when it is off (locked).
    lua.execute("""TEST.now = 1000 TEST.aura = { name = 'Walking on Air', spellId = 1259417, expirationTime = 1007, icon = 'x' }
      GetTime = function() return TEST.now end
      C_UnitAuras = { GetUnitAuras = function() if TEST.aura then return { TEST.aura } end return {} end }""")
    check(abs(lua.eval("(R2F.Timers.Remaining(R2F.Timers.TRACK[1]))") - 7) < 1e-9, "timer: 7 seconds left on Walking on Air")
    lua.execute("R2F.Timers.TRACK[1].module.SetLock(true) R2F.Timers.TRACK[1].module.Apply()")
    check(lua.eval("R2FWalkonairFrame:IsShown()") is True and lua.eval("R2FWalkonairFrame.count.__text") == "7.0", "timer: the icon counts down: 7.0")
    lua.execute("TEST.now = 1002.5 R2F.Timers.TRACK[1].module.Apply()")
    check(lua.eval("R2FWalkonairFrame.count.__text") == "4.5", "timer: 4.5 a little later")
    lua.execute("TEST.aura = nil R2F.Timers.TRACK[1].module.Apply()")
    check(lua.eval("R2FWalkonairFrame:IsShown()") is False, "timer: no buff, locked: hidden")
    lua.execute("TEST.aura = { name = 'Walking on Air', spellId = 1259417, expirationTime = 1007 } C_UnitAuras.GetUnitAuras = function() return { { name = 'x', spellId = 1, expirationTime = 5 } } end")
    check(lua.eval("(R2F.Timers.Remaining(R2F.Timers.TRACK[1]))") is None, "timer: another buff only: nothing")
    lua.execute("issecretvalue = function() return true end")
    check(lua.eval("(R2F.Timers.Remaining(R2F.Timers.TRACK[1]))") is None, "timer: secret values: nothing shown, nothing guessed")
    lua.execute("issecretvalue = nil")
    # The section of a buff nobody has to learn (food) shows for everyone, also when the client has the spell API;
    # the Walk on Air one only for a character who knows the spell.
    lua.execute("IsPlayerSpell = function() return false end")
    check(lua.eval("R2F.Timers.Applies(R2F.Timers.TRACK[2])") is True and lua.eval("R2F.Timers.Applies(R2F.Timers.TRACK[1])") is False,
          "timers: food is for everyone, Walk on Air only with the spell")
    lua.execute("IsPlayerSpell = function(id) return id == 1259416 end")
    check(lua.eval("R2F.Timers.Applies(R2F.Timers.TRACK[1])") is True, "timers: Walk on Air with the spell known")
    lua.execute("IsPlayerSpell = nil")
    # Food buff (0.64.1): any "Well Fed" buff counts down in minutes; optional "No food" nag only when the auras were readable.
    lua.execute("""WF = R2F.Timers.TRACK[2] TEST.now = 2000
      C_UnitAuras = { GetUnitAuras = function() return { { name = 'Well Fed', spellId = 5, expirationTime = 2900, icon = 'f' } } end }
      WF.module.SetLock(true) WF.module.Apply()""")
    check(lua.eval("WF.key") == "wellfed" and lua.eval("R2FWellfedFrame:IsShown()") is False, "food: Well Fed on, locked: no icon, no timer")
    lua.execute("R2FDB.timers.wellfed.remindMissing = true WF.module.Apply()")
    check(lua.eval("R2FWellfedFrame:IsShown()") is False, "food: Well Fed on, nag on: still nothing on screen")
    lua.execute("R2FDB.timers.wellfed.remindMissing = false WF.module.Apply()")
    lua.execute("C_UnitAuras.GetUnitAuras = function() return {} end WF.module.Apply()")
    check(lua.eval("R2FWellfedFrame:IsShown()") is False, "food: no buff, nag off: hidden")
    lua.execute("R2FDB.timers.wellfed.remindMissing = true WF.module.Apply()")
    check(lua.eval("R2FWellfedFrame:IsShown()") is True and lua.eval("R2FWellfedFrame.count.__text") == "No food", "food: nag on, no buff: No food")
    check(lua.eval("R2FWellfedFrame.icon:IsShown()") is False and lua.eval("R2FWellfedFrame.border:IsShown()") is False,
          "food: the No food nag is text only (no icon, no frame)")
    lua.execute("R2FDB.timers.wellfed.lock = false WF.module.Apply()")
    check(lua.eval("R2FWellfedFrame.icon:IsShown()") is True, "food: unlocked to move it: the icon is back")
    lua.execute("R2FDB.timers.wellfed.lock = true WF.module.Apply()")
    # Quiet on a flight and in the capitals (the nag is still on, no buff).
    lua.execute("UnitOnTaxi = function() return true end WF.module.Apply()")
    check(lua.eval("R2FWellfedFrame:IsShown()") is False, "food: on a flight: no nag")
    lua.execute("UnitOnTaxi = function() return false end WF.module.Apply()")
    check(lua.eval("R2FWellfedFrame:IsShown()") is True, "food: flight over: the nag is back")
    for mid in (1453, 1454, 1455, 1456, 1457, 1458):
        lua.execute("C_Map = { GetBestMapForUnit = function() return %d end } WF.module.Apply()" % mid)
        check(lua.eval("R2FWellfedFrame:IsShown()") is False, "food: capital map %d: no nag" % mid)
    lua.execute("C_Map = { GetBestMapForUnit = function() return 1429 end } WF.module.Apply()")
    check(lua.eval("R2FWellfedFrame:IsShown()") is True, "food: Elwynn Forest: nag shows")
    lua.execute("GetRealZoneText = function() return 'Orgrimmar' end WF.module.Apply()")
    check(lua.eval("R2FWellfedFrame:IsShown()") is False, "food: zone name Orgrimmar: no nag")
    lua.execute("GetRealZoneText = nil C_Map = nil UnitOnTaxi = nil WF.module.Apply()")
    check(lua.eval("R2FWellfedFrame:IsShown()") is True, "food: no location APIs: the nag shows as before")
    lua.execute("issecretvalue = function() return true end C_UnitAuras.GetUnitAuras = function() return { { name = 'x' } } end WF.module.Apply()")
    check(lua.eval("R2FWellfedFrame:IsShown()") is False, "food: auras unreadable: no nag")
    lua.execute("issecretvalue = nil R2FDB.timers.wellfed.remindMissing = false")
    # Newer version heard (0.64.1): compared as three numbers, said once, saved, ignored when old / invalid / mine / switched off.
    check(lua.eval("R2F.Version.Compare('0.64.1', '0.64.0')") == 1 and lua.eval("R2F.Version.Compare('0.9.0', '0.10.0')") == -1
          and lua.eval("R2F.Version.Compare('1.0.0', '1.0.0')") == 0 and lua.eval("R2F.Version.Compare('x', '1.0.0')") is None, "version: numbers compare as numbers")
    lua.execute("TEST.metadata.Version = '0.64.0' R2FDB.newerVersion = nil TEST.chat = {}")
    lua.execute("R2F.Version.OnAddonMessage('R2FV', 'V	0.63.0', 'GUILD', 'Old-Realm') R2F.Version.OnAddonMessage('R2FV', 'V	junk', 'GUILD', 'X-R')")
    lua.execute("R2F.Version.OnAddonMessage('OTHER', 'V	9.9.9', 'GUILD', 'X-R') R2F.Version.OnAddonMessage('R2FV', 'V	9.9.9', 'GUILD', UnitName('player') .. '-R')")
    check(lua.eval("R2FDB.newerVersion") is None and lua.eval("R2F.Version.Newer()") is None, "version: older, invalid, other prefix and my own message change nothing")
    lua.execute("R2F.Version.OnAddonMessage('R2FV', 'V	0.65.0', 'GUILD', 'New-Realm') R2F.Version.OnAddonMessage('R2FV', 'V	0.66.0', 'PARTY', 'New2-Realm')")
    check(lua.eval("R2F.Version.Newer()") == "0.66.0", "version: the newest heard version is kept")
    check(sum(1 for c in lua_table_to_list(lua.eval("TEST.chat")) if "new version is out" in c) == 1, "version: the chat line comes once")
    lua.execute("R2F.Gameplay.SetOn('updatecheck', false) R2FDB.newerVersion = nil R2F.Version.OnAddonMessage('R2FV', 'V	7.0.0', 'GUILD', 'A-R')")
    check(lua.eval("R2FDB.newerVersion") is None, "version: switched off, nothing is heard")
    lua.execute("R2F.Gameplay.SetOn('updatecheck', true) R2FDB.newerVersion = nil")
    # Pet reminder (0.62.0): Hunters and Warlocks only; missing / dead / unhappy, quiet when mounted or dead yourself.
    check(lua.eval("R2FPetFrame ~= nil") and lua.eval("R2FPetScale ~= nil"), "pet: the Hunter has the pet icon and its size slider")
    lua.execute("""TEST.pet = { exists = false, dead = false, happy = 3 } TEST.mounted = false TEST.selfDead = false
      UnitExists = function(u) if u == "pet" then return TEST.pet.exists end return true end
      UnitIsDead = function(u) return u == "pet" and TEST.pet.dead end
      UnitIsDeadOrGhost = function() return TEST.selfDead end
      IsMounted = function() return TEST.mounted end
      GetPetHappiness = function() return TEST.pet.happy end""")
    check(lua.eval("R2F.Pet.Problem()") == "missing", "pet: no pet out")
    lua.execute("TEST.pet.exists = true TEST.pet.dead = true")
    check(lua.eval("R2F.Pet.Problem()") == "dead", "pet: dead pet")
    lua.execute("TEST.pet.dead = false TEST.pet.happy = 1")
    check(lua.eval("R2F.Pet.Problem()") == "unhappy", "pet: unhappy Hunter pet")
    lua.execute("TEST.pet.happy = 3")
    check(lua.eval("R2F.Pet.Problem()") is None, "pet: a happy pet is fine")
    lua.execute("TEST.pet.exists = false TEST.mounted = true")
    check(lua.eval("R2F.Pet.Problem()") is None, "pet: no reminder while mounted")
    lua.execute("TEST.mounted = false TEST.selfDead = true")
    check(lua.eval("R2F.Pet.Problem()") is None, "pet: no reminder while you are dead")
    lua.execute("TEST.selfDead = false R2FDB.pet.shown = true R2F.Pet.SetLock(true) R2F.Pet.Update()")
    check(lua.eval("R2FPetFrame:IsShown()") is True and lua.eval("R2FPetFrame.count.__text") == "No pet", "pet: the icon says No pet")
    lua, T = reminder_runtime("PRIEST")
    check(lua.eval("R2FAmmoFrame == nil and R2FStanceFrame == nil and R2FAmmoScale == nil and R2FStanceScale == nil"),
          "15.4 Priest: no reminder frames or controls")
    lua.execute("R2F.MainWindow.Show('gameplay') R2F.GameplayTab.ShowPage('icons')")
    check(font_text(lua, "^No reminders for your class") is None and font_text(lua, "^" + "Missing group buffs") is not None, "15.4 every class has the group-buff reminder, so the 'none yet' line is gone")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("ammo")')
    check(any("Hunters only" in c for c in lua_table_to_list(lua.eval("TEST.chat"))), "15.4 /r2f ammo on a Priest explains")
    # Repair reminder (0.62.0): the worst piece you wear, in percent; red under the threshold.
    lua.execute("""TEST.dur = { [1] = { 100, 100 }, [5] = { 20, 100 }, [10] = { 90, 100 } }
      GetInventoryItemDurability = function(slot) local d = TEST.dur[slot] if d then return d[1], d[2] end end""")
    check(abs(lua.eval("R2F.Repair.Worst()") - 20) < 1e-9, "repair: the worst piece is 20 percent")
    check(lua.eval("R2F.Repair.IsLow(R2F.Repair.Worst())") is True and lua.eval("R2F.Repair.IsLow(60)") is False, "repair: low under the 25 percent default")
    lua.execute("R2FDB.repair.shown = true R2F.Repair.Update()")
    check(lua.eval("R2FRepairFrame:IsShown()") is True and lua.eval("R2FRepairFrame.count.__text") == "20%", "repair: the icon shows 20%")
    lua.execute("TEST.dur[5] = { 95, 100 } R2F.Repair.SetLock(true)")
    check(lua.eval("R2FRepairFrame:IsShown()") is False, "repair: fine gear hides the icon")
    lua.execute("TEST.dur = {} GetInventoryItemDurability = nil")
    check(lua.eval("R2F.Repair.Worst()") is None, "repair: nothing that wears, nothing to show")

    # --- Ammo counting ----------------------------------------------------------------
    lua, T = reminder_runtime("HUNTER")
    check(lua.eval("(R2F.Ammo.Count())") == 0, "15.4 no ammo equipped counts as 0")
    lua.execute("TEST.ammoItem = 11285 TEST.ammoCount = 1500")
    check(lua.eval("(R2F.Ammo.Count())") == 1500, "15.4 equipped ammo: the slot's total count")
    lua.execute("TEST.ammoCount = 37")
    check(lua.eval("(R2F.Ammo.Count())") == 37, "15.4 count follows the item")
    lua.execute("local old = C_Container.GetContainerItemInfo C_Container.GetContainerItemInfo = function() error('boom') end "
                "COUNT_ERR = R2F.Ammo.Count() C_Container.GetContainerItemInfo = old")
    check(lua.eval("COUNT_ERR") is None, "15.4 a failing bag API is caught: nothing to count, no error")

    # --- v0.24.1: this client has NO ammo slot; count the ammunition the ranged weapon fires -------------------------
    lua, T = reminder_runtime("HUNTER")
    check(lua.eval("GetInventoryItemID('player', 0)") == 0 and lua.eval("GetInventoryItemCount('player', 0)") == 1,
          "15.4.1 (the stub answers like the real client's ammo slot: id 0, count 1)")
    lua.execute("TEST.ammoItem = nil")
    check(lua.eval("(R2F.Ammo.Count())") == 0, "15.4.1 slot 0's fake 'count 1' is not used: a bow and no arrows is 0, not 1")
    lua.execute("TEST.bagItems = { [0] = { { itemID = 2512, stackCount = 100 }, { itemID = 2589, stackCount = 5 }, { itemID = 2512, stackCount = 250 } },"
                " [1] = { { itemID = 2516, stackCount = 400 }, { itemID = 2512, stackCount = 50 } } }")
    check(lua.eval("(R2F.Ammo.Count())") == 400, "15.4.1 a bow counts arrows only, over all bags and stacks (100 + 250 + 50), not bullets or other items: %s" % lua.eval("(R2F.Ammo.Count())"))
    lua.execute("TEST.rangedItem = 2507")
    check(lua.eval("(R2F.Ammo.Count())") == 400, "15.4.1 a gun counts bullets only (400)")
    lua.execute("TEST.bagItems[1][1].stackCount = 123 TEST.rangedItem = 2508")
    check(lua.eval("(R2F.Ammo.Count())") == 400, "15.4.1 a crossbow counts arrows too (400)")
    lua.execute("TEST.rangedItem = 2515")
    check(lua.eval("(R2F.Ammo.Count())") is None, "15.4.1 a thrown weapon needs no ammunition: nothing to count")
    lua.execute("TEST.noRanged = true")
    check(lua.eval("(R2F.Ammo.Count())") is None, "15.4.1 no ranged weapon: nothing to count")
    lua.execute("R2F.Ammo.SetLock(true) R2F.Ammo.Update()")
    check(lua.eval("R2FAmmoFrame:IsShown()") is False, "15.4.1 no ranged weapon + locked: the icon stays hidden (no red 'low ammo' for a Hunter who isn't shooting)")
    lua.execute("R2F.Ammo.SetLock(false) R2F.Ammo.Update()")
    check(lua.eval("R2FAmmoFrame:IsShown()") is True and lua.eval("R2FAmmoFrame.count.__text") == "-", "15.4.1 unlocked with nothing to count: shown grey with '-' so it can be placed")
    lua.execute("TEST.noRanged = nil TEST.rangedItem = 2504 R2F.Ammo.Update()")
    check(lua.eval("R2FAmmoFrame.icon.__tex") == "Interface\\Icons\\INV_Ammo_Arrow_03", "15.4.1 the icon is the arrows' icon from the bags")

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
    lua.execute("R2F.MainWindow.Show('gameplay') R2F.GameplayTab.ShowPage('icons') R2FAmmoThreshold:Fire('OnValueChanged', 650)")
    check(lua.eval("R2FDB.ammo.threshold") == 650, "15.4 the threshold slider sets it")
    check(font_text(lua, "^Turn red below: 650$") is not None, "15.4 the slider label shows the value")

    # --- Events and combat -------------------------------------------------------------------------
    lua, T = reminder_runtime("HUNTER")
    lua.execute("TEST.ammoItem = 11285 TEST.ammoCount = 1500 R2F.Ammo.SetLock(true)")
    for event in ("BAG_UPDATE_DELAYED", "UNIT_INVENTORY_CHANGED", "PLAYER_EQUIPMENT_CHANGED"):
        lua.execute("TEST.ammoCount = 1500 R2F.Ammo.Update()")
        lua.execute("TEST.ammoCount = 10")
        T.fire(event, "player")
        check(lua.eval("R2FAmmoFrame:IsShown()") is True, "15.4 %s updates the icon" % event)
    lua.execute("TEST.ammoCount = 1500 R2F.Ammo.Update() TEST.ammoCount = 10")
    T.fire("UNIT_INVENTORY_CHANGED", "party1")
    check(lua.eval("R2FAmmoFrame:IsShown()") is False, "15.4 a party member's inventory change doesn't recount your bags")
    T.combat = True
    T.errors = lua.table()
    lua.execute("TEST.ammoCount = 1500")
    T.fire("BAG_UPDATE_DELAYED")
    check(lua.eval("R2FAmmoFrame:IsShown()") is False and lua_table_to_list(lua.eval("TEST.errors")) == [],
          "15.4 works in combat: updates with no errors")
    lua.execute("TEST.ammoCount = 20")
    T.fire("BAG_UPDATE_DELAYED")
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
    check(lua.eval("R2FDB.stance.x") == 33 and lua.eval("R2FDB.stance.y") == 44 and lua.eval("R2FDB.ammo.x") == 327,
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


PLAN_MAPS_LUA = """
  C_Map = {
    GetMapChildrenInfo = function(root, mapType, all)
      if root ~= 947 then return {} end
      return {
        { mapID = 1426, name = 'Dun Morogh', mapType = 3 },
        { mapID = 9999, name = 'Dun Morogh', mapType = 4 },
        { mapID = 1455, name = 'Ironforge', mapType = 3 },
        { mapID = 1428, name = 'Burning Steppes', mapType = 3 },
      }
    end,
    GetMapInfo = function(id)
      local names = { [947] = 'Azeroth', [1426] = 'Dun Morogh', [9999] = 'Dun Morogh', [1455] = 'Ironforge' }
      if names[id] then return { mapID = id, name = names[id], mapType = 3 } end
    end,
    GetBestMapForUnit = function() return TEST.hereMap end,
    GetPlayerMapPosition = function(id, unit)
      if TEST.herePos then return { GetXY = function() return TEST.herePos[1], TEST.herePos[2] end } end
    end,
  }
"""

PLAN_SEP = chr(30)


# BiZNav world stub: Dun Morogh (1426) is a 1000 x 1000 yard square on continent 0 with the
# game's axes (world x = north, world y = west); Ironforge (1455) is on continent 1 so it
# counts as "another continent"; 9999 has no world position.
NAV_WORLD_LUA = """
  function CreateVector2D(x, y) return { x = x, y = y, GetXY = function(v) return v.x, v.y end } end
  C_Map.GetWorldPosFromMapPos = function(mapID, v)
    if mapID == 1426 then return 0, CreateVector2D(1000 * (1 - v.y), 1000 * (1 - v.x)) end
    if mapID == 1455 then return 1, CreateVector2D(1000 * (1 - v.y), 1000 * (1 - v.x)) end
  end
  C_Map.GetMapPosFromWorldPos = function(cont, v, mapID)
    if cont == 0 and mapID == 1426 then return 1426, CreateVector2D(1 - v.y / 1000, 1 - v.x / 1000) end
    return nil
  end
  TEST.facing = 0
  function GetPlayerFacing() return TEST.facing end
"""


def plan_runtime(templates=True, maps=True, nav=False, preset=None):
    lua = new_runtime(templates)
    lua.execute("TEST.reset()")
    if not templates:
        lua.execute("TEST.templates.UIPanelScrollFrameTemplate = nil")
    if maps:
        lua.execute(PLAN_MAPS_LUA)
    if nav:
        lua.execute(NAV_WORLD_LUA)
    if preset:
        lua.execute("R2FCharDB = %s" % preset)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    lua.execute("""function DUMP(plan)
      local o = {}
      for i, s in ipairs(R2F.Plan.Steps(plan)) do
        local tg = {}
        for _, t in ipairs(s.tags) do tg[#tg + 1] = t[1] .. ':' .. t[2] end
        o[i] = table.concat({ s.phase, s.id, s.lvl or '', s.t or '', s.n or '', table.concat(tg, '|') }, string.char(30))
      end
      return o
    end""")
    return lua, T


def chat_all(lua):
    return "\n".join(lua.eval("TEST.chat[%d]" % n) for n in range(1, lua.eval("#TEST.chat") + 1))


def test_plan(templates=True):
    """ADDON_PLAN 15.5: Launch Plan tab: plan filtering, ticks, map resolution, TomTom / no-TomTom."""
    import subprocess
    node_gen = os.path.join(ROOT, "addon", "tools", "gen_plan_data.js")
    tag = "templates" if templates else "fallbacks"

    if templates:
        # --- Generated data is current; plan filtering equals the site's own resolve() ------------
        r = subprocess.run(["node", node_gen, "--check"], capture_output=True, text=True)
        check(r.returncode == 0, "15.5 PlanData.lua is up to date with launch-plan.html (run python build.py): %s" % r.stderr.strip())
        exp = json.loads(subprocess.check_output(["node", node_gen, "--expected"]).decode("utf-8"))
        lua, T = plan_runtime()
        union = set()
        for plan, steps in exp["plans"].items():
            want = [PLAN_SEP.join([s["phase"], s["id"], s["lvl"], s["t"], s["n"], "|".join(k + ":" + v for k, v in s["tags"])]) for s in steps]
            got = lua_table_to_list(lua.eval("DUMP(%r)" % plan))
            check(got == want, "15.5 plan %s: the addon shows the same %d steps with the same texts as the site's resolve()" % (plan, len(want)))
            if got != want:
                for a, b in zip(got, want):
                    if a != b:
                        print("   first difference:", repr(a[:120]), "vs", repr(b[:120]))
                        break
            union |= {s["id"] for s in steps}
        check(len(union) == 45, "15.5 45 launch-day steps over all plans (got %d)" % len(union))
        check(not any(i.startswith("b-") or i.startswith("t-") for i in union) and "h-loot" not in union,
              "15.5 the pre-launch and beta lists are not in the data")
        check(exp["phases"] == ["night", "p1", "p2", "p3"], "15.5 only the launch-day phases")
        # Spot checks of the rules, independent of the comparison above.
        ids = lambda plan: [s.split(PLAN_SEP)[1] for s in lua_table_to_list(lua.eval("DUMP(%r)" % plan))]
        check("n-dalaran" not in ids("trio") and "n-dalaran" in ids("hwd"), "15.5 a step hidden for one plan (false) stays for the others")
        check("tr-coldridge" in ids("trio") and "tr-coldridge" not in ids("hunter") and "tr-coldridge" not in ids("hwd")
              and "tr-coldridge" not in ids("h3d"), "15.5 hidden on `hunter` also hides on its base-inheriting plans (hwd, h3d)")
        check("wd-bear" in ids("hwd") and "wd-bear" in ids("h3d") and "wd-bear" not in ids("hunter"),
              "15.5 an empty override (hwd = {}) keeps the step visible, shadowing the base's false")
        check(lua.eval("R2F.Plan.Resolve({ id = 'x', t = 'a', ov = { hunter = { t = 'b' } } }, 'h3d').t") == "b",
              "15.5 base override applies through the chain (h3d -> hunter)")
        check(lua.eval("R2F.Plan.Resolve({ id = 'x', t = 'a', ov = { hunter = { t = 'b' }, h3d = { t = 'c' } } }, 'h3d').t") == "c",
              "15.5 the plan's own override beats the base's")
        check(lua.eval("R2F.Plan.Resolve({ id = 'x', t = 'a', ov = { hunter = false, h3d = { n = 'z' } } }, 'h3d').t") == "a",
              "15.5 own override shadows the base's `false`")

        # --- Waypoint lists: plan list replaces the default ---------------------------------------
        check(lua.eval("#R2F.Plan.Points('tr-coldridge', 'trio')") == 1 and lua.eval("#R2F.Plan.Points('tr-coldridge', 'hwd')") == 0,
              "15.5 a step's per-plan points (trio) do not leak into other plans")
        check(lua.eval("R2F.Plan.Points('h-pet', 'hwd')[1].zone") == "Zephras Isle" and lua.eval("R2F.Plan.Points('h-pet', 'hwd')[1].x") == 45.2
              and lua.eval("R2F.Plan.Points('h-pet', 'trio')[1].zone") == "Dun Morogh",
              "15.5 per-plan list replaces the default for that plan only")
        check(lua.eval("#R2F.Plan.Points('nope', 'hwd')") == 0, "15.5 steps without points give an empty list")
        wp = json.load(open(os.path.join(ROOT, "launch-plan-waypoints.json"), encoding="utf-8"))["steps"]
        count = sum(len(pts) for st in wp.values() for pts in st.values())
        got = lua.eval("""(function() local n = 0 for id, w in pairs(R2F.PlanData.waypoints) do
          for _, pts in pairs(w) do n = n + #pts end end return n end)()""")
        check(got == count, "15.5 every waypoint point from the JSON is in the addon data (%d)" % count)

        # --- Ticks and saved state (per character) -------------------------------------------------
        lua, T = plan_runtime()
        check(lua.eval("R2F.Plan.Selected()") == "hwd" and lua.eval("R2FCharDB.plan ~= nil and R2FDB.plan == nil"),
              "15.5 default plan hwd, stored per character")
        done, total = lua.eval("R2F.Plan.Progress('hwd')")
        check(done == 0 and total == len(exp["plans"]["hwd"]), "15.5 progress 0 of %d for hwd" % total)
        first = lua.eval("R2F.Plan.Next('hwd').id")
        lua.execute("R2F.Plan.SetDone(%r, true)" % first)
        check(lua.eval("R2FCharDB.plan.done[%r]" % first) is True and lua.eval("R2F.Plan.IsDone(%r)" % first) is True, "15.5 a tick is saved")
        check(lua.eval("R2F.Plan.Next('hwd').id") != first, "15.5 the next step moves on after a tick")
        check(lua.eval("(R2F.Plan.Progress('hwd'))") == 1, "15.5 progress counts the tick")
        lua.execute("R2F.Plan.SetDone('n-camp', true)")
        check(lua.eval("(R2F.Plan.Progress('trio'))") == 1 and lua.eval("(R2F.Plan.Progress('hwd'))") == 2,
              "15.5 a tick is shared by every plan that has the step (n-camp is in hwd and trio)")
        lua.execute("R2F.Plan.SetDone('n-camp', false)")
        lua.execute("R2F.Plan.SetDone(%r, false)" % first)
        check(lua.eval("R2FCharDB.plan.done[%r]" % first) is None, "15.5 unticking removes it")
        check(lua.eval("R2F.Plan.Select('trio')") is True and lua.eval("R2FCharDB.plan.selected") == "trio", "15.5 the chosen plan is saved")
        check(lua.eval("R2F.Plan.Select('nope')") is False and lua.eval("R2F.Plan.Selected()") == "trio", "15.5 an unknown plan is refused")
        lua.execute("for _, s in ipairs(R2F.Plan.Steps('trio')) do R2F.Plan.SetDone(s.id, true) end")
        check(lua.eval("R2F.Plan.Next('trio')") is None, "15.5 all done: no next step")
        # Relog: ticks and the plan come back; a bad saved plan is repaired.
        lua, T = plan_runtime(preset="{ plan = { selected = 'h3d', done = { ['n-zephras'] = true } } }")
        check(lua.eval("R2F.Plan.Selected()") == "h3d" and lua.eval("R2F.Plan.IsDone('n-zephras')") is True, "15.5 relog: plan and ticks persisted")
        lua, T = plan_runtime(preset="{ plan = { selected = 'bogus' } }")
        check(lua.eval("R2F.Plan.Selected()") == "hwd" and lua.eval("type(R2FCharDB.plan.done)") == "table", "15.5 a bad saved plan falls back to hwd")

        # --- Map resolution -------------------------------------------------------------------------------
        lua, T = plan_runtime()
        check(lua.eval("R2F.Plan.ResolveMap('Dun Morogh', 1426)") == 1426, "15.5 map hint used when its name matches")
        check(lua.eval("R2F.Plan.ResolveMap('Dun Morogh', 555)") == 1426, "15.5 wrong hint ignored; name lookup prefers the zone map over the dungeon one")
        check(lua.eval("R2F.Plan.ResolveMap('ironforge')") == 1455, "15.5 name lookup is case-insensitive")
        check(lua.eval("R2F.Plan.ResolveMap('Zephras Isle')") is None, "15.5 a zone this client doesn't have resolves to nil")
        check(lua.eval("R2F.Plan.ResolveMap(nil)") is None, "15.5 no zone name -> nil")
        lua.execute("C_Map = nil R2F.Plan.ResetMapCache()")
        check(lua.eval("R2F.Plan.ResolveMap('Dun Morogh')") is None, "15.5 no C_Map at all -> nil, no error")
        lua.execute(PLAN_MAPS_LUA + " R2F.Plan.ResetMapCache()")
        check(lua.eval("R2F.Plan.ResolveMap('Burning Steppes')") == 1428, "15.5 the map list is rebuilt when C_Map shows up later")

        # --- Waypoint paths: our arrow (BiZNav), the /way line, check points ---------------------------
        exact = "{ zone = 'Dun Morogh', mapHint = 1426, x = 29.9, y = 71.2, label = 'Anvilmar', conf = 'exact' }"
        lua, T = plan_runtime(nav=True)
        T.chat = lua.table()
        lua.execute("R = R2F.Plan.Waypoint(%s)" % exact)
        tgt = lua.eval("R2F.Nav.Target()")
        check(lua.eval("R") == "arrow" and tgt is not None and tgt.mapID == 1426 and tgt.x == 29.9 and tgt.label == "Anvilmar",
              "BiZNav: the Waypoint button points the arrow at mapID x y")
        check("arrow: Anvilmar" in chat_all(lua) and lua.eval("R2FNavFrame:IsShown()") is True, "BiZNav: chat confirms and the arrow shows")
        T.chat = lua.table()
        lua.execute("R = R2F.Plan.Waypoint({ zone = 'Zephras Isle', x = 10, y = 20, label = 'Valanaar', conf = 'approx' })")
        check(lua.eval("R") == "line" and "/way Zephras Isle 10 20 Valanaar" in chat_all(lua)
              and "no map called Zephras Isle" in chat_all(lua) and lua.eval("R2F.Nav.Target().label") == "Anvilmar",
              "BiZNav: unknown map prints the /way line and keeps the old arrow")
        T.chat = lua.table()
        lua.execute("R = R2F.Plan.Waypoint({ zone = 'Zephras Isle', label = 'Valanaar', conf = 'check' })")
        check(lua.eval("R") is None and chat_all(lua) == "", "15.5 check points: no waypoint, nothing printed")
        lua, T = plan_runtime(nav=False)
        T.chat = lua.table()
        lua.execute("R = R2F.Plan.Waypoint(%s)" % exact)
        check(lua.eval("R") == "line" and "/way Dun Morogh 29.9 71.2 Anvilmar" in chat_all(lua) and lua.eval("R2F.Nav.Target()") is None,
              "BiZNav: a client without GetWorldPosFromMapPos gets the /way line: %r" % chat_all(lua))
        check(lua.eval("R2F.Nav.Supported()") is False and lua.eval("R2F.Plan.HasPosition({ conf = 'check' })") is False
              and lua.eval("R2F.Plan.HasPosition({ conf = 'exact', x = 1, y = 2 })") is True, "BiZNav Supported / HasPosition")

        # --- The arrow: direction, distance, other continent, no position, arrival, clear --------------------
        lua, T = plan_runtime(nav=True)
        lua.execute("R2F.Library.db.gameplay.arrow3d = false")   # the flat dart rotates; the 3D arrow picks a frame
        lua.execute("TEST.hereMap = 1426 TEST.herePos = { 0.5, 0.5 }")
        def arrow(facing, x, y):
            lua.execute("TEST.facing = %r R2F.Nav.SetTarget(1426, %r, %r, 'Spot', 'Dun Morogh')" % (facing, x, y))
            lua.execute("R2FNavFrame:Fire('OnUpdate', 1)")
            return lua.eval("R2FNavFrame.arrow.__rotation"), lua.eval("R2FNavFrame.dist.__text")
        import math
        rot, dist = arrow(0, 50, 40)
        check(abs(rot) < 1e-9 and dist == "100 yd", "BiZNav: target 100 yd north, facing north -> straight up: %r %r" % (rot, dist))
        rot, _ = arrow(0, 60, 50)
        check(abs(rot + math.pi / 2) < 1e-9, "BiZNav: target east, facing north -> arrow turned right (clockwise): %r" % rot)
        rot, _ = arrow(0, 40, 50)
        check(abs(rot - math.pi / 2) < 1e-9, "BiZNav: target west -> arrow turned left: %r" % rot)
        rot, _ = arrow(math.pi / 2, 50, 40)
        check(abs(rot + math.pi / 2) < 1e-9, "BiZNav: facing west, target north -> arrow turned right: %r" % rot)
        rot, _ = arrow(0, 50, 60)
        check(abs(abs(rot) - math.pi) < 1e-9, "BiZNav: target south -> arrow points down: %r" % rot)
        _, dist = arrow(0, 50, 0)  # 500 yd north, on the map's top edge
        check(dist == "500 yd", "BiZNav: a target on the map's edge still measures: %r" % dist)
        lua.execute("R2F.Nav.SetTarget(1426, 99.5, 99.5, 'Corner', 'Dun Morogh') R2FNavFrame:Fire('OnUpdate', 1)")
        check(abs(lua.eval("R2FNavFrame.arrow.__rotation") + 3 * math.pi / 4) < 1e-6,
              "BiZNav: south-east corner target (probe flipped at the edge) -> down-right: %r" % lua.eval("R2FNavFrame.arrow.__rotation"))
        lua.execute("R2F.Nav.SetTarget(1455, 50, 50, 'IF', 'Ironforge') R2FNavFrame:Fire('OnUpdate', 1)")
        check(lua.eval("R2FNavFrame.arrow:IsShown()") is False and "another continent (Ironforge)" in lua.eval("R2FNavFrame.dist.__text"),
              "BiZNav: another continent hides the arrow and says so")
        lua.execute("R2F.Nav.SetTarget(1426, 50, 40, 'Spot', 'Dun Morogh') TEST.hereMap = nil R2FNavFrame:Fire('OnUpdate', 1)")
        check(lua.eval("R2FNavFrame.arrow:IsShown()") is False and lua.eval("R2FNavFrame.dist.__text") == "no position here",
              "BiZNav: no player position (instance) hides the arrow")
        check(lua.eval("R2F.Nav.SetTarget(9999, 50, 50, 'X', 'Nowhere')") is False, "BiZNav: a map with no world position is refused")
        T.chat = lua.table()
        lua.execute("TEST.hereMap = 1426 TEST.herePos = { 0.5, 0.405 } R2FNavFrame:Fire('OnUpdate', 1)")
        check(lua.eval("R2F.Nav.Target()") is None and lua.eval("R2FNavFrame:IsShown()") is False and "arrived: Spot" in chat_all(lua),
              "BiZNav: within 10 yd the target is reached, cleared and announced")
        lua.execute("R2F.Nav.SetTarget(1426, 50, 40, 'Spot', 'Dun Morogh') R2FNavFrame:Fire('OnMouseUp', 'RightButton')")
        check(lua.eval("R2F.Nav.Target()") is None and lua.eval("R2FNavFrame:IsShown()") is False, "BiZNav: right-click clears the arrow")
        lua.execute("R2FNavFrame.__cx, R2FNavFrame.__cy = 30, 40 R2FNavFrame:Fire('OnDragStart') R2FNavFrame:Fire('OnDragStop')")
        check(lua.eval("R2FDB.nav.x") == 30 and lua.eval("R2FDB.nav.y") == 40, "BiZNav: dragging saves the arrow position")
        # /r2f way and /r2f clear
        T.chat = lua.table()
        lua.execute('SlashCmdList.R2F("way Dun Morogh 47.4 52.5 Kharanos Inn")')
        tgt = lua.eval("R2F.Nav.Target()")
        check(tgt is not None and tgt.mapID == 1426 and tgt.x == 47.4 and tgt.y == 52.5 and tgt.label == "Kharanos Inn"
              and "arrow: Kharanos Inn" in chat_all(lua), "BiZNav: /r2f way Zone x y label sets the arrow, label keeps its capitals")
        T.chat = lua.table()
        lua.execute('SlashCmdList.R2F("way dun morogh 10, 20")')
        check(lua.eval("R2F.Nav.Target().x") == 10 and "dun morogh 10.0, 20.0" in chat_all(lua), "BiZNav: /r2f way without a label names the spot")
        T.chat = lua.table()
        lua.execute('SlashCmdList.R2F("way Nowhere 1 2 spot")')
        check("no map called Nowhere" in chat_all(lua), "BiZNav: an unknown zone followed by a label says so")
        T.chat = lua.table()
        lua.execute('SlashCmdList.R2F("way")')
        lua.execute('SlashCmdList.R2F("way Dun Morogh 147 2")')
        check(chat_all(lua).count("usage: /bizway") == 2, "BiZNav: /r2f way without coordinates (or out of range) shows the usage")
        # /bizway: x y in the zone you are in, a label before the numbers, clear, size
        T.chat = lua.table()
        lua.execute('SlashCmdList.R2FWAY("45 34")')
        tgt = lua.eval("R2F.Nav.Target()")
        check(tgt is not None and tgt.mapID == 1426 and tgt.x == 45 and tgt.y == 34 and tgt.label == "Dun Morogh 45.0, 34.0",
              "BiZNav: /bizway x y points at that spot in the zone you are in")
        lua.execute('SlashCmdList.R2FWAY("go here 45 34")')
        tgt = lua.eval("R2F.Nav.Target()")
        check(tgt.mapID == 1426 and tgt.label == "go here" and tgt.x == 45, "BiZNav: /bizway go here 45 34 = label + spot in your zone")
        lua.execute('SlashCmdList.R2FWAY("12 13 Camp")')
        check(lua.eval("R2F.Nav.Target().label") == "Camp", "BiZNav: /bizway x y label")
        lua.execute('SlashCmdList.R2FWAY("Dun Morogh 47.4 52.5")')
        check(lua.eval("R2F.Nav.Target().x") == 47.4, "BiZNav: /bizway zone x y still works")
        lua.execute('SlashCmdList.R2FWAY("size large")')
        check(lua.eval("R2FDB.nav.size") == "large" and abs(lua.eval("R2FNavFrame:GetScale()") - 1.8) < 1e-9
              and "arrow size: Large" in chat_all(lua), "BiZNav: /bizway size large saves and scales the arrow")
        lua.execute('SlashCmdList.R2FWAY("size huge")')
        check(lua.eval("R2FDB.nav.size") == "large", "BiZNav: an unknown size changes nothing")
        lua.execute('SlashCmdList.R2FWAY("clear")')
        check(lua.eval("R2F.Nav.Target()") is None, "BiZNav: /bizway clear")
        lua.execute("TEST.hereMap = nil")
        T.chat = lua.table()
        lua.execute('SlashCmdList.R2FWAY("45 34")')
        check("couldn't read your position" in chat_all(lua) and lua.eval("R2F.Nav.Target()") is None,
              "BiZNav: /bizway x y where the game gives no zone says so")
        lua.execute("TEST.hereMap = 1426")

        # World map: pin at the target, Alt + right-click sets the arrow.
        lua.execute("""
          local wm = CreateFrame('Frame', 'WorldMapFrame', UIParent)
          wm.ScrollContainer = CreateFrame('Frame', nil, wm)
          wm.ScrollContainer.Child = CreateFrame('Frame', nil, wm.ScrollContainer)
          wm.ScrollContainer.Child.GetWidth = function() return 1000 end
          wm.ScrollContainer.Child.GetHeight = function() return 600 end
          wm.mapID = 1426
          wm.GetMapID = function(self) return self.mapID end
          wm.ScrollContainer.GetNormalizedCursorPosition = function() return TEST.cursor[1], TEST.cursor[2] end
          TEST.alt = false
          function IsAltKeyDown() return TEST.alt end
        """)
        check(lua.eval("R2F.Nav.HookMap()") is True, "BiZNav: the world map is hooked once it exists")
        lua.execute("R2F.Nav.SetTarget(1426, 40, 25, 'Spot', 'Dun Morogh') WorldMapFrame:Show() R2F.Nav.UpdatePin()")
        pt = lua.eval("R2FNavPin.__point")
        check(lua.eval("R2FNavPin:IsShown()") is True and pt is not None and abs(pt[4] - 400) < 1e-6 and abs(pt[5] + 150) < 1e-6,
              "BiZNav: the map pin sits at the target on its own map")
        lua.execute("WorldMapFrame.mapID = 1455 R2F.Nav.UpdatePin()")
        check(lua.eval("R2FNavPin:IsShown()") is False, "BiZNav: no pin on a map the target is not on")
        lua.execute("WorldMapFrame.mapID = 1426 WorldMapFrame:Hide() R2F.Nav.UpdatePin()")
        check(lua.eval("R2FNavPin:IsShown()") is False, "BiZNav: no pin while the map is closed")
        lua.execute("WorldMapFrame:Show() R2F.Nav.Clear()")
        check(lua.eval("R2FNavPin:IsShown()") is False, "BiZNav: clearing the arrow removes the pin")
        lua.execute("TEST.cursor = { 0.3, 0.6 } WorldMapFrame.ScrollContainer:Fire('OnMouseDown', 'RightButton')")
        check(lua.eval("R2F.Nav.Target()") is None, "BiZNav: a plain right-click on the map does nothing")
        T.chat = lua.table()
        lua.execute("TEST.alt = true WorldMapFrame.ScrollContainer:Fire('OnMouseDown', 'RightButton')")
        tgt = lua.eval("R2F.Nav.Target()")
        check(tgt is not None and tgt.mapID == 1426 and abs(tgt.x - 30) < 1e-9 and abs(tgt.y - 60) < 1e-9
              and "arrow: Dun Morogh 30.0, 60.0" in chat_all(lua), "BiZNav: Alt + right-click on the map sets the arrow there")
        lua.execute("R2F.Nav.Clear() WorldMapFrame.ScrollContainer:Fire('OnMouseDown', 'LeftButton')")
        check(lua.eval("R2F.Nav.Target()") is None, "BiZNav: Alt + left-click does nothing")
        lua.execute("TEST.alt = false R2F.Nav.SetTarget(1426, 50, 20, 'Spot', 'Dun Morogh')")

        # Tweaks > Waypoint arrow: Small / Medium / Large buttons; Reset page puts Medium back.
        lua.execute("R2F.MainWindow.Show('gameplay') R2F.GameplayTab.ShowPage('arrow')")
        find_frames(lua, "f.__kind == 'Button' and f.navSize ~= nil", "SIZEBTN")
        names = sorted(lua.eval("SIZEBTN[%d].navSize" % i) for i in range(1, lua.eval("#SIZEBTN") + 1))
        check(names == ["large", "medium", "small"], "BiZNav: Tweaks has Small / Medium / Large arrow buttons: %r" % names)
        lua.execute("for _, b in ipairs(SIZEBTN) do if b.navSize == 'small' then b:Click() end end")
        check(lua.eval("R2FDB.nav.size") == "small" and abs(lua.eval("R2FNavFrame:GetScale()") - 1.0) < 1e-9,
              "BiZNav: clicking Small saves and applies it")
        lua.execute("R2F.GameplayTab.ResetPage()")
        check(lua.eval("R2FDB.nav.size") == "medium", "BiZNav: Reset page on Waypoint arrow puts the arrow back to Medium")

        # Questie: Ctrl + click on a map icon calls TomTom:AddWaypoint(uiMapId, x/100, y/100, {title, crazy, from})
        # and, on the next click, TomTom:RemoveWaypoint(saved) first (same icon = toggle off).
        check(lua.eval("TomTom == R2F.Nav.TomTomShim") is True, "BiZNav: without TomTom the stand-in is installed at login")
        T.chat = lua.table()
        lua.execute("QWP = TomTom:AddWaypoint(1426, 0.3, 0.7, { title = 'Wendigo', crazy = true, from = 'Questie' })")
        tgt = lua.eval("R2F.Nav.Target()")
        check(tgt is not None and tgt.mapID == 1426 and abs(tgt.x - 30) < 1e-9 and abs(tgt.y - 70) < 1e-9 and tgt.label == "Wendigo"
              and lua.eval("QWP[1] == 1426 and QWP[2] == 0.3 and QWP[3] == 0.7 and QWP.title == 'Wendigo' and QWP.from == 'Questie'")
              and "arrow: Wendigo" in chat_all(lua), "BiZNav: Questie's AddWaypoint points the arrow and returns the waypoint it keeps")
        lua.execute("TomTom:RemoveWaypoint({ 1426, 0.1, 0.1 })")
        check(lua.eval("R2F.Nav.Target() ~= nil"), "BiZNav: removing a different waypoint keeps the arrow")
        lua.execute("TomTom:RemoveWaypoint(QWP)")
        check(lua.eval("R2F.Nav.Target()") is None, "BiZNav: Questie's RemoveWaypoint (same icon again) clears the arrow")
        check(lua.eval("TomTom:AddWaypoint(9999, 0.5, 0.5, { title = 'X' })") is None, "BiZNav: a map with no world position returns nil")
        lua.execute("TomTom = nil C_AddOns = C_AddOns or {} OLD_LOADED = C_AddOns.IsAddOnLoaded "
                    "C_AddOns.IsAddOnLoaded = function(n) return n == 'TomTom' end")
        check(lua.eval("R2F.Nav.InstallTomTomShim()") is False and lua.eval("TomTom") is None,
              "BiZNav: no stand-in when the real TomTom addon is loaded")
        lua.execute("REAL = { AddWaypoint = function() end } TomTom = REAL C_AddOns.IsAddOnLoaded = OLD_LOADED")
        check(lua.eval("R2F.Nav.InstallTomTomShim()") is False and lua.eval("TomTom == REAL"), "BiZNav: never replaces an existing TomTom table")
        lua.execute("TomTom = R2F.Nav.TomTomShim")
        lua.execute("R2F.Nav.SetTarget(1426, 50, 20, 'Spot', 'Dun Morogh')")

        T.chat = lua.table()
        lua.execute('SlashCmdList.R2F("clear")')
        check(lua.eval("R2F.Nav.Target()") is None and chat_all(lua) == "", "BiZNav: /r2f clear removes the arrow")
        lua.execute('SlashCmdList.R2F("clear")')
        check("no arrow set" in chat_all(lua), "BiZNav: /r2f clear with nothing set says so")
        check(lua.eval("R2F.Plan.MayHaveMoved({ conf = 'classic' })") is True and lua.eval("R2F.Plan.MayHaveMoved({ conf = 'approx' })") is True
              and lua.eval("R2F.Plan.MayHaveMoved({ conf = 'exact' })") is False, "15.5 classic / approx get the 'may have moved' note, exact does not")

        # --- /r2f here ---------------------------------------------------------------------------------------------
        lua, T = plan_runtime()
        T.chat = lua.table()
        lua.execute("TEST.hereMap = 1426 TEST.herePos = { 0.474, 0.525 }")
        lua.execute('SlashCmdList.R2F("here")')
        txt = chat_all(lua)
        check("here: Dun Morogh (uiMapID 1426) 47.4, 52.5" in txt and "/way Dun Morogh 47.4 52.5" in txt, "15.5 /r2f here prints zone, uiMapID, x, y and a /way line: %r" % txt)
        T.chat = lua.table()
        lua.execute("TEST.hereMap = nil")
        lua.execute('SlashCmdList.R2F("here")')
        check("couldn't read your position" in chat_all(lua), "15.5 /r2f here without a map says so")
        T.chat = lua.table()
        lua.execute("TEST.hereMap = 1426 TEST.herePos = nil")
        lua.execute('SlashCmdList.R2F("here")')
        check("couldn't read your position" in chat_all(lua), "15.5 /r2f here without a position says so")
        lua.execute('SlashCmdList.R2F("plan")')
        check(lua.eval("R2F.MainWindow.CurrentTab()") == "plan", "15.5 /r2f plan opens the Plan tab")

    # --- The Plan tab (both template chains) ------------------------------------------------------------------------
    lua, T = plan_runtime(templates=templates, nav=False)
    lua.execute("R2F.MainWindow.Show('plan')")
    title = lua.eval("R2F.MainWindow.Title()")
    check(title == "Road to Forever: Plan", "%s: Plan title: %r" % (tag, title))
    check(lua.eval("R2F.MainWindow.TABS[4]") == "plan" and lua.eval("#R2F.MainWindow.TABS") == 6, "%s: six tabs, Plan fourth" % tag)
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text ~= '' and f.stepId == nil", "PICKS")
    labels = [lua.eval("PICKS[%d].r2fLabel.__text" % i) for i in range(1, lua.eval("#PICKS") + 1)]
    wanted = [lua.eval("R2F.Plan.Label(%r)" % p) for p in ("hwd", "hunter", "h3d", "trio")]
    check(all(w in labels for w in wanted), "%s: the picker has all four group plans" % tag)
    n_hwd = lua.eval("#R2F.Plan.Steps('hwd')")
    check(font_text(lua, "^0 of %d launch%%-day steps done$" % n_hwd) is not None, "%s: progress line" % tag)
    find_frames(lua, "f.__kind == 'CheckButton' and f.stepId ~= nil and f:IsVisible()", "STEPS")
    check(lua.eval("#STEPS") == n_hwd, "%s: one tick box per step of the plan (%s)" % (tag, lua.eval("#STEPS")))
    lua.execute("STEPS[1]:Click()")
    first = lua.eval("STEPS[1].stepId")
    check(lua.eval("R2F.Plan.IsDone(%r)" % first) is True and font_text(lua, "^1 of %d launch" % n_hwd) is not None,
          "%s: ticking a box saves it and updates the progress line" % tag)
    # Switch plan: the list changes and ticks are kept per step id.
    wanted_trio = lua.eval("#R2F.Plan.Steps('trio')")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.Plan.Label('trio')", "TRIOBTN")
    lua.execute("TRIOBTN[1]:Click()")
    find_frames(lua, "f.__kind == 'CheckButton' and f.stepId ~= nil and f:IsVisible()", "STEPS")
    check(lua.eval("R2F.Plan.Selected()") == "trio" and lua.eval("#STEPS") == wanted_trio,
          "%s: picking Paladin · Hunter · Shaman shows its %d steps" % (tag, wanted_trio))
    # Waypoint lines: the trio's Coldridge step has a classic point; the Zephras step a check point.
    find_frames(lua, "f.__kind == 'Button' and f.point ~= nil and f:IsVisible()", "WPB")
    check(lua.eval("#WPB") >= 1 and lua.eval("WPB[1].__text") == "Show /way", "%s: a client without an arrow says Show /way" % tag)
    lua.execute("for _, b in ipairs(WPB) do if b.point.label:find('Anvilmar') then ANVIL = b end end")
    T.chat = lua.table()
    lua.execute("ANVIL:Click()")
    check("/way Dun Morogh 28.8 67.6 Anvilmar, Coldridge Valley" in chat_all(lua), "%s: clicking prints the /way line: %r" % (tag, chat_all(lua)))
    check(font_text(lua, "may have moved") is not None, "%s: a classic point shows the 'may have moved' note" % tag)
    # Every real position is known now; give the first step one spot with no position to see how the tab shows it.
    lua.execute("""local s = R2F.Plan.Steps('hwd')[1]
      R2F.PlanData.waypoints[s.id] = R2F.PlanData.waypoints[s.id] or { default = {} }
      table.insert(R2F.PlanData.waypoints[s.id].default, { zone = 'Nowhere', label = 'Unknown spot', conf = 'check' })
      R2F.Plan.Select('hwd') R2F.PlanTab.Refresh()""")
    check(font_text(lua, "position not known yet") is not None, "%s: a check point shows its label with 'position not known yet'" % tag)
    find_frames(lua, "f.__kind == 'Button' and f.point ~= nil and f:IsVisible() and f.point.conf == 'check'", "CHK")
    check(lua.eval("#CHK") == 0, "%s: check points have no button" % tag)
    # With the arrow available: the button says Waypoint and points the arrow.
    lua.execute(NAV_WORLD_LUA)
    lua.execute("R2F.Plan.Select('trio') R2F.PlanTab.Refresh()")
    find_frames(lua, "f.__kind == 'Button' and f.point ~= nil and f:IsVisible()", "WPB")
    check(lua.eval("WPB[1].__text") == "Waypoint", "%s: with the arrow the button says Waypoint" % tag)
    lua.execute("for _, b in ipairs(WPB) do if b.point.label:find('Anvilmar') then ANVIL = b end end ANVIL:Click()")
    check(lua.eval("R2F.Nav.Target() and R2F.Nav.Target().mapID") == 1426, "%s: clicking Waypoint points the arrow at the resolved map" % tag)
    # Works in combat (no protected calls).
    lua.execute("R2F.Nav.Clear()")
    T.combat = True
    T.fire("PLAYER_REGEN_DISABLED")
    lua.execute("ANVIL:Click() STEPS[1]:Click()")
    check(lua.eval("R2F.Nav.Target() ~= nil"), "%s: waypoints and ticks work in combat" % tag)
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")

    # --- Quest shopping list (the site's Buyable quests) -----------------------------------------------------------
    lua, T = plan_runtime(templates=templates)
    lua.execute("R2F.MainWindow.Show('plan') R2F.PlanTab.Refresh()")
    exp_q = json.loads(subprocess.check_output(["node", node_gen, "--expected"]).decode("utf-8"))["quests"]
    got_q = [lua.eval("R2F.PlanData.quests.list[%d].id" % i) for i in range(1, lua.eval("#R2F.PlanData.quests.list") + 1)]
    check(got_q == [q["id"] for q in exp_q] and len(got_q) > 10, "%s: the addon has the site's %d buyable quests, same order" % (tag, len(exp_q)))
    got_items = [lua.eval("R2F.PlanData.quests.list[%d].items" % (i + 1)) for i in range(len(exp_q))]
    check(all(len(got_items[i]) == len(q["items"]) for i, q in enumerate(exp_q)), "%s: every quest keeps all its items" % tag)
    find_frames(lua, "f.__kind == 'Button' and f.__text == 'Quest shopping list'", "BUYB")
    check(lua.eval("#BUYB") == 1, "%s: the Plan tab has a Quest shopping list button" % tag)
    lua.execute("BUYB[1]:Click()")
    find_frames(lua, "f.__kind == 'CheckButton' and f.questId ~= nil and f:IsVisible()", "QROWS")
    find_frames(lua, "f.__kind == 'CheckButton' and f.stepId ~= nil and f:IsVisible()", "SROWS")
    check(lua.eval("#QROWS") == len(exp_q) and lua.eval("#SROWS") == 0, "%s: the shopping list shows every quest, no launch steps" % tag)
    check(font_text(lua, "Thelsamar Blood Sausages") is not None and font_text(lua, "3x Boar Intestines") is not None,
          "%s: a quest shows its name and its items with counts" % tag)
    check(font_text(lua, "Phase 1") is not None and font_text(lua, "Off our route") is not None, "%s: grouped by route phase" % tag)
    b0, t0 = lua.eval("R2F.Plan.QuestProgress()")
    lua.execute("QROWS[1]:Click()")
    done_id = lua.eval("QROWS[1].questId")
    check(lua.eval("R2F.Plan.QuestBought('%s')" % done_id) is True and lua.eval("R2F.Plan.QuestProgress()") == (1, t0),
          "%s: ticking a quest is saved per character and counted (route quests only)" % tag)
    check(font_text(lua, "1 of %d route quests ticked off" % t0) is not None, "%s: progress line in the shopping list" % tag)
    check(lua.eval("R2FCharDB.plan.bought['%s']" % done_id) is True, "%s: stored in the character's saved variables" % tag)
    # Click an item: a small box with the NAME (no count) selected, to paste into the auction house search.
    find_frames(lua, "f.__kind == 'Button' and f.itemName ~= nil and f:IsVisible()", "IBTN")
    check(lua.eval("#IBTN") > 10, "%s: every item of every quest is a clickable line (%d)" % (tag, lua.eval("#IBTN")))
    lua.execute("IBTN[1]:Click()")
    find_frames(lua, "f.__kind == 'EditBox' and f.__text == IBTN[1].itemName and f:IsVisible()", "CEDIT")
    check(lua.eval("#CEDIT") >= 1 and lua.eval("R2FCopyItem:IsShown()") is True and lua.eval("not IBTN[1].itemName:find('^%d')"),
          "%s: clicking an item opens the copy box with just its name: %r" % (tag, lua.eval("IBTN[1].itemName")))
    lua.execute("R2FCopyItem:Hide() BUYB[1]:Click()")
    find_frames(lua, "f.__kind == 'CheckButton' and f.questId ~= nil and f:IsVisible()", "QROWS")
    find_frames(lua, "f.__kind == 'CheckButton' and f.stepId ~= nil and f:IsVisible()", "SROWS")
    check(lua.eval("#QROWS") == 0 and lua.eval("#SROWS") > 0, "%s: Back to the steps: the launch-day list returns" % tag)

    # --- Home: next step ------------------------------------------------------------------------------------------------
    lua, T = plan_runtime(templates=templates)
    lua.execute("R2F.MainWindow.Show('home')")
    find_frames(lua, "f.__kind == 'Button' and f.tab ~= nil and f.sub ~= nil", "HOME")
    check(lua.eval("#HOME") == 1 and lua.eval("HOME[1].tab") == "plan", "%s: Home has the launch plan entry" % tag)
    nxt = lua.eval("R2F.Plan.Next('hwd')")
    check(lua.eval("HOME[1].sub.__text") == "Next: [%s] %s" % (nxt.lvl, nxt.t), "%s: Home next-step line: %r" % (tag, lua.eval("HOME[1].sub.__text")))
    lua.execute("R2F.Plan.SetDone(R2F.Plan.Next('hwd').id, true) R2F.Home.Refresh()")
    nxt2 = lua.eval("R2F.Plan.Next('hwd')")
    check(lua.eval("HOME[1].sub.__text") == "Next: [%s] %s" % (nxt2.lvl, nxt2.t) and nxt2.id != nxt.id, "%s: the next-step line follows the ticks" % tag)
    lua.execute("for _, s in ipairs(R2F.Plan.Steps('hwd')) do R2F.Plan.SetDone(s.id, true) end R2F.Home.Refresh()")
    check(lua.eval("HOME[1].sub.__text") == "All launch-day steps done", "%s: Home says all done" % tag)
    lua.execute("HOME[1]:Click()")
    check(lua.eval("R2F.MainWindow.CurrentTab()") == "plan", "%s: clicking the Home entry opens the Plan tab" % tag)


RANK_SPELLBOOK_LUA = """
  -- A fake spellbook for ADDON_PLAN 16. Unranked "Charge" is Forever's top rank (1240289),
  -- which a level-18 Warrior doesn't know; "Rend" resolves to a spell the Warrior knows.
  SPELLS = {
    ['Charge'] = 1240289, ['Charge(Rank 1)'] = 100, ['Charge(Rank 2)'] = 101, ['Charge(Rank 3)'] = 102,
    ['Rend'] = 500, ['Rend(Rank 1)'] = 500, ['Rend(Rank 2)'] = 501,
    ['Hamstring'] = 700,
  }
  KNOWN = { [100] = true, [500] = true, [700] = true }
  C_Spell.GetSpellInfo = function(name)
    local id = SPELLS[name]
    if not id then
      for k, v in pairs(SPELLS) do if k:lower() == name:lower() then id = v name = k end end
    end
    if id then return { name = name, spellID = id } end
  end
  IsPlayerSpell = function(id) return KNOWN[id] == true end
"""


def rank_runtime(known_extra=""):
    lua = new_runtime()
    lua.execute("TEST.reset() R2FDB = nil R2FCharDB = nil")
    lua.execute(RANK_SPELLBOOK_LUA)
    if known_extra:
        lua.execute(known_extra)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    return lua, T


def rank_add(lua, short, body, class_="WARRIOR"):
    lua.globals().RS_SHORT, lua.globals().RS_BODY, lua.globals().RS_CLASS = short, body, class_
    lua.execute("R2F.Library.Apply({ { id = RS_CLASS .. '/' .. RS_SHORT, class = RS_CLASS, section = 'General', "
                "group = 'Damage / offensive', name = RS_SHORT, short = RS_SHORT, body = RS_BODY } }, 1)")
    return class_ + "/" + short


def rewrite(lua, body):
    lua.globals().RB = body
    return lua.eval("(R2F.Ranks.Rewrite(RB))")


def test_ranks():
    """ADDON_PLAN 16: rank-aware game macros (library bodies stay unranked)."""
    lua, T = rank_runtime()
    R1 = "Charge(Rank 1)"
    # --- Rewrite: the section 16 cases ----------------------------------------------------------
    check(rewrite(lua, "#showtooltip Charge\n/cast [harm] Charge") == "#showtooltip Charge(Rank 1)\n/cast [harm] Charge(Rank 1)",
          "16 unranked Charge resolves to an unknown spell -> Rank 1 in #showtooltip and /cast: %r" % rewrite(lua, "#showtooltip Charge\n/cast [harm] Charge"))
    check(rewrite(lua, "/cast Rend") == "/cast Rend", "16 Rend resolves to a known spell: left alone")
    check(rewrite(lua, "/cast Shoot") == "/cast Shoot", "16 a spell the client doesn't know at all: left alone")
    check(rewrite(lua, "/cast Hamstring") == "/cast Hamstring", "16 another known spell: left alone")
    lua.execute("KNOWN[101] = true")
    check(rewrite(lua, "/cast Charge") == "/cast Charge(Rank 2)", "16 Rank 1 and 2 known -> the highest known rank (2)")
    lua.execute("KNOWN[102] = true")
    check(rewrite(lua, "/cast Charge") == "/cast Charge(Rank 3)", "16 Rank 3 known too -> 3")
    lua.execute("KNOWN[100], KNOWN[101], KNOWN[102] = nil, nil, nil")
    check(rewrite(lua, "/cast Charge") == "/cast Charge", "16 no rank known (not learned yet): left alone")
    lua.execute("KNOWN[100] = true")
    # Pinned ranks (the site's Charge(Rank 1) stopgap).
    check(rewrite(lua, "#showtooltip Charge(Rank 1)\n/cast Charge(Rank 1)") == "#showtooltip Charge(Rank 1)\n/cast Charge(Rank 1)",
          "16 a pinned rank with nothing higher known: unchanged")
    lua.execute("KNOWN[101] = true")
    check(rewrite(lua, "/cast Charge(Rank 1)") == "/cast Charge(Rank 2)", "16 a pinned Rank 1 is raised once Rank 2 is known")
    check(rewrite(lua, "/cast Charge(Rank 3)") == "/cast Charge(Rank 3)", "16 a pinned higher rank is never lowered")
    check(rewrite(lua, "/cast Charge ( rank 1 )") == "/cast Charge(Rank 2)", "16 odd spacing / case in the pinned rank is understood")
    lua.execute("KNOWN[101] = nil")
    # Syntax around the name.
    check(rewrite(lua, "/cast [@mouseover,harm][harm] Charge; [help] Rend") == "/cast [@mouseover,harm][harm] Charge(Rank 1); [help] Rend",
          "16 conditionals and ;-clauses are kept")
    check(rewrite(lua, "/cast !Charge") == "/cast !Charge(Rank 1)", "16 the ! prefix is kept")
    check(rewrite(lua, "/CAST Charge") == "/CAST Charge(Rank 1)", "16 /CAST in capitals")
    check(rewrite(lua, "/castsequence reset=5 Charge, Rend") == "/castsequence reset=5 Charge(Rank 1), Rend", "16 /castsequence with reset=")
    check(rewrite(lua, "/castsequence [harm] reset=target Charge, Hamstring, Charge") ==
          "/castsequence [harm] reset=target Charge(Rank 1), Hamstring, Charge(Rank 1)", "16 /castsequence with conditions, repeats")
    check(rewrite(lua, "#showtooltip\n/cast Charge") == "#showtooltip\n/cast Charge(Rank 1)", "16 bare #showtooltip is left alone")
    check(rewrite(lua, "#showtooltip [harm] Charge; Rend") == "#showtooltip [harm] Charge(Rank 1); Rend", "16 #showtooltip with conditionals")
    check(rewrite(lua, "/use Charge\n/startattack\n/say Charge") == "/use Charge\n/startattack\n/say Charge", "16 other commands are never touched")
    check(rewrite(lua, "/cast   [harm]   Charge  ") == "/cast   [harm]   Charge(Rank 1)  ", "16 spacing is preserved")
    # 255-character limit: the ranked text must fit.
    long_body = "/cast Charge\n" + "/say " + "x" * 235
    check(len(long_body) <= 255 and len(long_body.replace("Charge", "Charge(Rank 1)")) > 255, "16 (test body is near the limit)")
    lua.globals().RB = long_body
    r, tooLong = lua.eval("R2F.Ranks.Rewrite(RB)")
    check(r == long_body and tooLong is True, "16 a ranked body over 255 characters is not used (original kept, flagged)")
    # No C_Spell.GetSpellInfo -> nothing happens (the old GetSpellInfo global doesn't exist on this client).
    lua.execute("SAVED_GSI = C_Spell.GetSpellInfo C_Spell.GetSpellInfo = nil")
    check(rewrite(lua, "/cast Charge") == "/cast Charge", "16 without C_Spell.GetSpellInfo nothing is rewritten")
    lua.execute("C_Spell.GetSpellInfo = SAVED_GSI")

    # --- Game macros: create, library untouched, stable on login ------------------------------------
    lua, T = rank_runtime()
    cid = rank_add(lua, "Charge", "#showtooltip Charge\n/cast [harm] Charge")
    rid = rank_add(lua, "Rend", "#showtooltip Rend\n/cast [harm] Rend")
    lua.execute("R2F.Macros.Ensure(%r) R2F.Macros.Ensure(%r)" % (cid, rid))
    check(T.bodyOf("Charge") == "#showtooltip Charge(Rank 1)\n/cast [harm] Charge(Rank 1)", "16 the dragged Charge macro is created with Rank 1: %r" % T.bodyOf("Charge"))
    check(T.bodyOf("Rend") == "#showtooltip Rend\n/cast [harm] Rend", "16 Rend is created exactly as the site has it")
    check(lua.eval("R2F.Library.Get(%r).body" % cid) == "#showtooltip Charge\n/cast [harm] Charge", "16 the library body stays unranked")
    check(lua.eval("R2F.Macros.Classify(%r, R2F.Library.Get(%r))" % (cid, cid)) == "unchanged", "16 a ranked macro counts as up to date, not edited")
    check("Charge" in names_of(lua.eval("R2F.Macros.TidyCandidates()")), "16 the ranked macro is still 'ours, unedited' (Tidy up sees it)")
    T.calls = lua.table()
    n = lua.eval("R2F.Macros.SyncOnLogin()")
    check(n == 0 and lua_table_to_list(lua.eval("TEST.calls")) == [], "16 login sync leaves ranked macros alone (no EditMacro): %s" % lua_table_to_list(lua.eval("TEST.calls")))
    # Import of the same site text: no update planned.
    lua.execute("local e = R2F.Library.Get(%r) PLAN = R2F.Macros.PlanUpdates({ { id = %r, body = e.body, icon = e.icon } }, R2F.Library.db.library)" % (cid, cid))
    plan_n = lua.eval("#PLAN.update")
    check(plan_n == 0, "16 re-importing the same text plans no update for a ranked macro")

    # --- Learning a rank raises the macro ----------------------------------------------------------------
    T.chat = lua.table()
    T.calls = lua.table()
    lua.execute("KNOWN[101] = true")
    T.fire("LEARNED_SPELL_IN_TAB")
    T.runTimers()
    check(T.bodyOf("Charge") == "#showtooltip Charge(Rank 2)\n/cast [harm] Charge(Rank 2)", "16 learning Rank 2 raises the macro: %r" % T.bodyOf("Charge"))
    check(T.bodyOf("Rend") == "#showtooltip Rend\n/cast [harm] Rend" and lua_table_to_list(lua.eval("TEST.calls")) == ["edit:Charge"],
          "16 only the macro that needed it was edited: %s" % lua_table_to_list(lua.eval("TEST.calls")))
    check("raised spell ranks in 1 macro." in chat_all(lua), "16 chat says it")
    check(lua.eval("R2F.Macros.SyncRanks()") == 0, "16 after raising, the macro is up to date again (not 'edited')")
    lua.execute("KNOWN[102] = true")
    T.fire("SPELLS_CHANGED")
    T.runTimers()
    check("Rank 3" in T.bodyOf("Charge"), "16 SPELLS_CHANGED works too (Rank 3)")

    # --- Combat: queued, then applied -----------------------------------------------------------------------------
    lua, T = rank_runtime()
    cid = rank_add(lua, "Charge", "#showtooltip Charge\n/cast [harm] Charge")
    lua.execute("R2F.Macros.Ensure(%r)" % cid)
    T.calls = lua.table()
    T.chat = lua.table()
    T.combat = True
    lua.execute("KNOWN[101] = true")
    T.fire("LEARNED_SPELL_IN_TAB")
    T.runTimers()
    check("Rank 1" in T.bodyOf("Charge") and lua_table_to_list(lua.eval("TEST.calls")) == [] and lua.eval("R2F.Macros.QueueSize()") == 1,
          "16 in combat nothing is edited; the update is queued")
    check("when combat ends" in chat_all(lua), "16 combat: the player is told")
    T.combat = False
    lua.execute("R2F.Macros.RunQueue()")
    check("Rank 2" in T.bodyOf("Charge") and lua.eval("R2F.Macros.QueueSize()") == 0, "16 after combat the rank is raised")

    # --- Edited by the player: never touched ---------------------------------------------------------------------------
    lua, T = rank_runtime()
    cid = rank_add(lua, "Charge", "#showtooltip Charge\n/cast [harm] Charge")
    lua.execute("R2F.Macros.Ensure(%r)" % cid)
    lua.execute("TEST.setBody('Charge', '/cast Charge(Rank 1)\\n/say my own')")
    lua.execute("KNOWN[101] = true")
    T.calls = lua.table()
    T.fire("LEARNED_SPELL_IN_TAB")
    T.runTimers()
    check(T.bodyOf("Charge") == "/cast Charge(Rank 1)\n/say my own" and lua_table_to_list(lua.eval("TEST.calls")) == [],
          "16 a macro the player edited is never touched")
    check(lua.eval("R2F.Macros.Classify(%r, R2F.Library.Get(%r))" % (cid, cid)) == "edited", "16 ... and still counts as edited")

    # --- Pinned site macro, update and replace paths ----------------------------------------------------------------------
    lua, T = rank_runtime("KNOWN[101] = true")
    pid = rank_add(lua, "ChargeP", "#showtooltip Charge(Rank 1)\n/cast [harm] Charge(Rank 1)")
    lua.execute("R2F.Macros.Ensure(%r)" % pid)
    check("Charge(Rank 2)" in T.bodyOf("ChargeP") and "Charge(Rank 1)" not in T.bodyOf("ChargeP"),
          "16 the site's pinned Charge(Rank 1) is created at the highest known rank (2)")
    # A site change to the body: the update is written ranked too.
    lua.globals().NEWBODY = "#showtooltip Charge\n/cast [harm] Charge\n/startattack"
    lua.execute("R2F.Library.Apply({ { id = %r, class = 'WARRIOR', section = 'General', group = 'Damage / offensive', name = 'ChargeP', "
                "short = 'ChargeP', body = NEWBODY } }, 2) R2F.Macros.Update(%r)" % (pid, pid))
    check(T.bodyOf("ChargeP") == "#showtooltip Charge(Rank 2)\n/cast [harm] Charge(Rank 2)\n/startattack", "16 a site update is written with ranks: %r" % T.bodyOf("ChargeP"))
    # Replace: another macro with the same name is overwritten with the ranked text.
    lua.execute("TEST.addMacro('Hamstringer', '/say hi', true)")
    hid = rank_add(lua, "Hamstringer", "/cast Charge")
    lua.execute("R2F.Macros.Replace(%r)" % hid)
    check(T.bodyOf("Hamstringer") == "/cast Charge(Rank 2)", "16 Replace writes the ranked body")

    # --- /r2f ranks ----------------------------------------------------------------------------------------------------------
    lua, T = rank_runtime()
    cid = rank_add(lua, "Charge", "#showtooltip Charge\n/cast [harm] Charge")
    cid2 = rank_add(lua, "Charge+Rend", "/cast Charge\n/cast Rend")
    rid = rank_add(lua, "Rend", "/cast Rend")
    lua.execute("R2F.Macros.Ensure(%r) R2F.Macros.Ensure(%r) R2F.Macros.Ensure(%r)" % (cid, cid2, rid))
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("ranks")')
    txt = chat_all(lua)
    check("Charge -> Charge(Rank 1) (in Charge, Charge+Rend)" in txt and "Rend ->" not in txt and "Hamstring" not in txt,
          "16 /r2f ranks lists Charge with the rank used and the macros, and not Rend: %r" % txt)
    lua.execute("KNOWN[101] = true")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("ranks")')
    check("Charge -> Charge(Rank 2)" in chat_all(lua), "16 /r2f ranks follows the learned rank")
    lua.execute("KNOWN[100], KNOWN[101] = nil, nil")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("ranks")')
    check("you know no rank of it yet" in chat_all(lua), "16 /r2f ranks: spell with no known rank says so")
    lua.execute("KNOWN[1240289] = true")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("ranks")')
    check("resolves to a spell you know" in chat_all(lua), "16 /r2f ranks: nothing to report when every plain name is known")
    lua.execute("KNOWN[1240289] = nil KNOWN[100] = true SAVED_GSI = C_Spell.GetSpellInfo C_Spell.GetSpellInfo = nil")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("ranks")')
    check("no C_Spell.GetSpellInfo" in chat_all(lua), "16 /r2f ranks without the API says so")
    lua.execute("C_Spell.GetSpellInfo = SAVED_GSI")
    longid = rank_add(lua, "Longone", "/cast Charge\n/say " + "x" * 235)
    lua.execute("R2F.Macros.Ensure(%r)" % longid)
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("ranks")')
    check("kept without ranks" in chat_all(lua) and "Longone" in chat_all(lua), "16 /r2f ranks names macros kept unranked because of the 255 limit")
    check(T.bodyOf("Longone") == "/cast Charge\n/say " + "x" * 235, "16 ... and that game macro really is the unranked text")

    # --- Spellbook scan: the rank is found even when the spell-id checks all say "unknown" ------------------
    lua, T = rank_runtime()
    lua.execute("KNOWN = {}")   # IsPlayerSpell says no to everything, like a client whose rank ids differ
    check(rewrite(lua, "/cast Charge") == "/cast Charge", "16.1 no id check and no spellbook: left alone")
    lua.execute('''BOOK = { { name = 'Charge', subName = 'Rank 1', spellID = 555 }, { name = 'Rend', subName = 'Rank 1' },
                    { name = 'Hamstring', subName = '' } }
      C_SpellBook = {
        GetNumSpellBookSkillLines = function() return 1 end,
        GetSpellBookSkillLineInfo = function(i) return { itemIndexOffset = 0, numSpellBookItems = #BOOK } end,
        GetSpellBookItemInfo = function(i, bank) return BOOK[i] end,
      }''')
    check(rewrite(lua, "#showtooltip Charge\n/cast Charge") == "#showtooltip Charge(Rank 1)\n/cast Charge(Rank 1)",
          "16.1 modern spellbook lists Charge, Rank 1 -> Rank 1 even though every spell-id check says no")
    lua.execute("BOOK[1].subName = 'Rank 2'")
    check(rewrite(lua, "/cast Charge(Rank 1)") == "/cast Charge(Rank 2)", "16.1 the spellbook's higher rank raises a pinned Rank 1")
    lua.execute("KNOWN[100] = true")   # id-based says Rank 1; the book says 2 -> the higher one wins
    check(rewrite(lua, "/cast Charge") == "/cast Charge(Rank 2)", "16.1 the higher of the two answers wins")
    lua.execute("BOOK[1].subName = ''")
    check(rewrite(lua, "/cast Charge") == "/cast Charge(Rank 1)", "16.1 a book entry without a rank text falls back to the id answer")
    # Classic tab functions instead of C_SpellBook.
    lua.execute('''C_SpellBook = nil KNOWN = {}
      BOOK2 = { { 'Charge', 'Rank 1' }, { 'Rend', 'Rank 1' } }
      GetNumSpellTabs = function() return 1 end
      GetSpellTabInfo = function(t) return 'General', nil, 0, #BOOK2 end
      GetSpellBookItemName = function(i, kind) local e = BOOK2[i] if e then return e[1], e[2] end end''')
    check(rewrite(lua, "/cast Charge") == "/cast Charge(Rank 1)", "16.1 classic spellbook tab functions work too")
    lua.execute("GetNumSpellTabs, GetSpellTabInfo, GetSpellBookItemName = nil, nil, nil")
    # /r2f ranks uses the book as well.
    lua.execute('''BOOK = { { name = 'Charge', subName = 'Rank 1', spellID = 555 } }
      C_SpellBook = {
        GetNumSpellBookSkillLines = function() return 1 end,
        GetSpellBookSkillLineInfo = function(i) return { itemIndexOffset = 0, numSpellBookItems = #BOOK } end,
        GetSpellBookItemInfo = function(i, bank) return BOOK[i] end,
      }''')
    cid = rank_add(lua, "Charge", "/cast Charge")
    lua.execute("R2F.Macros.Ensure(%r)" % cid)
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("ranks")')
    check("Charge -> Charge(Rank 1)" in chat_all(lua), "16.1 /r2f ranks reports the rank found in the spellbook: %r" % chat_all(lua))

    # --- /r2f rankdebug -------------------------------------------------------------------------------------------------
    lua, T = rank_runtime()
    lua.execute("KNOWN[100] = true")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("rankdebug charge")')
    txt = chat_all(lua)
    check("rankdebug Charge: plain name -> spellID 1240289" in txt and "IsPlayerSpell=no" in txt, "16.1 rankdebug shows the plain name's id and the known-checks: %r" % txt)
    check("(Rank 1) -> spellID 100" in txt and "IsPlayerSpell=yes" in txt and "(Rank 2) -> spellID 101" in txt, "16.1 rankdebug lists the ranks with their ids")
    check("spellbook: not listed under that name" in txt and "the addon would use: Charge(Rank 1)" in txt, "16.1 rankdebug: spellbook line and the rank the addon would use")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("rankdebug")')
    check("usage: /r2f debug rank Charge" in chat_all(lua), "16.1 rankdebug without a spell name prints the usage")


GAMEPLAY_API_LUA = """
  -- A fake vendor, bags, duel and error frame (ADDON_PLAN 17).
  REPAIRS, SOLD, DUELS_CANCELED, POPUPS, MONEY = {}, {}, 0, {}, 100000
  REPAIR_COST, CAN_REPAIR = 1250, true
  CanMerchantRepair = function() return CAN_REPAIR end
  GetRepairAllCost = function() return REPAIR_COST, REPAIR_COST > 0 end
  GetMoney = function() return MONEY end
  RepairAllItems = function(guild) table.insert(REPAIRS, guild == nil and 'own gold' or 'guild') end
  BAGS = {
    [0] = {
      { quality = 0, hasNoValue = false, stackCount = 3, hyperlink = 'gray1' },    -- sells, 25c x 3
      { quality = 1, hasNoValue = false, stackCount = 1, hyperlink = 'white' },    -- never
      { quality = 0, hasNoValue = true,  stackCount = 1, hyperlink = 'novalue' },  -- never (no vendor value)
      { quality = 0, hasNoValue = false, stackCount = 1, hyperlink = 'zero' },     -- price 0: skipped
    },
    [1] = { { quality = 0, hasNoValue = false, stackCount = 1, hyperlink = 'gray2' } },   -- sells, 100c
  }
  PRICES = { gray1 = 25, gray2 = 100, zero = 0, white = 50 }
  C_Container = {
    GetContainerNumSlots = function(bag) return BAGS[bag] and #BAGS[bag] or 0 end,
    GetContainerItemInfo = function(bag, slot) local it = BAGS[bag] and BAGS[bag][slot] if it and not it.sold then return it end end,
    UseContainerItem = function(bag, slot) table.insert(SOLD, bag .. ':' .. slot) BAGS[bag][slot].sold = true end,
  }
  GetItemInfo = function(link)
    if PRICES[link] ~= nil then return link, link, 0, 0, 0, '', '', 1, '', 0, PRICES[link] end
  end
  CancelDuel = function() DUELS_CANCELED = DUELS_CANCELED + 1 end
  StaticPopup_Hide = function(which) table.insert(POPUPS, which) end
  ERR_OUT_OF_RAGE = 'Not enough rage'
  SPELL_FAILED_NOT_READY = 'Ability is not ready yet'
  SHOWN = {}
  UIErrorsFrame = CreateFrame('Frame', 'UIErrorsFrame', UIParent)
  UIErrorsFrame.AddMessage = function(self, msg) table.insert(SHOWN, msg) end
  ERRORS_ADDMESSAGE = UIErrorsFrame.AddMessage
  -- Blizzard's own frame shows UI_ERROR_MESSAGE itself.
  UIErrorsFrame:RegisterEvent('UI_ERROR_MESSAGE')
  UIErrorsFrame:SetScript('OnEvent', function(self, event, errorType, msg) self:AddMessage(msg) end)
  TEST.cvars.xpBarText = '0'
"""


def gameplay_runtime(preset=None, token=None, api=True):
    lua = new_runtime()
    lua.execute("TEST.reset()")
    if token:
        lua.execute("TEST.classToken = %r" % token)
    lua.execute("TEST.cvars.xpBarText = nil")
    if api:
        lua.execute(GAMEPLAY_API_LUA)
    else:
        lua.execute("UIErrorsFrame = nil")
    if preset:
        lua.execute("R2FDB = %s" % preset)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    return lua, T


def test_gameplay():
    """ADDON_PLAN 17 step 1: Gameplay tab with repair, sell grey, block duels, error filter, XP bar text."""
    lua, T = gameplay_runtime()
    G = "R2FDB.gameplay."
    # --- Defaults and the tab ---------------------------------------------------------------------
    check(all(lua.eval(G + k) is False for k in ("repair", "sellgray", "duels", "errorfilter", "xpbar")),
          "17 every gameplay feature ships OFF")
    lua.execute('SlashCmdList.R2F("gameplay")')
    check(lua.eval("R2F.MainWindow.CurrentTab()") == "gameplay" and lua.eval("R2F.MainWindow.Title()") == "Road to Forever: Tweaks",
          "17 /r2f gameplay opens the Gameplay tab")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel", "GB")
    labels = {lua.eval("GB[%d].r2fLabel.__text" % i): i for i in range(1, lua.eval("#GB") + 1)}
    wanted = [lua.eval("R2F.L.%s" % k) for k in ("GP_REPAIR", "GP_SELLGRAY", "GP_DUELS", "GP_ERRORFILTER", "GP_XPBAR")]
    check(all(w in labels for w in wanted), "17 the tab has one box per feature")
    pages = [lua.eval("R2F.GameplayTab.PAGES[%d].key" % i) for i in range(1, 9)]
    check(pages == ["quests", "vendors", "screen", "bags", "alerts", "arrow", "icons", "bars"], "17.1 the tab has eight pages: %s" % pages)
    # Phase 3: alert text size/outline, reset page, changed dot.
    lua.execute("R2F.GameplayTab.ShowPage('alerts') R2F.GameplayTab.ResetPage()")
    check(lua.eval("R2F.GameplayTab.PAGES[5].key") == "alerts" and lua.eval("R2FDB.fct.textScale") == 1 and lua.eval("R2FDB.fct.outline") == "none",
          "alerts page defaults: size 100%, no outline")
    lua.execute("R2F.Gameplay.SetOn('reactalert', true) R2FDB.fct.textScale = 1.5 R2FDB.fct.outline = 'thick' R2F.Gameplay.ApplyAlertStyle() R2F.GameplayTab.Refresh()")
    check(lua.eval("R2FDB.fct.textScale") == 1.5, "alert text scale stored")
    lua.execute("R2F.GameplayTab.ResetPage()")
    check(lua.eval("R2F.Gameplay.IsOn('reactalert')") is False and lua.eval("R2FDB.fct.textScale") == 1 and lua.eval("R2FDB.fct.outline") == "none",
          "Reset page turns the page's boxes off and restores the alert text style")
    lua.execute("R2FDB.fct.textScale = 9 R2FDB.fct.outline = 'bogus' R2F.Library.Init()")
    check(lua.eval("R2FDB.fct.textScale") == 1 and lua.eval("R2FDB.fct.outline") == "thick", "bad alert style values are reset")
    find_frames(lua, "f.__kind == 'FontString' and type(f.__text) == 'string' and f.__text:find('Priest') and f.__text:find('/')", "PRG")
    check(lua.eval("#PRG") >= 1, "group buffs are grouped under a Priest fold-out header")
    lua.execute("R2F.GameplayTab.ShowPage('icons') R2F.RemindersTab.OpenGroups().PRIEST = true R2F.GameplayTab.Refresh()")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == 'Divine Spirit' and f.__shown", "PRS")
    check(lua.eval("#PRS") == 1, "opening the Priest group shows Divine Spirit")
    lua.execute("R2F.RemindersTab.OpenGroups().PRIEST = nil R2F.GameplayTab.Refresh()")
    lua.execute("R2F.GameplayTab.ShowPage('quests')")
    check(all(font_text(lua, "^$") is None or True for _ in [0]) and
          lua.eval("(function() local n = 0 for _, f in ipairs(TEST.allFrames) do if f.__kind == 'Button' and f.__text and (f.__text == R2F.L.GP_PAGE_QUESTS or f.__text == R2F.L.GP_PAGE_VENDORS or f.__text == R2F.L.GP_PAGE_SCREEN or f.__text == R2F.L.GP_PAGE_ALERTS) then n = n + 1 end end return n end)()") == 4,
          "17.1 four page buttons along the top")
    check(lua.eval("R2F.GameplayTab.CurrentPage()") == "quests", "17.1 the first page is Quests")
    boxvis = lambda lbl: lua.eval("(function() for _, f in ipairs(TEST.allFrames) do if f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.%s then return f:IsVisible() end end end)()" % lbl)
    check(boxvis("GP_QACCEPT") is True and boxvis("GP_REPAIR") is False, "17.1 only the page you are on shows its boxes")
    pagebtn = lambda lbl: "(function() for _, f in ipairs(TEST.allFrames) do if f.__kind == 'Button' and f.__text == R2F.L.%s then return f end end end)()" % lbl
    check(lua.eval("%s:IsEnabled()" % pagebtn("GP_PAGE_QUESTS")) is True and lua.eval("%s.mark.__shown" % pagebtn("GP_PAGE_QUESTS")) is True
          and lua.eval("%s.mark.__shown" % pagebtn("GP_PAGE_VENDORS")) is False,
          "17.1 the active page button stays enabled (not greyed) and carries the gold bar; the others don't")
    lua.execute("R2F.GameplayTab.ShowPage('vendors')")
    check(lua.eval("%s:IsEnabled()" % pagebtn("GP_PAGE_VENDORS")) is True and lua.eval("%s.mark.__shown" % pagebtn("GP_PAGE_VENDORS")) is True
          and lua.eval("%s.mark.__shown" % pagebtn("GP_PAGE_QUESTS")) is False, "17.1 the gold bar follows the page")
    lua.execute("UnitName = function() return 'Thorin' end UnitFullName = function() return 'Thorin', 'Realm' end GetRealmName = function() return 'Realm' end TEST.chat = {} R2F.Gameplay.PrintWho()")
    check(lua.eval("#TEST.chat") >= 1, "17.1 /r2f who prints the ways the client names the character, without error")
    check(boxvis("GP_QACCEPT") is False and boxvis("GP_REPAIR") is True and lua.eval("R2FDB.settings.gameplayPage") == "vendors", "17.1 switching pages swaps the boxes and is remembered")
    lua.execute("R2F.GameplayTab.ShowPage('icons')")
    check(lua.eval("R2FStanceScale ~= nil and R2FStanceScale:IsVisible()") is True, "17 the Warrior's stance options are on the Class icons page")
    lua.execute("R2F.GameplayTab.ShowPage('quests')")
    check(lua.eval("R2FStanceScale:IsVisible()") is False, "17.1 ... and not on the other pages")
    lua.execute("R2F.GameplayTab.ShowPage('nope')")
    check(lua.eval("R2F.GameplayTab.CurrentPage()") == "quests", "17.1 an unknown page falls back to Quests")
    box = lambda key: "GB[%d]" % labels[lua.eval("R2F.L.%s" % key)]
    # --- Repair ---------------------------------------------------------------------------------------
    T.fire("MERCHANT_SHOW")
    check(lua.eval("#REPAIRS") == 0, "17 repair off: nothing happens at a vendor")
    lua.execute(box("GP_REPAIR") + ":Click()")
    check(lua.eval(G + "repair") is True, "17 ticking the box turns the feature on")
    T.chat = lua.table()
    T.fire("MERCHANT_SHOW")
    check(lua.eval("#REPAIRS") == 1 and lua.eval("REPAIRS[1]") == "own gold", "17 repair on: repairs with your own gold (no guild bank)")
    check("repaired your gear for 12s 50c." in chat_all(lua), "17 repair says the cost: %r" % chat_all(lua))
    lua.execute("MONEY = 100 REPAIRS = {}")
    T.chat = lua.table()
    T.fire("MERCHANT_SHOW")
    check(lua.eval("#REPAIRS") == 0 and "more than you have" in chat_all(lua), "17 can't afford it: nothing repaired, says so")
    lua.execute("MONEY = 100000 REPAIR_COST = 0")
    T.fire("MERCHANT_SHOW")
    check(lua.eval("#REPAIRS") == 0, "17 nothing to repair: nothing done")
    lua.execute("REPAIR_COST = 1250 CAN_REPAIR = false")
    T.fire("MERCHANT_SHOW")
    check(lua.eval("#REPAIRS") == 0, "17 a vendor that can't repair: nothing done")
    lua.execute("CAN_REPAIR = true")
    # --- Sell grey items --------------------------------------------------------------------------------------
    lua.execute("SOLD = {}")
    T.fire("MERCHANT_SHOW")
    check(lua.eval("#SOLD") == 0, "17 sell grey off: nothing is sold")
    lua.execute(box("GP_SELLGRAY") + ":Click()")
    T.chat = lua.table()
    lua.execute("REPAIRS = {}")
    T.fire("MERCHANT_SHOW")
    T.runTimers()   # it sells a few at a time and checks again
    sold = lua_table_to_list(lua.eval("SOLD"))
    check(sold == ["0:1", "1:1"], "17 sell grey: only grey items with a vendor price are sold (not white, not 'no value', not 0c): %s" % sold)
    check("sold 2 grey items for 1g" not in chat_all(lua) and "sold 2 grey items for 1s 75c." in chat_all(lua), "17 sell grey says count and total (3 x 25c + 100c = 1s 75c): %r" % chat_all(lua))
    check(lua.eval("#REPAIRS") == 1, "17 both features run on the same vendor visit")
    lua.execute("SOLD = {}")
    T.fire("MERCHANT_CLOSED")
    lua.execute("BAGS[0][1].quality = 0 BAGS[0][1].sold = nil BAGS[1][1].sold = nil")
    T.fire("MERCHANT_SHOW")
    T.runTimers()
    check(lua.eval("#SOLD") == 2, "17 a second vendor visit sells again (state comes from the events)")
    # --- Block duels -------------------------------------------------------------------------------------------
    T.fire("DUEL_REQUESTED", "Bob")
    check(lua.eval("DUELS_CANCELED") == 0, "17 block duels off: the request is left alone")
    lua.execute(box("GP_DUELS") + ":Click()")
    T.chat = lua.table()
    T.fire("DUEL_REQUESTED", "Bob")
    check(lua.eval("DUELS_CANCELED") == 1 and lua.eval("POPUPS[1]") == "DUEL_REQUESTED" and "declined a duel from Bob." in chat_all(lua),
          "17 block duels on: declined, popup closed, says who")
    # --- Error filter ---------------------------------------------------------------------------------------------
    T.fire("UI_ERROR_MESSAGE", 51, "Not enough rage")
    check(lua_table_to_list(lua.eval("SHOWN")) == ["Not enough rage"], "17 error filter off: the message shows")
    lua.execute("SHOWN = {}" + " " + box("GP_ERRORFILTER") + ":Click()")
    for m in ("Not enough rage", "Ability is not ready yet", "You are being attacked"):
        T.fire("UI_ERROR_MESSAGE", 51, m)
    check(lua_table_to_list(lua.eval("SHOWN")) == ["You are being attacked"], "17 error filter on: the spam is hidden, other messages pass once: %s" % lua_table_to_list(lua.eval("SHOWN")))
    check(lua.eval("rawequal(UIErrorsFrame.AddMessage, ERRORS_ADDMESSAGE)") is True, "17 error filter never replaces Blizzard's AddMessage")
    check(lua.eval("UIErrorsFrame.__events.UI_ERROR_MESSAGE") is None, "17 error filter on: Blizzard's frame has handed the event to ours")
    lua.execute("SHOWN = {}" + " " + box("GP_ERRORFILTER") + ":Click()")
    T.fire("UI_ERROR_MESSAGE", 51, "Not enough rage")
    check(lua_table_to_list(lua.eval("SHOWN")) == ["Not enough rage"], "17 error filter off again: Blizzard's frame shows it again, once")
    # --- XP bar text ---------------------------------------------------------------------------------------------------
    lua2, T2 = gameplay_runtime()
    lua2.execute("TEST.cvars.xpBarText = '0'")
    lua2.execute("R2F.Gameplay.SetOn('xpbar', true)")
    check(lua2.eval("TEST.cvars.xpBarText") == "1" and lua2.eval("R2FDB.gameplayXpWas") == "0", "17 XP bar text on: the game's setting is set, the old value remembered")
    lua2.execute("R2F.Gameplay.SetOn('xpbar', false)")
    check(lua2.eval("TEST.cvars.xpBarText") == "0" and lua2.eval("R2FDB.gameplayXpWas") is None, "17 off: the player's old value is put back")
    lua2.execute("TEST.cvars.xpBarText = '1' R2F.Gameplay.SetOn('xpbar', true) R2F.Gameplay.SetOn('xpbar', false)")
    check(lua2.eval("TEST.cvars.xpBarText") == "1", "17 a player who already had it on keeps it on after unticking")
    T2.combat = True
    check(lua2.eval("R2F.Gameplay.SetOn('xpbar', true)") is False and lua2.eval("R2FDB.gameplay.xpbar") is False,
          "17 XP bar text can't be changed in combat (a game setting)")
    T2.combat = False

    # --- Persistence across login: on-state is applied again -----------------------------------------------------------------
    lua3, T3 = gameplay_runtime(preset="{ gameplay = { errorfilter = true, xpbar = true, repair = true }, gameplayXpWas = '0' }")
    T3.fire("UI_ERROR_MESSAGE", 51, "Not enough rage")
    check(lua_table_to_list(lua3.eval("SHOWN")) == [], "17 relog: the error filter is active again without opening the tab")
    check(lua3.eval("TEST.cvars.xpBarText") == "1", "17 relog: the XP bar setting is applied again")
    check(lua3.eval("R2FDB.gameplay.sellgray") is False, "17 relog: missing flags are filled in as off")
    lua4, T4 = gameplay_runtime(preset="{ gameplay = { repair = 'yes', duels = 5 } }")
    check(lua4.eval("R2FDB.gameplay.repair") is False and lua4.eval("R2FDB.gameplay.duels") is False, "17 invalid saved values are repaired to off")

    # --- Features the client can't do ----------------------------------------------------------------------------------------------
    lua5, T5 = gameplay_runtime(api=False)
    lua5.execute("R2F.MainWindow.Show('gameplay')")
    check(lua5.eval("R2F.Gameplay.SetOn('errorfilter', true)") is False and lua5.eval("R2FDB.gameplay.errorfilter") is False,
          "17 no UIErrorsFrame: the error filter can't be switched on")
    check(lua5.eval("R2F.Gameplay.SetOn('xpbar', true)") is False, "17 no xpBarText setting: XP bar text can't be switched on")
    find_frames(lua5, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.GP_XPBAR", "XB")
    check(lua5.eval("XB[1]:IsEnabled()") is False, "17 ... and its box is greyed out")

    # --- One feature failing never stops the others ------------------------------------------------------------------------------------
    lua6, T6 = gameplay_runtime()
    lua6.execute("R2F.Gameplay.SetOn('repair', true) R2F.Gameplay.SetOn('sellgray', true) CanMerchantRepair = function() error('boom') end")
    T6.chat = lua6.table()
    T6.fire("MERCHANT_SHOW")
    check(lua6.eval("#SOLD") == 2 and "gameplay feature repair hit an error" in chat_all(lua6), "17 a failing feature is reported and the others still run")
    T6.chat = lua6.table()
    T6.fire("MERCHANT_SHOW")
    check("hit an error" not in chat_all(lua6), "17 the error is reported once per session")

    # --- Combat: the tab's boxes stay usable ------------------------------------------------------------------------------------------------
    lua7, T7 = gameplay_runtime()
    lua7.execute("R2F.MainWindow.Show('gameplay')")
    T7.combat = True
    T7.fire("PLAYER_REGEN_DISABLED")
    find_frames(lua7, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.GP_REPAIR", "RB")
    check(lua7.eval("RB[1]:IsEnabled()") is True, "17 the Automatic boxes stay enabled in combat")
    T7.combat = False

    # --- Money text ------------------------------------------------------------------------------------------------------------------------------
    m = lambda c: lua.eval("R2F.Gameplay.Money(%d)" % c)
    check([m(0), m(5), m(100), m(1250), m(10000), m(123456)] == ["0c", "5c", "1s", "12s 50c", "1g", "12g 34s 56c"], "17 money text")

    # --- Other classes: no reminder column content for a Priest -------------------------------------------------------------------------------------
    lua8, T8 = gameplay_runtime(token="PRIEST")
    lua8.execute("R2F.MainWindow.Show('gameplay')")
    check(font_text(lua8, "^No reminders for your class") is None and lua8.eval("R2FStanceScale == nil and R2FAmmoScale == nil"),
          "17 a Priest has no stance/ammo controls, only the group-buff reminder")
    # --- Missing group buffs (Buffs.lua) ----------------------------------------------------------------------------------------------------
    lua8.execute("""
      GRP = { party1 = 'DRUID', party2 = 'PALADIN', party3 = 'MAGE' }
      AUR = {}
      IsInGroup = function() return GRP ~= false end
      IsInRaid = function() return false end
      UnitExists = function(u) return u == 'player' or (GRP and GRP[u] ~= nil) end
      local oldClass = UnitClass
      UnitClass = function(u) if u == 'player' then return 'Priest', 'PRIEST' end return GRP[u], GRP[u] end
      UnitIsDeadOrGhost = function() return false end
      C_UnitAuras = { GetUnitAuras = function() local t = {} for _, n in ipairs(AUR) do t[#t+1] = { name = n } end return t end }
      R2F.Buffs.Update()
    """)
    names = lambda: [lua8.eval("R2F.Buffs.Missing()[%d].key" % i) for i in range(1, lua8.eval("#R2F.Buffs.Missing()") + 1)]
    check(names() == ["fortitude", "motw", "intellect", "blessing"],
          "17.5 a Priest, Druid, Paladin and Mage group: Fortitude, Mark of the Wild, Intellect, a Blessing (Thorns is off by default) are all missing: %r" % names())
    check(lua8.eval("R2FGroupBuffFrame:IsShown()") is True, "17.5 the reminder shows")
    lua8.execute("AUR = { 'Power Word: Fortitude', 'Gift of the Wild', 'Greater Blessing of Kings' } R2F.Buffs.Update()")
    check(names() == ["intellect"], "17.5 Fortitude, Gift of the Wild (counts as Mark) and a Greater Blessing are recognised: %r" % names())
    lua8.execute("R2FDB.buffs.thorns = false R2F.Buffs.Update()")
    check(names() == ["intellect"], "17.5 a buff you switched off is not asked for")
    lua8.execute("AUR = { 'Power Word: Fortitude', 'Gift of the Wild', 'Blessing of Might', 'Arcane Intellect' } R2F.Buffs.Update()")
    check(names() == [] and lua8.eval("R2FGroupBuffFrame:IsShown()") is False, "17.5 nothing missing: the reminder is gone")
    lua8.execute("GRP = { party1 = 'ROGUE' } AUR = {} R2FDB.buffs.thorns = true R2F.Buffs.Update()")
    check(names() == ["fortitude"], "17.5 only buffs of classes in the group count (you are the Priest: Fortitude): %r" % names())
    lua8.execute("GRP = false R2F.Buffs.Update()")
    check(names() == [] and lua8.eval("R2FGroupBuffFrame:IsShown()") is False, "17.5 alone and locked: no reminder")
    lua8.execute("R2FDB.buffs.lock = false R2F.Buffs.Update()")
    check(lua8.eval("R2FGroupBuffFrame:IsShown()") is True, "17.5 alone and unlocked: a sample icon to drag into place")
    lua8.execute("GRP = { party1 = 'DRUID' } AUR = { 'Power Word: Fortitude', 'Mark of the Wild', 'Thorns' } R2F.Buffs.Update()")
    check(lua8.eval("R2FGroupBuffFrame:IsShown()") is True and lua8.eval("R2FGroupBuffFrame.icon.__desat") is True,
          "17.5 in a group with nothing missing, unlocked: still shown (dimmed) so it can be moved")
    lua8.execute("R2FDB.buffs.lock = true GRP = { party1 = 'DRUID' } issecretvalue = function(v) return v == 'SECRET' end AUR = { 'SECRET' } R2F.Buffs.Update()")
    check(names() == [], "17.5 hidden (secret) auras: it says nothing instead of guessing")



GAMEPLAY2_LUA = """
  GetRealmName = function() return 'Realm' end
  GetNormalizedRealmName = function() return 'RealmNorm' end
  UnitName = function(unit) return 'Thorin' end
  UnitFactionGroup = function() return 'Alliance' end
  UnitLevel = function() return TEST.level or 18 end
  RAID_CLASS_COLORS = { WARRIOR = { r = 0.78, g = 0.61, b = 0.43 }, HUNTER = { r = 0.67, g = 0.83, b = 0.45 } }
  SendMailFrame = CreateFrame('Frame', 'SendMailFrame', UIParent)
  SendMailNameEditBox = CreateFrame('EditBox', 'SendMailNameEditBox', SendMailFrame)
  MainMenuBarBackpackButton = CreateFrame('Button', 'MainMenuBarBackpackButton', UIParent)
  FREE = { [0] = 4, [1] = 6, [2] = 2, [3] = 0, [4] = 9 }
  BAGTYPE = { [0] = 0, [1] = 0, [2] = 0, [3] = 0, [4] = 1 }   -- bag 4 is a quiver: not counted
  C_Container = C_Container or {}
  C_Container.GetContainerNumFreeSlots = function(bag) return FREE[bag] or 0, BAGTYPE[bag] or 0 end
  LOOTED, LOOT_ITEMS = {}, 3
  GetNumLootItems = function() return LOOT_ITEMS end
  LootSlot = function(i) table.insert(LOOTED, i) end
  AUTOLOOT = true
  GetCVarBool = function(name) return name == 'autoLootDefault' and AUTOLOOT end
  TOGGLE_HELD = false
  IsModifiedClick = function(which) return which == 'AUTOLOOTTOGGLE' and TOGGLE_HELD end
  MENU = nil
  R2F.UI.ContextMenu = function(items) MENU = items end
"""


def gameplay2_runtime(preset=None, backpack=True):
    lua = new_runtime()
    lua.execute("TEST.reset()")
    lua.execute(GAMEPLAY2_LUA)
    if not backpack:
        lua.execute("MainMenuBarBackpackButton = nil")
    if preset:
        lua.execute("R2FDB = %s" % preset)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    return lua, T


def test_gameplay_extras():
    """ADDON_PLAN 17 step 2: own characters in mail, free bag slots, fast loot."""
    # --- Characters are remembered ---------------------------------------------------------------------
    lua, T = gameplay2_runtime(preset="{ chars = { Realm = { Alice = { class = 'HUNTER', level = 30, faction = 'Alliance' }, "
                               "Bob = { class = 'MAGE', level = 5, faction = 'Horde' } }, Other = { Carl = { class = 'WARRIOR', level = 9, faction = 'Alliance' } } } }")
    check(lua.eval("R2FDB.chars.Realm.Thorin.class") == "WARRIOR" and lua.eval("R2FDB.chars.Realm.Thorin.level") == 18
          and lua.eval("R2FDB.chars.Realm.Thorin.faction") == "Alliance", "17.2 this character is remembered at login")
    others = [lua.eval("R2F.Gameplay.OtherCharacters()[%d].name" % i) for i in range(1, lua.eval("#R2F.Gameplay.OtherCharacters()") + 1)]
    check(others == ["Alice"], "17.2 other characters: same realm and faction only, not yourself: %s" % others)
    lua.execute("TEST.level = 19")
    T.fire("PLAYER_LEVEL_UP")
    check(lua.eval("R2FDB.chars.Realm.Thorin.level") == 19, "17.2 the level is updated on level-up")
    # --- Mail ----------------------------------------------------------------------------------------------
    T.fire("MAIL_SHOW")
    check(lua.eval("R2FMailAltsButton == nil"), "17.2 mail off: no button")
    lua.execute("R2F.Gameplay.SetOn('mailalts', true)")
    T.fire("MAIL_SHOW")
    check(lua.eval("R2FMailAltsButton ~= nil and R2FMailAltsButton:IsShown()"), "17.2 mail on: a button after the recipient field")
    lua.execute("R2FMailAltsButton:Click()")
    items = lua.eval("MENU")
    check(lua.eval("#MENU") == 4 and lua.eval("MENU[1].kind") == "title", "17.2 the menu: a title, one character, a divider and the foot note")
    txt = lua.eval("MENU[2].text")
    check("Alice" in txt and "30" in txt and "|cffabd473" in txt, "17.2 the entry shows name, level and the class colour: %r" % txt)
    lua.execute("MENU[2].func()")
    check(lua.eval("SendMailNameEditBox:GetText()") == "Alice-RealmNorm", "17.2 clicking a character fills in the FULL name, Name-Realm (a bare name does not arrive on this client)")
    lua.execute("UnitName = function() return 'Zed' end GetUnitName = function() return 'Zed Stormborn' end R2F.Gameplay.RememberCharacter() UnitName = function() return 'Me' end")
    check(lua.eval("R2FDB.chars[GetRealmName()]['Zed Stormborn'].full") == "Zed Stormborn", "17.2 the character's full in-game name is remembered for mail (and is the key)")
    # Two characters sharing a first name (Venom Oathbreaker / Venom Madstorm) don't overwrite each other.
    lua.execute("UnitName = function() return 'Zed' end GetUnitName = function() return 'Zed Other' end R2F.Gameplay.RememberCharacter()")
    check(lua.eval("R2FDB.chars[GetRealmName()]['Zed Stormborn'] ~= nil and R2FDB.chars[GetRealmName()]['Zed Other'] ~= nil"),
          "17.2 same first name, different full names: both kept")
    lua.execute("GetUnitName = function() return 'Zed Stormborn' end")
    check(any(lua.eval("R2F.Gameplay.OtherCharacters()[%d].full" % i) == "Zed Other" for i in range(1, lua.eval("#R2F.Gameplay.OtherCharacters()") + 1)),
          "17.2 the same-first-name twin shows in the mail list")
    lua.execute("R2FDB.chars[GetRealmName()]['Zed Other'] = nil UnitName = function() return 'Me' end GetUnitName = function() return 'Me Full' end")
    check(any(lua.eval("R2F.Gameplay.OtherCharacters()[%d].full" % i) == "Zed Stormborn" for i in range(1, lua.eval("#R2F.Gameplay.OtherCharacters()") + 1)),
          "17.2 the mail list uses the full in-game name (Zed Stormborn), not Name-Realm")
    lua.execute("GetUnitName = nil UnitName = function() return 'Me' end")
    lua.execute("GetNormalizedRealmName = nil R2F.Gameplay.OtherCharacters()")
    check(lua.eval("R2F.Gameplay.OtherCharacters()[1].full") == "Alice-Realm", "17.2 without a normalised realm name the realm name is used")
    lua.execute("GetRealmName = function() return 'Mad Fury' end")
    check(lua.eval("R2F.Gameplay.OtherCharacters()") is not None, "17.2 realm names with spaces do not break the list")
    lua.execute("R2FDB.chars.Realm.Alice = nil R2FMailAltsButton:Click()")
    check(lua.eval("#MENU") == 4 and "No other characters" in lua.eval("MENU[2].text"), "17.2 no other characters: the menu says so")
    lua.execute("R2F.Gameplay.SetOn('mailalts', false)")
    check(lua.eval("R2FMailAltsButton:IsShown()") is False, "17.2 mail off again: the button goes")
    # --- Bag slots --------------------------------------------------------------------------------------------------
    lua.execute("R2F.Gameplay.SetOn('bagslots', true)")
    check(font_text(lua, "^12$") == "12", "17.2 free slots: general bags only (4 + 6 + 2 + 0 = 12, the quiver isn't counted)")
    lua.execute("FREE[0], FREE[1], FREE[2] = 1, 1, 1")
    T.fire("BAG_UPDATE_DELAYED")
    check(font_text(lua, "^3$") == "3", "17.2 BAG_UPDATE_DELAYED refreshes the number")
    lua.execute("""for _, f in ipairs(TEST.allFrames) do if f.__kind == 'FontString' and f.__text == '3' then BS = f end end""")
    check(lua.eval("BS.__color[1]") == 1 and lua.eval("BS.__color[2]") < 0.5, "17.2 3 or fewer free slots: red")
    lua.execute("R2F.Gameplay.SetOn('bagslots', false)")
    check(lua.eval("BS.__shown") is False, "17.2 off: the number is hidden")
    lua3, T3 = gameplay2_runtime(backpack=False)
    check(lua3.eval("R2F.Gameplay.SetOn('bagslots', true)") is False and lua3.eval("R2FDB.gameplay.bagslots") is False,
          "17.2 no backpack button on this client: can't be switched on")
    # --- Sort button -----------------------------------------------------------------------------------------------
    lua.execute("SORTED = 0 C_Container.SortBags = function() SORTED = SORTED + 1 end ContainerFrame1 = CreateFrame('Frame', nil, UIParent) ContainerFrame1.GetID = function() return 0 end ContainerFrame2 = CreateFrame('Frame', nil, UIParent) ContainerFrame2.GetID = function() return 1 end")
    btn = "(function() for _, f in ipairs(TEST.allFrames) do if f.__kind == 'Button' and f.__text == R2F.L.GP_SORT_BUTTON and f.__parent == %s then return f end end end)()"
    check(lua.eval("R2F.Gameplay.SetOn('bagsort', true)") is True, "17.2 sort button switches on")
    check(lua.eval(btn % "ContainerFrame1" + ":IsShown()") is True and lua.eval(btn % "ContainerFrame2" + ":IsShown()") is False,
          "17.2 the Sort button is on the backpack window only")
    lua.execute((btn % "ContainerFrame1") + ":Click()")
    check(lua.eval("SORTED") == 1, "17.2 clicking Sort runs the game's bag clean-up")
    T.combat = True
    lua.execute((btn % "ContainerFrame1") + ":Click()")
    check(lua.eval("SORTED") == 1, "17.2 no sorting in combat")
    T.combat = False
    lua.execute("R2F.Gameplay.SetOn('bagsort', false)")
    check(lua.eval(btn % "ContainerFrame1" + ":IsShown()") is False, "17.2 sort off: the button is gone")
    # --- Fast loot ----------------------------------------------------------------------------------------------------------
    lua.execute("LOOTED = {}")
    T.fire("LOOT_READY", True)
    check(lua.eval("#LOOTED") == 0, "17.2 fast loot off: nothing is looted for you")
    lua.execute("R2F.Gameplay.SetOn('fastloot', true)")
    T.fire("LOOT_READY", True)
    check(lua_table_to_list(lua.eval("LOOTED")) == [3, 2, 1], "17.2 fast loot on: every slot at once, last to first: %s" % lua_table_to_list(lua.eval("LOOTED")))
    lua.execute("LOOTED = {} AUTOLOOT = false")
    T.fire("LOOT_READY")
    check(lua.eval("#LOOTED") == 0, "17.2 the game's auto-loot is off: nothing happens")
    lua.execute("TOGGLE_HELD = true")
    T.fire("LOOT_READY")
    check(lua.eval("#LOOTED") == 3, "17.2 the auto-loot key flips it (held with auto-loot off: loots)")
    lua.execute("LOOTED = {} AUTOLOOT = true")
    T.fire("LOOT_READY")
    check(lua.eval("#LOOTED") == 0, "17.2 the auto-loot key held with auto-loot on: does not loot")
    lua.execute("TOGGLE_HELD = false LOOTED = {}")
    T.fire("LOOT_READY", False)
    check(lua.eval("#LOOTED") == 0, "17.2 LOOT_READY's own auto-loot flag false: nothing")
    # --- Tab ---------------------------------------------------------------------------------------------------------------------
    lua.execute("R2F.MainWindow.Show('gameplay')")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel", "GB2")
    labels = [lua.eval("GB2[%d].r2fLabel.__text" % i) for i in range(1, lua.eval("#GB2") + 1)]
    for k in ("GP_MAIL", "GP_BAGSLOTS", "GP_FASTLOOT"):
        check(lua.eval("R2F.L.%s" % k) in labels, "17.2 the Gameplay tab has the %s box" % k)
    check(all(lua.eval("R2FDB.gameplay.%s" % k) is not None for k in ("mailalts", "bagslots", "fastloot")), "17.2 the new switches have saved flags")


GAMEPLAY3_LUA = """
  ACCEPTED, COMPLETED, REWARDS, SEL_AVAIL, SEL_ACTIVE, GREET_AVAIL, GREET_ACTIVE = 0, 0, {}, {}, {}, {}, {}
  AUTOACC, COMPLETABLE, CHOICES = false, true, 0
  AVAIL, ACTIVE = {}, {}
  AcceptQuest = function() ACCEPTED = ACCEPTED + 1 end
  QuestGetAutoAccept = function() return AUTOACC end
  CompleteQuest = function() COMPLETED = COMPLETED + 1 end
  IsQuestCompletable = function() return COMPLETABLE end
  GetNumQuestChoices = function() return CHOICES end
  GetQuestReward = function(i) table.insert(REWARDS, i) end
  C_GossipInfo = {
    GetAvailableQuests = function() return AVAIL end,
    GetActiveQuests = function() return ACTIVE end,
    SelectAvailableQuest = function(id) table.insert(SEL_AVAIL, id) end,
    SelectActiveQuest = function(id) table.insert(SEL_ACTIVE, id) end,
  }
  GetNumAvailableQuests = function() return GREET_N or 0 end
  SelectAvailableQuest = function(i) table.insert(GREET_AVAIL, i) end
  GetNumActiveQuests = function() return 2 end
  GetActiveTitle = function(i) return 'T' .. i, i == 2 end
  SelectActiveQuest = function(i) table.insert(GREET_ACTIVE, i) end
  GetQuestItemLink = function(kind, i) return ({ 'a', 'b', 'c' })[i] end
  PRICES3 = { a = 100, b = 500, c = 0 }
  GetItemInfo = function(link) if PRICES3[link] ~= nil then return link, link, 1, 0, 0, '', '', 1, '', 0, PRICES3[link] end end
  for i = 1, 3 do CreateFrame('Button', 'QuestInfoRewardsFrameQuestInfoItem' .. i, UIParent) end
"""


def gameplay3_runtime(rewards_api=True):
    lua = new_runtime()
    lua.execute("TEST.reset()")
    lua.execute(GAMEPLAY3_LUA)
    if not rewards_api:
        lua.execute("GetNumQuestChoices = nil")
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    return lua, T


def test_gameplay_quests():
    """ADDON_PLAN 17 step 3: accept quests, hand in quests (never picks a reward), reward values."""
    lua, T = gameplay3_runtime()
    check(all(lua.eval("R2FDB.gameplay.%s" % k) is False for k in ("questaccept", "questturnin", "rewardvalue")), "17.3 all three ship OFF")
    # --- off: nothing happens ----------------------------------------------------------------------------
    lua.execute("AVAIL = { { questID = 11 } } ACTIVE = { { questID = 6, isComplete = true } } CHOICES = 0")
    for ev in ("QUEST_DETAIL", "GOSSIP_SHOW", "QUEST_PROGRESS", "QUEST_COMPLETE"):
        T.fire(ev)
    check(lua.eval("ACCEPTED + COMPLETED + #REWARDS + #SEL_AVAIL + #SEL_ACTIVE") == 0, "17.3 off: no quest event does anything")
    # --- accept ----------------------------------------------------------------------------------------------
    lua.execute("R2F.Gameplay.SetOn('questaccept', true)")
    T.fire("QUEST_DETAIL")
    check(lua.eval("ACCEPTED") == 1, "17.3 accept on: the quest window is accepted")
    lua.execute("AUTOACC = true")
    T.fire("QUEST_DETAIL")
    check(lua.eval("ACCEPTED") == 1, "17.3 a quest the game accepted by itself is left alone")
    lua.execute("AUTOACC = false TEST.shift = true")
    T.fire("QUEST_DETAIL")
    check(lua.eval("ACCEPTED") == 1, "17.3 Shift pauses accepting")
    lua.execute("TEST.shift = false ACTIVE = {} AVAIL = { { questID = 11 }, { questID = 12 } }")
    T.fire("GOSSIP_SHOW")
    check(lua_table_to_list(lua.eval("SEL_AVAIL")) == [11], "17.3 gossip: the first available quest is picked: %s" % lua_table_to_list(lua.eval("SEL_AVAIL")))
    lua.execute("GREET_N = 2")
    T.fire("QUEST_GREETING")
    check(lua_table_to_list(lua.eval("GREET_AVAIL")) == [1], "17.3 quest greeting: the first quest is picked")
    # --- hand in -----------------------------------------------------------------------------------------------------
    T.fire("QUEST_PROGRESS")
    check(lua.eval("COMPLETED") == 0, "17.3 hand-in off: a finished quest isn't completed")
    lua.execute("R2F.Gameplay.SetOn('questturnin', true) ACTIVE = { { questID = 5, isComplete = false }, { questID = 6, isComplete = true } } AVAIL = { { questID = 12 } } SEL_AVAIL = {}")
    T.fire("GOSSIP_SHOW")
    check(lua_table_to_list(lua.eval("SEL_ACTIVE")) == [6], "17.3 gossip: the finished quest is picked, not the unfinished one")
    check(lua.eval("#SEL_AVAIL") == 0, "17.3 with both on, a finished quest is handed in before a new one is picked")
    lua.execute("ACTIVE = { { questID = 5, isComplete = false } } SEL_ACTIVE = {}")
    T.fire("GOSSIP_SHOW")
    check(lua.eval("#SEL_ACTIVE") == 0 and lua_table_to_list(lua.eval("SEL_AVAIL")) == [12], "17.3 nothing finished here: the new quest is picked instead")
    T.fire("QUEST_GREETING")
    check(lua_table_to_list(lua.eval("GREET_ACTIVE")) == [2], "17.3 quest greeting: the finished quest (the 2nd) is picked")
    T.fire("QUEST_PROGRESS")
    check(lua.eval("COMPLETED") == 1, "17.3 a completable quest is completed")
    lua.execute("COMPLETABLE = false")
    T.fire("QUEST_PROGRESS")
    check(lua.eval("COMPLETED") == 1, "17.3 not completable: nothing")
    lua.execute("CHOICES = 0")
    T.fire("QUEST_COMPLETE")
    check(lua_table_to_list(lua.eval("REWARDS")) == [1], "17.3 no reward choice: the quest is turned in")
    lua.execute("REWARDS = {} CHOICES = 1")
    T.fire("QUEST_COMPLETE")
    check(lua_table_to_list(lua.eval("REWARDS")) == [1], "17.3 exactly one reward: nothing to choose between, the quest is turned in")
    lua.execute("REWARDS = {} CHOICES = 2")
    T.fire("QUEST_COMPLETE")
    check(lua.eval("#REWARDS") == 0, "17.3 NEVER picks between rewards: two choices are left for you")
    lua.execute("CHOICES = 3")
    T.fire("QUEST_COMPLETE")
    check(lua.eval("#REWARDS") == 0, "17.3 several choices: left for you")
    lua.execute("SAVED_GNC = GetNumQuestChoices GetNumQuestChoices = nil")
    T.fire("QUEST_COMPLETE")
    check(lua.eval("#REWARDS") == 0, "17.3 no way to count the choices: nothing is turned in")
    lua.execute("GetNumQuestChoices = SAVED_GNC")
    lua.execute("CHOICES = 0 TEST.shift = true")
    T.fire("QUEST_COMPLETE")
    check(lua.eval("#REWARDS") == 0, "17.3 Shift pauses handing in")
    lua.execute("TEST.shift = false")
    # --- classic gossip fallback ----------------------------------------------------------------------------------------------
    lua.execute("""C_GossipInfo = nil
      GetNumGossipAvailableQuests = function() return 1 end
      SelectGossipAvailableQuest = function(i) table.insert(SEL_AVAIL, 'classic' .. i) end
      GetNumGossipActiveQuests = function() return 2 end
      GetGossipActiveQuests = function() return 'A', 1, false, false, false, false, 'B', 1, false, true, false, false end
      SelectGossipActiveQuest = function(i) table.insert(SEL_ACTIVE, 'classic' .. i) end
      SEL_AVAIL, SEL_ACTIVE = {}, {}""")
    T.fire("GOSSIP_SHOW")
    check(lua_table_to_list(lua.eval("SEL_ACTIVE")) == ["classic2"], "17.3 classic gossip functions: the finished quest (2nd) is handed in")
    lua.execute("R2F.Gameplay.SetOn('questturnin', false) SEL_AVAIL = {}")
    T.fire("GOSSIP_SHOW")
    check(lua_table_to_list(lua.eval("SEL_AVAIL")) == ["classic1"], "17.3 classic gossip functions: a quest is accepted")
    # --- reward values ---------------------------------------------------------------------------------------------------------------
    lua2, T2 = gameplay3_runtime()
    lua2.execute("CHOICES = 3")
    T2.fire("QUEST_COMPLETE")
    T2.runTimers()
    check(font_text(lua2, "^1s$") is None, "17.3 reward values off: no numbers")
    lua2.execute("R2F.Gameplay.SetOn('rewardvalue', true)")
    T2.fire("QUEST_COMPLETE")
    T2.runTimers()
    check(font_text(lua2, "^1s$") == "1s" and font_text(lua2, "^5s$") == "5s", "17.3 reward values: 100c = 1s and 500c = 5s on the buttons")
    lua2.execute("""for _, f in ipairs(TEST.allFrames) do if f.__kind == 'FontString' and f.__text == '5s' then BEST = f end if f.__kind == 'FontString' and f.__text == '1s' then OTHER = f end end""")
    check(lua2.eval("BEST.__color[1]") < 0.5 and lua2.eval("BEST.__color[2]") == 1 and lua2.eval("OTHER.__color[1]") == 1 and lua2.eval("OTHER.__color[3]") == 1,
          "17.3 the best vendor price is green, the others white")
    lua2.execute("CHOICES = 1")
    T2.fire("QUEST_COMPLETE")
    T2.runTimers()
    lua2.execute("""for _, f in ipairs(TEST.allFrames) do if f.__kind == 'FontString' and f.__text == '1s' then ONLY = f end end""")
    check(lua2.eval("ONLY.__color[1]") == 1, "17.3 a single choice isn't marked best")
    lua2.execute("R2F.Gameplay.SetOn('rewardvalue', false)")
    check(lua2.eval("BEST.__shown") is False, "17.3 reward values off again: the numbers go")
    lua3, T3 = gameplay3_runtime(rewards_api=False)
    check(lua3.eval("R2F.Gameplay.SetOn('rewardvalue', true)") is False, "17.3 no quest reward API: reward values can't be switched on")
    # --- tab ---------------------------------------------------------------------------------------------------------------------------------------
    lua3.execute("R2F.MainWindow.Show('gameplay')")
    find_frames(lua3, "f.__kind == 'CheckButton' and f.r2fLabel", "GB3")
    labels = [lua3.eval("GB3[%d].r2fLabel.__text" % i) for i in range(1, lua3.eval("#GB3") + 1)]
    for k in ("GP_QACCEPT", "GP_QTURNIN", "GP_QVALUE"):
        check(lua3.eval("R2F.L.%s" % k) in labels, "17.3 the Gameplay tab has the %s box" % k)


COPYCHAT_LUA = """
  NUM_CHAT_WINDOWS = 3
  local function mkchat(i, lines)
    local f = CreateFrame('Frame', 'ChatFrame' .. i, UIParent)
    f.GetNumMessages = function() return #lines end
    f.GetMessageInfo = function(self, n) return lines[n] end
    return f
  end
  CHAT1 = {}
  for n = 1, 250 do CHAT1[n] = 'line ' .. n end
  CHAT1[250] = '|cffff0000Red|r |Hitem:1234:0|h[Sword]|h and |TInterface\\\\Icons\\\\X:16|t done ||'
  mkchat(1, CHAT1)
  mkchat(3, { 'third window' })
"""


def copychat_runtime(chat=True):
    lua = new_runtime()
    lua.execute("TEST.reset()")
    if chat:
        lua.execute(COPYCHAT_LUA)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    return lua, T


def test_copychat():
    """ADDON_PLAN 17.2: copy chat text (replaces Prat 3.0 for copying)."""
    lua, T = copychat_runtime()
    # --- plain text -----------------------------------------------------------------------------
    plain = lua.eval("R2F.CopyChat.Plain(CHAT1[250])")
    check(plain == "Red [Sword] and  done |", "17.2 plain text drops colours, links keep their text, textures go: %r" % plain)
    # --- the window ----------------------------------------------------------------------------------
    lua.execute('SlashCmdList.R2F("copychat")')
    check(lua.eval("R2FCopyChat ~= nil and R2FCopyChat:IsShown()") is True, "17.2 /r2f copychat opens the window")
    text = lua.eval("R2FCopyChatScroll.EditBox and R2FCopyChatScroll.EditBox:GetText() or ''")
    lua.execute("""for _, f in ipairs(TEST.allFrames) do if f.__kind == 'EditBox' and f.__parent and f.__parent.__name == 'R2FCopyChatScroll' then CCE = f end end
      if not CCE then for _, f in ipairs(TEST.allFrames) do if f.__kind == 'EditBox' and f.__text and f.__text:find('line 51') then CCE = f end end end""")
    shown = lua.eval("CCE and CCE:GetText() or ''")
    lines = shown.split("\n")
    check(len(lines) == 200, "17.2 the newest 200 of the 250 lines are shown (%d)" % len(lines))
    check(lines[0] == "line 51" and lines[-2] == "line 249", "17.2 oldest first, newest at the bottom: %r ... %r" % (lines[0], lines[-2]))
    check(lines[-1] == "Red [Sword] and  done |", "17.2 plain text is on by default: %r" % lines[-1])
    check(font_text(lua, "^200 lines$") == "200 lines", "17.2 the window says how many lines")
    check("R2FCopyChat" in lua_table_to_list(lua.eval("UISpecialFrames")), "17.2 Esc closes it")
    lua.execute("""for _, f in ipairs(TEST.allFrames) do if f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.CC_PLAIN then PB = f end end
      PB:SetChecked(false) PB:Click()""")
    raw = lua.eval("CCE:GetText()").split("\n")[-1]
    check("|cffff0000Red|r" in raw, "17.2 plain text unticked: the raw line with its colour codes: %r" % raw)
    lua.execute('R2FCopyChat:Hide() SlashCmdList.R2F("copychat 3")')
    check(lua.eval("CCE:GetText()") == "third window", "17.2 /r2f copychat 3 shows chat window 3")
    lua.execute('SlashCmdList.R2F("copychat 9")')
    check(lua.eval("R2FCopyChat:IsShown()") is True, "17.2 an unknown window number falls back to a window that exists")
    # --- the corner buttons ---------------------------------------------------------------------------------
    check(lua.eval("R2FCopyChatButton1 == nil"), "17.2 button off: no corner buttons")
    lua.execute("R2F.Gameplay.SetOn('copychat', true)")
    check(lua.eval("R2FCopyChatButton1 ~= nil and R2FCopyChatButton1:IsShown()") is True and lua.eval("R2FCopyChatButton3 ~= nil"),
          "17.2 button on: one in every chat window's corner")
    lua.execute("R2FCopyChat:Hide() R2FCopyChatButton3:Click()")
    check(lua.eval("R2FCopyChat:IsShown()") is True and lua.eval("CCE:GetText()") == "third window", "17.2 a corner button opens that window's text")
    lua.execute("R2F.Gameplay.SetOn('copychat', false)")
    check(lua.eval("R2FCopyChatButton1:IsShown()") is False, "17.2 off again: the buttons go")
    # --- no readable chat -----------------------------------------------------------------------------------------------
    lua2, T2 = copychat_runtime(chat=False)
    lua2.execute("ChatFrame1 = nil ChatFrame2 = nil ChatFrame3 = nil")
    T2.chat = lua2.table()
    lua2.execute('SlashCmdList.R2F("copychat")')
    check("no chat window whose text can be read" in chat_all(lua2), "17.2 no readable chat window: says so")
    check(lua2.eval("R2F.Gameplay.SetOn('copychat', true)") is False, "17.2 ... and the button feature can't be switched on")


QZONE_LUA = """
  ENTRIES = { { isHeader = true }, { questID = 11 }, { questID = 12 }, { isHeader = true }, { questID = 21 } }
  WATCH = {}
  C_QuestLog = {
    GetNumQuestLogEntries = function() return #ENTRIES end,
    GetInfo = function(i) return ENTRIES[i] end,
    GetQuestWatchType = function(id) if WATCH[id] then return 0 end end,
    AddQuestWatch = function(id) WATCH[id] = true end,
    RemoveQuestWatch = function(id) WATCH[id] = nil end,
  }
  HEAD1 = CreateFrame('Button', nil, UIParent) HEAD1.questLogIndex = 1
  HEAD2 = CreateFrame('Button', nil, UIParent) HEAD2.questLogIndex = 4
  HEAD2.CollapseButton = CreateFrame('Button', nil, HEAD2)
  ACTIVE = { [HEAD1] = true, [HEAD2] = true }
  QuestScrollFrame = { headerFramePool = { EnumerateActive = function() return pairs(ACTIVE) end } }
  QUESTLOG_UPDATES = 0
  function QuestLogQuests_Update() QUESTLOG_UPDATES = QUESTLOG_UPDATES + 1 end
"""


def test_questzone():
    """ADDON_PLAN 17 step 3b: a track-all box on every quest-log zone header."""
    lua = new_runtime()
    lua.execute("TEST.reset()")
    lua.execute(QZONE_LUA)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    box = lambda h: "(function() for _, f in ipairs(TEST.allFrames) do if f.__kind == 'CheckButton' and f.__parent == %s then return f end end end)()" % h
    check(lua.eval("R2FDB.gameplay.questzone") is False, "17.3b ships OFF")
    check(lua.eval(box("HEAD1")) is None, "17.3b off: no boxes on the headers")
    check(lua.eval("R2F.Gameplay.SetOn('questzone', true)") is True, "17.3b switched on")
    check(lua.eval(box("HEAD1")) is not None and lua.eval(box("HEAD2")) is not None, "17.3b a box on every zone header")
    check(lua.eval("%s:GetChecked()" % box("HEAD1")) is False, "17.3b nothing tracked: unticked")
    check(lua.eval("%s.__point[2] == HEAD2.CollapseButton and %s.__point[3] == 'LEFT'" % (box("HEAD2"), box("HEAD2"))) is True,
          "17.3b the box sits to the LEFT of the game's collapse button (not on top of it)")
    check(lua.eval("%s.__point[2] == HEAD1 and %s.__point[4] < -10" % (box("HEAD1"), box("HEAD1"))) is True,
          "17.3b a header without that button: the box keeps clear of the right edge")
    lua.execute("%s:Click()" % box("HEAD1"))
    check(lua.eval("WATCH[11] == true and WATCH[12] == true and WATCH[21] == nil"), "17.3b ticking tracks every quest under that header only")
    check(lua.eval("%s:GetChecked()" % box("HEAD1")) is True, "17.3b the box is ticked")
    lua.execute("%s:Click()" % box("HEAD1"))
    check(lua.eval("WATCH[11] == nil and WATCH[12] == nil"), "17.3b unticking untracks them all")
    lua.execute("WATCH[11] = true")
    lua.execute("QuestLogQuests_Update()")
    check(lua.eval("%s:GetChecked()" % box("HEAD1")) is False, "17.3b only some tracked: unticked (and redrawn after the game redraws its list)")
    lua.execute("%s:Click()" % box("HEAD1"))
    check(lua.eval("WATCH[11] == true and WATCH[12] == true"), "17.3b with only some tracked a click tracks the rest (not untrack)")
    lua.execute("WATCH[21] = true QuestLogQuests_Update()")
    check(lua.eval("%s:GetChecked()" % box("HEAD2")) is True, "17.3b the second header is ticked when its one quest is tracked")
    lua.execute("R2F.Gameplay.SetOn('questzone', false)")
    check(lua.eval(box("HEAD1")).__shown is False if False else lua.eval("%s.__shown" % box("HEAD1")) is False, "17.3b off again: the boxes go")
    lua.execute("ENTRIES = { { isHeader = true } }")
    lua.execute("R2F.Gameplay.SetOn('questzone', true) QuestLogQuests_Update()")
    check(lua.eval("%s:GetChecked()" % box("HEAD1")) is False, "17.3b an empty zone is never ticked")
    lua2 = new_runtime()
    lua2.execute("TEST.reset()")
    lua2.execute(QZONE_LUA + " QuestScrollFrame = nil")
    T2 = lua2.eval("TEST")
    T2.fire("ADDON_LOADED", "RoadToForever")
    T2.fire("PLAYER_LOGIN")
    check(lua2.eval("R2F.Gameplay.SetOn('questzone', true)") is False, "17.3b no quest log frame on this client: can't be switched on")


def test_reactalert():
    """17.3c: our own movable reactive-ability alert (replaces the 0.27.0 combat-text shift that tainted the game)."""
    lua = new_runtime()
    lua.execute("TEST.reset()")
    lua.execute("TEST.cvars.floatingCombatTextReactives_v2 = '1'")
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    shown = lambda: lua.eval("(function() for _, f in ipairs(TEST.allFrames) do if f.__kind == 'FontString' and f.__text and (f.__text:find('^<') or f.__text == 'Ability ready') and f.__shown then return f.__text end end end)()")
    check(all(lua.eval("R2FDB.gameplay.%s" % k) is False for k in ("reactalert", "reactlock", "reactblizz")) and lua.eval("R2FReactAlertAnchor == nil"),
          "17.3c all three ship OFF, no marker")
    T.fire("COMBAT_TEXT_UPDATE", "SPELL_ACTIVE", "Revenge")
    check(shown() is None, "17.3c off: nothing is shown")
    check(lua.eval("R2F.Gameplay.SetOn('reactalert', true)") is True and lua.eval("R2FReactAlertAnchor:IsShown()") is True, "17.3c on: the marker shows")
    T.fire("COMBAT_TEXT_UPDATE", "SPELL_ACTIVE", "Revenge")
    check(shown() == "<Revenge>", "17.3c a reactive ability announcement shows <Revenge> in our own text: %r" % shown())
    T.runTimers()
    check(shown() is None, "17.3c ... and it goes away after a couple of seconds")
    # no bar glow on this client: the name comes from the reactive spell that just became usable
    lua.execute("TEST.t = 0 GetTime = function() return TEST.t end")
    lua.execute("local u = {} TEST.usable = u C_Spell = C_Spell or {} C_Spell.IsSpellUsable = function(n) return u[n] == true end")
    lua.execute("issecretvalue = function() return false end")
    T.fire("SPELL_UPDATE_USABLE")
    lua.execute("TEST.usable.Revenge = true")
    T.fire("SPELL_UPDATE_USABLE")
    T.fire("COMBAT_TEXT_UPDATE", "SPELL_ACTIVE", None)
    check(shown() == "<Revenge>", "17.3c a hidden announcement name is filled in from the spell that just became usable: %r" % shown())
    T.runTimers()
    lua.execute("TEST.t = 10")
    lua.execute("TEST.usable.Revenge = nil")
    T.fire("SPELL_UPDATE_USABLE")
    T.fire("COMBAT_TEXT_UPDATE", "DAMAGE", "Revenge")
    check(shown() is None, "17.3c other combat text messages are ignored")
    lua.execute("issecretvalue = function(v) return v == 'SECRET' end")
    T.fire("COMBAT_TEXT_UPDATE", "SPELL_ACTIVE", "SECRET")
    check(shown() == "Ability ready", "17.3c a secret spell name falls back to 'Ability ready' (no error)")
    T.runTimers()
    # the real name from the glow event (spell id), whichever of the two announcements comes first
    lua.execute("GetTime = function() return TEST.time or 0 end TEST.spellNames[6572] = 'Revenge' TEST.time = 100")
    T.fire("SPELL_ACTIVATION_OVERLAY_GLOW_SHOW", 6572)
    check(shown() is None, "17.3c a glow alone doesn't show the alert")
    T.fire("COMBAT_TEXT_UPDATE", "SPELL_ACTIVE", "SECRET")
    check(shown() == "<Revenge>", "17.3c the glow announced a moment before names the hidden spell: %r" % shown())
    T.runTimers()
    lua.execute("TEST.time = 105")
    T.fire("COMBAT_TEXT_UPDATE", "SPELL_ACTIVE", "SECRET")
    check(shown() == "Ability ready", "17.3c a glow from five seconds ago is not used")
    lua.execute("TEST.time = 105.4")
    T.fire("SPELL_ACTIVATION_OVERLAY_GLOW_SHOW", 6572)
    check(shown() == "<Revenge>", "17.3c a glow that comes just after the announcement upgrades the text to the name: %r" % shown())
    T.runTimers()
    lua.execute("TEST.time = 200")
    T.fire("SPELL_ACTIVATION_OVERLAY_GLOW_SHOW", 6572)
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("reactlog")')
    check("GLOW_SHOW 6572 Revenge" in chat_all(lua) and "SPELL_ACTIVE (name hidden)" in chat_all(lua), "17.3c /r2f reactlog lists what the alert saw: %r" % chat_all(lua))
    # two alerts in a row: the older timer must not hide the newer text
    T.fire("COMBAT_TEXT_UPDATE", "SPELL_ACTIVE", "Revenge")
    T.fire("COMBAT_TEXT_UPDATE", "SPELL_ACTIVE", "Overpower")
    lua.execute("local first = table.remove(TEST.timers, 1) first()")
    check(shown() == "<Overpower>", "17.3c an older timer doesn't hide a newer alert")
    T.runTimers()
    # marker: drag, lock
    lua.execute("R2FReactAlertAnchor.__cx, R2FReactAlertAnchor.__cy = 80, 120 R2FReactAlertAnchor:Fire('OnDragStart') R2FReactAlertAnchor:Fire('OnDragStop')")
    check(lua.eval("R2FDB.fct.x") == 80 and lua.eval("R2FDB.fct.y") == 120, "17.3c dropping the marker saves its place")
    lua.execute("R2F.Gameplay.SetOn('reactlock', true)")
    check(lua.eval("R2FReactAlertAnchor:IsShown()") is False and lua.eval("R2FDB.fct.lock") is True, "17.3c locked: marker hidden, place kept")
    T.fire("COMBAT_TEXT_UPDATE", "SPELL_ACTIVE", "Revenge")
    check(shown() == "<Revenge>", "17.3c a locked alert still shows")
    lua.execute("R2F.Gameplay.SetOn('reactlock', false)")
    check(lua.eval("R2FReactAlertAnchor:IsShown()") is True, "17.3c unlocked: marker back")
    lua.execute("R2F.Gameplay.SetOn('reactalert', false)")
    check(lua.eval("R2FReactAlertAnchor:IsShown()") is False, "17.3c off: marker gone")
    # hide the game's own text
    check(lua.eval("R2F.Gameplay.SetOn('reactblizz', true)") is True and lua.eval("TEST.cvars.floatingCombatTextReactives_v2") == "0"
          and lua.eval("R2FDB.reactWas") == "1", "17.3c hide the game's own reactive text: its setting goes to 0, the old value is remembered")
    lua.execute("R2F.Gameplay.SetOn('reactblizz', false)")
    check(lua.eval("TEST.cvars.floatingCombatTextReactives_v2") == "1" and lua.eval("R2FDB.reactWas") is None, "17.3c untick: the player's value is back")
    T.chat = lua.table()
    lua.execute("R2F.Gameplay.SetOn('reactblizz', true)")
    check("type /reload" in chat_all(lua), "17.3c switching it tells the player a /reload is needed (the game reads the setting when it loads)")
    # A login re-applies the saved choice (onToggle(true) with the game's setting already at 0): no second /reload line.
    T.chat = lua.table()
    lua.eval("R2F.Gameplay.FEATURES")
    lua.execute("for _, d in ipairs(R2F.Gameplay.FEATURES) do if d.key == 'reactblizz' then d.onToggle(true) end end")
    check("type /reload" not in chat_all(lua), "17.3c the setting is already off at login: nothing is said, nothing is written again")
    lua.execute("R2F.Gameplay.SetOn('reactblizz', false)")
    T.combat = True
    check(lua.eval("R2F.Gameplay.SetOn('reactblizz', true)") is False, "17.3c a game setting can't be changed in combat")
    T.combat = False
    lua2 = new_runtime()
    lua2.execute("TEST.reset()")
    T2 = lua2.eval("TEST")
    T2.fire("ADDON_LOADED", "RoadToForever")
    T2.fire("PLAYER_LOGIN")
    check(lua2.eval("R2F.Gameplay.SetOn('reactblizz', true)") is False, "17.3c no such game setting: can't be switched on")
    # THE REGRESSION GUARD: nothing in the addon writes into the game's combat text (0.27.0 tainted it)
    bad = []
    for dirpath, _, names in os.walk(ADDON):
        for nm in names:
            if nm.endswith(".lua"):
                code = "\n".join(l.split("--", 1)[0] for l in open(os.path.join(dirpath, nm), encoding="utf-8"))
                if re.search(r"textLocations\s*(\.\s*\w+\s*=[^=]|=[^=])", code) or re.search(r"CombatText\s*(\.\s*\w+\s*=[^=]|:\s*\w+\s*\()", code):
                    bad.append(nm)
    check(bad == [], "17.3c no file writes into the game's CombatText / textLocations (it taints the game's code): %s" % bad)


def test_gossipshop():
    """ADDON_PLAN 17 step 4: skip the single shop line at an NPC (icon whitelist)."""
    lua = new_runtime()
    lua.execute("TEST.reset()")
    lua.execute("""
      OPTS, AVAIL, ACTIVE, PICKED = {}, {}, {}, {}
      C_GossipInfo = {
        GetOptions = function() return OPTS end,
        GetAvailableQuests = function() return AVAIL end,
        GetActiveQuests = function() return ACTIVE end,
        SelectOption = function(id) table.insert(PICKED, id) end,
      }
      function opt(id, icon, status, name) return { gossipOptionID = id, icon = icon, status = status or 0, name = name or 'x', flags = 0 } end
    """)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    check(lua.eval("R2FDB.gameplay.gossipshop") is False, "17.4 ships OFF")
    lua.execute("OPTS = { opt(7, 132060) }")
    T.fire("GOSSIP_SHOW")
    check(lua.eval("#PICKED") == 0, "17.4 off: nothing is picked")
    lua.execute("R2F.Gameplay.SetOn('gossipshop', true)")
    T.fire("GOSSIP_SHOW")
    check(lua_table_to_list(lua.eval("PICKED")) == [7], "17.4 one vendor line: picked")
    for icon, name in ((132058, "trainer"), (132050, "bank"), (132057, "flights"), (528409, "auctions")):
        lua.execute("PICKED = {} OPTS = { opt(8, %d) }" % icon)
        T.fire("GOSSIP_SHOW")
        check(lua_table_to_list(lua.eval("PICKED")) == [8], "17.4 one %s line: picked" % name)
    lua.execute("PICKED = {} OPTS = { opt(9, 132052) }")
    T.fire("GOSSIP_SHOW")
    check(lua.eval("#PICKED") == 0, "17.4 the innkeeper's 'make this your home' icon is never picked")
    lua.execute("OPTS = { opt(9, 132053) }")
    T.fire("GOSSIP_SHOW")
    check(lua.eval("#PICKED") == 0, "17.4 a plain gossip line (could start an escort or a fight) is never picked")
    lua.execute("OPTS = { opt(7, 132060), opt(8, 132053) }")
    T.fire("GOSSIP_SHOW")
    check(lua.eval("#PICKED") == 0, "17.4 more than one line: left for the player")
    lua.execute("OPTS = { opt(7, 132060, 1) }")
    T.fire("GOSSIP_SHOW")
    check(lua.eval("#PICKED") == 0, "17.4 an unavailable line is not picked")
    lua.execute("OPTS = { opt(7, 132060) } AVAIL = { { questID = 5 } }")
    T.fire("GOSSIP_SHOW")
    check(lua.eval("#PICKED") == 0, "17.4 the NPC offers a quest: nothing is picked")
    lua.execute("AVAIL = {} ACTIVE = { { questID = 6, isComplete = false } }")
    T.fire("GOSSIP_SHOW")
    check(lua.eval("#PICKED") == 0, "17.4 the NPC has a quest of yours: nothing is picked")
    lua.execute("ACTIVE = {} TEST.shift = true")
    T.fire("GOSSIP_SHOW")
    check(lua.eval("#PICKED") == 0, "17.4 Shift pauses it")
    lua.execute("TEST.shift = false")
    T.fire("GOSSIP_SHOW")
    check(lua_table_to_list(lua.eval("PICKED")) == [7], "17.4 back to normal without Shift")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("gossip")')
    txt = chat_all(lua)
    check("gossip options (1):" in txt and "icon 132060 (shop)" in txt and "the addon would pick: x" in txt, "17.4 /r2f gossip lists the options with icon ids: %r" % txt)
    lua.execute("OPTS = {}")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("gossip")')
    check("no gossip options" in chat_all(lua), "17.4 /r2f gossip with no window says so")
    lua2 = new_runtime()
    lua2.execute("TEST.reset() C_GossipInfo = nil")
    T2 = lua2.eval("TEST")
    T2.fire("ADDON_LOADED", "RoadToForever")
    T2.fire("PLAYER_LOGIN")
    check(lua2.eval("R2F.Gameplay.SetOn('gossipshop', true)") is False, "17.4 no gossip API: can't be switched on")


TRACK_LUA = """
  TRACKS = {
    { name = 'Find Herbs', texture = 133939, active = false, type = 'spell', subType = 0, spellID = 2383 },
    { name = 'Find Minerals', texture = 136025, active = false, type = 'spell', subType = 0, spellID = 2580 },
    { name = 'Track Humanoids', texture = 133939, active = false, type = 'spell', subType = 0, spellID = 19883 },
  }
  C_Minimap = {
    GetNumTrackingTypes = function() return #TRACKS end,
    GetTrackingInfo = function(i) return TRACKS[i] end,
  }
"""


def tracking_runtime(token="PRIEST", tracks=True, preset=None):
    lua = new_runtime()
    lua.execute("TEST.reset()")
    lua.execute("TEST.classToken = %r" % token)
    if tracks:
        lua.execute(TRACK_LUA)
    if preset:
        lua.execute("R2FDB = %s" % preset)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    return lua, T


def test_tracking():
    """ADDON_PLAN 17.1 step 5 (first cut): the minimap-tracking reminder (Find Minerals / Herbs / Treasure)."""
    lua, T = tracking_runtime()
    check(lua.eval("R2F.Tracking.Applies()") is True and lua.eval("R2FTrackingFrame ~= nil"), "17.5 a Priest who has Find Herbs / Minerals gets the tracking reminder (any class)")
    check(lua.eval("R2FDB.tracking.herbs") is True and lua.eval("R2FDB.tracking.minerals") is True and lua.eval("R2FDB.tracking.treasure") is True,
          "17.5 all three types are ticked by default")
    check(lua.eval("R2FTrackingFrame:IsShown()") is True and lua.eval("R2FTrackingFrame.border.__ctex[1]") > 0.9,
          "17.5 known and none active: shown with the attention colour")
    check(lua.eval("R2FTrackingFrame.icon.__tex") == 136025, "17.5 the icon is the first ticked tracking type's (minerals come first)")
    lua.execute("R2F.Tracking.SetLock(true)")
    check(lua.eval("R2FTrackingFrame:IsShown()") is True, "17.5 locked and needed: still shown")
    lua.execute("TRACKS[1].active = true") ; T.fire("MINIMAP_UPDATE_TRACKING")
    check(lua.eval("R2FTrackingFrame:IsShown()") is False, "17.5 one of them active: hidden (locked)")
    lua.execute("R2F.Tracking.SetLock(false)")
    check(lua.eval("R2FTrackingFrame:IsShown()") is False, "17.5 unlocked while tracking is on: still hidden (it is gone while you are tracking)")
    lua.execute("TRACKS[1].active = false TRACKS[2].active = true") ; T.fire("MINIMAP_UPDATE_TRACKING")
    lua.execute("R2F.Tracking.SetLock(true)")
    check(lua.eval("R2FTrackingFrame:IsShown()") is False, "17.5 the other type active also counts (only one tracking is on at a time)")
    lua.execute("TRACKS[2].active = false TRACKS[3].active = true") ; T.fire("MINIMAP_UPDATE_TRACKING")
    check(lua.eval("R2FTrackingFrame:IsShown()") is True, "17.5 an unrelated tracking (Track Humanoids) does not count as the ticked ones")
    lua.execute("R2F.Tracking.SetKind('herbs', false) R2F.Tracking.SetKind('minerals', false)")
    check(lua.eval("R2FTrackingFrame:IsShown()") is False, "17.5 no known type ticked: nothing to remind about")
    lua.execute("R2F.Tracking.SetKind('herbs', true)")
    check(lua.eval("R2FTrackingFrame:IsShown()") is True, "17.5 tick Herbs again: reminder is back")
    lua.execute("R2F.Tracking.SetShown(false)")
    check(lua.eval("R2FTrackingFrame:IsShown()") is False, "17.5 switched off: hidden")
    # persistence and the tab
    lua.execute("R2F.Tracking.SetShown(true) R2F.MainWindow.Show('gameplay') R2F.GameplayTab.ShowPage('icons')")
    check(lua.eval("R2FTrackingScale ~= nil and R2FTrackingScale:IsVisible()") is True, "17.5 the section is on the Gameplay tab's Reminders column")
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.TRACKING_HERBS", "TH")
    check(lua.eval("#TH") == 1 and lua.eval("TH[1]:GetChecked()") is True, "17.5 the 'remind about Find Herbs' box is ticked")
    lua.execute("TH[1]:Click()")
    check(lua.eval("R2FDB.tracking.herbs") is False and lua.eval("TH[1]:GetChecked()") is False, "17.5 clicking it unticks the type")
    # no tracking spell at all
    lua2, T2 = tracking_runtime(tracks=False)
    check(lua2.eval("R2F.Tracking.Applies()") is False and lua2.eval("R2FTrackingFrame:IsShown()") is False, "17.5 a character with no tracking spell: no icon (even unlocked)")
    lua2.execute("R2F.MainWindow.Show('gameplay') R2F.GameplayTab.ShowPage('icons')")
    check(lua2.eval("R2FTrackingScale == nil"), "17.5 ... and no section on the tab")
    # a Warrior still gets its own reminder next to it
    lua3, T3 = tracking_runtime(token="WARRIOR")
    lua3.execute("R2F.MainWindow.Show('gameplay') R2F.GameplayTab.ShowPage('icons')")
    check(lua3.eval("R2FStanceScale ~= nil and R2FTrackingScale ~= nil"), "17.5 class reminders and the tracking one live side by side")
    # bad saved values repaired
    lua4, T4 = tracking_runtime(preset="{ tracking = { scale = 9, herbs = 'x' } }")
    check(lua4.eval("R2FDB.tracking.scale") == 1 and lua4.eval("R2FDB.tracking.herbs") is True, "17.5 invalid saved values fall back to the defaults")


def test_aura_probe():
    """/r2f auras: a read-only probe of what the client lets an addon read."""
    lua = new_runtime()
    lua.execute("TEST.reset()")
    lua.execute("""
      UnitExists = function(u) return u == 'player' or u == 'party1' end
      IsInInstance = function() return false end
      C_Secrets = { HasSecretRestrictions = function() return true end, ShouldAurasBeSecret = function() return false end }
      C_UnitAuras = { GetUnitAuras = function(unit, filter)
        if unit == 'player' then return { { spellId = 1 }, { spellId = 2 }, { spellId = 3 } } end
        if unit == 'party1' then return { { spellId = 9 } } end
      end }
      issecretvalue = function(v) return v == 9 end
    """)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("auras")')
    txt = chat_all(lua)
    check("secret restrictions yes, auras secret no, in combat no, in an instance no" in txt, "aura probe header: %r" % txt)
    check("player: 3 buffs, 3 with a readable spell id" in txt, "aura probe: your own buffs are counted")
    check("party1: 1 buffs, 0 with a readable spell id" in txt, "aura probe: a secret spell id is not counted as readable")
    check("party2" not in txt, "aura probe: absent units are skipped")
    lua.execute("C_UnitAuras = nil")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("auras")')
    check("no C_UnitAuras.GetUnitAuras" in chat_all(lua), "aura probe without the API says so")
    lua.execute("C_UnitAuras = { GetUnitAuras = function() error('restricted') end }")
    T.chat = lua.table()
    lua.execute('SlashCmdList.R2F("auras")')
    check("reading failed" in chat_all(lua), "aura probe: a refused read is reported, not raised")


# ---------------------------------------------------------------------------
BIZ_STUBS = """
BIZ_Q = { [252512] = 2, [7374] = 3, [6720] = 2 }
C_Item = C_Item or {}
C_Item.GetItemQualityByID = function(id) return BIZ_Q[id] end
C_Item.GetItemIconByID = function(id) if BIZ_Q[id] then return 'Interface\\\\Icons\\\\INV_Helmet_' .. id end end
BIZ_REQUESTED = {}
C_Item.RequestLoadItemDataByID = function(id) BIZ_REQUESTED[id] = true end
function GetItemInfo(id)
  if BIZ_Q[id] then return 'Item ' .. id, '|cff1eff00|Hitem:' .. id .. '::::::::|h[Item ' .. id .. ']|h|r', BIZ_Q[id] end
end
BIZ_FACTION = 'Alliance'
function UnitFactionGroup() return BIZ_FACTION end
function GameTooltip:SetItemByID(id) self.itemArgs = { id }; table.insert(self.lines, 'ITEM ' .. id) end
function GameTooltip:Show() self.__shown = true end
function GameTooltip:Hide() self.__shown = false end
"""


def biz_runtime(templates=True, token="HUNTER", preset=None):
    lua = new_runtime(templates, before_load=BIZ_STUBS)
    lua.execute("TEST.reset()")
    lua.execute("TEST.classToken = '%s'" % token)
    if not templates:
        lua.execute("TEST.templates.UIPanelScrollFrameTemplate = nil")
    if preset:
        lua.execute("R2FCharDB = %s" % preset)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    return lua, T


def test_biz(templates=True):
    """ADDON_PLAN 19: Mr.BiZ tab: data, spec choice, filters, wishlist, tooltips, quality, site string."""
    import subprocess
    tag = "biz " + ("templates" if templates else "fallbacks")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "bis", "build_bis.py"), "--check"], capture_output=True, text=True)
    check(r.returncode == 0, "BiZData.lua and bis-data.json match bis/raw (run python bis/build_bis.py): %s" % r.stdout.strip())
    site = json.load(open(os.path.join(ROOT, "bis-data.json"), encoding="utf-8"))

    lua, T = biz_runtime(templates)
    BiZ = lua.eval("R2F.BiZ")
    D = lua.eval("R2F.BiZData")
    check(len(site["specs"]) == 27 and lua.eval("(function() local n = 0 for _ in pairs(R2F.BiZData.specs) do n = n + 1 end return n end)()") == 27,
          "%s: 27 specs in the addon and on the site" % tag)
    # every spec: the same 17 best picks in game as on the site
    same = True
    for sid, sp in site["specs"].items():
        for i, sl in enumerate(sp["slots"], 1):
            lb = lua.eval("R2F.BiZData.specs[%r].slots[%d].best" % (sid, i))
            want = sl.get("best")
            if (lb is None) != (want is None) or (want and (lb.id != want["id"] or lb.type != want["type"])):
                same = False
    check(same, "%s: addon data = site data for every spec and slot" % tag)

    # default class = the player's, first spec; choice remembered per class
    check(BiZ.Class() == "hunter" and BiZ.SpecId() == "hunter/beast-mastery", "%s: opens on your class, first spec" % tag)
    BiZ.SetSpec("hunter/survival")
    BiZ.SetClass("mage")
    check(BiZ.SpecId() == "mage/arcane", "%s: another class shows its first spec" % tag)
    BiZ.SetClass("hunter")
    check(BiZ.SpecId() == "hunter/survival", "%s: the spec picked for a class is remembered" % tag)
    BiZ.SetSpec("hunter/beast-mastery")
    check(lua.eval("R2FCharDB.biz.spec.hunter") == "hunter/beast-mastery", "%s: spec saved per character" % tag)
    roles = [lua.eval("R2F.BiZ.Spec(R2F.BiZ.SpecsOf('warrior')[1]).role")]
    check(roles == ["tank"], "%s: Warrior lists Protection (tank) first" % tag)

    # filters
    types = [lua.eval("R2F.BiZ.Types()[%d]" % i) for i in range(1, lua.eval("#R2F.BiZ.Types()") + 1)]
    check("raid" not in types and "quest" in types and "dungeon" in types, "%s: filter chips only for types in the data: %s" % (tag, types))
    legs = lua.eval("R2F.BiZData.specs['hunter/beast-mastery'].slots[9].best")
    check(legs.type == "quest" and BiZ.Passes(legs), "%s: quest pick passes by default" % tag)
    BiZ.SetTypeOn("quest", False)
    check(not BiZ.Passes(legs) and lua.eval("R2FCharDB.biz.types.quest") is False, "%s: quest filter off hides it (saved)" % tag)
    BiZ.SetTypeOn("quest", True)
    check(lua.eval("R2FCharDB.biz.types.quest") is None, "%s: back on clears the saved flag" % tag)
    unk = lua.eval("R2F.BiZData.specs['hunter/beast-mastery'].slots[12].best")
    check(unk.type == "unknown" and BiZ.Passes(unk), "%s: unknown source shows by default" % tag)
    BiZ.SetKnownOnly(True)
    check(not BiZ.Passes(unk), "%s: Known sources hides it" % tag)
    BiZ.SetKnownOnly(False)
    check(BiZ.FactionNote(legs) == lua.eval("R2F.L.BIZ_HORDE_ONLY"), "%s: Horde quest flagged for an Alliance player" % tag)
    lua.execute("BIZ_FACTION = 'Horde'")
    check(BiZ.FactionNote(legs) is None, "%s: no flag for a Horde player" % tag)
    lua.execute("BIZ_FACTION = 'Alliance'")

    # quality colour and icon from the game, white + request while unknown
    check(BiZ.ColoredName(252512, "Brawler's Leather Helm").startswith("|cff1eff00"), "%s: uncommon item in green" % tag)
    check(BiZ.ColoredName(7374, "Dusky Leather Armor").startswith("|cff0070dd"), "%s: rare item in blue" % tag)
    check(BiZ.ColoredName(999999, "X").startswith("|cffffffff") and lua.eval("BIZ_REQUESTED[999999]") is True,
          "%s: unknown item white, and the client is asked to load it" % tag)

    # wishlist + the site's string
    BiZ.ToggleWish(252512, "hunter/beast-mastery", "head")
    BiZ.ToggleWish(7374, "hunter/beast-mastery", "chest")
    BiZ.ToggleWish(6720, "hunter/beast-mastery", "head")
    check(BiZ.WishCount() == 3, "%s: three items wished" % tag)
    exp = BiZ.Export()
    check(exp == "R2FW1:6720:hunter/beast-mastery:head,7374:hunter/beast-mastery:chest,252512:hunter/beast-mastery:head",
          "%s: export string: %s" % (tag, exp))
    groups = lua.eval("R2F.BiZ.WishGroups()")
    gnames = [groups[i].name for i in range(1, len(groups) + 1)]
    check(gnames == ["Leatherworking", lua.eval("R2F.L.BIZ_GROUP_NEXT")], "%s: grouped by source, next-best picks last: %s" % (tag, gnames))
    BiZ.ToggleWish(6720, "hunter/beast-mastery", "head")
    check(not BiZ.IsWished(6720), "%s: toggling again removes it" % tag)
    bad = BiZ.Import("junk")
    check(isinstance(bad, tuple) and bad[0] is None and "R2FW1" in bad[1], "%s: a non-wishlist string is refused: %r" % (tag, bad))
    site_string = "R2FW1:252512:hunter/beast-mastery:head,2721:priest/holy:head,123:nope/nope:head,x:priest/holy:head"
    n = BiZ.Import("  " + site_string + "\\n")
    check(n == 1 and BiZ.IsWished(2721) and not BiZ.IsWished(123), "%s: import adds new valid items only (%s)" % (tag, n))
    check(lua.eval("R2FCharDB.biz.wish[2721].spec") == "priest/holy", "%s: imported item keeps its spec" % tag)

    # the tab
    lua.execute("R2F.MainWindow.Show('bis')")
    win = "R2FMain"
    title = lua.eval("R2F.MainWindow.Title()")
    check(title == "Road to Forever: Mr.BiZ", "%s: tab title %r" % (tag, title))
    # Paper doll: one button per gear slot; the head is selected first and its options are listed.
    n = find_frames(lua, "f.__kind == 'Button' and f.slotKey ~= nil and f.__shown", "DOLL")
    check(n == 17, "%s: 17 gear slots on the doll (%d)" % (tag, n))
    find_frames(lua, "f.__kind == 'Button' and f.slotKey == 'head'", "HEADBTN")
    check(lua.eval("HEADBTN[1].itemId") == 252512 and lua.eval("HEADBTN[1].sel.__shown") is True,
          "%s: head slot shows its best pick and is selected" % tag)
    find_frames(lua, "f.__kind == 'Button' and f.optRank == 1 and f.itemId == 252512 and f.__shown", "HELM")
    check(lua.eval("#HELM") == 1, "%s: Brawler's Leather Helm is option 1 of the head panel" % tag)
    txt = lua.eval("HELM[1].fs.__text")
    check(txt.startswith("|cff1eff00Brawler's Leather Helm"), "%s: name in its quality colour: %r" % (tag, txt))
    check(lua.eval("HEADBTN[1].border.__ctex[2]") == 1 and lua.eval("HEADBTN[1].border.__ctex[1]") < 0.2,
          "%s: the slot frame has the item's quality colour (green)" % tag)
    lua.execute("HELM[1]:Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(lua.eval("GameTooltip.itemArgs[1]") == 252512 and lines[0] == "ITEM 252512", "%s: mouseover shows the game's item tooltip" % tag)
    check(any("Bizzest for Beast Mastery" in (l or "") for l in lines), "%s: tooltip adds the Mr.BiZ rank line: %s" % (tag, lines))
    check(lua.eval("R2F.BiZ.RankName(2)") == "Bizzer" and lua.eval("R2F.BiZ.RankName(3)") == "Biz" and lua.eval("R2F.BiZ.RankName(5)") == "Almost biz", "%s: biz rank names" % tag)
    check(lua.eval("R2F.BiZ.IsTheBizz({ next = { { delta = -25 } } })") is True and lua.eval("R2F.BiZ.IsTheBizz({ next = { { delta = -12 } } })") is False and lua.eval("R2F.BiZ.IsTheBizz({ next = {} })") is False, "%s: The Bizz needs a 20%% lead" % tag)
    lua.execute("HELM[1]:Fire('OnLeave')")
    check(lua.eval("GameTooltip.__shown") is False, "%s: leaving hides the tooltip" % tag)
    # the other ranked picks are listed right under it
    find_frames(lua, "f.__kind == 'Button' and f.optRank == 2 and f.itemId == 6720 and f.__shown", "NEXT2")
    check(lua.eval("#NEXT2") == 1, "%s: rank 2 (Spirit Hunter Headdress) is listed too" % tag)
    lua.execute("NEXT2[1]:Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(any("Bizzer for Beast Mastery, 12% behind" in (l or "") for l in lines), "%s: rank 2 tooltip says how far behind: %s" % (tag, lines))

    # Enchants from the Professions page, per spec and slot.
    if templates:
        check(all(len(sp.get("enchants", {})) >= 3 for sp in site["specs"].values()),
              "%s: every spec has BiS enchants for several slots" % tag)
        check(site["specs"]["druid/feral"]["enchantPage"] == "Druid Tank", "%s: Feral (bear) uses the tank enchant page" % tag)
        check(lua.eval("R2F.BiZ.Enchants('hunter/beast-mastery', 'neck')[1].name") == "Enchant Necklace - Agility",
              "%s: Hunter neck = Enchant Necklace - Agility" % tag)
        check(lua.eval("#R2F.BiZ.Enchants('hunter/beast-mastery', 'trinket1')") == 0, "%s: no enchant for trinkets" % tag)
        lua.execute("R2F.BiZ.SetSpec('hunter/beast-mastery') for _, b in ipairs(DOLL) do if b.slotKey == 'neck' then b:Click() end end")
        check(font_text(lua, "^Enchant: Enchant Necklace %- Agility") is not None, "%s: the neck panel shows its enchant" % tag)
        check(font_text(lua, "^Agility %+5 .+ Enchanting 210") is not None, "%s: with effect, profession and skill" % tag)
        lua.execute("for _, b in ipairs(DOLL) do if b.slotKey == 'head' then b:Click() end end")

    # BiZNav: rows whose source has a place (bis/places.json) get a tooltip line and Alt + click.
    if templates:
        places = site["places"]
        check(len(places) >= 9 and all(lua.eval("R2F.BiZ.Place(%r).label" % k) == v["label"] for k, v in places.items()),
              "%s: every place from bis/places.json is in the addon" % tag)
        tagged = [r for sp in site["specs"].values() for sl in sp["slots"] if "best" in sl
                  for r in [sl["best"]] + sl.get("next", []) if "place" in r]
        check(len(tagged) > 300 and all(r["place"] in places for r in tagged), "%s: %d rows point at a known place" % (tag, len(tagged)))
        check(lua.eval("R2F.BiZ.PlaceOfItem(7684)") == "Scarlet Monastery" and lua.eval("R2F.BiZ.PlaceOfItem(6720)") is None,
              "%s: an item's place comes from its source (dungeon yes, quest no)" % tag)
        lua.execute("for _, b in ipairs(DOLL) do if b.slotKey == 'shoulder' then b:Click() end end")
        find_frames(lua, "f.__kind == 'Button' and f.optRank ~= nil and f.place ~= nil and f.__shown", "PLACED")
        check(lua.eval("#PLACED") >= 1, "%s: the shoulder list has a row with a place" % tag)
        lua.execute("PLACED[1]:Fire('OnEnter')")
        lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
        want = lua.eval("R2F.BiZ.Place(PLACED[1].place).label")
        check(any(("Alt + click: arrow to " + want) in (l or "") for l in lines), "%s: tooltip offers the arrow: %s" % (tag, lines))
        T.chat = lua.table()
        lua.execute("TEST.alt = true PLACED[1]:Click() TEST.alt = false")
        check("/way " in chat_all(lua), "%s: Alt + click without an arrow-capable map prints the /way line: %r" % (tag, chat_all(lua)))
        lua.execute(PLAN_MAPS_LUA)
        lua.execute(NAV_WORLD_LUA)
        lua.execute("R2F.Plan.ResetMapCache()")
        check(lua.eval("R2F.BiZ.Go('Gnomeregan')") == "arrow" and lua.eval("R2F.Nav.Target().label") == "Gnomeregan entrance",
              "%s: BiZ.Go points the arrow at the dungeon entrance" % tag)
        lua.execute("for _, b in ipairs(DOLL) do if b.slotKey == 'head' then b:Click() end end")

    # shift-click = link in chat
    lua.execute("TEST.shift = true; HELM[1]:Click(); TEST.shift = false")
    check("Hitem:252512" in (lua.eval("TEST.chatInsert") or ""), "%s: shift-click links the item in chat" % tag)
    lua.execute('R2F.BiZ.LinkInChat(999999, "Unknown Thing")')
    ins = lua.eval("TEST.chatInsert") or ""
    check("Hitem:999999" in ins and "[Unknown Thing]" in ins, "%s: an item the client doesn't know still gets a chat link: %r" % (tag, ins))
    # clicking another slot selects it and shows its options
    find_frames(lua, "f.__kind == 'Button' and f.slotKey == 'chest'", "CHESTBTN")
    lua.execute("CHESTBTN[1]:Click()")
    check(lua.eval("CHESTBTN[1].sel.__shown") is True and lua.eval("HEADBTN[1].sel.__shown") is False,
          "%s: clicking a slot selects it" % tag)
    find_frames(lua, "f.__kind == 'Button' and f.optRank == 1 and f.itemId == 7374 and f.__shown", "CHEST1")
    check(lua.eval("#CHEST1") == 1, "%s: the chest panel lists Chest's best pick" % tag)
    lua.execute("HEADBTN[1]:Click()")
    # wishlist switch on the helm option is on
    find_frames(lua, "f.__kind == 'CheckButton' and f.itemId == 252512 and f.__shown", "HBOX")
    check(lua.eval("#HBOX") >= 1 and lua.eval("HBOX[1]:GetChecked()") is True, "%s: wished item's switch is on" % tag)
    lua.execute("HBOX[1]:Click()")
    check(not BiZ.IsWished(252512), "%s: switching it off removes it from the wishlist" % tag)
    # filters on the tab
    find_frames(lua, "f.__kind == 'CheckButton' and f.r2fLabel and f.r2fLabel.__text == R2F.L.BIZ_TYPE_QUEST", "QBOX")
    lua.execute("QBOX[1]:SetChecked(false); QBOX[1]:Fire('OnClick')")
    find_frames(lua, "f.__kind == 'FontString' and f.__text and f.__text:find(' hidden', 1, true) and f.__shown", "HID")
    check(lua.eval("#HID") >= 1, "%s: unticking Quest reports hidden slots in the summary" % tag)
    find_frames(lua, "f.__kind == 'Button' and f.slotKey == 'legs'", "LEGSBTN")
    check(lua.eval("LEGSBTN[1].itemId") == 9509, "%s: Legs falls back to the rank 2 dungeon pick (Petrolspill Leggings)" % tag)
    lua.execute("LEGSBTN[1]:Click()")
    find_frames(lua, "f.__kind == 'Button' and f.optRank == 2 and f.itemId == 9509 and f.__shown", "STAND")
    check(lua.eval("#STAND") == 1, "%s: the legs panel lists the stand-in" % tag)
    lua.execute("STAND[1]:Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(any("From: Gnomeregan" in (l or "") for l in lines), "%s: tooltip says where it comes from: %s" % (tag, lines))
    lua.execute("QBOX[1]:SetChecked(true); QBOX[1]:Fire('OnClick')")
    # wishlist view
    find_frames(lua, "f.__kind == 'Button' and f.__text and f.__text:find('Wishlist', 1, true)", "WBTN")
    lua.execute("WBTN[1]:Click()")
    find_frames(lua, "f.__kind == 'Button' and f.itemId == 2721 and f.__shown", "WROW")
    check(lua.eval("#WROW") == 1, "%s: wishlist view lists the imported Holy Shroud" % tag)
    find_frames(lua, "f.__kind == 'Button' and f.__text == R2F.L.BIZ_EXPORT and f.__shown", "EXP")
    check(lua.eval("#EXP") == 1, "%s: Export button in the wishlist view" % tag)
    lua.execute("EXP[1]:Click()")
    check(lua.eval("R2FCopy:IsShown()") is True and lua.eval("R2FCopy.text") == BiZ.Export(), "%s: Export opens the copy box" % tag)
    find_frames(lua, "f.__kind == 'Button' and f.__text == R2F.L.BIZ_IMPORT and f.__shown", "IMP")
    lua.execute("IMP[1]:Click()")
    check(lua.eval("R2FBiZImport:IsShown()") is True, "%s: Import opens the paste box" % tag)
    # item info arriving redraws (no error)
    T.fire("GET_ITEM_INFO_RECEIVED", 999999, True)
    # slash commands
    lua.execute("R2F.MainWindow.Hide(); SlashCmdList.R2FBIZ('')")
    check(lua.eval("R2F.MainWindow.CurrentTab()") == "bis" and lua.eval("SLASH_R2FBIZ1") == "/biz" and lua.eval("SLASH_R2FBIZ2") == "/mrbiz",
          "%s: /biz opens the BiS tab" % tag)
    lua.execute("R2F.MainWindow.Hide(); SlashCmdList.R2F('bis')")
    check(lua.eval("R2F.MainWindow.CurrentTab()") == "bis", "%s: /r2f bis opens it too" % tag)

    # bad saved data is cleaned
    lua2, _ = biz_runtime(templates, preset="{ biz = { spec = 5, wish = { [1] = 'x', abc = {} , [7374] = { spec = 'hunter/survival' } } } }")
    check(lua2.eval("type(R2FCharDB.biz.spec)") == "table" and lua2.eval("R2FCharDB.biz.wish[1]") is None
          and lua2.eval("R2FCharDB.biz.wish.abc") is None and lua2.eval("R2FCharDB.biz.wish[7374].spec") == "hunter/survival",
          "%s: bad saved data cleaned, good entries kept" % tag)
    lua3, _ = biz_runtime(templates, token="DRUID")
    check(lua3.eval("R2F.BiZ.SpecId()") == "druid/feral" and lua3.eval("R2F.BiZ.Spec('druid/feral').name") == "Feral (Bear)",
          "%s: Druid opens on Feral (Bear)" % tag)



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
    check(lua.eval("R2FMain ~= nil"), "%s: main window created (flat window, no Blizzard template)" % tag)

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
    check(any("imported %d macros: %d new" % (n, n) in lua.eval("TEST.chat")[i] for i in range(1, len(lua.eval("TEST.chat")) + 1)), "chat confirms import")

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
    check(lua.eval("TIDY.__enabled") is False and lua.eval("COMBATTEXT.__shown") is True,
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
    check("R2FImport" in special and "R2FMain" in special, "windows close with Esc: %s" % special)
    new_globals = lua.eval("""(function()
      local out = {}
      for k in pairs(_G) do if not BEFORE[k] then table.insert(out, k) end end
      table.sort(out) return table.concat(out, ",") end)()""").split(",")
    allowed_exact = {"R2F", "R2FDB", "R2FCharDB", "SLASH_R2F1", "SLASH_R2FT1", "SLASH_R2FBIZ1", "SLASH_R2FBIZ2", "SLASH_R2FWAY1",
                     "TomTom"} | BINDING_GLOBALS  # TomTom = BiZNav's stand-in for Questie
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
    check(lua.eval("R2FDB.minimap.hide == true and R2FDB.minimap.lock == false and R2FDB.minimap.minimapPos == 270"),
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
    check(lua.eval("R2F.MainWindow.CurrentTab()") == "home" and lua.eval("R2F.Settings.IsShown()") is True
          and lua.eval("R2FSettings == nil"), "%s: Settings opens on the Home page" % tag)
    lua.execute("""
      CHECKS = {}
      for _, f in ipairs(TEST.allFrames) do
        if f.__kind == 'CheckButton' and f.r2fLabel then CHECKS[f.r2fLabel.__text] = f end
      end
      L = R2F.L""")
    rb = lambda key: "CHECKS[L.%s]" % key
    lua.execute("R2FDB.settings.slotsFirst = 'character' R2F.MacroBook.OptionsMenu() R2FMenu.rows[3]:Click()")
    check(lua.eval("R2FDB.settings.slotsFirst") == "account", "Options menu writes R2FDB.settings.slotsFirst")
    lua.execute('R2F.Macros.Ensure("WARRIOR/Ham")')
    check(lua.eval("#TEST.macros.acc") == 1 and lua.eval("#TEST.macros.char") == 0,
          "%s: after choosing Account first, a dragged macro is created in an account slot" % tag)
    lua.execute("R2F.MacroBook.OptionsMenu() R2FMenu.rows[2]:Click()")
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

    # Remove all through the real confirm dialog; accepted in combat -> queued.
    lua.execute('TEST.actions[1] = "Ham"')
    lua.execute("R2F.MacroBook.OptionsMenu() R2FMenu.rows[6]:Click()")
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
    lua.execute("R2F.MacroBook.OptionsMenu() R2FMenu.rows[6]:Click()")
    check(any(lua.eval("R2F.L.REMOVE_ALL_NONE") in c for c in chat_lines(lua)), "Remove all with nothing to remove just says so")

    # Esc closes the panel; one-global audit with Settings built.
    check("R2FMain" in lua_table_to_list(lua.eval("UISpecialFrames")),
          "Settings tab closes with Esc (it is part of the main window)")
    new_globals = lua.eval("""(function()
      local out = {}
      for k in pairs(_G) do if not BEFORE[k] then table.insert(out, k) end end
      table.sort(out) return table.concat(out, ",") end)()""").split(",")
    test_vars = {"SETBTN", "CHECKS", "REMOVEALL", "L", "APPLIED", "NS", "REAL_MM"}
    bad = [g for g in new_globals if g and g not in test_vars and g not in BINDING_GLOBALS
           and g not in ("SLASH_R2F1", "SLASH_R2FT1", "SLASH_R2FBIZ1", "SLASH_R2FBIZ2", "SLASH_R2FWAY1", "TomTom") and not g.startswith("R2F")]
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
    win = "R2FMain"

    # ---- Minimap button: own backend, R2F.Minimap.Apply -------------------
    check(lua.eval("R2F.Minimap.backend") == "own", "%s: no LibDBIcon loaded -> own minimap button" % tag)
    check(lua.eval("R2FMinimapButton ~= nil and R2FMinimapButton.__parent == Minimap"), "minimap button is a child of Minimap")
    check(lua.eval("R2FMinimapButton.icon.__tex") == "Interface\\AddOns\\RoadToForever\\media\\logo64",
          "minimap icon = media/logo64")
    pt = lua_table_to_list(lua.eval("R2FMinimapButton.__point"))
    import math
    want = (75 * math.cos(math.radians(270)), 75 * math.sin(math.radians(270)))
    check(pt[0] == "CENTER" and abs(pt[3] - want[0]) < 1e-6 and abs(pt[4] - want[1]) < 1e-6,
          "default minimapPos 270 puts the button on the rim (round minimap): %s" % pt)
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
                ("button", L.MENU_TALENTS), ("divider", None), ("check", L.MENU_LOCK), ("button", L.MENU_HIDE),
                ("divider", None), ("button", L.MENU_RELOAD)]
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
    # Damage meter toggle (0.63.1): only when the client has the damageMeterEnabled setting; it flips that CVar.
    check(lua.eval("(function() for _, it in ipairs(R2F.Minimap.MenuItems()) do if it.text == R2F.L.MENU_DAMAGEMETER then return true end end return false end)()") is False,
          "menu: no damage meter entry when the client has no such setting")
    lua.execute("""TEST.dm = '0' OLDGET, OLDSET = GetCVar, SetCVar
      GetCVar = function(n) if n == 'damageMeterEnabled' then return TEST.dm end return OLDGET and OLDGET(n) end
      SetCVar = function(n, v) if n == 'damageMeterEnabled' then TEST.dm = v return end if OLDSET then return OLDSET(n, v) end end""")
    lua.execute("DMI = nil for _, it in ipairs(R2F.Minimap.MenuItems()) do if it.text == R2F.L.MENU_DAMAGEMETER then DMI = it end end")
    check(lua.eval("DMI ~= nil and DMI.kind == 'check' and DMI.isChecked() == false"), "menu: a damage meter check item, unchecked while the meter is off")
    lua.execute("DMI.func()")
    check(lua.eval("TEST.dm") == "1" and lua.eval("DMI.isChecked()") is True, "menu: ticking it switches the game's damage meter on")
    lua.execute("DMI.func()")
    check(lua.eval("TEST.dm") == "0", "menu: and off again")
    lua.execute("GetCVar, SetCVar = OLDGET, OLDSET")
    # ThreatMaster toggle: only when its /tm command exists; it calls that command with no argument (what typing /tm does).
    check(lua.eval("(function() for _, it in ipairs(R2F.Minimap.MenuItems()) do if it.text == R2F.L.MENU_THREATMASTER then return true end end return false end)()") is False,
          "menu: no ThreatMaster entry when the addon is not there")
    lua.execute("""TMCALLS = {} ThreatMasterDB = { shown = true }
      SlashCmdList.THREATMASTER = function(msg) TMCALLS[#TMCALLS + 1] = msg ThreatMasterDB.shown = not ThreatMasterDB.shown end""")
    lua.execute("TMI = nil for _, it in ipairs(R2F.Minimap.MenuItems()) do if it.text == R2F.L.MENU_THREATMASTER then TMI = it end end")
    check(lua.eval("TMI ~= nil and TMI.kind == 'check' and TMI.isChecked() == true"), "menu: a ThreatMaster check item, ticked while its window is shown")
    lua.execute("TMI.func()")
    check(lua.eval("#TMCALLS") == 1 and lua.eval("TMCALLS[1]") == "" and lua.eval("TMI.isChecked()") is False,
          "menu: ticking it runs /tm (no argument) and the tick follows")
    lua.execute("SlashCmdList.THREATMASTER = nil ThreatMasterDB = nil")
    check(lua.eval("R2FDB.minimap.lock") is False, "Lock again unlocks")
    T.chat = lua.table()
    click(7)
    check(lua.eval("R2FDB.minimap.hide") is True and lua.eval("R2FMinimapButton:IsShown()") is False,
          "menu > Hide minimap button hides it")
    T.reloaded = 0
    click(9)
    check(T.reloaded == 1 and lua.eval("TEST.reloaded") == 1, "menu > Reload UI calls ReloadUI")
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
    help_lines = [h for h in lua_table_to_list(L.HELP_LINES) if not h.startswith("/r2f setup")]   # shown only where a setup is available
    chat = chat_lines(lua)
    check(len(chat) == len(help_lines) and all(c.endswith(h) for c, h in zip(chat, help_lines)), "/r2f help prints the list")
    for cmd in ("/r2f macros", "/r2ft", "/r2f talents", "/r2f minimap", "/r2f help"):
        check(any(h.startswith(cmd) or ("or " + cmd) in h for h in help_lines), "help lists " + cmd)
    check(not any(w in " ".join(help_lines) for w in ("rankdebug", "gossip", "reactlog", "auras", "profdebug", "/r2f who")),
          "/r2f help lists player commands only (troubleshooting tools are under /r2f debug)")
    T.chat = lua.table()
    slash("debug")
    debug_lines = lua_table_to_list(L.DEBUG_LINES)
    check(len(chat_lines(lua)) == len(debug_lines), "/r2f debug prints the troubleshooting list")
    T.chat = lua.table()
    slash("debug nosuchtool")
    check(any('unknown debug tool "nosuchtool"' in c for c in chat_lines(lua)), "/r2f debug with an unknown tool says so")
    T.chat = lua.table()
    slash("debug bags")
    bags_new = chat_lines(lua)
    T.chat = lua.table()
    slash("bags")
    check(bags_new != [] and chat_lines(lua) == bags_new, "/r2f debug bags and the old /r2f bags print the same")
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
    check(n == 6, "six sidebar entries")
    lua.execute("NAV = {} for _, f in ipairs(MTABS) do NAV[f.r2fKey] = f end "
                "MTABS = {NAV.home, NAV.macros, NAV.talents, NAV.plan, NAV.bis, NAV.gameplay}")
    labels = [lua.eval("MTABS[%d].r2fText.__text" % i) for i in range(1, 7)]
    check(labels == ["Home", "Macros", "Builds & talents", "Launch plan", "Gear (Mr.BiZ)", "Tweaks"],
          "sidebar labels %s" % labels)
    order = [lua.eval("R2F.MainWindow.NAV[%d].tabs[%d]" % (g, t)) for g, t in ((1, 1), (2, 1), (3, 1), (3, 2), (4, 1), (4, 2))]
    check(order == ["home", "plan", "talents", "bis", "macros", "gameplay"], "sidebar order %s" % order)
    heads = [lua.eval("R2F.MainWindow.NAV[%d].heading" % g) for g in (2, 3, 4)]
    check(heads == ["NAV_JOURNEY", "NAV_CHARACTER", "NAV_UI"], "sidebar groups: journey, character, UI: %s" % heads)
    # The launch countdown on Home.
    check(lua.eval("R2F.Home.CountdownText(R2F.Home.LAUNCH_AT - 18 * 86400 - 3600 - 44 * 60 - 5)") == "18d 01h 44m",
          "home countdown: 18 days 1 hour 44 minutes before the launch")
    check(lua.eval("R2F.Home.CountdownText(R2F.Home.LAUNCH_AT + 1)") == "Forever is live", "home countdown: after the launch it says so")
    check(lua.eval("R2F.Home.LAUNCH_AT") == 1793833200, "home countdown: the launch is 2026-11-04 23:00 UTC")
    lua.execute("MTABS[1]:Click()")
    check(MW.CurrentTab() == "home" and lua.eval("MTABS[1].r2fBar.__shown") is True and lua.eval("MTABS[2].r2fBar.__shown") is False,
          "clicking Home selects it (gold bar on the selected entry only)")
    check(lua.eval("R2FDB.settings.lastTab") == "home", "last tab saved in R2FDB.settings.lastTab")
    title = lua.eval("R2F.MainWindow.Title()")
    check(title == "Road to Forever", "Home title: %r" % title)
    lua.execute("MTABS[2]:Click()")
    title = lua.eval("R2F.MainWindow.Title()")
    check(MW.CurrentTab() == "macros" and title == "Road to Forever: Macros", "Macros tab + title")
    check(lua.eval("R2FDB.settings.lastTab") == "macros", "switching tabs saves lastTab")
    # Top bar: Reload UI, size and opacity sliders (apply on release, saved, clamped).
    lua.execute("R2F.MainWindow.Frame().r2fReload:Click()")
    check(lua.eval("TEST.reloaded") == 2, "top bar Reload UI button reloads")
    lua.execute("local sl = R2F.MainWindow.Frame().r2fSizeSlider sl:Fire('OnMouseDown') sl:SetValue(120) sl:Fire('OnValueChanged', 120) sl:Fire('OnMouseUp')")
    check(lua.eval("R2FDB.settings.menuScale") == 1.2 and lua.eval("R2FMain.__scale") == 1.2, "size slider sets the window scale")
    lua.execute("local sl = R2F.MainWindow.Frame().r2fOpacitySlider sl:Fire('OnMouseDown') sl:SetValue(40) sl:Fire('OnValueChanged', 40)")
    check(lua.eval("R2FDB.settings.menuAlpha") == 1, "opacity does not change while the thumb is held")
    lua.execute("local sl = R2F.MainWindow.Frame().r2fOpacitySlider sl:Fire('OnMouseUp')")
    check(lua.eval("R2FDB.settings.menuAlpha") == 0.4, "opacity applies on release")
    # A press away from the thumb is undone; the window never changes size.
    T.thumbOver = False
    lua.execute("local sl = R2F.MainWindow.Frame().r2fSizeSlider sl:Fire('OnMouseDown') sl:SetValue(150) sl:Fire('OnValueChanged', 150)")
    T.mouseDown = False
    lua.execute("R2F.MainWindow.Frame().r2fSizeSlider:Fire('OnUpdate', 0.1)")
    check(lua.eval("R2FDB.settings.menuScale") == 1.2 and lua.eval("R2F.MainWindow.Frame().r2fSizeSlider:GetValue()") == 120,
          "pressing the bar away from the thumb changes nothing")
    T.thumbOver = True
    # Real-client geometry: the thumb sits at left + 8 + 68 * fraction; a press 40 px away is ignored.
    cur = lua.eval("R2FDB.settings.menuScale") * 100
    thumb_x = 100 + 8 + 68 * (cur - 50) / 100
    lua.execute("R2F.MainWindow.Frame().r2fSizeSlider.__left = 100")
    for dx, expect in ((40, False), (3, True)):
        T.cursorX = thumb_x + dx
        T.mouseDown = True
        lua.execute("local sl = R2F.MainWindow.Frame().r2fSizeSlider sl:Fire('OnMouseDown') sl:SetValue(50) sl:Fire('OnValueChanged', 50)")
        check(lua.eval("R2F.MainWindow.Frame().r2fSizeSlider.r2fBlock") is (not expect), "press %+d px from the thumb %s" % (dx, "drags" if expect else "is ignored"))
        T.mouseDown = False
        lua.execute("R2F.MainWindow.Frame().r2fSizeSlider:Fire('OnUpdate', 0.1)")
        check((lua.eval("R2FDB.settings.menuScale") == cur / 100) is (not expect), "release: %s" % ("applied" if expect else "unchanged"))
        lua.execute("R2FDB.settings.menuScale = %s R2F.MainWindow.Frame().r2fSizeSlider:SetValue(%s)" % (cur / 100, cur))
    lua.execute("R2F.MainWindow.Frame().r2fSizeSlider.__left = nil")
    T.cursorX = None
    # Held thumb + cursor leaves the bar (no OnMouseUp): applied once the button is up, never while held.
    lua.execute("local sl = R2F.MainWindow.Frame().r2fSizeSlider sl:Fire('OnMouseDown') sl:SetValue(80) sl:Fire('OnValueChanged', 80)")
    T.mouseDown = True
    lua.execute("R2F.MainWindow.Frame().r2fSizeSlider:Fire('OnUpdate', 0.1)")
    check(lua.eval("R2FDB.settings.menuScale") == 1.2, "size does not change while the mouse button is held")
    T.mouseDown = False
    lua.execute("R2F.MainWindow.Frame().r2fSizeSlider:Fire('OnUpdate', 0.1)")
    check(lua.eval("R2FDB.settings.menuScale") == 0.8, "size applies once when the button is released outside the bar")
    lua.execute("R2FDB.settings.menuScale = 9 R2FDB.settings.menuAlpha = 0 R2F.Library.Init()")
    check(lua.eval("R2FDB.settings.menuScale") == 1 and lua.eval("R2FDB.settings.menuAlpha") == 1, "bad size / opacity values are reset")
    lua.execute("R2F.MainWindow.ApplyLook()")
    # Themes: default is classic, bad values fall back, every theme applies.
    check(lua.eval("R2FDB.settings.theme") == "classic", "theme defaults to classic")
    lua.execute("R2FDB.settings.theme = 'nope' R2F.Library.Init()")
    check(lua.eval("R2FDB.settings.theme") == "classic", "unknown theme falls back to classic")
    for key in ("azeroth", "obsidian", "forge", "arcane", "classic"):
        check(lua.eval("R2F.Theme.Set('%s')" % key) is True, "theme %s can be set" % key)
        lua.execute("R2F.MainWindow.ApplyLook()")
        check(lua.eval("R2FDB.settings.theme") == key, "theme %s is saved" % key)
    check(lua.eval("R2F.Theme.Set('bogus')") is False and lua.eval("R2FDB.settings.theme") == "classic",
          "setting an unknown theme is refused")
    check(lua.eval("R2F.Theme.PanelAlpha(R2F.Theme.Get('arcane'), 0.3)") >= 0.85,
          "glass theme stays readable at low opacity")
    # Text-colour pass: Classic's roles are EXACTLY the values the pages used to hardcode, and the game's own font colours.
    OLD = {"heading": (1, 0.82, 0), "body": (1, 1, 1), "dim": (0.5, 0.5, 0.5), "note": (0.7, 0.7, 0.7),
           "tagline": (0.75, 0.75, 0.75), "sub": (0.6, 0.6, 0.6), "group": (0.6, 0.6, 0.65)}
    OLD_TEX = {"accentTex": (1, 0.82, 0, 1), "thumb": (1, 1, 1, 1), "button": (1, 1, 1, 1), "tick": (0.75, 0.75, 0.78, 0.8),
               "menu": (0, 0, 0, 0.9), "edit": (0, 0, 0, 0.8), "bizBack": (0.03, 0.03, 0.05, 0.9), "highlight": (1, 1, 1, 1)}
    for role, want in list(OLD.items()) + list(OLD_TEX.items()):
        got = [lua.eval("R2F.Theme.Role(R2F.Theme.Get('classic'), '%s')[%d]" % (role, i + 1)) for i in range(len(want))]
        check(all(abs(g - w) < 1e-9 for g, w in zip(got, want)), "classic role %s equals the old hardcoded value %s: %s" % (role, want, got))
    lua.execute("R2F.Theme.Set('classic')")
    for font, role in (("R2FHeading", "heading"), ("R2FBody", "body"), ("R2FDim", "dim"), ("R2FHeadingLarge", "heading"),
                       ("R2FBodySmall", "body"), ("R2FDimSmall", "dim"), ("R2FHeadingSmall", "heading")):
        col = [lua.eval("%s.__color[%d]" % (font, i)) for i in (1, 2, 3)]
        check(all(abs(c - w) < 1e-9 for c, w in zip(col, OLD[role])), "classic font %s has the game's colour %s" % (font, OLD[role]))
    lua.execute("""PT = CreateFrame('Frame'):CreateFontString() PTX = CreateFrame('Frame'):CreateTexture()
      R2F.Theme.PaintText(PT, 'note') R2F.Theme.PaintTex(PTX, 'menu')""")
    check(abs(lua.eval("PT.__color[1]") - 0.7) < 1e-9, "painted text starts in Classic's value")
    lua.execute("R2F.Theme.Set('obsidian')")
    check(lua.eval("PT.__color[1]") != 0.7 and lua.eval("R2FBody.__color[1]") != 1 and lua.eval("R2FHeading.__color[2]") != 0.82,
          "a theme change repaints painted text and the font objects")
    lua.execute("R2F.Theme.Set('classic')")
    check(abs(lua.eval("PT.__color[1]") - 0.7) < 1e-9 and abs(lua.eval("R2FHeading.__color[2]") - 0.82) < 1e-9,
          "back to Classic restores the old values")
    # No page may go back to a hardcoded grey / white / gold text colour or a font that ignores the theme.
    import re as _re
    ui_dir = os.path.join(HERE, "..", "RoadToForever", "UI")
    bad = []
    for fname in sorted(os.listdir(ui_dir)):
        if not fname.endswith(".lua"):
            continue
        src = open(os.path.join(ui_dir, fname), encoding="utf-8").read()
        for m in _re.finditer(r":SetTextColor\((?:1, 0\.82, 0|1, 1, 1|0\.5, 0\.5, 0\.5|0\.7, 0\.7, 0\.7|0\.75, 0\.75, 0\.75|0\.6, 0\.6, 0\.6|0\.6, 0\.6, 0\.65)\)", src):
            bad.append("%s: %s" % (fname, m.group(0)))
        for m in _re.finditer(r"\"(GameFont(?:Normal|Highlight|Disable)[A-Za-z]*)\"", src):
            bad.append("%s: %s" % (fname, m.group(0)))
    check(not bad, "no hardcoded text colours or game fonts left in UI/*.lua: %s" % bad[:5])
    # Azeroth Reforged decoration (UI/Deco.lua) and its bundled fonts. First the code-drawn look (no image slices).
    lua.execute("R2F.Images.azeroth = false R2F.Theme.Set('azeroth')")
    D = "R2FMain.r2fDeco"
    check(lua.eval("%s.panel:IsShown()" % D) is True and lua.eval("%s.bannerEdge:IsShown()" % D) is True
          and lua.eval("%s.gems[1].gem:IsShown()" % D) is True and lua.eval("%s.frameInner[1]:IsShown()" % D) is True,
          "azeroth: panel, banner, corner gems and the inner frame line are drawn")
    check(lua.eval("R2FMain.r2fBgTex:IsShown()") is False, "azeroth: the flat panel colour is replaced by the gradient panel")
    check(all(lua.eval("%s.nav.%s.grad:IsShown()" % (D, k)) is True for k in ("home", "plan", "talents", "bis", "macros", "gameplay")),
          "azeroth: every navigation button has its stone gradient")
    check(lua.eval("R2FMain.r2fTitle.__point[2] == %s.bannerEdge" % D) is True, "azeroth: the title sits on the banner")
    # Then the image look: the exported slices (media/azeroth) replace the rectangles.
    lua.execute("R2F.Images.azeroth = true R2F.Theme.Set('azeroth')")
    IM = "R2FMain.r2fDeco.img"
    check(lua.eval("%s.panel:IsShown()" % IM) is True and lua.eval("%s.banner:IsShown()" % IM) is True
          and all(lua.eval("%s.frameArt.parts[%d]:IsShown()" % (IM, k)) is True for k in range(1, 9))
          and all(lua.eval("%s.crest.parts[%d]:IsShown()" % (IM, k)) is True for k in (1, 2, 3)),
          "azeroth with images: tiles, the ornate frame and the crest are drawn")
    check(lua.eval("%s.panel:IsShown()" % D) is False and lua.eval("%s.bannerEdge:IsShown()" % D) is False
          and lua.eval("R2FMain.r2fRimLines[1]:IsShown()") is False,
          "azeroth with images: the rectangle look and the plain rim line are hidden")
    check(lua.eval("R2FMain.r2fTitle.__point[2] == %s.banner" % IM) is True, "azeroth with images: the title sits on the banner image")
    cur = lua.eval("R2F.MainWindow.CurrentTab()")
    other = "macros" if cur != "macros" else "home"
    check("btn_selected" in lua.eval("%s.nav.%s.bar.parts[2].__tex" % (IM, cur)) and "gem_on" in lua.eval("%s.nav.%s.gem.__tex" % (IM, cur))
          and "btn_normal" in lua.eval("%s.nav.%s.bar.parts[2].__tex" % (IM, other)) and "gem_off" in lua.eval("%s.nav.%s.gem.__tex" % (IM, other)),
          "azeroth with images: the selected sidebar button (%s) and its gem are lit, the others are not" % cur)
    check(len(lua_table_to_list(lua.eval("R2FMain.r2fDeco.img.sliders"))) == 2, "azeroth with images: both top-bar sliders are re-skinned")
    check(all(lua.eval("%s.nav.%s.icon:IsShown()" % (IM, k)) is True for k in ("home", "plan", "talents", "bis", "macros", "gameplay")),
          "azeroth with images: every sidebar button has its icon")
    check(all(lua.eval("%s.heads[%d].word:IsShown()" % (IM, k)) is True for k in (1, 2, 3)),
          "azeroth with images: the three group headings are the letter-spaced images")
    check(lua.eval("(R2F.Home.CountdownParts(R2F.Home.LAUNCH_AT - 18 * 86400 - 3600 - 44 * 60 - 5))") == 18,
          "home countdown parts: 18 days")
    check(lua.eval("(select(3, R2F.Home.CountdownParts(R2F.Home.LAUNCH_AT - 18 * 86400 - 3600 - 44 * 60 - 5)))") == 44,
          "home countdown parts: 44 minutes")
    check(lua.eval("(select(4, R2F.Home.CountdownParts(R2F.Home.LAUNCH_AT + 5)))") is True, "home countdown parts: live after the launch")
    lua.execute("R2F.Home.UpdateCountdown()")
    check(lua.eval("R2F.Deco ~= nil") is True, "decoration module present")
    lua.execute("R2F.Theme.Set('obsidian')")
    check(lua.eval("%s.panel:IsShown()" % IM) is False and lua.eval("%s.banner:IsShown()" % IM) is False
          and lua.eval("%s.nav.home.bar.parts[1]:IsShown()" % IM) is False, "another theme hides every image piece again")
    import re as _re
    deco_src = open(os.path.join(HERE, "..", "RoadToForever", "UI", "Deco.lua"), encoding="utf-8").read()
    # Ember & Iron: the cut-corner steel look, with the sidebar as a 2 x 3 grid of 64 px tiles.
    lua.execute("R2F.Images.ember = true R2F.Theme.Set('forge')")
    EMI = "R2FMain.r2fDeco.em"
    check(lua.eval("%s.panel:IsShown()" % EMI) is True and lua.eval("%s.heat:IsShown()" % EMI) is True
          and all(lua.eval("%s.frame.parts[%d]:IsShown()" % (EMI, k)) is True for k in range(1, 9))
          and all(lua.eval("%s.rivets[%d]:IsShown()" % (EMI, k)) is True for k in (1, 2, 3, 4)),
          "ember: panel, heat strip, eight frame pieces and four rivets are drawn")
    check(lua.eval("R2FMain.r2fDeco.img.banner:IsShown()") is False and lua.eval("%s.panel:IsShown()" % D) is False,
          "ember: none of the Azeroth pieces show")
    check(all(lua.eval("%s.nav.%s.slot:IsShown()" % (EMI, k)) is True for k in ("home", "plan", "talents", "bis", "macros", "gameplay")),
          "ember: every sidebar button is an icon tile")
    check(lua.eval("NAV.plan.r2fText.__text") == "PLAN" and lua.eval("NAV.bis.r2fText.__text") == "GEAR",
          "ember: the tiles carry the short upper-case labels")
    check(lua.eval("R2F.Theme.Get().deco") == "ember" and "BarlowCondensed" in lua.eval("R2F.Theme.Get().font.heading"),
          "ember: Barlow Condensed for headings")
    check(lua.eval("R2FMain:GetWidth()") == 1010 and lua.eval("R2FMain.r2fClose:IsShown()") is True
          and lua.eval("R2FMain.r2fSizeSlider.r2fTicks[1]:IsShown()") is False
          and lua.eval("%s.card.parts[1]:IsShown()" % EMI) is True and lua.eval("%s.gaugeHead:IsShown()" % EMI) is True,
          "ember: a wide window, our own close button, the title card and the gauge panel, sliders without tick marks")
    check(lua.eval("R2FMain.r2fSide:GetWidth()") == 300, "ember: the sidebar is 300 px wide")
    lua.execute("R2F.MainWindow.SelectTab('plan')")
    check(lua.eval("%s.cardTitle.__text" % EMI) == "LAUNCH PLAN" and "launch plan" in lua.eval("%s.cardDesc.__text" % EMI).lower(),
          "ember: the title card follows the page")
    lua.execute("R2F.Theme.Set('azeroth')")
    check(lua.eval("%s.panel:IsShown()" % EMI) is False and lua.eval("NAV.plan.r2fText.__text") == "Launch plan",
          "back to Azeroth: the ember pieces are gone and the sidebar names are back")
    check(lua.eval("R2FMain:GetWidth()") == 980 and lua.eval("%s.gaugeHead:IsShown()" % EMI) is False,
          "back to Azeroth: its own width, no gauge panel")
    lua.execute("R2F.Theme.Set('classic')")
    check(lua.eval("NAV.talents.r2fText.__text") == "Builds & talents" and lua.eval("%s.panel:IsShown()" % EMI) is False,
          "classic: list sidebar again, nothing of ember left")
    # Every texture file the ember look names exists.
    emnames = set(_re.findall(r'EM \.\. "([a-z_]+)"', deco_src)) | set(_re.findall(r'EM \.\. \(sel and "([a-z_]+)"', deco_src))
    emnames |= {"slot_normal", "slot_hover", "slot_on", "display", "switch_knob_on", "switch_knob_off", "slider_fill", "slider_track", "slider_knob",
                "btn_normal", "btn_hover", "btn_primary", "btn_primary_hover", "btn_disabled", "check_on", "check_off", "switch_on", "switch_off"}
    emmissing = [n for n in sorted(emnames) if not os.path.exists(os.path.join(HERE, "..", "RoadToForever", "media", "ember", "ember_" + n + ".tga"))]
    check(not emmissing, "every ember texture exists as a .tga in media/ember: %s" % emmissing)
    fontsdir = os.path.join(HERE, "..", "RoadToForever", "media", "fonts")
    check(all(os.path.exists(os.path.join(fontsdir, f)) for f in ("BarlowCondensed-Bold.ttf", "Barlow-Medium.ttf", "ChakraPetch-Bold.ttf",
                                                                  "OFL-BarlowCondensed.txt", "OFL-Barlow.txt", "OFL-ChakraPetch.txt")),
          "the Ember & Iron fonts ship with their licence files")
    lua.execute("R2F.Images.azeroth = true")
    # Obsidian Night: the sidebar becomes a strip of tabs, the window 44 px taller, the pages move up and sideways.
    lua.execute("R2F.Images.obsidian = true R2F.Theme.Set('obsidian')")
    OBI = "R2FMain.r2fDeco.ob"
    check(all(lua.eval("%s.frame.parts[%d]:IsShown()" % (OBI, k)) is True for k in range(1, 9))
          and all(lua.eval("%s.plate.parts[%d]:IsShown()" % (OBI, k)) is True for k in range(1, 10))
          and lua.eval("%s.rule:IsShown()" % OBI) is True, "obsidian: rounded frame, card behind the pages and the line under the tabs are drawn")
    check(lua.eval("R2FMain.r2fBgTex:IsShown()") is True, "obsidian: the flat window colour stays (the frame art is border only)")
    check(lua.eval("R2FMain.r2fSide:IsShown()") is False, "obsidian: no sidebar background")
    check(lua.eval("NAV.plan.r2fText.__text") == "Launch plan" and lua.eval("NAV.talents.r2fText.__text") == "Builds",
          "obsidian: tab names")
    check(all(lua.eval("%s.nav.%s.icon:IsShown()" % (OBI, k)) is True for k in ("home", "plan", "talents", "bis", "macros", "gameplay")),
          "obsidian: every tab has its icon")
    check(len(lua_table_to_list(lua.eval("R2F.MainWindow.NavSeparators()"))) == 2, "obsidian: two separators between the tab groups")
    check(lua.eval("R2FMain.r2fDeco.img.banner:IsShown()") is False and lua.eval("%s.panel:IsShown()" % EMI) is False,
          "obsidian: nothing of Azeroth or Ember shows")
    check(lua.eval("R2FMain:GetWidth()") == 960 and lua.eval("R2FMain.r2fClose:IsShown()") is True
          and all(lua.eval("%s.topbar.parts[%d]:IsShown()" % (OBI, k)) is True for k in (1, 2, 3))
          and all(lua.eval("%s.footer.parts[%d]:IsShown()" % (OBI, k)) is True for k in (1, 2, 3)),
          "obsidian: a wider window, our own close button, the top bar and the footer strip")
    lua.execute("R2F.Theme.Set('classic')")
    check(lua.eval("%s.frame.parts[1]:IsShown()" % OBI) is False and lua.eval("R2FMain.r2fSide:IsShown()") is True
          and lua.eval("NAV.talents.r2fText.__text") == "Builds & talents", "classic after obsidian: sidebar and names are back")
    obsnames = set(_re.findall(r'OB \.\. "([a-z_]+)"', deco_src)) | set(_re.findall(r'OB \.\. \(sel and "([a-z_]+)"', deco_src))
    obsnames |= {"btn_normal", "btn_hover", "btn_primary", "btn_primary_hover", "btn_disabled", "check_on", "check_off", "switch_on", "switch_off",
                 "switch_knob_on", "switch_knob_off", "slider_track", "slider_fill", "slider_knob", "display"}
    obsmissing = [n for n in sorted(obsnames) if not os.path.exists(os.path.join(HERE, "..", "RoadToForever", "media", "obsidian", "obsidian_" + n + ".tga"))]
    check(not obsmissing, "every obsidian texture exists as a .tga in media/obsidian: %s" % obsmissing)
    check(all(os.path.exists(os.path.join(fontsdir, f)) for f in ("SpaceGrotesk-Medium.ttf", "JetBrainsMono-Bold.ttf", "OFL-SpaceGrotesk.txt", "OFL-JetBrainsMono.txt")),
          "the Obsidian Night fonts ship with their licence files")
    lua.execute("R2F.Images.azeroth = true")
    # Frost & Void: starfield window, glass panels and a chain of round orbs in place of the sidebar list.
    lua.execute("R2F.Images.frost = true R2F.Theme.Set('arcane')")
    FRI = "R2FMain.r2fDeco.fr"
    check(lua.eval("%s.panel:IsShown()" % FRI) is True and lua.eval("%s.shade:IsShown()" % FRI) is True
          and lua.eval("%s.glowV:IsShown()" % FRI) is True and lua.eval("%s.glowC:IsShown()" % FRI) is True
          and all(lua.eval("%s.frame.parts[%d]:IsShown()" % (FRI, k)) is True for k in range(1, 9))
          and all(lua.eval("%s.glass.parts[%d]:IsShown()" % (FRI, k)) is True for k in range(1, 10)),
          "frost: starfield, shade, both glows, the rounded frame and the glass panel are drawn")
    check(all(lua.eval("%s.nav.%s.orb:IsShown()" % (FRI, k)) is True for k in ("home", "plan", "talents", "bis", "macros", "gameplay"))
          and lua.eval("%s.link:IsShown()" % FRI) is True, "frost: every sidebar button is an orb on the chain")
    check(lua.eval("NAV.plan.r2fText.__text") == "Launch plan" and lua.eval("R2FMain.r2fSide:IsShown()") is False,
          "frost: the names stay, the sidebar background is gone")
    check(lua.eval("R2F.Theme.PanelAlpha(R2F.Theme.Get('arcane'), 0.3)") >= 0.85, "frost: stays nearly opaque at the lowest opacity")
    check(lua.eval("%s.panel:IsShown()" % EMI) is False and lua.eval("R2FMain.r2fDeco.img.banner:IsShown()") is False,
          "frost: nothing of Ember or Azeroth shows")
    check(lua.eval("R2FMain:GetWidth()") == 960 and lua.eval("R2FMain.r2fClose:IsShown()") is True
          and lua.eval("R2FMain.CloseButton:IsShown()") is False,
          "frost: a wider window with our own close button instead of the game's")
    check(lua.eval("R2FMain.r2fSizeSlider.r2fTicks[1]:IsShown()") is False, "frost: Size and Opacity have no tick marks")
    lua.execute("R2FMain.r2fClose:Fire('OnClick')")
    check(lua.eval("R2FMain:IsShown()") is False, "frost: our close button hides the window")
    lua.execute("R2F.MainWindow.Show('home')")
    lua.execute("R2F.Theme.Set('classic')")
    check(lua.eval("%s.panel:IsShown()" % FRI) is False and lua.eval("R2FMain.r2fSide:IsShown()") is True,
          "classic after frost: sidebar background is back, nothing of frost left")
    check(lua.eval("R2FMain:GetWidth()") == 820 and lua.eval("R2FMain.r2fClose:IsShown()") is False
          and lua.eval("R2FMain.CloseButton:IsShown()") is True and lua.eval("R2FMain.r2fSizeSlider.r2fTicks[1]:IsShown()") is True,
          "classic after frost: the original width, the game's close button and the tick marks are back")
    frnames = set(_re.findall(r'FR \.\. "([a-z_]+)"', deco_src)) | set(_re.findall(r'FR \.\. \(sel and "([a-z_]+)"', deco_src))
    frnames |= {"orb_hover", "orb_on", "orb_normal", "btn_normal", "btn_hover", "btn_primary", "btn_primary_hover", "btn_disabled", "check_on",
                "check_off", "switch_on", "switch_off", "switch_knob_on", "switch_knob_off", "slider_track", "slider_fill", "slider_knob", "display"}
    frmissing = [n for n in sorted(frnames) if not os.path.exists(os.path.join(HERE, "..", "RoadToForever", "media", "frost", "frost_" + n + ".tga"))]
    check(not frmissing, "every frost texture exists as a .tga in media/frost: %s" % frmissing)
    check(all(os.path.exists(os.path.join(fontsdir, f)) for f in ("Sora-Regular.ttf", "Sora-SemiBold.ttf", "OFL-Sora.txt")),
          "the Frost & Void fonts ship with their licence file")
    # Scribe's Tome (light): leather cover, two pages, the sidebar as a table of contents.
    lua.execute("R2F.Images.scribe = true R2F.Theme.Set('scribe')")
    SCI = "R2FMain.r2fDeco.sc"
    check(lua.eval("R2FMain:GetWidth()") == 1060 and lua.eval("R2FMain.r2fSide:GetWidth()") == 396
          and lua.eval("R2FMain.r2fSide:IsShown()") is False, "scribe: a book-wide window, no sidebar background")
    check(all(lua.eval("%s.cover.parts[%d]:IsShown()" % (SCI, k)) is True for k in range(1, 9))
          and all(lua.eval("%s.pageL.parts[%d]:IsShown()" % (SCI, k)) is True for k in range(1, 10))
          and lua.eval("%s.spine:IsShown()" % SCI) is True and lua.eval("%s.contents:IsShown()" % SCI) is True,
          "scribe: cover, both pages, spine and the Contents heading are drawn")
    check(all(lua.eval("%s.nav.%s.leader:IsShown()" % (SCI, k)) is True and lua.eval("%s.nav.%s.num:IsShown()" % (SCI, k)) is True
              for k in ("home", "plan", "talents", "bis", "macros", "gameplay")), "scribe: every contents line has a leader and a page number")
    check(lua.eval("%s.nav.home.marker:IsShown()" % SCI) is not lua.eval("%s.nav.plan.marker:IsShown()" % SCI),
          "scribe: only the open page has the bookmark")
    check(lua.eval("R2FMain.r2fClose:IsShown()") is True, "scribe: our own close button")
    lua.execute("R2F.Theme.Set('classic')")
    check(lua.eval("%s.contents:IsShown()" % SCI) is False and lua.eval("%s.cover.parts[1]:IsShown()" % SCI) is False
          and lua.eval("R2FMain:GetWidth()") == 820 and lua.eval("R2FMain.r2fSide:IsShown()") is True,
          "classic after scribe: nothing of the book is left")
    # Gnomish Workshop (light): cream window, coloured tabs along the top.
    lua.execute("R2F.Images.gnomish = true R2F.Theme.Set('gnomish')")
    GNI = "R2FMain.r2fDeco.gn"
    check(lua.eval("R2FMain:GetWidth()") == 1000 and lua.eval("R2FMain.r2fSide:IsShown()") is False
          and all(lua.eval("%s.frame.parts[%d]:IsShown()" % (GNI, k)) is True for k in range(1, 10))
          and all(lua.eval("%s.plate.parts[%d]:IsShown()" % (GNI, k)) is True for k in range(1, 10)),
          "gnomish: a cream window with the page the tabs sit on")
    lua.execute("R2F.MainWindow.SelectTab('plan')")
    check(lua.eval("%s.nav.plan.bg.parts[1].__tex" % GNI).endswith("gnomish_tab_active")
          and lua.eval("%s.nav.talents.bg.parts[1].__tex" % GNI).endswith("gnomish_tab_coral")
          and lua.eval("%s.nav.home.bg.parts[1].__tex" % GNI).endswith("gnomish_tab_cyan"),
          "gnomish: the open tab is cream, the others keep their colours")
    check(lua.eval("R2FMain.r2fClose:IsShown()") is True and lua.eval("R2F.Theme.Get().close") == "round", "gnomish: our own round close button")
    lua.execute("R2F.Theme.Set('classic')")
    check(lua.eval("%s.frame.parts[1]:IsShown()" % GNI) is False and lua.eval("R2FMain:GetWidth()") == 820,
          "classic after gnomish: nothing of the toy window is left")
    book_src = open(os.path.join(HERE, "..", "RoadToForever", "UI", "DecoBook.lua"), encoding="utf-8").read()
    toy_src = open(os.path.join(HERE, "..", "RoadToForever", "UI", "DecoToy.lua"), encoding="utf-8").read()
    home_src = open(os.path.join(HERE, "..", "RoadToForever", "UI", "Home.lua"), encoding="utf-8").read()
    scnames = set(_re.findall(r'SC \.\. "([a-z_]+)"', book_src)) | {"seal_red", "seal_green"}
    scnames |= {"btn_seal", "btn_seal_hover", "btn_stamp", "btn_stamp_hover", "btn_off", "check_on", "check_off", "switch_on", "switch_off",
                "switch_knob_on", "switch_knob_off", "slider_track", "slider_fill", "slider_knob", "close_normal", "close_hover"}
    scmissing = [n for n in sorted(scnames) if not os.path.exists(os.path.join(HERE, "..", "RoadToForever", "media", "scribe", "scribe_" + n + ".tga"))]
    check(not scmissing, "every scribe texture exists as a .tga in media/scribe: %s" % scmissing)
    gnnames = {n for n in _re.findall(r'GN \.\. "([a-z_]+)"', toy_src) if not n.endswith("_")} | {"tab_" + c for c in ("active", "cyan", "yellow", "coral", "green", "purple", "orange")}
    gnnames |= {"card_" + c for c in ("blue", "yellow", "green", "pink", "white")}
    gnnames |= {"btn_primary", "btn_primary_hover", "btn_normal", "btn_normal_hover", "btn_off", "check_on", "check_off", "switch_on", "switch_off",
                "switch_knob_on", "switch_knob_off", "slider_track", "slider_fill", "slider_knob", "close_normal", "close_hover"}
    gnmissing = [n for n in sorted(gnnames) if not os.path.exists(os.path.join(HERE, "..", "RoadToForever", "media", "gnomish", "gnomish_" + n + ".tga"))]
    check(not gnmissing, "every gnomish texture exists as a .tga in media/gnomish: %s" % gnmissing)
    check(all(os.path.exists(os.path.join(fontsdir, f)) for f in ("CormorantGaramond-SemiBold.ttf", "OFL-CormorantGaramond.txt",
                                                                    "Baloo2-Bold.ttf", "Nunito-SemiBold.ttf", "OFL-Baloo2.txt", "OFL-Nunito.txt")),
          "the Scribe's Tome and Gnomish Workshop fonts ship with their licence files")
    # The "Choose a look" gallery: preview, keep, revert, surprise.
    lua.execute("R2F.Theme.Set('classic') R2F.ThemePicker.Show()")
    PKF = "R2F.ThemePicker.Frame()"
    check(lua.eval("%s:IsShown()" % PKF) is True, "picker: the gallery opens")
    check(lua.eval("R2F.Theme.Get().key") == "classic", "picker: nothing changes until a card is clicked")
    lua.execute("R2F.ThemePicker.Preview('arcane')")
    check(lua.eval("R2F.Theme.Get().key") == "arcane", "picker: a card click tries the look on the window at once")
    lua.execute("R2F.ThemePicker.Preview('classic')")
    check(lua.eval("R2F.Theme.Get().key") == "classic", "picker: clicking the old look during a preview goes back")
    lua.execute("R2F.ThemePicker.Preview('forge')")
    lua.execute("%s:Hide()" % PKF)
    check(lua.eval("R2F.Theme.Get().key") == "classic", "picker: closing the gallery while trying a look puts the old one back")
    lua.execute("R2F.ThemePicker.Show() R2F.ThemePicker.Preview('forge')")
    lua.execute("R2F.ThemePicker.Frame():Hide() R2F.ThemePicker.Show()")
    lua.execute("R2F.ThemePicker.Preview('forge')")
    lua.execute("R2F.ThemePicker.Surprise()")
    check(lua.eval("R2F.Theme.Get().key") not in ("classic", "forge"), "picker: Surprise me tries another look")
    lua.execute("R2F.Theme.Set('classic')")
    pk_src = open(os.path.join(HERE, "..", "RoadToForever", "UI", "ThemePicker.lua"), encoding="utf-8").read()
    pknames = set(_re.findall(r'PK \.\. "([a-z_]+)"', pk_src))
    pkmissing = [n for n in sorted(pknames) if not os.path.exists(os.path.join(HERE, "..", "RoadToForever", "media", "picker", "picker_" + n + ".tga"))]
    check(len(pknames) >= 12 and not pkmissing, "every gallery texture exists as a .tga in media/picker: %s" % pkmissing)
    pk_other = _re.findall(r'IMG \.\. "([a-z]+)\\\\([a-z_0-9]+)"', pk_src)
    pk_other_missing = [a + "/" + b for a, b in pk_other if not b.endswith("_") and not os.path.exists(os.path.join(HERE, "..", "RoadToForever", "media", a, b + ".tga"))]
    check(len(pk_other) >= 14 and not pk_other_missing, "every look's art the gallery borrows exists: %s" % pk_other_missing)
    # The gallery wears the look in use, and changes with it.
    lua.execute("R2F.Images.gnomish = true R2F.Images.frost = true R2F.Theme.Set('gnomish') R2F.ThemePicker.Show()")
    check(lua.eval("R2F.ThemePicker.Frame():IsShown()") is True, "picker: opens under the gnomish look")
    lua.execute("R2F.Theme.Set('arcane')")
    check(lua.eval("R2F.ThemePicker.Frame():IsShown()") is True, "picker: stays open when the look changes")
    lua.execute("R2F.Theme.Set('classic') R2F.ThemePicker.Frame():Hide()")
    lua.execute("R2F.Images.azeroth = true")
    # A long window title is scaled to fit the crest (250 px) in image mode.
    lua.execute("""R2F.Images.azeroth = true R2F.Theme.Set('azeroth') TSCALE = nil
      R2FMain.r2fTitle.GetStringWidth = function() return 300 end
      R2FMain.r2fTitle.SetScale = function(self, v) TSCALE = v end
      R2F.Deco.FitTitle(R2FMain)""")
    check(abs(lua.eval("TSCALE") - 250 / 300.0) < 1e-6, "azeroth with images: a long title is scaled to fit the banner plate")
    lua.execute("R2FMain.r2fTitle.GetStringWidth = nil R2FMain.r2fTitle.SetScale = nil")
    lua.execute("R2F.Images.azeroth = false R2F.Theme.Set('azeroth')")
    check(lua.eval("%s.panel:IsShown()" % D) is True and lua.eval("%s.panel:IsShown()" % IM) is False,
          "without the image flag Azeroth falls back to the rectangle look")
    # The flag is only on when every texture the code names exists as a game texture.
    import re as _re
    deco_src = open(os.path.join(HERE, "..", "RoadToForever", "UI", "Deco.lua"), encoding="utf-8").read()
    names = set(_re.findall(r'"(azeroth_[a-z_]+)"', deco_src)) | set(_re.findall(r'IMG \.\. \(sel and "(azeroth_[a-z_]+)" or', deco_src))
    names |= set(_re.findall(r'"(azeroth_[a-z_]+)"\)', deco_src))
    names = {n for n in names if not n.endswith("_")}
    names |= {"azeroth_icon_" + n for n in _re.findall(r'= "([a-z]+)"', deco_src[deco_src.index("local NAV_ICON"):deco_src.index("-- The group heading images")])}
    missing = [n for n in sorted(names) if not os.path.exists(os.path.join(HERE, "..", "RoadToForever", "media", "azeroth", n + ".tga"))]
    check(not missing, "every azeroth texture named in Deco.lua exists as a .tga in media/azeroth: %s" % missing)
    lua.execute("R2F.Images.azeroth = true")
    lua.execute("R2F.Theme.Set('obsidian')")
    check(lua.eval("%s.panel:IsShown()" % D) is False and lua.eval("%s.bannerEdge:IsShown()" % D) is False
          and lua.eval("%s.nav.home.grad:IsShown()" % D) is False and lua.eval("R2FMain.r2fBgTex:IsShown()") is True,
          "another theme hides all of the azeroth decoration again")
    lua.execute("R2F.Theme.Set('classic')")
    check(lua.eval("%s.insetEdge:IsShown()" % D) is False, "classic shows none of the decoration")
    # Fonts: azeroth swaps the face of OUR font objects only; a refused file puts the game's font back.
    lua.execute("""FONTCALLS = {} FONTOK = true
      for _, n in ipairs({ 'GameFontNormal', 'GameFontNormalLarge', 'GameFontNormalSmall', 'GameFontHighlight', 'GameFontHighlightSmall',
                           'GameFontDisable', 'GameFontDisableSmall' }) do _G[n].GetFont = function() return 'GAME.ttf', 12, '' end end
      for _, n in ipairs({ 'R2FHeading', 'R2FHeadingLarge', 'R2FHeadingSmall', 'R2FBody', 'R2FBodySmall', 'R2FDim', 'R2FDimSmall' }) do
        _G[n].SetFont = function(self, file, size, flags) FONTCALLS[n] = { file, size } return FONTOK end
        _G[n].SetFontObject = function(self, parent) FONTCALLS[n] = { 'parent' } end
      end
      R2F.Theme.Set('azeroth')""")
    check("Cinzel" in lua.eval("FONTCALLS.R2FHeading[1]") and lua.eval("FONTCALLS.R2FHeading[2]") == 12,
          "azeroth: headings use the bundled Cinzel at the game font's size")
    check("AlegreyaSans" in lua.eval("FONTCALLS.R2FBody[1]") and lua.eval("FONTCALLS.R2FBody[2]") == 13,
          "azeroth: body text uses the bundled Alegreya Sans, one point larger")
    lua.execute("FONTOK = false FONTCALLS = {} R2F.Theme.Set('obsidian') R2F.Theme.Set('azeroth')")
    check(lua.eval("FONTCALLS.R2FBody[1]") == "parent", "a font file the game refuses falls back to the game's own font")
    lua.execute("FONTCALLS = {} R2F.Theme.Set('classic')")
    check(lua.eval("FONTCALLS.R2FBody[1]") == "parent" and lua.eval("FONTCALLS.R2FHeading[1]") == "parent",
          "classic puts the game's fonts back")
    fonts_dir = os.path.join(HERE, "..", "RoadToForever", "media", "fonts")
    check(all(os.path.exists(os.path.join(fonts_dir, f)) for f in ("Cinzel-Variable.ttf", "AlegreyaSans-Regular.ttf",
                                                                 "OFL-Cinzel.txt", "OFL-AlegreyaSans.txt")),
          "the bundled fonts ship with their licence files")
    # The rim: classic keeps Blizzard's dialog border (no extra lines); the others hide it and draw a thin coloured line.
    lua.execute("R2F.Theme.Set('classic')")
    check(lua.eval("R2FMain.r2fRimLines[1]:IsShown()") is False, "classic: no extra rim line")
    lua.execute("R2F.Images.obsidian = false R2F.Theme.Set('obsidian')")        # the drawn look, without the image slices
    check(all(lua.eval("R2FMain.r2fRimLines[%d]:IsShown()" % i) is True for i in (1, 2, 3, 4)),
          "obsidian: the thin rim line is drawn on all four sides")
    check(lua.eval("R2FDB.settings.theme") == "obsidian", "Theme.Set recolours the window by itself (MainWindow listens)")
    lua.execute("R2F.Theme.Set('classic')")
    # Theme.Get is safe before the library exists, and Set refuses to run without it.
    lua.execute("SAVED = R2F.Library.db R2F.Library.db = nil")
    check(lua.eval("R2F.Theme.Get().key") == "classic" and lua.eval("R2F.Theme.Set('azeroth')") is False,
          "Theme.Get falls back to classic and Set is refused before the library has loaded")
    lua.execute("R2F.Library.db = SAVED")
    lua.execute("MTABS[3]:Click()")
    check(MW.CurrentTab() == "talents" and lua.eval("R2F.MacroBook.IsShown()") is False, "Talents tab hides the book")
    # Step 9 replaced the placeholder with the real tab (tested in test_talent_preview).
    check(find_frames(lua, "f.__kind == 'Button' and f.__text == R2F.L.BTN_LOAD_LINK", "TT") == 1
          and lua.eval("R2F.L.TALENTS_TAB_LATER") is None, "Talents tab has its Load button, no placeholder")
    check(lua.eval("R2FMain.r2fLogo.__tex") == "Interface\\AddOns\\RoadToForever\\media\\logo128",
          "top bar logo = media/logo128")
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
    check(lua.eval("#HOME") == 1 and lua.eval("HOME[1].tab") == "plan", "Home has one entry: the launch plan (Phase 2)")
    check(lua.eval("R2F.Home.MacroLine()") == "%d macros in your library, 2 on your bars" % total,
          "Home macro line: %r" % lua.eval("R2F.Home.MacroLine()"))
    TL = lua.eval("R2F.Home.TalentLine")
    check(TL() == "No free talent points", "Talent points line with no free points")
    T.talentPoints = 5
    check(TL() == "5 free talent points", "Talent points line: 5 free talent points")
    T.talentPoints = 1
    check(TL() == "1 free talent point", "Talent points line: 1 free talent point")
    T.talentPoints = 0
    lua.execute("R2F.MainWindow.SelectTab('talents') R2F.TalentPanel.Refresh()")
    find_frames(lua, "f.__kind == 'FontString' and f.__text == '0 of 51 points spent, 51 left.'", "TPTS")
    check(lua.eval("#TPTS") >= 1, "the Talents page shows the sandbox points line")
    lua.execute('TEST.actions[80] = nil')
    T.fire("ACTIONBAR_SLOT_CHANGED")
    T.runTimers()
    check(lua.eval("R2F.Home.MacroLine()").endswith(", 1 on your bars"), "macro count follows ACTIONBAR_SLOT_CHANGED")
    lua.execute("R2F.Library.db.library = {} R2F.Library.Apply({ { id = 'ANY/Zoom', class = 'ANY', section = 'Universal',"
                " group = 'Misc / UI', name = 'Zoom', short = 'Zoom', body = '/x' } }, 1)")
    check(lua.eval("R2F.Home.MacroLine()").startswith("1 macro in your library"), "singular wording for 1 macro")
    lua.eval("R2F.Library.Apply")(res.records, 1)
    lua.execute("R2F.MainWindow.SelectTab('home') HOME[1]:Click()")
    check(MW.CurrentTab() == "plan", "clicking the plan entry switches to the Plan tab")

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
    check(lua.eval("TEST.menu ~= nil and #TEST.menu == 9"), "LDB OnClick right = the menu")
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
    # A lone backslash before a letter in a Lua string is silently dropped by Lua 5.1 ("Interface\Icons" with one
    # backslash becomes "InterfaceIcons", a missing texture). Every path must use "\\".
    bad = []
    for root, _, files in os.walk(ADDON):
        for fn in files:
            if fn.endswith(".lua"):
                with open(os.path.join(root, fn), encoding="utf-8") as fh:
                    for no, line in enumerate(fh, 1):
                        code = line.split("--", 1)[0]
                        for lit in re.findall(r'"((?:[^"\\]|\\.)*)"', code):
                            if any(c not in "abfnrtv\\\"'0123456789" for c in re.findall(r"\\(.)", lit)):
                                bad.append("%s:%d" % (fn, no))
    check(bad == [], "no single-backslash escapes in Lua strings (paths need \\\\): %s" % bad)


TALENT_FIXTURE = os.path.join(HERE, "talent_fixture.json")
SITE_TALENTS = "https://nobody174.github.io/wow-forever/talents.html#"


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


def use_fixture_data(lua, raw, cls="warrior"):
    """Replace the addon's bundled trees for `cls` with the small test fixture (Wowhead's format), so the sandbox board,
    the ~hash and the link digits match the fake game's talents."""
    sys.path.insert(0, os.path.join(ROOT, "addon", "tools"))
    import gen_talent_data as G
    entry = [c for c in G.CLASSES if c[0] == cls][0]
    lua.execute("R2F.TalentData.classes.%s = { token = %r, trees = {\n%s\n} }"
                % (cls, entry[1], "\n".join(G.trees_lua(raw, entry[2]))))


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
    use_fixture_data(lua, raw, "warrior")
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
              "https://nobody174.github.io/wow-forever/talents.html", "https://github.io/x"):
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

    # ---- The Talents tab (sandbox board) ----------------------------------------------
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
    for label in ("Load", "Copy link", "Learn this build", "Reset", "Save loadout", "Loadouts", "Recommended", "Share"):
        check(label in btn, "%s: Talents tab has %r" % (tag, label))
    check("Preview" not in btn and "Copy my build" not in btn, "%s: the old Preview / Copy my build buttons are gone" % tag)
    find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.TALENT_LINK_PLACEHOLDER:format('warrior')", "PH")
    check(lua.eval("#PH") == 1 and lua.eval("PH[1].__shown") is True, "%s: placeholder talents.html#warrior/... shown" % tag)
    check(lua.eval(btn["Learn this build"] + ".__enabled") is False, "%s: empty board: Learn disabled" % tag)
    c = lambda t, row, col: "R2F.TalentPanel.Cell(%d, %d, %d)" % (t, row, col)
    # The board is a sandbox: your real talents (Deflection 5 ...) are NOT shown on it.
    check(lua.eval(c(1, 1, 2) + ".__shown") is True and lua.eval(c(1, 1, 2) + ".badge.__shown") is False,
          "%s: the board starts empty, your real talents are not mirrored" % tag)
    check(lua.eval(c(2, 3, 1) + ".__shown") is False, "%s: empty grid cells hidden" % tag)
    check(lua.eval("R2F.TalentPanel.Class()") == "warrior", "%s: the board starts on your own class" % tag)
    total = "R2F.TalentCalc.Total(R2F.TalentPanel.Calc())"
    # Click: +1, right-click -1.
    lua.execute(c(1, 1, 2) + ".__scripts.OnClick(" + c(1, 1, 2) + ", 'LeftButton')")
    check(lua.eval(c(1, 1, 2) + ".rank.__text") == "1" and lua.eval(total) == 1, "%s: left-click adds a point" % tag)
    find_frames(lua, "f.__kind == 'FontString' and f.__text == '1 of 51 points spent, 50 left.'", "SUM1")
    check(lua.eval("#SUM1") == 1, "%s: summary counts the sandbox points" % tag)
    lua.execute(c(1, 1, 2) + ".__scripts.OnClick(" + c(1, 1, 2) + ", 'RightButton')")
    check(lua.eval(total) == 0, "%s: right-click takes it away" % tag)
    check(lua.eval("TEST.talentWrites") == 0, "%s: clicking never touches your real talents" % tag)
    # Tooltip: our own text (any class), name + rank.
    lua.execute(c(1, 1, 2) + ":Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(lines[0] == "Deflection" and "Rank 0 / 5" in lines, "%s: tooltip: name and rank: %s" % (tag, lines))
    check(lua.eval("GameTooltip.spellArgs") is None, "%s: tooltip does not need the game's spell data" % tag)
    # Load a link built on the site (same hash as the fixture's trees).
    game({}, 21)
    lua.execute("%s:SetText(%r) %s.__scripts.OnEnterPressed(%s)" % (edit, prot21, edit, edit))
    check(lua.eval(total) == 21, "%s: Enter loads the link onto the board (21 points)" % tag)
    res = P.Result()
    check(res.plan.learnable is True and lua.eval(btn["Learn this build"] + ".__enabled") is True,
          "%s: learnable build -> Learn this build enabled" % tag)
    find_frames(lua, "f.__kind == 'FontString' and f.__text == 'This build uses 21 points. You have 21 free. All 21 will be learned.'", "S21")
    check(lua.eval("#S21") == 1 and lua.eval("S21[1].__color[1]") == 1 and lua.eval("S21[1].__color[2]") == 1,
          "%s: learn line is white when there is no conflict" % tag)
    lua.execute(btn["Learn this build"] + ".__scripts.OnEnter(%s)" % btn["Learn this build"])
    check(lua_table_to_list(lua.eval("GameTooltip.lines")) == [L.TALENT_LEARN_TIP], "%s: Learn tooltip explains it" % tag)
    # Points spent elsewhere: the learn line follows CHARACTER_POINTS_CHANGED.
    game({"Shield Specialization": 5}, 16)
    T.fire("CHARACTER_POINTS_CHANGED")
    T.runTimers()
    check(P.Result().plan.summary == "This build uses 21 points, 5 of them already learned. You have 16 free. All 16 will be learned.",
          "%s: learn line re-read on CHARACTER_POINTS_CHANGED: %r" % (tag, P.Result().plan.summary))
    # A conflict (you have points the board doesn't use): red, Learn disabled.
    game({"Deflection": 5}, 4)
    T.fire("CHARACTER_POINTS_CHANGED")
    T.runTimers()
    find_frames(lua, "f.__kind == 'FontString' and type(f.__text) == 'string' and f.__text:find('^You already have 5 points')", "CON")
    check(lua.eval("#CON") == 1 and lua.eval("CON[1].__color[2]") < 0.2 and lua.eval(btn["Learn this build"] + ".__enabled") is False,
          "%s: conflict: red line, Learn disabled" % tag)
    # Bad links: shown in red on the tab, the board is kept.
    lua.execute("%s:SetText('garbage') %s:Click()" % (edit, btn["Load"]))
    find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.TALENT_BAD_LINK", "BAD")
    check(lua.eval("#BAD") == 1 and lua.eval("BAD[1].__color[2]") < 0.2 and lua.eval(total) == 21,
          "%s: junk: red message, board kept" % tag)
    lua.execute("%s:SetText('warrior/--55155~zzzz') %s:Click()" % (edit, btn["Load"]))
    find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.TALENT_HASH_MISMATCH_SB", "ERR")
    check(lua.eval("#ERR") == 1, "%s: a link made with other trees is refused (the digits could mean other talents)" % tag)
    lua.execute("%s:SetText('warrior/9~%s') %s:Click()" % (edit, wh, btn["Load"]))
    find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.TALENT_LINK_INVALID", "INV")
    check(lua.eval("#INV") == 1, "%s: an invalid build (rank past the maximum) is refused" % tag)
    lua.execute("%s:SetText('warrior/--55155') %s:Click()" % (edit, btn["Load"]))
    check(lua.eval(total) == 21, "%s: an old link without a hash still loads" % tag)
    # Another class: the board switches, learning is for your own class only.
    lua.execute("R2F.TalentPanel.SelectClass('mage')")
    check(lua.eval("R2F.TalentPanel.Class()") == "mage" and lua.eval(btn["Learn this build"] + ".__enabled") is False,
          "%s: a class circle opens that class's trees; Learn is off" % tag)
    find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.TALENT_PREVIEW_ONLY:format('Mage')", "PO")
    check(lua.eval("#PO") == 1, "%s: other class: 'Preview only' line" % tag)
    lua.execute("R2F.TalentPanel.SelectClass('warrior')")
    # Reset empties the board, Copy link opens the copy box with the board's link.
    lua.execute(btn["Reset"] + ":Click()")
    check(lua.eval(total) == 0, "%s: Reset empties the board" % tag)
    lua.execute(btn["Copy link"] + ":Click()")
    check(lua.eval("R2FCopy:IsShown()") is True and lua.eval("R2FCopy.edit:GetText()").startswith(SITE_TALENTS + "warrior/~"),
          "%s: Copy link opens the copy box with the board's link" % tag)
    lua.execute("R2FCopy:Hide()")

    # ---- The sandbox works in combat (it is only a calculator) -----------------------
    T.combat = True
    T.fire("PLAYER_REGEN_DISABLED")
    lua.execute(c(1, 1, 2) + ".__scripts.OnClick(" + c(1, 1, 2) + ", 'LeftButton')")
    check(lua.eval(total) == 1, "%s: clicking works in combat" % tag)
    check(lua.eval(btn["Load"] + ".__enabled") is True, "%s: Load not greyed out in combat (read-only)" % tag)
    game({}, 21)
    lua.execute("%s:SetText(%r) %s:Click()" % (edit, prot21, btn["Load"]))
    check(P.Result() is not None and P.Result().plan is not None and lua.eval(btn["Learn this build"] + ".__enabled") is False,
          "%s: Load works in combat, Learn does not" % tag)
    T.combat = False
    T.fire("PLAYER_REGEN_ENABLED")
    check(lua.eval("TEST.talentWrites") == 0, "%s: the Talents tab never calls LearnTalent or the preview API" % tag)
    check(len(lua_table_to_list(T.calls)) == 0, "%s: no macro API writes from the Talents tab" % tag)
    # Tab switch lets go of the keyboard.
    lua.execute("R2F.MainWindow.SelectTab('home')")
    check(lua.eval("R2F.MainWindow.CurrentTab()") == "home", "%s: leaving the Talents tab works" % tag)

    # ---- Globals ---------------------------------------------------------------------
    new_globals = lua.eval("""(function()
      local out = {}
      for k in pairs(_G) do if not BEFORE[k] then table.insert(out, k) end end
      table.sort(out) return table.concat(out, ",") end)()""").split(",")
    test_vars = {"NS", "TBTN", "PH", "SUM1", "S21", "CON", "BAD", "ERR", "INV", "PO"}
    bad = [g for g in new_globals if g and g not in test_vars and g not in BINDING_GLOBALS
           and g not in ("SLASH_R2F1", "SLASH_R2FT1", "SLASH_R2FBIZ1", "SLASH_R2FBIZ2", "SLASH_R2FWAY1", "TomTom") and not g.startswith("R2F")]
    check(not bad, "%s: step 9 adds no globals besides R2F* frames: %s" % (tag, bad))

    # ---- The last board comes back in a new session (lastTalentLink) -------------------
    lua2 = new_runtime(templates)
    lua2.execute("R2FCharDB = { lastTalentLink = %r }" % prot21)
    T2 = lua2.eval("TEST")
    T2.fire("ADDON_LOADED", "RoadToForever")
    T2.fire("PLAYER_LOGIN")
    use_fixture_data(lua2, raw, "warrior")
    lua2.execute("TEST.tabNames = { 'Arms', 'Fury', 'Protection' }")
    set_game_talents(lua2, raw, W, {})
    T2.talentPoints = 21
    lua2.execute("R2F.MainWindow.Show('talents')")
    check(lua2.eval("R2F.TalentCalc.Total(R2F.TalentPanel.Calc())") == 21
          and lua2.eval("R2F.TalentPanel.Result().plan.summary") == "This build uses 21 points. You have 21 free. All 21 will be learned.",
          "%s: last board restored after a reload" % tag)
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
        use_fixture_data(lua, raw, "warrior")
        lua.execute("TEST.tabNames = { 'Arms', 'Fury', 'Protection' }")
        set_game_talents(lua, raw, warrior, ranks)
        T.talentPoints = points
        lua.execute("R2F.MainWindow.Show('talents')")
        self.edit = "R2FTalentLink" if templates else "R2FTalentLinkPlain"
        find_frames(lua, "f.__kind == 'Button' and f.__text ~= nil and f.__text ~= ''", "LBTN")
        self.btn = {}
        for i in range(1, lua.eval("#LBTN") + 1):
            self.btn.setdefault(lua.eval("LBTN[%d].__text" % i), "LBTN[%d]" % i)
        self.learn, self.cancel = self.btn["Learn this build"], self.btn["Stop"]
        self.previewb, self.copy = self.btn["Load"], self.btn["Copy link"]
        find_frames(lua, "f.__kind == 'FontString' and f.__text == R2F.L.TALENT_TAB_HINT", "LHINT")
        if link:
            self.preview(link)

    def preview(self, link):
        """Put a build on the board without the validity checks (the fixture tree doesn't follow the real tier rules)."""
        m = re.search(r"(\w+)/([\d-]*)", link.split("#")[-1])
        self.lua.execute("R2F.TalentPanel.SetBoardUnchecked(%r, %r)" % (m.group(1), m.group(2)))

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
    check(c.enabled(c.learn) is True and c.text(c.learn) == "Learn this build", "%s: learnable -> Learn enabled" % tag)
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
    check(labels[:3] == ["Learning 3 / 17", "Learning 4 / 17", "Learning 5 / 17"] and labels[-1] == "Learn this build",
          "%s: label counts up, back to 'Learn this build' at the end: %s" % (tag, labels[-3:]))
    check(all(c.rank(n) == v for n, v in deep["ranks"].items()) and c.ev("TEST.talentPoints") == 0,
          "%s: the game now has exactly the build" % tag)
    check(c.said("Learned 17 talent points.") and c.status().phase == "done", "%s: 'Learned 17 talent points.' in chat" % tag)
    check("Learned 17 talent points." in c.status_line(), "%s: done line on the tab" % tag)
    check(c.ev("R2F.TalentPanel.Cell(1, 3, 2).rank.__text") == "1", "%s: trees refreshed (Anger Management rank 1)" % tag)
    check(c.ev("R2F.TalentPanel.Result().plan.summary") == "You already have this whole build."
          and c.enabled(c.learn) is False, "%s: afterwards: whole build, Learn disabled" % tag)
    check(c.enabled(c.previewb) is True and c.ev(c.edit + ".__enabled") is True and c.ev(c.cancel + ".__shown") is False,
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
        ({}, 0, link, False),                                        # no free points
        (deep["ranks"], 3, link, False),                             # whole build already learned
        ({}, 17, "warrior/~" + wh, False),                           # empty link
        ({}, 17, link, True),
        ({"Deflection": 5}, 2, link, True),                          # part learned, part free
    ]
    for ranks, pts, lnk, want in cases:
        c = ctx(ranks, pts, lnk)
        res = c.ev("R2F.TalentPanel.Result()")
        plan = res.plan if res is not None else None
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
    check(c.ev("R2F.Talents.LearnMode()") == "direct", "%s: LearnTalent worked earlier -> LearnMode stays direct" % tag)
    check(c.text(c.learn) == "Learn this build" and c.enabled(c.learn) is True and c.enabled(c.previewb) is True,
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
                 + c.ev("R2F.L.TALENT_BLOCKED_HINT")), "%s: LearnTalent error -> refused, blocked hint" % tag)

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
    check(c.ev("R2F.Talents.LearnMode()") == "none", "%s: first point refused, never worked -> learning off" % tag)
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

    # ---- Addon learning off ("none"): no write API, or this session saw it blocked -----------
    c = ctx({}, 17, setup="LearnTalent = nil")
    check(c.ev("R2F.Talents.LearnMode()") == "none", "%s: no LearnTalent -> mode none" % tag)
    c.click(c.learn)
    check(c.popup() is None and c.said(c.ev("R2F.L.TALENT_UNAVAILABLE")),
          "%s: mode none: no popup, chat says to use Blizzard's window" % tag)
    check(c.ev("TEST.talentWrites") == 0 and (c.ev("TEST.toggles") or 0) == 0 and c.status().phase == "idle",
          "%s: mode none: nothing written, Blizzard's window not touched, no run started" % tag)
    # Detection: first point refused -> hint -> the next Learn only says it is off.
    c = ctx({}, 17, setup="TEST.learnBlocked = true")
    c.click(c.learn)
    c.accept()
    c.T.runTimers()
    check(c.said("Stopped at Deflection: the game didn't accept the point. 0 of 17 learned. " + c.ev("R2F.L.TALENT_BLOCKED_HINT")),
          "%s: blocked LearnTalent -> stop + blocked hint" % tag)
    c.click(c.learn)
    check(c.popup() is None and c.ev("R2F.Talents.LearnMode()") == "none" and c.said(c.ev("R2F.L.TALENT_UNAVAILABLE")),
          "%s: next Learn -> off, says so, no popup" % tag)
    # ADDON_ACTION_FORBIDDEN for LearnTalent: stops at once, no timer needed.
    c = ctx({}, 17, setup="TEST.learnBlocked = true TEST.forbiddenEvent = true")
    c.click(c.learn)
    c.accept()
    check(c.status().phase == "stopped" and c.ev("R2F.Talents.LearnMode()") == "none",
          "%s: ADDON_ACTION_FORBIDDEN -> stop and learning off at once" % tag)
    c.T.fire("ADDON_ACTION_FORBIDDEN", "OtherAddon", "LearnTalent()")
    c.T.fire("ADDON_ACTION_BLOCKED", "RoadToForever", "CastSpellByName()")
    check(c.ev("R2F.Talents.LearnMode()") == "none", "%s: other addons' / other functions' events ignored" % tag)

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
    check(c.said(c.ev("R2F.L.TALENT_PREVIEW_FILLED").replace("%d", "17")) and (c.ev("TEST.toggles") or 0) == 0,
          "%s: the player is told to open the talent window for Blizzard's Learn button; we don't open it" % tag)
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
           and g not in ("SLASH_R2F1", "SLASH_R2FT1", "SLASH_R2FBIZ1", "SLASH_R2FBIZ2", "SLASH_R2FWAY1", "TomTom") and not g.startswith("R2F")]
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
    all: reading works, learning is off and writes nothing)."""
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
    check(fv.eval("R2F.Talents.LearnMode()") == "none",
          "%s: Forever client without C_Traits writes (13.12 adds them): addon learning is off" % tag)
    # Even if a LearnTalent (and a switched-on preview API) existed there: no
    # Classic GetTalentInfo = no way to confirm a (tab, index) address -> none.
    fv.execute("LearnTalent = function() error('must not be called') end "
               "AddPreviewTalentPoints = LearnTalent LearnPreviewTalents = LearnTalent "
               "GetCVarBool = function() return true end")
    check(fv.eval("R2F.Talents.LearnMode()") == "none",
          "%s: Forever client with a stray LearnTalent / preview API: still none" % tag)
    fv.execute("LearnTalent = nil AddPreviewTalentPoints = nil LearnPreviewTalents = nil GetCVarBool = nil")
    fv.execute("R2F.Talents.StartLearn(%s, R2F.Talents.LearnPoints(R2F.Talents.Preview(%s).plan))"
               % (lua_literal(link), lua_literal(link)))
    F.runTimers()
    st = fv.eval("R2F.Talents.LearnStatus()")
    check(st.phase == "stopped" and fv.eval("R2F.Talents.LearnMode()") == "none",
          "%s: Forever client: the run stops at once, learning is off" % tag)
    check(F.talentWrites == 0, "%s: Forever client: nothing written" % tag)

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
    check(d.ev("R2F.Talents.LearnMode()") == "none", "%s: C_Traits without GetNodeInfo -> none" % tag)
    d = ctx(extra="C_Traits.PurchaseRank = 'not a function'")
    check(d.ev("R2F.Talents.LearnMode()") == "none", "%s: PurchaseRank not a function -> none" % tag)

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
    check(labels[:2] == ["Learning 3 / 17", "Learning 4 / 17"] and labels[-1] == "Learn this build",
          "%s: traits: label counts up, back to 'Learn this build'" % tag)
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

    # ---- A rejected purchase mid-run: stop, learning off, nothing more fired --------
    c = ctx()
    c.click(c.learn)
    c.accept()
    c.T.traitServer(3)                          # 3 applied; the 4th is in flight
    c.T.purchaseRejects = True
    c.T.traitServer(1)                          # 4th applied -> 5th purchase refused
    want = "Stopped at Deflection: the game didn't accept the point. 4 of 17 learned. " + HINT
    check(c.status().phase == "stopped" and c.said(want), "%s: refused purchase -> stop + blocked hint: %s" % (tag, c.chat()[-1:]))
    check(want in c.status_line(), "%s: refused purchase: red line on the tab" % tag)
    check(purchases(c) == ["Deflection"] * 5 and commits(c) == 4, "%s: the refused purchase isn't committed" % tag)
    check(c.ev("R2F.Talents.LearnMode()") == "none", "%s: anything unexpected -> off for the session" % tag)
    writes = c.ev("TEST.talentWrites")
    c.T.purchaseRejects = False
    c.T.fire("TRAIT_CONFIG_UPDATED", 7001)
    c.T.runTimers()
    check(c.ev("TEST.talentWrites") == writes, "%s: stays stopped on later events / timers" % tag)
    c.click(c.learn)
    check(c.popup() is None and c.said(c.ev("R2F.L.TALENT_UNAVAILABLE")) and c.ev("TEST.talentWrites") == writes,
          "%s: Learn now only says addon learning is off: no popup, no C_Traits write" % tag)
    c.lua.execute("R2F.Talents.ResetSession()")
    check(c.ev("R2F.Talents.LearnMode()") == "traits", "%s: a new session (/reload) tries traits again" % tag)
    # PurchaseRank raising.
    c = ctx(extra="TEST.purchaseError = 'some client error'")
    c.click(c.learn)
    c.accept()
    check(c.said("Stopped at Deflection: the game didn't accept the point. 0 of 17 learned. " + HINT)
          and commits(c) == 0 and c.ev("R2F.Talents.LearnMode()") == "none", "%s: PurchaseRank error -> refused, off" % tag)
    # CanEditConfig says no: nothing purchased at all.
    c = ctx(extra="C_Traits.CanEditConfig = function() return false, 'nope' end")
    c.click(c.learn)
    c.accept()
    check(c.ev("TEST.talentWrites") == 0 and c.status().phase == "stopped" and c.ev("R2F.Talents.LearnMode()") == "none",
          "%s: CanEditConfig false -> stopped before any purchase, off" % tag)
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
    check(c.status().phase == "stopped" and commits(c) == 0 and c.ev("R2F.Talents.LearnMode()") == "none"
          and c.said("Stopped at Deflection: the game didn't accept the point. 0 of 17 learned. " + HINT),
          "%s: ADDON_ACTION_FORBIDDEN on PurchaseRank -> stop, no commit, off" % tag)
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
          and c.rank("Deflection") == 0 and len(purchases(c)) == 1 and c.ev("R2F.Talents.LearnMode()") == "none",
          "%s: false success caught by the read-back at the timeout; off" % tag)
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
          and c.ev("R2F.Talents.LearnMode()") == "none",
          "%s: player's Apply Changes -> counted late; the session stays off" % tag)
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
    check(c.said(staged_msg) and c.ev("R2F.Talents.LearnMode()") == "none", "%s: no CommitConfig -> 'Apply Changes' stop, off" % tag)
    c.click(c.learn)
    check(c.popup() is None and c.said(c.ev("R2F.L.TALENT_UNAVAILABLE")) and c.ev("TEST.talentWrites") == 1,
          "%s: ... Learn only says it is off, nothing more written" % tag)

    # ---- Commit failures --------------------------------------------------------------
    c = ctx(extra="TEST.commitRejects = true")
    c.click(c.learn)
    c.accept()
    c.T.runTimers()
    check(c.said(staged_msg) and c.status().phase == "stopped" and c.ev("R2F.Talents.LearnMode()") == "none",
          "%s: CommitConfig keeps returning false -> retried, then stop ('waiting in Blizzard's window'), off" % tag)
    # A commit that answers false once or twice (still busy with the last one) is asked again and the run goes on.
    c = ctx(extra="TEST.commitRejectsTimes = 2")
    c.click(c.learn)
    c.accept()
    for _ in range(80):
        c.T.runShortTimers()
        drain(c)
    check(c.said("Learned 17 talent points.") and exact_build(c) and c.ev("R2F.Talents.LearnMode()") == "traits",
          "%s: CommitConfig false twice, then fine -> the retries carry the run to the end" % tag)
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
    # could stack on an invisible one); it's reported, learning goes off.
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
    check(c.ev("R2F.Talents.LearnMode()") == "traits", "%s: ... no switch-off for that (nothing was sent)" % tag)
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
           and g not in ("SLASH_R2F1", "SLASH_R2FT1", "SLASH_R2FBIZ1", "SLASH_R2FBIZ2", "SLASH_R2FWAY1", "TomTom") and not g.startswith("R2F")]
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


def test_talent_calc():
    """The sandbox calculator (TalentCalc.lua + the generated TalentData.lua): the real bundled trees of all nine
    classes, the site's rules, the share code and ~hash, the recommended builds, and (with the small fixture)
    the same digits and hash as the site's talentcalc.js."""
    lua = new_runtime()
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    lua.execute("TC = R2F.TalentCalc TD = R2F.TalentData")
    classes = lua_table_to_list(lua.eval("TC.ORDER"))
    check(len(classes) == 9 and all(lua.eval("TC.Class(%r) ~= nil" % c) for c in classes), "calc: all nine classes are bundled")
    # Data shape: 3 trees, a 4 x 7 grid, talents in row/column order, sane prerequisites, a description per rank.
    check_fn = lua.eval("""function(c) local bad = {}
      for t, tree in ipairs(TC.Trees(c)) do
        local prev
        for k, x in ipairs(tree.talents) do
          if x.r < 0 or x.r > 6 or x.c < 0 or x.c > 3 then bad[#bad + 1] = x.n .. ' off the grid' end
          if prev and (x.r < prev.r or (x.r == prev.r and x.c <= prev.c)) then bad[#bad + 1] = x.n .. ' out of order' end
          if #x.d ~= x.m or x.m < 1 or x.m > 5 then bad[#bad + 1] = x.n .. ' ranks' end
          for _, q in ipairs(x.q) do if q[1] == k or q[1] < 1 or q[1] > #tree.talents or q[2] > tree.talents[q[1]].m then bad[#bad + 1] = x.n .. ' prerequisite' end end
          prev = x
        end
      end
      return table.concat(bad, '; ') end""")
    problems = []
    for cid in classes:
        n = lua.eval("#TC.Trees(%r)" % cid)
        if n != 3:
            problems.append("%s has %d trees" % (cid, n))
        out = check_fn(cid)
        if out:
            problems.append("%s: %s" % (cid, out))
    check(not problems, "calc: bundled trees are well-formed: %s" % problems)
    check(lua.eval("TC.Class('warrior').trees[1].name") == "Arms" and lua.eval("TC.Class('priest').trees[3].name") == "Shadow",
          "calc: tree names and order (Arms / Fury / Protection, Discipline / Holy / Shadow)")
    # Hash: the same algorithm as the site, over the names in link order (independent Python check).
    names_fn = lua.eval("""function(c) local o = {} for t, tree in ipairs(TC.Trees(c)) do local n = {}
      for k, x in ipairs(tree.talents) do n[k] = x.n end o[t] = table.concat(n, ',') end return table.concat(o, ';') end""")
    for cid in ("warrior", "priest", "mage"):
        check(lua.eval("TC.Hash(%r)" % cid) == ref_talent_hash(names_fn(cid)), "calc: ~hash of %s matches the reference" % cid)
    # Rules on real Warrior data.
    lua.execute("W = TC.New('warrior')")
    check(lua.eval("TC.Total(W)") == 0 and lua.eval("TC.Code(W)") == "", "calc: a new board is empty, code ''")
    check(lua.eval("TC.AddBlock(W, 1, 1)") is None, "calc: a row-1 talent can be taken")
    deep = lua.eval("(function() for k, x in ipairs(TC.Trees('warrior')[1].talents) do if x.r >= 2 then return k end end end)()")
    check(lua.eval("TC.AddBlock(W, 1, %d)" % deep) == "tier", "calc: a talent below row 1 needs points above it (tier)")
    check(lua.eval("TC.Add(W, 1, 1, true)") is True and lua.eval("TC.Rank(W, 1, 1)") == lua.eval("TC.Trees('warrior')[1].talents[1].m"),
          "calc: Shift adds up to the maximum rank")
    check(lua.eval("TC.AddBlock(W, 1, 1)") == "max", "calc: at the maximum rank: 'max'")
    check(lua.eval("TC.Remove(W, 1, 1, true)") is True and lua.eval("TC.Total(W)") == 0, "calc: remove all the way down")
    # A prerequisite blocks a talent until its ranks are there, and can't be removed while it is needed.
    pre = lua.eval("""(function() for t, tree in ipairs(TC.Trees('warrior')) do for k, x in ipairs(tree.talents) do
      if #x.q > 0 then return {t, k, x.q[1][1], x.q[1][2], x.r} end end end end)()""")
    if pre is not None:
        t, k, pk, pq, row = pre[1], pre[2], pre[3], pre[4], pre[5]
        lua.execute("""P = TC.New('warrior')
          local tree = TC.Trees('warrior')[%d]
          -- 5 points per row above, filled from the first talents, so only the prerequisite is missing
          for r = 0, %d - 1 do
            for j, x in ipairs(tree.talents) do if x.r == r and j ~= %d then TC.Add(P, %d, j, true) end end
          end""" % (t, row, pk, t))
        if lua.eval("TC.TierMet(P, %d, %d)" % (t, k)):
            check(lua.eval("TC.AddBlock(P, %d, %d)" % (t, k)) == "prereq", "calc: a talent without its prerequisite is blocked ('prereq')")
            lua.execute("for _ = 1, %d do TC.Add(P, %d, %d) end" % (pq, t, pk))
            lua.execute("TC.Add(P, %d, %d)" % (t, k))
            check(lua.eval("TC.Rank(P, %d, %d)" % (t, k)) == 1, "calc: with the prerequisite the talent can be taken")
            check(lua.eval("TC.CanRemove(P, %d, %d)" % (t, pk)) is False, "calc: the prerequisite can't be removed while it is needed")
    # Every recommended build respects the rules, and its code round-trips.
    builds = lua.eval("#TD.builds")
    check(builds >= 30, "calc: %d recommended builds bundled" % builds)
    bad = []
    for i in range(1, builds + 1):
        cls, lvl, role, name, code = [lua.eval("TD.builds[%d][%d]" % (i, j)) for j in range(1, 6)]
        total = lua.eval("(function() local c, ok = TC.FromCode(%r, %r) if not ok then return nil end return TC.Total(c) end)()" % (cls, code))
        if total is None:
            bad.append("%s %s %s" % (cls, name, code))
        elif total > 51:
            bad.append("%s %s has %s points" % (cls, name, total))
        elif lua.eval("(function() local c = TC.FromCode(%r, %r) return TC.Code(c) end)()" % (cls, code)) != code:
            bad.append("%s %s: code does not round-trip" % (cls, name))
    check(not bad, "calc: every recommended build is valid and round-trips: %s" % bad)
    # Cap: filling greedily stops at exactly 51 and stays valid; then the reason is 'cap'.
    lua.execute("""G = TC.New('warrior')
      for _ = 1, 80 do
        for t = 1, 3 do for k = 1, #TC.Trees('warrior')[t].talents do TC.Add(G, t, k, true) end end
      end""")
    check(lua.eval("TC.Total(G)") == 51 and lua.eval("TC.Valid(G)") is True, "calc: greedy fill stops at 51 points and stays valid")
    check(lua.eval("""(function() for t, tree in ipairs(TC.Trees('warrior')) do for k = 1, #tree.talents do
      if TC.Rank(G, t, k) < tree.talents[k].m and TC.AddBlock(G, t, k) == 'cap' then return true end end end end)()""") is True,
          "calc: at 51 points the reason is 'cap'")
    # Invalid codes leave an empty board, like the site.
    check(lua.eval("(function() local c, ok = TC.FromCode('warrior', '9') return ok == false and TC.Total(c) == 0 end)()"),
          "calc: a rank past the maximum is refused")
    check(lua.eval("(function() local c, ok = TC.FromCode('warrior', '---5') return ok == false end)()"),
          "calc: points in a fourth tree are refused")
    check(lua.eval("TC.FromCode('nope', '1')") is None, "calc: unknown class -> nil")
    # Recommended: Tank, DPS, Healer order, level 60 first inside a role.
    rec = lua_table_to_list(lua.eval("(function() local o = {} for i, b in ipairs(TC.Recommended('paladin')) do o[i] = b.role .. b.level end return o end)()"))
    check(rec[:1] == ["Tank60"] and rec[-1] == "Healer30", "calc: recommended Paladin builds are ordered Tank, DPS, Healer: %s" % rec)

    # Same digits and hash as the site's talentcalc.js, on the small fixture (Wowhead's format).
    fxt = json.load(open(TALENT_FIXTURE, encoding="utf-8"))
    js = talent_js()
    use_fixture_data(lua, fxt["talents"], "warrior")
    check(lua.eval("TC.Hash('warrior')") == js["hashes"]["warrior"], "calc: the ~hash equals talentcalc.js's on the fixture")
    for sc in fxt["scenarios"]:
        if sc["cls"] != "warrior":
            continue
        lua.execute("S = TC.New('warrior')")
        for name, rank in sc["ranks"].items():
            lua.execute("""for t, tree in ipairs(TC.Trees('warrior')) do for k, x in ipairs(tree.talents) do
              if x.n == %r then S.ranks[t][k] = %d end end end""" % (name, rank))
        check(lua.eval("TC.Code(S)") == sc["code"], "calc: code for '%s' equals the site's (%r)" % (sc["name"], sc["code"]))


def test_talent_sandbox_ui(templates):
    """The Talents tab on the real bundled data: class circles, any class's trees, tooltips, sharing, recommended builds."""
    tag = "templates" if templates else "fallbacks"
    lua = new_runtime(templates)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    lua.execute("R2F.MainWindow.Show('talents')")
    find_frames(lua, "f.__kind == 'CheckButton' and f.talentClass ~= nil", "CIR")
    check(lua.eval("#CIR") == 9, "%s: nine class circles" % tag)
    # Priest on a Warrior: the Priest trees, with real names and tooltips; nothing changes for the character.
    lua.execute("R2F.TalentPanel.SelectClass('priest')")
    find_frames(lua, "f.__kind == 'FontString' and f.__text == 'Discipline'", "DIS")
    check(lua.eval("#DIS") >= 1 and lua.eval("R2F.TalentPanel.Class()") == "priest", "%s: another class's trees open" % tag)
    check(lua.eval("""(function() local on = 0 for _, f in ipairs(CIR) do
      if f.r2fCheckRing and f.r2fCheckRing:IsShown() then on = on + 1 end end return on end)()""") == 1,
          "%s: exactly the selected class circle has the gold ring" % tag)
    cell = "R2F.TalentPanel.Cell(1, 1, 2)"
    check(lua.eval(cell + ".__shown") is True and lua.eval(cell + ".entry.name") != "", "%s: a Priest talent is drawn at row 1" % tag)
    lua.execute(cell + ":Fire('OnEnter')")
    lines = lua_table_to_list(lua.eval("GameTooltip.lines"))
    check(len(lines) >= 3 and lines[1].startswith("Rank 0 / "),
          "%s: tooltip has name, rank and text for a class you don't play: %s" % (tag, lines))
    lua.execute(cell + ".__scripts.OnClick(" + cell + ", 'LeftButton')")
    check(lua.eval("R2F.TalentCalc.Total(R2F.TalentPanel.Calc())") == 1 and lua.eval("TEST.talentWrites") == 0,
          "%s: clicking a Priest talent costs the Warrior nothing" % tag)
    # Recommended menu: DPS / Healer entries for Priest put a build on the board.
    lua.execute("R2F.UI.ContextMenu = function(items) MENU = items end R2F.TalentPanel.RecommendedMenu()")
    texts = lua_table_to_list(lua.eval("(function() local o = {} for i, it in ipairs(MENU) do o[i] = it.kind .. ':' .. it.text end return o end)()"))
    check(any(t.startswith("title:DPS") for t in texts) and any(t.startswith("title:Healer") for t in texts)
          and any("Shadow (level 30)" in t for t in texts), "%s: recommended menu groups by role: %s" % (tag, texts))
    lua.execute("for _, it in ipairs(MENU) do if it.kind == 'button' and it.text:find('Shadow %(level 30%)') then it.func() break end end")
    check(lua.eval("R2F.TalentCalc.Total(R2F.TalentPanel.Calc())") > 20, "%s: picking a recommended build fills the board" % tag)
    # Build in order (0.56.0): every recommended build's order is legal point by point and adds up to the build.
    bad = lua.eval("""(function()
      local TC, bad, n = R2F.TalentCalc, {}, 0
      for _, id in ipairs(TC.ORDER) do
        for _, b in ipairs(TC.Recommended(id)) do
          local calc = TC.FromCode(id, b.code)
          local order = TC.Order(calc)
          n = n + 1
          local walk = TC.New(id)
          for i, p in ipairs(order) do
            if TC.AddBlock(walk, p[1], p[2]) then bad[#bad + 1] = id .. ' ' .. b.name .. ' point ' .. i break end
            walk.ranks[p[1]][p[2]] = walk.ranks[p[1]][p[2]] + 1
          end
          if TC.Code(walk) ~= TC.Code(calc) then bad[#bad + 1] = id .. ' ' .. b.name .. ' differs' end
          if TC.Code(TC.Prefix(calc, #order)) ~= TC.Code(calc) or TC.Total(TC.Prefix(calc, 3)) ~= math.min(3, #order) then
            bad[#bad + 1] = id .. ' ' .. b.name .. ' prefix' end
        end
      end
      return n .. ':' .. table.concat(bad, ';')
    end)()""")
    check(bad.endswith(":") and int(bad.split(":")[0]) > 25, "%s: build order is legal for every recommended build: %s" % (tag, bad))
    # Next point (0.56.2): nothing taken -> the build's first point; everything taken -> nil; the Home line follows the board.
    chk = lua.eval("""(function()
      local TC = R2F.TalentCalc
      local calc = TC.FromCode('priest', '02--305022012013')
      local name, i = TC.NextPoint(calc, {})
      local full = {}
      for t = 1, #calc.ranks do
        full[t] = { talents = {} }
        for k = 1, #calc.ranks[t] do full[t].talents[k] = { rank = calc.ranks[t][k] } end
      end
      return tostring(name) .. ':' .. tostring(i) .. ':' .. tostring(TC.NextPoint(calc, full))
    end)()""")
    check(chk.endswith(":1:nil") and not chk.startswith("nil"), "%s: next point = first point of the order, none when all taken: %s" % (tag, chk))
    check(lua.eval("R2F.Talents.NextPointLine() == nil or type(R2F.Talents.NextPointLine()) == 'string'"), "%s: Home next-point line is text or nothing" % tag)
    # Loadouts menu starts with "My current talents" (the character's own build on the board).
    lua.execute("R2F.TalentPanel.LoadoutsMenu()")
    check(lua.eval("MENU[1].text") == lua.eval("R2F.L.TALENT_LOAD_MINE") and lua.eval("MENU[1].kind") == "button", "%s: loadouts menu offers my current talents first" % tag)
    # Pick order (0.63.0, owner rule): deepest first, the main tree first, a dip into another tree last.
    chk = lua.eval("""(function()
      local TC = R2F.TalentCalc
      local calc = TC.FromCode('priest', '02--305022012013')   -- Shadow, with 2 points in Discipline
      local o = TC.Order(calc)
      local last = o[#o]
      local depth = 0
      for i = 1, 10 do
        local x = TC.Trees('priest')[o[i][1]].talents[o[i][2]]
        if o[i][1] ~= 3 then return 'dip too early at ' .. i end
        depth = math.max(depth, x.r)
      end
      return (o[1][1] == 3 and last[1] == 1 and o[#o - 1][1] == 1) and 'ok' or 'wrong end'
    end)()""")
    check(chk == "ok", "%s: pick order: the main tree first, the dip last: %s" % (tag, chk))
    # Group picks (0.62.1): the owner's picks baked into TalentData show under the Recommended menu.
    lua.execute("R2F.TalentData.groupBuilds = { { 'priest', 'Raid healer', 'Venom', '003-0321510303' }, { 'mage', 'Not mine', '', '25' } }")
    check(lua.eval("#R2F.TalentCalc.GroupPicks('priest')") == 1 and lua.eval("R2F.TalentCalc.GroupPicks('priest')[1].by") == "Venom", "%s: group picks per class" % tag)
    lua.execute("R2F.TalentPanel.RecommendedMenu()")
    texts = lua_table_to_list(lua.eval("(function() local o = {} for i, it in ipairs(MENU) do o[i] = it.kind .. ':' .. (it.text or '') end return o end)()"))
    check("title:Group picks" in texts and any("Raid healer" in t for t in texts), "%s: the Recommended menu lists the group picks: %s" % (tag, texts))
    lua.execute("for _, it in ipairs(MENU) do if it.text and it.text:find('Raid healer') then it.func() end end")
    check(lua.eval("R2F.TalentCalc.Total(R2F.TalentPanel.Calc())") > 5, "%s: picking a group pick fills the board" % tag)
    lua.execute("R2F.TalentData.groupBuilds = {}")
    t0 = lua.eval("R2F.TalentCalc.Total(R2F.TalentPanel.Calc())")
    lua.execute("R2F.TalentPanel.Step(-1)")
    check(lua.eval("R2F.TalentCalc.Total(R2F.TalentPanel.Calc())") == t0 - 1, "%s: stepper back = one point less" % tag)
    lua.execute("R2F.TalentPanel.Step(1)")
    check(lua.eval("R2F.TalentCalc.Total(R2F.TalentPanel.Calc())") == t0, "%s: stepper forward = the build again" % tag)
    # Share to the party: any class, the same R2FT message; a teammate's addon saves it as a loadout.
    lua.execute("TEST.addonSent = {} R2F.TalentPanel.ShareMenu()")
    lua.execute("for _, it in ipairs(MENU) do if it.kind == 'button' and it.text == R2F.L.TALENT_SHARE_PARTY then it.func() end end")
    sent = lua.eval("TEST.addonSent[1] and TEST.addonSent[1][2]")
    check(lua.eval("#TEST.addonSent") == 1 and sent.startswith("L\t") and "priest/" in sent, "%s: sharing a Priest build sends one message" % tag)
    lua.execute("MSG = TEST.addonSent[1][2] R2F.Talents.OnAddonMessage('R2FT', MSG, 'PARTY', 'Thorin-Realm')")
    check(lua.eval("#R2F.Talents.Loadouts('priest')") == 1 and lua.eval("R2F.Talents.Loadouts('priest')[1].by") == "Thorin",
          "%s: a teammate's build is saved under Loadouts (class priest)" % tag)
    # Link round trip: take the board's link, switch class, load the link: back on the Priest board.
    lua.execute("LK = R2F.Talents.SITE_URL .. R2F.TalentCalc.Body(R2F.TalentPanel.Calc()) R2F.TalentPanel.SelectClass('mage')")
    check(lua.eval("R2F.TalentPanel.Class()") == "mage" and lua.eval("R2F.TalentCalc.Total(R2F.TalentPanel.Calc())") == 0,
          "%s: a class circle opens an empty board" % tag)
    lua.execute("R2F.TalentPanel.SetLink(LK)")
    check(lua.eval("R2F.TalentPanel.Class()") == "priest" and lua.eval("R2F.TalentCalc.Total(R2F.TalentPanel.Calc())") > 0,
          "%s: loading a link switches to its class" % tag)
    check("priest/" in lua.eval("R2FCharDB.lastTalentLink"), "%s: the board is remembered" % tag)


def test_talent_data_fresh():
    """TalentData.lua's recommended builds match builds.html (rerun addon/tools/gen_talent_data.py if not)."""
    r = subprocess.run([sys.executable, os.path.join(ROOT, "addon", "tools", "gen_talent_data.py"), "--check"],
                       capture_output=True, cwd=ROOT)
    check(r.returncode == 0, "TalentData.lua is current with builds.html: %s" % r.stdout.decode("utf-8", "replace").strip())


def test_enchant_tooltip():
    """The item tooltip's Mr.BiZ enchant line (green), from the real BiZData."""
    lua = new_runtime()
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    found = lua.eval("""(function()
      for id, sp in pairs(R2F.BiZData.specs) do
        local rows = sp.enchants and sp.enchants.chest
        if rows and rows[1] and rows[1].ids and rows[1].alts and rows[1].alts[1] then
          return { id, rows[1].ids[1], rows[1].alts[1].ids[1], rows[1].name } end
      end end)()""")
    check(found is not None, "enchant tip: a spec with a best and a stand-in chest enchant exists")
    spec, best_id, alt_id, best_name = found[1], found[2], found[3], found[4]
    fn = lua.eval("function(link, loc, spec) return R2F.BiZ.EnchantTipLine(link, loc, spec) end")
    text, r, g, b = fn("item:1000:0:0:0", "INVTYPE_CHEST", spec)
    check(text.startswith("Mr.BiZ enchant: " + best_name) and (r, g, b) == (1, 0.5, 0.85), "enchant tip: no enchant -> the BiZ pick, pink: %s" % text)
    text, r, g, b = fn("item:1000:%d:0:0" % best_id, "INVTYPE_CHEST", spec)
    check(text == "Mr.BiZ enchant in place: " + best_name and r == 1 and b == 0.85, "enchant tip: the best enchant already on -> 'in place': %s" % text)
    text, r, g, b = fn("item:1000:%d:0:0" % alt_id, "INVTYPE_CHEST", spec)
    check(text.startswith("Enchant: the #2 pick. Mr.BiZ best: ") and r == 1 and g == 0.82, "enchant tip: a stand-in -> gold, names the best: %s" % text)
    check(fn("item:1000:0:0:0", "INVTYPE_FINGER", spec) is None, "enchant tip: rings have no enchant line")
    check(fn("item:1000:0:0:0", "INVTYPE_CHEST", "nope/nope") is None, "enchant tip: unknown spec -> nothing")
    check(fn(None, "INVTYPE_CHEST", spec) is None, "enchant tip: no link -> nothing")
    check(fn("item:1000:0:0:0", "INVTYPE_ROBE", spec) is not None, "enchant tip: a robe counts as chest")


def test_open_command():
    """/r2f open only opens the window (0.55.1); /r2f toggles; an unknown word still says so."""
    lua = new_runtime()
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    lua.execute("SlashCmdList.R2F('open')")
    check(lua.eval("R2F.MainWindow.IsShown()") is True, "open: /r2f open opens the window")
    lua.execute("SlashCmdList.R2F('open')")
    check(lua.eval("R2F.MainWindow.IsShown()") is True, "open: /r2f open never closes it")
    lua.execute("SlashCmdList.R2F('')")
    check(lua.eval("R2F.MainWindow.IsShown()") is False, "open: /r2f alone toggles it shut")
    lua.execute("SlashCmdList.R2F('nonsense')")
    check(any("unknown command \"nonsense\"" in c for c in chat_lines(lua)), "open: an unknown word says unknown command")
    check("Options, then Import" in lua.eval("R2F.L.EMPTY_LIBRARY"), "open: the empty-library text points at Options > Import")


def test_sell_batches_and_chat_secret():
    """0.55.2: selling many grey items goes a few at a time until the bags are clean; copy chat skips lines the
    game keeps secret instead of coming up blank; the selected class circle gets a gold ring."""
    lua = new_runtime()
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    lua.execute("""
      SOLD = {}
      BAGS = { [0] = {} }
      for i = 1, 11 do BAGS[0][i] = { quality = 0, hasNoValue = false, stackCount = 1, hyperlink = 'g' .. i, itemID = i } end
      C_Container = { GetContainerNumSlots = function(b) return b == 0 and #BAGS[0] or 0 end,
        GetContainerItemInfo = function(b, s) local it = BAGS[b] and BAGS[b][s] if it and not it.sold then return it end end,
        UseContainerItem = function(b, s) table.insert(SOLD, b .. ':' .. s) BAGS[b][s].sold = true end }
      GetItemInfo = function(link) return link, link, 0, 0, 0, '', '', 1, '', 0, 10 end
      R2F.Gameplay.SetOn('sellgray', true)
    """)
    T.chat = lua.table()
    T.fire("MERCHANT_SHOW")
    check(lua.eval("#SOLD") <= 4, "sell batches: the first visit sends at most 4 at once (%s)" % lua.eval("#SOLD"))
    for _ in range(12):
        T.runTimers()
    check(lua.eval("#SOLD") == 11, "sell batches: all 11 grey items are sold without talking to the vendor again (%s)" % lua.eval("#SOLD"))
    check("sold 11 grey items for 1s 10c." in chat_all(lua), "sell batches: one summary line: %r" % chat_all(lua))
    # An item the game refuses to sell is tried twice, then left alone (no endless loop).
    lua.execute("""
      SOLD = {} BAGS = { [0] = { { quality = 0, hasNoValue = false, stackCount = 1, hyperlink = 'stuck', itemID = 99 } } }
      C_Container.UseContainerItem = function(b, s) table.insert(SOLD, b .. ':' .. s) end
    """)
    T.fire("MERCHANT_CLOSED")
    T.fire("MERCHANT_SHOW")
    for _ in range(6):
        T.runTimers()
    check(lua.eval("#SOLD") == 2, "sell batches: an item that will not sell is tried twice, then skipped (%s)" % lua.eval("#SOLD"))

    # Copy chat with a line the game keeps secret.
    lua2, T2 = copychat_runtime()
    lua2.execute("issecretvalue = function(v) return v == 'line 100' end")
    lua2.execute("CCF = R2F.CopyChat.Frames()[1].frame CCT, CCN, CCH = R2F.CopyChat.Text(CCF, true, 200)")
    check(lua2.eval("CCH") == 1 and lua2.eval("CCN") == 199 and "line 100" not in lua2.eval("CCT"),
          "copy chat: a secret line is skipped and counted (%s read, %s hidden)" % (lua2.eval("CCN"), lua2.eval("CCH")))
    lua2.execute("issecretvalue = function() return true end")
    lua2.execute('SlashCmdList.R2F("copychat")')
    lua2.execute("""for _, f in ipairs(TEST.allFrames) do if f.__kind == 'EditBox' and f.__parent and f.__parent.__name == 'R2FCopyChatScroll' then CCE2 = f end end""")
    check("does not let addons read" in lua2.eval("CCE2 and CCE2:GetText() or ''"), "copy chat: when nothing is readable the window says why instead of staying blank")


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
    check(body.count("pcall(C_Traits.PurchaseRank") == 1 and body.count("pcall(C_Traits.CommitConfig") == 2,
          "both writes are pcall-wrapped (CommitConfig twice: the first ask and the retry)")
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
    talent API in any other file; the addon never writes to Blizzard frames."""
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
    toc = open(os.path.join(ADDON, "RoadToForever.toc"), encoding="utf-8").read()
    check("UI\\TalentPanel.lua" in toc and "TalentGuide" not in toc, "TalentPanel.lua in the TOC, TalentGuide gone")
    check(not os.path.exists(os.path.join(ADDON, "UI", "TalentGuide.lua")), "UI/TalentGuide.lua is deleted")
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
    check([i[0] for i in items] == ["ANY/Zoom", "ANY/HideGuild", "ANY/HidePvP", None, None],
          "the three macro ids, then the 24-hour clock and the weather box with no site macro: %s" % items)
    check(items[3][1:] == ("timeMgrUseMilitaryTime", "1", "0"), "24-hour clock = timeMgrUseMilitaryTime 1 / 0")
    check(lua.eval("R2F.QuickSettings.HidesMacro(nil)") in (None, False), "an item with no macro hides no macro")
    lua.execute("TEST.cvars.timeMgrUseMilitaryTime = '0'")
    clear()
    lua.execute("R2F.QuickSettings.Toggle(R2F.QuickSettings.ITEMS[4])")
    check(lua.eval("TEST.cvars.timeMgrUseMilitaryTime") == "1" and lua.eval("R2F.QuickSettings.IsOn(R2F.QuickSettings.ITEMS[4])") is True,
          "24-hour clock box turns the game clock to 24 hours: %s" % writes())
    lua.execute("R2F.QuickSettings.Toggle(R2F.QuickSettings.ITEMS[4])")
    check(lua.eval("TEST.cvars.timeMgrUseMilitaryTime") == "0", "and back to 12 hours")
    check(items[4][1:] == ("weatherDensity", "0", None), "no weather = weatherDensity 0, off = the game's own default")
    clear()
    lua.execute("R2F.QuickSettings.Toggle(R2F.QuickSettings.ITEMS[5])")
    check(lua.eval("TEST.cvars.weatherDensity") == "0" and lua.eval("R2F.QuickSettings.IsOn(R2F.QuickSettings.ITEMS[5])") is True,
          "no weather box sets weatherDensity 0: %s" % writes())
    lua.execute("R2F.QuickSettings.Toggle(R2F.QuickSettings.ITEMS[5])")
    check(lua.eval("TEST.cvars.weatherDensity") == "3", "and unticking gives the game's own default back")
    clear()
    items = items[:3]
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
    check(lua.eval("R2F.MainWindow.CurrentTab()") == "home", "%s: /r2f settings opens Home (settings live there)" % tag)
    n = find_frames(lua, "f.qsItem ~= nil", "QSB")
    check(n == 5, "%s: five Quick settings boxes on the Settings tab (%d)" % (tag, n))
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
    check(lua.eval("R2F.Home.MacroLine()").startswith("%d macros in your library" % (total + 3)),
          "the library count still counts the whole library")

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
           and g not in ("SLASH_R2F1", "SLASH_R2FT1", "SLASH_R2FBIZ1", "SLASH_R2FBIZ2", "SLASH_R2FWAY1", "TomTom") and g not in BINDING_GLOBALS]
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
    test_unknown_events()
    test_bundle(fx)
    test_planner()
    test_talent_cache_and_clear()
    test_dungeon_entrances()
    test_worn_enchant()
    test_corpse_arrow()
    test_arrow_3d()
    test_talented_perk()
    test_bags()
    test_reminders()
    test_plan(True)
    test_plan(False)
    test_biz(True)
    test_biz(False)
    test_ranks()
    test_gameplay()
    test_gameplay_extras()
    test_combat_banner()
    test_recorder()
    test_setup()
    test_route_log()
    test_action_bars()
    test_gameplay_quests()
    test_copychat()
    test_questzone()
    test_reactalert()
    test_gossipshop()
    test_tracking()
    test_aura_probe()
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
    test_talent_calc()
    test_talent_data_fresh()
    test_enchant_tooltip()
    test_open_command()
    test_sell_batches_and_chat_secret()
    test_talent_sandbox_ui(True)
    test_talent_sandbox_ui(False)
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
    test_gearscore()
    test_training()
    test_class_timers()
    test_timers_in_combat()
    test_training_forever_shape()
    test_item_api_modern()
    test_own_spec()
    test_arrow_follows_plan()
    test_route_weapons()
    test_quest_weapons()
    print("%d checks passed, %d failed" % (PASSES, len(FAILS)))
    sys.exit(1 if FAILS else 0)


GS_LUA = """
  -- Items by link: stats, equip location, armor class / subclass.
  TEST.gsItems = {
    helmA = { stats = { ITEM_MOD_AGILITY_SHORT = 10, ITEM_MOD_STAMINA_SHORT = 10 }, loc = 'INVTYPE_HEAD', cls = 4, sub = 2 },
    helmB = { stats = { ITEM_MOD_AGILITY_SHORT = 4, ITEM_MOD_STAMINA_SHORT = 6 }, loc = 'INVTYPE_HEAD', cls = 4, sub = 2 },
    plate = { stats = { ITEM_MOD_AGILITY_SHORT = 30 }, loc = 'INVTYPE_CHEST', cls = 4, sub = 4 },
    mail = { stats = { ITEM_MOD_AGILITY_SHORT = 30 }, loc = 'INVTYPE_CHEST', cls = 4, sub = 3 },
    ringA = { stats = { ITEM_MOD_AGILITY_SHORT = 8 }, loc = 'INVTYPE_FINGER', cls = 4, sub = 0 },
    ringLo = { stats = { ITEM_MOD_AGILITY_SHORT = 2 }, loc = 'INVTYPE_FINGER', cls = 4, sub = 0 },
    ringHi = { stats = { ITEM_MOD_AGILITY_SHORT = 20 }, loc = 'INVTYPE_FINGER', cls = 4, sub = 0 },
    odd = { stats = { ITEM_MOD_NEW_THING = 5 }, loc = 'INVTYPE_NECK', cls = 4, sub = 0 },
    potion = { stats = {}, loc = '', cls = 0, sub = 1 },
    helmNotLoaded = { loc = 'INVTYPE_HEAD', cls = 4, sub = 2 },
  }
  TEST.worn = {}
  GetItemStats = function(link) local it = TEST.gsItems[link] return it and it.stats end
  GetItemInfoInstant = function(link) local it = TEST.gsItems[link]
    if it then return 1, '', '', it.loc, '', it.cls, it.sub end end
  GetInventoryItemLink = function(unit, slot) return TEST.worn[slot] end
  ITEM_MOD_NEW_THING = 'Agility'
  TEST.className, TEST.classToken = 'Hunter', 'HUNTER'
"""


def test_gearscore():
    """GearScore (BiZ score): weights, scoring, equipped comparison, armor rules, tooltip line, bag markers."""
    lua = new_runtime(True)
    lua.execute("TEST.reset()")
    lua.execute(GS_LUA)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    GS = lua.eval("R2F.GearScore")
    w = lua.eval("R2F.GearScore.ParseWeights('hit 1.2, mana per 5 sec 1.8, Agility 1')")
    check(w["hit"] == 1.2 and w["mana per 5 sec"] == 1.8 and w["Agility"] == 1, "gs: weights parsed from ForeverDB's line")
    names = set()
    for sp in json.load(open(os.path.join(ROOT, "bis-data.json"), encoding="utf-8"))["specs"].values():
        for part in sp["weights"].split(", "):
            names.add(part.rsplit(" ", 1)[0])
    school = {n for n in names if n.endswith("Damage Done")}
    missing = sorted(n for n in names - school if lua.eval("R2F.GearScore.KEYS[%r]" % n) is None)
    check(not missing, "gs: every weight name in the data has stat keys (school damage uses the label fallback): %s" % missing)

    spec = lua.eval("R2F.GearScore.SpecId()")
    check(spec == "hunter/beast-mastery", "gs: scores with your class's spec from Mr.BiZ (first until picked): %s" % spec)
    lua.execute("R2F.BiZ.SetSpec('hunter/marksmanship') R2F.BiZ.SetClass('mage')")
    check(lua.eval("R2F.GearScore.SpecId()") == "hunter/marksmanship", "gs: browsing another class in Mr.BiZ doesn't change it")
    wts = lua.eval("R2F.GearScore.ParseWeights(R2F.BiZData.specs['hunter/marksmanship'].weights)")
    agi, sta = wts["Agility"] or 0, wts["Stamina"] or 0
    want = round(10 * agi + 10 * sta, 1)
    check(abs(lua.eval("R2F.GearScore.Score('helmA')") - want) < 0.051, "gs: score = stats x weights (%s)" % want)
    check(abs(lua.eval("R2F.GearScore.Score('odd')") - round(5 * agi, 1)) < 0.051,
          "gs: an unknown stat key whose label is a weight name still counts")
    check(lua.eval("R2F.GearScore.Score('nothing')") is None, "gs: no stats from the game = no score")

    # Equipped comparison
    lua.execute("TEST.worn[1] = 'helmB'")
    s, d = lua.eval("R2F.GearScore.Compare('helmA')")
    check(d is not None and d > 0 and lua.eval("R2F.GearScore.Direction('helmA')") == 1, "gs: better than the worn head = upgrade (+%s)" % d)
    check(lua.eval("R2F.GearScore.Direction('helmB')") is None, "gs: the same item as worn = no marker")
    lua.execute("TEST.worn[11] = 'ringHi' TEST.worn[12] = 'ringLo'")
    check(lua.eval("R2F.GearScore.Direction('ringA')") == 1, "gs: rings compare with the weaker of the two")
    lua.execute("TEST.worn[11] = nil TEST.worn[12] = nil")
    check(lua.eval("R2F.GearScore.Direction('ringLo')") == 1, "gs: an empty slot counts as 0, so anything is an upgrade")
    lua.execute("TEST.worn[1] = 'helmA'")
    check(lua.eval("R2F.GearScore.Direction('helmB')") == -1, "gs: worse than worn = downgrade")

    check(lua.eval("R2F.GearScore.Compare('potion')") is None, "gs: a potion (no gear slot) gets no score")
    lua.execute("TEST.worn[1] = 'helmNotLoaded'")
    s2, d2 = lua.eval("R2F.GearScore.Compare('helmA')")
    check(s2 is not None and d2 is None and lua.eval("R2F.GearScore.Direction('helmA')") is None,
          "gs: a worn item the game hasn't loaded yet = no comparison, no arrow")
    lua.execute("TEST.worn[1] = 'helmA'")

    # Armor rules
    lua.execute("TEST.level = 30")
    check(lua.eval("R2F.GearScore.CanWear('mail')") is False and lua.eval("R2F.GearScore.CanWear('plate')") is False
          and lua.eval("R2F.GearScore.Direction('mail')") is None, "gs: a level 30 Hunter gets no marker on mail or plate")
    lua.execute("TEST.level = 40")
    check(lua.eval("R2F.GearScore.CanWear('mail')") is True and lua.eval("R2F.GearScore.CanWear('plate')") is False,
          "gs: from 40 a Hunter wears mail, never plate")
    check(lua.eval("R2F.GearScore.CanWear('ringA')") is True, "gs: rings / necks are for everyone")

    # Tooltip line (only with the switch on)
    lua.execute("TIP = { lines = {}, GetItem = function() return 'Helm', 'helmB' end, "
                "AddLine = function(self, t, r, g, b) table.insert(self.lines, { t, r, g, b }) end, Show = function() end }")
    lua.execute("R2F.GearScore.OnTooltip(TIP)")
    check(lua.eval("#TIP.lines") == 0, "gs: no tooltip line while Upgrade arrows is off")
    lua.execute("R2F.Gameplay.SetOn('upgrades', true) R2F.GearScore.OnTooltip(TIP)")
    line = lua.eval("TIP.lines[1] and TIP.lines[1][1]") or ""
    check(line.startswith("BiZ score ") and "Marksmanship" in line and "vs equipped" in line and lua.eval("TIP.lines[1][2]") > 0.9,
          "gs: tooltip line with the score, the spec and a red 'vs equipped': %r" % line)

    # Bag markers on a classic bag window
    lua.execute("""
      ContainerFrame1 = CreateFrame('Frame', 'ContainerFrame1', UIParent)
      ContainerFrame1.GetID = function() return 0 end
      for j = 1, 3 do
        local b = CreateFrame('Button', 'ContainerFrame1Item' .. j, ContainerFrame1)
        b.GetID = function() return j end
      end
      ContainerFrame1Item3:Hide()
      TEST.bagLinks = { [0] = { 'helmA', 'mail', 'ringLo' } }
      C_Container = C_Container or {}
      C_Container.GetContainerItemLink = function(bag, slot) return TEST.bagLinks[bag] and TEST.bagLinks[bag][slot] end
      TEST.worn[1] = 'helmB' TEST.level = 30
    """)
    n = len(lua_table_to_list(lua.eval("R2F.GearScore.BagButtons()")))
    check(n == 2, "gs: only shown item buttons are scanned (%d)" % n)
    lua.execute("R2F.GearScore.UpdateBags()")
    def shown(j):
        return lua.eval("(function() local m = R2F.GearScore.MarkerOf(ContainerFrame1Item%d) return m and m:IsShown() end)()" % j)
    check(shown(1) is True, "gs: the better helm gets a marker")
    check(shown(2) in (None, False), "gs: mail a level 30 Hunter can't wear gets none")
    check(lua.eval("R2F.GearScore.MarkerOf(ContainerFrame1Item3)") is None, "gs: a hidden button gets nothing")
    lua.execute("R2F.Gameplay.SetOn('upgrades', false) R2F.GearScore.UpdateBags()")
    check(shown(1) is False, "gs: switching Upgrade arrows off hides the markers")
    find = lua.eval("(function() for _, p in ipairs(R2F.GameplayTab.PAGES) do if p.key == 'bags' then for _, k in ipairs(p.features) do if k == 'upgrades' then return true end end end end end)()")
    check(find is True, "gs: the switch is on Tweaks > Bags")
    check(lua.eval("R2F.Library.db.gameplay.upgrades") is False, "gs: off by default (like every Tweaks feature)")


def test_own_spec():
    """The spec the arrows, the tooltip score and Mr.BiZ's first view use is the one you play (your most-spent
    talent tree), not the first spec in the Mr.BiZ list (Warrior: Protection)."""
    lua = new_runtime()
    lua.execute("R2FDB = nil R2FCharDB = nil R2F.Library.Init() R2F.playerClass = 'WARRIOR'")
    def trees(a, b, c):
        return ("R2F.Talents.ReadTrees = function() return { { {rank=%d} }, { {rank=%d} }, { {rank=%d} } } end "
                "R2F.BiZ.ForgetOwnSpec()") % (a, b, c)
    lua.execute(trees(0, 0, 0))
    check(lua.eval("R2F.BiZ.OwnSpec()") is None and lua.eval("R2F.GearScore.SpecId()") == "warrior/protection",
          "own spec: with no talent points it falls back to the list's first spec")
    lua.execute(trees(21, 3, 0))
    check(lua.eval("R2F.BiZ.OwnSpec()") == "warrior/arms", "own spec: most points in the first tree = Arms")
    check(lua.eval("R2F.GearScore.SpecId()") == "warrior/arms", "own spec: the upgrade arrows compare against Arms")
    check(lua.eval("R2F.BiZ.SpecId()") == "warrior/arms", "own spec: Mr.BiZ opens on Arms for an Arms warrior")
    lua.execute("R2F.BiZ.SetSpec('warrior/protection')")
    check(lua.eval("R2F.BiZ.SpecId()") == "warrior/protection" and lua.eval("R2F.GearScore.SpecId()") == "warrior/arms",
          "own spec: browsing Protection in Mr.BiZ does not change what the arrows use")
    lua.execute(trees(0, 26, 0))
    check(lua.eval("R2F.GearScore.SpecId()") == "warrior/fury", "own spec: points change -> Fury once the cache is dropped")
    lua.execute("R2F.playerClass = 'DRUID'")
    lua.execute(trees(0, 9, 3))
    check(lua.eval("R2F.BiZ.OwnSpec()") == "druid/feral", "own spec: 'Feral Combat' maps to druid/feral")
    lua.execute("R2F.playerClass = 'HUNTER'")
    lua.execute(trees(4, 0, 0))
    check(lua.eval("R2F.BiZ.OwnSpec()") == "hunter/beast-mastery", "own spec: 'Beast Mastery' maps to hunter/beast-mastery")


def test_arrow_follows_plan():
    """Ticking the plan step you are on points the arrow at the next step that has a known position."""
    lua, T = plan_runtime(True, True, True)
    lua.execute("""
      PLAN = R2F.Plan.Selected()
      FOUND = nil
      local steps = R2F.Plan.Steps(PLAN)
      local function first(s)
        for _, pt in ipairs(R2F.Plan.Points(s.id, PLAN)) do
          if R2F.Plan.HasPosition(pt) and R2F.Plan.ResolveMap(pt.zone, pt.mapHint) then return pt end
        end
      end
      for i = 1, #steps do
        local a = first(steps[i])
        if a then
          -- everything before step i is ticked, so step i is the one you are on
          for j = 1, i - 1 do R2F.Plan.SetDone(steps[j].id, true) end
          for k = i + 1, #steps do
            local b = first(steps[k])
            if b and b.label ~= a.label then FOUND = { a = a, b = b, sa = steps[i], sb = steps[k], mid = { i + 1, k - 1 } } break end
          end
          break
        end
      end
    """)
    check(lua.eval("FOUND ~= nil"), "arrow follows: found two plan steps with known positions")
    lua.execute("R2F.Library.db.gameplay.navfollow = true R2F.Nav.Clear() R2F.Plan.Waypoint(FOUND.a, FOUND.sa.id)")
    check(lua.eval("R2F.Nav.Target().label") == lua.eval("FOUND.a.label"), "arrow follows: the Waypoint button points at the step")
    # steps between a and b that have no position are passed over, everything between is ticked first
    lua.execute("for i = FOUND.mid[1], FOUND.mid[2] do R2F.Plan.SetDone(R2F.Plan.Steps(PLAN)[i].id, true) end")
    lua.execute("R2F.Plan.SetDone(FOUND.sa.id, true)")
    check(lua.eval("R2F.Nav.Target() ~= nil and R2F.Nav.Target().label") == lua.eval("FOUND.b.label"),
          "arrow follows: ticking the step moves the arrow to the next one with a position")
    # off: ticking does nothing to the arrow
    lua.execute("R2F.Library.db.gameplay.navfollow = false R2F.Nav.Clear() R2F.Plan.Waypoint(FOUND.a, FOUND.sa.id) R2F.Plan.SetDone(FOUND.sa.id, false) R2F.Plan.SetDone(FOUND.sa.id, true)")
    check(lua.eval("R2F.Nav.Target().label") == lua.eval("FOUND.a.label"), "arrow follows: switched off, ticking leaves the arrow alone")
    check(lua.eval("R2F.Gameplay.IsOn('navfollow')") is False, "arrow follows: the switch reads off")
    lua2, _ = plan_runtime(True, True, True)
    check(lua2.eval("R2F.Gameplay.IsOn('navfollow')") is True, "arrow follows: on by default for a new character")


def test_training_forever_shape():
    """Forever's trainer API (Blizzard's own trainer window, blizzard_trainerui): GetTrainerServiceInfo returns
    name, serviceType ('available' | 'unavailable' | 'used'), texture, reqLevel, subText (the rank), category.
    There is no GetTrainerServiceLevelReq. The level must come from the 4th return, the rank from the 5th."""
    lua = new_runtime(True)
    lua.execute("TEST.reset()")
    lua.execute("""
      TEST.level = 20
      TEST.trainer = {
        { 'Corruption', 'available', 'tex1', 14, 'Rank 2', 'Affliction', 600 },
        { 'Curse of Doom', 'unavailable', 'tex2', 60, '', 'Affliction', 90000 },
        { 'Shadow Bolt', 'unavailable', 'tex3', 22, 'Rank 4', 'Shadow', 1500 },
        { 'Siphon Life', 'unavailable', 'tex5', 22, 'Rank 1', 'Affliction', 2200 },
        { 'Fear', 'unavailable', 'tex6', 22, 'Rank 2', 'Fear', 1800 },
        { 'Drain Soul', 'unavailable', 'tex7', 22, 'Rank 2', 'Affliction', 1700 },
        { 'Immolate', 'used', 'tex4', 1, 'Rank 1', 'Fire', 50 },
      }
      GetNumTrainerServices = function() return #TEST.trainer end
      GetTrainerServiceInfo = function(i) local t = TEST.trainer[i] return t[1], t[2], t[3], t[4], t[5], t[6] end
      GetTrainerServiceLevelReq = nil
      GetTrainerServiceCost = function(i) return TEST.trainer[i][7], false end
      IsTradeskillTrainer = function() return false end
    """)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    T.fire("TRAINER_SHOW")
    check(lua.eval("#R2FCharDB.training.spells") == 7, "train (Forever API): all seven services are saved")
    check(lua.eval("R2FCharDB.training.spells[1].lvl") == 14 and lua.eval("R2FCharDB.training.spells[1].r") == "Rank 2"
          and lua.eval("R2FCharDB.training.spells[1].s") == "available",
          "train (Forever API): level from the 4th return, rank from the 5th, state from the 2nd")
    a, b = lua.eval("R2F.Training.Lines()")
    check(a.startswith("Train now: 1 spell") and "Corruption (Rank 2)" in a, "train (Forever API): level 14 spell is trainable at 20: %r" % a)
    check(b.startswith("Next: level 22: ") and all(n in b for n in ("Drain Soul (Rank 2)", "Fear (Rank 2)", "Shadow Bolt (Rank 4)", "Siphon Life (Rank 1)"))
          and "more" not in b, "train (Forever API): next lists every spell of the next level, no 'and N more': %r" % b)
    # An older saved line without a rank next to the ranked one (the trainer names "Rank 2" only once rank 1 is known)
    # must not show twice, neither on Home nor after the next trainer visit.
    lua.execute("table.insert(R2FCharDB.training.spells, { n = 'Fear', r = '', lvl = 22, cost = 0, s = 'unavailable' })")
    _, b2 = lua.eval("R2F.Training.Lines()")
    check(b2.count("Fear") == 1, "train: an older rank-less copy of a spell is not listed twice on Home: %r" % b2)
    T.fire("TRAINER_SHOW")
    check(lua.eval("#R2FCharDB.training.spells") == 7, "train: a trainer visit drops the older rank-less copy")


def test_class_timers():
    """Seal timer (Paladin) and Slice and Dice timer (Rogue): the seconds left on the buff, the buff's own icon, gone when
    the buff is off (locked), only for that class."""
    for token, key, frame, aura, other in (("PALADIN", "seal", "R2FSealFrame", "Seal of Command", "R2FSliceanddiceFrame"),
                                           ("ROGUE", "sliceanddice", "R2FSliceanddiceFrame", "Slice and Dice", "R2FSealFrame")):
        lua, T = reminder_runtime(token)
        lua.execute("""TEST.now = 500 TEST.aura = { name = '%s', spellId = 77, expirationTime = 520, icon = 'buffIcon' }
          GetTime = function() return TEST.now end
          C_UnitAuras = { GetUnitAuras = function() if TEST.aura then return { TEST.aura } end return {} end }
          for _, d in ipairs(R2F.Timers.TRACK) do if d.key == '%s' then TD = d end end
          TD.module.SetLock(true) TD.module.Apply()""" % (aura, key))
        check(lua.eval("%s ~= nil" % frame) and lua.eval("%s == nil" % other), "%s timer: only this class gets the icon" % key)
        check(lua.eval("%s:IsShown()" % frame) is True and lua.eval("%s.count.__text" % frame) == "20", "%s timer: 20 seconds left" % key)
        check(lua.eval("%s.icon.__tex" % frame) == "buffIcon", "%s timer: the buff's own icon" % key)
        lua.execute("TEST.aura = nil TD.module.Apply()")
        check(lua.eval("%s:IsShown()" % frame) is False, "%s timer: buff off, locked: hidden" % key)
        lua.execute("TD.module.SetLock(false)")
        check(lua.eval("%s:IsShown()" % frame) is True, "%s timer: unlocked it shows so it can be moved" % key)
        lua.execute("TD.module.SetShown(false)")
        check(lua.eval("%s:IsShown()" % frame) is False, "%s timer: switched off" % key)
        names = lua.eval("(function() local t = {} for _, d in ipairs(R2F.Reminders.ForPlayer()) do t[#t + 1] = d.key end return table.concat(t, ',') end)()")
        check(key in names.split(","), "%s timer: its section is on the Class icons page: %s" % (key, names))
    lua, T = reminder_runtime("MAGE")
    names = lua.eval("(function() local t = {} for _, d in ipairs(R2F.Reminders.ForPlayer()) do t[#t + 1] = d.key end return table.concat(t, ',') end)()")
    check("seal" not in names.split(",") and "sliceanddice" not in names.split(","), "class timers: not for a Mage")


def test_timers_in_combat():
    """The seal / Slice and Dice timers keep going in a fight when the game hides auras (2026-10-16): another hidden aura
    does not hide ours, a hidden buff of ours is counted down from the last readable look with a "~", a recast restarts the
    estimate, and a readable list without the buff clears it."""
    lua, T = reminder_runtime("PALADIN")
    lua.execute("""TEST.now = 500 SECRET = {}
      issecretvalue = function(v) return v == 'SECRET' end
      GetTime = function() return TEST.now end
      TEST.auras = { { name = 'Seal of Command', spellId = 77, expirationTime = 2300, duration = 1800, icon = 'sealIcon' } }
      C_UnitAuras = { GetUnitAuras = function() return TEST.auras end }
      C_Spell = { GetSpellName = function(id) if id == 77 then return 'Seal of Command' end end }
      for _, d in ipairs(R2F.Timers.TRACK) do if d.key == 'seal' then TD = d end end
      TD.module.SetLock(true) TD.module.Apply()""")
    check(lua.eval("R2FSealFrame.count.__text") == "1800", "combat timer: readable out of combat: 1800 s")
    # Another aura is hidden by the game, ours is still readable further down the list.
    lua.execute("TEST.auras = { { name = 'SECRET', spellId = 'SECRET', expirationTime = 'SECRET' }, "
                "{ name = 'Seal of Command', spellId = 77, expirationTime = 2300, duration = 1800, icon = 'sealIcon' } } TD.module.Apply()")
    check(lua.eval("R2FSealFrame:IsShown()") is True and lua.eval("R2FSealFrame.count.__text") == "1800",
          "combat timer: a hidden aura elsewhere in the list does not hide ours")
    # Ours is hidden too: count down from the last look, marked with ~.
    lua.execute("TEST.auras = { { name = 'Seal of Command', spellId = 77, expirationTime = 'SECRET', icon = 'x' } } TEST.now = 520 TD.module.Apply()")
    check(lua.eval("R2FSealFrame:IsShown()") is True and lua.eval("R2FSealFrame.count.__text") == "~1780",
          "combat timer: hidden buff: counts down from the last look, marked ~: %r" % lua.eval("R2FSealFrame.count.__text"))
    check(lua.eval("R2FSealFrame.icon.__tex") == "sealIcon", "combat timer: the estimate keeps the seal's icon")
    # Recast in the fight (a new seal): the estimate restarts from the last full duration.
    lua.execute("TEST.now = 600 R2F.Timers.OnCast(77) TD.module.Apply()")
    check(lua.eval("R2FSealFrame.count.__text") == "~30", "combat timer: casting the seal again restarts the estimate")
    lua.execute("R2F.Timers.OnCast(999) TD.module.Apply()")
    check(lua.eval("R2FSealFrame.count.__text") == "~30", "combat timer: another spell changes nothing")
    # The estimate runs out: nothing is shown.
    lua.execute("TEST.now = 2500 TD.module.Apply()")
    check(lua.eval("R2FSealFrame:IsShown()") is False, "combat timer: estimate past its end: hidden")
    # Out of combat again, list readable, buff not on you: cleared (a later hidden look has nothing to count from).
    lua.execute("TEST.now = 600 TEST.auras = {} TD.module.Apply()")
    lua.execute("TEST.auras = { { name = 'Seal of Command', spellId = 77, expirationTime = 'SECRET' } } TD.module.Apply()")
    check(lua.eval("R2FSealFrame:IsShown()") is False, "combat timer: buff gone while readable: no old estimate comes back")
    # The whole aura call fails in the fight: same estimate from the last look.
    lua.execute("TEST.now = 600 TEST.auras = { { name = 'Seal of Command', spellId = 77, expirationTime = 2300, duration = 1800 } } "
                "TD.module.Apply() TEST.now = 610 C_UnitAuras.GetUnitAuras = function() error('restricted') end TD.module.Apply()")
    check(lua.eval("R2FSealFrame.count.__text") == "~1690", "combat timer: the aura call failing: still counts from the last look: %r" % lua.eval("R2FSealFrame.count.__text"))
    # A seal swapped in the fight shows the NEW seal's icon and a fresh 30 seconds, even when the first one was never seen
    # (the aura is hidden): the timer must not stay on the first seal.
    lua.execute("""TEST.now = 700 TEST.auras = { { name = 'SECRET', spellId = 'SECRET', expirationTime = 'SECRET' } }
      C_Spell.GetSpellName = function(id) return ({ [77] = 'Seal of Command', [78] = 'Seal of Righteousness' })[id] end
      C_Spell.GetSpellTexture = function(id) return 'tex' .. id end
      R2F.playerClass = 'PALADIN'
      R2F.Timers.OnCast(77) TD.module.Apply()""")
    check(lua.eval("R2FSealFrame.icon.__tex") == "tex77" and lua.eval("R2FSealFrame.count.__text") == "~30",
          "combat timer: first seal cast in the fight, never seen: icon and 30 seconds")
    lua.execute("TEST.now = 705 R2F.Timers.OnCast(78) TD.module.Apply()")
    check(lua.eval("R2FSealFrame.icon.__tex") == "tex78" and lua.eval("R2FSealFrame.count.__text") == "~30",
          "combat timer: the next seal replaces the first one's icon and time: %r" % lua.eval("R2FSealFrame.icon.__tex"))
    # Nothing ever seen and everything hidden: nothing shown (never a guess).
    lua2, _ = reminder_runtime("ROGUE")
    lua2.execute("""issecretvalue = function(v) return v == 'SECRET' end GetTime = function() return 10 end
      C_UnitAuras = { GetUnitAuras = function() return { { name = 'SECRET', spellId = 'SECRET' } } end }
      for _, d in ipairs(R2F.Timers.TRACK) do if d.key == 'sliceanddice' then SD = d end end
      SD.module.SetLock(true) SD.module.Apply()""")
    check(lua2.eval("R2FSliceanddiceFrame:IsShown()") is False, "combat timer: nothing seen before and all hidden: nothing shown")
    # Slice and Dice cast in the fight with 3 combo points: 6 + 3 x 3 = 15 seconds, its own icon.
    lua2.execute("""C_Spell = { GetSpellName = function(id) if id == 5171 then return 'Slice and Dice' end end,
        GetSpellTexture = function() return 'sndTex' end }
      GetComboPoints = function() return 3 end
      R2F.playerClass = 'ROGUE'
      R2F.Timers.OnSent() R2F.Timers.OnCast(5171) SD.module.Apply()""")
    check(lua2.eval("R2FSliceanddiceFrame:IsShown()") is True and lua2.eval("R2FSliceanddiceFrame.count.__text") == "~15"
          and lua2.eval("R2FSliceanddiceFrame.icon.__tex") == "sndTex",
          "combat timer: Slice and Dice cast in a fight with 3 points: ~15 s and its icon: %r" % lua2.eval("R2FSliceanddiceFrame.count.__text"))
    # The debug tool reports what is readable.
    T2 = lua2.eval("TEST")
    T2.chat = lua2.table()
    lua2.execute("R2F.DEBUG.timers()")
    check("1 hidden by the game" in chat_all(lua2) or "hidden by the game" in chat_all(lua2), "combat timer: /r2f debug timers prints the hidden count")


def test_recorder():
    """The recorder writes down what loot, vendor and quest windows show (R2FDB.recorder), counts a corpse once, ignores players,
    can be switched off, and never raises when the game gives something odd."""
    lua, T = reminder_runtime("MAGE")
    lua.execute("""
      LOOT = { { link = '|cff1eff00|Hitem:7684::::|h[Bloodmage Mantle]|h|r', src = { 'Creature-0-1465-0-4-4278-0000AAAA11', 1 } },
               { link = '|Hitem:159::::|h[Water]|h', src = { 'Creature-0-1465-0-4-4278-0000AAAA11', 1 } },
               { link = nil, src = { 'Creature-0-1465-0-4-4278-0000AAAA11', 1 } } }
      GetNumLootItems = function() return #LOOT end
      GetLootSlotLink = function(i) return LOOT[i].link end
      GetLootSourceInfo = function(i) return unpack(LOOT[i].src) end
      GetRealZoneText = function() return 'Shadowfang Keep' end
      UnitGUID = function(u) if u == 'target' then return 'Creature-0-1465-0-4-4278-0000AAAA11' end if u == 'npc' then return 'Creature-0-1-0-4-8128-0000BBBB22' end end
      UnitLevel = function() return 24 end""")
    T.fire("LOOT_OPENED")
    check(lua.eval("R2FDB.recorder.drops[4278].k") == 1 and lua.eval("R2FDB.recorder.drops[4278].i[7684]") == 1
          and lua.eval("R2FDB.recorder.drops[4278].z") == "Shadowfang Keep" and lua.eval("R2FDB.recorder.drops[4278].lv") == 24,
          "recorder: a looted creature is written down with its item, zone and level")
    T.fire("LOOT_OPENED")
    check(lua.eval("R2FDB.recorder.drops[4278].k") == 1 and lua.eval("R2FDB.recorder.drops[4278].i[7684]") == 2,
          "recorder: the same corpse opened again is one kill (the item is seen again)")
    lua.execute("LOOT = { { link = '|Hitem:5::|h[x]|h', src = { 'Player-1-00000001', 1 } } }")
    T.fire("LOOT_OPENED")
    check(lua.eval("R2FDB.recorder.drops[5]") is None, "recorder: players are not recorded")
    lua.execute("""LOOT = { { link = '|Hitem:9::|h[x]|h', src = { 'GameObject-0-1-0-4-2843-0000CCCC33', 1 } } }""")
    T.fire("LOOT_OPENED")
    check(lua.eval("R2FDB.recorder.objects[2843].i[9]") == 1, "recorder: chests and nodes go to their own table")
    lua.execute("""GetMerchantNumItems = function() return 2 end
      GetMerchantItemLink = function(i) return ({ '|Hitem:1000::|h[A]|h', '|Hitem:2000::|h[B]|h' })[i] end
      GetMerchantItemInfo = function(i) if i == 1 then return 'A', 1, 1250, 1, -1, true, false end return 'B', 2, 0, 5, -1, true, true end""")
    T.fire("MERCHANT_SHOW")
    check(lua.eval("R2FDB.recorder.vendors[8128].i[1000].p") == 1250 and lua.eval("R2FDB.recorder.vendors[8128].i[2000].e") == 1,
          "recorder: a vendor's items, prices and extended costs")
    lua.execute("""GetQuestID = function() return 747 end GetTitleText = function() return 'The Hunt Begins' end
      GetNumQuestChoices = function() return 2 end GetNumQuestRewards = function() return 1 end
      GetQuestItemLink = function(kind, i) if kind == 'choice' then return '|Hitem:' .. (100 + i) .. '::|h[c]|h' end return '|Hitem:300::|h[r]|h' end""")
    T.fire("QUEST_COMPLETE")
    check(lua.eval("R2FDB.recorder.quests[747].c[2]") == 102 and lua.eval("R2FDB.recorder.quests[747].r[1]") == 300
          and lua.eval("R2FDB.recorder.quests[747].t") == "The Hunt Begins" and lua.eval("R2FDB.recorder.quests[747].n") == 8128,
          "recorder: a quest's choices and rewards with the title and the NPC")
    lua.execute("R2F.Recorder.SetOn(false) LOOT = { { link = '|Hitem:77::|h[x]|h', src = { 'Creature-0-1-0-4-999-0000DDDD44', 1 } } }")
    T.fire("LOOT_OPENED")
    check(lua.eval("R2FDB.recorder.drops[999]") is None, "recorder: switched off, nothing new is written")
    lua.execute("R2F.Recorder.SetOn(true) GetLootSourceInfo = function() error('boom') end")
    T.fire("LOOT_OPENED")
    check(True, "recorder: an error inside a getter never reaches the player")
    T2 = lua.eval("TEST")
    T2.chat = lua.table()
    lua.execute("R2F.DEBUG.recorder()")
    check("1 creatures looted" in chat_all(lua) and "vendors" in chat_all(lua), "recorder: /r2f debug recorder prints the counts")


def test_setup():
    """Setup Hunter: bars 2-6, auto loot, the Edit Mode layout, our macros on their buttons; skips filled buttons; undo."""
    lua, T = reminder_runtime("HUNTER")
    lua.execute("R2F.MacroData = NS.MacroDataReal R2F.Bundle.Run()")           # the macros that ship with the addon
    lua.execute("""
      TOG = { false, false, false, false, false, false, false }
      GetActionBarToggles = function() return unpack(TOG) end
      SetActionBarToggles = function(...) TOG = { ... } end
      ACTIONS = {}
      GetActionInfo = function(s) local a = ACTIONS[s] if a then return a.kind, 1 end end
      GetActionText = function(s) return ACTIONS[s] and ACTIONS[s].text end
      GetCursorInfo = function() if TEST.cursor then return 'macro', 1 end end
      ClearCursor = function() TEST.cursor = nil end
      PlaceAction = function(s) if TEST.cursor then ACTIONS[s] = { kind = 'macro', text = TEST.cursor } TEST.cursor = nil end end
      PickupAction = function(s) if ACTIONS[s] then TEST.cursor = ACTIONS[s].text ACTIONS[s] = nil end end
      BINDS = { ACTIONBUTTON3 = '2', MULTIACTIONBAR1BUTTON6 = 'E', MULTIACTIONBAR1BUTTON5 = 'Q' }
      GetBindingKey = function(cmd) return BINDS[cmd] end
      LAYOUTS = { { layoutName = 'Modern' }, { layoutName = 'Classic' }, { layoutName = 'Hunter' } }
      EditModeManagerFrame = { layoutInfo = { layouts = LAYOUTS, activeLayout = 1 } }
      SETLAYOUT = nil
      C_EditMode = { SetActiveLayout = function(i) SETLAYOUT = i EditModeManagerFrame.layoutInfo.activeLayout = i end }
      CVARS = { autoLootDefault = '0', raidFramesDisplayClassColor = '0', raidFramesDisplayPowerBars = '0', raidOptionDisplayPets = '0' }
      GetCVar = function(n) return CVARS[n] end
      SetCVar = function(n, v) CVARS[n] = v end
      function RUNTIMERS() local n = 0 while #TEST.timers > 0 and n < 400 do local l = TEST.timers TEST.timers = {} for _, f in ipairs(l) do f() end n = n + 1 end end
    """)
    check(lua.eval("R2F.Setup.Slot(1, 3)") == 3 and lua.eval("R2F.Setup.Slot(2, 6)") == 66 and lua.eval("R2F.Setup.Slot(5, 2)") == 38
          and lua.eval("R2F.Setup.Slot(3, 1)") == 49 and lua.eval("R2F.Setup.Slot(4, 1)") == 25 and lua.eval("R2F.Setup.Slot(6, 1)") == 145,
          "setup: bar and button to action slot (bar 2 = 61-72, bar 5 = 37-48, bar 6 = 145-156)")
    for k in ("Raptor+Clip", "AutoShot", "Serpent", "PetAtkMOTT", "PetFollow", "AspMonkey", "AspHawk"):
        check(lua.eval("R2F.Library.Get('HUNTER/%s') ~= nil" % k) is True, "setup: the library has the macro HUNTER/%s" % k)
    lua.execute("R2F.Setup.Execute(R2F.Setup.LIST.hunter) RUNTIMERS()")
    check(all(lua.eval("TOG[%d]" % i) is True for i in (1, 2, 3, 4, 5)) and lua.eval("TOG[6]") is False,
          "setup: Action Bars 2 to 6 are on, 7 and 8 untouched")
    check(lua.eval("CVARS.autoLootDefault") == "1", "setup: auto loot is on")
    check(all(lua.eval("CVARS.%s" % c) == "1" for c in ("raidFramesDisplayClassColor", "raidFramesDisplayPowerBars", "raidOptionDisplayPets")),
          "setup: raid frames show class colours, power bars and pets")
    check(lua.eval("SETLAYOUT") == 3, "setup: the Edit Mode layout 'Hunter' (third in the game's list after Modern and Classic) is made active")
    want = {3: "Raptor+Clip", 66: "AutoShot", 65: "Serpent", 63: "PetAtkMOTT", 69: "PetFollow", 38: "AspMonkey", 39: "AspHawk"}
    for slot, name in want.items():
        check(lua.eval("ACTIONS[%d] ~= nil and ACTIONS[%d].text" % (slot, slot)) == name, "setup: slot %d holds the macro %s" % (slot, name))
    check("placed (macros" in chat_all(lua), "setup: the chat says how many buttons were filled")
    check("should be on the key" not in chat_all(lua), "setup: no key warning when the keys are as listed")
    # Undo puts everything back.
    lua.execute("R2F.Setup.Undo()")
    check(all(lua.eval("TOG[%d]" % i) is False for i in range(1, 8)) and lua.eval("CVARS.autoLootDefault") == "0" and lua.eval("CVARS.raidOptionDisplayPets") == "0"
          and lua.eval("SETLAYOUT") == 1 and lua.eval("next(ACTIONS)") is None, "setup: undo restores the bars, auto loot, layout and empties the buttons it filled")
    # A button that holds something is left alone; a wrong key is reported; a missing layout is reported.
    lua.execute("""ACTIONS[3] = { kind = 'item', text = 'Mine' } BINDS.MULTIACTIONBAR1BUTTON6 = 'F' LAYOUTS[3].layoutName = 'Other' TEST.chat = {}
      R2F.Setup.LIST.hunter.clearAll = false R2F.Setup.Execute(R2F.Setup.LIST.hunter) RUNTIMERS() R2F.Setup.LIST.hunter.clearAll = true""")
    check(lua.eval("ACTIONS[3].text") == "Mine" and "not empty" in chat_all(lua), "setup: a filled button is left alone and reported")
    # A starting spell on a target button is lifted off and put back by Undo.
    lua.execute("""R2F.Setup.Undo() ACTIONS = { [3] = { kind = 'spell', text = 'Start' } } R2F.Setup.Execute(R2F.Setup.LIST.hunter) RUNTIMERS()""")
    check(lua.eval("ACTIONS[3] ~= nil and ACTIONS[3].text") == "Raptor+Clip", "setup: a spell on a target button is cleared and the macro goes there")
    # Clear-all: every button is emptied first, even one holding a non-spell.
    lua.execute("""R2F.Setup.Undo() ACTIONS = { [3] = { kind = 'item', text = 'Mine' }, [150] = { kind = 'item', text = 'Far' } } R2F.Setup.Execute(R2F.Setup.LIST.hunter) RUNTIMERS()""")
    check(lua.eval("ACTIONS[3].text") == "Raptor+Clip" and lua.eval("ACTIONS[150]") is None, "setup: every button is emptied first, then the macros go on")
    lua.execute("""R2F.Setup.Undo() RELOADED = false CONFIRMS = {} R2F.UI.Confirm = function(t, a, b, fn) table.insert(CONFIRMS, {text=t, fn=fn}) end
      ReloadUI = function() RELOADED = true end CHATOPENED = nil ChatFrame_OpenChat = function(t) CHATOPENED = t end R2F.Setup.Execute(R2F.Setup.LIST.hunter) RUNTIMERS()""")
    check(lua.eval("#CONFIRMS") == 1 and lua.eval("RELOADED") is False, "setup: when done it offers a reload and does not reload by itself")
    lua.execute("CONFIRMS[1].fn()")
    check(lua.eval("CHATOPENED") == "/reload" and lua.eval("RELOADED") is False,
          "setup: the reload button puts /reload in the chat line (Enter runs it with the game's own code)")
    lua.execute("R2F.Setup.Undo()")
    check("should be on the key E" in chat_all(lua), "setup: a key that differs is reported, not changed")
    check("no Edit Mode layout called" in chat_all(lua), "setup: a missing layout is reported")
    # Setup Druid, and the spell / item / General macro rows both setups share.
    lua.execute("""
      TEST.chat = {} R2F.playerClass = 'DRUID' ACTIONS = {} TEST.cursor = nil
      R2F.Ranks.Book = function() return { ['walk on air'] = { ids = { 1001 } }, ['read ley line'] = { ids = { 1002 } },
                                           ['teleport: moonglade'] = { ids = { 1003 } } } end
      GetActionInfo = function(s) local a = ACTIONS[s] if a then return a.kind, a.id or 1 end end
      GetCursorInfo = function() if TEST.cursor then return 'macro', 1 end return TEST.ckind, TEST.cid end
      ClearCursor = function() TEST.cursor = nil TEST.ckind = nil TEST.cid = nil TEST.ctext = nil end
      PlaceAction = function(s)
        if TEST.cursor then ACTIONS[s] = { kind = 'macro', text = TEST.cursor } TEST.cursor = nil
        elseif TEST.ckind then ACTIONS[s] = { kind = TEST.ckind, id = TEST.cid, text = TEST.ctext } ClearCursor() end
      end
      PickupAction = function(s) local a = ACTIONS[s] if a then TEST.ckind, TEST.cid, TEST.ctext = a.kind, a.id, a.text ACTIONS[s] = nil end end
      PickupSpell = function(id) TEST.ckind = 'spell' TEST.cid = id end
      PickupItem = function(id) TEST.ckind = 'item' TEST.cid = id end
      GetItemCount = function(id) return id == 6948 and 1 or 0 end
      TEST.addMacro('Sit', '/sit') TEST.addMacro('Mark1', '/m1') TEST.addMacro('Mark2', '/m2') TEST.addMacro('atk', '/startattack')
      KEYS = { Q = 'MULTIACTIONBAR1BUTTON5', F = 'MULTIACTIONBAR1BUTTON2' } SAVEDSET = nil
      GetBindingAction = function(k) return KEYS[k] or '' end
      SetBinding = function(k, c) KEYS[k] = c return true end
      SaveBindings = function(w) SAVEDSET = w end
      GetCurrentBindingSet = function() return 1 end
      TEST.classToken = 'DRUID'
    """)
    for k in ("HTouch", "Regrowth", "Rejuv", "Moonfire", "Wrath", "CatBear", "MotW", "Thorns"):
        check(lua.eval("R2F.Library.Get('DRUID/%s') ~= nil" % k) is True, "setup druid: the library has the macro DRUID/%s" % k)
    check(lua.eval("R2F.Setup.LIST.druid.layout") == "Warrior/Druid" and lua.eval("#R2F.Setup.LIST.druid.bars") == 5,
          "setup druid: the Warrior/Druid layout and Action Bars 2 to 6")
    lua.execute("R2F.Setup.Execute(R2F.Setup.LIST.druid) RUNTIMERS()")
    macros = {8: "HTouch", 9: "Regrowth", 10: "Rejuv", 11: "Moonfire", 12: "Wrath", 29: "CatBear", 40: "MotW", 39: "Thorns",
              145: "Sit", 146: "Mark1", 147: "Mark2"}
    for slot, name in macros.items():
        check(lua.eval("ACTIONS[%d] ~= nil and ACTIONS[%d].kind == 'macro' and ACTIONS[%d].text" % (slot, slot, slot)) == name,
              "setup druid: slot %d holds the macro %s" % (slot, name))
    spells = {67: 1001, 70: 1002, 52: 1003}
    for slot, sid in spells.items():
        check(lua.eval("ACTIONS[%d] ~= nil and ACTIONS[%d].kind == 'spell' and ACTIONS[%d].id" % (slot, slot, slot)) == sid,
              "setup druid: slot %d holds the spell %d" % (slot, sid))
    check(lua.eval("ACTIONS[156] ~= nil and ACTIONS[156].kind == 'item' and ACTIONS[156].id") == 6948,
          "setup druid: the Hearthstone is on bar 6 button 12")
    check(lua.eval("ACTIONS[2] ~= nil and ACTIONS[2].text") == "atk", "setup druid: the General macro atk is on the main bar button 2")
    check(lua.eval("KEYS.Q") == "ACTIONBUTTON11" and lua.eval("KEYS.F") == "ACTIONBUTTON8" and lua.eval("KEYS['1']") == "ACTIONBUTTON2"
          and lua.eval("KEYS['6']") is None and lua.eval("SAVEDSET") == 2,
          "setup druid: the Druid key bindings are set and saved for this character (set 2), NONE unbinds")
    lua.execute("R2F.Setup.Undo()")
    check(lua.eval("next(ACTIONS)") is None, "setup druid: undo empties the macros, spells and the item it placed")
    check(lua.eval("KEYS.Q") == "MULTIACTIONBAR1BUTTON5" and lua.eval("SAVEDSET") == 1,
          "setup druid: undo puts the old key bindings back and returns to the account's set")
    # The hunter gets the same racials, Hearthstone and General macros.
    lua.execute("TEST.chat = {} TEST.classToken = 'HUNTER' R2F.playerClass = 'HUNTER' R2F.Setup.Execute(R2F.Setup.LIST.hunter) RUNTIMERS()")
    check(lua.eval("ACTIONS[67] ~= nil and ACTIONS[67].id") == 1001 and lua.eval("ACTIONS[70] ~= nil and ACTIONS[70].id") == 1002
          and lua.eval("ACTIONS[156] ~= nil and ACTIONS[156].id") == 6948 and lua.eval("ACTIONS[146] ~= nil and ACTIONS[146].text") == "Mark1",
          "setup hunter: Walk on Air, Read Ley Line, the Hearthstone and Mark1 are on the same buttons")
    lua.execute("R2F.Setup.Undo() R2F.playerClass = 'HUNTER'")
    # Combat and class guards.
    lua.execute("TEST.chat = {} R2F.inCombat = true R2F.Setup.Run('hunter') R2F.inCombat = false")
    check("not in combat" in chat_all(lua), "setup: nothing runs in combat")
    lua.execute("TEST.chat = {} R2F.playerClass = 'MAGE' R2F.Setup.Run('hunter')")
    check("hunter; log in" in chat_all(lua), "setup: another class is told to log in on a hunter")
    check(lua.eval("(function() for _, it in ipairs(R2F.Minimap.MenuItems()) do if it.text == 'Setup Hunter' then return true end end return false end)()") is False,
          "setup: no menu entry for a Mage")
    lua.execute("R2F.playerClass = 'HUNTER' LAYOUTS[3].layoutName = 'Other'")
    check(lua.eval("(function() for _, it in ipairs(R2F.Minimap.MenuItems()) do if it.text == 'Setup Hunter' then return true end end return false end)()") is False,
          "setup: a Hunter without the Edit Mode layout 'Hunter' is not offered the setup (it is for the owner's characters)")
    lua.execute("TEST.chat = {} R2F.Setup.Run('hunter')")
    check("no Edit Mode layout called" in chat_all(lua), "setup: the command says the layout is missing, before asking anything")
    lua.execute("LAYOUTS[3].layoutName = 'Hunter'")
    check(lua.eval("(function() for _, it in ipairs(R2F.Minimap.MenuItems()) do if it.text == 'Setup Hunter' then return true end end return false end)()") is True,
          "setup: the minimap menu offers 'Setup Hunter' to a Hunter")


def test_route_log():
    """The route log: off until started; quests, levels, NPCs, notes and the path go into R2FDB.route; no character name."""
    lua, T = reminder_runtime("HUNTER")
    lua.execute("""
      QUESTS = { { title = 'Wolves', level = 3, suggestedGroup = 0, isHeader = false, questID = 4001 } }
      OBJ = { { text = 'Wolf slain: 0/5', numFulfilled = 0, numRequired = 5, type = 'monster' } }
      C_QuestLog = {
        GetTitleForQuestID = function(q) return 'Wolves' end,
        GetLogIndexForQuestID = function(q) return 1 end,
        GetInfo = function(i) return QUESTS[i] end,
        GetNumQuestLogEntries = function() return #QUESTS end,
        GetQuestObjectives = function(q) return OBJ end,
      }
      POS = { 0.123, 0.456 }
      C_Map = { GetBestMapForUnit = function() return 1411 end,
                GetPlayerMapPosition = function() return { GetXY = function() return POS[1], POS[2] end } end }
      LEVEL = 3 XPNOW = 120
      UnitLevel = function() return LEVEL end
      UnitXP = function() return XPNOW end
      UnitGUID = function(u) if u == 'questnpc' then return 'Creature-0-1465-0-4-6168-000012AB34' end end
      UnitName = function(u) return 'Hunter Trainer' end
      GetQuestID = function() return 4001 end
      GetTitleText = function() return 'Wolves' end
      GetSubZoneText = function() return 'Thendal Village' end
      GetZoneText = function() return 'Zephras Isle' end
      NOW = 1000 GetServerTime = function() return NOW end
    """)
    check(lua.eval("R2F.RouteLog.IsOn()") is False and lua.eval("#R2FDB.route.runs") == 0, "route: off until started, no runs")
    lua.execute("R2F.RouteLog.OnEvent('QUEST_ACCEPTED', 1, 4001)")
    check(lua.eval("#R2FDB.route.runs") == 0, "route: nothing is written while it is off")
    lua.execute("R2F.RouteLog.Start('first walk')")
    check(lua.eval("R2F.RouteLog.IsOn()") is True and lua.eval("R2FDB.route.active") == 1 and lua.eval("R2FDB.route.runs[1].label") == "first walk",
          "route: /r2f route start begins run 1 with its name")
    check(lua.eval("R2FDB.route.runs[1].class") == "HUNTER" and lua.eval("R2FDB.route.runs[1].name") is None,
          "route: the class is stored, no character name")
    check(lua.eval("R2FDB.route.runs[1].events[2].e") == "have" and lua.eval("R2FDB.route.runs[1].events[2].q") == 4001,
          "route: a quest already in the log when it starts is written down")
    lua.execute("NOW = 1005 R2F.RouteLog.OnEvent('QUEST_DETAIL') R2F.RouteLog.OnEvent('QUEST_DETAIL')")
    check(lua.eval("R2FDB.route.runs[1].events[3].e") == "offer" and lua.eval("R2FDB.route.runs[1].events[3].npc") == 6168
          and lua.eval("R2FDB.route.runs[1].events[3].t") == 5 and lua.eval("R2FDB.route.runs[1].events[3].x") == 12.3,
          "route: an offered quest has the giver, the time since the start and the map position")
    check(lua.eval("#R2FDB.route.runs[1].events") == 3, "route: an offer reopened is written once")
    lua.execute("NOW = 1010 R2F.RouteLog.OnEvent('QUEST_ACCEPTED', 2, 4002)")
    check(lua.eval("R2FDB.route.runs[1].events[4].e") == "accept" and lua.eval("R2FDB.route.runs[1].events[4].q") == 4002
          and lua.eval("R2FDB.route.runs[1].events[4].ql") == 3 and lua.eval("R2FDB.route.runs[1].events[4].obj[1][1]") == "Wolf slain: 0/5",
          "route: an accepted quest has its level and objectives (Classic's two-argument form too)")
    lua.execute("""NOW = 1020 OBJ[1].numFulfilled = 2 GetTime = function() return 10 end R2F.RouteLog.OnEvent('QUEST_LOG_UPDATE')
      GetTime = function() return 20 end R2F.RouteLog.OnEvent('QUEST_LOG_UPDATE')""")
    check(lua.eval("#R2FDB.route.runs[1].events") == 5 and lua.eval("R2FDB.route.runs[1].events[5].e") == "prog"
          and lua.eval("R2FDB.route.runs[1].events[5].n") == 2, "route: an objective that counted up is written once, with its count")
    lua.execute("NOW = 1030 XPNOW = 400 R2F.RouteLog.OnEvent('QUEST_TURNED_IN', 4001, 250, 55) R2F.RouteLog.OnEvent('QUEST_REMOVED', 4001)")
    check(lua.eval("R2FDB.route.runs[1].events[6].e") == "done" and lua.eval("R2FDB.route.runs[1].events[6].xpGain") == 250
          and lua.eval("#R2FDB.route.runs[1].events") == 6, "route: a hand-in is written with its xp, and its removal from the log is not an abandon")
    lua.execute("NOW = 1040 R2F.RouteLog.OnEvent('QUEST_REMOVED', 4002)")
    check(lua.eval("R2FDB.route.runs[1].events[7].e") == "drop", "route: a quest that leaves the log without a hand-in is an abandon")
    lua.execute("NOW = 1050 LEVEL = 4 R2F.RouteLog.OnEvent('PLAYER_LEVEL_UP', 4) R2F.RouteLog.OnEvent('PLAYER_DEAD')")
    check(lua.eval("R2FDB.route.runs[1].events[8].e") == "level" and lua.eval("R2FDB.route.runs[1].events[8].to") == 4
          and lua.eval("R2FDB.route.runs[1].events[9].e") == "dead", "route: levels and deaths")
    lua.execute("R2F.RouteLog.OnEvent('ZONE_CHANGED') R2F.RouteLog.OnEvent('ZONE_CHANGED') UnitGUID = function(u) if u == 'npc' then return 'Creature-0-1-0-4-777-0001' end end "
                "R2F.RouteLog.OnEvent('TRAINER_SHOW') R2F.RouteLog.OnEvent('TRAINER_SHOW') R2F.RouteLog.OnEvent('MERCHANT_SHOW')")
    kinds = [lua.eval("R2FDB.route.runs[1].events[%d].e" % i) for i in range(10, 13)]
    check(kinds == ["zone", "npc", "npc"], "route: a zone change and each kind of NPC window are written once: %s" % kinds)
    lua.execute("R2F.RouteLog.Note('boars here are slow')")
    check(lua.eval("R2FDB.route.runs[1].events[13].tx") == "boars here are slow", "route: /r2f route note adds your own note")
    lua.execute("T = TEST T.timers = {} R2F.RouteLog.Stop()")
    check(lua.eval("R2F.RouteLog.IsOn()") is False and lua.eval("R2FDB.route.active") is None and lua.eval("R2FDB.route.runs[1].events[14].e") == "stop",
          "route: stop ends the run and the run stays saved")
    lua.execute("NOW = 2000 R2F.RouteLog.OnEvent('PLAYER_DEAD')")
    check(lua.eval("#R2FDB.route.runs[1].events") == 14, "route: nothing more is written after stop")
    # A run that was on when you logged out goes on at the next login.
    lua.execute("R2FDB.route.active = 1 R2F.RouteLog.Init()")
    check(lua.eval("R2F.RouteLog.IsOn()") is True and lua.eval("R2FDB.route.runs[1].events[15].e") == "login",
          "route: a run that was on at logout resumes at login")
    lua.execute("TEST.chat = {} R2F.RouteLog.Command('status')")
    check("recording run 1" in chat_all(lua), "route: status says what is recording")
    help_lines = lua_table_to_list(lua.eval("R2F.L.HELP_LINES"))
    check(any(h.startswith("/r2f route") for h in help_lines), "help lists /r2f route")
    # The report script turns a run into a timeline and a quest table.
    import importlib.util
    spec = importlib.util.spec_from_file_location("route_report", os.path.join(HERE, "..", "tools", "route_report.py"))
    rr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rr)
    run = {"label": "t", "race": "SKYBORNE", "class": "HUNTER", "level": 1, "trail": [[0, 1411, 10.0, 10.0], [10, 1411, 13.0, 14.0]],
           "events": [{"e": "start", "t": 0, "lv": 1, "z": "Zephras Isle", "sz": "Thendal"},
                      {"e": "accept", "t": 10, "lv": 1, "q": 1, "title": "A", "ql": 1, "obj": [["Kill: 0/3", 0, 3]]},
                      {"e": "done", "t": 100, "lv": 2, "q": 1, "xpGain": 90},
                      {"e": "accept", "t": 130, "lv": 2, "q": 2, "title": "B", "ql": 2}]}
    text = rr.render(run, 1)
    check("ACCEPT #1" in text and "| 1 | A |" in text and "#2" in text.split("| 1 | A |")[1].split("\n")[0] and "map 1411: 5" in text,
          "route report: the timeline, the quest table with the follow-up of a hand-in, and the path length")


def test_action_bars():
    """Tweaks > Action bars: a red veil out of range or without resources, cooldown numbers; our own child frames only."""
    lua, T = reminder_runtime("HUNTER")
    lua.execute("""
      BTN = CreateFrame('Button', 'ActionButton1', UIParent)
      BTN:SetSize(36, 36)
      BTN.action = 1
      BTN.icon = BTN:CreateTexture(nil, 'ARTWORK')
      BTN2 = CreateFrame('Button', 'MultiBarBottomLeftButton1', UIParent)
      BTN2:SetSize(36, 36)
      BTN2.action = 61
      HAS = { [1] = true, [61] = true }
      HasAction = function(s) return HAS[s] end
      RANGE = {} NORES = {} CD = {}
      IsActionInRange = function(s) return RANGE[s] end
      IsUsableAction = function(s) return true, NORES[s] end
      GetActionCooldown = function(s) local c = CD[s] if c then return c[1], c[2], 1 end return 0, 0, 1 end
      GetTime = function() return 100 end
    """)
    OV = "R2F.ActionBars.Overlay(BTN)"
    check(lua.eval("R2F.Gameplay.SetOn('barrange', true)") is True, "bars: the range box can be ticked")
    check(lua.eval("%s ~= nil" % OV) is True and lua.eval("%s.tint:IsShown()" % OV) is False, "bars: our own frame is made, the veil hidden while in range / no range")
    lua.execute("RANGE[1] = false R2F.ActionBars.Refresh()")
    check(lua.eval("%s.tint:IsShown()" % OV) is True, "bars: out of range shows the red veil")
    lua.execute("RANGE[1] = true R2F.ActionBars.Refresh()")
    check(lua.eval("%s.tint:IsShown()" % OV) is False, "bars: back in range hides it")
    lua.execute("NORES[1] = true R2F.ActionBars.Refresh()")
    check(lua.eval("%s.tint:IsShown()" % OV) is False, "bars: no resource veil while that box is off")
    lua.execute("R2F.Gameplay.SetOn('barresource', true) R2F.ActionBars.Refresh()")
    check(lua.eval("%s.tint:IsShown()" % OV) is True, "bars: not enough mana / rage / energy shows the red veil")
    lua.execute("NORES[1] = nil RANGE[61] = false R2F.ActionBars.Refresh()")
    check(lua.eval("R2F.ActionBars.Overlay(BTN2).tint:IsShown()") is True and lua.eval("%s.tint:IsShown()" % OV) is False,
          "bars: every bar's buttons are handled on their own")
    lua.execute("HAS[61] = nil R2F.ActionBars.Refresh()")
    check(lua.eval("R2F.ActionBars.Overlay(BTN2).tint:IsShown()") is False, "bars: an empty button shows nothing")
    # cooldown numbers
    lua.execute("CD[1] = { 95, 30 } R2F.ActionBars.Refresh()")
    check(lua.eval("%s.text:IsShown()" % OV) is False, "bars: no number while that box is off")
    lua.execute("R2F.Gameplay.SetOn('barcd', true) R2F.ActionBars.Refresh()")
    check(lua.eval("%s.text:IsShown()" % OV) is True and lua.eval("%s.text.__text" % OV) == "25", "bars: 25 seconds left shows 25")
    lua.execute("CD[1] = { 98, 8 } R2F.ActionBars.Refresh()")
    check(lua.eval("%s.text.__text" % OV) == "6.0", "bars: under ten seconds shows a decimal")
    lua.execute("CD[1] = { 90, 1.5 } R2F.ActionBars.Refresh()")
    check(lua.eval("%s.text:IsShown()" % OV) is False, "bars: the global cooldown gets no number")
    lua.execute("CD[1] = { 50, 350 } R2F.ActionBars.Refresh()")
    check(lua.eval("%s.text.__text" % OV) == "5m", "bars: minutes show as 5m")
    check(lua.eval("R2F.ActionBars.Format(7200)") == "2h" and lua.eval("R2F.ActionBars.Format(59)") == "59", "bars: hours and seconds format")
    lua.execute("R2F.Gameplay.SetOn('barcd', false) R2F.Gameplay.SetOn('barrange', false) R2F.Gameplay.SetOn('barresource', false)")
    check(lua.eval("%s.text:IsShown()" % OV) is False and lua.eval("%s.tint:IsShown()" % OV) is False, "bars: everything hides when the boxes are off")
    # no game table is written to: the button keeps only the fields the game gave it
    check(lua.eval("BTN.R2Foverlay") is None, "bars: nothing of ours is written onto the game's button")
    # A client with the game's own cooldown numbers setting: the box turns it on (works in combat) and our own numbers stay out.
    lua.execute("""
      CV = { countdownForCooldowns = '0' }
      GetCVar = function(n) return CV[n] end
      SetCVar = function(n, v) CV[n] = v end
      CD[1] = { 95, 30 } RANGE[1] = nil HAS[1] = true
    """)
    lua.execute("R2F.Gameplay.SetOn('barcd', true) R2F.ActionBars.Refresh()")
    check(lua.eval("CV.countdownForCooldowns") == "1", "bars: the box turns the game's own cooldown numbers on")
    check(lua.eval("%s.text:IsShown()" % OV) is False, "bars: our own numbers stay out then, so nothing shows twice")
    lua.execute("R2F.Gameplay.SetOn('barcd', false)")
    check(lua.eval("CV.countdownForCooldowns") == "0", "bars: unticking puts the game's setting back as it was")
    lua.execute("TEST.chat = {} R2F.ActionBars.Debug()")
    check("buttons found" in chat_all(lua), "bars: /r2f debug bars reports")


def test_combat_banner():
    """Combat banner (Class icons page): off until ticked; then "Entering Combat" / "Leaving Combat" appear in our own text
    for a moment and go away by themselves; the position can be unlocked and dragged, the size is a slider."""
    lua, T = reminder_runtime("MAGE")
    banner = "R2F.CombatBanner.Frame()"
    T.fire("PLAYER_REGEN_DISABLED")
    check(lua.eval("%s:IsShown()" % banner) is False, "combat banner: off by default, nothing shows")
    lua.execute("R2F.CombatBanner.SetShown(true)")
    check(lua.eval("%s:IsShown()" % banner) is False, "combat banner: on and locked: nothing until combat")
    T.fire("PLAYER_REGEN_DISABLED")
    check(lua.eval("%s:IsShown()" % banner) is True and lua.eval("%s.text.__text" % banner) == "Entering Combat",
          "combat banner: Entering Combat shows")
    check(lua.eval("%s.icon:IsShown()" % banner) is False and lua.eval("%s.border:IsShown()" % banner) is False,
          "combat banner: locked, it is text only (no icon, no frame)")
    T.fire("PLAYER_REGEN_ENABLED")
    check(lua.eval("%s.text.__text" % banner) == "Leaving Combat", "combat banner: Leaving Combat replaces it")
    T.runTimers()
    check(lua.eval("%s:IsShown()" % banner) is False, "combat banner: it goes away after a moment")
    # Unlocked: a marker to drag, always there; the text still flashes on events.
    lua.execute("R2F.CombatBanner.SetLock(false)")
    check(lua.eval("%s:IsShown()" % banner) is True and lua.eval("%s.icon:IsShown()" % banner) is True
          and lua.eval("%s.count.__text" % banner) == "Banner", "combat banner: unlocked: a marker to move it")
    lua.execute("R2F.CombatBanner.Db().x = 40 R2F.CombatBanner.Db().y = 100 R2F.CombatBanner.Apply()")
    check(lua.eval("R2F.Library.db.banner.x") == 40, "combat banner: its position is stored")
    # Size.
    lua.execute("R2F.CombatBanner.SetScale(2)")
    check(lua.eval("%s.__scale" % banner) == 2 and lua.eval("R2F.Library.db.banner.scale") == 2, "combat banner: the size slider scales it")
    lua.execute("R2F.CombatBanner.SetLock(true)")
    check(lua.eval("%s:IsShown()" % banner) is False, "combat banner: locked again: hidden until combat")
    lua.execute("R2F.CombatBanner.SetShown(false)")
    T.fire("PLAYER_REGEN_DISABLED")
    check(lua.eval("%s:IsShown()" % banner) is False, "combat banner: switched off")
    names = lua.eval("(function() local t = {} for _, d in ipairs(R2F.Reminders.ForPlayer()) do t[#t + 1] = d.key end return table.concat(t, ',') end)()")
    check("combatbanner" in names.split(","), "combat banner: it has its section on the Class icons page: %s" % names)
    # The 0.66.4 switch (Gameplay combatbanner) moves over.
    lua2, _ = reminder_runtime("MAGE", preset="{ gameplay = { combatbanner = true } }")
    check(lua2.eval("R2F.Library.db.banner.shown") is True and lua2.eval("R2F.Library.db.gameplay.combatbanner") is None,
          "combat banner: the earlier Alerts-page switch carries over")


def test_item_api_modern():
    """Forever has no global GetItemInfo / GetItemInfoInstant (Blizzard's own UI only calls C_Item.*). Everything
    that needs an item's required level, slot or class must work through C_Item alone."""
    lua = new_runtime(True)
    lua.execute("TEST.reset()")
    lua.execute("""
      GetItemInfo = nil
      GetItemInfoInstant = nil
      C_Item = C_Item or {}
      C_Item.GetItemInfo = function(id)
        if id == 252512 then return 'Biz Blade', 'link', 3, 30, 40, 'Weapon', 'Swords', 1, 'INVTYPE_WEAPON' end
        if id == 6720 then return 'Old Helm', 'link', 2, 20, 10, 'Armor', 'Cloth', 1, 'INVTYPE_HEAD' end
      end
      C_Item.GetItemInfoInstant = function(id)
        if id == 777 then return 777, 'Armor', 'Plate', 'INVTYPE_CHEST', 12345, 4, 4 end
        if id == 778 then return 778, 'Armor', 'Cloth', 'INVTYPE_CHEST', 12346, 4, 1 end
      end
    """)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    check(lua.eval("R2F.Item.Available()") is True, "item api: available through C_Item alone")
    check(lua.eval("(select(5, R2F.Item.Info(252512)))") == 40, "item api: the required level comes from C_Item.GetItemInfo")
    lua.execute("R2F.playerClass = 'MAGE' TEST.level = 30")
    check(lua.eval("R2F.GearScore.CanWear(777)") is False and lua.eval("R2F.GearScore.CanWear(778)") is True,
          "item api: upgrade arrows know a Mage can't wear plate, from C_Item.GetItemInfoInstant alone")
    check(lua.eval("(select(4, R2F.Item.Instant(777)))") == "INVTYPE_CHEST", "item api: the equip slot comes from C_Item.GetItemInfoInstant")


def test_training():
    """What to train next: read from the class trainer window, Home lines, level-up reminder."""
    lua = new_runtime(True)
    lua.execute("TEST.reset()")
    lua.execute("""
      TEST.level = 20
      TEST.trainer = {
        { 'Class Skills', '', 'header', 0, 0 },
        { 'Arcane Shot', 'Rank 3', 'available', 20, 1200 },
        { 'Serpent Sting', 'Rank 3', 'available', 18, 900 },
        { 'Aspect of the Cheetah', '', 'unavailable', 22, 2000 },
        { 'Multi-Shot', 'Rank 2', 'unavailable', 22, 2200 },
        { 'Raptor Strike', 'Rank 4', 'unavailable', 24, 3000 },
        { 'Track Beasts', '', 'used', 4, 100 },
      }
      GetNumTrainerServices = function() return #TEST.trainer end
      GetTrainerServiceInfo = function(i) local t = TEST.trainer[i] return t[1], t[2], t[3] end
      GetTrainerServiceLevelReq = function(i) return TEST.trainer[i][4] end
      GetTrainerServiceCost = function(i) return TEST.trainer[i][5] end
      TEST.profTrainer = false
      IsTradeskillTrainer = function() return TEST.profTrainer end
    """)
    T = lua.eval("TEST")
    T.fire("ADDON_LOADED", "RoadToForever")
    T.fire("PLAYER_LOGIN")
    a, b = lua.eval("R2F.Training.Lines()")
    check(a.startswith("Open your class trainer once") and b is None, "train: before a trainer visit Home says to open it: %r" % a)
    lua.execute("TEST.profTrainer = true")
    T.fire("TRAINER_SHOW")
    check(lua.eval("#R2FCharDB.training.spells") == 0, "train: a profession trainer is not read")
    lua.execute("TEST.profTrainer = false")
    T.fire("TRAINER_SHOW")
    check(lua.eval("#R2FCharDB.training.spells") == 6, "train: the class trainer's spells are saved, headers skipped")
    a, b = lua.eval("R2F.Training.Lines()")
    check(a == "Train now: 2 spells, 21s (Serpent Sting (Rank 3), Arcane Shot (Rank 3))",
          "train: 'Train now' with count, total cost and names, by level: %r" % a)
    check(b == "Next: level 22: Aspect of the Cheetah, Multi-Shot (Rank 2)", "train: 'Next' = the next level with spells: %r" % b)
    # Re-read with "Unavailable" hidden and Serpent Sting learned (gone from the list): later spells are kept,
    # the learned one goes.
    lua.execute("TEST.saved = TEST.trainer TEST.trainer = { TEST.saved[2] }")
    T.fire("TRAINER_UPDATE")
    names = sorted(lua.eval("R2FCharDB.training.spells[%d].n" % i) for i in range(1, lua.eval("#R2FCharDB.training.spells") + 1))
    check(names == ["Arcane Shot", "Aspect of the Cheetah", "Multi-Shot", "Raptor Strike"],
          "train: a filtered re-read keeps hidden later spells, drops a learned one: %s" % names)
    lua.execute("TEST.trainer = TEST.saved")
    T.fire("TRAINER_SHOW")
    lua.execute("R2F.Training.MarkLearned('Arcane Shot', 'Rank 3')")
    a, _ = lua.eval("R2F.Training.Lines()")
    check(a == "Train now: 1 spell, 9s (Serpent Sting (Rank 3))", "train: a learned spell leaves the list: %r" % a)
    lua.execute("TEST.level = 24")
    _, b = lua.eval("R2F.Training.Lines(24)")
    check(b.startswith("Nothing later known"), "train: nothing above your level known -> hint about Unavailable: %r" % b)
    # Level-up line (only with the Tweaks switch on)
    T.chat = lua.table()
    T.fire("PLAYER_LEVEL_UP", 22)
    check(chat_all(lua) == "", "train: no level-up line while Training reminder is off")
    lua.execute("R2F.Gameplay.SetOn('training', true)")
    T.fire("PLAYER_LEVEL_UP", 22)
    txt = chat_all(lua)
    check("level 22: new at your class trainer: Aspect of the Cheetah, Multi-Shot (Rank 2)" in txt, "train: level-up names the new spells: %r" % txt)
    T.chat = lua.table()
    T.fire("PLAYER_LEVEL_UP", 23)
    check(chat_all(lua) == "", "train: a level with nothing new says nothing")
    # Home shows the lines
    lua.execute("TEST.level = 20 R2F.MainWindow.Show('home') R2F.Home.Refresh()")
    check(font_text(lua, "^Train now: 1 spell,") is not None and font_text(lua, "^Next: level 22") is not None,
          "train: Home shows Train now and Next")
    check(lua.eval("(function() for _, p in ipairs(R2F.GameplayTab.PAGES) do if p.key == 'alerts' then for _, k in ipairs(p.features) do if k == 'training' then return true end end end end end)()") is True,
          "train: the reminder switch is on Tweaks > Alerts")


def install_item_stubs(lua):
    """Fake item info keyed by 'item:<id>' links (the Plan tab asks for items by link): stats, equip location, worn gear."""
    lua.execute("""
      TEST.gsItems = TEST.gsItems or {}
      TEST.worn = TEST.worn or {}
      TEST.requested = {}
      GetItemStats = function(link) local it = TEST.gsItems[link] return it and it.stats end
      GetItemInfoInstant = function(x)
        local it = TEST.gsItems[type(x) == 'number' and ('item:' .. x) or x]
        if it then return 1, '', '', it.loc, '', it.cls, it.sub end
      end
      GetInventoryItemLink = function(unit, slot) return TEST.worn[slot] end
      C_Item = C_Item or {}
      C_Item.RequestLoadItemDataByID = function(id) TEST.requested[#TEST.requested + 1] = id end
    """)


def test_route_weapons():
    """On-route weapons: Mr.BiZ weapon picks matched to launch-plan step titles, best per slot marked."""
    lua, T = plan_runtime()
    check(lua.eval("R2F.BiZ.RouteKey({ type = 'dungeon', instance = 'Blackfathom Deeps' })") == "Blackfathom Deeps"
          and lua.eval("R2F.BiZ.RouteKey({ type = 'vendor', label = 'Illiyana Moonblaze, Ashenvale (1g 7s 72c)' })") == "Ashenvale"
          and lua.eval("R2F.BiZ.RouteKey({ type = 'quest', label = 'Quest: X (level 30)' })") is None,
          "route: dungeon -> instance, vendor -> zone, quest -> nothing")

    check(lua.eval("R2F.BiZ.RouteWeapons('warrior/fury', 'hwd')['p1-bfdq']") is None
          and lua.eval("R2F.BiZ.RouteWeapons('warrior/fury', 'hwd')['p3-stv'][1].row.name") in ("Ironspine's Fist", "Bloody Brass Knuckles"),
          "route: a dungeon drop shows at its run, not at a step that only collects quests (data of 2026-10-17)")
    best = lua.eval("""(function() local n = 0 for _, l in pairs(R2F.BiZ.RouteWeapons('rogue/combat', 'hwd')) do
      for _, m in ipairs(l) do if m.best then n = n + 1 end end end return n end)()""")
    check(best == 2, "route: one 'best on route' per weapon slot that has a match (Combat: main + off hand = %d)" % best)
    check(lua.eval("next(R2F.BiZ.RouteWeapons('nope/spec', 'hwd'))") is None, "route: unknown spec = nothing")
    # The Plan tab line, for a Fury Warrior (the stub player is a Warrior): shown when it beats what is worn, not otherwise.
    lua.execute("R2F.BiZ.SetSpec('warrior/fury') R2F.Plan.Select('hwd')")
    fid = lua.eval("""(function() for _, l in pairs(R2F.BiZ.RouteWeapons('warrior/fury', 'hwd')) do
      for _, m in ipairs(l) do if m.row.name == "Ironspine's Fist" then return m.row.id end end end end)()""")
    install_item_stubs(lua)
    lua.execute("TEST.gsItems['item:%d'] = { stats = { ITEM_MOD_STRENGTH_SHORT = 20 }, loc = 'INVTYPE_WEAPON', cls = 2, sub = 13 }" % fid)
    lua.execute("R2F.MainWindow.Show('plan') R2F.PlanTab.Refresh()")
    line = font_text(lua, "^Weapon: .*Ironspine's Fist")
    check(line is not None and "best on route" not in line, "route: the Plan tab shows the weapon line when it is an upgrade: %r" % line)
    lua.execute("TEST.gsItems['item:999'] = { stats = { ITEM_MOD_STRENGTH_SHORT = 99 }, loc = 'INVTYPE_WEAPON', cls = 2, sub = 13 } "
                "TEST.worn[16] = 'item:999' TEST.worn[17] = 'item:999' R2F.PlanTab.Refresh()")
    check(font_text(lua, "^Weapon: .*Ironspine's Fist") is None, "route: not an upgrade over what is worn -> no line")
    lua.execute("TEST.worn[16] = nil TEST.worn[17] = nil R2F.BiZ.SetSpec('warrior/protection') R2F.PlanTab.Refresh()")
    check(font_text(lua, "^Weapon: .*Ironspine") is None, "route: another spec, other lines (the old ones are hidden)")


if __name__ == "__main__":
    main()
