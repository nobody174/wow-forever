-- UI/DecoBook.lua: the image set "scribe" (Scribe's Tome), a light theme drawn as a leather-bound book.  The window is a
-- leather cover with two parchment pages and a spine between them. The left page is the sidebar, set as a table of contents
-- (group headings "BOOK I - JOURNEY", entries with a dotted leader and a page number, a bookmark flag on the page you are
-- on); the right page holds the tab's page. Art: media/scribe (converted by addon/art/slices_to_tga.py, flagged in
-- Images.lua). Registers with UI/Deco.lua (Deco.extra.scribe); nothing is written into the game's frames.

local _, R2F = ...
local L = R2F.L
local Deco = R2F.Deco

local SC = Deco.IMGROOT .. "scribe\\scribe_"
local ORDER = { home = 1, plan = 2, talents = 3, bis = 4, macros = 5, gameplay = 6 }
local GOLD = { 0.55, 0.4, 0.1 }
local HOVER = { 0.36, 0.2, 0.12 }

local function tile(parent, layer, sub, file, horiz, vert)
  local t = Deco.itex(parent, layer, sub)
  t:SetTexture(file, "REPEAT", "REPEAT")
  if horiz then t:SetHorizTile(true) end
  if vert then t:SetVertTile(true) end
  return t
end

local function anchor(frame, layer, sub)
  local a = frame:CreateTexture(nil, layer or "BACKGROUND", nil, sub or 2)
  a:SetColorTexture(0, 0, 0, 0)
  return a
end

local function setFont(fs, size)
  local th = R2F.Theme.Get()
  local face = th.font and th.font.heading
  if face and fs.SetFont then pcall(fs.SetFont, fs, face, size, "") end
end

local ex = { layout = "toc" }
Deco.extra.scribe = ex

function ex.build(frame, ctx, d)
  local e = { nav = {}, texts = {}, headOrig = {}, topH = ctx.topH }
  d.sc = e
  e.leather = tile(frame, "BACKGROUND", 1, SC .. "leather", true, true)
  e.leather:SetPoint("TOPLEFT", frame, "TOPLEFT", 4, -4)
  e.leather:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -4, 4)
  e.cover = Deco.NineSlice(frame, frame, frame, 32, 0.25, "BORDER", 2, true)
  e.cover.set(SC .. "frame")
  -- The two pages: invisible anchors, the page art over them and a faint parchment grain on top of each.
  e.pageLA, e.pageRA = anchor(frame), anchor(frame)
  e.pageL = Deco.NineSlice(frame, e.pageLA, e.pageLA, 32, 0.25, "BACKGROUND", 3)
  e.pageL.set(SC .. "page")
  e.pageR = Deco.NineSlice(frame, e.pageRA, e.pageRA, 32, 0.25, "BACKGROUND", 3)
  e.pageR.set(SC .. "page")
  e.paperL = tile(frame, "BACKGROUND", 4, SC .. "parchment", true, true)
  e.paperL:SetPoint("TOPLEFT", e.pageLA, "TOPLEFT", 10, -10)
  e.paperL:SetPoint("BOTTOMRIGHT", e.pageLA, "BOTTOMRIGHT", -10, 10)
  e.paperR = tile(frame, "BACKGROUND", 4, SC .. "parchment", true, true)
  e.paperR:SetPoint("TOPLEFT", e.pageRA, "TOPLEFT", 10, -10)
  e.paperR:SetPoint("BOTTOMRIGHT", e.pageRA, "BOTTOMRIGHT", -10, 10)
  e.spine = tile(frame, "BACKGROUND", 5, SC .. "spine", false, true)
  function e.setSide(w)
    e.pageLA:ClearAllPoints()
    e.pageLA:SetPoint("TOPLEFT", frame, "TOPLEFT", 16, -(e.topH + 4))
    e.pageLA:SetPoint("BOTTOMRIGHT", frame, "BOTTOMLEFT", w - 2, 16)
    e.pageRA:ClearAllPoints()
    e.pageRA:SetPoint("TOPLEFT", frame, "TOPLEFT", w + 2, -(e.topH + 4))
    e.pageRA:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -16, 16)
    e.spine:ClearAllPoints()
    e.spine:SetPoint("TOPLEFT", frame, "TOPLEFT", w - 8, -(e.topH + 4))
    e.spine:SetPoint("BOTTOMLEFT", frame, "BOTTOMLEFT", w - 8, 16)
    e.spine:SetWidth(16)
  end
  e.setSide(ctx.sideW)
  -- "Contents" with a rule and a diamond under it, centred on the left page.
  e.contents = frame:CreateFontString(nil, "ARTWORK", "R2FHeadingLarge")
  e.contents:SetPoint("TOP", e.pageLA, "TOP", 0, -24)
  e.contents:SetText(L.SCRIBE_CONTENTS)
  R2F.Theme.PaintText(e.contents, "body")
  e.texts[#e.texts + 1] = e.contents
  e.diamond = Deco.itex(frame, "ARTWORK", 3)
  e.diamond:SetSize(16, 16)
  e.diamond:SetPoint("TOP", e.pageLA, "TOP", 0, -72)
  e.diamond:SetTexture(SC .. "diamond")
  e.ruleL = tile(frame, "ARTWORK", 3, SC .. "rule", true, false)
  e.ruleL:SetSize(130, 8)
  e.ruleL:SetPoint("RIGHT", e.diamond, "LEFT", -6, 0)
  e.ruleR = tile(frame, "ARTWORK", 3, SC .. "rule", true, false)
  e.ruleR:SetSize(130, 8)
  e.ruleR:SetPoint("LEFT", e.diamond, "RIGHT", 6, 0)
  -- Contents lines: a bookmark flag for the page you are on, a dotted leader from the name to the page number.
  for key, b in pairs(ctx.nav) do
    local n = { btn = b, marker = Deco.itex(b, "ARTWORK", 3), leader = tile(b, "ARTWORK", 1, SC .. "leader", true, false) }
    n.marker:SetSize(28, 28)
    n.marker:SetPoint("LEFT", b, "LEFT", -40, 0)
    n.marker:SetTexture(SC .. "marker")
    n.num = b:CreateFontString(nil, "ARTWORK", "R2FBody")
    n.num:SetPoint("RIGHT", b, "RIGHT", -2, 0)
    n.num:SetText(tostring(ORDER[key] or 0))
    n.num:Hide()
    n.leader:SetHeight(8)
    if b.r2fText then n.leader:SetPoint("BOTTOMLEFT", b.r2fText, "BOTTOMRIGHT", 8, 3) end
    n.leader:SetPoint("BOTTOMRIGHT", n.num, "BOTTOMLEFT", -8, 3)
    e.nav[key] = n
    if b.HookScript then
      b:HookScript("OnEnter", function() n.hover = true Deco.RefreshNav() end)
      b:HookScript("OnLeave", function() n.hover = false Deco.RefreshNav() end)
    end
  end
  for i, h in ipairs(ctx.heads) do e.headOrig[i] = h:GetText() end
  e.heads = ctx.heads
end

-- Fonts and texts that are not textures: hidden (and the group headings given back) whenever another look is drawn.
function ex.hide(d)
  local e = d.sc
  if not e then return end
  for _, fs in ipairs(e.texts) do fs:Hide() end
  for _, n in pairs(e.nav) do
    n.num:Hide()
    local hl = n.btn.GetHighlightTexture and n.btn:GetHighlightTexture()
    if hl and hl.SetAlpha then hl:SetAlpha(1) end
  end
  for i, h in ipairs(e.heads) do
    if e.headOrig[i] then h:SetText(e.headOrig[i]) end
  end
end

function ex.closeArt(hot)
  if hot then return SC .. "close_hover" end
  return SC .. "close_normal"
end

function ex.sideWidth(d, w)
  if d.sc then d.sc.setSide(w) end
end

local function show(list, alpha)
  for _, t in ipairs(list) do
    if alpha then t:SetAlpha(alpha) end
    t:Show()
  end
end

function ex.apply(d, _, alpha)
  local e = d.sc
  e.leather:SetAlpha(alpha)
  e.leather:Show()
  show(e.cover.parts)
  show(e.pageL.parts, alpha)
  show(e.pageR.parts, alpha)
  e.paperL:SetAlpha(0.55 * alpha)
  e.paperR:SetAlpha(0.55 * alpha)
  e.paperL:Show()
  e.paperR:Show()
  e.spine:Show()
  e.diamond:Show()
  e.ruleL:Show()
  e.ruleR:Show()
  for _, fs in ipairs(e.texts) do fs:Show() end
  setFont(e.contents, 34)
  for _, n in pairs(e.nav) do
    n.num:Show()
    n.leader:Show()
    local hl = n.btn.GetHighlightTexture and n.btn:GetHighlightTexture()
    if hl and hl.SetAlpha then hl:SetAlpha(0) end
  end
  for i, h in ipairs(e.heads) do
    h:SetText(L.SCRIBE_BOOKS[i] or e.headOrig[i] or "")
    h:SetTextColor(GOLD[1], GOLD[2], GOLD[3])
  end
end

function ex.refreshNav(d, key)
  local e = d.sc
  local th = R2F.Theme.Get()
  for k, n in pairs(e.nav) do
    local sel = k == key
    n.marker:SetShown(sel)
    local c = sel and th.accent or (n.hover and HOVER or th.text)
    if n.btn.r2fText then n.btn.r2fText:SetTextColor(c[1], c[2], c[3]) end
    n.num:SetTextColor(c[1], c[2], c[3])
  end
end
