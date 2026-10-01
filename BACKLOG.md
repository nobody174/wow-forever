# Backlog

Active todo list — what's next, known gaps, findings not yet acted on. Shape B:
everything not shipped yet lives here, whether started or not. The moment
something ships, it moves to [CHANGELOG.md](CHANGELOG.md), not left here as a
stale checkmark.

## Waiting on Wowhead (2026-10-01)

- **Paladin "Crusade" talent (Retribution, row 4, far right, 2 ranks).** Shown in
  Mobalytics' Paladin leveling guide but missing from Wowhead's Forever data (and
  from Mobalytics' own calculator). Decision: we keep following Wowhead and don't
  patch it in by hand. The calculator loads Wowhead's data live, so it appears on
  its own once Wowhead adds it. When it does: old Paladin share links with points
  deep in Retribution will shift by one talent, and it's a good moment to add the
  Paladin (and Warrior) level-30 builds.

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
