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

-- ctx: { sideW, topH, nav = { key -> nav button }, heads = { group heading font strings } }
function Deco.Build(frame, ctx)
  if built then return end
  built = true
  local d = { nav = {}, heads = {} }
  frame.r2fDeco = d

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
end

local selectedKey
function Deco.Select(key)
  selectedKey = key
end

-- Show / recolour for theme th (th.deco == "azeroth"), or hide everything.
function Deco.Apply(frame, th, alpha)
  local d = frame.r2fDeco
  if not d then return end
  local on = th.deco == "azeroth"
  if not on then
    for _, t in ipairs(pieces) do t:Hide() end
    if frame.r2fBgTex then frame.r2fBgTex:Show() end
    if frame.r2fLogo and frame.r2fTitle then
      frame.r2fTitle:ClearAllPoints()
      frame.r2fTitle:SetPoint("LEFT", frame.r2fLogo, "RIGHT", 8, 0)
    end
    return
  end
  local a = alpha or 1
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
