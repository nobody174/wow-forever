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
-- slider so glass-style themes stay readable. rim tints the border.
Theme.LIST = {
  {
    key = "classic", name = "Classic",
    bg = { 0.07, 0.07, 0.09 }, bgAlpha = 1,
    side = { 0, 0, 0 }, sideAlpha = 0.45,
    rule = { 1, 0.82, 0 }, ruleAlpha = 0.35,
    accent = { 1, 0.82, 0 }, selAlpha = 0.16,
    text = { 1, 1, 1 }, rim = { 1, 1, 1 },
  },
  {
    key = "azeroth", name = "Azeroth Reforged",
    bg = { 0.17, 0.15, 0.125 }, bgAlpha = 1,
    side = { 0.1, 0.085, 0.07 }, sideAlpha = 0.6,
    rule = { 0.79, 0.64, 0.29 }, ruleAlpha = 0.6,
    accent = { 0.945, 0.81, 0.48 }, selAlpha = 0.18,
    text = { 0.91, 0.86, 0.72 }, rim = { 0.79, 0.64, 0.29 },
  },
  {
    key = "obsidian", name = "Obsidian Night",
    bg = { 0.055, 0.06, 0.075 }, bgAlpha = 1,
    side = { 0.09, 0.1, 0.13 }, sideAlpha = 0.8,
    rule = { 0.21, 0.84, 0.77 }, ruleAlpha = 0.45,
    accent = { 0.21, 0.84, 0.77 }, selAlpha = 0.16,
    text = { 0.91, 0.92, 0.94 }, rim = { 0.21, 0.84, 0.77 },
  },
  {
    key = "forge", name = "Ember & Iron",
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

local listeners = {}
function Theme.OnChange(fn) listeners[#listeners + 1] = fn end

function Theme.Set(key)
  if not Theme.IsValid(key) then return false end
  R2F.Library.db.settings.theme = key
  for _, fn in ipairs(listeners) do fn(byKey[key]) end
  return true
end
