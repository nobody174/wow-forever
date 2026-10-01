-- UI/ImportFrame.lua: paste box + preview + Import/Cancel (ADDON_PLAN.md 5.6).
--
-- Importing writes the addon's own saved library and (step 4) updates real
-- macros that are ours and unedited, through Macros.lua's combat-checked
-- write path. The button is greyed out in combat, as 6.5 asks; if an import
-- still ran in combat, those macro writes would be queued, not skipped.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI

local ImportFrame = {}
R2F.ImportFrame = ImportFrame

local frame, edit, preview, importBtn
local parsed -- last successful parse of the box's text, or nil

local function playerClass()
  return R2F.playerClass or select(2, UnitClass("player"))
end

local function refresh()
  local text = edit:GetText() or ""
  parsed = nil
  if text:match("^%s*$") then
    preview:SetText("")
    importBtn:Disable()
    return
  end
  local result, err = R2F.Import.Parse(text)
  if not result then
    preview:SetTextColor(1, 0.1, 0.1)
    preview:SetText(err)
    importBtn:Disable()
    return
  end
  parsed = result
  local diff = R2F.Import.Diff(result, R2F.Library.db.library, playerClass())
  preview:SetTextColor(1, 1, 1)
  preview:SetText(R2F.Import.PreviewText(diff))
  importBtn:SetEnabled(not R2F.InCombat())
end

local function doImport()
  if not parsed or R2F.InCombat() then return end
  -- Library write + real-macro updates + chat summary (Import.Commit).
  local diff = R2F.Import.Commit(parsed, playerClass(), time())
  frame:Hide()
  -- Jump to the first tab that got a new macro (5.6), if it's one we show.
  local first = diff.firstNew
  R2F.MacroBook.ShowSection(first and first.class, first and first.section)
end

local function build()
  local f = UI.DialogFrame("R2FImport", UIParent)
  -- 340 tall (was 320 in v0.1.0): the preview can now be two lines that
  -- each wrap (step 4's "will be updated / left as they are" line).
  f:SetSize(460, 340)
  f:SetPoint("CENTER", 0, 40)
  f:SetFrameStrata("DIALOG")
  f:SetToplevel(true)
  f:EnableMouse(true)
  f:SetMovable(true)
  f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving)
  f:SetScript("OnDragStop", f.StopMovingOrSizing)
  f:Hide()
  if UISpecialFrames then table.insert(UISpecialFrames, "R2FImport") end

  local title = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  title:SetPoint("TOP", 0, -18)
  title:SetText(L.IMPORT_TITLE)

  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton")
  close:SetPoint("TOPRIGHT", -4, -4)

  local scroll
  scroll, edit = UI.MultiLineEdit(f, "R2FImportScroll", 390, 170)
  scroll:SetPoint("TOPLEFT", 26, -46)

  -- Placeholder text, hidden while the box has text (5.6).
  local hint = f:CreateFontString(nil, "ARTWORK", "GameFontDisable")
  hint:SetPoint("TOPLEFT", scroll, "TOPLEFT", 4, -2)
  hint:SetWidth(380)
  hint:SetJustifyH("LEFT")
  hint:SetText(L.IMPORT_PLACEHOLDER)

  preview = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  preview:SetPoint("TOPLEFT", scroll, "BOTTOMLEFT", 0, -10)
  preview:SetWidth(400)
  preview:SetJustifyH("LEFT")

  importBtn = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  importBtn:SetSize(110, 22)
  importBtn:SetPoint("BOTTOMRIGHT", f, "BOTTOM", -6, 18)
  importBtn:SetText(L.BTN_IMPORT)
  importBtn:SetScript("OnClick", doImport)
  importBtn:Disable()

  local cancel = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  cancel:SetSize(110, 22)
  cancel:SetPoint("BOTTOMLEFT", f, "BOTTOM", 6, 18)
  cancel:SetText(L.BTN_CANCEL)
  cancel:SetScript("OnClick", function() f:Hide() end)

  -- A paste fires OnTextChanged once, but typing fires it per key; parse on
  -- the next frame at most once, so a big paste is decoded a single time.
  -- HookScript (on our own edit box) keeps InputScrollFrameTemplate's own
  -- handler, which scrolls the box to follow the cursor.
  local pending = false
  edit:HookScript("OnTextChanged", function(self)
    hint:SetShown((self:GetText() or "") == "")
    if pending then return end
    if C_Timer and C_Timer.After then
      pending = true
      C_Timer.After(0.05, function() pending = false; if f:IsShown() then refresh() end end)
    else
      refresh()
    end
  end)
  edit:SetScript("OnEscapePressed", function() f:Hide() end)

  f:SetScript("OnShow", function()
    edit:SetText("")
    preview:SetText("")
    hint:Show()
    importBtn:Disable()
    edit:SetFocus()
  end)
  return f
end

function ImportFrame.Show()
  frame = frame or build()
  frame:Show()
end

function ImportFrame.Hide()
  if frame then frame:Hide() end
end

-- PLAYER_REGEN_DISABLED / ENABLED (6.5).
function ImportFrame.SetCombat(inCombat)
  if not frame or not frame:IsShown() then return end
  if inCombat then importBtn:Disable() else refresh() end
end
