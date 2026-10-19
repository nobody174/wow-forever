-- UI/ThemePicker.lua: the "Choose a look" gallery (opened from the Theme button on Home).
--
-- One card per look, each with a small picture. Clicking a card tries that look on the main window at once (Theme.Set)
-- and starts an
-- eight second countdown: "Keep this look" makes it stay, "Revert" (or the countdown running out, or closing the
-- gallery) puts the
-- look from before back. "Surprise me" previews a random other look. The gallery wears the look in use: its panel, card
-- frames and
-- text come from that look's own art and colours (a flat panel in the look's colours when it has no art, as Classic does).
-- Only our own frames are touched.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI

local Picker = {}
R2F.ThemePicker = Picker

local IMG = "Interface\\AddOns\\RoadToForever\\media\\"
local PK = IMG .. "picker\\picker_"
local ORDER = { "azeroth", "obsidian", "gnomish", "scribe", "arcane", "forge", "classic" }
local COUNT = 8                 -- seconds before a preview goes back by itself
local CARD_W, CARD_H = 214, 150 -- a card, including the 4 px margin of its art

local frame, panel
local cards = {}
local previewing, revertTo, left, gen = nil, nil, 0, 0

-- A 3 x 3 slice of one texture on `parent`, anchored over `anchor` (not Deco's: those hide whenever a look is drawn).
-- bar.set(file) changes the art, bar.shape(capw, cap) the cut (corner size in px, corner size in texture coordinates).
local function nine(parent, anchor, layer, sub, noCentre)
  local bar = { parts = {} }
  for row = 1, 3 do
    for col = 1, 3 do
      if not (noCentre and row == 2 and col == 2) then
        local t = parent:CreateTexture(nil, layer, nil, sub)
        t:Hide()
        bar.parts[#bar.parts + 1] = { t = t, row = row, col = col }
      end
    end
  end
  function bar.shape(capw, cap)
    local xs = { 0, cap, 1 - cap, 1 }
    for _, p in ipairs(bar.parts) do
      local t, row, col = p.t, p.row, p.col
      t:ClearAllPoints()
      t:SetTexCoord(xs[col], xs[col + 1], xs[row], xs[row + 1])
      if col == 1 then t:SetPoint("LEFT", anchor, "LEFT", 0, 0) t:SetWidth(capw) end
      if col == 3 then t:SetPoint("RIGHT", anchor, "RIGHT", 0, 0) t:SetWidth(capw) end
      if row == 1 then t:SetPoint("TOP", anchor, "TOP", 0, 0) t:SetHeight(capw) end
      if row == 3 then t:SetPoint("BOTTOM", anchor, "BOTTOM", 0, 0) t:SetHeight(capw) end
      if col == 2 then t:SetPoint("LEFT", anchor, "LEFT", capw, 0) t:SetPoint("RIGHT", anchor, "RIGHT", -capw, 0) end
      if row == 2 then t:SetPoint("TOP", anchor, "TOP", 0, -capw) t:SetPoint("BOTTOM", anchor, "BOTTOM", 0, capw) end
    end
  end
  function bar.set(file)
    for _, p in ipairs(bar.parts) do p.t:SetTexture(file) end
  end
  function bar.show(on)
    for _, p in ipairs(bar.parts) do p.t:SetShown(on == true) end
  end
  bar.shape(16, 0.25)
  return bar
end

-- What each look's gallery is made of, by image set: panel layers (bottom to top: file, corner px, corner fraction, no
-- centre, tiled
-- leather fill) and the four card states. A look without an entry (or without its art installed) gets a flat panel in
-- its colours
-- and the plain gold card frames.
local FALLBACK_CARDS = { normal = PK .. "card_normal", hover = PK .. "card_hover", active = PK .. "card_active",
                         preview = PK .. "card_preview", capw = 16, cap = 0.25 }
local CHROME = {
  azeroth = { layers = { { PK .. "panel", 32, 0.25 } }, cards = FALLBACK_CARDS },
  frost = { flat = 0.9, layers = { { IMG .. "frost\\frost_glass", 22, 0.25 }, { IMG .. "frost\\frost_frame", 32, 0.25, true } },
            cards = { normal = IMG .. "frost\\frost_card_normal", hover = IMG .. "frost\\frost_card_highlight",
                      active = IMG .. "frost\\frost_card_highlight", preview = PK .. "card_preview", capw = 32, cap = 0.25 } },
  obsidian = { flat = 1, layers = { { IMG .. "obsidian\\obsidian_plate", 24, 0.1875 },
                                    { IMG .. "obsidian\\obsidian_frame", 24, 0.1875, true } },
               cards = { normal = IMG .. "obsidian\\obsidian_card_info", hover = IMG .. "obsidian\\obsidian_card_info_hover",
                         active = IMG .. "obsidian\\obsidian_card_info_hover", preview = PK .. "card_preview", capw = 16,
                         cap = 0.25 } },
  ember = { flat = 1, layers = { { IMG .. "ember\\ember_plate", 16, 0.25 }, { IMG .. "ember\\ember_frame", 32, 0.25, true } },
            cards = { normal = IMG .. "ember\\ember_gauge", hover = PK .. "card_hover", active = PK .. "card_active",
                      preview = PK .. "card_preview", capw = 16, cap = 0.25 } },
  scribe = { layers = { { IMG .. "scribe\\scribe_leather", 0, 0, false, true }, { IMG .. "scribe\\scribe_frame", 32, 0.25, true },
                        { IMG .. "scribe\\scribe_page", 32, 0.25 } },
             cards = FALLBACK_CARDS },
  gnomish = { layers = { { IMG .. "gnomish\\gnomish_frame", 40, 0.3125 } },
              cards = { normal = IMG .. "gnomish\\gnomish_card_white", hover = IMG .. "gnomish\\gnomish_card_yellow",
                        active = IMG .. "gnomish\\gnomish_card_green", preview = IMG .. "gnomish\\gnomish_card_blue",
                        capw = 24, cap = 0.375 } },
}

local function chromeFor(th)
  return th.deco and R2F.Images and R2F.Images[th.deco] == true and CHROME[th.deco] or nil
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
  local fs = b:CreateFontString(nil, "OVERLAY", "R2FHeadingSmall")
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

-- The panel in the look's own clothes.
local function dress()
  local th = R2F.Theme.Get()
  local c = chromeFor(th)
  for _, set in pairs(panel.sets) do
    local on = c ~= nil and set.spec == c
    for _, bar in ipairs(set.bars) do bar.show(on) end
    if set.leather then set.leather:SetShown(on) end
  end
  local flat = c == nil or c.flat ~= nil
  panel.base:SetShown(flat)
  if flat then
    local bg = th.bg
    panel.base:SetColorTexture(bg[1], bg[2], bg[3], c and c.flat or 0.97)
  end
  for _, line in ipairs(panel.rim) do
    line:SetShown(c == nil)
    line:SetColorTexture(th.rim[1], th.rim[2], th.rim[3], 1)
  end
  local spec = c and c.cards or FALLBACK_CARDS
  panel.cardSpec = spec
  for _, card in pairs(cards) do card.nine.shape(spec.capw, spec.cap) end
  panel.surprise.nine.shape(spec.capw, spec.cap)
end

local function refresh()
  if not frame then return end
  dress()
  local spec = panel.cardSpec
  local cur = R2F.Theme.Get().key
  for key, c in pairs(cards) do
    if previewing == key then
      c.nine.set(spec.preview)
    elseif cur == key then
      c.nine.set(spec.active)
    elseif c.hover then
      c.nine.set(spec.hover)
    else
      c.nine.set(spec.normal)
    end
    c.nine.show(true)
    c.activeBadge:SetShown(cur == key and previewing ~= key)
    c.previewBadge:SetShown(previewing == key)
  end
  panel.surprise.nine.set(panel.surprise.hover and spec.hover or spec.normal)
  panel.surprise.nine.show(true)
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
    if key ~= cur and key ~= previewing and key ~= revertTo then pool[#pool + 1] = key end
  end
  if #pool > 0 then Picker.Preview(pool[math.random(#pool)]) end
end

local function thumbFor(tex, key)
  if key == "azeroth" then tex:SetTexture(PK .. "thumb_azeroth")
  elseif key == "obsidian" then tex:SetTexture(PK .. "thumb_obsidian")
  elseif key == "gnomish" then tex:SetTexture(PK .. "thumb_gnomish")
  elseif key == "scribe" then tex:SetTexture(PK .. "thumb_scribe")
  elseif key == "arcane" then tex:SetTexture(PK .. "thumb_frost")
  elseif key == "forge" then tex:SetTexture(PK .. "thumb_ember")
  else tex:SetColorTexture(0.07, 0.07, 0.09, 1) end
end

local function slot(idx)
  return 30 + ((idx - 1) % 3) * (CARD_W + 4), -100 - math.floor((idx - 1) / 3) * (CARD_H + 6)
end

local function buildCard(parent, key, idx)
  local b = CreateFrame("Button", nil, parent)
  b:SetSize(CARD_W, CARD_H)
  local x, y = slot(idx)
  b:SetPoint("TOPLEFT", parent, "TOPLEFT", x, y)
  local c = { btn = b, key = key }
  c.nine = nine(b, b, "BACKGROUND", 1)
  c.thumb = b:CreateTexture(nil, "ARTWORK")
  c.thumb:SetSize(192, 96)
  c.thumb:SetPoint("TOP", b, "TOP", 0, -11)
  thumbFor(c.thumb, key)
  c.name = b:CreateFontString(nil, "OVERLAY", "R2FBody")
  c.name:SetPoint("BOTTOMLEFT", b, "BOTTOMLEFT", 14, 14)
  c.name:SetText(themeName(key))
  R2F.Theme.PaintText(c.name, "body")
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
  panel = { sets = {} }
  -- Under everything: a flat panel in the look's colours (and a thin rim when the look has no art).
  panel.base = f:CreateTexture(nil, "BACKGROUND", nil, 0)
  panel.base:SetPoint("TOPLEFT", f, "TOPLEFT", 4, -4)
  panel.base:SetPoint("BOTTOMRIGHT", f, "BOTTOMRIGHT", -4, 4)
  panel.rim = {}
  for _, sp in ipairs({ { "TOPLEFT", "TOPRIGHT", true }, { "BOTTOMLEFT", "BOTTOMRIGHT", true },
                        { "TOPLEFT", "BOTTOMLEFT", false }, { "TOPRIGHT", "BOTTOMRIGHT", false } }) do
    local t = f:CreateTexture(nil, "BORDER")
    t:SetPoint(sp[1], f, sp[1], 0, 0)
    t:SetPoint(sp[2], f, sp[2], 0, 0)
    if sp[3] then t:SetHeight(2) else t:SetWidth(2) end
    panel.rim[#panel.rim + 1] = t
  end
  -- One set of art layers per image set that has them.
  for deco, spec in pairs(CHROME) do
    local set = { spec = spec, bars = {} }
    for i, layer in ipairs(spec.layers) do
      if layer[5] then
        set.leather = f:CreateTexture(nil, "BACKGROUND", nil, 1)
        set.leather:SetPoint("TOPLEFT", f, "TOPLEFT", 4, -4)
        set.leather:SetPoint("BOTTOMRIGHT", f, "BOTTOMRIGHT", -4, 4)
        set.leather:SetTexture(layer[1], "REPEAT", "REPEAT")
        set.leather:SetHorizTile(true)
        set.leather:SetVertTile(true)
        set.leather:Hide()
      else
        local bar = nine(f, f, "BACKGROUND", i + 1, layer[4])
        bar.shape(layer[2], layer[3])
        bar.set(layer[1])
        set.bars[#set.bars + 1] = bar
      end
    end
    panel.sets[deco] = set
  end
  local title = f:CreateFontString(nil, "OVERLAY", "R2FHeadingLarge")
  title:SetPoint("TOPLEFT", f, "TOPLEFT", 36, -34)
  title:SetText(L.PICKER_TITLE)
  R2F.Theme.PaintText(title, "heading")
  local sub = f:CreateFontString(nil, "OVERLAY", "R2FBodySmall")
  sub:SetPoint("TOPLEFT", f, "TOPLEFT", 36, -68)
  sub:SetText(L.PICKER_SUB)
  R2F.Theme.PaintText(sub, "note")
  local close = CreateFrame("Button", nil, f)
  close:SetSize(28, 28)
  close:SetPoint("TOPRIGHT", f, "TOPRIGHT", -16, -16)
  close.x = close:CreateFontString(nil, "OVERLAY", "R2FHeadingLarge")
  close.x:SetPoint("CENTER", close, "CENTER", 0, 0)
  close.x:SetText("X")
  R2F.Theme.PaintText(close.x, "heading")
  close:SetScript("OnClick", function() f:Hide() end)
  for i, key in ipairs(ORDER) do buildCard(f, key, i) end
  -- Surprise me: the slot after the last look.
  local sur = CreateFrame("Button", nil, f)
  sur:SetSize(CARD_W, CARD_H)
  local sx, sy = slot(#ORDER + 1)
  sur:SetPoint("TOPLEFT", f, "TOPLEFT", sx, sy)
  sur.nine = nine(sur, sur, "BACKGROUND", 1)
  sur.text = sur:CreateFontString(nil, "OVERLAY", "R2FHeading")
  sur.text:SetPoint("CENTER", sur, "CENTER", 0, 0)
  sur.text:SetText(L.PICKER_SURPRISE)
  R2F.Theme.PaintText(sur.text, "body")
  sur:SetScript("OnClick", function() Picker.Surprise() end)
  sur:SetScript("OnEnter", function() sur.hover = true refresh() end)
  sur:SetScript("OnLeave", function() sur.hover = false refresh() end)
  panel.surprise = sur
  -- The preview panel: what is showing, Keep and Revert.
  local px, py = slot(#ORDER + 2)
  panel.text = f:CreateFontString(nil, "OVERLAY", "R2FBodySmall")
  panel.text:SetPoint("TOPLEFT", f, "TOPLEFT", px + 14, py - 16)
  panel.text:SetWidth(CARD_W - 28)
  panel.text:SetJustifyH("LEFT")
  R2F.Theme.PaintText(panel.text, "body")
  panel.keep = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  panel.keep:SetSize(CARD_W - 28, 24)
  panel.keep:SetPoint("TOPLEFT", f, "TOPLEFT", px + 14, py - 78)
  panel.keep:SetText(L.PICKER_KEEP)
  UI.ThemeButton(panel.keep, true)
  panel.keep:SetScript("OnClick", keep)
  panel.revert = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  panel.revert:SetSize(CARD_W - 28, 24)
  panel.revert:SetPoint("TOPLEFT", f, "TOPLEFT", px + 14, py - 106)
  panel.revert:SetText(L.PICKER_REVERT:format(COUNT))
  UI.ThemeButton(panel.revert)
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

-- The look changed elsewhere (the minimap menu, a command, a preview): redraw the gallery in it.
R2F.Theme.OnChange(function() refresh() end)
