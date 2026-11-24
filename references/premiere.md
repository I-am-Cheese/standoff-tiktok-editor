# Premiere Pro 2024 delivery

`scripts/build_premiere.py` uses Python 3.9+ and the standard library. It generates `timeline.xml` (UTF-8 FCP XML v5) and `import.jsx`. It never launches Premiere, saves a native project, or runs an export itself. Explicitly run the generated JSX through an available Premiere scripting runner after reviewing it. The runner must execute ExtendScript in Premiere Pro 2024.

```
python scripts/build_premiere.py --plan plan.json --output-dir delivery
python scripts/verify_project.py "delivery/Example.prproj" --shots 2 --release delivery
```

Plan media paths may be absolute or relative to the plan's directory. For a portable release, place every referenced medium, including optional originals, inside the delivery folder before building. The generated XML/JSX contains resolved absolute paths; rebuild it after moving to another computer before importing. A saved native project may also require Premiere's Link Media dialog after relocation. Multilingual paths are preserved through UTF-8 XML, URI encoding, and JSON-escaped ExtendScript strings.

Minimal plan (example has two seconds of intro and four seconds of gameplay):

```json
{
  "title": "Example",
  "fps": 60,
  "total_frames": 360,
  "intro_frames": 120,
  "fade_seconds": 2.814375,
  "montage_source": "delivery/Media/montage.mp4",
  "chad_overlay": "delivery/Media/chad.png",
  "audio": "delivery/Media/music.wav",
  "logo_steps": [
    {"path": "delivery/Media/logo.png", "start_frame": 0, "end_frame": 120}
  ],
  "shots": [
    {"start_frame": 0, "end_frame": 120, "source_in_frame": 0, "source_out_frame": 120, "source_label": "CUT 001"},
    {"start_frame": 120, "end_frame": 240, "source_in_frame": 120, "source_out_frame": 240, "source_label": "CUT 002"}
  ],
  "sources": [],
  "graphics": [],
  "references": []
}
```

Shot timeline times are relative to gameplay, excluding intro. Source in/out defaults to each shot's start/end. Intervals are half-open, at 60 fps, contiguous, and must cover gameplay; source and timeline durations must match. Distinct source in-points are required. Logo steps cover the intro contiguously. Prepare the montage at 720×732, the transparent Chad overlay at 720×732 in its original placement, and intro graphics at 720×1280. Audio must already be trimmed to the complete timeline and faded; XML imports it without new audio processing. The builder validates file presence and timeline structure, not decoded media dimensions or duration: probe/decode those separately before import.

The imported project has exactly three sequences. MAIN (720×1280) remains directly at project root. INTRO (720×1280) and GAMEPLAY (720×732) live in the subsequence bin. Every cut uses one shared montage-source file ID with its own source in/out, with Chad on a separate track. MAIN uses the same GAMEPLAY sequence on two native layers: a foreground and a full-height background. The JSX sets background scale to `1280/732*100`, Gaussian Blur to 52, and Repeat Edge Pixels to true. Both layers fade opacity over the final 2.814375 seconds by default, reaching zero on the final displayed frame. Sources, graphics, music, references, and prepared montage media are organized into named bins.

Some media transforms are baked into the prepared montage. Native timeline cuts, the shared foreground/background nesting, blur, scale, and final opacity keyframes remain editable. Preserve originals and SELECTS with source handles when future reframing or shot replacement is required; prepared montage alone cannot recover cropped pixels or original handles. Add these files to `sources` for the Sources bin.

The script refuses an existing native project or generated XML/JSX output and uses a unique scratch project path. Use a fresh output directory for another build. Scratch remains available for recovery. QE is Adobe's undocumented interface; effect lookup uses the English `Gaussian Blur` name and its Pro 2024 property layout, so localization/version changes can require adapting the JSX. Review `import.log`, inspect all three sequences and the final fade in Premiere, and save before delivering. Native verification checks project structure, shared sequence UIDs, distinct cut in-points and existing media; it cannot confirm visual correctness, decoder health, effects, or keyframes. Playback/render QA is still required.

Optional direct export is opt-in:

```
python scripts/build_premiere.py --plan plan.json --output-dir delivery --export-preset vertical-h264.epr
```

Only when that generated JSX is explicitly run will it save the native project and then call `exportAsMediaDirect` with the supplied `.epr` preset. Verify preset settings for 720×1280, 60 fps, audio, and full-sequence duration. Existing project/export files are protected from overwrite. Export status is logged; inspect and decode the resulting MP4 separately. No QE frame-export API is used.

## Windows runner used in the original environment

An installed Premiere 2024 accepted the command-line scripting runner below **only with a fresh Premiere process**. First inspect running Premiere instances and save state. Do not close or kill a user's unrelated/unsaved project. If an owned saved instance can be closed safely, use a normal close and wait for its exit; otherwise use an existing authorized ExtendScript runner or explain the specific blocker.

```powershell
$premiereExe = 'C:\Program Files\Adobe\Adobe Premiere Pro 2024\Adobe Premiere Pro.exe'
$importScript = (Resolve-Path -LiteralPath '.\delivery\import.jsx').Path
$scriptArguments = '/C es.processFile "' + $importScript + '"'
Start-Process -FilePath $premiereExe -ArgumentList $scriptArguments -WindowStyle Hidden
```

Check `import.log` for SAVED and export status, then inspect the actual resulting project and MP4. This is a measured local runner, not a supported promise for every Adobe version. If no installed Premiere or scripting route is available, deliver the importable XML only as an explicitly labeled intermediate and report that native `.prproj` remains blocked; never relabel XML as `.prproj` or claim complete native delivery.
