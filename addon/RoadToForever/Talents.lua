-- Talents.lua: talent links (ADDON_PLAN.md 13). Step 8 = export only:
-- read the character's talents in the site's link order, build the link with
-- its ~hash (Copy my build, 13.4). Steps 9/10 add parsing, preview and learning.
--
-- Read-only: this file only calls GetNumTalentTabs / GetNumTalents /
-- GetTalentInfo and shows our own copy box. It never learns a talent and never
-- touches a macro, so the InCombatLockdown() / RunOrQueue pattern that guards
-- macro writes (6.4, 6.9) doesn't apply: reading talent info and showing a
-- non-secure frame are both allowed in combat (ADDON_PLAN 13.6).

local _, R2F = ...
local L = R2F.L

local Talents = {}
R2F.Talents = Talents

Talents.SITE_URL = "https://nobody174.github.io/wow-forever-macros/talents.html#"

-- The game's talents, one list per talent tab, each sorted by tier, then
-- column. That is the order of the site's share code (one digit per talent,
-- Wowhead's row/column order), so digit k of a tree's part of a link is the
-- k-th talent here. GetTalentInfo's own index order is not guaranteed to be
-- that (it follows the client's talent table), hence the sort. Ties can't
-- happen in a real tree (one talent per cell); the index tiebreak only keeps
-- the order deterministic, since table.sort is not stable.
-- Returns { { {name, tier, column, rank, maxRank, index}, ... }, ... } or nil
-- when the client has no talent API, or no tabs / no talents yet.
function Talents.ReadTrees()
  if not (GetNumTalentTabs and GetNumTalents and GetTalentInfo) then return nil end
  local numTabs = GetNumTalentTabs() or 0
  if numTabs < 1 then return nil end
  local trees, count = {}, 0
  for tab = 1, numTabs do
    local list = {}
    for i = 1, (GetNumTalents(tab) or 0) do
      -- Classic: name, iconTexture, tier, column, rank, maxRank, ... (tier and
      -- column 1-based; rank = points learned, not a preview).
      local name, _, tier, column, rank, maxRank = GetTalentInfo(tab, i)
      if name then
        list[#list + 1] = { name = name, tier = tier or 0, column = column or 0,
                            rank = rank or 0, maxRank = maxRank or 0, index = i }
      end
    end
    table.sort(list, function(a, b)
      if a.tier ~= b.tier then return a.tier < b.tier end
      if a.column ~= b.column then return a.column < b.column end
      return a.index < b.index
    end)
    trees[tab] = list
    count = count + #list
  end
  -- Tabs but no talents at all = the client hasn't loaded talent data yet; a
  -- link from that would be an empty build with a wrong hash, so say "can't".
  if count == 0 then return nil end
  return trees
end

-- The ~hash (13.3). MUST match talentcalc.js's treeHash() byte for byte:
-- djb2 over the talent names in link order ("," between talents, ";" between
-- trees), as UTF-8 bytes (WoW's Lua strings already are UTF-8 bytes), 32-bit
-- wrap, then mod 36^4 written in base36 and zero-padded to 4 characters.
-- Names in link order is the point: if the game's sorted list differs from
-- the site's anywhere, a digit would land on a different talent, and the hash
-- changes. addon/tests/run_tests.py runs both implementations on one fixture.
local B36 = "0123456789abcdefghijklmnopqrstuvwxyz"

function Talents.HashText(s)
  -- Lua 5.1 has no bit ops; h * 33 + 255 stays far below 2^53, so the
  -- double arithmetic is exact before the % 2^32 wrap (same as Library.Hash).
  local h = 5381
  for i = 1, #s do
    h = (h * 33 + s:byte(i)) % 4294967296
  end
  local v = h % 1679616   -- 36^4
  local out = ""
  for _ = 1, 4 do
    local d = v % 36
    out = B36:sub(d + 1, d + 1) .. out
    v = (v - d) / 36
  end
  return out
end

function Talents.Hash(trees)
  local parts = {}
  for t, list in ipairs(trees) do
    local names = {}
    for k, x in ipairs(list) do names[k] = x.name end
    parts[t] = table.concat(names, ",")
  end
  return Talents.HashText(table.concat(parts, ";"))
end

-- The share code exactly like talentcalc.js's code(): per tree one digit per
-- talent (current rank) in sorted order, trailing zeros removed (a tree's
-- missing trailing digits mean 0, 13.2, so links stay short and match the
-- site's own output), trees joined with "-", trailing "-" removed (empty
-- trailing trees), e.g. "--05" -> "--05", "05--" -> "05", "" for no points.
function Talents.Encode(trees)
  local parts = {}
  for t, list in ipairs(trees) do
    local digits = {}
    for k, x in ipairs(list) do digits[k] = tostring(x.rank) end
    parts[t] = (table.concat(digits):gsub("0+$", ""))
  end
  return (table.concat(parts, "-"):gsub("%-+$", ""))
end

-- The site's class id: the English class token in lower case ("warrior"),
-- the same ids as talentcalc.js's CLASSES.
function Talents.ClassId()
  local _, token = UnitClass("player")
  return token and token:lower() or nil
end

-- "<class>/<code>~<hash>", always with the "/" and the hash, even with no
-- points ("warrior/~<hash>"): the same shape as talentcalc.js's link().
function Talents.LinkBody(classId, trees)
  return classId .. "/" .. Talents.Encode(trees) .. "~" .. Talents.Hash(trees)
end

-- The full link for the character's current talents, or nil if they can't
-- be read (no talent API / tabs not loaded yet).
function Talents.MyBuildLink()
  local trees, classId = Talents.ReadTrees(), Talents.ClassId()
  if not trees or not classId then return nil end
  return Talents.SITE_URL .. Talents.LinkBody(classId, trees)
end

-- Copy my build (13.4): the link in our copy box, text selected. Read-only,
-- so it works in combat too (see the header). Returns the link or nil.
function Talents.CopyMyBuild()
  local link = Talents.MyBuildLink()
  if not link then
    R2F.Print(L.TALENT_READ_FAILED)
    return nil
  end
  R2F.UI.ShowCopy(link, L.TALENT_COPY_HINT)
  return link
end
