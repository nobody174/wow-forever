-- Minimal fake WoW client for running the addon under plain Lua 5.1.
-- Not a WoW emulator: just enough API surface for the addon's code paths,
-- plus strictness where it matters (macro writes in combat raise an error,
-- like the real protected calls do).
--
-- Loaded by run_tests.py into a fresh Lua state before the addon files.

local T = {}          -- test controls, returned to the harness
_G.TEST = T

T.combat = false
T.timers = {}
T.errors = {}         -- UIErrorsFrame messages
T.chat = {}           -- DEFAULT_CHAT_FRAME messages
T.cursor = nil        -- name of the macro on the cursor
T.actions = {}        -- slot -> macro name
T.knownSpells = { ["Victory Rush"] = "Interface\\Icons\\Ability_Warrior_Devastate",
                  ["Heroic Strike"] = "Interface\\Icons\\Ability_Rogue_Ambush" }
T.templates = { PortraitFrameTemplate = true, InputScrollFrameTemplate = true,
                UIPanelButtonTemplate = true, UIPanelCloseButton = true,
                UIPanelScrollFrameTemplate = true, BackdropTemplate = true,
                ButtonFrameTemplate = true }
T.calls = {}          -- log of macro API writes

-- ---------------------------------------------------------------------------
-- Macros: account slots 1..120, character 121..138, each set kept sorted by
-- name like the real client (so indices shift on create/delete/rename).
-- ---------------------------------------------------------------------------
local MAX_ACC, MAX_CHAR = 120, 18
local acc, char = {}, {}
T.macros = { acc = acc, char = char }

local function sortSet(set) table.sort(set, function(a, b) return a.name < b.name end) end
local function byIndex(i)
  if i >= 1 and i <= MAX_ACC then return acc[i], acc, i end
  if i > MAX_ACC then return char[i - MAX_ACC], char, i - MAX_ACC end
end
local function protected(what)
  if T.combat then error(what .. ": blocked in combat (protected)", 2) end
end

function GetNumMacros() return #acc, #char end
function GetMacroIndexByName(name)
  for i, m in ipairs(acc) do if m.name == name then return i end end
  for i, m in ipairs(char) do if m.name == name then return MAX_ACC + i end end
  return 0
end
function GetMacroInfo(i)
  local m = byIndex(i)
  if m then return m.name, m.icon, m.body end
end
function CreateMacro(name, icon, body, perCharacter)
  protected("CreateMacro")
  local set = perCharacter and char or acc
  if #set >= (perCharacter and MAX_CHAR or MAX_ACC) then error("CreateMacro: macro limit reached") end
  table.insert(set, { name = name, icon = icon, body = body })
  sortSet(set)
  table.insert(T.calls, "create:" .. name)
  return GetMacroIndexByName(name)
end
function EditMacro(i, name, icon, body)
  protected("EditMacro")
  local m, set = byIndex(i)
  assert(m, "EditMacro: bad index " .. tostring(i))
  m.name = name or m.name
  if icon then m.icon = icon end
  if body then m.body = body end
  sortSet(set)
  table.insert(T.calls, "edit:" .. m.name)
  return GetMacroIndexByName(m.name)
end
function DeleteMacro(i)
  protected("DeleteMacro")
  local m, set, j = byIndex(i)
  assert(m, "DeleteMacro: bad index " .. tostring(i))
  table.remove(set, j)
  table.insert(T.calls, "delete:" .. m.name)
end
function PickupMacro(i)
  protected("PickupMacro")
  local m = byIndex(i)
  assert(m, "PickupMacro: bad index " .. tostring(i))
  T.cursor = m.name
end
-- Test helper: the player's own macro (not via the addon).
function T.addMacro(name, body, perCharacter)
  local set = perCharacter and char or acc
  table.insert(set, { name = name, icon = "X", body = body })
  sortSet(set)
end
function T.setBody(name, body)
  local m = byIndex(GetMacroIndexByName(name))
  m.body = body
end
function T.bodyOf(name)
  local i = GetMacroIndexByName(name)
  if i > 0 then return (select(3, GetMacroInfo(i))) end
end
function T.reset()
  for k in pairs(acc) do acc[k] = nil end
  for k in pairs(char) do char[k] = nil end
  T.actions, T.cursor, T.errors, T.chat, T.calls, T.combat = {}, nil, {}, {}, {}, false
end

function GetActionInfo(slot)
  local name = T.actions[slot]
  if name then
    local i = GetMacroIndexByName(name)
    if i > 0 then return "macro", i end
  end
  return nil
end
function GetActionText(slot)
  local name = T.actions[slot]
  if name and GetMacroIndexByName(name) > 0 then return name end
end

function InCombatLockdown() return T.combat end
function GetSpellTexture(name) return T.knownSpells[name] end
function GetItemInfo() return nil end
function UnitClass() return "Warrior", "WARRIOR", 1 end
function IsShiftKeyDown() return T.shift or false end
function GetCursorPosition() return 500, 400 end
function PlaySound() end
SOUNDKIT = { IG_SPELLBOOK_OPEN = 1, IG_SPELLBOOK_CLOSE = 2, IG_ABILITY_PAGE_TURN = 3, IG_MAINMENU_OPEN = 4 }
time = os.time
C_Timer = { After = function(_, fn) table.insert(T.timers, fn) end }
function T.runTimers()
  for _ = 1, 10 do
    local list = T.timers
    if #list == 0 then return end
    T.timers = {}
    for _, fn in ipairs(list) do fn() end
  end
end
C_XMLUtil = { GetTemplateInfo = function(name) if T.templates[name] then return {} end end }
CLASS_ICON_TCOORDS = { WARRIOR = { 0, 0.25, 0, 0.25 }, PALADIN = { 0, 0.25, 0.5, 0.75 } }
LOCALIZED_CLASS_NAMES_MALE = { WARRIOR = "Warrior", PALADIN = "Paladin", HUNTER = "Hunter",
  PRIEST = "Priest", ROGUE = "Rogue", MAGE = "Mage", WARLOCK = "Warlock", SHAMAN = "Shaman" }
UISpecialFrames = {}
SlashCmdList = {}
BackdropTemplateMixin = {}
function ChatEdit_InsertLink(text) T.chatInsert = text; return true end

-- ---------------------------------------------------------------------------
-- Frames: generic objects. Unknown methods are no-ops returning nil, so the
-- tests catch logic/nil errors in our code, not missing stub methods.
-- ---------------------------------------------------------------------------
local noop = function() end
local methods = {}
-- Strict like real widgets: unknown keys are nil, so a misspelt method or a
-- template child that doesn't exist fails the tests. Real widget methods we
-- call but don't need to model are listed here as no-ops.
for _, name in ipairs({
  "SetSize", "SetWidth", "SetHeight", "SetPoint", "ClearAllPoints", "SetAllPoints",
  "SetFrameStrata", "SetToplevel", "SetMovable", "EnableMouse", "RegisterForDrag",
  "SetClampedToScreen", "StartMoving", "StopMovingOrSizing", "SetBackdrop",
  "SetBackdropColor", "SetJustifyH", "SetTexCoord", "SetHighlightTexture",
  "SetPushedTexture", "SetDisabledTexture", "SetCheckedTexture", "RegisterForClicks",
  "SetMultiLine", "SetAutoFocus", "SetFontObject", "SetMaxLetters", "SetMaxBytes",
  "SetScrollChild", "SetFocus", "ClearFocus", "HighlightText",
  "SetMotionScriptsWhileDisabled",
}) do methods[name] = noop end
local MT = { __index = methods }

local function newObject(kind, name, parent)
  local o = setmetatable({ __kind = kind, __shown = true, __scripts = {}, __text = "",
    __parent = parent, __enabled = true, __name = name }, MT)
  if name then _G[name] = o end
  return o
end

function methods:GetName() return self.__name end
function methods:Show()
  local was = self:IsShown()
  self.__shown = true
  if not was and self:IsShown() and self.__scripts.OnShow then self.__scripts.OnShow(self) end
end
function methods:Hide()
  local was = self.__shown
  self.__shown = false
  if was and self.__scripts.OnHide then self.__scripts.OnHide(self) end
end
function methods:SetShown(v) if v then self:Show() else self:Hide() end end
function methods:IsShown() return self.__shown end
function methods:IsVisible() return self.__shown end
function methods:SetScript(k, fn) self.__scripts[k] = fn end
function methods:GetScript(k) return self.__scripts[k] end
function methods:HookScript(k, fn)
  local old = self.__scripts[k]
  self.__scripts[k] = old and function(...) old(...); fn(...) end or fn
end
function methods:SetText(t)
  self.__text = t
  if self.__kind == "EditBox" and self.__scripts.OnTextChanged then self.__scripts.OnTextChanged(self, false) end
end
function methods:GetText() return self.__text end
function methods:SetEnabled(v) self.__enabled = not not v end
function methods:Enable() self.__enabled = true end
function methods:Disable() self.__enabled = false end
function methods:IsEnabled() return self.__enabled end
function methods:SetChecked(v) self.__checked = not not v end
function methods:GetChecked() return self.__checked end
function methods:CreateTexture() return newObject("Texture") end
function methods:CreateFontString() return newObject("FontString") end
function methods:GetStringHeight() return 14 end
function methods:GetEffectiveScale() return 1 end
function methods:IsMouseOver() return false end
function methods:GetPoint() return "CENTER", nil, "CENTER", 10, 20 end
function methods:SetNormalTexture(t) self.__normal = self.__normal or newObject("Texture"); self.__normal.__tex = t end
function methods:GetNormalTexture() return self.__normal end
function methods:SetTexture(t) self.__tex = t end
function methods:SetDesaturated(v) self.__desat = v end
function methods:SetTextColor(r, g, b) self.__color = { r, g, b } end
function methods:SetVertexColor(r, g, b) self.__vertex = { r, g, b } end
function methods:RegisterEvent(e) self.__events = self.__events or {}; self.__events[e] = true end
function methods:UnregisterEvent(e) if self.__events then self.__events[e] = nil end end
-- Test helpers on frames
function methods:Click(button)
  if self.__enabled and self.__scripts.OnClick then self.__scripts.OnClick(self, button or "LeftButton") end
end
function methods:Fire(script, ...)
  if self.__scripts[script] then self.__scripts[script](self, ...) end
end

function CreateFrame(kind, name, parent, template)
  if template and not T.templates[template] then
    -- Real client: unknown template = frame without it (logged, no error).
    return newObject(kind, name, parent)
  end
  local f = newObject(kind, name, parent)
  if template == "PortraitFrameTemplate" or template == "ButtonFrameTemplate" then
    f.CloseButton = newObject("Button", nil, f)
    f.PortraitContainer = { portrait = newObject("Texture") }
    f.SetTitle = function(self, t) self.__title = t end
  elseif template == "InputScrollFrameTemplate" then
    f.EditBox = newObject("EditBox", nil, f)
    f.CharCount = newObject("FontString")
  end
  return f
end

UIParent = newObject("Frame", "UIParent")
GameTooltip = newObject("GameTooltip", "GameTooltip")
GameTooltip.lines = {}
function GameTooltip:SetOwner() self.lines = {} end
function GameTooltip:AddLine(t) table.insert(self.lines, t) end
UIErrorsFrame = newObject("Frame", "UIErrorsFrame")
function UIErrorsFrame:AddMessage(m) table.insert(T.errors, m) end
DEFAULT_CHAT_FRAME = newObject("Frame", "DEFAULT_CHAT_FRAME")
function DEFAULT_CHAT_FRAME:AddMessage(m) table.insert(T.chat, m) end

-- Find the frame the addon registered for events (Core.lua's anonymous one).
T.allFrames = {}
local origNew = newObject
newObject = function(kind, name, parent)
  local o = origNew(kind, name, parent)
  table.insert(T.allFrames, o)
  return o
end
function T.fire(event, ...)
  for _, f in ipairs(T.allFrames) do
    if f.__events and f.__events[event] and f.__scripts.OnEvent then
      f.__scripts.OnEvent(f, event, ...)
    end
  end
end

return T
