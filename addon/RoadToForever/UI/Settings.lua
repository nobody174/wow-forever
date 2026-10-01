-- UI/Settings.lua: the small Settings panel (ADDON_PLAN.md 5.8, step 5),
-- opened from the Macro Book's Settings button.
--
-- * New macros go to: Character slots first / Account slots first
--   -> R2FDB.settings.slotsFirst, read by Macros.ChooseSlot at every
--   CreateMacro (so it only affects macros made from then on).
-- * Show minimap button / Lock minimap button -> R2FDB.minimap.hide / .lock
--   (LibDBIcon's format, 6.3). The button itself is step 6; until then these
--   are stored only, and the panel says so. Step 6 provides
--   R2F.Minimap.Apply(), which this panel calls after every change.
-- * Remove all Road to Forever macros (confirm popup; Macros.RemoveAll).
--
-- Only the Remove all button is greyed out in combat (it deletes macros,
-- like Tidy up). The other settings only write SavedVariables, which is
-- allowed in combat and changes nothing protected.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI
local Library, Macros = R2F.Library, R2F.Macros

local Settings = {}
R2F.Settings = Settings

local frame
local ui = {}

local function refresh()
  if not frame then return end
  local s, mm = Library.db.settings, Library.db.minimap
  ui.char:SetChecked(s.slotsFirst ~= "account")
  ui.acc:SetChecked(s.slotsFirst == "account")
  ui.show:SetChecked(not mm.hide)
  ui.lock:SetChecked(mm.lock == true)
  ui.removeAll:SetEnabled(not R2F.InCombat())
end

local function setSlots(value)
  Library.db.settings.slotsFirst = value
  refresh()
end

-- Step 6 hook: the minimap button re-reads R2FDB.minimap.
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

local function build()
  local f = UI.DialogFrame("R2FSettings", UIParent)
  f:SetSize(340, 300)
  f:SetPoint("CENTER", 0, 40)
  f:SetFrameStrata("DIALOG")
  f:SetToplevel(true)
  f:EnableMouse(true)
  f:SetMovable(true)
  f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving)
  f:SetScript("OnDragStop", f.StopMovingOrSizing)
  f:Hide()
  if UISpecialFrames then table.insert(UISpecialFrames, "R2FSettings") end

  local title = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  title:SetPoint("TOP", 0, -18)
  title:SetText(L.SETTINGS_TITLE)
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton")
  close:SetPoint("TOPRIGHT", -4, -4)

  local slots = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  slots:SetPoint("TOPLEFT", 24, -46)
  slots:SetText(L.SETTINGS_SLOTS)

  ui.char = UI.CheckButton(f, L.SETTINGS_SLOTS_CHAR, true)
  ui.char:SetPoint("TOPLEFT", 32, -68)
  ui.char:SetScript("OnClick", function() setSlots("character") end)
  ui.acc = UI.CheckButton(f, L.SETTINGS_SLOTS_ACC, true)
  ui.acc:SetPoint("TOPLEFT", 32, -90)
  ui.acc:SetScript("OnClick", function() setSlots("account") end)

  -- Why "from now on": WoW can't move a macro between the account and
  -- character tabs; it would take delete + create, which empties every
  -- action button holding it. So existing macros stay where they are.
  local slotsNote = f:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
  slotsNote:SetPoint("TOPLEFT", 32, -112)
  slotsNote:SetWidth(280)
  slotsNote:SetJustifyH("LEFT")
  slotsNote:SetText(L.SETTINGS_SLOTS_NOTE)

  -- Values are flipped from the saved setting, then the boxes are redrawn
  -- from it (refresh), instead of reading GetChecked after the click.
  ui.show = UI.CheckButton(f, L.SETTINGS_MINIMAP_SHOW)
  ui.show:SetPoint("TOPLEFT", 24, -146)
  ui.show:SetScript("OnClick", function()
    local mm = Library.db.minimap
    mm.hide = not mm.hide
    refresh()
    applyMinimap()
  end)
  ui.lock = UI.CheckButton(f, L.SETTINGS_MINIMAP_LOCK)
  ui.lock:SetPoint("TOPLEFT", 24, -172)
  ui.lock:SetScript("OnClick", function()
    local mm = Library.db.minimap
    mm.lock = not mm.lock
    refresh()
    applyMinimap()
  end)
  -- Until step 6 adds the button, say so instead of letting the boxes look broken.
  ui.minimapNote = f:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
  ui.minimapNote:SetPoint("TOPLEFT", 52, -200)
  ui.minimapNote:SetWidth(260)
  ui.minimapNote:SetJustifyH("LEFT")
  ui.minimapNote:SetText(L.SETTINGS_MINIMAP_LATER)

  ui.removeAll = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  ui.removeAll:SetSize(270, 22)
  ui.removeAll:SetPoint("BOTTOM", 0, 22)
  ui.removeAll:SetText(L.BTN_REMOVE_ALL)
  ui.removeAll:SetScript("OnClick", onRemoveAll)

  f:SetScript("OnShow", refresh)
  return f
end

function Settings.Show()
  frame = frame or build()
  if R2F.Minimap and R2F.Minimap.Apply then ui.minimapNote:Hide() end
  frame:Show()
  refresh()
end

function Settings.Toggle()
  if frame and frame:IsShown() then frame:Hide() else Settings.Show() end
end

function Settings.IsShown()
  return frame ~= nil and frame:IsShown()
end

-- PLAYER_REGEN_DISABLED / ENABLED (6.5): grey out / re-enable Remove all.
function Settings.SetCombat()
  if frame and frame:IsShown() then refresh() end
end
