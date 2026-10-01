-- Macros.lua: every call that touches the game's real macros lives here
-- (ADDON_PLAN.md 6.4). Nothing else in the addon calls CreateMacro, EditMacro,
-- DeleteMacro or PickupMacro.
--
-- Rules:
-- * Find a macro by NAME (GetMacroIndexByName), never by a stored index.
--   Macro indices are positions in a sorted list: they shift whenever any
--   macro is created, renamed or deleted, so a saved index goes stale.
-- * "Ours and unedited" = we have a created record for the id AND the live
--   body hashes to the hash we stored when we wrote it. Only those are ever
--   edited or deleted by the addon; a macro the player changed is theirs.
-- * Every write checks InCombatLockdown() first. CreateMacro/EditMacro/
--   DeleteMacro are blocked in combat; calling them anyway would error.
--   Writes that can wait (Tidy up, step-4 updates) are queued and run on
--   PLAYER_REGEN_ENABLED; a drag in combat is refused instead, because
--   putting a macro on the cursor seconds later would surprise the player.

local _, R2F = ...
local L = R2F.L
local Library = R2F.Library

local Macros = {}
R2F.Macros = Macros

local QUESTION = "INV_MISC_QUESTIONMARK"
local ICON_PATH = "Interface\\Icons\\"
-- Highest action slot read by Tidy up / On-your-bars (6.4: slots 1-120).
local NUM_ACTION_SLOTS = 120

-- Slot limits. Blizzard defines MAX_ACCOUNT_MACROS / MAX_CHARACTER_MACROS in
-- Blizzard_MacroUI, which we must not load (6.6), so they're usually nil here.
function Macros.Limits()
  return MAX_ACCOUNT_MACROS or 120, MAX_CHARACTER_MACROS or 18
end

-- Character 7 / 18, Account 31 / 120 (5.5).
function Macros.Counts()
  local acc, char = GetNumMacros()
  local maxAcc, maxChar = Macros.Limits()
  return acc or 0, maxAcc, char or 0, maxChar
end

-- ---------------------------------------------------------------------------
-- Icons (3.3, 5.3)
-- ---------------------------------------------------------------------------

local function trim(s) return (s:gsub("^%s+", ""):gsub("%s+$", "")) end

-- First spell/item a macro shows: the #showtooltip argument, else the first
-- /cast, /use or /castsequence target. Returns nil if the macro has no
-- #showtooltip line (then it has a fixed icon instead).
function Macros.TooltipSpell(body)
  local arg = body:match("^#showtooltip([^\n]*)")
  if not arg then return nil end
  arg = trim(arg)
  if arg == "" then
    for line in body:gmatch("[^\n]+") do
      local seq = line:match("^/castsequence%s+(.*)$")
      if seq then
        arg = seq:gsub("reset=%S*%s*", ""):match("^[^,]*") or ""
        break
      end
      local cmd = line:match("^/cast%s+(.*)$") or line:match("^/use%s+(.*)$")
      if cmd then arg = cmd; break end
    end
  end
  -- Drop [conditions], take the first ;-clause, drop a leading "!".
  for clause in (arg:gsub("%b[]", "") .. ";"):gmatch("([^;]*);") do
    clause = trim(clause):gsub("^!", "")
    if clause ~= "" then return clause end
  end
  return nil
end

local function spellTexture(name)
  local fn = (C_Spell and C_Spell.GetSpellTexture) or GetSpellTexture
  return fn and fn(name) or nil
end

local function itemTexture(name)
  local fn = (C_Item and C_Item.GetItemInfo) or GetItemInfo
  if not fn then return nil end
  return (select(10, fn(name)))
end

-- Icon to show in the Macro Book, and whether it's a spell not learned yet.
-- #showtooltip macros: the spell's own icon (GetSpellTexture only knows
-- spells in your spellbook, so nil = "Learn later"); then the macro's icon
-- field; then the question mark.
function Macros.DisplayIcon(entry)
  local fallback = entry.icon and (ICON_PATH .. entry.icon) or (ICON_PATH .. QUESTION)
  local spell = Macros.TooltipSpell(entry.body)
  if not spell then return fallback, false end
  local tex = spellTexture(spell) or itemTexture(spell)
  if tex then return tex, false end
  -- Only a /cast macro can be "not learned yet"; an uncached item just
  -- shows the fallback.
  return fallback, entry.body:find("\n/cast") ~= nil
end

-- Icon passed to CreateMacro. #showtooltip macros get the question mark,
-- which the game swaps for the live spell icon on the bar (3.3).
local function createIcon(entry)
  if entry.body:match("^#showtooltip") then return QUESTION end
  return entry.icon or QUESTION
end

-- ---------------------------------------------------------------------------
-- Ownership
-- ---------------------------------------------------------------------------

-- Live body of the macro named `name`, and its index (0 if none).
local function live(name)
  local idx = GetMacroIndexByName(name) or 0
  if idx == 0 then return 0 end
  local _, _, body = GetMacroInfo(idx)
  return idx, body or ""
end

-- Is the macro currently called entry.short ours and unedited?
function Macros.IsOursUnedited(id, idx, body)
  local rec = Library.Created(id)
  return rec ~= nil and idx > 0 and Library.Hash(body) == rec.hash
end

-- Record what we wrote. The hash is taken from the body read BACK from the
-- game, not the one we sent, in case the client normalises it on save;
-- otherwise every macro would look "edited" right away.
local function record(id, name, idx)
  local _, body = live(name)
  local maxAcc = Macros.Limits()
  Library.SetCreated(id, { name = name, hash = Library.Hash(body or ""), account = idx <= maxAcc })
end

-- ---------------------------------------------------------------------------
-- Combat queue (6.4, 6.5)
-- ---------------------------------------------------------------------------

local queue = {}

-- Run fn now, or after combat if we're in combat. Returns true if it ran now.
function Macros.RunOrQueue(fn)
  if InCombatLockdown() then
    queue[#queue + 1] = fn
    R2F.Print(L.QUEUED)
    return false
  end
  fn()
  return true
end

-- PLAYER_REGEN_ENABLED. If combat starts again mid-way, the rest waits.
function Macros.RunQueue()
  local q = queue
  queue = {}
  for i, fn in ipairs(q) do
    if InCombatLockdown() then
      for j = i, #q do queue[#queue + 1] = q[j] end
      return
    end
    fn()
  end
end

function Macros.QueueSize() return #queue end

-- ---------------------------------------------------------------------------
-- Ensure / Create / Replace / Update
-- ---------------------------------------------------------------------------

-- Which slots a new macro goes to (2, setting slotsFirst). Returns
-- perCharacter (true/false) or nil when both are full.
function Macros.ChooseSlot()
  local acc, maxAcc, char, maxChar = Macros.Counts()
  local charFree, accFree = char < maxChar, acc < maxAcc
  if Library.db.settings.slotsFirst == "account" then
    if accFree then return false elseif charFree then return true end
  else
    if charFree then return true elseif accFree then return false end
  end
  return nil
end

-- Create the real macro for `id` and put it on the cursor.
function Macros.Create(id)
  if InCombatLockdown() then R2F.Error(L.ERR_COMBAT); return false end
  local e = Library.Get(id)
  if not e then R2F.Error(L.ERR_MISSING); return false end
  local perCharacter = Macros.ChooseSlot()
  if perCharacter == nil then R2F.Error(L.ERR_NO_SLOTS); return false end

  local ok = pcall(CreateMacro, e.short, createIcon(e), e.body, perCharacter)
  local idx = ok and GetMacroIndexByName(e.short) or 0
  if idx > 0 then
    record(id, e.short, idx)
    PickupMacro(idx)
    return true
  end
  -- ADDON_PLAN 11: unconfirmed whether a new macro can be found and picked
  -- up in the same frame it was created. If the lookup misses, try once more
  -- on the next frame (PickupMacro itself isn't combat-protected).
  if ok and C_Timer and C_Timer.After then
    C_Timer.After(0, function()
      if InCombatLockdown() then return end
      local i = GetMacroIndexByName(e.short) or 0
      if i > 0 then
        record(id, e.short, i)
        PickupMacro(i)
      else
        R2F.Error(L.ERR_CREATE_FAILED)
      end
    end)
    return true
  end
  R2F.Error(L.ERR_CREATE_FAILED)
  return false
end

-- Overwrite the existing macro called entry.short with the library version
-- (the "Replace" answer to the name-taken popup) and pick it up.
function Macros.Replace(id)
  if InCombatLockdown() then R2F.Error(L.ERR_COMBAT); return false end
  local e = Library.Get(id)
  if not e then R2F.Error(L.ERR_MISSING); return false end
  local idx = GetMacroIndexByName(e.short) or 0
  if idx == 0 then return Macros.Create(id) end
  -- EditMacro keeps the macro in its current (account or character) slot.
  EditMacro(idx, e.short, createIcon(e), e.body)
  idx = GetMacroIndexByName(e.short) or 0 -- re-sorted after the edit
  if idx == 0 then R2F.Error(L.ERR_CREATE_FAILED); return false end
  record(id, e.short, idx)
  PickupMacro(idx)
  return true
end

-- Drag or click on a Macro Book entry (5.3, 6.4).
function Macros.Ensure(id)
  if InCombatLockdown() then R2F.Error(L.ERR_COMBAT); return false end
  local e = Library.Get(id)
  if not e then R2F.Error(L.ERR_MISSING); return false end

  local idx, body = live(e.short)
  if idx == 0 then return Macros.Create(id) end

  if Macros.IsOursUnedited(id, idx, body) then
    PickupMacro(idx)
    return true
  end
  -- Same name and exactly our text (e.g. saved data lost after a reinstall,
  -- or the player typed it in by hand): nothing to ask, adopt it as ours.
  if body == e.body then
    record(id, e.short, idx)
    PickupMacro(idx)
    return true
  end
  -- A different macro with this name, or ours after the player edited it.
  R2F.UI.Confirm(L.REPLACE_TEXT:format(e.short), L.BTN_REPLACE, L.BTN_KEEP, function()
    Macros.Replace(id)
  end)
  return false
end

-- Bring an existing real macro up to the library version (6.4 Update). Only
-- if it's ours and unedited. Returns "updated", "unchanged", "edited",
-- "none" (no real macro) or "queued" (in combat; runs after combat).
-- Step 4 (re-import updates) wires this into the import; step 3 only ships it.
function Macros.Update(id)
  local e = Library.Get(id)
  local rec = Library.Created(id)
  if not e or not rec then return "none" end
  local idx, body = live(rec.name)
  if idx == 0 then return "none" end
  if not Macros.IsOursUnedited(id, idx, body) then return "edited" end
  if body == e.body then return "unchanged" end
  if InCombatLockdown() then
    Macros.RunOrQueue(function() Macros.Update(id) end)
    return "queued"
  end
  EditMacro(idx, rec.name, createIcon(e), e.body)
  local newIdx = GetMacroIndexByName(rec.name) or 0
  if newIdx > 0 then record(id, rec.name, newIdx) end
  return "updated"
end

-- ---------------------------------------------------------------------------
-- Action bars + Tidy up (6.4)
-- ---------------------------------------------------------------------------

-- Set of macro names on action slots 1-120. GetActionText returns a macro
-- button's name; GetMacroInfo(id) is the fallback in case it's empty.
-- Bar addons that draw their own buttons outside these slots aren't seen.
function Macros.NamesOnBars()
  local set = {}
  for slot = 1, NUM_ACTION_SLOTS do
    local kind, mid = GetActionInfo(slot)
    if kind == "macro" then
      local name = GetActionText and GetActionText(slot)
      if (not name or name == "") and mid then name = GetMacroInfo(mid) end
      if name and name ~= "" then set[name] = true end
    end
  end
  return set
end

-- Ours, unedited, not on any bar. Also forgets records whose macro the
-- player deleted, so they stop counting as ours.
-- Returns { {id=, name=}, ... } sorted by name.
function Macros.TidyCandidates()
  local onBars = Macros.NamesOnBars()
  local out = {}
  for id, rec in pairs(Library.AllCreated()) do
    local idx, body = live(rec.name)
    if idx == 0 then
      Library.SetCreated(id, nil)
    elseif Library.Hash(body) == rec.hash and not onBars[rec.name] then
      out[#out + 1] = { id = id, name = rec.name }
    end
  end
  table.sort(out, function(a, b) return a.name < b.name end)
  return out
end

-- Delete the given candidates. Each one is looked up by name again right
-- before deleting, because every DeleteMacro shifts the indices of the rest.
function Macros.Tidy(candidates)
  if InCombatLockdown() then R2F.Error(L.ERR_COMBAT); return 0 end
  local n = 0
  for _, c in ipairs(candidates) do
    local rec = Library.Created(c.id)
    local idx, body = live(c.name)
    if rec and idx > 0 and Library.Hash(body) == rec.hash then
      DeleteMacro(idx)
      Library.SetCreated(c.id, nil)
      n = n + 1
    end
  end
  return n
end

-- Is the real macro for `id` ours and on an action bar? (5.3 marker)
function Macros.OnBars(id, namesOnBars)
  local rec = Library.Created(id)
  if not rec or not namesOnBars[rec.name] then return false end
  return (GetMacroIndexByName(rec.name) or 0) > 0
end
