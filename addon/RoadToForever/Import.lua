-- Import.lua: parse + validate + diff the site's import string (ADDON_PLAN.md 7).
--
-- Format, as template.html's importString() writes it:
--   R2F1:<base64( "v=1\n" .. records joined by \30 )>
--   record = id, class, section, group, name, short, icon, body, note joined by \31
-- \30/\31 are the ASCII record/unit separators. They never occur in macro text,
-- so bodies keep real newlines and nothing needs unescaping here. The site
-- also strips them from every field before joining.
-- The R2F1: prefix is the format version: a future R2F2: (e.g. compressed)
-- must be rejected with "update the addon", not misread.

local _, R2F = ...
local L = R2F.L

local Import = {}
R2F.Import = Import

local RS, US = "\30", "\31"
local FIELDS = { "id", "class", "section", "group", "name", "short", "icon", "body", "note" }
local MAX_SHORT, MAX_BODY = 16, 255

-- Split keeping empty fields ("a\31\31b" -> "a", "", "b"); plain find, no patterns.
local function split(s, sep)
  local out, start = {}, 1
  while true do
    local i = s:find(sep, start, true)
    if not i then
      out[#out + 1] = s:sub(start)
      return out
    end
    out[#out + 1] = s:sub(start, i - 1)
    start = i + 1
  end
end
Import.split = split

-- Length in characters, not bytes, to match build.py's len() check and the
-- macro window's letter limit. Counts every byte that isn't a UTF-8
-- continuation byte (0x80-0xBF).
local function utf8len(s)
  local _, n = s:gsub("[^\128-\191]", "")
  return n
end
Import.utf8len = utf8len

-- Validate one split record. Returns a record table or nil.
local function toRecord(fields)
  if #fields ~= #FIELDS then return nil end
  local r = {}
  for i, key in ipairs(FIELDS) do r[key] = fields[i] end
  -- Required fields (icon and note may be empty).
  for _, key in ipairs({ "id", "class", "section", "group", "name", "short", "body" }) do
    if r[key] == "" then return nil end
  end
  if not R2F.Library.KNOWN_CLASSES[r.class] then return nil end
  if utf8len(r.short) > MAX_SHORT then return nil end
  if utf8len(r.body) > MAX_BODY then return nil end
  -- The id is how updates are recognised (3.4), so it must be the site's
  -- "<class>/<short>" exactly; anything else is a damaged record.
  if r.id ~= r.class .. "/" .. r.short then return nil end
  if r.icon == "" then r.icon = nil end
  if r.note == "" then r.note = nil end
  return r
end

-- Parse an import string.
-- Success: { records = {...valid, in string order}, skipped = n }
-- Failure: nil, message (already the player-facing text from Locale.lua)
function Import.Parse(text)
  if type(text) ~= "string" then return nil, L.IMPORT_BAD end
  text = text:gsub("^%s+", ""):gsub("%s+$", "")
  local version, payload = text:match("^R2F(%d+):(.*)$")
  if not version then return nil, L.IMPORT_BAD end
  if version ~= "1" then return nil, L.IMPORT_NEWER end

  local decoded = R2F.Base64.Decode(payload)
  if not decoded then return nil, L.IMPORT_BAD end

  local v, rest = decoded:match("^v=(%d+)\n(.*)$")
  if not v then return nil, L.IMPORT_BAD end
  if v ~= "1" then return nil, L.IMPORT_NEWER end

  local records, skipped, seen = {}, 0, {}
  if rest ~= "" then
    for _, raw in ipairs(split(rest, RS)) do
      local r = toRecord(split(raw, US))
      if r and not seen[r.id] then
        seen[r.id] = true
        records[#records + 1] = r
      else
        -- Invalid, or a duplicate id (the site never sends one; keep the first).
        skipped = skipped + 1
      end
    end
  end
  if #records == 0 then return nil, L.IMPORT_EMPTY end
  return { records = records, skipped = skipped }
end

-- Fields that make an imported macro "updated" when they differ.
local COMPARE = { "class", "section", "group", "name", "short", "icon", "body", "note" }

-- Diff parsed records against the current library (5.6 preview).
-- Returns { total, new, updated, unchanged, otherClass, skipped, firstNew = record,
--           firstNewOwn = first new Universal / own-class record (or nil),
--           status = {id -> "new"/"updated"/"unchanged"},
--           plan = { update = {ids}, edited = {ids} } }
-- `plan` (step 4) = real macros this import will rewrite, and ones the player
-- edited that it will leave alone (Macros.PlanUpdates). Must be computed
-- before Library.Apply, while `library` still holds the old versions.
function Import.Diff(parsed, library, playerClass)
  local d = { total = #parsed.records, new = 0, updated = 0, unchanged = 0,
              otherClass = 0, skipped = parsed.skipped, status = {} }
  d.plan = R2F.Macros.PlanUpdates(parsed.records, library)
  for _, r in ipairs(parsed.records) do
    local old = library[r.id]
    local status
    if not old then
      status = "new"
    else
      status = "unchanged"
      for _, key in ipairs(COMPARE) do
        if old[key] ~= r[key] then status = "updated"; break end
      end
    end
    d[status] = d[status] + 1
    d.status[r.id] = status
    if status == "new" and not d.firstNew then d.firstNew = r end
    if r.class ~= "ANY" and r.class ~= playerClass then
      d.otherClass = d.otherClass + 1
    elseif status == "new" and not d.firstNewOwn then
      -- The first new Universal / own-class record: where the book opens
      -- after the import (v0.10.0, ADDON_PLAN 5.10), ahead of other classes.
      d.firstNewOwn = r
    end
  end
  return d
end

-- The one-line preview text for a diff.
function Import.PreviewText(d)
  local s
  if d.total == 1 then
    s = L.IMPORT_PREVIEW_ONE:format(d.new, d.updated, d.unchanged)
  else
    s = L.IMPORT_PREVIEW:format(d.total, d.new, d.updated, d.unchanged)
  end
  if d.otherClass == 1 then
    s = s .. L.IMPORT_OTHER_CLASS_ONE
  elseif d.otherClass > 1 then
    s = s .. L.IMPORT_OTHER_CLASS:format(d.otherClass)
  end
  if d.skipped == 1 then
    s = s .. L.IMPORT_SKIPPED_ONE
  elseif d.skipped > 1 then
    s = s .. L.IMPORT_SKIPPED:format(d.skipped)
  end
  -- Step 4: what happens to macros already made in the game. A second line,
  -- so the counts line keeps 5.6's exact wording.
  local up, kept = #d.plan.update, #d.plan.edited
  local parts = {}
  if up == 1 then parts[#parts + 1] = L.IMPORT_WILL_UPDATE_ONE
  elseif up > 1 then parts[#parts + 1] = L.IMPORT_WILL_UPDATE:format(up) end
  if kept == 1 then parts[#parts + 1] = L.IMPORT_WILL_KEEP_ONE
  elseif kept > 1 then parts[#parts + 1] = L.IMPORT_WILL_KEEP:format(kept) end
  if #parts > 0 then s = s .. "\n" .. table.concat(parts, " ") end
  return s
end

-- Short names of a list of ids, for chat ("VR, HS").
local function shortNames(ids)
  local names = {}
  for i, id in ipairs(ids) do
    local e = R2F.Library.Get(id)
    names[i] = e and e.short or id
  end
  return table.concat(names, ", ")
end

-- Do the import: write the library, then update the real macros that are
-- ours and unedited (6.4 Update), then report. The order matters: the
-- plan is taken from the OLD library (to see what changed on the site), and
-- the writes read the NEW library entries.
--
-- An edited macro is left exactly as the player has it: they changed it on
-- purpose, and the addon can't know whether their version or the site's is
-- what they want. The library still takes the new version (it always mirrors
-- the latest import), so Replace in the book gets them the site's text.
--
-- No combat check here beyond the macro writes: the Import button is greyed
-- out in combat, and if this ever runs in combat anyway, Macros.UpdateMany
-- queues the EditMacro calls for PLAYER_REGEN_ENABLED instead of skipping them.
-- Returns the diff, plus d.applied ("now"/"queued") and d.imported (count).
function Import.Commit(parsed, playerClass, now)
  local d = Import.Diff(parsed, R2F.Library.db.library, playerClass)
  d.imported = R2F.Library.Apply(parsed.records, now)
  R2F.Print(d.imported == 1 and L.IMPORT_DONE_ONE or L.IMPORT_DONE:format(d.imported))

  local plan = d.plan
  -- Markers first: they depend on the macro being on a bar, which an edit
  -- doesn't change, and a queued update should show its marker right away.
  R2F.Macros.MarkChanged(plan.update, "updated")
  R2F.Macros.MarkChanged(plan.edited, "edited")
  local nUp = #plan.update
  d.applied = R2F.Macros.UpdateMany(plan.update, function(n)
    if n > 0 then R2F.Print(n == 1 and L.UPDATED_DONE_ONE or L.UPDATED_DONE:format(n)) end
    if R2F.MacroBook then R2F.MacroBook.Refresh() end
  end, nUp == 1 and L.UPDATED_QUEUED_ONE or L.UPDATED_QUEUED:format(nUp))
  if #plan.edited == 1 then
    R2F.Print(L.KEPT_EDITED_ONE:format(shortNames(plan.edited)))
  elseif #plan.edited > 1 then
    R2F.Print(L.KEPT_EDITED:format(#plan.edited, shortNames(plan.edited)))
  end
  return d
end
