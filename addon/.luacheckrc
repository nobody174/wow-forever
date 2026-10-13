-- luacheck config for the Road to Forever addon.
-- `globals` = the only globals the addon may WRITE. Anything else written
-- to _G is a warning. `read_globals` = WoW API the addon reads.
std = "lua51"
max_line_length = 130
exclude_files = { "tests/**" }

globals = {
  "R2F",                    -- the addon's one namespace table
  "R2FDB", "R2FCharDB",     -- SavedVariables (the TOC makes them global)
  "SLASH_R2F1", "SLASH_R2FT1", -- slash command registration (/r2f, /r2ft)
  "SLASH_R2FBIZ1", "SLASH_R2FBIZ2", -- /biz, /mrbiz (Mr.BiZ)
  "SlashCmdList",           -- .R2F field
  "UISpecialFrames",        -- Esc-to-close (append only)
  -- Key Bindings menu labels for Bindings.xml (names fixed by Blizzard)
  "BINDING_HEADER_ROADTOFOREVER", "BINDING_NAME_R2F_TOGGLE", "BINDING_NAME_R2F_MACROS",
  "BINDING_NAME_R2F_TALENTS",
}

read_globals = {
  -- Lua extras WoW provides
  "time", "C_ChatInfo",
  -- Macros
  "GetNumMacros", "GetMacroIndexByName", "GetMacroInfo", "CreateMacro", "EditMacro",
  "DeleteMacro", "PickupMacro", "MAX_ACCOUNT_MACROS", "MAX_CHARACTER_MACROS",
  -- Action bars, spells, items
  "GetActionInfo", "GetActionText", "GetSpellTexture", "GetItemInfo", "C_Spell", "C_Item",
  -- State
  "InCombatLockdown", "UnitClass", "IsShiftKeyDown", "IsAltKeyDown", "GetCursorPosition",
  -- Frames / UI
  "CreateFrame", "UIParent", "GameTooltip", "UIErrorsFrame", "DEFAULT_CHAT_FRAME",
  "BackdropTemplateMixin", "C_XMLUtil", "C_Timer", "ChatFontNormal", "GameFontHighlight",
  "ChatEdit_InsertLink", "ChatFrame_OpenChat",
  "CLASS_ICON_TCOORDS", "LOCALIZED_CLASS_NAMES_MALE",
  "PlaySound", "SOUNDKIT",
  -- Main window tabs, minimap button, menu
  "PanelTemplates_SetTab", "PanelTemplates_SetNumTabs", "PanelTemplates_TabResize",
  "GameFontNormalSmall", "GameFontHighlightSmall",
  "Minimap", "GetMinimapShape", "MenuUtil", "UnitCharacterPoints",
  -- Talent export (read-only), read through C_Traits; GetTalentInfo only confirms a
  -- Classic address before a Classic write.
  "GetTalentInfo", "C_Traits", "C_SpecializationInfo", "GetSpellInfo",
  -- TOC metadata for the Home footer
  "C_AddOns", "GetAddOnMetadata",
  -- Talent import preview (read-only)
  "GetTalentTabInfo", "GetLocale",
  -- Talent learning (the one talent write: LearnTalent), preview-API detection, guided
  -- mode (Blizzard talent window, read only)
  "LearnTalent", "GetTalentPrereqs", "AddPreviewTalentPoints", "LearnPreviewTalents", "GetCVarBool",
  "ToggleTalentFrame", "PanelTemplates_GetSelectedTab",
  -- Quick settings: game settings via CVars. QuickSettings.lua
  -- reads them through _G (falling back to C_CVar), so only C_CVar is named here.
  "C_CVar",
  -- Mr.BiZ: item quality / icon / links, faction for faction-only quest rewards
  "GetItemIcon", "GetItemInfoInstant", "ITEM_QUALITY_COLORS", "UnitFactionGroup", "GameFontDisableSmall",
  -- GearScore: worn items (read), the item tooltip post-call hook (modern clients)
  "GetInventoryItemLink", "TooltipDataProcessor",
  -- What to train next: the class trainer window (read only)
  "GetNumTrainerServices", "GetTrainerServiceInfo", "GetTrainerServiceLevelReq", "GetTrainerServiceCost",
  "IsTradeskillTrainer",
  -- API namespaces
  "C_Container", "C_GossipInfo", "C_Map", "C_PlayerInfo", "C_QuestLog", "C_SpellBook", "C_TradeSkillUI",
  "Enum",
  -- Functions the addon calls (all guarded or read-only; see the files for why)
  "AcceptQuest", "CanMerchantRepair", "CancelDuel", "CharacterFrameTitleText", "CompleteQuest",
  "CraftOnlyShowMakeable", "ExpandCraftSkillLine", "ExpandTradeSkillSubClass", "GetActiveTitle",
  "GetCraftDisplaySkillLine", "GetCraftInfo", "GetCraftItemLink", "GetCraftNumReagents",
  "GetCraftReagentInfo", "GetCraftReagentItemLink", "GetCraftSkillLine", "GetGossipActiveQuests",
  "GetInventoryItemID", "GetMoney", "GetNormalizedRealmName", "GetNumActiveQuests", "GetNumAvailableQuests",
  "GetNumCrafts", "GetNumGossipActiveQuests", "GetNumGossipAvailableQuests", "GetNumGroupMembers",
  "GetNumLootItems", "GetNumQuestChoices", "GetNumSpellTabs", "GetNumTradeSkills", "GetPlayerInfoByGUID",
  "GetQuestItemLink", "GetQuestReward", "GetRealmName", "GetRepairAllCost", "GetShapeshiftForm",
  "GetSpellBookItemName", "GetSpellTabInfo", "GetSubZoneText", "GetTime", "GetTradeSkillInfo",
  "GetTradeSkillItemLink", "GetTradeSkillLine", "GetTradeSkillNumReagents", "GetTradeSkillReagentInfo",
  "GetTradeSkillReagentItemLink", "GetUnitName", "IsInGroup", "IsInInstance", "IsInRaid", "IsModifiedClick",
  "IsMouseButtonDown", "IsPlayerSpell", "IsQuestCompletable", "IsSpellKnown", "IsSpellKnownOrOverridesKnown",
  "LootSlot", "QuestGetAutoAccept", "ReloadUI", "RepairAllItems", "SelectActiveQuest",
  "SelectAvailableQuest", "SelectGossipActiveQuest", "SelectGossipAvailableQuest",
  "SetTradeSkillItemNameFilter", "StaticPopup_Hide", "TradeSkillOnlyShowMakeable", "UnitExists",
  "UnitFullName", "UnitGUID", "UnitIsDeadOrGhost", "UnitLevel", "UnitName", "UnitPVPName", "hooksecurefunc",
  "issecretvalue",
  -- Constants
  "NUM_BAG_SLOTS", "NUM_REAGENTBAG_SLOTS",
}
-- Nothing is vendored in libs\, so there is no
-- third-party code to exclude; LibStub is only read through _G in Minimap.lua.

-- Generated and long-text files: long lines are expected there.
files["**/PlanData.lua"] = { ignore = { "631" } }
files["**/Locale.lua"] = { ignore = { "631" } }
