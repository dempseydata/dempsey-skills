# Briefs

Prompts for the shift's subagents. Fill each `{slot}` from the prescan report and the ledger. Spawn each brief as a fresh foreground subagent (`general-purpose`).

Slots used across briefs:

- `{ticket}`: the ticket's number and title, plus how to read it (the tracker file's **fetch** operation).
- `{spec}`: the spec, and how to read it.
- `{sources}`: the binding sources, in precedence order.
- `{project_rules}`: the project's rules from `CLAUDE.md`/`AGENTS.md`: visibility, guarded paths, hooks, anything never to be committed.
- `{conventions}`: contracts established so far: the sitting's decisions and earlier tickets' decisions from the ledger.
- `{owed}`: the ledger's **Owed** entries for this ticket.
- `{seams}`: the spec's test seams. Tests drive only these, never internals.
- `{test_cmd}`: the suite command, and how to run a single test file.
- `{probes}`: the full text of [probes.md](probes.md), pasted in. A subagent cannot open files inside the skill.

## Prescan

```
Read-only: edit nothing, commit nothing, write nothing to the tracker.

Scan for decision gaps before an unattended build of {spec}. Read the spec, every ticket in
{ticket_list}, and every binding source in {sources}.

A gap is a hard-to-reverse choice that no binding source makes, usually a contract: something
one ticket produces that another ticket, a user, or another program consumes. Look for: CLI
commands, arguments, flags and the tool's name (and collisions such as a command sharing the
tool's name); machine-readable output fields and exit codes; file and folder layouts and names;
file formats one ticket writes and another reads; config keys later tickets must follow;
URL/query/DOM contracts between components; where a deliverable lives and how it is installed;
places where binding sources contradict each other.

Easy-to-reverse choices are not gaps; leave them out.

Report each gap in under 80 words: the question; the producing and consuming tickets; two or
three options with your recommendation first; why it is hard to reverse. Then list any ticket
whose acceptance criteria need a human to judge or run.
```

## Implementer

```
Implement ticket {ticket} of {spec}, on the checked-out branch {branch}.

Read first: the ticket; the spec; {sources} (earlier entries win where they disagree); the
project's domain docs; the code already on the branch.

Established conventions (keep them): {conventions}
Owed to this ticket by earlier reviews: {owed}

Build it with the `implement` skill, using `tdd` as the red-green engine. Test only through
{seams}; never test internals. Smallest working change: no speculative abstractions, and
stdlib or already-installed dependencies first. Scope: this ticket's acceptance criteria only.
Every existing test stays green: {test_cmd}.

Project rules: {project_rules}. Commit nothing, push nothing, write nothing to the tracker.

If the ticket needs a hard-to-reverse decision that no binding source makes, STOP and report
the question with your recommendation instead of building. Make easy-to-reverse choices
yourself, and list them.

Report in under 200 words: files changed; the test command and its counts; each acceptance
criterion as met, not met, or needs a human run; every decision you made that no source made.
```

## Reviewer

```
Review only: edit nothing, commit nothing, write nothing to the tracker. Do the review
yourself; if a skill you use spawns sub-agents, wait for all of them before reporting.

Review the uncommitted diff for ticket {ticket} of {spec} on branch {branch}. Read the ticket,
the spec, {sources}, and the diff.

{prior_fixes}

1. Use the `code-review` skill against the acceptance criteria, the spec and the sources.
   Tests drive only {seams}.
2. Probe: try every applicable probe below by hand, with synthetic input. Report what you
   reproduced, not what you suspect.
   {probes}
3. Adjudicate each implementer decision: {decisions}. For each, quote the source that settles
   it, or say it is unsettled and whether it is hard to reverse.
4. Check the project rules: {project_rules}. Run a dry-run stage (`git add -A --dry-run`).
5. Run {test_cmd}; record the count and duration.
6. Run `ponytail:ponytail-review` over the diff, if installed.

Must-fix means: an unmet acceptance criterion; a contradiction of the spec, an ADR or a
binding decision ticket; a broken standing invariant; a defect you reproduced; a test likely
to flake. Everything else is a nit.

Report in under 220 words: CLEAN, or MUST-FIX with file:line and a one-line fix each; your
adjudications; nits; the test result.
```

`{prior_fixes}` is empty on a first review. On a re-review it lists the fixes applied, adds "Confirm each is correct and nothing regressed," and asks the reviewer to re-check the whole diff, not just the fixes.

## Fixer

```
Fix review findings in the uncommitted work for ticket {ticket} of {spec}, on branch
{branch}. Read the changed files and the ticket first.

Fix exactly these:
{findings}

Use `tdd`: write a failing test for each defect first, through {seams} only. Smallest change.
Nothing beyond the list. The ticket's tests stay green; run {test_cmd_ticket}.

Project rules: {project_rules}. Commit nothing, push nothing, write nothing to the tracker.

Report in under 100 words: what changed, and the test counts.
```
