-- CombatBanner.lua: "Entering Combat" / "Leaving Combat" in big text for a moment.
--
-- Our own frame and text only; the game's combat events are just listened to. Off until ticked (Tweaks > Class icons >
-- Combat banner). While the position is unlocked a small marker shows so you can drag the banner where you want it;
-- locked, only the text appears, for BANNER_SECONDS, when combat starts and ends. The Size slider scales the text.
-- Settings live in R2FDB.banner: shown, lock, scale, x, y.

local _, R2F = ...
local L = R2F.L

local Banner = {}
R2F.CombatBanner = Banner

local ICON = "Interface\\Icons\\Ability_DualWield"
local BANNER_SECONDS = 2

Banner.MIN_SCALE, Banner.MAX_SCALE = R2F.Reminders.MIN_SCALE, R2F.Reminders.MAX_SCALE

local frame, token = nil, 0
local flashing = false          -- the text is showing because combat just started or ended

local function db()
  return R2F.Library.db.banner
end
Banner.Db = db

function Banner.Frame() return frame end

local function refresh()
  if not frame then return end
  local d = db()
  local marker = d.shown and not d.lock            -- unlocked: a marker to drag, even when nothing is flashing
  local show = d.shown and (flashing or not d.lock)
  frame:SetShown(show)
  if not show then return end
  frame.border:SetShown(marker)
  frame.icon:SetShown(marker)
  frame.count:SetShown(marker and not flashing)
  frame.text:SetShown(flashing)
  frame.border:SetColorTexture(0.95, 0.75, 0.1, 1)
  frame.icon:SetTexture(ICON)
  frame.count:SetText(L.BANNER_MARKER)
  frame:EnableMouse(not d.lock)
end

local function flash(entering)
  local d = db()
  if not (frame and d.shown) then return end
  frame.text:SetText(entering and L.GP_COMBAT_ENTER or L.GP_COMBAT_LEAVE)
  if entering then frame.text:SetTextColor(1, 0.2, 0.2) else frame.text:SetTextColor(0.3, 1, 0.3) end
  flashing = true
  token = token + 1
  local mine = token
  refresh()
  if C_Timer and C_Timer.After then
    C_Timer.After(BANNER_SECONDS, function()
      if token == mine then flashing = false; refresh() end
    end)
  end
end

-- PLAYER_LOGIN (Core.lua).
function Banner.Init()
  if frame then return end
  local d = db()
  if type(d.y) ~= "number" then
    -- A hand below the top edge of the screen (the position is an offset from the screen centre).
    local h = UIParent and UIParent.GetHeight and UIParent:GetHeight() or 768
    d.y = math.floor(h / 2 - 150)
  end
  frame = R2F.Reminders.NewIcon("R2FCombatBannerFrame", db, "BANNER_DRAG_TIP")
  frame:SetFrameStrata("HIGH")
  frame.text = frame:CreateFontString(nil, "OVERLAY", "GameFontNormalHuge")
  frame.text:SetPoint("CENTER", frame, "CENTER", 0, 0)
  frame:Place()
  local ev = CreateFrame("Frame")
  ev:SetScript("OnEvent", function(_, event)
    if event == "PLAYER_REGEN_DISABLED" then flash(true) else flash(false) end
  end)
  for _, e in ipairs({ "PLAYER_REGEN_DISABLED", "PLAYER_REGEN_ENABLED" }) do pcall(ev.RegisterEvent, ev, e) end
  refresh()
end

function Banner.Apply()
  if not frame then return end
  frame:Place()
  refresh()
  R2F.Reminders.RefreshUI()
end

function Banner.SetShown(on)
  db().shown = on and true or false
  if not db().shown then flashing = false end
  Banner.Apply()
end

function Banner.SetLock(on)
  db().lock = on and true or false
  Banner.Apply()
end

function Banner.SetScale(v)
  db().scale = R2F.Reminders.ClampScale(v)
  Banner.Apply()
end

R2F.Reminders.Register({
  key = "combatbanner", general = true, module = Banner,
  title = "REM_BANNER_TITLE", show = "BANNER_SHOW", lock = "BANNER_LOCK", size = "BANNER_SIZE",
})
