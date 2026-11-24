#!/usr/bin/env python3
"""Audit a saved Premiere gzip XML project without launching Premiere."""
import argparse
import gzip
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def verify(project, shots, release=None):
    if shots < 1:
        raise ValueError("--shots must be positive")
    try:
        with gzip.open(project, "rb") as stream:
            root = ET.fromstring(stream.read())
    except (OSError, ET.ParseError) as exc:
        raise ValueError("Cannot read native Premiere gzip XML: %s" % exc) from exc
    ids = {e.get("ObjectID"): e for e in root if e.get("ObjectID")}
    uids = {e.get("ObjectUID"): e for e in root if e.get("ObjectUID")}

    def resolve(node, index, attr, context):
        if node is None or node.get(attr) not in index:
            raise ValueError("Missing or unresolved %s reference" % context)
        return index[node.get(attr)]

    def object_ref(node, selector, context):
        return resolve(node.find(selector), ids, "ObjectRef", context)

    def tracks(seq):
        group = object_ref(seq, ".//Second", "sequence video track group")
        return [resolve(n, uids, "ObjectURef", "video track") for n in group.findall(".//Track")]

    def clips(track):
        result = []
        for ref in track.findall(".//TrackItem"):
            item = resolve(ref, ids, "ObjectRef", "track item")
            sub = object_ref(item, ".//SubClip", "subclip")
            clip = object_ref(sub, "Clip", "clip")
            result.append((sub, clip))
        return result

    sequences = root.findall("Sequence")
    if len(sequences) != 3:
        raise ValueError("Expected exactly three native sequences; found %d" % len(sequences))
    def sequence(prefix):
        found = [s for s in sequences if s.findtext("Name", "").startswith(prefix)]
        if len(found) != 1:
            raise ValueError("Expected one sequence named %s; found %d" % (prefix, len(found)))
        return found[0]
    main, game = sequence("MAIN - "), sequence("02 GAMEPLAY")
    sequence("01 INTRO")
    project_root = root.find("RootProjectItem")
    if project_root is None:
        raise ValueError("Native project root container missing")
    root_items = [resolve(n, uids, "ObjectURef", "root project item") for n in project_root.findall("./ProjectItemContainer/Items/Item")]
    main_name = main.findtext("Name")
    matching = [n for n in root_items if n.findtext(".//Name") == main_name]
    if len(matching) != 1:
        raise ValueError("MAIN must appear exactly once directly in the project root")
    game_tracks = tracks(game)
    if not game_tracks:
        raise ValueError("Gameplay has no video tracks")
    cuts = clips(game_tracks[0])
    if len(cuts) != shots:
        raise ValueError("Expected %d gameplay cuts; found %d" % (shots, len(cuts)))
    ins = [c.findtext(".//InPoint") for _, c in cuts]
    if any(v is None for v in ins) or len(set(ins)) != shots:
        raise ValueError("Gameplay source in-points are missing or not distinct")
    sources = []
    for tr in tracks(main):
        for sub, clip in clips(tr):
            if sub.findtext("Name") in ("BACKGROUND - SAME GAMEPLAY", "GAMEPLAY"):
                source = object_ref(clip, ".//Source", "nested sequence source")
                ref = source.find(".//Sequence")
                resolve(ref, uids, "ObjectURef", "nested sequence UID")
                sources.append(ref.get("ObjectURef"))
    if len(sources) != 2 or sources[0] != sources[1] or sources[0] != game.get("ObjectUID"):
        raise ValueError("MAIN foreground and background must reference the same GAMEPLAY sequence UID")
    paths = [n.text for n in root.iter("FilePath")]
    if not paths:
        raise ValueError("Project contains no FilePath media records")
    release = Path(release).resolve() if release else None
    for raw in paths:
        if not raw:
            raise ValueError("Empty FilePath media record")
        p = Path(raw)
        if not p.is_absolute():
            raise ValueError("Media FilePath is not absolute: %s" % raw)
        if not p.is_file():
            raise ValueError("Media is missing: %s" % raw)
        if release and not p.resolve().is_relative_to(release):
            raise ValueError("Media lies outside release directory: %s" % raw)
    return {"sequences": len(sequences), "shots": len(cuts), "distinct_in_points": len(set(ins)), "media_records": len(paths), "main_at_root": True, "shared_gameplay": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--shots", required=True, type=int)
    parser.add_argument("--release", type=Path, help="Require all media inside this delivery directory")
    args = parser.parse_args()
    try:
        result = verify(args.project, args.shots, args.release)
    except (ValueError, OSError) as exc:
        parser.exit(2, "Verification failed: %s\n" % exc)
    print("Verified: %d sequences, %d distinct gameplay in-points, %d existing media records, MAIN at root, shared foreground/background" % (result["sequences"], result["shots"], result["media_records"]))


if __name__ == "__main__":
    main()
