-- UI/TalentPanel.lua: the Talents tab of the main window.
--
-- A talent-link box + Preview, Copy my build, three mini trees side by
-- side, the summary line. Learn talents -> confirm popup -> Talents.lua's
-- learning engine. This file only shows its state: "Learning X / N" on the
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
-- Look: Blizzard textures only, the talent frame's own pieces: the
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

local TREES, COLS, ROWS = 3, 4, 7    -- Three trees, each a 4 x 7 grid
local CELL, STEP_X, STEP_Y = 34, 42, 38
local TREE_W, TREE_TOP = 204, -150
TalentPanel.PAGE = { w = 650, h = 540 }

local page
local ui = {}
local cells = {}           -- cells[tree][row][col]
local heads = {}           -- heads[tree] = { name, counts }
local state = { text = nil, editing = false }   -- the link being previewed (nil = none)

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

-- Hover: the game's own talent tooltip plus "Build: 3 / 3".
-- Talents are read through C_Traits and carry their spell id, so
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
  if state.editing then GameTooltip:AddLine(L.TALENT_EDIT_HOW, 0.6, 0.85, 1) end
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
  b.glow = b:CreateTexture(nil, "OVERLAY")
  b.glow:SetTexture("Interface\\Buttons\\UI-ActionButton-Border")
  b.glow:SetBlendMode("ADD")
  b.glow:SetSize(CELL * 1.77, CELL * 1.77)
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
    setBadge(b, "+" .. e.now, GOLD)                -- "+2 in gold"
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
    local x0 = 10 + (t - 1) * TREE_W
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

local function build(f)
  -- Free talent points (moved here from Home): same wording as the minimap tooltip.
  ui.points = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  ui.points:SetPoint("TOPLEFT", 24, -52)
  -- Talented legacy perk (+5 points): only changes the level line under a build.
  ui.perk = UI.Switch(f, L.TALENT_PERK)
  ui.perk:SetPoint("TOPRIGHT", -190, -52)
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

  -- Copy my build lives on this tab. Read-only, so it works in
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
  ui.status:SetWidth(600)
  ui.status:SetJustifyH("LEFT")

  buildTrees(f)

  ui.summary = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  ui.summary:SetPoint("TOPLEFT", 24, TREE_TOP - 24 - (ROWS - 1) * STEP_Y - CELL - 16)
  ui.summary:SetWidth(600)
  ui.summary:SetJustifyH("LEFT")
  ui.level = f:CreateFontString(nil, "ARTWORK", "GameFontNormalSmall")
  ui.level:SetPoint("TOPLEFT", ui.summary, "BOTTOMLEFT", 0, -4)
  ui.level:SetTextColor(0.7, 0.7, 0.7)

  -- Learn talents. Enabled only for a plan with zero conflicts and
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

  -- Guided mode's "Click Cruelty (2 of 21)"; empty otherwise.
  ui.note = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  ui.note:SetPoint("BOTTOMLEFT", 24, 46)
  ui.note:SetWidth(270)
  ui.note:SetJustifyH("LEFT")

  -- Planner: edit switch, loadouts, sharing.
  ui.editMode = UI.Switch(f, L.TALENT_EDIT)
  ui.editMode:SetPoint("BOTTOMLEFT", 22, 20)
  ui.editMode:SetScript("OnClick", function(self)
    state.editing = self:GetChecked() and true or false
    TalentPanel.Refresh()
  end)
  ui.editMode:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_TOP")
    GameTooltip:AddLine(L.TALENT_EDIT, 1, 1, 1)
    GameTooltip:AddLine(L.TALENT_EDIT_TIP, 1, 0.82, 0, true)
    GameTooltip:Show()
  end)
  ui.editMode:SetScript("OnLeave", function() GameTooltip:Hide() end)
  ui.saveLoadout = button(f, L.BTN_SAVE_LOADOUT, 96)
  ui.saveLoadout:SetPoint("BOTTOMLEFT", 130, 16)
  ui.saveLoadout:SetScript("OnClick", function() TalentPanel.SaveLoadout() end)
  ui.loadouts = button(f, L.BTN_LOADOUTS, 86)
  ui.loadouts:SetPoint("LEFT", ui.saveLoadout, "RIGHT", 4, 0)
  ui.loadouts:SetScript("OnClick", function() TalentPanel.LoadoutsMenu() end)
  ui.share = button(f, L.BTN_SHARE, 66)
  ui.share:SetPoint("LEFT", ui.loadouts, "RIGHT", 4, 0)
  ui.share:SetScript("OnClick", function() TalentPanel.ShareMenu() end)
  return f
end

-- Called once by MainWindow with the Talents page frame.
function TalentPanel.Build(f)
  page = build(f)
  -- The last link previewed on this character (lastTalentLink) comes
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

-- The last result shown (for the tests).
function TalentPanel.Result() return state.result end

-- The Learn / Cancel buttons and the locks from the learning engine's state
-- (while learning the button reads "Learning 7 / 21" and everything else is
-- locked). `plan` = the build preview, nil when there is none.
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
  ui.points:SetText(R2F.Home.TalentLine())
  -- Re-run the preview every time: it's cheap and read-only, and the free
  -- points / learned talents may have changed since (CHARACTER_POINTS_CHANGED,
  -- PLAYER_LEVEL_UP, learning in Blizzard's own talent window).
  local res = state.text and Talents.Preview(state.text) or nil
  state.result = res
  local plan, withBuild = res and res.plan, true
  if not plan then
    -- No preview (none asked for, or a stop message): show the character's
    -- own trees, no plan: a stop means no preview.
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
    showStatus(res.caution, 1, 0.82, 0)            -- yellow caution line
  elseif not plan then
    showStatus(L.TALENT_READ_FAILED_TAB, 1, 0.15, 0.15)
  else
    showStatus(nil)
  end

  local perk = R2F.Library.db.settings.talented == true
  ui.perk:SetChecked(perk)
  if withBuild and plan.total and plan.total > 0 then
    local n, lvl = plan.total, Talents.LevelFor(plan.total, perk)
    ui.level:SetText((perk and L.TALENT_NEEDS_LEVEL_PERK or L.TALENT_NEEDS_LEVEL):format(n, lvl))
  else
    ui.level:SetText("")
  end
  if withBuild then
    ui.summary:SetText(plan.summary)
    -- Red only for the conflict line; the rest are plain information.
    if plan.kind == "conflict" then ui.summary:SetTextColor(1, 0.15, 0.15) else ui.summary:SetTextColor(1, 1, 1) end
  else
    ui.summary:SetText("")
  end
  ui.editMode:SetChecked(state.editing)
  applyLearnState(withBuild and plan or nil)
end

-- Learn talents. The preview is re-run here rather than taking
-- the one on screen (it may be up to 0.2 s old). Then, by client:
--   preview mode -> fill Blizzard's own preview (its Learn button commits,
--                   so no popup of ours);
--   a stopped run for this same link -> continue it ("Click Learn
--                   talents to continue"), no second popup;
--   otherwise    -> the confirm popup, the commit step on a client
--                   that learns a talent the moment it's sent. The same
--                   popup for "direct", "traits" and "guided".
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
-- in combat: nothing it calls is protected. Locked during a run.
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
  -- The trait config (C_SpecializationInfo / C_Traits) may not be
  -- readable in the first moments after login. One retry a moment later
  -- covers that without turning ReadTrees() into an async API for every
  -- other caller.
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
-- out in combat and comes back after (same for every destructive
-- button). A run in progress was already stopped by Talents.OnCombat.
function TalentPanel.SetCombat()
  TalentPanel.Refresh()
end

-- ---------------------------------------------------------------------------
-- Planner: cell clicks, loadouts, sharing
-- ---------------------------------------------------------------------------

-- Shows `link` in the box and redraws (like pressing Preview, without reading the box).
local function setLink(link)
  Talents.ResetLearn()
  state.text = link
  if Talents.ParseLink(link) then cdb().lastTalentLink = link end
  ui.edit:SetText(link)
  TalentPanel.Refresh()
end
TalentPanel.SetLink = setLink

-- The "class/code~hash" of the build on screen, or nil.
function TalentPanel.CurrentBody()
  local link = state.text and Talents.ParseLink(state.text)
  if not link then return nil end
  return link.class .. "/" .. link.code .. (link.hash and ("~" .. link.hash) or "")
end

-- Left click +1, right click -1, while "Edit build" is on and no learn run is active.
function TalentPanel.CellClick(cell, mouse)
  if not state.editing or Talents.LearnBusy() then return end
  local e = cell.entry
  if not e then return end
  local plan = state.result and state.result.plan or Talents.CurrentPlan()
  if not plan then return end
  local codes, why = Talents.EditPlan(plan, e.tab, e.pos, mouse == "RightButton" and -1 or 1)
  if not codes then
    if why == "cap" then R2F.Print(L.TALENT_EDIT_NOPOINTS:format(Talents.MAX_POINTS))
    elseif why == "tier" then R2F.Print(L.TALENT_EDIT_TIER)
    elseif why == "max" then R2F.Print(L.TALENT_EDIT_MAX) end
    return
  end
  local link = Talents.LinkFromCodes(codes)
  if link then setLink(link) end
  if GameTooltip:IsShown() then cellTooltip(cell) end
end

function TalentPanel.SaveLoadout()
  local body = TalentPanel.CurrentBody()
  if not body then R2F.Print(L.TALENT_LOADOUT_NEED_BUILD) return end
  UI.Prompt(L.TALENT_LOADOUT_NAME, "", L.BTN_PROMPT_OK, L.BTN_CANCEL, function(name)
    local l, why = Talents.SaveLoadout(name, body)
    if l then R2F.Print(L.TALENT_LOADOUT_SAVED:format(l.name))
    elseif why == "full" then R2F.Print(L.TALENT_LOADOUT_FULL) end
  end)
end

function TalentPanel.LoadoutsMenu()
  local list = Talents.Loadouts(Talents.ClassId())
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
    for _, l in ipairs(list) do
      items[#items + 1] = { kind = "button", text = L.TALENT_LOADOUT_DELETE:format(l.name),
                            func = function()
                              if Talents.DeleteLoadout(l.id) then R2F.Print(L.TALENT_LOADOUT_DELETED:format(l.name)) end
                            end }
    end
  end
  UI.ContextMenu(items)
end

function TalentPanel.ShareMenu()
  local body = TalentPanel.CurrentBody()
  if not body then R2F.Print(L.TALENT_LOADOUT_NEED_BUILD) return end
  local name = Talents.ClassName(body:match("^(%a+)/")) .. " build"
  for _, l in ipairs(Talents.Loadouts(Talents.ClassId())) do
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
