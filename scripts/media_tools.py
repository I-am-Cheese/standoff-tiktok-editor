#!/usr/bin/env python3
"""Small FFmpeg-backed probe, onset candidates, and contact-sheet helpers."""
import argparse
import io
import json
import re
import shutil
import subprocess
from pathlib import Path


def binary(value):
    result = shutil.which(value) or (str(Path(value).resolve()) if Path(value).is_file() else None)
    if not result:
        raise ValueError(f'Executable unavailable: {value}')
    return result


def run(argv):
    result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', 'replace')[-4000:])
    return result.stdout


def probe(path, ffmpeg, ffprobe=None):
    if ffprobe:
        return json.loads(run([binary(ffprobe), '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)]))
    result = subprocess.run([ffmpeg, '-hide_banner', '-i', str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stderr = result.stderr.decode('utf-8', 'replace')
    # FFmpeg -i exits nonzero when no output is given. Keep actual metadata text.
    if 'Input #' not in stderr:
        raise RuntimeError(stderr[-3000:])
    match = re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)', stderr)
    duration = sum(float(x) * mul for x, mul in zip(match.groups(), (3600, 60, 1))) if match else None
    return {'duration_seconds': duration, 'ffmpeg_metadata': stderr}


def analyze(args, ffmpeg):
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError('Onset analysis needs numpy. Probe does not; use existing environment or inspect audio manually.') from exc
    channel_filter = {'mix': 'aformat=channel_layouts=mono', 'left': 'pan=mono|c0=c0', 'right': 'pan=mono|c0=c1'}[args.channel]
    argv = [ffmpeg, '-v', 'error', '-ss', str(args.start), '-i', str(args.input)]
    if args.duration:
        argv += ['-t', str(args.duration)]
    raw = run(argv + ['-vn', '-af', channel_filter, '-ar', '16000', '-f', 'f32le', '-'])
    audio = np.frombuffer(raw, dtype='<f4')
    win, hop, sample_rate = 1024, 160, 16000
    if len(audio) < win:
        raise ValueError('Audio window too short.')
    frequencies = np.fft.rfftfreq(win, 1 / sample_rate)
    previous = None
    flux, energy = [], []
    for offset in range(0, len(audio) - win + 1, hop):
        spectrum = np.abs(np.fft.rfft(audio[offset:offset + win] * np.hanning(win)))
        high = spectrum[frequencies >= 5000]
        flux.append(float(np.maximum(high - previous, 0).sum()) if previous is not None else 0)
        energy.append(float(spectrum.sum()))
        previous = high
    values = np.asarray(flux)
    threshold = float(np.median(values) + 2 * np.median(np.abs(values - np.median(values))))
    peaks = [i for i in range(1, len(values) - 1) if values[i] > threshold and values[i] >= values[i - 1] and values[i] > values[i + 1]]
    # Suppress nearby transients, preserve timing/strength; no false instrument labels.
    selected = []
    for i in sorted(peaks, key=lambda i: values[i], reverse=True):
        if all(abs(i - j) >= 8 for j in selected):
            selected.append(i)
    candidates = [{'seconds': round(args.start + (i * hop + win / 2) / sample_rate, 6), 'strength': round(float(values[i]), 4)} for i in sorted(selected)]
    result = {'sample_rate': sample_rate, 'analysis_channel': args.channel, 'start': args.start,
              'duration': len(audio) / sample_rate, 'candidates': candidates,
              'warning': 'Percussive candidates only; not verified beats, chorus boundaries, instrument labels or lyrics.'}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {len(candidates)} onset candidates to {args.output}')


def sheet(args, ffmpeg):
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError('Contact sheets need Pillow. Probe/analysis do not.') from exc
    frames = []
    for seconds in args.times:
        filters = (args.filter + ',' if args.filter else '') + f'scale={args.width}:-1'
        raw = run([ffmpeg, '-v', 'error', '-ss', str(seconds), '-i', str(args.input), '-vf', filters,
                   '-frames:v', '1', '-f', 'image2pipe', '-c:v', 'png', '-'])
        frames.append(Image.open(io.BytesIO(raw)).convert('RGB'))
    tile_height = max(im.height for im in frames) + 26
    cols = min(args.columns, len(frames))
    canvas = Image.new('RGB', (cols * args.width, ((len(frames) + cols - 1) // cols) * tile_height), '#181818')
    draw = ImageDraw.Draw(canvas)
    for i, (seconds, image) in enumerate(zip(args.times, frames)):
        x, y = i % cols * args.width, i // cols * tile_height
        canvas.paste(image, (x, y))
        draw.text((x + 3, y + image.height + 4), f'{seconds:.3f}s', fill='white')
    canvas.save(args.output)
    print(args.output)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ffmpeg', default='ffmpeg')
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('probe'); p.add_argument('input', type=Path); p.add_argument('--ffprobe')
    p = sub.add_parser('analyze'); p.add_argument('input', type=Path); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--start', type=float, default=0); p.add_argument('--duration', type=float)
    p.add_argument('--channel', choices=['mix', 'left', 'right'], default='mix')
    p = sub.add_parser('sheet'); p.add_argument('input', type=Path); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--times', type=float, nargs='+', required=True); p.add_argument('--filter', default='')
    p.add_argument('--width', type=int, default=240); p.add_argument('--columns', type=int, default=4)
    args = ap.parse_args(); ffmpeg = binary(args.ffmpeg)
    if args.command == 'probe':
        print(json.dumps(probe(args.input, ffmpeg, args.ffprobe), ensure_ascii=False, indent=2))
    elif args.command == 'analyze':
        analyze(args, ffmpeg)
    else:
        sheet(args, ffmpeg)


if __name__ == '__main__':
    main()
