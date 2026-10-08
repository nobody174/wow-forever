# Backlog

Active todo list — what's next, known gaps, findings not yet acted on. Shape B:
everything not shipped yet lives here, whether started or not. The moment
something ships, it moves to [CHANGELOG.md](CHANGELOG.md), not left here as a
stale checkmark.

## Launch-day refresh (WoW Forever launches 2026-11-04)

Beta data on the site is level-30 data. Redo these once the live game is up:

- [ ] **Professions BiS list:** re-scrape ForeverChanges' BiS pages (level 60 lists
      will differ), re-check stand-ins (`ALT`/`LADDER`) and recipe sources against
      Wowhead's Forever data, update the "checked" dates in the page note.
- [ ] **AH market:** when AHledger lists EU markets (`/v1/markets`), switch
      `DEFAULT_MARKET` in professions.html to our realm's market (EU, ruleset +
      faction we actually play) and save fresh site prices as the fallback.
- [ ] **Builds and launch plan:** re-check builds (talents/rotations) and the
      `unverified` steps past level 30 in launch-plan.html. The Level 60 builds
      (added 2026-10-08) are our own proposals from Wowhead's trees: compare them
      with the first real Forever level-60 guides (Mobalytics, Icy Veins, wow.gg)
      and swap in better ones.
- [ ] **Mark beta data:** until the above is done, label level-30 beta data as such
      on Professions and Builds.

## Next up: addon round 2 (agreed 2026-10-08, spec: ADDON_PLAN.md section 15)

Build in this order; each step is its own release.
- [ ] **1. Import replaces, not only adds** (15.1): site adds `K <CLASS> ids` lines to the
      import string; addon drops library entries the site removed, deletes unedited
      unused game macros made from them, keeps edited/on-bar ones. Fixes "207 macros".
- [ ] **2. Settings tab + fixes** (15.2): 4th tab instead of the Settings button; Quick
      settings move there; talent tree names instead of "Tree 1/2/3"; fix the two black
      squares in the Macro Book (class circle, Universal tab); Home as "what's next".
- [ ] **3. Movable bags** (15.3): Quick setting replacing the Forever Bag Mover addon
      (then remove Forever Bag Mover from addons.html).
- [ ] **4. Reminders tab** (15.4): stance icon moves here; owner picks the first new
      reminder: Hunter ammo low (picked 2026-10-08). Revenge flash dropped (the macro
      handles it). No buff reminders (ForeverPlus does those).
- [ ] **5. Launch Plan in game + TomTom** (15.5): checklist tab from the site's plan data,
      waypoint buttons via TomTom. Needs coordinates researched for the steps.

## Next up: "Road to Forever" in-game addon (planned 2026-10-01)

Full spec: [ADDON_PLAN.md](ADDON_PLAN.md). Read it before starting any step.
One addon, "Road to Forever" (`/r2f`, minimap button). Macros: pick on the site
(export), paste one string in-game (import), drag them onto your bars from a
spellbook-style Macro Book. Talents: paste a talent-calc link, preview, confirm,
and the addon learns the build. Real macros are only created
when dragged, so the 30/120 slot limit only counts macros you actually use.

- [x] **1. Data:** shipped 2026-10-01 — see CHANGELOG.md.
- [x] **2. Site export:** shipped 2026-10-01 — see CHANGELOG.md.
- [x] **3. Addon MVP:** shipped 2026-10-02 as v0.1.0 (tag `r2f-v0.1.0`) — see
      CHANGELOG.md. Not yet run in the game: needs the
      `addon/RoadToForever/TESTING.md` pass in the beta.
- [x] **4. Updates:** shipped 2026-10-02 as v0.2.0 (tag `r2f-v0.2.0`) — see
      CHANGELOG.md. Not yet run in the game: `TESTING.md` section 8.
- [x] **5. Tidy up, Settings, Remove all, keybindings:** shipped 2026-10-02 as
      v0.3.0 (tag `r2f-v0.3.0`) — see CHANGELOG.md. Not yet run in the game:
      `TESTING.md` sections 7, 9, 10.
- [x] **6. Main window + minimap:** shipped 2026-10-02 as v0.4.0 (tag
      `r2f-v0.4.0`) — see CHANGELOG.md. Own minimap button instead of embedded
      LibDBIcon (LibDataBroker's license, ADDON_PLAN 6.10). Not yet run in the
      game: `TESTING.md` section 11.
- [x] **7. Release:** shipped 2026-10-02 as v0.5.0 (tag `r2f-v0.5.0`, first
      GitHub Release, pre-release) — see CHANGELOG.md. Tag prefix settled as
      `r2f-v*` (ADDON_PLAN 8.1). Check each release once: `TESTING.md` section 12.
- [ ] **Release workflow upkeep:** the first run warned that `actions/checkout@v4`
      and `softprops/action-gh-release@v2` target Node.js 20 (deprecated, forced
      onto Node 24 for now). Bump both to their Node-24 majors before GitHub
      drops Node 20, then tag the next release and check its run.
- [x] **8. Talent export:** shipped 2026-10-02 as v0.6.0 (tag `r2f-v0.6.0`) — see
      CHANGELOG.md. `/r2f copybuild` for now (the Talents tab button comes with 9/10,
      ADDON_PLAN 13.6). Not yet run in the game: `TESTING.md` section 13 (the hash
      must equal the site's per class).
- [x] **9. Talent import preview:** shipped 2026-10-02 as v0.7.0 (tag `r2f-v0.7.0`)
      — see CHANGELOG.md. Learn talents button present but disabled until step 10
      (ADDON_PLAN 13.7). Not yet run in the game: `TESTING.md` section 14.
- [x] **10. Talent learning:** shipped 2026-10-02 as v0.8.0 (tag `r2f-v0.8.0`) — see
      CHANGELOG.md. Decisions in ADDON_PLAN 13.8. **Never run on a real client:** do
      `TESTING.md` section 15 on a test character before learning a real build with it
      (`LearnTalent` from an addon/event, 0.5 s timeout vs ping, guided-mode frame names).
- [x] **Quick settings (Home tab):** shipped 2026-10-02 as v0.9.0 (tag
      `r2f-v0.9.0`) — see CHANGELOG.md. Documented in `ADDON_PLAN.md` 12.4,
      decisions in 12.4.1. Last item of the addon build. Not yet run in the game:
      `TESTING.md` section 16 (incl. whether `SetCVar` is combat-blocked for
      these CVars; the addon refuses in combat either way).
- [ ] **Beta checks** (plan section 11): ~~Interface number~~ (fixed 2026-10-02,
      see CHANGELOG — was `11507`, real value `16001`, addon v0.9.1), slot limits,
      templates, CreateMacro+PickupMacro, relog survival, paste speed,
      LibDBIcon, menu API, LearnTalent from a click, talent order vs our links.
      Step-by-step list for the addon so far: `addon/RoadToForever/TESTING.md`.
- [ ] **Confirm the C_Traits talent reader in game (v0.10.4, ADDON_PLAN 13.10):**
      `TESTING.md` section 19 on every class available — Paladin's posX for all three
      panes is now dumped (v0.10.5 fixed the jitter it showed, ADDON_PLAN 13.11), but
      v0.10.5 itself hasn't been run in game yet, Prot/Ret posY weren't dumped, and the
      pane split for other classes is a hypothesis.
- [ ] **Verify v0.11.0 in game (TESTING.md 20, ADDON_PLAN 13.12):** free talent
      points from `C_Traits` (should match Blizzard's "Unspent Talents"), then the new
      one-click "traits" learning, **starting with ONE point on a disposable
      character**. Never-run-for-real: `PurchaseRank` from an addon, staged vs
      immediate, whether `CommitConfig` exists, node-field meanings, which events fire,
      `GetTreeCurrencyInfo`'s shape. Note every dump result in ADDON_PLAN 13.12.

Decided: no Druid; only Warrior (General/Tank/DPS) and Paladin
(General/Tank/DPS/Healer) use role sections, other classes keep their spec
sections; Warrior Arms + Fury stay merged in DPS.

## Waiting on Wowhead (2026-10-01)

- **Paladin "Crusade" talent (Retribution, row 4, far right, 2 ranks).** Shown in
  Mobalytics' Paladin leveling guide but missing from Wowhead's Forever data (and
  from Mobalytics' own calculator). Decision: we keep following Wowhead and don't
  patch it in by hand. The calculator loads Wowhead's data live, so it appears on
  its own once Wowhead adds it. When it does: old Paladin share links with points
  deep in Retribution will shift by one talent, so re-check the level-30 Ret build
  then (its share code is stored in `builds.html`'s `DATA30`).

## Open findings (from the 2026-09-24 WoW role pass)

- **No arena/PvP-specific macro coverage.** No `arena1-3` unit tokens or
  stopcasting patterns anywhere, though focus-based interrupt/CC macros exist.
  Confirmed out of scope for now — this site is general-purpose/PvE-leaning per
  its own lede. Revisit only if PvP macro requests actually come in.
- **`/console` CVar combat-lockdown status not fully confirmed.** Verified via a
  live WoW Forever community post that `/console` macros work on this client
  (not a stale Classic assumption) — but whether any are specifically blocked
  in combat wasn't confirmed either way. Low priority: none of the current
  `/console` macros (zoom, hide guild/PvP names) are combat-relevant actions.

## Open findings (from the 2026-09-30 Forever macro research)

- **"Test in beta" macros to confirm:** Dark Pact, Elemental Mastery (both not seen
  in beta talent trees), Seal swap (Twist of Light), Voice of Truth (talent or baseline?),
  Rogue Venom name (replaced Envenom?), Survival melee button (does Raptor
  Strike still queue off the GCD?).

## Seen in the beta, not reproduced

- **Macros missing from bars after a relog (2026-10-07, owner):** sometimes a Road to
  Forever macro had to be dragged out again (or clicked in the book) after logging in.
  Didn't happen on the next test. If it comes back: check `/macro` first (macro gone =
  the game didn't save it, e.g. after Alt+F4; macro there but bar slot empty = ours).

## Ideas not yet built

- Group picks: publish real 60 / end-game builds for our group (Druid healer/tank,
  Warrior, Hunters) once specs are agreed — owner login → Publish to group. No Druid
  pick yet. First real owner login still to be done (create the token, sign in once).
- Saved builds (My builds) are per browser. Friends share by link; only the owner
  publishes to Group picks. A shared list everyone can write to would need a backend.

- Addons page: expand beyond the current 4-addon list as we adopt
  more addons for launch.
