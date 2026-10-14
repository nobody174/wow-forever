-- Gameplay.lua: the Gameplay features that replace ForeverPlus.
--
-- A small registry of features. Every feature has
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
  local ok, a, _, _, _, _, _, _, _, _, _, price = pcall(get, link)
  if ok and type(a) ~= "table" then return tonumber(price) end
  if ok and type(a) == "table" then return tonumber(a.sellPrice) end
end

-- Grey items worth selling right now: { { bag, slot, key, value }, ... }. Quality 0 only, never an item the
-- game says has no vendor value.
local function greyItems()
  local list = {}
  local lastBag = (NUM_BAG_SLOTS or 4)
  if NUM_REAGENTBAG_SLOTS then lastBag = lastBag + NUM_REAGENTBAG_SLOTS end
  for bag = 0, lastBag do
    for slot = 1, C_Container.GetContainerNumSlots(bag) or 0 do
      local info = C_Container.GetContainerItemInfo(bag, slot)
      if info and info.quality == 0 and not info.hasNoValue then
        local price = sellPrice(info.hyperlink or info.itemID)
        if price == nil or price > 0 then
          list[#list + 1] = { bag = bag, slot = slot, key = bag .. ":" .. slot .. ":" .. tostring(info.itemID),
                              value = (price or 0) * (info.stackCount or 1) }
        end
      end
    end
  end
  return list
end

-- Sells a few at a time and looks again: asking the game to sell a whole bag in one go only sold some of
-- it (you had to talk to the vendor again and again). An item that is still there after two tries is left alone.
local SELL_BATCH, SELL_DELAY = 4, 0.25
local selling = false

local function sellGray()
  if selling then return end
  if not (C_Container and C_Container.GetContainerNumSlots and C_Container.UseContainerItem) then return end
  local sold, total = 0, 0
  local tries, queued = {}, {}   -- tries[key] = attempts; queued[key] = value while waiting to leave the bag
  local function finish()
    selling = false
    if sold > 0 then
      R2F.Print(total > 0 and L.GP_SOLD:format(sold, Gameplay.Money(total)) or L.GP_SOLD_NOVALUE:format(sold))
    end
  end
  local function step()
    if not merchantOpen then return finish() end
    local list = greyItems()
    local present = {}
    for _, it in ipairs(list) do present[it.key] = true end
    -- What we sent last time and is gone now was sold.
    for key, value in pairs(queued) do
      if not present[key] then sold = sold + 1; total = total + value end
      queued[key] = nil
    end
    local sent = 0
    for _, it in ipairs(list) do
      if sent >= SELL_BATCH then break end
      if (tries[it.key] or 0) < 2 then
        tries[it.key] = (tries[it.key] or 0) + 1
        if pcall(C_Container.UseContainerItem, it.bag, it.slot) then
          queued[it.key] = it.value
          sent = sent + 1
        end
      end
    end
    if sent == 0 then return finish() end
    if C_Timer and C_Timer.After then C_Timer.After(SELL_DELAY, step) else step() end
  end
  selling = true
  step()
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
-- not ready yet", "Out of range"...). Matched against the client's own strings, so it works
-- in any language.
--
-- Blizzard's UIErrorsFrame shows these from the UI_ERROR_MESSAGE event. While the filter is
-- on, that frame stops listening to the event and a frame of ours takes it instead: a
-- filtered message is dropped, every other one is passed on with UIErrorsFrame:AddMessage
-- (the public call any addon uses to show a message there). Nothing on Blizzard's frame is
-- replaced or assigned; switching the filter off hands the event back.
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

local errorFrame   -- our listener, created the first time the filter is switched on

-- UI_ERROR_MESSAGE: (errorType, message) on modern clients, (message) on older ones.
local function onErrorMessage(_, _, a, b)
  local msg = type(a) == "string" and a or b
  if type(msg) ~= "string" or filtered(msg) then return end
  local frame = _G.UIErrorsFrame
  if frame and frame.AddMessage then frame:AddMessage(msg, 1.0, 0.1, 0.1, 1.0) end
  if type(a) == "number" and type(_G.PlayVocalErrorSoundID) == "function" then
    pcall(_G.PlayVocalErrorSoundID, a)
  end
end

local function setErrorFilter(on)
  local frame = _G.UIErrorsFrame
  if not (frame and frame.RegisterEvent and frame.UnregisterEvent) then return end
  if on then
    if not errorFrame then
      errorFrame = CreateFrame("Frame")
      errorFrame:SetScript("OnEvent", onErrorMessage)
    end
    frame:UnregisterEvent("UI_ERROR_MESSAGE")
    errorFrame:RegisterEvent("UI_ERROR_MESSAGE")
  elseif errorFrame then
    errorFrame:UnregisterEvent("UI_ERROR_MESSAGE")
    frame:RegisterEvent("UI_ERROR_MESSAGE")
  end
end

Gameplay.Register({
  key = "errorfilter", group = "screen", title = "GP_ERRORFILTER", tip = "GP_ERRORFILTER_TIP",
  available = function()
    local f = _G.UIErrorsFrame
    return f ~= nil and f.AddMessage ~= nil and f.UnregisterEvent ~= nil
  end,
  onToggle = setErrorFilter,
})

-- The experience bar's numbers always visible, through the game's own setting (read and
-- written via QuickSettings.Read / Write: every CVar call lives in that file). The value
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
