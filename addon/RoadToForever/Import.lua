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
-- Returns { total, new, updated, unchanged, otherClass, skipped, firstNew = record }
function Import.Diff(parsed, library, playerClass)
  local d = { total = #parsed.records, new = 0, updated = 0, unchanged = 0,
              otherClass = 0, skipped = parsed.skipped, status = {} }
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
  return s
end
