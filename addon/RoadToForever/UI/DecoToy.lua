-- UI/DecoToy.lua: the image set "gnomish" (Gnomish Workshop), a light, chunky toy look.  A cream window with a brown outline
-- and a hard shadow, a row of coloured tabs along the top that sit on the page, coloured cards on Home, digit boxes for the
-- countdown and a smiling sun. Art: media/gnomish (converted by addon/art/slices_to_tga.py, flagged in Images.lua). Registers
-- with UI/Deco.lua (Deco.extra.gnomish); nothing is written into the game's frames.

local _, R2F = ...
local Deco = R2F.Deco

local GN = Deco.IMGROOT .. "gnomish\\gnomish_"
local TAB_COLOUR = { home = "cyan", plan = "yellow", talents = "coral", bis = "green", macros = "purple", gameplay = "orange" }
local TAB_TOP = 6
local TAB_H = 32

local ex = { layout = "top" }
Deco.extra.gnomish = ex

-- A card of colour `kind` (blue, yellow, green, pink, white) at x, y of body size w x h, drawn as textures of `parent`. The
-- art keeps a 7 px shadow margin right and below its body. Shown with Deco.ShowCards("gnomish", true).
function Deco.ToyCard(parent, x, y, w, h, kind)
  local a = parent:CreateTexture(nil, "BACKGROUND", nil, 5)
  a:SetColorTexture(0, 0, 0, 0)
  a:SetPoint("TOPLEFT", parent, "TOPLEFT", x, y)
  a:SetSize(w + 7, h + 7)
  local bar = Deco.NineSlice(parent, a, a, 24, 0.375, "BACKGROUND", 5)
  bar.theme = "gnomish"
  bar.kind = kind
  bar.file = GN .. "card_" .. kind
  bar.anchor = a
  Deco.RegisterCard(bar)
  return bar
end

-- A countdown digit box on `frame` (the card frame of a number): white, or yellow for the minutes.
function Deco.ToyDigit(frame, yellow)
  local bar = Deco.NineSlice(frame, frame, frame, 20, 0.3125, "BACKGROUND", 1)
  bar.set(yellow and (GN .. "digit_yellow") or (GN .. "digit_white"))
  function bar.show(on)
    for _, t in ipairs(bar.parts) do t:SetShown(on == true) end
  end
  return bar
end

-- The sun mascot, `size` px, anchored by the caller. Shown / hidden by the caller.
function Deco.ToySun(parent, size)
  local t = parent:CreateTexture(nil, "ARTWORK", nil, 2)
  t:SetSize(size, size)
  t:SetTexture(GN .. "sun")
  t:Hide()
  return t
end

function ex.build(frame, ctx, d)
  local e = { nav = {} }
  d.gn = e
  e.frame = Deco.NineSlice(frame, frame, frame, 40, 0.3125, "BORDER", 2)
  e.frame.set(GN .. "frame")
  -- The page the tabs sit on (below the tab strip).
  e.region = frame:CreateTexture(nil, "BACKGROUND", nil, 1)
  e.region:SetColorTexture(0, 0, 0, 0)
  e.region:SetPoint("TOPLEFT", frame, "TOPLEFT", 14, -(ctx.topH + TAB_TOP + TAB_H - 2))
  e.region:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -18, 24)
  e.plate = Deco.NineSlice(frame, e.region, e.region, 24, 0.375, "BACKGROUND", 3)
  e.plate.set(GN .. "page")
  -- The yellow disc behind the logo.
  e.disc = Deco.itex(frame, "BORDER", 3)
  e.disc:SetSize(46, 46)
  if frame.r2fLogo then e.disc:SetPoint("CENTER", frame.r2fLogo, "CENTER", 0, 0) end
  e.disc:SetTexture(GN .. "logo_disc")
  for key, b in pairs(ctx.nav) do
    local n = { btn = b, bg = Deco.threeSlice(b, "BACKGROUND", 1, 16, 0.25), icon = Deco.itex(b, "ARTWORK", 2), key = key }
    n.icon:SetSize(16, 16)
    n.icon:SetPoint("LEFT", b, "LEFT", 10, 0)
    n.icon:SetTexture(Deco.IMGROOT .. "azeroth\\azeroth_icon_" .. (Deco.NAV_ICON[key] or "home"))
    e.nav[key] = n
    if b.HookScript then
      b:HookScript("OnEnter", function() n.hover = true Deco.RefreshNav() end)
      b:HookScript("OnLeave", function() n.hover = false Deco.RefreshNav() end)
    end
  end
end

function ex.closeArt(hot)
  if hot then return GN .. "close_hover" end
  return GN .. "close_normal"
end

function ex.apply(d, _, alpha)
  local e = d.gn
  for _, t in ipairs(e.frame.parts) do
    t:SetAlpha(alpha)
    t:Show()
  end
  for _, t in ipairs(e.plate.parts) do
    t:SetAlpha(alpha)
    t:Show()
  end
  e.disc:Show()
  for _, n in pairs(e.nav) do n.icon:Show() end
end

function ex.refreshNav(d, key)
  local e = d.gn
  local th = R2F.Theme.Get()
  local ink = th.text
  for k, n in pairs(e.nav) do
    local sel = k == key
    local colour = sel and "tab_active" or ("tab_" .. TAB_COLOUR[k])
    n.bg.set(GN .. colour)
    for _, t in ipairs(n.bg.parts) do t:Show() end
    n.icon:SetVertexColor(ink[1], ink[2], ink[3], 1)
    if n.btn.r2fText then n.btn.r2fText:SetTextColor(ink[1], ink[2], ink[3]) end
  end
end
