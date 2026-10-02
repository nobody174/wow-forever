# Road to Forever (addon) changelog

Version history of the in-game addon itself. The site's history is in the
repo's root `CHANGELOG.md`.

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
