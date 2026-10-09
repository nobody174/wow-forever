-- GameplayChat.lua: copy chat text (ADDON_PLAN.md 17.2, v0.24.0). Replaces Prat 3.0 for the one
-- thing the owner used it for: getting lines out of chat to paste somewhere (bug reports).
--
-- Chat text can't be selected in the game's own chat frames. This opens a window with the last
-- lines of a chat frame in an edit box: Ctrl+A, Ctrl+C. Two ways in:
--   * `/r2f copychat` (main chat frame) or `/r2f copychat 3` (chat frame 3), always available;
--   * the Gameplay tab's "Copy chat button" adds a small C button in the corner of every chat frame.
-- A "Plain text" tick strips colour codes, links and icons so the pasted text is readable.
--
-- Read-only: it only reads the chat frame's stored lines (GetNumMessages / GetMessageInfo). Written
-- from scratch; Prat 3.0 is GPLv3 and none of its code is used (only the idea of an edit box with
-- the frame's lines).

local _, R2F = ...
local L = R2F.L
local function UI() return R2F.UI end   -- the UI files load after this one
local Gameplay = R2F.Gameplay

local Chat = {}
R2F.CopyChat = Chat

Chat.LINES = 200          -- how many of the newest lines the window shows

local function chatFrame(i)
  local f = _G["ChatFrame" .. i]
  if f and f.GetNumMessages and f.GetMessageInfo then return f end
end

-- The chat frames this client has.
function Chat.Frames()
  local out = {}
  for i = 1, (_G.NUM_CHAT_WINDOWS or 10) do
    local f = chatFrame(i)
    if f then out[#out + 1] = { index = i, frame = f } end
  end
  return out
end

-- Colour codes, links, textures and atlas icons out; the link's visible text stays.
function Chat.Plain(s)
  s = s:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
  s = s:gsub("|H.-|h(.-)|h", "%1")
  s = s:gsub("|T.-|t", ""):gsub("|A.-|a", "")
  s = s:gsub("||", "|")
  return s
end

-- The newest `count` lines of a chat frame, oldest first, one per line.
function Chat.Text(frame, plain, count)
  count = count or Chat.LINES
  local n = frame:GetNumMessages() or 0
  local lines = {}
  for i = math.max(1, n - count + 1), n do
    local msg = frame:GetMessageInfo(i)
    if type(msg) == "string" and msg ~= "" then
      lines[#lines + 1] = plain and Chat.Plain(msg) or msg
    end
  end
  return table.concat(lines, "\n"), #lines
end

-- ---------------------------------------------------------------------------
-- The window
-- ---------------------------------------------------------------------------

local win, edit, countText, plainBox
local current          -- the chat frame shown

local function fill()
  if not (win and current) then return end
  local text, n = Chat.Text(current, plainBox:GetChecked(), Chat.LINES)
  edit:SetText(text)
  countText:SetText(L.CC_COUNT:format(n))
  edit:HighlightText()
  edit:SetFocus()
end

local function build()
  local f = UI().DialogFrame("R2FCopyChat", UIParent)
  f:SetSize(540, 380)
  f:SetPoint("CENTER", 0, 20)
  f:SetFrameStrata("DIALOG")
  f:SetToplevel(true)
  f:EnableMouse(true)
  f:SetMovable(true)
  f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving)
  f:SetScript("OnDragStop", f.StopMovingOrSizing)
  f:Hide()
  if UISpecialFrames then table.insert(UISpecialFrames, "R2FCopyChat") end

  local title = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
  title:SetPoint("TOP", 0, -18)
  title:SetText(L.CC_TITLE)
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton")
  close:SetPoint("TOPRIGHT", -4, -4)

  local scroll
  scroll, edit = UI().MultiLineEdit(f, "R2FCopyChatScroll", 470, 250)
  scroll:SetPoint("TOPLEFT", 26, -46)
  edit:SetScript("OnEscapePressed", function() f:Hide() end)

  plainBox = UI().CheckButton(f, L.CC_PLAIN)
  plainBox:SetPoint("BOTTOMLEFT", 22, 44)
  plainBox:SetChecked(true)
  plainBox:SetScript("OnClick", fill)

  countText = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  countText:SetPoint("BOTTOMRIGHT", -26, 50)

  local hint = f:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
  hint:SetPoint("BOTTOMLEFT", 26, 22)
  hint:SetWidth(480)
  hint:SetJustifyH("LEFT")
  hint:SetText(L.CC_HINT)
  return f
end

-- Open the window on a chat frame object.
function Chat.Show(frame)
  win = win or build()
  current = frame
  win:Show()
  fill()
end

-- `/r2f copychat` or `/r2f copychat 3`.
function Chat.Command(arg)
  local frames = Chat.Frames()
  if #frames == 0 then R2F.Print(L.CC_NONE) return end
  local want = tonumber(arg or "")
  local pick
  for _, c in ipairs(frames) do
    if (want and c.index == want) or (not want and c.index == 1) then pick = c end
  end
  pick = pick or frames[1]
  Chat.Show(pick.frame)
end

-- ---------------------------------------------------------------------------
-- The corner buttons (the Gameplay switch)
-- ---------------------------------------------------------------------------

local buttons = {}

local function makeButton(c)
  local b = buttons[c.index]
  if b then return b end
  b = CreateFrame("Button", "R2FCopyChatButton" .. c.index, c.frame)
  b:SetSize(18, 18)
  b:SetPoint("TOPRIGHT", c.frame, "TOPRIGHT", -2, -2)
  b:SetFrameLevel((c.frame.GetFrameLevel and c.frame:GetFrameLevel() or 0) + 5)
  b:SetNormalTexture("Interface\\Buttons\\UI-DialogBox-Button-Up")
  b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  local label = b:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  label:SetPoint("CENTER", 0, 1)
  label:SetText("C")
  b:SetAlpha(0.4)
  b:SetScript("OnEnter", function(self)
    self:SetAlpha(1)
    GameTooltip:SetOwner(self, "ANCHOR_LEFT")
    GameTooltip:AddLine(L.CC_TIP, 1, 1, 1, true)
    GameTooltip:Show()
  end)
  b:SetScript("OnLeave", function(self) self:SetAlpha(0.4) GameTooltip:Hide() end)
  b:SetScript("OnClick", function() Chat.Show(c.frame) end)
  buttons[c.index] = b
  return b
end

local function setButtons(on)
  for _, c in ipairs(Chat.Frames()) do
    local b = makeButton(c)
    b:SetShown(on)
  end
end

Gameplay.Register({
  key = "copychat", group = "screen", title = "GP_COPYCHAT", tip = "GP_COPYCHAT_TIP",
  available = function() return #Chat.Frames() > 0 end,
  onToggle = setButtons,
})
