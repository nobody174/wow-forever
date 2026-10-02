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
-- Confirm dialog (5.9 Replace/Keep mine, Tidy up, Settings > Remove all)
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

-- "VR, HS, Rend" for a popup. More than `max` names -> "VR, HS and 12 more",
-- so a big Remove all / Tidy up can't grow the dialog off the screen.
function UI.NameList(names, max)
  max = max or 20
  if #names <= max then return table.concat(names, ", ") end
  local head = {}
  for i = 1, max do head[i] = names[i] end
  return R2F.L.LIST_MORE:format(table.concat(head, ", "), #names - max)
end

-- ---------------------------------------------------------------------------
-- Check box / radio button (Settings, 5.8)
-- ---------------------------------------------------------------------------

-- Blizzard's UIRadioButtonTemplate / UICheckButtonTemplate when the client
-- has them, else a plain CheckButton with Blizzard's check-box textures.
-- The label is always our own font string to the right: the templates' text
-- region differs between clients (.text, .Text or only a global $parentText),
-- and the radio template's is not guaranteed to exist at all.
-- Callers set the checked state themselves from the saved setting after every
-- click, rather than trusting the button's own toggle, so a radio pair can't
-- end up with both or neither checked.
function UI.CheckButton(parent, label, radio)
  local isButton = function(b) return b.SetChecked ~= nil end
  local b = UI.TryTemplate("CheckButton", nil, parent, radio and "UIRadioButtonTemplate" or "UICheckButtonTemplate", isButton)
  if not b and radio then
    b = UI.TryTemplate("CheckButton", nil, parent, "UICheckButtonTemplate", isButton)
  end
  if not b then
    b = CreateFrame("CheckButton", nil, parent)
    b:SetNormalTexture("Interface\\Buttons\\UI-CheckBox-Up")
    b:SetPushedTexture("Interface\\Buttons\\UI-CheckBox-Down")
    b:SetHighlightTexture("Interface\\Buttons\\UI-CheckBox-Highlight", "ADD")
    b:SetCheckedTexture("Interface\\Buttons\\UI-CheckBox-Check")
  end
  b:SetSize(radio and 16 or 24, radio and 16 or 24)
  local text = b:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  text:SetPoint("LEFT", b, "RIGHT", 4, 0)
  text:SetText(label)
  -- Clicking the label toggles too, like Blizzard's own option check boxes.
  b:SetHitRectInsets(0, -(text:GetStringWidth() + 4), 0, 0)
  b.r2fLabel = text
  return b
end

-- ---------------------------------------------------------------------------
-- Context menu (minimap button right-click, 12.2)
-- ---------------------------------------------------------------------------

-- items = { { kind = "title" | "button" | "check" | "divider", text =,
--             func = function() end, isChecked = function() return bool end }, ... }
--
-- Why not UIDropDownMenu / EasyMenu: those write Blizzard's shared
-- UIDROPDOWNMENU_* globals, the classic source of "action blocked" taint in
-- Classic clients (6.7). Blizzard's newer MenuUtil doesn't have that problem
-- and Minimap.lua uses it when the client has it; this plain frame is the
-- fallback, built from tooltip/quest textures so it still looks native.
-- One menu at a time (named, so Esc closes it); it closes after a click or
-- when the mouse has left it for a moment, like MacroBook's two-item menu.
local menuFrame
local ROW_H, MENU_W = 18, 190

local function buildMenuFrame()
  local m = CreateFrame("Frame", "R2FMenu", UIParent, (BackdropTemplateMixin and "BackdropTemplate") or nil)
  if m.SetBackdrop then
    m:SetBackdrop({
      bgFile = "Interface\\Tooltips\\UI-Tooltip-Background",
      edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
      tile = true, tileSize = 16, edgeSize = 16,
      insets = { left = 4, right = 4, top = 4, bottom = 4 },
    })
    m:SetBackdropColor(0, 0, 0, 0.9)
  end
  m:SetFrameStrata("DIALOG")
  m:SetClampedToScreen(true)
  m:EnableMouse(true)
  m:Hide()
  m.rows = {}
  closeOnEsc("R2FMenu")
  m:SetScript("OnLeave", function(self)
    if not (C_Timer and C_Timer.After) then return end
    C_Timer.After(0.4, function()
      if self:IsShown() and not self:IsMouseOver() then self:Hide() end
    end)
  end)
  return m
end

local function menuRow(m, i)
  local r = m.rows[i]
  if r then return r end
  r = CreateFrame("Button", nil, m)
  r:SetSize(MENU_W - 16, ROW_H)
  r:SetPoint("TOPLEFT", 8, -8 - (i - 1) * ROW_H)
  r:SetHighlightTexture("Interface\\QuestFrame\\UI-QuestTitleHighlight", "ADD")
  r.text = r:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  r.text:SetPoint("LEFT", 20, 0)
  r.text:SetJustifyH("LEFT")
  r.check = r:CreateTexture(nil, "ARTWORK")
  r.check:SetSize(16, 16)
  r.check:SetPoint("LEFT", 0, 0)
  r.line = r:CreateTexture(nil, "ARTWORK")
  r.line:SetTexture("Interface\\Common\\UI-TooltipDivider-Transparent")
  r.line:SetSize(MENU_W - 24, 8)
  r.line:SetPoint("LEFT", 4, 0)
  -- Stay open while the mouse moves over the rows (they're the menu too).
  r:SetScript("OnLeave", function() local s = m:GetScript("OnLeave"); if s then s(m) end end)
  m.rows[i] = r
  return r
end

function UI.ContextMenu(items)
  menuFrame = menuFrame or buildMenuFrame()
  local m = menuFrame
  m.items = items
  for i, it in ipairs(items) do
    local r = menuRow(m, i)
    r.item = it
    r.text:SetText(it.text or "")
    r.line:SetShown(it.kind == "divider")
    if it.kind == "title" then
      r.text:SetFontObject(GameFontNormalSmall or GameFontHighlight)
      r.text:SetPoint("LEFT", 0, 0)
    else
      r.text:SetFontObject(GameFontHighlightSmall or GameFontHighlight)
      r.text:SetPoint("LEFT", 20, 0)
    end
    -- Title and divider rows aren't clickable (12.2: "not clickable").
    r:SetEnabled(it.kind == "button" or it.kind == "check")
    r:EnableMouse(it.kind == "button" or it.kind == "check")
    if it.kind == "check" then
      local on = it.isChecked and it.isChecked()
      r.check:SetTexture(on and "Interface\\Buttons\\UI-CheckBox-Check" or "Interface\\Buttons\\UI-CheckBox-Up")
      r.check:Show()
    else
      r.check:Hide()
    end
    r:SetScript("OnClick", function(self)
      m:Hide()
      if self.item and self.item.func then self.item.func() end
    end)
    r:Show()
  end
  for i = #items + 1, #m.rows do m.rows[i]:Hide(); m.rows[i].item = nil end
  m:SetSize(MENU_W, #items * ROW_H + 16)
  m:ClearAllPoints()
  -- Under the cursor, so the mouse starts inside it.
  local x, y = GetCursorPosition()
  local scale = UIParent:GetEffectiveScale()
  m:SetPoint("TOPLEFT", UIParent, "BOTTOMLEFT", x / scale - 20, y / scale + 10)
  m:Show()
  return m
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
