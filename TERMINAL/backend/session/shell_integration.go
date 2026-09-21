package session

import (
	"bytes"
	"fmt"
	"net/url"
	"strings"
	"time"

	"golang.org/x/crypto/ssh"

	"easyaiot/terminal/backend/log"
)

// TerminalCwdSink, when installed, receives each cwd reported through OSC-7
// so the App layer can forward it to the frontend as a Wails event. Installed
// once in NewApp, next to TransferEventSink.
var TerminalCwdSink func(sessionID, cwd string)

const (
	osc7Prefix            = "\x1b]7;"
	osc7BEL               = "\x07"
	osc7ST                = "\x1b\\"
	sshIntegrationTimeout = 5 * time.Second
	sshCleanupGracePeriod = 500 * time.Millisecond

	// maxOSCPending caps how long an unterminated OSC-7 payload may buffer
	// display output before it is dropped as garbage. Without this a program
	// emitting a bare "\x1b]7;" with no terminator would swallow the whole
	// rest of the terminal stream.
	maxOSCPending = 4096
)

// osc7Scanner extracts OSC-7 cwd reports from a terminal byte stream,
// tolerating sequences split across read chunks, and removes them from the
// display output (xterm.js would hide them, but stripping here keeps the
// raw stream clean for decoding/logging paths).
//
// State is a single leftover buffer that holds everything from the start of
// an unfinished sequence (prefix included) or, when no sequence is open, the
// tail bytes that could be a partial "\x1b]7;" prefix. Bytes before an
// unfinished sequence are emitted immediately, so the cleaned output of a
// chunk is always complete display text except for the held tail.
type osc7Scanner struct {
	leftover []byte
}

// Feed consumes the next chunk of the terminal byte stream. It returns the
// cwd of any OSC-7 sequence completed within this chunk (percent-decoded,
// "file://host" prefix stripped), the cleaned display bytes with all OSC-7
// sequences removed, and whether a cwd was found. cleaned must always be
// used in place of the input for display, even when nothing was found: a
// partially arrived sequence is withheld and flushed on a later Feed.
func (sc *osc7Scanner) Feed(data []byte) (cwd string, cleaned []byte, found bool) {
	buf := make([]byte, 0, len(sc.leftover)+len(data))
	buf = append(buf, sc.leftover...)
	buf = append(buf, data...)
	sc.leftover = nil

	var out []byte
	for {
		i := bytes.Index(buf, []byte(osc7Prefix))
		if i < 0 {
			// No sequence start in buf: flush everything except a tail that
			// could be a split prefix.
			keep := partialPrefixLen(buf)
			out = append(out, buf[:len(buf)-keep]...)
			sc.leftover = append(sc.leftover, buf[len(buf)-keep:]...)
			break
		}
		out = append(out, buf[:i]...)
		rest := buf[i+len(osc7Prefix):]
		// The payload ends at whichever terminator comes FIRST. Real prompts
		// emit an ST-terminated OSC-7 immediately followed by a BEL-terminated
		// OSC-0 title; searching for BEL first would swallow the ST plus the
		// whole title into the payload (field-reproduced).
		belIdx := bytes.IndexByte(rest, osc7BEL[0])
		stIdx := bytes.Index(rest, []byte(osc7ST))
		end, termLen := -1, 0
		if belIdx >= 0 && (stIdx < 0 || belIdx < stIdx) {
			end, termLen = belIdx, 1
		} else if stIdx >= 0 {
			end, termLen = stIdx, len(osc7ST)
		}
		if end < 0 {
			// Terminator not yet arrived: hold everything from the sequence
			// start and re-process it on the next Feed. Display bytes
			// collected so far (out) are returned now.
			if len(rest) > maxOSCPending {
				// Garbage (never-terminated sequence): drop it rather than
				// stalling the display stream forever.
				log.Writef("osc7: dropping unterminated sequence (%d bytes)", len(rest))
				buf = rest
				continue
			}
			sc.leftover = append(sc.leftover, buf[i:]...)
			return cwd, out, found
		}
		raw := string(rest[:end])
		buf = rest[end+termLen:]
		cwd = decodeOSC7Payload(raw)
		found = true
	}
	return cwd, out, found
}

// partialPrefixLen returns the length of the longest suffix of buf that is a
// proper prefix of osc7Prefix, i.e. how many trailing bytes must be withheld
// because a sequence start may be split across the chunk boundary.
func partialPrefixLen(buf []byte) int {
	max := len(osc7Prefix) - 1
	if len(buf) < max {
		max = len(buf)
	}
	for k := max; k > 0; k-- {
		if bytes.HasPrefix([]byte(osc7Prefix), buf[len(buf)-k:]) {
			return k
		}
	}
	return 0
}

// decodeOSC7Payload converts an OSC-7 payload ("file://host/path" or a bare
// path) into a plain path. url.Parse already percent-decodes u.Path, so the
// result is proper UTF-8 regardless of the session's display encoding; the
// value never re-enters the terminal stream, only the cwd sink.
func decodeOSC7Payload(raw string) string {
	if u, err := url.Parse(raw); err == nil && u.Path != "" {
		return u.Path
	}
	return raw
}

// buildShellBootstrap returns the temporary files and arguments used to start
// an SSH shell with integration injected. The user's
// own rc files are sourced FIRST; our hook is chained (prepended/appended),
// never overwriting user hooks. ok=false for unsupported/unknown shells.
//
// The <rcfile>/<dir> placeholders in startArgs are replaced by real temporary
// paths when starting SSH shell integration.
func buildShellBootstrap(shell string) (files map[string]string, startArgs []string, ok bool) {
	base := shellBasename(shell)
	const oscFn = `__terminal_osc7() { printf '\033]7;file://%s\033\\' "$PWD" 2>/dev/null; }`
	switch {
	case base == "bash":
		// Bash ignores --rcfile in login mode and login_shell is immutable, so
		// the injected shell cannot be a literal login shell. Reproduce its
		// startup-file order instead. User profiles commonly source ~/.bashrc
		// themselves; sourcing it here too would execute it twice.
		rc := "[ -r /etc/profile ] && . /etc/profile\n" +
			"if [ -r \"$HOME/.bash_profile\" ]; then\n" +
			"  . \"$HOME/.bash_profile\"\n" +
			"elif [ -r \"$HOME/.bash_login\" ]; then\n" +
			"  . \"$HOME/.bash_login\"\n" +
			"elif [ -r \"$HOME/.profile\" ]; then\n" +
			"  . \"$HOME/.profile\"\n" +
			"fi\n" +
			oscFn + "\n" +
			"case \"$(declare -p PROMPT_COMMAND 2>/dev/null)\" in\n" +
			"  \"declare -a\"*) PROMPT_COMMAND=(\"__terminal_osc7\" \"${PROMPT_COMMAND[@]}\") ;;\n" +
			"  *) PROMPT_COMMAND=\"__terminal_osc7${PROMPT_COMMAND:+;$PROMPT_COMMAND}\" ;;\n" +
			"esac\n"
		return map[string]string{"rcfile": rc}, []string{"--rcfile", "<rcfile>"}, true
	case base == "zsh":
		rc := "[ -f \"$HOME/.zshrc\" ] && . \"$HOME/.zshrc\"\n" +
			oscFn + "\n" +
			"precmd_functions+=(__terminal_osc7)\n"
		// zsh always sources $ZDOTDIR/.zshenv; ours chains the user's own
		// ~/.zshenv so nothing the user relies on is lost.
		env := "[ -f \"$HOME/.zshenv\" ] && . \"$HOME/.zshenv\"\n"
		profile := "[ -f \"$HOME/.zprofile\" ] && . \"$HOME/.zprofile\"\n"
		login := "[ -f \"$HOME/.zlogin\" ] && . \"$HOME/.zlogin\"\n"
		logout := "[ -f \"$HOME/.zlogout\" ] && . \"$HOME/.zlogout\"\n"
		return map[string]string{
			".zshrc": rc, ".zshenv": env, ".zprofile": profile,
			".zlogin": login, ".zlogout": logout,
		}, []string{"ZDOTDIR=<dir>"}, true
	case base == "fish":
		cmd := "functions -c fish_prompt __terminal_orig_prompt; " +
			"function fish_prompt; __terminal_osc7; __terminal_orig_prompt; end; " +
			"function __terminal_osc7; printf '\\e]7;file://%s\\e\\\\' $PWD; end"
		return nil, []string{"-l", "-C", cmd}, true
	}
	return nil, nil, false
}

// buildWSLShellBootstrap preserves the existing WSL startup behavior. SSH and
// WSL use different launch mechanisms, so changes made to approximate SSH
// login-shell semantics must not silently alter WSL initialization.
func buildWSLShellBootstrap(shell string) (files map[string]string, ok bool) {
	base := shellBasename(shell)
	const oscFn = `__terminal_osc7() { printf '\033]7;file://%s\033\\' "$PWD" 2>/dev/null; }`
	switch base {
	case "bash":
		rc := "[ -f \"$HOME/.bashrc\" ] && . \"$HOME/.bashrc\"\n" +
			"[ -f \"$HOME/.bash_profile\" ] && . \"$HOME/.bash_profile\"\n" +
			oscFn + "\n" +
			"case \"$(declare -p PROMPT_COMMAND 2>/dev/null)\" in\n" +
			"  \"declare -a\"*) PROMPT_COMMAND=(\"__terminal_osc7\" \"${PROMPT_COMMAND[@]}\") ;;\n" +
			"  *) PROMPT_COMMAND=\"__terminal_osc7${PROMPT_COMMAND:+;$PROMPT_COMMAND}\" ;;\n" +
			"esac\n"
		return map[string]string{"rcfile": rc}, true
	case "zsh":
		rc := "[ -f \"$HOME/.zshrc\" ] && . \"$HOME/.zshrc\"\n" +
			oscFn + "\nprecmd_functions+=(__terminal_osc7)\n"
		env := "[ -f \"$HOME/.zshenv\" ] && . \"$HOME/.zshenv\"\n"
		return map[string]string{".zshrc": rc, ".zshenv": env}, true
	}
	return nil, false
}

// buildRuntimeCwdHook returns a one-line snippet that installs the OSC-7 cwd
// hook into an ALREADY-RUNNING interactive shell (the startup injection in
// buildShellBootstrap can only change how the shell starts). The snippet is
// written to the session's stdin like a typed command: leading space keeps it
// out of bash history (HISTCONTROL=ignorespace), the trailing newline executes
// it. Re-injection is guarded so hooks are never chained twice. ok=false for
// unsupported shells.
func buildRuntimeCwdHook(shell string) (string, bool) {
	base := shellBasename(shell)
	const oscFn = `__terminal_osc7() { printf '\033]7;file://%s\033\\' "$PWD" 2>/dev/null; }`
	switch base {
	case "bash":
		return " " + oscFn + "; " +
			`case "$(declare -p PROMPT_COMMAND 2>/dev/null)" in` + " " +
			`"declare -a"*) [[ "${PROMPT_COMMAND[*]}" == *__terminal_osc7* ]] || PROMPT_COMMAND+=("__terminal_osc7") ;;` + " " +
			// ${PROMPT_COMMAND-} keeps the guard from erroring under set -u
			// when the variable is unset.
			`*) [[ "${PROMPT_COMMAND-}" == *__terminal_osc7* ]] || PROMPT_COMMAND="__terminal_osc7${PROMPT_COMMAND:+;$PROMPT_COMMAND}" ;;` + " " +
			"esac\n", true
	case "zsh":
		return " " + oscFn + "; " +
			// -0 default guards against set -u when precmd_functions is unset.
			`(( ${precmd_functions[(I)__terminal_osc7]-0} )) || precmd_functions+=(__terminal_osc7)` + "\n", true
	case "fish":
		return " if not functions -q __terminal_osc7; " +
			"functions -c fish_prompt __terminal_orig_prompt; " +
			"function fish_prompt; __terminal_osc7; __terminal_orig_prompt; end; " +
			`function __terminal_osc7; printf '\e]7;file://%s\e\\' $PWD; end; end` + "\n", true
	}
	return "", false
}

// shellBasename returns the basename of a shell path ("/usr/bin/zsh" →
// "zsh").
func shellBasename(shell string) string {
	if i := strings.LastIndexByte(shell, '/'); i >= 0 {
		return shell[i+1:]
	}
	return shell
}

func injectShellIntegration(client *ssh.Client) (command, tempPath string) {
	if client == nil {
		return "", ""
	}
	shell, err := sshRunCommand(client, "echo $SHELL", "", sshIntegrationTimeout)
	if err != nil {
		log.Writef("ssh: shell integration skipped (detect shell: %v)", err)
		return "", ""
	}
	shell = strings.TrimSpace(shell)
	files, args, ok := buildShellBootstrap(shell)
	if !ok {
		return "", ""
	}
	switch shellBasename(shell) {
	case "bash":
		path, err := sshWriteRemoteFile(client, files["rcfile"])
		if err != nil {
			log.Writef("ssh: shell integration skipped (write rcfile: %v)", err)
			return "", ""
		}
		return bashIntegrationCommand(path), path
	case "zsh":
		dir, err := sshWriteRemoteFiles(client, files, []string{".zshrc", ".zshenv", ".zprofile", ".zlogin", ".zlogout"})
		if err != nil {
			log.Writef("ssh: shell integration skipped (write zsh dir: %v)", err)
			return "", ""
		}
		return "exec env ZDOTDIR=" + dir + " zsh -l", dir
	case "fish":
		if len(args) >= 3 {
			return "exec fish -l -C " + fishSingleQuote(args[2]), ""
		}
	}
	return "", ""
}

func sshRunCommand(client *ssh.Client, cmd, stdin string, timeout time.Duration) (string, error) {
	// Start the timeout before opening the channel so the caller always returns
	// within its budget. x/crypto/ssh cannot cancel one pending channel-open;
	// if the peer never replies, this goroutine exits when the client closes.
	timer := time.NewTimer(timeout)
	defer timer.Stop()
	type sessionResult struct {
		sess *ssh.Session
		err  error
	}
	sessionReady := make(chan sessionResult)
	cancelOpen := make(chan struct{})
	defer close(cancelOpen)
	go func() {
		sess, err := client.NewSession()
		select {
		case sessionReady <- sessionResult{sess, err}:
		case <-cancelOpen:
			if sess != nil {
				_ = sess.Close()
			}
		}
	}()

	var sess *ssh.Session
	select {
	case opened := <-sessionReady:
		if opened.err != nil {
			return "", opened.err
		}
		sess = opened.sess
	case <-timer.C:
		return "", fmt.Errorf("command timed out opening SSH session after %s", timeout)
	}
	if stdin != "" {
		sess.Stdin = strings.NewReader(stdin)
	}
	type result struct {
		out []byte
		err error
	}
	done := make(chan result, 1)
	go func() {
		out, err := sess.Output(cmd)
		done <- result{out, err}
	}()
	select {
	case r := <-done:
		closeSSHSessionAsync(sess)
		return string(r.out), r.err
	case <-timer.C:
		// Session.Close writes a channel-close packet and can itself block when
		// the transport is wedged. Do it asynchronously so the timeout remains
		// a bound on this function; closing the client will eventually release it.
		closeSSHSessionAsync(sess)
		return "", fmt.Errorf("command timed out after %s", timeout)
	}
}

func closeSSHSessionAsync(sess *ssh.Session) {
	if sess != nil {
		go func() { _ = sess.Close() }()
	}
}

// bashIntegrationCommand runs the injected interactive shell and then mirrors
// login bash's logout behavior. Keeping logout outside the child avoids
// replacing an EXIT trap installed by the user's profile.
func bashIntegrationCommand(rcfile string) string {
	return "bash --rcfile " + rcfile +
		"; __terminal_status=$?; bash -c '[ -r \"$HOME/.bash_logout\" ] && . \"$HOME/.bash_logout\"'; exit $__terminal_status"
}

func sshWriteRemoteFile(client *ssh.Client, content string) (string, error) {
	out, err := sshRunCommand(client,
		`f=$(mktemp /tmp/terminal-XXXXXX) || exit; printf '%s\n' "$f"; cat > "$f"`,
		content, sshIntegrationTimeout)
	if err != nil {
		if path, pathErr := cleanRemoteTempPath(out); pathErr == nil {
			sshRemoveRemoteTemp(client, path)
		}
		return "", err
	}
	return cleanRemoteTempPath(out)
}

func sshWriteRemoteFiles(client *ssh.Client, files map[string]string, names []string) (string, error) {
	out, err := sshRunCommand(client,
		`d=$(mktemp -d /tmp/terminal-XXXXXX) || exit; printf '%s\n' "$d"`,
		"", sshIntegrationTimeout)
	if err != nil {
		if dir, pathErr := cleanRemoteTempPath(out); pathErr == nil {
			sshRemoveRemoteTemp(client, dir)
		}
		return "", err
	}
	dir, err := cleanRemoteTempPath(out)
	if err != nil {
		return "", err
	}
	for _, name := range names {
		content, ok := files[name]
		if !ok {
			sshRemoveRemoteTemp(client, dir)
			return "", fmt.Errorf("missing bootstrap file %q", name)
		}
		if _, err := sshRunCommand(client, "cat > '"+dir+"/"+name+"'", content, sshIntegrationTimeout); err != nil {
			sshRemoveRemoteTemp(client, dir)
			return "", err
		}
	}
	return dir, nil
}

func sshRemoveRemoteTemp(client *ssh.Client, path string) {
	if client == nil || !isSSHIntegrationTempPath(path) {
		return
	}
	if _, err := sshRunCommand(client, "rm -rf -- '"+path+"'", "", sshIntegrationTimeout); err != nil {
		log.Writef("ssh: shell integration temp cleanup failed for %s: %v", path, err)
	}
}

func isSSHIntegrationTempPath(path string) bool {
	const prefix = "/tmp/terminal-"
	if !strings.HasPrefix(path, prefix) || len(path) != len(prefix)+6 {
		return false
	}
	for _, ch := range path[len(prefix):] {
		if !((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9')) {
			return false
		}
	}
	return true
}

// sshCleanupRemoteTemp waits briefly for best-effort cleanup. If opening a new
// SSH channel stalls on a broken transport, the caller can close the client
// after this bounded grace period instead of blocking Disconnect indefinitely.
func sshCleanupRemoteTemp(client *ssh.Client, path string) {
	if client == nil || !isSSHIntegrationTempPath(path) {
		return
	}
	done := make(chan struct{})
	go func() {
		sshRemoveRemoteTemp(client, path)
		close(done)
	}()
	select {
	case <-done:
	case <-time.After(sshCleanupGracePeriod):
		log.Writef("ssh: shell integration temp cleanup timed out for %s", path)
	}
}

// cleanRemoteTempPath extracts exactly one standalone, strictly validated
// mktemp path. Login banners or shell startup messages may surround the path,
// but zero or multiple candidates are rejected so cleanup is never ambiguous.
func cleanRemoteTempPath(out string) (string, error) {
	var path string
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimSuffix(line, "\r")
		if !isSSHIntegrationTempPath(line) {
			continue
		}
		if path != "" {
			return "", fmt.Errorf("multiple remote temp paths in output %q", out)
		}
		path = line
	}
	if path == "" {
		return "", fmt.Errorf("remote temp path not found in output %q", out)
	}
	return path, nil
}

func fishSingleQuote(s string) string {
	s = strings.ReplaceAll(s, `\`, `\\`)
	s = strings.ReplaceAll(s, `'`, `\'`)
	return `'` + s + `'`
}
