# Can ModDash list installed plugins and switch them on and off?

Research for issue #14. Engine: Claude Code 2.1.308 (desktop) / 2.1.311 (CLI); the CLI checks below ran on 2.1.312.

**Primary sources**: the mod API types file `claude-code.d.ts` that the `plugin-authoring` skill writes for this build (22,516 lines on 2.1.308; line numbers below are from that file and drift between builds, so grep the symbol), the skill's `reference.md`, the official docs at code.claude.com, `claude plugin <cmd> --help` output, and user-visible strings in the 2.1.312 CLI binary (marked *binary string*; undocumented, may change). The old switchboard mod (`mods/switchboard/` at `18eea60^`, plugin name `mods`) is described for behaviour only; it derives from an unlicensed source and none of its code is reproduced.

No real plugin was toggled and no settings file was changed. Everything marked *untested* needs the experiment at the end.

## Answer in one line

There is **no `$.plugin.*` list/enable/disable API**; the mod does it by shelling out to the documented `claude plugin list --json` / `claude plugin enable|disable --json` through `$.process.run`. That covers every marketplace. A change is written to settings at once but reaches a running chat **only on `/reload-plugins` or a new session**, in this chat and every other one; whether a mod can trigger that reload itself is undocumented and, in the desktop app, probably not. Switching ModDash off works but unloads it, so it cannot switch itself back on.

## Summary table

| Sub-question | Verdict | How | Source |
| --- | --- | --- | --- |
| List installed plugins (with on/off state) | **Documented** (via CLI) | `$.process.run(["claude","plugin","list","--json"])` | CLI reference, `plugin list` JSON output; d.ts `process.run` (l. 3604) |
| List plugins offered but not installed | **Documented** (via CLI) | `claude plugin list --json --available` | CLI reference |
| Read on/off state without the CLI | **Documented**, read-only | `$.settings.read({ key: "enabledPlugins" })` (merged) or `{ source }` per layer | d.ts `settings.read` (l. 3652-3689), `Settings` (l. 12396), `SettingsSource` (l. 12506) |
| Switch a plugin on/off | **Documented** (via CLI) | `$.process.run(["claude","plugin","disable",id,"--scope",s,"--json"])` | CLI reference, `plugin enable` / `plugin disable` |
| A mod API to write settings or toggle plugins | **Unavailable** | `$.settings` is read only; `$.plugin` is only `{ name, root }`; `$.config.set` covers `/config` rows, not `enabledPlugins` | d.ts `plugin` (l. 2355), `config` (l. 3183), `settings` (l. 3652) |
| Takes effect in the chat that made it | **Documented: no, not by itself**. Needs `/reload-plugins` | `$.command.run({ command: "reload-plugins" })` from the mod: **untested**, and docs suggest it is refused in the desktop app | Loading reference ("Loaded" stage); CLI reference `/reload-plugins`, "Sessions without an interactive terminal" |
| Takes effect in other open chats | **Documented: no**, until each runs `/reload-plugins` or restarts; whether they show a "Plugins changed" notice for a settings edit is **untested** | none from outside that chat | Loading reference; *binary string* "Plugins changed. Run /reload-plugins to activate." |
| Any marketplace, not just this repo's | **Documented: yes** | `list --json` returns every install (`name@marketplace`), plus `@skills-dir` and `@synced`; `@inline` only when the flags are in the same command | CLI reference `plugin list` JSON `id` field; loading reference "Find where a plugin came from" |
| ModDash told to switch itself off | **Inferred** (from d.ts + docs): the write succeeds; on the next reload ModDash unloads, its pane closes, and nothing of it remains to switch it back | Must be refused or confirmed in the UI | d.ts `PaneCloseOrigin` (`unload`, l. 7566); `session.start` "an enable ... or a reload" (l. 4467) |
| How the old switchboard did it | Did **not** touch plugins at all: a cooperative off-switch file each mod polled | see below | `git show 18eea60^:mods/switchboard/hooks/register.tsx` |

## Detail

### 1. What the mod API offers (and does not)

- `$.plugin` is this plugin only: `name` and `root` (`CoreEngineInterface.plugin`, l. 2355). No list, enable, disable or reload method exists anywhere on `$`; there are no `plugin.*` events other than `plugin.register`.
- `plugin.register` (event l. 4579, `PluginRegisterInput` l. 7871) fires once per hooks module about to load and lets an earlier plugin `{ refuse }` it. Its input carries `name`, `tier`, `root`, `version` and `provenance` (`<name>@<marketplace>`, `@inline`, `@builtin`). Two limits: it sees **hooks modules only** (mods), not skill-only plugins, and only at load/reload; and refusing is a load-time veto in this process, not a persistent "off". Useful as a gate, not as a switch.
- `$.settings.read` (l. 3652-3689) is **read only**: "a write to it changes nothing the engine reads" (`Settings`, l. 12396). It reads the merge, one key (`{ key: "enabledPlugins" }`), or one source (`user | project | local | flag | policy`), so ModDash can show *where* a plugin is turned on, which matters because a project `true` overrides a user `false`.
- A `settings.read` **hook** can answer `enabledPlugins` differently from the files (l. 3673-3678): "No key is closed to a hook, the keys that decide which plugins load included ... an answer applies from the load after." This is a documented way to switch plugins off *without writing any file*, but only in processes where ModDash itself is loaded, and still only from the next load. The same passage covers the self-disable case: "A merge that never settles, an answer changing which plugins load and those answering otherwise, is told in the settings error list, and the files' own value stands for that key."
- `$.config.list/set` (l. 3183) is the `/config` menu: built-in rows and each enabled plugin's `userConfig` fields. `enabledPlugins` is not a row.
- `$.process.run` (l. 3604) runs any command by argv, with the session's cwd by default and a 30 s timeout. This is the route to the CLI.
- `$.command.run` (l. 3162) "Runs a slash command as if the person typed `/command args` ... queued and run once the session is idle." That is the only candidate for triggering `/reload-plugins` from a mod.

### 2. Listing: `claude plugin list --json`

- Documented at https://code.claude.com/docs/en/plugins/cli-reference.md#plugin-list. An array, one object per installation; always `id`, `version`, `scope` (`user | project | local | managed`, plus `session`, `synced`), `enabled` (merged settings), `installPath`; when they apply, `projectPath`, `projectEnabled`, `mcpServers`, `errors`, `notes`, `hasUserConfig`, `readFromFolder`, `folderVersion`.
- `--available` (with `--json`) returns `{ installed, available }`, the latter one entry per marketplace plugin not installed (`pluginId`, `marketplaceName`, `description`, ...).
- Project and local installs are resolved against the cwd, so run it with the session's cwd (the `$.process.run` default) to see the project's view.
- The files behind it, for reference only (formats are not a contract): `~/.claude/settings.json` (and project/local) `enabledPlugins`, a map `"<name>@<marketplace>": true|false`; `~/.claude/plugins/installed_plugins.json`, `{ version, plugins: { "<id>": [ { scope, installPath, version, installedAt, lastUpdated, gitCommitSha? } ] } }`; `~/.claude/plugins/known_marketplaces.json`, `{ "<marketplace>": { source, installLocation, lastUpdated, autoUpdate? } }`; files under `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. Documented at https://code.claude.com/docs/en/plugins/loading.md#find-plugins-on-disk. Reading them directly would skip the precedence rules, dependencies, synced and skills-dir plugins that the CLI resolves, so the CLI is the better source.

### 3. Switching: `claude plugin enable|disable`

- Documented at https://code.claude.com/docs/en/plugins/cli-reference.md#plugin-enable and `#plugin-disable`. `--scope user|project|local`, auto-detected (local, project, user) when omitted; `--json` prints one result line with `failureCode`.
- Scope matters: a `false` at user scope does not beat a project `true`; the docs' advice is to write the override at `local` (https://code.claude.com/docs/en/plugins/loading.md#disabled-in-user-settings-but-still-loads).
- Refusals the Mods Section must surface: already in that state (`already_in_goal_state`, safe to treat as success); another enabled plugin depends on it (disable names the dependents); a missing or blocked dependency (enable); a managed or org-required plugin (cannot be disabled).
- Writing `enabledPlugins` into `settings.json` directly with `$.fs.write` would also work mechanically but is undocumented as a mod practice, races with the CLI and other sessions, and skips the dependency checks. Not recommended.

### 4. Does it take effect in open chats?

- Documented, loading reference "Check which stage a plugin reached": the "Loaded" stage is "the plugin set Claude Code loaded at startup or at the last `/reload-plugins`. Changes to settings or to disk don't reach this layer until you run `/reload-plugins` or start a new session." This applies equally to the chat ModDash runs in and to every other open chat.
- `/reload-plugins` (https://code.claude.com/docs/en/plugins/cli-reference.md#reload-plugins): "Apply pending plugin changes to the running session without restarting it", including plugins "enabled, disabled". A reload that would add or remove a plugin MCP server or the LSP tool is **held** behind `/reload-plugins --force` because it invalidates the prompt cache.
- **Desktop app caveat** (same page, "Sessions without an interactive terminal"): there the command "runs only when you type it into the session yourself"; arriving another way it replies that it "isn't available over a remote connection". Also, in those sessions the reload "doesn't connect or disconnect plugin MCP servers", which wait for the next session. Whether a mod's `$.command.run({ command: "reload-plugins" })` counts as typed is **untested**; the documented wording suggests not in the desktop app, perhaps yes in a terminal session.
- Other chats: nothing in the mod API reaches another session. The settings docs say running sessions watch and reload settings files (https://code.claude.com/docs/en/settings#when-edits-take-effect), but plugin loading is the exception above. The binary carries a low-priority notice, *"Plugins changed. Run /reload-plugins to activate."*, and `/plugin list` marks a plugin "run /reload-plugins to apply"; whether the notice fires in other chats after a `claude plugin disable` is **untested**.
- Contrast with the session's own dev-mods folder, which hot-reloads at turn end (plugin-authoring skill). That is a separate mechanism for mods written in this session, not for installed plugins.

### 5. Any marketplace

Yes. The `id` field is `<name>@<origin>`: any added marketplace, `@skills-dir` (folders under `~/.claude/skills/` or the project's `.claude/skills/`), `@synced` (claude.ai), and `@inline` (`--plugin-dir`, `CLAUDE_CODE_PLUGIN_DIRS`) only "loaded by those flags in the same command" (loading reference table; CLI reference `plugin list`). A child `claude` process inherits the environment (`$.env` doc, l. 3692), so `CLAUDE_CODE_PLUGIN_DIRS` plugins probably appear; a `--plugin-dir` given to the parent session does not (*inferred*). Synced plugins are switched as `<name>@synced`; an org-required one refuses.

### 6. ModDash switching itself off

- The CLI does not refuse it: ModDash is an ordinary `name@marketplace`. The write lands; the running ModDash keeps going until the next `/reload-plugins` or restart, then unloads: its pane closes with origin `unload` and its hooks do not run (`PaneCloseOrigin`, l. 7566), and its `$.process.spawn` children are killed (l. 3610).
- From then on nothing of ModDash remains to switch it back; the person must use `/plugin` or `claude plugin enable`. If ModDash used the `settings.read`-hook route instead, the engine detects a merge that never settles and the files' value stands (l. 3673-3678), so that route cannot switch ModDash off at all.
- Specification consequence: either hide ModDash's own row, show it without a switch, or require a confirmation that says how to get it back.

### 7. How the old switchboard did it (behaviour only)

The ticket names `mods/mods/`; the mod actually lived at `mods/switchboard/`, plugin name `mods`.

- **Listing**: scanned disk itself, every 10 s while its pane was open: `~/.claude/mods/*`, each `CLAUDE_CODE_PLUGIN_DIRS` folder, `~/.claude/plugins/cache/<marketplace>/<plugin>/` (taking the highest-numbered version folder, not the installed version from `installed_plugins.json`), and the session's `~/.claude/dev-mods/<session>/`. It kept only folders whose `hooks/hooks.json` has `modules` (mods), so skill-only and MCP plugins never appeared. It ignored `enabledPlugins`: a disabled or uninstalled-but-cached plugin still listed. A hard-coded table supplied titles and flags for five known mods.
- **Switching**: never touched Claude Code's plugin state. It wrote `~/.claude/mods/switches.json` (`"<name>": false` for off, `"<name>:hidden": true` for hidden) and relied on each target mod reading that file and going quiet by itself. A mod that did not read it (detected by declaring `switchable` in `plugin.json` or by its source mentioning the file) showed "not switchable". "Open" requests used sentinel files `~/.claude/mods/.open-<name>-<session>` that the target deleted on success.
- **Open chats**: because every cooperating mod polled the file (about every 3 s), off/on reached every open chat within seconds without a reload. But "off" meant the mod's hooks were still loaded and running, just choosing to draw nothing.
- **Itself**: it excluded its own name from the list, so it could not be switched off.

So the switchboard answers a different question (a soft, cross-chat, instant mute for cooperating mods) from issue #14's (real enable/disable of any plugin, effective at reload).

## What this means for specifying the Mods Section

1. **List** from `claude plugin list --json` (optionally `--available`), run through `$.process.run` with the session's cwd, cached and refreshed on open. Group by origin (`@marketplace`, `@skills-dir`, `@synced`), show scope, `enabled`, `errors`/`notes`. Use `$.settings.read({ source })` to say which file decides a row.
2. **Switch** with `claude plugin enable|disable <id> --scope <s> --json`; default the scope to `local` when overriding a project `true`, else the auto-detected one. Show refusals (dependents, managed, required) verbatim.
3. **Do not promise instant effect.** After a switch, mark the row "pending: applies after /reload-plugins or a new chat". Offer a Reload button only if the experiment shows `$.command.run("reload-plugins")` works on the surface; otherwise tell the person to type `/reload-plugins`. Warn when the plugin has MCP servers (`mcpServers` in the list): the reload is held behind `--force` and costs the prompt cache, and on desktop MCP changes wait for a new session.
4. **Other chats**: state plainly that each open chat keeps its old set until reloaded.
5. **Own row**: no switch, or a confirmed switch that says how to turn ModDash back on.
6. **Soft mute is a separate feature.** If an instant cross-chat "hide" for ModDash's own sections is still wanted, that is the switchboard's cooperative pattern applied inside ModDash (`$.store` rather than a shared file), not plugin toggling.
7. **Binary path risk** (*inferred*): the desktop app runs its own engine build (2.1.308) while `claude` on `PATH` may be a different version, or absent from the desktop process's `PATH`. The spec should require resolving the executable and failing visibly when it is missing.

## Cheapest test (needs your go-ahead; it writes settings for a throwaway plugin only)

1. Make a do-nothing mod that sets a status line (`$.ui.status("probe on")`) in a scratch folder, add the folder as a local marketplace, install it at user scope.
2. Open two chats, A (desktop) and B (terminal). In A, have a test mod run `claude plugin disable probe@<scratch> --json` via `$.process.run`; check the status line remains in both (expected), and whether B shows "Plugins changed".
3. From the test mod call `$.command.run({ command: "reload-plugins" })` in A and in B; record whether it reloads or is refused.
4. Type `/reload-plugins` in each; confirm the status line goes. Re-enable, repeat. Then uninstall the probe and remove the scratch marketplace.

That settles the two *untested* rows (auto-reload from a mod per surface; notice in other chats) at the cost of one throwaway install.
