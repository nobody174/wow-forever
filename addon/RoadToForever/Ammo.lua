-- Ammo.lua: Hunter "ammo low" reminder (ADDON_PLAN.md 15.4, v0.17.0).
--
-- A framed icon (the same look as the stance icon, Reminders.lua) showing how
-- many arrows / bullets are left. It turns red under a threshold the player sets
-- (default 200) and is hidden while the ammo is fine, unless the icon is
-- unlocked so it can be moved. Hunters only.
--
-- The count is every piece of the ammunition the equipped ranged weapon fires, added up over
-- all bags (quivers and pouches included): arrows for a bow or crossbow, bullets for a gun.
-- v0.24.1: this client has NO ammo slot (owner test: GetInventoryItemID("player", 0) is 0 and
-- the count is 1), so 0.17.0-0.24.0 showed a wrong "1". Ammunition is item class 6
-- (subclass 2 arrows, 3 bullets) and the ranged weapon is slot 18 (class 2: subclass 2 bow,
-- 18 crossbow, 3 gun); the bags are read with C_Container.GetContainerItemInfo.
-- No ranged weapon (or a thrown weapon, a wand) = nothing to count: the icon stays hidden
-- (shown grey with "-" while unlocked so it can be placed). A ranged weapon and no ammo = red 0.
--
-- Read-only: only item and inventory getters, no protected calls, so it works in
-- combat. Settings live in R2FDB.ammo: shown, lock, scale, x, y, threshold. Changed
-- from the Reminders tab or /r2f ammo, /r2f ammo lock.

local _, R2F = ...
local L = R2F.L

local Ammo = {}
R2F.Ammo = Ammo

local RANGED_SLOT = 18
local ITEM_CLASS_WEAPON, ITEM_CLASS_AMMO = 2, 6
-- ranged weapon subclass -> ammunition subclass
local AMMO_FOR = { [2] = 2, [18] = 2, [3] = 3 }
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

-- classID, subclassID, icon of an item id (the instant lookup needs no server data).
local function instant(id)
  local get = (C_Item and C_Item.GetItemInfoInstant) or GetItemInfoInstant
  if not get then return nil end
  local ok, a, b, c, d, icon, classID, subClassID = pcall(get, id)
  if not ok then return nil end
  if type(a) == "table" then return a.classID, a.subclassID, a.icon end
  return classID, subClassID, icon
end

-- Pieces of ammunition for the equipped ranged weapon over all bags, and the ammunition's
-- icon; nil when there is nothing to count (no ranged weapon, or one that needs no ammo, or
-- the item or bag functions are missing / fail).
function Ammo.Count()
  local ok, count, icon = pcall(function()
    if not (GetInventoryItemID and C_Container and C_Container.GetContainerNumSlots) then return nil end
    local weapon = GetInventoryItemID("player", RANGED_SLOT)
    if not weapon or weapon == 0 then return nil end
    local class, sub = instant(weapon)
    local want = (class == ITEM_CLASS_WEAPON) and AMMO_FOR[sub] or nil
    if not want then return nil end
    local total, found = 0, nil
    for bag = 0, (NUM_BAG_SLOTS or 4) do
      for slot = 1, C_Container.GetContainerNumSlots(bag) or 0 do
        local info = C_Container.GetContainerItemInfo(bag, slot)
        if info and info.itemID then
          local c, s, tex = instant(info.itemID)
          if c == ITEM_CLASS_AMMO and s == want then
            total = total + (info.stackCount or 1)
            found = found or tex or info.iconFileID
          end
        end
      end
    end
    return total, found
  end)
  if not ok then return nil end
  return count, icon
end

function Ammo.IsLow(count)
  return count ~= nil and count < db().threshold
end

function Ammo.Update()
  if not frame then return end
  local d = db()
  local count, tex = Ammo.Count()
  local low = Ammo.IsLow(count)
  local show = d.shown and (low or not d.lock)
  frame:SetShown(show)
  if not show then return end
  local c = low and LOW or FINE
  frame.border:SetColorTexture(c.r, c.g, c.b, 1)
  frame.icon:SetTexture(tex or FALLBACK_ICON)
  frame.count:SetText(count == nil and "-" or tostring(count))
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
