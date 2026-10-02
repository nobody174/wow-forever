-- Core.lua: events, slash commands, key bindings, init (ADDON_PLAN.md 6.5, 12.3).
--
-- Event order on login: ADDON_LOADED (our SavedVariables are readable from
-- here on) -> PLAYER_LOGIN (UnitClass is reliable from here on). The main
-- window is only built when first opened, after both.

local ADDON_NAME, R2F = ...
local L = R2F.L

local events = CreateFrame("Frame")
local handlers = {}

handlers.ADDON_LOADED = function(name)
  if name ~= ADDON_NAME then return end
  R2F.Library.Init()
  events:UnregisterEvent("ADDON_LOADED")
end

handlers.PLAYER_LOGIN = function()
  R2F.playerClass = select(2, UnitClass("player"))
  -- An import on another character updated the shared library but not this
  -- character's macros; catch up now (combat-safe: queued if in combat,
  -- e.g. after a /reload mid-fight).
  R2F.Macros.SyncOnLogin()
  -- Minimap button (12.2). At PLAYER_LOGIN every other (non-load-on-demand)
  -- addon has loaded, so Minimap.Init can see whether one of them brought
  -- LibDBIcon (ADDON_PLAN 6.10).
  R2F.Minimap.Init()
end

-- Combat: grey out the Import / Tidy up buttons, show "In combat" (drags are
-- refused inside Macros.Ensure itself).
-- The flag matters: InCombatLockdown() is still false during this event.
handlers.PLAYER_REGEN_DISABLED = function()
  R2F.inCombat = true
  -- Talent learning stops at once, mid-run (13.5); the flag above is already
  -- set, so no further LearnTalent goes out.
  R2F.Talents.OnCombat()
  R2F.MainWindow.SetCombat()
  R2F.ImportFrame.SetCombat(true)
  R2F.Settings.SetCombat()
end

-- PLAYER_REGEN_ENABLED fires after the lockdown has lifted, so queued macro
-- writes are safe to run here.
handlers.PLAYER_REGEN_ENABLED = function()
  R2F.inCombat = false
  R2F.Macros.RunQueue()
  R2F.MainWindow.SetCombat()
  R2F.ImportFrame.SetCombat(false)
  R2F.Settings.SetCombat()
end

-- Slot counter, markers and the Home counts; no-ops while the window is closed.
handlers.UPDATE_MACROS = function() R2F.MainWindow.RequestRefresh() end
handlers.ACTIONBAR_SLOT_CHANGED = function() R2F.MainWindow.RequestRefresh() end
-- Newly learned spells: icons and "Learn later" states change.
handlers.LEARNED_SPELL_IN_TAB = function() R2F.MainWindow.RequestRefresh() end
-- Talent points spent (here or in Blizzard's talent window) or gained on a
-- level-up: Home's free-points line and the Talents tab's preview (6.5).
-- Step 10: CHARACTER_POINTS_CHANGED is the server's answer to a learned point
-- (or the player's click in guided mode); the engine checks it first, then
-- the tab redraws.
handlers.CHARACTER_POINTS_CHANGED = function()
  R2F.Talents.OnPointsChanged()
  R2F.MainWindow.RequestRefresh()
end
-- WoW Forever stores talents as a trait config (13.10): applying talents in
-- Blizzard's window fires TRAIT_CONFIG_UPDATED (WeakAuras Forever listens to
-- it for the same reason); whether CHARACTER_POINTS_CHANGED also fires there
-- isn't confirmed, so both run the same handler.
handlers.TRAIT_CONFIG_UPDATED = handlers.CHARACTER_POINTS_CHANGED
handlers.PLAYER_LEVEL_UP = function() R2F.MainWindow.RequestRefresh() end
-- A CVar changed (/console, Blizzard's options, another addon, or our own
-- Quick settings): redraw Home's boxes from the live values (12.4.1). They
-- are also re-read every time the Home tab opens, so a client without this
-- event only loses the live update while Home is already showing.
handlers.CVAR_UPDATE = function() R2F.Home.RequestRefresh() end
-- The game refusing a protected call from an addon (args: addon name,
-- function). Only ours matters; for LearnTalent it means guided mode (13.8).
local function actionBlocked(addon, fn)
  if addon == ADDON_NAME then R2F.Talents.OnActionBlocked(fn) end
end
handlers.ADDON_ACTION_FORBIDDEN = actionBlocked
handlers.ADDON_ACTION_BLOCKED = actionBlocked

events:SetScript("OnEvent", function(_, event, ...)
  local fn = handlers[event]
  if fn then fn(...) end
end)
for event in pairs(handlers) do
  -- pcall: an event this client doesn't have (e.g. LEARNED_SPELL_IN_TAB is
  -- renamed in some clients) must not stop the rest from registering.
  pcall(events.RegisterEvent, events, event)
end

-- Key bindings (Bindings.xml calls these; labels are in Locale.lua).
-- Bindings.xml runs its Lua as plain (insecure) code on key press, which is
-- fine here: opening our own non-secure frames is allowed in combat, and
-- nothing in these calls writes a macro.
-- * Toggle Road to Forever: the main window on the tab used last (= /r2f).
-- * Open Macros / Open Talents: the main window on that tab, or close it if
--   that tab is already showing, like Blizzard's Spellbook / Talents keys.
-- Bindings.xml is unchanged since step 5; only these three functions moved on
-- (ADDON_PLAN 6.9's hand-off).
R2F.Bindings = {
  Toggle = function() R2F.MainWindow.Toggle() end,
  OpenMacros = function() R2F.MainWindow.Toggle("macros") end,
  OpenTalents = function() R2F.MainWindow.Toggle("talents") end,
}

-- Slash commands (12.3). /r2f macros, /r2f talents and /r2ft OPEN their tab
-- (typing one never hides what you asked for); /r2f with nothing after it
-- toggles, like the minimap button's left-click and the Toggle key.
-- /r2f import (step 3) still works: Macros tab + Import window.
local function printHelp()
  for _, line in ipairs(L.HELP_LINES) do R2F.Print(line) end
end

local COMMANDS = {
  [""] = function() R2F.MainWindow.Toggle() end,
  macros = function() R2F.MainWindow.Show("macros") end,
  talents = function() R2F.MainWindow.Show("talents") end,
  minimap = function() R2F.Minimap.ToggleHidden() end,
  help = printHelp,
  import = function()
    R2F.MainWindow.Show("macros")
    R2F.ImportFrame.Show()
  end,
  -- Copy my build (step 8). Since step 9 it's also a button on the Talents
  -- tab; the command stays as a shortcut (ADDON_PLAN 13.7). Read-only, so no
  -- combat check.
  copybuild = function() R2F.Talents.CopyMyBuild() end,
}
R2F.COMMANDS = COMMANDS

-- SLASH_R2F1 / SLASH_R2FT1 and the R2F / R2FT fields in SlashCmdList are the
-- WoW API's way to register a command; with R2F, R2FDB, R2FCharDB, the
-- binding labels and the R2F-prefixed frame names they are the only globals
-- (ADDON_PLAN 6.6, 6.10).
_G.SLASH_R2F1 = "/r2f"
SlashCmdList.R2F = function(msg)
  msg = (msg or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
  local fn = COMMANDS[msg]
  if fn then
    fn()
  else
    R2F.Print(L.UNKNOWN_COMMAND:format(msg))
  end
end

_G.SLASH_R2FT1 = "/r2ft"
SlashCmdList.R2FT = function() R2F.MainWindow.Show("talents") end
