-- Progress.lua: the plan progress string, to share with a duo partner and the site's Launch Plan "Duo view".
--
-- Format (the site's progresscodec.js writes and reads the same):
--   R2FP1:<base64( "v=1\n" .. plan .. \30 .. level .. \30 .. ids joined by \31 )>
--   plan  = plan id ("skyborne:HUNTER", "hunter"), level = 0 (unknown) to 60, ids = the ticked launch-plan step ids.
-- \30 / \31 are the ASCII record / unit separators, like Import.lua's R2F1. Only these three things are in the
-- string: no character name, realm or guild (same rule as the route log). The label shown for a partner is typed
-- by whoever reads the string.
-- The R2FP1: prefix is the format version: R2FP2 and higher are rejected with "update the addon", never misread.
-- Total length is capped at 2 KB. Step ids this addon does not know are ignored when comparing, not an error.
--
-- Logic only, read-only game-wise: nothing here writes to the game, so it works in combat.

local _, R2F = ...
local L = R2F.L

local Progress = {}
R2F.Progress = Progress

local PREFIX = "R2FP1:"
local MAX_LEN = 2048
local MAX_ID = 40
local RS, US = "\30", "\31"
Progress.MAX_LEN = MAX_LEN

local function plan() return R2F.Plan end

-- Every step id of every phase in PlanData, in plan order: { ids = { id, ... }, known = { id = true } }.
local function knownIds()
  local ids, known = {}, {}
  for _, ph in ipairs(R2F.PlanData.phases) do
    for _, item in ipairs(ph.items) do
      if not known[item.id] then
        known[item.id] = true
        ids[#ids + 1] = item.id
      end
    end
  end
  return ids, known
end

-- Encode the ticks. doneSet = { stepId = true }. Returns the string, or nil and a message.
function Progress.Encode(planId, level, doneSet)
  if not plan().Parse(planId) then return nil, L.PROGRESS_BAD_PLAN end
  level = math.floor(tonumber(level) or 0)
  if level < 0 or level > 60 then level = 0 end
  local ids = {}
  for _, id in ipairs((knownIds())) do
    if doneSet[id] then ids[#ids + 1] = id end
  end
  local text = "v=1\n" .. planId .. RS .. level .. RS .. table.concat(ids, US)
  local out = PREFIX .. R2F.Base64.Encode(text)
  if #out > MAX_LEN then return nil, L.PROGRESS_TOO_LONG end
  return out
end

-- Parse a pasted string. Returns { plan =, level =, done = { id = true } } or nil and a message.
function Progress.Parse(input)
  if type(input) ~= "string" then return nil, L.PROGRESS_NOT end
  local s = input:gsub("%s", "")
  if s == "" then return nil, L.PROGRESS_NOT end
  if #s > MAX_LEN then return nil, L.PROGRESS_TOO_LONG end
  local ver = s:match("^R2FP(%d+):")
  if not ver then return nil, L.PROGRESS_NOT end
  if tonumber(ver) ~= 1 then return nil, L.PROGRESS_NEWER end
  local text = R2F.Base64.Decode(s:sub(#PREFIX + 1))
  if not text then return nil, L.PROGRESS_NOT end
  local body = text:match("^v=1\n(.*)$")
  if not body then return nil, L.PROGRESS_NOT end
  local planId, levelText, idText = body:match("^([^\30]*)\30([^\30]*)\30([^\30]*)$")
  if not planId then return nil, L.PROGRESS_NOT end
  local level = tonumber(levelText)
  if not level or level ~= math.floor(level) or level < 0 or level > 60 then return nil, L.PROGRESS_NOT end
  if not plan().Parse(planId) then return nil, L.PROGRESS_BAD_PLAN end
  local done = {}
  local start = 1
  while idText ~= "" do
    local i = idText:find(US, start, true)
    local id = idText:sub(start, (i or #idText + 1) - 1)
    if id ~= "" and #id <= MAX_ID and id:match("^[%w_%-]+$") then done[id] = true end
    if not i then break end
    start = i + 1
  end
  return { plan = planId, level = level, done = done }
end

-- My ticks as a set: R2FCharDB.plan.done restricted to known step ids.
function Progress.MyDone()
  local _, known = knownIds()
  local out = {}
  for id in pairs(R2F.Library.cdb.plan.done) do
    if known[id] then out[id] = true end
  end
  return out
end

-- The export string for this character: the selected plan, the current level and my ticks.
function Progress.Export()
  local level = UnitLevel and UnitLevel("player") or 0
  return Progress.Encode(plan().Selected() or plan().DEFAULT, level, Progress.MyDone())
end

-- Compare my ticks with a parsed partner string, over the steps of my selected plan:
-- { levelGap =, both =, mine = n, theirs = n, onlyMine = { step, ... }, onlyTheirs = { step, ... } }
-- levelGap = my level minus theirs (nil when either is unknown).
function Progress.Compare(theirs, myLevel)
  local mine = Progress.MyDone()
  local out = { both = 0, mine = 0, theirs = 0, onlyMine = {}, onlyTheirs = {} }
  myLevel = tonumber(myLevel) or 0
  if myLevel > 0 and theirs.level > 0 then out.levelGap = myLevel - theirs.level end
  for _, step in ipairs(plan().Steps(plan().Selected() or plan().DEFAULT)) do
    local a, b = mine[step.id], theirs.done[step.id]
    if a then out.mine = out.mine + 1 end
    if b then out.theirs = out.theirs + 1 end
    if a and b then out.both = out.both + 1
    elseif a then out.onlyMine[#out.onlyMine + 1] = step
    elseif b then out.onlyTheirs[#out.onlyTheirs + 1] = step end
  end
  return out
end
