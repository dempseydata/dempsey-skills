# Keep warm: what a ping costs, and how cache-clock pings today

Research for issue #6 (map: issue #1, ModDash). Researched 2026-10-27.
"Keep warm" = pinging a session so its prompt cache does not expire (see the map's glossary).

## Answer in brief

- A warm ping is billed as a **cache read of the whole context**, plus a few uncached tail tokens and a short reply.
  On Claude Opus 5.5 that is about **$0.01 / $0.03 / $0.08** for a 50k / 150k / 400k context. On Claude Sonnet 5.5 it is half that.
- A read **restarts the entry's TTL at no extra charge**, on either TTL. The clock runs from the *start* of the request [2].
- On the 5-minute TTL, keep warm costs about **$0.48 an hour** on Opus 5.5 at 150k. It beats letting the cache go cold
  for idle gaps up to roughly 90 minutes. On the 1-hour TTL, one ping an hour replaces a re-write that costs about 40 times as much.
- **Surprise:** sampled Claude Code transcripts on this machine write **1-hour** cache entries, not 5-minute ones.
  On the 1-hour TTL, cache-clock pings once every ~59 minutes, and its 2-hour cap allows at most 2 pings.
  The ping cadence that people picture (every ~4 minutes) only happens when a session writes 5-minute entries.
- Pro/Max subscribers pay in **usage-limit terms, not dollars** [3]. Anthropic does not publish how a cache read is weighted against those limits.

## Prices (Claude API, first party, per million tokens) [1]

| Model | Base input | 5m cache write (1.25×) | 1h cache write (2×) | Cache hit / refresh | Output |
|---|---|---|---|---|---|
| Claude Opus 5.5 | $4 | $5 | $8 | **$0.20 (0.05×)** | $20 |
| Claude Sonnet 5.5 | $2 | $2.50 | $4 | **$0.10 (0.05×)** | $10 |
| Claude Opus 5 | $5 | $6.25 | $10 | $0.50 (0.1×) | $25 |
| Claude Sonnet 4.6 | $3 | $3.75 | $6 | $0.30 (0.1×) | $15 |

- The pricing table names its column "Cache hits and refreshes", so a refresh is billed as a read [1].
- No long-context surcharge applies: 4.6-and-later models (except Haiku 5.5) bill the full 1M window at standard rates [1].
- `inference_geo` US-only adds 1.1× to every category [1].
- Discrepancy: the bundled `claude-api` skill (cached 2026-10-06) gives Sonnet 5.5 cache reads at $0.20. The live pricing page gives $0.10 (0.05 × $2). The live page wins.

## TTL mechanics [2]

- Default lifetime is 5 minutes. A 1-hour lifetime is opt-in (`"ttl": "1h"`) and costs 2× base input to write.
- "The cache is refreshed for no additional cost each time the cached content is used."
  A read keeps the duration of the write that preceded it [1].
- The lifetime runs from the **start** of the request that reads or writes. Generation time counts against it.
- Minimum cacheable prefix is 512 tokens on Opus 5.5 and Sonnet 5.5, and 1,024 on Sonnet 4.6 [2]. Any real chat clears this.
- The API's own cheapest keep-alive is a `max_tokens: 0` request. It bills the read and no output tokens [2].
  cache-clock cannot use it: the mod API's fork call takes only a prompt, with no output cap (see below).

## How cache-clock pings today (behaviour only)

Source: `mods/cache-clock/` (v0.3.0). That code is an unlicensed derivative, so this section describes behaviour only.
Its mechanism is the mod engine's `$.model.fork`, whose contract is documented in the engine's `claude-code.d.ts` (2.1.308).

1. **Trigger.** The user turns it on with `/keepwarm` or the band button. A one-second tick checks the countdown.
   When the cache is **45 s from expiry**, measured from the end of the last main-thread reply plus the TTL, the tick sends one ping.
   Nothing is sent while a turn is running or while a ping is already out.
2. **TTL detection.** A helper script scans the session transcript's tail, newest first. It reads the
   last main-thread assistant entry's `usage.cache_creation`: 1-hour tokens mean 1h, 5-minute tokens mean 5m.
   With no reply yet, or if detection fails, it assumes 5 minutes. So the cadence follows what Claude Code actually writes.
3. **The ping.** It calls `$.model.fork` with a fixed one-line prompt asking for a one-word reply.
   Per the engine contract, a fork re-sends the main thread's last request (same model, system prompt, tools and messages)
   with that user line appended. Every tool is denied. The fork's own tail is never cached, and it never writes to the transcript.
   The API therefore serves the prefix from cache and restarts the timer of the very entry that the next real turn will read.
4. **Bookkeeping.** On success the clock's reference point moves to the ping's **start time**, which matches the API's
   start-of-request rule. The mod records `cache_read_input_tokens` and `cache_creation_input_tokens`.
   If writes exceed reads it flags that the cache had already gone cold, and that ping paid the full re-write.
5. **Stops.** Keep warm stops when the user sends a message, after **2 hours**, after **30 pings**, after **3 failures in a row**
   (it retries 20 s after a failure), when the fork has nothing to fork (no reply yet, or after `/clear`), or when the mod is hidden or switched off.
6. **Disclosure.** The UI tells the user that each ping counts as a model call against their usage.

Effective cadence:

- **5m TTL:** one ping every ~4 min 15 s, about 14 an hour. The 2-hour cap ends it at about 28 pings, before the 30-ping cap.
- **1h TTL:** one ping every ~59 min 15 s, so at most 2 pings before the 2-hour cap.

## Tokens per ping

| Component | Tokens | Billed as |
|---|---|---|
| Cached prefix (the whole chat as last sent) | ≈ context size, *N* | cache read |
| Ping line plus any request tail after the last breakpoint | tens | base input (the fork's tail is never cached) |
| Cache write | ~0 when warm; ≈ *N* if the entry had lapsed or after `/model` | 5m or 1h write |
| Output | the one-word reply plus any thinking; **estimated 50–300, not measured** | output |

- **Output is not capped and not measured.** The fork contract exposes no `max_tokens`.
- On Opus 5.5, thinking cannot be disabled and default effort is `medium` (from the bundled `claude-api` skill).
  So a reply that says "ok" may still carry thinking tokens at the main thread's effort.
- The worked figures below assume **200 output tokens**. At these context sizes output is 5–30% of the ping cost, so the read dominates.
- To replace the estimate with a number, read the cache-clock log lines or a fork's `usage.output_tokens` on a real session.

## Worked cost per ping (warm, 200 output tokens)

| Model | 50k | 150k | 400k |
|---|---|---|---|
| Opus 5.5 | $0.014 | $0.034 | $0.084 |
| Sonnet 5.5 | $0.007 | $0.017 | $0.042 |
| Opus 5 | $0.030 | $0.080 | $0.205 |
| Sonnet 4.6 | $0.018 | $0.048 | $0.123 |

What the ping avoids: re-writing the whole context once it goes cold.

| Model | 5m re-write 50k / 150k / 400k | 1h re-write 50k / 150k / 400k |
|---|---|---|
| Opus 5.5 | $0.25 / $0.75 / $2.00 | $0.40 / $1.20 / $3.20 |
| Sonnet 5.5 | $0.125 / $0.375 / $1.00 | $0.20 / $0.60 / $1.60 |
| Opus 5 | $0.31 / $0.94 / $2.50 | $0.50 / $1.50 / $4.00 |

Break-even on a **5m TTL** is the number of pings that equal one 5m re-write:

- **Opus 5.5 / Sonnet 5.5:** about 18–24 pings, or **75–100 minutes** of idle time, because of their 0.05× reads.
- **Opus 5 / Sonnet 4.6:** about 10–12 pings, or **45–50 minutes**.

Past those points it is cheaper to let the cache go cold and pay one re-write. The cost is about $0.48 an hour for Opus 5.5 at 150k, and $1.19 an hour at 400k.

On a **1h TTL** each ping costs one read against one avoided 1h re-write:

- That is a 40× saving on Opus 5.5 and Sonnet 5.5, and 20× on older models.
- Keep warm is almost free there. It also rarely matters, because most gaps are shorter than an hour.

## Subscription (Pro / Max) users

- Pro and Max carry "a five-hour session limit and a weekly limit", shared across Claude and Claude Code [3].
- Dollar pricing applies only to extra usage bought past the limits, billed "at standard API rates" [3].
- A subscriber's ping therefore spends limit headroom, not money. cache-clock's own copy says so.
- **Gap:** Anthropic does not publish how cache reads are weighted against subscription limits [3]. The relative cost of a ping in limit terms cannot be computed from primary sources.
- The dollar tables above are the best available proxy. They are an assumption, not a documented equivalence.

## Implications for ModDash (for the spec, not decided here)

- Show the detected TTL. On 1h sessions, keep warm is near-pointless within its 2-hour cap. On 5m sessions it is worth it only up to roughly 1.5 hours on the current models.
- Show cost per ping (read × price) and the running total. Stop when the cumulative reads approach one re-write, rather than at a fixed 30 pings or 2 hours.
- Measure the ping's real `output_tokens` before relying on the estimate above.

## Sources

1. Pricing — https://platform.claude.com/docs/en/about-claude/pricing (model pricing table and footnotes, prompt caching multipliers, long context pricing). Fetched 2026-10-27.
2. Prompt caching — https://platform.claude.com/docs/en/build-with-claude/prompt-caching (cache lifetime, refresh, 1h TTL, `max_tokens: 0` pre-warm, minimum lengths). Fetched 2026-10-27.
3. Using Claude Code with your Pro or Max plan — https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan. Fetched 2026-10-27.
4. Claude Code mod engine type definitions, `claude-code.d.ts` 2.1.308: `$.model.fork` and `ModelForkRequest` / `ModelForkResult`.
5. `mods/cache-clock/` in this repo (v0.3.0), read for behaviour only.
6. Local observation: the newest Claude Code transcripts on the researching machine recorded `ephemeral_1h_input_tokens` > 0 and `ephemeral_5m_input_tokens` = 0 on main-thread replies. This is one machine and one account type, so treat it as indicative, not general.
