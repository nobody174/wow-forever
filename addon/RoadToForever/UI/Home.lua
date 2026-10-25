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

-- The next unticked step of your launch plan, "Next: [12] Skycutter to Dalaran".
function Home.PlanLine()
  local planId = R2F.Plan.Selected()
  if not planId then return L.HOME_PLAN_NONE end
  local s = R2F.Plan.Next(planId)
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
  -- Point at it: the glow takes the theme's colour (Classic keeps the game's own yellow-white).
  local hl = b.GetHighlightTexture and b:GetHighlightTexture()
  if hl then R2F.Theme.PaintVertex(hl, "highlight") end
  b.icon = b:CreateTexture(nil, "BORDER")
  b.icon:SetSize(44, 44)
  b.icon:SetPoint("LEFT", 6, 0)
  b.icon:SetTexture("Interface\\Icons\\" .. icon)
  local border = b:CreateTexture(nil, "OVERLAY")
  border:SetTexture("Interface\\Buttons\\UI-Quickslot2")
  border:SetSize(78, 78)
  border:SetPoint("CENTER", b.icon, "CENTER", 0, -1)
  b.name = b:CreateFontString(nil, "ARTWORK", "R2FHeadingLarge")
  b.name:SetPoint("TOPLEFT", b.icon, "TOPRIGHT", 14, -4)
  b.name:SetText(title)
  b.sub = b:CreateFontString(nil, "ARTWORK", "R2FBody")
  b.sub:SetPoint("TOPLEFT", b.name, "BOTTOMLEFT", 0, -6)
  b.sub:SetWidth((w or 420) - 80)
  b.sub:SetJustifyH("LEFT")
  b.tab = tab
  b:SetScript("OnClick", function() R2F.MainWindow.SelectTab(tab) end)
  return b
end

-- The launch moment (2026-11-04 23:00 UTC, the same target as the site's countdown).
Home.LAUNCH_AT = 1793833200

-- Days, hours, minutes left (all 0 once launched), and whether the launch has happened.
function Home.CountdownParts(now)
  now = now or (GetServerTime and GetServerTime()) or time()
  local left = Home.LAUNCH_AT - now
  if left <= 0 then return 0, 0, 0, true end
  return math.floor(left / 86400), math.floor(left % 86400 / 3600), math.floor(left % 3600 / 60), false
end

function Home.UpdateCountdown()
  if not ui.cards then return end
  local d, h, m, live = Home.CountdownParts()
  local values = { d, h, m }
  for k, card in ipairs(ui.cards) do
    card.num:SetText(("%02d"):format(values[k]))
    card.frame:SetShown(not live and not ui.frost and not ui.obsidian)
  end
  ui.cdHead:SetShown(not live)
  ui.cdLive:SetShown(live)
  if ui.ob then
    for k = 1, 3 do ui.ob.num[k]:SetText(("%02d"):format(values[k])) end
    for k = 1, 3 do
      ui.ob.num[k]:SetShown(ui.obsidian == true and not live)
      ui.ob.unit[k]:SetShown(ui.obsidian == true and not live)
    end
  end
  if ui.fr then
    local fr = ui.fr
    fr.days:SetText(tostring(d))
    fr.hm:SetText(("%02d %s    %02d %s"):format(h, L.HOME_CD_HOURS:lower(), m, L.HOME_CD_MINUTES:lower()))
    fr.ring.set(math.min(d, 30) / 30)
    fr.days:SetShown(ui.frost and not live)
    fr.daysLabel:SetShown(ui.frost and not live)
    fr.hm:SetShown(ui.frost and not live)
  end
end

-- "18d 01h 44m" until the launch, then "Forever is live". `now` is a Unix time (default: the server's).
function Home.CountdownText(now)
  now = now or (GetServerTime and GetServerTime()) or time()
  local left = Home.LAUNCH_AT - now
  if left <= 0 then return L.HOME_COUNTDOWN_LIVE end
  return L.HOME_COUNTDOWN_FMT:format(math.floor(left / 86400), math.floor(left % 86400 / 3600), math.floor(left % 3600 / 60))
end

local function build(f)
  ui.head = f:CreateFontString(nil, "ARTWORK", "R2FHeadingLarge")
  ui.head:SetText(L.ADDON_NAME)
  ui.tagline = f:CreateFontString(nil, "ARTWORK", "R2FBody")
  ui.tagline:SetPoint("TOPLEFT", ui.head, "BOTTOMLEFT", 0, -6)
  ui.tagline:SetText(L.HOME_TAGLINE)
  R2F.Theme.PaintText(ui.tagline, "tagline")

  -- The launch countdown, top right: three stone cards (days, hours, minutes) and the date under them. It counts down once a
  -- second while the page is showing. After the launch the cards give way to "Forever is live".
  ui.cards = {}
  for k, label in ipairs({ L.HOME_CD_DAYS, L.HOME_CD_HOURS, L.HOME_CD_MINUTES }) do
    local card = R2F.Deco.Card(f, 70, 84)
    card.num = card.frame:CreateFontString(nil, "ARTWORK", "R2FNumber")
    card.num:SetPoint("CENTER", card.frame, "CENTER", 0, 8)
    R2F.Theme.PaintText(card.num, "heading")
    card.label = card.frame:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
    card.label:SetPoint("BOTTOM", card.frame, "BOTTOM", 0, 14)
    card.label:SetText(label)
    R2F.Theme.PaintText(card.label, "group")
    ui.cards[k] = card
  end
  ui.cdHead = f:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
  ui.cdHead:SetText(L.HOME_COUNTDOWN_DATE)
  R2F.Theme.PaintText(ui.cdHead, "tagline")
  ui.cdLive = f:CreateFontString(nil, "ARTWORK", "R2FHeadingLarge")
  ui.cdLive:SetText(L.HOME_COUNTDOWN_LIVE)
  Home.UpdateCountdown()
  local waited = 0
  f:SetScript("OnUpdate", function(_, dt)
    waited = waited + dt
    if waited < 1 then return end
    waited = 0
    Home.UpdateCountdown()
  end)

  ui.plan = entry(f, -52, "INV_Misc_Map_01", L.HOME_PLAN, "plan", 420)

  -- What to train next (Training.lua), right column.
  ui.trainHead = f:CreateFontString(nil, "ARTWORK", "R2FHeadingLarge")
  ui.trainHead:SetText(L.TRAIN_HEAD)
  ui.trainNow = f:CreateFontString(nil, "ARTWORK", "R2FBodySmall")
  ui.trainNow:SetWidth(300)
  ui.trainNow:SetJustifyH("LEFT")
  ui.trainNext = f:CreateFontString(nil, "ARTWORK", "R2FBodySmall")
  ui.trainNext:SetPoint("TOPLEFT", ui.trainNow, "BOTTOMLEFT", 0, -6)
  ui.trainNext:SetWidth(300)
  ui.trainNext:SetJustifyH("LEFT")
  R2F.Theme.PaintText(ui.trainNext, "note")
  -- At most two lines each, so the Share card below never gets covered.
  for _, fs in ipairs({ ui.trainNow, ui.trainNext }) do
    if fs.SetMaxLines then fs:SetMaxLines(2) end
  end

  -- Share with the site (right column, under the bag switches).
  ui.shareHead = f:CreateFontString(nil, "ARTWORK", "R2FHeadingLarge")
  ui.shareHead:SetText(L.HOME_SHARE)
  ui.shareText = f:CreateFontString(nil, "ARTWORK", "R2FBodySmall")
  ui.shareText:SetWidth(300)
  ui.shareText:SetJustifyH("LEFT")
  R2F.Theme.PaintText(ui.shareText, "note")
  ui.shareText:SetText(L.HOME_PROFS_TIP)
  -- Export professions: same as /r2f profs and the profession
  -- window's Export button. Read-only, so it stays enabled in combat.
  ui.profs = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  R2F.UI.ThemeButton(ui.profs, true)
  ui.profs:SetSize(160, 24)
  ui.profs:SetText(L.HOME_PROFS)
  ui.profs:SetScript("OnClick", function() R2F.Professions.Export() end)
  ui.profs:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:SetText(L.HOME_PROFS, 1, 1, 1)
    GameTooltip:AddLine(L.HOME_PROFS_TIP, nil, nil, nil, true)
    GameTooltip:Show()
  end)
  ui.profs:SetScript("OnLeave", function() GameTooltip:Hide() end)

  ui.nextTalentHead = f:CreateFontString(nil, "ARTWORK", "R2FHeadingLarge")
  ui.nextTalentHead:SetText(L.HOME_NEXT_TALENT)
  ui.nextTalent = f:CreateFontString(nil, "ARTWORK", "R2FHeading")
  ui.nextTalent:SetWidth(300)
  ui.nextTalent:SetJustifyH("LEFT")
  R2F.Theme.PaintText(ui.nextTalent, "heading")
  if ui.nextTalent.SetMaxLines then ui.nextTalent:SetMaxLines(3) end
  ui.combat = f:CreateFontString(nil, "ARTWORK", "GameFontRed")
  ui.combat:SetText(L.IN_COMBAT)

  -- The game / minimap / bag options.
  R2F.Settings.Build(f)
  return f
end

-- ---------------------------------------------------------------------------
-- Layouts. Every theme shows the same things; a theme may lay them out its own way (Theme token `home`). `placeClassic` is the
-- original arrangement of the 650 x 540 page; `placeFrost` is the 790 x 540 card layout of Frost & Void.
-- ---------------------------------------------------------------------------
local function at(el, x, y, w)
  el:ClearAllPoints()
  el:SetPoint("TOPLEFT", page, "TOPLEFT", x, y)
  if w then el:SetWidth(w) end
end

local function placeClassic()
  at(ui.head, 0, -2)
  for k, card in ipairs(ui.cards) do
    card.frame:ClearAllPoints()
    card.frame:SetPoint("TOPRIGHT", page, "TOPRIGHT", -(3 - k) * 76, -2)
  end
  ui.cdHead:ClearAllPoints()
  ui.cdHead:SetPoint("TOPRIGHT", page, "TOPRIGHT", -4, -92)
  ui.cdLive:ClearAllPoints()
  ui.cdLive:SetPoint("TOPRIGHT", page, "TOPRIGHT", -4, -30)
  at(ui.plan, 0, -52)
  ui.plan:SetWidth(420)
  ui.plan.sub:SetWidth(420 - 80)
  at(ui.trainHead, 340, -150)
  at(ui.trainNow, 344, -176, 300)
  ui.trainNext:SetWidth(300)
  at(ui.shareHead, 340, -250)
  at(ui.shareText, 344, -278, 300)
  at(ui.profs, 344, -352)
  at(ui.nextTalentHead, 340, -404)
  at(ui.nextTalent, 344, -430, 300)
  at(ui.combat, 344, -384)
  R2F.Settings.Place(nil, 300)
end

-- Frost & Void: glass cards. Countdown ring left, then launch plan and training on the right, the settings along the bottom.
local FROST_CARDS = {
  { 0, 0, 400, 262 }, { 416, 0, 374, 72, "highlight" }, { 416, -84, 374, 178 },
  { 0, -274, 400, 224 }, { 416, -274, 374, 98 }, { 416, -384, 374, 118 },
}

local function buildFrost()
  local fr = {}
  ui.fr = fr
  fr.cards = {}
  for _, c in ipairs(FROST_CARDS) do fr.cards[#fr.cards + 1] = R2F.Deco.GlassCard(page, c[1], c[2], c[3], c[4], c[5]) end
  fr.centre = page:CreateTexture(nil, "ARTWORK")
  fr.centre:SetColorTexture(0, 0, 0, 0)
  fr.centre:SetSize(2, 2)
  fr.centre:SetPoint("TOPLEFT", page, "TOPLEFT", 199, -127)
  fr.art = R2F.Deco.RingArt(page, fr.centre)
  fr.ring = R2F.Deco.Ring(page, fr.centre, 84, 72, 6, { 0.48, 0.36, 1 }, { 0.5, 0.9, 1 }, { 0.16, 0.18, 0.4, 0.9 })
  fr.head = page:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
  fr.head:SetText(L.HOME_COUNTDOWN_HEAD)
  R2F.Theme.PaintText(fr.head, "group")
  fr.days = page:CreateFontString(nil, "ARTWORK", "R2FNumber")
  R2F.Theme.PaintText(fr.days, "body")
  fr.daysLabel = page:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
  fr.daysLabel:SetText(L.HOME_CD_DAYS)
  R2F.Theme.PaintText(fr.daysLabel, "group")
  fr.hm = page:CreateFontString(nil, "ARTWORK", "R2FBody")
  fr.hm:SetJustifyH("LEFT")
  return fr
end

-- The big days number: the theme's number face at 60 px (the shared number font is smaller).
local function bigNumber(fs)
  local th = R2F.Theme.Get()
  local face = th.font and th.font.number
  if face and fs.SetFont then pcall(fs.SetFont, fs, face, 60, "") end
end

local function placeFrost()
  local fr = ui.fr or buildFrost()
  fr.head:ClearAllPoints()
  fr.head:SetPoint("TOPLEFT", page, "TOPLEFT", 24, -20)
  fr.days:ClearAllPoints()
  fr.days:SetPoint("CENTER", fr.centre, "CENTER", 0, 10)
  bigNumber(fr.days)
  fr.daysLabel:ClearAllPoints()
  fr.daysLabel:SetPoint("CENTER", fr.centre, "CENTER", 0, -36)
  at(fr.hm, 28, -234)
  ui.cdHead:ClearAllPoints()
  ui.cdHead:SetPoint("TOPRIGHT", page, "TOPLEFT", 388, -234)
  ui.cdLive:ClearAllPoints()
  ui.cdLive:SetPoint("CENTER", fr.centre, "CENTER", 0, 0)
  at(ui.plan, 424, -8)
  ui.plan:SetWidth(358)
  ui.plan.sub:SetWidth(358 - 80)
  at(ui.trainHead, 428, -96)
  at(ui.trainNow, 432, -122, 340)
  ui.trainNext:SetWidth(340)
  at(ui.nextTalentHead, 428, -192)
  at(ui.nextTalent, 432, -214, 340)
  at(ui.shareHead, 428, -396)
  at(ui.shareText, 432, -422, 340)
  at(ui.profs, 432, -468)
  at(ui.combat, 432, -506)
  R2F.Settings.Place({ quick = { 16, -286 }, minimap = { 428, -286 }, theme = { 558, -282 } }, 360)
end

-- Ember & Iron: the countdown on one wide plate, then "work orders" (rows: launch plan, training, next talent, share with the
-- site), then the settings in two columns. The page is 690 x 580.
local EMBER_ROWS = 4
local ROW_Y, ROW_STEP, ROW_H = -150, 46, 40

local function buildEmber()
  local em = { rows = {} }
  ui.em = em
  em.head = page:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
  em.head:SetText(L.HOME_WORK_ORDERS)
  R2F.Theme.PaintText(em.head, "heading")
  local titles = { L.HOME_PLAN, L.TRAIN_HEAD, L.HOME_NEXT_TALENT, L.HOME_SHARE }
  for i = 1, EMBER_ROWS do
    local row = CreateFrame("Button", nil, page)
    row:SetSize(690, ROW_H)
    row.art = R2F.Deco.Row(row)
    row.bullet = row:CreateTexture(nil, "ARTWORK")
    row.bullet:SetSize(8, 8)
    row.bullet:SetPoint("LEFT", row, "LEFT", 14, 0)
    row.bullet:SetTexture("Interface\\AddOns\\RoadToForever\\media\\dot")
    row.title = row:CreateFontString(nil, "ARTWORK", "R2FHeading")
    row.title:SetPoint("LEFT", row, "LEFT", 32, 0)
    row.title:SetWidth(150)
    row.title:SetJustifyH("LEFT")
    row.title:SetText(titles[i])
    R2F.Theme.PaintText(row.title, "body")
    row.sub = row:CreateFontString(nil, "ARTWORK", "R2FBodySmall")
    row.sub:SetPoint("LEFT", row, "LEFT", 190, 0)
    row.sub:SetWidth(i == EMBER_ROWS and 270 or 480)
    row.sub:SetJustifyH("LEFT")
    if row.sub.SetMaxLines then row.sub:SetMaxLines(2) end
    R2F.Theme.PaintText(row.sub, "note")
    row:Hide()
    em.rows[i] = row
  end
  em.rows[1]:SetScript("OnClick", function() R2F.MainWindow.SelectTab("plan") end)
  em.rows[1]:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  return em
end

-- The old widgets keep refreshing (their text feeds the rows) but are not drawn while the work orders are.
local function oldShown(on)
  for _, el in ipairs({ ui.head, ui.tagline, ui.plan, ui.trainHead, ui.trainNow, ui.trainNext, ui.shareHead, ui.shareText,
                        ui.nextTalentHead, ui.nextTalent }) do
    el:SetShown(on)
  end
end

local function refreshEmber()
  local em = ui.em
  if not em then return end
  em.rows[1].sub:SetText(ui.plan.sub:GetText() or "")
  local now, nxt = ui.trainNow:GetText() or "", ui.trainNext:GetText() or ""
  em.rows[2].sub:SetText(nxt ~= "" and (now .. "  " .. nxt) or now)
  em.rows[3].sub:SetText(ui.nextTalent:GetText() or "")
  em.rows[4].sub:SetText(L.HOME_PROFS_TIP)
end

local function bigCardNumber(card, size)
  local th = R2F.Theme.Get()
  local face = th.font and (th.font.number or th.font.heading)
  if face and card.num.SetFont then pcall(card.num.SetFont, card.num, face, size or 54, "") end
end

-- Gnomish Workshop: coloured toy cards. Blue: the countdown in digit boxes. Yellow: launch plan and next talent. Green: training.
-- Pink: share with the site. White: a tip from the sun, the quick settings and the minimap options. The page is 920 x 540.
local GN_CARDS = {
  { 0, 0, 548, 224, "blue" }, { 564, 0, 348, 224, "yellow" },
  { 0, -240, 300, 124, "green" }, { 316, -240, 300, 124, "pink" }, { 632, -240, 280, 124, "white" },
  { 0, -380, 548, 156, "white" }, { 564, -380, 348, 156, "white" },
}

local function buildGnomish()
  local gn = { cards = {} }
  ui.gn = gn
  for _, c in ipairs(GN_CARDS) do gn.cards[#gn.cards + 1] = R2F.Deco.ToyCard(page, c[1], c[2], c[3], c[4], c[5]) end
  gn.head = page:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
  gn.head:SetText(L.HOME_COUNTDOWN_HEAD)
  R2F.Theme.PaintText(gn.head, "body")
  gn.digits = {}
  for k, card in ipairs(ui.cards) do gn.digits[k] = R2F.Deco.ToyDigit(card.frame, k == 3) end
  gn.sun = R2F.Deco.ToySun(page, 112)
  gn.tip = page:CreateFontString(nil, "ARTWORK", "R2FBody")
  gn.tip:SetText(L.GNOMISH_TIP)
  gn.tip:SetJustifyH("LEFT")
  R2F.Theme.PaintText(gn.tip, "body")
  return gn
end

local function placeGnomish()
  local gn = ui.gn or buildGnomish()
  at(ui.head, 24, -22)
  gn.head:ClearAllPoints()
  gn.head:SetPoint("TOPLEFT", page, "TOPLEFT", 24, -20)
  for k, card in ipairs(ui.cards) do
    card.frame:SetSize(112, 124)
    card.frame:ClearAllPoints()
    card.frame:SetPoint("TOPLEFT", page, "TOPLEFT", 24 + (k - 1) * 128, -52)
    card.num:ClearAllPoints()
    card.num:SetPoint("CENTER", card.frame, "CENTER", 0, 10)
    bigCardNumber(card, 56)
    card.label:ClearAllPoints()
    card.label:SetPoint("BOTTOM", card.frame, "BOTTOM", 0, 14)
  end
  ui.cdHead:ClearAllPoints()
  ui.cdHead:SetPoint("TOPLEFT", page, "TOPLEFT", 420, -96)
  ui.cdHead:SetWidth(120)
  ui.cdHead:SetJustifyH("LEFT")
  ui.cdLive:ClearAllPoints()
  ui.cdLive:SetPoint("TOPLEFT", page, "TOPLEFT", 40, -110)
  at(ui.plan, 580, -16)
  ui.plan:SetWidth(320)
  ui.plan.sub:SetWidth(320 - 80)
  at(ui.nextTalentHead, 580, -110)
  at(ui.nextTalent, 584, -136, 316)
  at(ui.trainHead, 18, -254)
  at(ui.trainNow, 22, -280, 268)
  ui.trainNext:SetWidth(268)
  at(ui.shareHead, 334, -254)
  at(ui.shareText, 338, -280, 268)
  at(ui.profs, 338, -334)
  at(ui.combat, 24, -196)
  gn.sun:ClearAllPoints()
  gn.sun:SetPoint("TOPRIGHT", page, "TOPRIGHT", -2, -236)
  gn.tip:ClearAllPoints()
  gn.tip:SetPoint("TOPLEFT", page, "TOPLEFT", 650, -262)
  gn.tip:SetWidth(150)
  R2F.Settings.Place({ quick = { 20, -396 }, minimap = { 580, -396 }, theme = { 700, -392 } }, 500,
    { quickCols = 2, quickColW = 260, quickStart = -52 })
end

-- Scribe's Tome: the countdown as three wax seals (red, red, green) with the numbers on them, the launch plan beside them, the
-- usual columns below. The page is the classic 650 x 540, set one block lower.
local SEAL_ART = { "seal_red", "seal_red", "seal_green" }
local SEAL_INK = { 0.96, 0.9, 0.78 }

local function placeScribe()
  at(ui.head, 0, -2)
  for k, card in ipairs(ui.cards) do
    card.frame:SetSize(105, 130)
    card.frame:ClearAllPoints()
    card.frame:SetPoint("TOPLEFT", page, "TOPLEFT", (k - 1) * 112, -62)
    if not card.seal then
      card.seal = card.frame:CreateTexture(nil, "BACKGROUND", nil, 2)
      card.seal:SetSize(105, 105)
      card.seal:SetPoint("TOP", card.frame, "TOP", 0, 0)
    end
    card.seal:SetTexture(R2F.Deco.IMGROOT .. "scribe\\scribe_" .. SEAL_ART[k])
    card.seal:Show()
    card.num:ClearAllPoints()
    card.num:SetPoint("CENTER", card.seal, "CENTER", 0, 4)
    bigCardNumber(card, 46)
    card.num:SetTextColor(SEAL_INK[1], SEAL_INK[2], SEAL_INK[3])
    card.label:ClearAllPoints()
    card.label:SetPoint("BOTTOM", card.frame, "BOTTOM", 0, 4)
  end
  ui.cdHead:ClearAllPoints()
  ui.cdHead:SetPoint("TOPLEFT", page, "TOPLEFT", 0, -198)
  ui.cdHead:SetWidth(0)
  ui.cdHead:SetJustifyH("LEFT")
  ui.cdLive:ClearAllPoints()
  ui.cdLive:SetPoint("TOPLEFT", page, "TOPLEFT", 0, -100)
  at(ui.plan, 360, -66)
  ui.plan:SetWidth(290)
  ui.plan.sub:SetWidth(290 - 80)
  at(ui.trainHead, 340, -232)
  at(ui.trainNow, 344, -258, 300)
  ui.trainNext:SetWidth(300)
  at(ui.shareHead, 340, -330)
  at(ui.shareText, 344, -358, 300)
  at(ui.profs, 344, -432)
  at(ui.nextTalentHead, 340, -474)
  at(ui.nextTalent, 344, -498, 300)
  at(ui.combat, 344, -454)
  R2F.Settings.Place({ quick = { 0, -232 }, minimap = { 0, -452 }, theme = { 130, -448 } }, 300)
end

-- Azeroth Reforged: a nested gold-dashed panel behind the page, "Forever launches in" over three big stone boxes, the launch plan
-- under them; training, next talent and the share card in a right column; the settings along the bottom. The page is 760 x 560.
local function buildAzeroth()
  local az = {}
  ui.az = az
  az.panel = R2F.Deco.NestedPanel(page, 0, 0, 760, 560)
  az.head = page:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
  az.head:SetText(L.HOME_COUNTDOWN_HEAD)
  R2F.Theme.PaintText(az.head, "heading")
  return az
end

local function placeAzeroth()
  local az = ui.az or buildAzeroth()
  at(ui.head, 28, -22)
  at(az.head, 30, -84)
  for k, card in ipairs(ui.cards) do
    card.frame:SetSize(128, 112)
    card.frame:ClearAllPoints()
    card.frame:SetPoint("TOPLEFT", page, "TOPLEFT", 28 + (k - 1) * 140, -108)
    card.num:ClearAllPoints()
    card.num:SetPoint("CENTER", card.frame, "CENTER", 0, 12)
    bigCardNumber(card, 50)
    card.label:ClearAllPoints()
    card.label:SetPoint("BOTTOM", card.frame, "BOTTOM", 0, 16)
  end
  ui.cdHead:ClearAllPoints()
  ui.cdHead:SetPoint("TOPLEFT", page, "TOPLEFT", 30, -232)
  ui.cdHead:SetWidth(0)
  ui.cdHead:SetJustifyH("LEFT")
  ui.cdLive:ClearAllPoints()
  ui.cdLive:SetPoint("TOPLEFT", page, "TOPLEFT", 30, -140)
  at(ui.plan, 28, -262)
  ui.plan:SetWidth(400)
  ui.plan.sub:SetWidth(400 - 80)
  at(ui.trainHead, 460, -84)
  at(ui.trainNow, 464, -110, 270)
  ui.trainNext:SetWidth(270)
  at(ui.nextTalentHead, 460, -200)
  at(ui.nextTalent, 464, -224, 270)
  at(ui.shareHead, 460, -296)
  at(ui.shareText, 464, -322, 270)
  at(ui.profs, 464, -392)
  at(ui.combat, 30, -318)
  R2F.Settings.Place({ quick = { 28, -336 }, minimap = { 460, -440 }, theme = { 590, -436 } }, 340)
  ui.footer:ClearAllPoints()
  ui.footer:SetPoint("BOTTOMLEFT", page, "BOTTOMLEFT", 30, 14)
  ui.update:ClearAllPoints()
  ui.update:SetPoint("BOTTOMLEFT", page, "BOTTOMLEFT", 30, 32)
end

-- Obsidian Night: info cards on a dark card, the countdown in mono numbers (18 d 01 h 44 m) with the minutes in teal.
local OBS_CARDS = {
  { 0, 0, 540, 276, "big" }, { 556, 0, 324, 100 }, { 556, -112, 324, 164 },
  { 0, -288, 540, 208 }, { 556, -288, 324, 104 }, { 556, -404, 324, 148 },
}

local function buildObsidian()
  local ob = { cards = {} }
  ui.ob = ob
  for _, c in ipairs(OBS_CARDS) do ob.cards[#ob.cards + 1] = R2F.Deco.ObsidianCard(page, c[1], c[2], c[3], c[4], c[5]) end
  ob.circle = R2F.Deco.CircleAccent(page, ob.cards[1])
  ob.head = page:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
  ob.head:SetText(L.HOME_COUNTDOWN_HEAD)
  R2F.Theme.PaintText(ob.head, "heading")
  ob.num, ob.unit = {}, {}
  for k, unit in ipairs({ L.HOME_CD_D, L.HOME_CD_H, L.HOME_CD_M }) do
    ob.num[k] = page:CreateFontString(nil, "ARTWORK", "R2FNumber")
    R2F.Theme.PaintText(ob.num[k], k == 3 and "heading" or "body")
    ob.unit[k] = page:CreateFontString(nil, "ARTWORK", "R2FHeading")
    ob.unit[k]:SetText(unit)
    R2F.Theme.PaintText(ob.unit[k], "dim")
  end
  return ob
end

local function bigObsNumber(fs)
  local th = R2F.Theme.Get()
  local face = th.font and th.font.number
  if face and fs.SetFont then pcall(fs.SetFont, fs, face, 72, "") end
end

local function placeObsidian()
  local ob = ui.ob or buildObsidian()
  ob.head:ClearAllPoints()
  ob.head:SetPoint("TOPLEFT", page, "TOPLEFT", 28, -28)
  for k = 1, 3 do
    ob.num[k]:ClearAllPoints()
    ob.unit[k]:ClearAllPoints()
    if k == 1 then
      ob.num[k]:SetPoint("TOPLEFT", page, "TOPLEFT", 28, -92)
    else
      ob.num[k]:SetPoint("BOTTOMLEFT", ob.unit[k - 1], "BOTTOMRIGHT", 22, -6)
    end
    bigObsNumber(ob.num[k])
    ob.unit[k]:SetPoint("BOTTOMLEFT", ob.num[k], "BOTTOMRIGHT", 6, 8)
  end
  ui.cdHead:ClearAllPoints()
  ui.cdHead:SetPoint("TOPLEFT", page, "TOPLEFT", 28, -214)
  ui.cdHead:SetJustifyH("LEFT")
  ui.cdLive:ClearAllPoints()
  ui.cdLive:SetPoint("TOPLEFT", page, "TOPLEFT", 28, -110)
  at(ui.plan, 564, -24)
  ui.plan:SetWidth(308)
  ui.plan.sub:SetWidth(308 - 80)
  at(ui.trainHead, 572, -124)
  at(ui.trainNow, 576, -150, 296)
  ui.trainNext:SetWidth(296)
  at(ui.nextTalentHead, 572, -222)
  at(ui.nextTalent, 576, -246, 296)
  at(ui.shareHead, 572, -416)
  at(ui.shareText, 576, -440, 296)
  at(ui.profs, 576, -504)
  at(ui.combat, 28, -250)
  R2F.Settings.Place({ quick = { 28, -300 }, minimap = { 572, -300 }, theme = { 700, -296 } }, 480,
    { quickCols = 2, quickColW = 250, quickStart = -52 })
  -- The footer line sits in the strip along the window's bottom edge.
  ui.footer:ClearAllPoints()
  ui.footer:SetPoint("TOPLEFT", page, "TOPLEFT", 16, -628)
  ui.update:ClearAllPoints()
  ui.update:SetPoint("TOPLEFT", page, "TOPLEFT", 400, -628)
end

local function placeEmber()
  local em = ui.em or buildEmber()
  for k, card in ipairs(ui.cards) do
    card.frame:SetSize(160, 100)
    card.frame:ClearAllPoints()
    card.frame:SetPoint("TOPLEFT", page, "TOPLEFT", (k - 1) * 168, 0)
    card.num:ClearAllPoints()
    card.num:SetPoint("CENTER", card.frame, "CENTER", 0, 10)
    bigCardNumber(card)
    card.label:ClearAllPoints()
    card.label:SetPoint("BOTTOM", card.frame, "BOTTOM", 0, 12)
  end
  ui.cdHead:ClearAllPoints()
  ui.cdHead:SetPoint("TOPLEFT", page, "TOPLEFT", 516, -40)
  ui.cdHead:SetWidth(170)
  ui.cdHead:SetJustifyH("LEFT")
  ui.cdLive:ClearAllPoints()
  ui.cdLive:SetPoint("TOPLEFT", page, "TOPLEFT", 516, -30)
  at(em.head, 2, -126)
  for i, row in ipairs(em.rows) do
    row:ClearAllPoints()
    row:SetPoint("TOPLEFT", page, "TOPLEFT", 0, ROW_Y - (i - 1) * ROW_STEP)
  end
  ui.profs:ClearAllPoints()
  ui.profs:SetPoint("TOPLEFT", page, "TOPLEFT", 510, ROW_Y - 3 * ROW_STEP - 8)
  ui.profs:SetWidth(170)
  at(ui.combat, 200, -126)
  R2F.Settings.Place({ quick = { 0, -344 }, minimap = { 0, -486 }, theme = { 130, -482 } }, 650,
    { quickCols = 2, quickColW = 330, quickStart = -52, miniCols = 2, miniColW = 330 })
end

-- Called by MainWindow after every look change (and once the window is built): pick the layout of the theme in use.
function Home.Layout()
  if not page then return end
  local th = R2F.Theme.Get()
  local D = R2F.Deco
  local frost = th.home == "frost" and D.imagesOn == true and D.set == "frost"
  local ember = th.home == "ember" and D.imagesOn == true and D.set == "ember"
  local obsidian = th.home == "obsidian" and D.imagesOn == true and D.set == "obsidian"
  local azeroth = th.home == "azeroth" and D.imagesOn == true and D.set == "azeroth"
  local scribe = th.home == "scribe" and D.imagesOn == true and D.set == "scribe"
  local gnomish = th.home == "gnomish" and D.imagesOn == true and D.set == "gnomish"
  ui.frost, ui.ember, ui.obsidian = frost, ember, obsidian
  if frost then
    placeFrost()
    R2F.MainWindow.SetPageSize("home", 790, 540)
  elseif ember then
    placeEmber()
    R2F.MainWindow.SetPageSize("home", 690, 580)
  elseif obsidian then
    placeObsidian()
    R2F.MainWindow.SetPageSize("home", 880, 560)
  elseif azeroth then
    placeAzeroth()
    R2F.MainWindow.SetPageSize("home", 760, 560)
  elseif scribe then
    placeScribe()
    R2F.MainWindow.SetPageSize("home", 650, 560)
  elseif gnomish then
    placeGnomish()
    R2F.MainWindow.SetPageSize("home", 920, 540)
  else
    placeClassic()
    R2F.MainWindow.SetPageSize("home", Home.PAGE.w, Home.PAGE.h)
  end
  oldShown(not ember)
  if not ember and not azeroth and not scribe and not gnomish then
    ui.profs:SetWidth(160)
    for _, card in ipairs(ui.cards) do
      if card.seal then card.seal:Hide() end
      R2F.Theme.PaintText(card.num, "heading")
      card.frame:SetSize(70, 84)
      card.num:ClearAllPoints()
      card.num:SetPoint("CENTER", card.frame, "CENTER", 0, 8)
      card.label:ClearAllPoints()
      card.label:SetPoint("BOTTOM", card.frame, "BOTTOM", 0, 14)
      if card.num.SetFontObject and R2F.Theme.FontObject("R2FNumber") then card.num:SetFontObject("R2FNumber") end
    end
    ui.cdHead:SetWidth(0)
    ui.cdHead:SetJustifyH("RIGHT")
  end
  ui.head:SetShown(not frost and not ember and not obsidian and not gnomish)
  ui.tagline:SetShown(not frost and not ember and not obsidian and not gnomish)
  D.ShowCards("gnomish", gnomish)
  if ui.gn then
    ui.gn.head:SetShown(gnomish)
    ui.gn.sun:SetShown(gnomish)
    ui.gn.tip:SetShown(gnomish)
    for _, bar in ipairs(ui.gn.digits) do bar.show(gnomish) end
  end
  D.ShowCards("frost", frost)
  D.ShowCards("obsidian", obsidian)
  if ui.ob then
    ui.ob.head:SetShown(obsidian)
    ui.ob.circle:SetShown(obsidian)
    for k = 1, 3 do
      ui.ob.num[k]:SetShown(obsidian)
      ui.ob.unit[k]:SetShown(obsidian)
    end
  end
  if ui.az then
    ui.az.panel.show(azeroth)
    ui.az.head:SetShown(azeroth)
  end
  if not obsidian and not azeroth then
    ui.footer:ClearAllPoints()
    ui.footer:SetPoint("BOTTOMLEFT", page, "BOTTOMLEFT", 0, 10)
    ui.update:ClearAllPoints()
    ui.update:SetPoint("BOTTOMLEFT", page, "BOTTOMLEFT", 0, 28)
  end
  if ui.fr then
    ui.fr.head:SetShown(frost)
    ui.fr.ring.show(frost)
    ui.fr.art.show(frost)
  end
  if ui.em then
    ui.em.head:SetShown(ember)
    for _, row in ipairs(ui.em.rows) do
      row:SetShown(ember)
      row.art.show(ember)
    end
  end
  refreshEmber()
  Home.UpdateCountdown()
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
  -- "Update available: 0.65.0" (Version.lua heard of a newer copy from your guild or group), above the footer.
  ui.update = f:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
  ui.update:SetPoint("BOTTOMLEFT", 0, 28)
  ui.update:SetWidth(600)
  ui.update:SetJustifyH("LEFT")
  R2F.Theme.PaintText(ui.update, "heading")
  ui.footer = f:CreateFontString(nil, "ARTWORK", "R2FDimSmall")
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
  placeClassic()
  return page
end

function Home.Refresh()
  if not page or not page:IsVisible() then return end
  ui.plan.sub:SetText(Home.PlanLine())
  local now, nxt = R2F.Training.Lines()
  ui.trainNow:SetText(now)
  ui.trainNext:SetText(nxt or "")
  local np = R2F.Talents.NextPointLine()
  ui.nextTalent:SetText(np or "")
  ui.nextTalentHead:SetShown(np ~= nil)
  local newer = R2F.Version.Newer()
  ui.update:SetText(newer and (L.HOME_UPDATE:format(newer) .. "  " .. R2F.Version.URL) or "")
  ui.combat:SetShown(R2F.InCombat())
  if ui.ember then oldShown(false) refreshEmber() end
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
