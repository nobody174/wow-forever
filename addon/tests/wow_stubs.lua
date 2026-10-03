-- Minimal fake WoW client for running the addon under plain Lua 5.1.
-- Not a WoW emulator: just enough API surface for the addon's code paths,
-- plus strictness where it matters (macro writes in combat raise an error,
-- like the real protected calls do).
--
-- Loaded by run_tests.py into a fresh Lua state before the addon files.

local T = {}          -- test controls, returned to the harness
_G.TEST = T

T.combat = false
T.timers = {}
T.errors = {}         -- UIErrorsFrame messages
T.chat = {}           -- DEFAULT_CHAT_FRAME messages
T.cursor = nil        -- name of the macro on the cursor
T.actions = {}        -- slot -> macro name
T.knownSpells = { ["Victory Rush"] = "Interface\\Icons\\Ability_Warrior_Devastate",
                  ["Heroic Strike"] = "Interface\\Icons\\Ability_Rogue_Ambush" }
T.templates = { PortraitFrameTemplate = true, InputScrollFrameTemplate = true,
                UIPanelButtonTemplate = true, UIPanelCloseButton = true,
                UIPanelScrollFrameTemplate = true, BackdropTemplate = true,
                ButtonFrameTemplate = true, UICheckButtonTemplate = true,
                UIRadioButtonTemplate = true,
                -- Step 6: only the Classic tab template, so the main window's
                -- PanelTabButtonTemplate -> CharacterFrameTabButtonTemplate
                -- chain is exercised (the first one is "missing").
                CharacterFrameTabButtonTemplate = true,
                -- Step 9: the Talents tab's link box.
                InputBoxTemplate = true }

-- Home footer (12.4.2): real client TOC metadata. Both the modern (C_AddOns)
-- and legacy (global function) APIs are wired on by default, same as the
-- templates table; a test clears one or both afterward (C_AddOns = nil,
-- GetAddOnMetadata = nil) the same way it clears a template to reach the
-- "neither API exists" fallback path.
T.metadata = { Version = "0.10.1", Author = "nobody174" }
C_AddOns = { GetAddOnMetadata = function(_, field) return T.metadata[field] end }
function GetAddOnMetadata(_, field) return T.metadata[field] end

-- On-demand addons. Blizzard_TalentUI does NOT exist on WoW Forever:
-- LoadAddOn("Blizzard_TalentUI") answers false, "MISSING" (confirmed in game,
-- ADDON_PLAN 13.10; 13.9 had wrongly modelled it as load-on-demand). Every
-- LoadAddOn call is logged in T.loadAddOnCalls so a test can prove the addon
-- doesn't depend on it any more.
T.loadedAddons = {}
T.loadAddOnCalls = {}
C_AddOns.IsAddOnLoaded = function(name) return T.loadedAddons[name] == true end
C_AddOns.LoadAddOn = function(name)
  table.insert(T.loadAddOnCalls, name)
  if T.loadedAddons[name] then return true end
  return false, "MISSING"
end
function IsAddOnLoaded(name) return C_AddOns.IsAddOnLoaded(name) end
function LoadAddOn(name) return C_AddOns.LoadAddOn(name) end

T.calls = {}          -- log of macro API writes

-- ---------------------------------------------------------------------------
-- Macros: account slots 1..120, character 121..150, each set kept sorted by
-- name like the real client (so indices shift on create/delete/rename).
-- 30 character slots, not vanilla/Classic Era's 18 — confirmed on a real WoW
-- Forever client 2026-10-02 (ADDON_PLAN.md section 2/11; MAX_CHARACTER_MACROS
-- itself is nil on this client, same as several other legacy globals).
-- ---------------------------------------------------------------------------
local MAX_ACC, MAX_CHAR = 120, 30
local acc, char = {}, {}
T.macros = { acc = acc, char = char }

local function sortSet(set) table.sort(set, function(a, b) return a.name < b.name end) end
local function byIndex(i)
  if i >= 1 and i <= MAX_ACC then return acc[i], acc, i end
  if i > MAX_ACC then return char[i - MAX_ACC], char, i - MAX_ACC end
end
local function protected(what)
  if T.combat then error(what .. ": blocked in combat (protected)", 2) end
end

function GetNumMacros() return #acc, #char end
function GetMacroIndexByName(name)
  for i, m in ipairs(acc) do if m.name == name then return i end end
  for i, m in ipairs(char) do if m.name == name then return MAX_ACC + i end end
  return 0
end
function GetMacroInfo(i)
  local m = byIndex(i)
  if m then return m.name, m.icon, m.body end
end
function CreateMacro(name, icon, body, perCharacter)
  protected("CreateMacro")
  local set = perCharacter and char or acc
  if #set >= (perCharacter and MAX_CHAR or MAX_ACC) then error("CreateMacro: macro limit reached") end
  table.insert(set, { name = name, icon = icon, body = body })
  sortSet(set)
  table.insert(T.calls, "create:" .. name)
  return GetMacroIndexByName(name)
end
function EditMacro(i, name, icon, body)
  protected("EditMacro")
  local m, set = byIndex(i)
  assert(m, "EditMacro: bad index " .. tostring(i))
  m.name = name or m.name
  if icon then m.icon = icon end
  if body then m.body = body end
  sortSet(set)
  table.insert(T.calls, "edit:" .. m.name)
  return GetMacroIndexByName(m.name)
end
function DeleteMacro(i)
  protected("DeleteMacro")
  local m, set, j = byIndex(i)
  assert(m, "DeleteMacro: bad index " .. tostring(i))
  table.remove(set, j)
  table.insert(T.calls, "delete:" .. m.name)
end
function PickupMacro(i)
  protected("PickupMacro")
  local m = byIndex(i)
  assert(m, "PickupMacro: bad index " .. tostring(i))
  T.cursor = m.name
end
-- Test helper: the player's own macro (not via the addon).
function T.addMacro(name, body, perCharacter)
  local set = perCharacter and char or acc
  table.insert(set, { name = name, icon = "X", body = body })
  sortSet(set)
end
function T.setBody(name, body)
  local m = byIndex(GetMacroIndexByName(name))
  m.body = body
end
function T.bodyOf(name)
  local i = GetMacroIndexByName(name)
  if i > 0 then return (select(3, GetMacroInfo(i))) end
end
function T.reset()
  for k in pairs(acc) do acc[k] = nil end
  for k in pairs(char) do char[k] = nil end
  T.actions, T.cursor, T.errors, T.chat, T.calls, T.combat = {}, nil, {}, {}, {}, false
end

function GetActionInfo(slot)
  local name = T.actions[slot]
  if name then
    local i = GetMacroIndexByName(name)
    if i > 0 then return "macro", i end
  end
  return nil
end
function GetActionText(slot)
  local name = T.actions[slot]
  if name and GetMacroIndexByName(name) > 0 then return name end
end

-- Talents. T.talentTabs[tab] = list of { name, tier, column, rank, maxRank,
-- prereq } per Classic pane, in the client's OWN order (deliberately not
-- tier/column order in the tests). It is the one source of truth; the APIs
-- below are views of it, so a rank changed by the fake server shows up in
-- all of them.
T.talentTabs = {}

-- C_Traits, the API WoW Forever really reads talents through (ADDON_PLAN
-- 13.10; same chain as WeakAuras Forever's Private.GetTalentData). Modelled
-- on the real data: ONE trait tree (1100, like Paladin's) holding all three
-- panes as side-by-side column groups. Grid step 600 in both axes, posY grows
-- downwards with the tier, pane 1 column 1 / tier 1 at (1020, 2130): exactly
-- the real Holy pane's numbers (the 8 dumped nodes, 13.10). The pane offset
-- (3930) is our reading of the screenshot (13.10), not a dumped value.
-- GetTreeNodes interleaves the panes (pane 1 node 1, pane 2 node 1, ...), so
-- a reader that groups by node order instead of by position fails the tests.
-- T.traitTree = { treeIDs = {...}, trees = { [treeID] = { {id, posX, posY,
--   name, rank, maxRank, spellID}, ... } } } replaces the derived layout (the
-- real-data test, odd layouts). T.traitsReady = false: no config yet (login).
T.traitTree = nil
T.traitsReady = true
T.traitPaneOffset = 3930
T.spellNames = {}
local CONFIG_ID = 7001

-- T.traitLayout = "perPane": one trait tree per pane (1101..1103) instead of
-- one tree for all. Never seen in game; ReadTrees supports it, and it's the
-- only layout that can express an EMPTY pane (a pane with no nodes has no
-- position to be found by), which the step-8 fixture's "hunter, missing third
-- tree" scenario needs.
T.traitLayout = "single"
local function traitData()
  if T.traitTree then return T.traitTree end
  local nodes, most = {}, 0
  local perPane = T.traitLayout == "perPane"
  local data = { treeIDs = {}, trees = {} }
  for p in ipairs(T.talentTabs) do
    if perPane then data.treeIDs[p] = 1100 + p; data.trees[1100 + p] = {} end
  end
  if not perPane then data.treeIDs[1] = 1100; data.trees[1100] = nodes end
  for _, list in ipairs(T.talentTabs) do most = math.max(most, #list) end
  for k = 1, most do
    for p, list in ipairs(T.talentTabs) do
      local x = list[k]
      if x then
        table.insert(perPane and data.trees[1100 + p] or nodes, { id = 100000 + p * 1000 + k,
          spellID = 200000 + p * 1000 + k,
          posX = 1020 + (p - 1) * T.traitPaneOffset + (x.column - 1) * 600,
          posY = 2130 + (x.tier - 1) * 600, src = x, name = x.name })
      end
    end
  end
  return data
end

local nodeIndex = {}     -- nodeID -> node record, rebuilt by GetTreeNodes
local function nodeRank(n) if n.src then return n.src.rank or 0 end return n.rank or 0 end
local function nodeMax(n) if n.src then return n.src.maxRank end return n.maxRank end
-- 13.12: ranks bought but not applied yet (retail's staged changes; the
-- "traits" write stub below). Applied rank = .rank, staged on top = .staged.
local function nodeStaged(n) return (n.src or n).staged or 0 end
local function stagedTotal()
  local s = 0
  for _, list in ipairs(T.talentTabs) do for _, x in ipairs(list) do s = s + (x.staged or 0) end end
  return s
end

C_SpecializationInfo = {
  GetActiveSpecGroup = function() return 1 end,
  GetCombatConfigIDForSpecGroup = function(group)
    if not T.traitsReady or group ~= 1 then return nil end
    return CONFIG_ID
  end,
}
C_Traits = {
  GetConfigInfo = function(configID)
    if configID ~= CONFIG_ID then return nil end
    local ids = {}
    for i, id in ipairs(traitData().treeIDs) do ids[i] = id end
    return { ID = configID, type = 1, name = "", treeIDs = ids }
  end,
  GetTreeNodes = function(treeID)
    local data = traitData()
    local out = {}
    for _, n in ipairs(data.trees[treeID] or {}) do
      nodeIndex[n.id] = n
      T.spellNames[n.spellID] = n.name
      out[#out + 1] = n.id
    end
    return out
  end,
  GetNodeInfo = function(configID, nodeID)
    local n = nodeIndex[nodeID]
    -- The real API answers an unknown node with a table whose ID is 0.
    if configID ~= CONFIG_ID or not n then return { ID = 0, entryIDs = {}, visibleEdges = {} } end
    -- Retail meaning (13.12): activeRank = applied, currentRank / ranksPurchased
    -- = applied + staged. T.activeIncludesStaged models a client where
    -- activeRank counts staged ranks too (the risk landed() guards against).
    local r, st = nodeRank(n), nodeStaged(n)
    return { ID = n.id, posX = n.posX, posY = n.posY, activeRank = T.activeIncludesStaged and r + st or r,
             ranksPurchased = r + st, currentRank = r + st, maxRanks = nodeMax(n), entryIDs = { n.id + 500000 },
             visibleEdges = {}, isVisible = true, canPurchaseRank = T.canPurchaseRank }
  end,
  GetEntryInfo = function(configID, entryID)
    if configID ~= CONFIG_ID or not nodeIndex[entryID - 500000] then return nil end
    return { definitionID = entryID + 500000, type = 1, maxRanks = nodeMax(nodeIndex[entryID - 500000]) }
  end,
  GetDefinitionInfo = function(definitionID)
    local n = nodeIndex[definitionID - 1000000]
    if not n then return nil end
    return { spellID = n.spellID }
  end,
  -- 13.12: unspent talent points as the tree's trait currency (retail shape:
  -- a list of { traitCurrencyID, quantity, maxQuantity, spent }). Same pool as
  -- UnitCharacterPoints below (T.talentPoints); excludeStagedChanges = false
  -- also subtracts the staged ranks, like the real one. A test removes it
  -- (= nil) for a client without it, or replaces it for odd answers.
  GetTreeCurrencyInfo = function(configID, _, excludeStaged)
    if configID ~= CONFIG_ID then return {} end
    local q = T.talentPoints or 0
    if not excludeStaged then q = q - stagedTotal() end
    return { { traitCurrencyID = 1, quantity = q, maxQuantity = 51, spent = 0 } }
  end,
}
C_Spell = {
  GetSpellName = function(id) return T.spellNames[id] end,
  -- Takes a spell id (talents) or a name (Macros.lua's spellbook check, same
  -- answer as the GetSpellTexture global below), like the real one.
  GetSpellTexture = function(id)
    if T.knownSpells[id] then return T.knownSpells[id] end
    if T.spellNames[id] then return "Interface\\Icons\\INV_Misc_QuestionMark" end
  end,
}

-- Classic's GetTalentInfo(tab, index): NOT on WoW Forever (13.10). It stays in
-- the default fake client only as the "hypothetical Classic client" that step
-- 10's direct LearnTalent engine is tested against: the addon reads talents
-- through C_Traits only, and uses GetTalentInfo just to confirm a (tab, index)
-- address before any Classic-style write (Talents.lua legacyMatches). The
-- realistic Forever client is new_runtime(forever=True), which removes it.
function GetTalentInfo(tab, i)
  local x = T.talentTabs[tab] and T.talentTabs[tab][i]
  if not x then return nil end
  return x.name, x.icon or "Interface\\Icons\\INV_Misc_QuestionMark", x.tier, x.column, x.rank or 0, x.maxRank,
    false, true
end
-- Step 9: tree names. Classic shape (name, icon, pointsSpent, fileName) by
-- default; T.tabInfoShape = "new" gives the newer id-first shape, "error"
-- makes it throw, and GetTalentTabInfo = nil tests a client without it.
T.tabNames = {}
function GetTalentTabInfo(tab)
  local name = T.tabNames[tab]
  if T.tabInfoShape == "error" then error("GetTalentTabInfo: bad argument") end
  if T.tabInfoShape == "new" then return 100 + tab, name, "desc", "icon", 0, "bg", 0, true end
  return name, "icon", 0, "file"
end
function GetLocale() return T.locale or "enUS" end

-- Step 10: a fake server for talent learning. LearnTalent only SENDS a
-- request (like the real one: the rank changes when the server answers);
-- T.server() delivers the queued requests, applying Classic's rules (a free
-- point, rank below max, 5 points in that tree per tier, prerequisite maxed),
-- and fires CHARACTER_POINTS_CHANGED for each point that landed. A refused
-- request changes nothing and fires nothing. T.learnBlocked = true: requests
-- vanish (an addon-blocked call; with T.forbiddenEvent the client also fires
-- ADDON_ACTION_FORBIDDEN). T.learnError: LearnTalent raises.
-- It raises in combat, so a learn sent in combat fails the tests.
-- talentWrites counts every call (steps 8/9 tests require 0).
T.talentWrites = 0
T.learnCalls = {}
T.learnQueue = {}
function LearnTalent(tab, i)
  T.talentWrites = T.talentWrites + 1
  if T.combat then error("LearnTalent: blocked in combat (test stub)", 2) end
  table.insert(T.learnCalls, tab .. ":" .. i)
  if T.learnError then error(T.learnError, 2) end
  if T.learnBlocked then
    if T.forbiddenEvent then T.fire("ADDON_ACTION_FORBIDDEN", "RoadToForever", "LearnTalent()") end
    return
  end
  table.insert(T.learnQueue, { tab, i })
end
local function talentAt(tab, tier, column)
  for _, x in ipairs(T.talentTabs[tab] or {}) do
    if x.tier == tier and x.column == column then return x end
  end
end
function T.canLearn(tab, i)
  local x = T.talentTabs[tab] and T.talentTabs[tab][i]
  if not x or (T.talentPoints or 0) <= 0 or (x.rank or 0) >= x.maxRank then return false end
  local spent = 0
  for _, y in ipairs(T.talentTabs[tab]) do spent = spent + (y.rank or 0) end
  if spent < (x.tier - 1) * 5 then return false end
  if x.prereq then
    local p = talentAt(tab, x.prereq[1], x.prereq[2])
    if p and (p.rank or 0) < p.maxRank then return false end
  end
  return true
end
local function applyPoint(tab, i)
  local x = T.talentTabs[tab][i]
  x.rank = (x.rank or 0) + 1
  T.talentPoints = T.talentPoints - 1
end
-- Deliver up to `max` queued requests (default: until the queue is empty;
-- each answer may make the addon send the next one).
function T.server(max)
  local n = 0
  while #T.learnQueue > 0 and n < (max or 1000) do
    local req = table.remove(T.learnQueue, 1)
    n = n + 1
    if not T.serverRejects and T.canLearn(req[1], req[2]) then
      applyPoint(req[1], req[2])
      T.fire("CHARACTER_POINTS_CHANGED")
    end
  end
  return n
end
-- The player clicking a talent in Blizzard's own window (guided mode).
function T.playerLearn(tab, i)
  if not T.canLearn(tab, i) then return false end
  applyPoint(tab, i)
  T.fire("CHARACTER_POINTS_CHANGED")
  return true
end
-- Classic shape: tier, column, isLearnable per prerequisite (isLearnable is
-- 1 or nil, so the addon must not count returns with #).
function GetTalentPrereqs(tab, i)
  local x = T.talentTabs[tab] and T.talentTabs[tab][i]
  if not (x and x.prereq) then return end
  local p = talentAt(tab, x.prereq[1], x.prereq[2])
  return x.prereq[1], x.prereq[2], (p and (p.rank or 0) >= p.maxRank) and 1 or nil
end
-- Blizzard's preview/commit API (Wrath-style). Present in the stubs but OFF
-- (no GetCVarBool), like a client that only carries the shared code. The
-- commit must never be called by the addon; the fill only in preview mode.
local function talentWrite(what)
  return function() T.talentWrites = T.talentWrites + 1; error(what .. " called outside preview mode", 2) end
end
LearnPreviewTalents = talentWrite("LearnPreviewTalents")
AddPreviewTalentPoints = talentWrite("AddPreviewTalentPoints")

-- 13.12: C_Traits WRITES ("traits" learning mode), OFF by default so every
-- earlier test runs on the client it was written for. T.installTraitWrites(
-- model) adds them:
--   "staged"         (retail-like, the expected case) PurchaseRank stages a
--                    rank locally (currentRank up, activeRank not, free points
--                    excluding staged unchanged); CommitConfig queues the
--                    commit; T.traitServer() applies everything staged and
--                    fires TRAIT_CONFIG_UPDATED(configID).
--   "stagedNoCommit" the same staging, but no CommitConfig at all.
--   "immediate"      no CommitConfig; PurchaseRank applies the rank and takes
--                    the point at once; TRAIT_CONFIG_UPDATED comes later
--                    (T.traitServer()).
--   "async"          no CommitConfig; PurchaseRank only sends; T.traitServer()
--                    applies it (Classic rules) and fires TRAIT_CONFIG_UPDATED.
-- Failure switches: T.purchaseRejects (returns false), T.purchaseError
-- (raises), T.purchaseLies (returns true, changes nothing, ever),
-- T.purchaseForbidden (ADDON_ACTION_FORBIDDEN inside the call),
-- T.commitRejects / T.commitError, T.commitServerFails (the server answers
-- CONFIG_COMMIT_FAILED; staged ranks stay staged), T.serverRejects (the
-- server applies nothing, silently). Both writes raise in combat and count in
-- T.talentWrites; T.traitCalls logs "purchase:<name>" / "commit".
T.traitCalls = {}
T.traitQueue = {}
local function nodeSrc(nodeID) local n = nodeIndex[nodeID]; return n and (n.src or n) end
local function tabOf(src)
  for t, list in ipairs(T.talentTabs) do for _, x in ipairs(list) do if x == src then return t end end end
end
-- Classic rules on applied + staged ranks (staging lets you plan the whole
-- tree before applying, like Blizzard's window).
local function canStage(x)
  local t = tabOf(x)
  if not t or (T.talentPoints or 0) - stagedTotal() <= 0 then return false end
  if (x.rank or 0) + (x.staged or 0) >= x.maxRank then return false end
  local spent = 0
  for _, y in ipairs(T.talentTabs[t]) do spent = spent + (y.rank or 0) + (y.staged or 0) end
  if spent < (x.tier - 1) * 5 then return false end
  if x.prereq then
    local p = talentAt(t, x.prereq[1], x.prereq[2])
    if p and (p.rank or 0) + (p.staged or 0) < p.maxRank then return false end
  end
  return true
end
local function traitWrite(what)
  T.talentWrites = T.talentWrites + 1
  if T.combat then error(what .. ": blocked in combat (test stub)", 3) end
end
function T.installTraitWrites(model)
  T.traitModel = model or "staged"
  C_Traits.PurchaseRank = function(configID, nodeID)
    traitWrite("PurchaseRank")
    local x = nodeSrc(nodeID)
    table.insert(T.traitCalls, "purchase:" .. (x and x.name or tostring(nodeID)))
    if T.purchaseError then error(T.purchaseError, 2) end
    if T.purchaseForbidden then
      T.fire("ADDON_ACTION_FORBIDDEN", "RoadToForever", "C_Traits.PurchaseRank()")
      return
    end
    if T.purchaseRejects then return false end
    if T.purchaseLies then return true end
    if configID ~= CONFIG_ID or not x then return false end
    if T.traitModel == "async" then
      table.insert(T.traitQueue, { kind = "apply", x = x })
      return true
    end
    if not canStage(x) then return false end
    if T.traitModel == "immediate" then
      x.rank = (x.rank or 0) + 1
      T.talentPoints = T.talentPoints - 1
      table.insert(T.traitQueue, { kind = "event" })
      return true
    end
    x.staged = (x.staged or 0) + 1
    return true
  end
  if T.traitModel == "staged" then
    C_Traits.CommitConfig = function(configID)
      traitWrite("CommitConfig")
      table.insert(T.traitCalls, "commit")
      if T.commitError then error(T.commitError, 2) end
      if T.commitRejects then return false end
      if configID ~= CONFIG_ID or stagedTotal() == 0 then return false end
      table.insert(T.traitQueue, { kind = "commit" })
      return true
    end
  else
    C_Traits.CommitConfig = nil
  end
end
-- Deliver up to `max` queued trait requests (default: until the queue is
-- empty; each answer may make the addon send the next one).
function T.traitServer(max)
  local n = 0
  while #T.traitQueue > 0 and n < (max or 1000) do
    local req = table.remove(T.traitQueue, 1)
    n = n + 1
    if req.kind == "commit" then
      if T.commitServerFails then
        T.fire("CONFIG_COMMIT_FAILED", CONFIG_ID)
      elseif not T.serverRejects then
        for _, list in ipairs(T.talentTabs) do
          for _, x in ipairs(list) do
            if (x.staged or 0) > 0 then
              x.rank = (x.rank or 0) + x.staged
              T.talentPoints = T.talentPoints - x.staged
              x.staged = 0
            end
          end
        end
        T.fire("TRAIT_CONFIG_UPDATED", CONFIG_ID)
      end
    elseif req.kind == "apply" then
      if not T.serverRejects and canStage(req.x) then
        req.x.rank = (req.x.rank or 0) + 1
        T.talentPoints = T.talentPoints - 1
        T.fire("TRAIT_CONFIG_UPDATED", CONFIG_ID)
      end
    else
      T.fire("TRAIT_CONFIG_UPDATED", CONFIG_ID)
    end
  end
  return n
end
-- The player clicking a talent in Blizzard's window WITHOUT applying it (a
-- staged change of their own), and clicking Apply Changes.
function T.playerStage(tab, i)
  local x = T.talentTabs[tab][i]
  x.staged = (x.staged or 0) + 1
end
function T.playerApply()
  table.insert(T.traitQueue, { kind = "commit" })
  T.traitServer()
end

-- Blizzard's talent window (load-on-demand Blizzard_TalentUI), for guided
-- mode: <name>, <name>Talent<i> (button i = talent index i of the tab shown),
-- <name>Tab<n>, .selectedTab. Not loaded until ToggleTalentFrame is called.
T.talentFrameName = "TalentFrame"
function T.makeTalentFrame(name)
  local f = CreateFrame("Frame", name, UIParent)
  f:Hide()
  f.selectedTab = 1
  for i = 1, 30 do CreateFrame("Button", name .. "Talent" .. i, f):SetSize(37, 37) end
  for t = 1, 3 do CreateFrame("Button", name .. "Tab" .. t, f):SetSize(60, 24) end
  return f
end
function ToggleTalentFrame()
  T.toggles = (T.toggles or 0) + 1
  local f = _G[T.talentFrameName] or T.makeTalentFrame(T.talentFrameName)
  if f:IsShown() then f:Hide() else f:Show() end
end
function PanelTemplates_GetSelectedTab(f) return f.selectedTab end

-- Quick settings (ADDON_PLAN 12.4.1): CVars as strings, like the client.
-- T.cvars = live values, T.cvarDefaults = what GetCVarDefault answers
-- (deliberately not a "usual" default, so a hardcoded guess fails the tests).
-- GetCVar of an unknown CVar = nil. SetCVar logs every call in T.cvarWrites and
-- RAISES in combat: that is test strictness (any SetCVar in combat fails the
-- suite), not a claim about the real client (TESTING.md 16). T.cvarClamp[name]
-- = the value the client stores instead (a client that clamps); T.cvarError =
-- SetCVar raises. It fires CVAR_UPDATE like the client.
T.cvars = { cameraDistanceMaxZoomFactor = "1.7", UnitNamePlayerGuild = "1", UnitNamePlayerPVPTitle = "1" }
T.cvarDefaults = { cameraDistanceMaxZoomFactor = "1.7", UnitNamePlayerGuild = "1", UnitNamePlayerPVPTitle = "1" }
T.cvarWrites = {}
T.cvarClamp = {}
function GetCVar(name) return T.cvars[name] end
function GetCVarDefault(name) return T.cvarDefaults[name] end
function SetCVar(name, value)
  if T.combat then error("SetCVar: called in combat (test stub)", 2) end
  table.insert(T.cvarWrites, name .. "=" .. tostring(value))
  if T.cvarError then error(T.cvarError, 2) end
  if T.cvars[name] == nil then return end
  T.cvars[name] = T.cvarClamp[name] or tostring(value)
  T.fire("CVAR_UPDATE", name, value)
end

function InCombatLockdown() return T.combat end
function GetSpellTexture(name) return T.knownSpells[name] end
function GetItemInfo() return nil end
function UnitClass() return T.className or "Warrior", T.classToken or "WARRIOR", 1 end
function IsShiftKeyDown() return T.shift or false end
function GetCursorPosition() return T.cursorX or 500, T.cursorY or 400 end
function UnitCharacterPoints() return T.talentPoints or 0 end
function PlaySound() end
SOUNDKIT = { IG_SPELLBOOK_OPEN = 1, IG_SPELLBOOK_CLOSE = 2, IG_ABILITY_PAGE_TURN = 3, IG_MAINMENU_OPEN = 4 }
time = os.time
C_Timer = { After = function(_, fn) table.insert(T.timers, fn) end }
function T.runTimers()
  for _ = 1, 10 do
    local list = T.timers
    if #list == 0 then return end
    T.timers = {}
    for _, fn in ipairs(list) do fn() end
  end
end
-- Step 10: only the timers pending NOW (one 0.5 s step), not the ones they
-- schedule (runTimers would also fire the next point's timeout at once).
function T.runTimersOnce()
  local list = T.timers
  T.timers = {}
  for _, fn in ipairs(list) do fn() end
end
C_XMLUtil = { GetTemplateInfo = function(name) if T.templates[name] then return {} end end }
CLASS_ICON_TCOORDS = { WARRIOR = { 0, 0.25, 0, 0.25 }, PALADIN = { 0, 0.25, 0.5, 0.75 } }
LOCALIZED_CLASS_NAMES_MALE = { WARRIOR = "Warrior", PALADIN = "Paladin", HUNTER = "Hunter",
  PRIEST = "Priest", ROGUE = "Rogue", MAGE = "Mage", WARLOCK = "Warlock", SHAMAN = "Shaman" }
UISpecialFrames = {}
SlashCmdList = {}
BackdropTemplateMixin = {}
function ChatEdit_InsertLink(text) T.chatInsert = text; return true end

-- ---------------------------------------------------------------------------
-- Frames: generic objects. Unknown methods are no-ops returning nil, so the
-- tests catch logic/nil errors in our code, not missing stub methods.
-- ---------------------------------------------------------------------------
local noop = function() end
local methods = {}
-- Strict like real widgets: unknown keys are nil, so a misspelt method or a
-- template child that doesn't exist fails the tests. Real widget methods we
-- call but don't need to model are listed here as no-ops.
for _, name in ipairs({
  "SetSize", "SetWidth", "SetHeight", "SetPoint", "ClearAllPoints", "SetAllPoints",
  "SetFrameStrata", "SetToplevel", "SetMovable", "EnableMouse", "RegisterForDrag",
  "SetClampedToScreen", "StartMoving", "StopMovingOrSizing", "SetBackdrop",
  "SetBackdropColor", "SetJustifyH", "SetTexCoord", "SetHighlightTexture",
  "SetPushedTexture", "SetDisabledTexture", "SetCheckedTexture", "RegisterForClicks",
  "SetMultiLine", "SetAutoFocus", "SetFontObject", "SetMaxLetters", "SetMaxBytes",
  "SetScrollChild", "SetFocus", "ClearFocus", "HighlightText",
  "SetMotionScriptsWhileDisabled", "SetHitRectInsets", "SetFrameLevel",
  "SetBlendMode", "SetTextInsets",
}) do methods[name] = noop end
local MT = { __index = methods }

local function newObject(kind, name, parent)
  local o = setmetatable({ __kind = kind, __shown = true, __scripts = {}, __text = "",
    __parent = parent, __enabled = true, __name = name }, MT)
  if name then _G[name] = o end
  return o
end

function methods:GetName() return self.__name end
function methods:Show()
  local was = self:IsShown()
  self.__shown = true
  if not was and self:IsShown() and self.__scripts.OnShow then self.__scripts.OnShow(self) end
end
function methods:Hide()
  local was = self.__shown
  self.__shown = false
  if was and self.__scripts.OnHide then self.__scripts.OnHide(self) end
end
function methods:SetShown(v) if v then self:Show() else self:Hide() end end
function methods:IsShown() return self.__shown end
-- Like the real client: IsShown is the frame's own flag, IsVisible also
-- needs every parent shown (the main window's pages rely on this, step 6).
function methods:IsVisible()
  local o = self
  while o do
    if not o.__shown then return false end
    o = o.__parent
  end
  return true
end
function methods:SetID(i) self.__id = i end
function methods:GetID() return self.__id end
function methods:SetSize(w, h) self.__w, self.__h = w, h end
function methods:GetWidth() return self.__w or 0 end
function methods:GetHeight() return self.__h or 0 end
function methods:GetCenter() return self.__cx or 0, self.__cy or 0 end
function methods:SetPoint(...) self.__point = { ... } end
function methods:ClearAllPoints() self.__point = nil end
function methods:SetScript(k, fn) self.__scripts[k] = fn end
function methods:GetScript(k) return self.__scripts[k] end
function methods:HookScript(k, fn)
  local old = self.__scripts[k]
  self.__scripts[k] = old and function(...) old(...); fn(...) end or fn
end
function methods:SetText(t)
  self.__text = t
  if self.__kind == "EditBox" and self.__scripts.OnTextChanged then self.__scripts.OnTextChanged(self, false) end
end
function methods:GetText() return self.__text end
function methods:SetEnabled(v) self.__enabled = not not v end
function methods:Enable() self.__enabled = true end
function methods:Disable() self.__enabled = false end
function methods:IsEnabled() return self.__enabled end
function methods:SetChecked(v) self.__checked = not not v end
function methods:GetChecked() return self.__checked end
function methods:CreateTexture() return newObject("Texture") end
function methods:CreateFontString() return newObject("FontString") end
function methods:GetStringHeight() return 14 end
function methods:GetStringWidth() return 7 * #(self.__text or "") end
function methods:GetEffectiveScale() return 1 end
function methods:IsMouseOver() return false end
function methods:GetPoint() return "CENTER", nil, "CENTER", 10, 20 end
function methods:SetNormalTexture(t) self.__normal = self.__normal or newObject("Texture"); self.__normal.__tex = t end
function methods:GetNormalTexture() return self.__normal end
function methods:SetTexture(t) self.__tex = t end
function methods:SetDesaturated(v) self.__desat = v end
function methods:SetTextColor(r, g, b) self.__color = { r, g, b } end
function methods:SetVertexColor(r, g, b) self.__vertex = { r, g, b } end
-- Step 10: the guided glow's pulse. T.frameMethods.CreateAnimationGroup = nil
-- simulates a client without it (the fallback runtime does).
function methods:CreateAnimationGroup()
  local ag = { playing = false }
  function ag:CreateAnimation()
    local a = {}
    for _, m in ipairs({ "SetFromAlpha", "SetToAlpha", "SetDuration" }) do a[m] = noop end
    return a
  end
  function ag:SetLooping(v) self.looping = v end
  function ag:Play() self.playing = true end
  function ag:Stop() self.playing = false end
  self.__anim = ag
  return ag
end
T.frameMethods = methods
function methods:RegisterEvent(e) self.__events = self.__events or {}; self.__events[e] = true end
function methods:UnregisterEvent(e) if self.__events then self.__events[e] = nil end end
-- Test helpers on frames
function methods:Click(button)
  if self.__enabled and self.__scripts.OnClick then self.__scripts.OnClick(self, button or "LeftButton") end
end
function methods:Fire(script, ...)
  if self.__scripts[script] then self.__scripts[script](self, ...) end
end

function CreateFrame(kind, name, parent, template)
  if template and not T.templates[template] then
    -- Real client: unknown template = frame without it (logged, no error).
    return newObject(kind, name, parent)
  end
  local f = newObject(kind, name, parent)
  if template == "PortraitFrameTemplate" or template == "ButtonFrameTemplate" then
    f.CloseButton = newObject("Button", nil, f)
    f.PortraitContainer = { portrait = newObject("Texture") }
    f.SetTitle = function(self, t) self.__title = t end
  elseif template == "InputScrollFrameTemplate" then
    f.EditBox = newObject("EditBox", nil, f)
    f.CharCount = newObject("FontString")
  end
  return f
end

UIParent = newObject("Frame", "UIParent")
GameTooltip = newObject("GameTooltip", "GameTooltip")
GameTooltip.lines = {}
function GameTooltip:SetOwner() self.lines = {} end
function GameTooltip:AddLine(t) table.insert(self.lines, t) end
function GameTooltip:NumLines() return #self.lines end
-- Step 9: the game's own talent tooltip. Records what it was asked for and
-- adds the talent's name, like the real one's first line.
function GameTooltip:SetTalent(tab, i)
  self.talentArgs = { tab, i }
  local name = GetTalentInfo(tab, i)
  if name then table.insert(self.lines, name) end
end
-- 13.10: the spell tooltip, used for talents read through C_Traits.
function GameTooltip:SetSpellByID(id)
  self.spellArgs = { id }
  local name = T.spellNames[id]
  if name then table.insert(self.lines, name) end
end
UIErrorsFrame = newObject("Frame", "UIErrorsFrame")
function UIErrorsFrame:AddMessage(m) table.insert(T.errors, m) end
DEFAULT_CHAT_FRAME = newObject("Frame", "DEFAULT_CHAT_FRAME")
function DEFAULT_CHAT_FRAME:AddMessage(m) table.insert(T.chat, m) end

-- Step 6: the minimap (140 x 140, centre at 1000, 600 on a scale-1 screen).
Minimap = newObject("Frame", "Minimap")
Minimap:SetSize(140, 140)
Minimap.__cx, Minimap.__cy = 1000, 600

-- Blizzard's tab helpers (SharedXML PanelTemplates), reduced to what the
-- main window uses: the selected tab is disabled, like the real one does.
function PanelTemplates_SetNumTabs(frame, n) frame.numTabs = n end
function PanelTemplates_TabResize() end
function PanelTemplates_SetTab(frame, id)
  frame.selectedTab = id
  for i = 1, frame.numTabs do
    local tab = frame.Tabs[i]
    if i == id then tab:Disable() else tab:Enable() end
  end
end

-- MenuUtil (newer clients): records the menu the generator builds into
-- T.menu = { {kind=, text=, ...}, ... } and keeps the callbacks callable.
MenuUtil = {
  CreateContextMenu = function(owner, generator)
    local items = {}
    local root = {}
    function root:CreateTitle(text) table.insert(items, { kind = "title", text = text }) end
    function root:CreateDivider() table.insert(items, { kind = "divider" }) end
    function root:CreateButton(text, fn) table.insert(items, { kind = "button", text = text, func = fn }) end
    function root:CreateCheckbox(text, isSel, setSel)
      table.insert(items, { kind = "check", text = text, isChecked = isSel, func = setSel })
    end
    generator(owner, root)
    T.menu, T.menuOwner = items, owner
  end,
}

-- Find the frame the addon registered for events (Core.lua's anonymous one).
T.allFrames = {}
local origNew = newObject
newObject = function(kind, name, parent)
  local o = origNew(kind, name, parent)
  table.insert(T.allFrames, o)
  return o
end
function T.fire(event, ...)
  for _, f in ipairs(T.allFrames) do
    if f.__events and f.__events[event] and f.__scripts.OnEvent then
      f.__scripts.OnEvent(f, event, ...)
    end
  end
end

return T
