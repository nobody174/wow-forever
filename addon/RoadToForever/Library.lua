-- Library.lua: SavedVariables access, ids, hashes (ADDON_PLAN.md 6.3, 6.5).
--
-- R2FDB (account) holds the macro library: every imported macro of every
-- class, keyed by its stable id "<CLASS>/<short>" (3.4). No slot limit here;
-- real macros are only made when one is dragged out (Macros.lua).
-- R2FCharDB (per character) records the real macros this addon created in
-- character slots; account-slot ones are in R2FDB.createdAccount. It also
-- holds the per-character "Changed" markers (R2FCharDB.changed, step 4).

local _, R2F = ...

local Library = {}
R2F.Library = Library

-- Shared output helpers. Calling AddMessage on Blizzard's frames is a plain
-- method call (no hook, no taint); errors go to UIErrorsFrame in red (5.9).
function R2F.Print(msg)
  if DEFAULT_CHAT_FRAME then DEFAULT_CHAT_FRAME:AddMessage(R2F.L.CHAT_PREFIX .. msg) end
end

-- For the UI's combat state (greyed-out buttons, "In combat"). WoW quirk:
-- InCombatLockdown() still returns false while PLAYER_REGEN_DISABLED is being
-- handled (the lockdown starts right after), so Core.lua also keeps a flag
-- from the events. Real macro writes check InCombatLockdown() itself, which
-- is what the game enforces.
function R2F.InCombat()
  return R2F.inCombat or InCombatLockdown()
end

function R2F.Error(msg)
  if UIErrorsFrame then
    UIErrorsFrame:AddMessage(msg, 1.0, 0.1, 0.1, 1.0)
  else
    R2F.Print(msg)
  end
end

local DB_VERSION = 1

-- Section order per class, mirroring data.py (3.1). The import string only
-- carries section names, not their order, so the tabs (5.2) are sorted by
-- this table; unknown sections (added on the site later) follow in the order
-- they were first imported. addon/tests/run_tests.py checks this table against
-- data.py so it can't silently drift.
Library.SECTION_ORDER = {
  ANY     = { "Universal" },
  PRIEST  = { "Shared", "Shadow", "Holy", "Discipline" },
  WARLOCK = { "Shared", "Affliction", "Demonology", "Destruction" },
  MAGE    = { "Shared", "Arcane", "Fire", "Frost" },
  ROGUE   = { "Shared", "Assassination", "Combat", "Subtlety" },
  SHAMAN  = { "Shared", "Elemental", "Enhancement" },
  HUNTER  = { "Shared", "Beast Mastery", "Marksmanship", "Survival" },
  PALADIN = { "General", "Tank", "DPS", "Healer" },
  WARRIOR = { "General", "Tank", "DPS" },
}

-- Group order inside a section = data.py's ORDER (build.py). Same drift check.
Library.GROUP_ORDER = {
  "Damage / offensive", "Mouseover healing / utility", "Cleanse / dispel",
  "Wand / auto-attack", "Buffs", "Panic / defensive", "Targeting helpers",
  "Class QoL", "Focus", "Misc / UI",
}

-- Every class token UnitClass can return in a Classic client, plus ANY for
-- Universal (7: "class is a known token or ANY").
Library.KNOWN_CLASSES = {
  ANY = true, WARRIOR = true, PALADIN = true, HUNTER = true, ROGUE = true,
  PRIEST = true, SHAMAN = true, MAGE = true, WARLOCK = true, DRUID = true,
}

local GROUP_RANK = {}
for i, g in ipairs(Library.GROUP_ORDER) do GROUP_RANK[g] = i end

-- djb2 over the bytes, as 8 hex digits. Used to tell "the macro is exactly
-- what we wrote" from "the player edited it" (6.4). Lua 5.1 has no bit ops,
-- so the 32-bit wrap is done with % 2^32; h * 33 + 255 stays below 2^53.
function Library.Hash(s)
  local h = 5381
  for i = 1, #s do
    h = (h * 33 + s:byte(i)) % 4294967296
  end
  return string.format("%08x", h)
end

-- ADDON_LOADED (own name): SavedVariables are loaded by now. Create missing
-- tables and migrate older layouts. Never wipe data we don't understand.
function Library.Init()
  local db = _G.R2FDB
  if type(db) ~= "table" then db = {} end
  db.version = db.version or DB_VERSION
  -- Future migrations go here: if db.version < 2 then ... db.version = 2 end
  if type(db.library) ~= "table" then db.library = {} end
  if type(db.settings) ~= "table" then db.settings = {} end
  if type(db.createdAccount) ~= "table" then db.createdAccount = {} end
  if type(db.sectionSeen) ~= "table" then db.sectionSeen = {} end
  if type(db.minimap) ~= "table" then db.minimap = { hide = false, minimapPos = 220, lock = false } end
  local s = db.settings
  if s.slotsFirst ~= "character" and s.slotsFirst ~= "account" then s.slotsFirst = "character" end
  _G.R2FDB = db

  local cdb = _G.R2FCharDB
  if type(cdb) ~= "table" then cdb = {} end
  if type(cdb.created) ~= "table" then cdb.created = {} end
  if type(cdb.changed) ~= "table" then cdb.changed = {} end
  _G.R2FCharDB = cdb

  Library.db, Library.cdb = db, cdb
end

function Library.Get(id)
  return Library.db.library[id]
end

-- Remove from library only. A real macro made from it stays (the player may
-- have it on a bar); Tidy up can delete it later because it's still recorded.
function Library.Remove(id)
  Library.db.library[id] = nil
  Library.SetChanged(id, nil) -- no slot left to hover, so it could never clear
end

-- "Changed" markers (5.3, step 4): id -> "updated" (an import rewrote the
-- real macro on your bars) or "edited" (the site changed it, your edited
-- macro was kept). Per character (R2FCharDB), not account-wide, because the
-- marker is about YOUR action bars, which are per character: an account-wide
-- flag would show on alts that don't have the macro on a bar, and hovering it
-- on one character would hide it on another that never saw the change.
-- A flag is cleared the first time its tooltip is shown (seen = done), when
-- the real macro or the library entry goes away, and on login if it can no
-- longer be shown (Macros.SyncOnLogin), so none can get stuck.
function Library.Changed(id)
  return Library.cdb.changed[id]
end

function Library.SetChanged(id, kind)
  Library.cdb.changed[id] = kind
end

-- Record a section name the first time it's seen for a class, so sections the
-- addon doesn't know yet still get a stable tab order (after the known ones).
local function noteSection(cls, section)
  local seen = Library.db.sectionSeen
  seen[cls] = seen[cls] or {}
  for _, s in ipairs(seen[cls]) do if s == section then return end end
  table.insert(seen[cls], section)
end

local function sectionRank(cls, section)
  local known = Library.SECTION_ORDER[cls] or {}
  for i, s in ipairs(known) do if s == section then return i end end
  local seen = Library.db.sectionSeen[cls] or {}
  for i, s in ipairs(seen) do if s == section then return 100 + i end end
  return 1000
end

-- Store validated import records (from Import.Parse). Returns the number stored.
-- `pos` = the record's place in the import string. The site writes records in
-- page order (4.5), and it remembers the selection (4.4), so a re-import is
-- normally a superset in the same order and re-stamps every pos consistently.
function Library.Apply(records, now)
  local lib = Library.db.library
  for i, r in ipairs(records) do
    lib[r.id] = {
      class = r.class, section = r.section, group = r.group, name = r.name,
      short = r.short, icon = r.icon, body = r.body, note = r.note,
      hash = Library.Hash(r.body), imported = now, pos = i,
    }
    noteSection(r.class, r.section)
  end
  return #records
end

local function entrySort(a, b)
  local ga, gb = GROUP_RANK[a.group] or 99, GROUP_RANK[b.group] or 99
  if ga ~= gb then return ga < gb end
  if (a.pos or 0) ~= (b.pos or 0) then return (a.pos or 0) < (b.pos or 0) end
  return a.id < b.id
end

-- Sections of one class that have macros, in tab order:
-- { { class=, section=, entries = { {id=, ...entry}, ... } }, ... }
function Library.Sections(cls)
  local by = {}
  for id, e in pairs(Library.db.library) do
    if e.class == cls then
      local list = by[e.section]
      if not list then list = {}; by[e.section] = list end
      local view = setmetatable({ id = id }, { __index = e })
      table.insert(list, view)
    end
  end
  local out = {}
  for section, entries in pairs(by) do
    table.sort(entries, entrySort)
    table.insert(out, { class = cls, section = section, entries = entries })
  end
  table.sort(out, function(a, b)
    local ra, rb = sectionRank(cls, a.section), sectionRank(cls, b.section)
    if ra ~= rb then return ra < rb end
    return a.section < b.section
  end)
  return out
end

-- Count library macros per class other than `cls` and ANY (5.7).
function Library.OtherClassCounts(cls)
  local counts = {}
  for _, e in pairs(Library.db.library) do
    if e.class ~= cls and e.class ~= "ANY" then
      counts[e.class] = (counts[e.class] or 0) + 1
    end
  end
  return counts
end

function Library.Count()
  local n = 0
  for _ in pairs(Library.db.library) do n = n + 1 end
  return n
end

-- The record of a real macro this addon created for `id`, character slots
-- first (they win if both exist; the name lookup decides which is live).
function Library.Created(id)
  return Library.cdb.created[id] or Library.db.createdAccount[id]
end

function Library.SetCreated(id, rec)
  if rec and rec.account then
    Library.db.createdAccount[id] = rec
    Library.cdb.created[id] = nil
  elseif rec then
    Library.cdb.created[id] = rec
    Library.db.createdAccount[id] = nil
  else
    Library.cdb.created[id] = nil
    Library.db.createdAccount[id] = nil
    Library.SetChanged(id, nil) -- no real macro, nothing on a bar to mark
  end
end

-- All created records visible to this character: id -> record.
function Library.AllCreated()
  local out = {}
  for id, rec in pairs(Library.db.createdAccount) do out[id] = rec end
  for id, rec in pairs(Library.cdb.created) do out[id] = rec end
  return out
end
