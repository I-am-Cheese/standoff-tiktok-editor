#!/usr/bin/env python3
"""Bounded cache discovery and explicitly owned temporary-file cleanup."""
import argparse
import hashlib
import gzip
import json
import os
from pathlib import Path
import shutil
import time
import uuid
import xml.etree.ElementTree as ET

OWNER = 'standoff-tiktok-editor'
STATE = Path.home() / '.codex' / OWNER
REGISTRY = STATE / 'cache-registry.json'
MARKER = '.standoff-tiktok-editor-owned.json'


def load_registry():
    return json.loads(REGISTRY.read_text(encoding='utf-8')) if REGISTRY.exists() else {'format': 1, 'entries': []}


def save_registry(data):
    STATE.mkdir(parents=True, exist_ok=True)
    temp = REGISTRY.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(REGISTRY)


def protected_paths():
    paths = [Path.home() / 'Downloads', Path(__file__).resolve().parent.parent,
             STATE / 'profile.json', REGISTRY]
    profile = STATE / 'profile.json'
    if profile.exists():
        data = json.loads(profile.read_text(encoding='utf-8-sig'))
        for key in ['release_root', 'assets_dir', 'ledger_path', 'last_approved_release',
                    'latest_generated_release', 'historical_context', 'ffmpeg', 'premiere_executable']:
            if data.get(key):
                paths.append(Path(data[key]))
    return [p.resolve() for p in paths]


def safe_root(path):
    path = Path(path)
    if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
        raise ValueError('Owned cache root cannot be a symlink/junction.')
    root = path.resolve()
    if root == Path(root.anchor) or root == Path.home().resolve() or len(root.parts) < 3:
        raise ValueError('Refusing broad filesystem root.')
    for protected in protected_paths():
        if root == protected or root.is_relative_to(protected) or protected.is_relative_to(root):
            raise ValueError('Protected source/release/skill/state location: ' + str(root))
    return root


def signature(path):
    value = path.stat()
    return {'bytes': value.st_size, 'mtime_ns': value.st_mtime_ns}


def saved_media_references():
    profile = STATE / 'profile.json'
    if not profile.exists():
        return set()
    data = json.loads(profile.read_text(encoding='utf-8-sig'))
    roots = [Path(p) for p in data.get('project_roots', [])]
    if data.get('release_root'):
        roots.append(Path(data['release_root']).parent)
    references, seen = set(), set()
    for root in roots:
        if not root.is_dir(): continue
        for project in root.rglob('*.prproj'):
            if str(project.resolve()) in seen: continue
            seen.add(str(project.resolve()))
            try:
                raw=project.read_bytes()
                if raw[:2]==b'\x1f\x8b':raw=gzip.decompress(raw)
                raw=raw.replace(b"encoding='utf8'",b"encoding='utf-8'").replace(b'encoding="utf8"',b'encoding="utf-8"')
                xml=ET.fromstring(raw)
                for item in xml.iter('FilePath'):
                    if item.text:references.add(os.path.normcase(str(Path(item.text).resolve())))
            except (OSError,ValueError,ET.ParseError) as error:
                raise ValueError('Cannot inspect saved project references before cleanup: '+str(project)) from error
    return references


def register_owned(path, purpose, allowed_files=None):
    root = safe_root(path)
    marker = root / MARKER
    registry = load_registry()
    entry = next((e for e in registry['entries'] if e['path'] == str(root)), None)
    if marker.exists():
        stamp = json.loads(marker.read_text(encoding='utf-8'))
        if stamp.get('owner') != OWNER or (entry and stamp.get('token') != entry.get('token')):
            raise ValueError('Cache ownership marker mismatch.')
    else:
        stamp = {'owner': OWNER, 'token': uuid.uuid4().hex, 'purpose': purpose}
        marker.write_text(json.dumps(stamp), encoding='utf-8')
    if entry is None:
        entry = {'path': str(root), 'purpose': purpose, 'token': stamp['token'], 'files': {}}
        registry['entries'].append(entry)
    if allowed_files is not None:
        candidates = [root / name for name in allowed_files]
        for file in candidates:
            if not file.resolve().is_relative_to(root) or file.is_symlink():
                raise ValueError('Tracked file escapes owned cache.')
            if file.is_file():
                entry['files'][str(file.relative_to(root))] = signature(file)
    save_registry(registry)
    return root


def create_owned(parent, purpose='scratch'):
    parent = Path(parent).resolve()
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / (purpose + '-' + uuid.uuid4().hex[:12])
    safe_root(root)
    root.mkdir()
    register_owned(root, purpose, [])
    return root


def track(path):
    root = safe_root(path)
    registry = load_registry()
    entry = next((e for e in registry['entries'] if e['path'] == str(root)), None)
    if entry is None:
        raise ValueError('Only caches created/verified by this skill can be tracked.')
    files = [str(p.relative_to(root)) for p in root.rglob('*')
             if p.is_file() and not p.is_symlink() and p.name != MARKER and p.resolve().is_relative_to(root)]
    register_owned(root, entry['purpose'], files)
    return len(files)


def cleanup(apply=False, only=None):
    registry = load_registry()
    references = saved_media_references()
    removed, preserved, total = [], [], 0
    remaining = []
    for entry in registry['entries']:
        if only is not None and Path(entry['path']).resolve() != Path(only).resolve():
            remaining.append(entry); continue
        root = safe_root(entry['path'])
        if not root.exists():
            continue
        marker = root / MARKER
        if not marker.is_file() or json.loads(marker.read_text(encoding='utf-8')).get('token') != entry['token']:
            preserved.append({'path': str(root), 'reason': 'missing/mismatched ownership marker'})
            remaining.append(entry); continue
        still = {}
        for relative, old in entry['files'].items():
            file = root / relative
            if file.is_symlink() or not file.resolve().is_relative_to(root):
                preserved.append({'path': str(file), 'reason': 'symlink/outside owned root'}); still[relative] = old; continue
            if not file.exists():
                continue
            if os.path.normcase(str(file.resolve())) in references:
                preserved.append({'path':str(file),'reason':'referenced by saved Premiere project'});still[relative]=old;continue
            if not file.is_file() or signature(file) != old:
                preserved.append({'path': str(file), 'reason': 'changed after registration'}); still[relative] = old; continue
            total += old['bytes']; removed.append(str(file))
            if apply:
                file.unlink()
            else:
                still[relative] = old
        if apply:
            for folder in sorted((p for p in root.rglob('*') if p.is_dir() and not p.is_symlink()), key=lambda p: len(p.parts), reverse=True):
                if folder.resolve().is_relative_to(root):
                    try: folder.rmdir()
                    except OSError: pass
            other = [p for p in root.iterdir() if p.name != MARKER]
            if not other:
                marker.unlink(); root.rmdir()
            else:
                preserved.append({'path': str(root), 'reason': 'contains changed or unregistered files'})
                entry['files'] = still; remaining.append(entry)
        else:
            remaining.append(entry)
    if apply:
        registry['entries'] = remaining; save_registry(registry)
    return {'applied': apply, 'files': len(removed), 'bytes': total, 'preserved': preserved,
            'note': 'Only registered, unchanged owned temporary files. No user originals, final releases, installed skill or shared tools removed.'}


def find(name, roots, size=None, sha256=None, max_files=40000, max_depth=7):
    matches, seen, scanned, truncated = [], set(), 0, False
    for base in roots:
        base = Path(base).expanduser()
        if not base.is_dir(): continue
        for folder, dirs, files in os.walk(base, followlinks=False):
            depth = len(Path(folder).relative_to(base).parts)
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__'} and depth < max_depth]
            for filename in files:
                scanned += 1
                if scanned > max_files:
                    truncated = True; break
                if filename.lower() != name.lower(): continue
                path = Path(folder) / filename
                try:
                    resolved = path.resolve()
                    if str(resolved) in seen: continue
                    seen.add(str(resolved))
                    length = resolved.stat().st_size
                    if size is not None and length != size: continue
                    if sha256:
                        digest = hashlib.sha256()
                        with resolved.open('rb') as stream:
                            for data in iter(lambda: stream.read(1024*1024), b''): digest.update(data)
                        if digest.hexdigest() != sha256.lower(): continue
                    matches.append({'path': str(resolved), 'bytes': length})
                except OSError: continue
            if truncated: break
        if truncated: break
    return {'matches': matches, 'scanned_files': scanned, 'truncated': truncated,
            'note': 'Bounded search of supplied relevant roots, not proof of absence on every drive.'}


def known_roots(name):
    roots = []
    executable=shutil.which(name)
    if executable:roots.append(Path(executable).parent)
    profile=STATE/'profile.json'
    data=json.loads(profile.read_text(encoding='utf-8-sig')) if profile.exists() else {}
    for key in ['ffmpeg','premiere_executable']:
        if data.get(key) and Path(data[key]).name.lower()==name.lower():roots.append(Path(data[key]).parent)
    roots.extend([Path.cwd()/'work',STATE/'scratch',STATE/'session-history',Path.home()/'Downloads'])
    if data.get('release_root'):roots.append(Path(data['release_root']))
    roots.extend(Path(p) for p in data.get('search_roots',[]))
    roots.extend([Path.home()/'.cache/huggingface',Path.home()/'.cache/whisper'])
    if os.environ.get('TEMP'):roots.append(Path(os.environ['TEMP']))
    return list(dict.fromkeys(roots))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    commands = ap.add_subparsers(dest='command', required=True)
    p=commands.add_parser('create'); p.add_argument('--parent', type=Path, default=STATE/'scratch'); p.add_argument('--purpose', choices=['scratch','download-cache','model-cache'], default='scratch')
    p=commands.add_parser('track'); p.add_argument('path', type=Path)
    p=commands.add_parser('cleanup'); p.add_argument('--apply', action='store_true'); p.add_argument('--only', type=Path)
    p=commands.add_parser('find'); p.add_argument('--name', required=True); p.add_argument('--roots', nargs='+', type=Path); p.add_argument('--size', type=int); p.add_argument('--sha256'); p.add_argument('--max-files', type=int, default=40000); p.add_argument('--max-depth', type=int, default=7)
    p=commands.add_parser('space'); p.add_argument('path', type=Path); p.add_argument('--required-bytes', type=int, default=0); p.add_argument('--reserve-bytes', type=int, default=512*1024*1024)
    args=ap.parse_args()
    if args.command=='create': result={'owned_path':str(create_owned(args.parent,args.purpose))}
    elif args.command=='track': result={'tracked_files':track(args.path)}
    elif args.command=='cleanup': result=cleanup(args.apply,args.only)
    elif args.command=='find': result=find(args.name,args.roots or known_roots(args.name),args.size,args.sha256,args.max_files,args.max_depth)
    else:
        path=args.path.resolve()
        while not path.exists():path=path.parent
        usage=shutil.disk_usage(path)
        result={'free_bytes':usage.free,'required_bytes':args.required_bytes,'reserve_bytes':args.reserve_bytes,'can_fit':usage.free>=args.required_bytes+args.reserve_bytes}
    print(json.dumps(result,ensure_ascii=True,indent=2))


if __name__=='__main__': main()
