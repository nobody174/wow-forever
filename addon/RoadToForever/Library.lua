-- Library.lua: SavedVariables access, ids, hashes.
--
-- R2FDB (account) holds the macro library: every imported macro of every
-- class, keyed by its stable id "<CLASS>/<short>". No slot limit here;
-- real macros are only made when one is dragged out (Macros.lua).
-- R2FCharDB (per character) records the real macros this addon created in
-- character slots; account-slot ones are in R2FDB.createdAccount. It also
-- holds the per-character "Changed" markers (R2FCharDB.changed).

local _, R2F = ...

local Library = {}
R2F.Library = Library

-- Shared output helpers. Calling AddMessage on Blizzard's frames is a plain
-- method call (no hook, no taint); errors go to UIErrorsFrame in red.
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

-- Section order per class, mirroring data.py. The import string only
-- carries section names, not their order, so the tabs are sorted by
-- this table; unknown sections (added on the site later) follow in the order
-- they were first imported. addon/tests/run_tests.py checks this table against
-- data.py so it can't silently drift.
Library.SECTION_ORDER = {
  ANY     = { "Universal" },
  PRIEST  = { "Shared", "Shadow", "Holy", "Discipline" },
  WARLOCK = { "Shared", "Affliction", "Demonology", "Destruction" },
  MAGE    = { "Shared", "Arcane" },
  ROGUE   = { "Shared", "Assassination", "Subtlety" },
  DRUID   = { "Shared", "Balance", "Feral", "Restoration" },
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
-- what we wrote" from "the player edited it". Lua 5.1 has no bit ops,
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
  -- LibDBIcon's own format. Minimap.lua reads it for our own
  -- button, or hands it to LibDBIcon:Register as-is when another addon has
  -- loaded LibDBIcon. Settings writes hide/lock, so fill each field
  -- separately rather than only when the whole table is missing.
  if type(db.minimap) ~= "table" then db.minimap = {} end
  local mm = db.minimap
  if type(mm.hide) ~= "boolean" then mm.hide = false end
  if type(mm.lock) ~= "boolean" then mm.lock = false end
  if type(mm.minimapPos) ~= "number" then mm.minimapPos = 220 end
  -- Warrior stance indicator (Stance.lua).
  if type(db.stance) ~= "table" then db.stance = {} end
  local st = db.stance
  if type(st.shown) ~= "boolean" then st.shown = true end
  if type(st.lock) ~= "boolean" then st.lock = false end
  if type(st.scale) ~= "number" or st.scale < 0.5 or st.scale > 3 then st.scale = 1 end
  if type(st.x) ~= "number" then st.x = 0 end
  if type(st.y) ~= "number" then st.y = -150 end
  -- Gameplay features (Gameplay.lua): one true / false per feature, all OFF until ticked.
  if type(db.gameplay) ~= "table" then db.gameplay = {} end
  for _, key in ipairs({ "repair", "sellgray", "duels", "errorfilter", "xpbar", "mailalts", "bagslots", "bagsort", "fastloot",
    "questaccept", "questturnin", "rewardvalue", "copychat", "questzone", "reactalert", "reactlock",
    "reactblizz", "gossipshop" }) do
    if type(db.gameplay[key]) ~= "boolean" then db.gameplay[key] = false end
  end
  -- "Arrow follows the plan" (Plan.lua) starts ON: it only acts on your own tick of a plan step.
  if db.gameplay.navfollow == nil then db.gameplay.navfollow = true end
  -- "Arrow to corpse when you die" (Nav.lua) starts ON as well: it only acts when you die.
  if db.gameplay.corpsearrow == nil then db.gameplay.corpsearrow = true end
  -- The 3D arrow (Nav.lua) starts ON; switching it off gives the flat dart.
  if db.gameplay.arrow3d == nil then db.gameplay.arrow3d = true end
  -- Where the floating combat text starts (GameplayExtras.lua): offset from the screen centre, UIParent units.
  if type(db.loadouts) ~= "table" then db.loadouts = {} end
  -- BiZNav arrow position (Nav.lua): offset from the screen centre, UIParent units.
  if type(db.nav) ~= "table" then db.nav = {} end
  if type(db.nav.x) ~= "number" then db.nav.x = 0 end
  if type(db.nav.y) ~= "number" then db.nav.y = 220 end
  if db.nav.size ~= "small" and db.nav.size ~= "medium" and db.nav.size ~= "large" then db.nav.size = "medium" end
  -- Which look the arrow has besides the flat dart (Nav.STYLES keys: dart, arrow, block, needle, gilded, plate, slab);
  -- the flat dart is the arrow3d switch off.
  local looks = { dart = true, arrow = true, block = true, needle = true, gilded = true, plate = true, slab = true }
  if not looks[db.nav.style] then db.nav.style = "arrow" end
  if type(db.fct) ~= "table" then db.fct = {} end
  local fc = db.fct
  if type(fc.x) ~= "number" then fc.x = 0 end
  if type(fc.y) ~= "number" then fc.y = 0 end
  if type(fc.scale) ~= "number" or fc.scale < 0.5 or fc.scale > 3 then fc.scale = 1 end
  if type(fc.lock) ~= "boolean" then fc.lock = false end
  if type(fc.textScale) ~= "number" or fc.textScale < 0.5 or fc.textScale > 2.5 then fc.textScale = 1 end
  if fc.outline ~= "none" and fc.outline ~= "thin" and fc.outline ~= "thick" then fc.outline = "none" end
  -- Tracking reminder (Tracking.lua): any class that has Find Minerals / Herbs / Treasure.
  if type(db.tracking) ~= "table" then db.tracking = {} end
  local tr = db.tracking
  if type(tr.shown) ~= "boolean" then tr.shown = true end
  if type(tr.lock) ~= "boolean" then tr.lock = false end
  if type(tr.scale) ~= "number" or tr.scale < 0.5 or tr.scale > 3 then tr.scale = 1 end
  if type(tr.x) ~= "number" then tr.x = 0 end
  if type(tr.y) ~= "number" then tr.y = -60 end
  for _, kind in ipairs({ "minerals", "herbs", "treasure" }) do
    if type(tr[kind]) ~= "boolean" then tr[kind] = true end
  end
  -- Group buff reminder (Buffs.lua): on, locked (unlock to place it), one switch per buff.
  if type(db.buffs) ~= "table" then db.buffs = {} end
  local bf = db.buffs
  if type(bf.shown) ~= "boolean" then bf.shown = true end
  if type(bf.lock) ~= "boolean" then bf.lock = true end
  if type(bf.scale) ~= "number" or bf.scale < 0.5 or bf.scale > 3 then bf.scale = 1 end
  if type(bf.x) ~= "number" then bf.x = 0 end
  if type(bf.y) ~= "number" then bf.y = 140 end
  for key, default in pairs({ fortitude = true, motw = true, thorns = true, intellect = true, blessing = true,
    spirit = false, shadowprot = false, battleshout = false, trueshot = false,
    strengthearth = false, graceair = false, windfury = false, manaspring = false }) do
    if type(bf[key]) ~= "boolean" then bf[key] = default end
  end
  -- Hunter ammo reminder (Ammo.lua).
  if type(db.ammo) ~= "table" then db.ammo = {} end
  local am = db.ammo
  if type(am.shown) ~= "boolean" then am.shown = true end
  if type(am.lock) ~= "boolean" then am.lock = false end
  if type(am.scale) ~= "number" or am.scale < 0.5 or am.scale > 3 then am.scale = 1 end
  if type(am.x) ~= "number" then am.x = 0 end
  if type(am.y) ~= "number" then am.y = -100 end
  if type(am.threshold) ~= "number" or am.threshold < 50 or am.threshold > 1000 then am.threshold = 200 end
  -- Repair reminder (Repair.lua).
  if type(db.repair) ~= "table" then db.repair = {} end
  local rp = db.repair
  if type(rp.shown) ~= "boolean" then rp.shown = true end
  if type(rp.lock) ~= "boolean" then rp.lock = false end
  if type(rp.scale) ~= "number" or rp.scale < 0.5 or rp.scale > 3 then rp.scale = 1 end
  if type(rp.x) ~= "number" then rp.x = 0 end
  if type(rp.y) ~= "number" then rp.y = -150 end
  if type(rp.threshold) ~= "number" or rp.threshold < 5 or rp.threshold > 90 then rp.threshold = 25 end
  local s = db.settings
  -- Main window size and opacity (top bar sliders).
  if type(s.menuScale) ~= "number" or s.menuScale < 0.5 or s.menuScale > 1.5 then s.menuScale = 1 end
  if type(s.menuAlpha) ~= "number" or s.menuAlpha < 0.3 or s.menuAlpha > 1 then s.menuAlpha = 1 end
  if s.slotsFirst ~= "character" and s.slotsFirst ~= "account" then s.slotsFirst = "character" end
  -- Talents tab: show build levels as if the Talented legacy perk (+5 points) is on. Display only.
  if type(s.talented) ~= "boolean" then s.talented = false end
  -- The bundled macro set (MacroData.lua) that is installed in the library; Bundle.lua compares it.
  if type(s.bundleVersion) ~= "string" then s.bundleVersion = "" end
  -- Alerts & HUD page: which class groups of group buffs are folded open (class token -> true).
  if type(s.hudOpen) ~= "table" then s.hudOpen = {} end
  -- Main window: the tab /r2f reopens. Home on first use.
  -- windowPos (the window's saved spot) is written by UI.Window when moved.
  -- Any tab of the main window (MainWindow.TABS), so a window last left on
  -- Plan / Gameplay / Settings reopens there.
  local TABS = { home = true, macros = true, talents = true, plan = true, bis = true, gameplay = true }
  if not TABS[s.lastTab] then s.lastTab = "home" end   -- includes the retired "settings"
  _G.R2FDB = db

  local cdb = _G.R2FCharDB
  if type(cdb) ~= "table" then cdb = {} end
  if type(cdb.created) ~= "table" then cdb.created = {} end
  if type(cdb.changed) ~= "table" then cdb.changed = {} end
  -- Talents tab: the last link previewed on this character,
  -- put back in the link box. Per character because a link is per class.
  if type(cdb.lastTalentLink) ~= "string" then cdb.lastTalentLink = nil end
  -- Professions: what Professions.lua read from the profession
  -- windows, keyed by profession name. Rebuilt each time a window opens.
  if type(cdb.professions) ~= "table" then cdb.professions = {} end
  -- What the class trainer offers (Training.lua): read each time the trainer window opens.
  if type(cdb.training) ~= "table" then cdb.training = {} end
  if type(cdb.training.spells) ~= "table" then cdb.training.spells = {} end
  -- Movable bags (Bags.lua): per character, because the bag windows
  -- are placed on THIS character's screen layout.
  if type(cdb.bags) ~= "table" then cdb.bags = {} end
  if type(cdb.bags.movable) ~= "boolean" then cdb.bags.movable = false end
  if type(cdb.bags.lock) ~= "boolean" then cdb.bags.lock = false end
  if type(cdb.bags.bags) ~= "table" then cdb.bags.bags = {} end
  if type(cdb.bags.combined) ~= "table" then cdb.bags.combined = nil end
  -- Launch Plan tab (Plan.lua): the chosen group plan and the ticked step ids.
  -- Per character: ticks are about THIS character's progress.
  if type(cdb.plan) ~= "table" then cdb.plan = {} end
  if type(cdb.plan.done) ~= "table" then cdb.plan.done = {} end
  if not (R2F.PlanData and R2F.PlanData.plans[cdb.plan.selected]) then cdb.plan.selected = "hwd" end
  -- Mr.BiZ tab (BiZ.lua): class / spec shown, source filters, the wishlist.
  -- Per character: the wishlist is this character's gear goals.
  if type(cdb.biz) ~= "table" then cdb.biz = {} end
  local bz = cdb.biz
  if type(bz.class) ~= "string" then bz.class = nil end
  if type(bz.spec) ~= "table" then bz.spec = {} end
  if type(bz.types) ~= "table" then bz.types = {} end
  if type(bz.known) ~= "boolean" then bz.known = false end
  if type(bz.wish) ~= "table" then bz.wish = {} end
  for id, w in pairs(bz.wish) do
    if type(id) ~= "number" or type(w) ~= "table" then bz.wish[id] = nil end
  end
  _G.R2FCharDB = cdb

  Library.db, Library.cdb = db, cdb
end

function Library.Get(id)
  return Library.db.library[id]
end

-- Remove from library only. A real macro made from it stays (the player may
-- have it on a bar); Tidy up can delete it later because it's still recorded.
-- A later import of the same id finds no library entry, so it counts as
-- "new" again (Import.Diff compares against the library only).
function Library.Remove(id)
  Library.db.library[id] = nil
  Library.SetChanged(id, nil) -- no slot left to hover, so it could never clear
end

-- "Changed" markers: id -> "updated" (an import rewrote the
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
-- page order, and it remembers the selection, so a re-import is
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

-- Count library macros per class token, Universal (ANY) left out: token -> n.
-- Only classes that really have macros appear (the Macro Book's class
-- picker lists exactly these).
function Library.ClassCounts()
  local counts = {}
  for _, e in pairs(Library.db.library) do
    if e.class ~= "ANY" then
      counts[e.class] = (counts[e.class] or 0) + 1
    end
  end
  return counts
end

-- Count library macros per class other than `cls` and ANY.
function Library.OtherClassCounts(cls)
  local counts = Library.ClassCounts()
  counts[cls or ""] = nil
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
