#!/usr/bin/env python3
"""Render visually reviewed 60fps shots, SELECTS and a portable Premiere plan."""
import argparse
import atexit
import json
import re
import shutil
import subprocess
from pathlib import Path
from check_job import validate
from cache_tools import create_owned, track

STAGES = ['3.55', '7', '12', '18', '24', '30', '37']


def track_if_present(path):
    if Path(path).is_dir():
        track(path)


def render(job_path, release, ffmpeg):
    job = json.loads(job_path.read_text(encoding='utf-8-sig'))
    result = validate(job)
    if not result['ok']:
        raise ValueError(json.dumps(result, ensure_ascii=False))
    if release.exists() and any(release.iterdir()):
        raise ValueError('Output directory must be empty: preserve previous releases.')
    release.mkdir(parents=True, exist_ok=True)
    release = release.resolve()
    def resolve(value):
        path = Path(value)
        path = path if path.is_absolute() else job_path.parent / path
        if not path.exists():
            raise ValueError(f'Input unavailable: {path}')
        return path.resolve()
    music = resolve(job['music'])
    assets = resolve(job.get('assets_dir', str(Path(__file__).resolve().parent.parent / 'assets')))
    source_specs = job['sources']
    resolved_sources = {key: resolve(spec['path']) for key, spec in source_specs.items()}
    for name in ['Chad overlay.png'] + [f'Exit {stage} percent.png' for stage in STAGES]:
        if not (assets / name).is_file():
            raise ValueError(f'Missing original branding asset: {name}')
    folders = {name: release / 'Media' / name for name in ['01 Sources', '02 Graphics', '03 Music', '04 References', '05 Prepared clips']}
    for path in folders.values():
        path.mkdir(parents=True, exist_ok=True)
    scratch = create_owned(Path(job.get('scratch_root', Path.home()/'.codex/standoff-tiktok-editor/scratch')), 'scratch')
    atexit.register(track_if_present, scratch)
    def ff(*args):
        subprocess.run([ffmpeg, '-v', 'error', '-nostdin', '-y', *map(str, args)], check=True)
    def concat(pieces, output, label):
        manifest = scratch / f'{label}.ffconcat'
        # FFmpeg concat escaping, not shell interpolation. File names may contain apostrophes.
        manifest.write_text('\n'.join("file '" + str(path.resolve()).replace('\\', '/').replace("'", "'\\''") + "'" for path in pieces), encoding='utf-8')
        ff('-f', 'concat', '-safe', '0', '-i', manifest, '-c', 'copy', output)
    graphics = []
    for name in ['Chad overlay.png', 'Chad.png', 'Exit.png'] + [f'Exit {stage} percent.png' for stage in STAGES]:
        if (assets / name).is_file():
            target = folders['02 Graphics'] / name
            shutil.copy2(assets / name, target)
            if name in ['Chad.png', 'Exit.png']:
                graphics.append(str(target))
    full_music = folders['03 Music'] / 'Full music.wav'
    trimmed_music = folders['03 Music'] / 'Selected music.wav'
    ff('-i', music, '-vn', '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', full_music)
    fps = 60; duration = job['total_frames'] / fps; fade = job.get('fade_seconds', 2.814375)
    ff('-ss', job['music_start'], '-i', full_music, '-t', duration,
       '-af', f'afade=t=in:d=0.008,afade=t=out:st={duration-fade}:d={fade}', trimmed_music)
    pieces, handles, audit, shots, cursor = [], {}, [], [], 0
    for i, shot in enumerate(job['shots'], 1):
        key = shot['source']; spec = source_specs[key]; source = resolved_sources[key]
        frames = shot['frames']; tail = shot.get('tail_frames', 3); anchor = shot['anchor']
        start = anchor - (frames - tail) / fps
        filters = [spec.get('normalize_filter', '').strip(','), 'fps=60',
                   spec.get('crop_filter', 'crop=567:576:357:72,scale=720:732:flags=lanczos')]
        piece = scratch / f'Shot {i:03}.mp4'
        ff('-ss', start, '-i', source, '-vf', ','.join(x for x in filters if x), '-frames:v', frames,
           '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '15', '-pix_fmt', 'yuv420p', piece)
        pieces.append(piece)
        handle_start = max(0, anchor - .65)
        group = handles.setdefault(key, [])
        handle = scratch / f'Handle {i:03}.mp4'
        ff('-ss', handle_start, '-i', source, '-vf', 'fps=60', '-frames:v', '72', '-an',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p', handle)
        excerpt_anchor = len(group) * 1.2 + anchor - handle_start
        group.append(handle)
        safe_key = re.sub(r'[^A-Za-z0-9_-]', '_', str(key))
        # Include index to avoid collisions between sanitized user source names.
        source_index = list(source_specs).index(key) + 1
        excerpt_name = f'{source_index:02}-{safe_key}-SELECTS.mp4'
        audit.append({'slot': i, 'file': source.name, 'source_id': key, 'event_id': shot['event_id'],
                      'sourceStart': start, 'sourceEnd': start + frames/fps, 'anchor': anchor,
                      'frames': frames, 'kind': shot.get('kind', 'combat'),
                      'reuseAcrossVideos': shot.get('reuseAcrossVideos', False),
                      'sourceExcerpt': excerpt_name, 'excerptAnchor': excerpt_anchor,
                      'originalExcerptStart': handle_start, 'normalize_filter': spec.get('normalize_filter', ''),
                      'crop_filter': spec.get('crop_filter', 'crop=567:576:357:72,scale=720:732:flags=lanczos')})
        shots.append({'start_frame': cursor, 'end_frame': cursor + frames, 'source_in_frame': cursor,
                      'source_out_frame': cursor + frames, 'source_label': f'{key} @ {start:.6f}s'})
        cursor += frames
        if i % 20 == 0:
            print(f'Prepared {i}/{len(job["shots"])}', flush=True)
    source_paths = []
    for key, group in handles.items():
        row = next(row for row in audit if row['source_id'] == key)
        path = folders['01 Sources'] / row['sourceExcerpt']
        concat(group, path, f'handles-{len(source_paths)}'); source_paths.append(str(path))
    bundle = folders['05 Prepared clips'] / 'Montage source.mp4'
    concat(pieces, bundle, 'montage')
    steps = [{'path': str(folders['02 Graphics'] / f'Exit {stage} percent.png'),
              'start_frame': job['logo_boundaries'][i], 'end_frame': job['logo_boundaries'][i+1]} for i, stage in enumerate(STAGES)]
    plan = {'title': job['title'], 'fps': fps, 'total_frames': job['total_frames'], 'intro_frames': job['intro_frames'],
            'fade_seconds': fade, 'montage_source': str(bundle), 'chad_overlay': str(folders['02 Graphics'] / 'Chad overlay.png'),
            'audio': str(trimmed_music), 'logo_steps': steps, 'shots': shots,
            'sources': source_paths, 'graphics': graphics, 'references': []}
    (release / 'premiere-plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
    (release / 'Used episodes.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    (release / 'Job validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    track(scratch)
    print(f'Ready: {cursor} gameplay frames. Registered scratch retained for QA: {scratch}. Build Premiere next.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--job', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--ffmpeg', default='ffmpeg')
    args = ap.parse_args()
    executable = shutil.which(args.ffmpeg) or (str(Path(args.ffmpeg).resolve()) if Path(args.ffmpeg).is_file() else None)
    if not executable:
        ap.error('FFmpeg unavailable; provide --ffmpeg path.')
    render(args.job.resolve(), args.output_dir, executable)


if __name__ == '__main__':
    main()
