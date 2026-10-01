-- Core.lua: events, slash command, key bindings, init (ADDON_PLAN.md 6.5, 12.3).
--
-- Event order on login: ADDON_LOADED (our SavedVariables are readable from
-- here on) -> PLAYER_LOGIN (UnitClass is reliable from here on). The UI is
-- only built when first opened, after both.

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
end

-- Combat: grey out Import / Tidy up, show "In combat" (drags are refused
-- inside Macros.Ensure itself).
-- The flag matters: InCombatLockdown() is still false during this event.
handlers.PLAYER_REGEN_DISABLED = function()
  R2F.inCombat = true
  R2F.MacroBook.SetCombat()
  R2F.ImportFrame.SetCombat(true)
  R2F.Settings.SetCombat()
end

-- PLAYER_REGEN_ENABLED fires after the lockdown has lifted, so queued macro
-- writes are safe to run here.
handlers.PLAYER_REGEN_ENABLED = function()
  R2F.inCombat = false
  R2F.Macros.RunQueue()
  R2F.MacroBook.SetCombat()
  R2F.ImportFrame.SetCombat(false)
  R2F.Settings.SetCombat()
end

-- Slot counter + markers; Refresh is a no-op while the book is closed.
handlers.UPDATE_MACROS = function() R2F.MacroBook.RequestRefresh() end
handlers.ACTIONBAR_SLOT_CHANGED = function() R2F.MacroBook.RequestRefresh() end
-- Newly learned spells: icons and "Learn later" states change.
handlers.LEARNED_SPELL_IN_TAB = function() R2F.MacroBook.RequestRefresh() end

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
-- Until step 6 builds the main window (Home / Macros / Talents, 12.4):
-- * Toggle Road to Forever and Open Macros both toggle the Macro Book, which
--   is what /r2f does today. Open Macros toggles too (not show-only), like
--   Blizzard's own Spellbook key, so the same key closes it again. Step 6:
--   Toggle = main window on its last tab, Open Macros = main window on the
--   Macros tab (or close it if that tab is already showing).
-- * Open Talents has nothing to open yet: it prints one chat line. Step 6
--   points it at the Talents tab (filled by step 9).
R2F.Bindings = {
  Toggle = function() R2F.MacroBook.Toggle() end,
  OpenMacros = function() R2F.MacroBook.Toggle() end,
  OpenTalents = function() R2F.Print(L.TALENTS_LATER) end,
}

-- /r2f opens the Macro Book. The full command set (12.3: /r2f macros,
-- /r2ft, /r2f minimap, /r2f help) comes with the main window in step 6.
-- SLASH_R2F1 / SlashCmdList.R2F are the WoW API's way to register a
-- command; they're the only globals besides R2F, R2FDB and R2FCharDB and
-- the R2F-prefixed frame names (see ADDON_PLAN 6.6).
_G.SLASH_R2F1 = "/r2f"
SlashCmdList.R2F = function(msg)
  msg = (msg or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
  if msg == "help" then
    R2F.Print(L.HELP)
  elseif msg == "import" then
    R2F.MacroBook.Show()
    R2F.ImportFrame.Show()
  else
    R2F.MacroBook.Toggle()
  end
end
