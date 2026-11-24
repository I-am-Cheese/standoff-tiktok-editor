#!/usr/bin/env python3
"""Reassemble the exact original session ZIP from verified repository parts."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, default=Path('restored-session-evidence.zip'))
    args = ap.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    if args.output.exists():
        ap.error('Output already exists; choose a new --output path.')
    data = []
    for entry in manifest['parts']:
        path = root / entry['file']
        if path.parent.resolve() != root:
            ap.error('Invalid part path in manifest.')
        content = path.read_bytes()
        if len(content) != entry['bytes'] or hashlib.sha256(content).hexdigest() != entry['sha256']:
            ap.error('Part checksum mismatch: ' + path.name)
        data.append(content)
    content = b''.join(data)
    if len(content) != manifest['archive_bytes'] or hashlib.sha256(content).hexdigest() != manifest['archive_sha256']:
        ap.error('Reassembled archive checksum mismatch.')
    with args.output.open('xb') as output:
        output.write(content)
    print('Verified original archive:', args.output.resolve())
    print('Entries:', manifest['entries_including_archive_readme'])
    print('SHA-256:', manifest['archive_sha256'])


if __name__ == '__main__':
    main()
