-- UI/BiZ.lua: the BiS tab of the main window, "Mr.BiZ". Logic in BiZ.lua.
--
-- Best in slot view (paper doll):
--   [Class v] [Spec v]                                   [Best in slot] [Wishlist (n)]
--   left: your character's 3D model with the 17 gear slots around it (the best pick's icon in
--     its quality colour; click a slot to select it, hover for the item tooltip), source
--     filters under it (switches).
--   right: the selected slot's options: the best pick and the next ranked ones (#2, #3 with how
--     far behind they score), each with its source, score and a wishlist switch. Hover any item:
--     the game's tooltip plus its rank. Shift-click: link in chat.
-- Wishlist view: grouped by where you get the items (a dungeon, a profession, a vendor), biggest
--   group first, in a scrolling list; Export / Import share the list with the site (R2FW1:).
-- The model is the game's PlayerModel showing "player" (drag to turn it). Class /
-- spec menus use UI.ContextMenu (no UIDropDownMenu: taint). Everything is redrawn from the data
-- on each refresh; the widgets are pooled per host frame and kind.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI
local BiZ = R2F.BiZ

local Tab = {}
R2F.BiZTab = Tab

local page, scroll, content, side
local ui = {}
local typeBoxes = {}
local slotBtns = {}               -- slot key -> doll button
local view = "set"                -- "set" | "wish"
local selected                    -- slot key selected on the doll

-- The page is bigger than the old 540 x 500 book pages; MainWindow reads this.
Tab.PAGE = { w = 650, h = 540 }

local CONTENT_W = 620
local SLOT = 40
local CONF_COLOR = {
  seen = "|cff7fd6a4", client = "|cff8db7ee", classic = "|cffe0be77", clue = "|cffd9a1e0", unknown = "|cffb5b1a6",
}
-- Doll layout: two columns of slots around the model, weapons under it.
local LEFT_SLOTS = { "head", "neck", "shoulder", "back", "chest", "wrist", "hands" }
local RIGHT_SLOTS = { "waist", "legs", "feet", "finger1", "finger2", "trinket1", "trinket2" }
local WEAPON_SLOTS = { "mainhand", "offhand", "ranged" }
local DOLL_Y, DOLL_STEP, DOLL_RIGHT_X, MODEL_W = 40, 46, 264, 204
local QUALITY_RGB = {
  [0] = { 0.62, 0.62, 0.62 }, { 1, 1, 1 }, { 0.12, 1, 0 }, { 0, 0.44, 0.87 }, { 0.64, 0.21, 0.93 }, { 1, 0.5, 0 },
}

local function visible() return page ~= nil and page:IsVisible() end

-- ---------------------------------------------------------------------------
-- Pools (one per widget kind and host frame; `used` counts what this pass took)
-- ---------------------------------------------------------------------------

local host                        -- the frame new widgets are created in / pooled for
local pools = {}
local function pool(kind, make)
  local key = (host == side and "s:" or "c:") .. kind
  local p = pools[key]
  if not p then p = { list = {}, used = 0, make = make }; pools[key] = p end
  p.used = p.used + 1
  local w = p.list[p.used]
  if not w then w = p.make(); p.list[p.used] = w end
  w:ClearAllPoints()
  w:Show()
  return w
end
local function resetPools()
  for _, p in pairs(pools) do p.used = 0 end
end
local function hideUnused()
  for _, p in pairs(pools) do
    for i = p.used + 1, #p.list do p.list[i]:Hide() end
  end
end

local function text(font)
  return pool("fs:" .. font, function()
    local fs = host:CreateFontString(nil, "ARTWORK", font)
    fs:SetJustifyH("LEFT")
    fs:SetWordWrap(false)
    return fs
  end)
end

local function icon(size)
  return pool("icon", function()
    local t = host:CreateTexture(nil, "ARTWORK")
    t:SetSize(size or 22, size or 22)
    return t
  end)
end

-- An item name: hover = tooltip, click = onClick, shift-click = chat link.
local function itemButton()
  return pool("item", function()
    local b = CreateFrame("Button", nil, host)
    b:SetHeight(18)
    b.fs = b:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    b.fs:SetAllPoints(b)
    b.fs:SetJustifyH("LEFT")
    b.fs:SetWordWrap(false)
    b:SetHighlightTexture("Interface\\QuestFrame\\UI-QuestTitleHighlight", "ADD")
    b:SetScript("OnEnter", function(self)
      if self.itemId then BiZ.ShowTooltip(self, self.itemId, self.rankLine, self.place) end
    end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    b:SetScript("OnClick", function(self)
      if IsAltKeyDown() and self.place and BiZ.Go(self.place) then return end
      if IsShiftKeyDown() and self.itemId and BiZ.LinkInChat(self.itemId, self.linkName) then return end
      if self.onClick then self.onClick() end
    end)
    return b
  end)
end

-- Wishlist switch. `label` shows next to it in the slot panel, none in the wishlist list.
local function wishBox(label)
  return pool("wish:" .. (label or ""), function()
    local c = UI.CheckButton(host, label or "")
    c:SetScript("OnClick", function(self)
      if self.itemId then
        BiZ.ToggleWish(self.itemId, self.specId, self.slot)
        Tab.Refresh()
      end
    end)
    c:SetScript("OnEnter", function(self)
      GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
      GameTooltip:AddLine(BiZ.IsWished(self.itemId) and L.BIZ_WISH_REMOVE or L.BIZ_WISH_ADD, 1, 1, 1)
      GameTooltip:Show()
    end)
    c:SetScript("OnLeave", function() GameTooltip:Hide() end)
    return c
  end)
end

local function placeItem(x, y, w, id, name, rankLine, onClick, iconSize)
  local ic = icon(iconSize)
  ic:SetPoint("TOPLEFT", host, "TOPLEFT", x, -y)
  ic:SetTexture(BiZ.Icon(id) or UI.FALLBACK_ICON)
  local b = itemButton()
  b:SetPoint("TOPLEFT", host, "TOPLEFT", x + (iconSize or 22), -y - 1)
  b:SetWidth(w)
  b.itemId, b.rankLine, b.onClick, b.linkName = id, rankLine, onClick, name
  b.place = BiZ.PlaceOfItem(id)
  b.fs:SetText(BiZ.ColoredName(id, name))
  return b
end

local function placeWish(x, y, id, specId, slot, label)
  local c = wishBox(label)
  c:SetPoint("TOPLEFT", host, "TOPLEFT", x, -y)
  c.itemId, c.specId, c.slot = id, specId, slot
  c:SetChecked(BiZ.IsWished(id))
  return c
end

local function line(font, x, y, w, str)
  local fs = text(font)
  fs:SetPoint("TOPLEFT", host, "TOPLEFT", x, -y)
  fs:SetWidth(w)
  fs:SetWordWrap(false)
  fs:SetTextColor(1, 1, 1)
  fs:SetText(str)
  return fs
end

-- ---------------------------------------------------------------------------
-- Best in slot view
-- ---------------------------------------------------------------------------

-- gap: how far (%) the next pick is behind the best when the best is The Bizz.
-- gap: how far (%) the next pick is behind the best when the best is The Bizz; label: where it comes from.
local function rankLine(specName, rank, score, delta, gap, label, via)
  local s
  if rank == 1 and gap then s = L.BIZ_TIP_BIZZ:format(specName, score, gap)
  elseif rank == 1 then s = L.BIZ_TIP_BEST:format(specName, score)
  elseif delta and delta ~= 0 then s = L.BIZ_TIP_RANK:format(BiZ.RankName(rank), specName, -delta)
  else s = L.BIZ_TIP_RANK_SAME:format(BiZ.RankName(rank), specName) end
  local from = L.BIZ_TIP_FROM:format(label or L.BIZ_TYPE_UNKNOWN)
  if via then from = from .. " |cff808080(" .. via .. ")|r" end
  return s .. "\n" .. from
end

-- The slot entry of the current spec for a slot key (nil when the spec has none).
local function slotOf(sp, key)
  for _, sl in ipairs(sp.slots) do
    if sl.slot == key then return sl end
  end
end

-- The ranked picks of a slot: best first, then the next ones.
local function allPicks(sl)
  local all = { sl.best }
  for _, n in ipairs(sl.next or {}) do all[#all + 1] = n end
  return all
end

-- The pick the doll shows for a slot: the first rank the filters let through (a stand-in when
-- the best is filtered out), its rank, or nil when nothing passes.
local function shownPick(sl)
  if not sl or not sl.best then return nil end
  for i, it in ipairs(allPicks(sl)) do
    if BiZ.Passes(it) then return it, i end
  end
end

local function paintSlotButton(key, sp)
  local b = slotBtns[key]
  local sl = slotOf(sp, key)
  local pick = shownPick(sl)
  b.slotKey = key
  b.itemId = pick and pick.id or nil
  b.linkName = pick and pick.name or nil
  b.place = pick and pick.place or nil
  b.rankLine = nil
  if pick then
    b.icon:SetTexture(BiZ.Icon(pick.id) or UI.FALLBACK_ICON)
    b.icon:SetVertexColor(1, 1, 1)
    local q = BiZ.Quality(pick.id)
    local c = QUALITY_RGB[q or 1]
    b.border:SetColorTexture(c[1], c[2], c[3], 1)
  else
    b.icon:SetTexture(UI.FALLBACK_ICON)
    b.icon:SetVertexColor(0.35, 0.35, 0.35)
    b.border:SetColorTexture(0.25, 0.25, 0.28, 1)
  end
  if selected == key then
    b.sel:Show()
  else
    b.sel:Hide()
  end
end

-- The slot panel on the right: the selected slot's options.
local function layoutSide()
  host = side
  local specId = BiZ.SpecId()
  local sp = BiZ.Spec(specId)
  local shown, hidden = 0, 0
  for _, sl in ipairs(sp.slots) do
    if sl.best then
      if shownPick(sl) then shown = shown + 1 else hidden = hidden + 1 end
    end
  end
  ui.summary:SetText(hidden > 0 and L.BIZ_SUMMARY_HIDDEN:format(shown, hidden) or L.BIZ_SUMMARY:format(shown))
  ui.footer:SetText(L.BIZ_FOOTER:format(R2F.BiZData.level, R2F.BiZData.source, sp.build))

  local sl = slotOf(sp, selected)
  line("GameFontNormalLarge", 0, 0, 320, BiZ.SlotLabel(selected))
  if not (sl and sl.best) then
    line("GameFontDisableSmall", 0, 30, 320, L.BIZ_NOTHING)
    if sl and sl.note then
      local n = line("GameFontDisableSmall", 0, 46, 320, (sl.note:gsub("^%l", string.upper)))
      n:SetWordWrap(true)
    end
    return
  end

  local b = sl.best
  local nxt = sl.next or {}
  local all = allPicks(sl)
  local gapOf = function(rank) return rank == 1 and BiZ.IsTheBizz(sl) and -nxt[1].delta or nil end
  -- BiS enchant for this slot (the site's Professions page; ForeverChanges' spec pages), right under the
  -- slot name so it is never pushed off the bottom by a long list of picks: the best one, the 2nd / 3rd best
  -- stand-ins under it, and what you wear there now.
  local y = 30
  local rows = BiZ.Enchants(specId, sl.slot)
  local altLines = 0
  for i, e in ipairs(rows) do
    if i > 2 then break end
    local head = line("GameFontNormalSmall", 0, y, 320, L.BIZ_ENCHANT:format(e.name))
    head:SetWordWrap(false)
    local kind = e.kind == "2h" and (" · " .. L.BIZ_ENCHANT_2H) or ""
    local sub = line("GameFontDisableSmall", 12, y + 14, 308, L.BIZ_ENCHANT_SUB:format(e.eff, e.prof, e.skill) .. kind)
    sub:SetWordWrap(false)
    y = y + 28
    for n, a in ipairs(e.alts or {}) do
      if altLines >= 3 then break end
      altLines = altLines + 1
      local al = line("GameFontDisableSmall", 12, y, 308, L.BIZ_ENCHANT_ALT:format(n + 1, a.name, a.prof, a.skill))
      al:SetWordWrap(false)
      y = y + 14
    end
  end
  if #rows > 0 then
    local state, _, rank = BiZ.EnchantState(rows, BiZ.WornEnchant(sl.slot))
    if state then
      local label = BiZ.SlotLabel(sl.slot):lower()
      local msg, cr, cg, cb
      if state == "best" then msg, cr, cg, cb = L.BIZ_WORN_BEST:format(label), 0.3, 1, 0.3
      elseif state == "alt" then msg, cr, cg, cb = L.BIZ_WORN_ALT:format(label, rank), 1, 0.82, 0
      elseif state == "other" then msg, cr, cg, cb = L.BIZ_WORN_OTHER:format(label), 0.7, 0.7, 0.7
      else msg, cr, cg, cb = L.BIZ_WORN_NONE:format(label), 1, 0.4, 0.4 end
      local wl = line("GameFontHighlightSmall", 0, y + 2, 320, msg)
      wl:SetTextColor(cr, cg, cb)
      wl:SetWordWrap(false)
      y = y + 18
    end
  end
  y = y + 6
  for rank, it in ipairs(all) do
    local passes = BiZ.Passes(it)
    local gap = gapOf(rank)
    local fnote = BiZ.FactionNote(it)
    local nb = placeItem(0, y, 270, it.id, it.name,
      rankLine(sp.name, rank, b.score, it.delta, gap, it.label, it.via), nil, 32)
    nb.optRank = rank
    local name = BiZ.ColoredName(it.id, it.name)
    if fnote then name = name .. " |cffe86a5a(" .. fnote .. ")|r" end
    nb.fs:SetText(passes and name or ("|cff808080" .. it.name .. "|r"))
    local rn = gap and L.BIZ_THE_BIZZ or BiZ.RankName(rank)
    local d = rank == 1 and tostring(b.score)
      or (it.delta == 0 and L.BIZ_SAME) or (it.delta and (it.delta .. "%")) or ""
    line("GameFontHighlightSmall", 40, y + 19, 280,
      "|cffffd100" .. rn .. "|r" .. (d ~= "" and ("  |cffe39a79" .. d .. "|r") or ""))
    local src = it.label or L.BIZ_TYPE_UNKNOWN
    local fs = line("GameFontDisableSmall", 40, y + 33, 280, passes and src or ("|cff707070" .. src .. "|r"))
    fs:SetWordWrap(false)
    local conf = it.conf or "unknown"
    local cf = line("GameFontHighlightSmall", 250, y + 19, 70, (CONF_COLOR[conf] or "") .. L["BIZ_CONF_" .. conf:upper()] .. "|r")
    cf:SetJustifyH("RIGHT")
    placeWish(40, y + 50, it.id, specId, sl.slot, L.BIZ_WISH_LABEL)
    y = y + 84
  end
  local ease = (b.ease and b.ease ~= "") and (" · " .. b.ease) or ""
  local facts = line("GameFontHighlightSmall", 0, y, 320, b.name .. ": " .. b.stats .. ease)
  facts:SetTextColor(0.7, 0.7, 0.7)
  facts:SetWordWrap(true)
  if #nxt == 0 then line("GameFontDisableSmall", 0, y + 30, 320, L.BIZ_NO_MORE) end
end

-- ---------------------------------------------------------------------------
-- Wishlist view
-- ---------------------------------------------------------------------------

local function layoutWish()
  host = content
  local y = 0
  local groups = BiZ.WishGroups()
  if #groups == 0 then
    local e = line("GameFontHighlight", 8, 8, 420, L.BIZ_WISH_EMPTY)
    e:SetWordWrap(true)
    return 60
  end
  for _, g in ipairs(groups) do
    line("GameFontNormal", 0, y, 330, g.name)
    local fmt = #g.items == 1 and L.BIZ_ONE_ITEM or L.BIZ_N_ITEMS
    local cnt = line("GameFontHighlightSmall", 500, y + 2, 96, fmt:format(#g.items))
    cnt:SetJustifyH("RIGHT")
    y = y + 20
    for _, it in ipairs(g.items) do
      local sp = it.spec and BiZ.Spec(it.spec)
      placeItem(8, y, 300, it.id, it.name, sp and L.BIZ_TIP_WISHED:format(sp.name, BiZ.SlotLabel(it.slot or "")) or nil)
      local detail = BiZ.SlotLabel(it.slot or "") .. (sp and (" · " .. sp.name) or "")
      line("GameFontDisableSmall", 330, y + 3, 200, detail)
      placeWish(560, y + 3, it.id, it.spec, it.slot)
      y = y + 22
    end
    y = y + 8
  end
  ui.summary:SetText(L.BIZ_WISH_SUMMARY:format(BiZ.WishCount()))
  return y
end

-- ---------------------------------------------------------------------------
-- Import dialog
-- ---------------------------------------------------------------------------

local importFrame
local function showImport()
  if not importFrame then
    local f = UI.DialogFrame("R2FBiZImport", UIParent)
    f:SetSize(420, 230)
    f:SetPoint("CENTER", 0, 80)
    f:SetFrameStrata("DIALOG")
    f:SetToplevel(true)
    f:EnableMouse(true)
    f:Hide()
    if UISpecialFrames then table.insert(UISpecialFrames, "R2FBiZImport") end
    local hint = f:CreateFontString(nil, "ARTWORK", "GameFontNormal")
    hint:SetPoint("TOP", 0, -18)
    hint:SetWidth(370)
    hint:SetText(L.BIZ_IMPORT_HINT)
    local sc, edit = UI.MultiLineEdit(f, "R2FBiZImportScroll", 350, 100)
    sc:SetPoint("TOPLEFT", 24, -54)
    edit:SetScript("OnEscapePressed", function() f:Hide() end)
    local msg = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    msg:SetPoint("TOPLEFT", 24, -162)
    msg:SetWidth(360)
    msg:SetJustifyH("LEFT")
    local ok = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
    ok:SetSize(120, 22)
    ok:SetPoint("BOTTOMRIGHT", f, "BOTTOM", -6, 18)
    ok:SetText(L.BIZ_IMPORT_ADD)
    ok:SetScript("OnClick", function()
      local n, err = BiZ.Import(edit:GetText())
      if not n then
        msg:SetText("|cffff4040" .. err .. "|r")
        return
      end
      R2F.Print(L.BIZ_IMPORT_DONE:format(n))
      f:Hide()
      Tab.Refresh()
    end)
    local close = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
    close:SetSize(120, 22)
    close:SetPoint("BOTTOMLEFT", f, "BOTTOM", 6, 18)
    close:SetText(L.BIZ_CLOSE)
    close:SetScript("OnClick", function() f:Hide() end)
    f.edit, f.msg = edit, msg
    importFrame = f
  end
  importFrame.edit:SetText("")
  importFrame.msg:SetText("")
  importFrame:Show()
  importFrame.edit:SetFocus()
end
Tab.ShowImport = showImport

-- ---------------------------------------------------------------------------
-- Menus
-- ---------------------------------------------------------------------------

local function classMenu()
  local items = { { kind = "title", text = L.BIZ_CLASS } }
  for _, c in ipairs(BiZ.Classes()) do
    items[#items + 1] = { kind = "check", text = c.name, isChecked = function() return BiZ.Class() == c.key end,
      func = function() BiZ.SetClass(c.key); scroll:SetVerticalScroll(0); Tab.Refresh() end }
  end
  UI.ContextMenu(items)
end

local ROLE_ORDER = { "tank", "dps", "healer" }
local function specMenu()
  local items = {}
  local specs = BiZ.SpecsOf(BiZ.Class())
  for _, role in ipairs(ROLE_ORDER) do
    local any = false
    for _, id in ipairs(specs) do
      local s = BiZ.Spec(id)
      if s.role == role then
        if not any then items[#items + 1] = { kind = "title", text = L["BIZ_ROLE_" .. role:upper()] }; any = true end
        items[#items + 1] = { kind = "check", text = s.name, isChecked = function() return BiZ.SpecId() == id end,
          func = function() BiZ.SetSpec(id); scroll:SetVerticalScroll(0); Tab.Refresh() end }
      end
    end
  end
  UI.ContextMenu(items)
end

-- ---------------------------------------------------------------------------
-- Refresh / build
-- ---------------------------------------------------------------------------

local function setViewShown()
  local isSet = view == "set"
  for _, b in pairs(slotBtns) do b:SetShown(isSet) end
  for _, w in pairs(typeBoxes) do w:SetShown(isSet) end
  ui.known:SetShown(isSet)
  ui.footer:SetShown(isSet)
  ui.side:SetShown(isSet)
  ui.modelBack:SetShown(isSet)
  if ui.model then ui.model:SetShown(isSet) end
  scroll:SetShown(not isSet)
  ui.exportBtn:SetShown(not isSet)
  ui.importBtn:SetShown(not isSet)
end

local function refresh()
  if not visible() then return end
  local sp = BiZ.Spec(BiZ.SpecId())
  ui.classBtn:SetText(BiZ.ClassName(BiZ.Class()))
  ui.specBtn:SetText(sp.name)
  ui.setBtn:SetEnabled(view ~= "set")
  ui.wishBtn:SetEnabled(view ~= "wish")
  ui.wishBtn:SetText(L.BIZ_VIEW_WISH:format(BiZ.WishCount()))
  for t, box in pairs(typeBoxes) do box:SetChecked(BiZ.TypeOn(t)) end
  ui.known:SetChecked(BiZ.KnownOnly())
  setViewShown()

  -- Keep the selected slot while the spec changes; fall back to the first slot with a pick.
  if not (selected and slotOf(sp, selected) and slotOf(sp, selected).best) then
    selected = nil
    for _, sl in ipairs(sp.slots) do
      if sl.best then selected = sl.slot; break end
    end
    selected = selected or "head"
  end

  resetPools()
  if view == "set" then
    for key in pairs(slotBtns) do paintSlotButton(key, sp) end
    layoutSide()
    ui.contentHeight = 0
  else
    local h = layoutWish()
    content:SetHeight(math.max(h, 1))
    ui.contentHeight = h
  end
  hideUnused()
end
Tab.Refresh = refresh

-- GET_ITEM_INFO_RECEIVED (Core.lua): an item's quality / icon arrived. Many come at once
-- when a list first shows, so redraw once, a moment later.
local pendingInfo = false
function Tab.OnItemInfo()
  if not visible() or pendingInfo then return end
  pendingInfo = true
  local function run() pendingInfo = false; refresh() end
  if C_Timer and C_Timer.After then C_Timer.After(0.2, run) else run() end
end

local function onWheel(self, delta)
  local maxScroll = math.max((ui.contentHeight or 0) - self:GetHeight(), 0)
  local v = (self:GetVerticalScroll() or 0) - delta * 40
  self:SetVerticalScroll(math.max(0, math.min(v, maxScroll)))
end

-- A button that opens a menu: the game's own down arrow sits at its right edge, the text is
-- moved left to make room.
local function dropButton(parent, w, fn)
  local b = CreateFrame("Button", nil, parent, "UIPanelButtonTemplate")
  b:SetSize(w, 24)
  b:SetScript("OnClick", fn)
  local arrow = b:CreateTexture(nil, "OVERLAY")
  arrow:SetSize(20, 20)
  arrow:SetPoint("RIGHT", b, "RIGHT", -3, -1)
  arrow:SetTexture("Interface\\ChatFrame\\UI-ChatIcon-ScrollDown-Up")
  local fs = b.GetFontString and b:GetFontString()
  if fs then
    fs:ClearAllPoints()
    fs:SetPoint("LEFT", b, "LEFT", 10, 0)
    fs:SetPoint("RIGHT", b, "RIGHT", -24, 0)
    fs:SetJustifyH("LEFT")
  end
  return b
end

local function button(parent, w, label, fn)
  local b = CreateFrame("Button", nil, parent, "UIPanelButtonTemplate")
  b:SetSize(w, 22)
  b:SetText(label)
  b:SetScript("OnClick", fn)
  return b
end

-- One gear slot button of the doll: item icon in a quality-coloured frame, a gold ring when selected.
local function buildSlotButton(f, key, x, y)
  local b = CreateFrame("Button", nil, f)
  b:SetSize(SLOT, SLOT)
  b:SetPoint("TOPLEFT", f, "TOPLEFT", x, -y)
  b.sel = b:CreateTexture(nil, "BACKGROUND")
  b.sel:SetPoint("TOPLEFT", b, "TOPLEFT", -3, 3)
  b.sel:SetPoint("BOTTOMRIGHT", b, "BOTTOMRIGHT", 3, -3)
  b.sel:SetColorTexture(1, 0.82, 0, 1)
  b.border = b:CreateTexture(nil, "BORDER")
  b.border:SetAllPoints(b)
  b.border:SetColorTexture(0.25, 0.25, 0.28, 1)
  b.icon = b:CreateTexture(nil, "ARTWORK")
  b.icon:SetPoint("TOPLEFT", b, "TOPLEFT", 2, -2)
  b.icon:SetPoint("BOTTOMRIGHT", b, "BOTTOMRIGHT", -2, 2)
  b.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  b.slotKey = key
  b:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    if self.itemId then
      BiZ.ShowTooltip(self, self.itemId, nil, self.place)
    else
      GameTooltip:AddLine(BiZ.SlotLabel(self.slotKey), 1, 1, 1)
      GameTooltip:AddLine(L.BIZ_NOTHING, 0.6, 0.6, 0.6)
      GameTooltip:Show()
    end
  end)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
  b:SetScript("OnClick", function(self)
    if IsAltKeyDown() and self.place and BiZ.Go(self.place) then return end
    if IsShiftKeyDown() and self.itemId and BiZ.LinkInChat(self.itemId, self.linkName) then return end
    selected = self.slotKey
    refresh()
  end)
  slotBtns[key] = b
  return b
end

-- The 3D model of the player's character. It stands still; drag with the left mouse button to
-- turn it. Everything is optional (a client without PlayerModel just shows the dark panel).
local function buildModel(f, x, y, w, h)
  local back = f:CreateTexture(nil, "BACKGROUND")
  back:SetPoint("TOPLEFT", f, "TOPLEFT", x, -y)
  back:SetSize(w, h)
  back:SetColorTexture(0.03, 0.03, 0.05, 0.9)
  ui.modelBack = back
  local ok, m = pcall(CreateFrame, "PlayerModel", nil, f)
  if not (ok and m) then return end
  m:SetSize(w, h)
  m:SetPoint("TOPLEFT", f, "TOPLEFT", x, -y)
  local facing, dragX = 0, nil
  local function face(v)
    if m.SetFacing then m:SetFacing(v) elseif m.SetRotation then m:SetRotation(v) end
  end
  local function reset()
    if m.SetUnit then pcall(m.SetUnit, m, "player") end
    if m.SetPortraitZoom then pcall(m.SetPortraitZoom, m, 0) end
    face(facing)
  end
  m:SetScript("OnShow", reset)
  m:EnableMouse(true)
  m:SetScript("OnMouseDown", function() if GetCursorPosition then dragX = GetCursorPosition() end end)
  m:SetScript("OnMouseUp", function() dragX = nil end)
  m:SetScript("OnUpdate", function()
    if dragX and GetCursorPosition then
      local cx = GetCursorPosition()
      facing = facing + (cx - dragX) * 0.012
      dragX = cx
    end
    face(facing)
  end)
  ui.model = m
  ui.modelReset = reset
  reset()
end

-- Called once by MainWindow with the BiS page frame.
function Tab.Build(f)
  page = f
  ui.classBtn = dropButton(f, 124, classMenu)
  ui.classBtn:SetPoint("TOPLEFT", 0, 0)
  ui.specBtn = dropButton(f, 156, specMenu)
  ui.specBtn:SetPoint("LEFT", ui.classBtn, "RIGHT", 6, 0)
  ui.wishBtn = button(f, 110, "", function() view = "wish"; scroll:SetVerticalScroll(0); refresh() end)
  ui.wishBtn:SetPoint("TOPRIGHT", f, "TOPRIGHT", 0, -1)
  ui.setBtn = button(f, 100, L.BIZ_VIEW_SET, function() view = "set"; refresh() end)
  ui.setBtn:SetPoint("RIGHT", ui.wishBtn, "LEFT", -2, 0)

  -- Paper doll: model in the middle, slots in two columns, weapons under it.
  buildModel(f, 50, DOLL_Y, MODEL_W, DOLL_STEP * 7 - 6)
  for i, key in ipairs(LEFT_SLOTS) do buildSlotButton(f, key, 0, DOLL_Y + (i - 1) * DOLL_STEP) end
  for i, key in ipairs(RIGHT_SLOTS) do buildSlotButton(f, key, DOLL_RIGHT_X, DOLL_Y + (i - 1) * DOLL_STEP) end
  local wy = DOLL_Y + 7 * DOLL_STEP + 4
  for i, key in ipairs(WEAPON_SLOTS) do buildSlotButton(f, key, 84 + (i - 1) * 48, wy) end

  -- Source filters (switches) under the doll.
  local fy = wy + SLOT + 12
  for i, t in ipairs(BiZ.Types()) do
    local box = UI.CheckButton(f, L["BIZ_TYPE_" .. t:upper()])
    local col, row = (i - 1) % 2, math.floor((i - 1) / 2)
    box:SetPoint("TOPLEFT", 4 + col * 150, -fy - row * 20)
    box:SetScript("OnClick", function(self) BiZ.SetTypeOn(t, self:GetChecked()); refresh() end)
    typeBoxes[t] = box
  end
  local n = #BiZ.Types()
  ui.known = UI.CheckButton(f, L.BIZ_KNOWN_ONLY)
  ui.known:SetPoint("TOPLEFT", 4 + (n % 2) * 150, -fy - math.floor(n / 2) * 20)
  ui.known:SetScript("OnClick", function(self) BiZ.SetKnownOnly(self:GetChecked()); refresh() end)

  -- Slot panel (right).
  side = CreateFrame("Frame", nil, f)
  side:SetPoint("TOPLEFT", f, "TOPLEFT", 332, -DOLL_Y)
  side:SetSize(318, 440)
  ui.side = side

  ui.summary = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  ui.summary:SetPoint("TOPRIGHT", f, "TOPRIGHT", 0, -26)
  ui.summary:SetJustifyH("RIGHT")
  ui.footer = f:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
  ui.footer:SetPoint("BOTTOMLEFT", f, "BOTTOMLEFT", 332, 6)
  ui.footer:SetWidth(318)
  ui.footer:SetJustifyH("LEFT")

  -- Wishlist view: a scrolling list over the whole page.
  scroll = UI.TryTemplate("ScrollFrame", "R2FBiZScroll", f, "UIPanelScrollFrameTemplate",
    function(s) return s.SetScrollChild ~= nil end) or CreateFrame("ScrollFrame", "R2FBiZScrollPlain", f)
  scroll:SetPoint("TOPLEFT", f, "TOPLEFT", 0, -DOLL_Y)
  scroll:SetSize(CONTENT_W, 440)
  content = CreateFrame("Frame", nil, scroll)
  content:SetSize(CONTENT_W, 10)
  scroll:SetScrollChild(content)
  scroll:EnableMouseWheel(true)
  scroll:SetScript("OnMouseWheel", onWheel)
  scroll:Hide()

  ui.exportBtn = button(f, 110, L.BIZ_EXPORT, function()
    UI.ShowCopy(BiZ.Export(), L.BIZ_EXPORT_HINT)
  end)
  ui.exportBtn:SetPoint("BOTTOMLEFT", f, "BOTTOMLEFT", 0, 4)
  ui.importBtn = button(f, 110, L.BIZ_IMPORT, showImport)
  ui.importBtn:SetPoint("LEFT", ui.exportBtn, "RIGHT", 6, 0)
  ui.exportBtn:Hide()
  ui.importBtn:Hide()
  return f
end

function Tab.Show(which)
  if which == "wish" or which == "set" then view = which end
  R2F.MainWindow.Show("bis")
end
