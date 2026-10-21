-- Setup.lua: "Setup <class>": one click that gets a fresh character ready to play.
--
-- A setup does four things, in this order, and tells you what it did (and what it left alone):
--   1. Action Bars 2 to 6 on (the game's own Options > Gameplay > Action Bars switches, SetActionBarToggles), and auto loot on.
--   2. Your saved Edit Mode layout of that name (for the Hunter setup: the layout called "Hunter") becomes the active one.
--   3. Our macros go on the action buttons listed for that class. A button that already holds something is never overwritten.
--   4. The keys on those buttons are checked against your key bindings (read only: it says so if one differs, it never rebinds).
--      The Druid setup is the exception: it sets the Druid's own key bindings, saved for that character only.
-- Nothing runs in combat. "Undo last setup" puts the bars, auto loot, layout and the buttons it filled back.
--
-- Read-only on game tables; the writes are the game's own calls a player would make by hand (the Options checkboxes, picking a
-- layout in Edit Mode, dragging a macro onto a button), made out of combat and one step at a time.

local _, R2F = ...
local L = R2F.L

local Setup = {}
R2F.Setup = Setup

-- "Action Bar N" of the game's options -> the first action slot of that bar (slots 1-12 are bar 1; the others follow the pages
-- the game's own multi bars use) and the command name of its buttons for the key check.
local BAR_FIRST = { [1] = 1, [2] = 61, [3] = 49, [4] = 25, [5] = 37, [6] = 145, [7] = 157, [8] = 169 }
local BAR_COMMAND = { [1] = "ACTIONBUTTON", [2] = "MULTIACTIONBAR1BUTTON", [3] = "MULTIACTIONBAR2BUTTON",
                      [4] = "MULTIACTIONBAR3BUTTON", [5] = "MULTIACTIONBAR4BUTTON" }

function Setup.Slot(bar, button)
  return BAR_FIRST[bar] + button - 1
end

-- The setups. `place` rows: bar (1 = the main bar), button, WHAT goes there, and optionally `key` (the key that should be on that
-- button). What is one of:
--   id = "HUNTER/AutoShot"        one of our macros (the library id); macros of spells you have not learned yet show a ?
--   spell = { "Walk on Air" }     a spell of your spellbook by name, and/or match = { "ley%s*line" } (lower-case patterns)
--   item = 6948                   an item from your bags (6948 = Hearthstone)
--   general = { "Mark1" }         one of your own macros of the game's General tab, by name (any capitals)
-- `label` names it in the chat report.
-- Hunter: Raptor + Wing Clip on button 3 of the main bar, Auto Shot / Serpent Sting / pet attack / pet follow on bar 2, the two
-- Aspects on bar 5. Druid: the caster and healing macros on the main bar, Cat / Bear form on bar 4, the buffs on bar 5, the
-- Moonglade teleport on bar 3. Both: the Skyborne racials on bar 2, the Hearthstone and the General macros on bar 6.
local COMMON = {
  { bar = 2, button = 7, spell = { "Walk on Air" }, label = "Walk on Air" },
  { bar = 2, button = 10, spell = { "Read Ley Line", "Read Layline" }, match = { "ley%s*line", "lay%s*line" },
    label = "Read Ley Line" },
  { bar = 6, button = 1, general = { "Sit" }, label = "Sit" },
  { bar = 6, button = 2, general = { "Mark1" }, label = "Mark1" },
  { bar = 6, button = 3, general = { "Mark2" }, label = "Mark2" },
  { bar = 6, button = 12, item = 6948, label = "Hearthstone" },
}

local function withCommon(rows)
  for _, row in ipairs(COMMON) do rows[#rows + 1] = row end
  return rows
end

-- The Druid's key bindings (the owner's own, from the Druid character's bindings-cache.wtf): { key, command }. They are saved
-- for this character only: the Warrior / Druid layout has different bars (forms), so it does not share the account's keys.
local DRUID_BINDINGS = {
  { "BUTTON3", "MULTIACTIONBAR1BUTTON7" }, { "Q", "ACTIONBUTTON11" }, { "LEFT", "STRAFELEFT" },
  { "E", "ACTIONBUTTON12" }, { "RIGHT", "STRAFERIGHT" }, { "A", "TURNLEFT" }, { "D", "TURNRIGHT" },
  { "X", "MULTIACTIONBAR3BUTTON5" }, { "Z", "MULTIACTIONBAR3BUTTON6" }, { "1", "ACTIONBUTTON2" },
  { "2", "ACTIONBUTTON3" }, { "3", "ACTIONBUTTON4" }, { "4", "ACTIONBUTTON5" }, { "5", "ACTIONBUTTON6" },
  { "6", "NONE" }, { "7", "NONE" }, { "8", "NONE" }, { "9", "NONE" }, { "0", "NONE" }, { "-", "NONE" },
  { "=", "NONE" }, { "CTRL-1", "MULTIACTIONBAR1BUTTON2" }, { "CTRL-2", "MULTIACTIONBAR1BUTTON3" },
  { "CTRL-3", "MULTIACTIONBAR1BUTTON4" }, { "CTRL-4", "MULTIACTIONBAR1BUTTON5" },
  { "CTRL-5", "MULTIACTIONBAR1BUTTON6" }, { "SHIFT-1", "NONE" }, { "SHIFT-2", "NONE" }, { "SHIFT-3", "NONE" },
  { "SHIFT-4", "NONE" }, { "SHIFT-5", "NONE" }, { "SHIFT-6", "NONE" }, { "F1", "MULTIACTIONBAR4BUTTON1" },
  { "F2", "MULTIACTIONBAR4BUTTON2" }, { "F3", "MULTIACTIONBAR4BUTTON3" }, { "F4", "MULTIACTIONBAR4BUTTON4" },
  { "G", "TOGGLEPINGLISTENER" }, { "F", "ACTIONBUTTON8" }, { "B", "OPENALLBAGS" }, { "SHIFT-B", "NONE" },
  { "MOUSEWHEELUP", "ACTIONBUTTON9" }, { "MOUSEWHEELDOWN", "MULTIACTIONBAR1BUTTON9" },
  { "CTRL-MOUSEWHEELUP", "CAMERAZOOMIN" }, { "CTRL-MOUSEWHEELDOWN", "CAMERAZOOMOUT" },
  { "BUTTON5", "ACTIONBUTTON10" }, { "CAPSLOCK", "ACTIONBUTTON7" }, { "ALT-E", "MULTIACTIONBAR1BUTTON12" },
  { "ALT-Q", "MULTIACTIONBAR1BUTTON11" }, { "ALT-BUTTON5", "MULTIACTIONBAR1BUTTON10" },
  { "CTRL-F", "MULTIACTIONBAR1BUTTON8" }, { "ALT-1", "MULTIACTIONBAR5BUTTON2" },
  { "ALT-2", "MULTIACTIONBAR5BUTTON3" }, { "ALT-3", "NONE" }, { "ALT-4", "NONE" },
  { "ALT-MOUSEWHEELUP", "BONUSACTIONBUTTON1" }, { "ALT-MOUSEWHEELDOWN", "BONUSACTIONBUTTON2" },
  { "|", "ACTIONBUTTON1" }, { "CTRL-|", "MULTIACTIONBAR1BUTTON1" }, { ";", "QUESTIE_TOGGLE_JOURNEY" },
}

Setup.LIST = {
  hunter = {
    key = "hunter", class = "HUNTER", layout = "Hunter", bars = { 2, 3, 4, 5, 6 }, autoLoot = true,
    raidFrames = true, clearAll = true,
    place = withCommon({
      { bar = 1, button = 3, id = "HUNTER/Raptor+Clip", key = "2" },
      { bar = 2, button = 6, id = "HUNTER/AutoShot", key = "E" },
      { bar = 2, button = 5, id = "HUNTER/Serpent", key = "Q" },
      { bar = 2, button = 3, id = "HUNTER/PetAtkMOTT" },
      { bar = 2, button = 9, id = "HUNTER/PetFollow" },
      { bar = 5, button = 2, id = "HUNTER/AspMonkey" },
      { bar = 5, button = 3, id = "HUNTER/AspHawk" },
    }),
  },
  druid = {
    key = "druid", class = "DRUID", layout = "Warrior/Druid", bars = { 2, 3, 4, 5, 6 }, autoLoot = true,
    raidFrames = true, clearAll = true, bindings = DRUID_BINDINGS, bindingsName = "Druid",
    place = withCommon({
      { bar = 1, button = 2, general = { "atk", "Attack" }, label = "atk" },
      { bar = 1, button = 8, id = "DRUID/HTouch" },
      { bar = 1, button = 9, id = "DRUID/Regrowth" },
      { bar = 1, button = 10, id = "DRUID/Rejuv" },
      { bar = 1, button = 11, id = "DRUID/Moonfire" },
      { bar = 1, button = 12, id = "DRUID/Wrath" },
      { bar = 3, button = 4, spell = { "Teleport: Moonglade" }, label = "Teleport: Moonglade" },
      { bar = 4, button = 5, id = "DRUID/CatBear" },
      { bar = 5, button = 3, id = "DRUID/Thorns" },
      { bar = 5, button = 4, id = "DRUID/MotW" },
    }),
  },
}

-- Raid frame options of the game's Options > Interface > Raid Frames (plain CVars): class colours, power bars, pets.
local RAID_CVARS = { "raidFramesDisplayClassColor", "raidFramesDisplayPowerBars", "raidOptionDisplayPets" }

local function db()
  return R2F.Library.db
end

local function say(msg) R2F.Print(msg) end

-- ---------------------------------------------------------------------------
-- Edit Mode layouts: the game numbers the preset layouts first and your saved ones after them.
-- ---------------------------------------------------------------------------

-- { names }, activeIndex  (nil, nil when this client has no Edit Mode layouts)
function Setup.Layouts()
  local mf = _G.EditModeManagerFrame
  if mf and type(mf.layoutInfo) == "table" and type(mf.layoutInfo.layouts) == "table" then
    local names = {}
    for i, l in ipairs(mf.layoutInfo.layouts) do names[i] = l.layoutName end
    return names, mf.layoutInfo.activeLayout
  end
  local api = _G.C_EditMode
  if not (api and api.GetLayouts) then return nil, nil end
  local ok, info = pcall(api.GetLayouts)
  if not (ok and type(info) == "table" and type(info.layouts) == "table") then return nil, nil end
  -- The saved list does not include the two presets (Modern, Classic): they come first in the game's numbering.
  local names = { "Modern", "Classic" }
  for _, l in ipairs(info.layouts) do names[#names + 1] = l.layoutName end
  return names, info.activeLayout
end

function Setup.FindLayout(name)
  local names, active = Setup.Layouts()
  if not names then return nil, nil, nil end
  for i, n in ipairs(names) do
    if n == name then return i, active, names end
  end
  return nil, active, names
end

-- ---------------------------------------------------------------------------
-- The steps
-- ---------------------------------------------------------------------------

local function toggles()
  local t = { _G.GetActionBarToggles() }
  for i = 1, 7 do t[i] = t[i] and true or false end
  return t
end

-- What a setup would do, as chat-ready lines (also the text of the confirmation).
function Setup.Describe(def)
  local lines = { L.SETUP_STEP_BARS:format(table.concat(def.bars, ", ")) }
  if def.autoLoot then lines[#lines + 1] = L.SETUP_STEP_LOOT end
  if def.layout then lines[#lines + 1] = L.SETUP_STEP_LAYOUT:format(def.layout) end
  if def.bindings then lines[#lines + 1] = L.SETUP_STEP_BINDINGS:format(def.bindingsName or def.key) end
  if def.raidFrames then lines[#lines + 1] = L.SETUP_STEP_RAID end
  if def.clearAll then lines[#lines + 1] = L.SETUP_STEP_CLEAR end
  lines[#lines + 1] = L.SETUP_STEP_MACROS:format(#def.place)
  return lines
end

-- Finding what a row wants. Each returns a `what` table { kind = "macro" | "spell" | "item", id / name, pickup } or nil.
local function lowerSet(list)
  local set = {}
  for _, n in ipairs(list or {}) do set[n:lower()] = true end
  return set
end

-- A spell of the spellbook: by exact name first, then by pattern.
function Setup.FindSpell(row, book)
  book = book or (R2F.Ranks and R2F.Ranks.Book and R2F.Ranks.Book()) or {}
  for _, n in ipairs(row.spell or {}) do
    local e = book[n:lower()]
    if e and e.ids and e.ids[1] then return e.ids[1], n end
  end
  for name, e in pairs(book) do
    for _, pat in ipairs(row.match or {}) do
      if name:find(pat) and e.ids and e.ids[1] then return e.ids[1], name end
    end
  end
  return nil
end

-- One of your own macros on the game's General tab (account macros come first in the game's list).
function Setup.FindGeneral(row)
  if not _G.GetNumMacros then return nil end
  local want = lowerSet(row.general)
  local nAccount = _G.GetNumMacros()
  for i = 1, nAccount or 0 do
    local name = _G.GetMacroInfo(i)
    if name and want[name:lower()] then return i, name end
  end
  return nil
end

local function itemCount(id)
  local get = (_G.C_Item and _G.C_Item.GetItemCount) or _G.GetItemCount
  return get and get(id) or 0
end

local function resolve(row, ctx)
  if row.id then
    local e = R2F.Library.Get(row.id)
    if not e then return nil end
    return { kind = "macro", name = e.short, pickup = function() return R2F.Macros.Ensure(row.id) end }
  end
  if row.spell or row.match then
    ctx.book = ctx.book or (R2F.Ranks and R2F.Ranks.Book and R2F.Ranks.Book()) or {}
    local id = Setup.FindSpell(row, ctx.book)
    if not id then return nil end
    local pick = (_G.C_Spell and _G.C_Spell.PickupSpell) or _G.PickupSpell
    if not pick then return nil end
    return { kind = "spell", id = id, name = row.label, pickup = function() pick(id) return true end }
  end
  if row.item then
    if itemCount(row.item) <= 0 then return nil end
    local pick = (_G.C_Item and _G.C_Item.PickupItem) or _G.PickupItem
    if not pick then return nil end
    return { kind = "item", id = row.item, name = row.label, pickup = function() pick(row.item) return true end }
  end
  if row.general then
    local index, name = Setup.FindGeneral(row)
    if not index or not _G.PickupMacro then return nil end
    return { kind = "macro", name = name, pickup = function() _G.PickupMacro(index) return true end }
  end
  return nil
end

local function slotHolds(slot, what)
  local kind, id = _G.GetActionInfo(slot)
  if not kind then return "empty" end
  if what and kind == what.kind then
    if kind == "macro" and _G.GetActionText and _G.GetActionText(slot) == what.name then return "ours" end
    if kind ~= "macro" and id == what.id then return "ours" end
  end
  return "other"
end

-- Puts one thing on one button. Calls done(result): "placed", "ours" (already there), "occupied", "missing" or "failed".
local function placeOne(row, undo, ctx, done)
  local slot = Setup.Slot(row.bar, row.button)
  local what = resolve(row, ctx)
  if not what then return done("missing") end
  local held = slotHolds(slot, what)
  if held == "ours" then return done("ours") end
  if held == "other" then
    -- A spell on the button (a starting spell) is lifted off and put back by Undo; anything else stays.
    local kind, id = _G.GetActionInfo(slot)
    if kind ~= "spell" or type(id) ~= "number" then return done("occupied") end
    _G.PickupAction(slot)
    _G.ClearCursor()
    if _G.GetActionInfo(slot) then return done("occupied") end
    undo.cleared[#undo.cleared + 1] = { slot = slot, spell = id }
  end
  if not what.pickup() then return done("failed") end
  -- The thing is on the cursor (a new macro a frame later): wait for it, then drop it on the button.
  local tries = 0
  local function step()
    tries = tries + 1
    if _G.GetCursorInfo() == what.kind then
      _G.PlaceAction(slot)
      _G.ClearCursor()
      if slotHolds(slot, what) == "ours" then
        undo.slots[#undo.slots + 1] = { slot = slot, name = what.name, kind = what.kind }
        return done("placed")
      end
      return done("failed")
    end
    if tries >= 8 then _G.ClearCursor() return done("failed") end
    _G.C_Timer.After(0.15, step)
  end
  _G.C_Timer.After(0.1, step)
end

-- Key check, read only: does the key on the button match the one listed?
local function keyNote(row)
  if not row.key then return nil end
  local cmd = BAR_COMMAND[row.bar]
  if not (cmd and _G.GetBindingKey) then return nil end
  local k1, k2 = _G.GetBindingKey(cmd .. row.button)
  if k1 == row.key or k2 == row.key then return nil end
  return L.SETUP_KEY_DIFFERS:format(row.bar, row.button, row.key, tostring(k1 or "-"))
end

-- Key bindings: the game keeps the bindings in memory and SaveBindings(set) writes them to the account's set (1) or this
-- character's (2) and makes that one the active set, which is what ticking "Character Specific Key Bindings" does. Out of combat
-- only. Undo puts the old commands back and returns to the old set.
function Setup.ApplyBindings(def, undo)
  if not (_G.SetBinding and _G.SaveBindings and _G.GetBindingAction) then return say(L.SETUP_BINDINGS_FAILED) end
  local current = _G.GetCurrentBindingSet and _G.GetCurrentBindingSet() or 1
  local old = {}
  for _, b in ipairs(def.bindings) do
    old[#old + 1] = { b[1], _G.GetBindingAction(b[1]) or "" }
  end
  local n = 0
  for _, b in ipairs(def.bindings) do
    local ok
    if b[2] == "NONE" then ok = _G.SetBinding(b[1]) else ok = _G.SetBinding(b[1], b[2]) end
    if ok ~= false then n = n + 1 end
  end
  _G.SaveBindings(2)
  undo.bindings = { set = current, old = old }
  say(L.SETUP_DONE_BINDINGS:format(n))
end

function Setup.Execute(def)
  local undo = { time = _G.time and _G.time() or 0, slots = {}, cleared = {}, setup = def.key }
  -- 1. bars and auto loot
  undo.toggles = toggles()
  local want = toggles()
  for _, bar in ipairs(def.bars) do want[bar - 1] = true end
  pcall(_G.SetActionBarToggles, want[1], want[2], want[3], want[4], want[5], want[6], want[7])
  if def.autoLoot then
    undo.autoLoot = R2F.QuickSettings.Read("autoLootDefault")
    R2F.QuickSettings.Write("autoLootDefault", "1")
  end
  say(L.SETUP_DONE_BARS:format(table.concat(def.bars, ", ")))
  if def.raidFrames then
    undo.cvars = {}
    for _, c in ipairs(RAID_CVARS) do
      undo.cvars[c] = R2F.QuickSettings.Read(c)
      R2F.QuickSettings.Write(c, "1")
    end
    say(L.SETUP_DONE_RAID)
  end
  -- 2. the Edit Mode layout
  if def.layout then
    local idx, active = Setup.FindLayout(def.layout)
    undo.layout = active
    if not idx then
      say(L.SETUP_NO_LAYOUT:format(def.layout))
    elseif idx == active then
      say(L.SETUP_LAYOUT_ALREADY:format(def.layout))
    else
      local ok = _G.C_EditMode and pcall(_G.C_EditMode.SetActiveLayout, idx)
      say(ok and L.SETUP_DONE_LAYOUT:format(def.layout) or L.SETUP_LAYOUT_FAILED:format(def.layout))
    end
  end
  -- 2b. key bindings, for this character only
  if def.bindings then Setup.ApplyBindings(def, undo) end
  -- Every button on the main bar and Action Bars 2 to 8 is emptied first (spells are put back by Undo).
  if def.clearAll and not R2F.InCombat() then
    local n = 0
    for _, first in pairs(BAR_FIRST) do
      for slot = first, first + 11 do
        local kind, id = _G.GetActionInfo(slot)
        if kind then
          _G.PickupAction(slot)
          _G.ClearCursor()
          if kind == "spell" and type(id) == "number" then undo.cleared[#undo.cleared + 1] = { slot = slot, spell = id } end
          n = n + 1
        end
      end
    end
    say(L.SETUP_DONE_CLEAR:format(n))
  end
  db().setupUndo = undo
  -- 3. the macros, one button at a time after the layout has had a moment to apply
  local results = { placed = 0, ours = 0, occupied = {}, missing = {}, failed = {} }
  local ctx = {}
  local i = 0
  local function nextRow()
    i = i + 1
    local row = def.place[i]
    if not row then return Setup.Finish(def, results) end
    if R2F.InCombat() then
      say(L.SETUP_STOPPED_COMBAT)
      return Setup.Finish(def, results)
    end
    placeOne(row, undo, ctx, function(r)
      if r == "placed" or r == "ours" then
        results[r] = results[r] + 1
      else
        results[r][#results[r] + 1] = ("bar %d button %d (%s)"):format(row.bar, row.button, row.label or row.id or "?")
      end
      _G.C_Timer.After(0.1, nextRow)
    end)
  end
  _G.C_Timer.After(1.0, nextRow)
end

function Setup.Finish(def, r)
  say(L.SETUP_DONE_MACROS:format(r.placed, r.ours))
  if #r.occupied > 0 then say(L.SETUP_OCCUPIED:format(table.concat(r.occupied, "; "))) end
  if #r.missing > 0 then say(L.SETUP_MISSING:format(table.concat(r.missing, "; "))) end
  if #r.failed > 0 then say(L.SETUP_FAILED:format(table.concat(r.failed, "; "))) end
  for _, row in ipairs(def.place) do
    local note = keyNote(row)
    if note then say(note) end
  end
  say(L.SETUP_FINISHED)
  -- The game shows newly switched-on bars only after a reload: offer it.
  if def.bars and R2F.UI and R2F.UI.Confirm and _G.ReloadUI then
    -- Calling ReloadUI from our button after the setup is blocked by the game ("Interface action failed because of an AddOn"),
    -- though it works from the window's Reload UI button. So the button puts "/reload" in the chat line instead: Enter runs
    -- it with the game's own code, which is never blocked. (A timer opens the dialog so it starts from a fresh call.)
    local function ask()
      R2F.UI.Confirm(L.SETUP_RELOAD_ASK, L.SETUP_RELOAD_GO, L.BTN_CANCEL, function()
        if R2F.InCombat() then return say(L.SETUP_COMBAT) end
        if _G.ChatFrame_OpenChat then
          _G.ChatFrame_OpenChat("/reload")
        else
          _G.ReloadUI()
        end
      end)
    end
    if _G.C_Timer and _G.C_Timer.After then _G.C_Timer.After(0.3, ask) else ask() end
  end
end

-- The entry point: checks, then a confirmation listing what will change.
function Setup.Run(key)
  local def = Setup.LIST[key or ""]
  if not def then return say(L.SETUP_UNKNOWN:format(tostring(key))) end
  if R2F.playerClass ~= def.class then return say(L.SETUP_WRONG_CLASS:format(def.class:lower())) end
  if R2F.InCombat() then return say(L.SETUP_COMBAT) end
  if not (_G.GetActionBarToggles and _G.SetActionBarToggles and _G.PlaceAction) then return say(L.SETUP_NO_API) end
  if not Setup.Available(def) then return say(L.SETUP_NO_LAYOUT:format(def.layout or "?")) end
  R2F.UI.Confirm(L.SETUP_CONFIRM:format(table.concat(Setup.Describe(def), "\n")), L.SETUP_GO, L.BTN_CANCEL, function()
    Setup.Execute(def)
  end)
end

-- A setup is for characters that have its Edit Mode layout saved ("Hunter", "Warrior/Druid"): everyone else never sees it.
function Setup.Available(def)
  return def ~= nil and def.layout ~= nil and (Setup.FindLayout(def.layout)) ~= nil
end

-- Is there a setup this character can use? (The menu entry and the help lines depend on it.)
function Setup.AvailableHere()
  local def = Setup.ForClass()
  return def ~= nil and Setup.Available(def)
end

-- Which setup belongs to this character (nil when there is none).
function Setup.ForClass()
  for _, def in pairs(Setup.LIST) do
    if def.class == R2F.playerClass then return def end
  end
  return nil
end

-- ---------------------------------------------------------------------------
-- Undo
-- ---------------------------------------------------------------------------

function Setup.CanUndo()
  return db() and type(db().setupUndo) == "table"
end

function Setup.Undo()
  local u = db().setupUndo
  if type(u) ~= "table" then return say(L.SETUP_NOTHING_TO_UNDO) end
  if R2F.InCombat() then return say(L.SETUP_COMBAT) end
  if u.toggles then
    local t = u.toggles
    pcall(_G.SetActionBarToggles, t[1], t[2], t[3], t[4], t[5], t[6], t[7])
  end
  for c, v in pairs(u.cvars or {}) do R2F.QuickSettings.Write(c, v) end
  if u.autoLoot ~= nil then R2F.QuickSettings.Write("autoLootDefault", u.autoLoot) end
  if u.layout and _G.C_EditMode then
    local _, active = Setup.Layouts()
    if active ~= u.layout then pcall(_G.C_EditMode.SetActiveLayout, u.layout) end
  end
  if u.bindings and _G.SetBinding and _G.SaveBindings then
    for _, b in ipairs(u.bindings.old) do
      if b[2] == "" then _G.SetBinding(b[1]) else _G.SetBinding(b[1], b[2]) end
    end
    _G.SaveBindings(u.bindings.set or 1)
  end
  local cleared = 0
  for _, s in ipairs(u.slots or {}) do
    -- only a button that still holds what we put there (a macro by name; a spell or an item by its kind)
    local held = _G.GetActionInfo(s.slot)
    local kind = s.kind or "macro"
    if held == kind and (kind ~= "macro" or (_G.GetActionText and _G.GetActionText(s.slot) == s.name)) then
      _G.PickupAction(s.slot)
      _G.ClearCursor()
      cleared = cleared + 1
    end
  end
  for _, c in ipairs(u.cleared or {}) do
    if not _G.GetActionInfo(c.slot) and _G.PickupSpell then
      _G.PickupSpell(c.spell)
      _G.PlaceAction(c.slot)
      _G.ClearCursor()
    end
  end
  db().setupUndo = nil
  say(L.SETUP_UNDONE:format(cleared))
end
