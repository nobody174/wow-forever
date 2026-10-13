-- UI/TalentPanel.lua: the Talents tab of the main window, a sandbox talent calculator.
--
-- Click talents freely on any class's three trees without spending anything (the trees come from
-- TalentData.lua, the rules from TalentCalc.lua, the same as the site's calculator). It does NOT mirror the
-- character's real talents. Save a build as a loadout, share it with teammates who run the addon, or, for
-- your own class and only after a trainer reset, learn it with Talents.lua's learning engine ("Learn this
-- build"). This file only shows state: "Learning X / N" on the button, the rest of the tab locked meanwhile
-- (Stop appears), the stop / done message in the status line, guided mode's "Click ..." in the note line.
-- The engine runs on events, not on this tab: closing the window doesn't stop a run.
--
-- Layout (page = PAGE, 650 x 566):
--   [class circles x 9]  Warrior (your class)                        [Talented perk]
--   Talent link [ talents.html#warrior/...              ] [Load]
--   hint line                                                        [Copy link]
--   status line (yellow caution / red stop message)
--   Arms  12           Fury  0            Protection  0
--   [4 x 7 tree]       [4 x 7 tree]       [4 x 7 tree]
--   12 of 51 points spent, 39 left.  / needs level  / learn info
--   [Reset] [Save] [Loadouts] [Recommended] [Share]                  [Stop] [Learn this build]
--
-- Look: Blizzard textures only: the UI-EmptySlot-White ring behind each icon tinted per state,
-- TalentFrame-RankBorder for the rank badge, ButtonHilight-Square on hover.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI

local TalentPanel = {}
R2F.TalentPanel = TalentPanel

local Talents = R2F.Talents
local Calc = R2F.TalentCalc

local TREES, COLS, ROWS = 3, 4, 7    -- Three trees, each a 4 x 7 grid
local CELL, STEP_X, STEP_Y = 34, 42, 38
local TREE_W, TREE_TOP = 204, -170
TalentPanel.PAGE = { w = 650, h = 566 }

local CLASS_CIRCLES = "Interface\\TargetingFrame\\UI-Classes-Circles"
local PICK_SIZE, PICK_STEP = 26, 31

local page
local ui = {}
local cells = {}           -- cells[tree][row][col]
local heads = {}           -- heads[tree] = { name, counts }
local picks = {}           -- picks[i] = class circle button
local readTries = 0   -- retries of a talent read that failed (names not loaded yet)
-- The sandbox: the class on the board, its calc (ranks per talent), and the share link of that build.
local state = { class = nil, calc = nil, text = nil }

local function cdb() return R2F.Library.cdb end

local function ownClass()
  return Talents.ClassId()
end

-- Colours (r, g, b) per talent state: the slot ring and the badge text.
local GOLD, WHITE, GREEN = { 1, 0.82, 0 }, { 1, 1, 1 }, { 0.1, 1, 0.1 }
local LOOK = {
  full    = { slot = GOLD, badge = GOLD },                          -- all ranks taken
  partial = { slot = GREEN, badge = GREEN },                        -- some ranks taken
  open    = { slot = { 0.85, 0.85, 0.85 } },                        -- can take a point now
  locked  = { slot = { 0.4, 0.4, 0.4 }, desat = true, dim = true }, -- tier points or prerequisite missing
}

-- ---------------------------------------------------------------------------
-- The board
-- ---------------------------------------------------------------------------

local function className(id)
  return Talents.ClassName(id)
end

-- The sandbox entry (what a cell shows) for talent k of tree t.
local function entryFor(t, k)
  local x = Calc.Trees(state.class)[t].talents[k]
  local rank = Calc.Rank(state.calc, t, k)
  local st
  if rank >= x.m then st = "full"
  elseif rank > 0 then st = "partial"
  elseif Calc.CanAdd(state.calc, t, k) then st = "open"
  else st = "locked" end
  return { tab = t, pos = k, name = x.n, icon = x.i, rank = rank, maxRank = x.m, tier = x.r + 1, column = x.c + 1,
           state = st, talent = x }
end

-- Hover: the talent's name, rank, what it needs and what it does (our own text from TalentData: it works
-- for every class, whether or not you know the spell).
local function cellTooltip(b)
  local e = b.entry
  if not e then return end
  local x = e.talent
  local tree = Calc.Trees(state.class)[e.tab]
  GameTooltip:SetOwner(b, "ANCHOR_RIGHT")
  GameTooltip:AddLine(e.name, 1, 1, 1)
  GameTooltip:AddLine(L.TALENT_TIP_RANK:format(e.rank, e.maxRank), 1, 0.82, 0)
  if x.p > 0 and not Calc.TierMet(state.calc, e.tab, e.pos) then
    GameTooltip:AddLine(L.TALENT_TIP_NEEDS_POINTS:format(x.p, tree.name), 1, 0.15, 0.15, true)
  end
  for _, q in ipairs(x.q) do
    if Calc.Rank(state.calc, e.tab, q[1]) < q[2] then
      local need = tree.talents[q[1]]
      GameTooltip:AddLine(L.TALENT_TIP_NEEDS_TALENT:format(q[2], need.n), 1, 0.15, 0.15, true)
    end
  end
  local text = x.d[e.rank > 0 and e.rank or 1]
  if text and text ~= "" then GameTooltip:AddLine(text, 1, 0.82, 0, true) end
  if e.rank > 0 and e.rank < e.maxRank and x.d[e.rank + 1] then
    GameTooltip:AddLine(L.TALENT_TIP_NEXT, 1, 1, 1)
    GameTooltip:AddLine(x.d[e.rank + 1], 0.1, 1, 0.1, true)
  end
  GameTooltip:AddLine(L.TALENT_EDIT_HOW, 0.6, 0.85, 1)
  GameTooltip:Show()
end

local function buildCell(parent, x, y)
  local b = CreateFrame("Button", nil, parent)
  b:SetSize(CELL, CELL)
  b:SetPoint("TOPLEFT", parent, "TOPLEFT", x, y)
  -- The talent frame draws a big ring behind a smaller icon; same ratio here
  -- (64 px ring behind a 37 px button there).
  b.slot = b:CreateTexture(nil, "BACKGROUND")
  b.slot:SetTexture("Interface\\Buttons\\UI-EmptySlot-White")
  b.slot:SetSize(CELL * 1.73, CELL * 1.73)
  b.slot:SetPoint("CENTER", 0, 0)
  b.icon = b:CreateTexture(nil, "BORDER")
  b.icon:SetAllPoints()
  b.badge = b:CreateTexture(nil, "OVERLAY")
  b.badge:SetTexture("Interface\\TalentFrame\\TalentFrame-RankBorder")
  b.badge:SetSize(22, 22)
  b.badge:SetPoint("CENTER", b, "BOTTOMRIGHT", 0, 0)
  b.rank = b:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  b.rank:SetPoint("CENTER", b.badge, "CENTER", 0, 0)
  b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  b:SetScript("OnEnter", cellTooltip)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
  b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
  b:SetScript("OnClick", function(self, button) TalentPanel.CellClick(self, button) end)
  return b
end

local function setBadge(b, text, color)
  b.rank:SetText(text or "")
  b.badge:SetShown(text ~= nil)
  b.rank:SetShown(text ~= nil)
  if text then b.rank:SetTextColor(color[1], color[2], color[3]) end
end

local function paintCell(b, e)
  b.entry = e
  b.icon:SetTexture("Interface\\Icons\\" .. (e.icon or "INV_Misc_QuestionMark"))
  local look = LOOK[e.state] or LOOK.locked
  b.slot:SetVertexColor(look.slot[1], look.slot[2], look.slot[3])
  b.icon:SetDesaturated(look.desat or false)
  if look.dim then b.icon:SetVertexColor(0.55, 0.55, 0.55) else b.icon:SetVertexColor(1, 1, 1) end
  if e.rank > 0 then setBadge(b, tostring(e.rank), look.badge or WHITE) else setBadge(b, nil) end
  b:Show()
end

local function buildTrees(f)
  for t = 1, TREES do
    local x0 = 10 + (t - 1) * TREE_W
    local name = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
    name:SetPoint("TOPLEFT", f, "TOPLEFT", x0 + 6, TREE_TOP)
    name:SetJustifyH("LEFT")
    local counts = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    counts:SetPoint("LEFT", name, "RIGHT", 6, 0)
    heads[t] = { name = name, counts = counts }
    cells[t] = {}
    -- Grid centred in the column: 4 cells, 42 px apart.
    local gx = x0 + math.floor((TREE_W - (CELL + (COLS - 1) * STEP_X)) / 2)
    for row = 1, ROWS do
      cells[t][row] = {}
      for col = 1, COLS do
        cells[t][row][col] = buildCell(f, gx + (col - 1) * STEP_X, TREE_TOP - 24 - (row - 1) * STEP_Y)
      end
    end
  end
end

-- ---------------------------------------------------------------------------
-- Class circles
-- ---------------------------------------------------------------------------

local function buildPick(parent, i, id)
  local p = CreateFrame("CheckButton", nil, parent)
  p:SetSize(PICK_SIZE, PICK_SIZE)
  p:SetPoint("TOPLEFT", parent, "TOPLEFT", 24 + (i - 1) * PICK_STEP, -44)
  p:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  UI.CheckedGlow(p)
  p.talentClass = id
  local coords = CLASS_ICON_TCOORDS and CLASS_ICON_TCOORDS[Calc.Token(id)]
  if coords then
    p:SetNormalTexture(CLASS_CIRCLES)
    p:GetNormalTexture():SetTexCoord(unpack(coords))
  else
    UI.SetNormalIcon(p, UI.FALLBACK_ICON)
  end
  p:SetScript("OnClick", function(self)
    UI.PlaySound("IG_ABILITY_PAGE_TURN")
    TalentPanel.SelectClass(self.talentClass)
  end)
  p:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:AddLine(className(self.talentClass), 1, 1, 1)
    if self.talentClass == ownClass() then
      GameTooltip:AddLine(L.TALENT_PICK_YOURS, 0.1, 1, 0.1, true)
    else
      local name = className(self.talentClass)
      GameTooltip:AddLine(L.TALENT_PICK_OTHER:format(name, name), 0.7, 0.7, 0.7, true)
    end
    GameTooltip:Show()
  end)
  p:SetScript("OnLeave", function() GameTooltip:Hide() end)
  return p
end

-- ---------------------------------------------------------------------------
-- Building
-- ---------------------------------------------------------------------------

-- Single-line link box: InputBoxTemplate (Blizzard's standard text field)
-- if the client has it, else a plain EditBox on a tooltip backdrop; checked
-- like every template. Named because the Classic InputBoxTemplate names
-- its border textures $parentLeft etc. (R2F prefix).
local function buildLinkBox(f)
  local edit = UI.TryTemplate("EditBox", "R2FTalentLink", f, "InputBoxTemplate",
    function(e) return e.SetAutoFocus ~= nil end)
  if not edit then
    edit = CreateFrame("EditBox", "R2FTalentLinkPlain", f, (BackdropTemplateMixin and "BackdropTemplate") or nil)
    if edit.SetBackdrop then
      edit:SetBackdrop({
        bgFile = "Interface\\Tooltips\\UI-Tooltip-Background",
        edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
        tile = true, tileSize = 16, edgeSize = 12,
        insets = { left = 3, right = 3, top = 3, bottom = 3 },
      })
      edit:SetBackdropColor(0, 0, 0, 0.8)
    end
    edit:SetFontObject(ChatFontNormal or GameFontHighlight)
    edit:SetTextInsets(6, 6, 0, 0)
  end
  edit:SetAutoFocus(false)
  edit:SetMaxLetters(512)
  edit:SetSize(300, 22)
  return edit
end

local function button(f, label, w)
  local b = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  b:SetSize(w, 22)
  b:SetText(label)
  return b
end

local function tip(b, title, text)
  b:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_TOP")
    GameTooltip:AddLine(title, 1, 1, 1)
    GameTooltip:AddLine(text, 1, 0.82, 0, true)
    GameTooltip:Show()
  end)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
end

local function build(f)
  -- Class circles: pick any class's trees.
  for i, id in ipairs(Calc.ORDER) do picks[i] = buildPick(f, i, id) end
  ui.classLabel = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  ui.classLabel:SetPoint("LEFT", picks[#picks], "RIGHT", 12, 0)

  -- Talented legacy perk (+5 points): only changes the level line under a build.
  ui.perk = UI.Switch(f, L.TALENT_PERK)
  ui.perk:SetPoint("TOPRIGHT", -190, -76)
  ui.perk:SetScript("OnClick", function(self)
    R2F.Library.db.settings.talented = self:GetChecked() and true or false
    TalentPanel.Refresh()
  end)
  ui.perk:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:AddLine(L.TALENT_PERK, 1, 1, 1)
    GameTooltip:AddLine(L.TALENT_PERK_TIP, 1, 0.82, 0, true)
    GameTooltip:Show()
  end)
  ui.perk:SetScript("OnLeave", function() GameTooltip:Hide() end)

  ui.label = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  ui.label:SetPoint("TOPLEFT", 24, -100)
  ui.label:SetText(L.TALENT_LINK_LABEL)

  ui.edit = buildLinkBox(f)
  ui.edit:SetPoint("LEFT", ui.label, "RIGHT", 12, 0)
  -- Grey placeholder (EditBoxes have none of their own in Classic).
  ui.placeholder = f:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
  ui.placeholder:SetPoint("LEFT", ui.edit, "LEFT", 6, 0)
  ui.edit:HookScript("OnTextChanged", function(self)
    ui.placeholder:SetShown((self:GetText() or "") == "")
  end)
  ui.edit:SetScript("OnEnterPressed", function() TalentPanel.Preview() end)
  ui.edit:SetScript("OnEscapePressed", function(self) self:ClearFocus() end)

  ui.preview = button(f, L.BTN_LOAD_LINK, 70)
  ui.preview:SetPoint("LEFT", ui.edit, "RIGHT", 8, 0)
  ui.preview:SetScript("OnClick", function() TalentPanel.Preview() end)

  -- Copy link: the board's link for the site or Discord. Pure text, works in combat.
  ui.copy = button(f, L.BTN_COPY_LINK, 100)
  ui.copy:SetPoint("TOPRIGHT", f, "TOPRIGHT", -20, -124)
  ui.copy:SetScript("OnClick", function() TalentPanel.CopyLink() end)

  ui.hint = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  ui.hint:SetPoint("TOPLEFT", 24, -128)
  ui.hint:SetWidth(480)
  ui.hint:SetJustifyH("LEFT")
  ui.hint:SetTextColor(0.7, 0.7, 0.7)
  ui.hint:SetText(L.TALENT_TAB_HINT)

  ui.status = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  ui.status:SetPoint("TOPLEFT", 24, -152)
  ui.status:SetWidth(600)
  ui.status:SetJustifyH("LEFT")

  buildTrees(f)

  local below = TREE_TOP - 24 - (ROWS - 1) * STEP_Y - CELL - 14
  ui.summary = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  ui.summary:SetPoint("TOPLEFT", 24, below)
  ui.summary:SetWidth(600)
  ui.summary:SetJustifyH("LEFT")
  ui.level = f:CreateFontString(nil, "ARTWORK", "GameFontNormalSmall")
  ui.level:SetPoint("TOPLEFT", ui.summary, "BOTTOMLEFT", 0, -3)
  ui.level:SetTextColor(0.7, 0.7, 0.7)
  -- Learning info: what learning this build would do on your character (your own class only).
  ui.learnInfo = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  ui.learnInfo:SetPoint("TOPLEFT", ui.level, "BOTTOMLEFT", 0, -3)
  ui.learnInfo:SetWidth(600)
  ui.learnInfo:SetJustifyH("LEFT")

  -- Learn this build. Enabled only for your own class, a plan with zero conflicts and points to learn now
  -- (plan.learnable), out of combat, while no run is active. The tooltip shows while disabled too
  -- (SetMotionScriptsWhileDisabled) so "why is it grey" has an answer.
  ui.learn = button(f, L.BTN_LEARN, 130)
  ui.learn:SetPoint("BOTTOMRIGHT", -20, 16)
  ui.learn:SetEnabled(false)
  if ui.learn.SetMotionScriptsWhileDisabled then ui.learn:SetMotionScriptsWhileDisabled(true) end
  ui.learn:SetScript("OnClick", function() TalentPanel.Learn() end)
  ui.learn:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    if R2F.InCombat() and not Talents.LearnBusy() then
      GameTooltip:AddLine(L.TALENT_LEARN_COMBAT, 1, 0.15, 0.15, true)
    else
      GameTooltip:AddLine(L.TALENT_LEARN_TIP, 1, 1, 1, true)
    end
    GameTooltip:Show()
  end)
  ui.learn:SetScript("OnLeave", function() GameTooltip:Hide() end)

  -- Stop: only while a run is active (a way out of a run that is waiting on the server or on the
  -- player's clicks in guided mode).
  ui.cancel = button(f, L.BTN_STOP, 70)
  ui.cancel:SetPoint("RIGHT", ui.learn, "LEFT", -8, 0)
  ui.cancel:SetScript("OnClick", function() Talents.StopLearn() end)
  ui.cancel:Hide()

  -- Guided mode's "Click Cruelty (2 of 21)"; empty otherwise.
  ui.note = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  ui.note:SetPoint("BOTTOMLEFT", 24, 46)
  ui.note:SetWidth(270)
  ui.note:SetJustifyH("LEFT")

  -- Reset, loadouts, recommended builds, sharing.
  ui.clear = button(f, L.BTN_RESET_TALENTS, 58)
  ui.clear:SetPoint("BOTTOMLEFT", 24, 16)
  ui.clear:SetScript("OnClick", function() TalentPanel.Clear() end)
  tip(ui.clear, L.BTN_RESET_TALENTS, L.TALENT_CLEAR_TIP)
  ui.saveLoadout = button(f, L.BTN_SAVE_LOADOUT, 84)
  ui.saveLoadout:SetPoint("LEFT", ui.clear, "RIGHT", 4, 0)
  ui.saveLoadout:SetScript("OnClick", function() TalentPanel.SaveLoadout() end)
  ui.loadouts = button(f, L.BTN_LOADOUTS, 74)
  ui.loadouts:SetPoint("LEFT", ui.saveLoadout, "RIGHT", 4, 0)
  ui.loadouts:SetScript("OnClick", function() TalentPanel.LoadoutsMenu() end)
  ui.recommended = button(f, L.BTN_RECOMMENDED, 104)
  ui.recommended:SetPoint("LEFT", ui.loadouts, "RIGHT", 4, 0)
  ui.recommended:SetScript("OnClick", function() TalentPanel.RecommendedMenu() end)
  tip(ui.recommended, L.BTN_RECOMMENDED, L.TALENT_RECOMMENDED_TIP)
  ui.share = button(f, L.BTN_SHARE, 56)
  ui.share:SetPoint("LEFT", ui.recommended, "RIGHT", 4, 0)
  ui.share:SetScript("OnClick", function() TalentPanel.ShareMenu() end)
  return f
end

-- ---------------------------------------------------------------------------
-- The board's state
-- ---------------------------------------------------------------------------

-- Puts a class on the board with an empty (or the given) code. Returns true when a class was set.
local function setBoard(classId, code)
  local calc, ok = Calc.FromCode(classId, code)
  if not calc then return false end
  state.class, state.calc = classId, calc
  return true, ok
end

local function linkText()
  return Talents.SITE_URL .. Calc.Body(state.calc)
end

local function remember()
  local c = cdb()
  if c then c.lastTalentLink = linkText() end
end

-- Called once by MainWindow with the Talents page frame.
function TalentPanel.Build(f)
  page = build(f)
  -- The last board on this character (lastTalentLink) comes back; none = an empty board of your own class.
  local last = cdb() and cdb().lastTalentLink
  local link = last and Talents.ParseLink(last)
  if not (link and setBoard(link.class, link.code)) then
    setBoard(ownClass() or "warrior", "")
  end
  state.text = linkText()
  ui.edit:SetText("")
  ui.placeholder:SetText(L.TALENT_LINK_PLACEHOLDER:format(state.class))
  ui.placeholder:SetShown(true)
  return page
end

-- Click a class circle: that class's trees, an empty board.
function TalentPanel.SelectClass(id)
  if Talents.LearnBusy() or id == state.class then return end
  Talents.ResetLearn()
  if setBoard(id, "") then
    ui.edit:SetText("")
    ui.placeholder:SetText(L.TALENT_LINK_PLACEHOLDER:format(id))
    remember()
  end
  TalentPanel.Refresh()
end

function TalentPanel.Class() return state.class end
function TalentPanel.Calc() return state.calc end

-- ---------------------------------------------------------------------------
-- Refresh
-- ---------------------------------------------------------------------------

local function showStatus(text, r, g, b)
  ui.status:SetText(text or "")
  if text then ui.status:SetTextColor(r, g, b) end
end

local function drawTrees()
  local trees = Calc.Trees(state.class)
  for t = 1, TREES do
    for row = 1, ROWS do
      for col = 1, COLS do
        local b = cells[t][row][col]
        b.entry = nil
        b:Hide()
      end
    end
    local tree = trees and trees[t]
    if tree then
      heads[t].name:SetText(tree.name)
      heads[t].counts:SetText(tostring(Calc.TreePoints(state.calc, t)))
      for k = 1, #tree.talents do
        local e = entryFor(t, k)
        -- A talent outside the 4 x 7 grid can't be drawn (no Classic tree has one).
        local b = cells[t][e.tier] and cells[t][e.tier][e.column]
        if b then paintCell(b, e) end
      end
    else
      heads[t].name:SetText("")
      heads[t].counts:SetText("")
    end
  end
end

-- The last learn preview (your own class's board against your real talents), for the tests.
function TalentPanel.Result() return state.result end

-- The Learn / Stop buttons and the locks from the learning engine's state (while learning the button reads
-- "Learning 7 / 21" and the board is locked): the board would show another build than the one being learned.
local function setLocked(locked)
  for _, w in ipairs({ ui.preview, ui.copy, ui.clear, ui.saveLoadout, ui.loadouts, ui.recommended, ui.share }) do
    w:SetEnabled(not locked)
  end
  for _, p in ipairs(picks) do p:SetEnabled(not locked) end
  if locked then
    ui.edit:ClearFocus()
    if ui.edit.Disable then ui.edit:Disable() end
  elseif ui.edit.Enable then
    ui.edit:Enable()
  end
end

local function applyLearnState(plan)
  local st = Talents.LearnStatus()
  local busy = Talents.LearnBusy()
  setLocked(busy)
  if busy then
    ui.learn:SetText(st.phase == "queued" and L.TALENT_LEARN_WAITING
      or L.TALENT_LEARNING:format(st.current, st.total))
    ui.learn:SetEnabled(false)
    ui.cancel:Show()
    ui.cancel:SetEnabled(true)
  else
    ui.learn:SetText(L.BTN_LEARN)
    -- plan.learnable = zero conflicts AND points needed AND points free
    -- (Talents.Plan). Nothing else can enable this button.
    ui.learn:SetEnabled(plan ~= nil and plan.learnable == true and not R2F.InCombat())
    ui.cancel:Hide()
  end
  ui.note:SetText(st.phase == "guided" and R2F.TalentGuide.Text() or "")
end

function TalentPanel.Refresh()
  if not page or not page:IsVisible() or not state.calc then return end
  state.text = linkText()
  drawTrees()
  for _, p in ipairs(picks) do p:SetChecked(p.talentClass == state.class) end
  local own = state.class == ownClass()
  ui.classLabel:SetText(own and L.TALENT_CLASS_YOURS:format(className(state.class))
    or L.TALENT_CLASS_OTHER:format(className(state.class)))
  if own then ui.classLabel:SetTextColor(1, 0.82, 0) else ui.classLabel:SetTextColor(0.7, 0.7, 0.7) end

  -- Your own class with points on the board: check it against your real talents (read-only), for the Learn
  -- button and the line under the board. No points yet = nothing to check.
  local total = Calc.Total(state.calc)
  local res = (own and total > 0) and Talents.Preview(state.text) or nil
  state.result = res
  local plan = res and res.plan

  local msg = Talents.LearnMessage()
  if res and res.error then
    showStatus(res.error, 1, 0.15, 0.15)
  elseif msg then
    -- A learning stop (red) / done (green) / preview-filled (gold) message outranks the yellow caution:
    -- it's what just happened to the character.
    if msg.kind == "stop" then
      showStatus(msg.text, 1, 0.15, 0.15)
    elseif msg.kind == "done" then
      showStatus(msg.text, 0.1, 1, 0.1)
    else
      showStatus(msg.text, 1, 0.82, 0)
    end
  elseif res and res.caution then
    showStatus(res.caution, 1, 0.82, 0)            -- yellow caution line
  else
    showStatus(nil)
  end
  -- Soon after login the game may not have the talent names loaded yet: try again a few times.
  if res and res.error == L.TALENT_READ_FAILED_TAB and readTries < 8 and C_Timer and C_Timer.After then
    readTries = readTries + 1
    C_Timer.After(0.8, function() if page and page:IsVisible() then TalentPanel.Refresh() end end)
  elseif not (res and res.error) then
    readTries = 0
  end

  local perk = R2F.Library.db.settings.talented == true
  ui.perk:SetChecked(perk)
  ui.summary:SetText(L.TALENT_SB_SUMMARY:format(total, Calc.MAX_POINTS, Calc.MAX_POINTS - total))
  if total > 0 then
    ui.level:SetText((perk and L.TALENT_NEEDS_LEVEL_PERK or L.TALENT_NEEDS_LEVEL):format(total, Calc.Level(state.calc, perk)))
  else
    ui.level:SetText("")
  end
  if not own then
    ui.learnInfo:SetText(L.TALENT_PREVIEW_ONLY:format(className(state.class)))
    ui.learnInfo:SetTextColor(0.7, 0.7, 0.7)
  elseif plan then
    ui.learnInfo:SetText(plan.summary)
    if plan.kind == "conflict" then ui.learnInfo:SetTextColor(1, 0.15, 0.15) else ui.learnInfo:SetTextColor(1, 1, 1) end
  else
    ui.learnInfo:SetText("")
  end
  applyLearnState(plan)
end

-- Learn this build (your own class only). The preview is re-run here rather than taking the one on
-- screen (it may be up to 0.2 s old). Then, by client:
--   preview mode -> fill Blizzard's own preview (its Learn button commits, so no popup of ours);
--   a stopped run for this same link -> continue it ("Click Learn talents to continue"), no second popup;
--   otherwise    -> the confirm popup, the commit step on a client that learns a talent the moment it's
--                   sent. The same popup for "direct", "traits" and "guided".
function TalentPanel.Learn()
  if Talents.LearnBusy() or R2F.InCombat() or not state.calc or state.class ~= ownClass() then return end
  local text = linkText()
  local plan = Talents.Preview(text).plan
  if not (plan and plan.learnable) then TalentPanel.Refresh(); return end
  local mode = Talents.LearnMode()
  if mode == "preview" then
    Talents.FillPreview(plan)
    return
  end
  if Talents.CanResume(text) then
    Talents.ResumeLearn()
    return
  end
  local points = Talents.LearnPoints(plan)
  local n = #points
  local question = n == 1 and L.TALENT_CONFIRM_ONE or L.TALENT_CONFIRM:format(n)
  if mode == "guided" then question = question .. "\n\n" .. L.TALENT_CONFIRM_GUIDED end
  UI.Confirm(question, L.BTN_LEARN_CONFIRM, L.BTN_CANCEL, function()
    -- The board may have been changed while the popup was open.
    if linkText() ~= text or Talents.LearnBusy() then return end
    Talents.StartLearn(text, points)
  end)
end

-- Loads a pasted link onto the board (any class). Returns true, or false and the reason shown to the player.
-- A link with a hash that differs from this addon's own talent data is refused: its digits could mean other
-- talents than the ones shown here (the site changed after this addon version was made).
local function loadLink(text)
  local link = Talents.ParseLink(text)
  if not link then return false, L.TALENT_BAD_LINK end
  if not Calc.Class(link.class) then return false, L.TALENT_BAD_LINK end
  if link.hash and link.hash ~= Calc.Hash(link.class) then return false, L.TALENT_HASH_MISMATCH_SB end
  local calc, ok = Calc.FromCode(link.class, link.code)
  if not ok then return false, L.TALENT_LINK_INVALID end
  Talents.ResetLearn()
  state.class, state.calc = link.class, calc
  return true
end

-- Load button / Enter in the link box: reads the box and puts that build on the board.
-- Read-only, so it isn't greyed out in combat. Locked during a run.
function TalentPanel.Preview()
  if Talents.LearnBusy() then return end
  local text = (ui.edit:GetText() or ""):gsub("^%s+", ""):gsub("%s+$", "")
  ui.edit:ClearFocus()
  if text == "" then return end
  local ok, why = loadLink(text)
  if ok then
    remember()
    ui.edit:SetText("")
    showStatus(nil)
    TalentPanel.Refresh()
  else
    TalentPanel.Refresh()
    showStatus(why, 1, 0.15, 0.15)
  end
end

-- MainWindow: the Talents page was hidden (tab switch or window closed).
-- Let go of the keyboard so typed keys go back to the game.
function TalentPanel.OnHide()
  if ui.edit then ui.edit:ClearFocus() end
end

-- CHARACTER_POINTS_CHANGED / PLAYER_LEVEL_UP (and the other window events):
-- throttled like the book and Home, no-op while the tab isn't showing.
local pending = false
function TalentPanel.RequestRefresh()
  if not page or not page:IsVisible() or pending then return end
  if not (C_Timer and C_Timer.After) then TalentPanel.Refresh(); return end
  pending = true
  C_Timer.After(0.2, function() pending = false; TalentPanel.Refresh() end)
end

-- PLAYER_REGEN_DISABLED / ENABLED (MainWindow.SetCombat): Learn greys out in combat and comes back after.
-- A run in progress was already stopped by Talents.OnCombat. The sandbox itself works in combat.
function TalentPanel.SetCombat()
  TalentPanel.Refresh()
end

-- ---------------------------------------------------------------------------
-- Clicks, loadouts, recommended builds, sharing
-- ---------------------------------------------------------------------------

-- Shows `link` on the board (any class), like pressing Load without reading the box. Returns true / false.
local function setLink(link)
  local ok = loadLink(link)
  if ok then remember() end
  TalentPanel.Refresh()
  return ok
end
TalentPanel.SetLink = setLink

-- The "class/code~hash" of the board, or nil.
function TalentPanel.CurrentBody()
  if not state.calc then return nil end
  return Calc.Body(state.calc)
end

-- Left click +1 (Shift: to the maximum), right click -1 (Shift: all the way down), unless a learn run is active.
function TalentPanel.CellClick(cell, mouse)
  if Talents.LearnBusy() then return end
  local e = cell.entry
  if not (e and state.calc) then return end
  local shift = IsShiftKeyDown and IsShiftKeyDown() or false
  Talents.ResetLearn()   -- a stopped run belonged to the build as it was
  if mouse == "RightButton" then
    Calc.Remove(state.calc, e.tab, e.pos, shift)
  else
    local why = Calc.AddBlock(state.calc, e.tab, e.pos)
    if why == "cap" then R2F.Print(L.TALENT_EDIT_NOPOINTS:format(Calc.MAX_POINTS))
    elseif why == "tier" then R2F.Print(L.TALENT_EDIT_TIER)
    elseif why == "prereq" then R2F.Print(L.TALENT_EDIT_PREREQ)
    elseif why == "max" then R2F.Print(L.TALENT_EDIT_MAX) end
    if not why then Calc.Add(state.calc, e.tab, e.pos, shift) end
  end
  remember()
  TalentPanel.Refresh()
  if GameTooltip:IsShown() then
    local entry = entryFor(e.tab, e.pos)
    cell.entry = entry
    cellTooltip(cell)
  end
end

-- Reset: an empty board of the same class. Your real talents are not touched.
function TalentPanel.Clear()
  if Talents.LearnBusy() then return end
  Talents.ResetLearn()
  Calc.Reset(state.calc)
  remember()
  TalentPanel.Refresh()
end

function TalentPanel.CopyLink()
  if not state.calc then return end
  R2F.UI.ShowCopy(linkText(), L.TALENT_COPY_HINT)
end

function TalentPanel.SaveLoadout()
  local body = TalentPanel.CurrentBody()
  if not body or Calc.Total(state.calc) == 0 then R2F.Print(L.TALENT_LOADOUT_NEED_BUILD) return end
  UI.Prompt(L.TALENT_LOADOUT_NAME, "", L.BTN_PROMPT_OK, L.BTN_CANCEL, function(name)
    local l, why = Talents.SaveLoadout(name, body)
    if l then R2F.Print(L.TALENT_LOADOUT_SAVED:format(l.name))
    elseif why == "full" then R2F.Print(L.TALENT_LOADOUT_FULL) end
  end)
end

-- Deleting lives in its own menu and always asks first.
function TalentPanel.DeleteMenu()
  local items = { { kind = "title", text = L.TALENT_LOADOUT_DELETE_TITLE } }
  for _, l in ipairs(Talents.Loadouts(state.class)) do
    items[#items + 1] = { kind = "button", text = l.by and L.TALENT_LOADOUT_BY:format(l.name, l.by) or l.name,
                          func = function()
                            UI.Confirm(L.TALENT_LOADOUT_CONFIRM:format(l.name), L.BTN_DELETE, L.BTN_CANCEL, function()
                              if Talents.DeleteLoadout(l.id) then R2F.Print(L.TALENT_LOADOUT_DELETED:format(l.name)) end
                            end)
                          end }
  end
  UI.ContextMenu(items)
end

function TalentPanel.LoadoutsMenu()
  local list = Talents.Loadouts(state.class)
  local items = {}
  if #list == 0 then
    items[1] = { kind = "title", text = L.TALENT_LOADOUT_NONE }
  else
    for _, l in ipairs(list) do
      local label = l.by and L.TALENT_LOADOUT_BY:format(l.name, l.by) or l.name
      items[#items + 1] = { kind = "button", text = L.TALENT_LOADOUT_LOAD:format(label),
                            func = function() setLink(l.body) end }
    end
    items[#items + 1] = { kind = "divider" }
    items[#items + 1] = { kind = "button", text = L.TALENT_LOADOUT_DELETE_MENU,
                          func = function() TalentPanel.DeleteMenu() end }
  end
  UI.ContextMenu(items)
end

-- Our recommended builds for the class on the board (builds.html), grouped Tank / DPS / Healer. A pick
-- puts it on the board; nothing is learned.
function TalentPanel.RecommendedMenu()
  local list = Calc.Recommended(state.class)
  local items = {}
  if #list == 0 then
    items[1] = { kind = "title", text = L.TALENT_RECOMMENDED_NONE }
  else
    local role
    for _, b in ipairs(list) do
      if b.role ~= role then
        role = b.role
        items[#items + 1] = { kind = "title", text = L["TALENT_ROLE_" .. role:upper()] }
      end
      items[#items + 1] = { kind = "button", text = L.TALENT_RECOMMENDED_ITEM:format(b.name, b.level),
                            func = function()
                              setLink(Talents.SITE_URL .. state.class .. "/" .. b.code .. "~" .. Calc.Hash(state.class))
                            end }
    end
  end
  UI.ContextMenu(items)
end

function TalentPanel.ShareMenu()
  local body = TalentPanel.CurrentBody()
  if not body or Calc.Total(state.calc) == 0 then R2F.Print(L.TALENT_LOADOUT_NEED_BUILD) return end
  local name = Talents.ClassName(state.class) .. " build"
  for _, l in ipairs(Talents.Loadouts(state.class)) do
    if l.body == body then name = l.name end
  end
  local items = { { kind = "title", text = L.TALENT_SHARE_TITLE },
                  { kind = "button", text = L.TALENT_SHARE_COPY,
                    func = function() R2F.UI.ShowCopy(Talents.SITE_URL .. body, L.TALENT_COPY_HINT) end } }
  for _, ch in ipairs(Talents.CHANNELS) do
    items[#items + 1] = { kind = "button", text = L["TALENT_SHARE_" .. ch],
                          func = function()
                            if Talents.ShareLoadout({ name = name, body = body }, ch) then
                              R2F.Print(L.TALENT_SHARE_SENT:format(name, L["TALENT_SHARE_" .. ch]))
                            else
                              R2F.Print(L.TALENT_SHARE_FAILED)
                            end
                          end }
  end
  UI.ContextMenu(items)
end

-- Test hook: the cell drawn for tree t, tier row, column col.
function TalentPanel.Cell(t, row, col) return cells[t] and cells[t][row] and cells[t][row][col] end

-- Test hook: puts a board on screen WITHOUT the validity checks (the learning-engine tests build boards from a small
-- fixture tree whose tier points and prerequisites don't follow the real rules).
function TalentPanel.SetBoardUnchecked(classId, code)
  local calc = Calc.New(classId)
  if not calc then return end
  local n = 0
  for part in ((code or "") .. "-"):gmatch("([^%-]*)%-") do
    n = n + 1
    local r = calc.ranks[n]
    if r then for k = 1, #r do r[k] = tonumber(part:sub(k, k)) or 0 end end
  end
  Talents.ResetLearn()
  state.class, state.calc = classId, calc
  remember()
  TalentPanel.Refresh()
end
