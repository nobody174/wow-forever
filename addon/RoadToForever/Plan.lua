-- Plan.lua: the Launch Plan in game (ADDON_PLAN.md 15.5, v0.18.0). Logic only; the tab
-- is UI/Plan.lua, the data is PlanData.lua (generated from the site, see below).
--
-- * Plans: the same group plans as launch-plan.html (hwd, hunter, h3d, trio) with the
--   site's rules: an item's own fields apply to every plan unless it has a key in `ov` for
--   that plan or for a plan up its `base` chain (the nearest one wins); `false` hides the
--   item, a table replaces the fields it names. Only the launch-day phases (night, p1, p2,
--   p3) are in the data.
-- * Ticks: R2FCharDB.plan.done[stepId] = true, per character, shared by every plan (a step
--   keeps its tick if you switch plans, like the site). R2FCharDB.plan.selected = the plan.
-- * Waypoints: PlanData.waypoints[stepId] = { default = {points}, <plan> = {points} }; a
--   plan's own list replaces the default for that plan. A point has zone (English name),
--   x / y in map percent, label and conf: exact | classic | approx | check. `check` = no
--   position known yet (label only, no button); classic / approx = "may have moved".
--   The zone name is turned into a uiMapID at run time (Plan.ResolveMap) by walking
--   C_Map.GetMapChildrenInfo, because the ids are not known for Forever's new zones.
--   With TomTom loaded the button calls TomTom:AddWaypoint(mapID, x/100, y/100, {title});
--   without it (or without a map id) it prints the "/way Zone x y label" line to chat.
-- * /r2f here prints the zone, uiMapID and x / y you stand at, so a `check` point can be
--   filled in from the beta.
--
-- Everything here is read-only game-wise (map getters, TomTom): it works in combat.

local _, R2F = ...
local L = R2F.L

local Plan = {}
R2F.Plan = Plan

local function data() return R2F.PlanData end
local function cdb() return R2F.Library.cdb.plan end

-- ---------------------------------------------------------------------------
-- Plans and steps
-- ---------------------------------------------------------------------------

-- The override for `planId`: its own key first, then up its base chain. nil = none,
-- false = hidden, table = fields to replace. (Site: override() in launch-plan.html.)
local function override(item, planId)
  local ov = item.ov
  if not ov then return nil end
  local p = planId
  while p do
    if ov[p] ~= nil then return ov[p] end
    local def = data().plans[p]
    p = def and def.base
  end
  return nil
end
Plan.Override = override

-- One item for one plan: nil if hidden, else a new table with the merged fields.
function Plan.Resolve(item, planId)
  local o = override(item, planId)
  if o == false then return nil end
  local out = { id = item.id, lvl = item.lvl, t = item.t, n = item.n, tags = item.tags or {} }
  if o then
    for k, v in pairs(o) do out[k] = v end
  end
  out.tags = out.tags or {}
  return out
end

-- Plan ids in the site's order, and the label of one.
function Plan.Order() return data().order end
function Plan.Label(planId)
  local def = data().plans[planId]
  return def and def.label or planId
end

-- { { id =, title =, steps = { resolved item, ... } }, ... } for one plan; phases with
-- no step for the plan are left out.
function Plan.Phases(planId)
  local out = {}
  for _, ph in ipairs(data().phases) do
    local steps = {}
    for _, item in ipairs(ph.items) do
      local r = Plan.Resolve(item, planId)
      if r then steps[#steps + 1] = r end
    end
    if #steps > 0 then out[#out + 1] = { id = ph.id, title = ph.title, steps = steps } end
  end
  return out
end

-- Every step of the plan in order (flat).
function Plan.Steps(planId)
  local out = {}
  for _, ph in ipairs(Plan.Phases(planId)) do
    for _, s in ipairs(ph.steps) do
      s.phase = ph.id
      s.phaseTitle = ph.title
      out[#out + 1] = s
    end
  end
  return out
end

-- ---------------------------------------------------------------------------
-- Saved state (per character)
-- ---------------------------------------------------------------------------

function Plan.Selected()
  return cdb().selected
end

function Plan.Select(planId)
  if not data().plans[planId] then return false end
  cdb().selected = planId
  return true
end

function Plan.IsDone(stepId)
  return cdb().done[stepId] == true
end

function Plan.SetDone(stepId, done)
  cdb().done[stepId] = done and true or nil
end

-- done, total for the plan.
function Plan.Progress(planId)
  local done, total = 0, 0
  for _, s in ipairs(Plan.Steps(planId)) do
    total = total + 1
    if Plan.IsDone(s.id) then done = done + 1 end
  end
  return done, total
end

-- The first step of the plan not ticked yet, or nil when all are done.
function Plan.Next(planId)
  for _, s in ipairs(Plan.Steps(planId)) do
    if not Plan.IsDone(s.id) then return s end
  end
end

-- The tag text shown after a step title: "[unverified: check quest]".
local TAG_NAMES = { unv = "unverified", dng = "dungeon", opt = "optional" }
function Plan.TagText(tag)
  local kind, text = tag[1], tag[2]
  local name = TAG_NAMES[kind] or kind
  if text and text ~= "" and text ~= name then return "[" .. name .. ": " .. text .. "]" end
  return "[" .. name .. "]"
end

-- ---------------------------------------------------------------------------
-- Waypoints
-- ---------------------------------------------------------------------------

-- The points of a step for a plan: its own list, else the default, else {}.
function Plan.Points(stepId, planId)
  local wp = data().waypoints[stepId]
  if not wp then return {} end
  return wp[planId] or wp.default or {}
end

-- Zone-type maps first, then dungeons, then anything else.
local TYPE_RANK = { [3] = 1, [4] = 2 }
local mapCache   -- lower-case name -> { {id =, rank =}, ... }

local function addMap(cache, info)
  if not (info and info.name and info.mapID) then return end
  local key = info.name:lower()
  cache[key] = cache[key] or {}
  table.insert(cache[key], { id = info.mapID, rank = TYPE_RANK[info.mapType] or 3 })
end

-- Walk everything under the world / continent maps once. Returns nil (and does not
-- cache) when the client has no C_Map, so a later call can try again.
local function buildMapCache()
  if not (C_Map and C_Map.GetMapChildrenInfo) then return nil end
  local cache, any = {}, false
  -- 946 = Cosmic, 947 = Azeroth, 1414 / 1415 = Kalimdor / Eastern Kingdoms: whichever the
  -- client has; allDescendants = true returns every zone below in one call.
  for _, root in ipairs({ 946, 947, 1414, 1415 }) do
    local ok, kids = pcall(C_Map.GetMapChildrenInfo, root, nil, true)
    if ok and type(kids) == "table" then
      for _, info in ipairs(kids) do
        addMap(cache, info)
        any = true
      end
    end
    if C_Map.GetMapInfo then
      local ok2, info = pcall(C_Map.GetMapInfo, root)
      if ok2 then addMap(cache, info) end
    end
  end
  if not any then return nil end
  for _, list in pairs(cache) do
    table.sort(list, function(a, b)
      if a.rank ~= b.rank then return a.rank < b.rank end
      return a.id < b.id
    end)
  end
  return cache
end

-- zone name (+ optional hint id) -> uiMapID, or nil if this client has no such map.
-- The hint wins only if the map with that id really has this name.
function Plan.ResolveMap(zone, hint)
  if not zone then return nil end
  if hint and C_Map and C_Map.GetMapInfo then
    local ok, info = pcall(C_Map.GetMapInfo, hint)
    if ok and info and info.name == zone then return hint end
  end
  mapCache = mapCache or buildMapCache()
  local list = mapCache and mapCache[zone:lower()]
  return list and list[1].id or nil
end

-- Forget the cached map list (tests; a client that loads maps late).
function Plan.ResetMapCache() mapCache = nil end

-- The /way line TomTom understands.
function Plan.WayLine(pt)
  return ("/way %s %s %s %s"):format(pt.zone, pt.x, pt.y, pt.label)
end

function Plan.HasTomTom()
  return _G.TomTom ~= nil and _G.TomTom.AddWaypoint ~= nil
end

-- A point with a position (not `check`).
function Plan.HasPosition(pt)
  return pt.conf ~= "check" and pt.x ~= nil and pt.y ~= nil
end

-- "may have moved" for positions copied from Classic or only roughly known.
function Plan.MayHaveMoved(pt)
  return pt.conf == "classic" or pt.conf == "approx"
end

-- The Waypoint button: set a TomTom waypoint, or print the /way line. Returns "tomtom",
-- "line", or nil for a point with no position.
function Plan.Waypoint(pt)
  if not Plan.HasPosition(pt) then return nil end
  local mapID = Plan.ResolveMap(pt.zone, pt.mapHint)
  if Plan.HasTomTom() and mapID then
    _G.TomTom:AddWaypoint(mapID, pt.x / 100, pt.y / 100, { title = pt.label })
    R2F.Print(L.PLAN_WAYPOINT_SET:format(pt.label))
    return "tomtom"
  end
  if Plan.HasTomTom() and not mapID then R2F.Print(L.PLAN_NO_MAP:format(pt.zone)) end
  R2F.Print(Plan.WayLine(pt))
  return "line"
end

-- /r2f here: where am I, in the numbers a `check` point needs.
function Plan.Here()
  local mapID = C_Map and C_Map.GetBestMapForUnit and C_Map.GetBestMapForUnit("player")
  if not mapID then R2F.Print(L.PLAN_HERE_NONE) return nil end
  local info = C_Map.GetMapInfo and C_Map.GetMapInfo(mapID)
  local name = info and info.name or "?"
  local pos = C_Map.GetPlayerMapPosition and C_Map.GetPlayerMapPosition(mapID, "player")
  local x, y
  if pos and pos.GetXY then x, y = pos:GetXY() end
  if not (x and y) then R2F.Print(L.PLAN_HERE_NONE) return nil end
  x, y = x * 100, y * 100
  local sub = GetSubZoneText and GetSubZoneText() or ""
  R2F.Print(L.PLAN_HERE:format(name, mapID, x, y, sub ~= "" and (" - " .. sub) or ""))
  R2F.Print(("/way %s %.1f %.1f"):format(name, x, y))
  return mapID, x, y
end
