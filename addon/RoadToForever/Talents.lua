-- Talents.lua: talent links (ADDON_PLAN.md 13).
--   Step 8: read the character's talents in the site's link order, build the
--           link with its ~hash (Copy my build, 13.4).
--   Step 9: read a pasted link (13.2), check it against the game (13.3) and
--           work out the preview: per talent learned / now / later / not in
--           the build / conflict, plus the summary line (13.4).
--   Step 10: the learning engine (13.5, decisions in ADDON_PLAN 13.8), at the
--           end of this file.
--
-- Steps 8 and 9 are read-only: they only call the C_Traits /
-- C_SpecializationInfo readers (13.10), GetTalentTabInfo, UnitCharacterPoints
-- and GetLocale and show our own copy box, which is all allowed in combat, so the
-- InCombatLockdown() / RunOrQueue pattern that guards macro writes (6.4, 6.9)
-- doesn't apply to them (ADDON_PLAN 13.6, 13.7).
-- Step 10 is the one irreversible write in the addon: the ONLY LearnTalent
-- call is learnPoint() below, every point is checked against combat first,
-- and nothing learns while R2F.InCombat() is true (13.8).
-- 13.12 adds the "traits" mode for WoW Forever: the ONLY C_Traits writes
-- (PurchaseRank, CommitConfig) are in purchasePoint() below, under the same
-- rules, plus a two-way read-back and a fall back to guided mode on anything
-- unexpected. It also moves the free-points source here (FreePointsInfo).

local _, R2F = ...
local L = R2F.L

local Talents = {}
R2F.Talents = Talents

Talents.SITE_URL = "https://nobody174.github.io/wow-forever-macros/talents.html#"

-- ---------------------------------------------------------------------------
-- Reading the talents: C_Traits (ADDON_PLAN 13.10)
-- ---------------------------------------------------------------------------
-- WoW Forever runs Classic's talent trees on the modern engine's trait
-- system, so the Classic globals (GetNumTalentTabs / GetTalentInfo) don't
-- exist at all -- not even after LoadAddOn("Blizzard_TalentUI"), which
-- answers false, "MISSING" there (13.9's premise was wrong; 13.10). The chain
-- below is the one WeakAuras Forever's Private.GetTalentData uses on the same
-- client, confirmed with live /dump output (13.10): active spec group ->
-- combat config -> config.treeIDs -> nodes -> entry -> definition -> spell.
--
-- Every call is guarded: the config may not exist yet right after login, and
-- a missing namespace or function must mean "can't read yet" (nil), never a
-- Lua error, same as every API check in this addon.
local function call(fn, ...)
  if type(fn) ~= "function" then return nil end
  local ok, a = pcall(fn, ...)
  if ok then return a end
  return nil
end

local function spellName(id)
  if C_Spell and C_Spell.GetSpellName then
    local n = call(C_Spell.GetSpellName, id)
    if n then return n end
  end
  return call(GetSpellInfo, id)
end

local function spellIcon(id)
  if C_Spell and C_Spell.GetSpellTexture then
    local t = call(C_Spell.GetSpellTexture, id)
    if t then return t end
  end
  return call(GetSpellTexture, id)
end

-- Distinct values of `key` over `nodes`, sorted ascending, as value -> rank
-- (1-based). Why ranks and not arithmetic: the 8 real Paladin nodes (13.10)
-- show posX/posY are Wowhead's col/row grid scaled by 600 with an offset, but
-- nothing promises the same scale or offset for every tree or class. Only the
-- ORDER of the distinct values is relied on, which survives any scale/offset.
local function ranks(nodes, key)
  local seen, list = {}, {}
  for _, n in ipairs(nodes) do
    local v = n[key]
    if not seen[v] then seen[v] = true; list[#list + 1] = v end
  end
  table.sort(list)
  local out = {}
  for i, v in ipairs(list) do out[v] = i end
  return out, #list
end
Talents.GridRanks = ranks   -- test hook (run_tests.py's real-data check, 13.10)

-- Jitter tolerance (ADDON_PLAN 13.11). Blizzard's own layout data is not
-- exactly on the grid: the full live dump of Paladin's tree 1100 (all 50
-- nodes) has 13 distinct posX values, and Protection's first column comes as
-- BOTH 5020 and 5030 -- 10 units apart, where every real column step in the
-- data is 590-600. Ranking raw values counted that as a fifth Protection
-- column, the "more than 4 columns" check refused the tree, and the player
-- got "couldn't read your talents". So before ranking, values that are much
-- closer together than a real grid step are snapped onto one grid line.
--
-- Why relative and not a fixed number of units: 13.10 chose ranks precisely
-- because nothing promises the same scale for every class and tree (a
-- threshold of, say, 100 would swallow whole columns on a grid with a step of
-- 60, and miss jitter of 300 on a step of 6000). The step is estimated from
-- the values themselves: the median of the gaps between consecutive distinct
-- values. Real steps are the large majority of gaps; jitter (too small) and
-- pane gutters (too big) are the outliers on either side, and a median
-- ignores outliers on both sides as long as they are fewer than half (the
-- UPPER median, so exactly half jitter gaps still finds the step). Then a gap
-- under SNAP_FRACTION of that step joins the current cluster. 0.2 leaves wide
-- margins both ways: the real jitter is 10 / 600 = 1.7% of a step, and a
-- real neighbouring column, even one a third of a step away, is kept apart.
-- If jitter were ever the majority of gaps, the median would be a jitter gap,
-- nothing would merge, and the column / tier count checks refuse: "can't
-- read", never a wrong mapping.
-- Proven on real data: X jitter (5020 / 5030). Y is snapped the same way as a
-- precaution; Y jitter has not been seen (the 8 dumped Holy posY are exact,
-- the other panes' posY weren't in the report).
-- Failing to snap is the safe direction: jitter is far below a step, so an
-- unsnapped value still sorts between the same neighbours (one talent per
-- cell), and the count checks refuse. Snapping two REAL lines together is the
-- dangerous one (two talents in one cell, order left to the index tiebreak),
-- which is why the fraction is small.
Talents.SNAP_FRACTION = 0.2

-- Distinct values of `key` over `nodes` -> snapped value (the cluster's
-- smallest value; only the order of the snapped values is used afterwards).
local function snapGrid(nodes, key)
  local seen, list = {}, {}
  for _, n in ipairs(nodes) do
    local v = n[key]
    if not seen[v] then seen[v] = true; list[#list + 1] = v end
  end
  table.sort(list)
  local gaps = {}
  for i = 2, #list do gaps[#gaps + 1] = list[i] - list[i - 1] end
  table.sort(gaps)
  local step = gaps[math.floor(#gaps / 2) + 1]
  local tol = step and step * Talents.SNAP_FRACTION or 0
  local out, anchor = {}, nil
  for _, v in ipairs(list) do
    -- Measured from the cluster's first value, not the previous one, so a
    -- run of small gaps can't chain distinct grid lines into one cluster.
    if anchor == nil or v - anchor >= tol then anchor = v end
    out[v] = anchor
  end
  return out
end
Talents.GridSnap = snapGrid  -- test hook (13.11)

-- Sets n[to] = the snapped value of n[from] on every node.
local function snapNodes(nodes, from, to)
  local snap = snapGrid(nodes, from)
  for _, n in ipairs(nodes) do n[to] = snap[n[from]] end
end

-- The three Classic panes (e.g. Holy / Protection / Retribution) inside ONE
-- trait tree. Paladin's config has a single treeID (1100) with 50 nodes, i.e.
-- all three panes in one tree (13.10); in the real Talents window they are
-- three side-by-side column groups sharing the same rows. So the panes are
-- found by X: the two widest gaps between consecutive distinct X values
-- are the gutters between panes. Inside a pane neighbouring columns are one
-- grid step apart, so a gutter only loses to an inner gap if a pane had two
-- empty columns side by side. When the split isn't clear-cut (fewer than 3
-- distinct X values, or a tie between the 2nd and 3rd widest gap) this
-- returns nil: "can't read" is safe, a wrong split would map link digits onto
-- the wrong talents (the ~hash would catch it, but nil says it earlier).
-- Reads the snapped gridX (13.11), so the panes are cut on exactly the values
-- their columns are counted on. Jitter gaps are the smallest gaps of all, so
-- they could never be taken for a gutter either way (real data: gutters 2200
-- and 2260, columns 590-600, jitter 10).
local function splitPanes(nodes)
  local xs, seen = {}, {}
  for _, n in ipairs(nodes) do
    if not seen[n.gridX] then seen[n.gridX] = true; xs[#xs + 1] = n.gridX end
  end
  if #xs < 3 then return nil end
  table.sort(xs)
  local gaps = {}
  for i = 2, #xs do gaps[#gaps + 1] = { size = xs[i] - xs[i - 1], at = i } end
  table.sort(gaps, function(a, b)
    if a.size ~= b.size then return a.size > b.size end
    return a.at < b.at
  end)
  if gaps[3] and gaps[3].size >= gaps[2].size then return nil end
  local cut1, cut2 = math.min(gaps[1].at, gaps[2].at), math.max(gaps[1].at, gaps[2].at)
  local panes = { {}, {}, {} }
  for _, n in ipairs(nodes) do
    local p = 1
    if n.gridX >= xs[cut2] then p = 3 elseif n.gridX >= xs[cut1] then p = 2 end
    table.insert(panes[p], n)
  end
  return panes
end

-- One node -> one talent, or nil for an empty/placeholder node. Classic
-- talents are single-choice nodes, so the first entry is the talent (the
-- node's activeEntry wins if a node ever carries more than one).
local function readNode(configID, nodeID, order)
  local node = call(C_Traits.GetNodeInfo, configID, nodeID)
  if type(node) ~= "table" or not node.ID or node.ID == 0 then return nil end
  if type(node.posX) ~= "number" or type(node.posY) ~= "number" then return nil end
  local entryID = node.activeEntry and node.activeEntry.entryID
  if not entryID and type(node.entryIDs) == "table" then entryID = node.entryIDs[1] end
  if not entryID then return nil end
  local entry = call(C_Traits.GetEntryInfo, configID, entryID)
  local def = entry and entry.definitionID and call(C_Traits.GetDefinitionInfo, entry.definitionID)
  if type(def) ~= "table" then return nil end
  local spellID = def.spellID
  local name = def.overrideName
  if type(name) ~= "string" or name == "" then name = spellID and spellName(spellID) end
  if type(name) ~= "string" or name == "" then return nil end
  -- activeRank = what's learned (WeakAuras Forever reads the same field);
  -- ranksPurchased is the older/other name for it.
  local rank = node.activeRank or node.ranksPurchased or 0
  return { name = name, icon = def.overrideIcon or (spellID and spellIcon(spellID)),
           rank = rank, maxRank = node.maxRanks or 0, posX = node.posX, posY = node.posY,
           nodeID = node.ID, entryID = entryID, spellID = spellID, configID = configID,
           order = order }
end

-- The game's talents, one list per Classic pane (in the site's tree order),
-- each sorted by tier, then column. That is the order of the site's share
-- code (one digit per talent, Wowhead's row/column order), so digit k of a
-- tree's part of a link is the k-th talent here. Ties can't happen in a real
-- tree (one talent per cell); the index tiebreak only keeps the order
-- deterministic, since table.sort is not stable.
-- Returns { { {name, icon, tier, column, rank, maxRank, index, nodeID,
-- spellID, ...}, ... } x3 } or nil when the client has no trait API, the
-- config isn't ready yet, or there are no talents.
--   tier   = rank of the node's posY among the whole tree's distinct posY
--            (rows are shared by all three panes; posY grows downwards:
--            tier 1 has the smallest posY, verified on the 8 real nodes).
--   column = rank of its posX among its own pane's distinct posX.
--            (Both after snapping near-equal values onto one grid line,
--            13.11: Blizzard's data has a few units of jitter.)
--   index  = its position in its pane, in C_Traits.GetTreeNodes order (the
--            trait API's own order, standing in for Classic's talent index).
-- Same shape as before 13.10, so encoding, hash, preview and learning order
-- keep working unchanged; nodeID / spellID are new extras.
-- Step 9's preview maps a pasted link onto exactly this list (13.2), so the
-- export and the import can never disagree about which digit is which talent.
-- The live talent config id (active spec group -> combat config), or nil.
-- Shared by the reader, the free-points source (13.12) and the "traits"
-- learning mode, so all three always look at the same config.
local function liveConfigID()
  if not (C_Traits and C_SpecializationInfo) then return nil end
  local group = call(C_SpecializationInfo.GetActiveSpecGroup)
  if not group then return nil end
  return call(C_SpecializationInfo.GetCombatConfigIDForSpecGroup, group)
end

function Talents.ReadTrees()
  local configID = liveConfigID()
  if not configID then return nil end
  local config = call(C_Traits.GetConfigInfo, configID)
  if type(config) ~= "table" or type(config.treeIDs) ~= "table" or #config.treeIDs == 0 then return nil end

  local panes
  if #config.treeIDs == 1 then
    -- The observed case (13.10): all three panes in one tree.
    local nodes = {}
    for _, nodeID in ipairs(call(C_Traits.GetTreeNodes, config.treeIDs[1]) or {}) do
      local x = readNode(configID, nodeID, #nodes + 1)
      if x then nodes[#nodes + 1] = x end
    end
    if #nodes == 0 then return nil end
    -- Snap X over the whole tree before the split (13.11).
    snapNodes(nodes, "posX", "gridX")
    panes = splitPanes(nodes)
  elseif #config.treeIDs == 3 then
    -- Never seen, but the other natural layout: one trait tree per pane, in
    -- the config's order. The ~hash still verifies the order on import.
    panes = {}
    for p, treeID in ipairs(config.treeIDs) do
      panes[p] = {}
      for _, nodeID in ipairs(call(C_Traits.GetTreeNodes, treeID) or {}) do
        local x = readNode(configID, nodeID, #panes[p] + 1)
        if x then table.insert(panes[p], x) end
      end
      -- Each tree is its own X space here, so snap per pane (13.11).
      snapNodes(panes[p], "posX", "gridX")
    end
  end
  if not panes then return nil end

  -- Rows over every pane together: the panes share their rows on screen, and
  -- a tier must mean the same thing in all three trees (13.5's learning order
  -- runs tier by tier across all trees).
  local all = {}
  for _, pane in ipairs(panes) do
    for _, x in ipairs(pane) do all[#all + 1] = x end
  end
  if #all == 0 then return nil end
  -- Ranks are taken on the snapped values (13.11), so jitter of a few units
  -- can't pose as an extra tier or column.
  snapNodes(all, "posY", "gridY")
  local tierOf, numTiers = ranks(all, "gridY")
  -- Classic grid: 7 tiers x 4 columns. More distinct values than that means
  -- the coordinates aren't the grid we verified: refuse rather than guess.
  if numTiers > 7 then return nil end

  local trees = {}
  for p, pane in ipairs(panes) do
    local colOf, numCols = ranks(pane, "gridX")
    if numCols > 4 then return nil end
    -- index = order within this pane, in GetTreeNodes order.
    table.sort(pane, function(a, b) return a.order < b.order end)
    local list = {}
    for i, x in ipairs(pane) do
      list[i] = { name = x.name, icon = x.icon, tier = tierOf[x.gridY], column = colOf[x.gridX],
                  rank = x.rank, maxRank = x.maxRank, index = i, nodeID = x.nodeID,
                  entryID = x.entryID, spellID = x.spellID, configID = x.configID }
    end
    table.sort(list, function(a, b)
      if a.tier ~= b.tier then return a.tier < b.tier end
      if a.column ~= b.column then return a.column < b.column end
      return a.index < b.index
    end)
    trees[p] = list
  end
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

-- ---------------------------------------------------------------------------
-- Unspent talent points (ADDON_PLAN 13.12): the ONE place the addon finds
-- them. The Talents tab, the learning engine, Home and the minimap tooltip
-- (Minimap.FreeTalentPoints) all come through here.
-- ---------------------------------------------------------------------------
-- Why C_Traits first: on WoW Forever the talents themselves live in a trait
-- config (13.10), and a real screenshot showed Blizzard's window at "Unspent
-- Talents: 17" while UnitCharacterPoints-based code said 0. In retail's trait
-- system (the API family Forever's client carries) unspent points are a trait
-- CURRENCY of the tree: C_Traits.GetTreeCurrencyInfo(configID, treeID,
-- excludeStagedChanges) returns a list of { traitCurrencyID, quantity,
-- maxQuantity, spent }, and quantity is what's left to spend.
--   Note: C_Traits.GetTraitCurrencyInfo (seen in the live /dump) is NOT the
--   amount in retail: it takes a traitCurrencyID and describes the currency
--   (flags, type, icon). So it isn't used here.
-- excludeStagedChanges = true: the rest of the addon reads activeRank, the
-- APPLIED rank (13.10), so the free points must be the applied ones too, not
-- "what's left after the changes sitting un-applied in Blizzard's window".
-- Confidence: medium. The retail signature is well known; that Forever's
-- client has GetTreeCurrencyInfo with the same shape is NOT confirmed (the
-- dump excerpt didn't list it). Every step is guarded, and anything odd gives
-- "unknown", never a guess.
-- excludeStaged: true for the applied amount (everything here); false only
-- to see how many points are staged (stagedPoints, 13.12).
local function traitFreePoints(configID, excludeStaged)
  if not (C_Traits and type(C_Traits.GetTreeCurrencyInfo) == "function") then return nil end
  local config = call(C_Traits.GetConfigInfo, configID)
  if type(config) ~= "table" or type(config.treeIDs) ~= "table" or #config.treeIDs == 0 then return nil end
  -- Per currency id, so a pool shared by several trees (one tree per pane,
  -- 13.10's other layout) is counted once, not once per tree.
  local byCurrency, n = {}, 0
  for _, treeID in ipairs(config.treeIDs) do
    local list = call(C_Traits.GetTreeCurrencyInfo, configID, treeID, excludeStaged)
    if type(list) ~= "table" then return nil end
    for _, c in ipairs(list) do
      local q = type(c) == "table" and c.quantity
      if type(q) ~= "number" or q < 0 then return nil end
      local id = c.traitCurrencyID or ("tree" .. treeID)
      if byCurrency[id] == nil then n = n + 1 end
      byCurrency[id] = q
    end
  end
  -- Retail's class trees have two currencies (class and spec points); which
  -- one a Classic pane would spend from is unknown. One currency, or several
  -- that agree, is a clear answer; anything else is "unknown".
  local value
  for _, q in pairs(byCurrency) do
    if value ~= nil and q ~= value then return nil end
    value = q
  end
  if n == 0 then return nil end
  return value
end

-- n, source: n = unspent points, or nil when the client gives no usable
-- answer ("unknown" is not "zero": the summary says so and Learn stays off).
-- source = "traits" | "classic".
function Talents.FreePointsInfo()
  local configID = liveConfigID()
  if configID then
    local n = traitFreePoints(configID, true)
    if n then return n, "traits" end
  end
  -- Classic's call, unchanged in meaning (first return = unspent points).
  if type(UnitCharacterPoints) == "function" then
    local ok, n = pcall(UnitCharacterPoints, "player")
    if ok and type(n) == "number" then
      -- On a client whose talents are a trait config (configID found) this
      -- legacy call is exactly what read 0 next to 17 real points. A positive
      -- answer is still believable; a 0 there could be that bug, so it's
      -- "unknown" rather than a confident "no points".
      if configID and n <= 0 then return nil end
      return math.max(n, 0), "classic"
    end
  end
  return nil
end

-- The number, for code that only compares it (unknown counts as 0, which
-- is the safe side: nothing is learned with 0 free points).
function Talents.FreePoints()
  return (Talents.FreePointsInfo()) or 0
end

-- Tree names per class in in-game tab order: the same names and order as
-- talentcalc.js CLASSES (run_tests.py compares them), because WoW Forever's
-- C_Traits gives no tree names (15.2). Keyed by class token.
Talents.TREE_NAMES = {
  PRIEST = { "Discipline", "Holy", "Shadow" },
  WARLOCK = { "Affliction", "Demonology", "Destruction" },
  MAGE = { "Arcane", "Fire", "Frost" },
  ROGUE = { "Assassination", "Combat", "Subtlety" },
  DRUID = { "Balance", "Feral Combat", "Restoration" },
  SHAMAN = { "Elemental", "Enhancement", "Restoration" },
  HUNTER = { "Beast Mastery", "Marksmanship", "Survival" },
  PALADIN = { "Holy", "Protection", "Retribution" },
  WARRIOR = { "Arms", "Fury", "Protection" },
}

-- Tree names for the mini-tree headers. GetTalentTabInfo's returns differ by
-- client generation (13.6 avoided it for that reason): Classic-era clients
-- return name first, newer ones id (a number) then name. Take whichever is
-- the first string; without one (missing API, error, odd shape, or WoW
-- Forever's C_Traits client) use our own list for `class` (default: the
-- player's), and only for an unknown class fall back to "Tree 1" etc. Only
-- the header text depends on this, never the mapping.
function Talents.TreeName(tab, class)
  if GetTalentTabInfo then
    local ok, a, b = pcall(GetTalentTabInfo, tab)
    if ok then
      if type(a) == "string" and a ~= "" then return a end
      if type(b) == "string" and b ~= "" then return b end
    end
  end
  class = class or R2F.playerClass or (UnitClass and select(2, UnitClass("player")))
  local names = class and Talents.TREE_NAMES[class]
  if names and names[tab] then return names[tab] end
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
  if plan.free <= 0 then
    -- 13.12: "couldn't read" is not "you have none"; say which one it is.
    if plan.freeKnown == false then return L.TALENT_SUMMARY_POINTS_UNKNOWN, "nopoints" end
    return L.TALENT_SUMMARY_NO_POINTS, "nopoints"
  end
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
--   build": everything you have counts as kept), free = unspent points, or
--   nil = couldn't be read (13.12: planned as 0, so nothing is learnable,
--   and plan.freeKnown = false makes the summary say why).
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
                 free = math.max(tonumber(free) or 0, 0), freeKnown = tonumber(free) ~= nil }
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
                  maxRank = x.maxRank, index = x.index, nodeID = x.nodeID, spellID = x.spellID,
                  tab = t, planned = planned,
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
  return Talents.Plan(trees, codes, (Talents.FreePointsInfo()))
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
  return { plan = Talents.Plan(trees, link.codes, (Talents.FreePointsInfo())), caution = caution, link = link }
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
-- "traits" mode (13.12): one point there is a purchase AND a commit, and the
-- commit is a server round trip (Blizzard's own window shows an "applying"
-- wait for it). A too-short wait only turns into a stop + guided mode (safe,
-- but annoying), so it gets more room than Classic's single LearnTalent.
Talents.TRAITS_TIMEOUT = 2

local run            -- the current / last run (see Talents.StartLearn)
-- worked: LearnTalent has landed a point this session (so addons may use it).
-- blocked: it was refused with no other explanation before ever working, so
-- this client probably blocks it for addons -> guided mode (13.5's fallback).
-- traitsWorked / traitsBlocked: the same two facts for the "traits" mode
-- (C_Traits.PurchaseRank, 13.12). Kept apart so one write path's trouble
-- never says anything about the other. traitsBlocked, unlike blocked, is never
-- cleared by a late success: anything unexpected in that mode means guided
-- mode for the rest of the session (a /reload tries "traits" again).
local session = { worked = false, blocked = false, traitsWorked = false, traitsBlocked = false }
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
-- target = the talent's rank once this point has landed. nodeID = its trait
-- node (13.10), the "traits" mode's address (13.12); the order is untouched.
function Talents.LearnPoints(plan)
  local out = {}
  for _, e in ipairs(Talents.LearnOrder(plan)) do
    for k = 1, e.now do
      out[#out + 1] = { tab = e.tab, index = e.index, name = e.name, tier = e.tier,
                        column = e.column, target = e.rank + k, nodeID = e.nodeID }
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
-- 13.10: the trees are read through C_Traits now, so a talent's (tab, index)
-- is OUR address (pane, position in GetTreeNodes order), not Classic's
-- talent-table index. LearnTalent and AddPreviewTalentPoints take Classic's
-- (tab, index). Both are irreversible-ish writes, so they are only used on a
-- client that also has Classic's GetTalentInfo (the "preview" and "direct"
-- modes require it) and, per point, only when GetTalentInfo names exactly this
-- talent at exactly this address. WoW Forever has no GetTalentInfo (13.10),
-- so there neither of those modes applies.
--   "traits"   (13.12) C_Traits.PurchaseRank(configID, nodeID), one point at a
--              time, committed and verified per point. The address is the
--              trait node itself (no Classic index to translate), checked
--              against the live config right before each write. Only when the
--              Classic modes don't apply, and never again this session once
--              anything in it looked wrong (session.traitsBlocked).
local function legacyMatches(tab, index, name)
  if type(GetTalentInfo) ~= "function" then return false end
  local ok, n = pcall(GetTalentInfo, tab, index)
  return ok and n == name
end

-- Everything the "traits" mode calls, present as functions. CommitConfig is
-- deliberately NOT required: whether a purchase needs it can only be seen at
-- run time (purchasePoint), and without it a staged point is handed to the
-- player's own Apply Changes button instead.
local function traitsWritable()
  return type(C_Traits) == "table" and type(C_SpecializationInfo) == "table"
    and type(C_Traits.PurchaseRank) == "function" and type(C_Traits.GetNodeInfo) == "function"
    and type(C_Traits.GetConfigInfo) == "function" and type(C_Traits.GetTreeNodes) == "function"
end

function Talents.LearnMode()
  local legacy = type(GetTalentInfo) == "function"
  if legacy and type(AddPreviewTalentPoints) == "function" and type(LearnPreviewTalents) == "function"
     and GetCVarBool then
    local ok, on = pcall(GetCVarBool, "previewTalents")
    if ok and on then return "preview" end
  end
  if legacy and type(LearnTalent) == "function" and not session.blocked then return "direct" end
  if traitsWritable() and not session.traitsBlocked then return "traits" end
  return "guided"
end

local function packed(...) return { n = select("#", ...), ... } end

-- Prerequisites (13.5: "double-check ... GetTalentPrereqs"). Classic returns
-- tier, column, isLearnable per prerequisite. We look the prerequisite up in
-- the live tree and require it maxed (the Classic rule) rather than trust
-- isLearnable, whose exact meaning can't be confirmed outside the game.
-- No API or an error: no extra check here; the server still refuses an
-- illegal point and the rank re-read after LearnTalent stops the run then.
-- 13.12: only at an address Classic's API confirms (legacyMatches). Without
-- it (WoW Forever) (tab, index) is our C_Traits address and GetTalentPrereqs,
-- if a client had it, would describe some other talent; the "traits" mode
-- asks the trait node itself instead (purchasePoint's canPurchaseRank).
local function prereqsMet(p, tree)
  if not GetTalentPrereqs or not legacyMatches(p.tab, p.index, p.name) then return true end
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

-- ---------------------------------------------------------------------------
-- C_Traits helpers for the "traits" mode (13.12)
-- ---------------------------------------------------------------------------
-- Node fields, retail meaning (the API family Forever's client carries; not
-- every field is confirmed on Forever, so each one is optional here):
--   activeRank    the APPLIED rank (what the reader shows, 13.10)
--   currentRank   the rank INCLUDING changes staged in the client but not yet
--                 applied (Blizzard's window shows those as pending)
--   ranksPurchased  purchased ranks (staged included); older/other name
local function traitNode(configID, nodeID)
  local node = call(C_Traits.GetNodeInfo, configID, nodeID)
  if type(node) ~= "table" or not node.ID or node.ID == 0 then return nil end
  return node
end

-- Same fallback as readNode's rank, so "applied" means one thing everywhere.
local function appliedOf(node) return node.activeRank or node.ranksPurchased or 0 end

local function stagedOf(node)
  if type(node.currentRank) == "number" then return node.currentRank end
  if type(node.ranksPurchased) == "number" then return node.ranksPurchased end
  return nil
end

-- Un-applied (staged) changes anywhere in the config, other than on node
-- `skip`. Why it matters: a commit applies EVERYTHING staged, so committing
-- while the player has half-made changes in Blizzard's window would apply
-- talents they never confirmed in our popup. An unreadable config counts as
-- "yes" (stop): never commit blind.
-- Points staged in the config according to its currency (applied free
-- points minus free points with staged changes), or nil if unreadable.
local function stagedPoints(configID)
  local applied, withStaged = traitFreePoints(configID, true), traitFreePoints(configID, false)
  if not (applied and withStaged) then return nil end
  return applied - withStaged
end

local function pendingElsewhere(configID, skip)
  -- The currency's view too, so staging is seen even on a client whose node
  -- fields don't show it. One staged point is expected right after our own
  -- purchase (skip given), none before it.
  local d = stagedPoints(configID)
  if d and d > (skip and 1 or 0) then return true end
  local config = call(C_Traits.GetConfigInfo, configID)
  if type(config) ~= "table" or type(config.treeIDs) ~= "table" then return true end
  for _, treeID in ipairs(config.treeIDs) do
    for _, nodeID in ipairs(call(C_Traits.GetTreeNodes, treeID) or {}) do
      if nodeID ~= skip then
        local node = traitNode(configID, nodeID)
        local s = node and stagedOf(node)
        if s and s ~= appliedOf(node) then return true end
      end
    end
  end
  return false
end

-- Point p is sitting in the run's config bought but not applied (its node
-- says so, or the currency shows staged points: see pendingElsewhere).
local function stagedPending(r, p)
  if not (C_Traits and r.configID and p.nodeID) then return false end
  local node = traitNode(r.configID, p.nodeID)
  local s = node and stagedOf(node)
  if s ~= nil and s > appliedOf(node) then return true end
  local d = stagedPoints(r.configID)
  return d ~= nil and d > 0
end

-- The talent's APPLIED rank in the live game, or nil when it can't be
-- confirmed to be this very talent. Classic: GetTalentInfo at the Classic
-- address (unchanged since step 10). "traits": the trait node in the run's
-- config, through the reader's own readNode (activeRank + the name check).
local function liveRank(r, p)
  if r.mode == "traits" then
    local configID = liveConfigID()
    if not configID or configID ~= r.configID or not p.nodeID then return nil end
    local x = readNode(configID, p.nodeID, 0)
    if not x or x.name ~= p.name then return nil end
    return x.rank
  end
  if not GetTalentInfo then return nil end
  local name, _, _, _, rank = GetTalentInfo(p.tab, p.index)
  if name ~= p.name then return nil end
  return rank or 0
end

-- Did point p land? Classic: the rank re-read (13.5), unchanged. "traits"
-- (13.12): the applied rank AND, independently, the free points (read with
-- staged changes excluded, 13.12) having gone down since the send. Two
-- different API answers must agree, because the one thing this mode must
-- never do is call a point learned when it isn't. If activeRank turned out to
-- count staged ranks on this client, the rank alone would say "yes" right
-- after a purchase that was never applied; the free points would still say
-- "no". Cost: a level-up landing in the same moment (+1 free) makes a real
-- point look unconfirmed -> a stop and guided mode, the safe direction.
local function landed(r, p)
  local rank = liveRank(r, p)
  if not (rank and rank >= p.target) then return false end
  if r.mode ~= "traits" then return true end
  local free = Talents.FreePointsInfo()
  return free ~= nil and r.freeBefore ~= nil and free < r.freeBefore
end

-- Stops that "Learn talents" can pick up again from the same point. The
-- others (no points, tier/prerequisite, trees changed) need a fresh preview,
-- so the next click starts over with a new popup. 13.12: "staged" (resumes in
-- guided mode) and "pending" (once Blizzard's window is applied or undone).
local RESUMABLE = { combat = true, user = true, rejected = true, staged = true, pending = true }

-- The guided-mode hint goes on a refusal when the mode that refused is now
-- switched off for this session.
local function blockedNow(r)
  if r.mode == "traits" then return session.traitsBlocked end
  return session.blocked
end

local function stopText(r, why, name)
  if why == "combat" then return L.TALENT_STOP_COMBAT:format(r.done, r.total) end
  if why == "user" then return L.TALENT_STOP_USER:format(r.done, r.total) end
  if why == "rejected" then
    local text = L.TALENT_STOP_REJECTED:format(name, r.done, r.total)
    if blockedNow(r) then text = text .. " " .. L.TALENT_BLOCKED_HINT end
    return text
  end
  if why == "staged" then
    return L.TALENT_STOP_STAGED:format(name, r.done, r.total) .. " " .. L.TALENT_BLOCKED_HINT
  end
  if why == "pending" then return L.TALENT_STOP_PENDING:format(r.done, r.total) end
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
  -- 13.10: never send a point to an address Classic's API doesn't confirm is
  -- this very talent (see legacyMatches).
  if not legacyMatches(p.tab, p.index, p.name) then return false, "mismatch" end
  if not pcall(LearnTalent, p.tab, p.index) then return false, "rejected" end
  return true
end

-- The ONLY C_Traits writes in the addon (13.12; Taint & secure execution,
-- 6.6): PurchaseRank, and CommitConfig when the purchase turned out to be
-- staged. Same order as learnPoint: combat first, then the address, then the
-- write; nothing is sent unless every check passes.
--
-- Signature: retail's C_Traits.PurchaseRank(configID, nodeID) -> success
-- (boolean), on the same (configID, nodeID) pair every C_Traits reader here
-- already uses (13.10). Only `false` or an error count as "refused" at once;
-- `true` or nothing proves nothing: the read-back (landed) decides.
--
-- Staged or applied at once? In retail, PurchaseRank only STAGES the change
-- in the client's copy of the config (Blizzard's window shows it pending and
-- lights "Apply Changes"); C_Traits.CommitConfig(configID) sends what's
-- staged to the server, which answers with TRAIT_CONFIG_UPDATED (or
-- CONFIG_COMMIT_FAILED). The "Apply Changes" button in the user's screenshot
-- of Forever's window points the same way. Not confirmed on Forever, so it is
-- read off the node right after the call instead of assumed. A server can't
-- answer inside the call, so ANY rank change visible right after it is the
-- client's local (staged) copy:
--   a rank moved      -> staged: commit exactly this one point, and only when
--                        nothing else is staged. Without CommitConfig, wait:
--                        landed() never counts a merely staged point, so it
--                        ends as a "waiting in Blizzard's window" stop.
--   nothing moved     -> the server may apply it later; wait, landed() decides
--                        (this also catches a "true" that changed nothing).
-- One commit per point, not one at the end: each point is then one server
-- round trip, exactly like Classic's LearnTalent, so every step-10 guard
-- (verify before each point, per-point combat check, read-back, timeout,
-- resume, no double send) applies unchanged, and at most one point is ever
-- un-applied. Confidence: medium on the signature, low-to-medium on staging
-- vs immediate on Forever; the read-back is what makes either answer safe.
-- Returns true (sent; wait for the answer) or false, why: "combat" |
-- "mismatch" | "pending" | "locked" | "rejected" | "staged" | "stopped" (the
-- run was already stopped inside the call, e.g. ADDON_ACTION_FORBIDDEN).
local function purchasePoint(r, p)
  r.freeBefore = nil
  if R2F.InCombat() then return false, "combat" end
  -- The config the run started on (a spec switch changes it), and the node
  -- there is still this very talent, exactly one applied rank short.
  local configID = liveConfigID()
  if not configID or configID ~= r.configID or not p.nodeID then return false, "mismatch" end
  local x = readNode(configID, p.nodeID, 0)
  if not x or x.name ~= p.name or x.rank ~= p.target - 1 then return false, "mismatch" end
  local node = traitNode(configID, p.nodeID)
  if not node then return false, "mismatch" end
  -- Nothing staged anywhere, this node included: a commit must only ever
  -- apply the one point the player confirmed, and a point already staged
  -- here must not get a second rank stacked on it (no double send).
  if pendingElsewhere(configID, nil) then return false, "pending" end
  -- The node's / config's own word, when the client gives it (retail
  -- fields). Absent = no extra check; the server still refuses and the
  -- read-back stops the run then.
  if node.canPurchaseRank == false then return false, "locked" end
  if type(C_Traits.CanEditConfig) == "function" then
    local ok, can = pcall(C_Traits.CanEditConfig, configID)
    if ok and can == false then return false, "rejected" end
  end
  -- The second, independent confirmation landed() needs. verify() has just
  -- checked there is at least one free point, so this is a real number.
  r.freeBefore = Talents.FreePointsInfo()
  if not r.freeBefore then return false, "mismatch" end
  local ok, res = pcall(C_Traits.PurchaseRank, configID, p.nodeID)
  if run ~= r or r.phase ~= "learning" then return false, "stopped" end
  if not ok or res == false then return false, "rejected" end
  node = traitNode(configID, p.nodeID)
  if not node then return false, "rejected" end
  local moved = math.max(appliedOf(node), stagedOf(node) or 0)
  if moved < p.target then return true end
  if type(C_Traits.CommitConfig) ~= "function" then return true end
  -- More than this one rank moved, or something else got staged meanwhile:
  -- don't commit what nobody confirmed.
  if moved > p.target or pendingElsewhere(configID, p.nodeID) then return false, "staged" end
  local cok, cres = pcall(C_Traits.CommitConfig, configID)
  if run ~= r or r.phase ~= "learning" then return false, "stopped" end
  if not cok or cres == false then return false, "staged" end
  return true
end

local stepSend, settle

-- A point that didn't land. Classic: guided mode is only suspected when
-- LearnTalent never worked this session (13.8). "traits" (13.12): ANY refusal,
-- error, failed commit or unconfirmed point switches the session to guided
-- mode at once; nothing more is fired at C_Traits until a /reload. If the
-- point is sitting staged in Blizzard's window, the message says so: the
-- player's Apply Changes keeps it (lateCheck counts it), undo drops it.
local function reject(r, p, why)
  r.waiting = nil
  r.late = p          -- if the answer was only slow, lateCheck still counts it
  if r.mode == "traits" then
    session.traitsBlocked = true
    if why == "staged" or stagedPending(r, p) then return stop(r, "staged", p) end
    return stop(r, "rejected", p)
  end
  if not session.worked then session.blocked = true end
  stop(r, "rejected", p)
end

-- One point, then wait: CHARACTER_POINTS_CHANGED / TRAIT_CONFIG_UPDATED
-- (OnPointsChanged), CONFIG_COMMIT_FAILED (OnCommitFailed) or the timeout,
-- whichever comes first, decides via settle(). The same for both write
-- modes; only the "spend this one point" call differs (r.mode).
stepSend = function(r)
  if run ~= r or r.phase ~= "learning" then return end
  if R2F.InCombat() then return stop(r, "combat", r.points[r.pos]) end
  local p = nextPoint(r)
  if not p then return end
  r.waiting = p
  r.token = r.token + 1
  local tok = r.token
  notify()
  local ok, why
  if r.mode == "traits" then
    ok, why = purchasePoint(r, p)
  else
    ok, why = learnPoint(p)
  end
  if not ok then
    if why == "stopped" then return end
    r.waiting = nil
    if why == "combat" then return stop(r, "combat", p) end
    -- Nothing was sent, so it's no sign the write is blocked: a plain
    -- "your talents changed" stop, not a refusal.
    if why == "mismatch" then return stop(r, "changed", p) end
    if why == "pending" or why == "locked" then return stop(r, why, p) end
    return reject(r, p, why)
  end
  -- ADDON_ACTION_FORBIDDEN can fire inside the write itself and has already
  -- stopped the run (Talents.OnActionBlocked).
  if r.phase ~= "learning" then return end
  if C_Timer and C_Timer.After then
    local wait = r.mode == "traits" and Talents.TRAITS_TIMEOUT or Talents.LEARN_TIMEOUT
    C_Timer.After(wait, function() settle(r, tok, true) end)
  end
end

-- Did the point land? (landed: the rank re-read, 13.5; "traits" also the
-- free points, 13.12.) Not yet on an event: keep waiting (the event also
-- fires for other reasons, e.g. a level-up). Not yet when it's final (the
-- timeout): stop, never continue past it.
-- resend = this was a point from before a stop that we only waited for (see
-- begin): not there after the wait = it never got through, so send it now.
-- Classic only: in "traits" a purchase whose commit is still on its way may
-- be invisible locally, and a second purchase could then land BOTH, so a
-- traits point is never sent twice; not there after the wait = a refusal.
settle = function(r, tok, final, resend)
  if run ~= r or r.token ~= tok or r.phase ~= "learning" or not r.waiting then return end
  local p = r.waiting
  if landed(r, p) then
    r.waiting = nil
    r.done, r.pos = r.done + 1, r.pos + 1
    if r.mode == "traits" then
      session.traitsWorked = true
    else
      session.worked, session.blocked = true, false
    end
    stepSend(r)
  elseif final and resend and r.mode ~= "traits" then
    r.waiting = nil
    stepSend(r)
  elseif final then
    reject(r, p)
  end
end

-- After a stop, the point that was on its way may still land (a slow
-- server, combat started right after it was sent, or the player clicked
-- Apply Changes on a staged point). Count it. Classic: if it was a "refused"
-- stop, LearnTalent does work after all, so no guided mode. "traits" stays
-- guided for the session (see session).
local function lateCheck(r)
  local p = r.late
  if not p then return end
  if not landed(r, p) then return end
  r.late = nil
  if r.mode == "traits" then
    session.traitsWorked = true
  else
    session.worked, session.blocked = true, false
  end
  if r.points[r.pos] == p then r.done, r.pos = r.done + 1, r.pos + 1 end
  if r.pos > r.total then return finish(r) end
  if r.why == "rejected" or r.why == "staged" then
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
  local mode = Talents.LearnMode()
  if mode == "guided" then
    r.mode, r.phase = "guided", "guided"
    if R2F.TalentGuide.OpenTalentWindow() then
      R2F.Print(L.TALENT_GUIDE_START)
    else
      R2F.Print(L.TALENT_GUIDE_OPEN)
    end
    stepGuided(r)
    return
  end
  r.mode, r.phase = mode == "traits" and "traits" or "direct", "learning"
  -- The config this (part of the) run writes to; every point checks the
  -- live one still matches (13.12).
  if r.mode == "traits" then r.configID = liveConfigID() end
  if pending and C_Timer and C_Timer.After then
    -- A point sent before the stop may still be on its way (Stop, then Learn
    -- talents clicked right away). Sending it again now could land BOTH: one
    -- rank more than the build wants, in a talent that may be at its planned
    -- maximum, which only a trainer reset undoes. So wait for it first,
    -- exactly like for a point just sent; only if it's still not there after
    -- the timeout is it sent again (settle's resend; never in "traits").
    -- Without C_Timer there's no way to wait; it is sent again at once (every
    -- Classic Era client has C_Timer, 13.8).
    r.waiting = pending
    r.token = r.token + 1
    local tok = r.token
    notify()
    local wait = r.mode == "traits" and Talents.TRAITS_TIMEOUT or Talents.LEARN_TIMEOUT
    C_Timer.After(wait, function() settle(r, tok, true, true) end)
    return
  end
  stepSend(r)
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
--   mode ("direct" | "traits" | "guided"), done, total, current (the point
--   being learned, 1-based), text, resumable, point }
function Talents.LearnStatus()
  local r = run
  if not r then return { phase = "idle" } end
  return { phase = r.phase, mode = r.mode, done = r.done, total = r.total,
           current = math.min(r.done + 1, r.total), text = r.text, resumable = r.resumable,
           point = r.points[r.pos] }
end

function Talents.LearnMessage() return message end

-- CHARACTER_POINTS_CHANGED, TRAIT_CONFIG_UPDATED and
-- TRAIT_TREE_CURRENCY_INFO_UPDATED (Core.lua, before the tab's refresh).
-- Which of them Forever fires for an applied point isn't confirmed (13.12);
-- none of them is trusted on its own: each one only makes settle() re-read
-- the game (landed), and the timeout is the final word.
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

-- CONFIG_COMMIT_FAILED (Core.lua; retail's "the server refused the commit",
-- args: configID). The server's explicit no for the point in flight: settle
-- it as final now (landed() still gets the last word, so a point that did
-- land is counted) instead of waiting for the timeout.
function Talents.OnCommitFailed(configID)
  local r = run
  if not (r and r.mode == "traits" and r.phase == "learning" and r.waiting) then return end
  if configID ~= nil and configID ~= r.configID then return end
  settle(r, r.token, true)
end

-- PLAYER_REGEN_DISABLED (Core.lua): stop AT ONCE, mid-run (13.5), not only
-- refuse to start. The point already sent can't be called back; it is
-- counted if it lands (lateCheck). No new write goes out after this:
-- learnPoint and purchasePoint check R2F.InCombat(), which is true from this
-- event on.
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
-- before, and the point in flight is settled as refused now. 13.12: the same
-- for the C_Traits writes (PurchaseRank / CommitConfig), on their own flag.
function Talents.OnActionBlocked(fn)
  if type(fn) ~= "string" then return end
  local r = run
  if fn:find("LearnTalent", 1, true) then
    session.blocked, session.worked = true, false
    if r and r.mode ~= "traits" and r.phase == "learning" and r.waiting then settle(r, r.token, true) end
  elseif fn:find("PurchaseRank", 1, true) or fn:find("CommitConfig", 1, true) then
    session.traitsBlocked = true
    if r and r.mode == "traits" and r.phase == "learning" and r.waiting then settle(r, r.token, true) end
  end
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
      if not legacyMatches(e.tab, e.index, e.name) then break end
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
function Talents.ResetSession()
  session.worked, session.blocked, session.traitsWorked, session.traitsBlocked = false, false, false, false
end
