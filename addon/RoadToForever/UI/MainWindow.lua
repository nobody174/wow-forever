-- UI/MainWindow.lua: the one Road to Forever window.
--
-- Flat 820 x 600 window (UI.FlatWindow): a top bar (logo + name, Size and
-- Opacity sliders, Reload UI, close), a sidebar on the left (Home; Journey:
-- Plan / Talents / BiZ; Tools: Macros / Gameplay; Options: Settings) and the
-- page on the right. Each tab is a page frame; the window shows one at a time:
--   Home    -> UI/Home.lua builds into it
--   Macros  -> UI/MacroBook.lua builds into it
--   Talents -> UI/TalentPanel.lua builds into it (link, preview, Copy my build,
--              Learn talents)
--   Plan    -> UI/Plan.lua builds into it (the launch-day checklist per group
--              plan, tick boxes, TomTom waypoints)
--   BiS     -> UI/BiZ.lua builds into it (Mr.BiZ: best in slot per class / spec
--              from the site's BiS data, item tooltips, the wishlist)
--   Gameplay-> UI/Gameplay.lua builds into it (features that act for you or
--              change the screen, plus the reminder icons' options)
--   Settings-> UI/Settings.lua builds into it (slots, minimap, Quick settings,
--              bags)
-- The pages are still the 540 x 500 layouts of the old book, centred in the
-- content area until they are reflowed one by one.
--
-- Saved in R2FDB.settings: windowPos (by UI.FlatWindow when dragged), lastTab,
-- menuScale (0.7 to 1.3) and menuAlpha (0.3 to 1). Esc closes it
-- (UISpecialFrames). Spellbook sounds.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI

local MainWindow = {}
R2F.MainWindow = MainWindow

MainWindow.TABS = { "home", "macros", "talents", "plan", "bis", "gameplay", "settings" }
local TAB_INDEX = { home = 1, macros = 2, talents = 3, plan = 4, bis = 5, gameplay = 6, settings = 7 }  -- membership check
local TITLES = { home = "TITLE_HOME", macros = "TITLE_MACROS", talents = "TITLE_TALENTS", plan = "TITLE_PLAN",
                 bis = "TITLE_BIS", gameplay = "TITLE_GAMEPLAY", settings = "TITLE_SETTINGS" }
local LABELS = { home = "TAB_HOME", macros = "TAB_MACROS", talents = "TAB_TALENTS", plan = "TAB_PLAN",
                 bis = "TAB_BIS", gameplay = "TAB_GAMEPLAY", settings = "TAB_SETTINGS" }
local LOGO = "Interface\\AddOns\\RoadToForever\\media\\logo128"

local frame
local pages, tabButtons = {}, {}   -- tabButtons: key -> sidebar button
local current            -- key of the page showing (kept while the window is closed)

local function settings() return R2F.Library.db.settings end

-- Page hooks: what to call when a page becomes visible / goes away.
local function refreshPage(key)
  if key == "home" then
    R2F.Home.Refresh()
  elseif key == "macros" then
    R2F.MacroBook.Refresh()
  elseif key == "talents" then
    R2F.TalentPanel.Refresh()
  elseif key == "plan" then
    R2F.PlanTab.Refresh()
  elseif key == "bis" then
    R2F.BiZTab.Refresh()
  elseif key == "gameplay" then
    R2F.GameplayTab.Refresh()
  elseif key == "settings" then
    R2F.Settings.Refresh()
  end
end

local function pageHidden(key)
  if key == "macros" then R2F.MacroBook.OnHide() end
  if key == "talents" then R2F.TalentPanel.OnHide() end
end

-- ---------------------------------------------------------------------------
-- Layout
-- ---------------------------------------------------------------------------

local WIN_W, WIN_H = 820, 600
local TOP_H, SIDE_W = 44, 150
-- The pages were laid out for the old 540 x 500 book and keep that size until
-- they are reflowed; they sit centred in the content area, shifted up because
-- their first ~44 px were the old title bar.
local PAGE_W, PAGE_H = 540, 500
local PAGE_X = SIDE_W + math.floor((WIN_W - SIDE_W - PAGE_W) / 2)
local PAGE_Y = -(TOP_H - 44)

-- Sidebar order: a group heading (or none) and the tabs under it.
MainWindow.NAV = {
  { tabs = { "home" } },
  { heading = "NAV_JOURNEY", tabs = { "plan", "talents", "bis" } },
  { heading = "NAV_TOOLS", tabs = { "macros", "gameplay" } },
  { heading = "NAV_OPTIONS", tabs = { "settings" } },
}

local GOLD = { 1, 0.82, 0 }

local function buildNavButton(parent, key, y)
  local b = CreateFrame("Button", nil, parent)
  b:SetSize(SIDE_W - 16, 26)
  b:SetPoint("TOPLEFT", parent, "TOPLEFT", 8, y)
  b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  local sel = b:CreateTexture(nil, "BACKGROUND")
  sel:SetAllPoints(b)
  sel:SetColorTexture(GOLD[1], GOLD[2], GOLD[3], 0.16)
  sel:Hide()
  local bar = b:CreateTexture(nil, "ARTWORK")
  bar:SetSize(3, 26)
  bar:SetPoint("LEFT", b, "LEFT", 0, 0)
  bar:SetColorTexture(GOLD[1], GOLD[2], GOLD[3], 1)
  bar:Hide()
  local fs = b:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  fs:SetPoint("LEFT", b, "LEFT", 14, 0)
  fs:SetText(L[LABELS[key]])
  b.r2fKey, b.r2fSel, b.r2fBar, b.r2fText = key, sel, bar, fs
  b:SetScript("OnClick", function() MainWindow.SelectTab(key) end)
  return b
end

local function showSelected(key)
  for k, b in pairs(tabButtons) do
    local on = k == key
    if on then b.r2fSel:Show() b.r2fBar:Show() else b.r2fSel:Hide() b.r2fBar:Hide() end
    if on then b.r2fText:SetTextColor(GOLD[1], GOLD[2], GOLD[3]) else b.r2fText:SetTextColor(1, 1, 1) end
  end
end

-- Apply the saved size and opacity. The backdrop frame carries the opacity
-- (text and controls stay fully readable).
function MainWindow.ApplyLook()
  if not frame then return end
  local st = settings()
  frame:SetScale(st.menuScale)
  frame:SetBackdropColor(1, 1, 1, st.menuAlpha)
  frame.r2fSide:SetColorTexture(0, 0, 0, 0.35 * st.menuAlpha)
end

-- Small labelled slider for the top bar. onApply(value) runs when the value
-- settles: while the mouse drags the thumb the window must not rescale under
-- it, so size changes apply on release.
local function topSlider(parent, label, min, max, get, set, x)
  local fs = parent:CreateFontString(nil, "ARTWORK", "GameFontNormalSmall")
  fs:SetPoint("TOPLEFT", parent, "TOPLEFT", x, -8)
  fs:SetText(label)
  local sl = CreateFrame("Slider", nil, parent, "OptionsSliderTemplate")
  sl:SetPoint("TOPLEFT", parent, "TOPLEFT", x, -22)
  sl:SetWidth(84)
  sl:SetMinMaxValues(min, max)
  sl:SetValueStep(5)
  if sl.SetObeyStepOnDrag then sl:SetObeyStepOnDrag(true) end
  for _, part in ipairs({ "Low", "High", "Text" }) do
    if sl[part] then sl[part]:SetText("") end
  end
  local function commit(v)
    v = math.floor(v / 5 + 0.5) / 100 * 5
    v = math.max(min / 100, math.min(max / 100, v))
    if math.abs(v - get()) > 0.001 then set(v) end
  end
  sl:SetScript("OnValueChanged", function(self, v)
    if not self.r2fDown then commit(v) end
  end)
  sl:SetScript("OnMouseDown", function(self) self.r2fDown = true end)
  sl:SetScript("OnMouseUp", function(self)
    self.r2fDown = false
    commit(self:GetValue())
  end)
  sl.r2fLabel = fs
  return sl
end

-- ---------------------------------------------------------------------------
-- Building
-- ---------------------------------------------------------------------------

local function build()
  local f = UI.FlatWindow("R2FMain", WIN_W, WIN_H, "windowPos")

  -- Sidebar background and the line under the top bar.
  local side = f:CreateTexture(nil, "BACKGROUND")
  side:SetPoint("TOPLEFT", f, "TOPLEFT", 4, -TOP_H)
  side:SetPoint("BOTTOMLEFT", f, "BOTTOMLEFT", 4, 4)
  side:SetWidth(SIDE_W - 4)
  side:SetColorTexture(0, 0, 0, 0.35)
  f.r2fSide = side
  local rule = f:CreateTexture(nil, "ARTWORK")
  rule:SetPoint("TOPLEFT", f, "TOPLEFT", 4, -TOP_H)
  rule:SetPoint("TOPRIGHT", f, "TOPRIGHT", -4, -TOP_H)
  rule:SetHeight(1)
  rule:SetColorTexture(GOLD[1], GOLD[2], GOLD[3], 0.35)

  -- Top bar: logo, name (real text), size + opacity sliders, Reload UI, close.
  local logo = f:CreateTexture(nil, "ARTWORK")
  logo:SetSize(30, 30)
  logo:SetPoint("TOPLEFT", f, "TOPLEFT", 12, -7)
  logo:SetTexture(LOGO)
  f.r2fLogo = logo
  local title = f:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
  title:SetPoint("LEFT", logo, "RIGHT", 8, 0)
  f.r2fTitle = title

  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton")
  close:SetPoint("TOPRIGHT", f, "TOPRIGHT", -2, -2)
  f.CloseButton = close
  local reload = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  reload:SetSize(84, 22)
  reload:SetPoint("TOPRIGHT", f, "TOPRIGHT", -36, -11)
  reload:SetText(L.MENU_RELOAD)
  reload:SetScript("OnClick", function() ReloadUI() end)
  f.r2fReload = reload
  f.r2fSizeSlider = topSlider(f, L.WIN_SIZE, 70, 130,
    function() return settings().menuScale end,
    function(v) settings().menuScale = v MainWindow.ApplyLook() end, WIN_W - 36 - 84 - 8 - 2 * 92)
  f.r2fOpacitySlider = topSlider(f, L.WIN_OPACITY, 30, 100,
    function() return settings().menuAlpha end,
    function(v) settings().menuAlpha = v MainWindow.ApplyLook() end, WIN_W - 36 - 84 - 8 - 92)
  f.r2fSizeSlider:SetValue(settings().menuScale * 100)
  f.r2fOpacitySlider:SetValue(settings().menuAlpha * 100)

  -- Sidebar.
  local y = -(TOP_H + 12)
  for _, group in ipairs(MainWindow.NAV) do
    if group.heading then
      y = y - 8
      local h = f:CreateFontString(nil, "ARTWORK", "GameFontNormalSmall")
      h:SetPoint("TOPLEFT", f, "TOPLEFT", 16, y)
      h:SetText(L[group.heading]:upper())
      h:SetTextColor(0.6, 0.6, 0.65)
      y = y - 18
    end
    for _, key in ipairs(group.tabs) do
      tabButtons[key] = buildNavButton(f, key, y)
      y = y - 28
    end
  end

  for _, key in ipairs(MainWindow.TABS) do
    local p = CreateFrame("Frame", nil, f)
    p:SetSize(PAGE_W, PAGE_H)
    p:SetPoint("TOPLEFT", f, "TOPLEFT", PAGE_X, PAGE_Y)
    p:Hide()
    pages[key] = p
  end
  R2F.Home.Build(pages.home)
  R2F.MacroBook.Build(pages.macros)
  R2F.TalentPanel.Build(pages.talents)
  R2F.PlanTab.Build(pages.plan)
  R2F.BiZTab.Build(pages.bis)
  R2F.GameplayTab.Build(pages.gameplay)
  R2F.Settings.Build(pages.settings)

  f:SetScript("OnShow", function()
    UI.PlaySound("IG_SPELLBOOK_OPEN")
    if current then refreshPage(current) end
  end)
  f:SetScript("OnHide", function()
    UI.PlaySound("IG_SPELLBOOK_CLOSE")
    if current then pageHidden(current) end
  end)
  frame = f
  MainWindow.ApplyLook()
  return f
end

local function ensure()
  frame = frame or build()
  return frame
end

-- ---------------------------------------------------------------------------
-- Public
-- ---------------------------------------------------------------------------

-- Show one page. Works whether the window is open or not (an open window
-- refreshes the page right away; a closed one does it in OnShow).
function MainWindow.SelectTab(key)
  if not TAB_INDEX[key] then key = "home" end
  ensure()
  if current ~= key then
    if current then
      pages[current]:Hide()
      pageHidden(current)
      if frame:IsShown() then UI.PlaySound("IG_CHARACTER_INFO_TAB") end
    end
    current = key
  end
  pages[key]:Show()
  frame.r2fTitle:SetText(L[TITLES[key]])
  showSelected(key)
  settings().lastTab = key
  if frame:IsShown() then refreshPage(key) end
end

-- Open on `tab`, or on the tab used last.
function MainWindow.Show(tab)
  MainWindow.SelectTab(tab or current or settings().lastTab)
  if not frame:IsShown() then frame:Show() end
end

-- Toggle(): close if open, else open on the last tab (the "/r2f" behaviour).
-- Toggle(tab): close if open ON THAT TAB, else open on it, like Blizzard's
-- own Spellbook / Talents keys (one key opens and closes its tab).
function MainWindow.Toggle(tab)
  if frame and frame:IsShown() and (tab == nil or tab == current) then
    frame:Hide()
  else
    MainWindow.Show(tab)
  end
end

function MainWindow.Hide()
  if frame then frame:Hide() end
end

function MainWindow.IsShown()
  return frame ~= nil and frame:IsShown()
end

-- The tab showing (nil while the window is closed).
function MainWindow.CurrentTab()
  if MainWindow.IsShown() then return current end
end

function MainWindow.Frame() return frame end

-- The title text in the top bar (nil before the window is built).
function MainWindow.Title()
  return frame and frame.r2fTitle:GetText() or nil
end

-- UPDATE_MACROS / ACTIONBAR_SLOT_CHANGED / LEARNED_SPELL_IN_TAB /
-- CHARACTER_POINTS_CHANGED / PLAYER_LEVEL_UP: redraw the visible page (all
-- all are throttled and no-ops while hidden).
function MainWindow.RequestRefresh()
  R2F.MacroBook.RequestRefresh()
  R2F.Home.RequestRefresh()
  R2F.TalentPanel.RequestRefresh()
  R2F.Settings.RequestRefresh()
end

-- PLAYER_REGEN_DISABLED / ENABLED.
function MainWindow.SetCombat()
  R2F.MacroBook.SetCombat()
  R2F.Home.SetCombat()
  R2F.TalentPanel.SetCombat()
  R2F.Settings.SetCombat()
end
