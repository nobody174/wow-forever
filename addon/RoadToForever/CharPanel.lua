-- CharPanel.lua: a small read-only panel docked on the right edge of the Character window with your Next upgrades
-- (BiZMe.lua): item, slot, gain, where it comes from. Click a row to point the BiZNav arrow at it; the buttons open the
-- full Mr.BiZ tab or step the arrow through the list.
-- Off until ticked (Tweaks, Bags: "Character window upgrades panel"). Taint rules: our own frame, parented to UIParent
-- and only ANCHORED to CharacterFrame (SetPoint on our frame); shown and hidden from CharacterFrame OnShow / OnHide hooks
-- (HookScript, run after the game's handlers). Nothing is written into the game's frames or tables.

local _, R2F = ...
local L = R2F.L

local CP = {}
R2F.CharPanel = CP

CP.MAX_ROWS = 8
local W, ROW = 300, 34
local frame

function CP.On() return R2F.Gameplay.IsOn("charpanel") end

local function quality(id)
  local q = R2F.BiZ.Quality(id)
  local c = q and _G.ITEM_QUALITY_COLORS and ITEM_QUALITY_COLORS[q]
  return c and c.r or 1, c and c.g or 1, c and c.b or 1
end

-- What to show: the first MAX_ROWS upgrades for the viewed spec and level (the same list as the Next upgrades view).
function CP.Rows()
  local specId = R2F.BiZ.SpecId()
  local list = R2F.BiZMe.Upgrades(specId, R2F.BiZ.Level())
  local rows = {}
  for i = 1, math.min(#list, CP.MAX_ROWS) do rows[i] = list[i] end
  return rows, #list, list
end

local function build()
  frame = CreateFrame("Frame", "R2FCharPanelFrame", UIParent)
  frame:SetSize(W, 100)
  frame:SetFrameStrata("MEDIUM")
  frame:EnableMouse(true)
  frame.bg = frame:CreateTexture(nil, "BACKGROUND")
  frame.bg:SetAllPoints()
  frame.bg:SetColorTexture(0.06, 0.05, 0.04, 0.92)
  frame.edge = frame:CreateTexture(nil, "BORDER")
  frame.edge:SetPoint("TOPLEFT")
  frame.edge:SetPoint("BOTTOMLEFT")
  frame.edge:SetWidth(2)
  frame.edge:SetColorTexture(0.75, 0.6, 0.15, 1)
  frame.title = frame:CreateFontString(nil, "OVERLAY", "GameFontNormal")
  frame.title:SetPoint("TOPLEFT", 10, -8)
  frame.sub = frame:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
  frame.sub:SetPoint("TOPLEFT", 10, -24)
  frame.rows = {}
  for i = 1, CP.MAX_ROWS do
    local b = CreateFrame("Button", nil, frame)
    b:SetSize(W - 16, ROW)
    b:SetPoint("TOPLEFT", 8, -42 - (i - 1) * ROW)
    b.name = b:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    b.name:SetPoint("TOPLEFT", 2, -2)
    b.name:SetWidth(W - 70)
    b.name:SetJustifyH("LEFT")
    b.gain = b:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    b.gain:SetPoint("TOPRIGHT", -2, -2)
    b.info = b:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
    b.info:SetPoint("TOPLEFT", 2, -17)
    b.info:SetWidth(W - 24)
    b.info:SetJustifyH("LEFT")
    b:SetScript("OnClick", function(self)
      local u = self.up
      if not u then return end
      if u.placeKey and R2F.BiZ.Go(u.placeKey) then return end
      R2F.Print(L.WT_NO_PLACE:format(u.row.name))
    end)
    b:SetScript("OnEnter", function(self)
      local u = self.up
      if not (u and GameTooltip) then return end
      GameTooltip:SetOwner(self, "ANCHOR_LEFT")
      GameTooltip:SetText(u.row.name)
      GameTooltip:AddLine(R2F.BiZ.SlotLabel(u.slot), 0.7, 0.7, 0.7)
      GameTooltip:AddLine(u.placeKey and L.WT_CLICK or L.WT_NO_PLACE_TIP, 0.4, 0.8, 1, true)
      GameTooltip:Show()
    end)
    b:SetScript("OnLeave", function() if GameTooltip then GameTooltip:Hide() end end)
    frame.rows[i] = b
  end
  frame.empty = frame:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
  frame.empty:SetPoint("TOPLEFT", 10, -46)
  frame.empty:SetWidth(W - 20)
  frame.empty:SetJustifyH("LEFT")
  frame.open = CreateFrame("Button", nil, frame, "UIPanelButtonTemplate")
  frame.open:SetSize(120, 22)
  frame.open:SetText(L.CP_OPEN)
  frame.open:SetScript("OnClick", function() R2F.BiZTab.Show("up") end)
  frame.guide = CreateFrame("Button", nil, frame, "UIPanelButtonTemplate")
  frame.guide:SetSize(120, 22)
  frame.guide:SetText(L.BIZ_ROUTE)
  frame.guide:SetScript("OnClick", function()
    local _, _, list = CP.Rows()
    local u, more = R2F.BiZMe.GuideNext(list)
    if u then R2F.Print(L.BIZ_ROUTE_TO:format(u.row.name, more)) else R2F.Print(L.BIZ_ROUTE_NONE) end
  end)
  frame:Hide()
end

function CP.Update()
  if CP.On() and not frame and _G.CharacterFrame then build() end
  if not frame then return end
  if not (CP.On() and _G.CharacterFrame and CharacterFrame:IsShown()) then frame:Hide() return end
  local rows, total = CP.Rows()
  local specId = R2F.BiZ.SpecId()
  local sp = R2F.BiZ.Spec(specId)
  frame.title:SetText(L.CP_TITLE)
  frame.sub:SetText(L.CP_SUB:format(sp and sp.name or "?", R2F.BiZ.Level(), total))
  for i, b in ipairs(frame.rows) do
    local u = rows[i]
    b.up = u
    if u then
      b.name:SetText(u.row.name)
      b.name:SetTextColor(quality(u.row.id))
      b.gain:SetText(("|cff1eff00+%d%%|r"):format(math.floor(u.gain + 0.5)))
      local src = u.row.label or ""
      if u.trip then src = src .. " · " .. L.BIZ_UP_TRIP end
      b.info:SetText(R2F.BiZ.SlotLabel(u.slot) .. " · " .. src)
      b:Show()
    else
      b:Hide()
    end
  end
  frame.empty:SetText(#rows == 0 and L.BIZ_UP_EMPTY or "")
  local y = 42 + math.max(#rows, 1) * ROW + (#rows == 0 and 20 or 0)
  frame.open:ClearAllPoints()
  frame.open:SetPoint("TOPLEFT", 10, -y - 4)
  frame.guide:ClearAllPoints()
  frame.guide:SetPoint("LEFT", frame.open, "RIGHT", 6, 0)
  frame:SetHeight(y + 34)
  frame:ClearAllPoints()
  frame:SetPoint("TOPLEFT", CharacterFrame, "TOPRIGHT", -30, -14)
  frame:Show()
end

local pending = false
function CP.Soon()
  if pending then return end
  pending = true
  local function run()
    pending = false
    local ok, err = pcall(function()
      CP.Update()
    end)
    if not ok then R2F.Gameplay.Report("charpanel", err) end
  end
  if C_Timer and C_Timer.After then C_Timer.After(0.1, run) else run() end
end

local hooked = false
local function hookFrame()
  if hooked or not (_G.CharacterFrame and CharacterFrame.HookScript) then return end
  hooked = true
  CharacterFrame:HookScript("OnShow", CP.Soon)
  CharacterFrame:HookScript("OnHide", function() if frame then frame:Hide() end end)
end

R2F.Gameplay.Register({
  key = "charpanel", group = "auto", title = "CP_FEATURE", tip = "CP_FEATURE_TIP",
  events = {
    PLAYER_EQUIPMENT_CHANGED = CP.Soon,
    PLAYER_LEVEL_UP = CP.Soon,
    BAG_UPDATE_DELAYED = CP.Soon,
  },
  onToggle = function()
    hookFrame()
    CP.Soon()
  end,
})
