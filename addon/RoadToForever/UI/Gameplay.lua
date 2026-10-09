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

-- Called once by MainWindow with the Gameplay page frame.
function Tab.Build(f)
  page = f
  heading(f, LEFT, -58, L.GP_AUTOMATIC)
  local y = addBoxes(f, "auto", -88)
  heading(f, LEFT, y - 20, L.GP_SCREEN)
  y = addBoxes(f, "screen", y - 50)
  local note = f:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
  note:SetPoint("TOPLEFT", LEFT + 4, y - 16)
  note:SetWidth(230)
  note:SetJustifyH("LEFT")
  note:SetText(L.GP_NOTE)

  heading(f, RIGHT, -58, L.GP_REMINDERS)
  R2F.RemindersTab.BuildInto(f, RIGHT + 2, -90, RIGHT_W)
  return f
end

Tab.Refresh = refresh

function Tab.Show()
  R2F.MainWindow.Show("gameplay")
end
