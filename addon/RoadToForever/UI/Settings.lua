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
    if enabled then R2F.Theme.PaintText(b.r2fLabel, "body") else R2F.Theme.PaintText(b.r2fLabel, "dim") end
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

-- Every element is placed from the origin of its block ("quick", "minimap", "theme"), so a theme's Home layout can move a block
-- with Settings.Place. Classic origins are the ones below; elements keep their offset inside the block.
local placed = {}
local ORIGIN = { quick = { LEFT, TOP }, minimap = { LEFT, TOP - 222 }, theme = { 130, TOP - 218 } }
for _, o in pairs(ORIGIN) do o.home = { o[1], o[2] } end
local function put(el, block, dx, dy, idx)
  placed[#placed + 1] = { el = el, block = block, dx = dx, dy = dy, idx = idx }
  el:ClearAllPoints()
  el:SetPoint("TOPLEFT", page, "TOPLEFT", ORIGIN[block][1] + dx, ORIGIN[block][2] + dy)
end

-- origins: { quick = { x, y }, minimap = { x, y }, theme = { x, y } } in page coordinates (nil = Classic's places).
-- `width` is the text width of the Quick settings note.
-- opts (optional): { quickCols, quickColW, quickStart, miniCols, miniColW } lay the switches out in columns.
function Settings.Place(origins, width, opts)
  origins = origins or {}
  opts = opts or {}
  for block, o in pairs(ORIGIN) do
    local n = origins[block]
    o[1], o[2] = n and n[1] or o.home[1], n and n[2] or o.home[2]
  end
  for _, p in ipairs(placed) do
    local dx, dy = p.dx, p.dy
    if p.idx and p.block == "quick" and opts.quickCols then
      dx = 4 + ((p.idx - 1) % opts.quickCols) * opts.quickColW
      dy = (opts.quickStart or -70) - math.floor((p.idx - 1) / opts.quickCols) * 26
    elseif p.idx and p.block == "minimap" and opts.miniCols then
      dx = 4 + ((p.idx - 1) % opts.miniCols) * opts.miniColW
      dy = -28 - math.floor((p.idx - 1) / opts.miniCols) * 26
    end
    p.el:ClearAllPoints()
    p.el:SetPoint("TOPLEFT", page, "TOPLEFT", ORIGIN[p.block][1] + dx, ORIGIN[p.block][2] + dy)
  end
  if ui.qsNote then ui.qsNote:SetWidth(width or 300) end
end

local function heading(f, block, dx, dy, text)
  local h = f:CreateFontString(nil, "ARTWORK", "R2FHeadingLarge")
  put(h, block, dx, dy)
  h:SetText(text)
  return h
end

local function buildMinimap(f)
  heading(f, "minimap", 0, 0, L.SETTINGS_MINIMAP)
  -- Values are flipped from the saved setting, then the boxes are redrawn
  -- from it (refresh), instead of reading GetChecked after the click.
  ui.show = UI.CheckButton(f, L.SETTINGS_MINIMAP_SHOW)
  put(ui.show, "minimap", 4, -28, 1)
  ui.show:SetScript("OnClick", function()
    local mm = Library.db.minimap
    mm.hide = not mm.hide
    refresh()
    applyMinimap()
  end)
  ui.lock = UI.CheckButton(f, L.SETTINGS_MINIMAP_LOCK)
  put(ui.lock, "minimap", 4, -54, 2)
  ui.lock:SetScript("OnClick", function()
    local mm = Library.db.minimap
    mm.lock = not mm.lock
    refresh()
    applyMinimap()
  end)
end

local function buildQuick(f)
  heading(f, "quick", 0, 0, L.QS_TITLE)
  local note = f:CreateFontString(nil, "ARTWORK", "R2FBodySmall")
  put(note, "quick", 4, -28)
  note:SetWidth(300)
  note:SetJustifyH("LEFT")
  R2F.Theme.PaintText(note, "note")
  note:SetText(L.QS_NOTE)
  ui.qsNote = note

  ui.quick = {}
  for i, item in ipairs(R2F.QuickSettings.ITEMS) do
    local b = UI.CheckButton(f, item.label)
    put(b, "quick", 4, -70 - (i - 1) * 26, i)
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

-- Theme: a button that opens the "Choose a look" gallery (UI/ThemePicker.lua); applying a look only recolours R2F frames.
local function buildTheme(f)
  -- On the Minimap heading's row, right of it: the right column starts at x = 340 and the minimap switches sit below.
  local b = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  b:SetSize(170, 22)
  put(b, "theme", 0, 0)
  b:SetText(L.SETTINGS_THEME_BTN:format(R2F.Theme.Get().name))
  -- As wide as its label: a theme's font can be wider than the game's.
  local function fit()
    local fs = b.GetFontString and b:GetFontString()
    local w = fs and fs.GetStringWidth and fs:GetStringWidth() or 0
    b:SetWidth(math.min(200, math.max(170, math.ceil(w) + 32)))
  end
  b.r2fFit = fit
  fit()
  R2F.Theme.OnChange(function() if b.r2fFit then b.r2fFit() end end)
  UI.ThemeButton(b)
  b:SetScript("OnClick", function() R2F.ThemePicker.Toggle() end)
  -- Whoever changes the look (the gallery, a command), the button names the one in use.
  R2F.Theme.OnChange(function(t) b:SetText(L.SETTINGS_THEME_BTN:format(t.name)) if b.r2fFit then b.r2fFit() end end)
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
