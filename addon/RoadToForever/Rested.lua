-- Rested.lua: "rested XP" reminder, every class.
--
-- A framed icon (the same look as the repair and pet icons, Reminders.lua) showing how much rested experience you have
-- left as a percentage of one level (the game banks up to 150% while you rest in an inn or a city). Gold while you have
-- some, hidden when you have none, unless the icon is unlocked so it can be moved. Hidden when the game gives no experience
-- numbers (nothing to gain).
--
-- Read-only: only experience getters, no protected calls. Settings live in R2FDB.rested: shown, lock, scale, x, y.

local _, R2F = ...
local L = R2F.L

local Rested = {}
R2F.Rested = Rested

local ICON = "Interface\\Icons\\Spell_Nature_Sleep"
local HAVE = { r = 0.95, g = 0.75, b = 0.1 }
local NONE = { r = 0.4, g = 0.4, b = 0.4 }

Rested.MIN_SCALE, Rested.MAX_SCALE = R2F.Reminders.MIN_SCALE, R2F.Reminders.MAX_SCALE

local frame

local function db()
  return R2F.Library.db.rested
end
Rested.Db = db

-- Rested experience as a percent of the current level's bar (0 .. 150), or nil when the game gives no answer.
function Rested.Percent()
  if not (GetXPExhaustion and UnitXPMax) then return nil end
  local ok, bank = pcall(GetXPExhaustion)
  local ok2, need = pcall(UnitXPMax, "player")
  if not (ok and ok2) or type(need) ~= "number" or need <= 0 then return nil end
  return (type(bank) == "number" and bank or 0) / need * 100
end

function Rested.Update()
  if not frame then return end
  local d = db()
  local pct = Rested.Percent()
  local has = pct ~= nil and pct > 0
  local show = d.shown and pct ~= nil and (has or not d.lock)
  frame:SetShown(show)
  if not show then return end
  local c = has and HAVE or NONE
  frame.border:SetColorTexture(c.r, c.g, c.b, 1)
  frame.icon:SetTexture(ICON)
  frame.count:SetText(has and (math.floor(pct + 0.5) .. "%") or "-")
  frame.count:SetTextColor(1, 1, 1)
  frame:EnableMouse(not d.lock)
end

-- PLAYER_LOGIN (Core.lua).
function Rested.Init()
  if frame then return end
  frame = R2F.Reminders.NewIcon("R2FRestedFrame", db, "REM_DRAG_TIP")
  frame:Place()
  local ev = CreateFrame("Frame")
  ev:SetScript("OnEvent", function() Rested.Update() end)
  for _, e in ipairs({ "PLAYER_XP_UPDATE", "UPDATE_EXHAUSTION", "PLAYER_UPDATE_RESTING", "PLAYER_LEVEL_UP",
                       "PLAYER_ENTERING_WORLD" }) do
    pcall(ev.RegisterEvent, ev, e)
  end
  Rested.Update()
end

function Rested.Apply()
  if not frame then return end
  frame:Place()
  Rested.Update()
  R2F.Reminders.RefreshUI()
end

function Rested.SetShown(on)
  db().shown = on and true or false
  Rested.Apply()
end

function Rested.SetLock(on)
  db().lock = on and true or false
  Rested.Apply()
end

function Rested.SetScale(v)
  db().scale = R2F.Reminders.ClampScale(v)
  Rested.Apply()
end

function Rested.ToggleShown()
  Rested.SetShown(not db().shown)
  R2F.Print(db().shown and L.RESTED_SHOWN or L.RESTED_HIDDEN)
end

R2F.Reminders.Register({
  key = "rested", general = true, module = Rested,
  title = "REM_RESTED_TITLE", show = "RESTED_SHOW", lock = "RESTED_LOCK", size = "RESTED_SIZE",
})
