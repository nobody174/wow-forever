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
    local rank, state, lvl
    if a2 == "available" or a2 == "unavailable" or a2 == "used" then
      rank, state, lvl = a5, a2, tonumber(a4)
    else
      rank, state = a2, a3
      lvl = GetTrainerServiceLevelReq and GetTrainerServiceLevelReq(i)
    end
    if name and state ~= "header" then
      list[#list + 1] = {
        n = name, r = rank or "",
        lvl = lvl or 0,
        cost = GetTrainerServiceCost and GetTrainerServiceCost(i) or 0,
        s = state,
      }
    end
  end
  if #list == 0 then return 0 end
  local d = db()
  -- Merge with what we knew: a later-level spell the trainer no longer lists was hidden by its
  -- "Unavailable" filter, so keep it. One that was trainable and is gone was learned (the trainer
  -- hides learned spells by default), so it goes.
  local seen = {}
  for _, e in ipairs(list) do seen[e.n .. "\0" .. e.r] = true end
  local level = UnitLevel("player")
  for _, old in ipairs(d.spells or {}) do
    if not seen[old.n .. "\0" .. old.r] and old.s == "unavailable" and (old.lvl or 0) > level then
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

local function sortSpells(a, b)
  if a.lvl ~= b.lvl then return a.lvl < b.lvl end
  return a.n < b.n
end

-- now: trainable at `level` (not used); next: the spells of the next level above it that has any;
-- nextLevel; known: whether anything has been read at all.
function Training.Status(level)
  level = level or UnitLevel("player")
  local now, later, nextLevel = {}, {}, nil
  for _, e in ipairs(db().spells) do
    if e.s ~= "used" then
      if e.lvl <= level then
        now[#now + 1] = e
      elseif not nextLevel or e.lvl < nextLevel then
        nextLevel = e.lvl
      end
    end
  end
  if nextLevel then
    for _, e in ipairs(db().spells) do
      if e.s ~= "used" and e.lvl == nextLevel then later[#later + 1] = e end
    end
  end
  table.sort(now, sortSpells)
  table.sort(later, sortSpells)
  return now, later, nextLevel, #db().spells > 0
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
    a = L.TRAIN_NOW_ONE:format(R2F.Gameplay.Money(cost(now)), names(now, 2))
  elseif #now > 1 then
    a = L.TRAIN_NOW:format(#now, R2F.Gameplay.Money(cost(now)), names(now, 2))
  end
  local b = nextLevel and L.TRAIN_NEXT:format(nextLevel, names(later, 2)) or L.TRAIN_NEXT_NONE
  return a, b
end

-- Level-up: what reaching `level` made trainable (entries of levels in (old, level]).
function Training.NewAt(old, level)
  local out = {}
  for _, e in ipairs(db().spells) do
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
  elseif (event == "LEARNED_SPELL_IN_SKILL_LINE" or event == "LEARNED_SPELL_IN_TAB") and a1 then
    local name = GetSpellInfo and GetSpellInfo(a1)
    local rank = _G.GetSpellSubtext and _G.GetSpellSubtext(a1) or nil
    Training.MarkLearned(name, rank)
  end
end)

-- The level-up line (Tweaks > Alerts & HUD > Training reminder).
R2F.Gameplay.Register({
  key = "training", group = "auto", title = "TRAIN_TITLE", tip = "TRAIN_TITLE_TIP",
  events = {
    PLAYER_LEVEL_UP = function(level)
      if not level then return end
      local list = Training.NewAt(level - 1, level)
      if #list > 0 then R2F.Print(L.TRAIN_LEVELUP:format(level, names(list, 6))) end
    end,
  },
})
