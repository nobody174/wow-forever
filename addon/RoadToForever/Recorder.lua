-- Recorder.lua: writes down what you SEE while you play, so Mr.BiZ can learn where items come from.
--
-- Where Forever-new items drop, who sells them and which quests give them is not in the game's files (the servers hold it),
-- so the
-- only way to know is to record it. This listens to three windows the game opens anyway and keeps counts in our own
-- SavedVariables (R2FDB.recorder), nothing else:
--   * the loot window: which item came from which creature or object (by id), how many corpses of that id were looted
--   * a vendor window: what the vendor sells and for how much
--   * a quest window: which items the quest offers as rewards / choices
-- Read-only: only the game's getters, called in the event handlers; nothing is written into game tables or sent anywhere.
-- Off with "/r2f record off". "/r2f debug recorder" prints the counts. A script (bis/tools/recorder_import.py) merges the
-- SavedVariables files of everyone in the group into the item database.
--
-- Shape of R2FDB.recorder:
--   on, since, version
--   drops   = { [npcId] = { k = corpses looted, z = zone, lv = level or nil, i = { [itemId] = times seen } } }
--   objects = { [objectId] = { k, z, i } }                       -- chests, nodes
--   vendors = { [npcId] = { z, i = { [itemId] = { p = copper price, q = stack, e = 1 if it costs more than gold } } } }
--   quests  = { [questId] = { t = title, n = npc id, z = zone, c = { choice item ids }, r = { reward item ids } } }

local _, R2F = ...
local L = R2F.L

local Rec = {}
R2F.Recorder = Rec

Rec.VERSION = 1
local MAX_NPCS = 6000            -- a safety cap per table; a few thousand creatures is already a whole level range

local seenGuids = {}             -- corpses counted this session (a corpse reopened is one kill)
local seenCount = 0

local function isSecret(v)
  return type(_G.issecretvalue) == "function" and _G.issecretvalue(v) == true
end

local function db()
  return R2F.Library.db.recorder
end

local function count(t)
  local n = 0
  for _ in pairs(t) do n = n + 1 end
  return n
end

-- "Creature-0-1465-0-4-6168-000012AB34" -> "Creature", 6168. Nil for anything else (players, items, pets of players).
function Rec.ParseGuid(guid)
  if type(guid) ~= "string" or isSecret(guid) then return nil end
  local kind, id = guid:match("^(%a+)%-%d+%-%d+%-%d+%-%d+%-(%d+)")
  if not kind then return nil end
  if kind == "Vehicle" then kind = "Creature" end
  if kind ~= "Creature" and kind ~= "GameObject" then return nil end
  return kind, tonumber(id)
end

local function itemId(link)
  if type(link) ~= "string" or isSecret(link) then return nil end
  local id = link:match("item:(%d+)")
  return id and tonumber(id) or nil
end

local function zone()
  local ok, z = pcall(function() return _G.GetRealZoneText and _G.GetRealZoneText() end)
  if ok and type(z) == "string" and z ~= "" and not isSecret(z) then return z end
  return nil
end

local function add(t, key)
  if t[key] then return t[key] end
  if count(t) >= MAX_NPCS then return nil end
  t[key] = {}
  return t[key]
end

-- The loot window. Every slot lists the corpse(s) it came from; a corpse is counted once per session.
function Rec.OnLoot()
  local d = db()
  if not (d and d.on) or not _G.GetNumLootItems then return end
  local z = zone()
  local counted = {}
  for slot = 1, _G.GetNumLootItems() do
    local id = itemId(_G.GetLootSlotLink and _G.GetLootSlotLink(slot))
    if id and _G.GetLootSourceInfo then
      local info = { _G.GetLootSourceInfo(slot) }
      for k = 1, #info, 2 do
        local kind, sid = Rec.ParseGuid(info[k])
        if kind then
          local tbl = kind == "Creature" and d.drops or d.objects
          local rec = add(tbl, sid)
          if rec then
            rec.i = rec.i or {}
            rec.z = rec.z or z
            rec.i[id] = (rec.i[id] or 0) + 1
            if not counted[info[k]] then
              counted[info[k]] = true
              if not seenGuids[info[k]] then
                seenGuids[info[k]] = true
                seenCount = seenCount + 1
                rec.k = (rec.k or 0) + 1
                if kind == "Creature" and _G.UnitGUID and _G.UnitGUID("target") == info[k] and _G.UnitLevel then
                  local lv = _G.UnitLevel("target")
                  if type(lv) == "number" and not isSecret(lv) and lv > 0 then rec.lv = lv end
                end
              end
            end
          end
        end
      end
    end
  end
  if seenCount > 3000 then seenGuids, seenCount = {}, 0 end
end

-- A vendor window: what is for sale and at what price.
function Rec.OnMerchant()
  local d = db()
  if not (d and d.on) or not _G.GetMerchantNumItems then return end
  local guid = _G.UnitGUID and (_G.UnitGUID("npc") or _G.UnitGUID("target"))
  local kind, npc = Rec.ParseGuid(guid)
  if kind ~= "Creature" then return end
  local rec = add(d.vendors, npc)
  if not rec then return end
  rec.i = rec.i or {}
  rec.z = rec.z or zone()
  for index = 1, _G.GetMerchantNumItems() do
    local id = itemId(_G.GetMerchantItemLink and _G.GetMerchantItemLink(index))
    if id then
      local price, stack, ext = 0, 1, false
      if _G.GetMerchantItemInfo then
        local _, _, p, q, _, _, e = _G.GetMerchantItemInfo(index)
        price, stack, ext = tonumber(p) or 0, tonumber(q) or 1, e and true or false
      end
      rec.i[id] = { p = price, q = stack, e = ext and 1 or nil }
    end
  end
end

-- A quest window (offer or hand-in): its reward and choice items. Item links can be empty for a moment while the game loads
-- the items, so one retry follows.
function Rec.OnQuest(retry)
  local d = db()
  if not (d and d.on) or not _G.GetQuestID then return end
  local qid = _G.GetQuestID()
  if type(qid) ~= "number" or qid <= 0 or isSecret(qid) then return end
  local choices, rewards = {}, {}
  for i = 1, (_G.GetNumQuestChoices and _G.GetNumQuestChoices() or 0) do
    local id = itemId(_G.GetQuestItemLink and _G.GetQuestItemLink("choice", i))
    if id then choices[#choices + 1] = id end
  end
  for i = 1, (_G.GetNumQuestRewards and _G.GetNumQuestRewards() or 0) do
    local id = itemId(_G.GetQuestItemLink and _G.GetQuestItemLink("reward", i))
    if id then rewards[#rewards + 1] = id end
  end
  local wanted = (_G.GetNumQuestChoices and _G.GetNumQuestChoices() or 0)
    + (_G.GetNumQuestRewards and _G.GetNumQuestRewards() or 0)
  if #choices + #rewards < wanted and not retry and _G.C_Timer and _G.C_Timer.After then
    _G.C_Timer.After(0.7, function() Rec.OnQuest(true) end)
    return
  end
  if #choices + #rewards == 0 then return end
  local rec = add(d.quests, qid)
  if not rec then return end
  local kind, npc = Rec.ParseGuid(_G.UnitGUID and (_G.UnitGUID("questnpc") or _G.UnitGUID("npc")))
  local title = _G.GetTitleText and _G.GetTitleText()
  rec.t = (type(title) == "string" and not isSecret(title)) and title or rec.t
  rec.n = (kind == "Creature" and npc) or rec.n
  rec.z = rec.z or zone()
  rec.c, rec.r = choices, rewards
end

-- /r2f debug recorder
function Rec.Debug()
  local d = db()
  local drops, items = 0, 0
  for _, r in pairs(d.drops) do
    for _ in pairs(r.i or {}) do drops = drops + 1 end
  end
  for _, r in pairs(d.vendors) do
    for _ in pairs(r.i or {}) do items = items + 1 end
  end
  R2F.Print(L.REC_DEBUG:format(d.on and L.REC_ON or L.REC_OFF, count(d.drops), drops, count(d.objects), count(d.vendors), items,
    count(d.quests)))
end

function Rec.SetOn(on)
  db().on = on and true or false
  R2F.Print(db().on and L.REC_NOW_ON or L.REC_NOW_OFF)
end

-- PLAYER_LOGIN (Core.lua).
function Rec.Init()
  local ev = CreateFrame("Frame")
  ev:SetScript("OnEvent", function(_, event)
    local ok = pcall(function()
      if event == "LOOT_OPENED" then Rec.OnLoot()
      elseif event == "MERCHANT_SHOW" then Rec.OnMerchant()
      else Rec.OnQuest() end
    end)
    if not ok then return end                 -- a recording problem must never reach the player
  end)
  for _, e in ipairs({ "LOOT_OPENED", "MERCHANT_SHOW", "QUEST_DETAIL", "QUEST_COMPLETE" }) do
    pcall(ev.RegisterEvent, ev, e)
  end
end
