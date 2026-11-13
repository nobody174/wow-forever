-- GameplayTravel.lua: two Gameplay features for getting around.
--
--   Flight timer   a small countdown while you ride a flight path. The game gives no flight time, so the
--                  addon LEARNS it: the first time you fly a route it counts up, and when you land the
--                  time is saved (R2FDB.flightTimes["From|To"]); every later flight on that route counts down.
--   Rare finder    when a rare or rare-elite enemy comes into range (its nameplate appears, or you target or
--                  mouse over it) a line appears on screen with a sound, and the mob gets the skull marker.
--
-- Same rules as Gameplay.lua: one switch each, OFF until ticked, handlers in pcall, written from scratch.
-- Read-only except the skull: it is only placed out of combat, only when you are alone or lead / assist the
-- group, and never over a marker that is already there.

local _, R2F = ...
local L = R2F.L
local Gameplay = R2F.Gameplay

local function isSecret(v)
  return type(_G.issecretvalue) == "function" and _G.issecretvalue(v) == true
end

local function now()
  return GetTime and GetTime() or 0
end

-- ---------------------------------------------------------------------------
-- Flight timer
-- ---------------------------------------------------------------------------

local pendingFrom, pendingTo   -- set when you pick a destination on the flight map
local flight                   -- { key =, to =, start =, known = seconds or nil } while in the air
local timerFrame, timerText, taxiHooked

local function flightTimes()
  local db = R2F.Library.db
  if type(db.flightTimes) ~= "table" then db.flightTimes = {} end
  return db.flightTimes
end

local function clock(seconds)
  seconds = math.max(0, math.floor(seconds + 0.5))
  return ("%d:%02d"):format(math.floor(seconds / 60), seconds % 60)
end

-- The name of the flight point you are standing at (the map marks it as CURRENT).
local function currentNodeName()
  if not (NumTaxiNodes and TaxiNodeGetType and TaxiNodeName) then return nil end
  for i = 1, NumTaxiNodes() or 0 do
    if TaxiNodeGetType(i) == "CURRENT" then
      local name = TaxiNodeName(i)
      if type(name) == "string" and not isSecret(name) then return name end
    end
  end
end

local function ensureTimer()
  if timerFrame then return end
  timerFrame = CreateFrame("Frame", "R2FFlightTimer", UIParent)
  timerFrame:SetSize(260, 24)
  timerFrame:SetPoint("TOP", UIParent, "TOP", 0, -150)
  timerFrame:Hide()
  timerText = timerFrame:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
  timerText:SetPoint("CENTER")
end

local function onTick()
  if not flight then return end
  local elapsed = now() - flight.start
  if flight.known then
    timerText:SetText(L.GP_FLIGHT_LEFT:format(flight.to, clock(flight.known - elapsed)))
  else
    timerText:SetText(L.GP_FLIGHT_LEARN:format(flight.to, clock(elapsed)))
  end
end

local function landed()
  if not flight then return end
  local elapsed = now() - flight.start
  -- Only a flight that really ran counts (a cancelled start or a loading blip would teach a wrong time).
  if flight.key and elapsed >= 8 then
    flightTimes()[flight.key] = math.floor(elapsed + 0.5)
    if not flight.known then R2F.Print(L.GP_FLIGHT_SAVED:format(flight.to, clock(elapsed))) end
  end
  flight = nil
  if timerFrame then timerFrame:Hide(); timerFrame:SetScript("OnUpdate", nil) end
end

local function takeoff()
  if not Gameplay.IsOn("flighttimer") or flight then return end
  local from, to = pendingFrom, pendingTo
  pendingFrom, pendingTo = nil, nil
  ensureTimer()
  local key = (from and to) and (from .. "|" .. to) or nil
  flight = { key = key, to = to or "?", start = now(), known = key and flightTimes()[key] or nil }
  timerFrame:Show()
  local acc = 0
  timerFrame:SetScript("OnUpdate", function(_, dt)
    acc = acc + (dt or 0)
    if acc < 0.25 then return end
    acc = 0
    local onTaxi = UnitOnTaxi and UnitOnTaxi("player")
    if not onTaxi and now() - flight.start > 2 then return landed() end
    onTick()
  end)
  onTick()
end

-- PLAYER_CONTROL_LOST comes at take-off (and for fears, stuns...), so ask whether we are on a taxi a moment later.
local function controlLost()
  if C_Timer and C_Timer.After then
    C_Timer.After(0.5, function() if UnitOnTaxi and UnitOnTaxi("player") then takeoff() end end)
  elseif UnitOnTaxi and UnitOnTaxi("player") then
    takeoff()
  end
end

Gameplay.Register({
  key = "flighttimer", group = "screen", title = "GP_FLIGHT", tip = "GP_FLIGHT_TIP",
  available = function() return UnitOnTaxi ~= nil and TakeTaxiNode ~= nil and hooksecurefunc ~= nil end,
  events = {
    PLAYER_CONTROL_LOST = controlLost,
    PLAYER_ENTERING_WORLD = function() if flight and not (UnitOnTaxi and UnitOnTaxi("player")) then landed() end end,
  },
  onToggle = function(on)
    if on and not taxiHooked and _G.TakeTaxiNode then
      taxiHooked = true
      -- A hook after the game's own call: we only note which node you picked.
      hooksecurefunc("TakeTaxiNode", function(index)
        if not Gameplay.IsOn("flighttimer") then return end
        local ok, name = pcall(TaxiNodeName, index)
        pendingTo = ok and type(name) == "string" and not isSecret(name) and name or nil
        pendingFrom = currentNodeName()
      end)
    end
    if not on then
      flight = nil
      if timerFrame then timerFrame:Hide(); timerFrame:SetScript("OnUpdate", nil) end
    end
  end,
})

-- ---------------------------------------------------------------------------
-- Rare finder
-- ---------------------------------------------------------------------------

local SKULL = 8
local REMEMBER = 300           -- seconds before the same rare may be announced again
local announced = {}           -- guid -> time

local function canMark()
  if R2F.InCombat and R2F.InCombat() then return false end
  if IsInGroup and IsInGroup() then
    return (UnitIsGroupLeader and UnitIsGroupLeader("player"))
      or (UnitIsGroupAssistant and UnitIsGroupAssistant("player")) or false
  end
  return true
end

-- Says it once per rare (per REMEMBER seconds). Returns true when it did.
local function announce(guid, name, where)
  local t = now()
  if announced[guid] and t - announced[guid] < REMEMBER then return false end
  announced[guid] = t
  local text = L.GP_RARE_FOUND:format(name or L.GP_RARE_UNKNOWN)
  if where then text = text .. " (" .. where .. ")" end
  R2F.Print(text)
  local frame = _G.UIErrorsFrame
  if frame and frame.AddMessage then frame:AddMessage(text, 1, 0.82, 0, 1) end
  if PlaySound and _G.SOUNDKIT and _G.SOUNDKIT.RAID_WARNING then pcall(PlaySound, _G.SOUNDKIT.RAID_WARNING) end
  return true
end

-- Looks at one unit token; announces it when it is a living rare that we have not announced lately.
local function inspect(unit)
  if type(unit) ~= "string" or not UnitExists or not UnitExists(unit) then return end
  local ok, class = pcall(UnitClassification, unit)
  if not ok or isSecret(class) or (class ~= "rare" and class ~= "rareelite") then return end
  if UnitIsPlayer(unit) or UnitIsDead(unit) or not UnitCanAttack("player", unit) then return end
  local okG, guid = pcall(UnitGUID, unit)
  if not okG or type(guid) ~= "string" or isSecret(guid) then return end
  local okN, name = pcall(UnitName, unit)
  if not okN or type(name) ~= "string" or isSecret(name) then name = nil end
  if not announce(guid, name, nil) then return end

  if canMark() and SetRaidTarget and GetRaidTargetIndex and not GetRaidTargetIndex(unit) then
    pcall(SetRaidTarget, unit, SKULL)
  end
end
Gameplay.InspectRare = inspect

-- The game also marks rares on the MINIMAP, from much further away than a nameplate reaches. Each marker
-- (a "vignette") has the creature's GUID, name and whether it is dead. A creature marker on the minimap
-- that is not dead counts as a rare. Where the game gives a position, it is added to the message.
local function vignettePosition(vguid)
  if not (C_Map and C_Map.GetBestMapForUnit and C_VignetteInfo.GetVignettePosition) then return nil end
  local okM, map = pcall(C_Map.GetBestMapForUnit, "player")
  if not okM or not map then return nil end
  local okP, pos = pcall(C_VignetteInfo.GetVignettePosition, vguid, map)
  if not okP or type(pos) ~= "table" then return nil end
  local x, y
  if pos.GetXY then x, y = pos:GetXY() else x, y = pos.x, pos.y end
  if type(x) ~= "number" or type(y) ~= "number" or isSecret(x) or isSecret(y) then return nil end
  if x <= 0 or y <= 0 or x >= 1 or y >= 1 then return nil end
  return ("%.1f, %.1f"):format(x * 100, y * 100)
end

local function checkVignette(vguid)
  if not (C_VignetteInfo and C_VignetteInfo.GetVignetteInfo) then return end
  local ok, info = pcall(C_VignetteInfo.GetVignetteInfo, vguid)
  if not ok or type(info) ~= "table" then return end
  if info.onMinimap ~= true or info.isDead == true then return end
  local guid = info.objectGUID
  if type(guid) ~= "string" or isSecret(guid) or guid:sub(1, 8) ~= "Creature" then return end
  local name = type(info.name) == "string" and not isSecret(info.name) and info.name or nil
  announce(guid, name, vignettePosition(vguid))
end

local function scanVignettes()
  if not (C_VignetteInfo and C_VignetteInfo.GetVignettes) then return end
  local ok, list = pcall(C_VignetteInfo.GetVignettes)
  if not ok or type(list) ~= "table" then return end
  for _, vguid in ipairs(list) do checkVignette(vguid) end
end
Gameplay.ScanRareVignettes = scanVignettes

Gameplay.Register({
  key = "rarefinder", group = "screen", title = "GP_RARE", tip = "GP_RARE_TIP",
  available = function() return UnitClassification ~= nil and UnitGUID ~= nil end,
  events = {
    NAME_PLATE_UNIT_ADDED = inspect,
    PLAYER_TARGET_CHANGED = function() inspect("target") end,
    UPDATE_MOUSEOVER_UNIT = function() inspect("mouseover") end,
    VIGNETTE_MINIMAP_UPDATED = function(vguid) if vguid then checkVignette(vguid) end end,
    VIGNETTES_UPDATED = scanVignettes,
    PLAYER_ENTERING_WORLD = scanVignettes,
  },
  onToggle = function(on) if on then scanVignettes() end end,
})
