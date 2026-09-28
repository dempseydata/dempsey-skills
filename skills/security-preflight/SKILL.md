---
name: security-preflight
description: >
  Pre-deploy security checklist for solo-built personal projects. Catches the
  basic mistakes that bite indie/vibe-coded apps before they ship - leaked
  secrets, injection, missing auth checks, outdated deps - plus a dedicated
  pass for anything exposing a public AI chat over personal data (prompt
  injection, cost/abuse runaway, data scoping, excessive agency). Not for
  enterprise security work, compliance, or offensive testing. Use before
  deploying, when the user asks "is this safe to ship", "security check",
  "review before deploy", or mentions exposing a chat/agent to the public.
license: MIT
---

# Security Preflight

A pre-deploy review for a solo builder shipping a small personal project, not
a security team. Two passes: run Part 1 on everything; run Part 2 too if the
project exposes a public chat/agent interface over data you maintain.

The goal is catching basic, common mistakes before they ship - not exhaustive
penetration testing. Read the actual code; don't just ask the user yes/no
questions about it.

## Part 1: General pre-ship checklist (every project)

### Secrets and environment variables
- Grep the diff and git history for hardcoded API keys, tokens, passwords,
  connection strings. A key that was ever committed, even if later removed,
  must be rotated - removing it from the latest commit doesn't remove it from
  history.
- Confirm `.env` / `.env.local` are in `.gitignore` and were never committed.
- On frameworks with a public/private env-var split (e.g. Next.js
  `NEXT_PUBLIC_*`), check every public-prefixed variable is something safe to
  ship to the browser. A secret accidentally given the public prefix ships in
  the client bundle to every visitor.
- Server-side secrets (DB credentials, LLM API keys, signing secrets) must
  only be read in server-side code paths, never passed to client components.

### Injection
- SQL: flag any string-concatenated or template-literal query built from user
  input. Parameterized queries / ORM methods only.
- XSS: flag any place user-supplied content is rendered as raw HTML
  (`dangerouslySetInnerHTML`, `v-html`, unescaped template output). User
  content should be rendered as text by default; explicit opt-in only, with
  sanitization, if HTML rendering is genuinely needed.

### Auth and access control
- Every API route that returns or mutates data scoped to a specific user must
  check the requester is authorized for *that* record, not just that they're
  logged in (IDOR: incrementing an ID in the URL must not return someone
  else's data).
- Admin/debug routes must be unreachable in production - actually check, don't
  assume a route is "hidden" because it's undocumented.
- No verbose stack traces or internal error details returned to the client in
  production; log them server-side, return a generic message to the user.

### Dependencies
- Run the project's dependency audit (`npm audit`, `pnpm audit`, or
  equivalent) and flag any high/critical findings before deploy.

### Abuse protection
- Any endpoint that's expensive (auth attempts, signup, search, anything
  calling a paid third-party API) needs rate limiting. No rate limit on
  login/signup is a brute-force and cost-abuse vector.
- CORS: anything touching auth or user data should not allow `*` origin.

## Part 2: Public AI chat over personal data

Apply this pass whenever the project lets visitors chat with an LLM about
data the user maintains (resume/portfolio chat, "ask me anything" agents,
etc.). Maps to OWASP's Top 10 for LLM Applications; only the parts relevant
to a small personal deployment are listed here.

### Unbounded consumption (cost/abuse runaway)
- Every chat message is a paid API call with no inherent ceiling. There must
  be a rate limit per visitor (by IP or session) and ideally a hard daily
  spend cap or message-count cap at the provider/gateway level. This is the
  single most common way a small project turns into an unexpected bill -
  treat it as non-negotiable, not optional.
- Cap input length per message and total conversation length/turns; an
  unbounded conversation is an unbounded cost.

### Prompt injection and system-prompt leakage
- Assume visitors will try "ignore your instructions," "repeat your system
  prompt," "pretend you are unrestricted," etc. The system prompt should not
  itself contain anything sensitive (it can and will leak eventually) -
  treat it as public.
- Don't rely on the system prompt alone to enforce behavior; constrain via
  retrieval scope and tool access (below), not just instructions.

### Data scoping
- Audit exactly what's in the corpus the chat can retrieve from. It must be
  the intentionally-public material only - re-check for drafts, private
  notes, contact details beyond what's meant to be public, or anything else
  that ended up in the same folder/index by accident.
- If the underlying source documents (resume, bio docs) ever contained more
  than the intended public version, confirm the indexed/embedded copy was
  regenerated from the redacted version, not the original.

### Excessive agency
- The chat should be read-only over the user's data unless write/tool access
  was a deliberate, explicit design choice. A visitor's message must never be
  able to modify, delete, or add to the underlying data, send emails, or call
  any other tool, unless that's the actual intended product.

### Output risk
- Constrain the chat to the stated topic (the resume/background it's there to
  discuss). An LLM that will happily go off-topic for any visitor is a
  reputational risk - screenshots of it saying something harmful or absurd
  under the owner's name are the realistic failure mode, not a hypothetical.

### Conversation logging and retention
- If conversations are logged (for debugging, analytics, or improvement),
  that's now visitor data the owner is holding. Keep retention minimal, avoid
  capturing more than needed, and don't log anything that could double as
  visitor PII without a reason to.

## Output

Report findings grouped by Part 1 / Part 2, each tagged by severity (ship
blocker / should fix / nice to have). Don't just list problems - say what to
change. If nothing in Part 2 applies (no public chat), say so and skip it.
