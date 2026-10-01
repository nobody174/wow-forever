-- luacheck config for the Road to Forever addon (ADDON_PLAN.md 6.6).
-- `globals` = the only globals the addon may WRITE. Anything else written
-- to _G is a warning. `read_globals` = WoW API the addon reads.
std = "lua51"
max_line_length = 130
exclude_files = { "tests/**" }

globals = {
  "R2F",                    -- the addon's one namespace table
  "R2FDB", "R2FCharDB",     -- SavedVariables (the TOC makes them global)
  "SLASH_R2F1",             -- slash command registration
  "SlashCmdList",           -- .R2F field
  "UISpecialFrames",        -- Esc-to-close (append only)
  -- Key Bindings menu labels for Bindings.xml (names fixed by Blizzard, 6.9)
  "BINDING_HEADER_ROADTOFOREVER", "BINDING_NAME_R2F_TOGGLE", "BINDING_NAME_R2F_MACROS",
  "BINDING_NAME_R2F_TALENTS",
}

read_globals = {
  -- Lua extras WoW provides
  "time",
  -- Macros
  "GetNumMacros", "GetMacroIndexByName", "GetMacroInfo", "CreateMacro", "EditMacro",
  "DeleteMacro", "PickupMacro", "MAX_ACCOUNT_MACROS", "MAX_CHARACTER_MACROS",
  -- Action bars, spells, items
  "GetActionInfo", "GetActionText", "GetSpellTexture", "GetItemInfo", "C_Spell", "C_Item",
  -- State
  "InCombatLockdown", "UnitClass", "IsShiftKeyDown", "GetCursorPosition",
  -- Frames / UI
  "CreateFrame", "UIParent", "GameTooltip", "UIErrorsFrame", "DEFAULT_CHAT_FRAME",
  "BackdropTemplateMixin", "C_XMLUtil", "C_Timer", "ChatFontNormal", "GameFontHighlight",
  "ChatEdit_InsertLink", "ChatFrame_OpenChat",
  "CLASS_ICON_TCOORDS", "LOCALIZED_CLASS_NAMES_MALE",
  "PlaySound", "SOUNDKIT",
}
