-- Professions.lua: read the recipes this character knows and export them for
-- the site's Professions page (ADDON_PLAN.md 14, v0.12.0).
--
-- The game only lists recipes while a profession window is open, so we read
-- them on TRADE_SKILL_SHOW / CRAFT_SHOW (and the UPDATE events that follow
-- while it's open) and keep the result per character in
-- R2FCharDB.professions[<profession name>]:
--   { rank, max, api = "trade"|"craft", ts = time(), recipes = {
--       { name, id = <crafted item id or enchant spell id>, kind = "i"|"s",
--         mats = { { id, count, name } ... } } } }
-- Read-only: nothing here calls a protected function, so it's fine in combat.
--
-- Two APIs (both checked at runtime, so a client without one just skips it):
--   trade: GetTradeSkillLine / GetNumTradeSkills / GetTradeSkillInfo /
--          GetTradeSkillItemLink / GetTradeSkillReagentInfo / ...ItemLink
--   craft: GetCraftDisplaySkillLine / GetNumCrafts / GetCraftInfo /
--          GetCraftItemLink / GetCraftReagentInfo / ...ItemLink
-- Classic Enchanting uses the craft window; if Forever moved it to the trade
-- window, the trade path reads it the same way. Collapsed headers and the
-- "Have materials" filter would hide recipes, so before reading we expand all
-- headers and clear that filter (both are plain UI state changes, not
-- protected). Unconfirmed in game: TESTING.md section 21.
--
-- Export string (ADDON_PLAN 14.2): "R2FP1:" .. base64(text), text = lines
-- joined by "\n", fields by "\t":
--   C  <name>  <realm>  <CLASS>  <faction>  <unix time>
--   P  <profession>  <rank>  <max>  <api>
--   R  <recipe name>  <i|s><id>  <matId>:<count>,<matId>:<count>...
-- A material whose item id can't be read (item not cached) is "n:<name>:<count>".

local _, R2F = ...
local L = R2F.L

local Professions = {}
R2F.Professions = Professions

local pending = {}        -- api -> true while a re-read is scheduled
local prepared = {}       -- api -> true once headers/filter were opened this showing

local function idFromLink(link, kind)
  if type(link) ~= "string" then return nil end
  return tonumber(link:match(kind .. ":(%d+)"))
end

-- The two APIs behind one small table, so the reader is written once.
local API = {
  trade = {
    -- (if/return, not "x and f()": "and" would keep only the first of the three values)
    line = function() if GetTradeSkillLine then return GetTradeSkillLine() end end,
    num = function() return GetNumTradeSkills and GetNumTradeSkills() or 0 end,
    info = function(i) return GetTradeSkillInfo(i) end, -- name, type, numAvailable, isExpanded
    link = function(i) return GetTradeSkillItemLink and GetTradeSkillItemLink(i) end,
    numMats = function(i) return GetTradeSkillNumReagents and GetTradeSkillNumReagents(i) or 0 end,
    mat = function(i, r) return GetTradeSkillReagentInfo(i, r) end, -- name, texture, count, have
    matLink = function(i, r) return GetTradeSkillReagentItemLink and GetTradeSkillReagentItemLink(i, r) end,
    prepare = function()
      if TradeSkillOnlyShowMakeable then pcall(TradeSkillOnlyShowMakeable, false) end
      if SetTradeSkillItemNameFilter then pcall(SetTradeSkillItemNameFilter, "") end
      if ExpandTradeSkillSubClass then pcall(ExpandTradeSkillSubClass, 0) end
    end,
  },
  craft = {
    line = function()
      if GetCraftDisplaySkillLine then return GetCraftDisplaySkillLine() end
      if GetCraftSkillLine then return GetCraftSkillLine(1) end
    end,
    num = function() return GetNumCrafts and GetNumCrafts() or 0 end,
    info = function(i) -- name, subSpellName, type, numAvailable, isExpanded
      local name, _, kind, _, expanded = GetCraftInfo(i)
      return name, kind, nil, expanded
    end,
    link = function(i) return GetCraftItemLink and GetCraftItemLink(i) end,
    numMats = function(i) return GetCraftNumReagents and GetCraftNumReagents(i) or 0 end,
    mat = function(i, r) return GetCraftReagentInfo(i, r) end, -- name, texture, count, have
    matLink = function(i, r) return GetCraftReagentItemLink and GetCraftReagentItemLink(i, r) end,
    prepare = function()
      if CraftOnlyShowMakeable then pcall(CraftOnlyShowMakeable, false) end
      if ExpandCraftSkillLine then pcall(ExpandCraftSkillLine, 0) end
    end,
  },
}

-- Read the open window. Returns the saved entry, or nil if nothing to read.
local function read(api)
  local a = API[api]
  local profName, rank, max = a.line()
  if not profName or profName == "" or profName == "UNKNOWN" then return nil end
  local recipes = {}
  for i = 1, a.num() do
    local name, kind = a.info(i)
    if name and kind ~= "header" and kind ~= "subheader" then
      local link = a.link(i)
      local itemId = idFromLink(link, "item")
      local spellId = idFromLink(link, "enchant") or idFromLink(link, "spell")
      local mats = {}
      for r = 1, a.numMats(i) do
        local mName, _, count = a.mat(i, r)
        if mName or count then
          mats[#mats + 1] = { id = idFromLink(a.matLink(i, r), "item"), count = count or 1, name = mName }
        end
      end
      recipes[#recipes + 1] = {
        name = name,
        kind = itemId and "i" or "s",
        id = itemId or spellId,
        mats = mats,
      }
    end
  end
  if #recipes == 0 then return nil end
  local entry = { rank = rank or 0, max = max or 0, api = api, ts = time(), recipes = recipes }
  R2F.Library.cdb.professions[profName] = entry
  return profName, entry
end

-- Re-read shortly after the last update event: the window fires a burst of
-- them while it fills, and item links can arrive a moment later.
local function schedule(api, announce)
  if pending[api] then return end
  pending[api] = true
  local run = function()
    pending[api] = nil
    local ok, profName, entry = pcall(read, api)
    if ok and profName and announce then
      local before = Professions.lastCount and Professions.lastCount[profName]
      Professions.lastCount = Professions.lastCount or {}
      if before ~= #entry.recipes then
        Professions.lastCount[profName] = #entry.recipes
        R2F.Print(L.PROF_SAVED:format(#entry.recipes, profName, entry.rank or 0))
      end
    end
  end
  if C_Timer and C_Timer.After then C_Timer.After(0.4, run) else run() end
end

-- A small "Export" button on Blizzard's profession window. Our own plain
-- button parented to their frame (no hooks, nothing secure), made once.
local buttons = {}
local function addButton(api)
  if buttons[api] then return end
  local parent = api == "craft" and _G.CraftFrame or _G.TradeSkillFrame
  if not parent then return end
  local b = CreateFrame("Button", nil, parent, "UIPanelButtonTemplate")
  b:SetSize(70, 20)
  local close = api == "craft" and _G.CraftFrameCloseButton or _G.TradeSkillFrameCloseButton
  if close then
    b:SetPoint("RIGHT", close, "LEFT", -2, 0)
  else
    b:SetPoint("TOPRIGHT", parent, "TOPRIGHT", -40, -14)
  end
  b:SetText(L.PROF_BUTTON)
  b:SetFrameLevel(parent:GetFrameLevel() + 5)
  b:SetScript("OnClick", function()
    pcall(read, api)
    Professions.Export()
  end)
  b:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:SetText(L.PROF_BUTTON_TIP, 1, 1, 1, 1, true)
    GameTooltip:Show()
  end)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
  buttons[api] = b
end

function Professions.OnShow(api)
  prepared[api] = nil
  pcall(addButton, api)
  -- Open every header and clear "Have materials" once per showing, so the
  -- list holds every known recipe; the UPDATE that follows triggers the read.
  pcall(API[api].prepare)
  prepared[api] = true
  schedule(api, true)
end

function Professions.OnUpdate(api)
  if not prepared[api] then return end
  schedule(api, true)
end

-- ---------------------------------------------------------------------------
-- Export
-- ---------------------------------------------------------------------------

local function clean(s)
  return (tostring(s or ""):gsub("[\t\n\r]", " "))
end

function Professions.ExportString()
  local profs = R2F.Library.cdb.professions
  local names = {}
  for name in pairs(profs) do names[#names + 1] = name end
  if #names == 0 then return nil end
  table.sort(names)
  local lines = {}
  local function add(...) lines[#lines + 1] = table.concat({ ... }, "\t") end
  local name, realm
  if UnitFullName then name, realm = UnitFullName("player") end
  name = name or UnitName("player")
  realm = realm or (GetRealmName and GetRealmName()) or ""
  add("C", clean(name), clean(realm), select(2, UnitClass("player")) or "", UnitFactionGroup("player") or "", tostring(time()))
  for _, profName in ipairs(names) do
    local e = profs[profName]
    add("P", clean(profName), tostring(e.rank or 0), tostring(e.max or 0), e.api or "")
    for _, r in ipairs(e.recipes or {}) do
      local mats = {}
      for _, m in ipairs(r.mats or {}) do
        if m.id then
          mats[#mats + 1] = m.id .. ":" .. (m.count or 1)
        else
          mats[#mats + 1] = "n:" .. clean(m.name):gsub("[:,]", " ") .. ":" .. (m.count or 1)
        end
      end
      add("R", clean(r.name), (r.kind or "s") .. tostring(r.id or 0), table.concat(mats, ","))
    end
  end
  return "R2FP1:" .. R2F.Base64.Encode(table.concat(lines, "\n"))
end

function Professions.Export()
  local s = Professions.ExportString()
  if not s then
    R2F.Print(L.PROF_NONE)
    return nil
  end
  R2F.UI.ShowCopy(s, L.PROF_COPY_HINT)
  return s
end
