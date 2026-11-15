-- CharMarks.lua: small marks on the Character window's gear slots showing how what you wear ranks on your Mr.BiZ list.
--   green square  = the BiZ pick for the slot at your level (Bizzest)
--   yellow square = one of the next two picks
--   green arrow   = an upgrade you can get now is on the Next upgrades list (BiZMe.lua)
-- Off until ticked (Tweaks, Bags: "Character slot marks"). The marks are textures on the slot buttons,
-- referenced only from our own table; nothing is written into the game's frames or tables, and no game
-- function is called in our name (hooks only).

local _, R2F = ...

local CM = {}
R2F.CharMarks = CM

-- Character window slot buttons -> Mr.BiZ slot keys.
CM.BUTTONS = {
  CharacterHeadSlot = "head", CharacterNeckSlot = "neck", CharacterShoulderSlot = "shoulder", CharacterBackSlot = "back",
  CharacterChestSlot = "chest", CharacterWristSlot = "wrist", CharacterHandsSlot = "hands", CharacterWaistSlot = "waist",
  CharacterLegsSlot = "legs", CharacterFeetSlot = "feet", CharacterFinger0Slot = "finger1", CharacterFinger1Slot = "finger2",
  CharacterTrinket0Slot = "trinket1", CharacterTrinket1Slot = "trinket2", CharacterMainHandSlot = "mainhand",
  CharacterSecondaryHandSlot = "offhand", CharacterRangedSlot = "ranged",
}

local ARROW = "Interface\\AddOns\\RoadToForever\\media\\upgrade"
local marks = {}   -- button -> { dot, arrow }

function CM.On() return R2F.Gameplay.IsOn("charmarks") end

local function markOf(btn)
  local m = marks[btn]
  if not m then
    local dot = btn:CreateTexture(nil, "OVERLAY", nil, 7)
    dot:SetSize(7, 7)
    dot:SetPoint("BOTTOMRIGHT", btn, "BOTTOMRIGHT", -2, 2)
    local arrow = btn:CreateTexture(nil, "OVERLAY", nil, 7)
    arrow:SetTexture(ARROW)
    arrow:SetVertexColor(0.25, 1, 0.25)
    arrow:SetSize(14, 14)
    arrow:SetPoint("TOPLEFT", btn, "TOPLEFT", 1, -1)
    m = { dot = dot, arrow = arrow }
    marks[btn] = m
  end
  return m
end

-- The rank (1-3) of the worn item in a slot's list, or nil.
function CM.RankOf(sp, lvl, slotKey, id)
  for _, sl in ipairs(R2F.BiZ.SlotsAt(sp, lvl)) do
    local same = sl.slot == slotKey
    if slotKey == "finger2" then same = same or sl.slot == "finger1" end
    if slotKey == "finger1" then same = same or sl.slot == "finger2" end
    if slotKey == "trinket2" then same = same or sl.slot == "trinket1" end
    if slotKey == "trinket1" then same = same or sl.slot == "trinket2" end
    if same and sl.best then
      if sl.best.id == id then return 1 end
      for i, n in ipairs(sl.next or {}) do
        if n.id == id then return i + 1 end
      end
    end
  end
  return nil
end

function CM.Update()
  for _, m in pairs(marks) do
    m.dot:Hide()
    m.arrow:Hide()
  end
  if not CM.On() then return end
  local specId = R2F.GearScore.SpecId()
  local sp = specId and R2F.BiZData.specs[specId]
  if not sp then return end
  local lo, hi = R2F.BiZ.Levels()
  local lvl = math.max(lo, math.min(hi, UnitLevel("player") or hi))
  local ups = {}
  for _, u in ipairs(R2F.BiZMe.Upgrades(specId, lvl, { level = lvl })) do ups[u.slot] = true end
  for name, slotKey in pairs(CM.BUTTONS) do
    local btn = _G[name]
    if btn and btn.CreateTexture then
      local m = markOf(btn)
      local inv = R2F.BiZ.INV_SLOT[slotKey]
      local link = inv and GetInventoryItemLink("player", inv)
      local id = type(link) == "string" and tonumber(link:match("item:(%d+)")) or nil
      local rank = id and CM.RankOf(sp, lvl, slotKey, id)
      if rank == 1 then
        m.dot:SetColorTexture(0.2, 0.9, 0.2, 1)
        m.dot:Show()
      elseif rank then
        m.dot:SetColorTexture(1, 0.82, 0, 1)
        m.dot:Show()
      end
      if ups[slotKey] then m.arrow:Show() end
    end
  end
end

local pending = false
local function soon()
  if pending then return end
  pending = true
  local function run()
    pending = false
    local ok, err = pcall(CM.Update)
    if not ok then R2F.Gameplay.Report("charmarks", err) end
  end
  if C_Timer and C_Timer.After then C_Timer.After(0.1, run) else run() end
end
CM.Soon = soon

local hooked = false
local function hookFrame()
  if hooked or not (_G.CharacterFrame and CharacterFrame.HookScript) then return end
  hooked = true
  CharacterFrame:HookScript("OnShow", soon)
end

R2F.Gameplay.Register({
  key = "charmarks", group = "auto", title = "CM_TITLE", tip = "CM_TITLE_TIP",
  events = {
    PLAYER_EQUIPMENT_CHANGED = soon,
    PLAYER_LEVEL_UP = soon,
  },
  onToggle = function()
    hookFrame()
    soon()
  end,
})
