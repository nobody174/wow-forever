-- UI/Plan.lua: the Plan tab of the main window.
--
--   Who the plan is for ("Alliance Skyborne Hunter": the logged-in character, read by Plan.lua) with a small
--   "Preview another combination" control -> progress line -> a scrolling list of
--   the launch-day steps grouped by phase. Each step: a tick box (saved per character),
--   the level, the title with its tags, the note, and one line per waypoint:
--     exact            [Waypoint]  label
--     classic / approx [Waypoint]  label  (may have moved)
--     check            label  (position not known yet)   -- no button
--   The button points our own arrow (Nav.lua) at the spot; where that isn't possible it
--   prints the /way line to chat (Plan.Waypoint).
-- The list is redrawn from the data every time (a few dozen rows): row frames are
-- pooled, heights come from the wrapped text so notes of any length fit.
-- The "Quest shopping list" button swaps the list for the site's Buyable quests (see layoutBuy).
-- Everything here only writes SavedVariables or calls map getters / our arrow, so it all
-- stays usable in combat.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI
local Plan = R2F.Plan

local Tab = {}
R2F.PlanTab = Tab

local page, scroll, content
local ui = {}
local headers = {}    -- pooled phase heading font strings
local rows = {}       -- pooled step rows
local view = "steps"  -- "steps" (the launch-day list) or "buy" (the quest shopping list)
local buyRows = {}    -- pooled shopping-list rows
local buyHeaders = {} -- pooled shopping-list phase headings

local CONTENT_W = 440
local TEXT_W = 360

local function visible()
  return page ~= nil and page:IsVisible()
end

-- A pooled phase heading.
local function header(i)
  local h = headers[i]
  if not h then
    h = content:CreateFontString(nil, "ARTWORK", "R2FHeadingLarge")
    headers[i] = h
  end
  return h
end

-- A pooled step row: tick box, level, title, note and waypoint lines.
local function row(i)
  local r = rows[i]
  if r then return r end
  r = { points = {} }
  r.check = UI.CheckButton(content, "")
  r.check:SetScript("OnClick", function(self)
    if self.stepId then
      Plan.SetDone(self.stepId, not Plan.IsDone(self.stepId))
      Tab.Refresh()
      if R2F.Home and R2F.Home.Refresh then R2F.Home.Refresh() end
    end
  end)
  r.lvl = content:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
  r.lvl:SetJustifyH("LEFT")
  r.lvl:SetWidth(46)
  r.title = content:CreateFontString(nil, "ARTWORK", "R2FBody")
  r.title:SetJustifyH("LEFT")
  r.title:SetWidth(TEXT_W)
  r.note = content:CreateFontString(nil, "ARTWORK", "R2FBodySmall")
  r.note:SetJustifyH("LEFT")
  R2F.Theme.PaintText(r.note, "note")
  r.note:SetWidth(TEXT_W)
  rows[i] = r
  return r
end

-- A pooled waypoint line inside a row.
local function pointLine(r, j)
  local p = r.points[j]
  if p then return p end
  p = {}
  p.btn = CreateFrame("Button", nil, content, "UIPanelButtonTemplate")
  R2F.UI.ThemeButton(p.btn)
  p.btn:SetSize(96, 18)
  p.btn:SetScript("OnClick", function(self)
    if self.point then Plan.Waypoint(self.point, self.stepId) end
  end)
  p.text = content:CreateFontString(nil, "ARTWORK", "R2FBodySmall")
  p.text:SetJustifyH("LEFT")
  p.text:SetWidth(TEXT_W - 100)
  r.points[j] = p
  return p
end

-- Hover on a weapon line: the item's own tooltip, then how much better it scores than what you wear and where it comes from.
local function weaponTip(hit)
  local w = hit.w
  if not w then return end
  GameTooltip:SetOwner(hit, "ANCHOR_RIGHT")
  local shown = false
  if GameTooltip.SetHyperlink then shown = pcall(GameTooltip.SetHyperlink, GameTooltip, "item:" .. w.id) end
  if shown and GameTooltip.NumLines then shown = GameTooltip:NumLines() > 0 end
  if not shown then GameTooltip:AddLine(w.name or "", 1, 1, 1) end
  GameTooltip:AddLine(" ")
  GameTooltip:AddLine(L.PLAN_WEAPON_TIP_UP:format(w.delta, w.specName or "?"), 0.3, 1, 0.3)
  if w.quest then
    GameTooltip:AddLine(L.PLAN_WEAPON_TIP_QUEST:format(w.quest, w.zone or "?"), 1, 0.82, 0, true)
  elseif w.rankText then
    GameTooltip:AddLine(L.PLAN_WEAPON_TIP_BIZ:format(w.rankText, w.source or "?"), 1, 0.82, 0, true)
  end
  GameTooltip:AddLine(L.PLAN_WEAPON_TIP_NOTE, 0.6, 0.6, 0.6, true)
  GameTooltip:Show()
end

local function hideRowsFrom(i)
  for k = i, #rows do
    local r = rows[k]
    r.check:Hide(); r.lvl:Hide(); r.title:Hide(); r.note:Hide()
    for _, p in ipairs(r.points) do p.btn:Hide(); p.text:Hide() end
    for _, g in ipairs(r.gears or {}) do g:Hide(); if g.hit then g.hit:Hide() end end
  end
end

local function titleWithTags(s)
  local text = s.t
  for _, tag in ipairs(s.tags) do
    text = text .. " |cffffd100" .. Plan.TagText(tag) .. "|r"
  end
  return text
end

local function layout()
  local planId = Plan.Selected()
  local arrow = R2F.Nav.Supported()
  if not planId then
    hideRowsFrom(1)
    for k = 1, #headers do headers[k]:Hide() end
    content:SetHeight(1)
    ui.contentHeight = 0
    return
  end
  -- Weapons you can get at a step that beat what you wear (quest rewards, Mr.BiZ dungeon / vendor picks).
  local route = R2F.QuestWeapons.StepLines(planId)
  local y, nHead, nRow = 0, 0, 0
  for _, ph in ipairs(Plan.Phases(planId)) do
    nHead = nHead + 1
    local h = header(nHead)
    h:ClearAllPoints()
    h:SetPoint("TOPLEFT", content, "TOPLEFT", 4, -y)
    h:SetText(ph.title)
    h:Show()
    y = y + 28
    for _, s in ipairs(ph.steps) do
      nRow = nRow + 1
      local r = row(nRow)
      r.check.stepId = s.id
      r.check:ClearAllPoints()
      r.check:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -y + 4)
      r.check:SetChecked(Plan.IsDone(s.id))
      r.check:Show()
      r.lvl:ClearAllPoints()
      r.lvl:SetPoint("TOPLEFT", content, "TOPLEFT", 46, -y - 3)
      r.lvl:SetText(s.lvl or "")
      r.lvl:Show()
      r.title:ClearAllPoints()
      r.title:SetPoint("TOPLEFT", content, "TOPLEFT", 96, -y)
      r.title:SetText(titleWithTags(s))
      if Plan.IsDone(s.id) then R2F.Theme.PaintText(r.title, "dim") else R2F.Theme.PaintText(r.title, "body") end
      r.title:Show()
      local used = math.max(r.title:GetStringHeight(), 14) + 2
      if s.n and s.n ~= "" then
        r.note:ClearAllPoints()
        r.note:SetPoint("TOPLEFT", content, "TOPLEFT", 96, -(y + used))
        r.note:SetText(s.n)
        r.note:Show()
        used = used + math.max(r.note:GetStringHeight(), 12) + 2
      else
        r.note:Hide()
      end
      local pts = Plan.Points(s.id, planId)
      for j, pt in ipairs(pts) do
        local p = pointLine(r, j)
        local py = -(y + used)
        local text = pt.label
        if not Plan.HasPosition(pt) then
          p.btn:Hide()
          p.text:ClearAllPoints()
          p.text:SetPoint("TOPLEFT", content, "TOPLEFT", 96, py - 2)
          text = text .. " |cffff8040(" .. L.PLAN_UNKNOWN_POS .. ")|r"
        else
          p.btn.point = pt
          p.btn.stepId = s.id
          p.btn:SetText(arrow and L.PLAN_WAYPOINT or L.PLAN_WAYLINE_BTN)
          p.btn:ClearAllPoints()
          p.btn:SetPoint("TOPLEFT", content, "TOPLEFT", 96, py)
          p.btn:Show()
          p.text:ClearAllPoints()
          p.text:SetPoint("TOPLEFT", content, "TOPLEFT", 96 + 104, py - 2)
          if Plan.MayHaveMoved(pt) then text = text .. " |cff999999(" .. L.PLAN_MAY_MOVE .. ")|r" end
        end
        p.text:SetText(text)
        p.text:Show()
        used = used + 22
      end
      for j = #pts + 1, #r.points do
        r.points[j].btn:Hide(); r.points[j].text:Hide()
      end
      r.gears = r.gears or {}
      local gear = route[s.id] or {}
      for j, w in ipairs(gear) do
        local g = r.gears[j]
        if not g then
          g = content:CreateFontString(nil, "ARTWORK", "R2FBodySmall")
          g:SetJustifyH("LEFT")
          g:SetWidth(TEXT_W)
          g.hit = CreateFrame("Frame", nil, content)
          g.hit:SetAllPoints(g)
          g.hit:EnableMouse(true)
          g.hit:SetScript("OnEnter", weaponTip)
          g.hit:SetScript("OnLeave", function() GameTooltip:Hide() end)
          r.gears[j] = g
        end
        g.hit.w = w
        g.hit:Show()
        g:ClearAllPoints()
        g:SetPoint("TOPLEFT", content, "TOPLEFT", 96, -(y + used))
        g:SetText(w.text)
        g:Show()
        used = used + 16
      end
      for j = #gear + 1, #r.gears do r.gears[j]:Hide(); r.gears[j].hit:Hide() end
      y = y + used + 8
    end
  end
  hideRowsFrom(nRow + 1)
  for k = nHead + 1, #headers do headers[k]:Hide() end
  content:SetHeight(math.max(y, 1))
  ui.contentHeight = y
end

-- Quest shopping list: the site's "Buyable quests" (quests whose items can be bought, not farmed),
-- grouped by route phase, each with a tick box (saved per character).
local BUY_W = 390

-- Click an item of the shopping list: a small box with its name selected. Ctrl+C, then paste it into the auction house
-- search. (Our own box only: nothing is written into the game's search field.) It closes when you click elsewhere.
local copyWin, copyEdit

local function showCopy(name)
  if not copyWin then
    local f = UI.DialogFrame("R2FCopyItem", UIParent)
    f:SetSize(330, 96)
    f:SetPoint("CENTER", UIParent, "CENTER", 0, 180)
    f:SetFrameStrata("DIALOG")
    f:SetToplevel(true)
    f:EnableMouse(true)
    f:Hide()
    if UISpecialFrames then table.insert(UISpecialFrames, "R2FCopyItem") end
    local title = f:CreateFontString(nil, "ARTWORK", "R2FHeading")
    title:SetPoint("TOP", 0, -14)
    title:SetText(L.PLAN_COPY_TITLE)
    local box
    box, copyEdit = UI.MultiLineEdit(f, "R2FCopyItemScroll", 290, 24)
    box:SetPoint("TOPLEFT", 18, -36)
    copyEdit:SetScript("OnEscapePressed", function() f:Hide() end)
    copyEdit:SetScript("OnEditFocusLost", function() f:Hide() end)
    local hint = f:CreateFontString(nil, "ARTWORK", "R2FDimSmall")
    hint:SetPoint("BOTTOMLEFT", 20, 12)
    hint:SetWidth(290)
    hint:SetJustifyH("LEFT")
    hint:SetText(L.PLAN_COPY_HINT)
    copyWin = f
  end
  copyWin:Show()
  copyEdit:SetText(name)
  copyEdit:HighlightText()
  copyEdit:SetFocus()
end
Tab.ShowCopy = showCopy

-- Progress string for a duo partner (Progress.lua): "Copy my progress" shows the string to copy; "Compare with partner"
-- takes the partner's string and shows both levels, the level gap and the steps only one of you has done.
-- Read-only: nothing in the game or in our saved ticks is written.
local progWin, progEdit, progOut, progMode

local function stepNames(label, list)
  if #list == 0 then return label .. " " .. L.PROGRESS_NONE end
  local names = {}
  for i = 1, math.min(#list, 4) do names[i] = list[i].t or list[i].id end
  return label .. " " .. table.concat(names, "; ") .. (#list > 4 and (" +" .. (#list - 4)) or "")
end

local function progressText(text)
  local theirs, err = R2F.Progress.Parse(text)
  if not theirs then return err, true end
  local mine = UnitLevel and UnitLevel("player") or 0
  local c = R2F.Progress.Compare(theirs, mine)
  local unknown = L.PROGRESS_UNKNOWN
  return table.concat({
    L.PROGRESS_LEVELS:format(mine > 0 and mine or unknown, theirs.level > 0 and theirs.level or unknown,
      c.levelGap and L.PROGRESS_GAP:format(c.levelGap) or ""),
    L.PROGRESS_COUNTS:format(c.both, #c.onlyMine, #c.onlyTheirs),
    stepNames(L.PROGRESS_ONLY_YOU, c.onlyMine),
    stepNames(L.PROGRESS_ONLY_THEM, c.onlyTheirs),
  }, "\n")
end

local function showProgress(mode)
  if not progWin then
    local f = UI.DialogFrame("R2FProgress", UIParent)
    f:SetSize(370, 230)
    f:SetPoint("CENTER", UIParent, "CENTER", 0, 120)
    f:SetFrameStrata("DIALOG")
    f:SetToplevel(true)
    f:EnableMouse(true)
    f:Hide()
    if UISpecialFrames then table.insert(UISpecialFrames, "R2FProgress") end
    f.title = f:CreateFontString(nil, "ARTWORK", "R2FHeading")
    f.title:SetPoint("TOP", 0, -14)
    local box
    box, progEdit = UI.MultiLineEdit(f, "R2FProgressScroll", 330, 56)
    box:SetPoint("TOPLEFT", 18, -36)
    progEdit:SetScript("OnEscapePressed", function() f:Hide() end)
    progEdit:SetScript("OnEditFocusLost", function() if progMode == "copy" then f:Hide() end end)
    progEdit:SetScript("OnTextChanged", function(self)
      if progMode ~= "paste" then return end
      local text = self:GetText() or ""
      if text:match("^%s*$") then progOut:SetText("") return end
      local msg, isError = progressText(text)
      if isError then progOut:SetTextColor(1, 0.1, 0.1) else R2F.Theme.PaintText(progOut, "body") end
      progOut:SetText(msg)
    end)
    progOut = f:CreateFontString(nil, "ARTWORK", "R2FBodySmall")
    progOut:SetPoint("TOPLEFT", 20, -104)
    progOut:SetWidth(330)
    progOut:SetJustifyH("LEFT")
    f.hint = f:CreateFontString(nil, "ARTWORK", "R2FDimSmall")
    f.hint:SetPoint("BOTTOMLEFT", 20, 12)
    f.hint:SetWidth(330)
    f.hint:SetJustifyH("LEFT")
    progWin = f
  end
  progMode = mode
  progWin:Show()
  progOut:SetText("")
  if mode == "copy" then
    progWin.title:SetText(L.PROGRESS_TITLE_COPY)
    progWin.hint:SetText(L.PROGRESS_COPY_HINT)
    local text, err = R2F.Progress.Export()
    progEdit:SetText(text or err or "")
    progEdit:HighlightText()
  else
    progWin.title:SetText(L.PROGRESS_TITLE_PASTE)
    progWin.hint:SetText(L.PROGRESS_PASTE_HINT)
    progEdit:SetText("")
  end
  progEdit:SetFocus()
end
Tab.ShowProgress = showProgress

local function itemButton(r, j)
  local b = r.itemBtns[j]
  if b then return b end
  b = CreateFrame("Button", nil, content)
  b:SetSize(BUY_W, 15)
  b.text = b:CreateFontString(nil, "ARTWORK", "R2FBodySmall")
  b.text:SetPoint("LEFT", 0, 0)
  b.text:SetJustifyH("LEFT")
  R2F.Theme.PaintText(b.text, "heading")
  -- No direct clipboard call: CopyToClipboard is a Blizzard-only action and the game blocks the addon for using it.
  b:SetScript("OnClick", function(self) if self.itemName then showCopy(self.itemName) end end)
  b:SetScript("OnEnter", function(self)
    R2F.Theme.PaintText(self.text, "body")
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:AddLine(L.PLAN_COPY_TIP:format(self.itemName or ""), 1, 1, 1, true)
    GameTooltip:Show()
  end)
  b:SetScript("OnLeave", function(self) R2F.Theme.PaintText(self.text, "heading") GameTooltip:Hide() end)
  r.itemBtns[j] = b
  return b
end

local function buyRow(i)
  local r = buyRows[i]
  if r then return r end
  r = { itemBtns = {} }
  r.check = UI.CheckButton(content, "")
  r.check:SetScript("OnClick", function(self)
    if self.questId then
      Plan.SetQuestBought(self.questId, not Plan.QuestBought(self.questId))
      Tab.Refresh()
    end
  end)
  r.title = content:CreateFontString(nil, "ARTWORK", "R2FBody")
  r.title:SetJustifyH("LEFT")
  r.title:SetWidth(BUY_W)
  r.note = content:CreateFontString(nil, "ARTWORK", "R2FBodySmall")
  r.note:SetJustifyH("LEFT")
  R2F.Theme.PaintText(r.note, "note")
  r.note:SetWidth(BUY_W)
  buyRows[i] = r
  return r
end

local function hideBuyFrom(i)
  for k = i, #buyRows do
    local r = buyRows[k]
    r.check:Hide(); r.title:Hide(); r.note:Hide()
    for _, b in ipairs(r.itemBtns) do b:Hide() end
  end
end

local function layoutBuy()
  hideRowsFrom(1)
  for k = 1, #headers do headers[k]:Hide() end
  local y, nHead, nRow = 0, 0, 0
  for _, g in ipairs(Plan.QuestGroups()) do
    nHead = nHead + 1
    local h = buyHeaders[nHead]
    if not h then
      h = content:CreateFontString(nil, "ARTWORK", "R2FHeadingLarge")
      buyHeaders[nHead] = h
    end
    h:ClearAllPoints()
    h:SetPoint("TOPLEFT", content, "TOPLEFT", 4, -y)
    h:SetText(g.title)
    h:Show()
    y = y + 28
    for _, q in ipairs(g.quests) do
      nRow = nRow + 1
      local r = buyRow(nRow)
      local bought = Plan.QuestBought(q.id)
      r.check.questId = q.id
      r.check:ClearAllPoints()
      r.check:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -y + 4)
      r.check:SetChecked(bought)
      r.check:Show()
      local head = q.name .. " |cff999999(" .. L.PLAN_BUY_LEVEL:format(q.zone, q.q) .. ")|r"
      if q.st == "verify" then head = head .. " |cffff8040(" .. L.PLAN_BUY_VERIFY .. ")|r" end
      r.title:ClearAllPoints()
      r.title:SetPoint("TOPLEFT", content, "TOPLEFT", 58, -y)
      r.title:SetText(head)
      if bought then R2F.Theme.PaintText(r.title, "dim") else R2F.Theme.PaintText(r.title, "body") end
      r.title:Show()
      local used = math.max(r.title:GetStringHeight(), 14) + 2
      for j, it in ipairs(q.items) do
        local b = itemButton(r, j)
        b.itemName = it[1]
        b.text:SetText(it[2] .. "x " .. it[1])
        b:ClearAllPoints()
        b:SetPoint("TOPLEFT", content, "TOPLEFT", 58, -(y + used))
        b:Show()
        used = used + 15
      end
      for j = #q.items + 1, #r.itemBtns do r.itemBtns[j]:Hide() end
      used = used + 2
      local extra = q.note
      if q.xp then extra = (extra and extra .. " " or "") .. q.xp end
      if extra and extra ~= "" then
        r.note:ClearAllPoints()
        r.note:SetPoint("TOPLEFT", content, "TOPLEFT", 58, -(y + used))
        r.note:SetText(extra)
        r.note:Show()
        used = used + math.max(r.note:GetStringHeight(), 12) + 2
      else
        r.note:Hide()
      end
      y = y + used + 8
    end
  end
  hideBuyFrom(nRow + 1)
  for k = nHead + 1, #buyHeaders do buyHeaders[k]:Hide() end
  content:SetHeight(math.max(y, 1))
  ui.contentHeight = y
end

local function refresh()
  if not visible() then return end
  local planId = Plan.Selected()
  local preview = Plan.Preview()
  local sel = Plan.Parse(preview or planId) or Plan.Parse(Plan.DEFAULT)
  if planId then
    ui.who:SetText(preview and L.PLAN_PREVIEWING:format(Plan.Label(planId)) or Plan.Label(planId))
  else
    ui.who:SetText(L.PLAN_HORDE)
  end
  ui.raceBtn:SetText(L.PLAN_RACE_BTN:format(Plan.RaceLabel(sel.race)))
  ui.classBtn:SetText(L.PLAN_CLASS_BTN:format(Plan.ClassLabel(sel.cls)))
  if preview then ui.mineBtn:Enable() else ui.mineBtn:Disable() end
  ui.follow:SetChecked(Plan.FollowOn())
  ui.buyBtn:SetText(view == "buy" and L.PLAN_BUY_BACK or L.PLAN_BUY_BTN)
  -- As wide as its label: a look's font can be wider than the game's.
  local bfs = ui.buyBtn.GetFontString and ui.buyBtn:GetFontString()
  local bw = bfs and bfs.GetStringWidth and bfs:GetStringWidth() or 0
  ui.buyBtn:SetWidth(math.max(150, math.ceil(bw) + 36))
  if view == "buy" then
    local done, total = Plan.QuestProgress()
    ui.progress:SetText(L.PLAN_BUY_PROGRESS:format(done, total))
    layoutBuy()
    return
  end
  hideBuyFrom(1)
  for k = 1, #buyHeaders do buyHeaders[k]:Hide() end
  local done, total = Plan.Progress(planId)
  ui.progress:SetText(L.PLAN_PROGRESS:format(done, total))
  layout()
end

-- Mouse-wheel scrolling (also the fallback when the scroll template is missing).
local function onWheel(self, delta)
  local maxScroll = math.max((ui.contentHeight or 0) - self:GetHeight(), 0)
  local v = (self:GetVerticalScroll() or 0) - delta * 40
  self:SetVerticalScroll(math.max(0, math.min(v, maxScroll)))
end

-- Called once by MainWindow with the Plan page frame.
function Tab.Build(f)
  page = f
  ui.who = f:CreateFontString(nil, "ARTWORK", "R2FHeading")
  ui.who:SetPoint("TOPLEFT", 28, -50)
  ui.who:SetWidth(300)
  ui.who:SetJustifyH("LEFT")
  ui.follow = UI.CheckButton(f, L.PLAN_FOLLOW)
  ui.follow:SetPoint("TOPLEFT", 340, -52)
  ui.follow:SetScript("OnClick", function(self)
    Plan.SetFollow(self:GetChecked() and true or false)
    Tab.Refresh()
  end)
  ui.follow:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:AddLine(L.PLAN_FOLLOW_TIP, 1, 1, 1, true)
    GameTooltip:Show()
  end)
  ui.follow:SetScript("OnLeave", function() GameTooltip:Hide() end)
  local hint = f:CreateFontString(nil, "ARTWORK", "R2FDimSmall")
  hint:SetPoint("TOPLEFT", 28, -72)
  hint:SetText(L.PLAN_PREVIEW)
  -- Preview buttons: each click picks the next race / class (a class that does not fit the race falls back to its
  -- first), so no dropdown is needed. Saved per character (R2FCharDB.plan.selected); "My character" clears it.
  local function previewButton(x, w, onClick)
    local b = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
    R2F.UI.ThemeButton(b)
    b:SetSize(w, 20)
    b:SetPoint("TOPLEFT", x, -88)
    b:SetScript("OnClick", function()
      onClick()
      scroll:SetVerticalScroll(0)
      Tab.Refresh()
      if R2F.Home and R2F.Home.Refresh then R2F.Home.Refresh() end
    end)
    return b
  end
  ui.raceBtn = previewButton(28, 130, function() Plan.SetPreview(Plan.CycleRace(Plan.Selected())) end)
  ui.classBtn = previewButton(164, 110, function() Plan.SetPreview(Plan.CycleClass(Plan.Selected())) end)
  ui.presetBtn = previewButton(280, 80, function() Plan.SetPreview(Plan.TogglePreset(Plan.Selected())) end)
  ui.presetBtn:SetText(L.PLAN_PRESET_BTN)
  ui.mineBtn = previewButton(366, 100, function() Plan.SetPreview(nil) end)
  ui.mineBtn:SetText(L.PLAN_MINE_BTN)
  ui.progress = f:CreateFontString(nil, "ARTWORK", "R2FBody")
  ui.progress:SetPoint("TOPLEFT", 28, -124)
  ui.buyBtn = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  R2F.UI.ThemeButton(ui.buyBtn)
  ui.buyBtn:SetSize(150, 22)
  ui.buyBtn:SetPoint("TOPRIGHT", f, "TOPRIGHT", -24, -126)
  ui.buyBtn:SetText(L.PLAN_BUY_BTN)
  ui.buyBtn:SetScript("OnClick", function()
    view = view == "buy" and "steps" or "buy"
    scroll:SetVerticalScroll(0)
    Tab.Refresh()
  end)

  -- Progress string row: share my progress with a duo partner / compare with theirs (Progress.lua).
  local function progressButton(x, w, text, mode)
    local b = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
    R2F.UI.ThemeButton(b)
    b:SetSize(w, 20)
    b:SetPoint("TOPLEFT", x, -148)
    b:SetText(text)
    b:SetScript("OnClick", function() showProgress(mode) end)
    return b
  end
  ui.copyBtn = progressButton(28, 150, L.PROGRESS_COPY_BTN, "copy")
  ui.cmpBtn = progressButton(184, 170, L.PROGRESS_PASTE_BTN, "paste")

  scroll = UI.TryTemplate("ScrollFrame", "R2FPlanScroll", f, "UIPanelScrollFrameTemplate",
    function(s) return s.SetScrollChild ~= nil end) or CreateFrame("ScrollFrame", "R2FPlanScrollPlain", f)
  scroll:SetPoint("TOPLEFT", 22, -172)
  scroll:SetSize(CONTENT_W + 8, 290)
  content = CreateFrame("Frame", nil, scroll)
  content:SetSize(CONTENT_W, 10)
  scroll:SetScrollChild(content)
  scroll:EnableMouseWheel(true)
  scroll:SetScript("OnMouseWheel", onWheel)
  return f
end

Tab.Refresh = refresh

-- GET_ITEM_INFO_RECEIVED: a weapon the Plan tab asked for has loaded; redraw once, a moment later (many arrive together).
local pendingInfo = false
function Tab.OnItemInfo()
  if not visible() or pendingInfo then return end
  pendingInfo = true
  local function run() pendingInfo = false; refresh() end
  if C_Timer and C_Timer.After then C_Timer.After(0.5, run) else run() end
end

function Tab.Show()
  R2F.MainWindow.Show("plan")
end
