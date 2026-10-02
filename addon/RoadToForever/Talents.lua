-- Talents.lua: talent links (ADDON_PLAN.md 13).
--   Step 8: read the character's talents in the site's link order, build the
--           link with its ~hash (Copy my build, 13.4).
--   Step 9: read a pasted link (13.2), check it against the game (13.3) and
--           work out the preview: per talent learned / now / later / not in
--           the build / conflict, plus the summary line (13.4).
--   Step 10 adds the learning engine (13.5).
--
-- Still read-only after step 9: this file only calls GetNumTalentTabs /
-- GetNumTalents / GetTalentInfo / GetTalentTabInfo / UnitCharacterPoints /
-- GetLocale and shows our own copy box. It never learns a talent (no
-- LearnTalent anywhere yet) and never touches a macro, so the
-- InCombatLockdown() / RunOrQueue pattern that guards macro writes (6.4, 6.9)
-- doesn't apply: reading talent info and showing non-secure frames are both
-- allowed in combat (ADDON_PLAN 13.6, 13.7).

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
-- Returns { { {name, icon, tier, column, rank, maxRank, index}, ... }, ... } or
-- nil when the client has no talent API, or no tabs / no talents yet.
-- Step 9's preview maps a pasted link onto exactly this list (13.2), so the
-- export and the import can never disagree about which digit is which talent.
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
      local name, icon, tier, column, rank, maxRank = GetTalentInfo(tab, i)
      if name then
        list[#list + 1] = { name = name, icon = icon, tier = tier or 0, column = column or 0,
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

-- ===========================================================================
-- Step 9: reading a pasted link and the preview (13.2 - 13.4)
-- ===========================================================================

-- talentcalc.js's CLASSES ids. A word before "/" that isn't one of these is
-- not a talent link (it's e.g. the "io" of "github.io/..." in a mangled paste).
local CLASS_IDS = { warrior = true, paladin = true, hunter = true, rogue = true, priest = true,
                    shaman = true, mage = true, warlock = true, druid = true }

-- "warrior" -> "Warrior". English on purpose: every message around it is
-- English (5.9), and 13.2's message is "This is a Paladin build. You're
-- playing a Warrior." A localized class name would mix two languages.
function Talents.ClassName(id)
  return id:sub(1, 1):upper() .. id:sub(2)
end

-- Accepts all four forms of 13.2: a full URL, "talents.html#warrior/...",
-- "#warrior/..." and bare "warrior/...". Everything up to the last "#" is
-- dropped first: on a full URL 13.2's pattern alone would happily match
-- "io/" in "github.io/". Then the plan's pattern, anchored so trailing junk
-- isn't silently ignored. Surrounding spaces, quotes and Discord's <...> are
-- trimmed. Case is ignored (class ids and the base36 hash are lower case).
-- Returns { class, code, hash (nil = old link without one), codes = {per
-- tree digit string} } or nil if it isn't a talent link.
function Talents.ParseLink(text)
  if type(text) ~= "string" then return nil end
  local s = text:gsub("^[%s<\"']+", ""):gsub("[%s>\"']+$", ""):lower()
  s = s:match("#([^#]*)$") or s
  local cls, code, tail = s:match("^(%a+)/([%d%-]*)(~?%w*)$")
  if not cls or not CLASS_IDS[cls] then return nil end
  -- "warrior/32a": the pattern's optional "~" lets letters follow the digits
  -- directly; that's not a link we made, so refuse it rather than guess.
  if tail ~= "" and tail:sub(1, 1) ~= "~" then return nil end
  local hash = tail:sub(2)
  -- A bare trailing "~" (no check after it) reads like the site does: no hash.
  if hash == "" then hash = nil end
  local codes = {}
  for part in (code .. "-"):gmatch("([^%-]*)%-") do codes[#codes + 1] = part end
  return { class = cls, code = code, hash = hash, codes = codes }
end

-- English client? The ~hash is over talent NAMES, and a non-English client
-- returns translated names, so its hash can never equal the site's (13.6).
-- No GetLocale at all: assume English, i.e. keep the strict check.
function Talents.IsEnglishClient()
  if not GetLocale then return true end
  local loc = GetLocale()
  return loc == nil or loc == "enUS" or loc == "enGB"
end

-- Unspent talent points: one function for the whole addon (the minimap
-- tooltip has had it since step 6; UnitCharacterPoints is guarded there).
function Talents.FreePoints()
  return R2F.Minimap.FreeTalentPoints()
end

-- Tree names for the mini-tree headers. GetTalentTabInfo's returns differ by
-- client generation (13.6 avoided it for that reason): Classic-era clients
-- return name first, newer ones id (a number) then name. Take whichever is
-- the first string; anything else (missing API, error, odd shape) falls back
-- to "Tree 1" etc. Only the header text depends on this, never the mapping.
function Talents.TreeName(tab)
  if GetTalentTabInfo then
    local ok, a, b = pcall(GetTalentTabInfo, tab)
    if ok then
      if type(a) == "string" and a ~= "" then return a end
      if type(b) == "string" and b ~= "" then return b end
    end
  end
  return L.TALENT_TREE_N:format(tab)
end

-- The order points would be learned in (13.5): tier 1 of all trees, then
-- tier 2, ...; within a tier tree order, then column. With fewer free points
-- than the build needs this fills from the top, which always satisfies the
-- 5-points-per-tier rule and prerequisites (they sit higher up). Step 9 uses
-- it to say which points come "now" and which "later"; step 10 learns in it.
function Talents.LearnOrder(plan)
  local list = {}
  for _, tree in ipairs(plan.trees) do
    for _, e in ipairs(tree.talents) do
      if (e.add or 0) > 0 then list[#list + 1] = e end
    end
  end
  table.sort(list, function(a, b)
    if a.tier ~= b.tier then return a.tier < b.tier end
    if a.tab ~= b.tab then return a.tab < b.tab end
    if a.column ~= b.column then return a.column < b.column end
    return a.index < b.index
  end)
  return list
end

local function points(n)
  return n == 1 and L.TALENT_POINT_ONE or L.TALENT_POINTS:format(n)
end

-- The summary line (13.4) for a plan. Returns text, kind:
--   "conflict" (red, Learn stays disabled), "nopoints", "done", "empty",
--   "all", "partial". Link problems (over max rank, no such talent) come
--   before "you have points this build doesn't use": a trainer reset can't
--   fix a bad link, so that's the more useful thing to say first.
local function conflictText(c)
  local e = c.talent
  if c.kind == "overmax" then
    return L.TALENT_CONFLICT_OVERMAX:format(points(e.planned), e.name, e.maxRank)
  elseif c.kind == "nospot" then
    return L.TALENT_CONFLICT_NOSPOT:format(c.treeName)
  elseif c.kind == "notree" then
    return L.TALENT_CONFLICT_NOTREE
  elseif e.planned == 0 then
    return L.TALENT_CONFLICT_UNUSED:format(points(e.rank), e.name)
  end
  return L.TALENT_CONFLICT_FEWER:format(points(e.rank), e.name, e.planned)
end

function Talents.Summary(plan)
  local first = plan.conflicts[1]
  if first then return conflictText(first), "conflict" end
  if plan.total == 0 then return L.TALENT_SUMMARY_EMPTY, "empty" end
  if plan.need == 0 then return L.TALENT_SUMMARY_DONE, "done" end
  if plan.free <= 0 then return L.TALENT_SUMMARY_NO_POINTS, "nopoints" end
  -- 13.4's two wordings, exactly, when none of the build is learned yet
  -- (the normal case). When part of it already is (a half-learned build
  -- after leveling), "uses 21 points ... All 21 will be learned" would be
  -- wrong, so the head says how many are already learned (13.7).
  local head = plan.have > 0 and L.TALENT_USES_HAVE:format(points(plan.total), plan.have)
    or L.TALENT_USES:format(points(plan.total))
  if plan.need <= plan.free then
    local tail = plan.need == 1 and L.TALENT_WILL_ONE or L.TALENT_WILL_ALL:format(plan.need)
    return head .. " " .. L.TALENT_FREE:format(plan.free) .. " " .. tail, "all"
  end
  return head .. " " .. L.TALENT_FREE_PART:format(plan.free, plan.learnNow, plan.learnLater), "partial"
end

-- Maps a link's digits onto the game's trees and works out every talent's
-- preview state. Takes the game state as arguments (the only API it calls is
-- the read-only GetTalentTabInfo, for header names), so the tests can feed it
-- any state.
--   trees = ReadTrees() output, codes = ParseLink(...).codes (or {} = "no
--   build": everything you have counts as kept), free = unspent points.
-- Per talent (on the ReadTrees entry's copy): planned, add (points to learn),
-- now / later (of add), state:
--   "learned"  you have it and the build wants exactly that (rank shown)
--   "now"      the build wants more and some of it fits in your free points
--   "later"    the build wants more, but no free points are left for it yet
--   "off"      not in the build, no points in it
--   "conflict" you have more points than the build wants (red, blocks Learn)
--   "overmax"  the link asks for more than the talent's max rank (red)
-- Conflicts still get a preview (the trees show WHERE the problem is, which
-- is what the player needs to fix it); they only block learning (13.4).
function Talents.Plan(trees, codes, free)
  local plan = { trees = {}, conflicts = {}, total = 0, have = 0, need = 0,
                 free = math.max(tonumber(free) or 0, 0) }
  local linkProblems, unused = {}, {}
  for t, list in ipairs(trees) do
    local code = codes[t] or ""
    local tree = { name = Talents.TreeName(t), talents = {}, current = 0, planned = 0 }
    for k, x in ipairs(list) do
      -- Digit k = planned rank of the k-th talent in tier/column order (13.2).
      -- Missing trailing digits = 0: the site strips trailing zeros from every
      -- tree (and drops empty trailing trees), so a short code is normal.
      local planned = tonumber(code:sub(k, k)) or 0
      local e = { name = x.name, icon = x.icon, tier = x.tier, column = x.column, rank = x.rank,
                  maxRank = x.maxRank, index = x.index, tab = t, planned = planned,
                  add = 0, now = 0, later = 0 }
      tree.current = tree.current + x.rank
      tree.planned = tree.planned + planned
      plan.total = plan.total + planned
      if planned > x.maxRank then
        -- The hash covers names only (13.6), so a matching hash can't vouch
        -- for max ranks: this check runs on every link (13.3).
        e.state = "overmax"
        linkProblems[#linkProblems + 1] = { kind = "overmax", talent = e }
      elseif x.rank > planned then
        e.state = "conflict"
        unused[#unused + 1] = { kind = "unused", talent = e }
      else
        e.add = planned - x.rank
        plan.have = plan.have + x.rank
        plan.need = plan.need + e.add
      end
      tree.talents[k] = e
    end
    -- Points for a position past the tree's last talent: the link was made
    -- for a tree with more talents than the game's (13.3's "no points in a
    -- tree position that doesn't exist"). Zeros there are harmless.
    if code:sub(#list + 1):find("[1-9]") then
      linkProblems[#linkProblems + 1] = { kind = "nospot", tab = t, treeName = tree.name }
    end
    plan.trees[t] = tree
  end
  -- A whole tree more than the class has, with points in it.
  for t = #trees + 1, #codes do
    if codes[t]:find("[1-9]") then
      linkProblems[#linkProblems + 1] = { kind = "notree", tab = t }
      break
    end
  end
  for _, c in ipairs(linkProblems) do plan.conflicts[#plan.conflicts + 1] = c end
  for _, c in ipairs(unused) do plan.conflicts[#plan.conflicts + 1] = c end

  -- Now / later: hand out the free points in learning order.
  local left = plan.free
  plan.learnNow = 0
  for _, e in ipairs(Talents.LearnOrder(plan)) do
    e.now = math.min(e.add, left)
    e.later = e.add - e.now
    left = left - e.now
    plan.learnNow = plan.learnNow + e.now
  end
  plan.learnLater = plan.need - plan.learnNow
  for _, tree in ipairs(plan.trees) do
    for _, e in ipairs(tree.talents) do
      if not e.state then
        if e.add == 0 then
          e.state = e.rank > 0 and "learned" or "off"
        else
          e.state = e.now > 0 and "now" or "later"
        end
      end
    end
  end
  plan.summary, plan.kind = Talents.Summary(plan)
  -- What step 10's Learn button will need. Step 9 never enables the button.
  plan.learnable = #plan.conflicts == 0 and plan.need > 0 and plan.free > 0
  return plan
end

-- The character's own trees with no build applied (what the Talents tab shows
-- before a preview, after Cancel, and behind a stop message).
function Talents.CurrentPlan()
  local trees = Talents.ReadTrees()
  if not trees then return nil end
  local codes = {}
  for t, list in ipairs(trees) do
    local d = {}
    for k, x in ipairs(list) do d[k] = tostring(x.rank) end
    codes[t] = table.concat(d)
  end
  return Talents.Plan(trees, codes, Talents.FreePoints())
end

-- Preview (13.2 - 13.4): text -> result.
--   { error = text }               stop: nothing to preview (red). Bad link,
--                                  wrong class, talents unreadable, or a hash
--                                  that doesn't match (13.3).
--   { plan = Plan(...), caution }  preview; caution = the yellow line for a
--                                  link that couldn't be checked (no hash, or
--                                  a non-English client), else nil.
-- Read-only, so no combat check (13.7): it parses a string and reads talent
-- info, both allowed in combat, and calls nothing protected.
function Talents.Preview(text)
  local link = Talents.ParseLink(text)
  if not link then return { error = L.TALENT_BAD_LINK } end
  local mine = Talents.ClassId()
  if not mine then return { error = L.TALENT_READ_FAILED_TAB, link = link } end
  if link.class ~= mine then
    return { error = L.TALENT_WRONG_CLASS:format(Talents.ClassName(link.class), Talents.ClassName(mine)),
             link = link }
  end
  local trees = Talents.ReadTrees()
  if not trees then return { error = L.TALENT_READ_FAILED_TAB, link = link } end
  local caution
  if not link.hash then
    -- Old (pre-step-8) link: allowed, with 13.3's yellow line. The sanity
    -- checks in Plan still run.
    caution = L.TALENT_NO_HASH
  elseif link.hash ~= Talents.Hash(trees) then
    if Talents.IsEnglishClient() then
      -- 13.3: different trees -> stop, no preview, no plan. A digit can't be
      -- trusted to mean the same talent here as on the site.
      return { error = L.TALENT_HASH_MISMATCH, link = link }
    end
    -- Non-English client: the names are translated, so the hash can't match
    -- even when the trees are identical (13.6). Refusing would lock every
    -- non-English player out for good, so this is treated exactly like an
    -- old link without a hash (13.7): can't check, say so, sanity checks
    -- still apply.
    caution = L.TALENT_HASH_LOCALE
  end
  return { plan = Talents.Plan(trees, link.codes, Talents.FreePoints()), caution = caution, link = link }
end
