---
name: mp-night-shift
description: Work a spec's agent-ready tickets unattended on Matt Pocock's engineering setup — a fresh implementer and reviewer per ticket — then leave a handover.
disable-model-invocation: true
---

# Night shift

You run the **night shift**: the user hands you a spec's tickets, you work the **frontier** while they are away, and you leave a **handover**. You orchestrate; subagents write and review the code. Your own context holds only their reports and the ledger.

The shift rides on Matt Pocock's engineering skills. `docs/agents/issue-tracker.md` defines how tickets are read, claimed and resolved and how the frontier is computed, for GitHub and `.scratch` alike — use its operations exactly. `implement`, `tdd` and `code-review` do the work inside each ticket.

Input: the spec (an issue number, or `.scratch/<feature>/spec.md`), and optionally a subset of its tickets.

## 1. Prescan

Run [references/prescan.md](references/prescan.md).

Done when the prescan report classes every ticket as agent, human-verified or human, with its blocking edges, lists the binding sources, records every mechanical check, and gives every decision gap a recommended answer.

## 2. Decision sitting

The only time the user is needed. Ask with `AskUserQuestion`, recommended option first, up to four questions per call, until everything is answered:

- every decision gap from the prescan;
- the shift's **authority**: push the build branch and write to the tracker as tickets finish — yes or no;
- the **end state**: leave the work on the branch, or fast-forward the default branch to it and push.

Record each decision as an ADR in the repo's ADR format (see `docs/agents/domain.md`).

Done when every gap is answered and recorded, and authority and end state are explicit.

## 3. Set up

From a clean default branch, create `night-shift/<spec-slug>` (or the name the user gives). Create the ledger at `.scratch/night-shift/<spec-slug>.md` in the format under **Ledger** below. Commit the ADRs and the ledger as the shift's first commit.

If a ledger for this spec already exists on its branch, the shift is **resuming**: check out that branch, read the ledger and the tracker, and go straight to the shift.

Done when the branch exists and that commit is made, or the resumed branch is checked out.

## 4. Shift

Work one ticket at a time until the frontier is empty. The frontier is the tracker's frontier, minus human tickets and anything downstream of an open blocker.

1. **Claim** the first frontier ticket, on GitHub and only with tracker authority. On `.scratch` there is no separate claim; the resolve rides in the ticket's commit.
2. **Implement.** Spawn a fresh foreground subagent with the implementer brief from [references/briefs.md](references/briefs.md).
3. **Review.** Spawn a separate subagent with the reviewer brief.
4. **Fix.** Send the must-fix findings to a fresh subagent with the fixer brief, then re-review. Up to three rounds.
5. **Verify.** Run the full suite yourself. It is green, with every earlier ticket's tests passing.
6. **Commit** `#<n>: <title>`, the body listing each acceptance criterion met. The ledger update rides in the same commit; on `.scratch`, so does the ticket's `Status: resolved`.
7. **Resolve.** On `.scratch` this happened in the commit; push only with authority. On GitHub, with tracker authority: push the branch, then comment with the criteria met, the commit, and any decision made, and close. A ticket whose criteria need a human run gets the comment and stays open.

Each ticket is done when it is committed on a green suite, the ledger row is written, and the tracker matches.

## 5. Handover

1. Run the full suite once more.
2. Run `security-preflight`, both parts, over the branch. List the findings; fix none.
3. Apply the end state the sitting authorised.
4. Write the handover report:
   - each ticket's status, commit, and one line on what it delivered;
   - the decisions worth an ADR;
   - the security findings;
   - every blocked ticket with its question;
   - the nits;
   - what remains.
5. Send one `PushNotification` with the headline, e.g. `shift done: 9/11 closed, 2 blocked on questions`.

Done when the end state is applied and the report is delivered.

## Rules

### Blockers

A **blocker** is any of these:
- a hard-to-reverse decision that no binding source makes;
- a ticket still carrying more than one must-fix, or one that is not small and contained, after three fix rounds;
- an action outside the shift's authority, including a push or tracker write the harness refuses.

A single small, contained defect left after round three is fixed in one more round rather than blocking.

On a blocker:
1. Park any uncommitted work on a local branch `<branch>-wip-<n>` and return to a clean build branch.
2. Mark the ticket and everything downstream of it blocked in the ledger.
3. Send a one-line `PushNotification`: the ticket, the question, the tickets still being worked, then "reply in session to unblock". Example: `#16 blocked: fetch's arguments undecided. Working #17, #18. Reply in session to unblock.`
4. Carry on with the frontier.

The user's reply arrives alongside a tool result, mid-turn. Act on it at once: record the decision (as an ADR if it is one), unpark the work, and put the ticket back on the frontier.

When only blocked tickets remain, ask every open question in one `AskUserQuestion` sitting and wait.

Send nothing for routine progress. A blocker and the handover are the only notifications.

### Must-fix and nits

A finding is **must-fix** when it is any of these:
- an unmet acceptance criterion;
- a contradiction of the spec, an ADR or a binding decision ticket;
- a broken standing invariant;
- a defect the reviewer reproduced;
- a test likely to flake.

Everything else is a **nit**. A nit of about ten lines or fewer, inside the ticket's own diff, is fixed in the fix round. The rest go to the ledger.

### Tests

Fix rounds run the ticket's own tests. The full suite runs before every commit, run by you.

Log each commit's suite duration in the ledger. When it passes twice the baseline, the next implementer moves tests that don't need the costly path onto the cheapest seam that still proves the same thing.

### Owed

When a review defers a finding to a later ticket, record it under that ticket in the ledger. That ticket's implementer brief carries it.

### Decisions

Each implementer reports the decisions no binding source made. Each one goes into the ledger in that ticket's commit. At handover, flag the ones worth an ADR.

## Ledger

```markdown
# Night shift: <spec> — branch <branch>

Authority: push + tracker <yes|no> · End state: <branch only | merge + push> · Baseline: <n> tests, <t> s

| Ticket | Status | Commit | Rounds | Suite | Notes |
| --- | --- | --- | --- | --- | --- |

## Owed
- #<later>: <finding deferred from #<earlier>>

## Decisions
- #<n>: <decision> — ADR? <yes|no>

## Blocked
- #<n>: <question> — downstream: #<m>, #<k>

## Nits
- #<n>: <nit>
```
