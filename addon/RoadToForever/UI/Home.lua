-- UI/Home.lua: the Home tab of the main window.
--
-- A headline (name + one line), the launch plan's next step as one large entry (spellbook-slot
-- style: big icon in the quick-slot border, gold name, white line under it; click opens the
-- Plan tab), then the game and minimap options (UI/Settings.lua builds them into this page)
-- and a "Share with the site" card (Export professions). Macro import, slots and Remove all
-- live on the Macros page; the free talent points on the Talents page.
-- At the very bottom, a version/author footer, so the addon's version and
-- author can be seen in game. Reads the TOC's own
-- ## Version / ## Author fields through GetAddOnMetadata so the footer can
-- never drift out of sync with the TOC the way a second hardcoded string
-- would.
--
-- Built into the page frame MainWindow hands it (650 x 540, Home.PAGE), like MacroBook.

local _, R2F = ...
local L = R2F.L
local Library, Macros = R2F.Library, R2F.Macros

local Home = {}
R2F.Home = Home

local page
local ui = {}

-- Home uses the whole content area; MainWindow reads this.
Home.PAGE = { w = 650, h = 540 }

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

-- "Macro slots: 7 of 30 character, 12 of 120 account" (Macros.Counts).
function Home.SlotLine()
  local acc, maxAcc, char, maxChar = Macros.Counts()
  return L.HOME_SLOTS_LINE:format(char, maxChar, acc, maxAcc)
end

-- The next unticked step of the chosen launch plan, "Next: [12] Skycutter to Dalaran".
function Home.PlanLine()
  local s = R2F.Plan.Next(R2F.Plan.Selected())
  if not s then return L.HOME_PLAN_DONE end
  return L.HOME_PLAN_NEXT:format(s.lvl and s.lvl ~= "" and ("[" .. s.lvl .. "] " .. s.t) or s.t)
end

function Home.MacroLine()
  local n, m = Home.Counts()
  return n == 1 and L.HOME_MACROS_COUNT_ONE:format(m) or L.HOME_MACROS_COUNT:format(n, m)
end

-- "5 free talent points", or "No free talent points". Same wording as the
-- minimap tooltip.
-- A client that gives no usable answer says so instead of "No free
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
local function entry(parent, y, icon, title, tab, w)
  local b = CreateFrame("Button", nil, parent)
  b:SetSize(w or 420, 56)
  b:SetPoint("TOPLEFT", 0, y)
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
  b.sub:SetWidth((w or 420) - 80)
  b.sub:SetJustifyH("LEFT")
  b.tab = tab
  b:SetScript("OnClick", function() R2F.MainWindow.SelectTab(tab) end)
  return b
end

local function build(f)
  ui.head = f:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
  ui.head:SetPoint("TOPLEFT", 0, -2)
  ui.head:SetText(L.ADDON_NAME)
  ui.tagline = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  ui.tagline:SetPoint("TOPLEFT", ui.head, "BOTTOMLEFT", 0, -6)
  ui.tagline:SetText(L.HOME_TAGLINE)
  ui.tagline:SetTextColor(0.75, 0.75, 0.75)

  ui.plan = entry(f, -52, "INV_Misc_Map_01", L.HOME_PLAN, "plan", 650)

  -- What to train next (Training.lua), right column.
  ui.trainHead = f:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
  ui.trainHead:SetPoint("TOPLEFT", 340, -150)
  ui.trainHead:SetText(L.TRAIN_HEAD)
  ui.trainNow = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  ui.trainNow:SetPoint("TOPLEFT", 344, -176)
  ui.trainNow:SetWidth(300)
  ui.trainNow:SetJustifyH("LEFT")
  ui.trainNext = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  ui.trainNext:SetPoint("TOPLEFT", ui.trainNow, "BOTTOMLEFT", 0, -6)
  ui.trainNext:SetWidth(300)
  ui.trainNext:SetJustifyH("LEFT")
  ui.trainNext:SetTextColor(0.7, 0.7, 0.7)
  -- At most two lines each, so the Share card below never gets covered.
  for _, fs in ipairs({ ui.trainNow, ui.trainNext }) do
    if fs.SetMaxLines then fs:SetMaxLines(2) end
  end

  -- Share with the site (right column, under the bag switches).
  ui.shareHead = f:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
  ui.shareHead:SetPoint("TOPLEFT", 340, -250)
  ui.shareHead:SetText(L.HOME_SHARE)
  ui.shareText = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  ui.shareText:SetPoint("TOPLEFT", 344, -278)
  ui.shareText:SetWidth(300)
  ui.shareText:SetJustifyH("LEFT")
  ui.shareText:SetTextColor(0.7, 0.7, 0.7)
  ui.shareText:SetText(L.HOME_PROFS_TIP)
  -- Export professions: same as /r2f profs and the profession
  -- window's Export button. Read-only, so it stays enabled in combat.
  ui.profs = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  ui.profs:SetSize(160, 24)
  ui.profs:SetPoint("TOPLEFT", 344, -352)
  ui.profs:SetText(L.HOME_PROFS)
  ui.profs:SetScript("OnClick", function() R2F.Professions.Export() end)
  ui.profs:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:SetText(L.HOME_PROFS, 1, 1, 1)
    GameTooltip:AddLine(L.HOME_PROFS_TIP, nil, nil, nil, true)
    GameTooltip:Show()
  end)
  ui.profs:SetScript("OnLeave", function() GameTooltip:Hide() end)

  ui.nextTalent = f:CreateFontString(nil, "ARTWORK", "GameFontNormalSmall")
  ui.nextTalent:SetPoint("TOPLEFT", 344, -408)
  ui.nextTalent:SetWidth(300)
  ui.nextTalent:SetJustifyH("LEFT")
  ui.combat = f:CreateFontString(nil, "ARTWORK", "GameFontRed")
  ui.combat:SetPoint("TOPLEFT", 344, -384)
  ui.combat:SetText(L.IN_COMBAT)

  -- The game / minimap / bag options.
  R2F.Settings.Build(f)
  return f
end

-- Reads the TOC's own ## Version / ## Author so the footer can't drift out of
-- sync with a second hardcoded copy. The metadata API moved from a global
-- function to C_AddOns sometime between Classic eras (same kind of API churn
-- already seen with GetBuildInfo()'s return count), so try both
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
  ui.footer:SetPoint("BOTTOMLEFT", 0, 10)
  ui.footer:SetWidth(600)
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
  ui.plan.sub:SetText(Home.PlanLine())
  local now, nxt = R2F.Training.Lines()
  ui.trainNow:SetText(now)
  ui.trainNext:SetText(nxt or "")
  ui.nextTalent:SetText(R2F.Talents.NextPointLine() or "")
  ui.combat:SetShown(R2F.InCombat())
  R2F.Settings.Refresh()
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
