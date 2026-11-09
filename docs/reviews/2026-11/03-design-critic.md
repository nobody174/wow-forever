# Review 3: Design Critic (UI / UX)

Date 2026-11-09. Read-only. Method: all ten site pages rendered in Edge at desktop width (1280) from the working tree and looked at; phone width (390) rendered too, but Edge's headless mode enforces a minimum viewport, so the phone shots crop the page and are **not** reliable evidence. The in-game addon windows were **not** rendered here (no game client), so the addon section below is based on code, the theme system and the screenshots you sent earlier.

## Verdict
The site has a clear, consistent identity: navy and gold, one serif display face, one sans, one mono for code, one top bar everywhere, gold used only for "this is the thing to click". Information-dense pages (Mr.BiZ, Professions, Macros) are well laid out and scannable. The design is not the weak point. The weak points are **state and honesty of the UI** (it still says "beta" and "launching tonight" after launch) and a few places where one more decision would remove noise.

## What works (keep)
- **Top bar and navigation.** Same bar on every page, active page in gold, order follows the player's path (plan, character, UI). Zero hunting.
- **Class colours** as the filter language (Priest white, Mage cyan, Hunter green, ...), reused on Builds, Talents, Macros, Professions. Players learn it once.
- **Macros page.** Search first, class tabs, spec chips, then a short list of macro "pills" with one code block and one Copy button. Best page on the site: one action per screen.
- **Mr.BiZ.** Slot rows with icon, rarity colour, source, score, "Next:" alternative and expandable detail. The stat-weight chips and the source filters give power without clutter. The "Seen / Client / Classic / Clue / Unknown" confidence tags are an honest touch most sites would hide.
- **Professions.** Medal coins (1 / 2 / 3) and the dot rows (which classes use it) read quickly; gold price column right-aligned; "Not covered yet" is a clear empty state.
- **Talent calculator.** Grey until you spend, green ring when allowed, arrows for prerequisites, `0/5` badges. Shows the whole page without scrolling at 1280.

## Findings

| # | Sev | Where | Finding | Suggestion |
|---|---|---|---|---|
| D1 | **High** | Index | Contradictory hero. It says **"WoW Forever is live!"** and directly under it **"Launches Thursday, November 5, 2026 at 12:00 AM your time"**, then "Launching tonight? Open the short night list", with the red **BETA** corner ribbon on top. Four messages, three of which are now wrong. (The HTML comment next to the ribbon even says to remove it when the countdown hits zero.) | Live state: hide the launch-date pill, the "tonight" chip and the ribbon; keep "is live" plus Server status; the three "start here" cards become the primary action. |
| D2 | **High** | Index, Builds, Mr.BiZ, Launch plan, Macros | The **BETA DATA** badge in the data strip (`Client 1.60.x · updated 2026-11-08 · BETA DATA`) is on every data page. A reader cannot tell whether the data is "from the beta" (old) or "current for 1.60.1" (new). On Builds and Macros the data was rebuilt for the live trees this week, so the badge now undersells it; on Mr.BiZ (list from 10-17) it is accurate. | Make the badge per page and truthful: "current build" vs "beta data (level 30), refresh pending". |
| D3 | **High** | Addons page | The install instruction says copy to `World of Warcraft\_classic_beta_\Interface\AddOns`. Your real client folder is `_forever_` and the beta client no longer matters. A new player following this puts addons in a folder the game never reads. The same page says "Versions checked on CurseForge: Oct 25, 2026" (two weeks ago) and lists our addon as "pre-release". | Fix the path (show `_forever_` first, mention that the folder name follows the client); refresh or hide the checked date; decide the "pre-release" wording. |
| D4 | Med | Builds | First view after the heading is a lede, a toggle card about the beta Legacy perk, then nine class buttons, then a large empty area with "Pick a class above". The class choice is the page's only job. | Remember the last class in `localStorage` (you do this elsewhere) and open it; or pre-select the visitor's class from `#hash`. The Legacy toggle could sit inside the build view instead of above it. |
| D5 | Med | Talents, Builds | The **Legacy perk** card (+5 talent points) is written for the beta ("In the beta every character has it; at launch you start with no Legacy points ... treat 26-point builds as beta-only"). It is the first thing read on two pages and describes a situation that is over. | Rewrite from what the live game does (see Writer review W1), shrink it to one line with a "?" link. |
| D6 | Med | Builds / Talents | Class buttons wrap 8 + 1: **Warrior alone** on a second row (on both pages). Small, but the first thing the eye sees as "unfinished". | `justify-content:center` with a width that fits 9 (about 112 px each at 1280) or a 3x3 grid. |
| D7 | Low | Index | The left rail (Sleeping Bag, Library Books, General Resources, Tools) is two columns of cards over the artwork. They read well, but there is a large empty band above them and the title is far from the cards; on a laptop screen (about 700 px high) the "start here" cards sit near the fold. | Pull the content block up about 100 px; keep the artwork. |
| D8 | Low | Launch plan | The "Draft." warning box, the "unverified" tags and the "Test in beta" section (D1/D2 again) make the page look unfinished even though 65 steps are verified. | After the post-launch pass, replace Draft with a "last verified" line. |
| D9 | Low | All pages | The footer is good. The red dot next to "What's new" is a nice unread marker, but it appears on every page and never clears in a fresh browser; check it clears after viewing. | Verify in a clean profile. |
| D10 | Info | Phone width | Not assessed reliably (see method). The code carries the 2026-11-02 accessibility pass (tap targets, scrolling top bar). | Check Index, Builds and Mr.BiZ on a real phone once. |

## The addon window (limited review)
- **Strength:** 10 theme sets, per-theme layouts, a theme picker with thumbnails, fonts per theme (R2FBody / R2FHeading / R2FDim) and a test that bans hard-coded grey/gold text colours. That is real design-system discipline for an addon.
- **Risk 1, scope:** every new tab (Training this week) has to be checked against 10 themes x 3 layouts (sidebar / grid / top). Today that is checked by the owner by eye. A one-page "theme matrix" test sheet in `TESTING.md` (tab x theme, tick when seen) would make that finite.
- **Risk 2, density:** the Training tab uses its own page size (640 x 590) while other tabs use the standard one. Looks right in the screenshot you sent, but it is the only tab that does it; keep it an exception, not a pattern.
- **Risk 3, "dim" text:** several themes use a dimmed text colour for notes; with the light themes that colour had to be reworked once (0.76). Every new dim line needs the same check; automate with a contrast calculation per theme if it keeps happening.
- **Not assessed:** the talent board's next-point pulse (unconfirmed by you), the sidebar with 7 tabs on grid and top layouts.

## Suggested order
D1 -> D3 -> D2 -> D5 (all copy/state, an hour of work), then D4/D6 (small polish), then D7/D8.
