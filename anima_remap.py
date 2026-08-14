from __future__ import annotations

import json
import re
from pathlib import Path

BLOCK_PATTERNS = [
    re.compile(r"(?P<prefix>(?:^|[_./])(?:net[_./])?blocks[_./])(?P<idx>\d+)(?P<suffix>(?:[_./]|$))"),
]

DEFAULT_OLD_BLOCK_COUNT = 28
DEFAULT_NEW_BLOCK_COUNT = 40
DEFAULT_INSERTIONS = [2, 5, 8, 11, 14, 17, 21, 24, 27, 30, 33, 36]
DEFAULT_INSERTED_TO_SOURCE = {
    "2": 1,
    "5": 3,
    "8": 5,
    "11": 7,
    "14": 9,
    "17": 11,
    "21": 14,
    "24": 16,
    "27": 18,
    "30": 20,
    "33": 22,
    "36": 24,
}


def load_manifest(path=None):
    if path is None:
        path = Path(__file__).with_name("expand_manifest.json")
    data = {}
    if path.is_file():
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    return {
        "old_block_count": int(data.get("old_block_count", DEFAULT_OLD_BLOCK_COUNT)),
        "new_block_count": int(data.get("new_block_count", DEFAULT_NEW_BLOCK_COUNT)),
        "insertion_positions": [int(p) for p in data.get("insertion_positions", DEFAULT_INSERTIONS)],
        "inserted_to_source": data.get("inserted_to_source", DEFAULT_INSERTED_TO_SOURCE),
    }


def build_block_maps(old_block_count, new_block_count, insertion_positions, inserted_to_source=None):
    inserts = sorted({int(p) for p in insertion_positions})
    insert_set = set(inserts)

    if len(inserts) != new_block_count - old_block_count:
        raise ValueError(
            "insertion count {} != new-old ({}-{}={})".format(
                len(inserts), new_block_count, old_block_count, new_block_count - old_block_count
            )
        )
    for p in inserts:
        if not (0 <= p < new_block_count):
            raise ValueError("insertion position out of range: {}".format(p))

    old_to_new = {}
    new_to_old = {}
    old_i = 0
    for new_i in range(new_block_count):
        if new_i in insert_set:
            new_to_old[new_i] = None
        else:
            if old_i >= old_block_count:
                raise ValueError("ran out of old blocks while building map")
            old_to_new[old_i] = new_i
            new_to_old[new_i] = old_i
            old_i += 1
    if old_i != old_block_count:
        raise ValueError("mapped {} old blocks, expected {}".format(old_i, old_block_count))

    inserted_from = {}
    if inserted_to_source:
        for k, v in inserted_to_source.items():
            inserted_from[int(k)] = int(v)
    else:
        for new_i in inserts:
            prev = new_i - 1
            while prev >= 0 and new_to_old.get(prev) is None:
                prev -= 1
            if prev < 0 or new_to_old[prev] is None:
                raise ValueError("cannot infer source for inserted block {}".format(new_i))
            inserted_from[new_i] = int(new_to_old[prev])

    missing = insert_set - set(inserted_from)
    if missing:
        raise ValueError("missing inserted_to_source for: {}".format(sorted(missing)))

    return old_to_new, new_to_old, inserted_from


def remap_key(key, old_to_new):
    for pat in BLOCK_PATTERNS:
        m = pat.search(key)
        if not m:
            continue
        old_idx = int(m.group("idx"))
        if old_idx not in old_to_new:
            return None, old_idx, None
        new_idx = old_to_new[old_idx]
        new_key = key[: m.start("idx")] + str(new_idx) + key[m.end("idx") :]
        return new_key, old_idx, new_idx
    return key, None, None


def detect_anima_28(keys):
    indices = []
    for key in keys:
        for pat in BLOCK_PATTERNS:
            for m in pat.finditer(key):
                indices.append(int(m.group("idx")))
    if not indices:
        return False
    return max(indices) <= 27


def remap_lora_dict(lora, manifest=None, fill_inserted="none"):
    if manifest is None:
        manifest = load_manifest()

    old_to_new, new_to_old, inserted_from = build_block_maps(
        manifest["old_block_count"],
        manifest["new_block_count"],
        manifest["insertion_positions"],
        manifest.get("inserted_to_source"),
    )

    src_to_inserts = {}
    for new_i, src_old in inserted_from.items():
        src_to_inserts.setdefault(int(src_old), []).append(new_i)

    out = {}
    unmapped = []
    stats = {
        "remapped": 0,
        "passthrough": 0,
        "unmapped": 0,
        "inserted_copied": 0,
        "collisions": 0,
    }

    for key, tensor in lora.items():
        new_key, old_idx, new_idx = remap_key(key, old_to_new)

        if old_idx is None:
            if new_key not in out:
                out[new_key] = tensor
                stats["passthrough"] += 1
            else:
                stats["collisions"] += 1
            continue

        if new_key is None:
            unmapped.append(key)
            stats["unmapped"] += 1
            continue

        out[new_key] = tensor
        stats["remapped"] += 1

        if fill_inserted == "copy" and old_idx in src_to_inserts:
            for dst in src_to_inserts[old_idx]:
                for pat in BLOCK_PATTERNS:
                    m = pat.search(key)
                    if m is None:
                        continue
                    ins_key = key[: m.start("idx")] + str(dst) + key[m.end("idx") :]
                    if ins_key not in out:
                        out[ins_key] = tensor.clone()
                        stats["inserted_copied"] += 1
                    else:
                        stats["collisions"] += 1
                    break

    return out, stats, unmapped
