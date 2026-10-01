"""Runs luacheck on the addon under real Lua 5.1 (lupa), without a luarocks install.

luacheck is pure Lua; only its CLI needs LuaFileSystem. This script uses
luacheck's library API (check_strings) instead, with addon/.luacheckrc.

Usage: python addon/tests/run_luacheck.py <path to luacheck-X.Y.Z/src> <dir with argparse.lua>
  (luacheck source: github.com/lunarmodules/luacheck releases;
   argparse.lua: github.com/mpeterv/argparse src/argparse.lua)
Exit code 0 = no warnings.
"""
import os
import sys

import lupa.lua51 as lua51

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.normpath(os.path.join(HERE, "..", "RoadToForever"))
RC = os.path.normpath(os.path.join(HERE, "..", ".luacheckrc"))


def main():
    src, argparse_dir = sys.argv[1], sys.argv[2]
    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    lua.execute('package.path = %r .. "/?.lua;" .. %r .. "/?/init.lua;" .. %r .. "/?.lua;" .. package.path'
                % (src.replace("\\", "/"), src.replace("\\", "/"), argparse_dir.replace("\\", "/")))
    luacheck = lua.eval('require("luacheck")')
    # .luacheckrc is plain Lua assignments; run it in its own environment.
    cfg = lua.eval("function(path) local env = {} local f = assert(loadfile(path)) setfenv(f, env) f() return env end")(
        RC.replace("\\", "/"))
    opts = lua.table(std=cfg.std, max_line_length=cfg.max_line_length,
                     globals=cfg.globals, read_globals=cfg.read_globals)

    files = []
    for dirpath, _, names in os.walk(ADDON):
        for n in sorted(names):
            if n.endswith(".lua"):
                files.append(os.path.join(dirpath, n))
    sources = lua.table(*[open(f, encoding="utf-8").read() for f in files])
    report = luacheck.check_strings(sources, opts)
    total = 0
    for i, path in enumerate(files, start=1):
        issues = report[i]
        for j in range(1, len(issues) + 1):
            issue = issues[j]
            total += 1
            print("%s:%s:%s: %s" % (os.path.relpath(path, ADDON), issue.line, issue.column,
                                    luacheck.get_message(issue)))
    print("luacheck (Lua %s): %d files, %d warnings" % (lua.eval("_VERSION"), len(files), total))
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
