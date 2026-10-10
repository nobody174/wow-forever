-- UI/Reminders.lua: the reminder sections of the Gameplay tab (ADDON_PLAN.md 15.4 / 17).
--
-- Until v0.20.1 these sections were a tab of their own (Reminders); since v0.21.0 they are
-- the right-hand column of the Gameplay tab (UI/Gameplay.lua calls Tab.BuildInto).
--
-- One section per reminder that applies to the player's class (Reminders.ForPlayer):
-- a heading, Show and Lock check boxes, a size slider, and for reminders that
-- have one a second slider (Ammo's "warn when under"). A class with no reminder
-- sees one line saying so. The reminders are read-only on-screen icons, and these
-- controls only write SavedVariables, so everything stays enabled in combat.
--
-- Sections are built once from the reminder registry (Reminders.lua): adding a
-- reminder means registering it, not editing this file.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI

local Tab = {}
R2F.RemindersTab = Tab

local page
local sections = {}   -- { def =, show =, lock =, size =, sizeText =, extra =, extraText = }

local SECTION_H = 150

local function visible()
  return page ~= nil and page:IsVisible()
end

local function refresh()
  if not visible() then return end
  for _, s in ipairs(sections) do
    local d = s.def.module.Db()
    s.show:SetChecked(d.shown)
    s.lock:SetChecked(d.lock)
    s.size:SetValue(d.scale * 100)
    s.sizeText:SetText(L[s.def.size]:format(d.scale * 100 + 0.5))
    if s.extra then
      local e = s.def.extra
      s.extra:SetValue(e.get())
      s.extraText:SetText(L[e.label]:format(e.get()))
    end
    for _, c in ipairs(s.checks or {}) do c.box:SetChecked(c.def.get() and true or false) end
  end
end

local function slider(f, name, x, y, width, min, max, step, onChange)
  local sl = CreateFrame("Slider", name, f, "OptionsSliderTemplate")
  sl:SetPoint("TOPLEFT", x, y)
  sl:SetWidth(width)
  sl:SetMinMaxValues(min, max)
  sl:SetValueStep(step)
  if sl.SetObeyStepOnDrag then sl:SetObeyStepOnDrag(true) end
  for _, part in ipairs({ "Low", "High", "Text" }) do
    local fs = sl[part] or _G[name .. part]
    if fs then fs:SetText("") end
  end
  sl:SetScript("OnValueChanged", onChange)
  return sl
end

local function buildSection(f, def, x, y, width)
  local m = def.module
  local s = { def = def }
  local head = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  head:SetPoint("TOPLEFT", x, y)
  head:SetText(L[def.title])

  s.show = UI.CheckButton(f, L[def.show])
  s.show:SetPoint("TOPLEFT", x + 8, y - 24)
  s.show:SetScript("OnClick", function() m.SetShown(not m.Db().shown) end)
  s.lock = UI.CheckButton(f, L[def.lock])
  s.lock:SetPoint("TOPLEFT", x + 8, y - 50)
  s.lock:SetScript("OnClick", function() m.SetLock(not m.Db().lock) end)

  s.sizeText = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  s.sizeText:SetPoint("TOPLEFT", x + 12, y - 82)
  -- Slider names are R2F<Key>Scale (R2FStanceScale, R2FAmmoScale).
  local name = "R2F" .. def.key:sub(1, 1):upper() .. def.key:sub(2) .. "Scale"
  s.size = slider(f, name, x + 14, y - 104, width, m.MIN_SCALE * 100, m.MAX_SCALE * 100, 5, function(_, v)
    local scale = math.floor(v / 5 + 0.5) * 5 / 100
    if math.abs(scale - m.Db().scale) > 0.001 then m.SetScale(scale) end
  end)

  local used = SECTION_H - 10
  if def.extra then
    local e = def.extra
    s.extraText = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    s.extraText:SetPoint("TOPLEFT", x + 12, y - 134)
    s.extra = slider(f, e.name, x + 14, y - 156, width, e.min, e.max, e.step, function(_, v)
      local value = math.floor(v / e.step + 0.5) * e.step
      if value ~= e.get() then e.set(value) end
    end)
    used = used + 66
  end
  -- Extra check boxes (def.checks): e.g. which tracking types to remind about.
  if def.checks then
    s.checks = {}
    local cy = y - used + 4
    for i, c in ipairs(def.checks) do
      local b = UI.CheckButton(f, L[c.label])
      b:SetPoint("TOPLEFT", x + 8, cy - (i - 1) * 24)
      b:SetScript("OnClick", function() c.set(not c.get()) end)
      s.checks[i] = { box = b, def = c }
    end
    used = used + #def.checks * 24 + 6
  end
  sections[#sections + 1] = s
  return used
end

-- Build the sections for this class into frame `f`, starting at (x, y) with sliders
-- `width` wide. `f` is the page whose visibility decides whether refresh draws.
function Tab.BuildInto(f, x, y, width)
  page = f
  local mine = R2F.Reminders.ForPlayer()
  if #mine == 0 then
    local none = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    none:SetPoint("TOPLEFT", x, y)
    none:SetWidth(width + 20)
    none:SetJustifyH("LEFT")
    none:SetText(L.REM_NONE)
    return y - 40
  end
  for _, def in ipairs(mine) do
    y = y - buildSection(f, def, x, y, width)
  end
  return y
end

Tab.Refresh = refresh
