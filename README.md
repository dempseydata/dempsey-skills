# dempsey-skills

Four Claude Code skills for solo builders: a security check before you deploy, an unattended
build of a ticketed spec, facilitated brainstorming, and architecture diagrams.

| Skill | Use it when |
| --- | --- |
| [`security-preflight`](#security-preflight) | You're about to deploy something you built alone |
| [`mp-night-shift`](#mp-night-shift) | A spec's tickets are ready and you're about to walk away. Built for [Matt Pocock's skills](https://github.com/mattpocock/skills) |
| [`brainstorm`](#brainstorm) | You have a rough idea and want more options before choosing one |
| [`archify`](#archify) | You need an architecture, sequence, data-flow or other technical diagram |

The first two are mine. The other two are other people's skills, adapted and credited under
[Credits and licences](#credits-and-licences).

## Install

```bash
claude plugin marketplace add dempseydata/dempsey-skills
claude plugin install dempsey-skills@dempsey --scope user
```

Update with `claude plugin update dempsey-skills@dempsey`. Anything you edit, or that is slow to
rebuild, lives under `~/.claude/<skill>/`, so updates never overwrite it.

## Skills

### security-preflight

**For** catching the ordinary mistakes that sink small projects before they ship: leaked keys,
injection, missing authorisation checks, vulnerable dependencies. If your app lets the public
chat with an AI about your data, a second pass covers prompt injection, runaway API bills, and
what the model can see and do.

**Try** "security check before I deploy".

**You get** findings from a read of your actual code, grouped as *ship blocker*, *should fix* or
*nice to have*, each with what to change.

**Needs** nothing.

### mp-night-shift

**For** people who build with [Matt Pocock's skills](https://github.com/mattpocock/skills): it turns
an agreed spec into committed, reviewed code while you're away.

**Try** `/dempsey-skills:mp-night-shift 42` (a GitHub issue number) or
`/dempsey-skills:mp-night-shift .scratch/<feature>/spec.md`.

**How a shift runs:**

1. **You start it.** Claude checks the repository is clean and the tests pass, maps the tickets
   and their dependencies, and sets aside any ticket that needs a person.
2. **It asks everything up front.** In one sitting, it puts to you every hard-to-undo decision
   the tickets leave open, each with a recommendation.
3. **You leave.** Each ticket gets its own implementer and its own reviewer. It is committed
   only when the whole test suite passes. A ticket that gets stuck sends you one notification,
   and the shift moves on to tickets that don't depend on it.
4. **You come back to a handover:** what was built, what's blocked and why, security findings,
   and what's left.

If the session dies, run the same command again and it resumes. The full procedure is in
[its SKILL.md](skills/mp-night-shift/SKILL.md).

**Needs** [Matt Pocock's skills](https://github.com/mattpocock/skills), with
`/setup-matt-pocock-skills` run in the project. The shift uses his ticket tracker conventions
(GitHub Issues or local files) and his `implement`, `tdd` and `code-review` skills.

```bash
claude plugin marketplace add mattpocock/skills
claude plugin install mattpocock-skills@mattpocock
```

It also uses `security-preflight` and, if installed,
[ponytail](https://github.com/DietrichGebert/ponytail)'s over-engineering review.

### brainstorm

**For** divergent thinking on an idea: a concept, a product premise, an open question. Choose
how involved Claude is: it only prompts you, it contributes alongside you, or it runs the whole
session itself. Pick techniques from a catalog of 108, then converge on what matters.

**Try** "brainstorm ways to get my first ten users".

**You get** a session folder with a log that resumes across conversations, and at the end your
choice of an HTML keepsake of the session or a short intent document to carry into the next step.

**Needs** [`uv`](https://docs.astral.sh/uv/) and Python 3.10+. The technique catalog is copied
to `~/.claude/brainstorm/techniques.csv` on first run, and from then on it's yours to edit.

### archify

**For** technical diagrams: architecture, workflows, API sequences, data pipelines, state
machines, ERDs, class diagrams, trees, timelines and waterfalls, plus one-page explainers. It
works from a plain description, pasted Mermaid, or your actual repository.

**Try** "draw the architecture of this repo".

**You get** a single HTML file with dark and light themes, validated before delivery, exportable
to PNG, SVG or video. Works offline.

**Needs** Node 18+.

## Credits and licences

| Skill | Source | Pinned at | Licence |
| --- | --- | --- | --- |
| `security-preflight`, `mp-night-shift` | Original | — | [MIT](LICENSE) |
| `brainstorm` | Fork of `bmad-brainstorming` from [BMad CIS](https://github.com/bmad-code-org/bmad-module-creative-intelligence-suite) | BMAD v6.9.0 | [MIT](skills/brainstorm/LICENSE), © BMad Code, LLC |
| `archify` | [tt-a1i/archify](https://github.com/tt-a1i/archify) | `v3.2.0` | [MIT](skills/archify/LICENSE), © tt-a1i |

The adapted copies don't update themselves. If you only want archify, install it from upstream
(`npx skills add tt-a1i/archify -g`) and you'll get its updates. [INVENTORY.md](INVENTORY.md)
records what was changed in each skill and how to refresh it.

This `brainstorm` is not affiliated with BMad Code, LLC. BMad™, BMAD-CORE™ and BMAD-METHOD™ are
their trademarks, used here only for credit.

## Contributing

Enable the pre-commit hook once per clone: `git config core.hooksPath .githooks`. It refuses
commits containing home-directory paths, key-shaped strings or transcript filenames. Extend
[the denylist](.githooks/denylist.txt) rather than bypassing it.
