-- Training.lua: what to train next, read from YOUR class trainer.
--
-- No spell list ships with the addon: each time the class trainer window opens (TRAINER_SHOW, not a
-- profession trainer) every service it lists is saved per character (R2FCharDB.training):
--   spells = { { n = name, r = "Rank 4", lvl = 24, cost = copper, s = "available"|"unavailable"|"used" } }
--   when = time(), level = your level then
-- So the list is Forever's own (prices with your reputation discount, Forever-only spells). Spells the
-- trainer hides (its "Unavailable" filter off) are not seen; the Home line says so when nothing later
-- than your level is known.
--
-- Home shows "Train now" (affordable by level, not learned) and "Next" (the next level that brings
-- something). The Tweaks switch "Training reminder" prints, on level-up, what just became trainable.
-- A spell learned since (LEARNED_SPELL_IN_SKILL_LINE, LEARNED_SPELL_IN_TAB on older clients) is marked so it leaves the lists.
--
-- Read-only game calls only (GetNumTrainerServices / GetTrainerServiceInfo / ...LevelReq / ...Cost);
-- the trainer's filters are never touched.

local _, R2F = ...
local L = R2F.L

local Training = {}
R2F.Training = Training

local function db() return R2F.Library.cdb.training end

-- The trainer's own tooltip for service `i`, as text lines { {l = left, r = right}, ... }, so the Training tab can show it
-- later without the trainer open. A hidden tooltip of ours reads it; nil when the client cannot do that.
local scan
local function scanTip(i)
  if not (CreateFrame and UIParent) then return nil end
  local ok, out = pcall(function()
    scan = scan or CreateFrame("GameTooltip", "R2FTrainScanTip", nil, "GameTooltipTemplate")
    if not (scan and scan.SetTrainerService and scan.NumLines) then return nil end
    scan:SetOwner(UIParent, "ANCHOR_NONE")
    scan:SetTrainerService(i)
    local lines = {}
    for k = 1, math.min(scan:NumLines() or 0, 12) do
      local l, r = _G["R2FTrainScanTipTextLeft" .. k], _G["R2FTrainScanTipTextRight" .. k]
      local lt, rt = l and l:GetText(), r and r:GetText()
      if type(lt) == "string" and (not _G.issecretvalue or not _G.issecretvalue(lt)) then
        if type(rt) ~= "string" or rt == "" or (_G.issecretvalue and _G.issecretvalue(rt)) then rt = nil end
        lines[#lines + 1] = { l = lt, r = rt }
      end
    end
    scan:Hide()
    return lines
  end)
  if ok and type(out) == "table" and #out > 0 then return out end
  return nil
end

-- Reads the open trainer window. Returns the number of spells saved, or nil when it isn't a class
-- trainer (or the API is missing).
function Training.Read()
  if not (GetNumTrainerServices and GetTrainerServiceInfo) then return nil end
  if IsTradeskillTrainer and IsTradeskillTrainer() then return nil end
  local n = GetNumTrainerServices() or 0
  local list = {}
  for i = 1, n do
    local name, a2, a3, a4, a5 = GetTrainerServiceInfo(i)
    -- Forever (modern engine, Blizzard's own trainer window): name, serviceType, texture, reqLevel, subText.
    -- serviceType is "available" | "unavailable" | "used"; subText is the rank ("Rank 2"). Classic returns
    -- name, rank, category ("header" for a heading) and has a separate GetTrainerServiceLevelReq.
    local rank, state, lvl, icon
    if a2 == "available" or a2 == "unavailable" or a2 == "used" then
      rank, state, lvl, icon = a5, a2, tonumber(a4), a3
    else
      rank, state = a2, a3
      lvl = GetTrainerServiceLevelReq and GetTrainerServiceLevelReq(i)
      icon = GetTrainerServiceIcon and GetTrainerServiceIcon(i)
    end
    if name and state ~= "header" then
      list[#list + 1] = {
        n = name, r = rank or "",
        lvl = lvl or 0,
        cost = GetTrainerServiceCost and GetTrainerServiceCost(i) or 0,
        s = state,
        ic = (type(icon) == "string" or type(icon) == "number") and icon or nil,
        tip = scanTip(i),
      }
    end
  end
  if #list == 0 then return 0 end
  local d = db()
  -- Merge with what we knew: a later-level spell the trainer no longer lists was hidden by its
  -- "Unavailable" filter, so keep it. One that was trainable and is gone was learned (the trainer
  -- hides learned spells by default), so it goes.
  -- The same spell at the same level under another rank text is the same entry: the trainer says "Rank 2" only once
  -- you know rank 1, while the older saved line has no rank.
  local seen = {}
  for _, e in ipairs(list) do seen[e.n .. "\0" .. e.r] = true seen[e.n .. "\0\0" .. e.lvl] = true end
  local level = UnitLevel("player")
  for _, old in ipairs(d.spells or {}) do
    if not seen[old.n .. "\0" .. old.r] and not seen[old.n .. "\0\0" .. (old.lvl or 0)] and old.s == "unavailable"
        and (old.lvl or 0) > level then
      list[#list + 1] = old
    end
  end
  d.spells = list
  d.when = time and time() or 0
  d.level = UnitLevel("player")
  return #list
end

-- A spell just learned: mark every saved entry with that name (and rank, when the game gives one).
function Training.MarkLearned(name, rank)
  if not name then return end
  for _, e in ipairs(db().spells) do
    if e.n == name and (not rank or rank == "" or e.r == rank) then e.s = "used" end
  end
end

-- The shipped list (TrainingData.lua: what your class trainer sells, from Wowhead Forever) merged under what your own
-- trainer showed: the trainer's real price and tooltip win, spells only the trainer showed are kept, learned spells are
-- marked "used". Names and icons come from the game by spell id. With no shipped list (other class, older data) it is
-- just what the trainer showed.
local names_cache = {}
local function spellName(id, fallback)
  local c = names_cache[id]
  if c then return c end
  local name
  if _G.C_Spell and _G.C_Spell.GetSpellInfo then
    local ok, info = pcall(_G.C_Spell.GetSpellInfo, id)
    if ok and type(info) == "table" then name = info.name end
  elseif _G.GetSpellInfo then
    local ok, n = pcall(_G.GetSpellInfo, id)
    if ok then name = n end
  end
  if type(name) == "string" and name ~= "" then names_cache[id] = name return name end
  return fallback
end

local function spellIcon(id)
  if _G.C_Spell and _G.C_Spell.GetSpellTexture then
    local ok, tex = pcall(_G.C_Spell.GetSpellTexture, id)
    if ok and tex then return tex end
  elseif _G.GetSpellTexture then
    local ok, tex = pcall(_G.GetSpellTexture, id)
    if ok and tex then return tex end
  end
  return nil
end

local function isKnown(id)
  local f = _G.IsPlayerSpell or _G.IsSpellKnown
  if not f then return false end
  local ok, v = pcall(f, id)
  return ok and v == true
end

local function rankNum(text)
  return tonumber((text or ""):match("(%d+)")) or 0
end

function Training.Icon(id) return spellIcon(id) end

function Training.All()
  local saved = db().spells
  local shipped = R2F.TrainingData and R2F.TrainingData[R2F.playerClass]
  if not shipped then return saved end
  local level = UnitLevel("player")
  local byKey, used = {}, {}
  for _, e in ipairs(saved) do byKey[e.n .. "|" .. rankNum(e.r)] = e end
  local top = {}                      -- highest known rank per spell name (a higher rank can replace the lower in the book)
  for _, row in ipairs(shipped) do
    if isKnown(row[1]) then
      local n = spellName(row[1], row[5])
      if (top[n] or 0) < row[3] then top[n] = row[3] end
    end
  end
  local out = {}
  for _, row in ipairs(shipped) do
    local id, lvl, rank, price, wname = row[1], row[2], row[3], row[4], row[5]
    local name = spellName(id, wname)
    local key = name .. "|" .. rank
    local sv = byKey[key]
    used[key] = true
    local learned = isKnown(id) or (top[name] ~= nil and top[name] >= rank and rank > 0) or (sv ~= nil and sv.s == "used")
    out[#out + 1] = {
      n = name, r = rank > 0 and ("Rank " .. rank) or "", lvl = lvl,
      cost = (sv and (sv.cost or 0) > 0) and sv.cost or price, estimate = not (sv and (sv.cost or 0) > 0),
      s = learned and "used" or (lvl <= level and "available" or "unavailable"),
      id = id, ic = (sv and sv.ic) or spellIcon(id), tip = sv and sv.tip,
    }
  end
  for _, e in ipairs(saved) do          -- spells only your trainer showed (a Forever-only spell the list lacks)
    if not used[e.n .. "|" .. rankNum(e.r)] then out[#out + 1] = e end
  end
  return out
end


local function sortSpells(a, b)
  if a.lvl ~= b.lvl then return a.lvl < b.lvl end
  return a.n < b.n
end

-- now: trainable at `level` (not used); next: the spells of the next level above it that has any;
-- nextLevel; known: whether anything has been read at all.
function Training.Status(level, list)
  level = level or UnitLevel("player")
  local spells = list or Training.All()      -- Upcoming passes the list it already built
  local now, later, nextLevel = {}, {}, nil
  -- A line without a rank next to one with a rank (same spell, same level) is an older copy: hide it.
  local ranked = {}
  for _, e in ipairs(spells) do
    if e.r ~= "" then ranked[e.n .. "\0" .. e.lvl] = true end
  end
  local function stale(e) return e.r == "" and ranked[e.n .. "\0" .. e.lvl] end
  for _, e in ipairs(spells) do
    if e.s ~= "used" and not stale(e) then
      if e.lvl <= level then
        now[#now + 1] = e
      elseif not nextLevel or e.lvl < nextLevel then
        nextLevel = e.lvl
      end
    end
  end
  if nextLevel then
    for _, e in ipairs(spells) do
      if e.s ~= "used" and e.lvl == nextLevel and not stale(e) then later[#later + 1] = e end
    end
  end
  table.sort(now, sortSpells)
  table.sort(later, sortSpells)
  return now, later, nextLevel, #spells > 0
end

-- The Training tab: `now` (trainable at `level`), `nextList` of `nextLevel`, and `later` = { {lvl = 30, list = {...}}, ... }
-- for every further level up to the cap, in level order. The same entries Status() hides are hidden here.
Training.CAP = 60
function Training.Upcoming(level)
  level = level or UnitLevel("player")
  local spells = Training.All()
  local now, later, nextLevel, known = Training.Status(level, spells)
  local ranked = {}
  for _, e in ipairs(spells) do
    if e.r ~= "" then ranked[e.n .. "\0" .. e.lvl] = true end
  end
  local byLevel, order = {}, {}
  for _, e in ipairs(spells) do
    if e.s ~= "used" and e.lvl > level and e.lvl ~= nextLevel and e.lvl <= Training.CAP
        and not (e.r == "" and ranked[e.n .. "\0" .. e.lvl]) then
      if not byLevel[e.lvl] then byLevel[e.lvl] = {} order[#order + 1] = e.lvl end
      table.insert(byLevel[e.lvl], e)
    end
  end
  table.sort(order)
  local out = {}
  for _, lv in ipairs(order) do
    table.sort(byLevel[lv], sortSpells)
    out[#out + 1] = { lvl = lv, list = byLevel[lv] }
  end
  return now, later, nextLevel, out, known
end

local function names(list, max)
  local out = {}
  for i, e in ipairs(list) do
    if i > max then out[#out + 1] = L.TRAIN_MORE:format(#list - max) break end
    out[#out + 1] = e.r ~= "" and (e.n .. " (" .. e.r .. ")") or e.n
  end
  return table.concat(out, ", ")
end

local function cost(list)
  local c = 0
  for _, e in ipairs(list) do c = c + (e.cost or 0) end
  return c
end

-- The Home lines: train now, and next.
function Training.Lines(level)
  local now, later, nextLevel, known = Training.Status(level)
  if not known then return L.TRAIN_UNKNOWN, nil end
  local a = L.TRAIN_NOW_NONE
  if #now == 1 then
    a = L.TRAIN_NOW_ONE:format(R2F.Gameplay.Money(cost(now)), names(now, 12))
  elseif #now > 1 then
    a = L.TRAIN_NOW:format(#now, R2F.Gameplay.Money(cost(now)), names(now, 12))
  end
  local b = nextLevel and L.TRAIN_NEXT:format(nextLevel, names(later, 12)) or L.TRAIN_NEXT_NONE
  return a, b
end

-- Level-up: what reaching `level` made trainable (entries of levels in (old, level]).
function Training.NewAt(old, level)
  local out = {}
  for _, e in ipairs(Training.All()) do
    if e.s ~= "used" and e.lvl > old and e.lvl <= level then out[#out + 1] = e end
  end
  table.sort(out, sortSpells)
  return out
end

local ev = CreateFrame("Frame")
-- pcall: the game errors on an event it does not know. Forever has no LEARNED_SPELL_IN_TAB (Blizzard's own
-- 11.0 transition guide renames it to LEARNED_SPELL_IN_SKILL_LINE; both pass the spell id first), older
-- clients have only the old name, so each is tried and the one the client lacks is skipped.
for _, event in ipairs({ "TRAINER_SHOW", "TRAINER_UPDATE", "LEARNED_SPELL_IN_SKILL_LINE", "LEARNED_SPELL_IN_TAB" }) do
  pcall(ev.RegisterEvent, ev, event)
end
ev:SetScript("OnEvent", function(_, event, a1)
  if event == "TRAINER_SHOW" or event == "TRAINER_UPDATE" then
    Training.Read()
    if R2F.Home and R2F.Home.Refresh then R2F.Home.Refresh() end
    if R2F.TrainingTab and R2F.TrainingTab.Refresh then R2F.TrainingTab.Refresh() end
  elseif (event == "LEARNED_SPELL_IN_SKILL_LINE" or event == "LEARNED_SPELL_IN_TAB") and a1 then
    local name = GetSpellInfo and GetSpellInfo(a1)
    local rank = _G.GetSpellSubtext and _G.GetSpellSubtext(a1) or nil
    Training.MarkLearned(name, rank)
  end
end)

-- The level-up line (Tweaks > Alerts > Training reminder).
R2F.Gameplay.Register({
  key = "training", group = "auto", title = "TRAIN_TITLE", tip = "TRAIN_TITLE_TIP",
  events = {
    PLAYER_LEVEL_UP = function(level)
      if not level then return end
      local list = Training.NewAt(level - 1, level)
      if #list > 0 then R2F.Print(L.TRAIN_LEVELUP:format(level, names(list, 6))) end
      local np = R2F.Talents.NextPointLine()
      if np then R2F.Print(L.HOME_NEXT_TALENT .. ": " .. np) end
    end,
  },
})
