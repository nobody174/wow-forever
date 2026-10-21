-- ActionBars.lua: red overlays and cooldown numbers on the action buttons (Tweaks > Action bars).
--
-- Three things the game's own bars do only partly, each one box on the Tweaks page (all OFF until ticked):
--   * Red when out of range: a red veil over the icon while the spell cannot reach your target (IsActionInRange).
--   * Red when you lack mana, rage or energy (the second answer of IsUsableAction).
--   * Cooldown numbers: the seconds left in big numbers on the button (GetActionCooldown), 2h / 5m / 12 / 3.4, turning
--     yellow under 5 s and red under 2 s. The global cooldown (2.5 s or less) gets no number.
-- Done the way other addons do it (tullaRange, OmniCC, RedRange): the game's buttons are only READ (their action slot);
-- everything drawn is our own child frame on top of each button, kept in our own table, so nothing of the game's is written to
-- and nothing can taint. Our frames are made out of combat. A shared 0.1 s timer refreshes them while a box is on.
-- /r2f debug bars prints what this client gives.

local _, R2F = ...
local L = R2F.L
local Gameplay = R2F.Gameplay

local Bars = {}
R2F.ActionBars = Bars

local BUTTONS = { "ActionButton", "MultiBarBottomLeftButton", "MultiBarBottomRightButton", "MultiBarRightButton",
                  "MultiBarLeftButton", "MultiBar5Button", "MultiBar6Button", "MultiBar7Button" }
local PERIOD = 0.1
local GCD = 2.5                       -- a cooldown this short is the global cooldown or too short for a number
local RED = { 0.9, 0.05, 0.05, 0.55 }

local overlays = {}                   -- button -> { frame, tint, text, last }
local buttons = {}                    -- every action button this client has
local driver                          -- the timer frame
local elapsed = 0

local function isSecret(v)
  return type(_G.issecretvalue) == "function" and _G.issecretvalue(v) == true
end

local function on(key)
  return Gameplay.IsOn(key)
end

local function anyOn()
  return on("barrange") or on("barresource") or on("barcd")
end

local function collect()
  buttons = {}
  for _, prefix in ipairs(BUTTONS) do
    for i = 1, 12 do
      local b = _G[prefix .. i]
      if type(b) == "table" and b.IsVisible then buttons[#buttons + 1] = b end
    end
  end
  return buttons
end

local function fontFile()
  return _G.STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"
end

local function textSize(button)
  local w = (button.GetWidth and button:GetWidth()) or 36
  if type(w) ~= "number" or w <= 0 then w = 36 end
  return math.max(10, math.floor(w * (on("barcdbig") and 0.62 or 0.42) + 0.5))
end

-- Our child frame for one button (out of combat only: nothing is made while the game locks its frames).
local function ensure(button)
  local o = overlays[button]
  if o then return o end
  if _G.InCombatLockdown and _G.InCombatLockdown() then return nil end
  local f = _G.CreateFrame("Frame", nil, button)
  f:SetAllPoints(button)
  f:SetFrameLevel((button.GetFrameLevel and button:GetFrameLevel() or 1) + 6)
  local tint = f:CreateTexture(nil, "OVERLAY", nil, 1)
  local icon = button.icon or _G[(button.GetName and button:GetName() or "") .. "Icon"]
  if type(icon) == "table" and icon.SetTexture then
    tint:SetAllPoints(icon)
  else
    tint:SetPoint("TOPLEFT", button, "TOPLEFT", 2, -2)
    tint:SetPoint("BOTTOMRIGHT", button, "BOTTOMRIGHT", -2, 2)
  end
  tint:SetColorTexture(RED[1], RED[2], RED[3], RED[4])
  tint:Hide()
  local fs = f:CreateFontString(nil, "OVERLAY")
  fs:SetPoint("CENTER", f, "CENTER", 0, 0)
  pcall(fs.SetFont, fs, fontFile(), 14, "OUTLINE")
  fs:Hide()
  o = { frame = f, tint = tint, text = fs, size = 0 }
  overlays[button] = o
  return o
end

-- The cooldown of an action slot: start, duration, enabled. Both API shapes (a table or three values) are read.
local function cooldown(slot)
  local c = _G.C_ActionBar
  if c and c.GetActionCooldown then
    local ok, info = pcall(c.GetActionCooldown, slot)
    if ok and type(info) == "table" then return info.startTime, info.duration, info.isEnabled end
  end
  if _G.GetActionCooldown then
    local ok, s, d, e = pcall(_G.GetActionCooldown, slot)
    if ok then return s, d, e end
  end
  return nil
end

function Bars.Format(seconds)
  if seconds >= 3600 then return ("%dh"):format(math.ceil(seconds / 3600)) end
  if seconds >= 60 then return ("%dm"):format(math.ceil(seconds / 60)) end
  if seconds >= 10 then return ("%d"):format(math.ceil(seconds)) end
  return ("%.1f"):format(seconds)
end

local function colour(seconds)
  if seconds <= 2 then return 1, 0.2, 0.2 end
  if seconds <= 5 then return 1, 0.82, 0.1 end
  return 1, 1, 1
end

local function hide(o)
  if o.tint:IsShown() then o.tint:Hide() end
  if o.text:IsShown() then o.text:Hide() end
end

local function update(button, o, now)
  local slot = button.action             -- read only: the game keeps it in step with the bar's page
  if type(slot) ~= "number" or not (_G.HasAction and _G.HasAction(slot)) or not button:IsVisible() then return hide(o) end
  -- the red veil
  local red = false
  if on("barrange") and _G.IsActionInRange then
    local r = _G.IsActionInRange(slot)
    if r == false or r == 0 then red = true end
  end
  if not red and on("barresource") and _G.IsUsableAction then
    local _, noResource = _G.IsUsableAction(slot)
    if noResource == true then red = true end
  end
  o.tint:SetShown(red)
  -- the number
  local shown = false
  if on("barcd") then
    local start, duration, enabled = cooldown(slot)
    if type(start) == "number" and type(duration) == "number" and not isSecret(start) and not isSecret(duration)
        and enabled ~= false and enabled ~= 0 and duration > GCD and start > 0 then
      local left = start + duration - now
      if left > 0 then
        local size = textSize(button)
        if size ~= o.size then
          o.size = size
          pcall(o.text.SetFont, o.text, fontFile(), size, "OUTLINE")
        end
        o.text:SetText(Bars.Format(left))
        o.text:SetTextColor(colour(left))
        if not o.text:IsShown() then o.text:Show() end
        shown = true
      end
    end
  end
  if not shown and o.text:IsShown() then o.text:Hide() end
end

-- The overlay of one button (for the tests and /r2f debug).
function Bars.Overlay(button) return overlays[button] end

-- One pass over every button (the timer and the action-bar events call it).
function Bars.Refresh()
  if not anyOn() then
    for _, o in pairs(overlays) do hide(o) end
    return
  end
  if #buttons == 0 then collect() end
  local now = _G.GetTime and _G.GetTime() or 0
  for _, b in ipairs(buttons) do
    local o = overlays[b] or ensure(b)
    if o then
      local ok = pcall(update, b, o, now)
      if not ok then hide(o) end
    end
  end
end

local function onUpdate(_, dt)
  elapsed = elapsed + dt
  if elapsed < PERIOD then return end
  elapsed = 0
  Bars.Refresh()
end

-- Starts or stops the timer: it runs only while a box is ticked.
function Bars.Apply()
  if not driver then
    driver = _G.CreateFrame("Frame")
    for _, e in ipairs({ "PLAYER_ENTERING_WORLD", "PLAYER_REGEN_ENABLED", "ACTIONBAR_SLOT_CHANGED", "UPDATE_BONUS_ACTIONBAR" }) do
      pcall(driver.RegisterEvent, driver, e)
    end
    driver:SetScript("OnEvent", function(_, event)
      if event == "PLAYER_ENTERING_WORLD" or event == "PLAYER_REGEN_ENABLED" then collect() end
      if anyOn() then pcall(Bars.Refresh) end
    end)
  end
  if anyOn() then
    collect()
    driver:SetScript("OnUpdate", onUpdate)
    Bars.Refresh()
  else
    driver:SetScript("OnUpdate", nil)
    Bars.Refresh()                         -- hides what is showing
  end
end

-- /r2f debug bars
function Bars.Debug()
  collect()
  local c = _G.C_ActionBar
  R2F.Print(L.BARS_DEBUG_APIS:format(tostring(_G.IsActionInRange ~= nil), tostring(_G.IsUsableAction ~= nil),
    tostring((c and c.GetActionCooldown) ~= nil or _G.GetActionCooldown ~= nil)))
  local per = {}
  for _, prefix in ipairs(BUTTONS) do
    local n = 0
    for i = 1, 12 do if _G[prefix .. i] then n = n + 1 end end
    if n > 0 then per[#per + 1] = prefix .. " x" .. n end
  end
  R2F.Print(L.BARS_DEBUG_BUTTONS:format(#buttons, table.concat(per, ", ")))
  local b = _G.ActionButton1
  if b then
    local slot = b.action
    local range = type(slot) == "number" and _G.IsActionInRange and _G.IsActionInRange(slot)
    local usable, noRes
    if type(slot) == "number" and _G.IsUsableAction then usable, noRes = _G.IsUsableAction(slot) end
    local s, d = cooldown(type(slot) == "number" and slot or 0)
    R2F.Print(L.BARS_DEBUG_SAMPLE:format(tostring(slot), tostring(range), tostring(usable), tostring(noRes), tostring(s),
      tostring(d)))
  end
end

-- ---------------------------------------------------------------------------
-- The four boxes
-- ---------------------------------------------------------------------------

local function available()
  return _G.IsActionInRange ~= nil and _G.HasAction ~= nil
end

Gameplay.Register({ key = "barrange", group = "bars", title = "GP_BARRANGE", tip = "GP_BARRANGE_TIP", available = available,
                    onToggle = Bars.Apply })
Gameplay.Register({ key = "barresource", group = "bars", title = "GP_BARRESOURCE", tip = "GP_BARRESOURCE_TIP",
                    available = function() return available() and _G.IsUsableAction ~= nil end, onToggle = Bars.Apply })
Gameplay.Register({ key = "barcd", group = "bars", title = "GP_BARCD", tip = "GP_BARCD_TIP", available = available,
                    onToggle = Bars.Apply })
Gameplay.Register({ key = "barcdbig", group = "bars", title = "GP_BARCDBIG", tip = "GP_BARCDBIG_TIP", available = available,
                    onToggle = function() for _, o in pairs(overlays) do o.size = 0 end Bars.Apply() end })
