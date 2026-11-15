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

-- What you wear in a slot: score (0 = empty slot, false = the item is not loaded yet, nil = cannot score), link.
function M.Worn(slotKey, specId)
  local inv = R2F.BiZ.INV_SLOT[slotKey]
  local link = inv and GetInventoryItemLink and GetInventoryItemLink("player", inv)
  if type(link) ~= "string" then return 0, nil end
  local s = R2F.GearScore and R2F.GearScore.Score(link, specId)
  if s == nil then return false, link end
  return s, link
end

-- Do you already have the item (worn, bags or bank)?
function M.Owns(id)
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
  ctx.faction = ctx.faction or ((UnitFactionGroup and UnitFactionGroup("player")) or "Alliance"):lower()
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
              local place = R2F.BiZ.Place(R2F.BiZ.PlaceOfItem(row.id))
              local trip = TRIP_TYPES[row.type] and not (place and M.OnRoute(place)) or false
              local threshold = (place and M.OnRoute(place)) and M.CARRY_ROUTE or M.CARRY_TRIP
              local left = M.Span(sp, i, row.id, lvl, false)
              local hi = select(2, R2F.BiZ.Levels())
              local soon = trip and lvl < hi and left < threshold
              if ok and not soon then
                choice = { slot = sl.slot, row = row, rank = rank, gain = gain, worn = wornLink, wornScore = wornScore,
                           score = score, left = left, trip = trip, place = place, note = (why == "rep") and "rep" or nil }
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
