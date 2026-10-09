-- UI/Plan.lua: the Plan tab of the main window (ADDON_PLAN.md 15.5, v0.18.0).
--
--   Group plan picker (the site's four plans) -> progress line -> a scrolling list of
--   the launch-day steps grouped by phase. Each step: a tick box (saved per character),
--   the level, the title with its tags, the note, and one line per waypoint:
--     exact            [Waypoint]  label
--     classic / approx [Waypoint]  label  (may have moved)
--     check            label  (position not known yet)   -- no button
--   With TomTom loaded the button sets a TomTom waypoint; without it, it prints the
--   /way line to chat (Plan.Waypoint).
-- The list is redrawn from the data every time (a few dozen rows): row frames are
-- pooled, heights come from the wrapped text so notes of any length fit.
-- Everything here only writes SavedVariables or calls map getters / TomTom, so it all
-- stays usable in combat.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI
local Plan = R2F.Plan

local Tab = {}
R2F.PlanTab = Tab

local page, scroll, content
local ui = {}
local picks = {}      -- plan id -> radio button
local headers = {}    -- pooled phase heading font strings
local rows = {}       -- pooled step rows

local CONTENT_W = 440
local TEXT_W = 360

local function visible()
  return page ~= nil and page:IsVisible()
end

-- A pooled phase heading.
local function header(i)
  local h = headers[i]
  if not h then
    h = content:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
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
  r.lvl = content:CreateFontString(nil, "ARTWORK", "GameFontNormalSmall")
  r.lvl:SetJustifyH("LEFT")
  r.lvl:SetWidth(46)
  r.title = content:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  r.title:SetJustifyH("LEFT")
  r.title:SetWidth(TEXT_W)
  r.note = content:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  r.note:SetJustifyH("LEFT")
  r.note:SetTextColor(0.7, 0.7, 0.7)
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
  p.btn:SetSize(96, 18)
  p.btn:SetScript("OnClick", function(self)
    if self.point then Plan.Waypoint(self.point) end
  end)
  p.text = content:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  p.text:SetJustifyH("LEFT")
  p.text:SetWidth(TEXT_W - 100)
  r.points[j] = p
  return p
end

local function hideRowsFrom(i)
  for k = i, #rows do
    local r = rows[k]
    r.check:Hide(); r.lvl:Hide(); r.title:Hide(); r.note:Hide()
    for _, p in ipairs(r.points) do p.btn:Hide(); p.text:Hide() end
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
  local tomtom = Plan.HasTomTom()
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
      r.lvl:SetPoint("TOPLEFT", content, "TOPLEFT", 28, -y - 3)
      r.lvl:SetText(s.lvl or "")
      r.lvl:Show()
      r.title:ClearAllPoints()
      r.title:SetPoint("TOPLEFT", content, "TOPLEFT", 78, -y)
      r.title:SetText(titleWithTags(s))
      if Plan.IsDone(s.id) then r.title:SetTextColor(0.5, 0.5, 0.5) else r.title:SetTextColor(1, 1, 1) end
      r.title:Show()
      local used = math.max(r.title:GetStringHeight(), 14) + 2
      if s.n and s.n ~= "" then
        r.note:ClearAllPoints()
        r.note:SetPoint("TOPLEFT", content, "TOPLEFT", 78, -(y + used))
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
          p.text:SetPoint("TOPLEFT", content, "TOPLEFT", 78, py - 2)
          text = text .. " |cffff8040(" .. L.PLAN_UNKNOWN_POS .. ")|r"
        else
          p.btn.point = pt
          p.btn:SetText(tomtom and L.PLAN_WAYPOINT or L.PLAN_WAYLINE_BTN)
          p.btn:ClearAllPoints()
          p.btn:SetPoint("TOPLEFT", content, "TOPLEFT", 78, py)
          p.btn:Show()
          p.text:ClearAllPoints()
          p.text:SetPoint("TOPLEFT", content, "TOPLEFT", 78 + 100, py - 2)
          if Plan.MayHaveMoved(pt) then text = text .. " |cff999999(" .. L.PLAN_MAY_MOVE .. ")|r" end
        end
        p.text:SetText(text)
        p.text:Show()
        used = used + 22
      end
      for j = #pts + 1, #r.points do
        r.points[j].btn:Hide(); r.points[j].text:Hide()
      end
      y = y + used + 8
    end
  end
  hideRowsFrom(nRow + 1)
  for k = nHead + 1, #headers do headers[k]:Hide() end
  content:SetHeight(math.max(y, 1))
  ui.contentHeight = y
end

local function refresh()
  if not visible() then return end
  local planId = Plan.Selected()
  for id, b in pairs(picks) do b:SetChecked(id == planId) end
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
  local pick = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  pick:SetPoint("TOPLEFT", 28, -52)
  pick:SetText(L.PLAN_PICK)
  for i, id in ipairs(Plan.Order()) do
    local b = UI.CheckButton(f, Plan.Label(id), true)
    local col, rowN = (i - 1) % 2, math.floor((i - 1) / 2)
    b:SetPoint("TOPLEFT", 36 + col * 240, -74 - rowN * 22)
    b:SetScript("OnClick", function()
      Plan.Select(id)
      scroll:SetVerticalScroll(0)
      Tab.Refresh()
      if R2F.Home and R2F.Home.Refresh then R2F.Home.Refresh() end
    end)
    picks[id] = b
  end
  ui.progress = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  ui.progress:SetPoint("TOPLEFT", 28, -124)

  scroll = UI.TryTemplate("ScrollFrame", "R2FPlanScroll", f, "UIPanelScrollFrameTemplate",
    function(s) return s.SetScrollChild ~= nil end) or CreateFrame("ScrollFrame", "R2FPlanScrollPlain", f)
  scroll:SetPoint("TOPLEFT", 22, -146)
  scroll:SetSize(CONTENT_W + 8, 316)
  content = CreateFrame("Frame", nil, scroll)
  content:SetSize(CONTENT_W, 10)
  scroll:SetScrollChild(content)
  scroll:EnableMouseWheel(true)
  scroll:SetScript("OnMouseWheel", onWheel)
  return f
end

Tab.Refresh = refresh

function Tab.Show()
  R2F.MainWindow.Show("plan")
end
