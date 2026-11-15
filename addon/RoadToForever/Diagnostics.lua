-- Diagnostics.lua: small read-only probes for questions about this client.
--
-- /r2f auras: can an addon read buffs here, on you and on your party, in or out of combat? The
-- game's API files mark aura queries as restricted ("secret" values: C_Secrets.ShouldAurasBeSecret,
-- RequiresUnitAuraAccess), and they can be refused in combat.
-- The group-buff reminder only makes sense if this says yes outside combat. Prints one block
-- of chat lines to include in a bug report.

local _, R2F = ...
local L = R2F.L

local Diag = {}
R2F.Diag = Diag

local function yn(v)
  if v == nil then return "-" end
  return v and "yes" or "no"
end

local function isSecret(v)
  return type(_G.issecretvalue) == "function" and _G.issecretvalue(v) == true
end

-- How many helpful auras can be read on `unit`, and how many of those have a readable spell id.
local function probe(unit)
  if not (UnitExists and UnitExists(unit)) then return nil end
  local ns = _G.C_UnitAuras
  if not (ns and ns.GetUnitAuras) then return { api = false } end
  local ok, list = pcall(ns.GetUnitAuras, unit, "HELPFUL")
  if not ok then return { api = true, error = tostring(list) } end
  if type(list) ~= "table" then return { api = true, count = 0, readable = 0, secret = true } end
  local readable = 0
  for _, aura in ipairs(list) do
    if type(aura) == "table" and aura.spellId ~= nil and not isSecret(aura.spellId) then readable = readable + 1 end
  end
  return { api = true, count = #list, readable = readable }
end

function Diag.Auras()
  local C = _G.C_Secrets
  R2F.Print(L.DIAG_AURAS_HEAD:format(
    yn(C and C.HasSecretRestrictions and C.HasSecretRestrictions()),
    yn(C and C.ShouldAurasBeSecret and C.ShouldAurasBeSecret()),
    yn(InCombatLockdown()), yn(IsInInstance and (IsInInstance()))))
  for _, unit in ipairs({ "player", "party1", "party2", "party3", "party4", "target" }) do
    local r = probe(unit)
    if r == nil then  -- luacheck: ignore 542
      -- unit not present: say nothing
    elseif r.api == false then
      R2F.Print(L.DIAG_AURAS_NOAPI)
      return
    elseif r.error then
      R2F.Print(L.DIAG_AURAS_ERR:format(unit, r.error))
    elseif r.secret then
      R2F.Print(L.DIAG_AURAS_SECRET:format(unit))
    else
      R2F.Print(L.DIAG_AURAS_LINE:format(unit, r.count, r.readable))
    end
  end
end


-- ---------------------------------------------------------------------------
-- /r2f debug talentdump: what the game's trait tree really says (Track B of docs/claude-code-wclbox-handoff.md)
-- ---------------------------------------------------------------------------
-- Read-only. Walks the live talent config the same way Talents.lua does (active spec group -> combat config -> trees -> nodes ->
-- entries -> definitions, plus the node's conditions and the tree currency) and copies every plain value (number, string,
-- boolean, and small tables of those) into R2FDB.talentDump[CLASS]. Nothing is written into a game table, nothing is hooked,
-- and it refuses in combat. The saved file (WTF/Account/<name>/SavedVariables/RoadToForever.lua) is written at /reload or logout;
-- the owner sends it, and the field names the printout lists tell which fields the game exposes
-- (so /r2f talentcheck can be built on them).
local function plain(v, depth)
  local t = type(v)
  if t == "number" or t == "boolean" or t == "string" then
    if isSecret(v) then return nil end
    return v
  end
  if t == "table" and depth > 0 and not isSecret(v) then
    local out, n = {}, 0
    for k, x in pairs(v) do
      n = n + 1
      if n > 64 then break end
      local kt = type(k)
      if kt == "number" or kt == "string" then
        local c = plain(x, depth - 1)
        if c ~= nil then out[k] = c end
      end
    end
    return out
  end
  return nil
end

local function safe(fn, ...)
  if type(fn) ~= "function" then return nil end
  local ok, a = pcall(fn, ...)
  if ok then return a end
  return nil
end

-- Adds the key names of `tbl` to the set `seen[kind]`.
local function noteFields(seen, kind, tbl)
  if type(tbl) ~= "table" then return end
  seen[kind] = seen[kind] or {}
  for k in pairs(tbl) do seen[kind][k] = true end
end

local function sortedKeys(set)
  local out = {}
  for k in pairs(set or {}) do out[#out + 1] = tostring(k) end
  table.sort(out)
  return table.concat(out, ",")
end

-- Pure part (tested without a client): the dump table for one config, from the C_Traits functions passed in `api`.
function Diag.BuildTalentDump(api, configID)
  local config = safe(api.GetConfigInfo, configID)
  if type(config) ~= "table" or type(config.treeIDs) ~= "table" then return nil end
  local seen = {}
  noteFields(seen, "config", config)
  local dump = { configID = configID, treeIDs = plain(config.treeIDs, 1), nodes = {}, currency = {}, edges = 0, conditions = 0 }
  for _, treeID in ipairs(config.treeIDs) do
    local cur = safe(api.GetTreeCurrencyInfo, configID, treeID, true)
    if type(cur) == "table" then
      dump.currency[#dump.currency + 1] = { treeID = treeID, info = plain(cur, 3) }
      noteFields(seen, "currency", cur[1])
    end
    for _, nodeID in ipairs(safe(api.GetTreeNodes, treeID) or {}) do
      local node = safe(api.GetNodeInfo, configID, nodeID)
      if type(node) == "table" then
        noteFields(seen, "node", node)
        local rec = plain(node, 3) or {}
        rec.treeID = treeID
        rec.entries = {}
        if type(node.visibleEdges) == "table" then dump.edges = dump.edges + #node.visibleEdges end
        for _, entryID in ipairs(type(node.entryIDs) == "table" and node.entryIDs or {}) do
          local entry = safe(api.GetEntryInfo, configID, entryID)
          local def = type(entry) == "table" and entry.definitionID and safe(api.GetDefinitionInfo, entry.definitionID) or nil
          noteFields(seen, "entry", entry)
          noteFields(seen, "definition", def)
          local e = { entryID = entryID, entry = plain(entry, 2), def = plain(def, 2) }
          if type(def) == "table" and def.spellID and not isSecret(def.spellID) then
            e.spellName = safe(api.GetSpellName, def.spellID)
          end
          rec.entries[#rec.entries + 1] = e
        end
        rec.conditionInfo = {}
        for _, condID in ipairs(type(node.conditionIDs) == "table" and node.conditionIDs or {}) do
          local cond = safe(api.GetConditionInfo, configID, condID)
          noteFields(seen, "condition", cond)
          dump.conditions = dump.conditions + 1
          rec.conditionInfo[#rec.conditionInfo + 1] = plain(cond, 2)
        end
        dump.nodes[#dump.nodes + 1] = rec
      end
    end
  end
  local fields = {}
  for kind, set in pairs(seen) do fields[kind] = sortedKeys(set) end
  dump.fields = fields
  return dump
end

function Diag.TalentDump()
  if R2F.InCombat() then R2F.Print(L.DIAG_TD_COMBAT) return end
  local CT, CS = _G.C_Traits, _G.C_SpecializationInfo
  if not (CT and CS and CT.GetConfigInfo and CT.GetTreeNodes and CT.GetNodeInfo) then R2F.Print(L.DIAG_TD_NOAPI) return end
  local group = safe(CS.GetActiveSpecGroup)
  local configID = group and safe(CS.GetCombatConfigIDForSpecGroup, group)
  if not configID then R2F.Print(L.DIAG_TD_NOCONFIG) return end
  local api = { GetConfigInfo = CT.GetConfigInfo, GetTreeNodes = CT.GetTreeNodes, GetNodeInfo = CT.GetNodeInfo,
                GetEntryInfo = CT.GetEntryInfo, GetDefinitionInfo = CT.GetDefinitionInfo, GetConditionInfo = CT.GetConditionInfo,
                GetTreeCurrencyInfo = CT.GetTreeCurrencyInfo, GetSpellName = _G.C_Spell and _G.C_Spell.GetSpellName }
  local dump = Diag.BuildTalentDump(api, configID)
  if not dump or #dump.nodes == 0 then R2F.Print(L.DIAG_TD_EMPTY) return end
  local _, class = UnitClass("player")
  class = class or "UNKNOWN"
  local build = GetBuildInfo and select(2, GetBuildInfo()) or nil
  dump.class, dump.build, dump.time = class, build, time and time() or 0
  if type(_G.R2FDB) ~= "table" then return end
  if type(_G.R2FDB.talentDump) ~= "table" then _G.R2FDB.talentDump = {} end
  _G.R2FDB.talentDump[class] = dump
  R2F.Print(L.DIAG_TD_DONE:format(class, #dump.nodes, #dump.treeIDs, dump.edges, dump.conditions))
  for _, kind in ipairs({ "node", "entry", "definition", "condition", "currency" }) do
    R2F.Print(L.DIAG_TD_FIELDS:format(kind, dump.fields[kind] or "-"))
  end
  R2F.Print(L.DIAG_TD_SAVE)
end

-- ---------------------------------------------------------------------------
-- BiZMe probes (read-only): /r2f debug ej | mem | inspect. They answer open questions in
-- addon/BiZMe/docs/data-sources.md and plan-review.md; results go to R2FDB.bizProbe (SavedVariables).
-- ---------------------------------------------------------------------------

local function probeStore()
  if type(_G.R2FDB) ~= "table" then return nil end
  if type(_G.R2FDB.bizProbe) ~= "table" then _G.R2FDB.bizProbe = {} end
  return _G.R2FDB.bizProbe
end

-- Pure part: the Encounter Journal walk, from the functions passed in `api` (nil = missing). Returns a table.
function Diag.BuildEJDump(api, maxInstances)
  local out = { have = {}, instances = {}, lootIds = {} }
  for name, fn in pairs(api) do out.have[name] = type(fn) == "function" end
  -- With no tier count (0 or nil) the walk still tries tiers 0-8, dungeons and raids, so an empty answer is a real answer.
  local tiers = { 0 }
  local nt = safe(api.GetNumTiers)
  if type(nt) ~= "number" or nt < 1 then nt = 8 end
  tiers = { 0 }
  for t = 1, nt do tiers[#tiers + 1] = t end
  out.tiers = safe(api.GetNumTiers)
  local total, seen = 0, {}
  for _, tier in ipairs(tiers) do
   if tier > 0 then safe(api.SelectTier, tier) end
   for _, raid in ipairs({ false, true }) do
    for i = 1, maxInstances do
      local id, name = safe(api.GetInstanceByIndex, i, raid)
      if not id or seen[id] then break end
      seen[id] = true
      total = total + 1
      local rec = { tier = tier, id = id, name = name, encounters = 0, loot = 0 }
      if api.GetInstanceInfo then
        local ok, _, _, _, _, _, _, areaMap, _, _, mapID = pcall(api.GetInstanceInfo, id)
        if ok then rec.mapID = mapID or areaMap end
      end
      safe(api.SelectInstance, id)
      for e = 1, 60 do
        local ename, _, encID = safe(api.GetEncounterInfoByIndex, e)
        if not ename then break end
        rec.encounters = rec.encounters + 1
        if api.SelectEncounter and api.GetNumLoot then
          safe(api.SelectEncounter, encID)
          local n = safe(api.GetNumLoot)
          if type(n) == "number" then
            rec.loot = rec.loot + n
            if n > 0 and #out.lootIds < 8 and api.GetLootInfoByIndex then
              local a, _, _, _, itemID = safe(api.GetLootInfoByIndex, 1)
              local id1 = type(a) == "table" and a.itemID or itemID
              if type(id1) == "number" then out.lootIds[#out.lootIds + 1] = id1 end
            end
          end
        end
      end
      out.instances[#out.instances + 1] = rec
    end
   end
  end
  out.total = total
  return out
end

function Diag.EJ(arg)
  if R2F.InCombat() then R2F.Print(L.DIAG_COMBAT) return end
  local G, CE = _G, _G.C_EncounterJournal or {}
  -- "/r2f debug ej load" also loads Blizzard's own Encounter Journal addon first (what opening the journal does).
  local AO = G.C_AddOns or {}
  local loader = AO.LoadAddOn or G.LoadAddOn
  local isLoaded = AO.IsAddOnLoaded or G.IsAddOnLoaded
  if arg == "load" and loader and not (isLoaded and isLoaded("Blizzard_EncounterJournal")) then
    pcall(loader, "Blizzard_EncounterJournal")
  end
  R2F.Print(L.DIAG_EJ_LOADED:format(tostring(isLoaded and isLoaded("Blizzard_EncounterJournal"))))
  local api = {
    GetNumTiers = G.EJ_GetNumTiers, SelectTier = G.EJ_SelectTier, GetInstanceByIndex = G.EJ_GetInstanceByIndex,
    GetInstanceInfo = G.EJ_GetInstanceInfo, SelectInstance = G.EJ_SelectInstance,
    GetEncounterInfoByIndex = G.EJ_GetEncounterInfoByIndex, SelectEncounter = G.EJ_SelectEncounter,
    GetNumLoot = G.EJ_GetNumLoot or CE.GetNumLoot, GetLootInfoByIndex = G.EJ_GetLootInfoByIndex or CE.GetLootInfoByIndex,
    GetDungeonEntrancesForMap = CE.GetDungeonEntrancesForMap, GetInstanceForGameMap = CE.GetInstanceForGameMap,
  }
  local d = Diag.BuildEJDump(api, 200)
  local have = {}
  for name, ok in pairs(d.have) do have[#have + 1] = name .. "=" .. (ok and "yes" or "no") end
  table.sort(have)
  R2F.Print(L.DIAG_EJ_API:format(table.concat(have, " ")))
  local withLoot, lootN = 0, 0
  for _, r in ipairs(d.instances) do
    if r.loot > 0 then withLoot = withLoot + 1; lootN = lootN + r.loot end
  end
  R2F.Print(L.DIAG_EJ_SUM:format(d.tiers or 0, d.total, withLoot, lootN))
  for i = 1, math.min(6, #d.instances) do
    local r = d.instances[i]
    R2F.Print(L.DIAG_EJ_ROW:format(r.tier, tostring(r.name), r.encounters, r.loot, tostring(r.mapID)))
  end
  if d.have.GetDungeonEntrancesForMap and G.C_Map and G.C_Map.GetBestMapForUnit then
    local map = safe(G.C_Map.GetBestMapForUnit, "player")
    local ent = map and safe(CE.GetDungeonEntrancesForMap, map)
    d.entrancesHere = { map = map, count = type(ent) == "table" and #ent or 0 }
    R2F.Print(L.DIAG_EJ_ENT:format(tostring(map), d.entrancesHere.count))
  end
  local s = probeStore()
  if s then
    d.build = GetBuildInfo and select(2, GetBuildInfo()) or nil
    s.ej = d
    R2F.Print(L.DIAG_SAVE)
  end
end

function Diag.Mem()
  if not (_G.UpdateAddOnMemoryUsage and _G.GetAddOnMemoryUsage) then R2F.Print(L.DIAG_NOAPI) return end
  _G.UpdateAddOnMemoryUsage()
  local kb = _G.GetAddOnMemoryUsage("RoadToForever")
  local rows = R2F.BiZData and #R2F.BiZData.rows or 0
  R2F.Print(L.DIAG_MEM:format(tonumber(kb) or 0, rows))
  -- What the Mr.BiZ data weighs: copy it, see how much the collector count grows, drop the copy.
  local dataKb
  if R2F.BiZData and _G.collectgarbage then
    local function copy(t)
      local c = {}
      for k, v in pairs(t) do c[k] = type(v) == "table" and copy(v) or v end
      return c
    end
    collectgarbage("collect")
    local before = collectgarbage("count")
    local c = copy(R2F.BiZData)
    local after = collectgarbage("count")
    dataKb = after - before
    c = nil
    collectgarbage("collect")
    R2F.Print(L.DIAG_MEM_DATA:format(dataKb))
  end
  local s = probeStore()
  if s then s.mem = { kb = kb, rows = rows, dataKb = dataKb, time = time and time() or 0 } end
end

local inspectFrame
local inspectAsked
function Diag.Inspect()
  if R2F.InCombat() then R2F.Print(L.DIAG_COMBAT) return end
  local G = _G
  if not (G.UnitExists and G.UnitExists("target") and G.UnitIsPlayer and G.UnitIsPlayer("target")) then
    R2F.Print(L.DIAG_INS_TARGET) return
  end
  local can = G.CanInspect and G.CanInspect("target")
  local near = G.CheckInteractDistance and G.CheckInteractDistance("target", 1)
  R2F.Print(L.DIAG_INS_CAN:format(tostring(can), tostring(near)))
  if not (can and G.NotifyInspect) then return end
  if not inspectFrame then
    inspectFrame = CreateFrame("Frame")
    inspectFrame:SetScript("OnEvent", function(self)
      self:UnregisterEvent("INSPECT_READY")
      local took = G.GetTime and (G.GetTime() - (inspectAsked or 0)) or 0
      local items, n = {}, 0
      for slot = 1, 19 do
        local link = G.GetInventoryItemLink and G.GetInventoryItemLink("target", slot)
        if type(link) == "string" then
          n = n + 1
          items[slot] = tonumber(link:match("item:(%d+)"))
        end
      end
      R2F.Print(L.DIAG_INS_DONE:format(n, took))
      local s = probeStore()
      if s then
        s.inspect = { items = items, seconds = took, time = time and time() or 0 }
        R2F.Print(L.DIAG_SAVE)
      end
      if G.ClearInspectPlayer then G.ClearInspectPlayer() end
    end)
  end
  inspectFrame:RegisterEvent("INSPECT_READY")
  inspectAsked = G.GetTime and G.GetTime() or 0
  G.NotifyInspect("target")
  R2F.Print(L.DIAG_INS_WAIT)
end
