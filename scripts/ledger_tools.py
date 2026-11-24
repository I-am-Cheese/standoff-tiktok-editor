#!/usr/bin/env python3
"""Query a local episode ledger without loading its contents into model context."""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ledger', type=Path, required=True)
    ap.add_argument('--source', help='Exact original filename or stable source ID; omit for compact inventory.')
    ap.add_argument('--anchor', type=float, help='Return events within --radius seconds or overlapping that point.')
    ap.add_argument('--radius', type=float, default=.55)
    ap.add_argument('--active-only', action='store_true', help='Omit superseded versions for frequency counts, not freshness claims.')
    args = ap.parse_args()
    data = json.loads(args.ledger.read_text(encoding='utf-8-sig'))
    releases = data.get('releases', [])
    if args.active_only:
        releases = [r for r in releases if not r.get('supersededBy')]
    if not args.source:
        sources = {}
        for release in releases:
            for shot in release.get('shots', []):
                name = shot.get('file', shot.get('source_id', '?'))
                sources.setdefault(name, {'plans': 0, 'releases': []})['plans'] += 1
                if release['release'] not in sources[name]['releases']:
                    sources[name]['releases'].append(release['release'])
        result = {'release_count': len(releases), 'sources': sources,
                  'note': 'Counts include historical revisions unless --active-only; never infer unique kills from plans.'}
    else:
        matches = []
        for release in releases:
            for shot in release.get('shots', []):
                if args.source not in [shot.get('file'), shot.get('source_id')]:
                    continue
                anchor = shot.get('anchor', shot.get('sourceStart', 0))
                if args.anchor is not None and abs(anchor - args.anchor) > args.radius:
                    if not shot.get('sourceStart', anchor) <= args.anchor < shot.get('sourceEnd', anchor):
                        continue
                matches.append({'release': release['release'], **{k: shot[k] for k in
                    ['slot', 'sourceStart', 'sourceEnd', 'anchor', 'frames', 'event_id', 'kind'] if k in shot}})
        result = {'source': args.source, 'matches': matches}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
