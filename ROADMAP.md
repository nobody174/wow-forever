# Roadmap

Future/unscoped ideas — the "someday" bucket — plus locked design decisions and
their history. Not active work; see [BACKLOG.md](BACKLOG.md) for what's actually
being worked on next.

## Someday ideas

- A companion WoW addon (Lua) instead of just a macro/text site — e.g. a settings
  panel to browse macros in-game. Would pull in the addon-development WoW roles
  (WoW Addon Architect, UI/Frame Designer, Event Flow Analyst, Taint & Secure
  Execution Auditor) that are currently out of scope for this macro-only project.
- Arena/PvP-specific macro set (arena1-3 tokens, stopcasting) if that ever becomes
  something Venom & Trollmann actually want covered. See BACKLOG for why this is
  currently deferred rather than in progress.

## Locked design decisions

- **Countdown target:** `2026-11-04T23:00:00Z`, fixed — confirmed correct as UTC,
  not a bug when it displays as Nov 5 in timezones ahead of UTC.
- **Site title:** "Road to Forever" (renamed from "Venom & Trollmann's Road to Forever" on 2026-09-30).
- **Macro style rules** (targeting conventions, `#showtooltip` placement,
  255-char limit) are locked in `CLAUDE.md` — treat any deviation as a bug, not
  a style choice, unless explicitly revisited.
- **Hero image pipeline:** local ComfyUI (SDXL base, no LoRAs) generation +
  Pillow finalization is the established asset pipeline for this project — reuse
  it for future site art rather than switching tools mid-project.
