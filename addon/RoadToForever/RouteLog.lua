-- RouteLog.lua: writes down the route you walk, so a launch route can be worked out from real play.
--
-- It is OFF until you type /r2f route start. While it records it keeps, in our own SavedVariables (R2FDB.route) and nowhere
-- else, a timeline of what the game tells the addon anyway:
--   * quests: offered (who, where), accepted (quest level, objectives), objective progress (where you were when a kill or an item
--     counted), handed in (xp, money), abandoned
--   * levels and zones, the NPCs you open a window with (quest giver, trainer, vendor, flight master, innkeeper), deaths
--   * your own notes (/r2f route note <text>)
--   * a position every few seconds (the path you walked)
-- Every record carries the time since the start, your level and xp, and the map position. No character name is stored, only
-- class and race. Read-only: only the game's getters, called in event handlers; nothing is sent anywhere.
-- addon/tools/route_report.py turns the SavedVariables file into a readable timeline and a quest table.
--
-- Shape of R2FDB.route:  { version, runs = { run, ... }, active = index of the run being written or nil }
--   run = { label, started (server time), class, race, level, events = { ev, ... }, trail = { { t, mapID, x, y }, ... } }
--   ev  = { e = kind, t = seconds since the start, lv, xp, m = mapID, x, y (map percent), z, sz, ... kind fields }

local _, R2F = ...
local L = R2F.L

local Route = {}
R2F.RouteLog = Route

local MAX_EVENTS = 6000
local MAX_TRAIL = 4000
local TRAIL_EVERY = 10          -- seconds between two path points
local PROGRESS_THROTTLE = 0.4   -- seconds between two objective checks

local active                    -- the run being written (nil when off)
local gen = 0                   -- bumped on start / stop so an old timer chain ends
local lastCheck = 0
local lastZone
local objectiveState = {}       -- questId -> { [index] = numFulfilled }
local turnedIn = {}             -- questId -> time it was handed in
local seenNpc = {}              -- "kind:id" -> true (once per run)
local offered = {}              -- questId -> true (once per run)

local function isSecret(v)
  return type(_G.issecretvalue) == "function" and _G.issecretvalue(v) == true
end

local function clean(v)
  if type(v) == "string" and not isSecret(v) and v ~= "" then return v end
  return nil
end

local function now()
  return (_G.GetServerTime and _G.GetServerTime()) or (_G.time and _G.time()) or 0
end

local function store()
  return R2F.Library.db.route
end

-- mapID, x, y (map percent with one decimal), nil where the game gives no position.
local function pos()
  if not (_G.C_Map and _G.C_Map.GetBestMapForUnit and _G.C_Map.GetPlayerMapPosition) then return nil end
  local ok, m, x, y = pcall(function()
    local map = _G.C_Map.GetBestMapForUnit("player")
    if not map then return nil end
    local p = _G.C_Map.GetPlayerMapPosition(map, "player")
    if not (p and p.GetXY) then return nil end
    local px, py = p:GetXY()
    return map, px, py
  end)
  if not ok or not m or type(x) ~= "number" or type(y) ~= "number" or isSecret(x) or (x == 0 and y == 0) then return nil end
  return m, math.floor(x * 1000 + 0.5) / 10, math.floor(y * 1000 + 0.5) / 10
end

local function push(kind, fields)
  if not active or #active.events >= MAX_EVENTS then return nil end
  local ev = fields or {}
  ev.e = kind
  ev.t = now() - active.started
  if _G.UnitLevel then
    local lv = _G.UnitLevel("player")
    if type(lv) == "number" and not isSecret(lv) then ev.lv = lv end
  end
  if _G.UnitXP then
    local xp = _G.UnitXP("player")
    if type(xp) == "number" and not isSecret(xp) then ev.xp = xp end
  end
  local m, x, y = pos()
  if m then ev.m, ev.x, ev.y = m, x, y end
  active.events[#active.events + 1] = ev
  return ev
end

-- The NPC behind an open window: id and name, from the unit token the game uses for it.
local function npcOf(...)
  for _, unit in ipairs({ ... }) do
    local guid = _G.UnitGUID and _G.UnitGUID(unit)
    if type(guid) == "string" and not isSecret(guid) then
      local id = guid:match("^%a+%-%d+%-%d+%-%d+%-%d+%-(%d+)")
      if id then return tonumber(id), clean(_G.UnitName and _G.UnitName(unit)) end
    end
  end
  return nil
end

local function questTitle(qid)
  local ql = _G.C_QuestLog
  if ql and ql.GetTitleForQuestID then
    local ok, t = pcall(ql.GetTitleForQuestID, qid)
    if ok then return clean(t) end
  end
  return nil
end

-- Quest level and suggested group size from the quest log entry, when it can be read.
local function questLevel(qid)
  local ql = _G.C_QuestLog
  if not (ql and ql.GetLogIndexForQuestID and ql.GetInfo) then return nil end
  local ok, idx = pcall(ql.GetLogIndexForQuestID, qid)
  if not (ok and idx) then return nil end
  local ok2, info = pcall(ql.GetInfo, idx)
  if not (ok2 and type(info) == "table") then return nil end
  return info.level, info.suggestedGroup, clean(info.title)
end

-- { { text, have, need }, ... } of a quest's objectives.
local function objectives(qid)
  local ql = _G.C_QuestLog
  if not (ql and ql.GetQuestObjectives) then return nil end
  local ok, list = pcall(ql.GetQuestObjectives, qid)
  if not (ok and type(list) == "table") then return nil end
  local out = {}
  for i, o in ipairs(list) do
    out[i] = { clean(o.text) or "?", tonumber(o.numFulfilled) or 0, tonumber(o.numRequired) or 0 }
  end
  return out
end

-- Every quest in the log: { questId, ... } (headers skipped).
local function logQuests()
  local out = {}
  local ql = _G.C_QuestLog
  if not (ql and ql.GetNumQuestLogEntries and ql.GetInfo) then return out end
  local ok, n = pcall(ql.GetNumQuestLogEntries)
  if not ok then return out end
  for i = 1, tonumber(n) or 0 do
    local ok2, info = pcall(ql.GetInfo, i)
    if ok2 and type(info) == "table" and not info.isHeader and info.questID then out[#out + 1] = info.questID end
  end
  return out
end

local function rememberObjectives(qid)
  local list = objectives(qid)
  if not list then return end
  local st = {}
  for i, o in ipairs(list) do st[i] = o[2] end
  objectiveState[qid] = st
end

-- The quest log changed: log every objective whose count went up, with where you stood.
local function checkProgress()
  for _, qid in ipairs(logQuests()) do
    local list = objectives(qid)
    if list then
      local st = objectiveState[qid] or {}
      for i, o in ipairs(list) do
        if st[i] ~= nil and o[2] > st[i] then
          push("prog", { q = qid, o = i, tx = o[1], n = o[2], of = o[3] })
        end
        st[i] = o[2]
      end
      objectiveState[qid] = st
    end
  end
end

local function trailTick(g)
  if g ~= gen or not active then return end
  local m, x, y = pos()
  if m and #active.trail < MAX_TRAIL then
    active.trail[#active.trail + 1] = { now() - active.started, m, x, y }
  end
  if _G.C_Timer and _G.C_Timer.After then _G.C_Timer.After(TRAIL_EVERY, function() trailTick(g) end) end
end

local function npcEvent(kind, ...)
  local id, name = npcOf(...)
  if not id then return end
  local key = kind .. ":" .. id
  if seenNpc[key] then return end
  seenNpc[key] = true
  push("npc", { kind = kind, id = id, name = name, sz = clean(_G.GetSubZoneText and _G.GetSubZoneText()) })
end

-- One game event (called by the event frame; tests call it directly).
function Route.OnEvent(event, a, b, c)
  if not active then return end
  if event == "QUEST_DETAIL" then
    local qid = _G.GetQuestID and _G.GetQuestID()
    if type(qid) == "number" and qid > 0 and not offered[qid] then
      offered[qid] = true
      local id, name = npcOf("questnpc", "npc", "target")
      push("offer", { q = qid, title = clean(_G.GetTitleText and _G.GetTitleText()), npc = id, npcName = name,
                      sz = clean(_G.GetSubZoneText and _G.GetSubZoneText()) })
    end
  elseif event == "QUEST_ACCEPTED" then
    local qid = b or a      -- Classic gives (logIndex, questID), the newer clients just the id
    if type(qid) ~= "number" then return end
    local lvl, group, title = questLevel(qid)
    push("accept", { q = qid, title = title or questTitle(qid), ql = lvl, grp = group, obj = objectives(qid) })
    rememberObjectives(qid)
  elseif event == "QUEST_COMPLETE" then
    local qid = _G.GetQuestID and _G.GetQuestID()
    if type(qid) == "number" and qid > 0 then
      local id, name = npcOf("questnpc", "npc", "target")
      push("handin", { q = qid, title = clean(_G.GetTitleText and _G.GetTitleText()), npc = id, npcName = name })
    end
  elseif event == "QUEST_TURNED_IN" then
    if type(a) ~= "number" then return end
    turnedIn[a] = now()
    objectiveState[a] = nil
    push("done", { q = a, xpGain = tonumber(b), copper = tonumber(c) })
  elseif event == "QUEST_REMOVED" then
    if type(a) ~= "number" then return end
    local when = turnedIn[a]
    objectiveState[a] = nil
    if not (when and now() - when <= 5) then push("drop", { q = a, title = questTitle(a) }) end
  elseif event == "QUEST_LOG_UPDATE" then
    local t = _G.GetTime and _G.GetTime() or 0
    if t - lastCheck < PROGRESS_THROTTLE then return end
    lastCheck = t
    checkProgress()
  elseif event == "PLAYER_LEVEL_UP" then
    push("level", { to = tonumber(a) })
  elseif event == "PLAYER_DEAD" then
    push("dead", { sz = clean(_G.GetSubZoneText and _G.GetSubZoneText()) })
  elseif event == "ZONE_CHANGED_NEW_AREA" or event == "ZONE_CHANGED" or event == "ZONE_CHANGED_INDOORS" then
    local z = clean(_G.GetZoneText and _G.GetZoneText())
    local sz = clean(_G.GetSubZoneText and _G.GetSubZoneText())
    local key = tostring(z) .. "/" .. tostring(sz)
    if key ~= lastZone then
      lastZone = key
      push("zone", { z = z, sz = sz })
    end
  elseif event == "GOSSIP_SHOW" then
    npcEvent("gossip", "npc", "target")
  elseif event == "TRAINER_SHOW" then
    npcEvent("trainer", "npc", "target")
  elseif event == "MERCHANT_SHOW" then
    npcEvent("vendor", "npc", "target")
  elseif event == "TAXIMAP_OPENED" then
    npcEvent("flight", "npc", "target")
  elseif event == "CONFIRM_BINDER" then
    push("bind", { sz = clean(_G.GetSubZoneText and _G.GetSubZoneText()) })
  end
end

local EVENTS = { "QUEST_DETAIL", "QUEST_ACCEPTED", "QUEST_COMPLETE", "QUEST_TURNED_IN", "QUEST_REMOVED", "QUEST_LOG_UPDATE",
                 "PLAYER_LEVEL_UP", "PLAYER_DEAD", "ZONE_CHANGED_NEW_AREA", "ZONE_CHANGED", "ZONE_CHANGED_INDOORS",
                 "GOSSIP_SHOW", "TRAINER_SHOW", "MERCHANT_SHOW", "TAXIMAP_OPENED", "CONFIRM_BINDER" }

local function begin(run)
  active = run
  gen = gen + 1
  objectiveState, turnedIn, seenNpc, offered = {}, {}, {}, {}
  lastZone = nil
  for _, qid in ipairs(logQuests()) do rememberObjectives(qid) end
  trailTick(gen)
end

function Route.IsOn() return active ~= nil end

-- /r2f route start [name]
function Route.Start(label)
  if active then return R2F.Print(L.ROUTE_ALREADY) end
  local s = store()
  local run = { v = 1, label = clean(label), started = now(), events = {}, trail = {} }
  if _G.UnitClass then run.class = select(2, _G.UnitClass("player")) end
  if _G.UnitRace then run.race = select(2, _G.UnitRace("player")) end
  if _G.UnitLevel then run.level = _G.UnitLevel("player") end
  s.runs[#s.runs + 1] = run
  s.active = #s.runs
  begin(run)
  push("start", { z = clean(_G.GetZoneText and _G.GetZoneText()), sz = clean(_G.GetSubZoneText and _G.GetSubZoneText()) })
  -- Quests already in the log when the run starts.
  for _, qid in ipairs(logQuests()) do
    local lvl = questLevel(qid)
    push("have", { q = qid, title = questTitle(qid), ql = lvl, obj = objectives(qid) })
  end
  R2F.Print(L.ROUTE_STARTED:format(s.active))
end

function Route.Stop()
  if not active then return R2F.Print(L.ROUTE_NOT_ON) end
  local run = active
  push("stop")
  active = nil
  gen = gen + 1
  store().active = nil
  R2F.Print(L.ROUTE_STOPPED:format(#run.events, #run.trail))
end

function Route.Note(text)
  if not active then return R2F.Print(L.ROUTE_NOT_ON) end
  text = clean(text)
  if not text then return R2F.Print(L.ROUTE_NOTE_USAGE) end
  push("note", { tx = text, sz = clean(_G.GetSubZoneText and _G.GetSubZoneText()) })
  R2F.Print(L.ROUTE_NOTED)
end

function Route.Status()
  local s = store()
  if active then
    R2F.Print(L.ROUTE_STATUS_ON:format(s.active or 0, #active.events, #active.trail, #s.runs))
  else
    R2F.Print(L.ROUTE_STATUS_OFF:format(#s.runs))
  end
end

-- /r2f route [start [name] | stop | note <text> | status]
function Route.Command(rest)
  rest = rest or ""
  local word, arg = rest:match("^(%S*)%s*(.-)%s*$")
  word = (word or ""):lower()
  if word == "start" then Route.Start(arg)
  elseif word == "stop" then Route.Stop()
  elseif word == "note" then Route.Note(arg)
  else Route.Status() end
end

-- PLAYER_LOGIN (Core.lua): a run that was on when you logged out goes on.
function Route.Init()
  local s = store()
  local run = s and s.active and s.runs[s.active]
  if run then
    begin(run)
    push("login", { z = clean(_G.GetZoneText and _G.GetZoneText()) })
    R2F.Print(L.ROUTE_RESUMED:format(s.active, #run.events))
  end
  local ev = _G.CreateFrame("Frame")
  ev:SetScript("OnEvent", function(_, event, a, b, c)
    local ok = pcall(Route.OnEvent, event, a, b, c)
    if not ok then return end               -- a recording problem must never reach the player
  end)
  for _, e in ipairs(EVENTS) do pcall(ev.RegisterEvent, ev, e) end
end
