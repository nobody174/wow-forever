-- Util.lua: small helpers shared by several files (loaded right after Locale.lua).
local _, R2F = ...

R2F.Util = R2F.Util or {}

-- True when the game hands back a "secret" value (restricted in combat / instances): such a value must not be
-- compared, printed or stored.
function R2F.Util.isSecret(v)
  return type(_G.issecretvalue) == "function" and _G.issecretvalue(v) == true
end
