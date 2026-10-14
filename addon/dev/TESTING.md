# Road to Forever: what still needs testing in game

Reply with the number: `3.2 done`, `3.4 needs more testing`, `5.1 not working: <what you saw>`. Passed items are removed
and noted in the CHANGELOG. The old long version (every step, every pass criterion) is in git history (`git log -- addon/dev/TESTING.md`).

**Setup:** newest release zip unzipped into AddOns, `/console scriptErrors 1`, TomTom off (BiZNav replaces it), Questie on.
Level 20+ character is best. Use a test character for anything marked **TEST CHAR**.
**Taint check, any time:** `/console taintLog 1`, play, `/reload`, search `Logs\taint.log` for `RoadToForever`: no entries.

## 1. Window, minimap, bindings
1. Tabs fit along the bottom edge (Home, Macros, Talents, Plan, Gameplay, BiZ, Settings) with the newest layout.
2. Window position and last tab are remembered over `/reload`.
3. Minimap button: drag follows the rim and is kept over `/reload`; Lock / Hide / Reload UI items; `/r2f minimap` shows it again.
4. Key bindings: a "Road to Forever" header with Toggle / Open Macros / Open Talents; they work, also in combat; survive relog.
5. Slash commands: `/r2ft`, `/r2f import`, `/r2f nonsense`, `/biz`.
6. Window Size / Opacity sliders: pressing the bar away from the thumb does nothing; dragging the thumb changes it on release.
7. Home: Quick-settings box fits above the Minimap heading; "What's next" lines (Talents points, Macro Book counts, Macro slots, Launch plan "Next") follow your actions.
8. Home footer hover tooltip shows the TOC notes; the footer does not overlap or clip.

## 2. Macros
1. Site "Copy import string" pasted in game: preview line within a second, Import enabled; `hello` gives the red "isn't a Road to Forever import string"; re-import = all unchanged.
2. Paste speed: the ~83 KB "Select everything" string does not freeze the game for more than about a second.
3. Macro Book: tab order, paging, slot counters match `/macro`, Shift-click puts the body in chat, right-click menu (Copy text). (Tooltips and the greyed "?" icons passed 2026-10-10.)
4. Icon macros (pet attack, `/use`) keep their own icon. (No duplicates and the Replace popup passed 2026-10-10.)
5. Edit a macro in `/macro`, drag it again: Replace / Keep mine popup. Same popup for your own macro with one of our names.
6. Both slot pools full: red "No free macro slots". Macros survive a full relog (no duplicates, no popup).
7. Tidy up: a macro on a stance / stealth bar page is not offered; a macro dragged to a bar after the popup opened is kept. (Basic Tidy up passed 2026-10-10.)
8. Updates: an import that changes macros updates them in place; edited ones are kept with a message; green arrow marker and "Updated by your last import" tooltip; arrows survive `/reload`; login sync updates macros of another character.
9. Rank-aware macros (low-level character, e.g. Charge): `/r2f ranks` lists Charge; the macro in `/macro` reads `Charge(Rank 1)` or your top rank and works; learning the next rank raises it within seconds (also after combat); a macro you edited is left alone; no "updated" arrows after relog. Failing: `/r2f debug rankdebug Charge` and send the lines.
10. Import replaces: an OLD string leaves the library as it was; a NEW string shows "N macros were removed from the site" and removes them (bar macros kept, edited kept); "Replace my library for these classes" works.
11. Class picker: importing another class's macros opens a read-only preview with class circles; dragging gives "Log in on a Warrior character..." and no taint; Universal still works in the preview; counters stay yours; the choice resets after `/reload`; Remove from library keeps the bar button working.
12. Macro Book hides Zoom / HideGuild / HidePvP and says why at the bottom.
13. Macros tab in combat: "In combat" shows, Import / Tidy up grey out, dragging gives the red combat message, no "action blocked".
14. Black squares: click every class circle and side tab (incl. Universal): gold glow, never a black square.

## 3. Talents tab (sandbox calculator, 0.54.0)
10. Share > Party (with a teammate who has the addon): they get a chat line and find it under Loadouts for that class. Also for a class the sender does not play.

## 4. Talent learning (TEST CHAR, never a main)
1. Read-only: the free-points number equals Blizzard's "Unspent Talents" (the source says `"traits"` and all four C_Traits functions exist, 2026-10-10; Home said "No free talent points", not yet compared); `/dump R2F.Talents.LearnMode()` says `traits`.
2. One point: click ONE tier-1 talent on the board (after a trainer reset), Learn this build, Cancel (nothing changes), Learn: applied within ~2 s, chat "Learned 1 talent point.", free points one lower, no "Interface action failed", survives `/reload`.
3. If it stops with "didn't accept" or "waiting in Blizzard's window": note the exact message and what Blizzard's window shows.
4. **Open until the owner drops it:** 5 points across tier 1 and 2: counts `Learning 1 / 5` ..., exact build at the end, none pending.
5. Your own unapplied click in Blizzard's window (not the addon's board) stops the run ("changes that aren't applied yet"), nothing learned.
6. Combat mid-run stops cleanly and continues after combat without a popup; Stop then Learn does not buy a point twice.
7. Full build then Copy my build: link equals the site's.

## 5. Settings, Tweaks, Quick settings
1. Quick settings boxes: they grey out in combat (the three boxes themselves passed 2026-10-10); read live values (`/console UnitNamePlayerGuild 0` ticks the box); survive relog.
2. Settings tab: Remove all (popup lists what goes and what is kept; edited ones kept; in combat finishes after); "New macros go to" Account first. (Settings in general passed 2026-10-10.)
3. Warrior stance icon: Show, Lock, size; colour and icon follow the stance.
4. Tweaks > Training reminder: at level-up chat names the new spells.

## 7. Gameplay tab (everything OFF until ticked; turn off ForeverPlus' matching modules)
1. Four page buttons (Quests, Vendors & loot, Screen & chat, Alerts); the current one is gold with a bar; the last page is remembered; wording clear.
2. Repair at vendors: repairs and prints the cost; nothing damaged = nothing; too little gold says so.
3. Sell grey items: only greys, count and total in chat; no-price greys stay.
4. Block duels: a friend's duel is declined with a chat line.
5. Hide red error spam: spam lines vanish, real ones ("in combat") stay.
6. XP bar text always shown on / off (greyed out = tell me).
7. Mail: alt-picker button next to the recipient (full names like "Thorin Stormborn", mail arrives); free bag slots; fast loot (needs game Auto Loot; Shift does the opposite).
8. Quests: accept, hand in (never picks among 2+ rewards, does turn in a single reward), finished quest goes first, reward sell prices on reward buttons, escort / group quests.
9. Quest log: track-all box per zone heading (collapsed headings too), not over text or arrow.
10. Reactive alert: own text `<Revenge>` / `<Overpower>` at a movable spot, hide Blizzard's own, no Lua error. If it says "Ability ready": `/r2f reactlog` and paste (look for a USABLE line).
11. Shop-line skipper: opens the shop for a vendor with one extra line; never at innkeeper, quest giver, multi-option NPC; Shift pauses. `/r2f gossip` lines for a vendor, trainer, flight master, innkeeper, banker, auctioneer.
12. `/r2f auras` probe: run alone out of combat, in a party out of combat, in a fight, in a dungeon; send the lines.
13. Tracking reminder (needs Find Minerals / Herbs / Treasure): icon shows when none is active, goes when one is; character without them never gets it.
14. Group buffs ("Missing group buffs"): icon for a missing Fortitude / Mark of the Wild etc., goes when cast; untick a buff; works in combat and dungeons; sample icon when unlocked.
15. Copy chat: `/r2f copychat` (oldest first, plain-text option, window number), the small C button per chat window not in a bad spot.
16. Hunter ammo (Hunter with a ranged weapon): count equals arrows / bullets in all bags; switching weapon type switches the label; red 0 with no ammo; hidden with no ranged weapon when locked; threshold slider; `/r2f ammo`.
17. Any "gameplay feature X hit an error" line: send it.

## 8. Plan tab and BiZNav arrow
1. Plan tab: four group plans differ as described, ticks persist per character, "N of M launch-day steps" counts, Home shows the next step.
2. Waypoint button arrow: "arrived" within 10 yards, "no position here" in dungeons; sharp at Medium and Large (3D arrow). Check a few places (Anvilmar, Thelsamar, Auberdine, Astranaar, Menethil, Southshore, Hall of Thanes). (Buttons set the arrow, direction and yards passed 2026-10-13.)
3. `/r2f here` at "position not known yet" places: send the lines (BACKLOG 2.2). Note any classic position that is off.
4. Arrow size Small / Medium / Large; drag keeps position over `/reload`; right-click clears.
5. `/bizway clear` and `/bizway size large` (own coordinates and the named form passed 2026-10-13).
6. World map: the small diamond pin shows (also zoomed out to the continent). Alt + right-click on the map sets the arrow (**passed**, incl. Questie objectives).

## 9. Mr.BiZ (BiZ tab)
1. `/biz` opens the tab on your class and first spec; item names in quality colours (white with "?" only for a moment); item tooltip with the gold "Mr.BiZ:" line; Shift-click links in chat.
2. Click a name: ranks 2 and 3 open with "where from" lines, Bizzest / Bizzer / Biz and "The Bizz" fit without overlapping the boxes; a filtered best shows "Bizzer, your filters hide the best".
3. Wishlist: tick items, grouped by dungeon / profession / vendor, Export list pastes on the site, Import list from the site works, survives `/reload`.
4. Class and Spec menus open under the cursor and switch the list.
5. Alt + click a Scarlet Monastery item (list, gear slot icon, wishlist): arrow to the entrance; the blue hint line shows on hover.
6. Enchant lines: shown on the right but white (should be coloured like enchant text, see BACKLOG 2.9); still to check they fit with three ranks shown.

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
3. Profession export: no recipes without materials after hovering a few; `/reload` then `/r2f profs` gives the same string. (Export itself passed 2026-10-10.)
4. `/r2f who` on the Paladin: send the lines (which one reads "Thorin Stormborn"?).
5. Interface templates (`/dump R2FMain ~= nil`, `R2FMainTab1.r2fTemplate`, `MenuUtil ~= nil`, `R2F.Minimap.backend`): note the answers in ADDON_PLAN 11 if not already there.

## 13. Druid macros (0.55.0, all untested in game; use a Druid, level 20+ for Cat)
1. Import the new string (or `/reload` after updating): a **Druid** tab with Shared / Balance / Feral / Restoration appears in the Macro Book and on the site.
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
**Confirmed working (kept for the record):** all of Bags (section 6), Plan weapon lines; Talents tab 3.1-3.9, 3.11, 3.12 (0.54.0); 3D arrow; bag upgrade arrows and tweaks; Plan weapon lines; window, help, tabs, minimap menu (Blizzard's own menu, `MenuUtil` = true), macro tooltips, no duplicate on re-drag, Replace popup, basic Tidy up, Settings, three Quick settings, profession export, Plan Waypoint buttons, `/bizway` with coordinates; Interface number 16001; slot limits 120 + 30; Home footer line; Plan weapon lines show; green bag upgrade arrows; Train now / Next on Home; Alt + right-click map arrow incl. Questie; 24-hour clock box (Quick settings).
**Dropped by the owner:** combat drag steps of the old section 6, Questie Ctrl + click (TomTom stand-in code stays, harmless), TomTom waypoint tests, "Required level" slider (removed 0.50.0), the old Classic-API talent learning checks (replaced by section 4).
