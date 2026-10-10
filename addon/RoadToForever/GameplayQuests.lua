-- GameplayQuests.lua: quest automation, Gameplay build order step 3 (ADDON_PLAN.md 17, v0.23.0).
--
--   Accept quests    accepts a quest when its window opens, and picks the next available quest
--                    at a quest giver (gossip list or quest greeting).
--   Hand in quests   completes finished quests and takes the reward when there is nothing to choose
--                    between (no reward, or exactly one). With two or more reward choices the window
--                    stays open for you: the addon never picks between rewards.
--   Reward values    shows what each reward choice sells for to a vendor, and marks the best.
--
-- All three are OFF until ticked. Holding Shift pauses the two that act, so you can read
-- a quest text or choose by hand without turning anything off. The quest APIs on this client
-- are partly unverified, so every call is guarded: modern C_GossipInfo first, the classic
-- gossip functions as the fallback, and anything missing simply does nothing.
-- Written from scratch (ForeverPlus was only used to learn what these features do).

local _, R2F = ...
local L = R2F.L
local Gameplay = R2F.Gameplay

local function paused()
  return IsShiftKeyDown and IsShiftKeyDown() and true or false
end

-- ---------------------------------------------------------------------------
-- Quest givers: gossip list and quest greeting, modern API with a classic fallback
-- ---------------------------------------------------------------------------

-- Quests this NPC offers: { {id =, index =}, ... } in list order (id may be nil on the
-- classic functions, which work by index).
local function gossipAvailable()
  local out = {}
  if C_GossipInfo and C_GossipInfo.GetAvailableQuests then
    for i, q in ipairs(C_GossipInfo.GetAvailableQuests() or {}) do out[i] = { id = q.questID, index = i } end
  elseif GetNumGossipAvailableQuests then
    for i = 1, GetNumGossipAvailableQuests() or 0 do out[i] = { index = i } end
  end
  return out
end

-- Quests of yours this NPC can take in: only the complete ones.
local function gossipComplete()
  local out = {}
  if C_GossipInfo and C_GossipInfo.GetActiveQuests then
    for i, q in ipairs(C_GossipInfo.GetActiveQuests() or {}) do
      if q.isComplete then out[#out + 1] = { id = q.questID, index = i } end
    end
  elseif GetNumGossipActiveQuests and GetGossipActiveQuests then
    -- Classic: GetGossipActiveQuests returns title, level, isLowLevel, isComplete, isLegendary, isIgnored per quest.
    local list = { GetGossipActiveQuests() }
    for i = 1, GetNumGossipActiveQuests() or 0 do
      if list[(i - 1) * 6 + 4] then out[#out + 1] = { index = i } end
    end
  end
  return out
end

local function selectAvailable(q)
  if C_GossipInfo and C_GossipInfo.SelectAvailableQuest and q.id then
    C_GossipInfo.SelectAvailableQuest(q.id)
  elseif SelectGossipAvailableQuest then
    SelectGossipAvailableQuest(q.index)
  end
end

local function selectActive(q)
  if C_GossipInfo and C_GossipInfo.SelectActiveQuest and q.id then
    C_GossipInfo.SelectActiveQuest(q.id)
  elseif SelectGossipActiveQuest then
    SelectGossipActiveQuest(q.index)
  end
end

-- ---------------------------------------------------------------------------
-- Accept quests
-- ---------------------------------------------------------------------------

Gameplay.Register({
  key = "questaccept", group = "auto", title = "GP_QACCEPT", tip = "GP_QACCEPT_TIP",
  events = {
    QUEST_DETAIL = function()
      if paused() then return end
      -- A quest the game already accepted by itself (auto-accept quests) needs nothing.
      if QuestGetAutoAccept and QuestGetAutoAccept() then return end
      if AcceptQuest then AcceptQuest() end
    end,
    GOSSIP_SHOW = function()
      if paused() then return end
      -- Handing in comes first: with both on, a finished quest here is taken in before a new one is picked.
      if Gameplay.IsOn("questturnin") and gossipComplete()[1] then return end
      local list = gossipAvailable()
      if list[1] then selectAvailable(list[1]) end
    end,
    QUEST_GREETING = function()
      if paused() or not (GetNumAvailableQuests and SelectAvailableQuest) then return end
      if (GetNumAvailableQuests() or 0) > 0 then SelectAvailableQuest(1) end
    end,
  },
})

-- ---------------------------------------------------------------------------
-- Hand in quests
-- ---------------------------------------------------------------------------

Gameplay.Register({
  key = "questturnin", group = "auto", title = "GP_QTURNIN", tip = "GP_QTURNIN_TIP",
  events = {
    GOSSIP_SHOW = function()
      if paused() then return end
      local list = gossipComplete()
      if list[1] then selectActive(list[1]) end
    end,
    QUEST_GREETING = function()
      if paused() or not (GetNumActiveQuests and SelectActiveQuest and GetActiveTitle) then return end
      for i = 1, GetNumActiveQuests() or 0 do
        local _, complete = GetActiveTitle(i)
        if complete then SelectActiveQuest(i) return end
      end
    end,
    QUEST_PROGRESS = function()
      if paused() then return end
      if IsQuestCompletable and IsQuestCompletable() and CompleteQuest then CompleteQuest() end
    end,
    QUEST_COMPLETE = function()
      if paused() then return end
      -- THE RULE: the addon never picks between rewards. With no reward or exactly one there is
      -- nothing to pick between, so the quest is turned in; with two or more it is left for you.
      -- (Without the API it can't tell, so it does nothing.)
      local choices = GetNumQuestChoices and GetNumQuestChoices()
      if choices ~= nil and choices <= 1 and GetQuestReward then GetQuestReward(1) end
    end,
  },
})

-- ---------------------------------------------------------------------------
-- Reward values
-- ---------------------------------------------------------------------------

local valueTexts = {}   -- button -> font string

-- The reward choice buttons of the open quest window, by index.
local function choiceButton(i)
  local name = _G["QuestInfoRewardsFrameQuestInfoItem" .. i]
  if name then return name end
  local frame = _G.QuestInfoRewardsFrame
  if frame and frame.RewardButtons then return frame.RewardButtons[i] end
end

local function vendorPrice(link)
  local get = (C_Item and C_Item.GetItemInfo) or GetItemInfo
  if not (get and link) then return nil end
  local ok, a, b, c, d, e, f, g, h, i, j, price = pcall(get, link)
  if ok and type(a) ~= "table" then return tonumber(price) end
  if ok and type(a) == "table" then return tonumber(a.sellPrice) end
end

local function showValues()
  if not (GetNumQuestChoices and GetQuestItemLink) then return end
  local n = GetNumQuestChoices() or 0
  local best, bestPrice = nil, 0
  local prices = {}
  for i = 1, n do
    local p = vendorPrice(GetQuestItemLink("choice", i))
    prices[i] = p
    if p and p > bestPrice then best, bestPrice = i, p end
  end
  for i = 1, n do
    local btn = choiceButton(i)
    if btn then
      local fs = valueTexts[btn]
      if not fs then
        fs = btn:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
        fs:SetPoint("BOTTOMRIGHT", btn, "BOTTOMRIGHT", -2, 2)
        valueTexts[btn] = fs
      end
      local p = prices[i]
      fs:SetText(p and p > 0 and Gameplay.Money(p) or "")
      if i == best and n > 1 then fs:SetTextColor(0.2, 1, 0.2) else fs:SetTextColor(1, 1, 1) end
      fs:Show()
    end
  end
end
Gameplay.ShowRewardValues = showValues

local function hideValues()
  for _, fs in pairs(valueTexts) do fs:Hide() end
end

Gameplay.Register({
  key = "rewardvalue", group = "screen", title = "GP_QVALUE", tip = "GP_QVALUE_TIP",
  available = function() return GetNumQuestChoices ~= nil and GetQuestItemLink ~= nil end,
  events = {
    -- A moment later: the game fills in the reward buttons on the same event, and which
    -- handler runs first isn't defined.
    QUEST_COMPLETE = function()
      if C_Timer and C_Timer.After then C_Timer.After(0.1, showValues) else showValues() end
    end,
    QUEST_ITEM_UPDATE = showValues,
  },
  onToggle = function(on) if not on then hideValues() end end,
})

-- ---------------------------------------------------------------------------
-- Quest log: a track-all box on every zone header
-- ---------------------------------------------------------------------------

-- The game's own way is a right-click menu on the zone header (Track All / Untrack All).
-- This puts that in one click: a small check box on each zone header, ticked when every quest
-- under it is tracked. Ticking tracks all, unticking untracks all. Built on the public
-- C_QuestLog functions (AddQuestWatch / RemoveQuestWatch), not by calling the game's quest
-- log code; the boxes are redrawn after the game redraws the list (hooksecurefunc on
-- QuestLogQuests_Update). The header buttons come from QuestScrollFrame.headerFramePool and
-- carry questLogIndex (read in the game's UI code, 1.60.1.70291; the exact look in game is
-- unverified: TESTING.md 33).
local zoneBoxes = {}   -- header button -> check button
local zoneHooked = false

-- The quest ids under a header, in order (stops at the next header).
local function questsUnder(headerIndex)
  local ids = {}
  for i = headerIndex + 1, C_QuestLog.GetNumQuestLogEntries() do
    local info = C_QuestLog.GetInfo(i)
    if not info or info.isHeader then break end
    if info.questID then ids[#ids + 1] = info.questID end
  end
  return ids
end

local function watched(questID)
  return C_QuestLog.GetQuestWatchType and C_QuestLog.GetQuestWatchType(questID) ~= nil
end

-- true when the header has quests and every one is tracked
local function allTracked(headerIndex)
  local ids = questsUnder(headerIndex)
  if #ids == 0 then return false end
  for _, id in ipairs(ids) do
    if not watched(id) then return false end
  end
  return true
end

local function setHeader(headerIndex, track)
  for _, id in ipairs(questsUnder(headerIndex)) do
    local on = watched(id)
    if track and not on then
      C_QuestLog.AddQuestWatch(id)
    elseif not track and on then
      C_QuestLog.RemoveQuestWatch(id)
    end
  end
end

local function activeHeaders()
  local pool = _G.QuestScrollFrame and _G.QuestScrollFrame.headerFramePool
  local out = {}
  if pool and pool.EnumerateActive then
    for header in pool:EnumerateActive() do
      if header.questLogIndex then out[#out + 1] = header end
    end
  end
  return out
end

local function drawZoneBoxes()
  local on = Gameplay.IsOn("questzone")
  for _, box in pairs(zoneBoxes) do box:Hide() end
  if not on then return end
  for _, header in ipairs(activeHeaders()) do
    local box = zoneBoxes[header]
    if not box then
      box = R2F.UI.CheckButton(header, "")
      box:SetSize(18, 18)
      box:SetPoint("RIGHT", header, "RIGHT", -6, 0)
      box:SetScript("OnClick", function(self)
        local h = self:GetParent()
        if h.questLogIndex then setHeader(h.questLogIndex, not allTracked(h.questLogIndex)) end
        self:SetChecked(allTracked(h.questLogIndex or 0))
      end)
      box:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
        GameTooltip:AddLine(L.GP_QZONE_TIP2, 1, 1, 1, true)
        GameTooltip:Show()
      end)
      box:SetScript("OnLeave", function() GameTooltip:Hide() end)
      zoneBoxes[header] = box
    end
    box:SetChecked(allTracked(header.questLogIndex))
    box:Show()
  end
end
Gameplay.DrawZoneBoxes = drawZoneBoxes

Gameplay.Register({
  key = "questzone", group = "screen", title = "GP_QZONE", tip = "GP_QZONE_TIP",
  available = function()
    return C_QuestLog ~= nil and C_QuestLog.GetNumQuestLogEntries ~= nil and C_QuestLog.GetInfo ~= nil
      and C_QuestLog.AddQuestWatch ~= nil and C_QuestLog.RemoveQuestWatch ~= nil
      and _G.QuestScrollFrame ~= nil
  end,
  events = {
    QUEST_WATCH_LIST_CHANGED = drawZoneBoxes,
    QUEST_LOG_UPDATE = drawZoneBoxes,
  },
  onToggle = function(on)
    if on and not zoneHooked and _G.QuestLogQuests_Update and hooksecurefunc then
      zoneHooked = true
      hooksecurefunc("QuestLogQuests_Update", drawZoneBoxes)
    end
    drawZoneBoxes()
  end,
})

-- ---------------------------------------------------------------------------
-- Gossip: skip the line in front of a shop
-- ---------------------------------------------------------------------------

-- Many NPCs open a gossip window with ONE line ("I want to browse your goods") before the shop.
-- This picks that line, and nothing else. The danger is a line that starts an escort, a fight or
-- an event, and this build's gossip options have no "type" (the game's API documentation lists
-- gossipOptionID, name, icon, status, flags...), so a line is recognised by its ICON, from a
-- short whitelist of the game's own gossip icons (file ids read in the game files:
-- GossipFrame\VendorGossipIcon 132060, TrainerGossipIcon 132058, BankerGossipIcon 132050,
-- TaxiGossipIcon 132057, AuctioneerGossipIcon 528409). Rules: exactly ONE option is listed, it is
-- Available, its icon is on the whitelist, and the NPC offers no quests (those are for you and
-- the quest features). Never the innkeeper's "make this your home", never a plain chat line.
-- Hold Shift to pause. `/r2f gossip` prints the open window's options with their icon ids, so
-- the whitelist can grow from real data.
local GOSSIP_ICONS = { [132060] = "shop", [132058] = "trainer", [132050] = "bank", [132057] = "flights", [528409] = "auctions" }
Gameplay.GOSSIP_ICONS = GOSSIP_ICONS

local function gossipOptions()
  if C_GossipInfo and C_GossipInfo.GetOptions then return C_GossipInfo.GetOptions() or {} end
  return {}
end

-- The one option to pick, or nil.
function Gameplay.GossipPick()
  local opts = gossipOptions()
  if #opts ~= 1 then return nil end
  local o = opts[1]
  if not (o and o.gossipOptionID and GOSSIP_ICONS[o.icon]) then return nil end
  if o.status ~= nil and o.status ~= 0 then return nil end      -- 0 = Available
  if #gossipAvailable() > 0 or #gossipComplete() > 0 then return nil end
  if C_GossipInfo.GetActiveQuests then
    for _ in ipairs(C_GossipInfo.GetActiveQuests() or {}) do return nil end
  end
  return o
end

Gameplay.Register({
  key = "gossipshop", group = "auto", title = "GP_GOSSIP", tip = "GP_GOSSIP_TIP",
  available = function() return C_GossipInfo ~= nil and C_GossipInfo.GetOptions ~= nil and C_GossipInfo.SelectOption ~= nil end,
  events = {
    GOSSIP_SHOW = function()
      if paused() then return end
      local o = Gameplay.GossipPick()
      if o then C_GossipInfo.SelectOption(o.gossipOptionID) end
    end,
  },
})

-- /r2f gossip: what the open gossip window offers.
function Gameplay.PrintGossip()
  if not (C_GossipInfo and C_GossipInfo.GetOptions) then R2F.Print(L.GP_GOSSIP_NOAPI) return end
  local opts = gossipOptions()
  if #opts == 0 then R2F.Print(L.GP_GOSSIP_NONE) return end
  R2F.Print(L.GP_GOSSIP_HEAD:format(#opts))
  for i, o in ipairs(opts) do
    R2F.Print(("  %d. %s | icon %s%s | status %s | flags %s | id %s"):format(
      i, o.name or "?", tostring(o.icon), GOSSIP_ICONS[o.icon] and (" (" .. GOSSIP_ICONS[o.icon] .. ")") or "",
      tostring(o.status), tostring(o.flags), tostring(o.gossipOptionID)))
  end
  local pick = Gameplay.GossipPick()
  R2F.Print(pick and L.GP_GOSSIP_WOULD:format(pick.name or "?") or L.GP_GOSSIP_WOULDNT)
end
