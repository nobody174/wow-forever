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
