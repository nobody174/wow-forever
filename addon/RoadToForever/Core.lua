-- Core.lua: events, slash commands, key bindings, init.
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
  -- The macros that ship inside the addon (MacroData.lua) go into the library first.
  R2F.Bundle.Run()
  R2F.Talents.RegisterShare()
  -- An import on another character updated the shared library but not this
  -- character's macros; catch up now (combat-safe: queued if in combat,
  -- e.g. after a /reload mid-fight).
  R2F.Macros.SyncOnLogin()
  -- Minimap button. At PLAYER_LOGIN every other (non-load-on-demand)
  -- addon has loaded, so Minimap.Init can see whether one of them brought
  -- LibDBIcon.
  R2F.Minimap.Init()
  R2F.Stance.Init()
  R2F.Ammo.Init()
  R2F.Tracking.Init()
  R2F.Buffs.Init()
  R2F.Gameplay.InitCharacters()
  R2F.Gameplay.Init()
  R2F.Bags.Init()
end

-- Combat: grey out the Import / Tidy up buttons, show "In combat" (drags are
-- refused inside Macros.Ensure itself).
-- The flag matters: InCombatLockdown() is still false during this event.
handlers.PLAYER_REGEN_DISABLED = function()
  R2F.inCombat = true
  -- Talent learning stops at once, mid-run; the flag above is already
  -- set, so no further LearnTalent goes out.
  R2F.Talents.OnCombat()
  R2F.MainWindow.SetCombat()
  R2F.ImportFrame.SetCombat(true)
  R2F.Settings.SetCombat()
  if R2F.GameplayTab and R2F.GameplayTab.Refresh then R2F.GameplayTab.Refresh() end
end

-- PLAYER_REGEN_ENABLED fires after the lockdown has lifted, so queued macro
-- writes are safe to run here.
handlers.PLAYER_REGEN_ENABLED = function()
  R2F.inCombat = false
  R2F.Macros.RunQueue()
  R2F.Bags.OnRegen()
  R2F.MainWindow.SetCombat()
  R2F.ImportFrame.SetCombat(false)
  R2F.Settings.SetCombat()
  if R2F.GameplayTab and R2F.GameplayTab.Refresh then R2F.GameplayTab.Refresh() end
end

-- Slot counter, markers and the Home counts; no-ops while the window is closed.
-- Talent loadouts shared by a group member (Talents.lua).
handlers.CHAT_MSG_ADDON = function(...) R2F.Talents.OnAddonMessage(...) end

handlers.UPDATE_MACROS = function() R2F.MainWindow.RequestRefresh() end
handlers.ACTIONBAR_SLOT_CHANGED = function() R2F.MainWindow.RequestRefresh() end
-- Newly learned spells: icons and "Learn later" states change.
handlers.LEARNED_SPELL_IN_TAB = function()
  R2F.MainWindow.RequestRefresh()
  R2F.Ranks.OnLearned()
end
-- A new spell rank can raise the ranks in the macros the addon made (Ranks.lua, 16).
handlers.SPELLS_CHANGED = function() R2F.Ranks.OnLearned() end
-- Talent points spent (here or in Blizzard's talent window) or gained on a
-- level-up: Home's free-points line and the Talents tab's preview.
-- CHARACTER_POINTS_CHANGED is the server's answer to a learned point
-- (or the player's click in guided mode); the engine checks it first, then
-- the tab redraws.
handlers.CHARACTER_POINTS_CHANGED = function()
  R2F.Talents.OnPointsChanged()
  R2F.MainWindow.RequestRefresh()
end
-- WoW Forever stores talents as a trait config: applying talents in
-- Blizzard's window fires TRAIT_CONFIG_UPDATED (WeakAuras Forever listens to
-- it for the same reason), and CHARACTER_POINTS_CHANGED may not fire there,
-- so both run the same handler.
handlers.TRAIT_CONFIG_UPDATED = handlers.CHARACTER_POINTS_CHANGED
-- The trait currency (= the free talent points on Forever) changing,
-- e.g. after an applied point. Same handler: the engine only re-reads the
-- game on it (no event is trusted alone), and Home / the tab redraw.
handlers.TRAIT_TREE_CURRENCY_INFO_UPDATED = handlers.CHARACTER_POINTS_CHANGED
-- The server refusing a trait commit (retail's event; args:
-- configID). Settles the "traits" point in flight at once instead of after
-- the timeout.
handlers.CONFIG_COMMIT_FAILED = function(configID)
  R2F.Talents.OnCommitFailed(configID)
  R2F.MainWindow.RequestRefresh()
end
handlers.PLAYER_LEVEL_UP = function() R2F.MainWindow.RequestRefresh() end
-- Mr.BiZ: an item the tab asked the client for has loaded (quality, icon).
handlers.GET_ITEM_INFO_RECEIVED = function() R2F.BiZTab.OnItemInfo() end
-- Professions: the game only lists recipes while a profession window
-- is open. Most professions use the trade skill window; Enchanting (and Beast
-- Training) used the older "craft" window in Classic. Both are read.
handlers.TRADE_SKILL_SHOW = function() R2F.Professions.OnShow("trade") end
handlers.TRADE_SKILL_UPDATE = function() R2F.Professions.OnUpdate("trade") end
handlers.CRAFT_SHOW = function() R2F.Professions.OnShow("craft") end
handlers.CRAFT_UPDATE = function() R2F.Professions.OnUpdate("craft") end
-- Modern clients: the recipe list arrives with these instead.
handlers.TRADE_SKILL_LIST_UPDATE = function() R2F.Professions.OnUpdate("trade") end
handlers.TRADE_SKILL_DATA_SOURCE_CHANGED = function() R2F.Professions.OnUpdate("trade") end
-- A CVar changed (/console, Blizzard's options, another addon, or our own
-- Quick settings): redraw Home's boxes from the live values. They
-- are also re-read every time the Home tab opens, so a client without this
-- event only loses the live update while Home is already showing.
handlers.CVAR_UPDATE = function() R2F.Settings.RequestRefresh() end
-- The game refusing a protected call from an addon (args: addon name,
-- function). Only ours matters; for LearnTalent it means guided mode.
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
R2F.Bindings = {
  Toggle = function() R2F.MainWindow.Toggle() end,
  OpenMacros = function() R2F.MainWindow.Toggle("macros") end,
  OpenTalents = function() R2F.MainWindow.Toggle("talents") end,
}

-- Slash commands. /r2f macros, /r2f talents and /r2ft OPEN their tab
-- (typing one never hides what you asked for); /r2f with nothing after it
-- toggles, like the minimap button's left-click and the Toggle key.
-- /r2f import still works: Macros tab + Import window.
local function printHelp()
  for _, line in ipairs(L.HELP_LINES) do R2F.Print(line) end
end

local COMMANDS = {
  [""] = function() R2F.MainWindow.Toggle() end,
  macros = function() R2F.MainWindow.Show("macros") end,
  talents = function() R2F.MainWindow.Show("talents") end,
  settings = function() R2F.MainWindow.Show("settings") end,
  gameplay = function() R2F.MainWindow.Show("gameplay") end,
  reminders = function() R2F.MainWindow.Show("gameplay") end,   -- the tab's former name
  plan = function() R2F.MainWindow.Show("plan") end,
  -- BiZNav arrow
  way = function() R2F.Print(L.NAV_WAY_USAGE) end,
  clear = function() if not R2F.Nav.Clear() then R2F.Print(L.NAV_NONE) end end,
  bis = function() R2F.MainWindow.Show("bis") end,
  biz = function() R2F.MainWindow.Show("bis") end,
  copychat = function() R2F.CopyChat.Command() end,
  ammo = function() R2F.Ammo.ToggleShown() end,
  ["ammo lock"] = function() R2F.Ammo.ToggleLock() end,
  minimap = function() R2F.Minimap.ToggleHidden() end,
  stance = function() R2F.Stance.ToggleShown() end,
  ["stance lock"] = function() R2F.Stance.ToggleLock() end,
  help = printHelp,
  import = function()
    R2F.MainWindow.Show("macros")
    R2F.ImportFrame.Show()
  end,
  -- Read-only, so these work in combat.
  copybuild = function() R2F.Talents.CopyMyBuild() end,
  profs = function() R2F.Professions.Export() end,
  professions = function() R2F.Professions.Export() end,
}

-- Troubleshooting tools: "/r2f debug <tool>". Each prints what the addon sees, so a bug report
-- can show it. They are also accepted without "debug" (the names they had before).
local DEBUG = {
  ranks = function() R2F.Ranks.Print() end,
  rank = function(arg) R2F.Ranks.Debug(arg) end,
  bags = function() R2F.Bags.Report() end,
  profs = function() R2F.Professions.Debug() end,
  auras = function() R2F.Diag.Auras() end,
  reactlog = function() R2F.Gameplay.PrintReactLog() end,
  gossip = function() R2F.Gameplay.PrintGossip() end,
  who = function() R2F.Gameplay.PrintWho() end,
  here = function() R2F.Plan.Here() end,
  gear = function() R2F.GearScore.Debug() end,
}
local DEBUG_ALIASES = { rankdebug = "rank", profdebug = "profs" }
R2F.DEBUG = DEBUG

local function printDebugHelp()
  for _, line in ipairs(L.DEBUG_LINES) do R2F.Print(line) end
end

-- The line was lower-cased; give a spell name its capitals back (lookups ignore case anyway).
local function titleCase(s)
  return (s:gsub("(%a)([%w']*)", function(c, rest) return c:upper() .. rest end))
end

-- Runs a debug tool if `name` is one (or an old alias). Returns true if it was.
local function runDebug(name, arg)
  name = DEBUG_ALIASES[name] or name
  local fn = DEBUG[name]
  if not fn then return false end
  fn(name == "rank" and titleCase(arg or "") or arg)
  return true
end
R2F.COMMANDS = COMMANDS

-- SLASH_R2F1 / SLASH_R2FT1 and the R2F / R2FT fields in SlashCmdList are the
-- WoW API's way to register a command; with R2F, R2FDB, R2FCharDB, the
-- binding labels and the R2F-prefixed frame names they are the only globals.
_G.SLASH_R2F1 = "/r2f"
SlashCmdList.R2F = function(msg)
  -- "/r2f way Zone x y label": keep the capitals the player typed for the arrow's label.
  local wayRest = (msg or ""):match("^%s*[Ww][Aa][Yy]%s+(.*)$")
  if wayRest then R2F.Nav.WayCommand(wayRest) return end
  msg = (msg or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
  local fn = COMMANDS[msg]
  local chatArg = msg:match("^copychat%s+(%d+)$")
  local word, rest = msg:match("^(%S+)%s*(.*)$")
  if fn then
    fn()
  elseif chatArg then
    R2F.CopyChat.Command(chatArg)
  elseif word == "debug" then
    local tool, arg = rest:match("^(%S+)%s*(.*)$")
    if not tool then
      printDebugHelp()
    elseif not runDebug(tool, arg) then
      R2F.Print(L.UNKNOWN_DEBUG:format(tool))
    end
  elseif not (word and runDebug(word, rest)) then
    R2F.Print(L.UNKNOWN_COMMAND:format(msg))
  end
end

-- BiZNav: /bizway (the arrow; Nav.WayCommand reads every form).
_G.SLASH_R2FWAY1 = "/bizway"
SlashCmdList.R2FWAY = function(msg) R2F.Nav.WayCommand(msg) end

_G.SLASH_R2FT1 = "/r2ft"
SlashCmdList.R2FT = function() R2F.MainWindow.Show("talents") end

-- Mr.BiZ: /biz and /mrbiz open the BiS tab (/bis is taken by several BiS
-- addons, so it is left to them). "/biz wish" opens the wishlist.
_G.SLASH_R2FBIZ1 = "/biz"
_G.SLASH_R2FBIZ2 = "/mrbiz"
SlashCmdList.R2FBIZ = function(msg)
  msg = (msg or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
  R2F.BiZTab.Show((msg == "wish" or msg == "wishlist") and "wish" or nil)
end
