-- WishTracker.lua: a small movable list of the items on your Mr.BiZ wishlist you do not own yet, with where each comes from.
-- Click a row to point the BiZNav arrow at its source (when the place is known); drag the title to move it.
-- Off until ticked (Tweaks, Bags: "Wishlist tracker"). Our own frame only: nothing is written into the game's frames or
-- tables. The position is kept in R2F.Library.db.wishTracker = { x, y } (offsets from the screen centre).

local _, R2F = ...
local L = R2F.L

local WT = {}
R2F.WishTracker = WT

WT.MAX_ROWS = 6
local W, ROW = 210, 16

local frame

function WT.On() return R2F.Gameplay.IsOn("wishtracker") end

-- The rows to show: wished items you do not own, a group at a time (biggest group first, as in the wishlist),
-- each with its source label and whether the BiZNav arrow can point at it. Returns rows and how many more there are.
function WT.Rows()
  local rows, extra = {}, 0
  for _, g in ipairs(R2F.BiZ.WishGroups()) do
    for _, it in ipairs(g.items) do
      if not it.owned then
        if #rows < WT.MAX_ROWS then
          local key = R2F.BiZ.PlaceOfItem(it.id)
          rows[#rows + 1] = { id = it.id, name = it.name, group = g.name, place = key,
                              go = key and R2F.BiZ.Place(key) and true or false }
        else
          extra = extra + 1
        end
      end
    end
  end
  return rows, extra
end

local function pos()
  local db = R2F.Library.db
  db.wishTracker = db.wishTracker or {}
  return db.wishTracker
end

local function place()
  local p = pos()
  frame:ClearAllPoints()
  frame:SetPoint("CENTER", UIParent, "CENTER", p.x or 380, p.y or 120)
end

local function build()
  frame = CreateFrame("Frame", "R2FWishTrackerFrame", UIParent)
  frame:SetSize(W, 40)
  frame:SetFrameStrata("MEDIUM")
  frame:SetClampedToScreen(true)
  frame:SetMovable(true)
  frame.bg = frame:CreateTexture(nil, "BACKGROUND")
  frame.bg:SetAllPoints()
  frame.bg:SetColorTexture(0, 0, 0, 0.55)
  frame.title = frame:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  frame.title:SetPoint("TOPLEFT", 6, -4)
  frame:EnableMouse(true)
  frame:RegisterForDrag("LeftButton")
  frame:SetScript("OnDragStart", function(self) self:StartMoving() end)
  frame:SetScript("OnDragStop", function(self)
    self:StopMovingOrSizing()
    local cx, cy = UIParent:GetCenter()
    local fx, fy = self:GetCenter()
    if cx and fx then
      local p = pos()
      p.x, p.y = math.floor(fx - cx + 0.5), math.floor(fy - cy + 0.5)
    end
  end)
  frame.rows = {}
  for i = 1, WT.MAX_ROWS do
    local b = CreateFrame("Button", nil, frame)
    b:SetSize(W - 8, ROW)
    b:SetPoint("TOPLEFT", 4, -18 - (i - 1) * ROW)
    b.text = b:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    b.text:SetPoint("LEFT", 2, 0)
    b.text:SetWidth(W - 14)
    b.text:SetJustifyH("LEFT")
    b:SetScript("OnClick", function(self)
      local r = self.row
      if not r then return end
      if r.go and R2F.BiZ.Go(r.place) then return end
      R2F.Print(L.WT_NO_PLACE:format(r.name))
    end)
    b:SetScript("OnEnter", function(self)
      local r = self.row
      if not (r and GameTooltip) then return end
      GameTooltip:SetOwner(self, "ANCHOR_LEFT")
      GameTooltip:SetText(r.name)
      GameTooltip:AddLine(r.group or "", 0.7, 0.7, 0.7)
      GameTooltip:AddLine(r.go and L.WT_CLICK or L.WT_NO_PLACE_TIP, 0.4, 0.8, 1, true)
      GameTooltip:Show()
    end)
    b:SetScript("OnLeave", function() if GameTooltip then GameTooltip:Hide() end end)
    frame.rows[i] = b
  end
  frame.more = frame:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
  place()
end

function WT.Update()
  if not WT.On() then
    if frame then frame:Hide() end
    return
  end
  if not frame then build() end
  local rows, extra = WT.Rows()
  if #rows == 0 then frame:Hide() return end
  frame.title:SetText(L.WT_TITLE:format(#rows + extra))
  for i, b in ipairs(frame.rows) do
    local r = rows[i]
    b.row = r
    if r then
      b.text:SetText((r.go and "|cff66ccff> |r" or "  ") .. r.name)
      b:Show()
    else
      b:Hide()
    end
  end
  frame.more:ClearAllPoints()
  if extra > 0 then
    frame.more:SetPoint("TOPLEFT", 8, -18 - #rows * ROW)
    frame.more:SetText(L.WT_MORE:format(extra))
    frame.more:Show()
  else
    frame.more:Hide()
  end
  frame:SetHeight(22 + #rows * ROW + (extra > 0 and 14 or 0))
  frame:Show()
end

local pending = false
function WT.Soon()
  if pending then return end
  pending = true
  local function run()
    pending = false
    local ok, err = pcall(WT.Update)
    if not ok then R2F.Gameplay.Report("wishtracker", err) end
  end
  if C_Timer and C_Timer.After then C_Timer.After(0.2, run) else run() end
end

R2F.Gameplay.Register({
  key = "wishtracker", group = "auto", title = "WT_FEATURE", tip = "WT_FEATURE_TIP",
  events = {
    PLAYER_ENTERING_WORLD = WT.Soon,
    BAG_UPDATE_DELAYED = WT.Soon,
    PLAYER_EQUIPMENT_CHANGED = WT.Soon,
  },
  onToggle = WT.Soon,
})
