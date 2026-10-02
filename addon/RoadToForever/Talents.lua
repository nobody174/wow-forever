-- Talents.lua: talent links (ADDON_PLAN.md 13).
--   Step 8: read the character's talents in the site's link order, build the
--           link with its ~hash (Copy my build, 13.4).
--   Step 9: read a pasted link (13.2), check it against the game (13.3) and
--           work out the preview: per talent learned / now / later / not in
--           the build / conflict, plus the summary line (13.4).
--   Step 10: the learning engine (13.5, decisions in ADDON_PLAN 13.8), at the
--           end of this file.
--
-- Steps 8 and 9 are read-only: they only call GetNumTalentTabs /
-- GetNumTalents / GetTalentInfo / GetTalentTabInfo / UnitCharacterPoints /
-- GetLocale and show our own copy box, which is all allowed in combat, so the
-- InCombatLockdown() / RunOrQueue pattern that guards macro writes (6.4, 6.9)
-- doesn't apply to them (ADDON_PLAN 13.6, 13.7).
-- Step 10 is the one irreversible write in the addon: the ONLY LearnTalent
-- call is learnPoint() below, every point is checked against combat first,
-- and nothing learns while R2F.InCombat() is true (13.8).

local _, R2F = ...
local L = R2F.L

local Talents = {}
R2F.Talents = Talents

Talents.SITE_URL = "https://nobody174.github.io/wow-forever-macros/talents.html#"

-- GetNumTalentTabs/GetNumTalents/GetTalentInfo (and PlayerTalentFrame) are not
-- globals until Blizzard's own on-demand UI addon, Blizzard_TalentUI, has
-- loaded -- normally only when the player opens the real Talent window by
-- hand, same as Blizzard_Calendar/Blizzard_MacroUI/etc. (confirmed 2026-10-02
-- against a real WoW Forever client: an addon already running there,
-- RXPGuides, waits on ADDON_LOADED("Blizzard_TalentUI") for exactly this
-- reason). Force-loading it here means Preview/Copy my build work the first
-- time, without the player having to separately open the Talent window first
-- -- same IsAddOnLoaded + LoadAddOn pattern already proven working on this
-- client by RXPGuides' own Blizzard_Calendar load. C_AddOns is tried first,
-- same as every other API-era check in this addon (ADDON_PLAN.md 12.4.2).
local IsAddOnLoaded = (C_AddOns and C_AddOns.IsAddOnLoaded) or _G.IsAddOnLoaded
local LoadAddOn = (C_AddOns and C_AddOns.LoadAddOn) or _G.LoadAddOn

local function ensureTalentUI()
  if not (IsAddOnLoaded and LoadAddOn) then return end
  local ok, loaded = pcall(IsAddOnLoaded, "Blizzard_TalentUI")
  if ok and not loaded then pcall(LoadAddOn, "Blizzard_TalentUI") end
end

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
  ensureTalentUI()
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
  -- Step 10's Learn button is enabled from exactly this (plus "not in combat,
  -- not already learning"), so a plan with ANY conflict can never be learned.
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

-- ===========================================================================
-- Step 10: learning (13.5; decisions in ADDON_PLAN 13.8)
-- ===========================================================================
--
-- Why a state machine and not a loop: the game confirms a point
-- asynchronously (the server answers, then CHARACTER_POINTS_CHANGED fires),
-- so "learn 21 points" is 21 round trips. A loop calling LearnTalent 21 times
-- in one go would send points whose tier requirement depends on points the
-- server hasn't confirmed yet, and could notice neither a refused point nor
-- combat starting halfway. So: one point, wait for the answer, re-check the
-- live game, next point. Everything a run needs is in `run`, so it can stop
-- at any moment (combat, a refused point, the Stop button) and continue from
-- the same place when Learn talents is clicked again.
--
-- `run` lives for this session only (a file local, not SavedVariables): after
-- a /reload the remembered link (lastTalentLink) previews what's left and a
-- new Learn click asks again. Resuming from saved data, possibly days later,
-- would act on a confirmation the player gave in another situation.

Talents.LEARN_TIMEOUT = 0.5   -- 13.5: how long to wait for the server's answer

local run            -- the current / last run (see Talents.StartLearn)
-- worked: LearnTalent has landed a point this session (so addons may use it).
-- blocked: it was refused with no other explanation before ever working, so
-- this client probably blocks it for addons -> guided mode (13.5's fallback).
local session = { worked = false, blocked = false }
local message        -- { text =, kind = "stop" | "done" | "info" } for the tab

local function say(text, kind)
  message = { text = text, kind = kind }
  R2F.Print(text)
end

-- Redraw the Talents tab (label "Learning X / N", locks, trees). It's a
-- no-op while the tab isn't showing; the run itself never depends on the UI.
local function notify()
  if R2F.TalentPanel then R2F.TalentPanel.Refresh() end
end

-- The points the confirm popup promises, one entry per point, in 13.5's order:
-- Talents.LearnOrder, the very list step 9's preview hands its "now" points
-- out from (13.7), so the run learns exactly the gold +N cells, in that order.
-- target = the talent's rank once this point has landed.
function Talents.LearnPoints(plan)
  local out = {}
  for _, e in ipairs(Talents.LearnOrder(plan)) do
    for k = 1, e.now do
      out[#out + 1] = { tab = e.tab, index = e.index, name = e.name, tier = e.tier,
                        column = e.column, target = e.rank + k }
    end
  end
  return out
end

-- Which way talents get learned on this client (13.5, 13.8):
--   "preview"  Blizzard's own preview/commit API exists AND is switched on
--              (Wrath-style; the previewTalents CVar). 13.5: prefer it. We
--              only fill Blizzard's preview; its own Learn button commits.
--   "direct"   LearnTalent(tab, index), one point at a time (Classic).
--   "guided"   no LearnTalent at all, or this session saw it refused with no
--              other explanation before it ever worked: we point at the
--              talent to click in Blizzard's own window instead.
-- The CVar test matters: a client can carry the preview functions without
-- the feature being on (shared code), and filling a preview nobody sees
-- would learn nothing.
function Talents.LearnMode()
  if type(AddPreviewTalentPoints) == "function" and type(LearnPreviewTalents) == "function"
     and GetCVarBool then
    local ok, on = pcall(GetCVarBool, "previewTalents")
    if ok and on then return "preview" end
  end
  if type(LearnTalent) == "function" and not session.blocked then return "direct" end
  return "guided"
end

local function packed(...) return { n = select("#", ...), ... } end

-- Prerequisites (13.5: "double-check ... GetTalentPrereqs"). Classic returns
-- tier, column, isLearnable per prerequisite. We look the prerequisite up in
-- the live tree and require it maxed (the Classic rule) rather than trust
-- isLearnable, whose exact meaning can't be confirmed outside the game.
-- No API or an error: no extra check here; the server still refuses an
-- illegal point and the rank re-read after LearnTalent stops the run then.
local function prereqsMet(p, tree)
  if not GetTalentPrereqs then return true end
  local got = packed(pcall(GetTalentPrereqs, p.tab, p.index))
  if not got[1] then return true end
  for i = 2, got.n, 3 do
    local tier, column = got[i], got[i + 1]
    if type(tier) == "number" and type(column) == "number" then
      for _, x in ipairs(tree.talents) do
        if x.tier == tier and x.column == column and x.rank < x.maxRank then return false end
      end
    end
  end
  return true
end

-- Re-check ONE point against the live game right before it's spent. The
-- point list was made when the popup opened; since then the player may have
-- spent points in Blizzard's window, levelled, entered combat and left it, or
-- the server refused something. So nothing precomputed is trusted for the
-- write itself: the whole preview is re-run (hash, sanity checks, conflicts)
-- and the tier rule and prerequisites are checked on live ranks.
-- Returns "ok" | "have" (the game already has this rank) | "nopoints" |
-- "locked" (tier / prerequisite not met) | "changed" (trees or build moved).
local function verify(r, p)
  local plan = Talents.Preview(r.text).plan
  if not plan or #plan.conflicts > 0 then return "changed" end
  local tree = plan.trees[p.tab]
  local e
  for _, x in ipairs(tree and tree.talents or {}) do
    if x.index == p.index then e = x; break end
  end
  if not e or e.name ~= p.name then return "changed" end
  if e.rank >= p.target then return "have" end
  -- Points go one at a time and in order, so this talent is exactly one short.
  if e.rank ~= p.target - 1 then return "changed" end
  if Talents.FreePoints() <= 0 then return "nopoints" end
  -- Classic tier rule: 5 points in this tree per tier above the first.
  if tree.current < (e.tier - 1) * 5 then return "locked" end
  if not prereqsMet(p, tree) then return "locked" end
  return "ok"
end

local function liveRank(p)
  if not GetTalentInfo then return nil end
  local name, _, _, _, rank = GetTalentInfo(p.tab, p.index)
  if name ~= p.name then return nil end
  return rank or 0
end

-- Stops that "Learn talents" can pick up again from the same point. The
-- others (no points, tier/prerequisite, trees changed) need a fresh preview,
-- so the next click starts over with a new popup.
local RESUMABLE = { combat = true, user = true, rejected = true }

local function stopText(r, why, name)
  if why == "combat" then return L.TALENT_STOP_COMBAT:format(r.done, r.total) end
  if why == "user" then return L.TALENT_STOP_USER:format(r.done, r.total) end
  if why == "rejected" then
    local text = L.TALENT_STOP_REJECTED:format(name, r.done, r.total)
    if session.blocked then text = text .. " " .. L.TALENT_BLOCKED_HINT end
    return text
  end
  if why == "locked" then return L.TALENT_STOP_LOCKED:format(name, r.done, r.total) end
  if why == "nopoints" then return L.TALENT_STOP_NOPOINTS:format(r.done, r.total) end
  return L.TALENT_STOP_CHANGED:format(r.done, r.total)
end

local function stop(r, why, p)
  r.phase, r.why = "stopped", why
  -- New token: a timeout or event still on its way for the old point is
  -- ignored (the point may still land; lateCheck counts it then).
  r.token = r.token + 1
  r.resumable = RESUMABLE[why] or false
  R2F.TalentGuide.Hide()
  say(stopText(r, why, p and p.name or ""), "stop")
  notify()
end

local function finish(r)
  r.phase = "done"
  r.token = r.token + 1
  R2F.TalentGuide.Hide()
  say(r.done == 1 and L.TALENT_LEARNED_ONE or L.TALENT_LEARNED:format(r.done), "done")
  notify()
end

-- The next point to spend, skipping points the game already has (spent by the
-- player in Blizzard's window, or an answer that arrived after a stop).
-- Returns the point, or nil after stopping or finishing the run.
local function nextPoint(r)
  while true do
    local p = r.points[r.pos]
    if not p then finish(r); return nil end
    local check = verify(r, p)
    if check == "have" then
      r.done, r.pos = r.done + 1, r.pos + 1
    elseif check == "ok" then
      return p
    else
      stop(r, check, p)
      return nil
    end
  end
end

-- The ONLY LearnTalent call in the addon (Taint & secure execution, 6.6).
-- Combat is checked here, at the write, not just when the button was clicked:
-- a run spans many server round trips and combat can start between any two.
-- R2F.InCombat() also covers the moment PLAYER_REGEN_DISABLED is handled,
-- when InCombatLockdown() is still false (6.7).
local function learnPoint(p)
  if R2F.InCombat() then return false, "combat" end
  if not pcall(LearnTalent, p.tab, p.index) then return false, "rejected" end
  return true
end

local stepDirect, settle

local function reject(r, p)
  r.waiting = nil
  r.late = p          -- if the answer was only slow, lateCheck still counts it
  if not session.worked then session.blocked = true end
  stop(r, "rejected", p)
end

-- One point, then wait: CHARACTER_POINTS_CHANGED (OnPointsChanged) or the
-- timeout, whichever comes first, decides via settle().
stepDirect = function(r)
  if run ~= r or r.phase ~= "learning" then return end
  if R2F.InCombat() then return stop(r, "combat", r.points[r.pos]) end
  local p = nextPoint(r)
  if not p then return end
  r.waiting = p
  r.token = r.token + 1
  local tok = r.token
  notify()
  local ok, why = learnPoint(p)
  if not ok then
    r.waiting = nil
    if why == "combat" then return stop(r, "combat", p) end
    return reject(r, p)
  end
  -- ADDON_ACTION_FORBIDDEN can fire inside the LearnTalent call itself and
  -- has already stopped the run (Talents.OnActionBlocked).
  if r.phase ~= "learning" then return end
  if C_Timer and C_Timer.After then
    C_Timer.After(Talents.LEARN_TIMEOUT, function() settle(r, tok, true) end)
  end
end

-- Did the point land? Re-read the rank (13.5). Not yet on an event: keep
-- waiting (the event also fires for other reasons, e.g. a level-up). Not
-- yet when it's final (the timeout): stop, never continue past it.
-- resend = this was a point from before a stop that we only waited for (see
-- begin): not there after the wait = it never got through, so send it now.
settle = function(r, tok, final, resend)
  if run ~= r or r.token ~= tok or r.phase ~= "learning" or not r.waiting then return end
  local p = r.waiting
  local rank = liveRank(p)
  if rank and rank >= p.target then
    r.waiting = nil
    r.done, r.pos = r.done + 1, r.pos + 1
    session.worked, session.blocked = true, false
    stepDirect(r)
  elseif final and resend then
    r.waiting = nil
    stepDirect(r)
  elseif final then
    reject(r, p)
  end
end

-- After a stop, the point that was on its way may still land (a slow
-- server, or combat started right after it was sent). Count it, and if it
-- was a "refused" stop, LearnTalent does work after all: no guided mode.
local function lateCheck(r)
  local p = r.late
  if not p then return end
  local rank = liveRank(p)
  if not (rank and rank >= p.target) then return end
  r.late = nil
  session.worked, session.blocked = true, false
  if r.points[r.pos] == p then r.done, r.pos = r.done + 1, r.pos + 1 end
  if r.pos > r.total then return finish(r) end
  if r.why == "rejected" then
    say(L.TALENT_LATE:format(p.name, r.done, r.total), "stop")
  else
    say(stopText(r, r.why, p.name), "stop")
  end
  notify()
end

-- Guided mode: show the next point in Blizzard's window and wait for the
-- player's click (CHARACTER_POINTS_CHANGED calls this again). The same
-- verify() runs before every point, so a click on the wrong talent stops it.
local function stepGuided(r)
  if run ~= r or r.phase ~= "guided" then return end
  if R2F.InCombat() then return stop(r, "combat", r.points[r.pos]) end
  local p = nextPoint(r)
  if not p then return end
  if r.shown ~= r.pos then
    r.shown = r.pos
    R2F.Print(L.TALENT_GUIDE_CLICK:format(p.name, r.done + 1, r.total))
  end
  R2F.TalentGuide.Show(p, r.done + 1, r.total, Talents.TreeName(p.tab))
  notify()
end

local function begin(r)
  if run ~= r then return end       -- cancelled while it waited for combat to end
  local pending = r.late
  r.waiting, r.late, r.shown = nil, nil, nil
  message = nil
  if Talents.LearnMode() == "guided" then
    r.mode, r.phase = "guided", "guided"
    if R2F.TalentGuide.OpenTalentWindow() then
      R2F.Print(L.TALENT_GUIDE_START)
    else
      R2F.Print(L.TALENT_GUIDE_OPEN)
    end
    stepGuided(r)
    return
  end
  r.mode, r.phase = "direct", "learning"
  if pending and C_Timer and C_Timer.After then
    -- A point sent before the stop may still be on its way (Stop, then Learn
    -- talents clicked right away). Sending it again now could land BOTH: one
    -- rank more than the build wants, in a talent that may be at its planned
    -- maximum, which only a trainer reset undoes. So wait for it first,
    -- exactly like for a point just sent; only if it's still not there after
    -- the timeout is it sent again (settle's resend). Without C_Timer there's
    -- no way to wait; it is sent again at once (every Classic Era client has
    -- C_Timer, 13.8).
    r.waiting = pending
    r.token = r.token + 1
    local tok = r.token
    notify()
    C_Timer.After(Talents.LEARN_TIMEOUT, function() settle(r, tok, true, true) end)
    return
  end
  stepDirect(r)
end

-- After the confirm popup's Learn (TalentPanel). `list` = LearnPoints(plan)
-- as counted in the popup: a run never learns more than the player agreed to,
-- even if a level-up adds points meanwhile. Accepted in combat (popup opened
-- before combat): the start waits for PLAYER_REGEN_ENABLED in
-- Macros.RunOrQueue, the queue every confirmed write in the addon uses (6.9),
-- and begin() re-checks everything when it runs. Returns the run.
function Talents.StartLearn(text, list)
  local r = { text = text, points = list, total = #list, done = 0, pos = 1,
              phase = "queued", token = 0, resumable = false }
  run = r
  message = nil
  notify()
  R2F.Macros.RunOrQueue(function() begin(r) end, L.TALENT_LEARN_QUEUED)
  return r
end

-- A stopped run for this exact link that Learn talents can continue (13.5:
-- "Click Learn talents to continue"); no second popup, same X of Y.
function Talents.CanResume(text)
  local r = run
  return r ~= nil and r.phase == "stopped" and r.resumable and r.text == text and r.pos <= r.total
end

function Talents.ResumeLearn()
  local r = run
  if not (r and r.phase == "stopped" and r.resumable) then return false end
  begin(r)
  return true
end

-- The tab's Stop button. A point already sent may still land (lateCheck).
function Talents.StopLearn()
  local r = run
  if not r then return end
  if r.phase == "queued" then
    run, message = nil, nil        -- the queued start finds run ~= r and does nothing
    notify()
  elseif r.phase == "learning" or r.phase == "guided" then
    if r.waiting then r.late, r.waiting = r.waiting, nil end
    stop(r, "user", r.points[r.pos])
  end
end

function Talents.LearnBusy()
  local r = run
  return r ~= nil and (r.phase == "queued" or r.phase == "learning" or r.phase == "guided")
end

-- New link previewed or Cancel: forget a stopped / finished run and its
-- message. Refused while a run is active (the tab is locked then anyway).
function Talents.ResetLearn()
  if Talents.LearnBusy() then return false end
  run, message = nil, nil
  R2F.TalentGuide.Hide()
  return true
end

-- { phase = "idle" | "queued" | "learning" | "guided" | "stopped" | "done",
--   mode, done, total, current (the point being learned, 1-based), text,
--   resumable, point }
function Talents.LearnStatus()
  local r = run
  if not r then return { phase = "idle" } end
  return { phase = r.phase, mode = r.mode, done = r.done, total = r.total,
           current = math.min(r.done + 1, r.total), text = r.text, resumable = r.resumable,
           point = r.points[r.pos] }
end

function Talents.LearnMessage() return message end

-- CHARACTER_POINTS_CHANGED (Core.lua, before the tab's refresh).
function Talents.OnPointsChanged()
  local r = run
  if not r then return end
  if r.phase == "learning" and r.waiting then
    -- Without C_Timer there is no timeout, so this event is the final word.
    settle(r, r.token, not (C_Timer and C_Timer.After))
  elseif r.phase == "guided" then
    stepGuided(r)
  elseif r.phase == "stopped" then
    lateCheck(r)
  end
end

-- PLAYER_REGEN_DISABLED (Core.lua): stop AT ONCE, mid-run (13.5), not only
-- refuse to start. The point already sent can't be called back; it is
-- counted if it lands (lateCheck). No new LearnTalent goes out after this:
-- learnPoint checks R2F.InCombat(), which is true from this event on.
function Talents.OnCombat()
  local r = run
  if r and (r.phase == "learning" or r.phase == "guided") then
    if r.waiting then r.late, r.waiting = r.waiting, nil end
    stop(r, "combat", r.points[r.pos])
  end
end

-- ADDON_ACTION_FORBIDDEN / ADDON_ACTION_BLOCKED (Core.lua, our addon only):
-- the game's own word that it refused a call. For LearnTalent that is the
-- clearest "blocked for addons" signal there is (13.5's guided fallback), so
-- it switches this session to guided mode at once, even if a point worked
-- before, and the point in flight is settled as refused now.
function Talents.OnActionBlocked(fn)
  if type(fn) ~= "string" or not fn:find("LearnTalent", 1, true) then return end
  session.blocked, session.worked = true, false
  local r = run
  if r and r.phase == "learning" and r.waiting then settle(r, r.token, true) end
end

-- "preview" mode (13.5: if the client has Blizzard's preview API, use it and
-- let Blizzard's own Learn button confirm): put the points into Blizzard's
-- preview in the same order and open the talent window. Nothing is learned
-- until the player clicks Blizzard's button, so our popup isn't shown, and
-- LearnPreviewTalents (the commit) is never called by us. Returns the number
-- of points placed.
function Talents.FillPreview(plan)
  if R2F.InCombat() then return 0 end
  local n = 0
  for _, e in ipairs(Talents.LearnOrder(plan)) do
    if e.now > 0 then
      if not pcall(AddPreviewTalentPoints, e.tab, e.index, e.now) then break end
      n = n + e.now
    end
  end
  R2F.TalentGuide.OpenTalentWindow()
  say(L.TALENT_PREVIEW_FILLED:format(n), "info")
  notify()
  return n
end

-- Test hook: forget what this session learned about LearnTalent.
function Talents.ResetSession() session.worked, session.blocked = false, false end
