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
Tokens per hour, counting every token that draws on usage limits (cache reads included), across all of today's sessions, stacked by session.
_Avoid_: Usage graph, history

**Context alert**:
The warning that a session's context has crossed its threshold.
_Avoid_: Context warning, token alarm

**Keep warm**:
Pinging a session so its prompt cache does not expire. Offered only for the session the pane belongs to, off until switched on.
_Avoid_: Heartbeat, cache ping

**Break-even stop**:
The point at which Keep warm stops by itself: when the pings so far have cost as much as one cold re-write of the context would.
_Avoid_: Timeout, ping cap
