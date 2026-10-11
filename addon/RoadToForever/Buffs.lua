-- Buffs.lua: "buffs your group could give you, that you don't have" reminder (ADDON_PLAN.md 17.1 step 5, v0.29.0).
--
-- While you are in a party or raid, the classes in it decide which buffs to look for: a Priest
-- (anyone in the group, you too) -> Power Word: Fortitude, a Druid -> Mark of the Wild and Thorns, a Mage ->
-- Arcane Intellect, a Paladin -> any Blessing, a Warrior -> Battle Shout, and so on. For every one of those
-- you are missing, a small framed icon shows on screen (a row of them if several are missing); each is gone
-- the moment you have the buff. Only YOUR buffs are looked at (not the other members').
--
-- Reads your own helpful auras (C_UnitAuras.GetUnitAuras("player", "HELPFUL"); /r2f auras showed they are
-- readable out of combat). If the game hides them (secret values, e.g. in combat or an instance) the reminder
-- says nothing rather than guessing: a missing buff is only shown when the list was fully readable.
-- Unlocked, it always shows (dimmed when nothing is missing) so it can be moved.
-- Buff names are matched in English (the game's spell names). Settings in R2FDB.buffs: shown, lock, scale, x, y,
-- and one true/false per buff in LIST.

local _, R2F = ...
local L = R2F.L

local Buffs = {}
R2F.Buffs = Buffs

local ATTENTION = { r = 0.95, g = 0.75, b = 0.1 }
local GAP = 4

-- key, provider class, the aura names that count as "you have it" (exact) and/or Lua patterns in `like`,
-- the icon file, label key.
Buffs.LIST = {
  { key = "fortitude", class = "PRIEST", names = { "Power Word: Fortitude", "Prayer of Fortitude" },
    icon = "Interface\\Icons\\Spell_Holy_WordFortitude", label = "BUFFS_FORTITUDE" },
  { key = "motw", class = "DRUID", names = { "Mark of the Wild", "Gift of the Wild" },
    icon = "Interface\\Icons\\Spell_Nature_Regeneration", label = "BUFFS_MOTW" },
  { key = "thorns", class = "DRUID", names = { "Thorns" },
    icon = "Interface\\Icons\\Spell_Nature_Thorns", label = "BUFFS_THORNS" },
  { key = "intellect", class = "MAGE", names = { "Arcane Intellect", "Arcane Brilliance" },
    icon = "Interface\\Icons\\Spell_Holy_MagicalSentry", label = "BUFFS_INTELLECT" },
  { key = "blessing", class = "PALADIN", like = { "^Blessing of ", "^Greater Blessing of " },
    icon = "Interface\\Icons\\Spell_Magic_GreaterBlessingofKings", label = "BUFFS_BLESSING" },
  { key = "spirit", class = "PRIEST", names = { "Divine Spirit", "Prayer of Spirit" },
    icon = "Interface\\Icons\\Spell_Holy_DivineSpirit", label = "BUFFS_SPIRIT" },
  { key = "shadowprot", class = "PRIEST", names = { "Shadow Protection", "Prayer of Shadow Protection" },
    icon = "Interface\\Icons\\Spell_Shadow_AntiShadow", label = "BUFFS_SHADOWPROT" },
  { key = "battleshout", class = "WARRIOR", names = { "Battle Shout" },
    icon = "Interface\\Icons\\Ability_Warrior_BattleShout", label = "BUFFS_BATTLESHOUT" },
  { key = "trueshot", class = "HUNTER", names = { "Trueshot Aura" },
    icon = "Interface\\Icons\\Ability_TrueShot", label = "BUFFS_TRUESHOT" },
}
local BY_KEY = {}
for _, b in ipairs(Buffs.LIST) do BY_KEY[b.key] = b end

Buffs.MIN_SCALE, Buffs.MAX_SCALE = R2F.Reminders.MIN_SCALE, R2F.Reminders.MAX_SCALE

local frame            -- the draggable first icon
local extras = {}      -- further icons, to the right of it

local function db()
  return R2F.Library.db.buffs
end
Buffs.Db = db

local function isSecret(v)
  return type(_G.issecretvalue) == "function" and _G.issecretvalue(v) == true
end

-- The classes in your group (you included): { PRIEST = true, ... }. Empty when you are alone.
function Buffs.GroupClasses()
  local out = {}
  local raid = IsInRaid and IsInRaid()
  if not (raid or (IsInGroup and IsInGroup())) then return out end
  local function add(unit)
    if UnitExists and UnitExists(unit) then
      local _, class = UnitClass(unit)
      if class then out[class] = true end
    end
  end
  add("player")
  if raid then
    for i = 1, (GetNumGroupMembers and GetNumGroupMembers() or 0) do add("raid" .. i) end
  else
    for i = 1, 4 do add("party" .. i) end
  end
  return out
end

-- The names of your helpful auras, or nil when the game won't tell (secret values / no API).
function Buffs.MyAuraNames()
  local ns = _G.C_UnitAuras
  if not (ns and ns.GetUnitAuras) then return nil end
  local ok, list = pcall(ns.GetUnitAuras, "player", "HELPFUL")
  if not ok or type(list) ~= "table" then return nil end
  local names = {}
  for _, aura in ipairs(list) do
    local name = type(aura) == "table" and aura.name or nil
    if name == nil or isSecret(name) or type(name) ~= "string" then return nil end
    names[#names + 1] = name
  end
  return names
end

local function haveBuff(buff, auraNames)
  for _, name in ipairs(auraNames) do
    for _, n in ipairs(buff.names or {}) do
      if name == n then return true end
    end
    for _, pat in ipairs(buff.like or {}) do
      if name:find(pat) then return true end
    end
  end
  return false
end

-- The buffs to show now: a list of LIST entries, in LIST order. Empty when nothing is missing or
-- when your auras can't be read.
function Buffs.Missing()
  local d = db()
  if not d.shown then return {} end
  local classes = Buffs.GroupClasses()
  if next(classes) == nil then return {} end
  if UnitIsDeadOrGhost and UnitIsDeadOrGhost("player") then return {} end
  local auras = Buffs.MyAuraNames()
  if not auras then return {} end
  local out = {}
  for _, b in ipairs(Buffs.LIST) do
    if d[b.key] and classes[b.class] and not haveBuff(b, auras) then out[#out + 1] = b end
  end
  return out
end

local function extraIcon(i)
  if extras[i] then return extras[i] end
  local f = CreateFrame("Frame", nil, frame)
  f:SetSize(frame:GetWidth(), frame:GetHeight())
  f.border = f:CreateTexture(nil, "BACKGROUND")
  f.border:SetAllPoints()
  f.border:SetColorTexture(ATTENTION.r, ATTENTION.g, ATTENTION.b, 1)
  f.icon = f:CreateTexture(nil, "ARTWORK")
  f.icon:SetPoint("TOPLEFT", 3, -3)
  f.icon:SetPoint("BOTTOMRIGHT", -3, 3)
  f.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  extras[i] = f
  return f
end

function Buffs.Update()
  if not frame then return end
  local d = db()
  local missing = Buffs.Missing()
  -- Unlocked with nothing missing (alone or in a full-buffed group): one dimmed sample icon so you
  -- can drag it into place (lock it to hide it).
  local sample = (#missing == 0) and d.shown and not d.lock
  if #missing == 0 and not sample then
    frame:Hide()
    for _, e in ipairs(extras) do e:Hide() end
    return
  end
  frame:Show()
  frame:EnableMouse(not d.lock)
  local first = missing[1] or BY_KEY.fortitude
  frame.icon:SetTexture(first.icon)
  frame.icon:SetDesaturated(sample and true or false)
  frame.border:SetColorTexture(ATTENTION.r, ATTENTION.g, ATTENTION.b, 1)
  frame.count:SetText("")
  frame.buff = first
  for i = 1, math.max(#extras, #missing - 1) do
    local b = missing[i + 1]
    if b then
      local f = extraIcon(i)
      f:ClearAllPoints()
      f:SetPoint("LEFT", i == 1 and frame or extras[i - 1], "RIGHT", GAP, 0)
      f.icon:SetTexture(b.icon)
      f.buff = b
      f:Show()
    elseif extras[i] then
      extras[i]:Hide()
    end
  end
end

-- PLAYER_LOGIN (Core.lua).
function Buffs.Init()
  if frame then return end
  frame = R2F.Reminders.NewIcon("R2FGroupBuffFrame", db, "REM_DRAG_TIP")
  frame:Place()
  local ev = CreateFrame("Frame")
  ev:SetScript("OnEvent", Buffs.Update)
  for _, e in ipairs({ "GROUP_ROSTER_UPDATE", "PLAYER_ENTERING_WORLD", "PLAYER_DEAD", "PLAYER_ALIVE", "PLAYER_UNGHOST" }) do
    pcall(ev.RegisterEvent, ev, e)
  end
  if not pcall(ev.RegisterUnitEvent, ev, "UNIT_AURA", "player") then pcall(ev.RegisterEvent, ev, "UNIT_AURA") end
  Buffs.Update()
end

function Buffs.Apply()
  if not frame then return end
  frame:Place()
  Buffs.Update()
  R2F.Reminders.RefreshUI()
end

function Buffs.SetShown(on)
  db().shown = on and true or false
  Buffs.Apply()
end

function Buffs.SetLock(on)
  db().lock = on and true or false
  Buffs.Apply()
end

function Buffs.SetScale(v)
  db().scale = R2F.Reminders.ClampScale(v)
  Buffs.Apply()
end

function Buffs.SetBuff(key, on)
  if BY_KEY[key] then db()[key] = on and true or false end
  Buffs.Apply()
end

local checks = {}
for _, b in ipairs(Buffs.LIST) do
  checks[#checks + 1] = { label = b.label, get = function() return db()[b.key] end, set = function(v) Buffs.SetBuff(b.key, v) end }
end

R2F.Reminders.Register({
  key = "buffs", class = nil, module = Buffs,
  title = "REM_BUFFS_TITLE", show = "BUFFS_SHOW", lock = "BUFFS_LOCK", size = "BUFFS_SIZE",
  checks = checks,
})
