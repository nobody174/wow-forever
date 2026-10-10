-- UI/Gameplay.lua: the Gameplay tab (ADDON_PLAN.md 17, v0.21.0).
--
--   left column   Automatic  (features that act for you: repair, sell grey items, block duels)
--                 Screen     (features that change what you see: error filter, XP bar text)
--   right column  Reminders  (the on-screen icons of your class: Warrior stance, Hunter ammo;
--                             UI/Reminders.lua draws these)
--
-- Every feature on the left has one check box and ships OFF. A feature the client can't do
-- (its game setting or frame is missing) is greyed out with the reason in its tooltip.
-- These controls only write SavedVariables or ask the client for a setting, so they stay
-- enabled in combat.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI
local Gameplay = R2F.Gameplay

local Tab = {}
R2F.GameplayTab = Tab

local page
local boxes = {}   -- feature key -> check button
local LEFT, RIGHT, RIGHT_W = 28, 282, 214

local function visible()
  return page ~= nil and page:IsVisible()
end

local function refresh()
  if not visible() then return end
  for _, def in ipairs(Gameplay.FEATURES) do
    local b = boxes[def.key]
    if b then
      local ok = Gameplay.Available(def)
      b:SetChecked(Gameplay.IsOn(def.key))
      b:SetEnabled(ok)
      if ok then b.r2fLabel:SetTextColor(1, 1, 1) else b.r2fLabel:SetTextColor(0.5, 0.5, 0.5) end
    end
  end
  R2F.RemindersTab.Refresh()
end

local function heading(f, x, y, text)
  local h = f:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
  h:SetPoint("TOPLEFT", x, y)
  h:SetText(text)
end

local function addBoxes(f, group, y)
  for _, def in ipairs(Gameplay.FEATURES) do
    if def.group == group then
      local b = UI.CheckButton(f, L[def.title])
      b:SetPoint("TOPLEFT", LEFT + 4, y)
      if b.SetMotionScriptsWhileDisabled then b:SetMotionScriptsWhileDisabled(true) end
      b:SetScript("OnClick", function()
        Gameplay.SetOn(def.key, not Gameplay.IsOn(def.key))
        refresh()
      end)
      b:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
        GameTooltip:AddLine(L[def.title], 1, 1, 1)
        GameTooltip:AddLine(L[def.tip], 1, 0.82, 0, true)
        if not Gameplay.Available(def) then GameTooltip:AddLine(L.GP_UNAVAILABLE, 1, 0.1, 0.1, true) end
        GameTooltip:Show()
      end)
      b:SetScript("OnLeave", function() GameTooltip:Hide() end)
      boxes[def.key] = b
      y = y - 26
    end
  end
  return y
end

-- Mouse-wheel scrolling (the page has more rows than the window is tall).
local function onWheel(self, delta)
  local maxScroll = math.max((self.r2fContentHeight or 0) - self:GetHeight(), 0)
  local v = (self:GetVerticalScroll() or 0) - delta * 40
  self:SetVerticalScroll(math.max(0, math.min(v, maxScroll)))
end

-- Called once by MainWindow with the Gameplay page frame. Everything sits in a scrolling area:
-- 17 features and a class's reminders are taller than the window (0.27.0 ran off the bottom).
function Tab.Build(f)
  page = f
  local scroll = UI.TryTemplate("ScrollFrame", "R2FGameplayScroll", f, "UIPanelScrollFrameTemplate",
    function(s) return s.SetScrollChild ~= nil end) or CreateFrame("ScrollFrame", "R2FGameplayScrollPlain", f)
  scroll:SetPoint("TOPLEFT", 6, -44)
  scroll:SetSize(500, 420)
  local c = CreateFrame("Frame", nil, scroll)
  c:SetSize(490, 100)
  scroll:SetScrollChild(c)
  scroll:EnableMouseWheel(true)
  scroll:SetScript("OnMouseWheel", onWheel)

  heading(c, LEFT, -10, L.GP_AUTOMATIC)
  local y = addBoxes(c, "auto", -40)
  heading(c, LEFT, y - 20, L.GP_SCREEN)
  y = addBoxes(c, "screen", y - 50)
  local note = c:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
  note:SetPoint("TOPLEFT", LEFT + 4, y - 16)
  note:SetWidth(230)
  note:SetJustifyH("LEFT")
  note:SetText(L.GP_NOTE)
  local leftEnd = y - 60

  heading(c, RIGHT, -10, L.GP_REMINDERS)
  local rightEnd = R2F.RemindersTab.BuildInto(c, RIGHT + 2, -42, RIGHT_W) or -100
  local height = -math.min(leftEnd, rightEnd) + 20
  c:SetHeight(height)
  scroll.r2fContentHeight = height
  return f
end

Tab.Refresh = refresh

function Tab.Show()
  R2F.MainWindow.Show("gameplay")
end
