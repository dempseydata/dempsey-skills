# Choosing Techniques In Chat

Loaded only when the user won't use the composer page (no browser, headless, or they declined). Here you pick the batch in conversation. **3–4 is the sweet spot.** Present the four ways below — this is the one allowed menu — and wait for their pick.

- **Facilitator Chosen (default)** — from the goal, your `{favourites}`, and the `categories` map, name a batch of 3–4. Confirm exact names with a targeted `list --category` on only the categories you're drawing from; never enumerate the library to choose.
- **Browse** — send them to the composer page after all (`## Run a Session` in `SKILL.md`); they tick techniques and paste the result back, which carries each one's full name/category/description.
- **Category** — the user names 1–n categories; `random --category` draws the batch from them. No listing needed.
- **Inventive Flow** — invent at least 3 techniques, announce the order before the first, touch no script. Log each one's name + description so you can offer to append a keeper to `{catalog}` at wrap-up.

The library is large — never pull it whole into context. The only way in is the helper, always passing `--file {catalog}`. Subcommands of `uv run {skill-dir}/scripts/brain.py --file {catalog}`:

- `categories` — names + counts; the cheap survey map.
- `list --category X [--category Y]` — the index (name + gist) for those categories. Bare `list` is refused by the script.
- `random --category X [...] -n 4` — draw a batch blind, listing nothing.
- `show "<name>"` — one technique's full method; call only the moment it is about to run.
- `html --out <path>` — write the composer page to a file (the Browse option above).

`{catalog}` is the user's own file, so anything they have added — including whole new categories — is already first-class in every command; prefer `{favourites}` where they fit. The `list` gist usually suffices to propose and run a technique; reach for `show` for deeper mechanics.
