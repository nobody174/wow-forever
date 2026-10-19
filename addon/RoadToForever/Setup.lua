-- Setup.lua: "Setup <class>": one click that gets a fresh character ready to play.
--
-- A setup does four things, in this order, and tells you what it did (and what it left alone):
--   1. Action Bars 2 to 6 on (the game's own Options > Gameplay > Action Bars switches, SetActionBarToggles), and auto loot on.
--   2. Your saved Edit Mode layout of that name (for the Hunter setup: the layout called "Hunter") becomes the active one.
--   3. Our macros go on the action buttons listed for that class. A button that already holds something is never overwritten.
--   4. The keys on those buttons are checked against your key bindings (read only: it says so if one differs, it never rebinds).
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

-- The setups. `place` rows: bar (1 = the main bar), button, the macro's library id, and optionally `key` (the key that should be
-- on that button). Hunter: Raptor + Wing Clip on button 3 of the main bar, Auto Shot / Serpent Sting / pet attack / pet follow on
-- bar 2, the two Aspects on bar 5. Macros of spells you have not learned yet show a ? until you learn them.
Setup.LIST = {
  hunter = {
    key = "hunter", class = "HUNTER", layout = "Hunter", bars = { 2, 3, 4, 5, 6 }, autoLoot = true,
    raidFrames = true, clearAll = true,
    place = {
      { bar = 1, button = 3, id = "HUNTER/Raptor+Clip", key = "2" },
      { bar = 2, button = 6, id = "HUNTER/AutoShot", key = "E" },
      { bar = 2, button = 5, id = "HUNTER/Serpent", key = "Q" },
      { bar = 2, button = 3, id = "HUNTER/PetAtkMOTT" },
      { bar = 2, button = 9, id = "HUNTER/PetFollow" },
      { bar = 5, button = 2, id = "HUNTER/AspMonkey" },
      { bar = 5, button = 3, id = "HUNTER/AspHawk" },
    },
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
  if def.raidFrames then lines[#lines + 1] = L.SETUP_STEP_RAID end
  if def.clearAll then lines[#lines + 1] = L.SETUP_STEP_CLEAR end
  lines[#lines + 1] = L.SETUP_STEP_MACROS:format(#def.place)
  return lines
end

local function slotHolds(slot, e)
  local kind = _G.GetActionInfo(slot)
  if not kind then return "empty" end
  if kind == "macro" and e and _G.GetActionText and _G.GetActionText(slot) == e.short then return "ours" end
  return "other"
end

-- Puts one of our macros on one button. Calls done(result): "placed", "ours" (already there), "occupied", "missing"
-- or "failed".
local function placeOne(row, undo, done)
  local slot = Setup.Slot(row.bar, row.button)
  local e = R2F.Library.Get(row.id)
  if not e then return done("missing") end
  local held = slotHolds(slot, e)
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
  if not R2F.Macros.Ensure(row.id) then return done("failed") end
  -- The macro is on the cursor (a new one a frame later): wait for it, then drop it on the button.
  local tries = 0
  local function step()
    tries = tries + 1
    if _G.GetCursorInfo() == "macro" then
      _G.PlaceAction(slot)
      _G.ClearCursor()
      if slotHolds(slot, e) == "ours" then
        undo.slots[#undo.slots + 1] = { slot = slot, name = e.short }
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
  local i = 0
  local function nextRow()
    i = i + 1
    local row = def.place[i]
    if not row then return Setup.Finish(def, results) end
    if R2F.InCombat() then
      say(L.SETUP_STOPPED_COMBAT)
      return Setup.Finish(def, results)
    end
    placeOne(row, undo, function(r)
      if r == "placed" or r == "ours" then
        results[r] = results[r] + 1
      else
        results[r][#results[r] + 1] = ("bar %d button %d"):format(row.bar, row.button)
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
    R2F.UI.Confirm(L.SETUP_RELOAD_ASK, L.SETUP_RELOAD_GO, L.BTN_CANCEL, function()
      if R2F.InCombat() then return say(L.SETUP_COMBAT) end
      _G.ReloadUI()
    end)
  end
end

-- The entry point: checks, then a confirmation listing what will change.
function Setup.Run(key)
  local def = Setup.LIST[key or ""]
  if not def then return say(L.SETUP_UNKNOWN:format(tostring(key))) end
  if R2F.playerClass ~= def.class then return say(L.SETUP_WRONG_CLASS:format(def.class:lower())) end
  if R2F.InCombat() then return say(L.SETUP_COMBAT) end
  if not (_G.GetActionBarToggles and _G.SetActionBarToggles and _G.PlaceAction) then return say(L.SETUP_NO_API) end
  R2F.UI.Confirm(L.SETUP_CONFIRM:format(table.concat(Setup.Describe(def), "\n")), L.SETUP_GO, L.BTN_CANCEL, function()
    Setup.Execute(def)
  end)
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
  local cleared = 0
  for _, s in ipairs(u.slots or {}) do
    -- only a button that still holds the macro we put there
    if _G.GetActionInfo(s.slot) == "macro" and _G.GetActionText and _G.GetActionText(s.slot) == s.name then
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
