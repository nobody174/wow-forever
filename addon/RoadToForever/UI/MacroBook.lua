-- UI/MacroBook.lua: the spellbook-style Macro Book (ADDON_PLAN.md 5.1 - 5.5, 5.7).
--
-- Layout: 2 columns x 6 rows of macro entries per page, side tabs on the
-- right edge (Universal, then the browsed class's sections), bottom bar with
-- slot counters, paging and the Import / Tidy up / Settings buttons.
--
-- Class picker (v0.10.0, ADDON_PLAN 5.10, asked for after the first real
-- in-game test): when the library holds macros for a class other than the
-- player's, a row of class icons at the top lets the player browse any of
-- them (your class pinned first). Browsing another class shows Universal +
-- that class's tabs READ-ONLY: icons, names, tooltips, Shift-click to chat
-- and the right-click menu work, but drag/click never makes a real macro,
-- because a Warrior can't cast a Paladin's spells and the macro would only
-- waste a slot and fail on the bar (Macros.UsableHere is the real gate).
-- The slot counters and gold "on your bars" checks always describe the
-- character you're PLAYING, whatever class is browsed: they're live game
-- state, and blanking them would hide real information.
--
-- Since step 6 the book is the Macros tab of the main window (12.4,
-- UI/MainWindow.lua). It was REPARENTED, not rebuilt: MainWindow calls
-- MacroBook.Build(page) with the tab's page frame and the book draws the same
-- slots, side tabs and bottom bar into it, at the same offsets (the page fills
-- the main window, which has the book's old size). Everything else stays
-- here, so the public functions (Show, Toggle, IsShown, Refresh,
-- RequestRefresh, SetCombat, ShowSection) keep their meaning for Core.lua,
-- ImportFrame.lua, Settings.lua and the tests: "shown" now means "the main
-- window is open on the Macros tab", and Show / Toggle go through MainWindow.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI
local Library, Macros = R2F.Library, R2F.Macros

local MacroBook = {}
R2F.MacroBook = MacroBook

local PER_PAGE, COLS = 12, 2
local ICONS = "Interface\\Icons\\"
local CLASS_CIRCLES = "Interface\\TargetingFrame\\UI-Classes-Circles"

-- Tab icons (5.2). Spec sections use the classic talent-tree icons.
local SECTION_ICONS = {
  Universal = "INV_Misc_Book_09",
  Tank = "INV_Shield_06",
  Healer = "Spell_Holy_HolyBolt",
  Shadow = "Spell_Shadow_ShadowWordPain", Holy = "Spell_Holy_HolyBolt",
  Discipline = "Spell_Holy_WordFortitude",
  Affliction = "Spell_Shadow_DeathCoil", Demonology = "Spell_Shadow_Metamorphosis",
  Destruction = "Spell_Shadow_RainOfFire",
  Arcane = "Spell_Holy_MagicalSentry", Fire = "Spell_Fire_FireBolt02",
  Frost = "Spell_Frost_FrostBolt02",
  Assassination = "Ability_Rogue_Eviscerate", Combat = "Ability_BackStab",
  Subtlety = "Ability_Stealth",
  Elemental = "Spell_Nature_Lightning", Enhancement = "Spell_Nature_LightningShield",
  Restoration = "Spell_Nature_MagicImmunity",
  ["Beast Mastery"] = "Ability_Hunter_BeastTaming", Marksmanship = "Ability_Marksmanship",
  Survival = "Ability_Hunter_SwiftStrike",
}
local MELEE = { WARRIOR = true, ROGUE = true, PALADIN = true }

-- Class picker order after your own class: the site's roster order (armor
-- type, cloth -> plate, CLAUDE.md), Druid with the leather classes. Any
-- token not listed (none today: imports only accept known classes) follows
-- alphabetically.
local CLASS_ORDER = { "PRIEST", "WARLOCK", "MAGE", "ROGUE", "DRUID", "SHAMAN", "HUNTER", "PALADIN", "WARRIOR" }
local PICK_SIZE, PICK_STEP = 24, 30

local book, slots, tabs = nil, {}, {}   -- book = the Macros tab's page frame
local ui = {}            -- bottom-bar widgets
local picks = {}         -- class picker buttons
-- browse = the class being looked at, nil = your own. Kept in this Lua
-- table only, NOT in SavedVariables (ADDON_PLAN 5.10): closing and reopening
-- the window (or switching tabs) keeps it, but a relog or /reload starts
-- every session on your own class, the one class you can actually use.
-- Saving it in R2FCharDB would only store a value that every login must
-- ignore.
local state = { key = nil, page = 1, tabs = {}, browse = nil }
local menu               -- right-click menu

local function escape(s) return (s:gsub("|", "||")) end

local function className(token)
  local names = LOCALIZED_CLASS_NAMES_MALE
  return (names and names[token]) or (token:sub(1, 1) .. token:sub(2):lower())
end

local function classCoords(token)
  return CLASS_ICON_TCOORDS and CLASS_ICON_TCOORDS[token]
end

-- "Damage / offensive" -> "Damage": the short subtext under each name (5.3).
local function groupLabel(group)
  return (group:match("^(.-)%s*/") or group)
end

local function tabKey(sec) return sec.class .. "\0" .. sec.section end

-- ---------------------------------------------------------------------------
-- Building
-- ---------------------------------------------------------------------------

local function showTooltip(btn)
  local e = btn.entry
  if not e then return end
  GameTooltip:SetOwner(btn, "ANCHOR_RIGHT")
  GameTooltip:AddLine(escape(e.name), 1, 1, 1)
  GameTooltip:AddLine(escape(e.short), 1, 0.82, 0)
  for line in e.body:gmatch("[^\n]+") do
    GameTooltip:AddLine(escape(line), 0.6, 0.6, 0.6)
  end
  if e.note then GameTooltip:AddLine(escape(e.note), 0.5, 0.75, 1, true) end
  if btn.onBars then GameTooltip:AddLine(L.TIP_ON_BARS, 1, 0.82, 0) end
  -- Changed marker (5.3): say what changed, then clear it. Hovering is the
  -- moment the player has seen it; clearing at import time instead would
  -- mean the arrow is never seen at all, and keeping it until some other
  -- action would leave arrows nobody knows how to get rid of.
  local changed = Library.Changed(e.id)
  if changed == "edited" then
    GameTooltip:AddLine(L.TIP_CHANGED_EDITED, 1, 0.5, 0.25, true)
  elseif changed then
    GameTooltip:AddLine(L.TIP_CHANGED, 0.1, 1, 0.1)
  end
  if changed then
    Library.SetChanged(e.id, nil)
    btn.arrow:Hide()
  end
  if btn.readOnly then
    -- Red like Blizzard's "requires" lines: says why it can't be dragged,
    -- then what CAN be done with it here.
    GameTooltip:AddLine(L.OTHER_CLASS_USE:format(className(e.class)), 1, 0.1, 0.1, true)
    GameTooltip:AddLine(L.TIP_SHARE, 0.1, 1, 0.1)
  else
    GameTooltip:AddLine(L.TIP_DRAG, 0.1, 1, 0.1)
  end
  GameTooltip:Show()
end

local function shareInChat(e)
  -- Chat is one line: join the macro's lines with " ; " so it stays readable.
  local text = escape(e.body:gsub("\n", " ; "))
  if ChatEdit_InsertLink and ChatEdit_InsertLink(text) then return end
  if ChatFrame_OpenChat then ChatFrame_OpenChat(text) end
end

local function buildMenu()
  local m = CreateFrame("Frame", nil, UIParent, (BackdropTemplateMixin and "BackdropTemplate") or nil)
  if m.SetBackdrop then
    m:SetBackdrop({
      bgFile = "Interface\\Tooltips\\UI-Tooltip-Background",
      edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
      tile = true, tileSize = 16, edgeSize = 16,
      insets = { left = 4, right = 4, top = 4, bottom = 4 },
    })
    m:SetBackdropColor(0, 0, 0, 0.9)
  end
  m:SetSize(176, 64)
  m:SetFrameStrata("DIALOG")
  m:EnableMouse(true)
  m:Hide()
  local function item(label, y, fn)
    local b = CreateFrame("Button", nil, m, "UIPanelButtonTemplate")
    b:SetSize(160, 22)
    b:SetPoint("TOP", 0, y)
    b:SetText(label)
    b:SetScript("OnClick", function() local id = m.id; m:Hide(); fn(id) end)
  end
  -- Remove from library (5.3). Since v0.10.0 it asks first (UI.Confirm, the
  -- dialog Tidy up / Remove all use): it used to remove on the spot, and the
  -- entry only comes back by importing it again. Library only, never the
  -- real macro (6.7): a macro made from it may be on a bar right now, and
  -- Tidy up / Remove all still know it (its created record stays).
  -- Allowed for another class's macros too, while browsing them (5.10):
  -- the library is account-wide and this writes SavedVariables only, never
  -- a game macro, so it isn't what "read-only" protects against; and a class
  -- imported by mistake (no character of it) could otherwise never leave.
  item(L.MENU_REMOVE, -8, function(id)
    local e = Library.Get(id)
    if not e then return end
    UI.Confirm(L.REMOVE_CONFIRM:format(e.name, e.short), L.BTN_REMOVE, L.BTN_CANCEL, function()
      -- Re-read at accept time: the popup may have sat open across an import.
      local now = Library.Get(id)
      if not now then return end
      Library.Remove(id)
      R2F.Print(L.REMOVED:format(now.short))
      MacroBook.Refresh()
    end)
  end)
  item(L.MENU_COPY, -34, function(id)
    local e = Library.Get(id)
    if e then UI.ShowCopy(e.body) end
  end)
  -- Close once the mouse has left the menu (and its buttons) for a moment.
  m:SetScript("OnLeave", function(self)
    if not (C_Timer and C_Timer.After) then return end
    C_Timer.After(0.4, function()
      if self:IsShown() and not self:IsMouseOver() then self:Hide() end
    end)
  end)
  return m
end

local function openMenu(btn)
  menu = menu or buildMenu()
  menu.id = btn.entry.id
  menu:ClearAllPoints()
  -- Under the cursor, so the mouse starts inside it.
  local x, y = GetCursorPosition()
  local scale = UIParent:GetEffectiveScale()
  menu:SetPoint("TOPLEFT", UIParent, "BOTTOMLEFT", x / scale - 20, y / scale + 10)
  menu:Show()
end

-- Left-click / drag on a slot. Another class's macro (browsing, 5.10) is
-- refused here with the tooltip's own words, before Macros is even asked;
-- Macros.Ensure refuses it again on its own (the real gate).
local function pickUp(self)
  if not self.entry then return end
  if self.readOnly then
    Macros.OtherClassError(self.entry)
    return
  end
  Macros.Ensure(self.entry.id)
end

local function slotOnClick(self, button)
  if not self.entry then return end
  if button == "RightButton" then
    openMenu(self)
  elseif IsShiftKeyDown() then
    shareInChat(self.entry)
  else
    pickUp(self)
  end
end

local function buildSlot(parent, i)
  local b = CreateFrame("Button", nil, parent)
  b:SetSize(36, 36)
  local col, row = (i - 1) % COLS, math.floor((i - 1) / COLS)
  b:SetPoint("TOPLEFT", parent, "TOPLEFT", 32 + col * 240, -80 - row * 52)

  b.icon = b:CreateTexture(nil, "BORDER")
  b.icon:SetAllPoints()
  local border = b:CreateTexture(nil, "OVERLAY")
  border:SetTexture("Interface\\Buttons\\UI-Quickslot2")
  border:SetSize(64, 64)
  border:SetPoint("CENTER", 0, -1)
  b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  b:SetPushedTexture("Interface\\Buttons\\UI-Quickslot-Depress")

  -- "On your bars" marker (5.3): small gold check, top-right of the icon.
  b.check = b:CreateTexture(nil, "OVERLAY", nil, 2)
  b.check:SetTexture("Interface\\Buttons\\UI-CheckBox-Check")
  b.check:SetSize(18, 18)
  b.check:SetPoint("TOPRIGHT", 7, 7)
  b.check:Hide()

  -- "Changed" marker (5.3): small green up-arrow, top-left of the icon (the
  -- check owns top-right, and both can show at once). Blizzard textures only
  -- (5): the scroll bar's up-arrow exists in every client; its arrow sits in
  -- the middle of a round button, so it's cropped to the arrow and tinted
  -- green. Exact crop/tint is unverified in the client: TESTING.md 8.
  b.arrow = b:CreateTexture(nil, "OVERLAY", nil, 2)
  b.arrow:SetTexture("Interface\\Buttons\\UI-ScrollBar-ScrollUpButton-Up")
  b.arrow:SetTexCoord(0.2, 0.8, 0.2, 0.8)
  b.arrow:SetVertexColor(0.2, 1, 0.2)
  b.arrow:SetSize(16, 16)
  b.arrow:SetPoint("TOPLEFT", -5, 5)
  b.arrow:Hide()

  b.name = b:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  b.name:SetPoint("LEFT", b, "RIGHT", 8, 7)
  b.name:SetWidth(180)
  b.name:SetJustifyH("LEFT")
  b.sub = b:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  b.sub:SetPoint("TOPLEFT", b.name, "BOTTOMLEFT", 0, -3)
  b.sub:SetWidth(180)
  b.sub:SetJustifyH("LEFT")
  b.sub:SetTextColor(0.6, 0.6, 0.6)

  b:RegisterForDrag("LeftButton")
  b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
  -- Dragging picks the macro up exactly like a spellbook spell (5.3).
  b:SetScript("OnDragStart", pickUp)
  b:SetScript("OnClick", slotOnClick)
  b:SetScript("OnEnter", showTooltip)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
  return b
end

local function setTabIcon(tab, sec)
  local icon = SECTION_ICONS[sec.section]
  if not icon and sec.section == "DPS" then
    -- The tab's own class, not the player's: a browsed Paladin's DPS tab is
    -- melee even on a Mage (5.10).
    icon = MELEE[sec.class] and "Ability_DualWield" or "Spell_Fire_FlameBolt"
  end
  local coords = classCoords(sec.class)
  if not icon and (sec.section == "General" or sec.section == "Shared") and coords then
    tab:SetNormalTexture(CLASS_CIRCLES)
    tab:GetNormalTexture():SetTexCoord(unpack(coords))
    return
  end
  -- Unknown section from a newer site: the book icon. Reset the tex coords
  -- in case this tab showed a class circle before.
  tab:SetNormalTexture(ICONS .. (icon or "INV_Misc_Book_09"))
  local tex = tab:GetNormalTexture()
  if tex then tex:SetTexCoord(0, 1, 0, 1) end
end

-- Side tab, built from the spellbook's own skill-line textures rather than
-- SpellBookSkillLineTabTemplate: that template's scripts call Blizzard's
-- spellbook functions, which we must not trigger or replace.
local function buildTab(parent, i)
  local t = CreateFrame("CheckButton", nil, parent)
  t:SetSize(32, 32)
  t:SetPoint("TOPLEFT", parent, "TOPRIGHT", 0, -48 - (i - 1) * 49)
  local bg = t:CreateTexture(nil, "BACKGROUND")
  bg:SetTexture("Interface\\SpellBook\\SpellBook-SkillLineTab")
  bg:SetSize(64, 64)
  bg:SetPoint("TOPLEFT", -3, 11)
  t:SetNormalTexture(ICONS .. "INV_Misc_Book_09")
  t:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  t:SetCheckedTexture("Interface\\Buttons\\CheckButtonHilight", "ADD")
  t:SetScript("OnClick", function(self)
    if self.sec then
      state.key, state.page = tabKey(self.sec), 1
      UI.PlaySound("IG_ABILITY_PAGE_TURN")
    end
    MacroBook.Refresh()
  end)
  t:SetScript("OnEnter", function(self)
    if not self.sec then return end
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:AddLine(self.sec.section, 1, 1, 1)
    local n = #self.sec.entries
    GameTooltip:AddLine(n == 1 and L.TAB_TOOLTIP_COUNT_ONE or L.TAB_TOOLTIP_COUNT:format(n), 1, 0.82, 0)
    GameTooltip:Show()
  end)
  t:SetScript("OnLeave", function() GameTooltip:Hide() end)
  return t
end

local function pageButton(parent, kind)
  local b = CreateFrame("Button", nil, parent)
  b:SetSize(32, 32)
  local base = "Interface\\Buttons\\UI-SpellbookIcon-" .. kind .. "Page-"
  b:SetNormalTexture(base .. "Up")
  b:SetPushedTexture(base .. "Down")
  b:SetDisabledTexture(base .. "Disabled")
  b:SetHighlightTexture("Interface\\Buttons\\UI-Common-MouseHilight", "ADD")
  return b
end

-- Class picker button (5.10): the class circle from the same
-- UI-Classes-Circles texture the General/Shared tabs use, with the side
-- tabs' highlight/checked textures, so it reads as part of the book. A
-- token without CLASS_ICON_TCOORDS (a client that lacks one) gets the
-- question-mark icon instead of a wrong slice of the sheet.
-- Not built from a dropdown template: UIDropDownMenu is the taint source
-- 6.7 already rules out, and nine icons fit in one row.
local function buildPick(parent, i)
  local p = CreateFrame("CheckButton", nil, parent)
  p:SetSize(PICK_SIZE, PICK_SIZE)
  -- A small extra gap after the first button: your own class is pinned
  -- there, apart from the classes you can only preview.
  local x = 70 + (i - 1) * PICK_STEP + (i > 1 and 8 or 0)
  p:SetPoint("TOPLEFT", parent, "TOPLEFT", x, -46)
  p:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  p:SetCheckedTexture("Interface\\Buttons\\CheckButtonHilight", "ADD")
  p:SetScript("OnClick", function(self)
    if self.cls then
      UI.PlaySound("IG_ABILITY_PAGE_TURN")
      MacroBook.Browse(self.cls)
    else
      MacroBook.Refresh()
    end
  end)
  p:SetScript("OnEnter", function(self)
    if not self.cls then return end
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:AddLine(className(self.cls), 1, 1, 1)
    local n = self.count or 0
    GameTooltip:AddLine(n == 1 and L.TAB_TOOLTIP_COUNT_ONE or L.TAB_TOOLTIP_COUNT:format(n), 1, 0.82, 0)
    if self.cls == R2F.playerClass then
      GameTooltip:AddLine(L.PICKER_TIP_YOURS, 0.1, 1, 0.1)
    else
      GameTooltip:AddLine(L.PICKER_TIP_OTHER:format(className(self.cls)), 1, 0.1, 0.1, true)
    end
    GameTooltip:Show()
  end)
  p:SetScript("OnLeave", function() GameTooltip:Hide() end)
  return p
end

local function setPickIcon(p, token)
  local coords = classCoords(token)
  if coords then
    p:SetNormalTexture(CLASS_CIRCLES)
    p:GetNormalTexture():SetTexCoord(unpack(coords))
  else
    p:SetNormalTexture(ICONS .. "INV_Misc_QuestionMark")
    local tex = p:GetNormalTexture()
    if tex then tex:SetTexCoord(0, 1, 0, 1) end
  end
end

-- Tidy up's tooltip (v0.10.0): the button name alone didn't say what it
-- deletes. It also points at Remove from library, so the two "remove"
-- actions can't be mixed up: Tidy up deletes real game macros and never
-- touches the library; Remove from library is the opposite.
local function showTidyTip(self)
  GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
  GameTooltip:AddLine(L.BTN_TIDY, 1, 1, 1)
  GameTooltip:AddLine(L.TIDY_TIP, 1, 0.82, 0, true)
  GameTooltip:AddLine(L.TIDY_TIP_LIBRARY, 0.6, 0.6, 0.6, true)
  if R2F.InCombat() then GameTooltip:AddLine(L.TIDY_TIP_COMBAT, 1, 0.1, 0.1, true) end
  GameTooltip:Show()
end

local function onTidy()
  local cands = Macros.TidyCandidates()
  if #cands == 0 then R2F.Print(L.TIDY_NONE); return end
  local names = {}
  for i, c in ipairs(cands) do names[i] = c.name end
  local text = #cands == 1 and L.TIDY_TEXT_ONE:format(names[1])
    or L.TIDY_TEXT:format(#cands, UI.NameList(names))
  -- Tidy up button is greyed out in combat (refreshBottom); a popup opened
  -- before the pull and accepted in combat is queued, not refused, because
  -- the player already said yes and nothing lands on the cursor later.
  -- Macros.Tidy re-checks "unedited and not on a bar" when it runs.
  UI.Confirm(text, L.BTN_DELETE, L.BTN_CANCEL, function()
    Macros.RunOrQueue(function()
      local n = Macros.Tidy(cands)
      R2F.Print(L.TIDY_DONE:format(n))
      MacroBook.Refresh()
    end)
  end)
end

-- Draws the book into `f`, the main window's Macros page (a frame filling
-- the 540 x 500 main window, so the offsets below are the same as when the
-- book was its own window). The window frame, title, portrait, Esc and
-- open/close sounds belong to MainWindow now; the portrait is the logo
-- (12.4), not the class icon of 5.1, since the window is shared by every tab.
local function build(f)
  for i = 1, PER_PAGE do slots[i] = buildSlot(f, i) end

  local empty = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  empty:SetPoint("TOP", 0, -150)
  empty:SetWidth(400)
  ui.empty = empty

  -- Class picker label (5.10), right of the picker row: which class the
  -- grid shows, and whether it's yours or a preview. The buttons are built
  -- on demand in Refresh (only classes with macros get one).
  ui.pickLabel = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  ui.pickLabel:SetJustifyH("LEFT")
  ui.pickLabel:Hide()

  -- 5.7: other classes' macros, shown on the Universal tab. Since 5.10 also
  -- the "previewing another class" note, on every tab of that class.
  local other = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  other:SetPoint("BOTTOMLEFT", 24, 76)
  other:SetWidth(490)
  other:SetJustifyH("LEFT")
  ui.other = other

  ui.char = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  ui.char:SetPoint("BOTTOMLEFT", 24, 52)
  ui.acc = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  ui.acc:SetPoint("LEFT", ui.char, "RIGHT", 20, 0)
  ui.combat = f:CreateFontString(nil, "ARTWORK", "GameFontRed")
  ui.combat:SetPoint("LEFT", ui.acc, "RIGHT", 20, 0)
  ui.combat:SetText(L.IN_COMBAT)

  ui.next = pageButton(f, "Next")
  ui.next:SetPoint("BOTTOMRIGHT", -16, 42)
  ui.prev = pageButton(f, "Prev")
  ui.prev:SetPoint("RIGHT", ui.next, "LEFT", -2, 0)
  ui.page = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  ui.page:SetPoint("RIGHT", ui.prev, "LEFT", -6, 0)
  ui.prev:SetScript("OnClick", function()
    state.page = state.page - 1
    UI.PlaySound("IG_ABILITY_PAGE_TURN")
    MacroBook.Refresh()
  end)
  ui.next:SetScript("OnClick", function()
    state.page = state.page + 1
    UI.PlaySound("IG_ABILITY_PAGE_TURN")
    MacroBook.Refresh()
  end)

  local function button(label, w)
    local b = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
    b:SetSize(w, 22)
    b:SetText(label)
    return b
  end
  ui.import = button(L.BTN_IMPORT, 100)
  ui.import:SetPoint("BOTTOMLEFT", 20, 16)
  ui.import:SetScript("OnClick", function() R2F.ImportFrame.Show() end)
  ui.tidy = button(L.BTN_TIDY, 100)
  ui.tidy:SetPoint("LEFT", ui.import, "RIGHT", 8, 0)
  ui.tidy:SetScript("OnClick", onTidy)
  -- Tooltip also while greyed out in combat, so it can say why (Home's
  -- Quick settings boxes do the same).
  if ui.tidy.SetMotionScriptsWhileDisabled then ui.tidy:SetMotionScriptsWhileDisabled(true) end
  ui.tidy:SetScript("OnEnter", showTidyTip)
  ui.tidy:SetScript("OnLeave", function() GameTooltip:Hide() end)
  -- Settings panel (5.8, step 5). Stays enabled in combat: the panel greys
  -- out its own Remove all button, and its other settings are safe anytime.
  ui.settings = button(L.BTN_SETTINGS, 100)
  ui.settings:SetPoint("BOTTOMRIGHT", -20, 16)
  ui.settings:SetScript("OnClick", function() R2F.Settings.Toggle() end)
  return f
end

-- Called once by MainWindow with the Macros page frame.
function MacroBook.Build(page)
  book = build(page)
  return book
end

-- MainWindow: the Macros page was hidden (tab switch or window closed).
-- The right-click menu belongs to UIParent, so it has to be closed by hand.
function MacroBook.OnHide()
  if menu then menu:Hide() end
end

-- ---------------------------------------------------------------------------
-- Refresh
-- ---------------------------------------------------------------------------

-- Quick settings (12.4.1) replace three Universal macros (ANY/Zoom,
-- ANY/HideGuild, ANY/HidePvP), so the book doesn't show them: offering a
-- macro that costs a slot for something a Home check box does for free would
-- only confuse. They stay in the library (an import still stores them, and a
-- real macro already made from one is still tracked, updated and tidied);
-- they're only left out of the grid here. The test is QuickSettings'
-- exact-id lookup, which also keeps a macro visible while its box can't work
-- (no CVar / SetCVar in this client). A section left empty gets no tab.
local function visibleEntries(sec)
  local out = {}
  for _, e in ipairs(sec.entries) do
    if not R2F.QuickSettings.HidesMacro(e.id) then out[#out + 1] = e end
  end
  return out
end

-- Tabs: Universal, then the sections of class `cls` (the browsed class, 5.10;
-- your own unless you picked another).
local function collectTabs(browsed)
  local list = {}
  for _, cls in ipairs({ "ANY", browsed }) do
    for _, sec in ipairs(Library.Sections(cls)) do
      sec.entries = visibleEntries(sec)
      if #sec.entries > 0 then list[#list + 1] = sec end
    end
  end
  return list
end

-- The Universal tab's note when the library holds any of the hidden three,
-- so a player who imported them knows where they went.
local function quickSettingsNote()
  for _, item in ipairs(R2F.QuickSettings.ITEMS) do
    if Library.Get(item.macro) and R2F.QuickSettings.HidesMacro(item.macro) then
      return L.BOOK_QUICK_SETTINGS
    end
  end
  return ""
end

local function otherClassesText()
  local counts = Library.OtherClassCounts(R2F.playerClass)
  local parts = {}
  for token, n in pairs(counts) do parts[#parts + 1] = L.OTHER_CLASS_ENTRY:format(className(token), n) end
  if #parts == 0 then return "" end
  table.sort(parts)
  return L.OTHER_CLASSES:format(table.concat(parts, ", "))
end

-- The class the grid shows (5.10). A browsed class whose macros are all gone
-- (removed from the library) falls back to your own, so the book can't be
-- stuck on a class that isn't in the picker any more.
local function browsedClass(counts)
  local own = R2F.playerClass
  if state.browse and state.browse ~= own and (counts[state.browse] or 0) > 0 then
    return state.browse
  end
  state.browse = nil
  return own
end

-- Picker entries: your class first (always, even with no class macros: it's
-- the way back, and its view still has Universal), then every other class
-- that has macros, in roster order. Empty when no other class has macros:
-- a picker with one choice would only take space, and the book then looks
-- exactly as it did before v0.10.0.
local function pickerClasses(counts)
  local own = R2F.playerClass
  local list, seen = {}, {}
  for token in pairs(counts) do
    if token ~= own then seen[token] = true end
  end
  if not next(seen) then return list end
  if own then list[1] = own end
  for _, token in ipairs(CLASS_ORDER) do
    if seen[token] then list[#list + 1] = token; seen[token] = nil end
  end
  local rest = {}
  for token in pairs(seen) do rest[#rest + 1] = token end
  table.sort(rest)
  for _, token in ipairs(rest) do list[#list + 1] = token end
  return list
end

local function refreshPicker(counts, browsed)
  local list = pickerClasses(counts)
  for i, token in ipairs(list) do
    picks[i] = picks[i] or buildPick(book, i)
    local p = picks[i]
    p.cls, p.count = token, counts[token] or 0
    setPickIcon(p, token)
    p:SetChecked(token == browsed)
    p:Show()
  end
  for i = #list + 1, #picks do picks[i]:Hide(); picks[i].cls = nil end
  -- No browsed class = class not read yet (before PLAYER_LOGIN): no label.
  if #list == 0 or not browsed then
    ui.pickLabel:Hide()
    return
  end
  local own = browsed == R2F.playerClass
  ui.pickLabel:ClearAllPoints()
  ui.pickLabel:SetPoint("LEFT", picks[#list], "RIGHT", 10, 0)
  ui.pickLabel:SetText((own and L.PICKER_YOURS or L.PICKER_PREVIEW):format(className(browsed)))
  -- Gold = yours (GameFontNormal's own colour), grey = preview only.
  if own then ui.pickLabel:SetTextColor(1, 0.82, 0) else ui.pickLabel:SetTextColor(0.7, 0.7, 0.7) end
  ui.pickLabel:Show()
end

local function refreshBottom()
  local acc, maxAcc, char, maxChar = Macros.Counts()
  ui.char:SetText(L.SLOTS_CHARACTER:format(char, maxChar))
  ui.acc:SetText(L.SLOTS_ACCOUNT:format(acc, maxAcc))
  -- Red when full (5.5).
  if char >= maxChar then ui.char:SetTextColor(1, 0.1, 0.1) else ui.char:SetTextColor(1, 1, 1) end
  if acc >= maxAcc then ui.acc:SetTextColor(1, 0.1, 0.1) else ui.acc:SetTextColor(1, 1, 1) end
  local combat = R2F.InCombat()
  ui.combat:SetShown(combat)
  ui.import:SetEnabled(not combat)
  ui.tidy:SetEnabled(not combat)
end

-- IsVisible, not IsShown: the page keeps its own "shown" flag while the
-- main window is closed or on another tab, and only IsVisible looks at the
-- parents.
local function bookVisible()
  return book ~= nil and book:IsVisible()
end

function MacroBook.Refresh()
  if not bookVisible() then return end
  local counts = Library.ClassCounts()
  local browsed = browsedClass(counts)
  local preview = browsed ~= R2F.playerClass
  refreshPicker(counts, browsed)
  state.tabs = collectTabs(browsed)

  -- Resolve the selected tab by key, so new imports can't shift it.
  local current
  for i, sec in ipairs(state.tabs) do
    if tabKey(sec) == state.key then current = i end
  end
  if not current and #state.tabs > 0 then
    current = 1
    state.key, state.page = tabKey(state.tabs[1]), 1
  end

  for i, sec in ipairs(state.tabs) do
    tabs[i] = tabs[i] or buildTab(book, i)
    tabs[i].sec = sec
    setTabIcon(tabs[i], sec)
    tabs[i]:SetChecked(i == current)
    tabs[i]:Show()
  end
  for i = #state.tabs + 1, #tabs do tabs[i]:Hide(); tabs[i].sec = nil end

  local sec = current and state.tabs[current]
  local entries = sec and sec.entries or {}
  local pages = math.max(1, math.ceil(#entries / PER_PAGE))
  state.page = math.min(math.max(state.page, 1), pages)

  local onBars = Macros.NamesOnBars()
  local first = (state.page - 1) * PER_PAGE
  for i, b in ipairs(slots) do
    local e = entries[first + i]
    b.entry = e
    if e then
      -- Another class's macro (browsing, 5.10): read-only, shown grey like
      -- an unusable spellbook entry. Its subtext is the group, never
      -- "Learn later": this character will never learn that spell.
      b.readOnly = not Macros.UsableHere(e)
      local tex, learnLater = Macros.DisplayIcon(e)
      if b.readOnly then learnLater = false end
      b.icon:SetTexture(tex)
      b.icon:SetDesaturated(learnLater or b.readOnly)
      b.name:SetText(e.short)
      b.sub:SetText(learnLater and L.LEARN_LATER or groupLabel(e.group))
      -- The gold check is THIS character's action bars even while browsing
      -- (5.10): it's real game state (an account-slot macro made on another
      -- character can sit on this one's bars), so it's never blanked.
      b.onBars = Macros.OnBars(e.id, onBars)
      b.check:SetShown(b.onBars)
      b.arrow:SetShown(Library.Changed(e.id) ~= nil)
      b:Show()
    else
      b.onBars, b.readOnly = false, false
      b.arrow:Hide()
      b:Hide()
    end
  end

  ui.page:SetText(L.PAGE:format(state.page, pages))
  ui.prev:SetEnabled(state.page > 1)
  ui.next:SetEnabled(state.page < pages)

  if Library.Count() == 0 then
    ui.empty:SetText(L.EMPTY_LIBRARY)
  elseif #state.tabs == 0 then
    ui.empty:SetText(L.EMPTY_CLASS)
  else
    ui.empty:SetText("")
  end
  local onUniversal = (not sec) or sec.class == "ANY"
  local lines = {}
  -- Previewing another class (5.10): on every tab, say it's read-only and
  -- that the counters / gold checks still describe the character you play.
  if preview then lines[#lines + 1] = L.BROWSE_NOTE:format(className(browsed)) end
  if onUniversal then
    -- 5.7's line only in your own view: while previewing, the picker row
    -- already shows the other classes, and the line would crowd the note.
    if not preview then lines[#lines + 1] = otherClassesText() end
    lines[#lines + 1] = quickSettingsNote()
  end
  local shown = {}
  for _, text in ipairs(lines) do
    if text ~= "" then shown[#shown + 1] = text end
  end
  ui.other:SetText(table.concat(shown, "\n"))

  refreshBottom()
end

-- ACTIONBAR_SLOT_CHANGED fires once per changed slot (a bar swap can fire
-- dozens at once), so markers refresh at most every 0.2 s, and only while open.
local pending = false
function MacroBook.RequestRefresh()
  if not bookVisible() or pending then return end
  if not (C_Timer and C_Timer.After) then MacroBook.Refresh(); return end
  pending = true
  C_Timer.After(0.2, function() pending = false; MacroBook.Refresh() end)
end

function MacroBook.SetCombat()
  if bookVisible() then refreshBottom() end
end

-- Open the main window on the Macros tab.
function MacroBook.Show()
  R2F.MainWindow.Show("macros")
end

-- Close the window if it's showing the book, else open it on the book.
function MacroBook.Toggle()
  R2F.MainWindow.Toggle("macros")
end

function MacroBook.IsShown()
  return bookVisible()
end

-- Open on a given section's tab (after an import, 5.6). Since v0.10.0 a
-- section of another class opens that class's preview (5.10): the import was
-- the player choosing that class on the site, so showing what just arrived
-- is no surprise (the first real-game test expected exactly that). Import
-- prefers a new Universal / own-class section when there is one
-- (Import.Diff's firstNewOwn), so a mixed import still lands on your class.
-- Universal / own class: back to your own view.
function MacroBook.ShowSection(cls, section)
  if cls and section then
    state.browse = (cls ~= "ANY" and cls ~= R2F.playerClass) and cls or nil
    state.key, state.page = cls .. "\0" .. section, 1
  end
  MacroBook.Show()
end

-- Class picker click (5.10): show Universal + that class, on the class's
-- first section (that's what the player asked to see), else Universal.
-- Your own class = nil, the default view.
function MacroBook.Browse(cls)
  state.browse = (cls ~= R2F.playerClass) and cls or nil
  local secs = Library.Sections(cls)
  state.key = secs[1] and tabKey(secs[1]) or nil
  state.page = 1
  MacroBook.Refresh()
end

-- The class the book shows right now (tests, /dump): your own unless browsing.
function MacroBook.BrowsedClass()
  return state.browse or R2F.playerClass
end
