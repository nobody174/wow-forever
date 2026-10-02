-- Minimap.lua: the minimap button (ADDON_PLAN.md 12.2) and its right-click menu.
--
-- Why there is no LibDBIcon in libs\ (full findings in ADDON_PLAN 6.10):
-- the plan wanted LibDataBroker-1.1 + LibDBIcon-1.0 embedded. LibStub (public
-- domain), CallbackHandler-1.0 (BSD) and LibDBIcon-1.0 (its CurseForge /
-- WowAce project page: "Ace3 Style BSD") could be shipped, but LibDBIcon
-- refuses to load without LibDataBroker-1.1, and LibDataBroker's own
-- project page says "All Rights Reserved" with no license file or grant
-- anywhere in its repository. So nothing is vendored, and this file draws
-- its own button from documented API and Blizzard's own minimap-button
-- textures (the same ones LibDBIcon uses, so it looks the same).
--
-- Two backends, picked once at PLAYER_LOGIN (every non-load-on-demand addon
-- has loaded by then):
--   "libdbicon": another installed addon already loaded LibDataBroker-1.1 and
--                LibDBIcon-1.0 (very common). We USE that copy at run time,
--                which is what those libraries are for, and redistribute
--                nothing. Benefit: minimap-button collector addons and
--                LibDBIcon's own features see our button like any other.
--   "own":       our button below, otherwise.
-- Both read and write the same R2FDB.minimap table (LibDBIcon's format, 6.3:
-- hide, lock, minimapPos in degrees counter-clockwise from 3 o'clock), so
-- the saved spot carries over if the backend changes between sessions.
--
-- Taint (6.6): plain Button parented to Minimap (what every minimap button
-- does); no secure templates, no hooks, Blizzard's frames are not changed.
-- The only OnUpdate script runs while the button is being dragged.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI

local Minimap_ = {}
R2F.Minimap = Minimap_

Minimap_.ICON = "Interface\\AddOns\\RoadToForever\\media\\logo64"
Minimap_.LDB_NAME = "RoadToForever"
local RADIUS_OFFSET = 5   -- button centre sits just outside the minimap rim

local button             -- our own button ("own" backend)
local dbicon             -- LibDBIcon-1.0 instance ("libdbicon" backend)

local function db() return R2F.Library.db.minimap end

-- ---------------------------------------------------------------------------
-- Tooltip and clicks (shared by both backends)
-- ---------------------------------------------------------------------------

-- Free talent points (12.2: "only when > 0"). UnitCharacterPoints is the
-- Classic call (first return = unspent talent points); guarded because
-- newer clients removed it.
function Minimap_.FreeTalentPoints()
  if not UnitCharacterPoints then return 0 end
  local n = UnitCharacterPoints("player")
  return type(n) == "number" and n or 0
end

-- `tt` is GameTooltip (own button) or LibDBIcon's tooltip; both have AddLine.
function Minimap_.FillTooltip(tt)
  tt:AddLine(L.ADDON_NAME, 1, 0.82, 0)
  local n = R2F.Library.Count()
  tt:AddLine(n == 1 and L.MM_LIBRARY_ONE or L.MM_LIBRARY:format(n), 1, 1, 1)
  local pts = Minimap_.FreeTalentPoints()
  if pts > 0 then
    tt:AddLine(pts == 1 and L.MM_TALENT_POINTS_ONE or L.MM_TALENT_POINTS:format(pts), 1, 1, 1)
  end
  tt:AddLine(L.MM_LEFT, 0.1, 1, 0.1)
  tt:AddLine(L.MM_RIGHT, 0.1, 1, 0.1)
  -- "Drag to move." only while it can be dragged (not when locked).
  if not db().lock then tt:AddLine(L.MM_DRAG, 0.1, 1, 0.1) end
end

function Minimap_.OnClick(owner, mouseButton)
  if mouseButton == "RightButton" then
    GameTooltip:Hide()
    Minimap_.OpenMenu(owner)
  else
    R2F.MainWindow.Toggle()
  end
end

-- ---------------------------------------------------------------------------
-- Hide / lock (12.2, Settings 5.8, /r2f minimap 12.3)
-- ---------------------------------------------------------------------------

-- Puts R2FDB.minimap on the button. Settings calls this after every change.
function Minimap_.Apply()
  local mm = db()
  if dbicon then
    if mm.hide then dbicon:Hide(Minimap_.LDB_NAME) else dbicon:Show(Minimap_.LDB_NAME) end
    if mm.lock then dbicon:Lock(Minimap_.LDB_NAME) else dbicon:Unlock(Minimap_.LDB_NAME) end
  elseif button then
    button:SetShown(not mm.hide)
    Minimap_.UpdatePosition()
  end
end

function Minimap_.SetHidden(hide)
  db().hide = hide and true or false
  Minimap_.Apply()
  R2F.Print(hide and L.MM_HIDDEN or L.MM_SHOWN)
  if R2F.Settings and R2F.Settings.Refresh then R2F.Settings.Refresh() end
end

function Minimap_.ToggleHidden()
  Minimap_.SetHidden(not db().hide)
end

function Minimap_.ToggleLock()
  db().lock = not db().lock
  Minimap_.Apply()
  if R2F.Settings and R2F.Settings.Refresh then R2F.Settings.Refresh() end
end

-- ---------------------------------------------------------------------------
-- Right-click menu (12.2)
-- ---------------------------------------------------------------------------

-- The menu as data, so both menu backends draw the same thing (and the
-- tests can check it): kind = title / button / check / divider.
function Minimap_.MenuItems()
  return {
    { kind = "title", text = L.ADDON_NAME },
    { kind = "button", text = L.MENU_OPEN, func = function() R2F.MainWindow.Show() end },
    { kind = "button", text = L.MENU_MACROS, func = function() R2F.MainWindow.Show("macros") end },
    { kind = "button", text = L.MENU_TALENTS, func = function() R2F.MainWindow.Show("talents") end },
    { kind = "divider" },
    { kind = "check", text = L.MENU_LOCK, isChecked = function() return db().lock == true end,
      func = Minimap_.ToggleLock },
    { kind = "button", text = L.MENU_HIDE, func = function() Minimap_.SetHidden(true) end },
  }
end

-- Which menu API (ADDON_PLAN 11 left it open): Blizzard's MenuUtil when the
-- client has it (newer engines, incl. recent Classic Era builds). It builds
-- its menus without the shared UIDROPDOWNMENU_* state, so no taint. Older
-- clients have only UIDropDownMenu / EasyMenu, which we deliberately skip
-- (that shared state is the known taint source, 6.7); UI.ContextMenu, our
-- own small frame, is the fallback there. Returns which one was used.
function Minimap_.OpenMenu(owner)
  local items = Minimap_.MenuItems()
  if MenuUtil and MenuUtil.CreateContextMenu then
    MenuUtil.CreateContextMenu(owner, function(_, root)
      for _, it in ipairs(items) do
        if it.kind == "title" then
          root:CreateTitle(it.text)
        elseif it.kind == "divider" then
          root:CreateDivider()
        elseif it.kind == "check" then
          root:CreateCheckbox(it.text, it.isChecked, it.func)
        else
          root:CreateButton(it.text, it.func)
        end
      end
    end)
    return "MenuUtil"
  end
  UI.ContextMenu(items)
  return "own"
end

-- ---------------------------------------------------------------------------
-- Own button ("own" backend)
-- ---------------------------------------------------------------------------

-- Minimap shapes: GetMinimapShape() is a global that minimap addons (e.g.
-- square-minimap skins) define; without it the minimap is round. For each
-- shape, which quadrants are round (1 = top right, 2 = top left,
-- 3 = bottom left, 4 = bottom right); in the others the button follows the
-- square edge instead of the circle.
local ROUND_QUADRANTS = {
  ["ROUND"] = { true, true, true, true },
  ["SQUARE"] = { false, false, false, false },
  ["CORNER-TOPRIGHT"] = { true, false, false, false },
  ["CORNER-TOPLEFT"] = { false, true, false, false },
  ["CORNER-BOTTOMLEFT"] = { false, false, true, false },
  ["CORNER-BOTTOMRIGHT"] = { false, false, false, true },
  ["SIDE-TOP"] = { true, true, false, false },
  ["SIDE-LEFT"] = { false, true, true, false },
  ["SIDE-BOTTOM"] = { false, false, true, true },
  ["SIDE-RIGHT"] = { true, false, false, true },
  ["TRICORNER-TOPRIGHT"] = { true, true, false, true },
  ["TRICORNER-TOPLEFT"] = { true, true, true, false },
  ["TRICORNER-BOTTOMLEFT"] = { false, true, true, true },
  ["TRICORNER-BOTTOMRIGHT"] = { true, false, true, true },
}

-- Offset of the button centre from the minimap centre for `degrees`.
function Minimap_.Offset(degrees)
  local a = math.rad(degrees)
  local cx, cy = math.cos(a), math.sin(a)
  local hw = Minimap:GetWidth() / 2 + RADIUS_OFFSET
  local hh = Minimap:GetHeight() / 2 + RADIUS_OFFSET
  local q = (cx >= 0 and cy >= 0 and 1) or (cx < 0 and cy >= 0 and 2) or (cx < 0 and 3) or 4
  local shape = (GetMinimapShape and GetMinimapShape()) or "ROUND"
  local round = (ROUND_QUADRANTS[shape] or ROUND_QUADRANTS.ROUND)[q]
  if round then return cx * hw, cy * hh end
  -- Square edge: stretch the direction until it touches the box.
  local k = math.min(math.abs(cx) > 1e-6 and hw / math.abs(cx) or math.huge,
                     math.abs(cy) > 1e-6 and hh / math.abs(cy) or math.huge)
  return cx * k, cy * k
end

function Minimap_.UpdatePosition()
  if not button then return end
  local x, y = Minimap_.Offset(db().minimapPos or 220)
  button:ClearAllPoints()
  button:SetPoint("CENTER", Minimap, "CENTER", x, y)
end

-- Angle of the cursor around the minimap centre, in LibDBIcon's convention.
local function cursorAngle()
  local mx, my = Minimap:GetCenter()
  local px, py = GetCursorPosition()
  local scale = Minimap:GetEffectiveScale()
  px, py = px / scale, py / scale
  return math.deg(math.atan2(py - my, px - mx)) % 360
end

local function onDragUpdate()
  db().minimapPos = cursorAngle()
  Minimap_.UpdatePosition()
end

local function buildButton()
  -- Named: minimap-button collector addons find buttons by scanning
  -- Minimap's children and reading their names (R2F-prefixed, 6.7).
  local b = CreateFrame("Button", "R2FMinimapButton", Minimap)
  b:SetSize(31, 31)
  b:SetFrameStrata("MEDIUM")
  b:SetFrameLevel(8)
  b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
  b:RegisterForDrag("LeftButton")
  b:SetHighlightTexture("Interface\\Minimap\\UI-Minimap-ZoomButton-Highlight")
  -- Blizzard's own tracking-button ring + dark round background, the look of
  -- every LibDBIcon button; our logo (already a navy disc) sits inside it.
  local overlay = b:CreateTexture(nil, "OVERLAY")
  overlay:SetSize(53, 53)
  overlay:SetTexture("Interface\\Minimap\\MiniMap-TrackingBorder")
  overlay:SetPoint("TOPLEFT")
  local bg = b:CreateTexture(nil, "BACKGROUND")
  bg:SetSize(20, 20)
  bg:SetTexture("Interface\\Minimap\\UI-Minimap-Background")
  bg:SetPoint("TOPLEFT", 7, -5)
  b.icon = b:CreateTexture(nil, "ARTWORK")
  b.icon:SetSize(19, 19)
  b.icon:SetTexture(Minimap_.ICON)
  b.icon:SetPoint("TOPLEFT", 6, -6)

  b:SetScript("OnClick", Minimap_.OnClick)
  b:SetScript("OnEnter", function(self)
    if self.r2fDragging then return end
    GameTooltip:SetOwner(self, "ANCHOR_LEFT")
    Minimap_.FillTooltip(GameTooltip)
    GameTooltip:Show()
  end)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
  -- Drag around the rim (12.2), not when locked. OnUpdate only during the drag.
  b:SetScript("OnDragStart", function(self)
    if db().lock then return end
    self.r2fDragging = true
    GameTooltip:Hide()
    self:SetScript("OnUpdate", onDragUpdate)
  end)
  b:SetScript("OnDragStop", function(self)
    self:SetScript("OnUpdate", nil)
    self.r2fDragging = false
  end)
  return b
end

-- ---------------------------------------------------------------------------
-- Init (PLAYER_LOGIN)
-- ---------------------------------------------------------------------------

-- LibStub is the libraries' own global, read only if another addon made it.
local function findLibDBIcon()
  local stub = _G.LibStub
  if type(stub) ~= "table" or type(stub.GetLibrary) ~= "function" then return nil end
  local ldb = stub:GetLibrary("LibDataBroker-1.1", true)
  local icon = stub:GetLibrary("LibDBIcon-1.0", true)
  if ldb and icon and ldb.NewDataObject and icon.Register then return ldb, icon end
end

function Minimap_.Init()
  if Minimap_.backend then return Minimap_.backend end
  local ldb, icon = findLibDBIcon()
  if ldb then
    -- pcall: a broken or very old copy in someone else's addon must not stop
    -- our login; we fall back to our own button instead.
    local ok = pcall(function()
      local obj = ldb:NewDataObject(Minimap_.LDB_NAME, {
        type = "launcher",
        label = L.ADDON_NAME,
        icon = Minimap_.ICON,
        OnClick = Minimap_.OnClick,
        OnTooltipShow = Minimap_.FillTooltip,
      })
      -- R2FDB.minimap as-is (6.3 / 6.9): LibDBIcon keeps minimapPos in it.
      icon:Register(Minimap_.LDB_NAME, obj, db())
    end)
    if ok then
      dbicon = icon
      Minimap_.backend = "libdbicon"
      Minimap_.Apply()
      return Minimap_.backend
    end
  end
  if not Minimap then
    Minimap_.backend = "none"   -- a UI without Blizzard's minimap: no button, no error
    return Minimap_.backend
  end
  button = buildButton()
  Minimap_.backend = "own"
  Minimap_.Apply()
  return Minimap_.backend
end

function Minimap_.Button() return button end
