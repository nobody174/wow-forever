-- Repair.lua: "your gear needs repair" reminder.
--
-- A framed icon (the same look as the stance and ammo icons, Reminders.lua) showing the condition of the most worn piece of
-- equipment, as a percentage. It turns red under a threshold the player sets (default 25%) and is hidden while the gear is fine,
-- unless the icon is unlocked so it can be moved. Every class.
--
-- The condition of a piece is current / maximum durability (GetInventoryItemDurability); pieces that cannot wear out have
-- no durability and are skipped, so a character with nothing that wears shows nothing (a grey "-" while unlocked, to place it).
--
-- Read-only: only inventory getters, no protected calls, so it works in combat. Settings live in R2FDB.repair: shown, lock,
-- scale, x, y, threshold. Changed from the Reminders tab or /r2f repair, /r2f repair lock.

local _, R2F = ...
local L = R2F.L

local Repair = {}
R2F.Repair = Repair

local ICON = "Interface\\Icons\\Trade_BlackSmithing"
local LOW = { r = 0.9, g = 0.1, b = 0.1 }
local FINE = { r = 0.4, g = 0.4, b = 0.4 }
local SLOTS = 19    -- the equipment slots (head ... tabard); shirt and tabard have no durability and are skipped

Repair.MIN_SCALE, Repair.MAX_SCALE = R2F.Reminders.MIN_SCALE, R2F.Reminders.MAX_SCALE
Repair.MIN_THRESHOLD, Repair.MAX_THRESHOLD, Repair.THRESHOLD_STEP = 5, 90, 5

local frame

local function db()
  return R2F.Library.db.repair
end
Repair.Db = db

-- The worst condition of what you wear, in percent (0 .. 100), or nil when nothing you wear can wear out (or the game has no
-- durability getter).
function Repair.Worst()
  if not GetInventoryItemDurability then return nil end
  local worst
  for slot = 1, SLOTS do
    local ok, cur, max = pcall(GetInventoryItemDurability, slot)
    if ok and type(cur) == "number" and type(max) == "number" and max > 0 then
      local pct = cur / max * 100
      if not worst or pct < worst then worst = pct end
    end
  end
  return worst
end

function Repair.IsLow(pct)
  return pct ~= nil and pct < db().threshold
end

function Repair.Update()
  if not frame then return end
  local d = db()
  local pct = Repair.Worst()
  local low = Repair.IsLow(pct)
  local show = d.shown and (low or not d.lock)
  frame:SetShown(show)
  if not show then return end
  local c = low and LOW or FINE
  frame.border:SetColorTexture(c.r, c.g, c.b, 1)
  frame.icon:SetTexture(ICON)
  frame.count:SetText(pct == nil and "-" or (math.floor(pct + 0.5) .. "%"))
  if low then frame.count:SetTextColor(1, 0.3, 0.3) else frame.count:SetTextColor(1, 1, 1) end
  frame:EnableMouse(not d.lock)
end

-- PLAYER_LOGIN (Core.lua).
function Repair.Init()
  if frame then return end
  frame = R2F.Reminders.NewIcon("R2FRepairFrame", db, "REM_DRAG_TIP")
  frame:Place()
  local ev = CreateFrame("Frame")
  ev:SetScript("OnEvent", function() Repair.Update() end)
  for _, e in ipairs({ "UPDATE_INVENTORY_DURABILITY", "PLAYER_EQUIPMENT_CHANGED", "MERCHANT_SHOW", "MERCHANT_CLOSED",
                       "PLAYER_ENTERING_WORLD" }) do
    pcall(ev.RegisterEvent, ev, e)
  end
  Repair.Update()
end

-- Re-read settings after a change (Reminders tab, slash commands).
function Repair.Apply()
  if not frame then return end
  frame:Place()
  Repair.Update()
  R2F.Reminders.RefreshUI()
end

function Repair.SetShown(on)
  db().shown = on and true or false
  Repair.Apply()
end

function Repair.SetLock(on)
  db().lock = on and true or false
  Repair.Apply()
end

function Repair.SetScale(v)
  db().scale = R2F.Reminders.ClampScale(v)
  Repair.Apply()
end

-- Round to the slider's step and clamp to its range.
function Repair.SetThreshold(v)
  local step = Repair.THRESHOLD_STEP
  v = math.floor(v / step + 0.5) * step
  db().threshold = math.max(Repair.MIN_THRESHOLD, math.min(Repair.MAX_THRESHOLD, v))
  Repair.Apply()
end

-- /r2f repair, /r2f repair lock
function Repair.ToggleShown()
  Repair.SetShown(not db().shown)
  R2F.Print(db().shown and L.REPAIR_SHOWN or L.REPAIR_HIDDEN)
end

function Repair.ToggleLock()
  Repair.SetLock(not db().lock)
  R2F.Print(db().lock and L.REPAIR_LOCKED or L.REPAIR_UNLOCKED)
end

R2F.Reminders.Register({
  key = "repair", module = Repair,
  title = "REM_REPAIR_TITLE", show = "REPAIR_SHOW", lock = "REPAIR_LOCK", size = "REPAIR_SIZE",
  extra = {
    label = "REPAIR_THRESHOLD", name = "R2FRepairThreshold",
    min = Repair.MIN_THRESHOLD, max = Repair.MAX_THRESHOLD, step = Repair.THRESHOLD_STEP,
    get = function() return db().threshold end,
    set = function(v) Repair.SetThreshold(v) end,
  },
})
