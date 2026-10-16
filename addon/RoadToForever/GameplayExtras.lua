-- GameplayExtras.lua: more Gameplay features:
-- mail to your own characters, free bag slots on the backpack, fast loot.
-- Same rules as Gameplay.lua: one switch each, all OFF until ticked, handlers in pcall,
-- written from scratch.

local _, R2F = ...
local L = R2F.L
local Gameplay = R2F.Gameplay

-- ---------------------------------------------------------------------------
-- Your own characters (for mail), remembered whenever one logs in
-- ---------------------------------------------------------------------------

-- R2FDB.chars[realm][full name or name] = { class = "WARRIOR", level = 18, faction = "Alliance" }.
-- Recorded always (a few bytes per character) so the list is complete the day the box is
-- ticked; only characters that have logged in with the addon are known.
function Gameplay.RememberCharacter()
  local name = UnitName and UnitName("player")
  local realm = GetRealmName and GetRealmName()
  if not (name and realm) then return end
  local db = R2F.Library.db
  db.chars = db.chars or {}
  db.chars[realm] = db.chars[realm] or {}
  local _, class = UnitClass("player")
  -- What the client calls the character in full (on this client, some names have a surname as
  -- UnitName's second value instead of a realm). Mail wants exactly this form.
  local full = GetUnitName and GetUnitName("player", true)
  if type(full) ~= "string" or full == "" or (issecretvalue and issecretvalue(full)) then full = nil end
  -- Keyed by the full name: two characters can share the first name (Anna Stormborn and
  -- Anna Ironfist) and one used to overwrite the other. An old entry saved under the bare
  -- name is dropped when it is this character.
  local key = full or name
  local old = db.chars[realm][name]
  if key ~= name and old and (old.full == full or old.full == nil) then db.chars[realm][name] = nil end
  db.chars[realm][key] = {
    name = name,
    full = full,
    class = class,
    level = UnitLevel and UnitLevel("player") or 0,
    faction = UnitFactionGroup and (UnitFactionGroup("player")) or "",
    seen = time and time() or 0,
  }
end

-- /r2f debug who: every way the client can name this character (useful for finding where a
-- two-part name comes from). Prints one line per candidate; secret values are shown as such.
function Gameplay.PrintWho()
  local function show(label, ...)
    local parts = {}
    for i = 1, select("#", ...) do
      local v = select(i, ...)
      if issecretvalue and issecretvalue(v) then v = "<secret>" end
      parts[#parts + 1] = tostring(v)
    end
    R2F.Print(label .. ": " .. table.concat(parts, " | "))
  end
  local function try(label, fn, ...)
    local ok, a, b = pcall(fn, ...)
    if ok then show(label, a, b) else R2F.Print(label .. ": error") end
  end
  if UnitName then try("UnitName", UnitName, "player") end
  if UnitFullName then try("UnitFullName", UnitFullName, "player") end
  if GetUnitName then
    try("GetUnitName(player)", GetUnitName, "player")
    try("GetUnitName(player, true)", GetUnitName, "player", true)
  end
  if UnitPVPName then try("UnitPVPName", UnitPVPName, "player") end
  if GetRealmName then try("GetRealmName", GetRealmName) end
  if GetNormalizedRealmName then try("GetNormalizedRealmName", GetNormalizedRealmName) end
  if GetPlayerInfoByGUID and UnitGUID then
    try("GetPlayerInfoByGUID", function() return GetPlayerInfoByGUID(UnitGUID("player")) end)
  end
  if CharacterFrameTitleText and CharacterFrameTitleText.GetText then
    try("Character window title", function() return CharacterFrameTitleText:GetText() end)
  end
  if C_PlayerInfo and C_PlayerInfo.GetName then try("C_PlayerInfo.GetName", C_PlayerInfo.GetName) end
end

-- The realm part of a full character name ("Name-Realm"): the game's normalised realm name
-- (no spaces or dashes) when it has one, else the realm name with those removed.
local function realmSuffix()
  local normalized = GetNormalizedRealmName and GetNormalizedRealmName()
  if normalized and normalized ~= "" then return normalized end
  local realm = GetRealmName and GetRealmName() or ""
  return (realm:gsub("[%s%-']", ""))
end

-- Your other characters on this realm and faction, sorted by name:
-- { { name =, full = "Name-Realm", class =, level = }, ... }. On this client mail needs the
-- FULL name (a bare name doesn't arrive).
function Gameplay.OtherCharacters()
  local out = {}
  local db = R2F.Library.db
  local realm = GetRealmName and GetRealmName()
  local me = UnitName and UnitName("player")
  local meFull = GetUnitName and GetUnitName("player", true)
  if type(meFull) ~= "string" or (issecretvalue and issecretvalue(meFull)) then meFull = nil end
  local faction = UnitFactionGroup and (UnitFactionGroup("player")) or ""
  for key, c in pairs((db.chars and realm and db.chars[realm]) or {}) do
    local name = c.name or key
    local isMe = (meFull and c.full) and c.full == meFull or (not (meFull and c.full) and name == me)
    if not isMe and (c.faction == faction or faction == "" or c.faction == "") then
      out[#out + 1] = { name = name, full = c.full or (name .. "-" .. realmSuffix()), class = c.class, level = c.level or 0 }
    end
  end
  table.sort(out, function(a, b) return (a.full or a.name) < (b.full or b.name) end)
  return out
end

local function classColor(class)
  local c = _G.RAID_CLASS_COLORS and _G.RAID_CLASS_COLORS[class]
  if c then return ("|cff%02x%02x%02x"):format(c.r * 255 + 0.5, c.g * 255 + 0.5, c.b * 255 + 0.5) end
  return "|cffffffff"
end

-- ---------------------------------------------------------------------------
-- Mail: a button after the recipient field listing your own characters
-- ---------------------------------------------------------------------------

local mailButton

local function mailBox()
  return _G.SendMailNameEditBox
end

local function openAltMenu()
  local items = { { kind = "title", text = L.GP_MAIL_TITLE } }
  local alts = Gameplay.OtherCharacters()
  if #alts == 0 then
    items[#items + 1] = { kind = "title", text = L.GP_MAIL_NONE }
  end
  for _, a in ipairs(alts) do
    items[#items + 1] = {
      kind = "button",
      text = ("%s%s|r  %d"):format(classColor(a.class), a.name, a.level),
      func = function()
        local box = mailBox()
        if box then
          box:SetText(a.full)
          if box.SetCursorPosition then box:SetCursorPosition(#a.full) end
        end
      end,
    }
  end
  items[#items + 1] = { kind = "divider" }
  items[#items + 1] = { kind = "title", text = L.GP_MAIL_FOOT }
  R2F.UI.ContextMenu(items)
end

local function ensureMailButton()
  local box = mailBox()
  if not box then return nil end
  if not mailButton then
    mailButton = CreateFrame("Button", "R2FMailAltsButton", box:GetParent() or UIParent)
    mailButton:SetSize(22, 22)
    mailButton:SetNormalTexture("Interface\\Buttons\\UI-DialogBox-Button-Up")
    mailButton:SetPushedTexture("Interface\\Buttons\\UI-DialogBox-Button-Down")
    mailButton:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    local arrow = mailButton:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    arrow:SetPoint("CENTER", 0, 1)
    arrow:SetText("v")
    mailButton:SetScript("OnClick", function(self) openAltMenu(self) end)
    mailButton:SetScript("OnEnter", function(self)
      GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
      GameTooltip:AddLine(L.GP_MAIL_TIP, 1, 1, 1, true)
      GameTooltip:Show()
    end)
    mailButton:SetScript("OnLeave", function() GameTooltip:Hide() end)
  end
  mailButton:ClearAllPoints()
  mailButton:SetPoint("LEFT", box, "RIGHT", 2, 0)
  return mailButton
end

Gameplay.Register({
  key = "mailalts", group = "screen", title = "GP_MAIL", tip = "GP_MAIL_TIP",
  events = {
    MAIL_SHOW = function() local b = ensureMailButton() if b then b:Show() end end,
  },
  onToggle = function(on)
    if mailButton then mailButton:SetShown(on) end
    if on and mailBox() and mailBox():IsVisible() then ensureMailButton():Show() end
  end,
})

-- ---------------------------------------------------------------------------
-- Free bag slots on the backpack
-- ---------------------------------------------------------------------------

local slotText

local function backpackButton()
  if _G.MainMenuBarBackpackButton then return _G.MainMenuBarBackpackButton end
  local bar = _G.BagsBar
  return bar and bar.MainMenuBarBackpackButton or nil
end

-- Free slots in the general-purpose bags (ammo pouches, quivers and the like don't count).
function Gameplay.FreeBagSlots()
  if not (C_Container and C_Container.GetContainerNumFreeSlots) then return nil end
  local free = 0
  for bag = 0, (NUM_BAG_SLOTS or 4) do
    local n, bagType = C_Container.GetContainerNumFreeSlots(bag)
    if n and (bagType == nil or bagType == 0) then free = free + n end
  end
  return free
end

local function updateSlots()
  if not slotText then return end
  local free = Gameplay.FreeBagSlots()
  if free == nil then slotText:SetText("") return end
  slotText:SetText(tostring(free))
  if free <= 3 then slotText:SetTextColor(1, 0.3, 0.3) else slotText:SetTextColor(1, 1, 1) end
end

Gameplay.Register({
  key = "bagslots", group = "screen", title = "GP_BAGSLOTS", tip = "GP_BAGSLOTS_TIP",
  available = function()
    return backpackButton() ~= nil and C_Container ~= nil and C_Container.GetContainerNumFreeSlots ~= nil
  end,
  events = {
    BAG_UPDATE_DELAYED = updateSlots,
    PLAYER_ENTERING_WORLD = updateSlots,
  },
  onToggle = function(on)
    local btn = backpackButton()
    if not btn then return end
    if not slotText then
      slotText = btn:CreateFontString(nil, "OVERLAY", "NumberFontNormal")
      -- Top edge: the game's own count sits at the bottom of the button.
      slotText:SetPoint("TOP", btn, "TOP", 0, -2)
    end
    slotText:SetShown(on)
    if on then updateSlots() end
  end,
})

-- ---------------------------------------------------------------------------
-- Sort button on the bags
-- ---------------------------------------------------------------------------

-- A small "Sort" button sitting just above the backpack window (or the combined bag), one click =
-- the game's own bag clean-up (C_Container.SortBags, the same thing its bag menu runs). It is a child
-- of the bag window, placed OUTSIDE it so it never covers the game's own buttons; nothing of the
-- game's is changed. Out of combat only (the game refuses to sort in combat).
local sortButtons = {}   -- bag window -> button

local function sortBagsNow()
  if InCombatLockdown and InCombatLockdown() then R2F.Print(L.GP_SORT_COMBAT) return end
  if C_Container and C_Container.SortBags then C_Container.SortBags() end
end

local function refreshSortButton(frame, btn)
  -- Only the combined bag, or the classic window of the backpack (bag id 0).
  local wanted = Gameplay.IsOn("bagsort") and (frame == _G.ContainerFrameCombinedBags or frame:GetID() == 0)
  btn:SetShown(wanted and true or false)
end

local function ensureSortButtons()
  local frames = { _G.ContainerFrameCombinedBags }
  for i = 1, (_G.NUM_CONTAINER_FRAMES or 13) do frames[#frames + 1] = _G["ContainerFrame" .. i] end
  for _, frame in ipairs(frames) do
    if frame and not sortButtons[frame] then
      local btn = CreateFrame("Button", nil, frame, "UIPanelButtonTemplate")
      btn:SetSize(54, 20)
      btn:SetText(L.GP_SORT_BUTTON)
      btn:SetPoint("BOTTOMRIGHT", frame, "TOPRIGHT", -4, 1)
      btn:SetScript("OnClick", sortBagsNow)
      btn:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
        GameTooltip:AddLine(L.GP_SORT_BUTTON, 1, 1, 1)
        GameTooltip:AddLine(L.GP_SORT_TIP, 1, 0.82, 0, true)
        GameTooltip:Show()
      end)
      btn:SetScript("OnLeave", function() GameTooltip:Hide() end)
      sortButtons[frame] = btn
      if frame.HookScript then frame:HookScript("OnShow", function() refreshSortButton(frame, btn) end) end
    end
  end
  for frame, btn in pairs(sortButtons) do refreshSortButton(frame, btn) end
end

Gameplay.Register({
  key = "bagsort", group = "auto", title = "GP_SORT", tip = "GP_SORT_TIP2",
  available = function() return C_Container ~= nil and C_Container.SortBags ~= nil end,
  events = { PLAYER_ENTERING_WORLD = ensureSortButtons },
  onToggle = function()
    ensureSortButtons()
  end,
})

-- ---------------------------------------------------------------------------
-- Fast loot
-- ---------------------------------------------------------------------------

-- Takes the waiting out of looting: when the loot window is ready, every slot is looted at
-- once instead of one slot per autoLootRate. It only speeds up what the game's own
-- auto-loot does: if auto-loot is off (and the toggle key isn't held), nothing happens.
-- Greed rolling on greens is not part of this (it acts in front of other people).
Gameplay.Register({
  key = "fastloot", group = "auto", title = "GP_FASTLOOT", tip = "GP_FASTLOOT_TIP",
  events = {
    LOOT_READY = function(autoLoot)
      local auto = autoLoot
      if auto == nil then
        local get = _G.GetCVarBool
        auto = get and get("autoLootDefault") or false
      end
      if IsModifiedClick and IsModifiedClick("AUTOLOOTTOGGLE") then auto = not auto end
      if not auto then return end
      for slot = (GetNumLootItems and GetNumLootItems() or 0), 1, -1 do
        LootSlot(slot)
      end
    end,
  },
})

-- ---------------------------------------------------------------------------
-- Remember characters
-- ---------------------------------------------------------------------------

-- PLAYER_LOGIN (Core.lua): note this character now and again when it levels up.
function Gameplay.InitCharacters()
  Gameplay.RememberCharacter()
  local f = CreateFrame("Frame")
  f:SetScript("OnEvent", function() Gameplay.RememberCharacter() end)
  pcall(f.RegisterEvent, f, "PLAYER_LEVEL_UP")
end

-- ---------------------------------------------------------------------------
-- Reactive ability alert ("<Revenge>"): our own, movable
-- ---------------------------------------------------------------------------

-- Moving the game's floating combat text path (CombatText.textLocations) to place the
-- "<Revenge>" alert does NOT work: writing into Blizzard's table taints it, and this client then
-- refuses arithmetic on tainted values ("attempt to perform arithmetic on field 'startY' (a secret
-- number value, while execution tainted by 'RoadToForever')"). So nothing of the
-- game's data or frames is written. Instead:
--   * "Reactive alert (own text)": when the game announces a reactive ability (COMBAT_TEXT_UPDATE
--     with "SPELL_ACTIVE", the same event its own text comes from) we show "<Revenge>" ourselves, in
--     our own frame, at a marker you drag where you want it, for a couple of seconds.
--   * "Lock reactive alert position": hides the marker, keeps the place.
--   * "Hide the game's own reactive text": sets the game's setting floatingCombatTextReactives_v2 to 0
--     (through QuickSettings, the one place that writes game settings) and puts your value back.
-- If the event's text is a "secret" value the alert says "Ability ready" instead of the name.
local ALERT_SECONDS = 2.5
local alertMarker, alertText, alertToken = nil, nil, 0
local REACT_CVAR = "floatingCombatTextReactives_v2"

local function alertDb()
  return R2F.Library.db.fct
end

local function updateAlertMarker()
  if not alertMarker then return end
  local show = Gameplay.IsOn("reactalert") and not Gameplay.IsOn("reactlock")
  alertMarker:SetShown(show)
  if show then
    alertMarker.border:SetColorTexture(0.95, 0.75, 0.1, 1)
    alertMarker.icon:SetTexture("Interface\\Icons\\Ability_Warrior_Revenge")
    alertMarker.count:SetText(L.GP_REACT_MARKER)
    alertMarker:EnableMouse(true)
  end
end

-- Size and outline of the alert text (Alerts page). Our own font string only.
local OUTLINE_FLAGS = { none = "", thin = "OUTLINE", thick = "THICKOUTLINE" }
function Gameplay.ApplyAlertStyle()
  if not alertText then return end
  local d = alertDb()
  local path, size = "Fonts\\FRIZQT__.TTF", 16
  local base = _G.GameFontNormalLarge
  if base and base.GetFont then
    local p, sz = base:GetFont()
    if type(p) == "string" then path = p end
    if type(sz) == "number" and sz > 0 then size = sz end
  end
  alertText:SetFont(path, math.floor(size * d.textScale + 0.5), OUTLINE_FLAGS[d.outline] or "")
end

local function ensureAlert()
  if alertMarker then return end
  alertMarker = R2F.Reminders.NewIcon("R2FReactAlertAnchor", alertDb, "GP_REACT_DRAGTIP")
  alertMarker:Place()
  local holder = CreateFrame("Frame", nil, UIParent)
  alertText = holder:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
  alertText:SetPoint("CENTER", alertMarker, "CENTER", 0, 0)
  alertText:Hide()
  Gameplay.ApplyAlertStyle()
end

local function now()
  return GetTime and GetTime() or 0
end

local function isSecret(v)
  return type(_G.issecretvalue) == "function" and _G.issecretvalue(v) == true
end

-- A short log of what the game announced (the last few entries), for /r2f reactlog.
local reactLog = {}
local function logReact(line)
  reactLog[#reactLog + 1] = ("%.1f %s"):format(now(), line)
  if #reactLog > 8 then table.remove(reactLog, 1) end
end
function Gameplay.PrintReactLog()
  if #reactLog == 0 then R2F.Print(L.GP_REACTLOG_NONE) return end
  for _, line in ipairs(reactLog) do R2F.Print("  " .. line) end
end

-- The spell name of the latest "spell glows on your bar" announcement, and when it came.
-- The combat-text announcement itself hides the spell name from addons on this client, but the
-- glow event carries a spell id (documented without restriction), so the name is read from that.
local lastGlow            -- { name =, t = }
local alertShownAt = -100
local alertIsGeneric = false

local function spellNameOf(spellID)
  local get = C_Spell and C_Spell.GetSpellName or _G.GetSpellInfo
  if not (get and spellID) or isSecret(spellID) then return nil end
  local ok, name = pcall(get, spellID)
  if ok and type(name) == "string" and not isSecret(name) then return name end
end

-- Revenge-type abilities have no bar glow on this client (/r2f debug reactlog shows only
-- SPELL_ACTIVE with a hidden name, no GLOW_SHOW). So the name is found the other way round: the
-- reactive spell that has just become usable. A spell is "reactive" if it only works after an event.
local REACTIVE = { "Revenge", "Overpower", "Riposte", "Counterattack", "Mongoose Bite", "Victory Rush" }
local wasUsable = {}

-- Returns the name of a reactive spell that is usable now but was not at the last scan (or nil).
local function scanUsable()
  local usable = C_Spell and C_Spell.IsSpellUsable
  if not usable then return nil end
  local newly
  for _, name in ipairs(REACTIVE) do
    local ok, u = pcall(usable, name)
    u = ok and u == true
    if u and not wasUsable[name] and not newly then newly = name end
    wasUsable[name] = u
  end
  return newly
end

-- Remember a name for the alert (and put it into an alert that is already up with the generic text).
local function noteName(name)
  lastGlow = { name = name, t = now() }
  if alertText and alertIsGeneric and now() - alertShownAt <= 1 and alertText:IsShown() then
    alertText:SetText("<" .. name .. ">")
    alertIsGeneric = false
  end
end

-- Show the alert for a spell name (may be secret / nil); a glow announced in the last second
-- supplies the name when the announcement doesn't.
local function showAlert(name)
  ensureAlert()
  local text
  if name ~= nil and not isSecret(name) then
    text = "<" .. tostring(name) .. ">"
    alertIsGeneric = false
  elseif lastGlow and now() - lastGlow.t <= 1 then
    text = "<" .. lastGlow.name .. ">"
    alertIsGeneric = false
  else
    text = L.GP_REACT_READY
    alertIsGeneric = true
  end
  alertShownAt = now()
  alertText:SetText(text)
  alertText:SetTextColor(1, 0.82, 0)
  alertText:Show()
  alertToken = alertToken + 1
  local mine = alertToken
  if C_Timer and C_Timer.After then
    C_Timer.After(ALERT_SECONDS, function() if mine == alertToken then alertText:Hide() end end)
  end
end
Gameplay.ShowReactiveAlert = showAlert

Gameplay.Register({
  key = "reactalert", group = "screen", title = "GP_REACT", tip = "GP_REACT_TIP",
  events = {
    COMBAT_TEXT_UPDATE = function(kind, name)
      if kind == "SPELL_ACTIVE" then
        logReact("SPELL_ACTIVE (name " .. ((name == nil or isSecret(name)) and "hidden" or tostring(name)) .. ")")
        showAlert(name)
      end
    end,
    SPELL_ACTIVATION_OVERLAY_GLOW_SHOW = function(spellID)
      local name = spellNameOf(spellID)
      logReact("GLOW_SHOW " .. (isSecret(spellID) and "hidden" or tostring(spellID)) .. " " .. tostring(name))
      if not name then return end
      noteName(name)
    end,
    SPELL_UPDATE_USABLE = function()
      local name = scanUsable()
      if name then
        logReact("USABLE " .. name)
        noteName(name)
      end
    end,
  },
  onToggle = function(on)
    if on then ensureAlert() end
    updateAlertMarker()
  end,
})

Gameplay.Register({
  key = "reactlock", group = "screen", title = "GP_REACTLOCK", tip = "GP_REACTLOCK_TIP",
  onToggle = function(on)
    alertDb().lock = on and true or false
    updateAlertMarker()
  end,
})

Gameplay.Register({
  key = "reactblizz", group = "screen", title = "GP_REACTBLIZZ", tip = "GP_REACTBLIZZ_TIP", noCombat = true,
  available = function() return R2F.QuickSettings.Read(REACT_CVAR) ~= nil end,
  onToggle = function(on)
    local db = R2F.Library.db
    local current = tostring(R2F.QuickSettings.Read(REACT_CVAR) or "")
    if on then
      -- Every login re-applies the saved choice: when the game's setting is already off there is nothing to
      -- change and nothing to say (it used to print the /reload line at each login).
      if current == "0" then return end
      if db.reactWas == nil then db.reactWas = current ~= "" and current or "1" end
      R2F.QuickSettings.Write(REACT_CVAR, "0")
    else
      local want = db.reactWas or "1"
      db.reactWas = nil
      if current == want then return end
      R2F.QuickSettings.Write(REACT_CVAR, want)
    end
    -- The game's combat text reads this setting when it loads (and when its own options change it);
    -- a setting changed from outside is picked up after the next /reload. Making the game re-read it
    -- now would mean calling its code from ours (tainting it again), so we say so instead.
    if R2F.Library.db.gameplay.reactblizzAsked ~= false then R2F.Print(L.GP_REACTBLIZZ_RELOAD) end
  end,
})
