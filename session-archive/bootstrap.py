#!/usr/bin/env python3
"""Always verify and materialize the saved history before a coordinator uses the skill."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache-dir', type=Path, help='Parent cache folder; a hash-specific subfolder is created.')
    args = ap.parse_args()
    package = Path(__file__).resolve().parent
    manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
    buffers = []
    for part in manifest['parts']:
        path = package / part['file']
        if path.parent.resolve() != package or path.is_symlink():
            raise ValueError('Invalid archive part path.')
        data = path.read_bytes()
        if len(data) != part['bytes'] or digest(data) != part['sha256']:
            raise ValueError('Archive part checksum mismatch: ' + part['file'])
        buffers.append(data)
    data = b''.join(buffers)
    if len(data) != manifest['archive_bytes'] or digest(data) != manifest['archive_sha256']:
        raise ValueError('Original session ZIP checksum mismatch.')
    parent = args.cache_dir or Path.home() / '.codex' / 'standoff-tiktok-editor' / 'session-history'
    cache = (parent / manifest['archive_sha256'][:16]).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    expected = {entry['path']: entry for entry in manifest['files']}
    archive = zipfile.ZipFile(io.BytesIO(data))
    if len(archive.infolist()) != len(expected) or set(archive.namelist()) != set(expected):
        raise ValueError('Archive entry list differs from manifest.')
    checked = 0
    for info in archive.infolist():
        relative = PurePosixPath(info.filename.replace('\\', '/'))
        if relative.is_absolute() or '..' in relative.parts or any(':' in p for p in relative.parts):
            raise ValueError('Unsafe archive entry: ' + info.filename)
        if stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError('Symlink archive entry is not allowed.')
        target = cache.joinpath(*relative.parts)
        if not target.resolve().is_relative_to(cache):
            raise ValueError('Archive target escapes cache.')
        content = archive.read(info)
        entry = expected[info.filename]
        if len(content) != entry['bytes'] or digest(content) != entry['sha256']:
            raise ValueError('Entry checksum mismatch: ' + info.filename)
        if target.exists():
            if not target.is_file() or target.is_symlink() or digest(target.read_bytes()) != entry['sha256']:
                raise ValueError('Cached entry changed; use a new --cache-dir: ' + str(target))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as output:
                output.write(content)
        checked += 1
    context = cache / 'outputs' / 'Контекст монтажа.md'
    ledger = cache / 'outputs' / 'Учёт использованных эпизодов.json'
    if not context.is_file() or not ledger.is_file():
        raise ValueError('Mandatory historical context/ledger absent.')
    report = {
        'archive_sha256': manifest['archive_sha256'], 'verified_entries': checked,
        'archive_root': str(cache), 'mandatory_historical_context': str(context),
        'historical_episode_ledger': str(ledger), 'complete_entry_index': str(package / 'manifest.json'),
        'mandatory_current_rules': str(package.parent / 'references' / 'editing-rules.md'),
        'next_action': 'Coordinator reads the complete historical context and current rules once in each new chat. Use current owner profile/ledger for live state. Workers receive this receipt and a bounded briefing; do not reread all history per worker.',
        'limits': 'This verifies saved artifacts, not hidden model state or proof that every image was visually reviewed.'
    }
    (cache / 'bootstrap-receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    sys.path.insert(0, str(package.parent / 'scripts'))
    from cache_tools import register_owned
    register_owned(cache, 'history-cache', list(expected) + ['bootstrap-receipt.json'])
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
