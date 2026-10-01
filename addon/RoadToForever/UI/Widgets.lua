-- UI/Widgets.lua: small shared UI pieces (window shell, confirm dialog,
-- multi-line edit box, sounds), all from Blizzard templates and textures
-- (ADDON_PLAN.md 5: no custom skinning).
--
-- Nothing here has run against the Forever client yet (ADDON_PLAN 11), so
-- every template is tried first and verified by the child keys we use; if
-- a template is missing or different, a plain fallback built from Blizzard
-- textures takes over instead of erroring.
--
-- Taint notes (6.6): no secure templates, no hooks, Blizzard frames are
-- never modified. The confirm dialog is our own frame instead of a
-- StaticPopupDialogs entry, so we don't write into a shared Blizzard table
-- that protected popups also use.

local _, R2F = ...

local UI = {}
R2F.UI = UI

local function templateKnown(template)
  -- C_XMLUtil.GetTemplateInfo exists in modern-engine clients (Classic Era
  -- included). If it's missing we just try the template and check the result.
  if C_XMLUtil and C_XMLUtil.GetTemplateInfo then
    return C_XMLUtil.GetTemplateInfo(template) ~= nil
  end
  return true
end

-- CreateFrame with `template`, accepted only if check(frame) is true.
-- Returns the frame or nil. A rejected frame is hidden and left unused.
function UI.TryTemplate(frameType, name, parent, template, check)
  if not templateKnown(template) then return nil end
  local ok, f = pcall(CreateFrame, frameType, name, parent, template)
  if ok and f and check(f) then return f end
  if ok and f then f:Hide() end
  return nil
end

function UI.PlaySound(key)
  if SOUNDKIT and SOUNDKIT[key] and PlaySound then PlaySound(SOUNDKIT[key]) end
end

local DIALOG_BACKDROP = {
  bgFile = "Interface\\DialogFrame\\UI-DialogBox-Background",
  edgeFile = "Interface\\DialogFrame\\UI-DialogBox-Border",
  tile = true, tileSize = 32, edgeSize = 32,
  insets = { left = 11, right = 12, top = 12, bottom = 11 },
}

-- A plain frame with Blizzard's dialog backdrop. BackdropTemplate is needed
-- for SetBackdrop on modern-engine clients; older ones have SetBackdrop built in.
function UI.DialogFrame(name, parent)
  local f = CreateFrame("Frame", name, parent or UIParent,
    (BackdropTemplateMixin and "BackdropTemplate") or nil)
  if f.SetBackdrop then f:SetBackdrop(DIALOG_BACKDROP) end
  return f
end

local function closeOnEsc(name)
  -- UISpecialFrames is how Blizzard's own Esc handler finds frames to close.
  -- Appending a name is the documented pattern (ADDON_PLAN 5.1) and needs
  -- a named frame; that's why our windows have global frame names.
  if name and UISpecialFrames then table.insert(UISpecialFrames, name) end
end

local function makeMovable(f, saveKey)
  f:SetMovable(true)
  f:EnableMouse(true)
  f:RegisterForDrag("LeftButton")
  f:SetClampedToScreen(true)
  f:SetScript("OnDragStart", f.StartMoving)
  f:SetScript("OnDragStop", function(self)
    self:StopMovingOrSizing()
    if saveKey then
      local point, _, relPoint, x, y = self:GetPoint(1)
      R2F.Library.db.settings[saveKey] = { point, relPoint, x, y }
    end
  end)
end

-- Main window shell (5.1): PortraitFrameTemplate if the client has it, else
-- ButtonFrameTemplate, else a dialog-backdrop frame with a close button.
-- Returns the frame; frame.r2fSetTitle(text), frame.r2fPortrait (texture or nil).
function UI.Window(name, width, height, saveKey)
  local hasClose = function(f) return f.CloseButton ~= nil end
  local f = UI.TryTemplate("Frame", name, UIParent, "PortraitFrameTemplate", hasClose)
    or UI.TryTemplate("Frame", name .. "B", UIParent, "ButtonFrameTemplate", hasClose)
  local frameName = f and f:GetName() or (name .. "Plain")
  if not f then
    f = UI.DialogFrame(frameName, UIParent)
    local close = CreateFrame("Button", nil, f, "UIPanelCloseButton")
    close:SetPoint("TOPRIGHT", -4, -4)
    f.CloseButton = close
    local title = f:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    title:SetPoint("TOP", 0, -16)
    f.r2fTitle = title
  end
  f:SetSize(width, height)
  f:SetFrameStrata("HIGH")
  f:SetToplevel(true)
  f:Hide()

  local pos = saveKey and R2F.Library.db.settings[saveKey]
  if type(pos) == "table" and pos[1] then
    f:SetPoint(pos[1], UIParent, pos[2] or pos[1], pos[3] or 0, pos[4] or 0)
  else
    f:SetPoint("CENTER", UIParent, "CENTER", 0, 40)
  end
  makeMovable(f, saveKey)
  closeOnEsc(frameName)

  -- Title: PortraitFrameMixin:SetTitle on modern templates, TitleText or
  -- TitleContainer.TitleText on others, our own font string on the fallback.
  function f.r2fSetTitle(text)
    if f.SetTitle then
      f:SetTitle(text)
    elseif f.TitleText then
      f.TitleText:SetText(text)
    elseif f.TitleContainer and f.TitleContainer.TitleText then
      f.TitleContainer.TitleText:SetText(text)
    elseif f.r2fTitle then
      f.r2fTitle:SetText(text)
    end
  end

  -- Portrait texture: newer templates nest it in PortraitContainer, older
  -- ones expose .portrait. Missing on the fallback (no portrait then).
  f.r2fPortrait = (f.PortraitContainer and f.PortraitContainer.portrait) or f.portrait
    or (f.GetPortrait and f:GetPortrait()) or nil
  return f
end

-- ---------------------------------------------------------------------------
-- Multi-line edit box (import paste box, copy box)
-- ---------------------------------------------------------------------------

-- InputScrollFrameTemplate if available (ADDON_PLAN 5.6), else
-- UIPanelScrollFrameTemplate + our own EditBox. Returns scrollFrame, editBox.
-- Scroll templates name their scroll bar "$parentScrollBar", so the scroll
-- frame gets a global name (R2F-prefixed) to keep that from colliding.
function UI.MultiLineEdit(parent, name, width, height)
  local scroll = UI.TryTemplate("ScrollFrame", name, parent, "InputScrollFrameTemplate",
    function(s) return s.EditBox ~= nil end)
  local edit
  if scroll then
    edit = scroll.EditBox
    -- No character limit (an all-classes string is ~83 KB, 4.5) and no
    -- counter under the box.
    edit:SetMaxLetters(0)
    if edit.SetMaxBytes then edit:SetMaxBytes(0) end
    if scroll.CharCount then scroll.CharCount:Hide() end
  else
    scroll = CreateFrame("ScrollFrame", name .. "Plain", parent, "UIPanelScrollFrameTemplate")
    edit = CreateFrame("EditBox", nil, scroll)
    edit:SetMultiLine(true)
    edit:SetAutoFocus(false)
    edit:SetFontObject(ChatFontNormal or GameFontHighlight)
    edit:SetMaxLetters(0)
    edit:SetScript("OnEscapePressed", edit.ClearFocus)
    scroll:SetScrollChild(edit)
    -- The edit box is only as tall as its text; clicks below it should
    -- still put the cursor in the box.
    scroll:EnableMouse(true)
    scroll:SetScript("OnMouseDown", function() edit:SetFocus() end)
  end
  scroll:SetSize(width, height)
  edit:SetWidth(width)
  return scroll, edit
end

-- ---------------------------------------------------------------------------
-- Confirm dialog (5.9 Replace/Keep mine, Tidy up)
-- ---------------------------------------------------------------------------

local confirm

local function buildConfirm()
  local f = UI.DialogFrame("R2FConfirm", UIParent)
  f:SetSize(380, 140)
  f:SetPoint("CENTER", 0, 120)
  f:SetFrameStrata("DIALOG")
  f:SetToplevel(true)
  f:EnableMouse(true)
  f:Hide()
  closeOnEsc("R2FConfirm")

  local text = f:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  text:SetPoint("TOP", 0, -24)
  text:SetWidth(330)
  text:SetJustifyH("CENTER")
  f.text = text

  local yes = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  yes:SetSize(120, 22)
  yes:SetPoint("BOTTOMRIGHT", f, "BOTTOM", -6, 18)
  local no = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
  no:SetSize(120, 22)
  no:SetPoint("BOTTOMLEFT", f, "BOTTOM", 6, 18)
  f.yes, f.no = yes, no

  yes:SetScript("OnClick", function()
    local fn = f.onAccept
    f.onAccept = nil
    f:Hide()
    if fn then fn() end
  end)
  no:SetScript("OnClick", function()
    f.onAccept = nil
    f:Hide()
  end)
  return f
end

-- One dialog at a time; a new request replaces the old one.
function UI.Confirm(text, acceptLabel, cancelLabel, onAccept)
  confirm = confirm or buildConfirm()
  confirm.text:SetText(text)
  confirm.yes:SetText(acceptLabel)
  confirm.no:SetText(cancelLabel)
  confirm.onAccept = onAccept
  confirm:SetHeight(math.max(140, confirm.text:GetStringHeight() + 80))
  confirm:Show()
  UI.PlaySound("IG_MAINMENU_OPEN")
end

-- ---------------------------------------------------------------------------
-- Copy box (right-click > Copy text)
-- ---------------------------------------------------------------------------

local copyBox

function UI.ShowCopy(text)
  if not copyBox then
    local f = UI.DialogFrame("R2FCopy", UIParent)
    f:SetSize(420, 220)
    f:SetPoint("CENTER", 0, 80)
    f:SetFrameStrata("DIALOG")
    f:SetToplevel(true)
    f:EnableMouse(true)
    f:Hide()
    closeOnEsc("R2FCopy")
    local hint = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
    hint:SetPoint("TOP", 0, -18)
    hint:SetText(R2F.L.COPY_HINT)
    local scroll, edit = UI.MultiLineEdit(f, "R2FCopyScroll", 350, 130)
    scroll:SetPoint("TOPLEFT", 24, -44)
    edit:SetScript("OnEscapePressed", function() f:Hide() end)
    -- Keep the text intact: typing into the copy box would only confuse.
    edit:HookScript("OnTextChanged", function(self, user)
      if user then self:SetText(f.text or ""); self:HighlightText() end
    end)
    local close = CreateFrame("Button", nil, f, "UIPanelCloseButton")
    close:SetPoint("TOPRIGHT", -4, -4)
    f.edit = edit
    copyBox = f
  end
  copyBox.text = text
  copyBox.edit:SetText(text)
  copyBox:Show()
  copyBox.edit:SetFocus()
  copyBox.edit:HighlightText()
end
