# Review 6: Critic / Devil's Advocate (with a short Architect read)

Date 2026-11-09. Read-only. This review is deliberately the skeptical voice: what a careful outsider, a teammate in a hurry, or you in three months would say is wrong. Where something is fine it says nothing, so read it as a list of risks, not a score.

## The five things I would worry about

### 1. Output is outrunning confirmation
Since 2026-10-13 the addon has had about 109 versions (0.55 to 0.84), roughly four a day. The open in-game test list has 16 items; the oldest note on it ("every theme was rebuilt blind, so expect rough edges") dates from 0.79.1 and six releases have been stacked on it. Every release passes 32,000 automated checks, but those check logic against stubs, not what the game draws. Today the real quality signal is you looking at the screen, and that is the scarce resource.
- **Effect:** the distance between "shipped" and "confirmed" only grows; a regression in a theme or tab can sit for weeks.
- **Suggestion:** a **test week**: no new features, close the 16 items with screenshots, run the 9 classes through Training and the talent board. Then a rule: no more than N unconfirmed releases (say 5) in a row.

### 2. The data pipeline depends on things that are not in the repository
- The 0.84.2 conversion (RankedBoost to our share codes) was done with scripts that live only in a temporary scratchpad (`repair.py`, `apply_rb.py`, `apply_builds.py`). The next talent hotfix (the game changed trees on 3-4 Nov, it can happen again) would mean writing them again from memory.
- The trainer list needs a browser console snippet and a saved file in Downloads; Wowhead blocks plain downloads; the Rehearsal and the daily CurseForge check cannot run from the sandbox.
- Mr.BiZ rests on ForeverDB (a hobby site that refreshed twice in a fortnight), builds on RankedBoost (a single commercial guide site whose Rogue numbers were already wrong against the live trees), prices on AHledger (free API, credit required).
- **Suggestion:** commit cleaned versions of the build-conversion scripts under `addon/tools/` this week with a `--source rankedboost` flag and a one-paragraph recipe in `docs/pipeline.md`. Pin each external source in one table (what we take, how often, who can break it, what we do if it is gone). The "own database" plan in `bis/OWN_DATABASE_PLAN.md` is the right long-term answer; the risk is that it stays a plan while the sources drift.

### 3. The site is a launch-night product that outlived its night
All of it is addressed in the Research, Design and Writer reviews, but the Critic's version is one sentence: five days after launch a visitor is told it is beta, told to put addons in the beta folder, shown level 30 gear, and told the game launches "tonight". The most credible thing the project can do this week is to look like the game is live.

### 4. Scope: the addon does a lot, and only part of it is the reason anyone would install it
52 modules and 34,000 lines. The unique value is the launch plan, the talent board and builds, Mr.BiZ and the macro book (things no other addon has for Forever). Next to them sit Tweaks that overlap mature addons (sell greys, auto repair, quest auto-accept, fast loot, bags, chat copy, action-bar veils, 10 looks, a recorder and a route log). Each one is small and optional, but each one is also surface area for taint, for combat bugs and for "why did my UI change". A skeptical player's first question is "is this safe to install next to my other addons?" and the honest answer is a 52-file one.
- **Suggestion:** keep shipping the unique parts as the front page of the README and the CurseForge listing; label the Tweaks as "optional extras, all off by default" (they already are); decide a policy that any new Tweak must be justified against Leatrix / the game's own settings before it is built.

### 5. Single person, single machine, many hidden habits
The memory file shows a lot of unwritten process: heredoc quirks, tag order, "wait for CI on the exact HEAD", the browser-subprocess trick for Wowhead, restoring settings on the release client by in-game commands rather than files. Useful, but all of it lives in session memory and one person's head. If you are away for a month, or a friend wants to help, none of it is discoverable from the repository.
- **Suggestion:** `docs/maintainers.md` of one page: the release steps, the data refresh steps (with the commands), what needs a browser and why, and the traps list. Most of the content already exists in scattered docs; this is a gathering job.

## Smaller doubts
- **"Verified" is a loaded word.** The launch plan shows "65 verified / 33 unverified". Verified by whom, when and against what build? A date and source per step (they exist in the JSON schema) would turn that from a claim into evidence.
- **Builds from one source.** After 0.84.2 the 23 rebuilt builds are one site's opinion. If RankedBoost is wrong for a class (as with Lethality), the page repeats the error with confidence. The "tell us if a class looks off" line is good; a second source on the three most played specs would be better.
- **The pace of change is visible to players.** An addon that changes every day (0.83 to 0.84.2 in two days) trains people to ignore update notices. The version-check feature then loses meaning.
- **Version 0.x with no 1.0 date.** HARDENING.md decided the first public release is 1.0.0 and the CurseForge upload is on hold until "works 100% for him and his friends". That is a good gate, but it has no definition. Write the three or four conditions down; it stops the gate from drifting and tells you when you are done.
- **Everything is in English and Alliance-only** by design; fine, but the README should say so in one line so Horde players do not install it for nothing (the Plan tab already says it, the README does not).

## Architect read (short)
- **Structure is sound.** One namespace (`R2F`), one module per concern, a clear load order in the `.toc`, generated data kept apart from hand-written code, a test that fails if generated files are stale. The "hooks only, never write into game tables" rule is easy to state and has held.
- **Risk: load-order coupling.** Modules reach each other as `R2F.X.Y` at call time, so the `.toc` order and "is it loaded yet?" checks are the integration contract. It works because the tests load the real `.toc`; keep that test.
- **Risk: SavedVariables schema is `version = 1` with no migration yet** (`Library.lua`: "Future migrations go here"). Eighty releases have been additive, which is the easy case. The first release that renames or restructures a key needs a migration and a test that loads an old saved-variables snapshot; write that test now while it is cheap (keep a frozen 0.60-era `R2FDB` fixture).
- **Duplication** (Code Review C8) is the main architecture debt: `safe`, `isSecret`, throttle written three to five times. One `R2F.Util` module.
- **Docs architecture** (Writer W11): `ADDON_PLAN.md` at 3,253 lines is a log; the short architecture page that a newcomer needs does not exist.

## Overall, in one paragraph
The engineering is better than the process around it: the code is careful, tested and honest; the weak spots are that the public face stopped at launch day, the reproducibility of the data refresh lives in a temp folder, and confirmation by eye is not keeping pace with release speed. All three are fixable in about a week of focused work without writing any new feature.
