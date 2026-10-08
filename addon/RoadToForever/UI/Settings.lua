-- UI/Settings.lua: the Settings tab of the main window (ADDON_PLAN.md 5.8,
-- 15.2). Until v0.15.0 this was a small floating panel opened from the Macro
-- Book's Settings button; now it is the fourth tab (Home / Macros / Talents /
-- Settings) and the button is gone.
--
-- Two columns:
--   left   Macros  -> New macros go to: Character / Account slots first
--                     (R2FDB.settings.slotsFirst, read by Macros.ChooseSlot at every
--                     CreateMacro), Remove all Road to Forever macros (confirm popup;
--                     Macros.RemoveAll)
--          Minimap -> Show / Lock the minimap button (R2FDB.minimap.hide / .lock,
--                     LibDBIcon's format, 6.3), then R2F.Minimap.Apply(). The minimap
--                     button's own menu and /r2f minimap change the same values and
--                     call Settings.Refresh.
--   right  Quick settings (moved from Home in 0.15.0, 12.4.1) -> check boxes that
--                     change game settings with SetCVar (QuickSettings.lua)
--          Stance icon (Warriors only, 0.13.0; moves to Reminders in step 4)
--
-- Only Remove all and the Quick settings boxes are greyed out in combat
-- (they delete macros / change CVars). The other settings only write
-- SavedVariables, which is allowed in combat and changes nothing protected.
--
-- Quick settings read the LIVE CVar every time the tab is drawn (opened, combat
-- change, CVAR_UPDATE), never GetChecked after the click, so a refused change
-- snaps the box back.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI
local Library, Macros = R2F.Library, R2F.Macros

local Settings = {}
R2F.Settings = Settings

local page
local ui = {}

local LEFT, RIGHT = 28, 282

local function visible()
  return page ~= nil and page:IsVisible()
end

local function refresh()
  if not visible() then return end
  local s, mm = Library.db.settings, Library.db.minimap
  ui.char:SetChecked(s.slotsFirst ~= "account")
  ui.acc:SetChecked(s.slotsFirst == "account")
  ui.show:SetChecked(not mm.hide)
  ui.lock:SetChecked(mm.lock == true)
  local combat = R2F.InCombat()
  ui.removeAll:SetEnabled(not combat)
  for _, b in ipairs(ui.quick) do
    local available = R2F.QuickSettings.Available(b.qsItem)
    b:SetChecked(available and R2F.QuickSettings.IsOn(b.qsItem))
    local enabled = available and not combat
    b:SetEnabled(enabled)
    if enabled then b.r2fLabel:SetTextColor(1, 1, 1) else b.r2fLabel:SetTextColor(0.5, 0.5, 0.5) end
  end
  if ui.stShow then
    local st = Library.db.stance
    ui.stShow:SetChecked(st.shown)
    ui.stLock:SetChecked(st.lock)
    ui.stScale:SetValue(st.scale * 100)
    ui.stScaleText:SetText(L.SETTINGS_STANCE_SIZE:format(st.scale * 100 + 0.5))
  end
end

local function setSlots(value)
  Library.db.settings.slotsFirst = value
  refresh()
end

-- The minimap button re-reads R2FDB.minimap. Still guarded: the Settings
-- tests swap R2F.Minimap out, and a client without a Minimap frame has none.
local function applyMinimap()
  if R2F.Minimap and R2F.Minimap.Apply then R2F.Minimap.Apply() end
end

local function names(list)
  local out = {}
  for i, c in ipairs(list) do out[i] = c.name end
  return UI.NameList(out)
end

local function onRemoveAll()
  local plan = Macros.RemoveAllPlan()
  local nDel, nKeep = #plan.delete, #plan.keep
  if nDel == 0 and nKeep == 0 then
    -- Only records of macros that are already gone (if any): forgetting
    -- them is SavedVariables only, so no popup and no combat check needed.
    for id in pairs(Library.AllCreated()) do Library.SetCreated(id, nil) end
    R2F.Print(L.REMOVE_ALL_NONE)
    return
  end
  local text, accept
  if nDel == 0 then
    text, accept = L.REMOVE_ALL_ONLY_KEEP:format(names(plan.keep)), L.BTN_OK
  else
    text = nDel == 1 and L.REMOVE_ALL_TEXT_ONE:format(names(plan.delete))
      or L.REMOVE_ALL_TEXT:format(nDel, names(plan.delete))
    if nKeep > 0 then
      text = text .. (nKeep == 1 and L.REMOVE_ALL_KEEP_ONE or L.REMOVE_ALL_KEEP):format(names(plan.keep))
    end
    text, accept = text .. L.REMOVE_ALL_LIBRARY, L.BTN_REMOVE
  end
  UI.Confirm(text, accept, L.BTN_CANCEL, function()
    -- Same path as Tidy up: the button is greyed out in combat, and a popup
    -- accepted in combat anyway (opened just before the pull) is queued for
    -- PLAYER_REGEN_ENABLED. RemoveAll re-reads everything when it runs.
    Macros.RunOrQueue(function()
      local deleted, kept = Macros.RemoveAll()
      local msg = deleted == 1 and L.REMOVE_ALL_DONE_ONE or L.REMOVE_ALL_DONE:format(deleted)
      if kept > 0 then msg = msg .. L.REMOVE_ALL_DONE_KEPT:format(kept) end
      R2F.Print(msg)
      R2F.MacroBook.Refresh()
    end)
  end)
end

-- Quick settings tooltip: what it changes, and why it is greyed out.
local function showQuickTip(b)
  local item = b.qsItem
  GameTooltip:SetOwner(b, "ANCHOR_RIGHT")
  GameTooltip:AddLine(item.label, 1, 1, 1)
  GameTooltip:AddLine(item.tip, 1, 0.82, 0, true)
  if not R2F.QuickSettings.Available(item) then
    GameTooltip:AddLine(L.QS_UNAVAILABLE, 1, 0.1, 0.1, true)
  elseif R2F.InCombat() then
    GameTooltip:AddLine(L.QS_TIP_COMBAT, 1, 0.1, 0.1, true)
  end
  GameTooltip:Show()
end

local function heading(f, x, y, text)
  local h = f:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
  h:SetPoint("TOPLEFT", x, y)
  h:SetText(text)
  return h
end

local function buildMacros(f)
  heading(f, LEFT, -58, L.SETTINGS_MACROS)
  local slots = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  slots:SetPoint("TOPLEFT", LEFT + 4, -86)
  slots:SetText(L.SETTINGS_SLOTS)

  ui.char = UI.CheckButton(f, L.SETTINGS_SLOTS_CHAR, true)
  ui.char:SetPoint("TOPLEFT", LEFT + 12, -108)
  ui.char:SetScript("OnClick", function() setSlots("character") end)
  ui.acc = UI.CheckButton(f, L.SETTINGS_SLOTS_ACC, true)
  ui.acc:SetPoint("TOPLEFT", LEFT + 12, -130)
  ui.acc:SetScript("OnClick", function() setSlots("account") end)

  -- Why "from now on": WoW can't move a macro between the account and
  -- character tabs; it would take delete + create, which empties every
  -- action button holding it. So existing macros stay where they are.
  local note = f:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
  note:SetPoint("TOPLEFT", LEFT + 12, -154)
  note:SetWidth(220)
  note:SetJustifyH("LEFT")
  note:SetText(L.SETTINGS_SLOTS_NOTE)

  ui.removeAll = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  ui.removeAll:SetSize(222, 22)
  ui.removeAll:SetPoint("TOPLEFT", LEFT + 4, -204)
  ui.removeAll:SetText(L.BTN_REMOVE_ALL)
  ui.removeAll:SetScript("OnClick", onRemoveAll)
end

local function buildMinimap(f)
  heading(f, LEFT, -256, L.SETTINGS_MINIMAP)
  -- Values are flipped from the saved setting, then the boxes are redrawn
  -- from it (refresh), instead of reading GetChecked after the click.
  ui.show = UI.CheckButton(f, L.SETTINGS_MINIMAP_SHOW)
  ui.show:SetPoint("TOPLEFT", LEFT + 4, -284)
  ui.show:SetScript("OnClick", function()
    local mm = Library.db.minimap
    mm.hide = not mm.hide
    refresh()
    applyMinimap()
  end)
  ui.lock = UI.CheckButton(f, L.SETTINGS_MINIMAP_LOCK)
  ui.lock:SetPoint("TOPLEFT", LEFT + 4, -310)
  ui.lock:SetScript("OnClick", function()
    local mm = Library.db.minimap
    mm.lock = not mm.lock
    refresh()
    applyMinimap()
  end)
end

local function buildQuick(f)
  heading(f, RIGHT, -58, L.QS_TITLE)
  local note = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  note:SetPoint("TOPLEFT", RIGHT + 4, -86)
  note:SetWidth(232)
  note:SetJustifyH("LEFT")
  note:SetTextColor(0.7, 0.7, 0.7)
  note:SetText(L.QS_NOTE)
  ui.qsNote = note

  ui.quick = {}
  for i, item in ipairs(R2F.QuickSettings.ITEMS) do
    local b = UI.CheckButton(f, item.label)
    b:SetPoint("TOPLEFT", RIGHT + 4, -124 - (i - 1) * 26)
    b.qsItem = item
    -- Tooltips still show while the box is greyed out (combat / missing),
    -- so the player can see why.
    if b.SetMotionScriptsWhileDisabled then b:SetMotionScriptsWhileDisabled(true) end
    b:SetScript("OnClick", function(self)
      R2F.QuickSettings.Toggle(self.qsItem)
      refresh()
    end)
    b:SetScript("OnEnter", showQuickTip)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    ui.quick[i] = b
  end
end

-- Warrior stance icon (Stance.lua): show, lock, size.
local function buildStance(f)
  heading(f, RIGHT, -226, L.SETTINGS_STANCE)
  local St = R2F.Stance
  ui.stShow = UI.CheckButton(f, L.SETTINGS_STANCE_SHOW)
  ui.stShow:SetPoint("TOPLEFT", RIGHT + 4, -254)
  ui.stShow:SetScript("OnClick", function() St.SetShown(not Library.db.stance.shown) end)
  ui.stLock = UI.CheckButton(f, L.SETTINGS_STANCE_LOCK)
  ui.stLock:SetPoint("TOPLEFT", RIGHT + 4, -280)
  ui.stLock:SetScript("OnClick", function() St.SetLock(not Library.db.stance.lock) end)
  ui.stScaleText = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  ui.stScaleText:SetPoint("TOPLEFT", RIGHT + 8, -314)
  local sl = CreateFrame("Slider", "R2FStanceScale", f, "OptionsSliderTemplate")
  sl:SetPoint("TOPLEFT", RIGHT + 10, -340)
  sl:SetWidth(220)
  sl:SetMinMaxValues(St.MIN_SCALE * 100, St.MAX_SCALE * 100)
  sl:SetValueStep(5)
  if sl.SetObeyStepOnDrag then sl:SetObeyStepOnDrag(true) end
  for _, part in ipairs({ "Low", "High", "Text" }) do
    local fs = sl[part] or _G["R2FStanceScale" .. part]
    if fs then fs:SetText("") end
  end
  sl:SetScript("OnValueChanged", function(_, v)
    local scale = math.floor(v / 5 + 0.5) * 5 / 100
    if math.abs(scale - Library.db.stance.scale) > 0.001 then St.SetScale(scale) end
  end)
  ui.stScale = sl
end

-- Called once by MainWindow with the Settings page frame.
function Settings.Build(f)
  page = f
  buildMacros(f)
  buildMinimap(f)
  buildQuick(f)
  if R2F.Stance.IsWarrior() then buildStance(f) end
  return f
end

-- Open the main window on this tab (the old floating panel's Show / Toggle).
function Settings.Show()
  R2F.MainWindow.Show("settings")
end

function Settings.Toggle()
  R2F.MainWindow.Toggle("settings")
end

function Settings.IsShown()
  return R2F.MainWindow.CurrentTab() == "settings"
end

-- PLAYER_REGEN_DISABLED / ENABLED (6.5): grey out / re-enable Remove all and
-- the Quick settings boxes.
function Settings.SetCombat()
  refresh()
end

-- Redraw the boxes after the minimap menu, /r2f minimap or the stance
-- commands changed a value; also MainWindow when the tab is selected.
Settings.Refresh = refresh

-- CVAR_UPDATE: a game setting changed elsewhere. Throttled to one redraw per
-- 0.2 s like Home's counts; no-op while the tab isn't showing.
local pending = false
function Settings.RequestRefresh()
  if not visible() or pending then return end
  if not (C_Timer and C_Timer.After) then refresh(); return end
  pending = true
  C_Timer.After(0.2, function() pending = false; refresh() end)
end
