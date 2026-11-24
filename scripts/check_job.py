#!/usr/bin/env python3
"""Validate timing and source-event invariants; not a visual kill detector."""
import argparse
import json
from collections import Counter
from pathlib import Path


def validate(job):
    errors, warnings = [], []
    fps = job.get('fps', 60)
    total, intro = job.get('total_frames', 0), job.get('intro_frames', 0)
    if fps != 60:
        errors.append('This baseline renderer expects 60 fps.')
    if not isinstance(total, int) or not isinstance(intro, int) or not 0 < intro < total:
        errors.append('total_frames and intro_frames must be positive integer frame counts.')
    if fps and not 28 <= total / fps <= 35:
        warnings.append('Duration outside the default 28–35s; require an explicit reason.')
    bounds = job.get('logo_boundaries', [])
    if (len(bounds) != 8 or any(not isinstance(x, int) for x in bounds)
            or bounds[:1] != [0] or bounds[-1:] != [intro]
            or any(b <= a for a, b in zip(bounds, bounds[1:]))):
        errors.append('Seven logo stages need eight increasing integer boundaries from 0 to intro_frames.')
    sources, shots = job.get('sources', {}), job.get('shots', [])
    events, intervals = Counter(), []
    movement, combat, frame_sum = 0, 0, 0
    for i, shot in enumerate(shots, 1):
        source = shot.get('source')
        frames = shot.get('frames', 0)
        tail = shot.get('tail_frames', 3)
        anchor = shot.get('anchor')
        if not isinstance(frames, int) or frames <= 0:
            errors.append(f'Slot {i}: frames must be a positive integer.')
            continue
        frame_sum += frames
        if not isinstance(tail, int) or not 0 <= tail < frames:
            errors.append(f'Slot {i}: invalid tail_frames.')
            continue
        if source not in sources:
            errors.append(f'Slot {i}: missing source {source!r}.')
        if shot.get('reviewed') is not True:
            errors.append(f'Slot {i}: visual review not recorded.')
        if not shot.get('event_id'):
            errors.append(f'Slot {i}: stable event_id required.')
        event = (source, shot.get('event_id'))
        events[event] += 1
        if events[event] > 1 and not shot.get('repeat_justification'):
            errors.append(f'Slot {i}: repeated event needs a deliberate justification.')
        kind = shot.get('kind', 'combat')
        if kind == 'movement':
            movement += 1
        elif kind == 'combat':
            combat += 1
        else:
            errors.append(f'Slot {i}: invalid kind {kind!r}.')
        if not isinstance(anchor, (float, int)):
            errors.append(f'Slot {i}: numeric source anchor required.')
            continue
        start = anchor - (frames - tail) / fps
        end = start + frames / fps
        if start < 0:
            errors.append(f'Slot {i}: source starts before zero.')
        for old_source, a, b, old_event, old_i in intervals:
            if source == old_source and min(end, b) - max(start, a) > 1e-6:
                deliberate = event == old_event and bool(shot.get('repeat_justification'))
                if not deliberate:
                    errors.append(f'Slots {old_i}/{i}: source intervals overlap.')
        intervals.append((source, start, end, event, i))
        if frames / fps > .5:
            warnings.append(f'Slot {i}: longer than .5s; inspect for idle tails.')
    if frame_sum != total - intro:
        errors.append(f'Gameplay frames {frame_sum} do not fill expected {total - intro}.')
    if movement > 2:
        errors.append('At most two deliberate movement inserts per video.')
    repeated = [n for n in events.values() if n > 1]
    if len(repeated) > 2 or any(n > 2 for n in repeated):
        errors.append('At most two events may be repeated once each; no loop blocks.')
    seconds = (total - intro) / fps if fps and total > intro else 0
    density = combat / seconds if seconds else 0
    if not 2 <= density <= 3:
        warnings.append(f'Combat-plan density {density:.3f}/s differs from 2–3 target. This is not a kill count.')
    return {'ok': not errors, 'errors': errors, 'warnings': warnings,
            'shots': len(shots), 'combat_plans': combat, 'movement_inserts': movement,
            'combat_plans_per_gameplay_second': round(density, 4)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('job', type=Path)
    args = ap.parse_args()
    result = validate(json.loads(args.job.read_text(encoding='utf-8-sig')))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
