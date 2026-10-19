-- UI/ThemePicker.lua: the "Choose a look" gallery (opened from the Theme button on Home).  One card per look, each with a
-- small picture. Clicking a card tries that look on the main window at once (Theme.Set) and starts an eight second countdown:
-- "Keep this look" makes it stay, "Revert" (or the countdown running out, or closing the gallery) puts the look from before
-- back. "Surprise me" previews a random other look. The gallery draws itself in fixed colours (the dark gold panel of
-- media/picker), whatever look the window has. Only our own frames are touched.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI

local Picker = {}
R2F.ThemePicker = Picker

local PK = "Interface\\AddOns\\RoadToForever\\media\\picker\\picker_"
local ORDER = { "azeroth", "obsidian", "gnomish", "scribe", "arcane", "forge", "classic" }
local COUNT = 8                 -- seconds before a preview goes back by itself
local CARD_W, CARD_H = 214, 150 -- a card, including the 4 px margin of its art
local GOLD, CREAM = { 0.95, 0.78, 0.36 }, { 0.93, 0.88, 0.75 }

local frame, panel
local cards = {}
local previewing, revertTo, left, gen = nil, nil, 0, 0

-- A 3 x 3 slice of one texture on `parent`, anchored over `anchor` (not Deco's: those hide whenever a look is drawn).
local function nine(parent, anchor, capw, cap, layer, sub)
  local bar = { parts = {} }
  local xs = { 0, cap, 1 - cap, 1 }
  for row = 1, 3 do
    for col = 1, 3 do
      local t = parent:CreateTexture(nil, layer, nil, sub)
      t:SetTexCoord(xs[col], xs[col + 1], xs[row], xs[row + 1])
      if col == 1 then t:SetPoint("LEFT", anchor, "LEFT", 0, 0) t:SetWidth(capw) end
      if col == 3 then t:SetPoint("RIGHT", anchor, "RIGHT", 0, 0) t:SetWidth(capw) end
      if row == 1 then t:SetPoint("TOP", anchor, "TOP", 0, 0) t:SetHeight(capw) end
      if row == 3 then t:SetPoint("BOTTOM", anchor, "BOTTOM", 0, 0) t:SetHeight(capw) end
      if col == 2 then t:SetPoint("LEFT", anchor, "LEFT", capw, 0) t:SetPoint("RIGHT", anchor, "RIGHT", -capw, 0) end
      if row == 2 then t:SetPoint("TOP", anchor, "TOP", 0, -capw) t:SetPoint("BOTTOM", anchor, "BOTTOM", 0, capw) end
      bar.parts[#bar.parts + 1] = t
    end
  end
  function bar.set(file)
    for _, t in ipairs(bar.parts) do t:SetTexture(file) end
  end
  return bar
end

-- A badge plate: left cap, stretchy middle, right cap (16 px caps of a 64 px wide texture), with its text.
local function badge(parent, file, text)
  local b = CreateFrame("Frame", nil, parent)
  b:SetSize(96, 24)
  local l, m, r = b:CreateTexture(nil, "ARTWORK"), b:CreateTexture(nil, "ARTWORK"), b:CreateTexture(nil, "ARTWORK")
  l:SetPoint("TOPLEFT", b, "TOPLEFT", 0, 4)
  l:SetPoint("BOTTOMLEFT", b, "BOTTOMLEFT", 0, -4)
  l:SetWidth(16)
  l:SetTexCoord(0, 0.25, 0, 1)
  r:SetPoint("TOPRIGHT", b, "TOPRIGHT", 0, 4)
  r:SetPoint("BOTTOMRIGHT", b, "BOTTOMRIGHT", 0, -4)
  r:SetWidth(16)
  r:SetTexCoord(0.75, 1, 0, 1)
  m:SetPoint("TOPLEFT", l, "TOPRIGHT", 0, 0)
  m:SetPoint("BOTTOMRIGHT", r, "BOTTOMLEFT", 0, 0)
  m:SetTexCoord(0.25, 0.75, 0, 1)
  for _, t in ipairs({ l, m, r }) do t:SetTexture(file) end
  local fs = b:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  fs:SetPoint("CENTER", b, "CENTER", 0, 0)
  fs:SetText(text)
  fs:SetTextColor(0.1, 0.08, 0.05)
  b:Hide()
  return b
end

local function themeName(key)
  return R2F.Theme.Get(key).name
end

local function stop() gen = gen + 1 end

local function refresh()
  if not frame then return end
  local cur = R2F.Theme.Get().key
  for key, c in pairs(cards) do
    if previewing == key then
      c.nine.set(PK .. "card_preview")
    elseif cur == key then
      c.nine.set(PK .. "card_active")
    elseif c.hover then
      c.nine.set(PK .. "card_hover")
    else
      c.nine.set(PK .. "card_normal")
    end
    c.activeBadge:SetShown(cur == key and previewing ~= key)
    c.previewBadge:SetShown(previewing == key)
  end
  local show = previewing ~= nil
  panel.keep:SetShown(show)
  panel.revert:SetShown(show)
  if show then
    panel.text:SetText(L.PICKER_SHOWING:format(themeName(previewing), themeName(revertTo)))
    panel.revert:SetText(L.PICKER_REVERT:format(left))
  else
    panel.text:SetText(L.PICKER_IDLE)
  end
end

local function revert()
  stop()
  local back = revertTo
  previewing, revertTo = nil, nil
  if back then R2F.Theme.Set(back) end
  refresh()
end

local function keep()
  stop()
  previewing, revertTo = nil, nil
  refresh()
end

local function tick(g)
  if g ~= gen or not previewing then return end
  left = left - 1
  if left <= 0 then
    revert()
  else
    refresh()
    C_Timer.After(1, function() tick(g) end)
  end
end

-- Try a look on the window and start the countdown.
function Picker.Preview(key)
  if not R2F.Theme.IsValid(key) then return end
  local cur = R2F.Theme.Get().key
  if previewing and key == revertTo then return revert() end
  if not previewing then
    if key == cur then return end
    revertTo = cur
  end
  previewing = key
  R2F.Theme.Set(key)
  stop()
  left = COUNT
  refresh()
  if C_Timer and C_Timer.After then
    local g = gen
    C_Timer.After(1, function() tick(g) end)
  end
end

function Picker.Surprise()
  local cur = R2F.Theme.Get().key
  local pool = {}
  for _, key in ipairs(ORDER) do
    if key ~= cur and key ~= previewing then pool[#pool + 1] = key end
  end
  if #pool > 0 then Picker.Preview(pool[math.random(#pool)]) end
end

local THUMB = { azeroth = "thumb_azeroth", obsidian = "thumb_obsidian", gnomish = "thumb_gnomish", scribe = "thumb_scribe",
                arcane = "thumb_frost", forge = "thumb_ember" }

local function buildCard(parent, key, idx)
  local b = CreateFrame("Button", nil, parent)
  b:SetSize(CARD_W, CARD_H)
  b:SetPoint("TOPLEFT", parent, "TOPLEFT", 30 + ((idx - 1) % 3) * (CARD_W + 4), -100 - math.floor((idx - 1) / 3) * (CARD_H + 6))
  local c = { btn = b, key = key }
  c.nine = nine(b, b, 16, 0.25, "BACKGROUND", 1)
  c.nine.set(PK .. "card_normal")
  c.thumb = b:CreateTexture(nil, "ARTWORK")
  c.thumb:SetSize(192, 96)
  c.thumb:SetPoint("TOP", b, "TOP", 0, -11)
  if THUMB[key] == "thumb_azeroth" then c.thumb:SetTexture(PK .. "thumb_azeroth")
  elseif THUMB[key] == "thumb_obsidian" then c.thumb:SetTexture(PK .. "thumb_obsidian")
  elseif THUMB[key] == "thumb_gnomish" then c.thumb:SetTexture(PK .. "thumb_gnomish")
  elseif THUMB[key] == "thumb_scribe" then c.thumb:SetTexture(PK .. "thumb_scribe")
  elseif THUMB[key] == "thumb_frost" then c.thumb:SetTexture(PK .. "thumb_frost")
  elseif THUMB[key] == "thumb_ember" then c.thumb:SetTexture(PK .. "thumb_ember")
  else c.thumb:SetColorTexture(0.07, 0.07, 0.09, 1) end
  c.name = b:CreateFontString(nil, "OVERLAY", "GameFontNormal")
  c.name:SetPoint("BOTTOMLEFT", b, "BOTTOMLEFT", 14, 14)
  c.name:SetText(themeName(key))
  c.name:SetTextColor(CREAM[1], CREAM[2], CREAM[3])
  c.activeBadge = badge(b, PK .. "badge_gold", L.PICKER_ACTIVE)
  c.activeBadge:SetPoint("TOPRIGHT", b, "TOPRIGHT", -12, -14)
  c.previewBadge = badge(b, PK .. "badge_cyan", L.PICKER_PREVIEWING)
  c.previewBadge:SetPoint("TOPRIGHT", b, "TOPRIGHT", -12, -14)
  b:SetScript("OnClick", function() Picker.Preview(key) end)
  b:SetScript("OnEnter", function() c.hover = true refresh() end)
  b:SetScript("OnLeave", function() c.hover = false refresh() end)
  cards[key] = c
  return c
end

local function build()
  local f = UI.FlatWindow("R2FThemePicker", 700, 640, nil)
  f:SetFrameStrata("DIALOG")
  if f.SetBackdropColor then f:SetBackdropColor(0, 0, 0, 0) end
  if f.SetBackdropBorderColor then f:SetBackdropBorderColor(1, 1, 1, 0) end
  nine(f, f, 32, 0.25, "BACKGROUND", 1).set(PK .. "panel")
  local title = f:CreateFontString(nil, "OVERLAY", "GameFontNormalHuge")
  title:SetPoint("TOPLEFT", f, "TOPLEFT", 36, -34)
  title:SetText(L.PICKER_TITLE)
  title:SetTextColor(GOLD[1], GOLD[2], GOLD[3])
  local sub = f:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
  sub:SetPoint("TOPLEFT", f, "TOPLEFT", 36, -68)
  sub:SetText(L.PICKER_SUB)
  sub:SetTextColor(CREAM[1], CREAM[2], CREAM[3])
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton")
  close:SetPoint("TOPRIGHT", f, "TOPRIGHT", -14, -14)
  for i, key in ipairs(ORDER) do buildCard(f, key, i) end
  -- Surprise me: the eighth slot.
  local sur = CreateFrame("Button", nil, f)
  sur:SetSize(CARD_W, CARD_H)
  sur:SetPoint("TOPLEFT", f, "TOPLEFT", 30 + ((#ORDER) % 3) * (CARD_W + 4), -100 - math.floor(#ORDER / 3) * (CARD_H + 6))
  sur.nine = nine(sur, sur, 16, 0.25, "BACKGROUND", 1)
  sur.nine.set(PK .. "card_normal")
  sur.text = sur:CreateFontString(nil, "OVERLAY", "GameFontNormal")
  sur.text:SetPoint("CENTER", sur, "CENTER", 0, 0)
  sur.text:SetText(L.PICKER_SURPRISE)
  sur.text:SetTextColor(CREAM[1], CREAM[2], CREAM[3])
  sur:SetScript("OnClick", function() Picker.Surprise() end)
  sur:SetScript("OnEnter", function() sur.nine.set(PK .. "card_hover") end)
  sur:SetScript("OnLeave", function() sur.nine.set(PK .. "card_normal") end)
  f.r2fSurprise = sur
  -- The preview panel: what is showing, Keep and Revert.
  panel = { }
  panel.text = f:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
  panel.text:SetPoint("TOPLEFT", f, "TOPLEFT", 30 + 2 * (CARD_W + 4) + 14, -100 - 2 * (CARD_H + 6) - 16)
  panel.text:SetWidth(CARD_W - 28)
  panel.text:SetJustifyH("LEFT")
  panel.text:SetTextColor(CREAM[1], CREAM[2], CREAM[3])
  panel.keep = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  panel.keep:SetSize(CARD_W - 28, 24)
  panel.keep:SetPoint("TOPLEFT", f, "TOPLEFT", 30 + 2 * (CARD_W + 4) + 14, -100 - 2 * (CARD_H + 6) - 78)
  panel.keep:SetText(L.PICKER_KEEP)
  panel.keep:SetScript("OnClick", keep)
  panel.revert = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  panel.revert:SetSize(CARD_W - 28, 24)
  panel.revert:SetPoint("TOPLEFT", f, "TOPLEFT", 30 + 2 * (CARD_W + 4) + 14, -100 - 2 * (CARD_H + 6) - 106)
  panel.revert:SetText(L.PICKER_REVERT:format(COUNT))
  panel.revert:SetScript("OnClick", revert)
  -- Closing the gallery while a look is only being tried puts the old one back.
  f:SetScript("OnHide", function() if previewing then revert() end end)
  f:SetScript("OnShow", refresh)
  frame = f
  refresh()
  return f
end

function Picker.Frame() return frame end

function Picker.Show()
  if not frame then build() end
  if not frame:IsShown() then frame:Show() end
  refresh()
end

function Picker.Toggle()
  if frame and frame:IsShown() then frame:Hide() else Picker.Show() end
end

-- The look changed elsewhere (the minimap menu, a command): redraw the cards.
R2F.Theme.OnChange(function() refresh() end)
