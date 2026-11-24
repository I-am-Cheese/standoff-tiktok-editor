# Local state and job contract

Do not put personal state into the installed skill or push it to the public repository. Store beside the user's releases, for example `local-state/profile.json`, `episodes.json`, `jobs/<id>.json`. Resolve paths explicitly; do not depend on this repository's creator's Windows username or old working directory.

Profile: `source_folder` (Drive URL or local folder), `release_root`, `ffmpeg`, optional `ffprobe`, `premiere_executable`, `assets_dir`, `preferred_language`, `current_rules_version`, `last_approved_release`, `ledger_path`. Ask once for genuinely missing access/branding; never ask again for a supplied choice. Optional model/budget preferences are explicit user configuration, not silently chosen worker overrides.

Optional `search_roots` lists additional local libraries/tool/model caches to inspect before downloads. Temporary ownership bookkeeping is separate: `~/.codex/standoff-tiktok-editor/cache-registry.json`. Use cache_tools create/track rather than treating every cache or old project as disposable. A job may set `scratch_root`; otherwise rendering uses an owned cache outside permanent release Media. See cache-and-downloads.md for the cleanup command and download/wait policy.

Ledger: `{ "format": 1, "releases": [{ "release": "id", "music": "title", "musicStart": 0.0, "musicEnd": 30.0, "introFrames": 180, "totalFrames": 1800, "supersededBy": null, "shots": [{ "slot": 1, "file": "stable-source-id", "sourceStart": 20.0, "sourceEnd": 20.35, "anchor": 20.30, "frames": 21, "event_id": "source-id:kill-03", "kind": "combat", "reuseAcrossVideos": false }] }] }`.

Keep original names, private Drive IDs, file size/hash, time base, orientation, normalization, downloaded/cached path and SELECTS-handle mapping in local source records. Superseded versions remain history; don't double count them as active releases. Check overlapping intervals AND event identity: different adjacent frames may show the same kill. Log decisions and observable evidence, never claim to archive hidden internal reasoning.

Query large ledgers with `scripts/ledger_tools.py --ledger path --source original-filename`, optionally `--anchor seconds --radius .55`. Without --source it returns a compact inventory. Consult all releases for freshness; use --active-only only for release frequency statistics. Do not paste the complete ledger or 16,000 historical frame rows into model context. Let a local script filter overlap/event checks and return only relevant results.

`render_montage.py --job job.json --output-dir release --ffmpeg ffmpeg` reads:

```json
{
  "title": "EXAMPLE",
  "fps": 60,
  "music": "music.wav",
  "music_start": 3.9,
  "total_frames": 1770,
  "intro_frames": 154,
  "fade_seconds": 2.814375,
  "logo_boundaries": [0, 25, 46, 68, 89, 111, 132, 154],
  "assets_dir": "path/to/skill/assets",
  "sources": {
    "source-01": {"path": "recording.mp4", "normalize_filter": "", "crop_filter": "crop=567:576:357:72,scale=720:732:flags=lanczos"}
  },
  "shots": [
    {"source": "source-01", "anchor": 44.8337, "frames": 25, "event_id": "kill-001", "kind": "combat", "reviewed": true}
  ]
}
```

The example has only one illustrative shot; a real job must fill `total_frames - intro_frames` exactly. Logo boundaries are relative to output, integer 60fps frames. Source anchors in source seconds. Default tail is 3 frames, configurable `tail_frames` per shot. `kind` is `combat` or `movement`. Every shot requires a stable `event_id` and explicit visual `reviewed: true`. Optional `repeat_justification` permits at most two repeated events; optional source `source_fps` defaults 60 for audit only, actual fps must be probed. Optional `normalize_filter` maps unusual orientations into the canonical 1280×720 view BEFORE crop; don't guess it.

Builder plan emitted by renderer: title, fps, total_frames, intro_frames, fade_seconds, montage_source, chad_overlay (transparent full 720×732 canvas), audio (already trimmed/faded WAV), logo_steps (`path/start_frame/end_frame`), shots (`start_frame/end_frame/source_in_frame/source_out_frame/source_label`), sources[], graphics[], references[]. All times are integer output frames except source audit seconds. Builder paths may be absolute or relative to the plan file. The examples with real timing are evidence, not assets or ready-to-render jobs.
