# How Claude Code writes auto-memory, and whether a mod can append to MEMORY.md safely

Research for issue #8 (ModDash map, issue #1): the "Remember" Memory destination.
Engine checked against: desktop 2.1.308 / CLI 2.1.311 docs as published October 2026.

## Answer

The model writes auto-memory itself, with its ordinary Write and Edit tools. There is no
dedicated memory API, and nothing serialises writes to the directory. The harness only
stamps a `modified` timestamp into the frontmatter and checks the index against its size
limits after each write. `MEMORY.md` is one line per memory. The model edits it in place;
the harness does not regenerate it. A mod can safely add a memory if it creates a **new
topic file** and then inserts **one index line** with a read-modify-write that rechecks the
file just before it writes. It must never rewrite the whole index from a stale copy.
The residual risk is a lost index line during a write that overlaps the model's own
index edit, which is narrow, and detectable and repairable afterwards because the topic
file survives.

## Sources

- [S1] Claude Code docs, "How Claude remembers your project", Auto memory section:
  https://code.claude.com/docs/en/memory#auto-memory
- [S2] Claude Code docs, Errors, "Memory index is over its read limit":
  https://code.claude.com/docs/en/errors#memory-index-is-over-its-read-limit
- [S3] Claude Code docs, Tools reference, Edit tool behaviour and Write:
  https://code.claude.com/docs/en/tools-reference
- [S4] Claude Code docs, Subagents, "Enable persistent memory":
  https://code.claude.com/docs/en/sub-agents#enable-persistent-memory
- [S5] Mod API type definitions shipped with the `plugin-authoring` skill,
  `types/claude-code.d.ts` (engine 2.1.308): `$.fs`, `AgentLoop`, `ContextMemoryFile`.
- [S6] Observed on disk: 10 local `~/.claude/projects/*/memory/` directories, about 70
  topic files, examined for **structure only** (key names, enum values, line shapes,
  sizes). This note quotes no memory content.

## 1. Who writes memory, and when

- **The model decides and writes.** Claude "saves four kinds of notes for itself" and
  "decides what's worth remembering based on whether the information would be useful in a
  future conversation"; it does not save every session [S1]. It "reads and writes memory
  files during your session", which the UI reports as "Saved N memories" [S1].
- **It uses ordinary file tools.** Subagents with `memory` set get "Read, Write, and Edit
  tools ... automatically enabled so the subagent can manage its memory files" [S4]. The
  main loop works the same way. In local transcripts every memory write was a `Write` to a
  new topic file or an `Edit` to `MEMORY.md` (11 and 1 occurrences; small sample) [S6].
- **The harness also writes, in two narrow ways:**
  1. It records "the write time in a `modified` frontmatter field as an ISO 8601
     timestamp" when the written file begins with YAML frontmatter [S1].
  2. After a write to `MEMORY.md` it measures the file against the limits and returns a
     reminder or an error to the model, but "the write still succeeds" [S1][S2]. It does
     not truncate or rewrite the index for you.
- **Possible background writer (not confirmed).** The mod API mentions "the engine's own
  forks (compaction, memory)" as loops that carry agent ids [S5]. So a memory-writing
  forked loop exists, separate from the main turn. Its timing (for example end of turn) is
  not documented. Treat it as a second concurrent writer that a mod cannot see coming.
- **Off switches:** `autoMemoryEnabled: false` (user or project settings), or
  `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` [S1]. A mod that writes to Remember should check for
  both, or it writes memory nobody loads.

## 2. Location

- `~/.claude/projects/<project>/memory/`, where `<project>` comes from the git repository,
  so **all worktrees and subdirectories of one repo share one directory** [S1]. Outside git,
  the project root is used.
- Overrides: `autoMemoryDirectory` in any settings scope (absolute path or `~/`), and
  `CLAUDE_CODE_PROJECT_DIR_NAME` with `CLAUDE_CONFIG_DIR` (v2.1.234+) [S1].
- Consequence for ModDash: do not compute the path from the cwd. Read it from the engine.
  `SessionContextBreakdown.memoryFiles` lists each loaded memory file with an absolute
  `path` and a `type` label, where auto-memory is `AutoMem` [S5]. Otherwise read
  `autoMemoryDirectory` with `$.settings.read({ key })` before falling back to a derived
  path.

## 3. File format

The documented layout is a `MEMORY.md` index plus "one topic file per memory" [S1].

**Topic file** (observed [S6], consistent with [S1]): Markdown with YAML frontmatter.
All files had these keys:

```yaml
---
name: <short title>
description: <one-line summary>
metadata:
  type: user | feedback | project | reference
  node_type: memory              # present on ~85% of files
  originSessionId: <uuid>        # present on ~85% of files
  modified: 2026-01-01T00:00:00.000Z   # harness-stamped, ~60% (older files predate it)
---
<body>
```

- [S1] documents `type` with exactly those four values and says it lives in the
  frontmatter. Observed files keep it **nested under `metadata:`**, not at the top level.
  A mod should copy the observed shape.
- Filenames follow the `<type>_<slug>.md` pattern the docs show (`user_role.md`) [S1].
  One directory had a non-memory dot-subfolder, so do not assume the directory holds only
  memories.

**Index line** (observed in all 69 indexed lines [S6]):

```markdown
- [Title](topic_file.md) — one-line hook
```

That is a bullet, a relative Markdown link to the topic file, then an em dash and a short
description. Some indexes also have `#` headings. The longest observed line was 280
characters. No index had frontmatter.

## 4. Is MEMORY.md rewritten or appended?

Neither, as a harness operation. The index is edited **by the model** like any file:
normally an `Edit` that inserts a line, and sometimes a full rewrite when the harness tells
it the index is near or over its limit ("Rewrite it to under 140 lines now: keep one line
per entry, move detail into topic files, and merge or drop stale entries") [S2]. Nothing in
the docs suggests the harness rebuilds the index from the topic files. That is why a
dropped line stays dropped: the topic file still exists but is no longer indexed.

## 5. Size limits and loading

- At session start the harness loads "the first 200 lines of `MEMORY.md`, or the first
  25KB, whichever comes first". Content past that is not loaded [S1].
- YAML frontmatter and block-level HTML comments are stripped before loading and before
  measuring (v2.1.211+) [S2].
- Write-time check (v2.1.210+): near a limit, a "milder reminder"; over a limit, an error
  telling the model to rewrite to under 140 lines [S2].
- Topic files are **not** loaded at start. The model reads them on demand, guided by the
  index [S1]. So an unindexed topic file is effectively invisible.
- Not loaded into subagents (forks excepted). A subagent's own `memory` directory is
  separate [S4]. Memory files are exempt from the `cleanupPeriodDays` sweep [S1].
- Observed scale [S6]: indexes ranged from 3 to 44 lines (largest about 7.7KB), well
  within limits.

## 6. Risks of a mod writing alongside it

| Risk | How it happens | Severity |
| --- | --- | --- |
| **Lost index line (mod's)** | The mod reads `MEMORY.md`, the model's `Edit` lands, then the mod writes its stale copy plus its line. `$.fs.write` replaces the whole file and has no compare-and-swap or append [S5]. | Silent loss of the model's entry. The worst case. |
| **Lost index line (model's)** | The model's `Edit` succeeds against changed content when `old_string` still matches [S3], so the model rarely clobbers the mod. But a model **rewrite** of the index (the over-limit path, or a `Write`) built from a copy read earlier drops the mod's line. | The mod's memory stops loading; its topic file is orphaned. |
| **Duplicates** | The mod retries after a partial failure, or proposes a Memory candidate the model has already saved (the model saves "corrections you give Claude" on its own [S1]). | Clutter; uses index budget. |
| **Index over limit** | The mod appends to an index near 200 lines or 25KB. The harness check runs after the *model's* writes; whether it fires on a mod's `$.fs.write` is undocumented. | Entries at the end are silently not loaded. |
| **Wrong directory** | Path derived from cwd or worktree rather than the git root or overrides [S1]. | Memory written where nothing loads it. |
| **Format drift** | `type` at the top level instead of under `metadata:`, or a missing frontmatter block (no `modified` stamp). | Probably tolerated (the model reads plain Markdown), but inconsistent. |

Read-before-write in `Edit` does **not** protect a mod: it applies to the model's tool
calls only. And since 2.1.228, newer models can overwrite or edit an unread file when the
read would need no permission prompt [S3]. The model's protection against a mod's change
is that `old_string` must still match; there is no lock.

## 7. Recommended safe write pattern

1. **Resolve the directory from the engine** (`memoryFiles` entry of type `AutoMem`, else
   `autoMemoryDirectory`, else derive from the git root). Skip Remember when auto-memory is
   disabled.
2. **Write the topic file first**, as a new file with a unique name (`<type>_<slug>.md`,
   with a short suffix if the name exists), in the observed frontmatter shape. It is a new
   file, so it cannot collide with a model edit. If the next step fails, the memory exists
   but is not indexed, which is recoverable.
3. **Insert the index line with a short optimistic read-modify-write:**
   - read `MEMORY.md` (missing means start empty);
   - skip if any line already links to the topic filename (makes retries idempotent);
   - append `- [Title](file.md) — hook` after the last line;
   - **read again immediately before writing**; if the content differs from the first
     read, redo from the start (bounded, for example 3 tries);
   - write the whole file.
   This narrows the race to the gap between the last read and the write (milliseconds)
   instead of the whole time a user takes to click. `$.fs` offers nothing tighter [S5].
4. **Do it between turns.** Run the write when the session is idle, not while a tool call
   is in flight, to avoid the model's own index edits. The background memory fork [S5]
   cannot be fully excluded.
5. **Respect the budget.** If the index would exceed about 180 lines or 22KB, do not add
   to it. Write the topic file and tell the user the index needs consolidating (the
   `consolidate-memory` skill exists for that), rather than push older entries past the
   load cutoff.
6. **Verify and repair.** After writing, and again at the next session start, check that
   the line is present. A cheap orphan check (topic files with no index link) recovers from
   both lost-line cases. This check alone makes the residual race harmless.
7. **Dedupe against the model.** Before offering a Memory candidate as Remember, compare
   its text with existing `description` fields, so ModDash does not record what the model
   already saved.

Alternative worth considering: let the **model** do the write, by queueing a prompt such
as "remember: ..." from the band. That uses the documented path, the frontmatter stamping
and the limit checks, and removes the race entirely. The costs are a turn and less
control over the wording.

## Open / unverified

- When the engine's memory fork runs and whether it rewrites `MEMORY.md` wholesale
  (only its existence is attested [S5]).
- Whether the harness `modified` stamp and the limit check also fire on a plugin's
  `$.fs.write` (the docs tie both to Claude's writes [S1][S2]).
- The official schema of the `metadata:` block. Observed only; not documented beyond `type`.
