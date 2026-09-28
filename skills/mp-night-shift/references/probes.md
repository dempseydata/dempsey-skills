# Probes

Reading the code misses what trying it catches. Try each probe that applies to the ticket by hand, with synthetic input, and report what you reproduce. Every probe here was drawn from a defect that passed a reading review.

## Input

- **Normalised to nothing.** Input that becomes empty after trimming or normalisation, such as `"   "` or `"**"`. An empty string is a substring of everything.
- **Inherited keys.** Lookups on user-controlled keys: try `toString`, `constructor`, `__proto__`. Own-property checks only.
- **Degenerate sizes.** Zero, one, and a size an order of magnitude past the fixtures. A value of zero used as a divisor or a duration.

## Files and paths

- **Confinement.** For any path built from input: `..`, absolute paths, a symlinked file, a symlinked directory, and a dangling symlink pointing outside the allowed tree.
- **Check-then-write races.** An existence check followed by a write: prefer an exclusive-create flag (`wx`) and refuse symlinked targets.
- **Half-written output.** Make a step fail midway. Nothing, or everything, is on disk: build every output before writing any.
- **Stale output.** Run twice with a smaller second run. Nothing from the first run survives to be mistaken for the second's.

## Failure paths

- **Crash still reports.** An unexpected exception still produces the documented report and its exit code, not a bare stack trace.
- **Every failure has its documented code.** Timeouts, refused connections, dropped responses, and tools missing from `PATH` each map to the exit code the contract names.
- **Cleanup on every path.** Browsers, child processes and temp directories are released when a step throws, including a throw during setup.

## Scale and time

- **Combinatorial search.** Anything that enumerates splits, orderings or subsets: time it at n = 10. Unbounded growth means it needs a bound from the sources, or a cheap cap.
- **Wall-clock tests.** A time bound needs at least 4× headroom over the measured run, on a loaded machine.

## Invariants

- **Cache keys track output.** Wherever a key claims "equal key, equal output", sweep a range of inputs and find a pair where the output differs and the key doesn't, especially at the boundaries of an animation or state change.
- **Determinism.** Anything random is seeded. Two runs produce identical output, or match within the documented tolerance.

## Trust

- **Untrusted text reaching a model.** Fetched pages, user files, issue bodies: the instructions treat them as data, and shell arguments built from them are quoted.
- **Secrets and machine paths** in anything that will be committed or published.
