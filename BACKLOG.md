# Backlog

Active todo list — what's next, known gaps, findings not yet acted on. Shape B:
everything not shipped yet lives here, whether started or not. The moment
something ships, it moves to [CHANGELOG.md](CHANGELOG.md), not left here as a
stale checkmark.

## Next up: "Road to Forever" in-game addon (planned 2026-10-01)

Full spec: [ADDON_PLAN.md](ADDON_PLAN.md). Read it before starting any step.
One addon, "Road to Forever" (`/r2f`, minimap button). Macros: pick on the site
(export), paste one string in-game (import), drag them onto your bars from a
spellbook-style Macro Book. Talents: paste a talent-calc link, preview, confirm,
and the addon learns the build. Real macros are only created
when dragged, so the 18/120 slot limit only counts macros you actually use.

- [x] **1. Data:** shipped 2026-10-01 — see CHANGELOG.md.
- [x] **2. Site export:** shipped 2026-10-01 — see CHANGELOG.md.
- [x] **3. Addon MVP:** shipped 2026-10-02 as v0.1.0 (tag `r2f-v0.1.0`) — see
      CHANGELOG.md. Not yet run in the game: needs the
      `addon/RoadToForever/TESTING.md` pass in the beta.
- [x] **4. Updates:** shipped 2026-10-02 as v0.2.0 (tag `r2f-v0.2.0`) — see
      CHANGELOG.md. Not yet run in the game: `TESTING.md` section 8.
- [ ] **5. Tidy up, Settings, Remove all, keybindings.**
- [ ] **6. Main window + minimap:** Home / Macros / Talents tabs, logo
      (road curling into ∞, gold on navy, readable at 20 px; SVG source ->
      .tga), LibDBIcon button draggable around the minimap, right-click menu
      (Open / Macros / Talents / Lock / Hide), `/r2f`, `/r2ft`, `/r2f minimap`.
- [ ] **7. Release:** GitHub Actions zip on `addon-v*` tags, Download link on the site.
- [ ] **8. Talent export:** Copy my build as a site link. Site links get the
      `~hash` check; `talentcalc.js` ignores `~...` when reading (bump `?v=`).
- [ ] **9. Talent import preview:** paste a Copy link URL, three mini trees,
      summary, conflict/mismatch warnings. Nothing learned.
- [ ] **10. Talent learning:** Learn talents + confirm popup, one point at a
      time, stops on combat/errors; guided glow mode if `LearnTalent` is blocked.
- [ ] **Quick settings (Home tab):** three checkboxes that change game settings
      directly with `SetCVar`, so no macro or macro slot is used. Max camera
      zoom = `cameraDistanceMaxZoomFactor 4` (unticked = game default via
      `GetCVarDefault`). Hide guild names = `UnitNamePlayerGuild 0` (unticked =
      1). Hide PvP titles = `UnitNamePlayerPVPTitle 0` (unticked = 1).
      Checkboxes read the current value with `GetCVar` when the tab opens. Out
      of combat only. The three macros stay on the website, but the addon
      hides them from the Macro Book. Add it to `ADDON_PLAN.md` section 12.4
      when it gets built.
- [ ] **Beta checks** (plan section 11): Interface number, slot limits,
      templates, CreateMacro+PickupMacro, relog survival, paste speed,
      LibDBIcon, menu API, LearnTalent from a click, talent order vs our links.
      Step-by-step list for the addon so far: `addon/RoadToForever/TESTING.md`.

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

- **Weapon-swap macro doesn't mention the combat restriction.** WoW blocks weapon
  swaps while in combat (a hard game rule, not a macro bug) — the site's
  description doesn't say this, so a player could try it mid-fight and be
  confused why nothing happens. Explicitly declined a fix when raised; revisit
  if it turns out to actually confuse people.
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

## Hero image replacement (in progress)

- New `assets/hero.webp`: four Skyborne (mixed male/female) — one Warrior, one Druid
  healer, two Hunters with pets — on Zephras Isle, no nameplates. Generated in the
  user's local ComfyUI (can't run from the cloud session); then crop/resize to
  2560×1080, export WebP < 500KB, keep the upper-middle clear for the title and the
  right side calm for the beta ribbon. Update CLAUDE.md's hero description after.

## Ideas not yet built

- Group picks: publish real 60 / end-game builds for our group (Druid healer/tank,
  Warrior, Hunters) once specs are agreed — owner login → Publish to group. No Druid
  pick yet. First real owner login still to be done (create the token, sign in once).
- Saved builds (My builds) are per browser. Friends share by link; only the owner
  publishes to Group picks. A shared list everyone can write to would need a backend.

- Addons page: expand beyond the current 4-addon list as we adopt
  more addons for launch.
- Builds page: still a coming-soon placeholder — needs actual talent build
  content once specs are locked in closer to November 4.
- Consider whether `assets/hero.webp`'s six-hero composite is worth another
  refinement pass (spell-effect colors read as mostly torch-glow rather than
  distinct lightning/ice/shield colors) — parked because the current version
  was accepted as good enough, not because it's blocked.
