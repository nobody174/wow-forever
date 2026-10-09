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

-- Your other characters on this realm and faction, sorted by name:
-- { { name =, class =, level = }, ... }.
function Gameplay.OtherCharacters()
  local out = {}
  local db = R2F.Library.db
  local realm = GetRealmName and GetRealmName()
  local me = UnitName and UnitName("player")
  local faction = UnitFactionGroup and (UnitFactionGroup("player")) or ""
  for name, c in pairs((db.chars and realm and db.chars[realm]) or {}) do
    if name ~= me and (c.faction == faction or faction == "" or c.faction == "") then
      out[#out + 1] = { name = name, class = c.class, level = c.level or 0 }
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
          box:SetText(a.name)
          if box.SetCursorPosition then box:SetCursorPosition(#a.name) end
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
      slotText:SetPoint("BOTTOM", btn, "BOTTOM", 0, 2)
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
