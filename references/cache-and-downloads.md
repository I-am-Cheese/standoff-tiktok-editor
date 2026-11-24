# Cache lifecycle, discovery, disk and waiting

## Always bootstrap; recreate cheaply

The complete session archive is bundled with the installed skill in small verified parts. Every montage invocation runs bootstrap. It validates/materializes all saved files; a new chat reads the full historical context/current rules. The unpacked history is an **owned temporary cache**, registered by bootstrap. Ending the chat may remove it. The next invocation recreates it **from local installed parts**, without another network download. Installed parts/assets/scripts remain persistent, so normal cleanup does not uninstall the skill. After compaction reread lost history from cache.

## Discover before download/install

Read the owner's local profile and registry without dumping long contents into context. Check direct configured paths and `PATH` first (`Get-Command`/`shutil.which`). Test available executables and Python modules before installing them. Look for FFmpeg/ffprobe/Premiere, source copies, PCM/music, prepared SELECTS and optional ASR models where they are already stored.

Search relevant locations in this order: explicit paths/current job; registered skill cache and workspace `work`/`.cache`; owner release library's Media/SELECTS and ledger-mapped originals; Downloads; known OS temp/cache directories; existing Hugging Face/faster-whisper cache if ASR is actually needed; other source/library/cache roots explicitly configured by the owner. Query other mounted/configured library locations when the first pass fails. Do not crawl every file of every drive, hash all recordings or read unrelated app secrets. This is a bounded search across plausible/configured locations, not a guarantee about arbitrary hidden directories.

```text
python scripts/cache_tools.py find --name recording.mp4 --size 123456 --roots PATH1 PATH2 PATH3
python scripts/cache_tools.py find --name archive.zip --sha256 EXPECTED --roots PATH1 PATH2
python scripts/cache_tools.py space DESTINATION --required-bytes ESTIMATED_NEW_BYTES
```

Find uses cheap names/sizes first, hashing only matching candidates when requested. Its scan/file-depth limit is explicit; if truncated, narrow/reorder roots instead of claiming absence. Verify actual media container, duration, orientation and provenance before reuse. An old filename alone is insufficient. Prefer local copies/NTFS hardlinks when appropriate; never “save space” by deleting user originals.

Omit `--roots` to search PATH/configured executable folders, workspace work, owned caches, Downloads, the release library, profile `search_roots`, known model caches and OS TEMP automatically. Explicit roots are useful to narrow a truncated search or inspect another configured drive. Do not conclude a dependency is absent only because one guessed folder was empty.

## Disk economy

Estimate downloads not already present + SELECTS/render scratch + export + reserve before transfer. `space` reports free bytes with a default 512 MiB reserve; adjust to the actual task/system needs. Select only enough recordings. Don't download all 27–32 sources for every video. Prefer sparse previews and existing selected handles, ordinary small PCM analysis windows and existing ASR models. Install no large library just for an optional flourish.

Create temporary work through `cache_tools.py create --purpose scratch|download-cache|model-cache`, then `track PATH` after writes. `render_montage.py` already creates/records an owned scratch folder; bootstrap records only its verified extracted files. Keep permanent final Media and original-time maps in the release. Temporary raw downloads can be removed only after checking they are not referenced by any affected saved project and equivalent source handles/mappings are preserved.

## Low-token transfers and waiting

Use a connector or existing transfer helper first. Run downloads as one resumable streaming process, optionally bounded parallel HTTP/file workers; don't spawn model agents merely to wait. Verify HTTPS response, expected size/hash and 206/Content-Range before appending a partial file. Reuse existing complete files and valid partial bytes. Keep raw progress on disk; print only start, meaningful milestones/errors and completion. Limit retries (normally 2–3), then change approach from evidence rather than loops.

Let the process perform its transfer and retries without model calls for each chunk/percent. Use at most roughly one status check per 30–60 seconds when a tool session requires checking, staying within host wait limits; completion-driven tool updates are preferable. Communicate meaningful progress concisely. Waiting does not require repeated transcript/tool dumps or reanalysis. Token use and subscription percentage cannot be guaranteed numerically, including a promise of exactly 20 tokens while waiting.

## «Завершаем чат»

This is an explicit request to clean this skill's temporary artifacts, not to delete the installed skill or the user's chat.

1. Save completed project/MP4, persistent preferences and used-episode ledger. Check no active export/download needs the files and no saved project references them. If necessary, wait for the current owned operation to finish. Don't blindly interrupt another user's app/process.
2. Run `python scripts/cache_tools.py cleanup` for a preview. It uses `~/.codex/standoff-tiktok-editor/cache-registry.json`, ownership markers, resolved path bounds and recorded file size/mtime. It scans saved Premiere project media references under the configured release library's parent and optional profile `project_roots`; referenced files are preserved and unreadable projects block deletion until resolved. It refuses protected roots and preserves changed/unregistered files. Inspect the preview and resolve any reference conflict; the user's cleanup command already authorizes deletion of the verified disposable files, so no repeated confirmation.
3. Run `python scripts/cache_tools.py cleanup --apply`. It unlinks only registered unchanged files and removes empty owned directories. No broad recursive delete. Profile, ledger, final releases, originals, installed skill/assets, shared software and shared caches are protected. Missing files are pruned from bookkeeping. Registry remains so later runs know the lifecycle.
4. Check plausible old scratch locations if the user asks for complete legacy cleanup. For artifacts predating the registry, identify their purpose and reference dependencies before registering/removing proven disposable files. Never treat an arbitrary folder called `temp`, all Downloads, all old projects or the entire skill as disposable. Preserve uncertain files and name the specific limitation rather than claiming every unknown cache was cleared.
5. Report reclaimed bytes and retained/changed files briefly. Do not run bootstrap again during this route, because that would immediately recreate the cache just removed. Do not call chat archive/delete tools unless the user separately requests that action.

On the next video request, normal intake and mandatory bootstrap run again. Discover cached installed dependencies before any download; only missing ephemeral material is recreated/fetched. The next user's own profile/source rights still govern their work even though the public historical archive contains the original creator's paths.
