-- UI/Reminders.lua: the Reminders tab of the main window (ADDON_PLAN.md 15.4,
-- v0.17.0): Home / Macros / Talents / Reminders / Settings.
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

local LEFT = 36
local SECTION_H = 150

local function visible()
  return page ~= nil and page:IsVisible()
end

local function refresh()
  if not visible() then return end
  for _, s in ipairs(sections) do
    local m, d = s.def.module, s.def.module.Db()
    s.show:SetChecked(d.shown)
    s.lock:SetChecked(d.lock)
    s.size:SetValue(d.scale * 100)
    s.sizeText:SetText(L[s.def.size]:format(d.scale * 100 + 0.5))
    if s.extra then
      local e = s.def.extra
      s.extra:SetValue(e.get())
      s.extraText:SetText(L[e.label]:format(e.get()))
    end
  end
end

local function slider(f, name, x, y, min, max, step, onChange)
  local sl = CreateFrame("Slider", name, f, "OptionsSliderTemplate")
  sl:SetPoint("TOPLEFT", x, y)
  sl:SetWidth(260)
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

local function buildSection(f, def, y)
  local m = def.module
  local s = { def = def }
  local head = f:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
  head:SetPoint("TOPLEFT", LEFT, y)
  head:SetText(L[def.title])

  s.show = UI.CheckButton(f, L[def.show])
  s.show:SetPoint("TOPLEFT", LEFT + 8, y - 30)
  s.show:SetScript("OnClick", function() m.SetShown(not m.Db().shown) end)
  s.lock = UI.CheckButton(f, L[def.lock])
  s.lock:SetPoint("TOPLEFT", LEFT + 8, y - 56)
  s.lock:SetScript("OnClick", function() m.SetLock(not m.Db().lock) end)

  s.sizeText = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  s.sizeText:SetPoint("TOPLEFT", LEFT + 12, y - 90)
  -- Slider names are R2F<Key>Scale (R2FStanceScale, R2FAmmoScale).
  local name = "R2F" .. def.key:sub(1, 1):upper() .. def.key:sub(2) .. "Scale"
  s.size = slider(f, name, LEFT + 14, y - 114, m.MIN_SCALE * 100, m.MAX_SCALE * 100, 5, function(_, v)
    local scale = math.floor(v / 5 + 0.5) * 5 / 100
    if math.abs(scale - m.Db().scale) > 0.001 then m.SetScale(scale) end
  end)

  local used = SECTION_H
  if def.extra then
    local e = def.extra
    s.extraText = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    s.extraText:SetPoint("TOPLEFT", LEFT + 12, y - 148)
    s.extra = slider(f, e.name, LEFT + 14, y - 172, e.min, e.max, e.step, function(_, v)
      local value = math.floor(v / e.step + 0.5) * e.step
      if value ~= e.get() then e.set(value) end
    end)
    used = used + 70
  end
  sections[#sections + 1] = s
  return used
end

-- Called once by MainWindow with the Reminders page frame.
function Tab.Build(f)
  page = f
  local mine = R2F.Reminders.ForPlayer()
  local y = -58
  if #mine == 0 then
    local none = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    none:SetPoint("TOPLEFT", LEFT, y)
    none:SetWidth(460)
    none:SetJustifyH("LEFT")
    none:SetText(L.REM_NONE)
    return f
  end
  for _, def in ipairs(mine) do
    y = y - buildSection(f, def, y)
  end
  local note = f:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
  note:SetPoint("BOTTOMLEFT", LEFT, 16)
  note:SetWidth(460)
  note:SetJustifyH("LEFT")
  note:SetText(L.REM_NOTE)
  return f
end

Tab.Refresh = refresh

function Tab.Show()
  R2F.MainWindow.Show("reminders")
end
