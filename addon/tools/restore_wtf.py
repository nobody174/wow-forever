"""Put the settings saved by backup_wtf.py (Edit Mode layouts, key bindings, macros) into the release client.

    python addon/tools/restore_wtf.py                  # shows what it would do, changes nothing
    python addon/tools/restore_wtf.py --apply          # does it (the game must be closed)

Options: --backup <folder>   a backup folder made by backup_wtf.py (default: the newest in D:\\Claude AI Projects\\wow-beta-backup)
         --client <folder>   the game folder to restore into (default: D:\\World of Warcraft\\_forever_)
         --account <id>      the account folder under WTF\\Account (default: the only one the client has)

What it copies (all account level): bindings-cache.wtf, edit-mode-cache-account.txt, macros-cache.txt, config-cache.wtf.
It never touches Config.wtf, SavedVariables or the per character folders. The beta and the release client name the account
folder differently (beta "575003#3", release "IZAK04"), which is why a plain copy by hand lands in the wrong place.

Safety: refuses to run while Wow.exe is running (the game rewrites these files when it closes and would undo the restore),
copies every file it replaces to wow-beta-backup\\before-restore-<time>\\ first, and deletes the account's cache.md5 (the game's
checksum of these files; with the old checksum the game treats the restored files as damaged and throws them away, it makes a new
one on start). To go back: copy the files from the before-restore folder over the client's again.
"""
import argparse
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_BACKUPS = Path("D:/Claude AI Projects/wow-beta-backup")
DEFAULT_CLIENT = Path("D:/World of Warcraft/_forever_")
FILES = ["bindings-cache.wtf", "edit-mode-cache-account.txt", "macros-cache.txt", "config-cache.wtf"]


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Wow.exe"], capture_output=True, text=True).stdout
    except OSError:
        return False
    return "Wow.exe" in out


def newest_backup(root):
    folders = sorted(p for p in root.glob("*") if p.is_dir() and (p / "Account").is_dir() and p.name[:1].isdigit())
    return folders[-1] if folders else None


def plan(backup, client, account):
    """[(source, destination)] for every file the backup has; also returns the account folder in the client."""
    accounts = [p for p in (client / "WTF" / "Account").glob("*") if p.is_dir() and p.name != "SavedVariables"]
    if account:
        dest = client / "WTF" / "Account" / account
    elif len(accounts) == 1:
        dest = accounts[0]
    else:
        raise SystemExit("The client has %d account folders (%s): choose one with --account." % (len(accounts), ", ".join(p.name for p in accounts)))
    if not dest.is_dir():
        raise SystemExit("No such account folder: %s (log in once with the release client first)" % dest)
    srcs = [p for p in (backup / "Account").glob("*") if p.is_dir() and p.name != "SavedVariables"]
    if len(srcs) != 1:
        raise SystemExit("The backup has %d account folders; expected one: %s" % (len(srcs), backup / "Account"))
    pairs = [(srcs[0] / name, dest / name) for name in FILES if (srcs[0] / name).exists()]
    return pairs, dest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--backup", type=Path)
    ap.add_argument("--client", type=Path, default=DEFAULT_CLIENT)
    ap.add_argument("--account")
    a = ap.parse_args(argv)
    backup = a.backup or newest_backup(DEFAULT_BACKUPS)
    if not backup or not backup.is_dir():
        raise SystemExit("No backup folder found (run backup_wtf.py on the beta client first).")
    pairs, dest = plan(backup, a.client, a.account)
    print("backup  : %s" % backup)
    print("into    : %s" % dest)
    for src, dst in pairs:
        have = dst.stat().st_size if dst.exists() else None
        print("  %-30s %6d bytes  replaces %s" % (src.name, src.stat().st_size, "a missing file" if have is None else "%d bytes" % have))
    md5 = dest / "cache.md5"
    print("  cache.md5 %s" % ("will be deleted (the game makes a new one)" if md5.exists() else "is not there"))
    if not a.apply:
        print("\nNothing changed. Close the game completely, then run again with --apply.")
        return 0
    if game_running():
        raise SystemExit("Wow.exe is running. Close the game completely first: it would overwrite the restored files when it closes.")
    keep = DEFAULT_BACKUPS / ("before-restore-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    keep.mkdir(parents=True, exist_ok=True)
    for _, dst in pairs:
        if dst.exists():
            shutil.copy2(dst, keep / dst.name)
    if md5.exists():
        shutil.copy2(md5, keep / md5.name)
    for src, dst in pairs:
        shutil.copy2(src, dst)
    if md5.exists():
        md5.unlink()
    print("\nDone. What was there before is in %s" % keep)
    print("Start the game: Edit Mode > pick the layout, Options > Key Bindings, /macro.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
