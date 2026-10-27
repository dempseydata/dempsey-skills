# dempsey-skills

Skills and mods for Claude Code, published through the `dempsey` marketplace.

## Language

### Mods

**Mod**:
A plugin that changes Claude Code's own interface or behaviour (a pane, band, status line or hook), as opposed to a skill.
_Avoid_: Extension, add-on

**ModDash**:
The single mod that replaces the six earlier dempsey mods: one docked pane of sections plus a one-line status-line summary.
_Avoid_: Dashboard mod, cockpit

**Section**:
One collapsible part of the ModDash pane, showing a summary when collapsed and detail when expanded.
_Avoid_: Panel, widget, tab

**Day chart**:
Tokens per hour across all of today's sessions, stacked by session.
_Avoid_: Usage graph, history

**Context alert**:
The warning that a session's context has crossed its threshold.
_Avoid_: Context warning, token alarm

**Keep warm**:
Pinging a session so its prompt cache does not expire.
_Avoid_: Heartbeat, cache ping

### Memory

**Memory candidate**:
A statement from the conversation detected as worth keeping as a standing instruction. "NewMem" is the label of the section that counts them, not a name for the thing.
_Avoid_: NewMem, reflection, lesson

**Memory destination**:
Where an accepted memory candidate is written: Everywhere, This project, or Remember.
_Avoid_: Target, scope
