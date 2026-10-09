-- QuickSettings.lua: the Home tab's Quick settings (ADDON_PLAN.md 12.4, 12.4.1).
--
-- Three game settings the site offers as /console macros (data.py's
-- Universal "Misc / UI" group), changed here directly with SetCVar instead,
-- so they cost no macro and no macro slot:
--   Max camera zoom   cameraDistanceMaxZoomFactor 4  (off = the game's default)
--   Hide guild names  UnitNamePlayerGuild 0          (off = 1)
--   Hide PvP titles   UnitNamePlayerPVPTitle 0       (off = 1)
--
-- Nothing is stored in SavedVariables: the game saves CVars itself, and the
-- boxes always show the LIVE value (GetCVar), so a value set by /console,
-- Blizzard's options or another addon shows up correctly.
--
-- The Macro Book hides exactly the three matching macros (HidesMacro), so it
-- doesn't offer a macro-slot way to do what a box here does for free. The
-- macros stay on the website for players without the addon.

local _, R2F = ...
local L = R2F.L

local QuickSettings = {}
R2F.QuickSettings = QuickSettings

-- One entry per box. `macro` = the id of the site macro it replaces, exactly
-- as data.py builds it ("ANY/" + short): "ANY/Zoom", "ANY/HideGuild",
-- "ANY/HidePvP". run_tests.py checks these against data.py, so a renamed
-- short on the site fails the tests instead of silently un-hiding a macro.
-- `off = nil` means "the game's own default" (read with GetCVarDefault).
QuickSettings.ITEMS = {
  { key = "zoom", cvar = "cameraDistanceMaxZoomFactor", on = "4", off = nil,
    macro = "ANY/Zoom", label = L.QS_ZOOM, tip = L.QS_ZOOM_TIP },
  { key = "guild", cvar = "UnitNamePlayerGuild", on = "0", off = "1",
    macro = "ANY/HideGuild", label = L.QS_GUILD, tip = L.QS_GUILD_TIP },
  { key = "pvp", cvar = "UnitNamePlayerPVPTitle", on = "0", off = "1",
    macro = "ANY/HidePvP", label = L.QS_PVP, tip = L.QS_PVP_TIP },
}

local byMacro = {}
for _, item in ipairs(QuickSettings.ITEMS) do byMacro[item.macro] = item end

-- The CVar API, looked up at call time (the tests swap it out). Classic Era
-- has the old globals; newer clients keep them as aliases of C_CVar, and a
-- client could have only the C_CVar table, so both are tried.
local function api(name)
  local fn = _G[name]
  if type(fn) == "function" then return fn end
  local ns = _G.C_CVar
  if type(ns) == "table" and type(ns[name]) == "function" then return ns[name] end
end

local function read(cvar)
  local get = api("GetCVar")
  if not get then return nil end
  local ok, value = pcall(get, cvar)
  if ok and value ~= nil then return tostring(value) end
end

-- CVars come back as strings, and a number may come back reformatted
-- ("4" -> "4.000000"), so numbers are compared as numbers.
local function same(a, b)
  if a == nil or b == nil then return false end
  local na, nb = tonumber(a), tonumber(b)
  if na and nb then return math.abs(na - nb) < 1e-6 end
  return a == b
end

-- What "unticked" writes. For the zoom it's the game's OWN default, read
-- from the client, not a number typed in here: the default differs between
-- client versions (and Forever may change it), and a guessed default would
-- quietly leave the player with a camera setting they never chose. No
-- GetCVarDefault (or no answer) = nil: the box then can't be unticked.
function QuickSettings.OffValue(item)
  if item.off then return item.off end
  local default = api("GetCVarDefault")
  if not default then return nil end
  local ok, value = pcall(default, item.cvar)
  if ok and value ~= nil then return tostring(value) end
end

-- The box can work at all: SetCVar exists and the client knows this CVar
-- (GetCVar returns a value; nil = unknown CVar, e.g. removed in this client).
function QuickSettings.Available(item)
  return api("SetCVar") ~= nil and read(item.cvar) ~= nil
end

-- Raw access for other features that need one game setting (Gameplay's XP bar text):
-- every CVar read and write in the addon stays in this file.
function QuickSettings.Read(cvar)
  return read(cvar)
end

function QuickSettings.Write(cvar, value)
  local set = api("SetCVar")
  if not set then return false end
  return pcall(set, cvar, value) and true or false
end

-- Ticked = the live value is the "on" value, whoever set it.
function QuickSettings.IsOn(item)
  return same(read(item.cvar), item.on)
end

-- Tick (on = true) or untick. Returns true when the game took the value.
-- Refused in combat, like every other write in this addon (6.4, 6.9): the
-- Home boxes are also greyed out then, this is the backstop. Refused, not
-- queued: a click is not a confirmed popup, and a setting flipping by itself
-- after the fight would be a surprise (the drag rule, 6.7).
function QuickSettings.Set(item, on)
  if R2F.InCombat() then
    R2F.Error(L.QS_COMBAT)
    return false
  end
  local set = api("SetCVar")
  if not set or read(item.cvar) == nil then
    R2F.Error(L.QS_UNAVAILABLE)
    return false
  end
  local value = on and item.on or QuickSettings.OffValue(item)
  if value == nil then
    R2F.Error(L.QS_NO_DEFAULT)
    return false
  end
  local ok = pcall(set, item.cvar, value)
  -- Read it back: a client may refuse or clamp a value without an error.
  if not ok or not same(read(item.cvar), value) then
    R2F.Error(L.QS_NOT_ACCEPTED)
    return false
  end
  return true
end

-- Flip a box from the LIVE value (not from the button's own checked state),
-- then the caller redraws from the live value again (Settings' rule, 6.9).
function QuickSettings.Toggle(item)
  return QuickSettings.Set(item, not QuickSettings.IsOn(item))
end

-- Macro Book filter. An exact id lookup, not a pattern on names or bodies:
-- only these three site macros are the same thing as a box here; another
-- macro that merely mentions the camera or a /console command is the
-- player's or the site's own and must stay visible. A macro is only hidden
-- while its box can actually work, so on a client without the CVar or
-- SetCVar the book still offers the macro way.
function QuickSettings.HidesMacro(id)
  local item = byMacro[id]
  return item ~= nil and QuickSettings.Available(item)
end
