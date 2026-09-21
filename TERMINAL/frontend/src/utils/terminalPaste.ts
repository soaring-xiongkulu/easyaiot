// Paste payload preparation + write/scroll for an SSH/local session.
//
// Extracted from BaseTerminal.pasteToSession so the paste behavior is
// unit-testable (the component itself is not mountable in vitest).

export interface PasteTarget {
  /** Already-known bracketed-paste mode of the target session's terminal. */
  bracketedPasteMode: boolean
  /** Write the final payload to the session. */
  write: (payload: string) => void
  /** Yank the viewport back to the bottom after writing. */
  scrollToBottom: () => void
}

/** Normalize line endings: \r\n -> \n, then drop leftover \r (Windows
 * clipboard). Keeps multi-line pastes from doubling newlines in vim. */
export function normalizePastedText(text: string): string {
  return text.replace(/\r\n/g, '\n').replace(/\r/g, '')
}

/** Wrap in bracketed-paste markers when the app enabled the mode, so vim etc.
 * don't re-indent each pasted line. */
export function bracketPaste(text: string, enabled: boolean): string {
  return enabled ? `\x1b[200~${text}\x1b[201~` : text
}

// Paste a block of text into one session: normalize + bracket-wrap, write to
// the session, then yank the viewport back to the bottom. Pasted input must
// behave like keyboard input — Enter/arrows already auto-scroll via xterm's
// scrollOnUserInput, but paste bypasses the keydown path (issue 629).
export function pasteWithScroll(target: PasteTarget, text: string): void {
  const payload = bracketPaste(normalizePastedText(text), target.bracketedPasteMode)
  target.write(payload)
  target.scrollToBottom()
}