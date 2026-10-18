-- Road to Forever: UI themes.
--
-- A theme is a table of colour tokens for the R2F-owned window shell (panel,
-- sidebar, rule, accent, rim). "classic" is the original look and the
-- default. Only tokens are stored here; the saved choice is
-- settings.theme (validated in Library.lua). Nothing is written into
-- Blizzard frames; the window reads the tokens when it applies its look.

local _, R2F = ...

local Theme = {}
R2F.Theme = Theme

Theme.DEFAULT = "classic"

-- bg/side/rule/accent/text: {r, g, b}. bgAlpha scales the window opacity
-- slider so glass-style themes stay readable. rim colours the thin frame line (classic keeps Blizzard's dialog border).
-- on/off/swRim colour UI.Switch and UI.BlackBox (classic = the original green and greys).
Theme.LIST = {
  {
    key = "classic", name = "Classic",
    on = { 0.13, 0.52, 0.21 }, off = { 0.04, 0.04, 0.05 }, swRim = { 0.45, 0.45, 0.48 },
    bg = { 0.07, 0.07, 0.09 }, bgAlpha = 1,
    side = { 0, 0, 0 }, sideAlpha = 0.45,
    rule = { 1, 0.82, 0 }, ruleAlpha = 0.35,
    accent = { 1, 0.82, 0 }, selAlpha = 0.16,
    text = { 1, 1, 1 }, rim = { 1, 1, 1 },
  },
  {
    key = "azeroth", name = "Azeroth Reforged",
    -- deco: the ornate frame of the design (gold double line, corner gems, banner title, gradient stone buttons), drawn from
    -- coloured rectangles by UI/Deco.lua. font: bundled OFL fonts (media/fonts); a missing or refused file falls back to
    -- the game's font.
    deco = "azeroth",
    font = { heading = "Interface\\AddOns\\RoadToForever\\media\\fonts\\Cinzel-Variable.ttf",
             body = "Interface\\AddOns\\RoadToForever\\media\\fonts\\AlegreyaSans-Regular.ttf", bodyBump = 1 },
    panelTop = { 0.23, 0.205, 0.17 }, panelBottom = { 0.145, 0.13, 0.1 },
    edgeOuter = { 0.54, 0.415, 0.165 }, edgeInner = { 0.79, 0.64, 0.29 }, gem = { 1, 0.78, 0.32 },
    stoneTop = { 0.24, 0.22, 0.185 }, stoneBottom = { 0.165, 0.15, 0.12 }, stoneEdge = { 0.06, 0.047, 0.03 },
    insetTop = { 0.12, 0.105, 0.085 }, insetBottom = { 0.08, 0.07, 0.055 },
    on = { 0.45, 0.58, 0.22 }, off = { 0.08, 0.07, 0.055 }, swRim = { 0.55, 0.45, 0.22 },
    bg = { 0.17, 0.15, 0.125 }, bgAlpha = 1,
    side = { 0.1, 0.085, 0.07 }, sideAlpha = 0.6,
    rule = { 0.79, 0.64, 0.29 }, ruleAlpha = 0.6,
    accent = { 0.945, 0.81, 0.48 }, selAlpha = 0.18,
    text = { 0.91, 0.86, 0.72 }, rim = { 0.79, 0.64, 0.29 },
  },
  {
    key = "obsidian", name = "Obsidian Night",
    on = { 0.1, 0.62, 0.57 }, off = { 0.035, 0.04, 0.05 }, swRim = { 0.16, 0.5, 0.47 },
    bg = { 0.055, 0.06, 0.075 }, bgAlpha = 1,
    side = { 0.09, 0.1, 0.13 }, sideAlpha = 0.8,
    rule = { 0.21, 0.84, 0.77 }, ruleAlpha = 0.45,
    accent = { 0.21, 0.84, 0.77 }, selAlpha = 0.16,
    text = { 0.91, 0.92, 0.94 }, rim = { 0.21, 0.84, 0.77 },
  },
  {
    key = "forge", name = "Ember & Iron",
    on = { 0.85, 0.4, 0.12 }, off = { 0.05, 0.047, 0.043 }, swRim = { 0.42, 0.44, 0.47 },
    bg = { 0.12, 0.115, 0.11 }, bgAlpha = 1,
    side = { 0.07, 0.065, 0.06 }, sideAlpha = 0.8,
    rule = { 1, 0.48, 0.18 }, ruleAlpha = 0.55,
    accent = { 1, 0.76, 0.28 }, selAlpha = 0.18,
    text = { 0.85, 0.83, 0.8 }, rim = { 0.42, 0.44, 0.47 },
  },
  {
    -- Glass look kept readable: the panel is nearly opaque whatever the
    -- opacity slider says (bgFloor).
    key = "arcane", name = "Frost & Void",
    on = { 0.35, 0.62, 0.95 }, off = { 0.02, 0.02, 0.05 }, swRim = { 0.4, 0.3, 0.8 },
    bg = { 0.07, 0.075, 0.17 }, bgAlpha = 0.97, bgFloor = 0.88,
    side = { 0.03, 0.03, 0.06 }, sideAlpha = 0.7,
    rule = { 0.5, 0.36, 1 }, ruleAlpha = 0.6,
    accent = { 0.5, 0.91, 1 }, selAlpha = 0.16,
    text = { 0.95, 0.96, 1 }, rim = { 0.48, 0.36, 1 },
  },
}

local byKey = {}
for _, t in ipairs(Theme.LIST) do byKey[t.key] = t end

function Theme.IsValid(key)
  return type(key) == "string" and byKey[key] ~= nil
end

function Theme.Get(key)
  if key == nil then
    local db = R2F.Library and R2F.Library.db
    key = db and db.settings and db.settings.theme
  end
  return byKey[key] or byKey[Theme.DEFAULT]
end

-- Panel alpha for the window opacity slider value a (0.3..1).
function Theme.PanelAlpha(t, a)
  local v = a * t.bgAlpha
  if t.bgFloor and v < t.bgFloor then v = t.bgFloor end
  return v
end

-- ---------------------------------------------------------------------------
-- Colour roles: every grey / white / gold text and every dark overlay of our windows is a role, not a literal.
-- Classic's roles are exactly the values the code used to hardcode (and Blizzard's own font colours); the other themes
-- derive theirs from their text / accent / bg tokens. Text, textures and backdrops painted through Paint* are repainted
-- on a theme change.
-- ---------------------------------------------------------------------------
local CLASSIC_ROLES = {
  heading = { 1, 0.82, 0 }, body = { 1, 1, 1 }, dim = { 0.5, 0.5, 0.5 }, note = { 0.7, 0.7, 0.7 },
  tagline = { 0.75, 0.75, 0.75 }, sub = { 0.6, 0.6, 0.6 }, group = { 0.6, 0.6, 0.65 },
  accentTex = { 1, 0.82, 0, 1 }, thumb = { 1, 1, 1, 1 }, button = { 1, 1, 1, 1 },
  tick = { 0.75, 0.75, 0.78, 0.8 }, menu = { 0, 0, 0, 0.9 }, edit = { 0, 0, 0, 0.8 }, bizBack = { 0.03, 0.03, 0.05, 0.9 },
}
Theme.CLASSIC_ROLES = CLASSIC_ROLES

local function mix(a, b, t)
  return { a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t, a[3] + (b[3] - a[3]) * t }
end

-- The colour {r, g, b[, a]} of a role in theme t.
function Theme.Role(t, role)
  if t.key == "classic" then return CLASSIC_ROLES[role] end
  local text, bg, accent, side = t.text, t.bg, t.accent, t.side
  if role == "heading" then return accent end
  if role == "body" then return text end
  if role == "dim" then return mix(text, bg, 0.55) end
  if role == "note" then return mix(text, bg, 0.3) end
  if role == "tagline" then return mix(text, bg, 0.22) end
  if role == "sub" then return mix(text, bg, 0.42) end
  if role == "group" then return mix(text, bg, 0.4) end
  if role == "accentTex" or role == "thumb" then return { accent[1], accent[2], accent[3], 1 } end
  if role == "button" then local c = mix({ 1, 1, 1 }, accent, 0.45) return { c[1], c[2], c[3], 1 } end
  if role == "tick" then local c = mix(text, bg, 0.35) return { c[1], c[2], c[3], 0.8 } end
  if role == "menu" then return { side[1], side[2], side[3], 0.92 } end
  if role == "edit" then return { bg[1], bg[2], bg[3], 0.85 } end
  if role == "bizBack" then return { side[1], side[2], side[3], 0.9 } end
  return CLASSIC_ROLES[role]
end

local function roleColor(role)
  return Theme.Role(Theme.Get(), role)
end

local weak = { __mode = "k" }
local painted = { text = setmetatable({}, weak), tex = setmetatable({}, weak), vertex = setmetatable({}, weak),
                  backdrop = setmetatable({}, weak) }

local function applyText(fs, role)
  local c = roleColor(role)
  if fs.SetTextColor then fs:SetTextColor(c[1], c[2], c[3]) end
end
local function applyTex(t, role)
  local c = roleColor(role)
  if t.SetColorTexture then t:SetColorTexture(c[1], c[2], c[3], c[4] or 1) end
end
local function applyVertex(t, role)
  local c = roleColor(role)
  if t.SetVertexColor then t:SetVertexColor(c[1], c[2], c[3], c[4] or 1) end
end
local function applyBackdrop(f, role)
  local c = roleColor(role)
  if f.SetBackdropColor then f:SetBackdropColor(c[1], c[2], c[3], c[4] or 1) end
end

function Theme.PaintText(fs, role) painted.text[fs] = role applyText(fs, role) end
function Theme.PaintTex(t, role) painted.tex[t] = role applyTex(t, role) end
function Theme.PaintVertex(t, role) painted.vertex[t] = role applyVertex(t, role) end
function Theme.PaintBackdrop(f, role) painted.backdrop[f] = role applyBackdrop(f, role) end

-- Our own font objects (copies of the game's, never the game's own): same face, size and shadow, colour from the theme.
-- Text created with R2FBody / R2FHeading / R2FDim (and the Small / Large sizes) follows the theme with no per-string work.
Theme.FONTS = {
  R2FHeading = { "GameFontNormal", "heading" }, R2FHeadingLarge = { "GameFontNormalLarge", "heading" },
  R2FHeadingSmall = { "GameFontNormalSmall", "heading" }, R2FBody = { "GameFontHighlight", "body" },
  R2FBodySmall = { "GameFontHighlightSmall", "body" }, R2FDim = { "GameFontDisable", "dim" },
  R2FDimSmall = { "GameFontDisableSmall", "dim" },
  R2FNumber = { "NumberFontNormalHuge", "heading" },
}
local fontObjects = {}
local function buildFonts()
  if not _G.CreateFont then return end
  for name, spec in pairs(Theme.FONTS) do
    local parent = _G[spec[1]]
    if parent and not fontObjects[name] then
      local f = _G.CreateFont(name)
      if f.SetFontObject then f:SetFontObject(parent) end
      fontObjects[name] = f
    end
  end
end
buildFonts()
function Theme.FontObject(name) return fontObjects[name] end

-- A theme with a font swaps the face of our own font objects (never the game's); the size is the game font's, plus `bodyBump` for
-- the body face (a smaller x-height needs a point more). A refused file puts the game's font back.
local function setFace(f, parent, face, bump)
  local ok = false
  if face and parent and parent.GetFont and f.SetFont then
    local fok, file, size, flags = pcall(parent.GetFont, parent)
    if fok and file and size then
      local sok, res = pcall(f.SetFont, f, face, size + (bump or 0), flags)
      ok = sok and res ~= false
    end
  end
  if not ok and f.SetFontObject and parent then f:SetFontObject(parent) end
  return ok
end

local function paintFonts()
  local t = Theme.Get()
  for name, spec in pairs(Theme.FONTS) do
    local f = fontObjects[name]
    if f then
      local face = t.font and t.font[spec[2] == "heading" and "heading" or "body"]
      setFace(f, _G[spec[1]], face, spec[2] ~= "heading" and t.font and t.font.bodyBump or 0)
      if f.SetTextColor then
        local c = roleColor(spec[2])
        f:SetTextColor(c[1], c[2], c[3])
      end
    end
  end
end

function Theme.Repaint()
  paintFonts()
  for fs, role in pairs(painted.text) do applyText(fs, role) end
  for t, role in pairs(painted.tex) do applyTex(t, role) end
  for t, role in pairs(painted.vertex) do applyVertex(t, role) end
  for f, role in pairs(painted.backdrop) do applyBackdrop(f, role) end
end

local listeners = {}
function Theme.OnChange(fn) listeners[#listeners + 1] = fn end

function Theme.Set(key)
  if not Theme.IsValid(key) then return false end
  local db = R2F.Library and R2F.Library.db
  if not (db and db.settings) then return false end
  db.settings.theme = key
  Theme.Repaint()
  for _, fn in ipairs(listeners) do fn(byKey[key]) end
  return true
end

-- A saved theme applies at login: the fonts take its colours before any window is built.
function Theme.Init() paintFonts() end
