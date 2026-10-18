-- UI/MainWindow.lua: the one Road to Forever window.
--
-- Flat 820 x 600 window (UI.FlatWindow): a top bar (logo + name, Size and
-- Opacity sliders, Reload UI, close), a sidebar on the left (Home; Journey:
-- Plan / Talents / BiZ; Tools: Macros / Gameplay) and the
-- page on the right. Each tab is a page frame; the window shows one at a time:
--   Home    -> UI/Home.lua builds into it
--   Macros  -> UI/MacroBook.lua builds into it
--   Talents -> UI/TalentPanel.lua builds into it (link, preview, Copy my build,
--              Learn talents)
--   Plan    -> UI/Plan.lua builds into it (the launch-day checklist per group
--              plan, tick boxes, waypoint arrow)
--   BiS     -> UI/BiZ.lua builds into it (Mr.BiZ: best in slot per class / spec
--              from the site's BiS data, item tooltips, the wishlist)
--   Gameplay-> UI/Gameplay.lua builds into it (features that act for you or
--              change the screen, plus the reminder icons' options)
--   (Settings is part of Home since 0.32: UI/Settings.lua builds the game, minimap and bag
--    switches into the Home page; /r2f settings opens Home.)
-- The pages are still the 540 x 500 layouts of the old book, centred in the
-- content area until they are reflowed one by one.
--
-- Saved in R2FDB.settings: windowPos (by UI.FlatWindow when dragged), lastTab,
-- menuScale (0.5 to 1.5) and menuAlpha (0.3 to 1). Esc closes it
-- (UISpecialFrames). Spellbook sounds.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI

local MainWindow = {}
R2F.MainWindow = MainWindow

MainWindow.TABS = { "home", "macros", "talents", "plan", "bis", "gameplay" }
local TAB_INDEX = { home = 1, macros = 2, talents = 3, plan = 4, bis = 5, gameplay = 6 }  -- membership check
-- Tabs that were folded into another one (the Settings tab became part of Home).
local ALIAS = { settings = "home" }
local TITLES = { home = "TITLE_HOME", macros = "TITLE_MACROS", talents = "TITLE_TALENTS", plan = "TITLE_PLAN",
                 bis = "TITLE_BIS", gameplay = "TITLE_GAMEPLAY" }
local LABELS = { home = "TAB_HOME", macros = "TAB_MACROS", talents = "TAB_TALENTS", plan = "TAB_PLAN",
                 bis = "TAB_BIS", gameplay = "TAB_GAMEPLAY" }
local LOGO = "Interface\\AddOns\\RoadToForever\\media\\logo128"

local frame
local navY, navHeads, pageCustom = {}, {}, {}      -- the list layout of the sidebar, to come back to from the tile grid
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
  end
end

local function pageHidden(key)
  if key == "macros" then R2F.MacroBook.OnHide() end
  if key == "talents" then R2F.TalentPanel.OnHide() end
end

-- ---------------------------------------------------------------------------
-- Layout
-- ---------------------------------------------------------------------------

local WIN_W, WIN_H = 820, 664   -- 36 taller than before: the Talents board's prerequisite arrows need room
local TOP_H, SIDE_W = 50, 150
-- The pages were laid out for the old 540 x 500 book and keep that size until
-- they are reflowed; they sit centred in the content area, shifted up because
-- their first ~44 px were the old title bar.
local PAGE_W, PAGE_H = 540, 500
local PAGE_X = SIDE_W + math.floor((WIN_W - SIDE_W - PAGE_W) / 2)
local PAGE_Y = -(TOP_H - 44)

-- Sidebar order: a group heading (or none) and the tabs under it.
MainWindow.NAV = {
  { tabs = { "home" } },
  { heading = "NAV_JOURNEY", tabs = { "plan" } },
  { heading = "NAV_CHARACTER", tabs = { "talents", "bis" } },
  { heading = "NAV_UI", tabs = { "macros", "gameplay" } },
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
  local fs = b:CreateFontString(nil, "ARTWORK", "R2FBody")
  fs:SetPoint("LEFT", b, "LEFT", 14, 0)
  fs:SetText(L[LABELS[key]])
  b.r2fKey, b.r2fSel, b.r2fBar, b.r2fText = key, sel, bar, fs
  b:SetScript("OnClick", function() MainWindow.SelectTab(key) end)
  return b
end

local selectedKey

local function showSelected(key)
  selectedKey = key
  R2F.Deco.Select(key)
  local th = R2F.Theme.Get()
  local ac, tx = th.accent, th.text
  for k, b in pairs(tabButtons) do
    local on = k == key
    b.r2fSel:SetColorTexture(ac[1], ac[2], ac[3], th.selAlpha)
    b.r2fBar:SetColorTexture(ac[1], ac[2], ac[3], 1)
    if on then b.r2fSel:Show() b.r2fBar:Show() else b.r2fSel:Hide() b.r2fBar:Hide() end
    if on then b.r2fText:SetTextColor(ac[1], ac[2], ac[3]) else b.r2fText:SetTextColor(tx[1], tx[2], tx[3]) end
  end
end

-- Apply the saved size and opacity. The backdrop frame carries the opacity
-- (text and controls stay fully readable).
function MainWindow.ApplyLook()
  if not frame then return end
  local st = settings()
  frame:SetScale(st.menuScale)
  frame:SetBackdropColor(0, 0, 0, 0)
  local th = R2F.Theme.Get(st.theme)
  local bg, sd, ru = th.bg, th.side, th.rule
  frame.r2fBgTex:SetColorTexture(bg[1], bg[2], bg[3], R2F.Theme.PanelAlpha(th, st.menuAlpha))
  frame.r2fSide:SetColorTexture(sd[1], sd[2], sd[3], th.sideAlpha * st.menuAlpha)
  frame.r2fRule:SetColorTexture(ru[1], ru[2], ru[3], th.ruleAlpha)
  -- Classic keeps Blizzard's dialog border exactly as it was. Other themes hide it (the dialog art is a fixed bronze
  -- texture that a tint only muddies) and show a thin line in the theme's rim colour instead.
  local classic = th.key == "classic"
  if frame.SetBackdropBorderColor then frame:SetBackdropBorderColor(1, 1, 1, classic and 1 or 0) end
  for _, line in ipairs(frame.r2fRimLines or {}) do
    line:SetColorTexture(th.rim[1], th.rim[2], th.rim[3], 1)
    line:SetShown(not classic)
  end
  if frame.r2fTitle then
    local tc = th.titleColor or th.accent
    frame.r2fTitle:SetTextColor(tc[1], tc[2], tc[3])
  end
  if selectedKey then showSelected(selectedKey) end
  R2F.Deco.Apply(frame, th, R2F.Theme.PanelAlpha(th, st.menuAlpha))
end

-- The sidebar as a list of wide buttons (the usual look), as a 2 x 3 grid of 64 px tiles (Ember & Iron, "grid") or as a row
-- of tabs under the top bar (Obsidian Night, "top"): the same buttons, moved. In the tab layout the window is 44 px taller
-- and the pages move up and sideways into the space the sidebar left.
local GRID_ORDER = { "home", "plan", "talents", "bis", "macros", "gameplay" }
local TOP_W = { home = 84, plan = 112, talents = 96, bis = 84, macros = 92, gameplay = 92 }
local TOP_SEPARATORS_AFTER = { plan = true, bis = true }
local navSeps = {}
local STRIP = 44

local function placePages(top)
  for key, p in pairs(pages) do
    local custom = pageCustom[key]
    p:ClearAllPoints()
    if top then
      local w = custom and custom.w or PAGE_W
      p:SetPoint("TOPLEFT", frame, "TOPLEFT", math.floor((WIN_W - w) / 2), -(TOP_H + 4 + STRIP + 8))
    elseif custom then
      p:SetPoint("TOPLEFT", frame, "TOPLEFT", SIDE_W + 12, -(TOP_H + 4))
    else
      p:SetPoint("TOPLEFT", frame, "TOPLEFT", PAGE_X, PAGE_Y)
    end
  end
end

function MainWindow.NavSeparators() return navSeps end

function MainWindow.SetNavLayout(layout)
  if not frame then return end
  if layout == true then layout = "grid" end
  navSeps = {}
  local x = 14
  for idx, key in ipairs(GRID_ORDER) do
    local b = tabButtons[key]
    if b then
      b:ClearAllPoints()
      if layout == "grid" then
        b:SetSize(64, 64)
        b:SetPoint("TOPLEFT", frame, "TOPLEFT", 8 + ((idx - 1) % 2) * 70, -(TOP_H + 12) - math.floor((idx - 1) / 2) * 70)
      elseif layout == "top" then
        b:SetSize(TOP_W[key], 32)
        b:SetPoint("TOPLEFT", frame, "TOPLEFT", x, -(TOP_H + 6))
        x = x + TOP_W[key] + 4
        if TOP_SEPARATORS_AFTER[key] then
          navSeps[#navSeps + 1] = x - 2
          x = x + 12
        end
      else
        b:SetSize(SIDE_W - 16, 26)
        b:SetPoint("TOPLEFT", frame, "TOPLEFT", 8, navY[key] or -(TOP_H + 12))
      end
    end
  end
  for _, h in ipairs(navHeads) do h:SetShown(layout == nil) end
  if frame.r2fSide then frame.r2fSide:SetShown(layout ~= "top") end
  frame:SetHeight(WIN_H + (layout == "top" and STRIP or 0))
  placePages(layout == "top")
end

-- Any theme change (the Home page picker, a future slash command) recolours the window.
R2F.Theme.OnChange(function() MainWindow.ApplyLook() end)

-- Small labelled slider for the top bar. onApply(value) runs when the value
-- settles: while the mouse drags the thumb the window must not rescale under
-- it, so size changes apply on release.
local STEP = 10
local function topSlider(parent, label, min, max, get, set, x)
  local fs = parent:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
  fs:SetPoint("TOPLEFT", parent, "TOPLEFT", x, -5)
  local function snap(v)
    v = math.floor(v / STEP + 0.5) * STEP
    return math.max(min, math.min(max, v))
  end
  local function caption(pct) fs:SetText(("%s %d%%"):format(label, pct)) end
  caption(math.floor(get() * 100 + 0.5))
  local sl = CreateFrame("Slider", nil, parent, "OptionsSliderTemplate")
  sl:SetPoint("TOPLEFT", parent, "TOPLEFT", x, -17)
  local knob = sl.GetThumbTexture and sl:GetThumbTexture()
  if knob then R2F.Theme.PaintVertex(knob, "thumb") end
  sl:SetWidth(84)
  sl:SetMinMaxValues(min, max)
  sl:SetValueStep(STEP)
  if sl.SetObeyStepOnDrag then sl:SetObeyStepOnDrag(true) end
  for _, part in ipairs({ "Low", "High", "Text" }) do
    if sl[part] then sl[part]:SetText("") end
  end
  -- The slider sits inside the window it scales, so changing the scale while
  -- the thumb is held moves the bar under the cursor and the value runs away.
  -- While the mouse button is down only the caption follows; the value is
  -- applied once, when the button is released (checked in OnUpdate as well,
  -- because OnMouseUp does not arrive when the cursor leaves the bar).
  local function commit()
    sl.r2fDown = false
    local v = snap(sl:GetValue()) / 100
    caption(math.floor(v * 100 + 0.5))
    if math.abs(v - get()) > 0.001 then set(v) end
  end
  -- Only dragging the thumb changes the slider. A press anywhere else on the bar is undone: the
  -- engine moves the bar to the click before our OnMouseDown runs, so nothing is ever applied from
  -- OnValueChanged. The value is applied once, on release, and only when the press began on the thumb
  -- (judged from where the thumb was before the press, i.e. from the applied value).
  local TRACK_W = 84
  local function pressedOnThumb()
    local left, scale = sl:GetLeft(), sl:GetEffectiveScale()
    if type(left) == "number" and type(scale) == "number" and scale > 0 and GetCursorPosition then
      local cx = GetCursorPosition() / scale
      local frac = (math.max(min, math.min(max, get() * 100)) - min) / (max - min)
      return math.abs(cx - (left + 8 + (TRACK_W - 16) * frac)) <= 14
    end
    local thumb = sl.GetThumbTexture and sl:GetThumbTexture()
    if not (thumb and thumb.IsMouseOver) then return true end
    local ok, over = pcall(thumb.IsMouseOver, thumb)
    return (not ok) or over == true
  end
  local function revert()
    sl.r2fBlock, sl.r2fDown = false, false
    local v = math.max(min, math.min(max, get() * 100))
    sl:SetValue(v)
    caption(math.floor(v + 0.5))
  end
  sl:SetScript("OnValueChanged", function(self, v)
    if self.r2fBlock then
      local keep = math.max(min, math.min(max, get() * 100))
      if self:GetValue() ~= keep then self:SetValue(keep) end
      return
    end
    caption(snap(v))
  end)
  sl:SetScript("OnMouseDown", function(self)
    self.r2fBlock = not pressedOnThumb()
    self.r2fDown = true
    if self.r2fBlock then caption(math.floor(get() * 100 + 0.5)) end
  end)
  local function release(self)
    if not self.r2fDown then return end
    if self.r2fBlock then revert() else commit() end
  end
  sl:SetScript("OnMouseUp", release)
  sl:SetScript("OnUpdate", function(self)
    if self.r2fDown and not IsMouseButtonDown("LeftButton") then release(self) end
  end)
  sl:SetScript("OnHide", function(self) self.r2fDown, self.r2fBlock = false, false end)
  -- Tick marks under the bar, one per step, with the end and middle values
  -- written under them. The thumb's centre travels about 8 px in from each
  -- end of the bar.
  local n = (max - min) / STEP
  for i = 0, n do
    local t = parent:CreateTexture(nil, "ARTWORK")
    local major = (i == 0 or i == n or min + i * STEP == 100)
    t:SetSize(1, major and 6 or 4)
    local tx = 8 + (84 - 16) * i / n
    t:SetPoint("TOP", sl, "BOTTOMLEFT", tx, 2)
    R2F.Theme.PaintTex(t, "tick")
    if major then
      local m = parent:CreateFontString(nil, "ARTWORK", "R2FDimSmall")
      m:SetPoint("TOP", sl, "BOTTOMLEFT", tx, -4)
      m:SetText(tostring(min + i * STEP))
    end
  end
  sl.r2fLabel = fs
  return sl
end

-- ---------------------------------------------------------------------------
-- Building
-- ---------------------------------------------------------------------------

local function build()
  local f = UI.FlatWindow("R2FMain", WIN_W, WIN_H, "windowPos")

  -- Solid panel (opacity from the top bar slider); the dialog backdrop only
  -- draws the rim.
  local bgTex = f:CreateTexture(nil, "BACKGROUND")
  bgTex:SetPoint("TOPLEFT", f, "TOPLEFT", 4, -4)
  bgTex:SetPoint("BOTTOMRIGHT", f, "BOTTOMRIGHT", -4, 4)
  bgTex:SetColorTexture(0.07, 0.07, 0.09, 1)
  f.r2fBgTex = bgTex
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
  f.r2fRule = rule
  -- Thin frame line for the non-classic themes (hidden for classic): two pixels just outside the panel.
  f.r2fRimLines = {}
  for _, spec in ipairs({
    { "TOPLEFT", 2, -2, "TOPRIGHT", -2, -2, true }, { "BOTTOMLEFT", 2, 2, "BOTTOMRIGHT", -2, 2, true },
    { "TOPLEFT", 2, -2, "BOTTOMLEFT", 2, 2, false }, { "TOPRIGHT", -2, -2, "BOTTOMRIGHT", -2, 2, false },
  }) do
    local line = f:CreateTexture(nil, "ARTWORK")
    line:SetPoint(spec[1], f, spec[1], spec[2], spec[3])
    line:SetPoint(spec[4], f, spec[4], spec[5], spec[6])
    if spec[7] then line:SetHeight(2) else line:SetWidth(2) end
    line:Hide()
    f.r2fRimLines[#f.r2fRimLines + 1] = line
  end

  -- Top bar: logo, name (real text), size + opacity sliders, Reload UI, close.
  local logo = f:CreateTexture(nil, "ARTWORK")
  logo:SetSize(30, 30)
  logo:SetPoint("TOPLEFT", f, "TOPLEFT", 12, -7)
  logo:SetTexture(LOGO)
  f.r2fLogo = logo
  local title = f:CreateFontString(nil, "ARTWORK", "R2FHeadingLarge")
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
  UI.ThemeButton(reload)
  f.r2fReload = reload
  f.r2fSizeSlider = topSlider(f, L.WIN_SIZE, 50, 150,
    function() return settings().menuScale end,
    function(v) settings().menuScale = v MainWindow.ApplyLook() end, WIN_W - 36 - 84 - 8 - 2 * 92)
  f.r2fOpacitySlider = topSlider(f, L.WIN_OPACITY, 30, 100,
    function() return settings().menuAlpha end,
    function(v) settings().menuAlpha = v MainWindow.ApplyLook() end, WIN_W - 36 - 84 - 8 - 92)
  f.r2fSizeSlider:SetValue(settings().menuScale * 100)
  f.r2fOpacitySlider:SetValue(settings().menuAlpha * 100)

  -- Sidebar.
  local groupHeads = navHeads
  local y = -(TOP_H + 12)
  for _, group in ipairs(MainWindow.NAV) do
    if group.heading then
      y = y - 8
      local h = f:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
      groupHeads[#groupHeads + 1] = h
      h:SetPoint("TOPLEFT", f, "TOPLEFT", 16, y)
      h:SetText(L[group.heading]:upper())
      R2F.Theme.PaintText(h, "group")
      y = y - 18
    end
    for _, key in ipairs(group.tabs) do
      tabButtons[key] = buildNavButton(f, key, y)
      navY[key] = y
      y = y - 28
    end
  end

  R2F.Deco.Build(f, { sideW = SIDE_W, topH = TOP_H, nav = tabButtons, heads = groupHeads,
    label = function(key) return L[LABELS[key]] end })
  R2F.Deco.AddSlider(f, f.r2fSizeSlider)
  R2F.Deco.AddSlider(f, f.r2fOpacitySlider)

  for _, key in ipairs(MainWindow.TABS) do
    local p = CreateFrame("Frame", nil, f)
    local custom = (key == "bis" and R2F.BiZTab.PAGE) or (key == "home" and R2F.Home.PAGE)
      or (key == "talents" and R2F.TalentPanel.PAGE)
    pageCustom[key] = custom
    if custom then
      -- Mr.BiZ and Home use the whole content area.
      p:SetSize(custom.w, custom.h)
      p:SetPoint("TOPLEFT", f, "TOPLEFT", SIDE_W + 12, -(TOP_H + 4))
    else
      p:SetSize(PAGE_W, PAGE_H)
      p:SetPoint("TOPLEFT", f, "TOPLEFT", PAGE_X, PAGE_Y)
    end
    p:Hide()
    pages[key] = p
  end
  R2F.Home.Build(pages.home)
  R2F.MacroBook.Build(pages.macros)
  R2F.TalentPanel.Build(pages.talents)
  R2F.PlanTab.Build(pages.plan)
  R2F.BiZTab.Build(pages.bis)
  R2F.GameplayTab.Build(pages.gameplay)

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
  key = ALIAS[key] or key
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
  R2F.Deco.FitTitle(frame)
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
