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
--   Writes that can wait (Tidy up, Remove all, step-4 updates) are queued and run on
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
-- Blizzard_MacroUI, which we must not load (6.6), so they're usually nil here
-- and we fall back to a hardcoded default. On a real WoW Forever client
-- /dump MAX_CHARACTER_MACROS also came back nil (same client quirk as
-- GetBuildInfo()'s 4th return value, ADDON_PLAN.md 6.2/11), so the fallback
-- is load-bearing, not just a last resort — confirmed 2026-10-02 by counting
-- the in-game /macro Character tab directly: 30 slots (5 rows x 6), not the
-- vanilla/Classic Era 18 (3 rows x 6) this addon originally assumed.
function Macros.Limits()
  return MAX_ACCOUNT_MACROS or 120, MAX_CHARACTER_MACROS or 30
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

-- The body the GAME macro gets for a library entry: the same text with spell
-- names raised to a rank the player knows where the unranked name would resolve
-- to an unknown spell (Ranks.lua, ADDON_PLAN 16). Library bodies stay as the site
-- sends them; everything that writes or compares a game macro uses this.
local function wantBody(e)
  return R2F.Ranks.Rewrite(e.body)
end
Macros.WantBody = wantBody

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
-- `icon` = the icon name we passed (step 4). The game reports a macro's icon
-- back as a file id, not the name we gave it, so we can't compare against
-- the live icon; we compare against what we last wrote instead.
local function record(id, name, idx, icon)
  local _, body = live(name)
  local maxAcc = Macros.Limits()
  Library.SetCreated(id, { name = name, hash = Library.Hash(body or ""), account = idx <= maxAcc, icon = icon })
end

-- Read-only check of the real macro for `id` against `want` (a library entry
-- or an import record: needs body, icon). Safe in combat (no writes).
-- Returns one of:
--   "none"      no real macro of ours (no record, or the macro is gone)
--   "unchanged" the real macro already has this body (and icon)
--   "edited"    the player changed it since we wrote it: never touched
--   "needed"    ours, unedited, and different: an EditMacro would update it
-- A live body equal to `want` counts as unchanged even if the player edited
-- it into exactly that text: there is nothing to write either way.
-- Records from v0.1.0 have no icon; they're treated as up to date on the icon
-- (worst case an icon-only change on the site waits for the next body change).
local function classify(id, want)
  local rec = Library.Created(id)
  if not rec or not want then return "none" end
  local idx, body = live(rec.name)
  if idx == 0 then return "none" end
  local iconStale = rec.icon ~= nil and rec.icon ~= createIcon(want)
  if body == wantBody(want) and not iconStale then return "unchanged" end
  if Library.Hash(body) ~= rec.hash then return "edited" end
  return "needed"
end
Macros.Classify = classify

-- The one place that rewrites an existing macro (Replace, Update, Ensure).
-- EditMacro keeps the macro in its current (account or character) slot; the
-- index is looked up again afterwards because the list re-sorts by name.
-- Callers check InCombatLockdown() first. Returns the new index (0 = lost).
local function write(id, idx, name, e)
  local icon = createIcon(e)
  EditMacro(idx, name, icon, wantBody(e))
  local newIdx = GetMacroIndexByName(name) or 0
  if newIdx > 0 then record(id, name, newIdx, icon) end
  return newIdx
end

-- ---------------------------------------------------------------------------
-- Combat queue (6.4, 6.5)
-- ---------------------------------------------------------------------------

local queue = {}

-- Run fn now, or after combat if we're in combat. Returns true if it ran now.
-- `msg` = the chat line saying it was put off (default: the generic one).
function Macros.RunOrQueue(fn, msg)
  if InCombatLockdown() then
    queue[#queue + 1] = fn
    R2F.Print(msg or L.QUEUED)
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

-- Can this character use library entry `e`? Universal macros: always. Class
-- macros: only on a character of that class. Since v0.10.0 the Macro Book
-- can show another class's macros (class picker, ADDON_PLAN 5.10), read-only.
-- The book already refuses drag/click on those, but this is the real gate:
-- Create / Replace / Ensure check it too, so no code path can ever put a
-- Paladin macro into a Warrior's macro list or onto its bars, where every
-- spell in it would fail ("Unknown spell") and it would cost a macro slot.
local function playerClass()
  return R2F.playerClass or select(2, UnitClass("player"))
end

function Macros.UsableHere(e)
  return e ~= nil and (e.class == "ANY" or e.class == playerClass())
end

-- The red refusal for another class's macro (same wording as its tooltip).
function Macros.OtherClassError(e)
  local names = LOCALIZED_CLASS_NAMES_MALE
  local cls = e.class or ""
  local name = (names and names[cls]) or (cls:sub(1, 1) .. cls:sub(2):lower())
  R2F.Error(L.OTHER_CLASS_USE:format(name))
end

-- Which slots a new macro goes to (2, setting slotsFirst). Returns
-- perCharacter (true/false) or nil when both are full.
-- Read at every CreateMacro, so changing the setting (Settings panel, step 5)
-- only steers macros made from then on. Existing macros are NOT moved: WoW
-- has no "move macro to the other tab" call, so moving would mean delete +
-- create, which empties every action button holding the old macro.
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
  if not Macros.UsableHere(e) then Macros.OtherClassError(e); return false end
  local perCharacter = Macros.ChooseSlot()
  if perCharacter == nil then R2F.Error(L.ERR_NO_SLOTS); return false end

  local icon = createIcon(e)
  local ok = pcall(CreateMacro, e.short, icon, wantBody(e), perCharacter)
  local idx = ok and GetMacroIndexByName(e.short) or 0
  if idx > 0 then
    record(id, e.short, idx, icon)
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
        record(id, e.short, i, icon)
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
  if not Macros.UsableHere(e) then Macros.OtherClassError(e); return false end
  local idx = GetMacroIndexByName(e.short) or 0
  if idx == 0 then return Macros.Create(id) end
  idx = write(id, idx, e.short, e)
  if idx == 0 then R2F.Error(L.ERR_CREATE_FAILED); return false end
  -- The player chose the site version: any "Changed" note is answered.
  Library.SetChanged(id, nil)
  PickupMacro(idx)
  return true
end

-- Drag or click on a Macro Book entry (5.3, 6.4).
function Macros.Ensure(id)
  if InCombatLockdown() then R2F.Error(L.ERR_COMBAT); return false end
  local e = Library.Get(id)
  if not e then R2F.Error(L.ERR_MISSING); return false end
  -- Before anything else: not even the Replace popup for another class's
  -- macro (its Replace would overwrite one of YOUR macros with it).
  if not Macros.UsableHere(e) then Macros.OtherClassError(e); return false end

  local idx, body = live(e.short)
  if idx == 0 then return Macros.Create(id) end

  if Macros.IsOursUnedited(id, idx, body) then
    -- Ours but older than the library (an import on another character, or a
    -- login sync that couldn't read the macros yet): bring it up to date
    -- before handing it over, so the book never gives out a stale version.
    if classify(id, e) == "needed" then
      idx = write(id, idx, e.short, e)
      if idx == 0 then R2F.Error(L.ERR_CREATE_FAILED); return false end
    end
    PickupMacro(idx)
    return true
  end
  -- Same name and exactly our text (e.g. saved data lost after a reinstall,
  -- or the player typed it in by hand): nothing to ask, adopt it as ours.
  if body == e.body or body == wantBody(e) then
    record(id, e.short, idx, createIcon(e))
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
-- Everything is re-checked at write time, so a queued update still leaves
-- a macro alone if the player edited it before combat ended.
function Macros.Update(id)
  local e = Library.Get(id)
  local status = classify(id, e)
  if status ~= "needed" then return status end
  if InCombatLockdown() then
    Macros.RunOrQueue(function() Macros.Update(id) end)
    return "queued"
  end
  local rec = Library.Created(id)
  write(id, (live(rec.name)), rec.name, e)
  return "updated"
end

-- ---------------------------------------------------------------------------
-- Updates after an import, and on login (step 4, ADDON_PLAN 6.4 / 6.8)
-- ---------------------------------------------------------------------------

-- Which real macros an import of `records` would update, and which ones the
-- player edited (and so will be left alone). Read-only, called for the
-- preview BEFORE the library is written, so it compares the real macros
-- against the incoming records, and `oldLibrary` tells which records really
-- changed on the site.
-- Returns { update = {ids}, edited = {ids} }.
-- "edited" only lists macros whose site text changed in this import: an
-- edited macro whose site version didn't move is nothing to report, and
-- reporting it on every re-import would be noise.
function Macros.PlanUpdates(records, oldLibrary)
  local plan = { update = {}, edited = {} }
  for _, r in ipairs(records) do
    local status = classify(r.id, r)
    if status == "needed" then
      plan.update[#plan.update + 1] = r.id
    elseif status == "edited" then
      local old = oldLibrary[r.id]
      if old and (old.body ~= r.body or old.icon ~= r.icon) then
        plan.edited[#plan.edited + 1] = r.id
      end
    end
  end
  return plan
end

-- Run Update for every id, as ONE batch: out of combat it writes now; in
-- combat it queues a single job for PLAYER_REGEN_ENABLED (one "after combat"
-- chat line, not one per macro). `done(n)` is called with the number of
-- macros actually rewritten, whenever that happens. `queuedMsg` = chat line
-- if it has to wait for combat to end.
-- Returns "now" or "queued".
function Macros.UpdateMany(ids, done, queuedMsg)
  local function run()
    local n = 0
    for _, id in ipairs(ids) do
      if Macros.Update(id) == "updated" then n = n + 1 end
    end
    if done then done(n) end
  end
  if #ids == 0 then return "now" end
  return Macros.RunOrQueue(run, queuedMsg) and "now" or "queued"
end

-- The player learned a spell (Ranks.OnLearned): raise the ranks in the macros the
-- addon made. classify() compares each live macro with its rank-aware body, so
-- only unedited macros whose body would change are "needed"; edited macros are
-- left alone, and in combat UpdateMany queues the EditMacro calls. Returns the
-- number of macros it set out to update.
function Macros.SyncRanks()
  local ids = {}
  for id in pairs(Library.AllCreated()) do
    if classify(id, Library.Get(id)) == "needed" then ids[#ids + 1] = id end
  end
  table.sort(ids)
  if #ids == 0 then return 0 end
  Macros.UpdateMany(ids, function(n)
    if n > 0 then R2F.Print(n == 1 and L.RANKS_SYNC_DONE_ONE or L.RANKS_SYNC_DONE:format(n)) end
    if R2F.MacroBook then R2F.MacroBook.Refresh() end
  end, L.RANKS_SYNC_QUEUED)
  return #ids
end

-- Should this character get a Changed flag for `id`? Only Universal and the
-- player's own class: the flag is about THIS character's action bars, and
-- another class's macro can't be on them (v0.10.0's class picker shows
-- other classes read-only, but a flag there would mean nothing).
local function visible(id)
  return Macros.UsableHere(Library.Get(id))
end

-- Set the Changed marker (5.3) for each id whose real macro is on a bar.
-- `kind` = "updated" (we rewrote it) or "edited" (site changed, player's
-- edit kept). Macros not on a bar get no marker: nothing visible changed.
function Macros.MarkChanged(ids, kind)
  local onBars = Macros.NamesOnBars()
  for _, id in ipairs(ids) do
    if visible(id) and Macros.OnBars(id, onBars) then Library.SetChanged(id, kind) end
  end
end

-- PLAYER_LOGIN. The library is account-wide but character-slot macros (and
-- their records) are per character, so an import on one character can't
-- reach another character's macros. On login, bring this character's
-- unedited macros up to the library. Also drops Changed flags that could
-- never clear (macro gone from the library, or another class).
-- If the game hasn't loaded the macros yet at this point, every lookup misses
-- and nothing is written (safe); Ensure still updates on the next drag.
function Macros.SyncOnLogin()
  for id in pairs(Library.cdb.changed) do
    if not visible(id) or not Library.Created(id) then Library.SetChanged(id, nil) end
  end
  local ids = {}
  for id in pairs(Library.AllCreated()) do
    if classify(id, Library.Get(id)) == "needed" then ids[#ids + 1] = id end
  end
  table.sort(ids)
  Macros.MarkChanged(ids, "updated")
  Macros.UpdateMany(ids, function(n)
    if n > 0 then R2F.Print(n == 1 and L.SYNC_DONE_ONE or L.SYNC_DONE:format(n)) end
  end)
  return #ids
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
-- Why only unedited AND unused: Tidy up is the routine "give me my slots
-- back" button, pressed without much thought. A macro on a bar is in use
-- (deleting it would empty the button), and an edited one is the player's
-- work, which a cleanup button must never throw away.
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
-- Both Tidy rules are checked again here, not only when the popup was built:
-- a Tidy up confirmed in combat runs later from the queue, and by then the
-- player may have edited a macro or put it on a bar.
function Macros.Tidy(candidates)
  if InCombatLockdown() then R2F.Error(L.ERR_COMBAT); return 0 end
  local onBars = Macros.NamesOnBars()
  local n = 0
  for _, c in ipairs(candidates) do
    local rec = Library.Created(c.id)
    local idx, body = live(c.name)
    if rec and idx > 0 and Library.Hash(body) == rec.hash and not onBars[c.name] then
      DeleteMacro(idx)
      Library.SetCreated(c.id, nil)
      n = n + 1
    end
  end
  return n
end

-- ---------------------------------------------------------------------------
-- Macros made from library entries the site removed (ADDON_PLAN 15.1)
-- ---------------------------------------------------------------------------

-- Read-only. For each id with a real macro of ours: delete = unedited and not
-- on a bar (Tidy up's rule), onBar = unedited but on a bar, edited = changed by
-- the player. The last two are lists of macro names, sorted; delete is
-- { {id=, name=}, ... } sorted by name. Records whose macro is gone are skipped.
function Macros.GonePlan(ids)
  local plan = { delete = {}, onBar = {}, edited = {} }
  local onBars = Macros.NamesOnBars()
  for _, id in ipairs(ids) do
    local rec = Library.Created(id)
    if rec then
      local idx, body = live(rec.name)
      if idx > 0 then
        if Library.Hash(body) ~= rec.hash then
          plan.edited[#plan.edited + 1] = rec.name
        elseif onBars[rec.name] then
          plan.onBar[#plan.onBar + 1] = rec.name
        else
          plan.delete[#plan.delete + 1] = { id = id, name = rec.name }
        end
      end
    end
  end
  table.sort(plan.delete, function(a, b) return a.name < b.name end)
  table.sort(plan.onBar)
  table.sort(plan.edited)
  return plan
end

-- Delete the real macros GonePlan says can go (Macros.Tidy re-checks both
-- rules right before each delete). Records whose macro is already gone are
-- forgotten. Re-reads everything, so it can run from the combat queue.
-- Returns deleted (count), plan (the fresh GonePlan, for the chat lines).
function Macros.RemoveGone(ids)
  local plan = Macros.GonePlan(ids)
  local deleted = 0
  if #plan.delete > 0 then deleted = Macros.Tidy(plan.delete) end
  for _, id in ipairs(ids) do
    local rec = Library.Created(id)
    if rec and (GetMacroIndexByName(rec.name) or 0) == 0 then Library.SetCreated(id, nil) end
  end
  return deleted, plan
end

-- ---------------------------------------------------------------------------
-- Remove all (Settings, 5.8; decisions in ADDON_PLAN 6.9)
-- ---------------------------------------------------------------------------

-- What "Remove all Road to Forever macros" would do right now, read-only.
-- Returns { delete = {{id=, name=}}, keep = {{id=, name=}} }, each sorted by
-- name. `delete` = every real macro we made that is still unedited, ON A BAR
-- OR NOT (that's the difference from Tidy up: this is the deliberate "take
-- all of it out of my game" button). `keep` = ours but edited by the player:
-- 5.8 says Remove all deletes only macros "you haven't edited", so those
-- stay, as the player's own macros (we stop tracking them).
-- Records whose macro is already gone are in neither list.
function Macros.RemoveAllPlan()
  local plan = { delete = {}, keep = {} }
  for id, rec in pairs(Library.AllCreated()) do
    local idx, body = live(rec.name)
    if idx > 0 then
      local list = Library.Hash(body) == rec.hash and plan.delete or plan.keep
      list[#list + 1] = { id = id, name = rec.name }
    end
  end
  local byName = function(a, b) return a.name < b.name end
  table.sort(plan.delete, byName)
  table.sort(plan.keep, byName)
  return plan
end

-- Delete every unedited real macro this addon made (character slots of THIS
-- character + account slots) and forget all tracking: R2FCharDB.created and
-- R2FDB.createdAccount end up empty, so edited macros become plain player
-- macros the addon never touches again. R2FDB.library is NOT touched: the
-- imported macros stay in the book and can be dragged out again.
-- Re-reads everything at run time (it may run from the combat queue).
-- Returns deleted, kept (counts).
-- Other characters' character-slot macros can't be reached from here (the
-- game only exposes the logged-in character's), so their records stay in
-- their own R2FCharDB until Remove all is used on that character.
function Macros.RemoveAll()
  if InCombatLockdown() then R2F.Error(L.ERR_COMBAT); return 0, 0 end
  local plan = Macros.RemoveAllPlan()
  local deleted = 0
  for _, c in ipairs(plan.delete) do
    -- By name each time: every DeleteMacro shifts the other indices.
    local idx = GetMacroIndexByName(c.name) or 0
    if idx > 0 then
      DeleteMacro(idx)
      deleted = deleted + 1
    end
  end
  for id in pairs(Library.AllCreated()) do Library.SetCreated(id, nil) end
  return deleted, #plan.keep
end

-- Is the real macro for `id` ours and on an action bar? (5.3 marker)
function Macros.OnBars(id, namesOnBars)
  local rec = Library.Created(id)
  if not rec or not namesOnBars[rec.name] then return false end
  return (GetMacroIndexByName(rec.name) or 0) > 0
end
