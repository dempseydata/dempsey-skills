# Prescan

Two parts: mechanical checks you run yourself, and a decision-gap scan run by one read-only subagent. Together they settle, before the first ticket, everything that would otherwise stop the shift at 2 a.m.

## Prerequisites

- `docs/agents/issue-tracker.md` exists. If it doesn't, stop and tell the user to run `/setup-matt-pocock-skills` first.
- Read it, then `docs/agents/triage-labels.md`, `docs/agents/domain.md`, and the root `CLAUDE.md` or `AGENTS.md`. The project's own rules (visibility, hooks, paths that never enter git) come from these files, and every brief carries them.

## Mechanical checks

Run every row. A failed row becomes a question for the sitting.

| Check | How | Why it earns its place |
| --- | --- | --- |
| Clean start | The working tree is clean, on the default branch, level with its remote | The shift's first commit sits on a known base |
| Guards hold | Hooks the project configures are active (`git config core.hooksPath`, `.githooks/`, husky). What `CLAUDE.md` claims they enforce, they do enforce | A guard claimed but missing fails silently until publication |
| Ticket set | **GitHub:** the spec's sub-issues (`gh api repos/<owner>/<repo>/issues/<n>/sub_issues`), else its task list. **`.scratch`:** `.scratch/<feature>/issues/*.md` | The shift works the spec's tickets and nothing else |
| Blocking edges | Per the tracker file's **Blocking** operation. Order the tickets topologically. A cycle is a question | The frontier needs them |
| Agent, human-verified, or human | A `ready-for-human` label or `Status:` line makes a ticket **human**: the shift skips it. A `ready-for-agent` ticket whose building an agent can do, but some of whose criteria need a person to judge or run, is **human-verified**: the shift builds it and leaves it open (step 7). Otherwise it is **agent**. Unsure means ask. Criteria missing altogether means ask | Human work is excluded up front; human verification is scheduled, not discovered at the end |
| Binding sources | Collect every ADR, closed issue, decision ticket and doc that the spec and tickets cite. Precedence: ADRs, then closed decision tickets, then the spec, then briefs and background only where the others are silent | Implementers who skip a decision ticket build against the wrong rule |
| Tools | Every CLI and binary the spec or tickets name is installed (`command -v`) | A missing tool surfaces mid-ticket as a confusing failure |
| Baseline suite | Find the test command. It passes. Record the test count and duration. No suite means ask | Red-to-green needs a green start; duration growth needs a baseline |

## Decision-gap scan

Spawn one foreground subagent with the prescan brief from [briefs.md](briefs.md).

The heuristic: a gap is almost always a **contract**. Something one ticket produces is consumed by another ticket, by a user, or by another program, and no binding source fixes its shape. Look for:

- CLI commands, arguments, flags, and the tool's own name (watch for collisions such as a command sharing the tool's name);
- machine-readable output fields and exit codes;
- file and folder layouts and names, and which paths are gitignored;
- file formats one ticket writes and another reads;
- config and pack keys that a later ticket must follow;
- URL, query-string or DOM attribute contracts between components;
- where a deliverable lives and how it is installed;
- places where two binding sources contradict each other.

For each gap, the scan returns:
- the question;
- the producing and consuming tickets;
- two or three options, with a recommendation;
- why the choice is hard to reverse.

Easy-to-reverse choices are not gaps. Implementers make those and record them.

## Report

Present these to the user, then move to the sitting:
- the ticket table: order, class (agent, human-verified or human), blocking edges;
- the binding sources, in precedence order;
- each check's result;
- the gaps, each with its recommendation.
