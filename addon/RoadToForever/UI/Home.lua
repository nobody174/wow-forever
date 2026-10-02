-- UI/Home.lua: the Home tab of the main window (ADDON_PLAN.md 12.4).
--
-- Two large entries in spellbook-slot style (big icon in the quick-slot
-- border, gold name, white line under it): Macro Book with live counts, and
-- Talents (a placeholder until the talent steps). Clicking an entry switches
-- the main window to that tab. Below them: the Import macros button (opens
-- the existing Import window) and one line on how to get an import string.
--
-- Built into the page frame MainWindow hands it, like MacroBook.

local _, R2F = ...
local L = R2F.L
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

local function build(f)
  ui.macros = entry(f, -86, "INV_Misc_Book_09", L.HOME_MACROS, "macros")
  ui.talents = entry(f, -156, "INV_Misc_Book_11", L.HOME_TALENTS, "talents")
  ui.talents.sub:SetText(L.HOME_TALENTS_LATER)
  ui.talents.sub:SetTextColor(0.6, 0.6, 0.6)

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
  return f
end

-- Called once by MainWindow with the Home page frame.
function Home.Build(f)
  page = build(f)
  return page
end

function Home.Refresh()
  if not page or not page:IsVisible() then return end
  ui.macros.sub:SetText(Home.MacroLine())
  -- Import is greyed out in combat, like the book's Import button (6.7):
  -- every import button behaves the same.
  local combat = R2F.InCombat()
  ui.import:SetEnabled(not combat)
  ui.combat:SetShown(combat)
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
