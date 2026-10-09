-- Stance.lua: Warrior stance indicator (v0.13.0; a reminder since v0.17.0).
--
-- One icon on screen showing the current stance, with a coloured frame:
-- Battle (Arms) blue, Defensive (tank) green, Berserker red. Warriors only; the
-- frame is never created for other classes.
-- Settings live in R2FDB.stance (Library.Init): shown, lock, scale, x, y (the
-- icon's centre as an offset from the screen centre, in UIParent units, so
-- changing the scale keeps it in place). Changed from the Reminders tab or
-- /r2f stance, /r2f stance lock. The framed-icon look, dragging and position
-- saving are shared with the other reminders (Reminders.lua).
--
-- Stance index from GetShapeshiftForm(): 0 none (below level 10), 1 Battle,
-- 2 Defensive, 3 Berserker. Icons are fixed textures, not looked up, so the
-- indicator can't break on a client whose GetShapeshiftFormInfo differs.
-- Unlocked, the frame also shows with no stance (grey) so it can be placed
-- before level 10.

local _, R2F = ...
local L = R2F.L

local Stance = {}
R2F.Stance = Stance

local STANCES = {
  [1] = { icon = "Interface\\Icons\\Ability_Warrior_OffensiveStance", r = 0.15, g = 0.45, b = 1.0 },
  [2] = { icon = "Interface\\Icons\\Ability_Warrior_DefensiveStance", r = 0.1, g = 0.8, b = 0.2 },
  [3] = { icon = "Interface\\Icons\\Ability_Racial_Avatar", r = 0.9, g = 0.1, b = 0.1 },
}
local NONE = { icon = STANCES[1].icon, r = 0.4, g = 0.4, b = 0.4 }

Stance.MIN_SCALE, Stance.MAX_SCALE = R2F.Reminders.MIN_SCALE, R2F.Reminders.MAX_SCALE

local frame

local function db()
  return R2F.Library.db.stance
end
Stance.Db = db

function Stance.IsWarrior()
  return R2F.playerClass == "WARRIOR"
end

function Stance.Update()
  if not frame then return end
  local d = db()
  local idx = GetShapeshiftForm and GetShapeshiftForm() or 0
  local s = STANCES[idx]
  local show = d.shown and (s ~= nil or not d.lock)
  frame:SetShown(show)
  if not show then return end
  s = s or NONE
  frame.border:SetColorTexture(s.r, s.g, s.b, 1)
  frame.icon:SetTexture(s.icon)
  frame.icon:SetDesaturated(STANCES[idx] == nil)
  frame:EnableMouse(not d.lock)
end

-- PLAYER_LOGIN (Core.lua).
function Stance.Init()
  if not Stance.IsWarrior() or frame then return end
  frame = R2F.Reminders.NewIcon("R2FStanceFrame", db, "REM_DRAG_TIP")
  frame:Place()
  local ev = CreateFrame("Frame")
  ev:SetScript("OnEvent", Stance.Update)
  for _, e in ipairs({ "UPDATE_SHAPESHIFT_FORM", "UPDATE_SHAPESHIFT_FORMS", "PLAYER_ENTERING_WORLD" }) do
    pcall(ev.RegisterEvent, ev, e)
  end
  Stance.Update()
end

-- Re-read settings after a change (Reminders tab, slash commands).
function Stance.Apply()
  if not frame then return end
  frame:Place()
  Stance.Update()
  R2F.Reminders.RefreshUI()
end

function Stance.SetShown(on)
  db().shown = on and true or false
  Stance.Apply()
end

function Stance.SetLock(on)
  db().lock = on and true or false
  Stance.Apply()
end

function Stance.SetScale(v)
  db().scale = R2F.Reminders.ClampScale(v)
  Stance.Apply()
end

-- /r2f stance, /r2f stance lock
function Stance.ToggleShown()
  if not Stance.IsWarrior() then R2F.Print(L.STANCE_WARRIOR_ONLY) return end
  Stance.SetShown(not db().shown)
  R2F.Print(db().shown and L.STANCE_SHOWN or L.STANCE_HIDDEN)
end

function Stance.ToggleLock()
  if not Stance.IsWarrior() then R2F.Print(L.STANCE_WARRIOR_ONLY) return end
  Stance.SetLock(not db().lock)
  R2F.Print(db().lock and L.STANCE_LOCKED or L.STANCE_UNLOCKED)
end

R2F.Reminders.Register({
  key = "stance", class = "WARRIOR", module = Stance,
  title = "REM_STANCE_TITLE", show = "SETTINGS_STANCE_SHOW", lock = "SETTINGS_STANCE_LOCK",
  size = "SETTINGS_STANCE_SIZE",
})
