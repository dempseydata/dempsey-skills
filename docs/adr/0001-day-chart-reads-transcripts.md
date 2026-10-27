# The Day chart reads session transcripts, not $.store

No API exposes other sessions' usage, so the Day chart reads every session's transcript under `~/.claude/projects/` (undocumented format) instead of having each ModDash report its own samples to `$.store` (documented). Self-reporting silently omits any session not running ModDash, and a chart that quietly under-reports is worse than none; a transcript parse failure, by contrast, shows as "unavailable". Nothing is stored past today, so changing source later costs a rewrite of the reader, not a data migration.

## Consequences

- Assistant usage is repeated per content block, so counting de-duplicates by message id across all files.
- Each ModDash session parses today's transcripts once, then reads incrementally from byte offsets held in `$.state`. A shared `$.store` cache is warranted only if first draw measures above ~2 s.
