-- UI/BiZ.lua: the BiS tab of the main window, "Mr.BiZ". Logic in BiZ.lua.
--
--   [Class v] [Spec v]                       [Best in slot] [Wishlist (n)]
--   source filters (check boxes, two rows) + Known sources only
--   scrolling list:
--     Best in slot: one row per slot (slot, icon, name in its quality colour, source,
--       score, confidence, wishlist box). Click the name: the next best picks open under
--       it (#2, #3 with how far behind they score). Hover any item: the game's tooltip
--       plus its rank. Shift-click: link in chat. Box ticked = on the wishlist.
--     Wishlist: grouped by where you get the items (a dungeon, a profession, a vendor),
--       biggest group first; Export / Import share the list with the site (R2FW1:).
--   footer: level, data source and build (Best in slot) or Export / Import (Wishlist).
-- Class / spec menus use UI.ContextMenu (no UIDropDownMenu: taint).
-- Everything is redrawn from the data on each refresh (17 slots, a few extra lines); the
-- widgets are pooled per kind.

local _, R2F = ...
local L = R2F.L
local UI = R2F.UI
local BiZ = R2F.BiZ

local Tab = {}
R2F.BiZTab = Tab

local page, scroll, content
local ui = {}
local typeBoxes = {}
local view = "set"            -- "set" | "wish"
local open = {}               -- "<spec>|<slot>" -> true while expanded

local CONTENT_W = 440
local CONF_COLOR = {
  seen = "|cff7fd6a4", client = "|cff8db7ee", classic = "|cffe0be77", clue = "|cffd9a1e0", unknown = "|cffb5b1a6",
}

local function visible() return page ~= nil and page:IsVisible() end

-- ---------------------------------------------------------------------------
-- Pools (one per widget kind; `used` counts what this layout pass took)
-- ---------------------------------------------------------------------------

local pools = {}
local function pool(kind, make)
  local p = pools[kind]
  if not p then p = { list = {}, used = 0, make = make }; pools[kind] = p end
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
    local fs = content:CreateFontString(nil, "ARTWORK", font)
    fs:SetJustifyH("LEFT")
    fs:SetWordWrap(false)
    return fs
  end)
end

local function icon()
  return pool("icon", function()
    local t = content:CreateTexture(nil, "ARTWORK")
    t:SetSize(22, 22)
    return t
  end)
end

-- An item name: hover = tooltip, click = onClick (expand), shift-click = chat link.
local function itemButton()
  return pool("item", function()
    local b = CreateFrame("Button", nil, content)
    b:SetHeight(18)
    b.fs = b:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    b.fs:SetAllPoints(b)
    b.fs:SetJustifyH("LEFT")
    b.fs:SetWordWrap(false)
    b:SetHighlightTexture("Interface\\QuestFrame\\UI-QuestTitleHighlight", "ADD")
    b:SetScript("OnEnter", function(self)
      if self.itemId then BiZ.ShowTooltip(self, self.itemId, self.rankLine) end
    end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    b:SetScript("OnClick", function(self)
      if IsShiftKeyDown() and self.itemId and BiZ.LinkInChat(self.itemId) then return end
      if self.onClick then self.onClick() end
    end)
    return b
  end)
end

local function wishBox()
  return pool("wish", function()
    local c = UI.CheckButton(content, "")
    c:SetSize(20, 20)
    c:SetHitRectInsets(0, 0, 0, 0)
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

local function placeItem(x, y, w, id, name, rankLine, onClick)
  local ic = icon()
  ic:SetPoint("TOPLEFT", content, "TOPLEFT", x, -y)
  ic:SetTexture(BiZ.Icon(id) or UI.FALLBACK_ICON)
  local b = itemButton()
  b:SetPoint("TOPLEFT", content, "TOPLEFT", x + 22, -y - 1)
  b:SetWidth(w)
  b.itemId, b.rankLine, b.onClick = id, rankLine, onClick
  b.fs:SetText(BiZ.ColoredName(id, name))
  return b
end

local function placeWish(x, y, id, specId, slot)
  local c = wishBox()
  c:SetPoint("TOPLEFT", content, "TOPLEFT", x, -y + 1)
  c.itemId, c.specId, c.slot = id, specId, slot
  c:SetChecked(BiZ.IsWished(id))
  return c
end

local function line(font, x, y, w, str)
  local fs = text(font)
  fs:SetPoint("TOPLEFT", content, "TOPLEFT", x, -y)
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

local function layoutSet()
  local specId = BiZ.SpecId()
  local sp = BiZ.Spec(specId)
  local y = 0
  local shown, hidden = 0, 0
  for _, sl in ipairs(sp.slots) do
    local key = specId .. "|" .. sl.slot
    line("GameFontNormalSmall", 0, y + 3, 64, BiZ.SlotLabel(sl.slot))
    local b = sl.best
    if not b then
      line("GameFontDisableSmall", 88, y, 300, L.BIZ_NOTHING)
      line("GameFontDisableSmall", 88, y + 14, 320, (sl.note:gsub("^%l", string.upper)))
    else
      local nxt = sl.next or {}
      local all = { b }
      for _, n in ipairs(nxt) do all[#all + 1] = n end
      -- The row shows the best, or when the filters hide it, the next rank they let through (a stand-in).
      local pick
      for i, it in ipairs(all) do
        if BiZ.Passes(it) then pick = i; break end
      end
      local gapOf = function(rank) return rank == 1 and BiZ.IsTheBizz(sl) and -nxt[1].delta or nil end
      local isOpen = open[key]
      local toggle = function()
        open[key] = (not open[key]) or nil
        Tab.Refresh()
      end
      if pick then
        shown = shown + 1
        local p, gap = all[pick], gapOf(pick)
        local fnote = BiZ.FactionNote(p)
        local nb = placeItem(66, y, 226, p.id, p.name, rankLine(sp.name, pick, b.score, p.delta, gap, p.label, p.via), toggle)
        if fnote then nb.fs:SetText(BiZ.ColoredName(p.id, p.name) .. " |cffe86a5a(" .. fnote .. ")|r") end
        local prefix
        if gap then
          prefix = "|cffffd100" .. L.BIZ_THE_BIZZ .. "|r · "
        elseif pick == 1 then
          prefix = "|cffffd100" .. BiZ.RankName(1) .. "|r · "
        else
          prefix = "|cffd9d4c3" .. L.BIZ_STANDIN:format(BiZ.RankName(pick)) .. "|r · "
        end
        line("GameFontDisableSmall", 88, y + 19, 228, prefix .. (p.label or L.BIZ_TYPE_UNKNOWN))
        local sc = line("GameFontHighlightSmall", 318, y + 3, 40,
          pick == 1 and tostring(b.score) or ("|cffe39a79" .. (p.delta == 0 and "=" or (tostring(p.delta) .. "%")) .. "|r"))
        sc:SetJustifyH("RIGHT")
        local conf = p.conf or "unknown"
        line("GameFontHighlightSmall", 366, y + 3, 46, (CONF_COLOR[conf] or "") .. L["BIZ_CONF_" .. conf:upper()] .. "|r")
        placeWish(414, y, p.id, specId, sl.slot)
      else
        hidden = hidden + 1
        local hb = itemButton()
        hb:SetPoint("TOPLEFT", content, "TOPLEFT", 88, -y - 1)
        hb:SetWidth(226)
        hb.itemId, hb.rankLine, hb.onClick = nil, nil, toggle
        hb.fs:SetText("|cff808080" .. L.BIZ_HIDDEN .. "|r")
        line("GameFontDisableSmall", 88, y + 19, 228, L.BIZ_HIDDEN_HINT:format(L["BIZ_TYPE_" .. b.type:upper()]))
      end
      y = y + 38
      if isOpen then
        -- Every other rank, each with where it comes from (greyed when the filters hide it).
        for rank, it in ipairs(all) do
          if rank ~= pick then
            local gap = gapOf(rank)
            line("GameFontNormalSmall", 70, y + 3, 20, "#" .. rank)
            placeItem(88, y, 210, it.id, it.name, rankLine(sp.name, rank, b.score, it.delta, gap, it.label, it.via))
            local src = (it.label or L.BIZ_TYPE_UNKNOWN)
            line("GameFontDisableSmall", 88, y + 19, 214, BiZ.Passes(it) and src or ("|cff707070" .. src .. "|r"))
            local rn = gap and L.BIZ_THE_BIZZ or BiZ.RankName(rank)
            local d = (it.delta == 0 and L.BIZ_SAME) or (it.delta and (it.delta .. "%")) or ""
            local dl = line("GameFontHighlightSmall", 302, y + 3, 108,
              "|cffffd100" .. rn .. "|r" .. (d ~= "" and ("  |cffe39a79" .. d .. "|r") or ""))
            dl:SetJustifyH("RIGHT")
            placeWish(414, y, it.id, specId, sl.slot)
            y = y + 38
          end
        end
        local ease = (b.ease and b.ease ~= "") and (" · " .. b.ease) or ""
        local facts = line("GameFontHighlightSmall", 88, y + 2, 320, b.name .. ": " .. b.stats .. ease)
        facts:SetTextColor(0.7, 0.7, 0.7)
        y = y + 18
        if #nxt == 0 then
          line("GameFontDisableSmall", 88, y, 320, L.BIZ_NO_MORE)
          y = y + 14
        end
        y = y + 6
      end
    end
    if not b then y = y + 38 end
  end
  ui.footer:SetText(L.BIZ_FOOTER:format(R2F.BiZData.level, R2F.BiZData.source, sp.build))
  ui.summary:SetText(hidden > 0 and L.BIZ_SUMMARY_HIDDEN:format(shown, hidden) or L.BIZ_SUMMARY:format(shown))
  return y
end

-- ---------------------------------------------------------------------------
-- Wishlist view
-- ---------------------------------------------------------------------------

local function layoutWish()
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
    local cnt = line("GameFontHighlightSmall", 340, y + 2, 96, fmt:format(#g.items))
    cnt:SetJustifyH("RIGHT")
    y = y + 20
    for _, it in ipairs(g.items) do
      local sp = it.spec and BiZ.Spec(it.spec)
      placeItem(8, y, 230, it.id, it.name, sp and L.BIZ_TIP_WISHED:format(sp.name, BiZ.SlotLabel(it.slot or "")) or nil)
      local detail = BiZ.SlotLabel(it.slot or "") .. (sp and (" · " .. sp.name) or "")
      line("GameFontDisableSmall", 262, y + 3, 148, detail)
      placeWish(414, y, it.id, it.spec, it.slot)
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
  for _, w in pairs(typeBoxes) do w:SetShown(view == "set") end
  ui.known:SetShown(view == "set")
  ui.footer:SetShown(view == "set")
  ui.exportBtn:SetShown(view == "wish")
  ui.importBtn:SetShown(view == "wish")

  resetPools()
  local h = view == "set" and layoutSet() or layoutWish()
  hideUnused()
  content:SetHeight(math.max(h, 1))
  ui.contentHeight = h
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

-- Called once by MainWindow with the BiS page frame.
function Tab.Build(f)
  page = f
  ui.classBtn = dropButton(f, 124, classMenu)
  ui.classBtn:SetPoint("TOPLEFT", 28, -54)
  ui.specBtn = dropButton(f, 156, specMenu)
  ui.specBtn:SetPoint("LEFT", ui.classBtn, "RIGHT", 6, 0)
  ui.setBtn = button(f, 96, L.BIZ_VIEW_SET, function() view = "set"; scroll:SetVerticalScroll(0); refresh() end)
  ui.setBtn:SetPoint("TOPLEFT", 324, -54)
  ui.wishBtn = button(f, 96, "", function() view = "wish"; scroll:SetVerticalScroll(0); refresh() end)
  ui.wishBtn:SetPoint("LEFT", ui.setBtn, "RIGHT", 2, 0)

  for i, t in ipairs(BiZ.Types()) do
    local box = UI.CheckButton(f, L["BIZ_TYPE_" .. t:upper()])
    local col, row = (i - 1) % 4, math.floor((i - 1) / 4)
    box:SetPoint("TOPLEFT", 26 + col * 122, -82 - row * 22)
    box:SetScript("OnClick", function(self) BiZ.SetTypeOn(t, self:GetChecked()); refresh() end)
    typeBoxes[t] = box
  end
  local n = #BiZ.Types()
  ui.known = UI.CheckButton(f, L.BIZ_KNOWN_ONLY)
  ui.known:SetPoint("TOPLEFT", 26 + (n % 4) * 122, -82 - math.floor(n / 4) * 22)
  ui.known:SetScript("OnClick", function(self) BiZ.SetKnownOnly(self:GetChecked()); refresh() end)

  ui.summary = f:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
  ui.summary:SetPoint("TOPRIGHT", -30, -132)
  ui.summary:SetJustifyH("RIGHT")

  scroll = UI.TryTemplate("ScrollFrame", "R2FBiZScroll", f, "UIPanelScrollFrameTemplate",
    function(s) return s.SetScrollChild ~= nil end) or CreateFrame("ScrollFrame", "R2FBiZScrollPlain", f)
  scroll:SetPoint("TOPLEFT", 22, -146)
  scroll:SetSize(CONTENT_W + 8, 286)
  content = CreateFrame("Frame", nil, scroll)
  content:SetSize(CONTENT_W, 10)
  scroll:SetScrollChild(content)
  scroll:EnableMouseWheel(true)
  scroll:SetScript("OnMouseWheel", onWheel)

  ui.footer = f:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
  ui.footer:SetPoint("BOTTOMLEFT", 28, 34)
  ui.footer:SetWidth(480)
  ui.footer:SetJustifyH("LEFT")
  ui.exportBtn = button(f, 110, L.BIZ_EXPORT, function()
    UI.ShowCopy(BiZ.Export(), L.BIZ_EXPORT_HINT)
  end)
  ui.exportBtn:SetPoint("BOTTOMLEFT", 28, 28)
  ui.importBtn = button(f, 110, L.BIZ_IMPORT, showImport)
  ui.importBtn:SetPoint("LEFT", ui.exportBtn, "RIGHT", 6, 0)
  return f
end

function Tab.Show(which)
  if which == "wish" or which == "set" then view = which end
  R2F.MainWindow.Show("bis")
end
