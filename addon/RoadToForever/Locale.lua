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
  -- Main window (12.4): title per tab, bottom tabs
  TITLE_HOME = "Road to Forever",
  TITLE_MACROS = "Road to Forever: Macros",
  TITLE_TALENTS = "Road to Forever: Talents",
  TAB_HOME = "Home",
  TAB_MACROS = "Macros",
  TAB_TALENTS = "Talents",
  CHAT_PREFIX = "|cffffd100Road to Forever:|r ",

  -- Macro Book (5.3 - 5.5, 5.7)
  SLOTS_CHARACTER = "Character %d / %d",
  SLOTS_ACCOUNT = "Account %d / %d",
  PAGE = "Page %d of %d",
  IN_COMBAT = "In combat",
  BTN_IMPORT = "Import",
  BTN_TIDY = "Tidy up",
  BTN_SETTINGS = "Settings",
  EMPTY_LIBRARY = "Your macro library is empty.\n\nClick Import and paste the import string from the Macros page.",
  EMPTY_CLASS = "No macros for your class or Universal yet.\n\nPick some on the Macros page and import them.",
  OTHER_CLASSES = "You also have macros for %s. Click a class icon at the top to look at them; "
    .. "log in on that character to use them.",
  OTHER_CLASS_ENTRY = "%s (%d)",
  -- Class picker (v0.10.0, ADDON_PLAN 5.10): browse any class in the library
  PICKER_YOURS = "%s (your class)",
  PICKER_PREVIEW = "%s (preview)",
  PICKER_TIP_YOURS = "Your class: drag these to your bars.",
  PICKER_TIP_OTHER = "Preview only. Log in on a %s character to use these macros.",
  OTHER_CLASS_USE = "Log in on a %s character to use this macro.",
  BROWSE_NOTE = "Previewing %s macros: read-only on this character. "
    .. "The slot counts and gold checks below are for the character you're playing.",
  TIP_SHARE = "Shift-click to put it in chat.",
  -- Remove from library (right-click menu, v0.10.0 confirm popup, ADDON_PLAN 5.10)
  REMOVE_CONFIRM = "Remove %s (%s) from your library?\n\nIt disappears from the Macro Book. "
    .. "Any macro you already made from it stays in the game and on your bars; "
    .. "Tidy up or Remove all can delete it later.",
  -- Tidy up button tooltip (v0.10.0): what it does, and how it differs from
  -- Remove from library.
  TIDY_TIP = "Deletes the macros Road to Forever made in your game that aren't on any action bar "
    .. "and that you haven't edited, to give you those macro slots back. "
    .. "Macros on a bar, and macros you edited, are left alone.",
  TIDY_TIP_LIBRARY = "Your library doesn't change: the macros stay in this book and can be dragged out again. "
    .. "To take a macro out of the book itself, right-click it and choose Remove from library.",
  TIDY_TIP_COMBAT = "Can't be used in combat.",
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
  -- Long name lists in popups are cut short (the dialog grows with its text).
  LIST_MORE = "%s and %d more",

  -- Settings panel (5.8, step 5)
  SETTINGS_TITLE = "Settings",
  SETTINGS_SLOTS = "New macros go to:",
  SETTINGS_SLOTS_CHAR = "Character slots first",
  SETTINGS_SLOTS_ACC = "Account slots first",
  SETTINGS_SLOTS_NOTE = "Only for macros made from now on. Macros you already have stay where they are.",
  SETTINGS_MINIMAP_SHOW = "Show minimap button",
  SETTINGS_MINIMAP_LOCK = "Lock minimap button",
  BTN_REMOVE_ALL = "Remove all Road to Forever macros",
  BTN_REMOVE = "Remove",
  BTN_OK = "OK",
  REMOVE_ALL_NONE = "there are no Road to Forever macros in the game to remove.",
  REMOVE_ALL_TEXT = "Delete %d Road to Forever macros from the game, including any on your action bars?\n\n%s",
  REMOVE_ALL_TEXT_ONE = "Delete 1 Road to Forever macro from the game, even if it's on your action bars?\n\n%s",
  REMOVE_ALL_KEEP = "\n\nKept: %s. You edited them, so they stay as your own macros.",
  REMOVE_ALL_KEEP_ONE = "\n\nKept: %s. You edited it, so it stays as your own macro.",
  REMOVE_ALL_ONLY_KEEP = "Nothing to delete: you edited every Road to Forever macro in the game (%s). "
    .. "They stay as your own macros, and Road to Forever stops tracking them.",
  REMOVE_ALL_LIBRARY = "\n\nYour macro library stays, so you can drag them out again later.",
  REMOVE_ALL_DONE = "removed %d Road to Forever macros. Your macro library is unchanged.",
  REMOVE_ALL_DONE_ONE = "removed 1 Road to Forever macro. Your macro library is unchanged.",
  REMOVE_ALL_DONE_KEPT = " Kept %d you edited as your own.",

  -- Home tab (12.4)
  HOME_MACROS = "Macro Book",
  HOME_MACROS_COUNT = "%d macros in your library, %d on your bars",
  HOME_MACROS_COUNT_ONE = "1 macro in your library, %d on your bars",
  HOME_TALENTS = "Talents",
  HOME_NO_TALENT_POINTS = "No free talent points",
  -- 13.12: the client gave no usable free-points answer (not the same as 0).
  HOME_TALENT_POINTS_UNKNOWN = "Free talent points: couldn't read them",
  HOME_IMPORT = "Import macros",
  HOME_IMPORT_HINT = "Pick macros on the Macros page of the Road to Forever site, click Copy import string, "
    .. "then click Import macros and paste it.",

  -- Version/author footer at the bottom of Home (12.4.2). %s/%s = version, author.
  HOME_FOOTER = "Road to Forever v%s \194\183 by %s \194\183 nobody174.github.io/wow-forever",
  HOME_FOOTER_FALLBACK = "Road to Forever \194\183 nobody174.github.io/wow-forever",
  HOME_FOOTER_TIP = "Import macros and talent builds from the Road to Forever site.",

  -- Quick settings on the Home tab (12.4.1): game settings via SetCVar, no macro
  QS_TITLE = "Quick settings",
  QS_NOTE = "These change your game settings directly. No macro or macro slot needed.",
  QS_ZOOM = "Max camera zoom",
  QS_ZOOM_TIP = "Lets you zoom the camera out further (cameraDistanceMaxZoomFactor 4). "
    .. "Untick to go back to the game's default.",
  QS_GUILD = "Hide guild names",
  QS_GUILD_TIP = "Hides guild names under players' names (UnitNamePlayerGuild 0).",
  QS_PVP = "Hide PvP titles",
  QS_PVP_TIP = "Hides PvP rank titles in players' names (UnitNamePlayerPVPTitle 0).",
  QS_TIP_COMBAT = "Can't be changed in combat.",
  QS_COMBAT = "You can't change game settings in combat.",
  QS_UNAVAILABLE = "Your game doesn't have this setting.",
  QS_NO_DEFAULT = "Couldn't read the game's default for this setting, so it was left as it is.",
  QS_NOT_ACCEPTED = "The game didn't accept that setting.",
  BOOK_QUICK_SETTINGS = "Zoom, guild names and PvP titles are Quick settings on the Home tab, so no macro is needed.",

  -- Talent export (13.4 Copy my build, step 8)
  TALENT_COPY_HINT = "Press Ctrl+C, then paste it in your browser or Discord.",
  TALENT_READ_FAILED = "couldn't read your talents yet. Try again in a moment.",

  -- Talents tab: link box, preview, summary (13.2 - 13.4, step 9)
  TALENT_LINK_LABEL = "Talent link",
  TALENT_LINK_PLACEHOLDER = "talents.html#%s/...",
  TALENT_TAB_HINT = "Paste a link from the site's talent calculator (Copy link), then click Preview. "
    .. "Nothing is learned by previewing.",
  BTN_PREVIEW = "Preview",
  BTN_COPY_BUILD = "Copy my build",
  BTN_LEARN = "Learn talents",
  TALENT_READ_FAILED_TAB = "Couldn't read your talents yet. Try again in a moment.",
  TALENT_BAD_LINK = "That isn't a talent link. Click Copy link on the site's talent calculator and paste it here.",
  TALENT_WRONG_CLASS = "This is a %s build. You're playing a %s.",
  TALENT_HASH_MISMATCH = "This link was made with different talent trees than your game has. Nothing was learned. "
    .. "Make a new link on the site or wait for the site to update.",
  TALENT_NO_HASH = "Older link: can't check it against your talent trees.",
  TALENT_HASH_LOCALE = "Your game isn't in English, so this link can't be checked against your talent trees.",
  TALENT_POINTS = "%d points",
  TALENT_POINT_ONE = "1 point",
  TALENT_USES = "This build uses %s.",
  TALENT_USES_HAVE = "This build uses %s, %d of them already learned.",
  TALENT_FREE = "You have %d free.",
  TALENT_FREE_PART = "You have %d free: %d will be learned now, %d later.",
  TALENT_WILL_ALL = "All %d will be learned.",
  TALENT_WILL_ONE = "It will be learned.",
  TALENT_SUMMARY_NO_POINTS = "No free talent points.",
  TALENT_SUMMARY_POINTS_UNKNOWN = "Couldn't read your free talent points, so nothing can be learned from here. "
    .. "Learn them in Blizzard's talent window.",
  TALENT_SUMMARY_DONE = "You already have this whole build.",
  TALENT_SUMMARY_EMPTY = "This link has no talent points in it.",
  TALENT_CONFLICT_UNUSED = "You already have %s in %s, which this build doesn't use. "
    .. "Reset your talents at a trainer first.",
  TALENT_CONFLICT_FEWER = "You have %s in %s, but this build only uses %d. Reset your talents at a trainer first.",
  TALENT_CONFLICT_OVERMAX = "The link puts %s in %s, which has only %d ranks in your game. "
    .. "Make a new link on the site or wait for the site to update.",
  TALENT_CONFLICT_NOSPOT = "The link has points in a talent your %s tree doesn't have. "
    .. "Make a new link on the site or wait for the site to update.",
  TALENT_CONFLICT_NOTREE = "The link has points in a talent tree your class doesn't have. "
    .. "Make a new link on the site or wait for the site to update.",
  TALENT_TREE_N = "Tree %d",
  TALENT_TREE_HEAD = "%d -> %d",
  TALENT_LATER = "later",
  TALENT_TIP_BUILD = "Build: %d / %d",
  TALENT_TIP_NOW = "Learned now: +%d",
  TALENT_TIP_LATER = "Later, when you have free points: +%d",
  TALENT_TIP_CONFLICT = "You have points here that this build doesn't use.",
  TALENT_TIP_OVERMAX = "The link asks for more ranks than this talent has.",

  -- Talent learning (13.4, 13.5, step 10; decisions in ADDON_PLAN 13.8)
  BTN_LEARN_CONFIRM = "Learn",
  BTN_STOP = "Stop",
  TALENT_CONFIRM = "Learn %d talent points? Only a trainer reset can undo this.",
  TALENT_CONFIRM_ONE = "Learn 1 talent point? Only a trainer reset can undo this.",
  TALENT_CONFIRM_GUIDED = "Your game doesn't let addons learn talents, so Blizzard's talent window opens "
    .. "and shows you which talent to click, one at a time.",
  TALENT_LEARN_TIP = "Learns the gold +N points shown in the trees, one at a time. Only a trainer reset can undo it.",
  TALENT_LEARN_COMBAT = "You can't learn talents in combat.",
  TALENT_LEARNING = "Learning %d / %d",
  TALENT_LEARN_WAITING = "After combat",
  TALENT_LEARN_QUEUED = "you're in combat; learning starts when combat ends.",
  TALENT_LEARNED = "Learned %d talent points.",
  TALENT_LEARNED_ONE = "Learned 1 talent point.",
  TALENT_STOP_REJECTED = "Stopped at %s: the game didn't accept the point. %d of %d learned.",
  TALENT_STOP_COMBAT = "Stopped: you entered combat. %d of %d learned. Click Learn talents to continue.",
  TALENT_STOP_USER = "Stopped. %d of %d learned. Click Learn talents to continue.",
  TALENT_STOP_LOCKED = "Stopped at %s: its tier or prerequisite isn't met in your game. %d of %d learned.",
  TALENT_STOP_NOPOINTS = "Stopped: no free talent points left. %d of %d learned.",
  TALENT_STOP_CHANGED = "Stopped: your talents changed while learning. %d of %d learned. "
    .. "Check the preview, then click Learn talents again.",
  TALENT_BLOCKED_HINT = "Your game may not let addons learn talents. "
    .. "Click Learn talents to be shown which talents to click instead.",
  TALENT_LATE = "The point in %s arrived late after all. %d of %d learned. Click Learn talents to continue.",
  -- 13.12 ("traits" learning on WoW Forever)
  TALENT_STOP_STAGED = "Stopped at %s: the point is waiting in Blizzard's talent window but wasn't applied. "
    .. "Click Apply Changes there to keep it, or undo it there. %d of %d learned.",
  TALENT_STOP_PENDING = "Stopped: Blizzard's talent window has changes that aren't applied yet. "
    .. "Apply or undo them there first. %d of %d learned. Click Learn talents to continue.",
  TALENT_GUIDE_CLICK = "Click %s (%d of %d)",
  TALENT_GUIDE_TAB = "Open the %s tab, then click %s (%d of %d)",
  TALENT_GUIDE_START = "click the glowing talent in Blizzard's talent window, one at a time.",
  TALENT_GUIDE_OPEN = "open your talent window (default key N) and click the talents named here, one at a time.",
  TALENT_PREVIEW_FILLED = "added %d talent points to the talent window's preview. Click its Learn button to keep them.",

  -- Minimap button (12.2)
  MM_LIBRARY = "%d macros in your library",
  MM_LIBRARY_ONE = "1 macro in your library",
  MM_TALENT_POINTS = "%d free talent points",
  MM_TALENT_POINTS_ONE = "1 free talent point",
  MM_LEFT = "Left-click to open.",
  MM_RIGHT = "Right-click for options.",
  MM_DRAG = "Drag to move.",
  MENU_OPEN = "Open Road to Forever",
  MENU_MACROS = "Macros",
  MENU_TALENTS = "Talents",
  MENU_LOCK = "Lock button position",
  MENU_HIDE = "Hide minimap button",
  MM_HIDDEN = "minimap button hidden. Type /r2f minimap to show it again.",
  MM_SHOWN = "minimap button shown.",

  -- Slash commands (12.3). /r2f help prints HELP_LINES, one chat line each.
  HELP_LINES = {
    "commands:",
    "/r2f  open Road to Forever (the tab you used last)",
    "/r2f macros  the Macros tab",
    "/r2ft or /r2f talents  the Talents tab",
    "/r2f minimap  show or hide the minimap button",
    "/r2f import  paste an import string",
    "/r2f copybuild  copy your talents as a site link (also a button on the Talents tab)",
    "/r2f help  this list",
  },
  UNKNOWN_COMMAND = "unknown command \"%s\". Type /r2f help for the list.",
}

-- Key Bindings menu labels (Bindings.xml). The client looks these up as
-- globals named BINDING_HEADER_<header> and BINDING_NAME_<binding name>; that
-- naming is fixed by Blizzard, so they can't be R2F-prefixed or live on R2F.
-- They must exist before the Key Bindings window first opens; setting them
-- while the addon loads is the standard way.
_G.BINDING_HEADER_ROADTOFOREVER = "Road to Forever"
_G.BINDING_NAME_R2F_TOGGLE = "Toggle Road to Forever"
_G.BINDING_NAME_R2F_MACROS = "Open Macros"
_G.BINDING_NAME_R2F_TALENTS = "Open Talents"
