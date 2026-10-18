-- UI/Deco.lua: theme decoration drawn from coloured rectangles and one round dot texture (no image files).
--
-- Today one decoration exists, "azeroth" (Azeroth Reforged): a stone-coloured gradient panel, a gold double frame line,
-- round corner gems, a banner behind the window title, gradient "stone" navigation buttons with a gem, group headings with
-- a fading gold underline and a darker inset behind the pages. Every piece is a texture on our own main window; Deco.Apply
-- shows them for a theme with `deco = "azeroth"` and hides them for any other. Nothing is written into the game's frames.
-- Gradients use Texture:SetGradient (guarded: without it the piece is flat, in the middle colour).

local _, R2F = ...

local Deco = {}
R2F.Deco = Deco

local DOT = "Interface\\AddOns\\RoadToForever\\media\\dot"

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
local imgPieces = {}
local BTN_CAP = 16 / 128          -- cap width in texture coordinates
local TRACK_CAP = 8 / 128

local function itex(parent, layer, sub)
  local t = parent:CreateTexture(nil, layer or "BACKGROUND", nil, sub or 0)
  imgPieces[#imgPieces + 1] = t
  t:Hide()
  return t
end

local function imagesOn()
  return R2F.Images ~= nil and R2F.Images.azeroth == true
end

-- A three-part bar (left cap, stretchy middle, right cap) on `parent`, filled from one texture file; `capw` is the cap's
-- display width in px, `cap` its width in texture coordinates. Returns { parts, set = function(file) }.
local function threeSlice(parent, layer, sub, capw, cap)
  local l, m, r = itex(parent, layer, sub), itex(parent, layer, sub), itex(parent, layer, sub)
  l:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, 0)
  l:SetPoint("BOTTOMLEFT", parent, "BOTTOMLEFT", 0, 0)
  l:SetWidth(capw)
  l:SetTexCoord(0, cap, 0, 1)
  r:SetPoint("TOPRIGHT", parent, "TOPRIGHT", 0, 0)
  r:SetPoint("BOTTOMRIGHT", parent, "BOTTOMRIGHT", 0, 0)
  r:SetWidth(capw)
  r:SetTexCoord(1 - cap, 1, 0, 1)
  m:SetPoint("TOPLEFT", l, "TOPRIGHT", 0, 0)
  m:SetPoint("BOTTOMRIGHT", r, "BOTTOMLEFT", 0, 0)
  m:SetTexCoord(cap, 1 - cap, 0, 1)
  local bar = { parts = { l, m, r } }
  function bar.set(file)
    for _, t in ipairs(bar.parts) do t:SetTexture(file) end
  end
  return bar
end

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
  -- Banner: hangs 20 px above the top edge, between the logo and the Size slider (x 252 to 500).
  i.banner = itex(frame, "BORDER", 3)
  i.banner:SetSize(248, 62)
  i.banner:SetPoint("TOPLEFT", frame, "TOPLEFT", 252, 20)
  i.banner:SetTexture(IMG .. "azeroth_banner")
  -- Sidebar buttons: three-slice bar per state plus the gem.
  for key, b in pairs(ctx.nav) do
    local n = { bar = threeSlice(b, "BACKGROUND", 1, 16, BTN_CAP), key = key }
    n.gem = itex(b, "ARTWORK", 2)
    n.gem:SetSize(16, 16)
    n.gem:SetPoint("RIGHT", b, "RIGHT", -6, 0)
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
    i.heads[#i.heads + 1] = { fs = h, line = line, sideW = ctx.sideW }
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
  track.parts[1]:SetSize(8, 16)
  track.parts[3]:ClearAllPoints()
  track.parts[3]:SetPoint("RIGHT", sl, "RIGHT", 0, 0)
  track.parts[3]:SetSize(8, 16)
  track.parts[2]:ClearAllPoints()
  track.parts[2]:SetPoint("LEFT", track.parts[1], "RIGHT", 0, 0)
  track.parts[2]:SetPoint("RIGHT", track.parts[3], "LEFT", 0, 0)
  track.parts[2]:SetHeight(16)
  track.set(IMG .. "azeroth_slider_track")
  d.img.sliders[#d.img.sliders + 1] = { sl = sl, own = own, track = track, knob = knob,
                                        knobFile = knob and knob.GetTexture and knob:GetTexture() or DEFAULT_KNOB }
end

-- A game button (UIPanelButtonTemplate) drawn from the button art: the template's own art is hidden while the images are on.
local imgButtons = {}
function Deco.AddButton(btn)
  local bar = threeSlice(btn, "BACKGROUND", 1, 16, BTN_CAP)
  bar.set(IMG .. "azeroth_btn_normal")
  local entry = { btn = btn, bar = bar, art = {} }
  for _, key in ipairs({ "Left", "Middle", "Right" }) do
    if btn[key] then entry.art[#entry.art + 1] = btn[key] end
  end
  imgButtons[#imgButtons + 1] = entry
  if btn.HookScript then
    btn:HookScript("OnEnter", function() bar.set(IMG .. "azeroth_btn_hover") end)
    btn:HookScript("OnLeave", function() bar.set(IMG .. "azeroth_btn_normal") end)
  end
end

function Deco.RefreshNav()
  local frame = Deco.frame
  local d = frame and frame.r2fDeco
  if not (d and d.img and d.imagesActive) then return end
  for key, n in pairs(d.img.nav) do
    local sel = key == selectedKey
    n.bar.set(IMG .. (sel and "azeroth_btn_selected" or (n.hover and "azeroth_btn_hover" or "azeroth_btn_normal")))
    n.gem:SetTexture(IMG .. (sel and "azeroth_gem_on" or "azeroth_gem_off"))
  end
end

-- Image mode on / off. Returns true when the images are in use (the caller then skips the rectangle look).
local function applyImages(d, th, alpha)
  local i = d.img
  local on = th.deco == "azeroth" and imagesOn() and i ~= nil
  d.imagesActive = on
  for _, t in ipairs(imgPieces) do t:Hide() end
  for _, e in ipairs(imgButtons) do
    for _, region in ipairs(e.art) do region:SetAlpha(on and 0 or 1) end
    local hl = e.btn.GetHighlightTexture and e.btn:GetHighlightTexture()
    if hl and hl.SetAlpha then hl:SetAlpha(on and 0 or 1) end
    if on then for _, t in ipairs(e.bar.parts) do t:Show() end end
  end
  for _, s in ipairs(i and i.sliders or {}) do
    for _, region in ipairs(s.own) do region:SetAlpha(on and 0 or 1) end
    if s.knob then
      if on then
        s.sl:SetThumbTexture(IMG .. "azeroth_slider_knob")
        s.knob = s.sl:GetThumbTexture()
        if s.knob then s.knob:SetSize(24, 24) s.knob:SetVertexColor(1, 1, 1, 1) end
      else
        s.sl:SetThumbTexture(s.knobFile)
        s.knob = s.sl:GetThumbTexture()
        if s.knob then s.knob:SetSize(32, 32) end
      end
    end
    if on then for _, t in ipairs(s.track.parts) do t:Show() end end
  end
  if not on then return false end
  i.panel:SetAlpha(alpha)
  i.inset:SetAlpha(alpha)
  i.panel:Show()
  i.inset:Show()
  for _, t in ipairs(i.corners) do t:Show() end
  for _, t in ipairs(i.edges) do t:Show() end
  for _, t in ipairs(i.gems) do t:Show() end
  i.banner:Show()
  for _, n in pairs(i.nav) do
    for _, t in ipairs(n.bar.parts) do t:Show() end
    n.gem:Show()
  end
  for _, h in ipairs(i.heads) do
    h.line:SetWidth(math.max(h.sideW - 22 - ((h.fs.GetStringWidth and h.fs:GetStringWidth()) or 0) - 8, 10))
    h.line:Show()
  end
  Deco.RefreshNav()
  return true
end

-- ctx: { sideW, topH, nav = { key -> nav button }, heads = { group heading font strings } }
function Deco.Build(frame, ctx)
  if built then return end
  built = true
  local d = { nav = {}, heads = {} }
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
end

function Deco.Select(key)
  selectedKey = key
  Deco.RefreshNav()
end

-- Show / recolour for theme th (th.deco == "azeroth"), or hide everything.
function Deco.Apply(frame, th, alpha)
  local d = frame.r2fDeco
  if not d then return end
  local a = alpha or 1
  local imageMode = applyImages(d, th, a)
  local on = th.deco == "azeroth"
  if imageMode then
    for _, t in ipairs(pieces) do t:Hide() end
    for _, line in ipairs(frame.r2fRimLines or {}) do line:Hide() end
    if frame.r2fBgTex then frame.r2fBgTex:Hide() end
    if frame.r2fTitle then
      frame.r2fTitle:ClearAllPoints()
      frame.r2fTitle:SetPoint("CENTER", d.img.banner, "CENTER", 0, -2)
    end
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
