-- Reminders.lua: what every reminder icon has in common (ADDON_PLAN.md 15.4,
-- v0.17.0). The Reminders tab (UI/Reminders.lua) lists the reminders that apply
-- to the player's class; each reminder is its own module (Stance.lua, Ammo.lua)
-- with its own on/off, lock and size, kept in R2FDB under its own key.
--
-- A reminder registers itself here with:
--   key        "stance" / "ammo": also the SavedVariables key (R2FDB[key]) and the
--              global name of its frame (R2F<Key>Frame) and size slider (R2F<Key>Scale)
--   class      the class token it is for ("WARRIOR"); other classes never get a frame
--              and never see it on the Reminders tab
--   module     the module table: needs Db(), SetShown(on), SetLock(on), SetScale(v),
--              MIN_SCALE / MAX_SCALE, and optionally `extra` (a second slider on the
--              tab, e.g. Ammo's threshold)
--   labels     L keys: title, show, lock, size (a %d% format)
--
-- All reminders are read-only: they look at game state and draw an icon. No
-- protected calls, so they keep working in combat (and the tab's controls stay
-- enabled in combat: they only write SavedVariables).
--
-- NewIcon builds the one shared look: a framed icon (coloured border, icon,
-- optional count text), draggable unless locked, position stored as the icon's
-- centre offset from the screen centre in UIParent units (so changing the size
-- keeps it in place), scale from the saved settings.

local _, R2F = ...
local L = R2F.L

local Reminders = {}
R2F.Reminders = Reminders

local SIZE = 44
local BORDER = 3
Reminders.MIN_SCALE, Reminders.MAX_SCALE = 0.5, 3

Reminders.LIST = {}

function Reminders.Register(def)
  Reminders.LIST[#Reminders.LIST + 1] = def
end

-- The reminders that apply to this character, in registration order.
function Reminders.ForPlayer()
  local out = {}
  for _, def in ipairs(Reminders.LIST) do
    if def.class == R2F.playerClass then out[#out + 1] = def end
  end
  return out
end

-- Clamp a size to the slider's range.
function Reminders.ClampScale(v)
  return math.max(Reminders.MIN_SCALE, math.min(Reminders.MAX_SCALE, v))
end

-- A framed icon. `dbfn()` returns the reminder's settings table: scale, x, y,
-- lock. `tipKey` = the L key of the tooltip shown while it can be dragged.
-- The frame gets :Place() (apply scale + saved position), .border, .icon, .count.
function Reminders.NewIcon(name, dbfn, tipKey)
  local f = CreateFrame("Frame", name, UIParent)
  f:SetSize(SIZE, SIZE)
  f:SetFrameStrata("MEDIUM")
  f:SetClampedToScreen(true)
  f:SetMovable(true)
  f:RegisterForDrag("LeftButton")
  f.border = f:CreateTexture(nil, "BACKGROUND")
  f.border:SetAllPoints()
  f.icon = f:CreateTexture(nil, "ARTWORK")
  f.icon:SetPoint("TOPLEFT", BORDER, -BORDER)
  f.icon:SetPoint("BOTTOMRIGHT", -BORDER, BORDER)
  f.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  f.count = f:CreateFontString(nil, "OVERLAY", "NumberFontNormal")
  f.count:SetPoint("BOTTOMRIGHT", -BORDER, BORDER)

  function f:Place()
    local d = dbfn()
    local scale = d.scale
    self:SetScale(scale)
    self:ClearAllPoints()
    self:SetPoint("CENTER", UIParent, "CENTER", d.x / scale, d.y / scale)
  end

  -- Drag end: store the centre as an offset from the screen centre.
  local function savePosition(self)
    local cx, cy = self:GetCenter()
    local ux, uy = UIParent:GetCenter()
    if not (cx and ux) then return end
    local es, ues = self:GetEffectiveScale(), UIParent:GetEffectiveScale()
    local d = dbfn()
    d.x = (cx * es - ux * ues) / ues
    d.y = (cy * es - uy * ues) / ues
    self:Place()
  end

  f:SetScript("OnDragStart", function(self)
    if not dbfn().lock then self:StartMoving() end
  end)
  f:SetScript("OnDragStop", function(self)
    self:StopMovingOrSizing()
    savePosition(self)
  end)
  f:SetScript("OnEnter", function(self)
    if dbfn().lock or not tipKey then return end
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:AddLine(L[tipKey], 1, 1, 1)
    GameTooltip:Show()
  end)
  f:SetScript("OnLeave", function() GameTooltip:Hide() end)
  return f
end

-- Refresh whatever shows the reminders' settings (the Reminders tab).
function Reminders.RefreshUI()
  if R2F.RemindersTab and R2F.RemindersTab.Refresh then R2F.RemindersTab.Refresh() end
end
