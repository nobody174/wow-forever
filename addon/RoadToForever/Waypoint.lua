-- Waypoint.lua: where a place is on the map, and pointing our arrow at it (BiZNav).
--
-- * A point is { zone (English name), x / y in map percent, label, conf = exact | classic | approx | check, dungeon? }.
--   `check` = no position known, unless the point has `dungeon` = the dungeon's name: then the position is the
--   dungeon entrance the game's own world map shows (C_EncounterJournal.GetDungeonEntrancesForMap), looked up at
--   run time (Waypoint.EntranceFor); classic / approx = "may have moved".
-- * The zone name is turned into a uiMapID at run time (Waypoint.ResolveMap) by walking C_Map.GetMapChildrenInfo,
--   because the ids are not known for Forever's new zones.
-- * Waypoint.Go points our own arrow (Nav.lua) at it; without a map id, or on a client that can't place the map in
--   the world, it prints the "/way Zone x y label" line.
-- * /r2f here prints the zone, uiMapID and x / y you stand at.
--
-- Everything here is read-only game-wise (map getters, our own arrow frame): it works in combat.

local _, R2F = ...
local L = R2F.L

local Waypoint = {}
R2F.Waypoint = Waypoint

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
function Waypoint.ResolveMap(zone, hint)
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
function Waypoint.ResetMapCache() mapCache = nil end

-- The /way line TomTom understands.
function Waypoint.WayLine(pt)
  return ("/way %s %s %s %s"):format(pt.zone, pt.x, pt.y, pt.label)
end

-- Dungeon entrances the game's own world map knows, by lower-case name: { mapID, x, y (map percent), name }.
-- Built once from every zone map (the same call Blizzard's map pins use); an empty answer is not kept, so a client
-- that has not loaded its maps yet is asked again (at most every 30 seconds).
local entranceCache, entranceTried

local function buildEntrances()
  if not (C_EncounterJournal and C_EncounterJournal.GetDungeonEntrancesForMap) then return nil end
  mapCache = mapCache or buildMapCache()
  if not mapCache then return nil end
  local out, any = {}, false
  for _, list in pairs(mapCache) do
    for _, m in ipairs(list) do
      local ok, entrances = pcall(C_EncounterJournal.GetDungeonEntrancesForMap, m.id)
      if ok and type(entrances) == "table" then
        for _, e in ipairs(entrances) do
          local pos = e.position
          local x, y
          if type(pos) == "table" then
            if pos.GetXY then x, y = pos:GetXY() else x, y = pos.x, pos.y end
          end
          if type(e.name) == "string" and x and y then
            local key = e.name:lower()
            if not out[key] then out[key] = { mapID = m.id, x = x * 100, y = y * 100, name = e.name } end
            any = true
          end
        end
      end
    end
  end
  return any and out or nil
end

-- The game's entrance for a dungeon name (exact, else one name containing the other), or nil.
function Waypoint.EntranceFor(name)
  if type(name) ~= "string" or name == "" then return nil end
  if not entranceCache then
    local now = GetTime and GetTime() or 0
    if entranceTried and now - entranceTried < 30 then return nil end
    entranceTried = now
    entranceCache = buildEntrances()
    if not entranceCache then return nil end
  end
  local key = name:lower()
  if entranceCache[key] then return entranceCache[key] end
  for k, e in pairs(entranceCache) do
    if k:find(key, 1, true) or key:find(k, 1, true) then return e end
  end
end

function Waypoint.ResetEntrances() entranceCache, entranceTried = nil, nil end

-- Where a point is: mapID, x, y (map percent), or nil when no position is known.
local function spot(pt)
  if pt.conf ~= "check" and pt.x ~= nil and pt.y ~= nil then
    return Waypoint.ResolveMap(pt.zone, pt.mapHint), pt.x, pt.y, true
  end
  local e = pt.dungeon and Waypoint.EntranceFor(pt.dungeon)
  if e then return e.mapID, e.x, e.y, false end
end
Waypoint.Spot = spot

-- A point with a position (not `check`), or a dungeon whose entrance the game's map knows.
function Waypoint.HasPosition(pt)
  if pt.conf ~= "check" and pt.x ~= nil and pt.y ~= nil then return true end
  return pt.dungeon ~= nil and Waypoint.EntranceFor(pt.dungeon) ~= nil
end

-- "may have moved" for positions copied from Classic or only roughly known.
function Waypoint.MayHaveMoved(pt)
  return pt.conf == "classic" or pt.conf == "approx"
end

-- The Waypoint button: point our arrow (Nav.lua) at the spot, or print the /way line when
-- this game has no such map or can't place it. Returns "arrow", "line", or nil for a
-- point with no position.
function Waypoint.Go(pt)
  local mapID, x, y, explicit = spot(pt)
  if not (x and y) then return nil end
  if mapID and R2F.Nav.SetTarget(mapID, x, y, pt.label, pt.zone) then
    R2F.Print(L.NAV_SET:format(pt.label))
    return "arrow"
  end
  if not mapID then R2F.Print(L.NAV_NO_MAP:format(pt.zone)) end
  if explicit then
    R2F.Print(Waypoint.WayLine(pt))
  else
    R2F.Print(Waypoint.WayLine({ zone = pt.zone, x = ("%.1f"):format(x), y = ("%.1f"):format(y), label = pt.label }))
  end
  return "line"
end

-- /r2f here: where am I, in the numbers a `check` point needs.
function Waypoint.Here()
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
