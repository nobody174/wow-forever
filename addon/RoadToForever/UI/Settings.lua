-- UI/Settings.lua: the game and minimap options that live on the Home page.
--
-- (Until 0.32 this was the Settings tab. Macro slots + Remove all moved to the Macros page's
-- Options menu; what is left is built into the Home page frame.)
--   left   Quick settings -> switches that change game settings with SetCVar (QuickSettings.lua)
--          Minimap        -> Show / Lock the minimap button (R2FDB.minimap.hide / .lock,
--                            LibDBIcon's format), then R2F.Minimap.Apply(). The minimap
--                            button's own menu and /r2f minimap change the same values and
--                            call Settings.Refresh.
--   right  Bags           -> Movable bags / Lock bags (Bags.lua)
--
-- Only the Quick settings and bag switches are greyed out in combat (they change CVars / bag
-- frames). The minimap switches only write SavedVariables.
--
-- Quick settings read the LIVE CVar every time the page is drawn (opened, combat
-- change, CVAR_UPDATE), never GetChecked after the click, so a refused change
-- snaps the switch back.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI
local Library = R2F.Library

local Settings = {}
R2F.Settings = Settings

local page
local ui = {}

-- Positions inside the Home page (650 wide): left column, right column.
local LEFT = 0
local TOP = -150

local function visible()
  return page ~= nil and page:IsVisible()
end

local function refresh()
  if not visible() then return end
  local mm = Library.db.minimap
  ui.show:SetChecked(not mm.hide)
  ui.lock:SetChecked(mm.lock == true)
  local combat = R2F.InCombat()
  for _, b in ipairs(ui.quick) do
    local available = R2F.QuickSettings.Available(b.qsItem)
    b:SetChecked(available and R2F.QuickSettings.IsOn(b.qsItem))
    local enabled = available and not combat
    b:SetEnabled(enabled)
    if enabled then b.r2fLabel:SetTextColor(1, 1, 1) else b.r2fLabel:SetTextColor(0.5, 0.5, 0.5) end
  end
end

-- The minimap button re-reads R2FDB.minimap. Still guarded: the Settings
-- tests swap R2F.Minimap out, and a client without a Minimap frame has none.
local function applyMinimap()
  if R2F.Minimap and R2F.Minimap.Apply then R2F.Minimap.Apply() end
end

-- Quick settings tooltip: what it changes, and why it is greyed out.
local function showQuickTip(b)
  local item = b.qsItem
  GameTooltip:SetOwner(b, "ANCHOR_RIGHT")
  GameTooltip:AddLine(item.label, 1, 1, 1)
  GameTooltip:AddLine(item.tip, 1, 0.82, 0, true)
  if not R2F.QuickSettings.Available(item) then
    GameTooltip:AddLine(L.QS_UNAVAILABLE, 1, 0.1, 0.1, true)
  elseif R2F.InCombat() then
    GameTooltip:AddLine(L.QS_TIP_COMBAT, 1, 0.1, 0.1, true)
  end
  GameTooltip:Show()
end

local function heading(f, x, y, text)
  local h = f:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
  h:SetPoint("TOPLEFT", x, y)
  h:SetText(text)
  return h
end

local function buildMinimap(f)
  heading(f, LEFT, TOP - 222, L.SETTINGS_MINIMAP)
  -- Values are flipped from the saved setting, then the boxes are redrawn
  -- from it (refresh), instead of reading GetChecked after the click.
  ui.show = UI.CheckButton(f, L.SETTINGS_MINIMAP_SHOW)
  ui.show:SetPoint("TOPLEFT", LEFT + 4, TOP - 250)
  ui.show:SetScript("OnClick", function()
    local mm = Library.db.minimap
    mm.hide = not mm.hide
    refresh()
    applyMinimap()
  end)
  ui.lock = UI.CheckButton(f, L.SETTINGS_MINIMAP_LOCK)
  ui.lock:SetPoint("TOPLEFT", LEFT + 4, TOP - 276)
  ui.lock:SetScript("OnClick", function()
    local mm = Library.db.minimap
    mm.lock = not mm.lock
    refresh()
    applyMinimap()
  end)
end

local function buildQuick(f)
  heading(f, LEFT, TOP, L.QS_TITLE)
  local note = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  note:SetPoint("TOPLEFT", LEFT + 4, TOP - 28)
  note:SetWidth(300)
  note:SetJustifyH("LEFT")
  note:SetTextColor(0.7, 0.7, 0.7)
  note:SetText(L.QS_NOTE)
  ui.qsNote = note

  ui.quick = {}
  for i, item in ipairs(R2F.QuickSettings.ITEMS) do
    local b = UI.CheckButton(f, item.label)
    b:SetPoint("TOPLEFT", LEFT + 4, TOP - 70 - (i - 1) * 26)
    b.qsItem = item
    -- Tooltips still show while the box is greyed out (combat / missing),
    -- so the player can see why.
    if b.SetMotionScriptsWhileDisabled then b:SetMotionScriptsWhileDisabled(true) end
    b:SetScript("OnClick", function(self)
      R2F.QuickSettings.Toggle(self.qsItem)
      refresh()
    end)
    b:SetScript("OnEnter", showQuickTip)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    ui.quick[i] = b
  end
end

-- Theme picker: a button that opens the addon's own menu (no
-- UIDropDownMenu, which taints). Applying a theme only recolours R2F frames.
local function themeItems()
  local items = {}
  local cur = R2F.Theme.Get().key
  for _, t in ipairs(R2F.Theme.LIST) do
    items[#items + 1] = {
      kind = "check", text = t.name,
      isChecked = function() return t.key == cur end,
      func = function()
        R2F.Theme.Set(t.key)           -- recolours our own frames (MainWindow listens), nothing of the game's
        ui.theme:SetText(L.SETTINGS_THEME_BTN:format(t.name))
      end,
    }
  end
  return items
end

local function buildTheme(f)
  -- On the Minimap heading's row, right of it: the right column starts at x = 340 and the minimap switches sit below.
  local b = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  b:SetSize(170, 22)
  b:SetPoint("TOPLEFT", 130, TOP - 218)
  b:SetText(L.SETTINGS_THEME_BTN:format(R2F.Theme.Get().name))
  b:SetScript("OnClick", function() UI.ContextMenu(themeItems()) end)
  b:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:SetText(L.SETTINGS_THEME_TIP, 1, 1, 1, 1, true)
    GameTooltip:Show()
  end)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
  ui.theme = b
end

-- Called once by Home.Build with the Home page frame.
function Settings.Build(f)
  page = f
  buildMinimap(f)
  buildTheme(f)
  buildQuick(f)
  return f
end

-- Open the main window on the Home page (the old floating panel's Show / Toggle).
function Settings.Show()
  R2F.MainWindow.Show("home")
end

function Settings.Toggle()
  R2F.MainWindow.Toggle("home")
end

function Settings.IsShown()
  return R2F.MainWindow.CurrentTab() == "home"
end

-- PLAYER_REGEN_DISABLED / ENABLED: grey out / re-enable Remove all and
-- the Quick settings boxes.
function Settings.SetCombat()
  refresh()
end

-- Redraw the boxes after the minimap menu, /r2f minimap or the stance
-- commands changed a value; also MainWindow when the tab is selected.
Settings.Refresh = refresh

-- CVAR_UPDATE: a game setting changed elsewhere. Throttled to one redraw per
-- 0.2 s like Home's counts; no-op while the tab isn't showing.
local pending = false
function Settings.RequestRefresh()
  if not visible() or pending then return end
  if not (C_Timer and C_Timer.After) then refresh(); return end
  pending = true
  C_Timer.After(0.2, function() pending = false; refresh() end)
end
