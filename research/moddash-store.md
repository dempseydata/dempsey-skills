# What `$.store` guarantees when several sessions write at once

Research for [#4](https://github.com/dempseydata/dempsey-skills/issues/4), part of the ModDash map ([#1](https://github.com/dempseydata/dempsey-skills/issues/1)). ModDash's Day chart needs token samples from several concurrent sessions persisted through `$.store`.

Engine: Claude Code CLI 2.1.311 (the `claude -p` runs below); API types from the desktop 2.1.308 build.

Each claim is tagged:

- **[doc]**: stated in the mod API types (`claude-code.d.ts`, the `store:` block on `$`) or the plugin-authoring `reference.md`.
- **[obs]**: observed in the empirical check below.
- **[inf]**: inferred from the above, not proven.

## Answer

| Question | Answer |
| --- | --- |
| Atomicity | Each `set` / `delete` is a single write under a file lock **[obs]**. There is no multi-key transaction and no compare-and-set on `$.store` **[doc: the API is `get`, `set`, `delete`, `keys` only]**. |
| Last-writer-wins or merge | **Per key, last writer wins; across keys, writes merge.** Concurrent sessions writing different keys all survive **[obs]**. A read-modify-write of one shared key loses updates **[obs]**. |
| Granularity | The key. One JSON file per plugin holds all keys **[doc + obs]**; the engine re-reads it under the lock, so a `set` replaces only its own key **[inf from obs]**. |
| Contention | **`set` can reject** with `Lock file is already being held` when another session holds the lock. It does not wait **[obs]**. Undocumented. |
| Size limit | `set` rejects once the store would exceed **4 MiB of JSON text in all** (all keys together, not per key) **[doc]**. |
| Values | JSON data: `get` returns `JSON.parse(JSON.stringify(value))`; a Date becomes its ISO string, `undefined` fields drop, Map/Set become `{}`; functions and cycles are rejected **[doc]**. |
| Persistence | "A JSON file of the plugin's own under the user's Claude Code configuration directory" **[doc]**. On disk: `~/.claude/plugins/store/<plugin>_<marketplace>-<hash>.json`, mode `0600`, pretty-printed; a `--plugin-dir` mod is `<plugin>_inline-<hash>.json` **[obs]**. Kept across sessions and hot reloads **[doc]**. |
| Visibility | `get` / `keys` in one session see other sessions' writes (they read disk, not a session snapshot) **[obs]**. |

## Recommended write pattern for Day chart samples

1. **One key per writer, never a shared array.** Key each sample (or each session's batch) by something only that session writes, e.g. `day:<YYYY-MM-DD>:<sessionId>`. No two sessions ever write the same key, so last-writer-wins never bites. A shared `samples` array updated by get-push-set lost two thirds of its entries in the test.
2. **Retry `set` on rejection.** Wrap it: on a throw, sleep 5 to 25 ms (`$.clock.sleep`) and retry, capped (the test used 50 attempts and needed at most 7). Without this, a lock collision throws out of the hook and the sample is gone.
3. **Batch per session, not per sample.** Hold the session's samples in memory (or `$.state`) and write the session's own key on an interval or at `session.end`, rewriting that one key with the whole session's list. Fewer writes means fewer lock collisions. A hot reload drops module variables, so flush to `$.store` or keep the buffer in `$.state`.
4. **Read by listing.** The Day chart reads `keys()`, filters `day:<today>:`, and merges the per-session lists at draw time.
5. **Prune to stay under 4 MiB.** The cap is on the whole store, so old days must be deleted (or rolled up into a compact per-day summary key) on `session.start`. Pruning is a `delete` of keys any session may own; that is safe as long as only past days are pruned, since no live session still writes them **[inf]**.

## Empirical check

A throwaway mod (not committed) registered `/storetest`, run headless with `claude -p "/storetest" --plugin-dir <mod>`, which answers the command with no model call. Four sessions ran at once.

**Run 1, no retry.** Each session wrote 100 keys of its own (`k:<tag>:<i>`) and, after each, appended to a shared `log` array by get-push-set.

- Two of four sessions threw `$.store.set failed: Lock file is already being held` and stopped (one on its first write, one after eight).
- The two that finished had all 100 of their own keys on disk.
- The shared `log` held 66 entries of the 208 appends made: a classic lost-update race.

**Run 2, retry on rejection.** Each session wrote 100 keys of its own, retrying a rejected `set` after 5 to 25 ms.

- All four finished; 400 of 400 keys on disk. Retries per session: 0, 4, 5, 7.
- After a 3 s pause, `keys()` in each session listed the other sessions' keys (300, or 263 for one that looked early), so reads go to disk.

## Not checked

- Whether the file write itself is atomic (temp file plus rename) or could be torn by a crash mid-write. Not documented; not tested.
- Lock behaviour across the desktop app and the CLI at once (both ran as CLI here; same engine and path, so likely the same) **[inf]**.
- Whether a stale lock from a crashed process clears itself.
- The 4 MiB rejection was not exercised.

## Sources

- `claude-code.d.ts` (2.1.308), the `store:` member of `$`: description, `get`, `set` (JSON round-trip, 4 MiB cap), `delete`, `keys`; and the `state:` member, "Persist through `$.store`". Written by the engine into the `plugin-authoring` skill's `types/` folder.
- `plugin-authoring` skill `reference.md` (2.1.308): "`$.store` keeps values across sessions"; a hot reload keeps `$.state` and `$.store`, module variables start over.
- On-disk inspection of `~/.claude/plugins/store/` and the two probe runs above, 2026-10-27.
