-- Plan.lua: the Launch Plan in game. Logic only; the tab
-- is UI/Plan.lua, the data is PlanData.lua (generated from the site, see below).
--
-- * Plans: a plan id is "race:CLASS" ("skyborne:HUNTER", the Alliance races and classes of launch-plan.html) or a
--   preset id ("hunter" = 2 Hunters, Skyborne Hunter plus the duo tips). The plan is the logged-in character's own
--   race and class (UnitRace / UnitClass) unless a preview is set (R2FCharDB.plan.selected, "Preview another
--   combination"). Horde characters have no plan. The site's rules: a step with `only` is shown to those races /
--   classes only; then the layers of `ov` apply in order race, class, preset: a table replaces the fields it
--   names, `false` hides the step for good. Only the launch-day phases (night, p1, p2, p3)
--   are in the data.
-- * Ticks: R2FCharDB.plan.done[stepId] = true, per character, shared by every plan (a step keeps its tick if you
--   switch race or class, like the site).
-- * Waypoints: PlanData.waypoints[stepId] = { default = {points}, <race> = {points} }; a
--   race's own list replaces the default for that race. A point has zone (English name),
--   x / y in map percent, label and conf: exact | classic | approx | check. `check` = no
--   position known yet (label only, no button), unless the point has `dungeon` = the dungeon's name: then
--   the position is the dungeon entrance the game's own world map shows (C_EncounterJournal.GetDungeonEntrancesForMap,
--   what Leatrix Maps draws), looked up at run time (Plan.EntranceFor); classic / approx = "may have moved".
--   The zone name is turned into a uiMapID at run time (Plan.ResolveMap) by walking
--   C_Map.GetMapChildrenInfo, because the ids are not known for Forever's new zones.
--   The button points our own arrow (Nav.lua, BiZNav) at it; without a map id, or on a
--   client that can't place the map in the world, it prints the "/way Zone x y label" line.
-- * /r2f here prints the zone, uiMapID and x / y you stand at, so a `check` point can be
--   filled in from the game.
--
-- Everything here is read-only game-wise (map getters, our own arrow frame): it works in combat.

local _, R2F = ...
local L = R2F.L

local Plan = {}
R2F.Plan = Plan

local function data() return R2F.PlanData end
local function cdb() return R2F.Library.cdb.plan end

-- ---------------------------------------------------------------------------
-- Plans and steps
-- ---------------------------------------------------------------------------

local function contains(list, v)
  for _, x in ipairs(list) do
    if x == v then return true end
  end
  return false
end

-- { race =, cls =, preset = } for a plan id, or nil when the id is not a valid combination.
function Plan.Parse(planId)
  local d = data()
  if type(planId) ~= "string" then return nil end
  local pr = d.presets[planId]
  if pr then return { race = pr.race, cls = pr.cls, preset = planId } end
  local race, cls = planId:match("^(%a+):(%u+)$")
  local def = race and d.races[race]
  if def and contains(def.classes, cls) then return { race = race, cls = cls } end
  return nil
end

function Plan.Id(sel)
  return sel.preset or (sel.race .. ":" .. sel.cls)
end

-- Does the selection pass the step's `only` filter? (Site: allowed().)
local function allowed(item, sel)
  local o = item.only
  if not o then return true end
  if o.race and not contains(o.race, sel.race) then return false end
  if o.cls and not contains(o.cls, sel.cls) then return false end
  return true
end

-- The override layers that apply, in order: race, class, preset. (Site: override().)
local function layers(item, sel)
  local out = {}
  local ov = item.ov
  if not ov then return out end
  if ov.race and ov.race[sel.race] ~= nil then out[#out + 1] = ov.race[sel.race] end
  if ov.cls and ov.cls[sel.cls] ~= nil then out[#out + 1] = ov.cls[sel.cls] end
  if sel.preset and ov.preset and ov.preset[sel.preset] ~= nil then out[#out + 1] = ov.preset[sel.preset] end
  return out
end
Plan.Layers = layers

-- One item for one plan: nil if hidden, else a new table with the merged fields. (Site: resolve().)
function Plan.Resolve(item, planId)
  local sel = type(planId) == "table" and planId or Plan.Parse(planId)
  if not sel or not allowed(item, sel) then return nil end
  local out = { id = item.id, lvl = item.lvl, t = item.t, n = item.n, tags = item.tags or {},
                quests = item.quests, reach = item.reach }
  for _, o in ipairs(layers(item, sel)) do
    if o == false then return nil end
    for k, v in pairs(o) do out[k] = v end
  end
  out.tags = out.tags or {}
  return out
end

-- Race ids in the site's order, the classes one race can be (class order), and the presets.
function Plan.Races() return data().raceOrder end
function Plan.Classes(race)
  local def = data().races[race]
  return def and def.classes or {}
end
function Plan.RaceLabel(race)
  local def = data().races[race]
  return def and (def.label:gsub("%s*%b()", "")) or tostring(race)
end
function Plan.ClassLabel(cls)
  local def = data().classes[cls]
  return def and def.label or tostring(cls)
end
function Plan.Presets() return data().presets end

-- "Alliance Skyborne Hunter", or the preset's label.
function Plan.Label(planId)
  local sel = Plan.Parse(planId)
  if not sel then return tostring(planId) end
  if sel.preset then return data().presets[sel.preset].label end
  return "Alliance " .. Plan.RaceLabel(sel.race) .. " " .. Plan.ClassLabel(sel.cls)
end

-- { { id =, title =, steps = { resolved item, ... } }, ... } for one plan; phases with
-- no step for the plan are left out.
function Plan.Phases(planId)
  local out = {}
  local sel = Plan.Parse(planId)
  if not sel then return out end
  for _, ph in ipairs(data().phases) do
    local steps = {}
    for _, item in ipairs(ph.items) do
      local r = Plan.Resolve(item, sel)
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

-- The character's race id from UnitRace's English name ("NightElf" / "Night Elf" -> "nightelf"); Skyborne's own
-- English name is not known for sure, so anything naming Skyborne or the High Order counts. nil for other races.
function Plan.RaceId(english)
  local k = tostring(english or ""):lower():gsub("[^%a]", "")
  if k:find("skyborne", 1, true) or k:find("highorder", 1, true) then return "skyborne" end
  if data().races[k] then return k end
  return nil
end

-- The plan for the logged-in character (its race and class), or nil: Horde, or a race / class the plan does not cover.
function Plan.OwnPlan()
  if UnitFactionGroup and UnitFactionGroup("player") == "Horde" then return nil end
  local race = UnitRace and Plan.RaceId(select(2, UnitRace("player")))
  local cls = R2F.playerClass or (UnitClass and select(2, UnitClass("player")))
  if not (race and cls) then return nil end
  local id = race .. ":" .. cls
  return Plan.Parse(id) and id or nil
end

-- The preview the player picked ("Preview another combination"), or nil.
function Plan.Preview()
  local id = cdb().selected
  return Plan.Parse(id) and id or nil
end

-- Set (or, with nil, clear) the preview. Returns false for an id that is not a valid plan.
function Plan.SetPreview(planId)
  if planId == nil then
    cdb().selected = nil
    return true
  end
  if not Plan.Parse(planId) then return false end
  cdb().selected = planId
  return true
end

Plan.DEFAULT = "skyborne:HUNTER"

local function indexOf(list, v)
  for i, x in ipairs(list) do
    if x == v then return i end
  end
  return 1
end

-- The next race in the site's order, keeping the class when this race can be it (else its first class). Returns a plan id.
-- (Buttons of the preview control; `planId` may be nil or a preset.)
function Plan.CycleRace(planId)
  local sel = Plan.Parse(planId) or Plan.Parse(Plan.DEFAULT)
  local order = data().raceOrder
  local race = order[indexOf(order, sel.race) % #order + 1]
  local classes = Plan.Classes(race)
  return race .. ":" .. (contains(classes, sel.cls) and sel.cls or classes[1])
end

-- The next class this race can be.
function Plan.CycleClass(planId)
  local sel = Plan.Parse(planId) or Plan.Parse(Plan.DEFAULT)
  local classes = Plan.Classes(sel.race)
  return sel.race .. ":" .. classes[indexOf(classes, sel.cls) % #classes + 1]
end

-- Switch the preset (2 Hunters) on, or off again (back to its race and class).
function Plan.TogglePreset(planId)
  local sel = Plan.Parse(planId) or Plan.Parse(Plan.DEFAULT)
  if sel.preset then return sel.race .. ":" .. sel.cls end
  local id = next(data().presets)
  return id
end

-- The plan shown: the preview if set, else the character's own; nil when there is none (a Horde character).
function Plan.Selected()
  return Plan.Preview() or Plan.OwnPlan()
end

function Plan.IsDone(stepId)
  return cdb().done[stepId] == true
end

-- ---------------------------------------------------------------------------
-- Quest shopping list (the site's "Buyable quests"): quests whose objectives can be bought on the
-- auction house or from a vendor instead of farmed. Ticks are per character, like the steps.
-- ---------------------------------------------------------------------------

-- { { id =, title =, quests = { { id, name, zone, q, st, items = { { name, count } }, note, xp }, ... } }, ... }
-- in the site's route order; phases with no quest are left out.
function Plan.QuestGroups()
  local qd = data().quests
  local out = {}
  if not qd then return out end
  for _, ph in ipairs(qd.phases) do
    local list = {}
    for _, q in ipairs(qd.list) do
      if q.phase == ph.id then list[#list + 1] = q end
    end
    if #list > 0 then out[#out + 1] = { id = ph.id, title = ph.title, quests = list } end
  end
  return out
end

function Plan.QuestBought(id)
  return cdb().bought[id] == true
end

function Plan.SetQuestBought(id, done)
  cdb().bought[id] = done and true or nil
end

-- bought, total of the quests on our route (the "off our route" group is for reference only).
function Plan.QuestProgress()
  local done, total = 0, 0
  for _, g in ipairs(Plan.QuestGroups()) do
    if g.id ~= "off" then
      for _, q in ipairs(g.quests) do
        total = total + 1
        if Plan.QuestBought(q.id) then done = done + 1 end
      end
    end
  end
  return done, total
end

-- ---------------------------------------------------------------------------
-- Follow the plan (Plan tab switch, off by default; R2FCharDB.plan.follow): a step ticks itself when all its
-- `quests` are turned in, or when your level reaches its `reach`. Only steps with quests or a reach do this; the
-- others stay manual. It only ever ticks: a manual tick is never undone, and a step you untick by hand is left alone
-- afterwards (R2FCharDB.plan.noauto) until you tick it again yourself.
-- Read-only on the game's side: quest flags, UnitLevel and the QUEST_TURNED_IN / PLAYER_LEVEL_UP events.
-- ---------------------------------------------------------------------------
local turned = {}   -- quest ids turned in this session (the quest flag can lag behind QUEST_TURNED_IN)

local function questDone(id)
  if turned[id] then return true end
  local flagged
  if C_QuestLog and C_QuestLog.IsQuestFlaggedCompleted then flagged = C_QuestLog.IsQuestFlaggedCompleted(id)
  elseif IsQuestFlaggedCompleted then flagged = IsQuestFlaggedCompleted(id) end
  return flagged == true
end

function Plan.FollowOn() return cdb().follow == true end

-- Is the step finished by the game's own state (quests turned in, or the level reached)?
function Plan.StepReached(step, level)
  if step.quests and #step.quests > 0 then
    local all = true
    for _, id in ipairs(step.quests) do
      if not questDone(id) then all = false break end
    end
    if all then return true end
  end
  return step.reach ~= nil and (level or 0) >= step.reach
end

-- Tick every step of the character's own plan that the game says is done. Returns how many it ticked.
function Plan.AutoTick(level)
  if not Plan.FollowOn() then return 0 end
  local planId = Plan.OwnPlan()
  if not planId then return 0 end
  level = level or (UnitLevel and UnitLevel("player")) or 0
  local n = 0
  for _, s in ipairs(Plan.Steps(planId)) do
    if not Plan.IsDone(s.id) and not cdb().noauto[s.id] and Plan.StepReached(s, level) then
      Plan.SetDone(s.id, true)
      n = n + 1
    end
  end
  if n > 0 then
    if R2F.PlanTab and R2F.PlanTab.Refresh then R2F.PlanTab.Refresh() end
    if R2F.Home and R2F.Home.Refresh then R2F.Home.Refresh() end
  end
  return n
end

function Plan.SetFollow(on)
  cdb().follow = on and true or false
  if on then Plan.AutoTick() end
end

function Plan.OnQuestTurnedIn(id)
  if type(id) == "number" then turned[id] = true end
  Plan.AutoTick()
end

function Plan.OnLevelUp(level)
  Plan.AutoTick(tonumber(level))
end

-- The step whose Waypoint button last pointed the arrow (so ticking it moves the arrow on).
local arrowStep

function Plan.SetDone(stepId, done)
  -- Was this the step you were on (the first one not ticked), or the one the arrow points from?
  local cur = done and Plan.Next(Plan.Selected())
  local onIt = done and ((cur and cur.id == stepId) or arrowStep == stepId)
  cdb().done[stepId] = done and true or nil
  cdb().noauto[stepId] = (not done) and true or nil   -- unticked by hand: Follow the plan leaves it alone
  if onIt and R2F.Gameplay and R2F.Gameplay.IsOn("navfollow") and R2F.Nav and R2F.Nav.Supported() then
    Plan.AdvanceArrow()
  end
end

-- Point the arrow at the first step not ticked yet that has a known position. Returns true when it did.
-- A step with no known position is passed over; if nothing is left the arrow is cleared.
function Plan.AdvanceArrow()
  local planId = Plan.Selected()
  for _, s in ipairs(Plan.Steps(planId)) do
    if not Plan.IsDone(s.id) then
      for _, pt in ipairs(Plan.Points(s.id, planId)) do
        if Plan.HasPosition(pt) then
          R2F.Print(L.NAV_NEXT_STEP:format(s.t or pt.label))
          return Plan.Waypoint(pt, s.id) == "arrow"
        end
      end
    end
  end
  if R2F.Nav.Target() then R2F.Nav.Clear() end
  return false
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

-- The points of a step for a plan: its race's own list, else the default, else {}.
function Plan.Points(stepId, planId)
  local wp = data().waypoints[stepId]
  local sel = Plan.Parse(planId)
  if not (wp and sel) then return {} end
  return wp[sel.race] or wp.default or {}
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
function Plan.EntranceFor(name)
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

function Plan.ResetEntrances() entranceCache, entranceTried = nil, nil end

-- Where a point is: mapID, x, y (map percent), or nil when no position is known.
local function spot(pt)
  if pt.conf ~= "check" and pt.x ~= nil and pt.y ~= nil then
    return Plan.ResolveMap(pt.zone, pt.mapHint), pt.x, pt.y, true
  end
  local e = pt.dungeon and Plan.EntranceFor(pt.dungeon)
  if e then return e.mapID, e.x, e.y, false end
end
Plan.Spot = spot

-- A point with a position (not `check`), or a dungeon whose entrance the game's map knows.
function Plan.HasPosition(pt)
  if pt.conf ~= "check" and pt.x ~= nil and pt.y ~= nil then return true end
  return pt.dungeon ~= nil and Plan.EntranceFor(pt.dungeon) ~= nil
end

-- "may have moved" for positions copied from Classic or only roughly known.
function Plan.MayHaveMoved(pt)
  return pt.conf == "classic" or pt.conf == "approx"
end

-- The Waypoint button: point our arrow (Nav.lua) at the spot, or print the /way line when
-- this game has no such map or can't place it. Returns "arrow", "line", or nil for a
-- point with no position.
function Plan.Waypoint(pt, stepId)
  local mapID, x, y, explicit = spot(pt)
  if not (x and y) then return nil end
  if mapID and R2F.Nav.SetTarget(mapID, x, y, pt.label, pt.zone) then
    arrowStep = stepId
    R2F.Print(L.NAV_SET:format(pt.label))
    return "arrow"
  end
  if not mapID then R2F.Print(L.NAV_NO_MAP:format(pt.zone)) end
  if explicit then
    R2F.Print(Plan.WayLine(pt))
  else
    R2F.Print(Plan.WayLine({ zone = pt.zone, x = ("%.1f"):format(x), y = ("%.1f"):format(y), label = pt.label }))
  end
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

-- Tweaks > Waypoint arrow: "Arrow follows the plan". Ticking the step you are on points the arrow at the next one.
-- On by default (Library.lua), because it only ever acts on your own tick.
R2F.Gameplay.Register({ key = "navfollow", group = "screen", title = "NAV_FOLLOW", tip = "NAV_FOLLOW_TIP" })
