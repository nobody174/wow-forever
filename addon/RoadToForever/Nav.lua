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

local _, R2F = ...
local L = R2F.L

local Nav = {}
R2F.Nav = Nav

Nav.ARRIVE_YARDS = 10
local EPS = 0.01          -- map fraction used to probe east / south
local THROTTLE = 0.05     -- seconds between arrow updates

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
  if cx and ux then s.x, s.y = cx - ux, cy - uy end
end

local function place(f)
  local s = settings()
  f:ClearAllPoints()
  f:SetPoint("CENTER", UIParent, "CENTER", s and s.x or 0, s and s.y or 220)
end

local function fmtYards(y)
  if y >= 1000 then return ("%.1fk yd"):format(y / 1000) end
  return ("%d yd"):format(math.floor(y + 0.5))
end

local elapsed = 0
local function update(f, dt)
  elapsed = elapsed + (dt or THROTTLE)
  if elapsed < THROTTLE then return end
  elapsed = 0
  if not target then f:Hide() return end
  local pc, px, py = Nav.PlayerWorld()
  local facing = _G.GetPlayerFacing and _G.GetPlayerFacing() or nil
  local state, yards, angle = Nav.Solve(pc, px, py, target, facing)
  if state == "ok" and yards <= Nav.ARRIVE_YARDS then
    R2F.Print(L.NAV_ARRIVED:format(target.label or ""))
    Nav.Clear()
    return
  end
  if state == "ok" and angle then
    f.arrow:SetRotation(angle)
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
  f.arrow:SetTexture("Interface\\Minimap\\MinimapArrow")
  f.arrow:SetSize(48, 48)
  f.arrow:SetPoint("TOP", f, "TOP", 0, 0)
  f.arrow:SetVertexColor(1, 0.82, 0)

  f.dist = f:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
  f.dist:SetPoint("TOP", f.arrow, "BOTTOM", 0, -2)
  f.label = f:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  f.label:SetPoint("TOP", f.dist, "BOTTOM", 0, -2)
  f.label:SetWidth(200)

  f:SetScript("OnUpdate", update)
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
  return had
end

-- "/r2f way Zone Name 47.4 52.5 optional label": the TomTom-style command.
-- Returns true when the arrow was set.
function Nav.WayCommand(rest)
  rest = (rest or ""):gsub("^%s+", ""):gsub("%s+$", "")
  local zone, xs, ys, label = rest:match("^(.-)[%s,]+([%d%.]+)[%s,]+([%d%.]+)%s*(.*)$")
  local x, y = tonumber(xs), tonumber(ys)
  if not (zone and zone ~= "" and x and y and x >= 0 and x <= 100 and y >= 0 and y <= 100) then
    R2F.Print(L.NAV_WAY_USAGE)
    return false
  end
  local mapID = R2F.Plan.ResolveMap(zone)
  if not mapID then R2F.Print(L.NAV_NO_MAP:format(zone)) return false end
  if label == "" then label = ("%s %.1f, %.1f"):format(zone, x, y) end
  if Nav.SetTarget(mapID, x, y, label, zone) then
    R2F.Print(L.NAV_SET:format(label))
    return true
  end
  R2F.Print(L.NAV_NO_WORLD)
  return false
end
