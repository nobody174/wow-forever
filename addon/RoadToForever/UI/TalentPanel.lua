-- UI/TalentPanel.lua: the Talents tab of the main window (ADDON_PLAN.md 13.4).
--
-- Step 9: a talent-link box + Preview, Copy my build (step 8's function, now
-- with its button), three mini trees side by side, the summary line.
-- Step 10: Learn talents -> confirm popup -> Talents.lua's learning engine
-- (13.5, 13.8). This file only shows its state: "Learning X / N" on the
-- button, the rest of the tab locked meanwhile (Cancel becomes Stop), the
-- stop / done message in the status line, guided mode's "Click ..." in the
-- note line. The engine runs on events, not on this tab: closing the window
-- doesn't stop a run.
--
-- Layout (page = the 540 x 500 main window):
--   Talent link [ talents.html#warrior/...               ] [Preview]
--   hint line                                          [Copy my build]
--   status line (yellow caution / red stop message)
--   Arms  0 -> 0       Fury  0 -> 0        Protection  0 -> 21
--   [4 x 7 mini tree]  [4 x 7 mini tree]   [4 x 7 mini tree]
--   summary line
--   learning note                            [Cancel] [Learn talents]
--
-- Look: Blizzard textures only (5), the talent frame's own pieces: the
-- UI-EmptySlot-White ring behind each icon tinted per state (the talent frame
-- tints the same texture green/gold/grey), TalentFrame-RankBorder for the rank
-- badge, the action-button glow for "learned now", ButtonHilight-Square on
-- hover like the Macro Book's grid.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI

local TalentPanel = {}
R2F.TalentPanel = TalentPanel

local Talents = R2F.Talents

local TREES, COLS, ROWS = 3, 4, 7    -- 13.4: three trees, each a 4 x 7 grid
local CELL, STEP_X, STEP_Y = 26, 32, 30
local TREE_W, TREE_TOP = 172, -158

local page
local ui = {}
local cells = {}           -- cells[tree][row][col]
local heads = {}           -- heads[tree] = { name, counts }
local state = { text = nil }   -- the link being previewed (nil = none)

local function cdb() return R2F.Library.cdb end

-- Colours (r, g, b) per preview state: the slot ring and the badge text.
local GOLD, WHITE, RED = { 1, 0.82, 0 }, { 1, 1, 1 }, { 1, 0.15, 0.15 }
local LOOK = {
  learned  = { slot = { 0.75, 0.75, 0.75 } },
  now      = { slot = GOLD, glow = true },
  later    = { slot = { 0.6, 0.49, 0 }, dim = true },
  off      = { slot = { 0.4, 0.4, 0.4 }, desat = true },
  conflict = { slot = RED },
  overmax  = { slot = RED },
}

-- ---------------------------------------------------------------------------
-- Mini-tree cells
-- ---------------------------------------------------------------------------

-- Hover (13.4): the game's own talent tooltip plus "Build: 3 / 3".
-- Since 13.10 talents are read through C_Traits and carry their spell id, so
-- the tooltip is GameTooltip:SetSpellByID(spellID): our (tab, index) is no
-- longer Classic's talent index, and SetTalent(tab, index) could show another
-- talent's text. SetTalent stays only for an entry without a spell id. Both
-- guarded: missing, an error, or an empty tooltip all fall back to the name.
local function cellTooltip(b)
  local e = b.entry
  if not e then return end
  GameTooltip:SetOwner(b, "ANCHOR_RIGHT")
  local shown = false
  if e.spellID then
    if GameTooltip.SetSpellByID then
      shown = pcall(GameTooltip.SetSpellByID, GameTooltip, e.spellID)
      if shown and GameTooltip.NumLines then shown = GameTooltip:NumLines() > 0 end
    end
  elseif GameTooltip.SetTalent then
    shown = pcall(GameTooltip.SetTalent, GameTooltip, e.tab, e.index)
    if shown and GameTooltip.NumLines then shown = GameTooltip:NumLines() > 0 end
  end
  if not shown then GameTooltip:AddLine(e.name, 1, 1, 1) end
  if b.withBuild then
    GameTooltip:AddLine(L.TALENT_TIP_BUILD:format(e.planned, e.maxRank), 1, 0.82, 0)
    if e.now > 0 then GameTooltip:AddLine(L.TALENT_TIP_NOW:format(e.now), 1, 0.82, 0) end
    if e.later > 0 then GameTooltip:AddLine(L.TALENT_TIP_LATER:format(e.later), 0.7, 0.7, 0.7) end
    if e.state == "conflict" then GameTooltip:AddLine(L.TALENT_TIP_CONFLICT, 1, 0.15, 0.15, true) end
    if e.state == "overmax" then GameTooltip:AddLine(L.TALENT_TIP_OVERMAX, 1, 0.15, 0.15, true) end
  end
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
  b.slot:SetSize(45, 45)
  b.slot:SetPoint("CENTER", 0, 0)
  b.icon = b:CreateTexture(nil, "BORDER")
  b.icon:SetAllPoints()
  b.glow = b:CreateTexture(nil, "OVERLAY")
  b.glow:SetTexture("Interface\\Buttons\\UI-ActionButton-Border")
  b.glow:SetBlendMode("ADD")
  b.glow:SetSize(46, 46)
  b.glow:SetPoint("CENTER", 0, 0)
  b.glow:SetVertexColor(1, 0.82, 0)
  b.glow:Hide()
  b.badge = b:CreateTexture(nil, "OVERLAY")
  b.badge:SetTexture("Interface\\TalentFrame\\TalentFrame-RankBorder")
  b.badge:SetSize(22, 22)
  b.badge:SetPoint("CENTER", b, "BOTTOMRIGHT", 0, 0)
  b.rank = b:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  b.rank:SetPoint("CENTER", b.badge, "CENTER", 0, 0)
  b.later = b:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  b.later:SetPoint("BOTTOM", b, "BOTTOM", 0, -1)
  b.later:SetText(L.TALENT_LATER)
  b.later:SetTextColor(0.8, 0.65, 0)
  b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  b:SetScript("OnEnter", cellTooltip)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
  return b
end

local function setBadge(b, text, color)
  b.rank:SetText(text or "")
  b.badge:SetShown(text ~= nil)
  b.rank:SetShown(text ~= nil)
  if text then b.rank:SetTextColor(color[1], color[2], color[3]) end
end

-- One talent's look. withBuild = false is the "your talents, no build" view
-- (before a preview, after Cancel, behind a stop message): rank badges only.
local function paintCell(b, e, withBuild)
  b.entry, b.withBuild = e, withBuild
  b.icon:SetTexture(e.icon or "Interface\\Icons\\INV_Misc_QuestionMark")
  local look = LOOK[e.state] or LOOK.off
  b.slot:SetVertexColor(look.slot[1], look.slot[2], look.slot[3])
  b.icon:SetDesaturated(look.desat or false)
  if look.dim then b.icon:SetVertexColor(0.55, 0.55, 0.55) else b.icon:SetVertexColor(1, 1, 1) end
  b.glow:SetShown(look.glow or false)
  b.later:SetShown(e.state == "later")
  if e.state == "now" then
    setBadge(b, "+" .. e.now, GOLD)                -- 13.4: "+2 in gold"
  elseif e.state == "overmax" then
    setBadge(b, tostring(e.planned), RED)
  elseif e.rank > 0 then
    setBadge(b, tostring(e.rank), WHITE)           -- learned / conflict / later
  else
    setBadge(b, nil)
  end
  b:Show()
end

-- ---------------------------------------------------------------------------
-- Building
-- ---------------------------------------------------------------------------

local function buildTrees(f)
  for t = 1, TREES do
    local x0 = 12 + (t - 1) * TREE_W
    local name = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
    name:SetPoint("TOPLEFT", f, "TOPLEFT", x0 + 6, TREE_TOP)
    name:SetJustifyH("LEFT")
    local counts = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    counts:SetPoint("LEFT", name, "RIGHT", 6, 0)
    heads[t] = { name = name, counts = counts }
    cells[t] = {}
    -- Grid centred in the column: 4 cells, 32 px apart.
    local gx = x0 + math.floor((TREE_W - (CELL + (COLS - 1) * STEP_X)) / 2)
    for row = 1, ROWS do
      cells[t][row] = {}
      for col = 1, COLS do
        cells[t][row][col] = buildCell(f, gx + (col - 1) * STEP_X, TREE_TOP - 24 - (row - 1) * STEP_Y)
      end
    end
  end
end

-- Single-line link box: InputBoxTemplate (Blizzard's standard text field)
-- if the client has it, else a plain EditBox on a tooltip backdrop; checked
-- like every template (6.7). Named because the Classic InputBoxTemplate names
-- its border textures $parentLeft etc. (R2F prefix, 6.7's naming rule).
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

local function build(f)
  ui.label = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  ui.label:SetPoint("TOPLEFT", 24, -74)
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

  ui.preview = button(f, L.BTN_PREVIEW, 90)
  ui.preview:SetPoint("LEFT", ui.edit, "RIGHT", 8, 0)
  ui.preview:SetScript("OnClick", function() TalentPanel.Preview() end)

  -- 13.4 puts Copy my build on this tab. Read-only (13.6), so it works in
  -- combat too, like /r2f copybuild.
  ui.copy = button(f, L.BTN_COPY_BUILD, 130)
  ui.copy:SetPoint("TOPRIGHT", f, "TOPRIGHT", -20, -100)
  ui.copy:SetScript("OnClick", function() Talents.CopyMyBuild() end)

  ui.hint = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  ui.hint:SetPoint("TOPLEFT", 24, -102)
  ui.hint:SetWidth(340)
  ui.hint:SetJustifyH("LEFT")
  ui.hint:SetTextColor(0.7, 0.7, 0.7)
  ui.hint:SetText(L.TALENT_TAB_HINT)

  ui.status = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  ui.status:SetPoint("TOPLEFT", 24, -134)
  ui.status:SetWidth(490)
  ui.status:SetJustifyH("LEFT")

  buildTrees(f)

  ui.summary = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  ui.summary:SetPoint("TOPLEFT", 24, TREE_TOP - 24 - (ROWS - 1) * STEP_Y - CELL - 16)
  ui.summary:SetWidth(490)
  ui.summary:SetJustifyH("LEFT")

  -- Learn talents (13.4). Enabled only for a plan with zero conflicts and
  -- points to learn now (plan.learnable), out of combat, while no run is
  -- active. The tooltip shows while disabled too (SetMotionScriptsWhileDisabled)
  -- so "why is it grey" has an answer in combat.
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

  -- Cancel; while a run is active it reads Stop (a way out of a run that is
  -- waiting on the server or on the player's clicks in guided mode).
  ui.cancel = button(f, L.BTN_CANCEL, 90)
  ui.cancel:SetPoint("RIGHT", ui.learn, "LEFT", -8, 0)
  ui.cancel:SetScript("OnClick", function()
    if Talents.LearnBusy() then Talents.StopLearn() else TalentPanel.Cancel() end
  end)

  -- Guided mode's "Click Cruelty (2 of 21)" (13.5); empty otherwise.
  ui.note = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  ui.note:SetPoint("BOTTOMLEFT", 24, 20)
  ui.note:SetWidth(270)
  ui.note:SetJustifyH("LEFT")
  return f
end

-- Called once by MainWindow with the Talents page frame.
function TalentPanel.Build(f)
  page = build(f)
  -- The last link previewed on this character (6.3's lastTalentLink) comes
  -- back in the box and is previewed again, against the live talents.
  state.text = cdb() and cdb().lastTalentLink or nil
  ui.edit:SetText(state.text or "")
  ui.placeholder:SetText(L.TALENT_LINK_PLACEHOLDER:format(Talents.ClassId() or "warrior"))
  ui.placeholder:SetShown((state.text or "") == "")
  return page
end

-- ---------------------------------------------------------------------------
-- Refresh
-- ---------------------------------------------------------------------------

local function showStatus(text, r, g, b)
  ui.status:SetText(text or "")
  if text then ui.status:SetTextColor(r, g, b) end
end

local function drawTrees(plan, withBuild)
  for t = 1, TREES do
    local tree = plan and plan.trees[t]
    for row = 1, ROWS do
      for col = 1, COLS do
        local b = cells[t][row][col]
        b.entry = nil
        b:Hide()
      end
    end
    if tree then
      heads[t].name:SetText(tree.name)
      heads[t].counts:SetText(withBuild and L.TALENT_TREE_HEAD:format(tree.current, tree.planned)
        or tostring(tree.current))
      for _, e in ipairs(tree.talents) do
        -- A talent outside the 4 x 7 grid can't be drawn (no Classic tree has
        -- one); it still counts in the plan and the summary.
        local b = cells[t][e.tier] and cells[t][e.tier][e.column]
        if b then paintCell(b, e, withBuild) end
      end
    else
      heads[t].name:SetText("")
      heads[t].counts:SetText("")
    end
  end
end

-- The last result shown (for the tests and step 10).
function TalentPanel.Result() return state.result end

-- The Learn / Cancel buttons and the locks from the learning engine's state
-- (13.4: "While learning: button reads Learning 7 / 21, everything else
-- locked"). `plan` = the build preview, nil when there is none.
-- Locked while a run is active: the link box, Preview, Copy my build. They
-- would be harmless (read-only), but changing the link mid-run would make
-- the trees show another build than the one being learned. Cancel turns into
-- Stop, the one way out.
local function setLocked(locked)
  for _, w in ipairs({ ui.preview, ui.copy }) do w:SetEnabled(not locked) end
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
    ui.cancel:SetText(L.BTN_STOP)
    ui.cancel:SetEnabled(true)
  else
    ui.learn:SetText(L.BTN_LEARN)
    -- plan.learnable = zero conflicts AND points needed AND points free
    -- (Talents.Plan). Nothing else can enable this button.
    ui.learn:SetEnabled(plan ~= nil and plan.learnable == true and not R2F.InCombat())
    ui.cancel:SetText(L.BTN_CANCEL)
    ui.cancel:SetEnabled(state.text ~= nil)
  end
  ui.note:SetText(st.phase == "guided" and R2F.TalentGuide.Text() or "")
end

function TalentPanel.Refresh()
  if not page or not page:IsVisible() then return end
  -- Re-run the preview every time: it's cheap and read-only, and the free
  -- points / learned talents may have changed since (CHARACTER_POINTS_CHANGED,
  -- PLAYER_LEVEL_UP, learning in Blizzard's own talent window).
  local res = state.text and Talents.Preview(state.text) or nil
  state.result = res
  local plan, withBuild = res and res.plan, true
  if not plan then
    -- No preview (none asked for, or a stop message): show the character's
    -- own trees, no plan. 13.3: "stop entirely, no preview, no plan".
    plan, withBuild = Talents.CurrentPlan(), false
  end
  drawTrees(plan, withBuild)

  local msg = Talents.LearnMessage()
  if res and res.error then
    showStatus(res.error, 1, 0.15, 0.15)
  elseif msg then
    -- A learning stop (red) / done (green) / preview-filled (gold) message
    -- outranks the yellow caution: it's what just happened to the character.
    if msg.kind == "stop" then
      showStatus(msg.text, 1, 0.15, 0.15)
    elseif msg.kind == "done" then
      showStatus(msg.text, 0.1, 1, 0.1)
    else
      showStatus(msg.text, 1, 0.82, 0)
    end
  elseif res and res.caution then
    showStatus(res.caution, 1, 0.82, 0)            -- 13.3's yellow line
  elseif not plan then
    showStatus(L.TALENT_READ_FAILED_TAB, 1, 0.15, 0.15)
  else
    showStatus(nil)
  end

  if withBuild then
    ui.summary:SetText(plan.summary)
    -- Red only for the conflict line (13.4); the rest are plain information.
    if plan.kind == "conflict" then ui.summary:SetTextColor(1, 0.15, 0.15) else ui.summary:SetTextColor(1, 1, 1) end
  else
    ui.summary:SetText("")
  end
  applyLearnState(withBuild and plan or nil)
end

-- Learn talents (13.4, 13.5). The preview is re-run here rather than taking
-- the one on screen (it may be up to 0.2 s old). Then, by client:
--   preview mode -> fill Blizzard's own preview (its Learn button commits,
--                   so no popup of ours);
--   a stopped run for this same link -> continue it (13.5: "Click Learn
--                   talents to continue"), no second popup;
--   otherwise    -> the confirm popup (13.4), the commit step on a client
--                   that learns a talent the moment it's sent.
function TalentPanel.Learn()
  if Talents.LearnBusy() or R2F.InCombat() or not state.text then return end
  local text = state.text
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
    -- The link may have been changed or cancelled while the popup was open.
    if state.text ~= text or Talents.LearnBusy() then return end
    Talents.StartLearn(text, points)
  end)
end

-- Preview button / Enter in the link box. Reads the box, remembers the link
-- for this character, redraws. Read-only, so it isn't greyed out or queued
-- in combat (13.7): nothing it calls is protected. Locked during a run.
function TalentPanel.Preview()
  if Talents.LearnBusy() then return end
  local text = (ui.edit:GetText() or ""):gsub("^%s+", ""):gsub("%s+$", "")
  ui.edit:ClearFocus()
  if text == "" then
    TalentPanel.Cancel()
    return
  end
  -- Another link: a stopped run (and its message) belonged to the old one.
  if text ~= state.text then Talents.ResetLearn() end
  state.text = text
  -- Only a readable link is remembered; junk would come back on every open.
  if Talents.ParseLink(text) then cdb().lastTalentLink = text end
  TalentPanel.Refresh()
  -- The trait config (C_SpecializationInfo / C_Traits, 13.10) may not be
  -- readable in the first moments after login. One retry a moment later
  -- covers that without turning ReadTrees() into an async API for every
  -- other caller (13.7-style defensive check). Kept from 13.9, whose
  -- Blizzard_TalentUI premise was wrong but whose "not ready yet" case isn't.
  if state.result and state.result.error == L.TALENT_READ_FAILED_TAB and C_Timer and C_Timer.After then
    C_Timer.After(0.5, function()
      if state.text == text then TalentPanel.Refresh() end
    end)
  end
end

-- Cancel: drop the previewed build, back to the character's own trees.
function TalentPanel.Cancel()
  if Talents.LearnBusy() then return end
  Talents.ResetLearn()
  state.text = nil
  cdb().lastTalentLink = nil
  ui.edit:SetText("")
  ui.edit:ClearFocus()
  TalentPanel.Refresh()
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

-- PLAYER_REGEN_DISABLED / ENABLED (MainWindow.SetCombat): Learn talents greys
-- out in combat and comes back after (6.9's rule for every destructive
-- button). A run in progress was already stopped by Talents.OnCombat.
function TalentPanel.SetCombat()
  TalentPanel.Refresh()
end

-- Test hook: the cell drawn for tree t, tier row, column col.
function TalentPanel.Cell(t, row, col) return cells[t] and cells[t][row] and cells[t][row][col] end
