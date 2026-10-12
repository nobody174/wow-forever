-- UI/TalentGuide.lua: guided mode, the fallback for a client where addons
-- can't call LearnTalent.
--
-- The player learns each point with Blizzard's own talent window; we only
-- point at the talent to click: a pulsing gold glow plus "Click Cruelty
-- (2 of 21)". Talents.lua decides WHICH point (the same verified list as the
-- direct mode) and calls Show / Hide; this file only draws.
--
-- Taint rules, the reason for the shape of this file:
-- * Nothing of Blizzard's is modified: no SetScript / HookScript / SetPoint /
--   Show / Hide / SetParent on any Blizzard frame, no new keys on them.
--   Blizzard's frames are only READ (_G lookup, IsVisible, selectedTab).
-- * The glow is our own frame, parented to UIParent and only ANCHORED to
--   Blizzard's talent button (SetPoint on OUR frame with theirs as the
--   relative frame). Talent buttons aren't protected, and anchoring an
--   insecure frame to another frame doesn't touch the other frame.
-- * It doesn't take the mouse, so the click goes to Blizzard's button.
-- * Because we may not hook Blizzard's OnHide / tab clicks, a small throttled
--   OnUpdate on our own invisible host frame (0.2 s, only while guiding)
--   re-checks whether the talent window is open and which tab it shows.
--   (Throttled refresh only while the window is open, like every other
--   refresh in the addon.)
-- * The window is never opened from here: calling Blizzard's ToggleTalentFrame()
--   would run its code (panel layout, tab state) in our name and taint it. The
--   player opens it (default key N) and the chat/note text says so; the glow
--   appears as soon as the window is showing.
--
-- Frame names differ by client generation: vanilla's Blizzard_TalentUI has
-- TalentFrame with buttons TalentFrameTalent<i> and tabs TalentFrameTab<n>;
-- TBC/Wrath-era code has PlayerTalentFrame / PlayerTalentFrameTalent<i>. In
-- both, button i is talent index i (GetTalentInfo(selectedTab, i)) of the tab
-- that's showing. Clients differ in which one they have, so
-- both are tried; with neither, the text alone still says what to click.

local _, R2F = ...
local L = R2F.L

local TalentGuide = {}
R2F.TalentGuide = TalentGuide

TalentGuide.FRAMES = { "PlayerTalentFrame", "TalentFrame" }
local THROTTLE = 0.2

local host, glow
local current       -- { point, x, n, treeName } while guiding, else nil

-- Blizzard's talent window if it's loaded: frame, its global name.
local function blizzard()
  for _, name in ipairs(TalentGuide.FRAMES) do
    local f = _G[name]
    if type(f) == "table" and f.IsVisible then return f, name end
  end
end

-- Which tab Blizzard's window shows (read only). nil = can't tell.
local function selectedTab(f)
  if PanelTemplates_GetSelectedTab then
    local ok, v = pcall(PanelTemplates_GetSelectedTab, f)
    if ok and type(v) == "number" then return v end
  end
  return type(f.selectedTab) == "number" and f.selectedTab or nil
end

-- What to glow for point p: Blizzard's talent button, or its tab button when
-- another tab is showing. Returns frame, "talent" | "tab"; nil when the
-- window is closed or the button can't be found.
function TalentGuide.Target(p)
  local f, name = blizzard()
  if not f or not f:IsVisible() then return nil end
  local sel = selectedTab(f)
  if sel and sel ~= p.tab then
    local tab = _G[name .. "Tab" .. p.tab]
    if type(tab) == "table" and tab.IsVisible and tab:IsVisible() then return tab, "tab" end
    return nil
  end
  -- P.index comes from C_Traits (our pane position), not Classic's
  -- talent index, so a glow on Button<index> is only right if Classic's
  -- GetTalentInfo names this very talent there. Otherwise no glow: the text
  -- alone is better than a gold ring on the wrong talent.
  if type(GetTalentInfo) ~= "function" then return nil end
  local ok, n = pcall(GetTalentInfo, p.tab, p.index)
  if not ok or n ~= p.name then return nil end
  local b = _G[name .. "Talent" .. p.index]
  if type(b) == "table" and b.IsVisible and b:IsVisible() then return b, "talent" end
  return nil
end

local function instruction(kind)
  local c = current
  if kind == "tab" then
    return L.TALENT_GUIDE_TAB:format(c.treeName, c.point.name, c.x, c.n)
  end
  return L.TALENT_GUIDE_CLICK:format(c.point.name, c.x, c.n)
end

local function build()
  glow = CreateFrame("Frame", nil, UIParent)
  glow:SetFrameStrata("DIALOG")
  glow:EnableMouse(false)                -- clicks go through to Blizzard's button
  glow:Hide()
  -- The action-button border glow, gold, the same texture the mini trees use
  -- for "learned now", so it reads as "this one".
  glow.tex = glow:CreateTexture(nil, "OVERLAY")
  glow.tex:SetTexture("Interface\\Buttons\\UI-ActionButton-Border")
  glow.tex:SetBlendMode("ADD")
  glow.tex:SetVertexColor(1, 0.82, 0)
  glow.tex:SetAllPoints()
  glow.label = glow:CreateFontString(nil, "OVERLAY", "GameFontNormal")
  glow.label:SetPoint("BOTTOM", glow, "TOP", 0, -6)
  -- Pulse: an AnimationGroup (no OnUpdate needed). Missing or different API:
  -- a steady glow, which still works.
  if glow.CreateAnimationGroup then
    local ok = pcall(function()
      local ag = glow:CreateAnimationGroup()
      local a = ag:CreateAnimation("Alpha")
      a:SetFromAlpha(1)
      a:SetToAlpha(0.3)
      a:SetDuration(0.6)
      ag:SetLooping("BOUNCE")
      glow.pulse = ag
    end)
    if not ok then glow.pulse = nil end
  end

  host = CreateFrame("Frame", nil, UIParent)
  host:Hide()
  host.elapsed = 0
  host:SetScript("OnUpdate", function(self, elapsed)
    self.elapsed = self.elapsed + (elapsed or 0)
    if self.elapsed < THROTTLE then return end
    self.elapsed = 0
    TalentGuide.Update()
  end)
end

-- Re-anchor (or hide) the glow for the current point. Called on Show and by
-- the host's throttled OnUpdate while guiding.
function TalentGuide.Update()
  if not current or not glow then return end
  local target, kind = TalentGuide.Target(current.point)
  if not target then
    glow:Hide()
    if glow.pulse then glow.pulse:Stop() end
    return
  end
  local size = math.max(target:GetWidth() or 0, target:GetHeight() or 0)
  if size <= 0 then size = 37 end
  glow:ClearAllPoints()
  glow:SetPoint("CENTER", target, "CENTER", 0, 0)
  glow:SetSize(size * 1.8, size * 1.8)
  glow.label:SetText(instruction(kind))
  glow.anchor, glow.kind = target, kind
  if not glow:IsShown() then
    glow:Show()
    if glow.pulse then glow.pulse:Play() end
  end
end

-- Point at `p` (a Talents.LearnPoints entry), the x-th point of n.
function TalentGuide.Show(p, x, n, treeName)
  if not glow then build() end
  current = { point = p, x = x, n = n, treeName = treeName }
  host.elapsed = 0
  host:Show()
  TalentGuide.Update()
end

function TalentGuide.Hide()
  current = nil
  if not glow then return end
  host:Hide()
  glow:Hide()
  glow.anchor, glow.kind = nil, nil
  if glow.pulse then glow.pulse:Stop() end
end

-- The text for the Talents tab's note line while guiding, or nil.
function TalentGuide.Text()
  if not current then return nil end
  local _, kind = TalentGuide.Target(current.point)
  return instruction(kind)
end

-- Is Blizzard's talent window showing? Read only: it is never opened from
-- here (see the header), so false means "ask the player to open it".
function TalentGuide.IsWindowOpen()
  local f = blizzard()
  return (f and f:IsVisible()) and true or false
end

-- Test hooks.
function TalentGuide.Glow() return glow end
function TalentGuide.Host() return host end
function TalentGuide.Current() return current end
