-- General.lua: "my general settings": the game settings you set up once, saved on the account and applied to any character.
--
-- "Save my general settings" (minimap menu, or /r2f general save) reads this character and keeps, in R2FDB (account wide):
--   1. Game settings (CVars) from the list below: camera, auto loot, names and nameplates, class colours, silhouette, raid
--      frames, combat text, chat behaviour and the like. Only the ones this client knows are kept.
--   2. Which Action Bars are switched on (Action Bars 2 to 8).
--   3. Chat: the windows (name, font size, colour, locked, which message groups and channels each shows) and which message
--      types show names in class colours. The Combat Log window is left alone.
-- "Apply my general settings" (any character, /r2f general apply) lists what it will do, asks, then writes them with the
-- game's own calls (SetCVar, SetActionBarToggles and the chat window functions of the Chat Settings), out of combat.
--
-- Not in here on purpose: graphics, sound and the Edit Mode layouts (placement and size of the chat windows come with the
-- layout) are already shared by every character of the account; key bindings have their own account set; the buttons'
-- contents are per class (see Setup.lua).
--
-- Read-only on game tables; the writes are what a player would do by hand in Options and the chat window's settings.

local _, R2F = ...
local L = R2F.L

local General = {}
R2F.General = General

-- The settings kept. Unknown CVars (this client does not have them) are skipped, so the list may be generous.
General.CVARS = {
  -- camera
  "cameraDistanceMaxZoomFactor", "cameraSmoothStyle", "cameraSmoothTrackingStyle", "cameraPivot", "cameraWaterCollision",
  "cameraYawMoveSpeed", "cameraPitchMoveSpeed", "cameraTerrainTilt", "cameraBobbing", "cameraReduceUnexpectedMovement",
  "cameraSmoothPitch", "cameraSmoothYaw",
  -- loot and combat behaviour
  "autoLootDefault", "autoLootRate", "lootUnderMouse", "autoSelfCast", "autoDismountFlying", "stopAutoAttackOnTargetChange",
  "assistAttack", "ActionButtonUseKeyDown", "lockActionBars", "alwaysShowActionBars", "countdownForCooldowns",
  "showTargetOfTarget", "threatShowNumeric", "spellActivationOverlayOpacity",
  -- names, nameplates, silhouette
  "UnitNameOwn", "UnitNameNPC", "UnitNameFriendlyPlayerName", "UnitNameFriendlyPetName", "UnitNameFriendlyGuardianName",
  "UnitNameFriendlyTotemName", "UnitNameEnemyPlayerName", "UnitNameEnemyPetName", "UnitNameEnemyGuardianName",
  "UnitNameEnemyTotemName", "UnitNamePlayerGuild", "UnitNamePlayerPVPTitle", "UnitNameNonCombatCreatureName",
  "UnitNameGuildTitle", "UnitNameHostleNPC", "UnitNameInteractiveNPC", "UnitNameFriendlySpecialNPCName",
  "nameplateShowEnemies", "nameplateShowFriends", "nameplateShowAll", "nameplateShowEnemyMinus", "nameplateShowEnemyPets",
  "nameplateShowEnemyGuardians", "nameplateShowEnemyTotems", "nameplateShowFriendlyNPCs", "nameplateShowClassColor",
  "nameplateShowFriendlyClassColor", "nameplateUseClassColorForFriendlyPlayerUnitNames", "nameplateInfoDisplay",
  "nameplateOtherAtBase", "nameplateMotion", "nameplateMaxDistance", "nameplateSelfAlpha",
  "occludedSilhouettePlayer", "occludedSilhouetteNPC", "OutlineEngineMode",
  -- raid and party frames
  "raidFramesDisplayClassColor", "raidFramesDisplayPowerBars", "raidOptionDisplayPets", "raidFramesHealthText",
  "raidOptionKeepGroupsTogether", "raidOptionDisplayMainTankAndAssist", "raidFramesDisplayOnlyDispellableDebuffs",
  "useCompactPartyFrames", "showPartyBackground", "partyFramesDisplayPowerBars",
  -- floating combat text
  "enableFloatingCombatText", "floatingCombatTextCombatDamage", "floatingCombatTextCombatHealing",
  "floatingCombatTextCombatState", "floatingCombatTextReactives", "floatingCombatTextEnergyGains",
  "floatingCombatTextComboPoints", "floatingCombatTextLowManaHealth", "floatingCombatTextDodgeParryMiss",
  "floatingCombatTextSpellMechanics", "floatingCombatTextHonorGains", "floatingCombatTextRepChanges",
  "floatingCombatTextFriendlyHealers", "floatingCombatTextDirectionalScale", "floatingCombatTextCombatLogPeriodicSpells",
  "floatingCombatTextPetMeleeDamage", "floatingCombatTextPetSpellDamage", "floatingCombatTextAuras",
  "floatingCombatTextCombatDamageAllAutos", "floatingCombatTextCombatHealingAbsorbSelf",
  "floatingCombatTextCombatHealingAbsorbTarget", "floatingCombatTextCombatDamageDirectionalOffset",
  "floatingCombatTextCombatDamageDirectionalScale", "WorldTextScale", "floatingCombatTextFloatMode",
  -- interface
  "questPOI", "showQuestLevel", "mapFade", "combinedBags", "xpBarText", "timeMgrUseMilitaryTime", "timeMgrUseLocalTime",
  "showTutorials", "showToastOnline", "showToastOffline", "showToastBroadcast", "displayFreeBagSlots", "weatherDensity",
  "minimapZoom", "rotateMinimap", "scriptErrors", "UberTooltips", "showNPETutorials", "colorblindMode", "Sound_EnableErrorSpeech",
  "mouseSpeed", "enableMouseSpeed", "autoInteract", "interactOnLeftClick", "autoQuestWatch", "autoQuestProgress",
  "showGameTips", "gameTip", "synchronizeChatFrames", "profanityFilter", "spamFilter",
  -- chat behaviour
  "chatStyle", "chatMouseScroll", "whisperMode", "removeChatDelay", "chatBubbles", "chatBubblesParty", "colorChatNamesByClass",
  "speechToText", "textToSpeech", "chatClassColorOverride", "wholeChatWindowClickable", "showTimestamps",
}

local function db()
  return R2F.Library.db
end

local function say(msg) R2F.Print(msg) end

local function numWindows()
  return tonumber(_G.NUM_CHAT_WINDOWS) or 10
end

local function chatFrame(i)
  return _G["ChatFrame" .. i]
end

-- ---------------------------------------------------------------------------
-- Reading this character
-- ---------------------------------------------------------------------------

-- The swing timer switch (Options > Advanced Options > "Enable Swing Timer") is a game setting whose CVar name we are not
-- sure of, so the client's own list of console variables is searched for names with "swing" in them.
-- Returns { { name, value }, ... } sorted by name; empty when the client cannot list them.
function General.SwingCVars()
  local out = {}
  local c = _G.C_Console
  if not (c and c.GetAllCommands) then return out end
  local ok, list = pcall(c.GetAllCommands)
  if not (ok and type(list) == "table") then return out end
  for _, info in ipairs(list) do
    local name = type(info) == "table" and info.command
    -- commandType 0 = a console variable (the others are commands, macros and scripts)
    if type(name) == "string" and name:lower():find("swing") and (info.commandType == nil or info.commandType == 0) then
      local v = R2F.QuickSettings.Read(name)
      if v ~= nil then out[#out + 1] = { name = name, value = v } end
    end
  end
  table.sort(out, function(a, b) return a.name < b.name end)
  return out
end

local function readCVars()
  local out, n = {}, 0
  local names = {}
  for _, name in ipairs(General.CVARS) do names[#names + 1] = name end
  for _, sc in ipairs(General.SwingCVars()) do names[#names + 1] = sc.name end
  for _, name in ipairs(names) do
    local v = R2F.QuickSettings.Read(name)
    if v ~= nil then out[name] = v n = n + 1 end
  end
  return out, n
end

local function readToggles()
  if not _G.GetActionBarToggles then return nil end
  local t = { _G.GetActionBarToggles() }
  for i = 1, 7 do t[i] = t[i] and true or false end
  return t
end

-- Alternating values (name, zoneID, name, zoneID ...) of GetChatWindowChannels / GetChatWindowMessages into a list of names.
local function names(first, step, ...)
  local out = {}
  local n = select("#", ...)
  for i = first, n, step do
    local v = select(i, ...)
    if type(v) == "string" then out[#out + 1] = v end
  end
  return out
end

local function readWindow(i)
  if not _G.GetChatWindowInfo then return nil end
  local name, size, r, g, b, a, shown, locked, docked = _G.GetChatWindowInfo(i)
  if type(name) ~= "string" or name == "" then return nil end
  -- The combat log has its own filters and is never touched.
  if name == (_G.COMBAT_LOG or "Combat Log") or name == "Combat Log" then return nil end
  local groups = _G.GetChatWindowMessages and names(1, 1, _G.GetChatWindowMessages(i)) or {}
  local channels = _G.GetChatWindowChannels and names(1, 2, _G.GetChatWindowChannels(i)) or {}
  return { name = name, size = size, r = r, g = g, b = b, a = a, shown = shown and true or false,
           locked = locked and true or false, docked = docked and tonumber(docked) or 0, groups = groups, channels = channels }
end

local function readChat()
  local windows = {}
  for i = 1, numWindows() do
    local w = readWindow(i)
    if w then windows[#windows + 1] = w end
  end
  -- Message types whose sender names are painted in class colours (the Chat Settings' "Class colors" boxes).
  local classNames = {}
  if type(_G.ChatTypeInfo) == "table" then
    for key, info in pairs(_G.ChatTypeInfo) do
      if type(key) == "string" and type(info) == "table" and info.colorNameByClass then classNames[#classNames + 1] = key end
    end
    table.sort(classNames)
  end
  return { windows = windows, classNames = classNames }
end

-- Saves this character's settings on the account. Returns the saved table.
function General.Save()
  local cvars, nCvars = readCVars()
  local saved = { time = _G.time and _G.time() or 0, cvars = cvars, bars = readToggles(), chat = readChat() }
  db().general = saved
  say(L.GENERAL_SAVED:format(nCvars, #saved.chat.windows, #saved.chat.classNames))
  return saved
end

function General.Has()
  local g = db() and db().general
  return type(g) == "table" and type(g.cvars) == "table"
end

function General.Clear()
  db().general = nil
  say(L.GENERAL_CLEARED)
end

-- ---------------------------------------------------------------------------
-- Applying
-- ---------------------------------------------------------------------------

-- What Apply would do, as chat-ready lines (also the text of the confirmation).
function General.Describe()
  local g = db().general
  local lines = { L.GENERAL_STEP_CVARS:format(General.CountCVars(g.cvars)) }
  if g.bars then lines[#lines + 1] = L.GENERAL_STEP_BARS end
  local w = g.chat and g.chat.windows or {}
  if #w > 0 then
    local list = {}
    for _, win in ipairs(w) do list[#list + 1] = win.name end
    lines[#lines + 1] = L.GENERAL_STEP_CHAT:format(#w, table.concat(list, ", "))
  end
  if g.chat and #g.chat.classNames > 0 then lines[#lines + 1] = L.GENERAL_STEP_CLASSNAMES end
  return lines
end

function General.CountCVars(t)
  local n = 0
  for _ in pairs(t or {}) do n = n + 1 end
  return n
end

local function applyCVars(g)
  local set, skipped = 0, {}
  for name, value in pairs(g.cvars) do
    -- A CVar this client does not know is left alone (a setting saved on another client version).
    if R2F.QuickSettings.Read(name) ~= nil then
      if R2F.QuickSettings.Write(name, value) then set = set + 1 else skipped[#skipped + 1] = name end
    end
  end
  table.sort(skipped)
  say(L.GENERAL_DONE_CVARS:format(set))
  if #skipped > 0 then say(L.GENERAL_NOT_TAKEN:format(table.concat(skipped, ", "))) end
end

local function applyBars(g)
  if not (g.bars and _G.SetActionBarToggles) then return end
  local t = g.bars
  pcall(_G.SetActionBarToggles, t[1], t[2], t[3], t[4], t[5], t[6], t[7])
  say(L.GENERAL_DONE_BARS)
end

-- The window called `name`: an existing one, or a new one (nil when the game would not make one).
local function windowByName(name)
  for i = 1, numWindows() do
    local n = _G.GetChatWindowInfo and _G.GetChatWindowInfo(i)
    if n == name then return chatFrame(i), i end
  end
  if _G.FCF_OpenNewWindow then
    local ok, frame = pcall(_G.FCF_OpenNewWindow, name)
    if ok and frame then return frame, frame:GetID() end
  end
  return nil
end

local function applyWindow(w)
  local frame, id = windowByName(w.name)
  if not frame then return false end
  local function try(fn, ...)
    if type(fn) == "function" then pcall(fn, ...) end
  end
  try(_G.FCF_SetChatWindowFontSize, nil, frame, w.size)
  if w.r then try(_G.FCF_SetWindowColor, frame, w.r, w.g, w.b) end
  if w.a then try(_G.FCF_SetWindowAlpha, frame, w.a) end
  -- Which message types and channels this window shows: cleared, then the saved ones.
  try(_G.ChatFrame_RemoveAllMessageGroups, frame)
  for _, group in ipairs(w.groups) do try(_G.ChatFrame_AddMessageGroup, frame, group) end
  try(_G.ChatFrame_RemoveAllChannels, frame)
  for _, ch in ipairs(w.channels) do try(_G.ChatFrame_AddChannel, frame, ch) end
  try(_G.FCF_SetLocked, frame, w.locked)
  -- A window that was a tab of the main window (docked) becomes one here; where a loose window sits is part of the Edit Mode
  -- layout, so it follows the layout, not this.
  local dock = _G.GENERAL_CHAT_DOCK
  if w.docked and w.docked > 0 and id and id > 2 and type(dock) == "table" and dock.DOCKED_CHAT_FRAMES then
    local docked = false
    for _, f in ipairs(dock.DOCKED_CHAT_FRAMES) do if f == frame then docked = true end end
    if not docked then try(_G.FCF_DockFrame, frame, #dock.DOCKED_CHAT_FRAMES + 1, true) end
  end
  return true
end

local function applyChat(g)
  if not g.chat then return end
  local ok, failed = 0, {}
  for _, w in ipairs(g.chat.windows or {}) do
    if applyWindow(w) then ok = ok + 1 else failed[#failed + 1] = w.name end
  end
  if _G.ToggleChatColorNamesByClassGroup then
    for _, key in ipairs(g.chat.classNames or {}) do pcall(_G.ToggleChatColorNamesByClassGroup, true, key) end
  end
  say(L.GENERAL_DONE_CHAT:format(ok))
  if #failed > 0 then say(L.GENERAL_CHAT_FAILED:format(table.concat(failed, ", "))) end
end

function General.Execute()
  local g = db().general
  if type(g) ~= "table" then return say(L.GENERAL_NOTHING_SAVED) end
  if R2F.InCombat() then return say(L.SETUP_COMBAT) end
  applyCVars(g)
  applyBars(g)
  applyChat(g)
  say(L.GENERAL_FINISHED)
end

-- Entry points: Save asks nothing (it only reads); Apply lists what it will do and asks first.
function General.Apply()
  if not General.Has() then return say(L.GENERAL_NOTHING_SAVED) end
  if R2F.InCombat() then return say(L.SETUP_COMBAT) end
  R2F.UI.Confirm(L.GENERAL_CONFIRM:format(table.concat(General.Describe(), "\n")), L.GENERAL_GO, L.BTN_CANCEL, function()
    General.Execute()
  end)
end

-- /r2f general [save | apply | clear]
function General.Command(rest)
  rest = (rest or ""):lower()
  if rest == "save" then General.Save()
  elseif rest == "apply" then General.Apply()
  elseif rest == "clear" then General.Clear()
  elseif rest == "swing" then
    local list = General.SwingCVars()
    if #list == 0 then say(L.GENERAL_SWING_NONE) end
    for _, sc in ipairs(list) do say(L.GENERAL_SWING_LINE:format(sc.name, sc.value)) end
  else
    say(General.Has() and L.GENERAL_STATUS:format(General.CountCVars(db().general.cvars), #db().general.chat.windows)
        or L.GENERAL_NOTHING_SAVED)
    say(L.GENERAL_USAGE)
  end
end
