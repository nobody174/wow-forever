-- UI/Gameplay.lua: the Gameplay tab (ADDON_PLAN.md 17 / 18).
--
-- v0.28.0 redesign (UX pass, ADDON_PLAN 18): one long scrolling list of 17 boxes was too much to
-- read. The tab now has four small pages, picked with buttons along the top, grouped by what the
-- player is doing:
--   Quests            auto-accept, auto turn-in, skip the NPC chat, reward prices, track-all box
--   Vendors & loot    auto-repair, auto-sell grey items, fast looting, free bag slots, mail list
--   Screen & chat     hide red errors, XP numbers, copy-chat button, decline duels
--   Alerts            the "ability ready" alert (three boxes) and your class's on-screen icons
--                     (Warrior stance, Hunter ammo, tracking: UI/Reminders.lua draws these)
-- Every feature has one check box with a plain name and one grey line under it saying what it
-- does (the tooltip has the full text). All ship OFF. A feature the client can't do is greyed
-- out with the reason in its tooltip. The page you last used is remembered. These controls only
-- write SavedVariables or ask the client for a setting, so they stay usable in combat.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI
local Gameplay = R2F.Gameplay

local Tab = {}
R2F.GameplayTab = Tab

local page
local boxes = {}        -- feature key -> check button
local pages = {}        -- page key -> container frame
local pageButtons = {}  -- page key -> button
local pageHeight = {}
local scroll, content
local LEFT, RIGHT, RIGHT_W = 22, 270, 214

-- page key -> label key and the features on it (in this order)
Tab.PAGES = {
  { key = "quests", label = "GP_PAGE_QUESTS", features = { "questaccept", "questturnin", "gossipshop", "rewardvalue", "questzone" } },
  { key = "vendors", label = "GP_PAGE_VENDORS", features = { "repair", "sellgray", "fastloot", "bagslots", "mailalts" } },
  { key = "screen", label = "GP_PAGE_SCREEN", features = { "errorfilter", "xpbar", "copychat", "duels" } },
  { key = "alerts", label = "GP_PAGE_ALERTS", features = { "reactalert", "reactlock", "reactblizz" } },
}

local function visible()
  return page ~= nil and page:IsVisible()
end

local function refresh()
  if not visible() then return end
  for _, def in ipairs(Gameplay.FEATURES) do
    local b = boxes[def.key]
    if b then
      local ok = Gameplay.Available(def)
      b:SetChecked(Gameplay.IsOn(def.key))
      b:SetEnabled(ok)
      if ok then b.r2fLabel:SetTextColor(1, 1, 1) else b.r2fLabel:SetTextColor(0.5, 0.5, 0.5) end
    end
  end
  R2F.RemindersTab.Refresh()
end

local function byKey()
  local map = {}
  for _, def in ipairs(Gameplay.FEATURES) do map[def.key] = def end
  return map
end

-- One feature: check box + a grey one-line hint under it. Returns the y for the next row.
local function addRow(parent, def, x, y)
  local b = UI.CheckButton(parent, L[def.title])
  b:SetPoint("TOPLEFT", x, y)
  if b.SetMotionScriptsWhileDisabled then b:SetMotionScriptsWhileDisabled(true) end
  b:SetScript("OnClick", function()
    Gameplay.SetOn(def.key, not Gameplay.IsOn(def.key))
    refresh()
  end)
  b:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:AddLine(L[def.title], 1, 1, 1)
    GameTooltip:AddLine(L[def.tip], 1, 0.82, 0, true)
    if not Gameplay.Available(def) then GameTooltip:AddLine(L.GP_UNAVAILABLE, 1, 0.1, 0.1, true) end
    GameTooltip:Show()
  end)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
  boxes[def.key] = b
  local hint = L[def.title .. "_HINT"]
  if hint then
    local fs = parent:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
    fs:SetPoint("TOPLEFT", x + 28, y - 22)
    fs:SetWidth(200)
    fs:SetJustifyH("LEFT")
    fs:SetText(hint)
  end
  return y - (hint and 52 or 28)
end

-- Mouse-wheel scrolling (only needed when a page is taller than the window, e.g. Alerts for a Hunter).
local function onWheel(self, delta)
  local maxScroll = math.max((self.r2fContentHeight or 0) - self:GetHeight(), 0)
  local v = (self:GetVerticalScroll() or 0) - delta * 40
  self:SetVerticalScroll(math.max(0, math.min(v, maxScroll)))
end

function Tab.ShowPage(key)
  if not pages[key] then key = Tab.PAGES[1].key end
  for k, p in pairs(pages) do p:SetShown(k == key) end
  for k, b in pairs(pageButtons) do b:SetEnabled(k ~= key) end
  content:SetHeight(pageHeight[key] or 100)
  scroll.r2fContentHeight = pageHeight[key] or 100
  scroll:SetVerticalScroll(0)
  R2F.Library.db.settings.gameplayPage = key
  refresh()
end

function Tab.CurrentPage()
  return R2F.Library.db.settings.gameplayPage
end

-- Called once by MainWindow with the Gameplay page frame.
function Tab.Build(f)
  page = f
  local defs = byKey()

  -- The page buttons along the top.
  local x = 22
  for _, pg in ipairs(Tab.PAGES) do
    local b = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
    b:SetSize(112, 22)
    b:SetPoint("TOPLEFT", x, -46)
    b:SetText(L[pg.label])
    b:SetScript("OnClick", function() Tab.ShowPage(pg.key) end)
    pageButtons[pg.key] = b
    x = x + 116
  end

  scroll = UI.TryTemplate("ScrollFrame", "R2FGameplayScroll", f, "UIPanelScrollFrameTemplate",
    function(s) return s.SetScrollChild ~= nil end) or CreateFrame("ScrollFrame", "R2FGameplayScrollPlain", f)
  scroll:SetPoint("TOPLEFT", 6, -76)
  scroll:SetSize(500, 390)
  content = CreateFrame("Frame", nil, scroll)
  content:SetSize(490, 100)
  scroll:SetScrollChild(content)
  scroll:EnableMouseWheel(true)
  scroll:SetScript("OnMouseWheel", onWheel)

  for _, pg in ipairs(Tab.PAGES) do
    local c = CreateFrame("Frame", nil, content)
    c:SetPoint("TOPLEFT", 0, 0)
    c:SetSize(490, 400)
    pages[pg.key] = c
    local y = -10
    for _, key in ipairs(pg.features) do
      if defs[key] then y = addRow(c, defs[key], LEFT, y) end
    end
    local bottom = y
    if pg.key == "alerts" then
      local note = c:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
      note:SetPoint("TOPLEFT", LEFT + 4, y - 4)
      note:SetWidth(230)
      note:SetJustifyH("LEFT")
      note:SetText(L.GP_ALERTS_NOTE)
      bottom = y - 70
      local head = c:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
      head:SetPoint("TOPLEFT", RIGHT, -10)
      head:SetText(L.GP_ICONS)
      local rightEnd = R2F.RemindersTab.BuildInto(c, RIGHT + 2, -42, RIGHT_W) or -100
      bottom = math.min(bottom, rightEnd)
    else
      local note = c:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
      note:SetPoint("TOPLEFT", LEFT + 4, y - 4)
      note:SetWidth(440)
      note:SetJustifyH("LEFT")
      note:SetText(L.GP_NOTE)
      bottom = y - 30
    end
    pageHeight[pg.key] = -bottom + 20
    c:Hide()
  end
  Tab.ShowPage(R2F.Library.db.settings.gameplayPage or Tab.PAGES[1].key)
  return f
end

Tab.Refresh = refresh

function Tab.Show()
  R2F.MainWindow.Show("gameplay")
end
