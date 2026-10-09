-- Ranks.lua: rank-aware macros (ADDON_PLAN.md 16, v0.19.0).
--
-- On WoW Forever an unranked spell name can resolve to a rank the character doesn't
-- know: on a level-18 Warrior `/cast Charge` fails because C_Spell.GetSpellInfo("Charge")
-- gives Forever's level-46 Charge (spell id 1240289), not Rank 1, while `/cast Rend`
-- works. Which spells are affected isn't known in advance, so this checks them all.
--
-- Rewrite(body) returns the body the GAME macro should have:
--   * every spell name in a /cast, /castsequence or #showtooltip line without (Rank N):
--     if C_Spell.GetSpellInfo(name).spellID is a spell the player knows -> left alone;
--     if not, the highest rank the player does know is written in: Name(Rank K);
--     if no rank is known (not learned yet) -> left alone.
--   * a name that already pins a rank (the site's `Charge(Rank 1)` stopgap) is raised to
--     the highest known rank when that is higher (and left alone otherwise).
-- The highest known rank is found with C_Spell.GetSpellInfo("Name(Rank N)") for N = 12..1.
-- (The old global GetSpellInfo doesn't exist on this client; without C_Spell.GetSpellInfo
-- nothing is rewritten.) A rewritten body over 255 characters is not used: the macro
-- keeps its site text.
--
-- Library bodies are never changed: only what Macros.lua writes into game macros
-- (create, update, replace) goes through Rewrite, and Macros.Classify compares the live
-- macro with the rewritten body, so a ranked macro isn't mistaken for "needs update"
-- or "edited". When the player learns a spell (LEARNED_SPELL_IN_TAB / SPELLS_CHANGED)
-- Macros.SyncRanks re-checks the macros the addon made and raises ranks; macros the
-- player edited are never touched, and in combat the EditMacro calls wait for its end
-- (Macros.UpdateMany queues them).
--
-- Read-only except through Macros.lua's writes: spell getters only.

local _, R2F = ...
local L = R2F.L

local Ranks = {}
R2F.Ranks = Ranks

local MAX_RANK = 12
local MAX_BODY = 255

local function getInfo(name)
  if not (C_Spell and C_Spell.GetSpellInfo) then return nil end
  local ok, info = pcall(C_Spell.GetSpellInfo, name)
  if ok and type(info) == "table" then return info end
end

local function isKnown(id)
  if not id then return false end
  if IsPlayerSpell and IsPlayerSpell(id) then return true end
  if IsSpellKnown and IsSpellKnown(id) then return true end
  if C_SpellBook and C_SpellBook.IsSpellKnown and C_SpellBook.IsSpellKnown(id) then return true end
  return false
end

-- "Charge(Rank 2)" -> "Charge", 2.   "Charge" -> "Charge", nil.
local function parseName(name)
  local base, rank = name:match("^(.-)%s*%(%s*[Rr]ank%s+(%d+)%s*%)$")
  if base then return base, tonumber(rank) end
  return name, nil
end

-- Highest rank of `base` the player knows, and its spell id; nil if none.
function Ranks.HighestKnown(base)
  for n = MAX_RANK, 1, -1 do
    local info = getInfo(base .. "(Rank " .. n .. ")")
    if info and isKnown(info.spellID) then return n, info.spellID end
  end
end

-- Resolve one name for one rewrite pass: the name to write, or nil to leave it as is.
-- Also used by /r2f ranks.
local function decide(name, memo)
  local base, pinned = parseName(name)
  if base == "" then return nil end
  local key = base .. "\0" .. tostring(pinned)
  if memo[key] ~= nil then return memo[key] or nil end
  local result = false
  if pinned then
    local best = Ranks.HighestKnown(base)
    if best and best > pinned then result = base .. "(Rank " .. best .. ")" end
  else
    local info = getInfo(base)
    if info and info.spellID and not isKnown(info.spellID) then
      local best = Ranks.HighestKnown(base)
      if best then result = base .. "(Rank " .. best .. ")" end
    end
  end
  memo[key] = result
  return result or nil
end

-- Apply `fix` to the spell-name part of one clause: leading [conditions], then
-- an optional "!", the name, trailing blanks. Returns the clause with the name replaced.
local function mapClause(clause, fix)
  local pos = 1
  while true do
    local _, e = clause:find("^%s*%b[]", pos)
    if not e then break end
    pos = e + 1
  end
  local head, tail = clause:sub(1, pos - 1), clause:sub(pos)
  local ws, bang, name, trail = tail:match("^(%s*)(!?)(.-)(%s*)$")
  if not name or name == "" then return clause end
  return head .. ws .. bang .. (fix(name) or name) .. trail
end

local function mapLine(line, fix)
  local cmd, rest = line:match("^(/%a+)(.*)$")
  if cmd then
    cmd = cmd:lower()
    if cmd == "/cast" then
      if not rest:match("^%s") then return line end
      return line:match("^/%a+") .. rest:gsub("[^;]+", function(clause) return mapClause(clause, fix) end)
    elseif cmd == "/castsequence" then
      if not rest:match("^%s") then return line end
      -- [conditions] reset=... Name1, Name2, ...
      local head, names = "", rest
      local pos = 1
      while true do
        local _, e = names:find("^%s*%b[]", pos)
        if not e then break end
        pos = e + 1
      end
      head, names = names:sub(1, pos - 1), names:sub(pos)
      local reset, list = names:match("^(%s*reset=%S+)(.*)$")
      if reset then head, names = head .. reset, list end
      names = names:gsub("[^,]+", function(item) return mapClause(item, fix) end)
      return line:match("^/%a+") .. head .. names
    end
  end
  local arg = line:match("^#[Ss][Hh][Oo][Ww][Tt][Oo][Oo][Ll][Tt][Ii][Pp]( .*)$")
  if arg then
    return line:sub(1, #line - #arg) .. arg:gsub("[^;]+", function(clause) return mapClause(clause, fix) end)
  end
  return line
end

-- The body the game macro should have. Second return: true if the ranked body would
-- have been over 255 characters (so the original is returned).
function Ranks.Rewrite(body)
  if not (C_Spell and C_Spell.GetSpellInfo) or type(body) ~= "string" then return body end
  local memo = {}
  local fix = function(name) return decide(name, memo) end
  local out = body:gsub("[^\n]+", function(line) return mapLine(line, fix) end)
  if out == body then return body end
  local _, chars = out:gsub("[^\128-\191]", "")
  if chars > MAX_BODY then return body, true end
  return out
end

-- Every spell used by the macros this character made whose unranked name doesn't
-- resolve to a known spell: { { spell =, use = "Charge(Rank 1)" or nil, macros = {short, ...} }, ... }
-- sorted by spell name; `tooLong` = names of macros that stay unranked because the
-- ranked text would not fit in 255 characters.
function Ranks.Report()
  local rows, order, tooLong = {}, {}, {}
  if not (C_Spell and C_Spell.GetSpellInfo) then return order, tooLong, false end
  local seen = {}
  for id in pairs(R2F.Library.AllCreated()) do
    local e = R2F.Library.Get(id)
    if e and e.body then
      local names = {}
      local collect = function(name)
        local base = parseName(name)
        if base ~= "" then names[base] = true end
        return nil
      end
      for line in e.body:gmatch("[^\n]+") do mapLine(line, collect) end
      for base in pairs(names) do
        local info = getInfo(base)
        if info and info.spellID and not isKnown(info.spellID) then
          local row = rows[base]
          if not row then
            local best = Ranks.HighestKnown(base)
            row = { spell = base, use = best and (base .. "(Rank " .. best .. ")") or nil, macros = {} }
            rows[base] = row
            order[#order + 1] = row
          end
          if not seen[base .. "\0" .. e.short] then
            seen[base .. "\0" .. e.short] = true
            row.macros[#row.macros + 1] = e.short
          end
        end
      end
      local _, long = Ranks.Rewrite(e.body)
      if long then tooLong[#tooLong + 1] = e.short end
    end
  end
  table.sort(order, function(a, b) return a.spell < b.spell end)
  for _, row in ipairs(order) do table.sort(row.macros) end
  table.sort(tooLong)
  return order, tooLong, true
end

-- /r2f ranks
function Ranks.Print()
  local order, tooLong, ok = Ranks.Report()
  if not ok then R2F.Print(L.RANKS_NO_API) return end
  if #order == 0 then
    R2F.Print(L.RANKS_NONE)
  else
    R2F.Print(L.RANKS_HEAD)
    for _, row in ipairs(order) do
      local macros = table.concat(row.macros, ", ")
      if row.use then
        R2F.Print(L.RANKS_LINE:format(row.spell, row.use, macros))
      else
        R2F.Print(L.RANKS_LINE_NONE:format(row.spell, macros))
      end
    end
  end
  if #tooLong > 0 then R2F.Print(L.RANKS_TOO_LONG:format(table.concat(tooLong, ", "))) end
end

-- LEARNED_SPELL_IN_TAB / SPELLS_CHANGED (Core.lua): re-check the macros after a short
-- pause (the events come in bursts; the spellbook has to settle first).
local pending = false
function Ranks.OnLearned()
  if pending then return end
  if not (C_Timer and C_Timer.After) then R2F.Macros.SyncRanks() return end
  pending = true
  C_Timer.After(1, function()
    pending = false
    R2F.Macros.SyncRanks()
  end)
end
