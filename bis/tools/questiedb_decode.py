"""Decode the installed QuestieDB (Forever flavor) into plain JSON, read only.

QuestieDB "baked mode" keeps its database in the addon's .toc as `## X-<Type>-<id>-<field>: <base64 of CBOR>` lines (see its
src/read/baked.lua and src/meta/*.lua for the layout: one scalar row `-S` per entity, one `-<field>` value per table field, large values
split into numbered parts behind a `~N~` header). This reads the lines, decodes them and writes a compact JSON the other Mr.BiZ tools use.
Questie / QuestieDB are GPL v3; the output is only a cache (gitignored), credit goes on the page and in the README where its data shows.

Usage (repo root):  python -I bis/tools/questiedb_decode.py [path-to-QuestieDB_Forever.toc]
Output:             bis/own/cache/questiedb_live.json   {"build": ..., "npc": {id: {...}}, "quest": {...}, "item": {...}, "object": {...}}
"""
import base64
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BIS = os.path.normpath(os.path.join(HERE, ".."))
DEFAULT = r"D:\World of Warcraft\_forever_\Interface\AddOns\QuestieDB\QuestieDB_Forever.toc"
OUT = os.path.join(BIS, "own", "cache", "questiedb_live.json")

FIELDS = {
    "Npc": {1: "name", 4: "minLevel", 5: "maxLevel", 6: "rank", 7: "spawns", 9: "zoneID", 10: "questStarts", 11: "questEnds",
            12: "factionID", 13: "friendly", 14: "subName", 15: "npcFlags"},
    "Quest": {1: "name", 2: "startedBy", 3: "finishedBy", 4: "requiredLevel", 5: "questLevel", 6: "requiredRaces",
              7: "requiredClasses", 17: "zoneOrSort", 22: "nextQuestInChain", 12: "preQuestGroup", 13: "preQuestSingle"},
    "Item": {1: "name", 2: "npcDrops", 3: "objectDrops", 4: "itemDrops", 5: "startQuest", 6: "questRewards", 7: "flags",
             9: "itemLevel", 10: "requiredLevel", 12: "class", 13: "subClass", 14: "vendors", 15: "relatedQuests"},
    "Object": {1: "name", 2: "questStarts", 3: "questEnds", 4: "spawns", 5: "zoneID", 6: "factionID"},
}
TABLE_FIELDS = {"Npc": {7, 10, 11}, "Quest": {2, 3, 12, 13}, "Item": {2, 3, 4, 6, 14, 15}, "Object": {2, 3, 4}}


def cbor(data, pos=0):
    """Minimal CBOR decoder (ints, byte/text strings, arrays, maps, floats, bool/null): returns (value, next position)."""
    b = data[pos]
    major, info = b >> 5, b & 31
    pos += 1
    if info < 24:
        arg = info
    elif info == 24:
        arg = data[pos]; pos += 1
    elif info == 25:
        arg = int.from_bytes(data[pos:pos + 2], "big"); pos += 2
    elif info == 26:
        arg = int.from_bytes(data[pos:pos + 4], "big"); pos += 4
    elif info == 27:
        arg = int.from_bytes(data[pos:pos + 8], "big"); pos += 8
    else:
        arg = None
    if major == 0:
        return arg, pos
    if major == 1:
        return -1 - arg, pos
    if major in (2, 3):
        raw = bytes(data[pos:pos + arg])
        return raw.decode("utf-8", "replace"), pos + arg
    if major == 4:
        out = []
        for _ in range(arg):
            v, pos = cbor(data, pos)
            out.append(v)
        return out, pos
    if major == 5:
        out = {}
        for _ in range(arg):
            k, pos = cbor(data, pos)
            v, pos = cbor(data, pos)
            out[k] = v
        return out, pos
    if major == 7:
        if info == 20: return False, pos
        if info == 21: return True, pos
        if info in (22, 23): return None, pos
        if info == 25:
            h = int.from_bytes(data[pos - 2:pos], "big")
            return struct.unpack(">e", h.to_bytes(2, "big"))[0], pos
        if info == 26: return struct.unpack(">f", data[pos - 4:pos])[0], pos
        if info == 27: return struct.unpack(">d", data[pos - 8:pos])[0], pos
    raise ValueError("unsupported CBOR byte %02x at %d" % (b, pos))


def load_store(path):
    store = {}
    meta = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.startswith("## X-"):
                continue
            key, _, val = line[3:].rstrip("\r\n").partition(": ")
            store[key] = val
            if key in ("X-BUILD-COMMIT", "X-BUILD-TIME", "X-Flavor"):
                meta[key] = val
    return store, meta


def stored(store, key):
    v = store.get(key)
    if v is None:
        return None
    m = re.fullmatch(r"~(\d+)~", v)
    if not m:
        return v
    return "".join(store[key + "-" + str(i)] for i in range(1, int(m.group(1)) + 1))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    store, meta = load_store(path)
    print("read %d metadata lines" % len(store))
    import zlib
    out = {"build": meta, "npc": {}, "quest": {}, "item": {}, "object": {}}
    for kind, names in (("Npc", "npc"), ("Quest", "quest"), ("Item", "item"), ("Object", "object")):
        ids_raw = stored(store, "X-%s-IDS" % kind)
        ids = None
        if ids_raw:
            raw = base64.b64decode(ids_raw)
            try:
                ids = cbor(zlib.decompress(raw))[0]
            except Exception:
                try:
                    ids = cbor(zlib.decompress(raw, -15))[0]
                except Exception as e:
                    print("ids for %s: %s" % (kind, e))
        if not ids:
            # fall back to the ids that have a scalar row
            ids = sorted(int(k.split("-")[2]) for k in store if k.startswith("X-%s-" % kind) and k.endswith("-S"))
        print(kind, len(ids), "ids")
        fmap = FIELDS[kind]
        tables = TABLE_FIELDS[kind]
        for i in ids:
            s = stored(store, "X-%s-%d-S" % (kind, i))
            if s is None:
                continue
            row = cbor(base64.b64decode(s))[0]
            rec = {}
            for fi, name in fmap.items():
                if fi in tables:
                    v = stored(store, "X-%s-%d-%d" % (kind, i, fi))
                    if v is not None:
                        rec[name] = cbor(base64.b64decode(v))[0]
                elif isinstance(row, dict) and fi in row:
                    rec[name] = row[fi]
                elif isinstance(row, list) and fi - 1 < len(row) and row[fi - 1] is not None:
                    rec[name] = row[fi - 1]
            out[names][str(i)] = rec
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()
