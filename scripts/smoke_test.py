#!/usr/bin/env python3
"""Short synthetic integration test; no network, Adobe launch or user media."""
import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
from check_job import validate
from render_montage import render
from build_premiere import build
from media_tools import binary, probe


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ffmpeg', default='ffmpeg')
    args = ap.parse_args(); ffmpeg = binary(args.ffmpeg)
    assets = Path(__file__).resolve().parent.parent / 'assets'
    # ASCII apostrophe and Cyrillic test both URI and ffconcat path escaping.
    with tempfile.TemporaryDirectory(prefix="монтаж's-smoke-") as temp:
        folder = Path(temp)
        source, audio = folder / 'video.mp4', folder / 'audio.wav'
        subprocess.run([ffmpeg, '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=1280x720:rate=60',
                        '-t', '8', '-an', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '32', str(source)], check=True)
        subprocess.run([ffmpeg, '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000',
                        '-t', '8', '-ac', '2', str(audio)], check=True)
        job = {'title': 'Synthetic test', 'fps': 60, 'music': str(audio), 'music_start': .1,
               'total_frames': 360, 'intro_frames': 120, 'fade_seconds': 2.814375,
               'logo_boundaries': [0, 17, 34, 51, 68, 85, 102, 120], 'assets_dir': str(assets),
               'sources': {'test': {'path': str(source)}},
               'shots': [{'source': 'test', 'anchor': .8 + i * .8, 'frames': 30, 'event_id': f'test-{i}',
                          'kind': 'combat', 'reviewed': True} for i in range(8)]}
        assert validate(job)['ok']
        bad = json.loads(json.dumps(job)); bad['shots'][1]['event_id'] = 'test-0'
        assert not validate(bad)['ok'], 'Duplicate event escaped validation'
        bad = json.loads(json.dumps(job)); bad['shots'][0]['frames'] += 1
        assert not validate(bad)['ok'], 'Off-by-one escaped validation'
        job_path = folder / 'job.json'; job_path.write_text(json.dumps(job), encoding='utf-8')
        release = folder / 'release'
        render(job_path, release, ffmpeg)
        plan_path = release / 'premiere-plan.json'
        xml, jsx = build(plan_path, release, assets / 'vertical-h264.epr')
        root = ET.parse(xml).getroot()
        assert len([e for e in root.iter('sequence') if e.find('name') is not None]) == 3
        files = [e for e in root.iter('file') if e.get('id') == 'montage-source']
        assert len([e for e in files if e.find('pathurl') is not None]) == 1
        bundle = release / 'Media/05 Prepared clips/Montage source.mp4'
        decoded = subprocess.run([ffmpeg, '-v', 'error', '-i', str(bundle), '-f', 'framemd5', '-'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        count = len([line for line in decoded.stdout.splitlines() if line and not line.startswith(b'#')])
        assert count == 240, count
        subprocess.run([sys.executable, str(Path(__file__).with_name('media_tools.py')), '--ffmpeg', ffmpeg,
                        'probe', str(bundle)], stdout=subprocess.DEVNULL, check=True)
        if importlib.util.find_spec('numpy'):
            subprocess.run([sys.executable, str(Path(__file__).with_name('media_tools.py')), '--ffmpeg', ffmpeg,
                            'analyze', str(audio), '--duration', '2', '--output', str(folder/'onsets.json')], check=True)
        try:
            build(plan_path, release)
            raise AssertionError('Overwrite protection failed')
        except ValueError as error:
            assert 'overwrite' in str(error).lower()
    print('PASS: review/timing/event checks, synthetic render, SELECTS, quoted Unicode paths, 240 decoded frames, shared montage XML and overwrite protection. Adobe not launched.')


if __name__ == '__main__':
    main()
