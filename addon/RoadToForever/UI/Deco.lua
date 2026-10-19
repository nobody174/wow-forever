-- UI/Deco.lua: theme decoration drawn from coloured rectangles and one round dot texture (no image files).
--
-- Today one decoration exists, "azeroth" (Azeroth Reforged): a stone-coloured gradient panel, a gold double frame line,
-- round corner gems, a banner behind the window title, gradient "stone" navigation buttons with a gem, group headings with
-- a fading gold underline and a darker inset behind the pages. Every piece is a texture on our own main window; Deco.Apply
-- shows them for a theme with `deco = "azeroth"` and hides them for any other. Nothing is written into the game's frames.
-- Gradients use Texture:SetGradient (guarded: without it the piece is flat, in the middle colour).

local _, R2F = ...
local L = R2F.L

local Deco = {}
R2F.Deco = Deco

local DOT = "Interface\\AddOns\\RoadToForever\\media\\dot"

-- Further image sets live in their own files (UI/DecoBook.lua, UI/DecoToy.lua) and register here: Deco.extra[set] = { layout,
-- build, apply, refreshNav }. build(frame, ctx, d) runs once with the window, apply(d, th, alpha) shows the set's pieces,
-- refreshNav(d, key) repaints the navigation for the selected key.
Deco.extra = {}

local pieces = {}        -- every texture we made, to show / hide together
local built
local selectedKey

local function tex(parent, layer, sub)
  local t = parent:CreateTexture(nil, layer or "BACKGROUND", nil, sub or 0)
  pieces[#pieces + 1] = t
  t:Hide()
  return t
end

local function flat(t, c, a)
  t:SetColorTexture(c[1], c[2], c[3], a or 1)
end

-- orientation "VERTICAL" (lo = bottom, hi = top) or "HORIZONTAL" (lo = left, hi = right); alphas optional.
local function gradient(t, orientation, lo, hi, alo, ahi)
  local function middle()
    flat(t, { (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2, (lo[3] + hi[3]) / 2 }, ((alo or 1) + (ahi or 1)) / 2)
  end
  if not (t.SetGradient and _G.CreateColor) then return middle() end
  local ok = pcall(function()
    t:SetColorTexture(1, 1, 1, 1)
    t:SetGradient(orientation, _G.CreateColor(lo[1], lo[2], lo[3], alo or 1), _G.CreateColor(hi[1], hi[2], hi[3], ahi or 1))
  end)
  if not ok then middle() end
end

-- Four thin lines forming a box `inset` px inside `rel`'s edge. The textures belong to `frame` (a region cannot own a texture);
-- `rel` is the frame or texture they are anchored to. Returns them as a list.
local function box(frame, rel, inset, thickness, layer, sub)
  local out = {}
  local spec = {
    { "TOPLEFT", inset, -inset, "TOPRIGHT", -inset, -inset, true },
    { "BOTTOMLEFT", inset, inset, "BOTTOMRIGHT", -inset, inset, true },
    { "TOPLEFT", inset, -inset, "BOTTOMLEFT", inset, inset, false },
    { "TOPRIGHT", -inset, -inset, "BOTTOMRIGHT", -inset, inset, false },
  }
  for _, sp in ipairs(spec) do
    local t = tex(frame, layer, sub)
    t:SetPoint(sp[1], rel, sp[1], sp[2], sp[3])
    t:SetPoint(sp[4], rel, sp[4], sp[5], sp[6])
    if sp[7] then t:SetHeight(thickness) else t:SetWidth(thickness) end
    out[#out + 1] = t
  end
  return out
end

-- ---------------------------------------------------------------------------
-- Image mode: the exported slices of media/azeroth (converted by addon/art/slices_to_tga.py, flagged in Images.lua). Used when
-- R2F.Images.azeroth is true; without them every piece above is drawn from rectangles as before. Sizes of the art: corner 64x64
-- (frame depth 16, gem socket centre at 10, 10), edge strips 64x16 / 16x64, gem 32x32, banner 256x64, buttons 128x32 with
-- 16 px caps, slider track 128x16 with 8 px caps, knob 32x32, divider 128x8, tiles 256x256.
-- ---------------------------------------------------------------------------
local IMG = "Interface\\AddOns\\RoadToForever\\media\\azeroth\\"
local IMGROOT = "Interface\\AddOns\\RoadToForever\\media\\"
-- Art of the shared pieces (buttons, switches, check boxes, sliders) of the image set in use (azeroth until another is chosen).
-- Sets whose art names a shared piece differently: shared name -> file name (without the set prefix).
local ALIAS = {
  scribe = { btn_normal = "btn_stamp", btn_hover = "btn_stamp_hover", btn_primary = "btn_seal",
             btn_primary_hover = "btn_seal_hover", btn_disabled = "btn_off" },
  gnomish = { btn_hover = "btn_normal_hover", btn_disabled = "btn_off" },
}
local function P(name)
  local set = Deco.set or "azeroth"
  local a = ALIAS[set]
  return IMGROOT .. set .. "\\" .. set .. "_" .. ((a and a[name]) or name)
end
Deco.P = P
local imgPieces = {}
local BTN_CAP = 16 / 128          -- cap width in texture coordinates
local TRACK_CAP = 8 / 128

-- Per image set: how the three-part pieces are cut and how thick the slider groove is. `pad` = how far the art of a button
-- reaches beyond the button (Obsidian's glow sits in a 3 px margin of the art).
local SHAPE = {
  azeroth = { btnCap = 16 / 128, btnCapW = 16, pad = 0, groove = 10, knob = { 22, 22 } },
  ember = { btnCap = 16 / 128, btnCapW = 16, pad = 0, groove = 12, knob = { 32, 22 }, twoKnobs = true, clipFill = true,
            plate = true },
  obsidian = { btnCap = 12 / 128, btnCapW = 12, pad = 3, groove = 16, knob = { 26, 26 }, twoKnobs = true, plate = true },
  frost = { btnCap = 16 / 128, btnCapW = 16, pad = 3, groove = 16, knob = { 28, 28 }, twoKnobs = true, clipFill = true,
            plate = true },
  -- Light sets: `primaryText` is the label colour on the primary button's art.
  scribe = { btnCap = 16 / 128, btnCapW = 16, pad = 0, groove = 6, knob = { 32, 32 }, twoKnobs = true, clipFill = true,
             primaryText = { 0.97, 0.93, 0.84 } },
  gnomish = { btnCap = 16 / 128, btnCapW = 16, pad = 0, groove = 9, knob = { 32, 32 }, twoKnobs = true, clipFill = true,
              primaryText = { 0.29, 0.208, 0.141 } },
}
local function shape() return SHAPE[Deco.set or "azeroth"] end
Deco.shape = shape

local function itex(parent, layer, sub)
  local t = parent:CreateTexture(nil, layer or "BACKGROUND", nil, sub or 0)
  imgPieces[#imgPieces + 1] = t
  t:Hide()
  return t
end

Deco.itex = itex
Deco.IMGROOT = IMGROOT

-- The image set of a theme (its `deco` token) when the slices of that set are installed, else nil.
local function imageSet(th)
  if th.deco and R2F.Images and R2F.Images[th.deco] == true then return th.deco end
  return nil
end

-- A three-part bar (left cap, stretchy middle, right cap) on `parent`, filled from one texture file; `capw` is the cap's
-- display width in px, `cap` its width in texture coordinates. Returns { parts, set = function(file) }.
local function threeSlice(parent, layer, sub, capw, cap, rel)
  rel = rel or parent
  local l, m, r = itex(parent, layer, sub), itex(parent, layer, sub), itex(parent, layer, sub)
  l:SetPoint("TOPLEFT", rel, "TOPLEFT", 0, 0)
  l:SetPoint("BOTTOMLEFT", rel, "BOTTOMLEFT", 0, 0)
  l:SetWidth(capw)
  l:SetTexCoord(0, cap, 0, 1)
  r:SetPoint("TOPRIGHT", rel, "TOPRIGHT", 0, 0)
  r:SetPoint("BOTTOMRIGHT", rel, "BOTTOMRIGHT", 0, 0)
  r:SetWidth(capw)
  r:SetTexCoord(1 - cap, 1, 0, 1)
  m:SetPoint("TOPLEFT", l, "TOPRIGHT", 0, 0)
  m:SetPoint("BOTTOMRIGHT", r, "BOTTOMLEFT", 0, 0)
  m:SetTexCoord(cap, 1 - cap, 0, 1)
  local bar = { parts = { l, m, r } }
  function bar.set(file)
    for _, t in ipairs(bar.parts) do t:SetTexture(file) end
  end
  -- Cut the caps differently (texture coordinates, display width) and let the art reach `pad` px beyond the parent.
  function bar.shape(newCap, newCapW, pad)
    pad = pad or 0
    l:ClearAllPoints()
    l:SetPoint("TOPLEFT", parent, "TOPLEFT", -pad, pad)
    l:SetPoint("BOTTOMLEFT", parent, "BOTTOMLEFT", -pad, -pad)
    l:SetWidth(newCapW)
    l:SetTexCoord(0, newCap, 0, 1)
    r:ClearAllPoints()
    r:SetPoint("TOPRIGHT", parent, "TOPRIGHT", pad, pad)
    r:SetPoint("BOTTOMRIGHT", parent, "BOTTOMRIGHT", pad, -pad)
    r:SetWidth(newCapW)
    r:SetTexCoord(1 - newCap, 1, 0, 1)
    m:SetTexCoord(newCap, 1 - newCap, 0, 1)
  end
  return bar
end

local function exportThreeSlice() Deco.threeSlice = threeSlice end
exportThreeSlice()
local NAV_ICON = { home = "home", plan = "plan", talents = "talents", bis = "gear", macros = "macros", gameplay = "tweaks" }
Deco.NAV_ICON = NAV_ICON
-- The group heading images (word baked in) and how wide the word is, so the fading line can start after it.
local HEAD_IMG = { JOURNEY = { "azeroth_head_journey", 76 }, CHARACTER = { "azeroth_head_character", 100 },
                   UI = { "azeroth_head_ui", 17 } }
-- Sidebar label colours of the design: #CDBF9C normal, #FFF0C4 hover, #FFF3CC selected.
local NAV_TEXT = { normal = { 0.804, 0.749, 0.612 }, hover = { 1, 0.941, 0.769 }, selected = { 1, 0.953, 0.8 } }

local function buildImages(frame, ctx, d)
  local i = { nav = {}, heads = {}, sliders = {} }
  d.img = i
  -- Tiles: the stone panel over the whole window and the darker inset behind the pages.
  i.panel = itex(frame, "BACKGROUND", 1)
  i.panel:SetPoint("TOPLEFT", frame, "TOPLEFT", 4, -4)
  i.panel:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -4, 4)
  i.panel:SetTexture(IMG .. "azeroth_panel", "REPEAT", "REPEAT")
  i.panel:SetHorizTile(true)
  i.panel:SetVertTile(true)
  i.inset = itex(frame, "BACKGROUND", 2)
  i.inset:SetPoint("TOPLEFT", d.insetEdge, "TOPLEFT", 0, 0)
  i.inset:SetPoint("BOTTOMRIGHT", d.insetEdge, "BOTTOMRIGHT", 0, 0)
  i.inset:SetTexture(IMG .. "azeroth_inset", "REPEAT", "REPEAT")
  i.inset:SetHorizTile(true)
  i.inset:SetVertTile(true)
  -- Frame: four corners (one art, mirrored by texture coordinates) and four tiled edge strips between them.
  i.corners = {}
  for _, c in ipairs({
    { "TOPLEFT", 0, 1, 0, 1 }, { "TOPRIGHT", 1, 0, 0, 1 }, { "BOTTOMLEFT", 0, 1, 1, 0 }, { "BOTTOMRIGHT", 1, 0, 1, 0 },
  }) do
    local t = itex(frame, "BORDER", 1)
    t:SetSize(64, 64)
    t:SetPoint(c[1], frame, c[1], 0, 0)
    t:SetTexture(IMG .. "azeroth_corner")
    t:SetTexCoord(c[2], c[3], c[4], c[5])
    i.corners[#i.corners + 1] = t
  end
  local top = itex(frame, "BORDER", 0)
  top:SetPoint("TOPLEFT", frame, "TOPLEFT", 64, 0)
  top:SetPoint("TOPRIGHT", frame, "TOPRIGHT", -64, 0)
  top:SetHeight(16)
  top:SetTexture(IMG .. "azeroth_edge_h", "REPEAT", "REPEAT")
  top:SetHorizTile(true)
  local bottom = itex(frame, "BORDER", 0)
  bottom:SetPoint("BOTTOMLEFT", frame, "BOTTOMLEFT", 64, 0)
  bottom:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -64, 0)
  bottom:SetHeight(16)
  bottom:SetTexture(IMG .. "azeroth_edge_h", "REPEAT", "REPEAT")
  bottom:SetHorizTile(true)
  bottom:SetTexCoord(0, 1, 1, 0)
  local left = itex(frame, "BORDER", 0)
  left:SetPoint("TOPLEFT", frame, "TOPLEFT", 0, -64)
  left:SetPoint("BOTTOMLEFT", frame, "BOTTOMLEFT", 0, 64)
  left:SetWidth(16)
  left:SetTexture(IMG .. "azeroth_edge_v", "REPEAT", "REPEAT")
  left:SetVertTile(true)
  local right = itex(frame, "BORDER", 0)
  right:SetPoint("TOPRIGHT", frame, "TOPRIGHT", 0, -64)
  right:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", 0, 64)
  right:SetWidth(16)
  right:SetTexture(IMG .. "azeroth_edge_v", "REPEAT", "REPEAT")
  right:SetVertTile(true)
  right:SetTexCoord(1, 0, 0, 1)
  i.edges = { top, bottom, left, right }
  -- Corner gems sit on the empty sockets (centre 10, 10 in the corner art), a little larger than the socket.
  i.gems = {}
  for _, g in ipairs({
    { "TOPLEFT", 10, -10 }, { "TOPRIGHT", -10, -10 }, { "BOTTOMLEFT", 10, 10 }, { "BOTTOMRIGHT", -10, 10 },
  }) do
    local t = itex(frame, "OVERLAY", 1)
    t:SetSize(24, 24)
    t:SetPoint("CENTER", frame, g[1], g[2], g[3])
    t:SetTexture(IMG .. "azeroth_gem")
    i.gems[#i.gems + 1] = t
  end
  -- The ornate gold frame (one 9-slice, finials in the corners) in place of the corner and edge pieces above.
  i.frameArt = Deco.NineSlice(frame, frame, frame, 32, 0.25, "BORDER", 1, true)
  i.frameArt.set(IMG .. "azeroth_frame_ornate")
  -- Crest: the pointed banner hangs 22 px above the top edge, centred; the title sits on it. `banner` is its anchor.
  i.banner = itex(frame, "BORDER", 3)
  i.banner:SetColorTexture(0, 0, 0, 0)
  i.banner:SetSize(320, 64)
  i.banner:SetPoint("TOP", frame, "TOP", 0, 22)
  i.crest = threeSlice(frame, "BORDER", 3, 64, 0.25, i.banner)
  i.crest.set(IMG .. "azeroth_crest")
  -- Sidebar buttons: three-slice bar per state plus the gem.
  for key, b in pairs(ctx.nav) do
    local n = { bar = threeSlice(b, "BACKGROUND", 1, 16, BTN_CAP), key = key }
    n.gem = itex(b, "ARTWORK", 2)
    n.gem:SetSize(12, 12)
    n.gem:SetPoint("RIGHT", b, "RIGHT", -4, 0)
    n.icon = itex(b, "ARTWORK", 2)
    n.icon:SetSize(18, 18)
    n.icon:SetPoint("LEFT", b, "LEFT", 10, 0)
    n.icon:SetTexture(IMG .. "azeroth_icon_" .. (NAV_ICON[key] or "home"))
    n.btn = b
    i.nav[key] = n
    if b.HookScript then
      b:HookScript("OnEnter", function() n.hover = true Deco.RefreshNav() end)
      b:HookScript("OnLeave", function() n.hover = false Deco.RefreshNav() end)
    end
  end
  -- Group headings: the fading gold line.
  for _, h in ipairs(ctx.heads) do
    local line = itex(frame, "ARTWORK", 1)
    line:SetHeight(6)
    line:SetPoint("LEFT", h, "RIGHT", 8, 0)
    line:SetTexture(IMG .. "azeroth_divider")
    local word = itex(frame, "ARTWORK", 2)
    word:SetSize(128, 16)
    word:SetPoint("LEFT", h, "LEFT", -1, 0)
    local spec = HEAD_IMG[(h.GetText and h:GetText() or ""):upper()]
    if spec then word:SetTexture(IMG .. spec[1]) end
    i.heads[#i.heads + 1] = { fs = h, line = line, word = word, wordWidth = spec and spec[2], sideW = ctx.sideW }
  end
end

-- Ember & Iron (media/ember): panel tile with a heat glow along the bottom, a cut-corner steel frame, four rivets,
-- the plate behind the pages and icon tiles for the sidebar.
local EM = IMGROOT .. "ember\\ember_"
-- Tile label and icon colours: #B5AFA5 normal, #FFC247 hover, a paler #FFE8B0 selected (readable on the orange glow).
local NAV_TEXT_EMBER = { normal = { 0.71, 0.686, 0.647 }, hover = { 1, 0.76, 0.28 }, selected = { 1, 0.91, 0.69 } }

local function buildEmber(frame, ctx, d)
  local e = { nav = {} }
  d.em = e
  e.panel = itex(frame, "BACKGROUND", 1)
  e.panel:SetPoint("TOPLEFT", frame, "TOPLEFT", 4, -4)
  e.panel:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -4, 4)
  e.panel:SetTexture(EM .. "panel", "REPEAT", "REPEAT")
  e.panel:SetHorizTile(true)
  e.panel:SetVertTile(true)
  e.heat = itex(frame, "BACKGROUND", 2)
  e.heat:SetPoint("BOTTOMLEFT", frame, "BOTTOMLEFT", 4, 4)
  e.heat:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -4, 4)
  e.heat:SetHeight(16)
  e.heat:SetTexture(EM .. "heat", "REPEAT", "REPEAT")
  e.heat:SetHorizTile(true)
  e.plate = Deco.NineSlice(frame, d.insetEdge, d.insetEdge, 16, 0.25, "BACKGROUND", 3)
  e.plate.set(EM .. "plate")
  e.frame = Deco.NineSlice(frame, frame, frame, 32, 0.25, "BORDER", 2, true)
  e.frame.set(EM .. "frame")
  e.rivets = {}
  for _, rv in ipairs({
    { "TOPLEFT", 22, -22 }, { "TOPRIGHT", -22, -22 }, { "BOTTOMLEFT", 22, 22 }, { "BOTTOMRIGHT", -22, 22 },
  }) do
    local t = itex(frame, "OVERLAY", 1)
    t:SetSize(16, 16)
    t:SetPoint("CENTER", frame, rv[1], rv[2], rv[3])
    t:SetTexture(EM .. "rivet")
    e.rivets[#e.rivets + 1] = t
  end
  -- The title card and the window gauges panel under the tile grid (the sliders themselves are MainWindow's).
  e.texts = {}
  e.cardAnchor = frame:CreateTexture(nil, "BACKGROUND", nil, 5)
  e.cardAnchor:SetColorTexture(0, 0, 0, 0)
  e.cardAnchor:SetSize(280, 100)
  e.cardAnchor:SetPoint("TOPLEFT", frame, "TOPLEFT", 12, -(ctx.topH + 12 + 144 + 14))
  e.card = Deco.NineSlice(frame, e.cardAnchor, e.cardAnchor, 16, 0.25, "BACKGROUND", 5)
  e.card.set(EM .. "gauge")
  e.gaugeAnchor = frame:CreateTexture(nil, "BACKGROUND", nil, 5)
  e.gaugeAnchor:SetColorTexture(0, 0, 0, 0)
  e.gaugeAnchor:SetSize(280, 130)
  e.gaugeAnchor:SetPoint("TOPLEFT", frame, "TOPLEFT", 12, -(ctx.topH + 12 + 144 + 14 + 100 + 12))
  e.gauge = Deco.NineSlice(frame, e.gaugeAnchor, e.gaugeAnchor, 16, 0.25, "BACKGROUND", 5)
  e.gauge.set(EM .. "gauge")
  e.cardTitle = frame:CreateFontString(nil, "ARTWORK", "R2FHeadingLarge")
  e.cardTitle:SetPoint("TOPLEFT", e.cardAnchor, "TOPLEFT", 16, -14)
  R2F.Theme.PaintText(e.cardTitle, "heading")
  e.cardDesc = frame:CreateFontString(nil, "ARTWORK", "R2FBodySmall")
  e.cardDesc:SetPoint("TOPLEFT", e.cardAnchor, "TOPLEFT", 16, -46)
  e.cardDesc:SetWidth(248)
  e.cardDesc:SetJustifyH("LEFT")
  R2F.Theme.PaintText(e.cardDesc, "tagline")
  e.gaugeHead = frame:CreateFontString(nil, "ARTWORK", "R2FHeadingSmall")
  e.gaugeHead:SetPoint("TOPLEFT", e.gaugeAnchor, "TOPLEFT", 20, -14)
  e.gaugeHead:SetText(L.GAUGES_HEAD)
  R2F.Theme.PaintText(e.gaugeHead, "heading")
  e.texts = { e.cardTitle, e.cardDesc, e.gaugeHead }
  for _, fs in ipairs(e.texts) do fs:Hide() end
  for key, b in pairs(ctx.nav) do
    local n = { btn = b, slot = itex(b, "BACKGROUND", 1), icon = itex(b, "ARTWORK", 2) }
    n.slot:SetAllPoints(b)
    n.slot:SetTexture(EM .. "slot_normal")
    n.icon:SetSize(24, 24)
    n.icon:SetPoint("TOP", b, "TOP", 0, -10)
    n.icon:SetTexture(IMG .. "azeroth_icon_" .. (NAV_ICON[key] or "home"))
    e.nav[key] = n
    if b.HookScript then
      b:HookScript("OnEnter", function() n.hover = true Deco.RefreshNav() end)
      b:HookScript("OnLeave", function() n.hover = false Deco.RefreshNav() end)
    end
  end
end

-- Obsidian Night (media/obsidian): rounded window frame, a card behind the pages, and a strip of tabs in place of the sidebar.
local OB = IMGROOT .. "obsidian\\obsidian_"
local NAV_TEXT_OBS = { normal = { 0.541, 0.569, 0.639 }, hover = { 0.91, 0.918, 0.941 }, selected = { 0.208, 0.839, 0.769 } }
local TAB_H, TAB_TOP = 32, 6        -- the tab strip: pills 32 px high, 6 px under the top bar

local function buildObsidian(frame, ctx, d)
  local e = { nav = {}, seps = {} }
  d.ob = e
  e.frame = Deco.NineSlice(frame, frame, frame, 24, 0.1875, "BORDER", 2, true)
  e.frame.set(OB .. "frame")
  -- A region the card behind the pages is anchored to (below the tab strip).
  e.region = frame:CreateTexture(nil, "BACKGROUND", nil, 1)
  e.region:SetColorTexture(0, 0, 0, 0)
  e.region:SetPoint("TOPLEFT", frame, "TOPLEFT", 12, -(ctx.topH + TAB_TOP + TAB_H + 10))
  e.region:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -12, 38)
  e.plate = Deco.NineSlice(frame, e.region, e.region, 24, 0.1875, "BACKGROUND", 2)
  e.plate.set(OB .. "plate")
  -- The thin line under the tab strip (the one under the top bar is the window's own rule).
  e.rule = itex(frame, "ARTWORK", 0)
  e.rule:SetHeight(1)
  e.rule:SetPoint("TOPLEFT", frame, "TOPLEFT", 4, -(ctx.topH + TAB_TOP + TAB_H + 4))
  e.rule:SetPoint("TOPRIGHT", frame, "TOPRIGHT", -4, -(ctx.topH + TAB_TOP + TAB_H + 4))
  e.rule:SetColorTexture(0.118, 0.133, 0.169, 1)
  for key, b in pairs(ctx.nav) do
    local n = { btn = b, bg = threeSlice(b, "BACKGROUND", 1, 12, 12 / 64), icon = itex(b, "ARTWORK", 2) }
    n.icon:SetSize(16, 16)
    n.icon:SetPoint("LEFT", b, "LEFT", 10, 0)
    n.icon:SetTexture(IMG .. "azeroth_icon_" .. (NAV_ICON[key] or "home"))
    e.nav[key] = n
    if b.HookScript then
      b:HookScript("OnEnter", function() n.hover = true Deco.RefreshNav() end)
      b:HookScript("OnLeave", function() n.hover = false Deco.RefreshNav() end)
    end
  end
  for k = 1, 2 do
    local t = itex(frame, "ARTWORK", 1)
    t:SetSize(8, 32)
    t:SetTexture(OB .. "tab_sep")
    e.seps[k] = t
  end
  -- The top bar and the footer strip, one pixel inside the frame (fixed-height art, stretched across).
  e.topAnchor = frame:CreateTexture(nil, "BACKGROUND", nil, 2)
  e.topAnchor:SetColorTexture(0, 0, 0, 0)
  e.topAnchor:SetPoint("TOPLEFT", frame, "TOPLEFT", 1, -1)
  e.topAnchor:SetPoint("TOPRIGHT", frame, "TOPRIGHT", -1, -1)
  e.topAnchor:SetHeight(ctx.topH)
  e.topbar = threeSlice(frame, "BACKGROUND", 2, 16, 0.125, e.topAnchor)
  e.topbar.set(OB .. "topbar")
  e.footAnchor = frame:CreateTexture(nil, "BACKGROUND", nil, 2)
  e.footAnchor:SetColorTexture(0, 0, 0, 0)
  e.footAnchor:SetPoint("BOTTOMLEFT", frame, "BOTTOMLEFT", 1, 1)
  e.footAnchor:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -1, 1)
  e.footAnchor:SetHeight(32)
  e.footer = threeSlice(frame, "BACKGROUND", 2, 16, 0.125, e.footAnchor)
  e.footer.set(OB .. "footer")
end

-- Frost & Void (media/frost): a starfield window, two soft glows, glass panels and a chain of round orbs as the sidebar.
local FR = IMGROOT .. "frost\\frost_"
-- Labels: #A9B0D6 normal, #F2F4FF hover and selected. Icons: #A9B0D6 normal, #7FE7FF hover and selected.
local NAV_TEXT_FROST = { normal = { 0.663, 0.69, 0.839 }, hover = { 0.949, 0.957, 1 }, selected = { 0.949, 0.957, 1 } }
local ICON_FROST = { normal = { 0.663, 0.69, 0.839 }, hover = { 0.498, 0.906, 1 }, selected = { 0.498, 0.906, 1 } }

local function buildArcane(frame, ctx, d)
  local e = { nav = {} }
  d.fr = e
  e.panel = itex(frame, "BACKGROUND", 1)
  e.panel:SetPoint("TOPLEFT", frame, "TOPLEFT", 4, -4)
  e.panel:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -4, 4)
  e.panel:SetTexture(FR .. "panel", "REPEAT", "REPEAT")
  e.panel:SetHorizTile(true)
  e.panel:SetVertTile(true)
  -- The board's window gradient (#14163A at the top to #07070F) is not in the tile: a shade over it, darker towards the bottom.
  e.shade = itex(frame, "BACKGROUND", 2)
  e.shade:SetPoint("TOPLEFT", frame, "TOPLEFT", 4, -4)
  e.shade:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -4, 4)
  e.glowV = itex(frame, "BACKGROUND", 3)
  e.glowV:SetSize(330, 250)
  e.glowV:SetPoint("BOTTOMLEFT", frame, "BOTTOMLEFT", -40, 20)
  e.glowV:SetTexture(FR .. "glow_violet")
  e.glowV:SetBlendMode("ADD")
  e.glowC = itex(frame, "BACKGROUND", 3)
  e.glowC:SetSize(320, 220)
  e.glowC:SetPoint("TOPRIGHT", frame, "TOPRIGHT", 30, -10)
  e.glowC:SetTexture(FR .. "glow_cyan")
  e.glowC:SetBlendMode("ADD")
  e.frame = Deco.NineSlice(frame, frame, frame, 32, 0.25, "BORDER", 2, true)
  e.frame.set(FR .. "frame")
  e.glass = Deco.NineSlice(frame, d.insetEdge, d.insetEdge, 22, 0.25, "BACKGROUND", 4)
  e.glass.set(FR .. "glass")
  e.brackets = {}
  for _, c in ipairs({ { "TOPLEFT", "bracket_tl", 6, -6 }, { "TOPRIGHT", "bracket_tr", -6, -6 },
                       { "BOTTOMLEFT", "bracket_bl", 6, 6 }, { "BOTTOMRIGHT", "bracket_br", -6, 6 } }) do
    local t = itex(frame, "OVERLAY", 1)
    t:SetSize(32, 32)
    t:SetPoint(c[1], frame, c[1], c[3], c[4])
    t:SetTexture(FR .. c[2])
    e.brackets[#e.brackets + 1] = t
  end
  -- The pill behind Size, Opacity, Reload UI and the close button (top right).
  e.pillAnchor = frame:CreateTexture(nil, "BACKGROUND", nil, 6)
  e.pillAnchor:SetColorTexture(0, 0, 0, 0)
  e.pillAnchor:SetSize(372, 52)
  e.pillAnchor:SetPoint("TOPRIGHT", frame, "TOPRIGHT", -8, -3)
  e.pill = threeSlice(frame, "BACKGROUND", 6, 32, 0.25, e.pillAnchor)
  e.pill.set(FR .. "pill")
  e.link = itex(frame, "ARTWORK", 0)
  e.link:SetWidth(8)
  e.link:SetTexture(FR .. "link", "REPEAT", "REPEAT")
  e.link:SetVertTile(true)
  for key, b in pairs(ctx.nav) do
    local n = { btn = b, orb = itex(b, "BACKGROUND", 1), icon = itex(b, "ARTWORK", 2) }
    n.orb:SetSize(44, 44)
    n.orb:SetPoint("CENTER", b, "LEFT", 16, 0)
    n.orb:SetTexture(FR .. "orb_normal")
    n.icon:SetSize(14, 14)
    n.icon:SetPoint("CENTER", b, "LEFT", 16, 0)
    n.icon:SetTexture(IMG .. "azeroth_icon_" .. (NAV_ICON[key] or "home"))
    e.nav[key] = n
    if b.HookScript then
      b:HookScript("OnEnter", function() n.hover = true Deco.RefreshNav() end)
      b:HookScript("OnLeave", function() n.hover = false Deco.RefreshNav() end)
    end
  end
end

-- Slider track and knob (the top bar's Size and Opacity). `sl` is our own slider; the template's own track textures are hidden
-- while the images are on and put back otherwise.
local DEFAULT_KNOB = "Interface\\Buttons\\UI-SliderBar-Button-Horizontal"
function Deco.AddSlider(frame, sl)
  local d = frame.r2fDeco
  if not (d and d.img) then return end
  local own = {}
  if sl.GetRegions then
    for _, region in ipairs({ sl:GetRegions() }) do
      if region.IsObjectType and region:IsObjectType("Texture") then own[#own + 1] = region end
    end
  end
  local knob = sl.GetThumbTexture and sl:GetThumbTexture()
  local track = threeSlice(sl, "BACKGROUND", 1, 8, TRACK_CAP)
  track.parts[1]:ClearAllPoints()
  track.parts[1]:SetPoint("LEFT", sl, "LEFT", 0, 0)
  track.parts[1]:SetSize(8, 10)
  track.parts[3]:ClearAllPoints()
  track.parts[3]:SetPoint("RIGHT", sl, "RIGHT", 0, 0)
  track.parts[3]:SetSize(8, 10)
  track.parts[2]:ClearAllPoints()
  track.parts[2]:SetPoint("LEFT", track.parts[1], "RIGHT", 0, 0)
  track.parts[2]:SetPoint("RIGHT", track.parts[3], "LEFT", 0, 0)
  track.parts[2]:SetHeight(10)
  track.set(P("slider_track"))
  -- The amber filled part, clipped to the value: its width follows the slider.
  local fill = threeSlice(sl, "ARTWORK", 0, 8, TRACK_CAP)
  fill.parts[1]:ClearAllPoints()
  fill.parts[1]:SetPoint("LEFT", sl, "LEFT", 0, 0)
  fill.parts[1]:SetSize(8, 10)
  fill.parts[3]:ClearAllPoints()
  fill.parts[3]:SetPoint("LEFT", fill.parts[1], "RIGHT", 0, 0)
  fill.parts[3]:SetSize(8, 10)
  fill.parts[2]:ClearAllPoints()
  fill.parts[2]:SetPoint("LEFT", fill.parts[1], "RIGHT", 0, 0)
  fill.parts[2]:SetHeight(10)
  fill.set(P("slider_fill"))
  -- Ember & Iron: the fill is one picture with its gradient baked in; show the left part of it, clipped to the value.
  local clip = itex(sl, "ARTWORK", 0)
  clip:SetPoint("LEFT", sl, "LEFT", 0, 0)
  clip:SetHeight(12)
  local s = { sl = sl, own = own, track = track, fill = fill, clip = clip, knob = knob,
              knobFile = knob and knob.GetTexture and knob:GetTexture() or DEFAULT_KNOB }
  function s.updateFill()
    local lo, hi = 0, 1
    if sl.GetMinMaxValues then lo, hi = sl:GetMinMaxValues() end
    local w = (sl.GetWidth and sl:GetWidth() or 84)
    local frac = (lo and hi and hi > lo and sl.GetValue) and (sl:GetValue() - lo) / (hi - lo) or 0
    local px = math.max(0, math.min(w, w * frac))
    if shape().clipFill then
      for _, t in ipairs(fill.parts) do t:Hide() end
      clip:SetTexture(P("slider_fill"))
      clip:SetTexCoord(0, w > 0 and px / w or 0, 0, 1)
      clip:SetWidth(math.max(px, 1))
      clip:SetShown(Deco.imagesOn and px > 0)
      return
    end
    clip:Hide()
    -- the cap of the fill sits at its right end: left cap, plain middle, then the right cap at the value
    fill.parts[2]:SetWidth(math.max(0, px - 16))
    fill.parts[3]:ClearAllPoints()
    fill.parts[3]:SetPoint("LEFT", fill.parts[2], "RIGHT", 0, 0)
    for _, t in ipairs(fill.parts) do t:SetShown(Deco.imagesOn and px > 0) end
  end
  if sl.HookScript then sl:HookScript("OnValueChanged", function() s.updateFill() end) end
  d.img.sliders[#d.img.sliders + 1] = s
end

-- A game button (UIPanelButtonTemplate) drawn from the button art: the template's own art is hidden while the images are on.
-- `primary` = the gold call-to-action look. Art follows the button's state (normal, hover, disabled).
local imgButtons = {}
local function buttonArt(e)
  local kind = e.primary and "btn_primary" or "btn_normal"
  if e.btn.IsEnabled and not e.btn:IsEnabled() then return P("btn_disabled") end
  if e.hover then return P(e.primary and "btn_primary_hover" or "btn_hover") end
  return P(kind)
end
function Deco.AddButton(btn, primary)
  local bar = threeSlice(btn, "BACKGROUND", 1, 16, BTN_CAP)
  local entry = { btn = btn, bar = bar, art = {}, primary = primary }
  bar.set(buttonArt(entry))
  for _, key in ipairs({ "Left", "Middle", "Right" }) do
    if btn[key] then entry.art[#entry.art + 1] = btn[key] end
  end
  imgButtons[#imgButtons + 1] = entry
  local function refresh() bar.set(buttonArt(entry)) end
  if btn.HookScript then
    btn:HookScript("OnEnter", function() entry.hover = true refresh() end)
    btn:HookScript("OnLeave", function() entry.hover = false refresh() end)
    btn:HookScript("OnEnable", refresh)
    btn:HookScript("OnDisable", refresh)
  end
  entry.refresh = refresh
  if Deco.imagesOn then Deco.RefreshButtons() end
end

function Deco.RefreshButtons()
  for _, e in ipairs(imgButtons) do
    local on = Deco.imagesOn == true
    for _, region in ipairs(e.art) do region:SetAlpha(on and 0 or 1) end
    local hl = e.btn.GetHighlightTexture and e.btn:GetHighlightTexture()
    if hl and hl.SetAlpha then hl:SetAlpha(on and 0 or 1) end
    if on then
      local sh = shape()
      e.bar.shape(sh.btnCap, sh.btnCapW, sh.pad)
    end
    e.refresh()
    for _, t in ipairs(e.bar.parts) do t:SetShown(on) end
    -- The gold primary button carries dark text on the gold art.
    local fs = e.primary and e.btn.GetFontString and e.btn:GetFontString()
    if fs then
      if on then
        local pc = shape().primaryText or { 0.165, 0.102, 0.008 }
        fs:SetTextColor(pc[1], pc[2], pc[3])
      else
        R2F.Theme.PaintText(fs, "heading")
      end
    end
  end
end

-- Switches and tick boxes (UI.Switch / UI.BlackBox) drawn from images: `own` are the code-drawn parts to hide meanwhile.
local imgSwitches = {}
function Deco.StyleSwitch(b, own, knob, small)
  local e = { b = b, own = own, knob = knob, small = small, w = b:GetWidth(), h = b:GetHeight() }
  e.track = threeSlice(b, "BACKGROUND", 1, 11, 16 / 64)
  e.kn = itex(b, "ARTWORK", 3)
  e.kn:SetSize(22, 22)
  e.kn:SetTexture(P("switch_knob"))
  e.box = itex(b, "ARTWORK", 3)
  e.box:SetAllPoints(b)
  imgSwitches[#imgSwitches + 1] = e
  function e.paint()
    local on = b.GetChecked and b:GetChecked() and true or false
    if small then
      e.box:SetTexture(P(on and "check_on" or "check_off"))
    else
      e.track.set(P(on and "switch_on" or "switch_off"))
      e.kn:ClearAllPoints()
      if on then e.kn:SetPoint("RIGHT", b, "RIGHT", -1, 0) else e.kn:SetPoint("LEFT", b, "LEFT", 1, 0) end
      if shape().twoKnobs then
        -- two knobs: off and on
        e.kn:SetTexture(P(on and "switch_knob_on" or "switch_knob_off"))
        e.kn:SetVertexColor(1, 1, 1, 1)
      else
        e.kn:SetTexture(P("switch_knob"))
        if on then e.kn:SetVertexColor(1, 0.78, 0.35, 1) else e.kn:SetVertexColor(1, 1, 1, 1) end
      end
    end
  end
  b.r2fImgPaint = e.paint
  if Deco.imagesOn then Deco.RefreshSwitches() end
end

function Deco.RefreshSwitches()
  local on = Deco.imagesOn == true
  for _, e in ipairs(imgSwitches) do
    -- Hide, not fade: the code-drawn parts set their own alpha when recoloured (SetVertexColor), which would undo a fade.
    for _, t in ipairs(e.own) do t:SetShown(not on) end
    if e.knob then e.knob:SetShown(not on) end
    if not e.small then e.b:SetSize(on and 44 or e.w, on and 22 or e.h) end
    for _, t in ipairs(e.track.parts) do t:SetShown(on and not e.small) end
    e.kn:SetShown(on and not e.small)
    e.box:SetShown(on and e.small == true)
    if on then e.paint() elseif e.b.r2fPaint then e.b.r2fPaint() end
  end
end

-- A 3x3 slice of one square texture drawn between two regions (corner `capw` px, `cap` of the texture), centre included.
function Deco.NineSlice(parent, from, to, capw, cap, layer, sub, noCentre)
  local xs = { 0, cap, 1 - cap, 1 }
  local bar = { parts = {} }
  for row = 1, 3 do
    for col = 1, 3 do
      if not (noCentre and row == 2 and col == 2) then
        local t = parent:CreateTexture(nil, layer or "BACKGROUND", nil, sub or 0)
        imgPieces[#imgPieces + 1] = t
        t:SetTexCoord(xs[col], xs[col + 1], xs[row], xs[row + 1])
        if col == 1 then t:SetPoint("LEFT", from, "LEFT", 0, 0) t:SetWidth(capw) end
        if col == 3 then t:SetPoint("RIGHT", to, "RIGHT", 0, 0) t:SetWidth(capw) end
        if row == 1 then t:SetPoint("TOP", from, "TOP", 0, 0) t:SetHeight(capw) end
        if row == 3 then t:SetPoint("BOTTOM", to, "BOTTOM", 0, 0) t:SetHeight(capw) end
        if col == 2 then t:SetPoint("LEFT", from, "LEFT", capw, 0) t:SetPoint("RIGHT", to, "RIGHT", -capw, 0) end
        if row == 2 then t:SetPoint("TOP", from, "TOP", 0, -capw) t:SetPoint("BOTTOM", to, "BOTTOM", 0, capw) end
        t:Hide()
        bar.parts[#bar.parts + 1] = t
      end
    end
  end
  function bar.set(file)
    for _, t in ipairs(bar.parts) do t:SetTexture(file) end
  end
  return bar
end

-- Stone cards (the launch countdown): the 9-slice card art in image mode, a plain dark rectangle with a thin line otherwise.
local cards = {}
function Deco.Card(parent, w, h)
  local c = { frame = CreateFrame("Frame", nil, parent) }
  c.frame:SetSize(w, h)
  local cap = 24 / 128
  c.parts = {}
  local xs, ys = { 0, cap, 1 - cap, 1 }, { 0, cap, 1 - cap, 1 }
  local capw = 13
  for row = 1, 3 do
    for col = 1, 3 do
      local t = c.frame:CreateTexture(nil, "BACKGROUND", nil, 1)
      t:SetTexCoord(xs[col], xs[col + 1], ys[row], ys[row + 1])
      if col == 1 then t:SetPoint("LEFT", c.frame, "LEFT", 0, 0) t:SetWidth(capw) end
      if col == 3 then t:SetPoint("RIGHT", c.frame, "RIGHT", 0, 0) t:SetWidth(capw) end
      if row == 1 then t:SetPoint("TOP", c.frame, "TOP", 0, 0) t:SetHeight(capw) end
      if row == 3 then t:SetPoint("BOTTOM", c.frame, "BOTTOM", 0, 0) t:SetHeight(capw) end
      if col == 2 then t:SetPoint("LEFT", c.frame, "LEFT", capw, 0) t:SetPoint("RIGHT", c.frame, "RIGHT", -capw, 0) end
      if row == 2 then t:SetPoint("TOP", c.frame, "TOP", 0, -capw) t:SetPoint("BOTTOM", c.frame, "BOTTOM", 0, capw) end
      t:Hide()
      c.parts[#c.parts + 1] = t
    end
  end
  c.flat = c.frame:CreateTexture(nil, "BACKGROUND", nil, 0)
  c.flat:SetAllPoints(c.frame)
  c.lines = {}
  for _, sp in ipairs({ { "TOPLEFT", "TOPRIGHT", true }, { "BOTTOMLEFT", "BOTTOMRIGHT", true },
                        { "TOPLEFT", "BOTTOMLEFT", false }, { "TOPRIGHT", "BOTTOMRIGHT", false } }) do
    local t = c.frame:CreateTexture(nil, "BORDER")
    t:SetPoint(sp[1], c.frame, sp[1], 0, 0)
    t:SetPoint(sp[2], c.frame, sp[2], 0, 0)
    if sp[3] then t:SetHeight(1) else t:SetWidth(1) end
    c.lines[#c.lines + 1] = t
  end
  cards[#cards + 1] = c
  return c
end

-- Glass cards for a theme's Home layout (Frost & Void): the glass art of media/frost as a 9-slice at x, y (from the page's
-- top left) of size w x h, drawn as textures of the page itself so the page's text stays above them. Hidden until
-- Deco.ShowCards(theme, true).
local glassCards = {}
function Deco.GlassCard(parent, x, y, w, h, kind)
  local a = parent:CreateTexture(nil, "BACKGROUND", nil, 5)
  a:SetColorTexture(0, 0, 0, 0)
  -- The art keeps a 4 px transparent margin for its glow: the texture is 8 px larger than the card body.
  a:SetPoint("TOPLEFT", parent, "TOPLEFT", x - 4, y + 4)
  a:SetSize(w + 8, h + 8)
  local bar = Deco.NineSlice(parent, a, a, 32, 0.25, "BACKGROUND", 5)
  bar.kind = kind or "normal"
  bar.theme = "frost"
  bar.anchor = a
  glassCards[#glassCards + 1] = bar
  return bar
end

-- Obsidian Night's cards: "big" (the countdown card) or "info" (the small ones), at x, y of size w x h, no margin.
function Deco.ObsidianCard(parent, x, y, w, h, kind)
  local a = parent:CreateTexture(nil, "BACKGROUND", nil, 5)
  a:SetColorTexture(0, 0, 0, 0)
  a:SetPoint("TOPLEFT", parent, "TOPLEFT", x, y)
  a:SetSize(w, h)
  local big = kind == "big"
  local bar = Deco.NineSlice(parent, a, a, big and 24 or 16, big and 0.1875 or 0.25, "BACKGROUND", 5)
  bar.kind = big and "big" or "info"
  bar.theme = "obsidian"
  bar.anchor = a
  glassCards[#glassCards + 1] = bar
  return bar
end

-- Cards made by another set's file (UI/DecoToy.lua) register here; `bar.file` is their art.
function Deco.RegisterCard(bar) glassCards[#glassCards + 1] = bar end

-- Show the cards of one theme ("frost", "obsidian" or "gnomish") and hide the rest.
function Deco.ShowCards(theme, on)
  for _, bar in ipairs(glassCards) do
    local mine = bar.theme == theme
    if mine and on then
      if bar.file then
        bar.set(bar.file)
      elseif bar.theme == "obsidian" then
        if bar.kind == "big" then bar.set(OB .. "card_big") else bar.set(OB .. "card_info") end
      elseif bar.kind == "highlight" then bar.set(FR .. "card_highlight")
      elseif bar.kind == "dark" then bar.set(FR .. "card_dark")
      else bar.set(FR .. "card_normal") end
    end
    for _, t in ipairs(bar.parts) do
      t:SetAlpha(Deco.alpha or 1)
      t:SetShown(mine and on == true)
    end
  end
end

-- The faint circle in the top right corner of Obsidian's countdown card; `card` is the bar ObsidianCard returned.
function Deco.CircleAccent(parent, card)
  local t = parent:CreateTexture(nil, "BACKGROUND", nil, 6)
  t:SetSize(150, 150)
  t:SetPoint("TOPRIGHT", card.anchor, "TOPRIGHT", -8, -8)
  t:SetTexture(OB .. "circle_accent")
  t:Hide()
  return t
end

-- The glass disc and the thin track the countdown ring runs on: `anchor` is the ring's centre. Shown with show(true).
function Deco.RingArt(parent, anchor)
  local art = {}
  art.orb = parent:CreateTexture(nil, "ARTWORK", nil, 0)
  art.orb:SetSize(222, 222)
  art.orb:SetPoint("CENTER", anchor, "CENTER", 0, 0)
  art.orb:SetTexture(FR .. "orb_frame")
  art.track = parent:CreateTexture(nil, "ARTWORK", nil, 0)
  art.track:SetSize(196, 196)
  art.track:SetPoint("CENTER", anchor, "CENTER", 0, 0)
  art.track:SetTexture(FR .. "ring_track_mid")
  function art.show(on)
    art.orb:SetShown(on == true)
    art.track:SetShown(on == true)
  end
  return art
end

-- The picture of a theme's own close button, when its image set is on: nil otherwise (the button then draws itself).
function Deco.CloseArt(hot)
  if not Deco.imagesOn then return nil end
  local ex = Deco.extra[Deco.set or ""]
  if ex and ex.closeArt then return ex.closeArt(hot) end
  if Deco.set == "frost" then
    if hot then return FR .. "close_hover" end
    return FR .. "close_normal"
  end
  if Deco.set == "ember" then
    if hot then return EM .. "close_hover" end
    return EM .. "close_normal"
  end
  if Deco.set == "obsidian" then
    if hot then return OB .. "close_hover" end
    return OB .. "close_normal"
  end
  if Deco.set == "azeroth" then
    if hot then return IMG .. "azeroth_close_hover" end
    return IMG .. "azeroth_close_normal"
  end
  return nil
end

-- Azeroth Reforged's nested Home panel: four 32 px corners, edges TILED in 64 px pieces (the dashed gold line must not stretch)
-- and a stretched flat centre, from x, y (the page's top left) at the fixed size w x h. np.show(true / false) toggles it.
function Deco.NestedPanel(parent, x, y, w, h)
  local np = { parts = {} }
  local function piece(l, r, t, b, px, py, pw, ph)
    local tx = itex(parent, "BACKGROUND", 3)
    tx:SetTexture(IMG .. "azeroth_panel_nested")
    tx:SetTexCoord(l, r, t, b)
    tx:SetSize(pw, ph)
    tx:SetPoint("TOPLEFT", parent, "TOPLEFT", px, py)
    np.parts[#np.parts + 1] = tx
  end
  piece(0, 0.25, 0, 0.25, x, y, 32, 32)
  piece(0.75, 1, 0, 0.25, x + w - 32, y, 32, 32)
  piece(0, 0.25, 0.75, 1, x, y - h + 32, 32, 32)
  piece(0.75, 1, 0.75, 1, x + w - 32, y - h + 32, 32, 32)
  local px = 0
  while px < w - 64 do
    local len = math.min(64, w - 64 - px)
    piece(0.25, 0.25 + len / 128, 0, 0.25, x + 32 + px, y, len, 32)
    piece(0.25, 0.25 + len / 128, 0.75, 1, x + 32 + px, y - h + 32, len, 32)
    px = px + len
  end
  local py = 0
  while py < h - 64 do
    local len = math.min(64, h - 64 - py)
    piece(0, 0.25, 0.25, 0.25 + len / 128, x, y - 32 - py, 32, len)
    piece(0.75, 1, 0.25, 0.25 + len / 128, x + w - 32, y - 32 - py, 32, len)
    py = py + len
  end
  piece(0.25, 0.75, 0.25, 0.75, x + 32, y - 32, w - 64, h - 64)
  function np.show(on)
    for _, t in ipairs(np.parts) do
      t:SetAlpha(Deco.alpha or 1)
      t:SetShown(on == true)
    end
  end
  return np
end

-- The page name and its one-line description on the title card of Ember & Iron's sidebar.
function Deco.SetPageInfo(title, desc)
  local d = Deco.frame and Deco.frame.r2fDeco
  local e = d and d.em
  if not e then return end
  e.cardTitle:SetText((title or ""):upper())
  e.cardDesc:SetText(desc or "")
end

-- Re-anchor the page plate when a theme asks for another sidebar width.
function Deco.SetSideWidth(w)
  local d = Deco.frame and Deco.frame.r2fDeco
  if not (d and d.insetEdge) then return end
  d.insetEdge:ClearAllPoints()
  d.insetEdge:SetPoint("TOPLEFT", Deco.frame, "TOPLEFT", w + 2, -(d.topH + 6))
  d.insetEdge:SetPoint("BOTTOMRIGHT", Deco.frame, "BOTTOMRIGHT", -8, 8)
  for _, ex in pairs(Deco.extra) do
    if ex.sideWidth then ex.sideWidth(d, w) end
  end
end

-- A work-order row's art (Ember & Iron): a three-part plate on a button; bar.show(true / false) toggles it.
function Deco.Row(btn)
  local bar = threeSlice(btn, "BACKGROUND", 1, 12, 12 / 128)
  bar.set(EM .. "row_normal")
  function bar.show(on)
    for _, t in ipairs(bar.parts) do t:SetShown(on == true) end
  end
  return bar
end

-- A ring of `count` round dots of `size` px on a circle of `radius` px around `anchor`'s centre (the countdown ring). The first
-- dot is at the top, they run clockwise. set(frac) lights the first frac of them, with a gradient from `lo` to `hi`; the rest
-- stay in `dim`. Colours are { r, g, b, a }.
function Deco.Ring(parent, anchor, radius, count, size, lo, hi, dim)
  local ring = { dots = {} }
  for i = 1, count do
    local t = parent:CreateTexture(nil, "ARTWORK", nil, 1)
    t:SetTexture(DOT)
    t:SetSize(size, size)
    local ang = 2 * math.pi * (i - 1) / count
    t:SetPoint("CENTER", anchor, "CENTER", radius * math.sin(ang), radius * math.cos(ang))
    ring.dots[i] = t
  end
  function ring.set(frac)
    local lit = math.floor(math.max(0, math.min(1, frac)) * count + 0.5)
    for i, t in ipairs(ring.dots) do
      if i <= lit then
        local k = lit > 1 and (i - 1) / (lit - 1) or 1
        t:SetVertexColor(lo[1] + (hi[1] - lo[1]) * k, lo[2] + (hi[2] - lo[2]) * k, lo[3] + (hi[3] - lo[3]) * k, 1)
      else
        t:SetVertexColor(dim[1], dim[2], dim[3], dim[4] or 1)
      end
    end
  end
  function ring.show(on)
    for _, t in ipairs(ring.dots) do t:SetShown(on == true) end
  end
  return ring
end

local function refreshCards(th)
  local on = Deco.imagesOn == true
  for _, c in ipairs(cards) do
    for k, t in ipairs(c.parts) do
      if on then t:SetTexture(P("card")) end
      t:SetShown(on and Deco.set == "azeroth")
      if k == 1 then c.sliceDone = true end
    end
    local sd, ru = th.side, th.rule
    c.flat:SetColorTexture(sd[1], sd[2], sd[3], 0.85)
    c.flat:SetShown(not on)
    for _, t in ipairs(c.lines) do
      t:SetColorTexture(ru[1], ru[2], ru[3], 0.55)
      t:SetShown(not on)
    end
  end
  -- Ember & Iron shows the three numbers on one wide display plate.
  if cards[3] then
    if not Deco.plate then
      Deco.plate = Deco.NineSlice(cards[1].frame, cards[1].frame, cards[3].frame, 16, 0.25, "BACKGROUND", 1)
    end
    local show = on and shape().plate == true
    for _, t in ipairs(Deco.plate.parts) do t:SetShown(show) end
    if show then Deco.plate.set(P("display")) end
    for _, c in ipairs(cards) do
      c.frame.r2fPlated = show
    end
  end
end

function Deco.RefreshNav()
  local frame = Deco.frame
  local d = frame and frame.r2fDeco
  if not (d and d.img and d.imagesActive) then return end
  local ex = Deco.extra[Deco.set or ""]
  if ex then
    ex.refreshNav(d, selectedKey)
    return
  end
  if Deco.set == "frost" then
    for key, n in pairs(d.fr.nav) do
      local sel = key == selectedKey
      local state = sel and "selected" or (n.hover and "hover" or "normal")
      n.orb:SetTexture(FR .. (sel and "orb_on" or (n.hover and "orb_hover" or "orb_normal")))
      local ic, tc = ICON_FROST[state], NAV_TEXT_FROST[state]
      n.icon:SetVertexColor(ic[1], ic[2], ic[3], 1)
      if n.btn.r2fText then n.btn.r2fText:SetTextColor(tc[1], tc[2], tc[3]) end
    end
    return
  end
  if Deco.set == "obsidian" then
    for key, n in pairs(d.ob.nav) do
      local sel = key == selectedKey
      local c = sel and NAV_TEXT_OBS.selected or (n.hover and NAV_TEXT_OBS.hover or NAV_TEXT_OBS.normal)
      n.bg.set(OB .. (sel and "tab_on" or "tab_hover"))
      for _, t in ipairs(n.bg.parts) do t:SetShown(sel or n.hover == true) end
      n.icon:SetVertexColor(c[1], c[2], c[3], 1)
      if n.btn.r2fText then n.btn.r2fText:SetTextColor(c[1], c[2], c[3]) end
    end
    return
  end
  if Deco.set == "ember" then
    for key, n in pairs(d.em.nav) do
      local sel = key == selectedKey
      n.slot:SetTexture(EM .. (sel and "slot_on" or (n.hover and "slot_hover" or "slot_normal")))
      local c = sel and NAV_TEXT_EMBER.selected or (n.hover and NAV_TEXT_EMBER.hover or NAV_TEXT_EMBER.normal)
      n.icon:SetVertexColor(c[1], c[2], c[3], 1)
      if n.btn.r2fText then n.btn.r2fText:SetTextColor(c[1], c[2], c[3]) end
    end
    return
  end
  for key, n in pairs(d.img.nav) do
    local sel = key == selectedKey
    n.bar.set(IMG .. (sel and "azeroth_btn_selected" or (n.hover and "azeroth_btn_hover" or "azeroth_btn_normal")))
    n.gem:SetTexture(IMG .. (sel and "azeroth_gem_on" or "azeroth_gem_off"))
    local c = sel and NAV_TEXT.selected or (n.hover and NAV_TEXT.hover or NAV_TEXT.normal)
    n.icon:SetVertexColor(c[1], c[2], c[3], 1)
    if n.btn.r2fText then n.btn.r2fText:SetTextColor(c[1], c[2], c[3]) end
  end
end

-- Image mode on / off. Returns true when the images are in use (the caller then skips the rectangle look).
local function applyImages(d, th, alpha)
  local i = d.img
  local set = imageSet(th)
  local on = set ~= nil and i ~= nil
  d.imagesActive = on
  Deco.imagesOn = on
  Deco.set = on and set or nil
  for _, t in ipairs(imgPieces) do t:Hide() end
  if d.em then for _, fs in ipairs(d.em.texts) do fs:Hide() end end
  for _, ex in pairs(Deco.extra) do
    if ex.hide then ex.hide(d) end
  end
  Deco.RefreshButtons()
  Deco.RefreshSwitches()
  local ex = on and Deco.extra[set] or nil
  local layout = on and ((set == "ember" and "grid") or (set == "obsidian" and "top") or (set == "frost" and "chain")
    or (ex and ex.layout)) or nil
  local grid = layout == "grid"
  if R2F.MainWindow and R2F.MainWindow.SetNavLayout then R2F.MainWindow.SetNavLayout(layout) end
  for key, n in pairs(i and i.nav or {}) do
    local fs = n.btn.r2fText
    if fs then
      fs:ClearAllPoints()
      if grid then
        fs:SetPoint("BOTTOM", n.btn, "BOTTOM", 0, 8)
        fs:SetText(L.NAV_TILE and L.NAV_TILE[key] or (d.label and d.label(key)) or "")
      elseif layout == "chain" then
        fs:SetPoint("LEFT", n.btn, "LEFT", 40, 0)
        fs:SetText(d.label and d.label(key) or "")
      elseif layout == "top" then
        fs:SetPoint("LEFT", n.btn, "LEFT", 32, 0)
        fs:SetText(L.NAV_TAB and L.NAV_TAB[key] or (d.label and d.label(key)) or "")
      elseif layout == "toc" then
        fs:SetPoint("LEFT", n.btn, "LEFT", 30, 0)
        fs:SetText(d.label and d.label(key) or "")
      else
        fs:SetPoint("LEFT", n.btn, "LEFT", on and 32 or 14, 0)
        if d.label then fs:SetText(d.label(key)) end
      end
      if fs.SetJustifyH then fs:SetJustifyH(grid and "CENTER" or "LEFT") end
    end
  end
  for _, h in ipairs(i and i.heads or {}) do h.fs:SetAlpha((on and set == "azeroth") and 0 or 1) end
  for _, s in ipairs(i and i.sliders or {}) do
    for _, region in ipairs(s.own) do region:SetAlpha(on and 0 or 1) end
    local thick = (SHAPE[set] and SHAPE[set].groove) or 10
    s.track.parts[1]:SetHeight(thick)
    s.track.parts[2]:SetHeight(thick)
    s.track.parts[3]:SetHeight(thick)
    if on then s.track.set(P("slider_track")) end
    if s.knob then
      if on then
        s.sl:SetThumbTexture(P("slider_knob"))
        s.knob = s.sl:GetThumbTexture()
        if s.knob then
          s.knob:SetSize(SHAPE[set].knob[1], SHAPE[set].knob[2])
          s.knob:SetVertexColor(1, 1, 1, 1)
        end
      else
        s.sl:SetThumbTexture(s.knobFile)
        s.knob = s.sl:GetThumbTexture()
        if s.knob then s.knob:SetSize(32, 32) end
      end
    end
    if on then for _, t in ipairs(s.track.parts) do t:Show() end end
    if s.updateFill then s.updateFill() end
  end
  if not on then return false end
  if set == "azeroth" then
    i.panel:SetAlpha(alpha)
    i.inset:SetAlpha(alpha)
    i.panel:Show()
    i.inset:Show()
    for _, t in ipairs(i.frameArt.parts) do t:Show() end
    for _, t in ipairs(i.crest.parts) do t:Show() end
    i.banner:Show()
    for _, n in pairs(i.nav) do
      for _, t in ipairs(n.bar.parts) do t:Show() end
      n.gem:Show()
      n.icon:Show()
    end
    for _, h in ipairs(i.heads) do
      local w = h.wordWidth or ((h.fs.GetStringWidth and h.fs:GetStringWidth()) or 0)
      h.line:ClearAllPoints()
      h.line:SetPoint("LEFT", h.fs, "LEFT", w + 8, 0)
      h.line:SetWidth(math.max(h.sideW - 22 - w - 8, 10))
      h.line:Show()
      if h.wordWidth then h.word:Show() end
    end
  elseif set == "frost" then
    local e = d.fr
    e.panel:SetAlpha(alpha)
    e.panel:Show()
    gradient(e.shade, "VERTICAL", { 0.027, 0.027, 0.059 }, { 0.078, 0.086, 0.227 }, 0.62 * alpha, 0)
    e.shade:Show()
    e.glowV:SetAlpha(alpha)
    e.glowC:SetAlpha(alpha)
    e.glowV:Show()
    e.glowC:Show()
    for _, t in ipairs(e.frame.parts) do t:Show() end
    for _, t in ipairs(e.glass.parts) do t:SetAlpha(alpha) t:Show() end
    for _, t in ipairs(e.brackets) do t:Show() end
    for _, t in ipairs(e.pill.parts) do t:Show() end
    for _, n in pairs(e.nav) do
      n.orb:Show()
      n.icon:Show()
    end
    -- The thin chain joining the orbs, from the first orb to the last.
    e.link:ClearAllPoints()
    e.link:SetPoint("TOPLEFT", Deco.frame, "TOPLEFT", 8 + 16 - 4, -(50 + 16 + 16))
    e.link:SetPoint("BOTTOMLEFT", Deco.frame, "TOPLEFT", 8 + 16 - 4, -(50 + 16 + 16 + 5 * 38))
    e.link:Show()
  elseif ex then
    ex.apply(d, th, alpha)
  elseif set == "obsidian" then
    local e = d.ob
    e.frame.set(OB .. "frame")
    for _, t in ipairs(e.frame.parts) do t:Show() end
    for _, t in ipairs(e.plate.parts) do t:SetAlpha(alpha) t:Show() end
    e.rule:Show()
    for _, t in ipairs(e.topbar.parts) do t:Show() end
    for _, t in ipairs(e.footer.parts) do t:Show() end
    for _, n in pairs(e.nav) do n.icon:Show() end
    local seps = R2F.MainWindow and R2F.MainWindow.NavSeparators and R2F.MainWindow.NavSeparators() or {}
    for k, t in ipairs(e.seps) do
      if seps[k] then
        t:ClearAllPoints()
        t:SetPoint("TOPLEFT", Deco.frame, "TOPLEFT", seps[k], -(50 + TAB_TOP))
        t:Show()
      end
    end
  else
    local e = d.em
    e.panel:SetAlpha(alpha)
    e.panel:Show()
    e.heat:Show()
    for _, t in ipairs(e.plate.parts) do t:SetAlpha(alpha) t:Show() end
    for _, t in ipairs(e.frame.parts) do t:Show() end
    for _, t in ipairs(e.rivets) do t:Show() end
    for _, t in ipairs(e.card.parts) do t:Show() end
    for _, t in ipairs(e.gauge.parts) do t:Show() end
    for _, fs in ipairs(e.texts) do fs:Show() end
    for _, n in pairs(e.nav) do
      n.slot:Show()
      n.icon:Show()
    end
  end
  Deco.RefreshNav()
  return true
end

-- ctx: { sideW, topH, nav = { key -> nav button }, heads = { group heading font strings } }
function Deco.Build(frame, ctx)
  if built then return end
  built = true
  local d = { nav = {}, heads = {}, label = ctx.label, topH = ctx.topH }
  frame.r2fDeco = d
  Deco.frame = frame

  d.panel = tex(frame, "BACKGROUND", 1)
  d.panel:SetPoint("TOPLEFT", frame, "TOPLEFT", 4, -4)
  d.panel:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -4, 4)

  -- The darker inset the pages sit in.
  d.insetEdge = tex(frame, "BACKGROUND", 2)
  d.insetEdge:SetPoint("TOPLEFT", frame, "TOPLEFT", ctx.sideW + 2, -(ctx.topH + 6))
  d.insetEdge:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -8, 8)
  d.insetFill = tex(frame, "BACKGROUND", 3)
  d.insetFill:SetPoint("TOPLEFT", d.insetEdge, "TOPLEFT", 2, -2)
  d.insetFill:SetPoint("BOTTOMRIGHT", d.insetEdge, "BOTTOMRIGHT", -2, 2)
  d.insetLines = box(frame, d.insetEdge, 3, 1, "BACKGROUND", 4)

  -- Gold double frame line: the window already draws the outer one (r2fRimLines, 2 px); this is the thin inner line.
  d.frameInner = box(frame, frame, 6, 1, "ARTWORK", 0)

  -- Corner gems.
  d.gems = {}
  for _, corner in ipairs({ { "TOPLEFT", 5, -5 }, { "TOPRIGHT", -5, -5 }, { "BOTTOMLEFT", 5, 5 }, { "BOTTOMRIGHT", -5, 5 } }) do
    local ring = tex(frame, "OVERLAY", 1)
    ring:SetTexture(DOT)
    ring:SetSize(17, 17)
    ring:SetPoint("CENTER", frame, corner[1], corner[2], corner[3])
    local gem = tex(frame, "OVERLAY", 2)
    gem:SetTexture(DOT)
    gem:SetSize(11, 11)
    gem:SetPoint("CENTER", frame, corner[1], corner[2], corner[3])
    d.gems[#d.gems + 1] = { ring = ring, gem = gem }
  end

  -- Banner behind the title: gold edge, dark fill, a gem at each end.
  d.bannerEdge = tex(frame, "ARTWORK", 1)
  d.bannerEdge:SetSize(196, 34)
  d.bannerEdge:SetPoint("TOPLEFT", frame, "TOPLEFT", 304, -8)
  d.bannerFill = tex(frame, "ARTWORK", 2)
  d.bannerFill:SetPoint("TOPLEFT", d.bannerEdge, "TOPLEFT", 2, -2)
  d.bannerFill:SetPoint("BOTTOMRIGHT", d.bannerEdge, "BOTTOMRIGHT", -2, 2)
  d.bannerGems = {}
  for _, side in ipairs({ { "LEFT", -2 }, { "RIGHT", 2 } }) do
    local g = tex(frame, "ARTWORK", 3)
    g:SetTexture(DOT)
    g:SetSize(9, 9)
    g:SetPoint("CENTER", d.bannerEdge, side[1], side[2], 0)
    d.bannerGems[#d.bannerGems + 1] = g
  end

  -- Navigation buttons: gradient stone, dark border, a gem at the right that lights up when selected.
  for key, b in pairs(ctx.nav) do
    local n = { grad = tex(b, "BACKGROUND", 1) }
    n.grad:SetAllPoints(b)
    n.border = box(b, b, 0, 1, "BORDER", 0)
    n.gem = tex(b, "ARTWORK", 2)
    n.gem:SetTexture(DOT)
    n.gem:SetSize(8, 8)
    n.gem:SetPoint("RIGHT", b, "RIGHT", -10, 0)
    d.nav[key] = n
  end

  -- Group headings: a gold line that fades out to the right of the word.
  for _, h in ipairs(ctx.heads) do
    local line = tex(frame, "ARTWORK", 1)
    line:SetHeight(1)
    line:SetPoint("LEFT", h, "RIGHT", 8, 0)
    d.heads[#d.heads + 1] = { fs = h, line = line, sideW = ctx.sideW }
  end
  buildImages(frame, ctx, d)
  buildEmber(frame, ctx, d)
  buildObsidian(frame, ctx, d)
  buildArcane(frame, ctx, d)
  for _, ex in pairs(Deco.extra) do ex.build(frame, ctx, d) end
end

-- The banner plate is about 200 px wide: a long window title (Road to Forever: Tweaks) is scaled down to fit it.
function Deco.FitTitle(frame)
  local t = frame and frame.r2fTitle
  if not (t and t.SetScale) then return end
  t:SetScale(1)
  local w = t.GetStringWidth and t:GetStringWidth() or 0
  if Deco.set == "azeroth" and w > 250 then t:SetScale(250 / w) end
end

function Deco.Select(key)
  selectedKey = key
  Deco.RefreshNav()
end

-- Show / recolour for theme th (th.deco == "azeroth"), or hide everything.
local applyMain
function Deco.Apply(frame, th, alpha)
  Deco.alpha = alpha
  applyMain(frame, th, alpha)
  refreshCards(th)
end

applyMain = function(frame, th, alpha)
  local d = frame.r2fDeco
  if not d then return end
  local a = alpha or 1
  local imageMode = applyImages(d, th, a)
  local on = th.deco == "azeroth"
  if imageMode then
    for _, t in ipairs(pieces) do t:Hide() end
    for _, line in ipairs(frame.r2fRimLines or {}) do line:Hide() end
    if frame.r2fBgTex then
      if Deco.set == "obsidian" then frame.r2fBgTex:Show() else frame.r2fBgTex:Hide() end
    end
    if frame.r2fTitle then
      frame.r2fTitle:ClearAllPoints()
      if Deco.set == "azeroth" then
        frame.r2fTitle:SetPoint("CENTER", d.img.banner, "CENTER", 0, -2)
      elseif frame.r2fLogo then
        frame.r2fTitle:SetPoint("LEFT", frame.r2fLogo, "RIGHT", 8, 0)
      end
    end
    Deco.FitTitle(frame)
    return
  end
  if not on then
    for _, t in ipairs(pieces) do t:Hide() end
    if frame.r2fBgTex then frame.r2fBgTex:Show() end
    if frame.r2fLogo and frame.r2fTitle then
      frame.r2fTitle:ClearAllPoints()
      frame.r2fTitle:SetPoint("LEFT", frame.r2fLogo, "RIGHT", 8, 0)
    end
    return
  end
  if frame.r2fBgTex then frame.r2fBgTex:Hide() end
  gradient(d.panel, "VERTICAL", th.panelBottom, th.panelTop, a, a)
  d.panel:Show()
  flat(d.insetEdge, th.stoneEdge, a)
  gradient(d.insetFill, "VERTICAL", th.insetBottom, th.insetTop, a, a)
  d.insetEdge:Show()
  d.insetFill:Show()
  for _, t in ipairs(d.insetLines) do flat(t, th.edgeOuter, 0.55 * a) t:Show() end
  for _, t in ipairs(d.frameInner) do flat(t, th.edgeInner, 0.9) t:Show() end
  for _, g in ipairs(d.gems) do
    g.ring:SetTexture(DOT)
    g.gem:SetTexture(DOT)
    g.ring:SetVertexColor(th.stoneEdge[1], th.stoneEdge[2], th.stoneEdge[3], 1)
    g.gem:SetVertexColor(th.gem[1], th.gem[2], th.gem[3], 1)
    g.ring:Show()
    g.gem:Show()
  end
  flat(d.bannerEdge, th.edgeInner)
  flat(d.bannerFill, th.stoneEdge)
  d.bannerEdge:Show()
  d.bannerFill:Show()
  for _, g in ipairs(d.bannerGems) do
    g:SetVertexColor(th.gem[1], th.gem[2], th.gem[3], 1)
    g:Show()
  end
  if frame.r2fTitle then
    frame.r2fTitle:ClearAllPoints()
    frame.r2fTitle:SetPoint("CENTER", d.bannerEdge, "CENTER", 0, 0)
  end
  for key, n in pairs(d.nav) do
    local sel = key == selectedKey
    gradient(n.grad, "VERTICAL", sel and { 0.18, 0.14, 0.07 } or th.stoneBottom, sel and { 0.32, 0.25, 0.12 } or th.stoneTop)
    n.grad:Show()
    for _, t in ipairs(n.border) do flat(t, sel and th.edgeInner or th.stoneEdge) t:Show() end
    if sel then n.gem:SetVertexColor(1, 0.62, 0.18, 1) else n.gem:SetVertexColor(0.23, 0.18, 0.09, 1) end
    n.gem:Show()
  end
  for _, h in ipairs(d.heads) do
    local w = h.sideW - 22 - ((h.fs.GetStringWidth and h.fs:GetStringWidth()) or 0) - 8
    h.line:SetWidth(math.max(w, 10))
    gradient(h.line, "HORIZONTAL", th.edgeOuter, th.edgeOuter, 1, 0)
    h.line:Show()
  end
end
