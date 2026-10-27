# Which engine events and APIs feed each ModDash section?

Research for issue #2 (map: issue #1). Engine: Claude Code 2.1.308 (desktop) / 2.1.311 (CLI).

**Primary source**: the mod API types file `claude-code.d.ts` that the `plugin-authoring` skill writes for this build (about 22,500 lines on 2.1.308), plus the skill's `reference.md`. Symbols below are names in that file; line numbers drift between builds, so grep for the symbol. The six mods in `mods/` are cited for *behaviour only* (how they obtain data today); none of their code is reproduced.

## Answer in one line

Everything ModDash needs inside its own session is observable through documented hooks (`tool.call`, `agent.spawn`, `turn.*`, `prompt.submit`, `skill.prompt`, `session.measure`, `$.session.usage`, `$.agent.list`); the two gaps are **other sessions' usage** (no API: read transcript files from disk) and **prompt-cache TTL** (no API: infer or read the transcript).

## Summary table

| Item | Section | Verdict | Hook / API | `claude-code.d.ts` symbol |
| --- | --- | --- | --- | --- |
| Task list (items, states) | Tracker | **Available**, by replaying tool calls | `tool.call` on `TodoWrite`, `TaskCreate`, `TaskUpdate` (and the desktop plan tool, see note); seed from `$.session.messages()` | `ToolCallInput`, built-in tool inputs `TodoWrite` / `TaskCreate` / `TaskUpdate`, `ToolUseSummary`; also `classic.TaskCreated` / `classic.TaskCompleted` (`TaskCreatedHookInput`, `TaskCompletedHookInput`) |
| Subagent start | (Sub)Agents | **Available** | `agent.spawn` (`await next(e)` yields `agentId`); `classic.SubagentStart` | `AgentSpawnInput`, `AgentSpawnResult.agentId`, `SubagentStartHookInput` |
| Subagent running | (Sub)Agents | **Available** | `$.agent.list()` (status), `turn.start` / `turn.step` / `tool.call` carrying `agentId` | `AgentInfo.status`, `AgentStatus`, `AgentLoop.agentId`, `TurnStepResult` |
| Subagent finish | (Sub)Agents | **Available** | `turn.complete` with `e.agentId` (reason, usage); `classic.SubagentStop` | `TurnCompleteInput` (`reason`, `isAborted`, `usage`), `SubagentStopHookInput` |
| Tool calls | (Sub)Agents / Tracker | **Available** | `tool.call` (every built-in and MCP tool, main and subagent loops) | `ToolCallInput`, `ToolCallResult` (`isError`, `text`) |
| Skill invocations | Context & Cache / Tracker | **Available** | `skill.prompt` (covers `/name`, the Skill tool and preloads); `tool.call` with `tool === 'Skill'` | `SkillPromptInput`; `Skill` tool input |
| Connector (MCP) calls | Context & Cache / Tracker | **Available** | `tool.call` where `e.tool` starts `mcp__` | `McpToolCallInput`, `McpToolCallInputFallback`, `McpToolName` |
| File reads | Context & Cache | **Partial** | `tool.call` on `Read` (and `Glob`/`Grep` paths); `@`-mentions only via `prompt.mention` | `ToolCallInput`, `PromptMentionInput` ("No `tool.call` is raised for this read") |
| File writes | Context & Cache | **Partial** | `tool.call` on `Write`, `Edit`, `NotebookEdit`; Bash side-effects invisible; `classic.FileChanged` only for watched paths | `ToolCallInput`, `FileChangedHookInput` |
| User message text | NewMem | **Available** | `prompt.submit` (`e.text`, `e.origin`), `turn.start` (`e.text`), `$.session.messages()` (`role: 'user'`) | `PromptSubmitInput`, `PromptOrigin`, `TurnStartInput`, `SessionMessage` |
| Context tokens and window | Context & Cache | **Available** | `session.measure` (pushed after each main turn), `$.session.usage()` on demand, `{ breakdown: 'summary' }` for categories | `SessionMeasureInput`, `SessionUsage`, `SessionContextUsage` (`tokens`, `window`, `percent`, `breakdown`) |
| Prompt-cache state (for Keep warm) | Context & Cache | **Partial** | last main `turn.complete` time + per-turn cache tokens; TTL (5 min vs 1 h) not in the API | `TurnCompleteInput.usage`, `ModelUsage.cache_read_input_tokens` / `cache_creation_input_tokens` |
| Other concurrent sessions' usage | Day chart | **Unavailable** via API; **partial** via files | `$.fs.list` / `$.fs.read` over `~/.claude/projects/*/*.jsonl` (undocumented format); or each ModDash instance publishing its own figures to `$.store` | no `$.session.*` call addresses another session; `$.store` (`store: { get, set, keys }`) |

## Detail per item

### Task list (Tracker)

- There is no "task list" noun on `$`. The list exists only as the model's calls to the list tools, so the mod rebuilds it by replaying them.
- `tool.call` gives the arguments before the call and, after `await next(e)`, the result. Built-in tool inputs in the d.ts: `TodoWrite.todos[]` (`content`, `status: pending | in_progress | completed`, `activeForm`) replaces the whole list each call; `TaskCreate` (`subject`, `description`, `activeForm`) and `TaskUpdate` (`taskId`, `status: pending | in_progress | completed | deleted`, blocks/blockedBy, `owner`) are incremental, and the `TaskCreate` result carries the new id. The result types (`BuiltinToolResults`) include `TodoWrite`'s `oldTodos` / `newTodos`.
- Classic events `classic.TaskCreated` and `classic.TaskCompleted` fire too (`task_id`, `task_subject`), but there is no classic event for `in_progress` or `deleted`, so they cannot replace `tool.call`.
- On load or reload, seed from `$.session.messages()`: each `ToolUseSummary` has `tool`, `input`, `result`. It has no timestamp (`chat-inventory` reads the transcript file for call times for exactly this reason).
- Filter by `e.agentId === undefined` to keep the main chat's plan apart from subagents' own lists.
- **Desktop note (needs checking in the prototype)**: in the desktop app the model is also offered a host plan tool, `mcp__ccd_turn__update_plan` (observed in a desktop session's tool list on 2.1.308; it is not in `claude-code.d.ts`). Its input is incremental: `items` (whole list), `advance`, `done`, `start`. It is an MCP tool, so `tool.call` sees it, but the Tracker must replay it as well, or the desktop list will look empty when the model uses it instead of `TodoWrite`.
- How today's mods do it: `helper-desk` and `chat-inventory` both hook `tool.call` on the three list tools (main loop only) and seed from `$.session.messages()`; `helper-desk` also registers its own plan tool via `$.tool.register`.

### Subagents ((Sub)Agents)

- **Start**: `agent.spawn` fires before start with `description`, `subagentType`, `model`, `prompt`; `await next(e)` resolves `AgentSpawnResult` with `agentId` and resolved `model`. Covers the Agent tool, workflow agents, teammates and resumes. `classic.SubagentStart` (`agent_id`, `agent_type`) also fires.
- **Running**: `$.agent.list()` returns `AgentInfo[]` with `status` (`pending | running | waiting | idle | completed | failed | killed`), `parentId` and `description`, the authority after a reload. Live activity: every `tool.call`, `turn.start` and `turn.step` inside a subagent carries `agentId`; `turn.step`'s result gives per-request `usage`, model and effort.
- **Finish**: `turn.complete` with `agentId` gives `reason` (`answer | aborted | refusal | error`), `durationMs`, `usage` (`TurnUsage`: four token counts + model). `classic.SubagentStop` gives `agent_transcript_path` and `last_assistant_message`.
- Caveat in `AgentLoop`: "A workflow's agents and the engine's own forks (compaction, memory) carry ids no list names", so the Section must tolerate `agentId`s that `$.agent.list()` does not know.
- Today: `helper-desk` builds its per-subagent cards from `agent.spawn`, `tool.call` with `agentId`, `turn.step` and `turn.complete`, with `$.agent.list()` as the fallback for spawns it missed.

### Tool calls, skills, connectors

- `tool.call` sees every tool call in every loop, before and after. MCP tools arrive as `mcp__<server>__<tool>` (`McpToolCallInput`). A claude.ai connector's server segment is a random id, not a readable name; `helper-desk` and `chat-inventory` each carry a lookup to name them.
- Skills: `skill.prompt` fires once per skill expansion from any route (`/name`, the Skill tool, a preload), so it is the single hook for "skills used", better than matching the `Skill` tool alone (a typed `/name` raises no `Skill` tool call). `chat-inventory` and `handoff` match the Skill tool and slash-command text instead.

### File reads and writes

- Reads: `tool.call` on `Read` (`file_path`); `Glob`/`Grep` name directories, not files read. An `@path` in a prompt is read without a `tool.call`; `prompt.mention` fires per path instead.
- Writes: `tool.call` on `Write`, `Edit`, `NotebookEdit`. Anything Bash writes (`sed -i`, redirects, `git checkout`) is invisible except by parsing the command. `classic.FileChanged` (`file_path`, `event: change | add | unlink`) reports watcher changes, not attribution.
- Hence partial: complete for the model's file tools, blind to shell side-effects.

### User message text (NewMem)

- `prompt.submit` carries the text as typed, pastes expanded, and `origin` (`PromptOrigin`) separating the person's Enter from peers, notifications and plugins; `isMeta` and `command` flag hidden prompts and slash commands. That is enough to run the Memory candidate detector only on the person's own words.
- `turn.start` (main loop) repeats the settled text; `$.session.messages()` gives history (`role: 'user'`, `text`) for a scan on load.
- A detector can call `$.model.classify` / `$.model.complete` without touching the main context (`reflect` does this from `turn.complete`).

### Context tokens and window (Context & Cache, Context alert, status line)

- `$.session.usage()` returns `context.tokens`, `context.window` (the model's window) and `context.percent`, plus `rateLimits` and `cost`. `tokens` is absent until the first response of the live window (fresh session, or just after compaction).
- `session.measure` pushes the same figures after each main-thread turn and when a rate-limit window moves a point, with `changed` naming what moved. The Context alert (250k or 80%) can therefore be pure push: no polling, no `turn.complete` hook. Today's `cache-clock` and `handoff` instead read `$.session.usage()` on `turn.complete` or on a timer.
- `{ breakdown: 'summary' }` gives the /context categories estimated locally at no API cost; `'full'` sends token-count requests.

### Prompt cache (Keep warm)

- The engine does not expose cache TTL or expiry. What is observable: the time of the last main-loop `turn.complete` and that turn's `cache_read_input_tokens` / `cache_creation_input_tokens`.
- `cache-clock` therefore assumes 5 minutes and runs a helper script over the transcript file to detect a 1-hour cache write. ModDash inherits the same limitation: partial.

### Other sessions' usage (Day chart)

- No `$.session.*` call takes a session id other than the current one; `session.measure` and `$.session.usage()` are this session's figures only. The SendMessage / ListAgents tools reach peer sessions for messaging, not usage.
- Two workarounds, neither an API:
  1. **Transcript files**: every session writes `~/.claude/projects/<cwd slug>/<session id>.jsonl`, whose assistant rows carry `usage` and a timestamp. `$.fs.list` + `$.fs.read` can sum tokens per hour per session for today. Cost: an undocumented file format, O(file size) reads (tail-read or cache offsets in `$.store`), and the home folder must come from `$.env.get('HOME')`, not from splitting `$.plugin.root` (see the givens in #1). `chat-inventory` already reads this file for timestamps.
  2. **Self-reporting**: each running ModDash appends its own hourly counts (from `turn.step` / `turn.complete` usage) to `$.store`. Only covers sessions running ModDash, and `$.store`'s behaviour under concurrent writers from several processes is not documented (it is a single 4 MiB JSON store per plugin with plain `get`/`set`, no version check, unlike `$.state`'s `ifVersion`).
- Verdict: unavailable through the API; option 1 is the only route that counts every session.

## What changes the Section designs

1. **Day chart rests on reading transcript files**, not on an engine API. It needs a reader with an offset cache and a tolerance for format change; the prototype should time it on a busy day.
2. **Tracker must replay three or four tools**, including the desktop host plan tool if confirmed, and merge `TodoWrite`'s whole-list snapshots with `TaskCreate`/`TaskUpdate` deltas.
3. **Context alert can be push-driven** by `session.measure`; no timer is needed for it. The timer is needed only for the Keep warm countdown.
4. **Skills via `skill.prompt`**, not the Skill tool, to catch typed `/name` invocations.
5. **File writes by Bash are invisible**: the Section should say "files Claude edited with its file tools", not "files changed".
6. **Cache TTL stays inferred**; the Keep warm countdown must show its assumption, as `cache-clock` does.

## Sources

- `claude-code.d.ts` (2.1.308), written by the `plugin-authoring` skill: `EngineEventOf` (event docs for `tool.call`, `agent.spawn`, `prompt.submit`, `prompt.mention`, `skill.prompt`, `session.measure`, `turn.start`, `turn.step`, `turn.complete`), `ClassicEventOf` / `ClassicEventName`, `AgentInfo`, `AgentStatus`, `AgentLoop`, `AgentSpawnInput`, `AgentSpawnResult`, `ToolCallInput`, `ToolCallResult`, `McpToolCallInputFallback`, `SessionUsage`, `SessionUsageArgs`, `SessionContextUsage`, `SessionMeasureInput`, `SessionMessage`, `ToolUseSummary`, `PromptSubmitInput`, `TurnStartInput`, `TurnCompleteInput`, `TurnUsage`, `ModelUsage`, `SessionRateLimit`, `store` on the engine interface, built-in tool inputs `TodoWrite` / `TaskCreate` / `TaskUpdate`, `TaskCreatedHookInput`, `TaskCompletedHookInput`, `SubagentStartHookInput`, `SubagentStopHookInput`, `FileChangedHookInput`.
- `plugin-authoring` `reference.md`: `$.store` across sessions, `$.state` with `ifVersion`, `session.append` semantics.
- Behaviour of `mods/helper-desk`, `mods/chat-inventory`, `mods/cache-clock`, `mods/handoff`, `mods/reflect` (hooks they register and `$` calls they make), described not copied.
- Desktop host plan tool `mcp__ccd_turn__update_plan`: observed in the tool list offered to a desktop session on 2.1.308; not in the d.ts. Unverified beyond that.
