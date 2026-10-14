-- GearScore.lua: BiZ score (stat weights per spec) and upgrade markers.
--
-- Score = sum of the item's stats times the spec's weights. The weights are ForeverDB's, the
-- same line Mr.BiZ shows for each spec (BiZData.specs[id].weights, "hit 1.2, Agility 1, ...").
-- The spec is the one picked in Mr.BiZ for YOUR class (its first spec until you pick one).
--
-- Stats come from the game (C_Item.GetItemStats). Each weight name is matched to the game's stat keys
-- (ITEM_MOD_AGILITY_SHORT ...); where Forever uses a key this file doesn't know, the stat's own
-- label (_G[key], "Agility") is compared with the weight name as a fallback. `/r2f debug gear`
-- prints what the game gives for the item under the mouse, so a missing stat can be added.
--
-- Shown when the Tweaks switch "Upgrade arrows" is on:
--   * a line in item tooltips: "BiZ score 34.2 (+5.1 vs equipped)", green / red / grey
--   * a small green up / red down marker on bag items that would be better / worse than what
--     you wear in that slot (rings, trinkets and one-handers: against the weaker of the two)
-- Armor your class can't wear (by its level) gets no marker. Weapon skills are not checked.
--
-- Taint: the tooltip line is added from a hook (TooltipDataProcessor post-call, or HookScript
-- OnTooltipSetItem on older clients). The markers are textures (regions, never protected) on
-- the bag item buttons, referenced only from our own table. Nothing in the game's tables is
-- written; no game function is called in our name.

local _, R2F = ...
local L = R2F.L

local GS = {}
R2F.GearScore = GS

-- Weight name (as ForeverDB writes it) -> the game's stat keys.
GS.KEYS = {
  ["Stamina"] = { "ITEM_MOD_STAMINA_SHORT" },
  ["Agility"] = { "ITEM_MOD_AGILITY_SHORT" },
  ["Strength"] = { "ITEM_MOD_STRENGTH_SHORT" },
  ["Intellect"] = { "ITEM_MOD_INTELLECT_SHORT" },
  ["Spirit"] = { "ITEM_MOD_SPIRIT_SHORT" },
  ["crit"] = { "ITEM_MOD_CRIT_RATING_SHORT", "ITEM_MOD_CRIT_MELEE_RATING_SHORT", "ITEM_MOD_CRIT_RANGED_RATING_SHORT",
    "ITEM_MOD_CRIT_SPELL_RATING_SHORT" },
  ["haste"] = { "ITEM_MOD_HASTE_RATING_SHORT", "ITEM_MOD_HASTE_MELEE_RATING_SHORT", "ITEM_MOD_HASTE_SPELL_RATING_SHORT" },
  ["hit"] = { "ITEM_MOD_HIT_RATING_SHORT", "ITEM_MOD_HIT_MELEE_RATING_SHORT", "ITEM_MOD_HIT_RANGED_RATING_SHORT",
    "ITEM_MOD_HIT_SPELL_RATING_SHORT" },
  ["spell power"] = { "ITEM_MOD_SPELL_POWER_SHORT" },
  ["spell damage"] = { "ITEM_MOD_SPELL_DAMAGE_DONE_SHORT" },
  ["healing"] = { "ITEM_MOD_SPELL_HEALING_DONE_SHORT" },
  ["attack power"] = { "ITEM_MOD_ATTACK_POWER_SHORT", "ITEM_MOD_MELEE_ATTACK_POWER_SHORT" },
  ["ranged attack power"] = { "ITEM_MOD_RANGED_ATTACK_POWER_SHORT" },
  ["mana per 5 sec"] = { "ITEM_MOD_MANA_REGENERATION_SHORT", "ITEM_MOD_POWER_REGEN0_SHORT" },
  ["weapon DPS"] = { "ITEM_MOD_DAMAGE_PER_SECOND_SHORT" },
  ["expertise"] = { "ITEM_MOD_EXPERTISE_RATING_SHORT" },
  ["defense"] = { "ITEM_MOD_DEFENSE_SKILL_RATING_SHORT" },
  ["dodge"] = { "ITEM_MOD_DODGE_RATING_SHORT" },
  ["parry"] = { "ITEM_MOD_PARRY_RATING_SHORT" },
  ["block"] = { "ITEM_MOD_BLOCK_RATING_SHORT" },
  ["block value"] = { "ITEM_MOD_BLOCK_VALUE_SHORT" },
  ["armor"] = { "RESISTANCE0_NAME" },
  ["Bonus Armor"] = { "ITEM_MOD_EXTRA_ARMOR_SHORT" },
  ["Spell Penetration"] = { "ITEM_MOD_SPELL_PENETRATION_SHORT" },
}

-- Inventory slots per equip location (rings, trinkets, one-handers have two).
GS.SLOTS = {
  INVTYPE_HEAD = { 1 }, INVTYPE_NECK = { 2 }, INVTYPE_SHOULDER = { 3 }, INVTYPE_CHEST = { 5 }, INVTYPE_ROBE = { 5 },
  INVTYPE_WAIST = { 6 }, INVTYPE_LEGS = { 7 }, INVTYPE_FEET = { 8 }, INVTYPE_WRIST = { 9 }, INVTYPE_HAND = { 10 },
  INVTYPE_FINGER = { 11, 12 }, INVTYPE_TRINKET = { 13, 14 }, INVTYPE_CLOAK = { 15 },
  INVTYPE_WEAPON = { 16, 17 }, INVTYPE_2HWEAPON = { 16 }, INVTYPE_WEAPONMAINHAND = { 16 },
  INVTYPE_WEAPONOFFHAND = { 17 }, INVTYPE_SHIELD = { 17 }, INVTYPE_HOLDABLE = { 17 },
  INVTYPE_RANGED = { 18 }, INVTYPE_RANGEDRIGHT = { 18 }, INVTYPE_THROWN = { 18 }, INVTYPE_RELIC = { 18 },
}

-- Heaviest armor (1 cloth, 2 leather, 3 mail, 4 plate) per class: { before 40, from 40 }.
local ARMOR = {
  PRIEST = { 1, 1 }, MAGE = { 1, 1 }, WARLOCK = { 1, 1 }, ROGUE = { 2, 2 }, DRUID = { 2, 2 },
  HUNTER = { 2, 3 }, SHAMAN = { 2, 3 }, WARRIOR = { 3, 4 }, PALADIN = { 3, 4 },
}
local SHIELD = { WARRIOR = true, PALADIN = true, SHAMAN = true }

-- ---------------------------------------------------------------------------
-- Weights and scores (pure; the tests call these directly)
-- ---------------------------------------------------------------------------

local weightCache = {}
-- "hit 1.2, Agility 1" -> { hit = 1.2, Agility = 1 }
function GS.ParseWeights(text)
  if weightCache[text] then return weightCache[text] end
  local w = {}
  for part in (text or ""):gmatch("[^,]+") do
    local name, num = part:match("^%s*(.-)%s+([%d%.]+)%s*$")
    if name and tonumber(num) then w[name] = tonumber(num) end
  end
  weightCache[text] = w
  return w
end

-- The spec scoring uses: the spec you really play (your most-spent talent tree). Only when no talents
-- can be read yet: the one picked in Mr.BiZ for your class, or its first. Browsing another spec in the
-- Mr.BiZ tab does not change what the arrows and the tooltip line compare against.
function GS.SpecId()
  local BiZ = R2F.BiZ
  local own = BiZ.OwnSpec()
  if own then return own end
  local cls = BiZ.PlayerClassKey()
  local cdb = R2F.Library.cdb and R2F.Library.cdb.biz
  local id = cdb and cdb.spec and cdb.spec[cls]
  local specs = R2F.BiZData.specs
  if not (id and specs[id] and specs[id].class == cls) then id = BiZ.SpecsOf(cls)[1] end
  return id
end

local function lower(s) return type(s) == "string" and s:lower() or nil end

-- Score a stats table ({ [statKey] = value }) with a weights table. Returns score, matched
-- (how many of the item's stats had a weight).
function GS.ScoreStats(stats, weights)
  local score, matched, used = 0, 0, {}
  for name, wt in pairs(weights) do
    for _, key in ipairs(GS.KEYS[name] or {}) do
      local v = stats[key]
      if v and not used[key] then
        used[key] = true
        score = score + v * wt
        matched = matched + 1
      end
    end
  end
  -- Fallback: a stat whose own label is a weight name (keys this file doesn't list).
  for key, v in pairs(stats) do
    if not used[key] then
      local label = lower(_G[key])
      for name, wt in pairs(weights) do
        if label and label == name:lower() then
          used[key] = true
          score = score + v * wt
          matched = matched + 1
          break
        end
      end
    end
  end
  return score, matched
end

local function itemStats(link)
  local fn = (C_Item and C_Item.GetItemStats) or _G.GetItemStats
  if not (fn and link) then return nil end
  local ok, stats = pcall(fn, link)
  if ok and type(stats) == "table" then return stats end
  return nil
end

-- link -> score (nil when the game gives no stats yet or no spec).
function GS.Score(link, specId)
  specId = specId or GS.SpecId()
  local sp = specId and R2F.BiZData.specs[specId]
  local stats = itemStats(link)
  if not (sp and stats) then return nil end
  local score = GS.ScoreStats(stats, GS.ParseWeights(sp.weights))
  return math.floor(score * 10 + 0.5) / 10
end

-- Can the player wear this armor? (cloth / leather / mail / plate by class and level; shields)
function GS.CanWear(link)
  if not R2F.Item.Instant(link) then return true end
  local _, _, _, equipLoc, _, classID, subID = R2F.Item.Instant(link)
  if classID ~= 4 then return true end              -- not armor: weapons are not checked
  local token = R2F.playerClass or select(2, UnitClass("player"))
  if subID == 6 or equipLoc == "INVTYPE_SHIELD" then return SHIELD[token] == true end
  if not (subID and subID >= 1 and subID <= 4) then return true end   -- misc (rings, cloaks...)
  if equipLoc == "INVTYPE_CLOAK" then return true end
  local a = ARMOR[token]
  if not a then return true end
  local lvl = UnitLevel and UnitLevel("player") or 60
  return subID <= (lvl >= 40 and a[2] or a[1])
end

local function equipLoc(link)
  local loc = select(4, R2F.Item.Instant(link))
  if loc then return loc end
  return select(9, R2F.Item.Info(link))
end

-- Score of what is worn where this item would go (the weaker of two slots), or 0 if empty.
-- Returns nil when the item doesn't go in a slot we compare, false while a worn item isn't loaded.
function GS.EquippedScore(link, specId)
  local slots = GS.SLOTS[equipLoc(link) or ""]
  if not slots then return nil end
  local worst
  for _, slot in ipairs(slots) do
    local worn = GetInventoryItemLink and GetInventoryItemLink("player", slot)
    local s = 0
    if worn then
      s = GS.Score(worn, specId)
      if s == nil then return false end   -- worn item not loaded yet: don't compare (no false arrows)
    end
    if worst == nil or s < worst then worst = s end
  end
  return worst or 0
end

-- link -> score, delta vs equipped (nil when not comparable).
-- Only gear (an item with a slot in GS.SLOTS) is scored: potions and quest items give an empty
-- stats table, which would read "BiZ score 0.0".
function GS.Compare(link, specId)
  if not GS.SLOTS[equipLoc(link) or ""] then return nil end
  local s = GS.Score(link, specId)
  if not s then return nil end
  local eq = GS.EquippedScore(link, specId)
  if not eq then return s, nil end
  return s, math.floor((s - eq) * 10 + 0.5) / 10
end

function GS.On() return R2F.Gameplay.IsOn("upgrades") end

-- ---------------------------------------------------------------------------
-- Tooltip line
-- ---------------------------------------------------------------------------

function GS.TooltipLine(link)
  local specId = GS.SpecId()
  local s, delta = GS.Compare(link, specId)
  if not s then return nil end
  local spec = R2F.BiZData.specs[specId]
  local text = L.GS_TIP:format(s, spec and spec.name or "")
  local r, g, b = 0.9, 0.82, 0.5
  if delta and GS.CanWear(link) then
    if delta > 0 then
      text, r, g, b = text .. " " .. L.GS_TIP_UP:format(delta), 0.3, 1, 0.3
    elseif delta < 0 then
      text, r, g, b = text .. " " .. L.GS_TIP_DOWN:format(delta), 1, 0.35, 0.35
    else
      text = text .. " " .. L.GS_TIP_SAME
    end
  end
  return text, r, g, b
end

local function onTooltip(tip)
  if not GS.On() or not (tip and tip.GetItem) then return end
  local _, link = tip:GetItem()
  if not link then return end
  local text, r, g, b = GS.TooltipLine(link)
  if text then
    tip:AddLine(text, r, g, b)
    tip:Show()
  end
  -- The Mr.BiZ enchant for this slot (green), like the enchant line on Sixty Upgrades' gear list.
  local etext, er, eg, eb = R2F.BiZ.EnchantTipLine(link, equipLoc(link), GS.SpecId())
  if etext then
    tip:AddLine(etext, er, eg, eb)
    tip:Show()
  end
end
GS.OnTooltip = onTooltip

local tipHooked = false
function GS.HookTooltips()
  if tipHooked then return end
  tipHooked = true
  if _G.TooltipDataProcessor and TooltipDataProcessor.AddTooltipPostCall and Enum and Enum.TooltipDataType then
    TooltipDataProcessor.AddTooltipPostCall(Enum.TooltipDataType.Item, function(tip)
      if tip == GameTooltip or tip == _G.ItemRefTooltip then onTooltip(tip) end
    end)
    return
  end
  for _, tip in ipairs({ GameTooltip, _G.ItemRefTooltip }) do
    if tip and tip.HookScript then pcall(tip.HookScript, tip, "OnTooltipSetItem", onTooltip) end
  end
end

-- ---------------------------------------------------------------------------
-- Bag markers
-- ---------------------------------------------------------------------------

local markers = {}   -- item button -> our texture
local MARK = "Interface\\AddOns\\RoadToForever\\media\\upgrade"

-- Every shown bag item button with its bag and slot: { button, bag, slot }.
function GS.BagButtons()
  local out = {}
  local function add(btn, bag)
    if not (btn and btn.IsShown and btn:IsShown()) then return end
    local b = bag
    if btn.GetBagID then b = btn:GetBagID() end
    local slot = btn.GetID and btn:GetID()
    if b and slot then out[#out + 1] = { btn, b, slot } end
  end
  -- The combined bag (modern client) and the classic windows ContainerFrame1..13.
  local combined = _G.ContainerFrameCombinedBags
  if combined and combined:IsShown() and combined.EnumerateValidItems then
    for _, btn in combined:EnumerateValidItems() do add(btn, nil) end
  end
  for i = 1, 13 do
    local f = _G["ContainerFrame" .. i]
    if f and f:IsShown() then
      if f.EnumerateValidItems then
        for _, btn in f:EnumerateValidItems() do add(btn, nil) end
      else
        local bag = f.GetID and f:GetID()
        for j = 1, 36 do add(_G["ContainerFrame" .. i .. "Item" .. j], bag) end
      end
    end
  end
  return out
end

local function marker(btn)
  local t = markers[btn]
  if not t then
    t = btn:CreateTexture(nil, "OVERLAY", nil, 7)
    t:SetTexture(MARK)
    t:SetSize(14, 14)
    t:SetPoint("TOPLEFT", btn, "TOPLEFT", 1, -1)
    markers[btn] = t
  end
  return t
end

-- Our marker on a bag button, if one was made (tests, debugging).
function GS.MarkerOf(btn) return markers[btn] end

local function itemLink(bag, slot)
  if C_Container and C_Container.GetContainerItemLink then return C_Container.GetContainerItemLink(bag, slot) end
  return _G.GetContainerItemLink and _G.GetContainerItemLink(bag, slot) or nil
end

-- +1 upgrade, -1 downgrade, nil nothing to show.
function GS.Direction(link)
  if not link or not GS.CanWear(link) then return nil end
  local _, delta = GS.Compare(link)
  if not delta or delta == 0 then return nil end
  return delta > 0 and 1 or -1
end

function GS.UpdateBags()
  for _, t in pairs(markers) do t:Hide() end
  if not GS.On() then return end
  for _, e in ipairs(GS.BagButtons()) do
    local dir = GS.Direction(itemLink(e[2], e[3]))
    if dir then
      local t = marker(e[1])
      if dir > 0 then
        t:SetVertexColor(0.25, 1, 0.25)
        t:SetTexCoord(0, 1, 0, 1)
      else
        t:SetVertexColor(1, 0.25, 0.25)
        t:SetTexCoord(0, 1, 1, 0)        -- upside down
      end
      t:Show()
    end
  end
end

local pending = false
local function soon()
  if pending then return end
  pending = true
  local function run()
    pending = false
    local ok, err = pcall(GS.UpdateBags)
    if not ok then R2F.Gameplay.Report("upgrades", err) end
  end
  if C_Timer and C_Timer.After then C_Timer.After(0.1, run) else run() end
end
GS.Soon = soon

local shownHooked = {}
local function hookBagFrames()
  local frames = { _G.ContainerFrameCombinedBags }
  for i = 1, 13 do frames[#frames + 1] = _G["ContainerFrame" .. i] end
  for _, f in pairs(frames) do
    if f and f.HookScript and not shownHooked[f] then
      shownHooked[f] = true
      f:HookScript("OnShow", soon)
    end
  end
end

-- /r2f debug gear: the stats the game gives for the item under the mouse, and the score.
function GS.Debug()
  local link = GameTooltip and GameTooltip.GetItem and select(2, GameTooltip:GetItem())
  if not link then R2F.Print(L.GS_DEBUG_NONE) return end
  local stats = itemStats(link) or {}
  R2F.Print(L.GS_DEBUG_HEAD:format(link, GS.SpecId() or "?"))
  local weights = GS.ParseWeights((R2F.BiZData.specs[GS.SpecId()] or {}).weights)
  for key, v in pairs(stats) do
    local known
    for name in pairs(weights) do
      for _, k in ipairs(GS.KEYS[name] or {}) do if k == key then known = name end end
    end
    R2F.Print(("  %s = %s  (%s)"):format(key, tostring(v), known or L.GS_DEBUG_UNUSED))
  end
  local s, delta = GS.Compare(link)
  R2F.Print(L.GS_DEBUG_SCORE:format(tostring(s), tostring(delta)))
end

R2F.Gameplay.Register({
  key = "upgrades", group = "auto", title = "GS_TITLE", tip = "GS_TITLE_TIP",
  events = {
    BAG_UPDATE_DELAYED = soon,
    PLAYER_EQUIPMENT_CHANGED = soon,
    PLAYER_LEVEL_UP = soon,
  },
  onToggle = function()
    GS.HookTooltips()
    hookBagFrames()
    soon()
  end,
})
