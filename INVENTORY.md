# Inventory

What is in this plugin, where each piece came from, what was changed on the way in, and how to
refresh it later. Keep this current — it is the only record of provenance, because folding a
skill in here severs it from whatever update mechanism it shipped with.

Last reviewed: **2026-09-28** · plugin version **0.4.2**

| Skill | Origin | Pinned at | Licence | Files | Size | Local mods |
| --- | --- | --- | --- | --- | --- | --- |
| `brainstorm` | [bmad-code-org/bmad-module-creative-intelligence-suite](https://github.com/bmad-code-org/bmad-module-creative-intelligence-suite), skill `bmad-brainstorming` (installed via `npx bmad-method install`, BMAD v6.9.0) | forked 2026-09-06 | MIT, © BMad Code, LLC | 14 | 172K | **Extensive — a fork, not a copy** |
| `archify` | [tt-a1i/archify](https://github.com/tt-a1i/archify) | `v2.17.0-dev.1` (development channel) | MIT | 194 | 7.4M | 3 files, path rewrites |
| `excalidraw-diagram` | [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill) | `8646fcc9f74f38539c6cdb4c969723336a96ddcd` (2026-03-01, "Better setup") | **None stated** (checked 2026-09-28) | 9 | 88K | 1 file, path + venv rewrites |
| `security-preflight` | Original, no upstream | — | MIT | 1 | 8.0K | none — verbatim |
| `mp-night-shift` | Original, no upstream | — | MIT | 4 | 24K | none — original |

Nothing here tracks upstream automatically. Refreshing is always: fetch upstream to a scratch
directory, diff against `skills/<name>/`, copy the changes in, then **re-apply the local mods
listed below**. Nothing else in this repo will remind you.

## Licences

The repo's root `LICENSE` (MIT) covers the originals and everything outside `skills/`. A skill
folder that carries its own `LICENSE` is governed by that file instead.

| Skill | Licence file | Status |
| --- | --- | --- |
| `brainstorm` | `skills/brainstorm/LICENSE` | Upstream MIT notice retained, as MIT requires, plus a trademark disclaimer: BMad™ and its variants are BMad Code, LLC's marks, so they may credit the source but never brand this fork. |
| `archify` | `skills/archify/LICENSE` | Upstream's, verbatim. |
| `excalidraw-diagram` | none | **Upstream states no licence**: no `LICENSE` file, GitHub reports none, and its README is silent (checked 2026-09-28). Without one, no redistribution right is granted. Worth re-checking — one may have been added since: `gh api repos/coleam00/excalidraw-diagram-skill --jq .license`. If it has, copy the file into `skills/excalidraw-diagram/` and update this row. |
| `security-preflight`, `mp-night-shift` | root `LICENSE` | Originals, MIT. |

`plugin.json`'s `license` reads `SEE LICENSE IN README.md` rather than `MIT`, because the plugin
as a whole is not uniformly MIT while `excalidraw-diagram` is in it.

## State that lives outside the plugin

A plugin install is *copied* into `~/.claude/plugins/cache/dempsey/dempsey-skills/<version>/`,
even from a local directory source. Anything inside the plugin is therefore frozen at install
and replaced on every update. So anything the user edits, or anything expensive to rebuild,
lives outside it:

| Path | Belongs to | Why outside | If deleted |
| --- | --- | --- | --- |
| `~/.claude/brainstorm/techniques.csv` | `brainstorm` | User-owned catalog, edited over time | Re-seeded from `skills/brainstorm/assets/techniques-seed.csv` on next run; **your edits are gone** |
| `~/.claude/brainstorm/favourites.txt` | `brainstorm` | Optional, user-written | Skill runs without it |
| `~/.claude/excalidraw-diagram/.venv` | `excalidraw-diagram` | 146 MB; would rebuild on every plugin update | Rebuild with the setup command below (~40s from uv cache) |
| `~/Library/Caches/ms-playwright/` | `excalidraw-diagram` | Playwright's own machine-wide Chromium cache | `uv run playwright install chromium` re-downloads (~150 MB) |

Back up `~/.claude/brainstorm/` before reinstalling anything. It is the only irreplaceable
state in the list.

---

## brainstorm

**Upstream:** https://github.com/bmad-code-org/bmad-module-creative-intelligence-suite
(the skill ships as part of https://github.com/bmad-code-org/BMAD-METHOD's installer).

A fork, taken over wholesale on 2026-09-06 — treat upstream as dead, not as something to
merge from. See `README.md` for what was cut and why.

**Why it will never be refreshed from upstream:** BMAD's only update path is
`npx bmad-method install`, which restores all 22 deliberately-removed CIS skills every time.
That is precisely what forking retired.

**Vendored from outside the original skill directory:** `scripts/memlog.py`, taken from
`_bmad/scripts/memlog.py`. Stdlib-only, no BMAD coupling.

## archify

**Upstream:** https://github.com/tt-a1i/archify

Upstream ships **no plugin manifest** — no `.claude-plugin/`, `marketplace.json` or
`plugin.json`. Its distribution is `npx skills add tt-a1i/archify -g`, which copies into
`~/.claude/skills/`. Folding therefore severed no update path Claude Code was using.

`skill-release.json` names an update manifest at
`https://tt-a1i.github.io/archify/skill-updates/archify/stable.json`. That is consumed by the
`skills` CLI, not by Claude Code. It is left in place as a provenance record; it does nothing here.

**Local mods to re-apply after any refresh** — 16 occurrences across 3 files:

```bash
# from skills/archify/
for f in SKILL.md references/brand-marks.md references/delivery-contract.md; do
  sed -i '' 's|node bin/archify\.mjs|node {skill-dir}/bin/archify.mjs|g' "$f"
done
```

Plus the `## Paths` section inserted after the `# Archify` heading in `SKILL.md`. Both exist
because upstream assumes cwd is the skill directory, which is false for a plugin skill.

**Runtime:** Node ≥ 18, and **no `npm install`**. The `devDependencies` in `package.json`
(ajv, parse5, saxes, simple-icons) serve the upstream test suite only. Verify with
`node skills/archify/bin/archify.mjs doctor` from any directory — it should end "Archify is ready."

**Known upstream defect, not introduced here:** `package.json`'s npm scripts reference
`../scripts/`, outside the skill directory. The skill was extracted from a monorepo, so
`npm test` and the `build:*` scripts are broken as distributed. The CLI itself is unaffected.

**Refresh:**

```bash
npx skills add tt-a1i/archify -g          # lands in ~/.claude/skills/archify
diff -rq --exclude=.git ~/.claude/skills/archify skills/archify
# copy across, re-apply the sed above, re-add the Paths section, then:
rm -rf ~/.claude/skills/archify           # never leave a duplicate — it double-triggers
```

## excalidraw-diagram

**Upstream:** https://github.com/coleam00/excalidraw-diagram-skill · **Licence: none stated
upstream as of 2026-09-28** — see *Licences* above, and re-check before relying on it.

Upstream is 9 files with no manifest; its README says to `cp -r` the repo into
`.claude/skills/`. Two commits total, effectively static.

**Left behind on fold:** the upstream `.git` clone (136K) and `references/.venv` (146 MB).
Also `.gitignore`, which excluded `uv.lock` — the lock file **is** committed here deliberately,
for reproducible renders.

**Local mods to re-apply after any refresh** — all in `SKILL.md`:

1. A `## Paths` section after the `# Excalidraw Diagram Creator` heading.
2. The render command: `cd .claude/skills/excalidraw-diagram/references && uv run …`
   → `cd {skill-dir}/references && UV_PROJECT_ENVIRONMENT=~/.claude/excalidraw-diagram/.venv uv run …`
3. The first-time-setup block: same two changes, plus `export UV_PROJECT_ENVIRONMENT=…`.

**Setup, once per machine:**

```bash
cd skills/excalidraw-diagram/references
export UV_PROJECT_ENVIRONMENT=~/.claude/excalidraw-diagram/.venv
uv sync && uv run playwright install chromium
```

**Known constraint:** `references/render_template.html` line 16 imports
`@excalidraw/excalidraw` from `esm.sh` at render time. The visual-validation loop needs live
network and times out offline or in a restricted sandbox — verified as upstream behaviour, not
a fold defect.

**Refresh:**

```bash
git clone https://github.com/coleam00/excalidraw-diagram-skill /tmp/exc
diff -rq -x .git -x .venv -x .gitignore /tmp/exc skills/excalidraw-diagram
# copy across, re-apply the three SKILL.md mods above
```

## security-preflight

Single file, MIT, no upstream, no dependencies, no coupling. Verbatim. Nothing to refresh.

## mp-night-shift

Original, no upstream. Coupled to `mattpocock-skills` by convention, not by copy: it reads the
project's `docs/agents/*.md` (written by `/setup-matt-pocock-skills`) and calls `implement`,
`tdd` and `code-review` by name. If Matt renames those skills or changes the tracker
operations' vocabulary (frontier, claim, resolve, blocking), update `SKILL.md` and
`references/briefs.md`. Nothing to refresh otherwise.

---

## Adding a skill to this plugin

1. Copy the payload into `skills/<name>/`. Exclude `.git`, `node_modules`, `.venv`,
   `__pycache__`, `.pytest_cache` — plugin installs copy the working tree, not `git archive`,
   so ignored files still get copied into the cache.
2. Rewrite any path that assumes cwd is the skill directory, or that hardcodes
   `.claude/skills/<name>/`, to `{skill-dir}`-anchored form. **`CLAUDE_PLUGIN_ROOT` does not
   work here** — it is a hooks-only variable, unset in the session shell. Bind `{skill-dir}` to
   the runtime-reported skill base directory instead, as every skill here does.
3. Move anything user-editable or expensive to rebuild to `~/.claude/<name>/`, and say so in
   the table above.
4. Add the path to `skills` in `.claude-plugin/plugin.json` and bump `version`.
5. Add a row and a section here, with the upstream URL and the licence **as checked at source**,
   not as remembered. Copy any upstream `LICENSE` into the skill folder.
6. `claude plugin update dempsey-skills@dempsey`, then verify from a directory that is **not**
   this repo — that is what catches a missed relative path.
7. Delete the original from `~/.claude/skills/`. Two copies double-trigger.

## Related, deliberately not folded in

- **`diagram-design`** ([cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design))
  — ships its own `.claude-plugin/` marketplace manifest, so it is installed as
  `diagram-design@diagram-design` and stays updatable at no maintenance cost. Folding a
  maintained plugin would be strictly worse.
- **`graphify`**, **`playwright-cli`** — still loose in `~/.claude/skills/`. Not evaluated.
