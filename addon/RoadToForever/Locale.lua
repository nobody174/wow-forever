-- Locale.lua: every player-facing string (ADDON_PLAN.md 5.9). English only.
--
-- This is the first file in the TOC, so it also creates the addon's one and
-- only global, R2F. WoW passes every file of an addon the same private table
-- as its second vararg; we publish that table as R2F (handy for /dump while
-- testing) and every other file reaches it through `...`, never through _G.

local _, R2F = ...
_G.R2F = R2F

R2F.L = {
  ADDON_NAME = "Road to Forever",
  BOOK_TITLE = "Road to Forever",
  CHAT_PREFIX = "|cffffd100Road to Forever:|r ",

  -- Macro Book (5.3 - 5.5, 5.7)
  SLOTS_CHARACTER = "Character %d / %d",
  SLOTS_ACCOUNT = "Account %d / %d",
  PAGE = "Page %d of %d",
  IN_COMBAT = "In combat",
  BTN_IMPORT = "Import",
  BTN_TIDY = "Tidy up",
  BTN_SETTINGS = "Settings",
  SETTINGS_LATER = "Settings come in a later version.",
  EMPTY_LIBRARY = "Your macro library is empty.\n\nClick Import and paste the import string from the Macros page.",
  EMPTY_CLASS = "No macros for your class or Universal yet.\n\nPick some on the Macros page and import them.",
  OTHER_CLASSES = "You also have macros for %s. Log in on that character to use them.",
  OTHER_CLASS_ENTRY = "%s (%d)",
  TAB_TOOLTIP_COUNT_ONE = "1 macro",
  TAB_TOOLTIP_COUNT = "%d macros",
  LEARN_LATER = "Learn later",
  TIP_DRAG = "Drag to an action bar.",
  TIP_ON_BARS = "On your action bars.",
  MENU_REMOVE = "Remove from library",
  MENU_COPY = "Copy text",
  COPY_HINT = "Press Ctrl+C to copy, then Esc.",
  REMOVED = "removed %s from the library.",

  -- Import window (5.6, 7)
  IMPORT_TITLE = "Import macros",
  IMPORT_PLACEHOLDER = "Paste the import string from the Macros page (Ctrl+V).",
  IMPORT_PREVIEW = "%d macros: %d new, %d updated, %d unchanged.",
  IMPORT_PREVIEW_ONE = "1 macro: %d new, %d updated, %d unchanged.",
  IMPORT_OTHER_CLASS = " %d are for another class and will be kept for those characters.",
  IMPORT_OTHER_CLASS_ONE = " 1 is for another class and will be kept for those characters.",
  IMPORT_SKIPPED = " %d could not be read and will be skipped.",
  IMPORT_SKIPPED_ONE = " 1 could not be read and will be skipped.",
  IMPORT_BAD = "That isn't a Road to Forever import string. Copy it again from the Macros page.",
  IMPORT_NEWER = "This import string is from a newer site version. Update the addon.",
  IMPORT_EMPTY = "This import string has no usable macros. Copy it again from the Macros page.",
  IMPORT_DONE = "imported %d macros.",
  IMPORT_DONE_ONE = "imported 1 macro.",
  BTN_CANCEL = "Cancel",

  -- Updates of real macros after an import (step 4, ADDON_PLAN 6.8)
  IMPORT_WILL_UPDATE = "%d macros you already made in the game will be updated too.",
  IMPORT_WILL_UPDATE_ONE = "1 macro you already made in the game will be updated too.",
  IMPORT_WILL_KEEP = "%d you edited yourself will be left as they are.",
  IMPORT_WILL_KEEP_ONE = "1 you edited yourself will be left as it is.",
  UPDATED_DONE = "updated %d of your macros to the new version.",
  UPDATED_DONE_ONE = "updated 1 of your macros to the new version.",
  UPDATED_QUEUED = "you're in combat; %d of your macros will be updated when combat ends.",
  UPDATED_QUEUED_ONE = "you're in combat; 1 of your macros will be updated when combat ends.",
  KEPT_EDITED = "kept your edits to %d macros (%s). To get the new version, drag one from the book and choose Replace.",
  KEPT_EDITED_ONE = "kept your edits to %s. To get the new version, drag it from the book and choose Replace.",
  SYNC_DONE = "updated %d of your macros to the version in your library.",
  SYNC_DONE_ONE = "updated 1 of your macros to the version in your library.",
  TIP_CHANGED = "Updated by your last import.",
  TIP_CHANGED_EDITED = "The site has a new version. You edited this macro, so yours was kept. "
    .. "Drag it and choose Replace to use the new one.",

  -- Errors (5.9), shown red in UIErrorsFrame
  ERR_COMBAT = "You can't create macros in combat.",
  ERR_NO_SLOTS = "No free macro slots. Click Tidy up or delete a macro in /macro.",
  ERR_CREATE_FAILED = "The game didn't create the macro. Try again out of combat.",
  ERR_MISSING = "That macro is no longer in your library.",

  -- Popups (5.9, 6.4)
  REPLACE_TEXT = "You already have a macro called \"%s\". Replace it?",
  BTN_REPLACE = "Replace",
  BTN_KEEP = "Keep mine",
  TIDY_NONE = "Nothing to tidy up: every Road to Forever macro is on an action bar or was edited by you.",
  TIDY_TEXT = "Delete %d Road to Forever macros that are not on any action bar?\n\n%s\n\n"
    .. "Bar addons that don't use the standard action slots aren't seen (rare).",
  TIDY_TEXT_ONE = "Delete 1 Road to Forever macro that is not on any action bar?\n\n%s\n\n"
    .. "Bar addons that don't use the standard action slots aren't seen (rare).",
  BTN_DELETE = "Delete",
  TIDY_DONE = "deleted %d unused macros.",
  QUEUED = "you're in combat; finishing this when combat ends.",

  -- Slash command
  HELP = "type /r2f to open the Macro Book.",
}
