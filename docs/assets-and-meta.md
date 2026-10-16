# Assets, icons, manifest

Images, link previews, installable-app meta. Moved out of CLAUDE.md 2026-10-16.

- `assets/hero-1.webp` … `hero-4.webp` — landing page backgrounds (painted road-to-a-gate
  scenes, made by the owner with free outside image tools, not Claude). `index.html`'s inline
  script right after `<div class="hero" id="hero">` rotates them every 2 days (UTC day / 2,
  same picture for everyone), each with its own `background-position` so the party and gate
  stay in view; `?bg=1..4` previews one. CSS default is hero-1. Sources are the owner's
  downloaded files (1584×672 for hero-1, 1248×832 for the rest), upscaled to 2560/1920 wide.
  `assets/og.jpg` is built from hero-1.
- `assets/sleepingbag.webp` — small icon (256×256) for the Cozy Sleeping Bag overlay
  plaque on `index.html`. Generated via local ComfyUI (SDXL base txt2img), finalized
  with Pillow (resize, exported as WebP).
- `assets/universal-icon.webp` — roster icon for the "Universal" tab on `macros.html`
  (dwarf+bear emblem, self-hosted from wow4ever.quest's own logo, converted to WebP).
  Class roster icons (Priest/Shaman/Paladin/Warlock/Hunter/Warrior/Rogue/Mage) are
  NOT local assets — they're hotlinked from Wowhead's icon CDN (`wow.zamimg.com`)
  directly in `template.html`'s `CLASS_ICONS` map.

- `assets/og.jpg` (1200×630 link-preview image, hero crop + "Road to Forever" in
  Marcellus), `assets/favicon.png` + `assets/icon-180.png` (gold "R" tab icon). Every
  page's `<head>` has description, `og:*`/`twitter:card` tags and the icons — new pages
  need the same block (macros.html gets it from template.html).
- `manifest.webmanifest` + the `manifest` / `apple-mobile-web-app-*` tags in every page's `<head>` (2026-10-12): makes the site an installable
  standalone app (iPhone: Safari > Share > Add to Home Screen; Edge on iOS may still open a normal tab). `assets/icon-192.png` / `icon-512.png`
  come from `addon/art/logo.svg`; the apple-touch icon stays the gold R. New pages need the same four meta lines.
- `assets/drafts/` — gitignored scratch folder for image-generation drafts/
  intermediates (hero and icon art both land here). Not part of the deployed site.
