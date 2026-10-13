-- UI/Gameplay.lua: the Gameplay tab.
--
-- The tab has four small pages (one long list of boxes was too much to read), picked
-- with buttons along the top, grouped by what the player is doing:
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
local outlineButtons = {}   -- "none" / "thin" / "thick" -> button (Alerts & HUD page)
local arrowButtons = {}     -- BiZNav arrow size: "small" / "medium" / "large" -> button (Alerts & HUD page)
local sizeSlider, sizeText
local searchBox, results, resultRows = nil, nil, {}
local bagBoxes = {}     -- Movable bags / Lock bags (Bags.lua), on the Bags page
local scroll, content
local LEFT, RIGHT, RIGHT_W = 22, 270, 214

-- page key -> label key and the features on it (in this order)
Tab.PAGES = {
  { key = "quests", label = "GP_PAGE_QUESTS",
    features = { "questaccept", "questturnin", "gossipshop", "rewardvalue", "questzone" } },
  { key = "vendors", label = "GP_PAGE_VENDORS",
    features = { "repair", "sellgray", "fastloot", "mailalts" } },
  { key = "screen", label = "GP_PAGE_SCREEN", features = { "errorfilter", "xpbar", "copychat", "duels" } },
  { key = "bags", label = "GP_PAGE_BAGS", features = { "bagslots", "bagsort", "upgrades" } },
  { key = "alerts", label = "GP_PAGE_ALERTS", features = { "reactalert", "reactlock", "reactblizz", "training", "navfollow" } },
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
  if sizeSlider then
    local d = R2F.Library.db.fct
    sizeSlider:SetValue(d.textScale * 100)
    sizeText:SetText(L.GP_ALERT_SIZE:format(d.textScale * 100 + 0.5))
    for k, b in pairs(outlineButtons) do
      local fs = b.GetFontString and b:GetFontString()
      if fs then
        if k == d.outline then fs:SetTextColor(1, 0.82, 0) else fs:SetTextColor(1, 1, 1) end
      end
    end
    local size = R2F.Nav.Size()
    for k, b in pairs(arrowButtons) do
      local fs = b.GetFontString and b:GetFontString()
      if fs then
        if k == size then fs:SetTextColor(1, 0.82, 0) else fs:SetTextColor(1, 1, 1) end
      end
    end
  end
  local bagsOk = R2F.Bags.Available() and not R2F.InCombat()
  for _, b in ipairs(bagBoxes) do
    b:SetEnabled(bagsOk)
    if bagsOk then b.r2fLabel:SetTextColor(1, 1, 1) else b.r2fLabel:SetTextColor(0.5, 0.5, 0.5) end
  end
  if bagBoxes[1] then
    bagBoxes[1]:SetChecked(R2F.Bags.IsMovable())
    bagBoxes[2]:SetChecked(R2F.Bags.IsLocked())
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

-- Movable bags / Lock bags: not features (no SavedVariables toggle of ours), so their own boxes.
local function addBagBox(parent, label, tip, y, onClick)
  local b = UI.CheckButton(parent, label)
  b:SetPoint("TOPLEFT", LEFT, y)
  if b.SetMotionScriptsWhileDisabled then b:SetMotionScriptsWhileDisabled(true) end
  b:SetScript("OnClick", function() onClick() refresh() end)
  b:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:AddLine(label, 1, 1, 1)
    GameTooltip:AddLine(tip, 1, 0.82, 0, true)
    if not R2F.Bags.Available() then
      GameTooltip:AddLine(L.BAGS_UNAVAILABLE, 1, 0.1, 0.1, true)
    elseif R2F.InCombat() then
      GameTooltip:AddLine(L.QS_TIP_COMBAT, 1, 0.1, 0.1, true)
    end
    GameTooltip:Show()
  end)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
  bagBoxes[#bagBoxes + 1] = b
  return y - 28
end

-- Mouse-wheel scrolling (only needed when a page is taller than the window, e.g. Alerts for a Hunter).
local function onWheel(self, delta)
  local maxScroll = math.max((self.r2fContentHeight or 0) - self:GetHeight(), 0)
  local v = (self:GetVerticalScroll() or 0) - delta * 40
  self:SetVerticalScroll(math.max(0, math.min(v, maxScroll)))
end

-- Search: matches the option names, their hints and tooltips, and the page names. Returns a list of
-- { label, page } (up to 10). Options that are not plain features are listed in EXTRA.
local EXTRA = {
  { "BAGS_MOVABLE", "bags" }, { "BAGS_LOCK", "bags" },
  { "GP_ALERT_OUTLINE", "alerts" }, { "GP_ICONS", "alerts" }, { "NAV_SIZE", "alerts" },
}

function Tab.Search(q)
  q = tostring(q or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
  local out = {}
  if q == "" then return out end
  local function hit(...)
    for i = 1, select("#", ...) do
      local t = select(i, ...)
      if t and tostring(t):lower():find(q, 1, true) then return true end
    end
  end
  for _, pg in ipairs(Tab.PAGES) do
    for _, key in ipairs(pg.features) do
      local def
      for _, d in ipairs(Gameplay.FEATURES) do if d.key == key then def = d end end
      if def and #out < 10 and hit(L[def.title], L[def.title .. "_HINT"], L[def.tip], L[pg.label]) then
        out[#out + 1] = { label = L[def.title], page = pg.key }
      end
    end
  end
  for _, e in ipairs(EXTRA) do
    if #out < 10 and hit(L[e[1]], L[e[1] .. "_TIP"]) then out[#out + 1] = { label = L[e[1]], page = e[2] } end
  end
  return out
end

local function showResults(list, q)
  for _, r in ipairs(resultRows) do r:Hide() end
  results:SetShown(q ~= "")
  results.none:SetShown(q ~= "" and #list == 0)
  for i, item in ipairs(list) do
    local r = resultRows[i]
    if not r then
      r = CreateFrame("Button", nil, results, "UIPanelButtonTemplate")
      r:SetSize(300, 24)
      r:SetPoint("TOPLEFT", 16, -10 - (i - 1) * 28)
      r:SetScript("OnClick", function(self)
        searchBox:SetText("")
        searchBox:ClearFocus()
        Tab.ShowPage(self.page)
      end)
      resultRows[i] = r
    end
    r.page = item.page
    r:SetText(item.label .. "  |cff999999(" .. L["GP_PAGE_" .. item.page:upper()] .. ")|r")
    r:Show()
  end
end

function Tab.ShowPage(key)
  if not pages[key] then key = Tab.PAGES[1].key end
  for k, p in pairs(pages) do p:SetShown(k == key) end
  -- The page you are on stands out (gold text, a gold bar under it, the button kept lit) and stays
  -- ENABLED: a greyed-out button reads as "not learned / not working".
  for k, b in pairs(pageButtons) do
    local on = (k == key)
    b.mark:SetShown(on)
    if b.LockHighlight then
      if on then b:LockHighlight() else b:UnlockHighlight() end
    end
    local fs = b.GetFontString and b:GetFontString()
    if fs then
      if on then fs:SetTextColor(1, 0.82, 0) else fs:SetTextColor(1, 1, 1) end
    end
  end
  content:SetHeight(pageHeight[key] or 100)
  scroll.r2fContentHeight = pageHeight[key] or 100
  scroll:SetVerticalScroll(0)
  R2F.Library.db.settings.gameplayPage = key
  refresh()
end

-- Turns every box on the page you are on off again (the defaults) and puts the alert text style back.
function Tab.ResetPage()
  local key = Tab.CurrentPage()
  for _, pg in ipairs(Tab.PAGES) do
    if pg.key == key then
      for _, f in ipairs(pg.features) do
        if Gameplay.IsOn(f) then Gameplay.SetOn(f, false) end
      end
      if key == "alerts" then
        local d = R2F.Library.db.fct
        d.textScale, d.outline = 1, "none"
        Gameplay.ApplyAlertStyle()
        R2F.Nav.SetSize("medium")
      end
    end
  end
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
  local x = 12
  for _, pg in ipairs(Tab.PAGES) do
    local b = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
    b:SetSize(100, 22)
    b:SetPoint("TOPLEFT", x, -46)
    b:SetText(L[pg.label])
    b:SetScript("OnClick", function() Tab.ShowPage(pg.key) end)
    b.mark = b:CreateTexture(nil, "OVERLAY")
    b.mark:SetColorTexture(1, 0.82, 0, 1)
    b.mark:SetPoint("BOTTOMLEFT", b, "BOTTOMLEFT", 6, 1)
    b.mark:SetPoint("BOTTOMRIGHT", b, "BOTTOMRIGHT", -6, 1)
    b.mark:SetHeight(3)
    b.mark:Hide()
    pageButtons[pg.key] = b
    x = x + 104
  end

  local reset = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  reset:SetSize(100, 22)
  reset:SetPoint("BOTTOMRIGHT", -20, 12)
  reset:SetText(L.GP_RESET_PAGE)
  reset:SetScript("OnClick", function() Tab.ResetPage() end)
  reset:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_TOP")
    GameTooltip:AddLine(L.GP_RESET_TIP, 1, 1, 1, true)
    GameTooltip:Show()
  end)
  reset:SetScript("OnLeave", function() GameTooltip:Hide() end)

  -- Search box (bottom left): lists the options that match; a click opens the page they are on.
  searchBox = CreateFrame("EditBox", "R2FGameplaySearch", f, "InputBoxTemplate")
  searchBox:SetSize(200, 22)
  searchBox:SetPoint("BOTTOMLEFT", 24, 12)
  searchBox:SetAutoFocus(false)
  searchBox:SetMaxLetters(40)
  local hint = f:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
  hint:SetPoint("LEFT", searchBox, "LEFT", 6, 0)
  hint:SetText(L.GP_SEARCH)
  searchBox:SetScript("OnTextChanged", function(self)
    local q = self:GetText() or ""
    hint:SetShown(q == "")
    showResults(Tab.Search(q), q)
  end)
  searchBox:SetScript("OnEscapePressed", function(self) self:SetText("") self:ClearFocus() end)
  searchBox:SetScript("OnEnterPressed", function(self) self:ClearFocus() end)

  scroll = UI.TryTemplate("ScrollFrame", "R2FGameplayScroll", f, "UIPanelScrollFrameTemplate",
    function(s) return s.SetScrollChild ~= nil end) or CreateFrame("ScrollFrame", "R2FGameplayScrollPlain", f)
  scroll:SetPoint("TOPLEFT", 6, -76)
  scroll:SetSize(500, 390)
  content = CreateFrame("Frame", nil, scroll)
  content:SetSize(490, 100)
  scroll:SetScrollChild(content)
  scroll:EnableMouseWheel(true)
  scroll:SetScript("OnMouseWheel", onWheel)

  results = CreateFrame("Frame", nil, f)
  results:SetPoint("TOPLEFT", 6, -76)
  results:SetSize(500, 390)
  results:SetFrameLevel(scroll:GetFrameLevel() + 5)
  results.bg = results:CreateTexture(nil, "BACKGROUND")
  results.bg:SetAllPoints()
  results.bg:SetColorTexture(0.04, 0.04, 0.05, 0.97)
  results:Hide()
  results.none = results:CreateFontString(nil, "ARTWORK", "GameFontDisable")
  results.none:SetPoint("TOPLEFT", 20, -14)
  results.none:SetText(L.GP_SEARCH_NONE)

  for _, pg in ipairs(Tab.PAGES) do
    local c = CreateFrame("Frame", nil, content)
    c:SetPoint("TOPLEFT", 0, 0)
    c:SetSize(490, 400)
    pages[pg.key] = c
    local y = -10
    for _, key in ipairs(pg.features) do
      if defs[key] then y = addRow(c, defs[key], LEFT, y) end
    end
    if pg.key == "bags" then
      y = addBagBox(c, L.BAGS_MOVABLE, L.BAGS_MOVABLE_TIP, y,
        function() R2F.Bags.SetMovable(not R2F.Bags.IsMovable()) end)
      y = addBagBox(c, L.BAGS_LOCK, L.BAGS_LOCK_TIP, y,
        function() R2F.Bags.SetLock(not R2F.Bags.IsLocked()) end)
    end
    local bottom = y  -- luacheck: ignore 311
    if pg.key == "alerts" then
      sizeText = c:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
      sizeText:SetPoint("TOPLEFT", LEFT + 4, y - 6)
      sizeSlider = CreateFrame("Slider", nil, c, "OptionsSliderTemplate")
      sizeSlider:SetPoint("TOPLEFT", LEFT + 4, y - 30)
      sizeSlider:SetWidth(200)
      sizeSlider:SetMinMaxValues(50, 250)
      sizeSlider:SetValueStep(10)
      if sizeSlider.SetObeyStepOnDrag then sizeSlider:SetObeyStepOnDrag(true) end
      for _, part in ipairs({ "Low", "High", "Text" }) do
        if sizeSlider[part] then sizeSlider[part]:SetText("") end
      end
      sizeSlider:SetScript("OnValueChanged", function(_, v)
        local d = R2F.Library.db.fct
        v = math.max(50, math.min(250, math.floor(v / 10 + 0.5) * 10))
        sizeText:SetText(L.GP_ALERT_SIZE:format(v))
        if math.abs(v / 100 - d.textScale) > 0.001 then
          d.textScale = v / 100
          Gameplay.ApplyAlertStyle()
          refresh()
        end
      end)
      local ol = c:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
      ol:SetPoint("TOPLEFT", LEFT + 4, y - 56)
      ol:SetText(L.GP_ALERT_OUTLINE)
      local bx = LEFT + 4
      for _, k in ipairs({ "none", "thin", "thick" }) do
        local ob = CreateFrame("Button", nil, c, "UIPanelButtonTemplate")
        ob:SetSize(64, 22)
        ob:SetPoint("TOPLEFT", bx, y - 74)
        ob:SetText(L["GP_OUTLINE_" .. k:upper()])
        ob:SetScript("OnClick", function()
          R2F.Library.db.fct.outline = k
          Gameplay.ApplyAlertStyle()
          refresh()
        end)
        outlineButtons[k] = ob
        bx = bx + 68
      end
      -- BiZNav arrow size.
      local al = c:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
      al:SetPoint("TOPLEFT", LEFT + 4, y - 104)
      al:SetText(L.NAV_SIZE)
      bx = LEFT + 4
      for _, k in ipairs(R2F.Nav.SIZE_ORDER) do
        local ab = CreateFrame("Button", nil, c, "UIPanelButtonTemplate")
        ab:SetSize(64, 22)
        ab:SetPoint("TOPLEFT", bx, y - 122)
        ab:SetText(L["NAV_SIZE_" .. k:upper()])
        ab.navSize = k
        ab:SetScript("OnClick", function()
          R2F.Nav.SetSize(k)
          refresh()
        end)
        arrowButtons[k] = ab
        bx = bx + 68
      end
      y = y - 156
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
      local leftBottom = bottom
      bottom = math.min(bottom, rightEnd)
      -- Folding a class group in or out changes the right column's height.
      R2F.RemindersTab.OnReflow = function()
        local h = math.max(-leftBottom, 42 + R2F.RemindersTab.TotalHeight()) + 20
        pageHeight.alerts = h
        if Tab.CurrentPage() == "alerts" then
          content:SetHeight(h)
          scroll.r2fContentHeight = h
        end
      end
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
