-- UI/Reminders.lua: the reminder sections of the Gameplay tab.
--
-- They form the right-hand column of the Gameplay tab (UI/Gameplay.lua calls
-- Tab.BuildInto).
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
local CLASS_ORDER = { "PRIEST", "MAGE", "DRUID", "PALADIN", "WARRIOR", "HUNTER", "WARLOCK", "ROGUE", "SHAMAN" }

local function className(cls)
  local names = _G.LOCALIZED_CLASS_NAMES_MALE
  return (names and names[cls]) or (cls:sub(1, 1) .. cls:sub(2):lower())
end

function Tab.OpenGroups()
  local st = R2F.Library.db.settings
  if type(st.hudOpen) ~= "table" then st.hudOpen = {} end
  return st.hudOpen
end

-- Places a section's class groups according to which are open, sets its container height and tells
-- the page (Tab.OnReflow) so the scroll height follows.
function Tab.Relayout(s)
  local open = Tab.OpenGroups()
  local y = -s.baseUsed
  for _, g in ipairs(s.groups) do
    local on = 0
    for _, c in ipairs(g.items) do if c.get() then on = on + 1 end end
    g.head:ClearAllPoints()
    g.head:SetPoint("TOPLEFT", s.f, "TOPLEFT", s.x + 4, y)
    g.head.text:SetText(("%s %s  |cff999999%d / %d|r"):format(open[g.class] and "-" or "+", className(g.class), on, #g.items))
    y = y - 24
    for _, c in ipairs(g.items) do
      c.box:ClearAllPoints()
      c.box:SetPoint("TOPLEFT", s.f, "TOPLEFT", s.x + 22, y)
      c.box:SetShown(open[g.class] and true or false)
      if open[g.class] then y = y - 24 end
    end
    y = y - 2
  end
  s.height = -y + 6
  s.container:SetHeight(s.height)
  if Tab.OnReflow then Tab.OnReflow() end
end

-- Total height of the sections of one column (all of them when `col` is nil), for the page's scroll height.
function Tab.TotalHeight(col)
  local h = 0
  for _, s in ipairs(sections) do
    if col == nil or s.col == col then h = h + (s.height or 0) end
  end
  return h
end

-- The taller of the two columns.
function Tab.MaxHeight()
  return math.max(Tab.TotalHeight(1), Tab.TotalHeight(2), Tab.TotalHeight())
end

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
    if s.groups and s.container then Tab.Relayout(s) end
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
  -- Extra check boxes (def.checks): e.g. which tracking types to remind about. Checks that carry a
  -- `class` are grouped under a fold-out header per class (group buffs: Priest -> Fortitude, Spirit...).
  if def.checks then
    s.checks = {}
    local grouped = def.checks[1] and def.checks[1].class ~= nil
    if not grouped then
      local cy = y - used + 4
      for i, c in ipairs(def.checks) do
        local b = UI.CheckButton(f, L[c.label])
        b:SetPoint("TOPLEFT", x + 8, cy - (i - 1) * 24)
        b:SetScript("OnClick", function() c.set(not c.get()) end)
        s.checks[i] = { box = b, def = c }
      end
      used = used + #def.checks * 24 + 6
    else
      s.groups = {}
      local byClass = {}
      for _, c in ipairs(def.checks) do
        local g = byClass[c.class]
        if not g then
          g = { class = c.class, items = {} }
          byClass[c.class] = g
        end
        g.items[#g.items + 1] = c
      end
      local ordered = {}
      for _, cls in ipairs(CLASS_ORDER) do if byClass[cls] then ordered[#ordered + 1] = byClass[cls] end end
      for _, g in ipairs(ordered) do
        g.head = CreateFrame("Button", nil, f)
        g.head:SetSize(width, 22)
        g.head:SetHighlightTexture("Interface\\QuestFrame\\UI-QuestTitleHighlight", "ADD")
        g.head.text = g.head:CreateFontString(nil, "ARTWORK", "GameFontNormal")
        g.head.text:SetPoint("LEFT", 4, 0)
        g.head:SetScript("OnClick", function()
          local open = Tab.OpenGroups()
          open[g.class] = not open[g.class] or nil
          Tab.Relayout(s)
        end)
        for _, c in ipairs(g.items) do
          local b = UI.CheckButton(f, (L[c.label]:gsub("%s*%(.-%)%s*$", "")))
          b:SetScript("OnClick", function() c.set(not c.get()) Tab.Relayout(s) end)
          s.checks[#s.checks + 1] = { box = b, def = c }
          c.box = b
        end
        s.groups[#s.groups + 1] = g
      end
      s.baseUsed, s.x, s.f = used, x, f
      sections[#sections + 1] = s
      return nil
    end
  end
  sections[#sections + 1] = s
  s.height = used
  return used
end

-- Build the sections for this class into frame `f`, starting at (x, y) with sliders
-- `width` wide. `f` is the page whose visibility decides whether refresh draws.
-- `filter(def)` (optional) picks which reminders go into this column, `col` (1 or 2) names the column for TotalHeight.
function Tab.BuildInto(f, x, y, width, filter, col)
  page = f
  local mine = {}
  for _, def in ipairs(R2F.Reminders.ForPlayer()) do
    if not filter or filter(def) then mine[#mine + 1] = def end
  end
  if #mine == 0 and filter then return y end
  if #mine == 0 then
    local none = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    none:SetPoint("TOPLEFT", x, y)
    none:SetWidth(width + 20)
    none:SetJustifyH("LEFT")
    none:SetText(L.REM_NONE)
    return y - 40
  end
  local prev
  for _, def in ipairs(mine) do
    local box = CreateFrame("Frame", nil, f)
    box:SetSize(width + 20, 10)
    if prev then box:SetPoint("TOPLEFT", prev, "BOTTOMLEFT", 0, 0) else box:SetPoint("TOPLEFT", f, "TOPLEFT", x, y) end
    local before = #sections
    local used = buildSection(box, def, 0, 0, width)
    local s = sections[before + 1]
    s.col = col
    s.container = box
    if used then
      s.height = used
      box:SetHeight(used)
    else
      Tab.Relayout(s)
    end
    prev = box
  end
  return y - Tab.TotalHeight(col)
end

Tab.Refresh = refresh
