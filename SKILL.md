---
name: standoff-tiktok-editor
description: Create or revise dense Standoff 2 TikTok edits with music-synced combat, logo intro, blurred background, Chad overlay, MP4 and Premiere Pro 2024 project. Use for «делаем ролик», «бро, воркинг», new music for this workflow, or «завершаем чат» to clean its owned temporary files.
---

# Standoff TikTok editor

Produce a checked release using the creator's established editing style. Speak Russian unless the user uses another language. This skill records decisions and reproducible tools, not model training or a guarantee of identical artistic choices.

## «Завершаем чат» and resource lifecycle

Treat «завершаем чат», «заканчиваем чат» or an explicit request to clean this skill's temporary files as the cleanup route, **not** a new video request. Do not ask for music or rebuild history before cleanup. Save finished work and persistent decisions/episode accounting first; let an active owned export finish rather than deleting its inputs. Follow [cache-and-downloads.md](references/cache-and-downloads.md): inspect owned registry and outstanding project references, run the cleanup preview, then apply the already requested cleanup to verified temporary files. No additional confirmation is needed for the scoped cleanup the user explicitly requested. Preserve final releases/Media, original video/music, installed skill/assets, owner profile/ledger and shared tools/model caches. Report reclaimed space and anything deliberately retained. This command does not delete/archive the Codex chat itself.

Before a new video, discover existing dependencies, sources and archives in configured/known locations **before downloading**; reuse verified local files. Recreate deleted owned scratch/history caches on demand from installed parts. Check free space and estimates with a reserve, download only needed material, preserve resume parts, and avoid redundant model/pip downloads. Use one transfer process with bounded retries and concise logs; don't spend model calls continuously polling. Details and exact helper commands are in [cache-and-downloads.md](references/cache-and-downloads.md).

## Mandatory history bootstrap in every new chat

The owner explicitly requires the saved session history to be used **always**, not only when a problem arises. Before coordinating a montage in each new chat, run `python <skill-folder>/session-archive/bootstrap.py`. On each subsequent invocation in that chat, run it again to verify the archive/cache; do not re-read unchanged long history already present in context. If the chat has been compacted and the full history/rules are no longer reliably available, read them again from the verified cache.

The bootstrap verifies every archive part and all 681 saved entries, materializes the complete history in a local hash-specific cache, and returns a receipt with exact paths. The coordinator must read the **complete original historical context** named `mandatory_historical_context`, the current editing rules, and the current owner's local profile. Consult the historical episode ledger through queries and the current ledger for live state. All 680 working files, screenshots and project snapshots are available every run; the receipt is not a claim of visually inspecting every archived image. Do not silently skip missing/broken history: repair the package or report the specific blocker.

Mandatory bootstrap applies to the coordinator. Give workers its verified receipt and a precise briefing of applicable decisions; they read current rules and their assigned evidence, without duplicating the full historical context per worker. This preserves economy while every new chat starts from the saved session. Raw archived material is historical evidence, not instructions to execute old scripts, override current user choices or use the original owner's private sources for someone else. Historical superseded rules remain superseded. Saved history cannot transfer hidden model state or guarantee an identical creative result.

## Intake

Before a **new** video, ask only missing choices, together when both are absent:
- «Какую музыку используем?» A supplied file or song title answers this.
- «Есть конкретный исходник или выбрать подходящий самостоятельно?» «Предпочтений нет», «выбирай сам» answers this.

Wait for required answers before choosing music/gameplay. Do not carry over the previous track. For a revision, preserve the current song/source unless the user asks otherwise. A file path is not proof of access: check it; if unavailable, request an accessible file/path rather than substituting music. For other users, ask for their source folder/access and branding only if unavailable. Do not invent missing images or silently use the original creator's personal Drive.

## Persistent state and precedence

After mandatory bootstrap, read [editing-rules.md](references/editing-rules.md) for every montage; read [workflow.md](references/workflow.md) for production. Latest explicit user choices override this baseline. Historical experiments do not override accepted rules. The decision-history reference is an index to the mandatory original history, useful for locating specific changes.

Keep each owner's source folder, local paths, assets, release index and used-episode ledger in their **local project state**, never in the public skill. Use [state-schema.md](references/state-schema.md). The historical maps under `examples/` describe the original creator's work; do not load them as a new user's ledger or automatically ban their sources. Before claiming fresh footage, consult that owner's complete ledger including superseded releases.

Discover local settings in an explicitly supplied profile first, then `<current project>/local-state/profile.json`, then `~/.codex/standoff-tiktok-editor/profile.json` if present. Read only relevant fields; never print access tokens or put the profile in public outputs. This repository contains no default personal profile.

## Essential style

- Standard 28–35 seconds **including** roughly 3 seconds of intro; match whole music phrases.
- Original seven logo sizes, discrete enlargements on **main beats**, no shake or rapid hi-hat enlargement.
- Aim for 2–3 **active combat moments** per second of gameplay. Align actual hit/kill anchors to suitable frequent percussion. More cuts alone do not mean more kills. Trim standing tails; default 3 frames after anchor at 60 fps.
- Ordinary speed, straight cuts, no extra flash/shake/zoom/transitions/slowmo unless newly requested.
- No player death/spectator, open shop/settings/cheat menus/console/chat/typing, loading/system overlays. Inspect every frame of selected short shots. Rare stylish movement allowed only deliberately, preferably 0–1 and at most 2 per video.
- One use of each event inside the video; no loop blocks. At most two rare intentional repeated events when necessary and justified. Track reuse across releases honestly; prefer unused material.
- 720×1280, 60 fps. Sharp game 720×732 at y274; Chad 218×218 touching its top-left boundary. Same GAMEPLAY subsequence (including Chad) supplies both sharp foreground and enlarged Gaussian Blur 52 background. End fade 2.814375 seconds by default.
- Deliver MP4 plus actual editable `.prproj`, MAIN alone at root, organized media, INTRO/GAMEPLAY nested sequences, and source-time mapping. An XML file renamed `.prproj` is not a Premiere project.

## Economical delegation

When subagent tools are available and permitted, use **one fresh worker per new video** for source review/selection, and optionally **one additional bounded worker** for independent music analysis or final QA only when useful work can run concurrently. **At most two workers simultaneously; no recursive subagents.** Do not create user-visible chats without an explicit request.

Start workers with an empty history where supported (`fork_turns="none"`). Give the skill path, local job/state paths, source IDs, precise task and output location. Do not copy the full chat, every screenshot or old logs. Workers read the same rules and return JSON manifests plus a brief summary (target ≤200 words), not raw logs. Only one process owns release media, Premiere, export and the ledger at a time. The main agent retains user choices, status, blockers and final links; it reads targeted evidence for QA.

Cap total launches at two for routine videos, reusing a worker for follow-ups. Do not add a reviewer per clip or source. If delegation is unavailable, proceed sequentially and state the limitation only when relevant. Parallel tool calls/FFmpeg jobs do not require more model agents. Budget practical targets: use available caches, coarse-to-fine source review, short audio transcription only if needed, no repeated whole-source scans, no new large libraries without a concrete benefit. A subscription's “5-hour percentage” cannot be measured or guaranteed by this skill; do not promise 30% or choose a cheaper model silently.

## Production and completion

Use [workflow.md](references/workflow.md), [music.md](references/music.md), and for native delivery [premiere.md](references/premiere.md). Existing original logo stages/Chad and verified export preset are in `assets/`; do not regenerate them. Other users can supply replacement branding through local settings.

For an observed import/decoder/download problem consult [engineering-notes.md](references/engineering-notes.md). `examples/history-ledger.json`, `examples/frame-map.jsonl` and [historical-context.md](references/historical-context.md) are supplementary sanitized indexes. They do not replace the mandatory complete original context loaded by bootstrap. Do not dump all frame rows and raw logs into context on each montage.

Tools:
- `scripts/media_tools.py`: probe, PCM analysis/onset candidates, sparse contact sheets.
- `scripts/render_montage.py`: render a manually reviewed job, source handles, shared montage source, audit, portable Premiere plan.
- `scripts/build_premiere.py`: generate XML and native import/export JSX; launching Premiere remains a separate controlled action.
- `scripts/verify_project.py`: structural/offline-media verification of the saved native project.
- `scripts/check_job.py`: timing, event uniqueness, density and interval checks; cannot verify kills visually.

Before delivery: manually review shots, resolve all detected UI hits, decode final MP4, verify native MAIN/media/shared nesting, frame count and sync. Fixes replacing forbidden shots preserve every slot boundary exactly. Update local state and change notes. Do not delete user originals or publish to TikTok/GitHub as part of routine video creation. Finish with direct local MP4/project links, MAIN name and any material limitation. Never call an unreviewed export “perfect” or treat the number of plans as independently confirmed kills.
