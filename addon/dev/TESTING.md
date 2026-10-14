# Road to Forever: what still needs testing in game

Reply with the number: `4.2 done`, `7.3 needs more testing`, `13.2 not working: <what you saw>`. Passed items are removed (numbers stay the
same, so there are gaps) and are listed at the bottom. The old long version is in git history (`git log -- addon/dev/TESTING.md`).
This is the only place to look: the site's pages have no test lists. Checked against the 0.55.0 interface on 2026-10-14.

**Layout today (0.55.0):** a sidebar on the left: **Home** at the top, **JOURNEY** (Plan, Talents, BiZ) and **TOOLS** (Macros, Tweaks), with
Size / Opacity sliders and a Reload UI button in the window's top bar. There is no Settings or Gameplay tab any more: the game and
minimap options are on Home, the macro slot choice and Remove all are under Macros > Options, and the old Gameplay tab is **Tweaks**
(pages: Quests, Vendors & loot, Chat & screen, Bags, Alerts & HUD).

**Setup:** newest release zip unzipped into AddOns, `/console scriptErrors 1`, TomTom off (BiZNav replaces it), Questie on.
Level 20+ character is best. Use a test character for anything marked **TEST CHAR**.
**Taint check, any time:** `/console taintLog 1`, play, `/reload`, search `Logs\taint.log` for `RoadToForever`: no entries.

## 1. Window, minimap, bindings
4. Key bindings (Esc > Options > Key Bindings): a "Road to Forever" header with Toggle / Open Macros / Open Talents; each key opens the window on that tab and closes it when pressed again on that tab; they work in combat; they survive a relog.
5. Slash commands: `/r2f nonsense` should print `unknown command "nonsense". Type /r2f help for the list.` in chat (that IS the pass: tell me if nothing prints). New in 0.55.0: `/r2f open` only opens the window (it never closes it); `/r2f` alone toggles.

## 2. Macros (Macros tab; the Options button holds Import, "New macros go to" and Remove all)
1. Site "Copy import string", then Macros > **Options > Import**, paste: preview line within a second, Import enabled; `hello` gives the red "isn't a Road to Forever import string"; re-import = all unchanged. With an empty library the page now says to click Options, then Import (0.55.0).
2. Paste speed: the ~83 KB "Select everything" string does not freeze the game for more than about a second.
3. Macro Book: tab order, paging, slot counters match `/macro`, Shift-click puts the body in chat, right-click menu (Copy text).
4. Icon macros (pet attack, `/use`) keep their own icon.
5. Edit a macro in `/macro`, drag it again: Replace / Keep mine popup. Same popup for your own macro with one of our names.
6. Both slot pools full: red "No free macro slots". Macros survive a full relog (no duplicates, no popup).
7. Tidy up: a macro on a stance / stealth bar page is not offered; a macro dragged to a bar after the popup opened is kept.
8. Updates: an import that changes macros updates them in place; edited ones are kept with a message; green arrow marker and "Updated by your last import" tooltip; arrows survive `/reload`; login sync updates macros of another character.
9. Rank-aware macros (low-level character, e.g. Charge): `/r2f debug ranks` lists Charge; the macro in `/macro` reads `Charge(Rank 1)` or your top rank and works; learning the next rank raises it within seconds (also after combat); a macro you edited is left alone; no "updated" arrows after relog. Failing: `/r2f debug rank Charge` and send the lines.
10. Import replaces: an OLD string leaves the library as it was; a NEW string shows "N macros were removed from the site" and removes them (bar macros kept, edited kept); "Replace my library for these classes" works.
11. Class picker: importing another class's macros opens a read-only preview with class circles; dragging gives "Log in on a Warrior character..." and no taint; Universal still works in the preview; counters stay yours; the choice resets after `/reload`; Remove from library keeps the bar button working.
12. Macro Book hides Zoom / HideGuild / HidePvP and says why at the bottom.
13. Combat: "In combat" shows at the bottom, Tidy up greys out, Options > Import / Remove all answer "can't be used in combat", dragging a macro gives the red combat message, no "action blocked".
14. Black squares: click every class circle and side tab (incl. Universal): gold glow, never a black square.
15. Options menu: "New macros go to" Character / Account slots first (Account first puts the next new macro in the General tab of `/macro`); Remove all (popup lists what goes and what is kept; edited ones kept; in combat finishes after).

## 4. Talent learning (TEST CHAR, never a main)
1. Read-only: the free-points number on the Talents tab equals Blizzard's "Unspent Talents" (the source says `"traits"` and all four C_Traits functions exist, 2026-10-10; not yet compared); `/dump R2F.Talents.LearnMode()` says `traits`.
2. One point: click ONE tier-1 talent on the board (after a trainer reset), Learn this build, Cancel (nothing changes), Learn: applied within ~2 s, chat "Learned 1 talent point.", free points one lower, no "Interface action failed", survives `/reload`.
3. If it stops with "didn't accept" or "waiting in Blizzard's window": note the exact message and what Blizzard's window shows.
4. **Open until the owner drops it:** 5 points across tier 1 and 2: counts `Learning 1 / 5` ..., exact build at the end, none pending.
5. Your own unapplied click in Blizzard's window (not the addon's board) stops the run ("changes that aren't applied yet"), nothing learned.
6. Combat mid-run stops cleanly and continues after combat without a popup; Stop then Learn does not buy a point twice.
7. Full build, then Copy link: the link equals the site's for that build.

## 5. Home and Tweaks extras
1. Home > Quick settings (Max camera zoom, Hide guild names, Hide PvP titles, 24-hour clock): they grey out in combat; they read live values (`/console UnitNamePlayerGuild 0` ticks the box); they survive a relog.
3. Warrior stance icon (Tweaks > Alerts & HUD > Icons for your class): Show, Lock, size; colour and icon follow the stance.
4. Training reminder (Tweaks > Alerts & HUD): at level-up chat names the new spells; Home's "Training" block lists what to train after you visit your trainer once.

## 7. Tweaks tab (everything is OFF until ticked; turn off ForeverPlus' matching modules)
1. The five page buttons (Quests, Vendors & loot, Chat & screen, Bags, Alerts & HUD): the current one is gold with a bar; the last page is remembered; every option has a plain name and a grey line; "Reset page" puts that page back to defaults.
2. Vendors & loot > Auto-repair at vendors: repairs and prints the cost; nothing damaged = nothing; too little gold says so.
3. Vendors & loot > Auto-sell grey items: only greys, count and total in chat; greys with no sell price stay.
4. Chat & screen > Decline duel requests: a friend's duel is declined with a chat line.
5. Chat & screen > Hide red error messages: spam lines vanish, real ones ("in combat") stay.
6. Chat & screen > Always show XP numbers on / off (greyed out = tell me).
7. Vendors & loot > Mail: list my other characters (alt-picker button next to the recipient, full names like "Thorin Stormborn", the mail arrives) and Fast looting (needs the game's Auto Loot; Shift does the opposite).
8. Quests > Auto-accept quests / Auto turn-in quests: accepts, hands in (never picks among 2+ rewards, does turn in a single reward), finished quest goes first; Show sell price on quest rewards (price on each reward button); escort / group quests.
9. Quests > Track-all box in the quest log: one box per zone heading (collapsed headings too), not over text or arrow.
10. Alerts & HUD > Show an 'ability ready' alert: own text `<Revenge>` / `<Overpower>` at a movable gold marker, Lock the alert's position, Hide Blizzard's alert text (needs `/reload`), no Lua error. If it says "Ability ready": `/r2f debug reactlog` and paste (look for a USABLE line).
11. Quests > Skip the NPC chat before shops: opens the shop for a vendor with one extra line; never at an innkeeper, quest giver or multi-option NPC; Shift pauses. `/r2f debug gossip` lines for a vendor, trainer, flight master, innkeeper, banker, auctioneer.
12. `/r2f debug auras` probe: run alone out of combat, in a party out of combat, in a fight, in a dungeon; send the lines.
13. Alerts & HUD > Icons for your class > tracking reminder (needs Find Minerals / Herbs / Treasure): icon shows when none is active, goes when one is; a character without them never gets it.
14. Alerts & HUD > Icons for your class > Missing group buffs: icon for a missing Fortitude / Mark of the Wild etc., goes when cast; untick a buff in the list; works in combat and dungeons; sample icon when the lock is off.
15. Chat & screen > Copy-chat button (small C on each chat window, not in a bad spot) and `/r2f copychat` (oldest first, plain-text option, window number).
16. Hunter ammo (Hunter with a ranged weapon; Icons for your class): the count equals arrows / bullets in all bags; switching weapon type switches the label; red 0 with no ammo; hidden with no ranged weapon when locked; the "warn when under" slider; `/r2f ammo`.
17. Any "gameplay feature X hit an error" line in chat: send it.

## 8. Plan tab and BiZNav arrow
1. Plan tab: four group plans differ as described, ticks persist per character, "N of M launch-day steps" counts, Home's "Launch plan" line shows the next step.
2. Waypoint button arrow: "arrived" within 10 yards, "no position here" in dungeons; sharp at Medium and Large (3D arrow). Check a few places (Anvilmar, Thelsamar, Auberdine, Astranaar, Menethil, Southshore, Hall of Thanes).
3. `/r2f debug here` at "position not known yet" places: send the lines (BACKLOG 2.2). Note any classic position that is off.
4. Arrow size Small / Medium / Large (Tweaks > Alerts & HUD); drag keeps position over `/reload`; right-click clears.
5. `/bizway clear` and `/bizway size large`.
6. World map: the small diamond pin shows (also zoomed out to the continent).

## 9. Mr.BiZ (BiZ tab)
1. `/biz` opens the tab on your class and first spec; item names in quality colours (white with "?" only for a moment); item tooltip with the gold "Mr.BiZ:" line; Shift-click links in chat.
2. Click a name: ranks 2 and 3 open with "where from" lines, Bizzest / Bizzer / Biz and "The Bizz" fit without overlapping the boxes; a filtered best shows "Bizzer, your filters hide the best".
3. Wishlist: tick items, grouped by dungeon / profession / vendor, Export list pastes on the site, Import list from the site works, survives `/reload`.
4. Class and Spec menus open under the cursor and switch the list.
5. Alt + click a Scarlet Monastery item (list, gear slot icon, wishlist): arrow to the entrance; the blue hint line shows on hover.
6. Enchant lines in an opened slot are now green (0.54.1); check they fit with three ranks shown.
7. **New in 0.54.2:** hover a piece of gear (chest, cloak, bracers, gloves, legs, boots, neck, weapon, shield; in your bags or on your character): a green line "Mr.BiZ enchant: <name> (<effect>)" at the bottom of its tooltip; "Mr.BiZ enchant in place" once the best one is on; a gold line when a stand-in is on. Rings and trinkets get none. It needs Tweaks > Bags > Upgrade arrows ticked (same switch as the BiZ score line).

## 10. Corpse arrow (not tested yet, you have not died since 0.51.0)
1. Tweaks > Alerts & HUD "Arrow to corpse when you die" is ticked on a fresh character; tooltip explains it.
2. With an arrow set, die outdoors: it jumps to "Your corpse", chat says so, yards count down while running back.
3. Release spirit: the arrow stays on the corpse (does it appear only after release?).
4. Alive again: corpse arrow goes, the earlier arrow returns (none before = none left).
5. Setting another arrow while dead is not replaced on revive.
6. `/reload` as a ghost: arrow points at the corpse again.
7. Switch unticked: no arrow on death.
8. Death inside a dungeon: error, or just no arrow?

## 12. Release and exports
1. Each new release: the tag's Actions run is green; release named `Road to Forever <version>`, pre-release for 0.x, notes from the addon CHANGELOG, exactly one zip asset; unzipping gives `AddOns\RoadToForever\RoadToForever.toc` (no nested folder) and the addon shows on the character screen.
2. The Macros page's "How to import" Download link opens the Releases page with that release on top.
3. Profession export (Home > Export professions, or `/r2f profs`): no recipes without materials after hovering a few; `/reload` then `/r2f profs` gives the same string.
4. `/r2f debug who` on the Paladin: send the lines (which one reads "Thorin Stormborn"?).
5. Interface templates (`/dump R2FMain ~= nil`, `R2FMainTab1.r2fTemplate`, `MenuUtil ~= nil`, `R2F.Minimap.backend`): note the answers in ADDON_PLAN 11 if not already there.

## 13. Druid macros (0.55.0, all untested in game; use a Druid, level 20+ for Cat)
2. **Form numbers (the key check).** Cat Form + Prowl: press once, you become a cat; press again, you Prowl. If it casts the wrong form or does nothing, tell me your learned forms (Aquatic Form learned? level 16) and the number that works (2 or 3). Same for Claw / Shred / Rake / Dash.
3. Bear: Bear Form (no unshift) does nothing when already a bear; Growl@ taunts the mouseover; Maul queues on the next hit; Swipe, Demoralizing Roar, Enrage, Frenzied Regeneration shift you first and work. One press must be enough (not two).
4. Cat from stealth: Ravage / Pounce from Prowl; Tiger's Fury, Dash, Rip, Ferocious Bite work.
5. Heal from any form (Shift = Regrowth) leaves the form and heals; plain heals (Healing Touch, Regrowth, Rejuvenation) work on mouseover / target / yourself.
6. Cleanse: Abolish Poison, Shift = Remove Curse; Cure Poison / Remove Curse singles.
7. Rebirth in combat / Revive outside it (on a dead friend under the mouse); Innervate; Barkskin and Shift = Nature's Grasp (do they drop your form?).
8. Travel / Aquatic / Cat on one key; Cat Form (Shift = Bear Form); Leave form and dismount; Teleport: Moonglade.
9. Rune abilities (engrave the rune first): Starsurge, Sunfire, Starfall, Lacerate, Skull Bash, Survival Instincts, Lifebloom, Nourish: does the macro cast it? Is the spell name right?
10. Balance: Starfire (back into Moonkin, Ctrl = Wrath), Insect Swarm, Hurricane at cursor.
11. Level 40: does "Bear Form" in the macros need to become "Dire Bear Form"?

---
**Confirmed working (kept for the record):**
- *Window and Home:* the sidebar layout (6 tabs on the left), window position and last tab kept, minimap button (drag, lock, hide, Reload UI), Size / Opacity sliders, Home Quick settings box and footer, `/r2ft`, `/r2f import`, `/biz`, the 24-hour clock box and the three other Quick settings, Settings, profession export.
- *Macros:* tooltips, greyed "?" icons, no duplicate on re-drag, Replace popup, basic Tidy up, Druid macros appear in the Macro Book.
- *Talents tab (0.54.0):* the whole sandbox calculator, 3.1 to 3.12 including Share to Party and the Recommended builds.
- *Other:* all of Bags (arrows, sort, movable), Plan weapon lines, Plan Waypoint buttons, `/bizway` with coordinates, Alt + right-click map arrow incl. Questie, 3D arrow, Home Training lines (Train now / Next), Interface number 16001, slot limits 120 + 30.

**Dropped by the owner:** combat drag steps of the old section 6, Questie Ctrl + click (TomTom stand-in code stays, harmless), TomTom waypoint tests, "Required level" slider (removed 0.50.0), the old Classic-API talent learning checks.
