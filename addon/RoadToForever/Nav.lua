-- Nav.lua: BiZNav, our own waypoint arrow (replaces TomTom for the Plan tab).
--
-- One target at a time: { mapID, x, y (map percent 0-100), label, zone }. Nav.SetTarget
-- shows a small movable arrow that points at it, with the distance in yards and the label.
-- Left-drag moves the arrow, right-click clears the target. Within ARRIVE_YARDS the target
-- is reached: chat says so and the arrow hides.
--
-- Math, without guessing the game's world axes: C_Map.GetWorldPosFromMapPos turns a map
-- position into world yards. Moving a little east / south on the target's map gives the
-- east and south directions in world space, so the player-to-target vector splits into
-- yards east and yards north. GetPlayerFacing() is radians counter-clockwise from north,
-- and Texture:SetRotation turns counter-clockwise, so the arrow angle is
-- bearing - facing with bearing = atan2(-east, north).
--
-- Where the game gives no position (inside instances, some cities) or the target is on
-- another continent, the arrow is replaced by a line saying so. Without
-- GetWorldPosFromMapPos the client can't place the arrow at all; then SetTarget returns
-- false and the caller prints the /way line instead.
--
-- Only our own frame, read-only map getters and SavedVariables: works in combat, no taint.
-- Without TomTom installed, a small `TomTom` table with AddWaypoint / RemoveWaypoint lets
-- Questie's Ctrl + click on its map icons point this arrow (see the end of the file).

local _, R2F = ...
local L = R2F.L

local Nav = {}
R2F.Nav = Nav

Nav.ARRIVE_YARDS = 10
local EPS = 0.01          -- map fraction used to probe east / south
local THROTTLE = 0.05     -- seconds between arrow updates

-- Arrow sizes (Tweaks > Alerts & HUD): frame scale per choice. Medium is the default.
Nav.SIZES = { small = 1.0, medium = 1.4, large = 1.8 }
Nav.SIZE_ORDER = { "small", "medium", "large" }

local target              -- { mapID, x, y, label, zone, continent, wx, wy, ex, ey, sx, sy }

-- ---------------------------------------------------------------------------
-- Map / world helpers (read-only, guarded)
-- ---------------------------------------------------------------------------

function Nav.Supported()
  return C_Map ~= nil and C_Map.GetWorldPosFromMapPos ~= nil and _G.CreateVector2D ~= nil
end

-- mapID, x01, y01 -> continentID, worldX, worldY (nil when the map has no world position)
function Nav.WorldPos(mapID, x, y)
  if not (Nav.Supported() and mapID and x and y) then return nil end
  local ok, cont, pos = pcall(C_Map.GetWorldPosFromMapPos, mapID, _G.CreateVector2D(x, y))
  if not (ok and cont and pos) then return nil end
  local wx, wy
  if pos.GetXY then wx, wy = pos:GetXY() else wx, wy = pos.x, pos.y end
  if not (wx and wy) then return nil end
  return cont, wx, wy
end

-- The player's world position: continentID, worldX, worldY, mapID (nil where there is none).
function Nav.PlayerWorld()
  if not (C_Map and C_Map.GetBestMapForUnit and C_Map.GetPlayerMapPosition) then return nil end
  local mapID = C_Map.GetBestMapForUnit("player")
  if not mapID then return nil end
  local pos = C_Map.GetPlayerMapPosition(mapID, "player")
  if not (pos and pos.GetXY) then return nil end
  local x, y = pos:GetXY()
  if not (x and y) or (x == 0 and y == 0) then return nil end
  local cont, wx, wy = Nav.WorldPos(mapID, x, y)
  if not cont then return nil end
  return cont, wx, wy, mapID
end

-- Pure: where is the target from the player? Returns state, yards, angle.
--   state "ok"    : yards and angle (radians to turn the up-pointing arrow, counter-clockwise)
--   state "far"   : the target is on another continent
--   state "nopos" : no player position here
-- t = { continent, wx, wy, ex, ey, sx, sy } (e* / s* = unit east / south in world space)
function Nav.Solve(pc, px, py, t, facing)
  if not pc then return "nopos" end
  if pc ~= t.continent then return "far" end
  local dx, dy = t.wx - px, t.wy - py
  local yards = math.sqrt(dx * dx + dy * dy)
  local east = dx * t.ex + dy * t.ey
  local north = -(dx * t.sx + dy * t.sy)
  local bearing = math.atan2(-east, north)
  if not facing then return "ok", yards, nil end
  local a = bearing - facing
  local tau = 2 * math.pi
  a = a % tau
  if a > math.pi then a = a - tau end
  return "ok", yards, a
end

local function unit(ax, ay, bx, by)
  local dx, dy = bx - ax, by - ay
  local len = math.sqrt(dx * dx + dy * dy)
  if len == 0 then return nil end
  return dx / len, dy / len
end

-- Builds the internal target (world position + east / south axes) or nil.
function Nav.MakeTarget(mapID, x, y, label, zone)
  local fx, fy = x / 100, y / 100
  local cont, wx, wy = Nav.WorldPos(mapID, fx, fy)
  if not cont then return nil end
  local sgnx = fx + EPS <= 1 and 1 or -1
  local sgny = fy + EPS <= 1 and 1 or -1
  local _, ewx, ewy = Nav.WorldPos(mapID, fx + sgnx * EPS, fy)
  local _, swx, swy = Nav.WorldPos(mapID, fx, fy + sgny * EPS)
  if not (ewx and swx) then return nil end
  local ex, ey = unit(wx, wy, ewx, ewy)
  local sx, sy = unit(wx, wy, swx, swy)
  if not (ex and sx) then return nil end
  if sgnx < 0 then ex, ey = -ex, -ey end
  if sgny < 0 then sx, sy = -sx, -sy end
  return { mapID = mapID, x = x, y = y, label = label, zone = zone, continent = cont,
    wx = wx, wy = wy, ex = ex, ey = ey, sx = sx, sy = sy }
end

-- ---------------------------------------------------------------------------
-- The arrow frame
-- ---------------------------------------------------------------------------

local frame

local function settings()
  local db = R2F.Library and R2F.Library.db
  return db and db.nav
end

local function savePos(f)
  local s = settings()
  if not s then return end
  local cx, cy = f:GetCenter()
  local ux, uy = UIParent:GetCenter()
  -- GetCenter is in the frame's own scale (Small / Medium / Large), UIParent's in its own: compare in screen units and
  -- save in UIParent units, so the arrow comes back where it was dropped at any size.
  if cx and ux then
    local fs, us = f:GetEffectiveScale(), UIParent:GetEffectiveScale()
    s.x, s.y = (cx * fs - ux * us) / us, (cy * fs - uy * us) / us
  end
end

local function place(f)
  local s = settings()
  f:ClearAllPoints()
  -- SetPoint offsets are in the frame's own scale; the saved ones are in UIParent units.
  local k = UIParent:GetEffectiveScale() / f:GetEffectiveScale()
  f:SetPoint("CENTER", UIParent, "CENTER", (s and s.x or 0) * k, (s and s.y or 220) * k)
end

local elapsed, update   -- the arrow's OnUpdate state, defined below

-- The 3D look: addon/art/export_arrow3d.py renders the arrow from FRAMES turn angles into one sprite sheet
-- (media/arrow3d.tga, CELL px cells in a SHEET px square, COLS per row). Frame k = the arrow turned counter-clockwise
-- by k * 360 / FRAMES degrees, which is what Nav.Solve's angle means. The game has no height for waypoints, so
-- this is a ground-plane perspective only.
Nav.FRAMES, Nav.COLS, Nav.CELL, Nav.SHEET = 100, 10, 102, 1024
local ARROW_FLAT = "Interface\\AddOns\\RoadToForever\\media\\arrow"
local ARROW_3D = "Interface\\AddOns\\RoadToForever\\media\\arrow3d"
-- The looks to choose from (Tweaks > Alerts & HUD): the flat dart, and a sprite sheet per 3D look
-- (all share FRAMES / COLS / CELL).
-- A new look: render it with addon/art/export_arrow3d.py, add it here and a NAV_STYLE_<KEY> text in Locale.lua.
Nav.STYLE_ORDER = { "flat", "dart", "arrow", "block", "needle" }
Nav.STYLES = {
  flat = {},
  dart = { tex = "Interface\\AddOns\\RoadToForever\\media\\arrow3d_dart" },
  arrow = { tex = ARROW_3D },
  block = { tex = "Interface\\AddOns\\RoadToForever\\media\\arrow3d_block" },
  needle = { tex = "Interface\\AddOns\\RoadToForever\\media\\arrow3d_needle" },
}

-- Sprite frame (0 .. FRAMES - 1) for a turn angle in radians (counter-clockwise, any size).
function Nav.FrameFor(angle)
  local k = math.floor(angle / (2 * math.pi) * Nav.FRAMES + 0.5)
  return k % Nav.FRAMES
end

-- left, right, top, bottom texture coordinates of frame k.
function Nav.FrameCoords(k)
  local c, r = k % Nav.COLS, math.floor(k / Nav.COLS)
  local u = Nav.CELL / Nav.SHEET
  return c * u, (c + 1) * u, r * u, (r + 1) * u
end

function Nav.Is3D()
  return R2F.Gameplay ~= nil and R2F.Gameplay.IsOn("arrow3d") and true or false
end

-- The look in use: "flat", "dart" or "arrow".
function Nav.Style()
  if not Nav.Is3D() then return "flat" end
  local st = settings()
  local k = st and st.style
  return (k and k ~= "flat" and Nav.STYLES[k]) and k or "arrow"
end

-- Choose a look. Saved, applied at once.
function Nav.SetStyle(key)
  if not Nav.STYLES[key] then return false end
  local st = settings()
  if key ~= "flat" and st then st.style = key end
  R2F.Gameplay.SetOn("arrow3d", key ~= "flat")
  Nav.ApplyStyle()
  return true
end

-- Switch the arrow's picture between the flat dart and a 3D sheet (also when the look or the Tweaks switch changes).
local function applyStyle(f)
  local key = Nav.Style()
  if f.style == key then return end
  f.style = key
  if key ~= "flat" then
    f.arrow:SetTexture(Nav.STYLES[key].tex)
    f.arrow:SetSize(64, 64)
    f.arrow:SetRotation(0)
    f:SetSize(120, 108)
  else
    f.arrow:SetTexture(ARROW_FLAT)
    f.arrow:SetTexCoord(0, 1, 0, 1)
    f.arrow:SetSize(48, 48)
    f:SetSize(120, 92)
  end
end

function Nav.ApplyStyle()
  if frame then
    frame.style = nil
    applyStyle(frame)
    elapsed = THROTTLE
    if target then update(frame, 0) end
  end
end

local function fmtYards(y)
  if y >= 1000 then return ("%.1fk yd"):format(y / 1000) end
  return ("%d yd"):format(math.floor(y + 0.5))
end

elapsed = 0
update = function(f, dt)
  elapsed = elapsed + (dt or THROTTLE)
  if elapsed < THROTTLE then return end
  elapsed = 0
  if not target then f:Hide() return end
  Nav.UpdatePin()
  local pc, px, py = Nav.PlayerWorld()
  local facing = _G.GetPlayerFacing and _G.GetPlayerFacing() or nil
  local state, yards, angle = Nav.Solve(pc, px, py, target, facing)
  if state == "ok" and yards <= Nav.ARRIVE_YARDS then
    R2F.Print(L.NAV_ARRIVED:format(target.label or ""))
    Nav.Clear()
    return
  end
  if state == "ok" and angle then
    applyStyle(f)
    if f.style ~= "flat" then
      f.arrow:SetTexCoord(Nav.FrameCoords(Nav.FrameFor(angle)))
    else
      f.arrow:SetRotation(angle)
    end
    f.arrow:Show()
    f.dist:SetText(fmtYards(yards))
  else
    f.arrow:Hide()
    if state == "far" then
      f.dist:SetText(L.NAV_FAR:format(target.zone or "?"))
    elseif state == "ok" then
      f.dist:SetText(fmtYards(yards))
    else
      f.dist:SetText(L.NAV_NOPOS)
    end
  end
end

local function build()
  if frame then return frame end
  local f = CreateFrame("Frame", "R2FNavFrame", UIParent)
  f:SetSize(120, 92)
  f:SetFrameStrata("MEDIUM")
  f:SetClampedToScreen(true)
  f:SetMovable(true)
  f:EnableMouse(true)
  f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", function(self) self:StartMoving() end)
  f:SetScript("OnDragStop", function(self)
    self:StopMovingOrSizing()
    savePos(self)
    place(self)
  end)
  f:SetScript("OnMouseUp", function(_, button)
    if button == "RightButton" then Nav.Clear() end
  end)
  f:SetScript("OnEnter", function(self)
    if not GameTooltip then return end
    GameTooltip:SetOwner(self, "ANCHOR_BOTTOM")
    GameTooltip:SetText(target and target.label or "")
    if target and target.zone then GameTooltip:AddLine(target.zone, 1, 1, 1) end
    GameTooltip:AddLine(L.NAV_TIP, 0.7, 0.7, 0.7)
    GameTooltip:Show()
  end)
  f:SetScript("OnLeave", function() if GameTooltip then GameTooltip:Hide() end end)

  f.arrow = f:CreateTexture(nil, "ARTWORK")
  -- Our own 128 px dart (addon/art/export_arrow.py) or the 3D sprite sheet (export_arrow3d.py), so it stays sharp at Large.
  f.arrow:SetTexture(ARROW_FLAT)
  f.arrow:SetSize(48, 48)
  f.arrow:SetPoint("TOP", f, "TOP", 0, 0)
  applyStyle(f)

  f.dist = f:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
  f.dist:SetPoint("TOP", f.arrow, "BOTTOM", 0, -2)
  f.label = f:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  f.label:SetPoint("TOP", f.dist, "BOTTOM", 0, -2)
  f.label:SetWidth(200)

  f:SetScript("OnUpdate", update)
  local st = settings()
  f:SetScale(Nav.SIZES[st and st.size] or Nav.SIZES.medium)
  place(f)
  f:Hide()
  frame = f
  return f
end

-- ---------------------------------------------------------------------------
-- Public API
-- ---------------------------------------------------------------------------

function Nav.Target() return target end

-- Point the arrow at mapID x, y (map percent). Returns true if the arrow is set, false if
-- this client can't place that map in the world (the caller falls back to the /way line).
function Nav.SetTarget(mapID, x, y, label, zone)
  local t = mapID and x and y and Nav.MakeTarget(mapID, x, y, label, zone)
  if not t then return false end
  target = t
  local f = build()
  f.label:SetText(label or "")
  elapsed = THROTTLE
  f:Show()
  update(f, 0)
  return true
end

function Nav.Clear()
  local had = target ~= nil
  target = nil
  if frame then frame:Hide() end
  Nav.UpdatePin()
  return had
end

function Nav.Size()
  local st = settings()
  return st and Nav.SIZES[st.size] and st.size or "medium"
end

-- "small" / "medium" / "large": saved, applied at once.
function Nav.SetSize(key)
  if not Nav.SIZES[key] then return false end
  local st = settings()
  if st then st.size = key end
  if frame then
    -- Keep the arrow's centre where it is while the scale changes.
    frame:SetScale(Nav.SIZES[key])
    place(frame)
  end
  return true
end

-- The zone the player is in: mapID, name (nil where the game gives no map).
local function currentZone()
  if not (C_Map and C_Map.GetBestMapForUnit) then return nil end
  local id = C_Map.GetBestMapForUnit("player")
  if not id then return nil end
  local info = C_Map.GetMapInfo and C_Map.GetMapInfo(id)
  return id, info and info.name or "?"
end

local function setAndSay(mapID, x, y, label, zone)
  if Nav.SetTarget(mapID, x, y, label, zone) then
    R2F.Print(L.NAV_SET:format(label))
    return true
  end
  R2F.Print(L.NAV_NO_WORLD)
  return false
end

local function inRange(x, y) return x and y and x >= 0 and x <= 100 and y >= 0 and y <= 100 end

-- "/bizway" and "/r2f way". Accepted forms:
--   <x> <y> [label]           in the zone you are in
--   <zone> <x> <y> [label]    in that zone
--   <label> <x> <y>           when the words before the numbers are not a zone: label, zone you are in
--   clear  /  size small|medium|large
-- Returns true when the arrow was set (or the size / clear done).
function Nav.WayCommand(rest)
  rest = (rest or ""):gsub("^%s+", ""):gsub("%s+$", "")
  local lower = rest:lower()
  if lower == "clear" then
    if not Nav.Clear() then R2F.Print(L.NAV_NONE) end
    return true
  end
  local sz = lower:match("^size%s+(%a+)$")
  if sz then
    if Nav.SetSize(sz) then R2F.Print(L.NAV_SIZE_SET:format(L["NAV_SIZE_" .. sz:upper()])) return true end
    R2F.Print(L.NAV_WAY_USAGE)
    return false
  end
  -- x y [label]: the zone you are in.
  local xs, ys, label = rest:match("^([%d%.]+)[%s,]+([%d%.]+)%s*(.*)$")
  if xs then
    local x, y = tonumber(xs), tonumber(ys)
    local mapID, zone = currentZone()
    if not inRange(x, y) then R2F.Print(L.NAV_WAY_USAGE) return false end
    if not mapID then R2F.Print(L.PLAN_HERE_NONE) return false end
    if label == "" then label = ("%s %.1f, %.1f"):format(zone, x, y) end
    return setAndSay(mapID, x, y, label, zone)
  end
  local words
  words, xs, ys, label = rest:match("^(.-)[%s,]+([%d%.]+)[%s,]+([%d%.]+)%s*(.*)$")
  local x, y = tonumber(xs), tonumber(ys)
  if not (words and words ~= "" and inRange(x, y)) then
    R2F.Print(L.NAV_WAY_USAGE)
    return false
  end
  local mapID = R2F.Plan.ResolveMap(words)
  if mapID then
    if label == "" then label = ("%s %.1f, %.1f"):format(words, x, y) end
    return setAndSay(mapID, x, y, label, words)
  end
  -- Not a zone name: with nothing after the numbers, the words are the label in this zone.
  local here, zone = currentZone()
  if label == "" and here then
    return setAndSay(here, x, y, words, zone)
  end
  R2F.Print(L.NAV_NO_MAP:format(words))
  return false
end

-- ---------------------------------------------------------------------------
-- World map: a pin at the target, and Alt + right-click to set the arrow there.
-- Our own pin frame is parented to the map canvas; the click is read with HookScript
-- (runs after the game's own handler, like hooksecurefunc). Nothing is written into the
-- map's own tables, no data provider is added.
-- ---------------------------------------------------------------------------

local pin, hooked

local function mapFrame() return _G.WorldMapFrame end

local function canvas()
  local wm = mapFrame()
  return wm and wm.ScrollContainer and wm.ScrollContainer.Child
end

-- Where the target sits on map `mapID`, as 0-1 fractions (nil if it isn't on that map).
function Nav.PinPos(mapID)
  if not (target and mapID) then return nil end
  if mapID == target.mapID then return target.x / 100, target.y / 100 end
  if not (C_Map and C_Map.GetMapPosFromWorldPos and _G.CreateVector2D) then return nil end
  local ok, _, pos = pcall(C_Map.GetMapPosFromWorldPos, target.continent,
    _G.CreateVector2D(target.wx, target.wy), mapID)
  if not (ok and pos) then return nil end
  local x, y
  if pos.GetXY then x, y = pos:GetXY() else x, y = pos.x, pos.y end
  if not (x and y) or x < 0 or x > 1 or y < 0 or y > 1 then return nil end
  return x, y
end

local function buildPin(parent)
  local p = CreateFrame("Frame", "R2FNavPin", parent)
  p:SetSize(14, 14)
  p:SetFrameStrata("HIGH")
  p.icon = p:CreateTexture(nil, "OVERLAY")
  p.icon:SetAllPoints()
  p.icon:SetTexture("Interface\\TargetingFrame\\UI-RaidTargetingIcon_3")
  p:EnableMouse(true)
  p:SetScript("OnEnter", function(self)
    if not (GameTooltip and target) then return end
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:SetText(target.label or "")
    GameTooltip:AddLine(L.NAV_PIN_TIP, 0.7, 0.7, 0.7)
    GameTooltip:Show()
  end)
  p:SetScript("OnLeave", function() if GameTooltip then GameTooltip:Hide() end end)
  p:Hide()
  return p
end

function Nav.UpdatePin()
  local wm, c = mapFrame(), canvas()
  if not (wm and c) then return end
  pin = pin or buildPin(c)
  if not (target and wm:IsShown()) then pin:Hide() return end
  local mapID = wm.GetMapID and wm:GetMapID()
  local x, y = Nav.PinPos(mapID)
  if not x then pin:Hide() return end
  local w, h = c:GetWidth(), c:GetHeight()
  local sc = c.GetScale and c:GetScale() or 1
  pin:SetScale(sc > 0 and 1 / sc or 1)
  local ps = pin:GetScale()
  pin:ClearAllPoints()
  pin:SetPoint("CENTER", c, "TOPLEFT", x * w / ps, -y * h / ps)
  pin:Show()
end

-- Alt + right-click on the world map: point the arrow at that spot. Read on mouse-down,
-- before the game's right-click zooms the map out.
local function onMapMouseDown(self, button)
  if button ~= "RightButton" or not (IsAltKeyDown and IsAltKeyDown()) then return end
  local wm = mapFrame()
  local mapID = wm and wm.GetMapID and wm:GetMapID()
  if not (mapID and self.GetNormalizedCursorPosition) then return end
  local x, y = self:GetNormalizedCursorPosition()
  if not (x and y) or x < 0 or x > 1 or y < 0 or y > 1 then return end
  local info = C_Map.GetMapInfo and C_Map.GetMapInfo(mapID)
  local zone = info and info.name or "?"
  setAndSay(mapID, x * 100, y * 100, ("%s %.1f, %.1f"):format(zone, x * 100, y * 100), zone)
end

-- Hooks the map once it exists (at login, or when the game loads its map addon).
function Nav.HookMap()
  if hooked then return true end
  local wm = mapFrame()
  local sc = wm and wm.ScrollContainer
  if not (sc and sc.HookScript) then return false end
  sc:HookScript("OnMouseDown", onMapMouseDown)
  if wm.HookScript then wm:HookScript("OnShow", function() Nav.UpdatePin() end) end
  hooked = true
  return true
end

-- ---------------------------------------------------------------------------
-- Questie: Ctrl + click on a Questie map icon (and its "Set TomTom Target" buttons) calls
-- TomTom:AddWaypoint / TomTom:RemoveWaypoint when a TomTom table exists. When the real TomTom
-- is not installed we provide those two calls and point BiZNav instead. Only set at login,
-- after every addon has loaded, and never when TomTom itself is there.
-- ---------------------------------------------------------------------------

local function zoneName(mapID)
  local info = C_Map and C_Map.GetMapInfo and C_Map.GetMapInfo(mapID)
  return info and info.name or "?"
end

Nav.TomTomShim = {
  r2f = true,
  -- (mapID, x 0-1, y 0-1, { title = }) -> a waypoint table Questie keeps, or nil.
  AddWaypoint = function(_, mapID, x, y, opts)
    if not (mapID and x and y) then return nil end
    local title = opts and opts.title or ("%s %.1f, %.1f"):format(zoneName(mapID), x * 100, y * 100)
    if not Nav.SetTarget(mapID, x * 100, y * 100, title, zoneName(mapID)) then return nil end
    R2F.Print(L.NAV_SET:format(title))
    return { mapID, x, y, title = title, from = opts and opts.from }
  end,
  -- Clears the arrow if it still points at that waypoint.
  RemoveWaypoint = function(_, wp)
    local t = target
    if type(wp) == "table" and t and t.mapID == wp[1] and math.abs(t.x - (wp[2] or -1) * 100) < 1e-6
        and math.abs(t.y - (wp[3] or -1) * 100) < 1e-6 then
      Nav.Clear()
    end
  end,
}

local function tomTomInstalled()
  local loaded = C_AddOns and C_AddOns.IsAddOnLoaded or _G.IsAddOnLoaded
  if not loaded then return false end
  local ok, yes = pcall(loaded, "TomTom")
  return ok and yes and true or false
end

-- Returns true when the stand-in is in place.
function Nav.InstallTomTomShim()
  if _G.TomTom ~= nil then return _G.TomTom == Nav.TomTomShim end
  if tomTomInstalled() then return false end
  _G.TomTom = Nav.TomTomShim
  return true
end

-- ---------------------------------------------------------------------------
-- Corpse arrow: when you die the arrow points at your corpse; when you are alive again the arrow you had comes back.
-- ---------------------------------------------------------------------------

local corpse = { active = false, prev = nil }

-- mapID, x, y (map percent) of your corpse on the map you are on, or nil (not released yet, other map, no API).
local function corpsePos()
  if not (C_DeathInfo and C_DeathInfo.GetCorpseMapPosition and C_Map and C_Map.GetBestMapForUnit) then return nil end
  local mapID = C_Map.GetBestMapForUnit("player")
  if not mapID then return nil end
  local ok, pos = pcall(C_DeathInfo.GetCorpseMapPosition, mapID)
  if not (ok and pos) then return nil end
  local x, y
  if pos.GetXY then x, y = pos:GetXY() else x, y = pos.x, pos.y end
  if not (x and y) or (x == 0 and y == 0) then return nil end
  return mapID, x * 100, y * 100
end

-- Point the arrow at the corpse (keeps the arrow you had to bring back later). True when it is set.
function Nav.ShowCorpse()
  if target and target.isCorpse then return true end
  local mapID, x, y = corpsePos()
  if not mapID then return false end
  local prev = target
  if not Nav.SetTarget(mapID, x, y, L.NAV_CORPSE, nil) then return false end
  target.isCorpse = true
  if not corpse.active and prev then
    corpse.prev = { mapID = prev.mapID, x = prev.x, y = prev.y, label = prev.label, zone = prev.zone }
  end
  corpse.active = true
  R2F.Print(L.NAV_CORPSE_SET)
  return true
end

-- Alive again: drop the corpse arrow and put the one from before back (if any). A target you set yourself
-- while dead is left alone.
function Nav.RestoreAfterCorpse()
  if not corpse.active then return end
  local prev = corpse.prev
  corpse.active, corpse.prev = false, nil
  if target and not target.isCorpse then return end
  if target then Nav.Clear() end
  if prev then Nav.SetTarget(prev.mapID, prev.x, prev.y, prev.label, prev.zone) end
end

local function isGhost() return _G.UnitIsGhost and _G.UnitIsGhost("player") end

-- Tweaks > Alerts & HUD: "3D arrow" (on by default, Library.lua); off = the flat dart.
R2F.Gameplay.Register({ key = "arrow3d", group = "screen", title = "NAV_3D_TITLE", tip = "NAV_3D_TIP",
  onToggle = function() Nav.ApplyStyle() end })

-- Tweaks > Alerts & HUD: "Arrow to corpse when you die" (on by default, Library.lua).
R2F.Gameplay.Register({
  key = "corpsearrow", group = "screen", title = "NAV_CORPSE_TITLE", tip = "NAV_CORPSE_TIP",
  events = {
    PLAYER_DEAD = function() Nav.ShowCorpse() end,
    -- Releasing the spirit and being resurrected both fire PLAYER_ALIVE: a ghost has a corpse to find, anyone else is back.
    PLAYER_ALIVE = function() if isGhost() then Nav.ShowCorpse() else Nav.RestoreAfterCorpse() end end,
    PLAYER_UNGHOST = function() Nav.RestoreAfterCorpse() end,
    -- Reload or login as a ghost.
    PLAYER_ENTERING_WORLD = function() if isGhost() then Nav.ShowCorpse() end end,
    CORPSE_POSITION_UPDATE = function() if isGhost() or (_G.UnitIsDead and _G.UnitIsDead("player")) then Nav.ShowCorpse() end end,
  },
})

local ev = CreateFrame("Frame")
ev:RegisterEvent("PLAYER_LOGIN")
ev:RegisterEvent("ADDON_LOADED")
ev:SetScript("OnEvent", function(_, event, name)
  if event == "PLAYER_LOGIN" then Nav.InstallTomTomShim() end
  if event == "PLAYER_LOGIN" or name == "Blizzard_WorldMap" then Nav.HookMap() end
end)
