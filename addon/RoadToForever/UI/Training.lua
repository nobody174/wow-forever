-- UI/Training.lua: the Training tab.
--
-- Everything your class trainer teaches next, up to level 60, laid out like the spellbook: a slot with the spell's icon, its
-- name and rank, the cost; hover for the trainer's own tooltip. Three blocks: "Train now" (your level allows it), "Next
-- level" (the next level that brings something) and "Later" (every further level, with a heading each).
--
-- The data is Training.lua's: what each visit to the class trainer saved (R2FCharDB.training). Nothing ships with the addon,
-- so an unvisited trainer, or one with Unavailable hidden, gives a short list; the page says so. Read-only: our own frames
-- and our own tooltip, no game call.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI

local Tab = {}
R2F.TrainingTab = Tab

local COL_W, ROW_H = 252, 46
local VIEW_W, VIEW_H = 506, 450
local ICON_FALLBACK = "Interface\\Icons\\INV_Misc_QuestionMark"

local page, scroll, content, note, empty
local slots, heads = {}, {}

local function showTip(self)
  local e = self.entry
  if not e then return end
  GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
  if type(e.tip) == "table" and #e.tip > 0 then
    for k, line in ipairs(e.tip) do
      local long = #line.l > 40
      local r, g, b = 1, 1, 1
      if k > 1 and long then r, g, b = 1, 0.82, 0 end
      if line.r then
        GameTooltip:AddDoubleLine(line.l, line.r, r, g, b, 1, 1, 1)
      else
        GameTooltip:AddLine(line.l, r, g, b, long)
      end
    end
  else
    GameTooltip:AddLine(e.r ~= "" and (e.n .. " (" .. e.r .. ")") or e.n, 1, 1, 1)
    if (e.cost or 0) > 0 then GameTooltip:AddLine(L.TRAIN_TIP_COST .. " " .. R2F.Gameplay.Money(e.cost), 1, 1, 1) end
  end
  if (e.lvl or 0) > UnitLevel("player") then
    GameTooltip:AddLine(L.TRAIN_TIP_LEVEL:format(e.lvl), 1, 0.2, 0.2)
  end
  GameTooltip:Show()
end

local function slot(i)
  if slots[i] then return slots[i] end
  local b = CreateFrame("Button", nil, content)
  b:SetSize(COL_W, ROW_H)
  b:SetHighlightTexture("Interface\\QuestFrame\\UI-QuestTitleHighlight", "ADD")
  local hl = b.GetHighlightTexture and b:GetHighlightTexture()
  if hl then R2F.Theme.PaintVertex(hl, "highlight") end
  b.icon = b:CreateTexture(nil, "BORDER")
  b.icon:SetSize(34, 34)
  b.icon:SetPoint("LEFT", 6, 0)
  -- The spellbook's own slot frame around the icon.
  local border = b:CreateTexture(nil, "OVERLAY")
  border:SetTexture("Interface\\Buttons\\UI-Quickslot2")
  border:SetSize(60, 60)
  border:SetPoint("CENTER", b.icon, "CENTER", 0, -1)
  b.name = b:CreateFontString(nil, "ARTWORK", "R2FBody")
  b.name:SetPoint("TOPLEFT", b.icon, "TOPRIGHT", 12, 0)
  b.name:SetWidth(COL_W - 62)
  b.name:SetJustifyH("LEFT")
  b.sub = b:CreateFontString(nil, "ARTWORK", "R2FDim")
  b.sub:SetPoint("TOPLEFT", b.name, "BOTTOMLEFT", 0, -2)
  b.sub:SetWidth(COL_W - 62)
  b.sub:SetJustifyH("LEFT")
  b:SetScript("OnEnter", showTip)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
  slots[i] = b
  return b
end

local function head(i)
  if heads[i] then return heads[i] end
  local fs = content:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
  R2F.Theme.PaintText(fs, "group")
  heads[i] = fs
  return fs
end

-- Lay the blocks out; returns the content height used.
local function layout(blocks, level)
  local si, hi, y = 0, 0, -4
  for _, block in ipairs(blocks) do
    hi = hi + 1
    local h = head(hi)
    h:ClearAllPoints()
    h:SetPoint("TOPLEFT", content, "TOPLEFT", 6, y)
    h:SetText(block.title)
    h:Show()
    y = y - 22
    for idx, e in ipairs(block.list) do
      si = si + 1
      local b = slot(si)
      local col = (idx - 1) % 2
      b:ClearAllPoints()
      b:SetPoint("TOPLEFT", content, "TOPLEFT", col * COL_W, y)
      b.entry = e
      b.icon:SetTexture(e.ic or ICON_FALLBACK)
      local trainable = (e.lvl or 0) <= level
      b.name:SetText(e.r ~= "" and (e.n .. " |cff9d9d9d(" .. e.r .. ")|r") or e.n)
      b.name:SetFontObject(trainable and "R2FHeading" or "R2FDim")
      local parts = {}
      if not trainable then parts[#parts + 1] = L.TRAIN_PAGE_LEVEL:format(e.lvl or 0) end
      if (e.cost or 0) > 0 then parts[#parts + 1] = R2F.Gameplay.Money(e.cost) end
      b.sub:SetText(table.concat(parts, "   "))
      b.icon:SetDesaturated(not trainable)
      b:Show()
      if col == 1 or idx == #block.list then y = y - ROW_H end
    end
    y = y - 10
  end
  for k = si + 1, #slots do slots[k]:Hide() slots[k].entry = nil end
  for k = hi + 1, #heads do heads[k]:Hide() end
  return -y + 4
end

function Tab.Refresh()
  if not page then return end
  local level = UnitLevel("player")
  local now, nextList, nextLevel, later, known = R2F.Training.Upcoming(level)
  local blocks = {}
  if #now > 0 then blocks[#blocks + 1] = { title = L.TRAIN_PAGE_NOW, list = now } end
  if nextLevel and #nextList > 0 then blocks[#blocks + 1] = { title = L.TRAIN_PAGE_NEXT:format(nextLevel), list = nextList } end
  -- A heading over the "later" levels, once, when something came before it.
  if #later > 0 and #blocks > 0 then blocks[#blocks + 1] = { title = L.TRAIN_PAGE_LATER, list = {} } end
  for _, grp in ipairs(later) do
    blocks[#blocks + 1] = { title = L.TRAIN_PAGE_LEVEL:format(grp.lvl), list = grp.list }
  end
  local height = layout(blocks, level)
  content:SetHeight(math.max(height, VIEW_H))
  empty:SetShown(#blocks == 0)
  local d = R2F.Library.cdb.training
  if known and d.when and d.when > 0 then
    note:SetText(L.TRAIN_PAGE_NOTE:format(date and date("%Y-%m-%d", d.when) or ""))
  else
    note:SetText("")
  end
  scroll:SetVerticalScroll(0)
end

local function onWheel(self, delta)
  local max = math.max(0, content:GetHeight() - VIEW_H)
  self:SetVerticalScroll(math.max(0, math.min(max, (self:GetVerticalScroll() or 0) - delta * 46)))
end

function Tab.Build(f)
  if page then return end
  page = f
  note = f:CreateFontString(nil, "ARTWORK", "R2FDim")
  note:SetPoint("BOTTOMLEFT", f, "BOTTOMLEFT", 10, 6)
  scroll = UI.TryTemplate("ScrollFrame", "R2FTrainingScroll", f, "UIPanelScrollFrameTemplate",
    function(s) return s.SetScrollChild ~= nil end) or CreateFrame("ScrollFrame", "R2FTrainingScrollPlain", f)
  scroll:SetPoint("TOPLEFT", 6, -4)
  scroll:SetSize(VIEW_W, VIEW_H)
  content = CreateFrame("Frame", nil, scroll)
  content:SetSize(VIEW_W - 6, VIEW_H)
  scroll:SetScrollChild(content)
  scroll:EnableMouseWheel(true)
  scroll:SetScript("OnMouseWheel", onWheel)
  empty = f:CreateFontString(nil, "ARTWORK", "R2FBody")
  empty:SetPoint("TOPLEFT", f, "TOPLEFT", 20, -30)
  empty:SetWidth(VIEW_W - 40)
  empty:SetJustifyH("LEFT")
  empty:SetText(L.TRAIN_PAGE_EMPTY)
  empty:Hide()
end

function Tab.Frame() return page end
