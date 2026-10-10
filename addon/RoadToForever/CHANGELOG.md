# Road to Forever (addon) changelog

Version history of the in-game addon itself. The site's history is in the
repo's root `CHANGELOG.md`.

## 0.28.3 (2026-10-10): the mail list uses the full in-game name

- **Fix:** the mail button filled in "Venom-ClassicBetaPvE2"; this client names characters "Venom Oathbreaker"
  (UnitName's second value is a surname, found with `/r2f who`). Each character now remembers that full name and the
  list fills it in. **Log in once on each alt with this version** so it is remembered; alts not seen again keep the old form.

## 0.28.2 (2026-10-10): /r2f who

- **`/r2f who`** lists every way the client names your character (UnitName, UnitFullName, PvP name, realm names,
  the character window title...). Used to find where a two-part name such as "Venom Oathbreaker" comes from, so the
  mail list can fill in the right name for every alt. Run it on the paladin and send us the lines.

## 0.28.1 (2026-10-10): the active Gameplay page stands out

- Owner: the page you are on looked greyed out (the button was disabled), which reads as "not learned / not working".
  It now stays enabled, with gold text, a gold bar under it and the button kept lit; the other pages are normal white.

## 0.28.0 (2026-10-10): Gameplay tab redesign, plain names, the real ability name in the alert

**Never run in game yet: TESTING.md 35.**

- **The alert says which ability.** The game's own announcement hides the spell name from addons, but the
  "spell glows on your bar" event (`SPELL_ACTIVATION_OVERLAY_GLOW_SHOW`) carries a spell id; the name is read from
  that (a glow from the last second, or one that comes just after the announcement, fills it in). If your client
  sends no glow for that ability the alert still says "Ability ready". **`/r2f reactlog`** prints the last
  announcements it saw (paste it to us if the name stays missing).
- **Gameplay tab redesign (UX pass, ADDON_PLAN 18).** Four small pages picked with buttons along the top instead of
  one long scrolling list: **Quests**, **Vendors & loot**, **Screen & chat**, **Alerts**. The page you used last is
  remembered. Each option has a plain name and a grey one-line explanation under it (the tooltip keeps the full text).
- **Plain names** everywhere on the tab: "Auto-accept quests", "Auto turn-in quests", "Skip the NPC chat before
  shops", "Auto-repair at vendors", "Auto-sell grey items", "Fast looting", "Show free bag slots", "Hide red error
  messages", "Always show XP numbers", "Decline duel requests", "Show an 'ability ready' alert", "Lock the alert's
  position", "Hide Blizzard's alert text"... and the class icons: "Warrior stance icon", "Hunter ammo counter",
  "Tracking reminder" with "Show the icon / Lock its position / Size".
- **Fix:** the main window reopened on Home after every login if you had last used Plan, Gameplay or Settings (the
  saved-tab check only knew the first three tabs).

## 0.27.2 (2026-10-10): "Hide the game's own reactive text" needs a /reload

- Owner test of 0.27.1: our `Ability ready` alert showed where he put it, but the game's own "<Revenge>" text was
  still there. The game's combat text reads its "Reactive ability alerts" setting (`floatingCombatTextReactives_v2`) when
  it loads, and when its own options change it, not when another addon changes the setting. So the hide box takes
  effect after a `/reload`; the addon now says so in chat. (Making the game re-read it now would mean calling its code
  from ours, which is what tainted it in 0.27.0.) There is no Edit Mode setting for this text: the game's code has none.
- The alert says "Ability ready" instead of the spell name: the announcement's spell name is a hidden ("secret") value on
  this client.

## 0.27.1 (2026-10-10): URGENT fix for 0.27.0 (Lua errors in fights), Gameplay tab scrolls

- **0.27.0 broke the game's floating combat text** ("attempt to perform arithmetic on field 'startY' (a secret
  number value, while execution tainted by 'RoadToForever')", 96 errors in one fight). Cause: it wrote into
  Blizzard's `CombatText.textLocations` table to move the "<Revenge>" text. Writing into a game table taints it, and
  on this client tainted values refuse arithmetic. **That code is gone.** After updating, `/reload` once (the old
  tainted table lives until the UI reloads).
- The replacement never touches the game's data: **Reactive alert (own text, movable)** listens for the game's own
  announcement (`COMBAT_TEXT_UPDATE` / `SPELL_ACTIVE`) and shows `<Revenge>` in OUR text at a marker you drag
  (**Lock reactive alert position** hides the marker); **Hide the game's own reactive text** switches off the game's
  setting `floatingCombatTextReactives_v2` (through QuickSettings; your value is put back when unticked). If the event
  text is a secret value the alert says "Ability ready". All three are OFF by default.
- A test now fails if any file writes into `CombatText` / `textLocations`.
- The Gameplay tab **scrolls** (mouse wheel): with 17 features the lower boxes ran off the bottom of the window.

## 0.27.0 (2026-10-10): move the floating combat text where you want it

**Never run in game yet: TESTING.md 33 item 2 (rewritten).**

- The fixed "Raise floating combat text" box (0.25.0) is replaced by **Move floating combat text** (Gameplay >
  Screen): a marker with the Revenge icon appears on screen; drag it where the "<Revenge>" alert (and damage
  numbers) should start. The game's whole scroll path (start and end) is shifted by the marker's offset from the
  screen centre; the shift is re-applied after every relayout and taken out when the box is unticked.
  **Lock floating combat text position** hides the marker and keeps the spot. Needs floating combat text switched
  on in the game's options (the box is greyed out until the game has loaded it).
- Saved in `R2FDB.fct` (x, y, lock); applied at login without opening the tab.

## 0.26.1 (2026-10-10): two fixes from the 0.26.0 test

- **Tracking reminder:** it stayed up, grey, while a tracking was on (unlocked). It is now only shown while a tracking
  is NEEDED (none of the ticked ones active) and gone otherwise. To place it, switch your tracking off: it appears and
  can be dragged.
- **Quest log track-all box:** it sat on top of the game's collapse / expand button. It is now to the LEFT of that
  button (`header.CollapseButton`).
- Probe result for the buff reminder (owner, out of combat, in a party of two): `/r2f auras` reads 1 buff on the player
  and 6 on party1, all with readable spell ids; secret restrictions "yes", auras secret "no" outside combat.

## 0.26.0 (2026-10-10): shop-line skipper, tracking reminder, aura probe

**Never run in game yet: TESTING.md 34.**

- **Skip the shop line at NPCs** (Gameplay tab, Automatic; OFF by default). Many NPCs open a gossip window with one
  line before their shop. This picks that line, and only when: it is the ONLY option, it is Available, the NPC offers
  no quests, and its ICON is one of the game's shop / trainer / bank / flight-map / auction-house icons (file ids
  132060, 132058, 132050, 132057, 528409, read from the game files; this build's gossip options have no "type").
  The innkeeper's "make this your home" and plain chat lines are never picked. Shift pauses it.
  **`/r2f gossip`** prints the open NPC window's options with their icon ids, so the whitelist can grow from real data.
- **Minimap tracking reminder** (Gameplay tab, Reminders column; any class that has Find Minerals / Herbs / Treasure):
  the framed icon shows while you know at least one ticked tracking type and none of them is active; hidden otherwise
  (when locked). Three boxes choose which types to remind about. Draggable, lockable, resizable like the other
  reminders. No aura reading, works in combat. (Part of the "buff reminders" ForeverPlus feature the owner used.)
- **`/r2f auras`** (probe): says whether this client lets an addon read buffs on you and your party, in and out of
  combat (the game's API files mark aura reads as restricted "secret" values). The group-buff reminder waits for
  its answer.

## 0.25.0 (2026-10-10): quest-log track-all boxes, raise the "<Revenge>" text

**Never run in game yet: TESTING.md 33.** Both OFF until ticked on the Gameplay tab (Screen).

- **Quest log: track-all box per zone.** A small check box on every zone heading in the quest log: tick it to
  track every quest under that heading, untick to untrack them all. Built on `C_QuestLog.AddQuestWatch` /
  `RemoveQuestWatch` (the game's own way is the right-click menu on the heading). Frame names read in the
  game's UI code (`QuestScrollFrame.headerFramePool`, `questLogIndex`); where the box lands on the heading
  is unverified.
- **Raise floating combat text.** The "<Revenge>" alert the owner sees at the bottom middle of the screen is the
  game's floating combat text ("Reactive ability alerts" setting, CVar `floatingCombatTextReactives_v2`; found in
  `Blizzard_CombatText`). It scrolls from y 384 down to 159 when scrolling is set to "down". This box raises that
  whole scroll path by 200 (also damage numbers). Needs floating combat text switched on in the game's options.

## 0.24.1 (2026-10-10): Hunter ammo counts the real ammunition

- **Bug found by an owner test of the 178 on the backpack:** this client has no ammo slot
  (`GetInventoryItemID("player", 0)` is 0 and `GetInventoryItemCount("player", 0)` is 1), so the Hunter ammo
  reminder from 0.17.0 would have shown a wrong "1" (red) for every Hunter. It now counts the ammunition the
  equipped ranged weapon fires, over all bags: arrows for a bow or crossbow, bullets for a gun (item class 6,
  weapon in slot 18). No ranged weapon (or a thrown weapon) = nothing to count: the icon stays hidden, grey with
  "-" while unlocked. A ranged weapon and no ammunition = red 0.
- The "178" on the backpack button is still unexplained (it is the game's own `Count` text on the backpack
  button; it is not the ammo slot, not the item total, not the slot total).

## 0.24.0 (2026-10-09): copy chat (replaces Prat 3.0 for copying)

**Never run in game yet: TESTING.md 32.**

- **`/r2f copychat`** opens a window with the newest 200 lines of your main chat window in a box you can
  select and copy (Ctrl+A, Ctrl+C); **`/r2f copychat 3`** does it for chat window 3. Oldest line first.
  A **Plain text** tick (on by default) strips colour codes, links and icons so pasted text is readable.
- **Copy chat button** (Gameplay tab, Screen, off by default): a small C in the corner of every chat window;
  click it for that window's text.
- Read-only: only the chat windows' stored lines are read. Written from scratch (Prat 3.0 is GPLv3, none of
  its code is used).
- Backpack: still open whether the game's own "178" on the backpack button should be hidden while our free-slot
  number is on (it is not the item total or the slot total).

## 0.23.2 (2026-10-09): mail uses the full character name

- Owner test of 0.22.0: the mail button filled in a bare name ("Alice") and the mail didn't go: on this
  client a recipient needs the full name, "Name-Realm". The button now fills in `Name-Realm` (the game's
  normalised realm name, else the realm name without spaces).

## 0.23.1 (2026-10-09): single quest rewards are taken

- Owner test of 0.23.0: accept and hand in work, but a quest with exactly ONE reward stopped at the reward
  window. With one reward there is nothing to choose, so it is now turned in; with two or more choices the
  window still stays open and the addon never picks.

## 0.23.0 (2026-10-09): Gameplay step 3 (quest automation)

**Never run in game yet: TESTING.md 31.** All three are OFF until ticked on the Gameplay tab. Hold
**Shift** to pause the two that act.

- **Accept quests:** accepts a quest when its window opens and picks the next quest a quest giver offers
  (gossip list or quest greeting). A quest the game accepted by itself is left alone.
- **Hand in quests:** completes finished quests at the quest giver. **It never picks a reward**: the
  quest is only turned in when it has no reward choice at all; with one or more choices the window
  stays open for you. With both boxes on, a finished quest is handed in before a new one is picked.
- **Show reward sell prices:** writes what each reward choice sells for to a vendor in the corner of its
  button; the best is green (not marked when there is only one choice).
- The quest APIs on this client are partly unverified, so the modern gossip functions are tried first with
  the classic ones as the fallback, and anything missing does nothing.
- Free bag slots: the number now sits at the TOP of the backpack button, so it no longer lands on top of
  the game's own count at the bottom.

## 0.22.0 (2026-10-09): Gameplay step 2 (mail to your characters, free bag slots, fast loot)

**Never run in game yet: TESTING.md 30.** All three are OFF until ticked on the Gameplay tab.

- **Mail: pick your own characters.** A small button after the recipient field in the mail window lists
  your other characters on this realm and faction (class colour, level); click one to fill in the name.
  The addon remembers every character that logs in with it (name, class, level, faction), so log in on
  each once.
- **Free bag slots on the backpack.** The number of free general-purpose bag slots (quivers and ammo pouches
  not counted) on the backpack button; red at 3 or fewer. Greyed out if the client has no such button.
- **Fast loot.** Loots every slot at once when the loot window opens. Only when the game's own auto-loot
  would loot (the auto-loot key flips it). Greed rolling on greens is NOT included.
- Quest log "track all in this zone" is not built yet: it needs the quest log's frame names on this client.

## 0.21.0 (2026-10-09): Gameplay tab, first five features (ADDON_PLAN 17 step 1)

**Never run in game yet: TESTING.md 29.**

- **The Reminders tab is now the Gameplay tab** (Home / Macros / Talents / Plan / Gameplay /
  Settings). `/r2f gameplay` opens it (`/r2f reminders` still works and opens the same tab).
  Left column: **Automatic** and **Screen** features; right column: **Reminders** (your class's
  stance / ammo icons and their options, exactly as before).
- **Everything ships OFF.** One check box per feature; each says in chat what it did.
  - **Repair at vendors:** repairs everything with your own gold when you open a vendor that can
    repair; says the cost; does nothing if you can't afford it.
  - **Sell grey items:** at a vendor, sells grey (poor quality) items that have a vendor price.
    Nothing else is ever sold; says the count and total.
  - **Block duels:** declines every duel request, says who.
  - **Hide red error spam:** hides "Not enough rage", "Ability is not ready yet", "Out of range",
    wrong facing and similar lines above the action bar (matched against the client's own texts).
  - **XP bar text always shown:** uses the game's own setting and puts your old value back when
    you untick it (can't be changed in combat).
- A feature the client can't do is greyed out with a tooltip; an error in one feature is reported
  once and never stops the others.
- Written from scratch; ForeverPlus was only used as a list of what these features do.

## 0.20.1 (2026-10-09): addon list icon

- The addon list in the game's AddOns window showed a "?" icon: the TOC now has
  `## IconTexture` (our logo, `media/logo64`).

## 0.20.0 (2026-10-09): bags rebuilt (Shift+drag), Reload UI in the minimap menu

**Never run in game yet: TESTING.md 24 (rewritten) and 28.**

- **Movable bags didn't work in game** (owner test of 0.19.x, with every other addon off). Cause,
  confirmed in ForeverPlus' BagWindow module: Blizzard puts an invisible button over the whole
  title bar that opens the bag menu when the mouse goes down, so a drag that starts on the title
  never reaches the window. Now **hold Shift and drag** (title or empty background): while Shift is
  held a grip of our own covers the title bar, without Shift the title is the game's again (click
  for its menu). **Movable bags** on, **Lock bags** off. Position still saved per character.
- **No more taint risk:** 0.16.0 called the game's `UpdateContainerFrameAnchors()` when Movable was
  switched off. That runs the game's bag placement in our name and can make the game refuse item use
  ("blocked from an action"; ForeverPlus hit this on 2026-10-04). Switching Movable off now puts each
  window back where the game last placed it, read off the frame.
- Windows anchored to a moved bag that would fall off the screen are hung off the other side.
- `/r2f bags` warns when ForeverPlus (which also moves the bag window) is loaded: use one of the two.
- **Minimap button right-click menu: Reload UI** (last line), instead of typing /reload.

## 0.19.1 (2026-10-09): rank detection from the spellbook, /r2f rankdebug

**Never run in game yet.**

- Owner test of 0.19.0: `/r2f ranks` said "you know no rank of it yet" for Charge on a character
  that has Charge Rank 1 (and `/cast Charge(Rank 1)` works), so the spell-id check missed it:
  `C_Spell.GetSpellInfo("Charge(Rank 1)")` gives id 1240287, but `IsPlayerSpell` of it didn't say yes.
- The highest known rank is now also read from the spellbook itself (the "Rank N" text of each
  entry, modern `C_SpellBook` or the classic tab functions), and several "do I know this id"
  checks are tried (`IsPlayerSpell`, `IsSpellKnown`, `C_SpellBook.IsSpellKnown`,
  `C_SpellBook.IsSpellInSpellBook`, `IsSpellKnownOrOverridesKnown`). The higher answer wins.
- New `/r2f rankdebug <spell>` (e.g. `/r2f rankdebug Charge`): prints the spell id of the plain
  name and of each `(Rank N)`, what every known-check answers, what the spellbook lists, and the
  rank the addon would use. Paste it to us if a macro still isn't ranked.

## 0.19.0 (2026-10-09): rank-aware macros (ADDON_PLAN 16)

**Never run in game yet: TESTING.md 27.**

- **Why:** on WoW Forever an unranked spell name can resolve to a rank you don't know: on a
  level-18 Warrior `/cast Charge` failed (the name gave the level-46 Charge) while `/cast Rend`
  worked. The addon now fixes this in the game macros it makes.
- When the addon **creates, updates or replaces** a game macro, every spell name in its `/cast`,
  `/castsequence` and `#showtooltip` lines is checked with `C_Spell.GetSpellInfo`: if the plain
  name is a spell you don't know, the highest rank you do know is written in (`Charge(Rank 1)`).
  Spells that resolve to something you know (Rend) are left alone, and so are spells you haven't
  learned any rank of yet. A name that already pins a rank (the site's `Charge(Rank 1)`) is raised
  when you know a higher one, never lowered. A ranked text over 255 characters isn't used.
- **Learning a spell** (`LEARNED_SPELL_IN_TAB` / `SPELLS_CHANGED`) re-checks the macros the addon
  made and raises ranks, after a one second pause; in combat the update waits for the end of the
  fight. Macros you edited yourself are never touched.
- **The library keeps the site's text.** Only what is written into game macros is ranked; the book,
  imports and the "edited / updated" checks compare the live macro with its ranked version, so a
  ranked macro is not mistaken for an edited or outdated one.
- New `/r2f ranks`: which spells in your macros have a plain name you don't know, the rank used
  instead, and the macros it is in (also macros kept unranked because of the 255 limit).

## 0.18.0 (2026-10-09): Launch Plan in game, TomTom waypoints (ADDON_PLAN 15.5)

**Never run in game yet: TESTING.md 26.**

- **New tab: Plan** (Home / Macros / Talents / Plan / Reminders / Settings; `/r2f plan`). Pick
  the group plan (2 Hunters · Warrior · Druid, 2 Hunters, 3 Hunters · Druid, Paladin · Hunter
  · Shaman: the site's plans with the site's override / `base` rules), then tick off the
  launch-day steps (launch night, phases 1 to 3). Ticks and the chosen plan are saved per
  character. The pre-launch and beta lists are not included.
- **Home shows the next step** ("Next: [12] Skycutter to Dalaran ...") and opens the tab.
- **Waypoints:** each step with known places lists them. A **Waypoint** button sets a TomTom
  waypoint (`TomTom:AddWaypoint`, zone names turned into uiMapIDs at run time); without TomTom
  the button (**Show /way**) prints the `/way Zone x y label` line to chat. Points with no known
  position yet show their label and "position not known yet" (no button); points taken from
  Classic or only roughly known say "may have moved".
- **`/r2f here`** prints your zone, uiMapID and x, y (and a `/way` line), so the missing
  positions can be captured in the beta and sent to us.
- The plan data (`PlanData.lua`) is generated from `launch-plan.html` and
  `launch-plan-waypoints.json` by `python build.py` (needs node); a test fails if the checked-in
  file is out of date or the addon's plan filtering differs from the site's own `resolve()`.

## 0.17.0 (2026-10-09): Reminders tab, Hunter ammo low (ADDON_PLAN 15.4)

**Never run in game yet: TESTING.md 25.**

- **New tab: Reminders** (Home / Macros / Talents / Reminders / Settings). It lists the
  on-screen reminder icons that apply to your class, each with its own Show, Lock and size
  slider. `/r2f reminders` opens it. A class without a reminder sees a line saying so.
- **The Warrior stance icon and its options moved here** from the Settings tab (same
  settings and saved position, `/r2f stance` unchanged).
- **New reminder: Hunter ammo low** (`Ammo.lua`). A framed icon with the number of arrows or
  bullets left (the equipped ammo, counted across quiver / pouch and bags). It turns red under
  a threshold you set on the tab (default 200, steps of 50, 50 to 1000) and is hidden while
  the ammo is fine, unless it is unlocked so you can move it. No ammo equipped shows a red 0.
  `/r2f ammo` shows or hides it, `/r2f ammo lock` locks it. Hunters only.
- Reminders are read-only (inventory getters only, no protected calls), so they work in
  combat, and their controls stay enabled in combat. Shared code for the framed icon,
  dragging and saved position is in `Reminders.lua`; adding a reminder means registering it.

## 0.16.0 (2026-10-08): movable bags (ADDON_PLAN 15.3)

**Never run in game yet: TESTING.md 24.** Which bag windows WoW Forever uses is
unconfirmed, so both kinds are handled and `/r2f bags` says what was found.

- **New: Movable bags / Lock bags** (`Bags.lua`), two more Quick settings on the Settings
  tab. Movable: drag the backpack and bags anywhere (grab the title or background, not an
  item). The position is saved per character (`R2FCharDB.bags`) and re-applied right after
  the game re-anchors the bags (`hooksecurefunc` on `UpdateContainerFrameAnchors`, plus
  `OnShow` on every window). Lock: keeps the spot, stops dragging. Replaces the Forever Bag
  Mover addon.
- Works with the classic bag windows (`ContainerFrame1..N`, saved per bag id so the
  backpack keeps its spot) and the modern combined bag (`ContainerFrameCombinedBags`),
  whichever the client has, or both.
- Nothing is moved, hooked or dragged in combat (bag windows hold protected item buttons);
  what was skipped runs when combat ends. The two boxes grey out in combat and when no bag
  window is found. Turning Movable off lets the game re-stack the bags; saved spots are
  kept for the next time.
- New `/r2f bags`: which bag windows were found and the movable / lock state.

## 0.15.0 (2026-10-08): Settings tab, tree names, Home as "what's next" (ADDON_PLAN 15.2)

**Never run in game yet: TESTING.md 23.**

- **Settings is the 4th tab** (Home / Macros / Talents / Settings). The Settings button
  left the Macro Book and the floating panel is gone; `/r2f settings` opens the tab.
  Left column: Macros (slots first, Remove all) and Minimap (show, lock). Right column:
  **Quick settings** (moved from Home: max camera zoom, hide guild names, hide PvP
  titles) and, for Warriors, the stance icon options (Show, Lock, size; they move to
  Reminders in step 4).
- **Home is a short "what's next" list:** free talent points, macros in the library and on
  your bars, and macro slot use (`7 of 30 character slots, 12 of 120 account slots used`),
  plus the Import / Export professions buttons.
- **Talents tab shows real tree names** (Arms / Fury / Protection ...) instead of
  "Tree 1 / 2 / 3": the same names and order as the site's talent calculator, for all nine
  classes. Names the game itself gives still win.
- **Black squares fixed (best guess, check in game):** the selected class circle and the
  selected side tab (Universal) were drawn with `SetCheckedTexture(..., "ADD")`, but the
  second argument only works for highlight textures, so the glow texture was drawn with
  normal blending as a black square. Selected state is now the same square glow as the
  hover highlight, blended additively (`UI.CheckedGlow`); icons that can't be named fall
  back to the question-mark icon (`UI.SetNormalIcon`).

## 0.14.0 (2026-10-08): import replaces, not only adds (ADDON_PLAN 15.1)

**Never run in game yet: TESTING.md 22.**

- The site's import string now ends with one `K <CLASS> id,id,...` record per class it
  carries (every id that class has on the site, picked or not). On import, library
  entries of a carried class that are not in that list are gone from the site and leave
  your library. Macros you just didn't pick are in the list and stay. Fixes the
  "207 macros in your library" pile-up after the site's 2026-10-08 macro cleanup.
- Game macros made from removed entries follow Tidy up's rules: unedited and not on a bar
  are deleted (queued until combat ends); on a bar, or edited by you, are kept and listed
  in chat ("kept, still on your bars: ...", "kept, edited by you: ..."). Kept ones stay
  tracked, so Tidy up can take them later. Macros still on the site but changed there
  update in place, as before.
- The preview says `12 macros were removed from the site and leave your library.` plus
  how many of them exist as game macros.
- Import window: new checkbox **Replace my library for these classes** (clean slate:
  removes everything of the carried classes that is not in the pasted string).
- Strings without `K` records (older site copies) keep the add-only behaviour. Older
  addons skip the new records and show "1 skipped" (harmless).

## 0.13.0 (2026-10-08): Warrior stance icon

**Tested in game by the owner (2026-10-08): works.**

- **New: stance icon** (`Stance.lua`), Warriors only. One icon showing the current
  stance, with a coloured frame: Battle blue, Defensive green, Berserker red. Drag it
  anywhere; Settings has Show, Lock and a size slider (50% to 300%). `/r2f stance`
  shows or hides it, `/r2f stance lock` locks it. Unlocked, it also shows with no stance
  so it can be placed before level 10.
- Section order follows the site's macro cleanup (2026-10-08): Mage has no Fire/Frost
  tabs and Rogue no Combat tab any more (all their macros were plain casts). Older
  versions just keep the unused names in their order table; nothing breaks.

## 0.12.2 (2026-10-07): Export professions button on Home

- **Export professions** button on the Home tab, next to Import (same as `/r2f profs`
  and the Export button on the profession window). Owner's request after the first real
  exports worked: a button in the addon window instead of typing a command.

## 0.12.1 (2026-10-07): profession export on modern profession windows

- 0.12.0 showed no Export button and no "saved N recipes" line in game: WoW Forever runs
  on a modern client, so the Classic profession functions are probably missing. Now also
  reads the modern profession window (`C_TradeSkillUI`: recipe ids, `GetRecipeInfo`,
  `GetRecipeSchematic` basic reagents), listens to `TRADE_SKILL_LIST_UPDATE` /
  `TRADE_SKILL_DATA_SOURCE_CHANGED`, and puts the Export button on `ProfessionsFrame` too.
- `/r2f profs` reads the open window itself if nothing was saved yet.
- New `/r2f profdebug`: one chat block showing which profession functions and windows this
  client has, how many rows the open window has, and what's saved. Paste it to us if the
  export still doesn't work.

## 0.12.0 (2026-10-07): export your professions for the site

**Never run in game yet: TESTING.md 21.**

- **New: profession export** (ADDON_PLAN 14). Open a profession window (Enchanting,
  Leatherworking, Tailoring, First Aid, ...) and the addon saves every recipe this
  character knows, with skill level and each recipe's materials (item ids + counts).
  Chat says "saved N Enchanting recipes". An **Export** button sits on the profession
  window next to its close button; `/r2f profs` does the same. Both show one
  `R2FP1:` string to copy, for the site's Professions page (Crafters).
- Reads both the trade skill window and Classic's craft window (Enchanting); opens all
  headers and clears "Have materials" first so the list is complete.
- Base64 encoding added (the export string is plain base64, safe in chat and Discord).

## 0.11.0 (2026-10-03): free talent points on WoW Forever + one-click learning through C_Traits

**The new learning path has never run against a real WoW Forever server. Test it with
ONE point on a disposable character first (TESTING.md 20), never on a main's build.**
Full design, confidence levels and the "not verified" list: `ADDON_PLAN.md` 13.12.

- **Fix: free talent points said 0** while Blizzard's window showed "Unspent Talents:
  17" (real screenshot), so Learn talents stayed grey. The count now comes from
  `C_Traits.GetTreeCurrencyInfo` (applied points, staged changes excluded), with
  Classic's `UnitCharacterPoints` kept unchanged for Classic-era clients. One function
  for the whole addon (`Talents.FreePointsInfo`; the minimap tooltip, Home, the Talents
  tab and the learning engine all use it). When no API gives a usable answer the addon
  now says **"couldn't read"** (Talents tab, Home) instead of a misleading "No free
  talent points", and Learn stays disabled.
- **New: "traits" learning mode** (WoW Forever). Learn talents spends points itself:
  `C_Traits.PurchaseRank(configID, nodeID)` per point, then `C_Traits.CommitConfig`
  when the purchase turns out to be staged (like Blizzard's own Apply Changes), one
  point at a time. Same order, popup, `Learning X / N`, combat stop, Stop / resume and
  no-double-send rules as before. A point only counts when its applied rank went up
  AND the free points went down. Anything unexpected (refused, error, failed commit,
  unconfirmed point) stops the run and switches to the existing guided mode for the
  rest of the session. Your own un-applied changes in Blizzard's window are never
  committed: the run stops and asks you to apply or undo them first.
- Classic's direct mode and guided mode are unchanged.
- Tests: fake trait servers (staged + commit, immediate, async, no commit) and every
  failure case; free points from the currency (17 with the legacy call saying 0),
  Classic path, unknown. Suite: 10927 checks, 0 failed (9389 before); 22 of 23 hand
  mutations fail the suite (the 23rd is equivalent); luacheck 0 warnings.

## 0.10.5 (2026-10-03): fix — Paladin talents unreadable (position jitter)

Follow-up to 0.10.4's C_Traits reader, found by live testing: a dump of all 50
real nodes of a Paladin's talent tree showed Protection's first column at both
posX 5020 and 5030. That's a few units of jitter in Blizzard's own layout data
(real columns are 590-600 apart), but 0.10.4 counted it as a fifth Protection
column, refused the tree, and Preview / Copy my build said "couldn't read your
talents yet." Full analysis: `ADDON_PLAN.md` 13.11.

- **Fix:** positions that are much closer together than a grid step (under 20% of
  the median gap) count as one row/column before rows and columns are numbered.
  The step is measured from the data itself, so it works at any scale. It applies
  to columns and to rows. Real columns that are just a little closer together than
  usual stay separate.
- Nothing changes when there's no jitter (Holy, and every earlier test, read
  exactly as before).
- Tests: the real 13 posX values in a 50-node Paladin tree read as 4/4/4 columns
  (was 4/5/4 -> nil), link + hash equal to the site's `talentcalc.js`; plus
  synthetic row jitter, several jitter pairs, other grid scales, a too-aggressive
  tolerance caught, and a jitter-majority tree refused. Suite: 9389 checks, 0
  failed (9259 before); luacheck 0 warnings.
- Still to confirm in game (TESTING.md 19): 0.10.5 on the Paladin, other classes.

## 0.10.4 (2026-10-03): fix — read talents through C_Traits (corrects 0.10.3)

0.10.3's fix was wrong: it force-loaded `Blizzard_TalentUI`, but on WoW Forever
`LoadAddOn("Blizzard_TalentUI")` answers `false, "MISSING"` and the Classic talent
functions never exist. So Preview and Copy my build still said "couldn't read your
talents yet." WoW Forever keeps its talents in the trait system (`C_Traits`), the
same API WeakAuras Forever reads them with. Full evidence: `ADDON_PLAN.md` 13.10.

- **Fix:** `Talents.ReadTrees()` reads the active talent config through
  `C_SpecializationInfo` / `C_Traits` / `C_Spell`. Rows and columns come from the
  nodes' positions (ranked, so any scale works; checked against 8 real Paladin nodes
  and Wowhead's row/col for the same ids). The three panes (e.g. Holy / Protection /
  Retribution) are one trait tree on Forever, split by the gaps between columns.
  Same output shape as before, so links, the `~hash`, the preview and the learning
  order are unchanged. Every call is guarded: a missing or not-ready API means
  "couldn't read yet", never an error.
- **Learning is guided on WoW Forever.** `LearnTalent(tab, index)` addresses
  talents the Classic way, which this client doesn't have, so the addon no longer
  calls it unless Classic's `GetTalentInfo` confirms the exact talent at that
  address. On Forever, Learn talents names each talent to click in Blizzard's window
  and writes nothing itself.
- Talent tooltips use `GameTooltip:SetSpellByID`; `TRAIT_CONFIG_UPDATED` refreshes
  the Talents tab like `CHARACTER_POINTS_CHANGED`.
- Removed: the `Blizzard_TalentUI` force-load and its tests. The test stub now models
  `C_Traits` (and answers `MISSING` for `Blizzard_TalentUI`), plus a realistic
  Forever client with no Classic talent API at all.
- Suite: 9259 checks, 0 failed (8770 before); luacheck 0 warnings.
- Still to confirm in game (TESTING.md 19): every class other than Paladin, the
  Protection/Retribution positions, pending (un-applied) points.

## 0.10.3 (2026-10-02): fix — Talent Preview failed on a fresh login

> Superseded by 0.10.4: `Blizzard_TalentUI` turned out not to exist on WoW Forever.

Reported from real in-game testing: pasting a talent link and clicking Preview
always showed "couldn't read your talents yet. Try again in a moment," even
though the character genuinely had talent points spent. `/dump
GetNumTalentTabs()` confirmed the cause directly: the function doesn't exist
as a global until Blizzard's own on-demand `Blizzard_TalentUI` addon has
loaded, which normally only happens the first time the player opens the real
Talent window by hand — the addon never tried to make that happen itself, it
only checked whether it already had.

- **Fix:** `Talents.ReadTrees()` now force-loads `Blizzard_TalentUI` via
  `LoadAddOn` (tries `C_AddOns.LoadAddOn` first, falls back to the bare
  global, `pcall`-wrapped) before checking for the talent functions, so
  Preview and Copy my build work the first time without the player needing
  to open their Talent window separately first. A one-shot retry 0.5s later
  covers the (believed unlikely) case where the force-load succeeds but the
  data isn't queryable in the exact same tick.
- Found by reading a third-party addon (RXPGuides) already working on the
  same WoW Forever client — it already solved this exact problem for its own
  talent-related features, and separately already has a proven, working
  `LoadAddOn` call for a different on-demand Blizzard addon. See
  `ADDON_PLAN.md` 13.9 for the full investigation and reasoning.
- The Lua test stub (`wow_stubs.lua`) previously defined the talent functions
  as always-available globals — an inaccurate model of the real client that
  every prior talent test was unknowingly built against. Fixed to match
  reality: they're now genuinely load-on-demand in the stub too.
- Full suite re-run: 8770 checks, 0 failed (up from 8688), including new
  tests specifically covering the cold-login scenario, no-LoadAddOn-at-all,
  and a refused load — each confirmed to fail cleanly, no errors.

## 0.10.2 (2026-10-02): version/author footer on the Home tab (ADDON_PLAN.md 12.4.2)

**Requested from real in-game testing, 2026-10-02** — there was no way to see
the addon's version or who made it without opening the TOC file.

- A quiet line at the bottom of the Home tab reads the TOC's own `## Version:`
  / `## Author:` fields through `GetAddOnMetadata` (tries `C_AddOns` first,
  falls back to the bare global, never a second hardcoded copy that could
  drift out of sync): `Road to Forever v0.10.2 · by nobody174 ·
  nobody174.github.io/wow-forever`.
- If neither metadata API exists on this client, shows a plain line with no
  version instead of erroring.
- Hovering it shows the TOC's `## Notes:` text as a one-line "what is this."
- Full suite re-run: 8688 checks, 0 failed.

## 0.10.1 (2026-10-02): fix — character macro slot limit was wrong

Reported from real in-game testing: the Macro Book's Character counter should
read out of 30, not 18.

- **Fix:** `Macros.Limits()`'s fallback (used when the game doesn't define
  `MAX_CHARACTER_MACROS`, which WoW Forever's client doesn't) was hardcoded to
  the vanilla/Classic Era value, 18. The user counted WoW Forever's real
  `/macro` Character tab directly: **30** slots (5 rows of 6). Fixed the
  constant; no other logic changed, since everything already correctly reads
  through `Macros.Limits()` rather than hardcoding 18 anywhere else.
- Updated the Lua test stub (`wow_stubs.lua`) and every test assertion that
  checked the old 18/138 numbers to match. Full suite re-run: 8608 checks,
  0 failed.
- Account-wide limit (120) is unchanged and still unverified directly — only
  the per-character number was actually in question.

## 0.10.0 (2026-10-02): class picker, Remove from library asks first, Tidy up tooltip

**Requested from first real in-game testing, 2026-10-02** — not part of the original
build plan (steps 3 to 10 + Quick settings). On a Paladin, the tester imported Warrior
macros: chat said `imported 51 macros.`, but no Warrior tab ever appeared, because the
book only showed the class you're logged in as. Decisions in `ADDON_PLAN.md` 5.10. Not
tested in the game yet; see `TESTING.md` section 17.

- **Class picker in the Macro Book:** when your library has macros for another class, a
  row of class icons appears at the top of the book (your class first). Click one to
  look at that class's macros from any character, e.g. to prepare an alt.
- **Other classes are preview only:** their macros show grey, with tooltips, and
  Shift-click still puts them in chat, but they can't be dragged to your bars (a Warrior
  can't cast Paladin spells; the addon refuses and says `Log in on a Paladin character
  to use this macro.`). Universal macros keep working in every view.
- The slot counters and gold "on your bars" checks always describe the character you're
  playing; a note says so while you preview another class.
- The book remembers the class you picked while you play, and opens on your own class
  again after a relog or `/reload`.
- After an import, the book opens on your own class if the import brought anything new
  for it, otherwise on the imported class's preview.
- **Remove from library** (right-click a macro) now asks first. It only takes the macro
  out of your book: a macro you already made from it stays in the game and on your bars
  (Tidy up or Remove all can delete it later). Importing it again brings it back as new.
  Works on previewed classes too, so a class imported by mistake can be cleared out.
- **Tidy up has a tooltip** saying what it deletes (unedited Road to Forever macros that
  aren't on any bar) and that it never changes your library.

## 0.9.1 (2026-10-02): fix — addon wouldn't load at all

First real in-game install of 0.9.0 reported: addon shows in the list, no
minimap icon, `/r2f` does nothing, no Lua errors. Turned out the game flagged
it "Incompatible" (yellow) in the AddOns list and refused to load any of it —
so there was nothing to error, since nothing ever ran.

- **Fix:** `## Interface: 11507` was a Classic Era placeholder, never actually
  checked against a real WoW Forever client. The real value, confirmed via
  `/dump GetBuildInfo()` on a live Forever client, is **16001**
  (`version="1.60.1", build="70170", tocversion=16001`).
- No code changed — this is the TOC fix alone. Everything built in 0.1.0
  through 0.9.0 should now actually load for the first time.

## 0.9.0 (2026-10-02): Quick settings (ADDON_PLAN.md 12.4.1)

Not tested in the game yet; see `TESTING.md` section 16.

- **Quick settings on the Home tab:** three check boxes that change game settings
  directly, with no macro and no macro slot: **Max camera zoom** (zoom the camera out
  further; untick = the game's own default), **Hide guild names** and **Hide PvP
  titles**. They always show your game's current setting, also when you changed it
  some other way (`/console`, the game's options, another addon).
- **Not in combat:** the boxes grey out in combat and can't be changed until it ends.
- **The Macro Book no longer shows** the Zoom out more, Hide guild names and Hide PvP
  titles macros, since Quick settings does the same for free. A line on the Universal
  tab says so. They're still on the website for players without the addon, and a real
  macro you already made from one keeps working.
- If your game lacks one of these settings, its box is greyed out and its macro shows
  in the book again.

## 0.8.0 (2026-10-02): talent learning (ADDON_PLAN.md step 10)

Not tested in the game yet. **This version can learn talents, which only a trainer
reset undoes: do `TESTING.md` section 15 on a test character first.**

- **Learn talents works.** After a Preview with no red problems, click **Learn
  talents**: `Learn 21 talent points? Only a trainer reset can undo this.` [Learn]
  [Cancel]. The addon then learns exactly the gold `+N` points of the preview, one at a
  time, tier by tier, and checks each one against your game first (tier, prerequisite,
  free points, nothing else changed). The button counts `Learning 7 / 21`; the rest of
  the tab is locked and Cancel becomes **Stop**. Done: `Learned 21 talent points.` and
  the trees redraw.
- **It stops instead of guessing:** if the game doesn't take a point (`Stopped at
  Improved Thunder Clap: the game didn't accept the point. 14 of 21 learned.`), if you
  enter combat (`Stopped: you entered combat. 9 of 21 learned. Click Learn talents to
  continue.`), or if your talents change meanwhile. After combat or Stop, Learn talents
  continues where it stopped, without asking again.
- **Not in combat:** Learn talents is greyed out in combat; a popup accepted just as
  combat starts waits until combat ends.
- **Guided mode:** if the game doesn't let addons learn talents, the addon opens
  Blizzard's talent window instead and puts a pulsing gold glow on the next talent to
  click (`Click Cruelty (2 of 21)`). It never changes Blizzard's window.
- If the game turns out to have Blizzard's own talent preview, Learn talents fills that
  preview and you confirm with Blizzard's Learn button.

## 0.7.0 (2026-10-02): talent import preview (ADDON_PLAN.md step 9)

Not tested in the game yet; see `TESTING.md` section 14. **Nothing is learned yet:**
this version only shows what a build would do. Learning comes in the next version.

- **The Talents tab is real now** (`/r2ft`). Paste a link from the site's talent
  calculator (Copy link; a full URL, `talents.html#...`, `#...` or just
  `warrior/...` all work) and click **Preview**: three small talent trees show what
  you already have, what would be learned now (gold glow, `+2`), what has to wait for
  more points (`later`), what isn't in the build (grey), and any problem (red).
  Hover a talent for the game's own tooltip plus `Build: 3 / 3`.
- **A summary line** says how many points the build uses and how many you have free,
  e.g. `This build uses 21 points. You have 16 free: 16 will be learned now, 5
  later.`, or what's in the way (`You already have 2 points in Improved Rend, which
  this build doesn't use. Reset your talents at a trainer first.`).
- **Safety checks:** a link for another class is refused (`This is a Paladin build.
  You're playing a Warrior.`); a link whose check (`~xxxx`) doesn't match your game's
  talent trees is refused; an older link without a check gets a yellow warning; a
  link asking for more ranks than a talent has, or points in a talent your tree
  doesn't have, is shown as a problem. On a non-English game client links can't be
  checked (talent names are translated), so you get the yellow warning instead.
- **Copy my build** is a button on the Talents tab (`/r2f copybuild` still works).
- **Learn talents** is there but greyed out until the next version.
- The tab remembers the last link per character and updates live when you spend
  points or level up. Home's Talents entry shows your free talent points.
- Works in combat: previewing only reads your talents.

## 0.6.0 (2026-10-02): Copy my build (ADDON_PLAN.md step 8)

Not tested in the game yet; see `TESTING.md` section 13.

- **`/r2f copybuild`** reads your current talents and shows them as a link to the
  Road to Forever talent calculator, already selected: press Ctrl+C and paste it in
  your browser or Discord. The link opens the site's calculator with your build.
  It only reads your talents (it never learns or changes anything), so it also
  works in combat.
- Links end in a short check (`~` and 4 characters) made from your class's talent
  names. The site's links now carry the same check, so the next version can warn you
  when a link was made with different talent trees than your game has.
- The Talents tab still has its placeholder; it now mentions `/r2f copybuild`. The
  Talents tab's own Copy my build button comes with the talent import version.
- `/r2f help` lists the new command.

## 0.5.0 (2026-10-02): first downloadable release (ADDON_PLAN.md step 7)

No change to what the addon does in the game: same code as 0.4.0. This is the
first version you can download as a zip instead of copying the folder from the
repository. Not tested in the game yet; see `TESTING.md`.

- **Download:** `RoadToForever-0.5.0.zip` on the GitHub Releases page (linked from
  the Macros page's "How to import" steps). Unzip it into your game's
  `Interface\AddOns\` folder; it contains one `RoadToForever` folder.
- Marked as a **pre-release** on GitHub, like every 0.x version, because nothing
  has been checked in the real game client yet.

## 0.4.0 (2026-10-02): main window, minimap button, logo (ADDON_PLAN.md step 6)

Not tested in the game yet; see `TESTING.md` section 11.

- **One window with three tabs** at the bottom: **Home**, **Macros** and
  **Talents**. The Macro Book is now the Macros tab (same book, same buttons),
  and the window has the Road to Forever logo as its portrait. It remembers where
  you put it and which tab you used last.
- **Home** shows how many macros are in your library and how many are on your
  bars, a Talents entry (coming in a later version), and an **Import macros**
  button. Click an entry to go to that tab.
- **Minimap button** with the logo: left-click opens/closes the window, right-click
  opens a menu (Open Road to Forever, Macros, Talents, Lock button position, Hide
  minimap button), drag it around the minimap. The tooltip shows your library
  count (and free talent points, if any). The Show / Lock minimap button settings
  now work. If you have another addon that uses LibDBIcon, the button goes through
  it, so minimap-button collector addons see it too.
- **Slash commands:** `/r2f` (window, last tab), `/r2f macros`, `/r2f talents` or
  `/r2ft`, `/r2f minimap` (hide/show the button), `/r2f import`, `/r2f help`.
- **Key bindings:** Toggle Road to Forever opens the window on your last tab;
  Open Macros / Open Talents open (or close) that tab.
- The Talents tab is a placeholder until the talent versions.

## 0.3.0 (2026-10-02): Settings, Remove all, key bindings (ADDON_PLAN.md step 5)

Not tested in the game yet; see `TESTING.md` sections 7, 9 and 10.

- **Settings** button in the Macro Book now works. It opens a small panel:
  - **New macros go to:** Character slots first / Account slots first. Only for
    macros made from then on; macros you already have stay where they are.
  - **Show minimap button / Lock minimap button**: saved now, used once the
    minimap button arrives (next version).
  - **Remove all Road to Forever macros**: after a confirm listing them, deletes
    every macro the addon made that you haven't edited, also ones on your action
    bars, in character and account slots. Macros you edited are kept as your own.
    Your macro library is not touched, so you can drag them out again. Greyed out
    in combat; if you accept it in combat, it runs when combat ends.
- **Key bindings** (Key Bindings menu, "Road to Forever"): Toggle Road to Forever
  and Open Macros open/close the Macro Book; Open Talents is a placeholder until
  the Talents window exists.
- **Tidy up** checks again, right when it deletes, that each macro is still not on
  a bar (matters when you accepted it in combat and it ran afterwards). Long name
  lists in popups are shortened (`... and 12 more`).

## 0.2.0 (2026-10-02): updates and Changed markers (ADDON_PLAN.md step 4)

Not tested in the game yet; see `TESTING.md` section 8.

- **Re-importing updates your macros.** When an import changes a macro you
  already made in the game, and you haven't edited it, the real macro gets the
  new text (and icon) right away. The preview says so before you click Import
  (`2 macros you already made in the game will be updated too.`), and chat
  confirms it afterwards.
- **Your edits are kept.** If you changed one of these macros yourself, it's left
  exactly as it is; the preview and chat say which ones (`kept your edits to HS`),
  and the library still has the new version: drag it from the book and choose
  Replace if you want it.
- **Changed marker:** a small green up-arrow on the macro's icon in the Macro Book
  when an import changed a macro that's on your action bars. Hover it to see what
  changed; the arrow goes away once you've seen it. Kept-edited macros on your bars
  get the arrow too, with a tooltip explaining your version was kept.
- **Other characters catch up on login.** The library is shared by all your
  characters, so macros you made on another character are brought up to date the
  next time you log in on it (only unedited ones). Dragging an older macro from the
  book also updates it first.
- In combat, these updates wait until combat ends (one chat line says so), and are
  checked again then, so anything you edited meanwhile is still left alone.
- The Import window is a little taller so the longer preview fits.

## 0.1.0 (2026-10-02): first version, Macro Book MVP (ADDON_PLAN.md step 3)

Not tested in the game yet; see `TESTING.md` for the beta checklist.

- `/r2f` opens the **Macro Book**, a spellbook-style window: side tabs for
  Universal and your class's sections, 2 x 6 macros per page, short names with
  the group underneath, the spell's icon (desaturated `Learn later` for spells
  you don't know yet), full tooltip (name, short name, body, note), page buttons,
  slot counter (`Character x / 18`, `Account y / 120`, red when full).
- **Import** window: paste the string from the site's "Copy import string",
  preview (`N macros: x new, y updated, z unchanged`, other-class and skipped
  counts), Import. The library is saved account-wide and has no size limit;
  every class's macros are kept.
- **Drag or click** a macro to create the real macro and put it on your cursor.
  Character slots first, account slots when those are full. Already created =
  just picked up again. A macro with the same name that isn't ours, or ours
  after you edited it, asks `Replace it?` [Replace] [Keep mine].
- **Tidy up** deletes Road to Forever macros that aren't on any action bar and
  that you haven't edited (with a confirm listing them).
- Right-click a macro: Remove from library, Copy text. Shift-click: body in chat.
- Combat-safe: no macro is created, edited, deleted or picked up in combat;
  Import / Tidy up grey out with `In combat`; a Tidy up confirmed in combat runs
  when combat ends.
- Settings (step 5), re-import updates of existing macros (step 4) and the main
  window + minimap button (step 6) are not in this version.
