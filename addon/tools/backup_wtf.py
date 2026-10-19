"""Copy the settings that make the game feel like yours out of the beta client, so they can be put into the release client.

    python addon/tools/backup_wtf.py [destination folder]      # default: D:\Claude AI Projects\wow-beta-backup\<today>

Saved (all from <client>\WTF): Config.wtf (graphics, gamma, CVars), and per account: bindings-cache.wtf (key bindings),
macros-cache.txt (macros), edit-mode-cache-account.txt (your Edit Mode layouts, e.g. "Hunter"), config-cache.wtf, the other
*-cache files, and SavedVariables\RoadToForever.lua (our addon's saved settings and what the recorder wrote).
The folder is OUTSIDE the repository on purpose (character names and keys do not belong in git). To use it on the release client,
see docs/beta-backup.md.
"""
import datetime
import shutil
import sys
from pathlib import Path

CLIENT = Path("D:/World of Warcraft/_classic_beta_")
DEFAULT = Path("D:/Claude AI Projects/wow-beta-backup")
ACCOUNT_FILES = ["bindings-cache.wtf", "edit-mode-cache-account.txt", "macros-cache.txt", "config-cache.wtf",
                 "flagged-cache-account.txt", "chat-frontend-cache.txt", "tts-cache-account.txt"]


def main():
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT / datetime.date.today().isoformat()
    dest.mkdir(parents=True, exist_ok=True)
    wtf = CLIENT / "WTF"
    copied = []
    if (wtf / "Config.wtf").exists():
        shutil.copy2(wtf / "Config.wtf", dest / "Config.wtf")
        copied.append("Config.wtf")
    for acct in sorted((wtf / "Account").glob("*")):
        if not acct.is_dir() or acct.name == "SavedVariables":
            continue
        out = dest / "Account" / acct.name
        out.mkdir(parents=True, exist_ok=True)
        for name in ACCOUNT_FILES:
            if (acct / name).exists():
                shutil.copy2(acct / name, out / name)
                copied.append("%s/%s" % (acct.name, name))
        sv = acct / "SavedVariables" / "RoadToForever.lua"
        if sv.exists():
            (out / "SavedVariables").mkdir(exist_ok=True)
            shutil.copy2(sv, out / "SavedVariables" / "RoadToForever.lua")
            copied.append("%s/SavedVariables/RoadToForever.lua" % acct.name)
    print("%d files copied to %s" % (len(copied), dest))
    for c in copied:
        print("  ", c)


if __name__ == "__main__":
    main()
