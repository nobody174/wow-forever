-- Ammo.lua: Hunter "ammo low" reminder (ADDON_PLAN.md 15.4, v0.17.0).
--
-- A framed icon (the same look as the stance icon, Reminders.lua) showing how
-- many arrows / bullets are left. It turns red under a threshold the player sets
-- (default 200) and is hidden while the ammo is fine, unless the icon is
-- unlocked so it can be moved. Hunters only.
--
-- The count is the equipped ammo (ammo slot 0): GetInventoryItemCount on that
-- slot is the total of that ammo across the quiver / ammo pouch and bags, which
-- is what a hunter means by "how much do I have left". An empty ammo slot counts
-- as 0, so a hunter out of ammo gets the red icon with "0" (a hunter who doesn't
-- use a ranged weapon can switch the reminder off on the Reminders tab).
--
-- Read-only: only item and inventory getters, no protected calls, so it works in
-- combat. Settings live in R2FDB.ammo: shown, lock, scale, x, y, threshold. Changed
-- from the Reminders tab or /r2f ammo, /r2f ammo lock.

local _, R2F = ...
local L = R2F.L

local Ammo = {}
R2F.Ammo = Ammo

local AMMO_SLOT = 0
local FALLBACK_ICON = "Interface\\Icons\\INV_Ammo_Arrow_02"
local LOW = { r = 0.9, g = 0.1, b = 0.1 }
local FINE = { r = 0.4, g = 0.4, b = 0.4 }

Ammo.MIN_SCALE, Ammo.MAX_SCALE = R2F.Reminders.MIN_SCALE, R2F.Reminders.MAX_SCALE
Ammo.MIN_THRESHOLD, Ammo.MAX_THRESHOLD, Ammo.THRESHOLD_STEP = 50, 1000, 50

local frame

local function db()
  return R2F.Library.db.ammo
end
Ammo.Db = db

function Ammo.IsHunter()
  return R2F.playerClass == "HUNTER"
end

-- Number of the equipped ammo left (0 with none equipped), and its item id.
function Ammo.Count()
  local ok, id = pcall(function() return GetInventoryItemID and GetInventoryItemID("player", AMMO_SLOT) end)
  if not ok or not id then return 0, nil end
  local ok2, n = pcall(function() return GetInventoryItemCount and GetInventoryItemCount("player", AMMO_SLOT) end)
  return (ok2 and tonumber(n)) or 0, id
end

function Ammo.IsLow(count)
  return count < db().threshold
end

function Ammo.Update()
  if not frame then return end
  local d = db()
  local count = Ammo.Count()
  local low = Ammo.IsLow(count)
  local show = d.shown and (low or not d.lock)
  frame:SetShown(show)
  if not show then return end
  local c = low and LOW or FINE
  frame.border:SetColorTexture(c.r, c.g, c.b, 1)
  local tex = GetInventoryItemTexture and GetInventoryItemTexture("player", AMMO_SLOT)
  frame.icon:SetTexture(tex or FALLBACK_ICON)
  frame.count:SetText(tostring(count))
  if low then frame.count:SetTextColor(1, 0.3, 0.3) else frame.count:SetTextColor(1, 1, 1) end
  frame:EnableMouse(not d.lock)
end

-- PLAYER_LOGIN (Core.lua).
function Ammo.Init()
  if not Ammo.IsHunter() or frame then return end
  frame = R2F.Reminders.NewIcon("R2FAmmoFrame", db, "REM_DRAG_TIP")
  frame:Place()
  local ev = CreateFrame("Frame")
  ev:SetScript("OnEvent", Ammo.Update)
  -- BAG_UPDATE fires when a shot uses up ammo; the others cover swapping ammo.
  for _, e in ipairs({ "BAG_UPDATE", "UNIT_INVENTORY_CHANGED", "PLAYER_EQUIPMENT_CHANGED", "PLAYER_ENTERING_WORLD" }) do
    pcall(ev.RegisterEvent, ev, e)
  end
  Ammo.Update()
end

-- Re-read settings after a change (Reminders tab, slash commands).
function Ammo.Apply()
  if not frame then return end
  frame:Place()
  Ammo.Update()
  R2F.Reminders.RefreshUI()
end

function Ammo.SetShown(on)
  db().shown = on and true or false
  Ammo.Apply()
end

function Ammo.SetLock(on)
  db().lock = on and true or false
  Ammo.Apply()
end

function Ammo.SetScale(v)
  db().scale = R2F.Reminders.ClampScale(v)
  Ammo.Apply()
end

-- Round to the slider's step and clamp to its range.
function Ammo.SetThreshold(v)
  local step = Ammo.THRESHOLD_STEP
  v = math.floor(v / step + 0.5) * step
  db().threshold = math.max(Ammo.MIN_THRESHOLD, math.min(Ammo.MAX_THRESHOLD, v))
  Ammo.Apply()
end

-- /r2f ammo, /r2f ammo lock
function Ammo.ToggleShown()
  if not Ammo.IsHunter() then R2F.Print(L.AMMO_HUNTER_ONLY) return end
  Ammo.SetShown(not db().shown)
  R2F.Print(db().shown and L.AMMO_SHOWN or L.AMMO_HIDDEN)
end

function Ammo.ToggleLock()
  if not Ammo.IsHunter() then R2F.Print(L.AMMO_HUNTER_ONLY) return end
  Ammo.SetLock(not db().lock)
  R2F.Print(db().lock and L.AMMO_LOCKED or L.AMMO_UNLOCKED)
end

R2F.Reminders.Register({
  key = "ammo", class = "HUNTER", module = Ammo,
  title = "REM_AMMO_TITLE", show = "AMMO_SHOW", lock = "AMMO_LOCK", size = "AMMO_SIZE",
  extra = {
    label = "AMMO_THRESHOLD", name = "R2FAmmoThreshold",
    min = Ammo.MIN_THRESHOLD, max = Ammo.MAX_THRESHOLD, step = Ammo.THRESHOLD_STEP,
    get = function() return db().threshold end,
    set = function(v) Ammo.SetThreshold(v) end,
  },
})
