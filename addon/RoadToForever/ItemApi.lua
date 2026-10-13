-- ItemApi.lua: item lookups that work on every client.
--
-- WoW Forever runs the modern engine: the global GetItemInfo / GetItemInfoInstant are gone there
-- (Blizzard's own UI calls C_Item.GetItemInfo 94 times and the bare global never), while the Classic
-- clients only have the globals. So the C_Item function is used when it exists, the global otherwise.
-- Returns are the same as the game's: GetItemInfo -> name, link, quality, itemLevel, minLevel, type,
-- subType, stackCount, equipLoc, icon, sellPrice, classID, subClassID ...; GetItemInfoInstant ->
-- itemID, type, subType, equipLoc, icon, classID, subClassID. Nothing here writes to the game.

local _, R2F = ...

local Item = {}
R2F.Item = Item

function Item.Info(item)
  if item == nil then return nil end
  local fn = (C_Item and C_Item.GetItemInfo) or _G.GetItemInfo
  if fn then return fn(item) end
  return nil
end

function Item.Instant(item)
  if item == nil then return nil end
  local fn = (C_Item and C_Item.GetItemInfoInstant) or _G.GetItemInfoInstant
  if fn then return fn(item) end
  return nil
end

-- True when this client can answer item lookups at all.
function Item.Available()
  return ((C_Item and C_Item.GetItemInfo) or _G.GetItemInfo) ~= nil
end
