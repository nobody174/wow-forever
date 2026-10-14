-- Pet.lua: "pet missing / dead / unhappy" reminder, for Hunters and Warlocks.
--
-- A framed icon (the same look as the stance, ammo and repair icons, Reminders.lua) that appears when your pet needs you:
-- no pet out, a dead pet, or a pet that is not happy. Hidden while the pet is fine, unless the icon is unlocked so it can
-- be moved.
-- It stays quiet when you cannot do anything about it anyway: dead or a ghost yourself, or mounted (a pet is normally put away
-- while you ride).
--
-- Read-only: only unit getters, no protected calls, so it works in combat. Settings live in R2FDB.pet: shown, lock, scale, x, y.
-- Changed from the Reminders tab or /r2f pet, /r2f pet lock.

local _, R2F = ...
local L = R2F.L

local Pet = {}
R2F.Pet = Pet

local ICONS = { missing = "Interface\\Icons\\Ability_Hunter_BeastCall", dead = "Interface\\Icons\\Ability_Hunter_BeastSoothe",
                unhappy = "Interface\\Icons\\Ability_Hunter_MendPet" }
local BAD = { r = 0.9, g = 0.1, b = 0.1 }
local FINE = { r = 0.4, g = 0.4, b = 0.4 }

Pet.MIN_SCALE, Pet.MAX_SCALE = R2F.Reminders.MIN_SCALE, R2F.Reminders.MAX_SCALE

local frame

local function db()
  return R2F.Library.db.pet
end
Pet.Db = db

function Pet.Applies()
  return R2F.playerClass == "HUNTER" or R2F.playerClass == "WARLOCK"
end

-- What is wrong with the pet: "missing", "dead", "unhappy", or nil (fine, or nothing to say right now).
function Pet.Problem()
  local function call(fn, ...)
    if not fn then return nil end
    local ok, a = pcall(fn, ...)
    if ok then return a end
    return nil
  end
  if call(_G.UnitIsDeadOrGhost, "player") or call(_G.IsMounted) then return nil end
  if not call(_G.UnitExists, "pet") then return "missing" end
  if call(_G.UnitIsDead, "pet") then return "dead" end
  -- Hunter pets only: 1 = unhappy, 2 = content, 3 = happy (the game has no happiness for a warlock's demon).
  if R2F.playerClass == "HUNTER" and call(_G.GetPetHappiness) == 1 then return "unhappy" end
  return nil
end

function Pet.Update()
  if not frame then return end
  local d = db()
  local problem = Pet.Problem()
  local show = d.shown and (problem ~= nil or not d.lock)
  frame:SetShown(show)
  if not show then return end
  local c = problem and BAD or FINE
  frame.border:SetColorTexture(c.r, c.g, c.b, 1)
  frame.icon:SetTexture(ICONS[problem or "missing"])
  frame.count:SetText(problem and L["PET_" .. problem:upper()] or "-")
  if problem then frame.count:SetTextColor(1, 0.3, 0.3) else frame.count:SetTextColor(1, 1, 1) end
  frame:EnableMouse(not d.lock)
end

-- PLAYER_LOGIN (Core.lua).
function Pet.Init()
  if not Pet.Applies() or frame then return end
  frame = R2F.Reminders.NewIcon("R2FPetFrame", db, "REM_DRAG_TIP")
  frame:Place()
  local ev = CreateFrame("Frame")
  ev:SetScript("OnEvent", function(_, event, unit)
    if (event == "UNIT_HEALTH" or event == "UNIT_PET" or event == "UNIT_HAPPINESS") and unit ~= "pet" and unit ~= "player" then
      return
    end
    Pet.Update()
  end)
  for _, e in ipairs({ "UNIT_PET", "UNIT_HEALTH", "UNIT_HAPPINESS", "PLAYER_ENTERING_WORLD", "PLAYER_DEAD", "PLAYER_ALIVE",
                       "PLAYER_UNGHOST", "PLAYER_MOUNT_DISPLAY_CHANGED" }) do
    pcall(ev.RegisterEvent, ev, e)
  end
  Pet.Update()
end

-- Re-read settings after a change (Reminders tab, slash commands).
function Pet.Apply()
  if not frame then return end
  frame:Place()
  Pet.Update()
  R2F.Reminders.RefreshUI()
end

function Pet.SetShown(on)
  db().shown = on and true or false
  Pet.Apply()
end

function Pet.SetLock(on)
  db().lock = on and true or false
  Pet.Apply()
end

function Pet.SetScale(v)
  db().scale = R2F.Reminders.ClampScale(v)
  Pet.Apply()
end

-- /r2f pet, /r2f pet lock
function Pet.ToggleShown()
  if not Pet.Applies() then R2F.Print(L.PET_ONLY) return end
  Pet.SetShown(not db().shown)
  R2F.Print(db().shown and L.PET_SHOWN or L.PET_HIDDEN)
end

function Pet.ToggleLock()
  if not Pet.Applies() then R2F.Print(L.PET_ONLY) return end
  Pet.SetLock(not db().lock)
  R2F.Print(db().lock and L.PET_LOCKED or L.PET_UNLOCKED)
end

R2F.Reminders.Register({
  key = "pet", applies = Pet.Applies, module = Pet,
  title = "REM_PET_TITLE", show = "PET_SHOW", lock = "PET_LOCK", size = "PET_SIZE",
})
