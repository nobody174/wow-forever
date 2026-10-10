-- Tracking.lua: "turn your minimap tracking on" reminder (ADDON_PLAN.md 17.1 step 5, v0.26.0).
--
-- Find Minerals, Find Herbs and Find Treasure are minimap tracking spells: only one tracking is
-- active at a time (the game switches between them), and it does not stay on by itself after a
-- reload or after you use another tracking. This reminder shows the framed icon (the same look
-- as the stance and ammo icons, Reminders.lua) while you KNOW at least one of the tracking types
-- you ticked and NONE of them is active, and is gone otherwise. (Unlike the stance and ammo
-- icons it is not shown just for placing: switch your tracking off to see it and drag it.)
-- Any class: it only exists for a character that has a tracking spell.
--
-- Read-only and no aura reading (the game's tracking list, C_Minimap.GetNumTrackingTypes /
-- GetTrackingInfo; documented in the game's API files: name, texture, active, spellID), so it
-- works in combat. Settings in R2FDB.tracking: shown, lock, scale, x, y, minerals, herbs, treasure.
-- Names are matched in English (the game's spell names); other languages get no section.

local _, R2F = ...
local L = R2F.L

local Tracking = {}
R2F.Tracking = Tracking

local FALLBACK_ICON = "Interface\\Icons\\INV_Misc_Spyglass_02"
local ATTENTION = { r = 0.95, g = 0.75, b = 0.1 }
local FINE = { r = 0.4, g = 0.4, b = 0.4 }

-- kind -> the tracking spell's name
local KINDS = { minerals = "Find Minerals", herbs = "Find Herbs", treasure = "Find Treasure" }
Tracking.KINDS = KINDS
local ORDER = { "minerals", "herbs", "treasure" }

Tracking.MIN_SCALE, Tracking.MAX_SCALE = R2F.Reminders.MIN_SCALE, R2F.Reminders.MAX_SCALE

local frame

local function db()
  return R2F.Library.db.tracking
end
Tracking.Db = db

-- The tracking types the game lists: { [kind] = { active = bool, texture = fileID } } for the
-- three we know by name.
function Tracking.Known()
  local out = {}
  local ns = _G.C_Minimap
  if not (ns and ns.GetNumTrackingTypes and ns.GetTrackingInfo) then return out end
  local ok = pcall(function()
    for i = 1, ns.GetNumTrackingTypes() or 0 do
      local info = ns.GetTrackingInfo(i)
      if type(info) == "table" and info.name then
        for kind, name in pairs(KINDS) do
          if info.name == name then out[kind] = { active = info.active == true, texture = info.texture } end
        end
      end
    end
  end)
  return ok and out or {}
end

-- Does this character have any of the three? (The Gameplay tab shows the section only then.)
function Tracking.Applies()
  return next(Tracking.Known()) ~= nil
end

-- State for the icon: needs = true when a ticked, known tracking type exists and none of those is
-- active; texture = the first ticked known one's icon; has = at least one ticked known type.
function Tracking.State()
  local known, d = Tracking.Known(), db()
  local has, anyActive, texture = false, false, nil
  for _, kind in ipairs(ORDER) do
    local k = known[kind]
    if k and d[kind] then
      has = true
      texture = texture or k.texture
      if k.active then anyActive = true end
    end
  end
  return has and not anyActive, has, texture
end

function Tracking.Update()
  if not frame then return end
  local d = db()
  local needs, has, texture = Tracking.State()
  -- Only while a tracking is needed (owner test of 0.26.0: unlocked it stayed up, grey, while
  -- tracking was on). To place it, switch your tracking off: it appears and can be dragged.
  local show = Tracking.Applies() and d.shown and needs
  frame:SetShown(show)
  if not show then return end
  local c = needs and ATTENTION or FINE
  frame.border:SetColorTexture(c.r, c.g, c.b, 1)
  frame.icon:SetTexture(texture or FALLBACK_ICON)
  frame.icon:SetDesaturated(false)
  frame.count:SetText("")
  frame:EnableMouse(not d.lock)
end

-- PLAYER_LOGIN (Core.lua).
function Tracking.Init()
  if frame then return end
  frame = R2F.Reminders.NewIcon("R2FTrackingFrame", db, "REM_DRAG_TIP")
  frame:Place()
  local ev = CreateFrame("Frame")
  ev:SetScript("OnEvent", Tracking.Update)
  for _, e in ipairs({ "MINIMAP_UPDATE_TRACKING", "PLAYER_ENTERING_WORLD", "SPELLS_CHANGED" }) do
    pcall(ev.RegisterEvent, ev, e)
  end
  Tracking.Update()
end

function Tracking.Apply()
  if not frame then return end
  frame:Place()
  Tracking.Update()
  R2F.Reminders.RefreshUI()
end

function Tracking.SetShown(on)
  db().shown = on and true or false
  Tracking.Apply()
end

function Tracking.SetLock(on)
  db().lock = on and true or false
  Tracking.Apply()
end

function Tracking.SetScale(v)
  db().scale = R2F.Reminders.ClampScale(v)
  Tracking.Apply()
end

function Tracking.SetKind(kind, on)
  if KINDS[kind] then db()[kind] = on and true or false end
  Tracking.Apply()
end

R2F.Reminders.Register({
  key = "tracking", class = nil, applies = Tracking.Applies, module = Tracking,
  title = "REM_TRACKING_TITLE", show = "TRACKING_SHOW", lock = "TRACKING_LOCK", size = "TRACKING_SIZE",
  checks = {
    { label = "TRACKING_MINERALS", get = function() return db().minerals end, set = function(v) Tracking.SetKind("minerals", v) end },
    { label = "TRACKING_HERBS", get = function() return db().herbs end, set = function(v) Tracking.SetKind("herbs", v) end },
    { label = "TRACKING_TREASURE", get = function() return db().treasure end, set = function(v) Tracking.SetKind("treasure", v) end },
  },
})
