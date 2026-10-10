-- GameplayExtras.lua: Gameplay features, build order step 2 (ADDON_PLAN.md 17, v0.22.0):
-- mail to your own characters, free bag slots on the backpack, fast loot.
-- Same rules as Gameplay.lua: one switch each, all OFF until ticked, handlers in pcall,
-- written from scratch (ForeverPlus only taught us what these features are).

local _, R2F = ...
local L = R2F.L
local Gameplay = R2F.Gameplay

-- ---------------------------------------------------------------------------
-- Your own characters (for mail), remembered whenever one logs in
-- ---------------------------------------------------------------------------

-- R2FDB.chars[realm][name] = { class = "WARRIOR", level = 18, faction = "Alliance" }.
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
  db.chars[realm][name] = {
    class = class,
    level = UnitLevel and UnitLevel("player") or 0,
    faction = UnitFactionGroup and (UnitFactionGroup("player")) or "",
    seen = time and time() or 0,
  }
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
-- FULL name (owner test of 0.22.0: a bare name didn't arrive).
function Gameplay.OtherCharacters()
  local out = {}
  local db = R2F.Library.db
  local realm = GetRealmName and GetRealmName()
  local me = UnitName and UnitName("player")
  local faction = UnitFactionGroup and (UnitFactionGroup("player")) or ""
  for name, c in pairs((db.chars and realm and db.chars[realm]) or {}) do
    if name ~= me and (c.faction == faction or faction == "" or c.faction == "") then
      out[#out + 1] = { name = name, full = name .. "-" .. realmSuffix(), class = c.class, level = c.level or 0 }
    end
  end
  table.sort(out, function(a, b) return a.name < b.name end)
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

local function openAltMenu(owner)
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
  available = function() return backpackButton() ~= nil and C_Container ~= nil and C_Container.GetContainerNumFreeSlots ~= nil end,
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
-- Floating combat text: a place you can move it to (the "<Revenge>" alert)
-- ---------------------------------------------------------------------------

-- The game's floating combat text (damage numbers, and alerts like "<Revenge>" when an ability
-- becomes usable, setting "Reactive ability alerts") scrolls along a path in
-- `CombatText.textLocations`: startX / startY to endX / endY, in WorldFrame units from the
-- bottom centre of the screen (read in Blizzard_CombatText, 1.60.1.70291). The game rebuilds that
-- table every time it relayouts. With "Move floating combat text" on, a framed marker (the
-- Revenge icon) shows on screen; drag it where the text should start. The whole scroll path is
-- shifted by the marker's offset from the screen centre (a hook re-applies it after each
-- relayout, and switching it off takes the shift back out). "Lock" hides the marker and keeps the
-- position. Needs floating combat text switched on in the game's options (the frame is loaded then).
local fctHooked = false
local fctMarker

local function fctDb()
  return R2F.Library.db.fct
end

local function worldScale()
  local w = _G.WorldFrame
  local ws = w and w.GetEffectiveScale and w:GetEffectiveScale() or 1
  return (UIParent:GetEffectiveScale() or 1) / (ws ~= 0 and ws or 1)
end

local function applyFct()
  local ct = _G.CombatText
  local t = ct and ct.textLocations
  if not t then return end
  local ox, oy = 0, 0
  if Gameplay.IsOn("fctmove") then
    local d, f = fctDb(), worldScale()
    ox, oy = d.x * f, d.y * f
  end
  local oldx, oldy = t.r2fOx or 0, t.r2fOy or 0
  if ox ~= oldx or oy ~= oldy then
    t.startX = t.startX + (ox - oldx)
    t.endX = t.endX + (ox - oldx)
    t.startY = t.startY + (oy - oldy)
    t.endY = t.endY + (oy - oldy)
    t.r2fOx, t.r2fOy = ox, oy
  end
end

local function updateMarker()
  if not fctMarker then return end
  local show = Gameplay.IsOn("fctmove") and not Gameplay.IsOn("fctlock")
  fctMarker:SetShown(show)
  if show then
    fctMarker.border:SetColorTexture(0.95, 0.75, 0.1, 1)
    fctMarker.icon:SetTexture("Interface\Icons\Ability_Warrior_Revenge")
    fctMarker.count:SetText(L.GP_FCT_MARKER)
    fctMarker:EnableMouse(true)
  end
end

Gameplay.Register({
  key = "fctmove", group = "screen", title = "GP_FCTMOVE", tip = "GP_FCTMOVE_TIP",
  available = function() return _G.CombatText ~= nil and _G.CombatText.textLocations ~= nil end,
  onToggle = function()
    local ct = _G.CombatText
    if ct and not fctHooked and ct.UpdateDisplayedMessages and hooksecurefunc then
      fctHooked = true
      hooksecurefunc(ct, "UpdateDisplayedMessages", applyFct)
    end
    if ct and not fctMarker then
      fctMarker = R2F.Reminders.NewIcon("R2FCombatTextAnchor", fctDb, "GP_FCT_DRAGTIP")
      fctMarker.onMoved = applyFct
      fctMarker:Place()
    end
    applyFct()
    updateMarker()
  end,
})

-- Lock: hide the marker, keep the position.
Gameplay.Register({
  key = "fctlock", group = "screen", title = "GP_FCTLOCK", tip = "GP_FCTLOCK_TIP",
  onToggle = function(on)
    fctDb().lock = on and true or false
    updateMarker()
  end,
})
