-- TalentCalc.lua: the Talents tab's sandbox calculator, no UI.
--
-- The same rules and the same share codes as the site's talent calculator (talentcalc.js): 51 points, a
-- talent needs 5 points per row above it in its tree (`p`), prerequisites, a point can only be taken
-- away if nothing taken depends on it. Trees come from TalentData.lua (generated from the same Wowhead
-- data the site loads), so any class can be built on any character. Nothing here reads or changes the
-- character's real talents.
--
-- A calc is a plain table: { class = "warrior", ranks = { {r1, r2, ...}, {...}, {...} } } where
-- ranks[tree][k] is the rank of talent k (link order). Functions take the calc as first argument.

local _, R2F = ...

local Calc = {}
R2F.TalentCalc = Calc

Calc.MAX_POINTS = 51

local function data() return R2F.TalentData and R2F.TalentData.classes end

-- Roster order (the site's armor-type order): the class-icon row.
Calc.ORDER = { "priest", "warlock", "mage", "rogue", "druid", "shaman", "hunter", "paladin", "warrior" }

function Calc.Class(id)
  local d = data()
  return d and d[id]
end

function Calc.Trees(id)
  local c = Calc.Class(id)
  return c and c.trees
end

-- The class token ("WARRIOR") of a class id, for the class icon.
function Calc.Token(id)
  local c = Calc.Class(id)
  return c and c.token
end

function Calc.New(classId)
  local trees = Calc.Trees(classId)
  if not trees then return nil end
  local calc = { class = classId, ranks = {} }
  for t, tree in ipairs(trees) do
    local r = {}
    for k = 1, #tree.talents do r[k] = 0 end
    calc.ranks[t] = r
  end
  return calc
end

local function talent(calc, t, k)
  local tree = Calc.Trees(calc.class)[t]
  return tree.talents[k]
end

function Calc.Rank(calc, t, k) return calc.ranks[t][k] end

function Calc.TreePoints(calc, t)
  local n = 0
  for _, r in ipairs(calc.ranks[t]) do n = n + r end
  return n
end

function Calc.Total(calc)
  local n = 0
  for t = 1, #calc.ranks do n = n + Calc.TreePoints(calc, t) end
  return n
end

-- Points in the tree in rows above talent row `row` (0-based rows).
local function pointsAbove(calc, t, row)
  local tree, n = Calc.Trees(calc.class)[t], 0
  for k, x in ipairs(tree.talents) do
    if x.r < row then n = n + calc.ranks[t][k] end
  end
  return n
end

function Calc.TierMet(calc, t, k)
  local x = talent(calc, t, k)
  return pointsAbove(calc, t, x.r) >= x.p
end

function Calc.PrereqsMet(calc, t, k)
  for _, q in ipairs(talent(calc, t, k).q) do
    if calc.ranks[t][q[1]] < q[2] then return false end
  end
  return true
end

-- Why a point can't be added: nil = it can; "max" | "cap" | "tier" | "prereq".
function Calc.AddBlock(calc, t, k)
  local x = talent(calc, t, k)
  if calc.ranks[t][k] >= x.m then return "max" end
  if Calc.Total(calc) >= Calc.MAX_POINTS then return "cap" end
  if not Calc.TierMet(calc, t, k) then return "tier" end
  if not Calc.PrereqsMet(calc, t, k) then return "prereq" end
  return nil
end

function Calc.CanAdd(calc, t, k) return Calc.AddBlock(calc, t, k) == nil end

-- A point can come off unless a talent you have depends on it (prerequisite) or a lower tier
-- would no longer have enough points for a deeper talent you have taken.
function Calc.CanRemove(calc, t, k)
  local r = calc.ranks[t][k]
  if r <= 0 then return false end
  local tree = Calc.Trees(calc.class)[t]
  local x = talent(calc, t, k)
  for j, u in ipairs(tree.talents) do
    if calc.ranks[t][j] > 0 then
      for _, q in ipairs(u.q) do
        if q[1] == k and r - 1 < q[2] then return false end
      end
      if u.r > x.r and pointsAbove(calc, t, u.r) - 1 < u.p then return false end
    end
  end
  return true
end

-- Add one point (all the way to the maximum when `max`). Returns true if anything changed.
function Calc.Add(calc, t, k, max)
  local changed = false
  while Calc.CanAdd(calc, t, k) do
    calc.ranks[t][k] = calc.ranks[t][k] + 1
    changed = true
    if not max then break end
  end
  return changed
end

function Calc.Remove(calc, t, k, all)
  local changed = false
  while Calc.CanRemove(calc, t, k) do
    calc.ranks[t][k] = calc.ranks[t][k] - 1
    changed = true
    if not all then break end
  end
  return changed
end

function Calc.Reset(calc)
  for t = 1, #calc.ranks do
    for k = 1, #calc.ranks[t] do calc.ranks[t][k] = 0 end
  end
end

-- Every rank within its maximum, every taken talent has its tier points and prerequisites, at most 51.
function Calc.Valid(calc)
  if Calc.Total(calc) > Calc.MAX_POINTS then return false end
  for t, tree in ipairs(Calc.Trees(calc.class)) do
    for k, x in ipairs(tree.talents) do
      local r = calc.ranks[t][k]
      if r > x.m then return false end
      if r > 0 and not (Calc.TierMet(calc, t, k) and Calc.PrereqsMet(calc, t, k)) then return false end
    end
  end
  return true
end

-- ---- Codes and links (the site's format) -------------------------------------------------------

-- "<tree1>-<tree2>-<tree3>", one digit per talent, trailing zeros and trailing empty trees dropped.
function Calc.Code(calc)
  local parts = {}
  for t = 1, #calc.ranks do
    parts[t] = (table.concat(calc.ranks[t]):gsub("0+$", ""))
  end
  return (table.concat(parts, "-"):gsub("%-+$", ""))
end

-- The ~hash over the class's talent names in link order (the same as talentcalc.js's treeHash and
-- Talents.Hash over the game's own list, so a link made here opens on the site and in the game).
function Calc.Hash(classId)
  local trees = Calc.Trees(classId)
  if not trees then return nil end
  local parts = {}
  for t, tree in ipairs(trees) do
    local names = {}
    for k, x in ipairs(tree.talents) do names[k] = x.n end
    parts[t] = table.concat(names, ",")
  end
  return R2F.Talents.HashText(table.concat(parts, ";"))
end

-- "class/code~hash" (always with the "/" and the hash, like the site's link()).
function Calc.Body(calc)
  return calc.class .. "/" .. Calc.Code(calc) .. "~" .. Calc.Hash(calc.class)
end

-- Fills a calc from a code ("05-3-" ...). An invalid code (past a maximum, a talent without its
-- tier points or prerequisite, more than 51 points) leaves the calc empty, like the site. Returns
-- true when the code was applied.
function Calc.Apply(calc, code)
  Calc.Reset(calc)
  local n = 0
  for part in ((code or "") .. "-"):gmatch("([^%-]*)%-") do
    n = n + 1
    local t = calc.ranks[n]
    if t then
      for k = 1, #t do t[k] = tonumber(part:sub(k, k)) or 0 end
    elseif part:find("[1-9]") then
      Calc.Reset(calc)
      return false
    end
  end
  if not Calc.Valid(calc) then Calc.Reset(calc) return false end
  return true
end

-- Builds a calc from a class id and a code in one go; nil for an unknown class.
function Calc.FromCode(classId, code)
  local calc = Calc.New(classId)
  if not calc then return nil end
  local ok = Calc.Apply(calc, code)
  return calc, ok
end

-- The level a build needs (Talents.LevelFor: talent points start at level 10, the Talented perk 5 earlier).
-- The points of a build in the order to take them: tier by tier (and tree by tree, column by column inside a
-- tier), every rank of a talent together. The same order Learn this build uses (Talents.LearnOrder), and always
-- legal: a tier's points above it and a talent's prerequisite are complete before it. -> { {tree, talent}, ... }
function Calc.Order(calc)
  local list = {}
  for t, tree in ipairs(Calc.Trees(calc.class) or {}) do
    for k, x in ipairs(tree.talents) do
      if calc.ranks[t][k] > 0 then list[#list + 1] = { t = t, k = k, r = x.r, c = x.c } end
    end
  end
  table.sort(list, function(a, b)
    if a.r ~= b.r then return a.r < b.r end
    if a.t ~= b.t then return a.t < b.t end
    return a.c < b.c
  end)
  -- A prerequisite in the same row (a horizontal link) comes first, even when it sits to the right.
  local moved = true
  for _ = 1, #list do
    if not moved then break end
    moved = false
    for i, e in ipairs(list) do
      for _, q in ipairs(Calc.Trees(calc.class)[e.t].talents[e.k].q) do
        for j = i + 1, #list do
          if list[j].t == e.t and list[j].k == q[1] then
            table.remove(list, i)
            table.insert(list, j, e)
            moved = true
            break
          end
        end
        if moved then break end
      end
      if moved then break end
    end
  end
  local order = {}
  for _, e in ipairs(list) do
    for _ = 1, calc.ranks[e.t][e.k] do order[#order + 1] = { e.t, e.k } end
  end
  return order
end

-- A copy of a build with only its first n points (in Calc.Order).
function Calc.Prefix(calc, n)
  local out = Calc.New(calc.class)
  if not out then return nil end
  for i, p in ipairs(Calc.Order(calc)) do
    if i > n then break end
    out.ranks[p[1]][p[2]] = out.ranks[p[1]][p[2]] + 1
  end
  return out
end

-- The first point of a build (in Calc.Order) that the character does not have yet. `tree` = Talents.Plan's trees
-- (each talent's real `rank`). -> name, point number, or nil when every point is taken.
function Calc.NextPoint(calc, planTrees)
  local seen = {}
  for i, p in ipairs(Calc.Order(calc)) do
    local t, k = p[1], p[2]
    seen[t] = seen[t] or {}
    seen[t][k] = (seen[t][k] or 0) + 1
    local e = planTrees[t] and planTrees[t].talents[k]
    if seen[t][k] > (e and e.rank or 0) then return Calc.Trees(calc.class)[t].talents[k].n, i end
  end
  return nil
end

function Calc.Level(calc, perk)
  return R2F.Talents.LevelFor(Calc.Total(calc), perk)
end

-- ---- Recommended builds (TalentData.builds) ----------------------------------------------------

Calc.ROLES = { "Tank", "DPS", "Healer" }

-- { { level, role, name, code } } for a class, role order Tank / DPS / Healer, then level 60 before 30.
function Calc.Recommended(classId)
  local out = {}
  local b = R2F.TalentData and R2F.TalentData.builds or {}
  for _, e in ipairs(b) do
    if e[1] == classId then out[#out + 1] = { level = e[2], role = e[3], name = e[4], code = e[5] } end
  end
  local rank = { Tank = 1, DPS = 2, Healer = 3 }
  table.sort(out, function(x, y)
    if x.role ~= y.role then return rank[x.role] < rank[y.role] end
    if x.level ~= y.level then return x.level > y.level end
    return x.name < y.name
  end)
  return out
end
