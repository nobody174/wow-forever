-- Aspect.lua: Hunter aspect reminder.
--
-- A framed icon (the look of the stance, pet and ammo icons, Reminders.lua) that appears when your aspect needs you:
--   "none"    you know an aspect but none is up (not mounted, not dead, not feigning death)
--   "cheetah" Aspect of the Cheetah / Pack is up while you are in combat: it dazes you when hit, swap to Hawk
-- Hidden otherwise, unless the icon is unlocked so it can be moved. Hunters only; the frame is never made for other classes.
--
-- Read-only: unit getters and your own aura names (Buffs.MyAuraNames: nothing is said when the game hides them). No
-- protected calls, so it works in combat. Aura names are matched in English (the game's spell names).
-- Settings live in R2FDB.aspect: shown, lock, scale, x, y. Changed from the Reminders tab or /r2f aspect, /r2f aspect lock.

local _, R2F = ...
local L = R2F.L

local Aspect = {}
R2F.Aspect = Aspect

local ICONS = { none = "Interface\\Icons\\Spell_Nature_RavenForm", cheetah = "Interface\\Icons\\Ability_Mount_JungleTiger" }
local BAD = { r = 0.9, g = 0.1, b = 0.1 }
local WARN = { r = 0.95, g = 0.75, b = 0.1 }
local FINE = { r = 0.4, g = 0.4, b = 0.4 }

-- The aspects that must not stay up in a fight (they daze you when you are hit).
local RUNNING = { ["Aspect of the Cheetah"] = true, ["Aspect of the Pack"] = true }

Aspect.MIN_SCALE, Aspect.MAX_SCALE = R2F.Reminders.MIN_SCALE, R2F.Reminders.MAX_SCALE

local frame

local function db()
  return R2F.Library.db.aspect
end
Aspect.Db = db

function Aspect.Applies()
  return R2F.playerClass == "HUNTER"
end

local function call(fn, ...)
  if not fn then return nil end
  local ok, a = pcall(fn, ...)
  if ok then return a end
  return nil
end

-- Does the hunter know any aspect yet? (Aspect of the Hawk is the first, at level 10.)
local function knowsAspect()
  local known = _G.IsPlayerSpell or _G.IsSpellKnown
  if not known then return true end            -- cannot tell: assume yes rather than stay silent
  for _, name in ipairs({ "Aspect of the Hawk", "Aspect of the Monkey", "Aspect of the Cheetah" }) do
    local id
    if _G.C_Spell and _G.C_Spell.GetSpellInfo then
      local ok, info = pcall(_G.C_Spell.GetSpellInfo, name)
      id = ok and type(info) == "table" and info.spellID or nil
    elseif _G.GetSpellInfo then
      local ok, _, _, _, _, _, _, spellId = pcall(_G.GetSpellInfo, name)
      id = ok and spellId or nil
    end
    if id and call(known, id) then return true end
  end
  return false
end

-- What is wrong: "none", "cheetah", or nil (fine, or nothing to say right now).
function Aspect.Problem()
  if call(_G.UnitIsDeadOrGhost, "player") or call(_G.IsMounted) then return nil end
  local names = R2F.Buffs and R2F.Buffs.MyAuraNames()
  if not names then return nil end             -- the game hides the auras: say nothing rather than guess
  local have, running = false, false
  for _, n in ipairs(names) do
    if n:find("^Aspect of ") then
      have = true
      if RUNNING[n] then running = true end
    elseif n == "Feign Death" then
      return nil
    end
  end
  if running and call(_G.UnitAffectingCombat, "player") then return "cheetah" end
  if not have and knowsAspect() then return "none" end
  return nil
end

function Aspect.Update()
  if not frame then return end
  local d = db()
  local problem = Aspect.Problem()
  local show = d.shown and (problem ~= nil or not d.lock)
  frame:SetShown(show)
  if not show then return end
  local c = (problem == "none" and BAD) or (problem == "cheetah" and WARN) or FINE
  frame.border:SetColorTexture(c.r, c.g, c.b, 1)
  frame.icon:SetTexture(ICONS[problem or "none"])
  frame.count:SetText(problem and L["ASPECT_" .. problem:upper()] or "-")
  if problem then frame.count:SetTextColor(1, 0.3, 0.3) else frame.count:SetTextColor(1, 1, 1) end
  frame:EnableMouse(not d.lock)
end

-- PLAYER_LOGIN (Core.lua).
function Aspect.Init()
  if not Aspect.Applies() or frame then return end
  frame = R2F.Reminders.NewIcon("R2FAspectFrame", db, "REM_DRAG_TIP")
  frame:Place()
  local ev = CreateFrame("Frame")
  -- UNIT_AURA fires many times a second in combat: bursts are merged into one refresh.
  local queued = false
  ev:SetScript("OnEvent", function(_, event)
    if event ~= "UNIT_AURA" or not (C_Timer and C_Timer.After) then Aspect.Update() return end
    if queued then return end
    queued = true
    C_Timer.After(0.2, function() queued = false; Aspect.Update() end)
  end)
  for _, e in ipairs({ "PLAYER_REGEN_DISABLED", "PLAYER_REGEN_ENABLED", "PLAYER_ENTERING_WORLD", "PLAYER_DEAD",
                       "PLAYER_ALIVE", "PLAYER_UNGHOST", "PLAYER_MOUNT_DISPLAY_CHANGED", "SPELLS_CHANGED" }) do
    pcall(ev.RegisterEvent, ev, e)
  end
  if not pcall(ev.RegisterUnitEvent, ev, "UNIT_AURA", "player") then pcall(ev.RegisterEvent, ev, "UNIT_AURA") end
  Aspect.Update()
end

-- Re-read settings after a change (Reminders tab, slash commands).
function Aspect.Apply()
  if not frame then return end
  frame:Place()
  Aspect.Update()
  R2F.Reminders.RefreshUI()
end

function Aspect.SetShown(on)
  db().shown = on and true or false
  Aspect.Apply()
end

function Aspect.SetLock(on)
  db().lock = on and true or false
  Aspect.Apply()
end

function Aspect.SetScale(v)
  db().scale = R2F.Reminders.ClampScale(v)
  Aspect.Apply()
end

-- /r2f aspect, /r2f aspect lock
function Aspect.ToggleShown()
  if not Aspect.Applies() then R2F.Print(L.ASPECT_ONLY) return end
  Aspect.SetShown(not db().shown)
  R2F.Print(db().shown and L.ASPECT_SHOWN or L.ASPECT_HIDDEN)
end

function Aspect.ToggleLock()
  if not Aspect.Applies() then R2F.Print(L.ASPECT_ONLY) return end
  Aspect.SetLock(not db().lock)
  R2F.Print(db().lock and L.ASPECT_LOCKED or L.ASPECT_UNLOCKED)
end

R2F.Reminders.Register({
  key = "aspect", class = "HUNTER", module = Aspect,
  title = "REM_ASPECT_TITLE", show = "ASPECT_SHOW", lock = "ASPECT_LOCK", size = "ASPECT_SIZE",
})
