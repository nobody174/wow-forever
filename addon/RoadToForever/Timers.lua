-- Timers.lua: "buff countdown" reminders, an on-screen timer for a buff you set off yourself.
--
-- A framed icon (the same look as the stance, ammo, repair and pet icons, Reminders.lua) with the seconds left on a buff
-- of yours, big enough to read at a glance: for example the Skyborne racial Walk on Air (a short glide, the game shows the
-- buff only as a tiny icon). Hidden while the buff is not on you, unless the icon is unlocked so it can be moved.
--
-- One entry of Timers.TRACK = one reminder (icon, Class icons page section, saved settings). Add a line there for another
-- buff: `names` are the aura names to match (English), `spells` the aura / spell ids, `learned` spell ids that tell the
-- section is for you. Auras are read like Buffs.lua does: if the game hands out secret values (in combat, in an instance)
-- nothing is shown rather than guessed.
--
-- Read-only: only aura getters, no protected calls. Settings live in R2FDB.timers[key]: shown, lock, scale, x, y.

local _, R2F = ...
local L = R2F.L

local Timers = {}
R2F.Timers = Timers

Timers.TRACK = {
  { key = "walkonair", names = { "Walking on Air", "Walk on Air" }, spells = { 1259417, 1259416, 1308663 },
    learned = { 1259416, 1308663 }, icon = "Interface\\Icons\\inv_elemental_primal_air",
    title = "REM_WALKAIR_TITLE", show = "TIMER_SHOW", lock = "TIMER_LOCK", size = "TIMER_SIZE" },
  -- Every food that gives a stat also gives +5% experience from kills ("you become well fed"): the aura is "Well Fed".
  -- `missing`: an optional nag (off by default) when you have none; `nagOnly`: show nothing while the buff is on (no icon,
-- no timer), only the "No food" nag once it is gone; `clock`: show minutes (the buff lasts 15 minutes).
  { key = "wellfed", names = {}, spells = {}, like = { "^Well Fed" }, missing = true, nagOnly = true, clock = true,
    icon = "Interface\\Icons\\INV_Misc_Food_15",
    title = "REM_WELLFED_TITLE", show = "TIMER_SHOW", lock = "TIMER_LOCK", size = "TIMER_SIZE" },
}

Timers.MIN_SCALE, Timers.MAX_SCALE = R2F.Reminders.MIN_SCALE, R2F.Reminders.MAX_SCALE

local frames = {}     -- key -> icon frame
local active = {}     -- key -> true while the throttled countdown loop runs
local THROTTLE = 0.1

local function isSecret(v)
  return type(_G.issecretvalue) == "function" and _G.issecretvalue(v) == true
end

local function settings(def)
  local t = R2F.Library.db.timers
  return t and t[def.key]
end

-- Seconds left on the buff, its icon, and whether the auras could be read at all: (nil, nil, false) when the game hides them
-- (secret values, no API), (nil, nil, true) when they were read and the buff is simply not on you.
function Timers.Remaining(def)
  local ns = _G.C_UnitAuras
  if not (ns and ns.GetUnitAuras) then return nil, nil, false end
  local ok, list = pcall(ns.GetUnitAuras, "player", "HELPFUL")
  if not ok or type(list) ~= "table" then return nil, nil, false end
  local now = GetTime and GetTime() or 0
  for _, aura in ipairs(list) do
    if type(aura) ~= "table" then return nil, nil, false end
    local name, id, expires = aura.name, aura.spellId, aura.expirationTime
    if isSecret(name) or isSecret(id) or isSecret(expires) then return nil, nil, false end
    local match = false
    for _, n in ipairs(def.names) do if name == n then match = true end end
    for _, sid in ipairs(def.spells) do if id == sid then match = true end end
    for _, pat in ipairs(def.like or {}) do if type(name) == "string" and name:find(pat) then match = true end end
    if match then
      if type(expires) ~= "number" or expires <= 0 then return nil, nil, false end
      return math.max(0, expires - now), aura.icon, true
    end
  end
  return nil, nil, true
end

-- Does this character have the buff's spell (so the section is for them)? Without the spell API: yes.
function Timers.Applies(def)
  if not def.learned then return true end   -- a buff for everyone (food): no spell to know
  if not (_G.IsPlayerSpell or _G.IsSpellKnown) then return true end
  for _, id in ipairs(def.learned or {}) do
    local ok, known = pcall(_G.IsPlayerSpell or _G.IsSpellKnown, id)
    if ok and known then return true end
  end
  return false
end

local function text(sec, clock)
  if clock and sec >= 60 then return ("%d:%02d"):format(math.floor(sec / 60), math.floor(sec % 60)) end
  if sec >= 10 then return tostring(math.floor(sec + 0.5)) end
  return ("%.1f"):format(sec)
end

-- The "you have no food buff" nag: only when the player turned it on, the auras were readable, and you are alive.
local function missingNag(def, d, sec, readable)
  if not (def.missing and d.remindMissing and sec == nil and readable) then return false end
  return not (UnitIsDeadOrGhost and UnitIsDeadOrGhost("player"))
end

local function update(def)
  local f = frames[def.key]
  if not f then return end
  local d = settings(def)
  local sec, icon, readable = Timers.Remaining(def)
  local nag = missingNag(def, d, sec, readable)
  local show = d.shown and (nag or (sec ~= nil and not def.nagOnly) or not d.lock)
  f:SetShown(show)
  active[def.key] = sec ~= nil
  if not show then return end
  -- A nag-only entry says it in plain red text: no icon, no frame (they come back while the icon is unlocked to move it).
  local plain = def.nagOnly and nag and d.lock
  f.border:SetShown(not plain)
  f.icon:SetShown(not plain)
  f.count:ClearAllPoints()
  if plain then
    f.count:SetPoint("CENTER", f, "CENTER", 0, 0)
  else
    f.count:SetPoint("BOTTOMRIGHT", -3, 3)   -- the icon frame's own corner (Reminders.NewIcon)
  end
  if nag then
    f.border:SetColorTexture(0.9, 0.1, 0.1, 1)
  else
    f.border:SetColorTexture((sec and 0.95 or 0.4), (sec and 0.75 or 0.4), (sec and 0.1 or 0.4), 1)
  end
  f.icon:SetTexture(icon or def.icon)
  f.count:SetText(sec and text(sec, def.clock) or (nag and L.TIMER_NOFOOD) or "-")
  f.count:SetTextColor(1, nag and 0.3 or 1, nag and 0.3 or 1)
  f:EnableMouse(not d.lock)
end

local function modules()
  for _, def in ipairs(Timers.TRACK) do
    local m = { def = def, MIN_SCALE = Timers.MIN_SCALE, MAX_SCALE = Timers.MAX_SCALE }
    function m.Db() return settings(def) end
    function m.Apply()
      local f = frames[def.key]
      if not f then return end
      f:Place()
      update(def)
      R2F.Reminders.RefreshUI()
    end
    function m.SetShown(on) settings(def).shown = on and true or false; m.Apply() end
    function m.SetLock(on) settings(def).lock = on and true or false; m.Apply() end
    function m.SetScale(v) settings(def).scale = R2F.Reminders.ClampScale(v); m.Apply() end
    def.module = m
    local checks
    if def.missing then
      checks = { { label = "TIMER_REMIND_FOOD", get = function() return settings(def).remindMissing == true end,
                   set = function(on) settings(def).remindMissing = on and true or false; m.Apply() end } }
    end
    R2F.Reminders.Register({
      key = def.key, general = true, applies = function() return Timers.Applies(def) end, module = m,
      title = def.title, show = def.show, lock = def.lock, size = def.size, checks = checks,
    })
  end
end
modules()

-- PLAYER_LOGIN (Core.lua).
function Timers.Init()
  for _, def in ipairs(Timers.TRACK) do
    if not frames[def.key] then
      local name = "R2F" .. def.key:sub(1, 1):upper() .. def.key:sub(2) .. "Frame"
      local f = R2F.Reminders.NewIcon(name, def.module.Db, "REM_DRAG_TIP")
      f:Place()
      pcall(f.count.SetFontObject, f.count, "NumberFontNormalHuge")
      frames[def.key] = f
      -- While the buff is on you, count down smoothly (a small throttled loop on the icon itself).
      local elapsed = 0
      f:SetScript("OnUpdate", function(_, dt)
        elapsed = elapsed + dt
        if elapsed < THROTTLE then return end
        elapsed = 0
        if active[def.key] then update(def) end
      end)
    end
  end
  local ev = CreateFrame("Frame")
  ev:SetScript("OnEvent", function(_, event, unit)
    if event == "UNIT_AURA" and unit ~= "player" then return end
    for _, def in ipairs(Timers.TRACK) do update(def) end
  end)
  for _, e in ipairs({ "UNIT_AURA", "PLAYER_ENTERING_WORLD", "PLAYER_DEAD", "PLAYER_ALIVE" }) do
    pcall(ev.RegisterEvent, ev, e)
  end
  for _, def in ipairs(Timers.TRACK) do update(def) end
end
