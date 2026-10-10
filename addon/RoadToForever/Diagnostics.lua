-- Diagnostics.lua: small read-only probes for questions about this client (v0.26.0).
--
-- /r2f auras: can an addon read buffs here, on you and on your party, in or out of combat? The
-- game's API files mark aura queries as restricted ("secret" values: C_Secrets.ShouldAurasBeSecret,
-- RequiresUnitAuraAccess), and the owner's old ForeverPlus notes say they were refused in combat.
-- A reminder for buffs the group can give you (ADDON_PLAN 17.1 step 5) only makes sense if this
-- says yes outside combat, so the answer is measured before anything is designed. Prints one block
-- of chat lines; paste them to us.

local _, R2F = ...
local L = R2F.L

local Diag = {}
R2F.Diag = Diag

local function yn(v)
  if v == nil then return "-" end
  return v and "yes" or "no"
end

local function isSecret(v)
  return type(_G.issecretvalue) == "function" and _G.issecretvalue(v) == true
end

-- How many helpful auras can be read on `unit`, and how many of those have a readable spell id.
local function probe(unit)
  if not (UnitExists and UnitExists(unit)) then return nil end
  local ns = _G.C_UnitAuras
  if not (ns and ns.GetUnitAuras) then return { api = false } end
  local ok, list = pcall(ns.GetUnitAuras, unit, "HELPFUL")
  if not ok then return { api = true, error = tostring(list) } end
  if type(list) ~= "table" then return { api = true, count = 0, readable = 0, secret = true } end
  local readable = 0
  for _, aura in ipairs(list) do
    if type(aura) == "table" and aura.spellId ~= nil and not isSecret(aura.spellId) then readable = readable + 1 end
  end
  return { api = true, count = #list, readable = readable }
end

function Diag.Auras()
  local C = _G.C_Secrets
  R2F.Print(L.DIAG_AURAS_HEAD:format(
    yn(C and C.HasSecretRestrictions and C.HasSecretRestrictions()),
    yn(C and C.ShouldAurasBeSecret and C.ShouldAurasBeSecret()),
    yn(InCombatLockdown()), yn(IsInInstance and (IsInInstance()))))
  for _, unit in ipairs({ "player", "party1", "party2", "party3", "party4", "target" }) do
    local r = probe(unit)
    if r == nil then
      -- unit not present: say nothing
    elseif r.api == false then
      R2F.Print(L.DIAG_AURAS_NOAPI)
      return
    elseif r.error then
      R2F.Print(L.DIAG_AURAS_ERR:format(unit, r.error))
    elseif r.secret then
      R2F.Print(L.DIAG_AURAS_SECRET:format(unit))
    else
      R2F.Print(L.DIAG_AURAS_LINE:format(unit, r.count, r.readable))
    end
  end
end
