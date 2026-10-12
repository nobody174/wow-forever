-- Bundle.lua: installs the macros that ship inside the addon (MacroData.lua) into the library.
--
-- MacroData.lua holds every macro of the site as one import string, so the Macros page is full
-- from the first login and needs no copy and paste. It goes through the same path as a manual
-- import (Import.Parse -> Import.Commit): new macros are added, changed ones are updated (macros
-- already made in the game follow the usual rules for unedited / edited ones), and macros the
-- site dropped leave the library. It runs once per bundled version (R2FDB.bundleVersion), so a
-- new addon release with changed macros updates them once and says so in chat.
-- The Import window stays for custom strings from the site's export tray.

local _, R2F = ...

local Bundle = {}
R2F.Bundle = Bundle

-- True when the bundled macros are not installed yet (or are an older version).
function Bundle.Pending()
  local data = R2F.MacroData
  return data ~= nil and R2F.Library.db.bundleVersion ~= data.version
end

-- Installs the bundle when needed. Returns the import diff, or nil when nothing was done.
function Bundle.Run()
  if not Bundle.Pending() then return nil end
  local data = R2F.MacroData
  local parsed = R2F.Import.Parse(data.string)
  if not parsed then return nil end
  local d = R2F.Import.Commit(parsed, R2F.playerClass, time())
  R2F.Library.db.bundleVersion = data.version
  if R2F.MacroBook and R2F.MacroBook.Refresh then R2F.MacroBook.Refresh() end
  return d
end
