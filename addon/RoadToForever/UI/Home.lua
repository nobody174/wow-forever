-- UI/Home.lua: the Home tab of the main window (ADDON_PLAN.md 12.4).
--
-- Two large entries in spellbook-slot style (big icon in the quick-slot
-- border, gold name, white line under it): Macro Book with live counts, and
-- Talents with the free talent points (12.4). Clicking an entry switches
-- the main window to that tab. Below them: the Import macros button (opens
-- the existing Import window) and one line on how to get an import string.
-- Under that, Quick settings (12.4.1, step "Quick settings", v0.9.0): three
-- check boxes that change game settings with SetCVar (QuickSettings.lua).
-- At the very bottom, a version/author footer (12.4.2, added 2026-10-02 from
-- real in-game feedback: there was no in-game way to see the addon's version
-- or who made it short of opening the TOC file). Reads the TOC's own
-- ## Version / ## Author fields through GetAddOnMetadata so the footer can
-- never drift out of sync with the TOC the way a second hardcoded string
-- would.
--
-- Built into the page frame MainWindow hands it, like MacroBook.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI
local Library, Macros = R2F.Library, R2F.Macros

local Home = {}
R2F.Home = Home

local page
local ui = {}

-- "N macros in your library, M on your bars". N = every imported macro, any
-- class (the library is account-wide). M = real macros this addon made
-- (this character's records + account-slot records) that sit on one of
-- this character's action slots, the same test as the book's gold check.
function Home.Counts()
  local inLibrary = Library.Count()
  local onBars, names = 0, Macros.NamesOnBars()
  for id in pairs(Library.AllCreated()) do
    if Macros.OnBars(id, names) then onBars = onBars + 1 end
  end
  return inLibrary, onBars
end

function Home.MacroLine()
  local n, m = Home.Counts()
  return n == 1 and L.HOME_MACROS_COUNT_ONE:format(m) or L.HOME_MACROS_COUNT:format(n, m)
end

-- 12.4: "5 free talent points", or "No free talent points" (step 9 replaced
-- the step-6 placeholder). Same wording as the minimap tooltip.
-- 13.12: a client that gives no usable answer says so instead of "No free
-- talent points" (which is what hid 17 real points on WoW Forever).
function Home.TalentLine()
  local n = R2F.Talents.FreePointsInfo()
  if n == nil then return L.HOME_TALENT_POINTS_UNKNOWN end
  if n <= 0 then return L.HOME_NO_TALENT_POINTS end
  return n == 1 and L.MM_TALENT_POINTS_ONE or L.MM_TALENT_POINTS:format(n)
end

-- One big entry: a 44 px icon in the quick-slot border (the spellbook's look,
-- 5.3, scaled up), name and sub line to the right. The whole row is the
-- button, with the quest log's row highlight, so the click target is large.
local function entry(parent, y, icon, title, tab)
  local b = CreateFrame("Button", nil, parent)
  b:SetSize(420, 56)
  b:SetPoint("TOPLEFT", 40, y)
  b:SetHighlightTexture("Interface\\QuestFrame\\UI-QuestTitleHighlight", "ADD")
  b.icon = b:CreateTexture(nil, "BORDER")
  b.icon:SetSize(44, 44)
  b.icon:SetPoint("LEFT", 6, 0)
  b.icon:SetTexture("Interface\\Icons\\" .. icon)
  local border = b:CreateTexture(nil, "OVERLAY")
  border:SetTexture("Interface\\Buttons\\UI-Quickslot2")
  border:SetSize(78, 78)
  border:SetPoint("CENTER", b.icon, "CENTER", 0, -1)
  b.name = b:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
  b.name:SetPoint("TOPLEFT", b.icon, "TOPRIGHT", 14, -4)
  b.name:SetText(title)
  b.sub = b:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  b.sub:SetPoint("TOPLEFT", b.name, "BOTTOMLEFT", 0, -6)
  b.sub:SetWidth(340)
  b.sub:SetJustifyH("LEFT")
  b.tab = tab
  b:SetScript("OnClick", function() R2F.MainWindow.SelectTab(tab) end)
  return b
end

-- Quick settings (12.4.1): one check box per QuickSettings item, below the
-- import hint. UI.CheckButton = the same template + fallback chain as the
-- Settings panel (6.9). A click flips the LIVE value and the boxes are then
-- redrawn from the live value (refreshQuick), never from GetChecked, so a
-- refused change (combat, no default, game said no) snaps the box back.
local function showQuickTip(b)
  local item = b.qsItem
  GameTooltip:SetOwner(b, "ANCHOR_RIGHT")
  GameTooltip:AddLine(item.label, 1, 1, 1)
  GameTooltip:AddLine(item.tip, 1, 0.82, 0, true)
  if not R2F.QuickSettings.Available(item) then
    GameTooltip:AddLine(L.QS_UNAVAILABLE, 1, 0.1, 0.1, true)
  elseif R2F.InCombat() then
    GameTooltip:AddLine(L.QS_TIP_COMBAT, 1, 0.1, 0.1, true)
  end
  GameTooltip:Show()
end

local function buildQuickSettings(f)
  ui.qsTitle = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  ui.qsTitle:SetPoint("TOPLEFT", 52, -330)
  ui.qsTitle:SetText(L.QS_TITLE)
  ui.qsNote = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  ui.qsNote:SetPoint("TOPLEFT", ui.qsTitle, "BOTTOMLEFT", 0, -4)
  ui.qsNote:SetWidth(420)
  ui.qsNote:SetJustifyH("LEFT")
  ui.qsNote:SetTextColor(0.7, 0.7, 0.7)
  ui.qsNote:SetText(L.QS_NOTE)

  ui.quick = {}
  for i, item in ipairs(R2F.QuickSettings.ITEMS) do
    local b = UI.CheckButton(f, item.label)
    b:SetPoint("TOPLEFT", 48, -366 - (i - 1) * 26)
    b.qsItem = item
    -- Tooltips still show while the box is greyed out (combat / missing),
    -- so the player can see why.
    if b.SetMotionScriptsWhileDisabled then b:SetMotionScriptsWhileDisabled(true) end
    b:SetScript("OnClick", function(self)
      R2F.QuickSettings.Toggle(self.qsItem)
      Home.Refresh()
    end)
    b:SetScript("OnEnter", showQuickTip)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    ui.quick[i] = b
  end
end

-- Read every box from GetCVar each time the Home tab is drawn (tab opened,
-- combat change, CVAR_UPDATE), so a value set elsewhere (/console, Blizzard's
-- options, another addon) is what the box shows.
local function refreshQuick(combat)
  for _, b in ipairs(ui.quick) do
    local available = R2F.QuickSettings.Available(b.qsItem)
    b:SetChecked(available and R2F.QuickSettings.IsOn(b.qsItem))
    local enabled = available and not combat
    b:SetEnabled(enabled)
    if enabled then b.r2fLabel:SetTextColor(1, 1, 1) else b.r2fLabel:SetTextColor(0.5, 0.5, 0.5) end
  end
end

local function build(f)
  ui.macros = entry(f, -86, "INV_Misc_Book_09", L.HOME_MACROS, "macros")
  ui.talents = entry(f, -156, "INV_Misc_Book_11", L.HOME_TALENTS, "talents")

  ui.import = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  ui.import:SetSize(160, 24)
  ui.import:SetPoint("TOPLEFT", 52, -246)
  ui.import:SetText(L.HOME_IMPORT)
  ui.import:SetScript("OnClick", function() R2F.ImportFrame.Show() end)

  ui.hint = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  ui.hint:SetPoint("TOPLEFT", ui.import, "BOTTOMLEFT", 0, -10)
  ui.hint:SetWidth(420)
  ui.hint:SetJustifyH("LEFT")
  ui.hint:SetTextColor(0.7, 0.7, 0.7)
  ui.hint:SetText(L.HOME_IMPORT_HINT)

  ui.combat = f:CreateFontString(nil, "ARTWORK", "GameFontRed")
  ui.combat:SetPoint("LEFT", ui.import, "RIGHT", 12, 0)
  ui.combat:SetText(L.IN_COMBAT)

  buildQuickSettings(f)
  return f
end

-- Reads the TOC's own ## Version / ## Author so the footer can't drift out of
-- sync with a second hardcoded copy. The metadata API moved from a global
-- function to C_AddOns sometime between Classic eras (same kind of API churn
-- already found with GetBuildInfo()'s return count, section 11), so try both
-- and fall back to a plain "no version info" line rather than erroring if
-- this client has neither.
local function addonMetadata(field)
  local fn = (C_AddOns and C_AddOns.GetAddOnMetadata) or GetAddOnMetadata
  if not fn then return nil end
  local ok, value = pcall(fn, "RoadToForever", field)
  if ok then return value end
  return nil
end

local function buildFooter(f)
  local version, author = addonMetadata("Version"), addonMetadata("Author")
  ui.footer = f:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
  ui.footer:SetPoint("BOTTOMLEFT", 52, 14)
  ui.footer:SetWidth(440)
  ui.footer:SetJustifyH("LEFT")
  if version and author then
    ui.footer:SetText(L.HOME_FOOTER:format(version, author))
  else
    -- Missing metadata isn't a sign of anything broken (just an older/odd
    -- API surface), so this stays a plain line, not an error state.
    ui.footer:SetText(L.HOME_FOOTER_FALLBACK)
  end
  local hit = CreateFrame("Frame", nil, f)
  hit.r2fFooterHit = true  -- marks this frame for the test harness (find_frames)
  hit:SetAllPoints(ui.footer)
  hit:SetScript("OnEnter", function()
    GameTooltip:SetOwner(hit, "ANCHOR_TOP")
    GameTooltip:AddLine(L.HOME_FOOTER_TIP, nil, nil, nil, true)
    GameTooltip:Show()
  end)
  hit:SetScript("OnLeave", function() GameTooltip:Hide() end)
  ui.footerHit = hit
end

-- Called once by MainWindow with the Home page frame.
function Home.Build(f)
  page = build(f)
  buildFooter(f)
  return page
end

function Home.Refresh()
  if not page or not page:IsVisible() then return end
  ui.macros.sub:SetText(Home.MacroLine())
  ui.talents.sub:SetText(Home.TalentLine())
  -- Import is greyed out in combat, like the book's Import button (6.7):
  -- every import button behaves the same.
  local combat = R2F.InCombat()
  ui.import:SetEnabled(not combat)
  ui.combat:SetShown(combat)
  -- Quick settings grey out in combat too (12.4.1); QuickSettings.Set also
  -- refuses then, in case a click lands between the event and this redraw.
  refreshQuick(combat)
end

-- PLAYER_REGEN_DISABLED / ENABLED: redraw at once (the button must grey out
-- before the first click in combat).
Home.SetCombat = Home.Refresh

-- UPDATE_MACROS / ACTIONBAR_SLOT_CHANGED: the latter fires once per slot (a
-- bar swap fires dozens), and each redraw reads 120 action slots, so this is
-- throttled to one redraw per 0.2 s like the book's markers. No-op while the
-- Home tab isn't showing.
local pending = false
function Home.RequestRefresh()
  if not page or not page:IsVisible() or pending then return end
  if not (C_Timer and C_Timer.After) then Home.Refresh(); return end
  pending = true
  C_Timer.After(0.2, function() pending = false; Home.Refresh() end)
end
