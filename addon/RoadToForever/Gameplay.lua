-- Gameplay.lua: the Gameplay features that replace ForeverPlus (ADDON_PLAN.md 17, v0.21.0).
--
-- A small registry plus the first five features (build order step 1). Every feature has
-- ONE switch, stored in R2FDB.gameplay[key] (true / false), and ships OFF: nothing here
-- acts until the player ticks it on the Gameplay tab. Features register what they need:
--   key        "repair" ...
--   group      "auto" (acts for you) or "screen" (changes what you see)
--   title, tip L keys for the tab
--   events     { EVENT_NAME = function(...) }, called only while the feature is on
--   onToggle   function(on), called when switched and once at login while on
--   available  function() -> bool, false greys the box (the client lacks what it needs)
--   noCombat   true: can't be switched in combat (it changes a game setting)
-- Every handler runs in pcall: one bug in one feature can't stop the others or the addon.
--
-- Written from scratch for this addon. ForeverPlus (a separate addon, All Rights Reserved)
-- was only used to learn WHAT these features do and which traps exist on this client:
-- merchant state is tracked from events (frame visibility isn't reliable), nothing calls
-- the game's bag code, and a quest turn-in never picks a reward.

local _, R2F = ...
local L = R2F.L

local Gameplay = {}
R2F.Gameplay = Gameplay

Gameplay.FEATURES = {}
local byKey = {}
local failed = {}   -- key -> true once an error was reported for it

function Gameplay.Register(def)
  Gameplay.FEATURES[#Gameplay.FEATURES + 1] = def
  byKey[def.key] = def
end

function Gameplay.IsOn(key)
  local g = R2F.Library.db.gameplay
  return g ~= nil and g[key] == true
end

function Gameplay.Available(def)
  if not def.available then return true end
  local ok, yes = pcall(def.available)
  return ok and yes and true or false
end

function Gameplay.SetOn(key, on)
  local def = byKey[key]
  if not def then return false end
  if on and not Gameplay.Available(def) then return false end
  if def.noCombat and InCombatLockdown() then R2F.Error(L.QS_COMBAT); return false end
  R2F.Library.db.gameplay[key] = on and true or false
  if def.onToggle then
    local ok, err = pcall(def.onToggle, on and true or false)
    if not ok then Gameplay.Report(key, err) end
  end
  if R2F.GameplayTab and R2F.GameplayTab.Refresh then R2F.GameplayTab.Refresh() end
  return true
end

-- One chat line per feature per session when a handler fails.
function Gameplay.Report(key, err)
  if failed[key] then return end
  failed[key] = true
  R2F.Print(L.GP_ERROR:format(key, tostring(err)))
end

-- "1g 20s 5c" for an amount in copper.
function Gameplay.Money(copper)
  copper = math.floor(tonumber(copper) or 0)
  local g, s, c = math.floor(copper / 10000), math.floor(copper / 100) % 100, copper % 100
  local parts = {}
  if g > 0 then parts[#parts + 1] = g .. "g" end
  if s > 0 then parts[#parts + 1] = s .. "s" end
  if c > 0 or #parts == 0 then parts[#parts + 1] = c .. "c" end
  return table.concat(parts, " ")
end

-- ---------------------------------------------------------------------------
-- Events: one frame, routed to the features that are on
-- ---------------------------------------------------------------------------

local ev
local function dispatch(_, event, ...)
  for _, def in ipairs(Gameplay.FEATURES) do
    local fn = def.events and def.events[event]
    if fn and Gameplay.IsOn(def.key) then
      local ok, err = pcall(fn, ...)
      if not ok then Gameplay.Report(def.key, err) end
    end
  end
end

-- PLAYER_LOGIN (Core.lua).
function Gameplay.Init()
  if ev then return end
  ev = CreateFrame("Frame")
  ev:SetScript("OnEvent", dispatch)
  local seen = {}
  for _, def in ipairs(Gameplay.FEATURES) do
    for event in pairs(def.events or {}) do
      if not seen[event] then
        seen[event] = true
        pcall(ev.RegisterEvent, ev, event)
      end
    end
    if def.onToggle and Gameplay.IsOn(def.key) then
      local ok, err = pcall(def.onToggle, true)
      if not ok then Gameplay.Report(def.key, err) end
    end
  end
end

-- ---------------------------------------------------------------------------
-- Vendor: auto repair, sell grey items
-- ---------------------------------------------------------------------------

-- The merchant window state comes from events, not from asking a frame whether it is
-- shown (the order in which MERCHANT_SHOW handlers run isn't defined).
local merchantOpen = false

local function repair()
  if not (CanMerchantRepair and CanMerchantRepair()) then return end
  local cost, canRepair = GetRepairAllCost()
  if not canRepair or not cost or cost <= 0 then return end
  if GetMoney() < cost then
    R2F.Print(L.GP_REPAIR_POOR:format(Gameplay.Money(cost)))
    return
  end
  RepairAllItems()   -- your own gold: no guild-bank argument
  R2F.Print(L.GP_REPAIRED:format(Gameplay.Money(cost)))
end

-- Sell price of one item by link (nil when the client hasn't cached the item).
local function sellPrice(link)
  local get = (C_Item and C_Item.GetItemInfo) or GetItemInfo
  if not (get and link) then return nil end
  local ok, a, b, c, d, e, f, g, h, i, j, price = pcall(get, link)
  if ok and type(a) ~= "table" then return tonumber(price) end
  if ok and type(a) == "table" then return tonumber(a.sellPrice) end
end

local function sellGray()
  if not (C_Container and C_Container.GetContainerNumSlots and C_Container.UseContainerItem) then return end
  local sold, total = 0, 0
  local lastBag = (NUM_BAG_SLOTS or 4)
  if NUM_REAGENTBAG_SLOTS then lastBag = lastBag + NUM_REAGENTBAG_SLOTS end
  for bag = 0, lastBag do
    for slot = 1, C_Container.GetContainerNumSlots(bag) or 0 do
      if not merchantOpen then break end
      local info = C_Container.GetContainerItemInfo(bag, slot)
      -- Quality 0 only (grey), never an item the game says has no vendor value.
      if info and info.quality == 0 and not info.hasNoValue then
        local price = sellPrice(info.hyperlink or info.itemID)
        if price == nil or price > 0 then
          local ok = pcall(C_Container.UseContainerItem, bag, slot)
          if ok then
            sold = sold + 1
            total = total + (price or 0) * (info.stackCount or 1)
          end
        end
      end
    end
  end
  if sold > 0 then
    R2F.Print(total > 0 and L.GP_SOLD:format(sold, Gameplay.Money(total)) or L.GP_SOLD_NOVALUE:format(sold))
  end
end

Gameplay.Register({
  key = "repair", group = "auto", title = "GP_REPAIR", tip = "GP_REPAIR_TIP",
  events = {
    MERCHANT_SHOW = function() merchantOpen = true; repair() end,
    MERCHANT_CLOSED = function() merchantOpen = false end,
  },
})

Gameplay.Register({
  key = "sellgray", group = "auto", title = "GP_SELLGRAY", tip = "GP_SELLGRAY_TIP",
  events = {
    MERCHANT_SHOW = function() merchantOpen = true; sellGray() end,
    MERCHANT_CLOSED = function() merchantOpen = false end,
  },
})

-- ---------------------------------------------------------------------------
-- Block duels
-- ---------------------------------------------------------------------------

Gameplay.Register({
  key = "duels", group = "auto", title = "GP_DUELS", tip = "GP_DUELS_TIP",
  events = {
    DUEL_REQUESTED = function(challenger)
      if CancelDuel then CancelDuel() end
      if StaticPopup_Hide then StaticPopup_Hide("DUEL_REQUESTED") end
      R2F.Print(L.GP_DUEL_DECLINED:format(challenger or "?"))
    end,
  },
})

-- ---------------------------------------------------------------------------
-- Screen: error filter, XP bar text
-- ---------------------------------------------------------------------------

-- The red lines above the action bar that say nothing new ("Not enough rage", "Ability is
-- not ready yet", "Out of range"...). Matched against the client's own strings, so it
-- works in any language. The game's UIErrorsFrame:AddMessage on the FRAME OBJECT is
-- wrapped once; the wrapper asks whether the filter is on every time.
local FILTERED = {
  "ERR_OUT_OF_MANA", "ERR_OUT_OF_RAGE", "ERR_OUT_OF_ENERGY", "ERR_OUT_OF_FOCUS", "ERR_OUT_OF_RUNIC_POWER",
  "SPELL_FAILED_NOT_READY", "ERR_ABILITY_COOLDOWN", "ERR_SPELL_COOLDOWN", "ERR_ITEM_COOLDOWN",
  "SPELL_FAILED_OUT_OF_RANGE", "ERR_OUT_OF_RANGE", "ERR_BADATTACKFACING", "ERR_BADATTACKPOS",
  "SPELL_FAILED_UNIT_NOT_INFRONT", "SPELL_FAILED_SPELL_IN_PROGRESS",
}
local filterSet
local function filtered(msg)
  if type(msg) ~= "string" then return false end
  if not filterSet then
    filterSet = {}
    for _, name in ipairs(FILTERED) do
      local s = _G[name]
      if type(s) == "string" and s ~= "" then filterSet[s] = true end
    end
  end
  return filterSet[msg] == true
end
Gameplay.IsFilteredError = filtered

local errorsWrapped = false
local function wrapErrors()
  if errorsWrapped then return true end
  local f = _G.UIErrorsFrame
  if not (f and f.AddMessage) then return false end
  local original = f.AddMessage
  f.AddMessage = function(self, msg, ...)
    if Gameplay.IsOn("errorfilter") and filtered(msg) then return end
    return original(self, msg, ...)
  end
  errorsWrapped = true
  return true
end

Gameplay.Register({
  key = "errorfilter", group = "screen", title = "GP_ERRORFILTER", tip = "GP_ERRORFILTER_TIP",
  available = function() return _G.UIErrorsFrame ~= nil and _G.UIErrorsFrame.AddMessage ~= nil end,
  onToggle = function(on) if on then wrapErrors() end end,
})

-- The experience bar's numbers always visible, through the game's own setting (read and written via QuickSettings.Read / Write: every CVar call lives in that file). The value
-- the player had is remembered and put back when the box is unticked.
local XP_CVAR = "xpBarText"
Gameplay.Register({
  key = "xpbar", group = "screen", title = "GP_XPBAR", tip = "GP_XPBAR_TIP", noCombat = true,
  available = function() return R2F.QuickSettings.Read(XP_CVAR) ~= nil end,
  onToggle = function(on)
    local g = R2F.Library.db
    if on then
      if g.gameplayXpWas == nil then g.gameplayXpWas = R2F.QuickSettings.Read(XP_CVAR) or "0" end
      R2F.QuickSettings.Write(XP_CVAR, "1")
    else
      R2F.QuickSettings.Write(XP_CVAR, g.gameplayXpWas or "0")
      g.gameplayXpWas = nil
    end
  end,
})
