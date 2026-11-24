# Production workflow and quality gates

## Plan cheaply

Run the mandatory session-archive/bootstrap.py and read its complete original historical context in each new coordinator chat, then SKILL/current editing rules and this owner's live profile/ledger. Verify bootstrap on subsequent invocations; reread lost history after compaction. Workers use the coordinator's receipt/briefing instead of duplicating full history. Resolve music/source preferences first. Probe tools, disk space, actual media metadata and the approved assets. Download/inspect only enough material; use previews and sparse contact sheets when possible. The old Drive inventory durations were sometimes misassigned; actual media probe is authoritative. Do not claim “watched all 32 recordings” after seeing thumbnails.

Use cache-and-downloads.md before transfers: search existing owner/configured/tool/model caches, verify matching candidates and free space, then fetch only missing bytes. Create/track temporary folders through cache_tools.py. The «завершаем чат» cleanup route skips bootstrap/intake and removes only verified disposable registered files after saving persistent state; it does not uninstall the skill or erase releases.

Give a fresh worker source review or bounded music analysis and have it write a compact manifest. At most two concurrent workers and two launches for routine runs; workers never spawn workers. Keep one owner for all release writes and Premiere. Agent concurrency is distinct from up to two independent FFmpeg processes. Logs/images stay on disk, and workers return counts, paths, risks and targeted evidence. No full-history forks by default. Reuse cached analysis when unchanged; a new song needs its own phase/phrase analysis.

## Review footage

Coarse overview → candidate event windows → first/mid/last and anchor inspection → full short-shot scan. Select hit markers, kill feed changes, recoil/impact plus target context, not arbitrary white pixels. Marker templates depend on HUD and normalization. Low HP alone is not death. Victory text or a normal HUD notification alone does not prove a forbidden screen.

Select enough clean, unique events before rendering. Prefer unused intervals. Two or three shorter recordings may be combined. Across-release reuse is allowed but must be truthful; don't claim all-new if the ledger says otherwise. A full source can contain mostly menus even when long. Don't force 30 seconds by looping blocks or adding standing. If the accessible material genuinely cannot supply the requested release, state the shortage and offer the smallest actionable choice.

Inspect orientation and baked bars. Canonical landscape source 1280×720 had useful game pixels y72..648; center crop `crop=567:576:357:72,scale=720:732`. One portrait source was 720×1280 with horizontal game 720×324 at y478: first `crop=720:324:0:478,scale=1280:576,pad=1280:720:0:72`, then canonical crop. These are measured examples; inspect each new source instead of applying blindly. Contact sheet tile height must match source aspect ratio; fixed landscape rows hide portrait content.

## Render and assemble

Keep a short job JSON, audited anchors and exact integer frame counts. Run check_job.py. Renderer creates normal-speed prepared shots, one shared Montage source.mp4, source SELECTS handles (0.65s before, 0.55s after anchor), original-time mappings, full PCM + trimmed/faded music and assets. Native SELECTS retain original orientation; prepared shots normalize/crop. No source audio unless explicitly requested. Safe frame alignment matters more than rounded millisecond displays.

Build XML + import.jsx with build_premiere.py, then use installed Premiere Pro 2024 to import/save/export. Read premiere.md. MAIN has two instances of SAME GAMEPLAY, so the blurred background includes Chad; don't blur a separate raw-game copy. Keep Media beside the project. Prepared geometry is baked in the shared source, while individual cuts, branding, blur, opacity and audio remain editable and full-frame SELECTS allow reframing/replacement. Tell the user this limit if they ask about editability.

## Verify once, fix narrowly

- Review every chosen shot, including first 1–6 frames where menus can flash. Optional known-template scan runs over **all** prepared game frames. Any hit must be inspected and resolved before native export. An empty detector result is not universal proof; unknown UI still needs visual review.
- Replace only bad slots, with identical frame counts. Preserve neighbors, music, rare intentional movement and exact pacing; compare unchanged ranges if the task is a surgical fix.
- Check final MP4 metadata (720×1280, square pixels, 60fps, AAC stereo48k), expected frame count and full decode. Check representative cuts at final export, first words and ending. After replacing a shot, verify updated pixels appear in final MP4 to catch native caches.
- Verify actual gzip/XML prproj: 3 sequences, MAIN at root, separate cut inpoints, same nested sequence UID for both MAIN game layers, all media online under release. XML alone is an intermediate, not the promised prproj.
- Update episode ledger, release notes, source handles and original timestamps. Distinguish plans from verified unique kills and “generated” from “approved by user.” Keep earlier versions recoverable; archive deliberately, don't shuffle unrelated releases.

No repetitive broad reruns after unchanged checks pass. Temporary raw downloads may be removed only after all affected saved projects' references are checked and preserved SELECTS/mappings verified; never delete user Downloads/originals. Prefer retaining until delivery when disk permits. On Windows use native single-shell literal paths and verify intended absolute workspace targets before recursive operations.

## Limits and deliverables

The owner-authorized public session archive includes saved screenshots, operational logs, project snapshots, personal paths and source links. It does not grant another user rights/access to those recordings or include raw video/audio, unsaved private chats or hidden reasoning. Bootstrap always verifies/materializes it; the coordinator always reads the complete saved context in a new chat. Public frame maps record frame-to-source timing rather than shipping every decoded frame. Saved evidence transfers rules and mechanics; it cannot guarantee the same creative outcome, identical hidden model state or a fixed subscription usage percentage.

Deliver MP4, native prproj, Media, a per-shot source ledger and concise release notes. Name MAIN plainly and link both deliverables. Do not auto-publish to TikTok or modify the public skill repository when merely asked for another video. New accepted preferences update local rules; promote to the shared skill only on explicit request.
