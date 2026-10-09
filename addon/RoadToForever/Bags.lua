-- Bags.lua: movable bags (ADDON_PLAN.md 15.3, v0.16.0; rebuilt in v0.20.0). Replaces
-- the Forever Bag Mover addon.
--
-- Two Quick settings on the Settings tab: Movable bags (take over the bag windows'
-- position) and Lock bags (keep the position, stop dragging). Stored per character in
-- R2FCharDB.bags:
--   movable, lock   booleans
--   combined        saved point of the combined bag, or nil
--   bags[bagId]     saved point of one classic bag window (backpack = 0), or nil
-- A saved point = { point, relPoint, x, y }, always relative to UIParent.
--
-- HOLD SHIFT AND DRAG (v0.20.0). A drag that starts on a bag window's title never reached
-- 0.16.0's drag script: Blizzard lays an invisible button over the whole title bar that
-- opens the bag menu when the mouse goes down, so it swallowed the drag (found in game
-- 2026-10-09, and the same finding is in ForeverPlus' BagWindow module). So, like that
-- module: while Shift is held (and Movable is on, Lock off, out of combat) a grip of our
-- own covers the title bar, and Shift+drag on the title or the empty background moves
-- the window. Without Shift the title is the game's again (a click opens its menu).
-- Item buttons keep their own drag (picking an item up).
--
-- NEVER CALL THE GAME'S BAG PLACEMENT. 0.16.0 called UpdateContainerFrameAnchors() when
-- Movable was switched off. That runs the game's placement code in this addon's name and
-- taints the bag code until the game refuses a protected action ("blocked from an
-- action", UseContainerItem; ForeverPlus hit exactly that on 2026-10-04). Now the spot
-- the game last gave each window is read off the frame (noteGameAnchor, in a secure hook
-- that runs after the game placed it) and switching Movable off puts the window back
-- there itself.
--
-- Which bag windows exist is decided at run time:
--   * the combined bag  _G.ContainerFrameCombinedBags
--   * the classic bag windows  _G.ContainerFrame1 .. ContainerFrameN (also present on the
--     modern client, used when the combined bag is switched off)
-- Both are handled when present. Classic windows are keyed by bag id (frame:GetID(),
-- backpack 0), not by position in the stack.
--
-- The game re-anchors bags every time one opens or closes (UpdateContainerFrameAnchors)
-- and when a window is shown; we re-apply the saved point right after it (hooksecurefunc
-- + HookScript OnShow), so our position wins without replacing any game function.
--
-- Combat: bag windows hold protected item buttons, so nothing is moved, hooked or
-- dragged while InCombatLockdown(); what was skipped runs on PLAYER_REGEN_ENABLED.
-- ForeverPlus has a bag window module that does the same job: use one of the two (both
-- on means two addons placing the same window).

local _, R2F = ...
local L = R2F.L

local Bags = {}
R2F.Bags = Bags

local SIDE_GAP = 11           -- the gap the game leaves between two bag windows

local hooked = {}             -- frame -> true once our scripts are on it
local grips = {}              -- frame -> grip frame over its title
local gameAnchor = {}         -- frame -> { game's first point } as it last placed the window
local anchorsHooked = false
local pending = false         -- something was skipped in combat
local watcher, events

local function db()
  return R2F.Library.cdb.bags
end

local function shift()
  return IsShiftKeyDown and IsShiftKeyDown() and true or false
end

-- Every bag window the client has right now: { {frame =, combined =, bagId =}, ... }.
local function windows()
  local out = {}
  local combined = _G.ContainerFrameCombinedBags
  if combined then out[#out + 1] = { frame = combined, combined = true } end
  local n = _G.NUM_CONTAINER_FRAMES or 13
  for i = 1, n do
    local f = _G["ContainerFrame" .. i]
    if f then out[#out + 1] = { frame = f, bagId = f:GetID() } end
  end
  return out
end

-- Do we have any bag window to move? (The Settings boxes grey out if not.)
function Bags.Available()
  return #windows() > 0
end

-- "combined", "classic", "both" or nil: what a /r2f bags report calls it.
function Bags.Style()
  local c = _G.ContainerFrameCombinedBags ~= nil
  local k = _G.ContainerFrame1 ~= nil
  if c and k then return "both" end
  if c then return "combined" end
  if k then return "classic" end
  return nil
end

function Bags.ForeverPlusActive()
  local isLoaded = (C_AddOns and C_AddOns.IsAddOnLoaded) or _G.IsAddOnLoaded
  return isLoaded ~= nil and isLoaded("ForeverPlus") and true or false
end

local function savedFor(w)
  local d = db()
  if w.combined then return d.combined end
  return d.bags[w.bagId]
end

local function applyOne(w)
  local p = savedFor(w)
  if not p then return end
  local f = w.frame
  f:ClearAllPoints()
  f:SetPoint(p[1], UIParent, p[2], p[3], p[4])
end

-- Compared in screen units, because a bag window carries a scale of its own.
local function offRight(f)
  local right, screen = f:GetRight(), UIParent:GetRight()
  if not (right and screen) then return false end
  return right * f:GetEffectiveScale() > screen * UIParent:GetEffectiveScale() + 1
end

-- Once a window has moved, the game's other bag windows (anchored to it) may no longer
-- fit on the screen: hang those that don't off the other side. Only windows anchored to
-- `frame` and only when they are off the screen.
local function keepOthersOnScreen(frame)
  for _, w in ipairs(windows()) do
    local other = w.frame
    if other ~= frame and other:IsShown() and other.GetPoint then
      local _, relativeTo = other:GetPoint(1)
      if relativeTo == frame then
        local left = other:GetLeft()
        if left and left < 0 then
          other:ClearAllPoints()
          other:SetPoint("BOTTOMLEFT", frame, "BOTTOMRIGHT", SIDE_GAP, 0)
        elseif offRight(other) then
          other:ClearAllPoints()
          other:SetPoint("BOTTOMRIGHT", frame, "BOTTOMLEFT", -SIDE_GAP, 0)
        end
      end
    end
  end
end

-- Put every shown bag window on its saved point. Safe to call anytime: it does nothing
-- unless Movable bags is on, and waits out combat.
function Bags.Apply()
  if not db().movable then return end
  if InCombatLockdown() then pending = true; return end
  for _, w in ipairs(windows()) do
    if w.frame:IsShown() then
      applyOne(w)
      keepOthersOnScreen(w.frame)
    end
  end
end

-- Where the game just put each shown window (read off the frame; called right after the
-- game placed them, before ours is applied).
local function noteGameAnchors()
  for _, w in ipairs(windows()) do
    local f = w.frame
    if f:IsShown() and f.GetNumPoints and f:GetNumPoints() > 0 then
      gameAnchor[f] = { f:GetPoint(1) }
    end
  end
end

-- Hand the windows back to the spot the game last gave them, without asking the game
-- to place anything (see the head of this file).
local function giveBack()
  for _, w in ipairs(windows()) do
    local f, a = w.frame, gameAnchor[w.frame]
    if a and f:IsShown() then
      f:ClearAllPoints()
      f:SetPoint(unpack(a))
    end
  end
end

-- Remember where `w` is now (after a drag).
local function savePoint(w)
  local f = w.frame
  local point, rel, relPoint, x, y = f:GetPoint()
  if rel ~= nil and rel ~= UIParent then
    -- Anchored to some other frame: use the absolute spot instead.
    point, relPoint, x, y = "BOTTOMLEFT", "BOTTOMLEFT", f:GetLeft(), f:GetBottom()
  end
  if not (point and x and y) then return end
  local p = { point, relPoint or point, x, y }
  local d = db()
  if w.combined then d.combined = p else d.bags[w.bagId] = p end
end

local function windowOf(frame)
  for _, w in ipairs(windows()) do
    if w.frame == frame then return w end
  end
end

local function canDrag()
  local d = db()
  return d.movable and not d.lock and not InCombatLockdown()
end

-- The grips take the mouse while Shift is held (or a drag runs) and give it back after.
function Bags.SyncGrips()
  local want = canDrag() and (shift() or watcher ~= nil and watcher.active) and true or false
  if InCombatLockdown() then want = false end
  for _, g in pairs(grips) do g:EnableMouse(want) end
end

local function stopDrag(frame)
  if not frame.r2fDragging then return end
  frame.r2fDragging = nil
  if watcher then watcher.active = nil; watcher:SetScript("OnUpdate", nil) end
  frame:StopMovingOrSizing()
  -- Moving a named frame by hand makes the client remember it in its own layout cache;
  -- we remember it ourselves.
  if frame.SetUserPlaced then pcall(frame.SetUserPlaced, frame, false) end
  local w = windowOf(frame)
  if w then
    savePoint(w)
    keepOthersOnScreen(frame)
  end
  Bags.SyncGrips()
end

-- A safety net under OnDragStop: the window must not hang on the cursor if the end of
-- the drag never reaches us (Shift let go mid-drag). Asks the mouse button every frame
-- while a drag runs, never otherwise.
local function watchRelease(frame)
  if type(IsMouseButtonDown) ~= "function" then return end
  watcher = watcher or CreateFrame("Frame")
  watcher.active = true
  watcher:SetScript("OnUpdate", function()
    local ok, down = pcall(IsMouseButtonDown, "LeftButton")
    if ok and not down then stopDrag(frame) end
  end)
end

local function startDrag(frame)
  if not (canDrag() and shift()) then return end
  frame.r2fDragging = true
  frame:StartMoving()
  watchRelease(frame)
  Bags.SyncGrips()
end

local function hookFrame(w)
  local f = w.frame
  if hooked[f] then return end
  hooked[f] = true
  f:SetMovable(true)
  f:SetClampedToScreen(true)
  f:RegisterForDrag("LeftButton")
  f:HookScript("OnShow", function(self)
    local cur = windowOf(self)
    if cur and db().movable then
      if InCombatLockdown() then pending = true else applyOne(cur) end
    end
    Bags.SyncGrips()
  end)
  f:HookScript("OnDragStart", startDrag)
  f:HookScript("OnDragStop", stopDrag)

  -- The grip over the title bar: our own frame, above Blizzard's title button.
  local grip = CreateFrame("Frame", nil, f)
  local title = f.TitleContainer
  if type(title) == "table" and title.GetObjectType then
    grip:SetPoint("TOPLEFT", title, "TOPLEFT")
    grip:SetPoint("BOTTOMRIGHT", title, "BOTTOMRIGHT")
  else
    grip:SetPoint("TOPLEFT", f, "TOPLEFT")
    grip:SetPoint("TOPRIGHT", f, "TOPRIGHT")
    grip:SetHeight(24)
  end
  grip:SetFrameLevel((f.GetFrameLevel and f:GetFrameLevel() or 0) + 20)
  grip:EnableMouse(false)
  grip:RegisterForDrag("LeftButton")
  grip:SetScript("OnDragStart", function() startDrag(f) end)
  grip:SetScript("OnDragStop", function() stopDrag(f) end)
  grips[f] = grip
end

-- Install our scripts on every window (and the anchor hook) once; windows the client
-- creates later are picked up the next time this runs.
function Bags.Hook()
  if InCombatLockdown() then pending = true; return end
  for _, w in ipairs(windows()) do hookFrame(w) end
  if not events then
    events = CreateFrame("Frame")
    events:SetScript("OnEvent", function() Bags.SyncGrips() end)
    pcall(events.RegisterEvent, events, "MODIFIER_STATE_CHANGED")
  end
  if not anchorsHooked and _G.UpdateContainerFrameAnchors and hooksecurefunc then
    anchorsHooked = true
    -- After the game placed the windows: note where, then put ours on top.
    hooksecurefunc("UpdateContainerFrameAnchors", function()
      noteGameAnchors()
      Bags.Apply()
    end)
  end
end

-- PLAYER_LOGIN (Core.lua).
function Bags.Init()
  if db().movable then
    Bags.Hook()
    Bags.Apply()
  end
end

-- PLAYER_REGEN_ENABLED: do what combat postponed.
function Bags.OnRegen()
  if not pending then return end
  pending = false
  if db().movable then
    Bags.Hook()
    Bags.Apply()
  end
  Bags.SyncGrips()
end

function Bags.IsMovable() return db().movable == true end
function Bags.IsLocked() return db().lock == true end

-- Settings: Movable bags. Turning it off puts the windows back where the game last
-- placed them (read off the frames; the game's placement code is never called); saved
-- spots are kept for the next time it is switched on.
function Bags.SetMovable(on)
  if InCombatLockdown() then R2F.Error(L.QS_COMBAT); return false end
  db().movable = on and true or false
  if db().movable then
    Bags.Hook()
    Bags.Apply()
  else
    giveBack()
  end
  Bags.SyncGrips()
  if R2F.Settings and R2F.Settings.Refresh then R2F.Settings.Refresh() end
  return true
end

function Bags.SetLock(on)
  db().lock = on and true or false
  Bags.SyncGrips()
  if R2F.Settings and R2F.Settings.Refresh then R2F.Settings.Refresh() end
end

-- /r2f bags: what this client has, so a wrong guess shows up in chat.
function Bags.Report()
  local style = Bags.Style()
  R2F.Print(style and L.BAGS_STYLE:format(style) or L.BAGS_NONE)
  local d = db()
  R2F.Print(L.BAGS_STATE:format(d.movable and "on" or "off", d.lock and "on" or "off"))
  if Bags.ForeverPlusActive() then R2F.Print(L.BAGS_FOREVERPLUS) end
end
