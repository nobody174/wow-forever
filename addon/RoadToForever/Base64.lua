-- Base64.lua: decode only (ADDON_PLAN.md 6.1, 7).
--
-- The site encodes with btoa(unescape(encodeURIComponent(text))): the text is
-- turned into its UTF-8 bytes first, then standard base64 (A-Z a-z 0-9 + /,
-- "=" padding). Decoding back to bytes therefore gives the original UTF-8
-- string as-is; Lua strings are byte strings and WoW font strings render
-- UTF-8, so no further conversion is needed.
--
-- WoW runs Lua 5.1: no bitwise operators, so the 6-bit groups are combined
-- with plain arithmetic (every value stays far below 2^53, so it is exact).

local _, R2F = ...

local byte, char, concat, floor = string.byte, string.char, table.concat, math.floor

local ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
local VALUE = {}
for i = 1, 64 do VALUE[byte(ALPHABET, i)] = i - 1 end

local Base64 = {}
R2F.Base64 = Base64

-- Returns the decoded string, or nil if the input isn't valid base64.
-- Whitespace anywhere is ignored (chat/clipboard can add line breaks).
function Base64.Decode(input)
  if type(input) ~= "string" then return nil end
  local s = input:gsub("%s", "")
  -- Padding may only appear at the end, at most two characters.
  local body, pad = s:match("^([^=]*)(=*)$")
  if not body or #pad > 2 then return nil end
  if (#body + #pad) % 4 ~= 0 and #pad > 0 then return nil end
  if #body % 4 == 1 then return nil end -- 6 lone bits can't form a byte

  local out, n = {}, 0
  for i = 1, #body, 4 do
    local a, b, c, d = byte(body, i, i + 3)
    local va, vb = VALUE[a], VALUE[b]
    local vc, vd = c and VALUE[c], d and VALUE[d]
    if not va or not vb or (c and not vc) or (d and not vd) then return nil end
    local bits = va * 262144 + vb * 4096 + (vc or 0) * 64 + (vd or 0)
    n = n + 1
    if vd then
      out[n] = char(floor(bits / 65536), floor(bits / 256) % 256, bits % 256)
    elseif vc then
      out[n] = char(floor(bits / 65536), floor(bits / 256) % 256)
    else
      out[n] = char(floor(bits / 65536))
    end
  end
  return concat(out)
end
