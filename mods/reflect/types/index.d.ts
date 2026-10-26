export type Undo =
  | { kind: 'file'; path: string }
  | { kind: 'text'; path: string; before: string; slug: string; prevLine: string | null }

export type Band = {
  /** offer: the rule, editable, and the buttons. saved: one line with Open, for 8 seconds. */
  phase: 'offer' | 'saved'
  /** Changes with every new band, so an old timer never clears a newer one. */
  id: number
  /** The drafted rule, one line; edited in place before saving. */
  rule: string
  /** 3 to 6 words, kebab-case: the vault file name, and the CLAUDE.md-style dedup key. */
  slug: string
  /** The person's correction, as typed. */
  correction: string
  /** Where the rule was saved (saved phase). */
  path: string
  /** The path as shown on the band. */
  shortPath: string
  /** A line under the buttons: an error, "Already saved" or "Updated". */
  note: string
  /** How to reverse the save just made (saved phase); null once nothing can be undone. */
  undo: Undo | null
}

declare module 'claude-code' {
  interface PluginState {
    reflect: { band: Band | null }
  }
}
