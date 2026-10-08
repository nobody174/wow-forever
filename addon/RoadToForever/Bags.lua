-- Bags.lua: movable bags (ADDON_PLAN.md 15.3, v0.16.0). Replaces the
-- Forever Bag Mover addon.
--
-- Two Quick settings on the Settings tab: Movable bags (take over the bag
-- windows' position) and Lock bags (keep the position, stop dragging).
-- Stored per character in R2FCharDB.bags:
--   movable, lock   booleans
--   combined        saved point of the combined bag, or nil
--   bags[bagId]     saved point of one classic bag window (backpack = 0), or nil
-- A saved point = { point, relPoint, x, y }, always relative to UIParent.
--
-- Which bag windows exist is decided at run time, because WoW Forever's
-- client generation is not known (ADDON_PLAN 15.3, TESTING.md 24):
--   * the combined bag  _G.ContainerFrameCombinedBags (modern client)
--   * the classic bag windows  _G.ContainerFrame1 .. ContainerFrameN (also present
--     on modern clients, used when the combined bag is switched off)
-- Both are handled when present. Classic windows are keyed by bag id
-- (frame:GetID(), backpack 0), not by position in the stack, so the backpack
-- keeps its spot whichever window the game opens it in.
--
-- The game re-anchors bags every time one opens or closes
-- (UpdateContainerFrameAnchors) and when a window is shown. We re-apply the saved
-- point right after it (hooksecurefunc on that function, HookScript OnShow on
-- every window), so our position wins without replacing any game function.
--
-- Combat: bag windows hold protected item buttons, so moving or anchoring them
-- in combat is blocked. Nothing is moved, hooked or dragged while
-- InCombatLockdown(); whatever was skipped runs on PLAYER_REGEN_ENABLED.
-- Dragging works on the window's title / background (an item button starts a
-- normal item pickup instead).

local _, R2F = ...
local L = R2F.L

local Bags = {}
R2F.Bags = Bags

local hooked = {}        -- frame -> true once our scripts are on it
local anchorsHooked = false
local pending = false    -- something was skipped in combat

local function db()
  return R2F.Library.cdb.bags
end

-- Every bag window the client has right now: { {frame =, key =, combined =}, ... }.
-- `key` = the saved-point slot ("combined" or the bag id).
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

-- Put every shown bag window on its saved point. Safe to call anytime: it
-- does nothing unless Movable bags is on, and waits out combat.
function Bags.Apply()
  if not db().movable then return end
  if InCombatLockdown() then pending = true; return end
  for _, w in ipairs(windows()) do
    if w.frame:IsShown() then applyOne(w) end
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
  end)
  f:HookScript("OnDragStart", function(self)
    local d = db()
    if not d.movable or d.lock or InCombatLockdown() then return end
    self.r2fDragging = true
    self:StartMoving()
  end)
  f:HookScript("OnDragStop", function(self)
    if not self.r2fDragging then return end
    self.r2fDragging = nil
    self:StopMovingOrSizing()
    local cur = windowOf(self)
    if cur then savePoint(cur) end
  end)
end

-- Install our scripts on every window (and the anchor hook) once; windows the
-- client creates later are picked up the next time this runs.
function Bags.Hook()
  if InCombatLockdown() then pending = true; return end
  for _, w in ipairs(windows()) do hookFrame(w) end
  if not anchorsHooked and _G.UpdateContainerFrameAnchors and hooksecurefunc then
    anchorsHooked = true
    hooksecurefunc("UpdateContainerFrameAnchors", function() Bags.Apply() end)
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
end

function Bags.IsMovable() return db().movable == true end
function Bags.IsLocked() return db().lock == true end

-- Settings: Movable bags. Turning it off hands the windows back to the game,
-- which re-stacks them with its own anchor function; saved points are kept for
-- the next time it is switched on.
function Bags.SetMovable(on)
  if InCombatLockdown() then R2F.Error(L.QS_COMBAT); return false end
  db().movable = on and true or false
  if db().movable then
    Bags.Hook()
    Bags.Apply()
  elseif _G.UpdateContainerFrameAnchors then
    _G.UpdateContainerFrameAnchors()
  end
  if R2F.Settings and R2F.Settings.Refresh then R2F.Settings.Refresh() end
  return true
end

function Bags.SetLock(on)
  db().lock = on and true or false
  if R2F.Settings and R2F.Settings.Refresh then R2F.Settings.Refresh() end
end

-- /r2f bags: what this client has, so a wrong guess shows up in chat.
function Bags.Report()
  local style = Bags.Style()
  R2F.Print(style and L.BAGS_STYLE:format(style) or L.BAGS_NONE)
  local d = db()
  R2F.Print(L.BAGS_STATE:format(d.movable and "on" or "off", d.lock and "on" or "off"))
end
