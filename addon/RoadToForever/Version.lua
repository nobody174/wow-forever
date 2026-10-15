-- Version.lua: "is there a newer Road to Forever?", without the internet.
--
-- An addon cannot reach GitHub, so it asks the people around you instead: at login (guild) and when your group changes (party /
-- raid) every copy of the addon says which version it is, over the addon channel (prefix R2FV, a tiny "V<tab>0.64.0" message).
-- When you hear a higher version than yours, the chat says so once per session and Home shows a gold line with the release page.
-- Nothing is sent or read unless the Tweaks > Chat & screen box "Tell me when a newer version exists" is ticked (it is, by default).
-- Everything received is validated (three numbers separated by dots) and only compared, never run.

local _, R2F = ...
local L = R2F.L

local Version = {}
R2F.Version = Version

Version.PREFIX = "R2FV"
Version.URL = "github.com/nobody174/wow-forever/releases"
local THROTTLE = 60          -- seconds between two group announcements
local lastSent = 0
local told = false           -- the chat line comes once per session

-- "0.64.0" -> { 0, 64, 0 }, nil when it is not three plain numbers.
function Version.Parse(s)
  if type(s) ~= "string" then return nil end
  local a, b, c = s:match("^(%d+)%.(%d+)%.(%d+)$")
  if not a then return nil end
  return { tonumber(a), tonumber(b), tonumber(c) }
end

-- 1 when a is newer than b, -1 when older, 0 when equal (nil when either is not a version).
function Version.Compare(a, b)
  local pa, pb = Version.Parse(a), Version.Parse(b)
  if not (pa and pb) then return nil end
  for i = 1, 3 do
    if pa[i] ~= pb[i] then return pa[i] > pb[i] and 1 or -1 end
  end
  return 0
end

-- The version in the TOC of this copy of the addon.
function Version.Mine()
  local get = (_G.C_AddOns and _G.C_AddOns.GetAddOnMetadata) or _G.GetAddOnMetadata
  if not get then return nil end
  local ok, v = pcall(get, "RoadToForever", "Version")
  if ok and Version.Parse(v) then return v end
end

local function enabled()
  return R2F.Gameplay and R2F.Gameplay.IsOn("updatecheck")
end

-- The newest version heard of so far that is newer than this one (the account saves it), or nil.
function Version.Newer()
  local mine, seen = Version.Mine(), R2F.Library.db.newerVersion
  if mine and seen and Version.Compare(seen, mine) == 1 then return seen end
end

local function announce()
  if not enabled() then return end
  local send = _G.C_ChatInfo and _G.C_ChatInfo.SendAddonMessage
  local mine = Version.Mine()
  if not (send and mine) then return end
  local msg = "V\t" .. mine
  if _G.IsInGuild and _G.IsInGuild() then pcall(send, Version.PREFIX, msg, "GUILD") end
  local channel
  if _G.IsInRaid and _G.IsInRaid() then channel = "RAID"
  elseif _G.IsInGroup and _G.IsInGroup() then channel = "PARTY" end
  if channel then pcall(send, Version.PREFIX, msg, channel) end
end

-- CHAT_MSG_ADDON(prefix, message, channel, sender)
function Version.OnAddonMessage(prefix, msg, _, sender)
  if prefix ~= Version.PREFIX or type(msg) ~= "string" or not enabled() then return end
  local me = _G.UnitName and _G.UnitName("player")
  local short = type(sender) == "string" and (sender:match("^([^-]+)") or sender) or nil
  if short and short == me then return end
  local ver = msg:match("^V\t(%d+%.%d+%.%d+)$")
  local mine = Version.Mine()
  if not (ver and mine) or Version.Compare(ver, mine) ~= 1 then return end
  local db = R2F.Library.db
  if not db.newerVersion or Version.Compare(ver, db.newerVersion) == 1 then db.newerVersion = ver end
  if not told then
    told = true
    R2F.Print(L.VERSION_NEWER:format(db.newerVersion, mine, Version.URL))
  end
  if R2F.Home and R2F.Home.RequestRefresh then R2F.Home.RequestRefresh() end
end

-- /r2f update
function Version.Report()
  local mine = Version.Mine() or "?"
  local newer = Version.Newer()
  if newer then
    R2F.Print(L.VERSION_NEWER:format(newer, mine, Version.URL))
  else
    R2F.Print(L.VERSION_CURRENT:format(mine))
  end
end

-- PLAYER_LOGIN (Core.lua).
function Version.Init()
  local db = R2F.Library.db
  -- A version heard earlier that this copy has caught up with is forgotten.
  local mine = Version.Mine()
  if mine and db.newerVersion and Version.Compare(db.newerVersion, mine) ~= 1 then db.newerVersion = nil end
  local reg = _G.C_ChatInfo and _G.C_ChatInfo.RegisterAddonMessagePrefix
  if reg then pcall(reg, Version.PREFIX) end
  local ev = CreateFrame("Frame")
  ev:SetScript("OnEvent", function(_, event, ...)
    if event == "CHAT_MSG_ADDON" then
      Version.OnAddonMessage(...)
    elseif event == "GROUP_ROSTER_UPDATE" then
      local now = GetTime and GetTime() or 0
      if now - lastSent >= THROTTLE then
        lastSent = now
        announce()
      end
    end
  end)
  for _, e in ipairs({ "CHAT_MSG_ADDON", "GROUP_ROSTER_UPDATE" }) do pcall(ev.RegisterEvent, ev, e) end
  -- A few seconds after login the guild channel is ready.
  if C_Timer and C_Timer.After then C_Timer.After(8, announce) end
end

R2F.Gameplay.Register({
  key = "updatecheck", group = "screen", title = "VERSION_TITLE", tip = "VERSION_TIP",
})
