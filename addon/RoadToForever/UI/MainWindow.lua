-- UI/MainWindow.lua: the one Road to Forever window (ADDON_PLAN.md 12.4).
--
-- PortraitFrameTemplate shell (UI.Window: same template checks and
-- fallbacks the Macro Book used since step 3), portrait = our logo, and
-- six bottom tabs in the character frame's style: Home / Macros / Talents / Plan / Gameplay / Settings.
-- Each tab is a page frame filling the window; the window shows one page at
-- a time:
--   Home    -> UI/Home.lua builds into it
--   Macros  -> UI/MacroBook.lua builds into it (the step-3 book, reparented)
--   Talents -> UI/TalentPanel.lua builds into it (step 9: link, preview,
--              Copy my build; step 10: Learn talents)
--   Plan    -> UI/Plan.lua builds into it (15.5, v0.18.0: the launch-day checklist
--              per group plan, tick boxes, TomTom waypoints)
--   Gameplay-> UI/Gameplay.lua builds into it (ADDON_PLAN 17, v0.21.0: features that
--              act for you or change the screen, plus the reminder icons' options:
--              Warrior stance, Hunter ammo; this was the Reminders tab until 0.20.1)
--   Settings-> UI/Settings.lua builds into it (15.2, v0.15.0: slots, minimap,
--              Quick settings, stance icon; was a floating panel)
--
-- Saved in R2FDB.settings: windowPos (by UI.Window when dragged) and
-- lastTab. The size is fixed (540 x 500, the book's size): the book's grid is
-- laid out for that size, so a resize handle would only show empty space.
-- Esc closes it (UISpecialFrames, via UI.Window). Spellbook sounds (12.4).

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI

local MainWindow = {}
R2F.MainWindow = MainWindow

MainWindow.TABS = { "home", "macros", "talents", "plan", "gameplay", "settings" }
local TAB_INDEX = { home = 1, macros = 2, talents = 3, plan = 4, gameplay = 5, settings = 6 }
local TITLES = { home = "TITLE_HOME", macros = "TITLE_MACROS", talents = "TITLE_TALENTS", plan = "TITLE_PLAN", gameplay = "TITLE_GAMEPLAY", settings = "TITLE_SETTINGS" }
local LABELS = { home = "TAB_HOME", macros = "TAB_MACROS", talents = "TAB_TALENTS", plan = "TAB_PLAN", gameplay = "TAB_GAMEPLAY", settings = "TAB_SETTINGS" }
local LOGO = "Interface\\AddOns\\RoadToForever\\media\\logo128"

local frame
local pages, tabButtons = {}, {}
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
-- Bottom tabs
-- ---------------------------------------------------------------------------

-- Blizzard's character-frame tab look (12.4): PanelTabButtonTemplate in
-- newer clients, CharacterFrameTabButtonTemplate in older Classic ones,
-- whichever the client has (checked like every template, 6.7). Without
-- either, plain UIPanelButtonTemplate buttons along the bottom edge.
-- Tabs get global names <window>Tab<n> because the Classic template's
-- textures are named $parentLeft etc. and PanelTemplates_* find tabs by
-- that name in older clients (all R2F-prefixed, 6.7's naming rule).
-- Offsets between tabs: the Classic template's art overlaps by design.
local TAB_TEMPLATES = {
  { name = "PanelTabButtonTemplate", gap = 3 },
  { name = "CharacterFrameTabButtonTemplate", gap = -15 },
}

local function buildTab(f, i, key)
  local name = f:GetName() .. "Tab" .. i
  local t, gap
  for _, tpl in ipairs(TAB_TEMPLATES) do
    t = UI.TryTemplate("Button", name, f, tpl.name, function(b) return b.SetText ~= nil end)
    if t then
      t.r2fTemplate, gap = tpl.name, tpl.gap
      break
    end
  end
  if not t then
    t = CreateFrame("Button", name, f, "UIPanelButtonTemplate")
    t:SetSize(110, 24)
    t.r2fTemplate, gap = "UIPanelButtonTemplate", 4
  end
  t:SetID(i)
  t:SetText(L[LABELS[key]])
  if t.r2fTemplate ~= "UIPanelButtonTemplate" and PanelTemplates_TabResize then
    PanelTemplates_TabResize(t, 0)
  end
  if i == 1 then
    t:SetPoint("TOPLEFT", f, "BOTTOMLEFT", 12, 2)
  else
    t:SetPoint("LEFT", tabButtons[i - 1], "RIGHT", gap, 0)
  end
  t.r2fKey = key
  t:SetScript("OnClick", function() MainWindow.SelectTab(key) end)
  return t
end

-- Selected look. PanelTemplates_SetTab is Blizzard's helper for exactly this
-- (it only touches the frame and tabs passed in, which are ours: no taint);
-- it needs frame.numTabs / frame.Tabs. Without it, or with the plain-button
-- fallback, the selected tab is simply disabled (greyed, not clickable).
local function showSelected(index)
  if PanelTemplates_SetTab and tabButtons[1].r2fTemplate ~= "UIPanelButtonTemplate" then
    PanelTemplates_SetTab(frame, index)
  else
    for i, t in ipairs(tabButtons) do t:SetEnabled(i ~= index) end
  end
end

-- ---------------------------------------------------------------------------
-- Building
-- ---------------------------------------------------------------------------

local function build()
  local f = UI.Window("R2FMain", 540, 500, "windowPos")
  if f.r2fPortrait then
    f.r2fPortrait:SetTexture(LOGO)
    f.r2fPortrait:SetTexCoord(0, 1, 0, 1)
  end

  for _, key in ipairs(MainWindow.TABS) do
    local p = CreateFrame("Frame", nil, f)
    p:SetAllPoints(f)
    p:Hide()
    pages[key] = p
  end
  R2F.Home.Build(pages.home)
  R2F.MacroBook.Build(pages.macros)
  R2F.TalentPanel.Build(pages.talents)
  R2F.PlanTab.Build(pages.plan)
  R2F.GameplayTab.Build(pages.gameplay)
  R2F.Settings.Build(pages.settings)

  for i, key in ipairs(MainWindow.TABS) do tabButtons[i] = buildTab(f, i, key) end
  f.Tabs = tabButtons
  f.numTabs = #tabButtons
  if PanelTemplates_SetNumTabs then PanelTemplates_SetNumTabs(f, #tabButtons) end

  f:SetScript("OnShow", function()
    UI.PlaySound("IG_SPELLBOOK_OPEN")
    if current then refreshPage(current) end
  end)
  f:SetScript("OnHide", function()
    UI.PlaySound("IG_SPELLBOOK_CLOSE")
    if current then pageHidden(current) end
  end)
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
  frame.r2fSetTitle(L[TITLES[key]])
  showSelected(TAB_INDEX[key])
  settings().lastTab = key
  if frame:IsShown() then refreshPage(key) end
end

-- Open on `tab`, or on the tab used last (12.3 / 12.4).
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
