-- BiZMe.lua: Mr.BiZ for YOU. Logic only (the tab is UI/BiZ.lua, the data BiZData.lua, the list BiZ.lua).
--
-- * Worn vs BiZ: what you wear in a slot against the spec's picks for the level.
-- * Reachable now: can you get this pick today? (faction, quest level, profession skill, unknown / PvP sources are left out)
-- * Next upgrades: per slot the best reachable pick that beats what you wear by MIN_GAIN percent, ranked by gain,
--   with the owner's carry rule: no trip for a pick that the list replaces within CARRY_TRIP levels
--   (CARRY_ROUTE when the source is in the zone you are in).
--
-- Everything reads the data and the game's getters only; nothing is written into the game and it works in combat.
-- Scores: ForeverDB's score for a pick (the best pick carries it, the next picks a percent behind),
-- GearScore's for what you wear (same weights).

local _, R2F = ...

local M = {}
R2F.BiZMe = M

M.MIN_GAIN = 5        -- percent a pick must beat what you wear by to count as an upgrade
M.CARRY_ROUTE = 5     -- levels a pick must stay on the list when its source is where you are
M.CARRY_TRIP = 10     -- levels a pick must stay on the list when you have to travel for it

local function data() return R2F.BiZData end

local TRIP_TYPES = { dungeon = true, raid = true, quest = true, reputation = true, crafted = true, pvp = true }

-- Index of a slot key in the data's slot list (the order of sp.runs).
function M.SlotIndex(slotKey)
  for i, s in ipairs(data().slots) do
    if s.key == slotKey then return i end
  end
end

-- Score of a pick: the best pick's own score, a next pick's score a percent (delta, negative) behind it.
function M.PickScore(best, row)
  if not (best and row and type(best.score) == "number") then return nil end
  if row == best then return best.score end
  if type(row.delta) == "number" then return best.score * (1 + row.delta / 100) end
  return nil
end

-- ---------------------------------------------------------------------------
-- "Viewing as": another character (an alt, a friend you inspected). Profiles are account-wide:
--   R2FDB.bizProfiles[name] = { class = "hunter", spec = "hunter/marksmanship", level = 38, faction = "alliance",
--                               gear = { head = itemId, ... }, time = <seconds>, inspected = true }
-- While one is viewed (R2FCharDB.biz.viewing = name) the worn-vs-BiZ comparison reads that character's gear.
-- ---------------------------------------------------------------------------

local function profiles()
  local d = R2F.Library and R2F.Library.db
  if not d then return {} end
  d.bizProfiles = d.bizProfiles or {}
  return d.bizProfiles
end

function M.Profiles()
  local names = {}
  for name in pairs(profiles()) do names[#names + 1] = name end
  table.sort(names)
  return names
end

function M.Viewing()
  local c = R2F.Library and R2F.Library.cdb and R2F.Library.cdb.biz
  local name = c and c.viewing
  if name and profiles()[name] then return name, profiles()[name] end
  return nil
end

-- View a saved character (nil = back to yourself). Sets the tab's class, spec and level to theirs.
function M.View(name)
  local c = R2F.Library.cdb.biz
  local p = name and profiles()[name]
  if not p then
    c.viewing = nil
    c.level = nil
    c.class = nil
    return
  end
  c.viewing = name
  R2F.BiZ.SetClass(p.class)
  if p.spec and R2F.BiZ.Spec(p.spec) then R2F.BiZ.SetSpec(p.spec) end
  R2F.BiZ.SetLevel(p.level)
end

function M.Forget(name)
  profiles()[name] = nil
  if M.Viewing() == nil then M.View(nil) end
end

local SLOT_OF_INV = {}
for key, inv in pairs(R2F.BiZ.INV_SLOT) do SLOT_OF_INV[inv] = key end

-- Save a profile from gear you read: `gear` = { [inventory slot id] = item link }.
function M.SaveProfile(name, info, gear)
  local ids = {}
  for inv, link in pairs(gear) do
    local key = SLOT_OF_INV[inv]
    local id = type(link) == "string" and tonumber(link:match("item:(%d+)"))
    if key and id then ids[key] = id end
  end
  local old = profiles()[name]
  profiles()[name] = { class = info.class, spec = (old and old.spec) or info.spec, level = info.level, faction = info.faction,
                       gear = ids, time = time and time() or 0, inspected = info.inspected or false }
  return profiles()[name]
end

-- Remember the spec chosen for the viewed character.
function M.NoteSpec(specId)
  local _, p = M.Viewing()
  if p then p.spec = specId end
end

local inspectFrame, pending
-- Inspect your target (a player within range, out of combat) and save them as a profile;
-- `done(name)` or `done(nil, reason)` is called after.
function M.Inspect(done)
  if R2F.InCombat and R2F.InCombat() then return done(nil, "combat") end
  if not (UnitExists and UnitExists("target") and UnitIsPlayer and UnitIsPlayer("target")) then return done(nil, "target") end
  if not (CanInspect and CanInspect("target") and NotifyInspect) then return done(nil, "range") end
  local name = GetUnitName and GetUnitName("target", true) or UnitName("target")
  local token = select(2, UnitClass("target"))
  local classKey = R2F.BiZ.ClassKeyOf and R2F.BiZ.ClassKeyOf(token)
  if not classKey then return done(nil, "class") end
  pending = { name = name, class = classKey, level = UnitLevel("target"),
              faction = ((UnitFactionGroup and UnitFactionGroup("target")) or "Alliance"):lower(), done = done }
  if not inspectFrame then
    inspectFrame = CreateFrame("Frame")
    inspectFrame:SetScript("OnEvent", function(self)
      self:UnregisterEvent("INSPECT_READY")
      local p = pending
      pending = nil
      if not p then return end
      local gear = {}
      for inv = 1, 19 do
        gear[inv] = GetInventoryItemLink and GetInventoryItemLink("target", inv) or nil
      end
      if ClearInspectPlayer then ClearInspectPlayer() end
      p.inspected = true
      M.SaveProfile(p.name, p, gear)
      p.done(p.name)
    end)
  end
  inspectFrame:RegisterEvent("INSPECT_READY")
  NotifyInspect("target")
end

-- What you wear in a slot: score (0 = empty slot, false = the item is not loaded yet, nil = cannot score), link.
function M.Worn(slotKey, specId)
  local _, prof = M.Viewing()
  if prof then
    local id = prof.gear[slotKey]
    if not id then return 0, nil end
    local link = "item:" .. id
    local sc = R2F.GearScore and R2F.GearScore.Score(link, specId)
    if sc == nil then return false, link end
    return sc, link
  end
  local inv = R2F.BiZ.INV_SLOT[slotKey]
  local link = inv and GetInventoryItemLink and GetInventoryItemLink("player", inv)
  if type(link) ~= "string" then return 0, nil end
  local s = R2F.GearScore and R2F.GearScore.Score(link, specId)
  if s == nil then return false, link end
  return s, link
end

-- Do you already have the item (worn, bags or bank)?
function M.Owns(id)
  local _, prof = M.Viewing()
  if prof then
    for _, v in pairs(prof.gear) do
      if v == id then return true end
    end
    return false
  end
  if GetItemCount and (GetItemCount(id, true) or 0) > 0 then return true end
  for _, inv in pairs(R2F.BiZ.INV_SLOT) do
    local link = GetInventoryItemLink and GetInventoryItemLink("player", inv)
    if type(link) == "string" and tonumber(link:match("item:(%d+)")) == id then return true end
  end
  return false
end

-- A profession's skill (nil when you do not have it, or the client cannot tell).
function M.ProfSkill(prof)
  if not (GetNumSkillLines and GetSkillLineInfo) then return nil, false end
  local n = GetNumSkillLines() or 0
  for i = 1, n do
    local name, header, _, rank = GetSkillLineInfo(i)
    if not header and name == prof then return rank, true end
  end
  return nil, true
end

-- Consecutive levels from `lvl` on that the item stays on the list for a slot (best only with `onlyBest`):
-- 0 when it is not there at `lvl`.
function M.Span(sp, slotIdx, itemId, lvl, onlyBest)
  local runs = sp.runs[slotIdx]
  if not runs then return 0 end
  local rows = data().rows
  local _, hi = R2F.BiZ.Levels()
  local function has(run)
    if run[2] <= 0 then return false end
    if rows[run[2]].id == itemId then return true end
    if not onlyBest then
      for _, ri in ipairs(run[3] or {}) do
        if rows[ri].id == itemId then return true end
      end
    end
    return false
  end
  local k = 1
  for i, r in ipairs(runs) do
    if r[1] <= lvl then k = i end
  end
  if not has(runs[k]) then return 0 end
  for j = k + 1, #runs do
    if not has(runs[j]) then return runs[j][1] - lvl end
  end
  return hi - lvl + 1
end

-- Is the place in the zone you are standing in?
function M.OnRoute(place)
  if not (place and place.mapHint and C_Map and C_Map.GetBestMapForUnit) then return false end
  return C_Map.GetBestMapForUnit("player") == place.mapHint
end

-- Can you get this pick now? -> ok (boolean), reason ("unknown", "faction", "pvp", "level", "skill",
-- "profession", "rep" = maybe), detail.
function M.Reachable(row, ctx)
  local t = row.type
  if t == "unknown" then return false, "unknown" end
  if t == "pvp" then return false, "pvp" end
  if row.faction and ctx.faction and row.faction ~= ctx.faction then return false, "faction" end
  if t == "quest" and type(row.qlevel) == "number" and row.qlevel > ctx.level + 2 then return false, "level", row.qlevel end
  if t == "crafted" and row.prof then
    local skill, known = M.ProfSkill(row.prof)
    if known then
      if skill == nil then return false, "profession", row.prof end
      if type(row.skill) == "number" and skill < row.skill then return false, "skill", row.skill end
    end
  end
  if t == "reputation" then return true, "rep" end
  return true
end

-- The ranked upgrade list for a spec at a level, best gain first:
-- { { slot, row, gain, worn, wornScore, score, left, trip, place, note }, ... }.
-- `ctx` = { level, faction } (defaults: you). Slots with nothing to improve are left out.
-- The second result lists the BiZ picks that would be an upgrade but are out of reach: { slot, row, why, detail, gain }.
function M.Upgrades(specId, lvl, ctx)
  ctx = ctx or {}
  ctx.level = ctx.level or lvl
  local _, viewed = M.Viewing()
  local mine = ((UnitFactionGroup and UnitFactionGroup("player")) or "Alliance"):lower()
  ctx.faction = ctx.faction or (viewed and viewed.faction) or mine
  local sp = data().specs[specId]
  local out, blocked = {}, {}
  if not sp then return out, blocked end
  local taken = {}
  for i, sl in ipairs(R2F.BiZ.SlotsAt(sp, lvl)) do
    if sl.best then
      local wornScore, wornLink = M.Worn(sl.slot, specId)
      if wornScore ~= false then
        local picks = { sl.best }
        for _, n in ipairs(sl.next or {}) do picks[#picks + 1] = n end
        local choice
        for rank, row in ipairs(picks) do
          local score = M.PickScore(sl.best, row)
          local ok, why, detail = M.Reachable(row, ctx)
          if score and not taken[row.id] and not M.Owns(row.id) then
            local gain = wornScore > 0 and (score - wornScore) / wornScore * 100 or 100
            if gain >= M.MIN_GAIN then
              local placeKey = R2F.BiZ.PlaceOfItem(row.id)
              local place = R2F.BiZ.Place(placeKey)
              local trip = TRIP_TYPES[row.type] and not (place and M.OnRoute(place)) or false
              local threshold = (place and M.OnRoute(place)) and M.CARRY_ROUTE or M.CARRY_TRIP
              local left = M.Span(sp, i, row.id, lvl, false)
              local hi = select(2, R2F.BiZ.Levels())
              local soon = trip and lvl < hi and left < threshold
              if ok and not soon then
                choice = { slot = sl.slot, row = row, rank = rank, gain = gain, worn = wornLink, wornScore = wornScore,
                           score = score, left = left, trip = trip, place = place, placeKey = placeKey,
                           note = (why == "rep") and "rep" or nil }
                break
              elseif rank == 1 then
                -- the BiZ pick itself is out of reach: say why ("soon" = replaced within the carry rule's levels)
                blocked[#blocked + 1] = { slot = sl.slot, row = row, why = (not ok) and why or "soon",
                                          detail = detail, gain = gain }
              end
            end
          end
        end
        if choice then
          taken[choice.row.id] = true
          out[#out + 1] = choice
        end
      end
    end
  end
  table.sort(out, function(a, b)
    if a.gain ~= b.gain then return a.gain > b.gain end
    return a.slot < b.slot
  end)
  return out, blocked
end

-- The line on any item's tooltip: where it ranks for your spec at the level you look at
-- ("Mr.BiZ: Bizzer for Beast Mastery (Head), on the list for 12 more levels").
-- Returns text, r, g, b (nil when the item is on none of the spec's lists for that level).
function M.RankLine(id, specId, lvl)
  local BiZ = R2F.BiZ
  specId = specId or BiZ.SpecId()
  lvl = lvl or BiZ.Level()
  local sp = specId and data().specs[specId]
  local L = R2F.L
  if not sp then return nil end
  for i, sl in ipairs(BiZ.SlotsAt(sp, lvl)) do
    if sl.best then
      local picks = { sl.best }
      for _, n in ipairs(sl.next or {}) do picks[#picks + 1] = n end
      for rank, row in ipairs(picks) do
        if row.id == id then
          local left = M.Span(sp, i, id, lvl, false)
          return L.BIZ_TIP_GAME:format(BiZ.RankName(rank), sp.name, BiZ.SlotLabel(sl.slot), left), 0.4, 0.8, 1
        end
      end
    end
  end
  return nil
end

-- The route: point the BiZNav arrow at the next upgrade (in the list's order) that has a known place.
-- Each call moves on to the one after the last; returns that entry and how many more places are in the list, or nil with none.
local routeAt = 0
function M.GuideNext(list)
  local n = #list
  for step = 1, n do
    local i = (routeAt + step - 1) % n + 1
    local u = list[i]
    if u.placeKey and R2F.BiZ.Go(u.placeKey) then
      routeAt = i
      local more = 0
      for _, x in ipairs(list) do
        if x.placeKey and x ~= u then more = more + 1 end
      end
      return u, more
    end
  end
  return nil
end
function M.ResetRoute() routeAt = 0 end
