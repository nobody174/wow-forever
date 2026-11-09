-- UI/SetupTab.lua: the Setup tab (sidebar group Character).
--
-- Two blocks. "This character": Setup <class> (Setup.lua, re-runnable), Undo last setup, and whether the setup has run here.
-- "All characters": Save / Apply my general settings (General.lua). The minimap menu only offers the class setup until it has
-- run once; everything else lives here. The buttons call the same functions as the slash commands; those refuse in combat and
-- this page greys the buttons out in combat to say so. Our own frames only, no game call.

local _, R2F = ...
local L = R2F.L

local Tab = {}
R2F.SetupTab = Tab

local WIDTH = 500
local page
local ui = {}

local function className(def)
  return def.class:sub(1, 1) .. def.class:sub(2):lower()
end

local function newButton(parent, width)
  local b = CreateFrame("Button", nil, parent, "UIPanelButtonTemplate")
  R2F.UI.ThemeButton(b)
  b:SetSize(width, 24)
  return b
end

local function newText(parent, font, role)
  local fs = parent:CreateFontString(nil, "ARTWORK", font)
  fs:SetWidth(WIDTH)
  fs:SetJustifyH("LEFT")
  if role then R2F.Theme.PaintText(fs, role) end
  return fs
end

function Tab.Refresh()
  if not page then return end
  local combat = R2F.InCombat()
  local def = R2F.Setup.ForClass()
  local usable = def ~= nil and R2F.Setup.Available(def)

  if def then
    ui.setupBtn:SetText(L.MENU_SETUP:format(className(def)))
    ui.setupBtn:Show()
    ui.setupBtn:SetEnabled(usable and not combat)
    ui.undoBtn:Show()
    ui.undoBtn:SetEnabled(R2F.Setup.CanUndo() and not combat)
    ui.note:SetText(L.SETUP_TAB_NOTE)
    if not usable then
      ui.status:SetText(L.SETUP_TAB_NO_LAYOUT)
    else
      ui.status:SetText(R2F.Setup.IsDone() and L.SETUP_TAB_DONE or L.SETUP_TAB_NOT_RUN)
    end
  else
    ui.setupBtn:Hide()
    ui.undoBtn:Hide()
    ui.note:SetText("")
    ui.status:SetText(L.SETUP_TAB_NONE)
  end

  ui.saveBtn:SetEnabled(not combat)
  local has = R2F.General.Has()
  ui.applyBtn:SetEnabled(has and not combat)
  ui.generalStatus:SetText(has and L.SETUP_TAB_GENERAL_SAVED or L.SETUP_TAB_GENERAL_NONE)
  ui.combat:SetShown(combat)
end

function Tab.Build(f)
  if page then return end
  page = f

  ui.head1 = newText(f, "R2FHeadingLarge")
  ui.head1:SetPoint("TOPLEFT", f, "TOPLEFT", 10, -10)
  ui.head1:SetText(L.SETUP_TAB_THIS)

  ui.note = newText(f, "R2FBody", "body")
  ui.note:SetPoint("TOPLEFT", ui.head1, "BOTTOMLEFT", 0, -8)

  ui.setupBtn = newButton(f, 190)
  ui.setupBtn:SetPoint("TOPLEFT", ui.note, "BOTTOMLEFT", 0, -12)
  ui.setupBtn:SetScript("OnClick", function()
    local def = R2F.Setup.ForClass()
    if def then R2F.Setup.Run(def.key) end
  end)

  ui.undoBtn = newButton(f, 160)
  ui.undoBtn:SetPoint("LEFT", ui.setupBtn, "RIGHT", 8, 0)
  ui.undoBtn:SetText(L.MENU_SETUP_UNDO)
  ui.undoBtn:SetScript("OnClick", function() R2F.Setup.Undo() end)

  ui.status = newText(f, "R2FDim", "dim")
  ui.status:SetPoint("TOPLEFT", ui.setupBtn, "BOTTOMLEFT", 0, -8)

  ui.head2 = newText(f, "R2FHeadingLarge")
  ui.head2:SetPoint("TOPLEFT", ui.status, "BOTTOMLEFT", 0, -26)
  ui.head2:SetText(L.SETUP_TAB_ALL)

  ui.generalNote = newText(f, "R2FBody", "body")
  ui.generalNote:SetPoint("TOPLEFT", ui.head2, "BOTTOMLEFT", 0, -8)
  ui.generalNote:SetText(L.SETUP_TAB_GENERAL_NOTE)

  ui.saveBtn = newButton(f, 190)
  ui.saveBtn:SetPoint("TOPLEFT", ui.generalNote, "BOTTOMLEFT", 0, -12)
  ui.saveBtn:SetText(L.MENU_GENERAL_SAVE)
  ui.saveBtn:SetScript("OnClick", function() R2F.General.Save() end)

  ui.applyBtn = newButton(f, 190)
  ui.applyBtn:SetPoint("LEFT", ui.saveBtn, "RIGHT", 8, 0)
  ui.applyBtn:SetText(L.MENU_GENERAL_APPLY)
  -- Apply lists what it will change and asks first (General.lua); nothing more to confirm here.
  ui.applyBtn:SetScript("OnClick", function() R2F.General.Apply() end)

  ui.generalStatus = newText(f, "R2FDim", "dim")
  ui.generalStatus:SetPoint("TOPLEFT", ui.saveBtn, "BOTTOMLEFT", 0, -8)

  ui.combat = newText(f, "R2FDim", "dim")
  ui.combat:SetPoint("TOPLEFT", ui.generalStatus, "BOTTOMLEFT", 0, -14)
  ui.combat:SetText(L.SETUP_TAB_IN_COMBAT)
  ui.combat:Hide()

  Tab.Refresh()
end

function Tab.Frame() return page end

-- The controls, for the tests.
function Tab.Controls() return ui end
