package session

import (
	"bytes"
	"net"
	"os/exec"
	"strings"
	"testing"
	"time"

	"golang.org/x/crypto/ssh"
)

func TestOSC7ScannerSplitAcrossChunks(t *testing.T) {
	var sc osc7Scanner
	// partial sequence in first chunk, rest in second
	cwd1, cleaned1, found1 := sc.Feed([]byte("hello\x1b]7;file://myhost/ho"))
	cwd2, cleaned2, found2 := sc.Feed([]byte("me/user\x1b\\world"))
	if found1 || cwd1 != "" {
		t.Fatal("must not report before terminator")
	}
	if !found2 || cwd2 != "/home/user" {
		t.Fatalf("cwd=%q found=%v", cwd2, found2)
	}
	combined := string(cleaned1) + string(cleaned2)
	if combined != "helloworld" {
		t.Fatalf("cleaned = %q, want helloworld", combined)
	}
	if bytes.Contains([]byte(combined), []byte("\x1b]7;")) {
		t.Fatal("cleaned output still contains the OSC-7 sequence")
	}
}

func TestOSC7ScannerSplitTerminator(t *testing.T) {
	var sc osc7Scanner
	cwd1, _, found1 := sc.Feed([]byte("\x1b]7;file://h/a\x1b"))
	cwd2, cleaned2, found2 := sc.Feed([]byte("\\next"))
	if found1 || cwd1 != "" {
		t.Fatal("must not report before terminator")
	}
	if !found2 || cwd2 != "/a" {
		t.Fatalf("cwd=%q found=%v", cwd2, found2)
	}
	if string(cleaned2) != "next" {
		t.Fatalf("cleaned = %q, want next", cleaned2)
	}
}

func TestOSC7UrlDecoding(t *testing.T) {
	var sc osc7Scanner
	cwd, _, found := sc.Feed([]byte("\x1b]7;file://h/space%20dir\x07"))
	if !found || cwd != "/space dir" {
		t.Fatalf("cwd=%q found=%v", cwd, found)
	}
}

func TestOSC7ScannerEmptyHostBEL(t *testing.T) {
	var sc osc7Scanner
	// BEL-terminated sequence with an empty host part (file:///...)
	cwd, cleaned, found := sc.Feed([]byte("pre\x1b]7;file:///home/x\x07post"))
	if !found || cwd != "/home/x" {
		t.Fatalf("cwd=%q found=%v", cwd, found)
	}
	if string(cleaned) != "prepost" {
		t.Fatalf("cleaned = %q, want prepost", cleaned)
	}
}

// Reproduced in the field (dev log): real prompts emit the ST-terminated OSC-7
// immediately followed by a BEL-terminated OSC-0 title sequence. The scanner
// must terminate the OSC-7 payload at the FIRST terminator (ST here), not at
// the later BEL — swallowing "\x1b\\" plus the whole title into the payload
// produced a garbage cwd and disabled path following entirely.
func TestOSC7ScannerSTTerminatedBeforeFollowingOSC0(t *testing.T) {
	var sc osc7Scanner
	input := "\x1b]7;file:///root\x1b\\\x1b]0;root@localhost:~\x07"
	cwd, cleaned, found := sc.Feed([]byte(input))
	if !found || cwd != "/root" {
		t.Fatalf("cwd=%q found=%v, want /root", cwd, found)
	}
	if !strings.Contains(string(cleaned), "\x1b]0;root@localhost:~\x07") {
		t.Fatalf("following OSC-0 title must pass through to the display: %q", cleaned)
	}
	if strings.Contains(string(cleaned), "\x1b]7;") {
		t.Fatal("cleaned output still contains the OSC-7 sequence")
	}
}

func TestBashBootstrapPreservesLoginStartupOrder(t *testing.T) {
	files, args, ok := buildShellBootstrap("/bin/bash")
	if !ok {
		t.Fatal("bash must be supported")
	}
	rc := files["rcfile"]
	startupFiles := []string{"/etc/profile", "$HOME/.bash_profile", "$HOME/.bash_login", "$HOME/.profile"}
	last := -1
	for _, name := range startupFiles {
		i := strings.Index(rc, name)
		if i <= last {
			t.Fatalf("bash login startup order is wrong for %s: %s", name, rc)
		}
		last = i
	}
	if strings.Contains(rc, "$HOME/.bashrc") {
		t.Fatalf("login bootstrap must let the selected profile decide whether to source .bashrc: %s", rc)
	}
	if !strings.Contains(rc, "elif [ -r \"$HOME/.bash_login\" ]") ||
		!strings.Contains(rc, "elif [ -r \"$HOME/.profile\" ]") {
		t.Fatalf("bootstrap must source only the first readable user login file: %s", rc)
	}
	// chain, never overwrite: ours prepends, user's command survives
	if !strings.Contains(rc, "__terminal_osc7") || !strings.Contains(rc, "${PROMPT_COMMAND:+") {
		t.Fatalf("PROMPT_COMMAND must be chained: %s", rc)
	}
	// bash 5.1+ array form handled
	if !strings.Contains(rc, "declare -a") {
		t.Fatal("must special-case array PROMPT_COMMAND")
	}
	if len(args) < 2 || args[0] != "--rcfile" {
		t.Fatalf("startArgs = %v", args)
	}
}

func TestBashIntegrationCommandRunsLogoutFile(t *testing.T) {
	cmd := bashIntegrationCommand("/tmp/terminal-Ab12Z9")
	if !strings.HasPrefix(cmd, "bash --rcfile /tmp/terminal-Ab12Z9;") {
		t.Fatalf("unexpected bash command: %s", cmd)
	}
	if !strings.Contains(cmd, "$HOME/.bash_logout") {
		t.Fatalf("bash command must preserve login-shell logout behavior: %s", cmd)
	}
	if strings.HasPrefix(cmd, "exec ") {
		t.Fatalf("bash command must retain an outer shell to run .bash_logout: %s", cmd)
	}
}

func TestBashBootstrapPreservesExistingPromptCommand(t *testing.T) {
	files, _, ok := buildShellBootstrap("/bin/bash")
	if !ok {
		t.Fatal("bash must be supported")
	}
	rc := files["rcfile"]
	// The chained assignment keeps any PROMPT_COMMAND the user's rc set.
	if !strings.Contains(rc, "${PROMPT_COMMAND:+;$PROMPT_COMMAND}") {
		t.Fatalf("pre-existing PROMPT_COMMAND must be preserved: %s", rc)
	}
}

func TestGeneratedBashBootstrapsHaveValidSyntax(t *testing.T) {
	bash, err := exec.LookPath("bash")
	if err != nil {
		t.Skip("bash is not available for generated-script syntax checks")
	}
	sshFiles, _, ok := buildShellBootstrap("/bin/bash")
	if !ok {
		t.Fatal("SSH bash must be supported")
	}
	wslFiles, ok := buildWSLShellBootstrap("/bin/bash")
	if !ok {
		t.Fatal("WSL bash must be supported")
	}
	runtimeHook, ok := buildRuntimeCwdHook("/bin/bash")
	if !ok {
		t.Fatal("runtime bash hook must be supported")
	}
	for name, script := range map[string]string{
		"ssh":     sshFiles["rcfile"],
		"wsl":     wslFiles["rcfile"],
		"runtime": runtimeHook,
	} {
		cmd := exec.Command(bash, "-n")
		cmd.Stdin = strings.NewReader(script)
		if out, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("%s bash bootstrap has invalid syntax: %v: %s\n%s", name, err, out, script)
		}
	}
}

func TestZshBootstrapZDOTDIR(t *testing.T) {
	files, args, ok := buildShellBootstrap("/usr/bin/zsh")
	if !ok {
		t.Fatal("zsh must be supported")
	}
	for _, name := range []string{".zshrc", ".zshenv", ".zprofile", ".zlogin", ".zlogout"} {
		if files[name] == "" {
			t.Fatalf("zsh bootstrap is missing %s: %v", name, files)
		}
	}
	if !strings.Contains(files[".zprofile"], "$HOME/.zprofile") {
		t.Fatalf("redirected .zprofile must chain the user's ~/.zprofile: %s", files[".zprofile"])
	}
	if !strings.Contains(files[".zlogin"], "$HOME/.zlogin") {
		t.Fatalf("redirected .zlogin must chain the user's ~/.zlogin: %s", files[".zlogin"])
	}
	if !strings.Contains(files[".zlogout"], "$HOME/.zlogout") {
		t.Fatalf("redirected .zlogout must chain the user's ~/.zlogout: %s", files[".zlogout"])
	}
	if !strings.Contains(files[".zshrc"], "precmd_functions+=(__terminal_osc7)") {
		t.Fatal("zsh must append to precmd_functions, not replace")
	}
	// the redirected .zshenv must chain the user's own ~/.zshenv
	if !strings.Contains(files[".zshenv"], "$HOME/.zshenv") {
		t.Fatalf("redirected .zshenv must chain the user's ~/.zshenv: %s", files[".zshenv"])
	}
	found := false
	for _, a := range args {
		if strings.HasPrefix(a, "ZDOTDIR=") {
			found = true
		}
	}
	if !found {
		t.Fatalf("startArgs must set ZDOTDIR: %v", args)
	}
}

func TestFishBootstrapUsesLoginShell(t *testing.T) {
	_, args, ok := buildShellBootstrap("/usr/bin/fish")
	if !ok {
		t.Fatal("fish must be supported")
	}
	if len(args) < 3 || args[0] != "-l" || args[1] != "-C" {
		t.Fatalf("fish startArgs = %v, want login shell with -C bootstrap", args)
	}
}

func TestWSLBootstrapKeepsIndependentStartupBehavior(t *testing.T) {
	files, ok := buildWSLShellBootstrap("/bin/bash")
	if !ok {
		t.Fatal("WSL bash must be supported")
	}
	rc := files["rcfile"]
	if !strings.Contains(rc, "$HOME/.bashrc") || !strings.Contains(rc, "$HOME/.bash_profile") {
		t.Fatalf("WSL bootstrap must preserve its existing rc files: %s", rc)
	}
	if strings.Contains(rc, "/etc/profile") || strings.Contains(rc, "$HOME/.bash_login") {
		t.Fatalf("SSH login emulation must not leak into WSL bootstrap: %s", rc)
	}
}

func TestSSHRunCommandTimesOutWhileOpeningSession(t *testing.T) {
	signer, err := ssh.ParsePrivateKey([]byte(testHostKeyPEM))
	if err != nil {
		t.Fatalf("parse test host key: %v", err)
	}
	serverConfig := &ssh.ServerConfig{NoClientAuth: true}
	serverConfig.AddHostKey(signer)

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	defer listener.Close()
	releaseServer := make(chan struct{})
	serverDone := make(chan struct{})
	go func() {
		defer close(serverDone)
		serverConn, err := listener.Accept()
		if err != nil {
			return
		}
		defer serverConn.Close()
		_, channels, requests, err := ssh.NewServerConn(serverConn, serverConfig)
		if err != nil {
			return
		}
		go ssh.DiscardRequests(requests)
		_, ok := <-channels
		if !ok {
			return
		}
		<-releaseServer
		// Closing the transport unblocks the pending channel-open without
		// depending on a channel rejection completing first.
		_ = serverConn.Close()
	}()

	clientConn, err := net.Dial("tcp", listener.Addr().String())
	if err != nil {
		t.Fatalf("dial test server: %v", err)
	}
	conn, channels, requests, err := ssh.NewClientConn(clientConn, "pipe", &ssh.ClientConfig{
		User:            "test",
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
	})
	if err != nil {
		t.Fatalf("create SSH client: %v", err)
	}
	client := ssh.NewClient(conn, channels, requests)

	const timeout = 50 * time.Millisecond
	started := time.Now()
	_, err = sshRunCommand(client, "true", "", timeout)
	if err == nil || !strings.Contains(err.Error(), "timed out opening SSH session") {
		t.Fatalf("sshRunCommand error = %v, want channel-open timeout", err)
	}
	if elapsed := time.Since(started); elapsed > time.Second {
		t.Fatalf("channel-open timeout took %s, want a bounded return", elapsed)
	}

	close(releaseServer)
	select {
	case <-serverDone:
	case <-time.After(time.Second):
		t.Fatal("test SSH server did not stop")
	}
	_ = client.Close()
}

func TestShellIntegrationUnsupportedShell(t *testing.T) {
	for _, shell := range []string{"/bin/sh", "/bin/tcsh", "/usr/bin/ksh", ""} {
		if _, _, ok := buildShellBootstrap(shell); ok {
			t.Fatalf("shell %q must degrade to a plain shell", shell)
		}
	}
}

func TestRuntimeCwdHook(t *testing.T) {
	tests := []struct {
		name      string
		shell     string
		wantOK    bool
		mustHave  []string
	}{
		{
			name:     "bash",
			shell:    "/bin/bash",
			wantOK:   true,
			mustHave: []string{"declare -a", "== *__terminal_osc7*", "${PROMPT_COMMAND:+"},
		},
		{
			name:     "zsh",
			shell:    "/usr/bin/zsh",
			wantOK:   true,
			mustHave: []string{"(I)__terminal_osc7", "precmd_functions"},
		},
		{
			name:     "fish",
			shell:    "/usr/bin/fish",
			wantOK:   true,
			mustHave: []string{"if not functions -q __terminal_osc7"},
		},
		{
			name:   "unsupported ksh",
			shell:  "/usr/bin/ksh",
			wantOK: false,
		},
		{
			name:   "empty",
			shell:  "",
			wantOK: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, ok := buildRuntimeCwdHook(tt.shell)
			if ok != tt.wantOK {
				t.Fatalf("buildRuntimeCwdHook(%q) ok = %v, want %v", tt.shell, ok, tt.wantOK)
			}
			if !ok {
				return
			}
			if !strings.HasPrefix(got, " ") || !strings.HasSuffix(got, "\n") {
				t.Fatalf("snippet must start with a space and end with a newline: %q", got)
			}
			if !strings.Contains(got, "__terminal_osc7") {
				t.Fatalf("snippet must define the __terminal_osc7 hook: %q", got)
			}
			for _, want := range tt.mustHave {
				if !strings.Contains(got, want) {
					t.Fatalf("snippet for %s must contain %q: %q", tt.shell, want, got)
				}
			}
		})
	}
}

// The installed-flag short-circuit runs before any network access, so it can
// be exercised on a bare session: a flagged session returns nil even when
// disconnected, and an un-flagged disconnected session still reports the
// connection error (so a later toggle retries).
func TestSSHSessionInjectCwdHookFlagShortCircuit(t *testing.T) {
	s := NewSSHSession("test-cwd-hook")
	if injected, err := s.InjectCwdHook(); err == nil || injected {
		t.Fatalf("un-flagged disconnected session must report an error, got injected=%v err=%v", injected, err)
	}
	s.cwdHookInstalled.Store(true)
	injected, err := s.InjectCwdHook()
	if err != nil {
		t.Fatalf("flagged session must short-circuit to nil, got %v", err)
	}
	if injected {
		t.Fatal("flagged session short-circuit must report injected=false")
	}
}

// CwdHookInstalled exposes the installed flag so the frontend can skip its
// confirmation dialog when the runtime hook is already present.
func TestSSHSessionCwdHookInstalledFlag(t *testing.T) {
	s := NewSSHSession("test-cwd-hook-flag")
	if s.CwdHookInstalled() {
		t.Fatal("fresh session must report cwd hook not installed")
	}
	s.cwdHookInstalled.Store(true)
	if !s.CwdHookInstalled() {
		t.Fatal("flagged session must report cwd hook installed")
	}
}

func TestSSHIntegrationTempPathValidation(t *testing.T) {
	valid := []string{
		"/tmp/terminal-Ab12Z9",
		"/tmp/terminal-000000",
	}
	for _, path := range valid {
		if !isSSHIntegrationTempPath(path) {
			t.Errorf("isSSHIntegrationTempPath(%q) = false, want true", path)
		}
	}

	invalid := []string{
		"",
		"/tmp/terminal-",
		"/tmp/terminal-short",
		"/tmp/terminal-Ab12Z9/child",
		"/tmp/terminal-Ab12Z_",
		"/var/tmp/terminal-Ab12Z9",
	}
	for _, path := range invalid {
		if isSSHIntegrationTempPath(path) {
			t.Errorf("isSSHIntegrationTempPath(%q) = true, want false", path)
		}
	}
}

func TestCleanRemoteTempPath(t *testing.T) {
	tests := []struct {
		name    string
		out     string
		want    string
		wantErr bool
	}{
		{name: "plain", out: "/tmp/terminal-Ab12Z9\n", want: "/tmp/terminal-Ab12Z9"},
		{name: "crlf", out: "/tmp/terminal-Ab12Z9\r\n", want: "/tmp/terminal-Ab12Z9"},
		{name: "surrounded by banner", out: "Welcome\n/tmp/terminal-Ab12Z9\nLast login\n", want: "/tmp/terminal-Ab12Z9"},
		{name: "embedded path rejected", out: "created /tmp/terminal-Ab12Z9\n", wantErr: true},
		{name: "whitespace rejected", out: " /tmp/terminal-Ab12Z9 \n", wantErr: true},
		{name: "multiple paths rejected", out: "/tmp/terminal-Ab12Z9\n/tmp/terminal-Cd34Y8\n", wantErr: true},
		{name: "invalid suffix rejected", out: "/tmp/terminal-Ab12Z_\n", wantErr: true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := cleanRemoteTempPath(tt.out)
			if (err != nil) != tt.wantErr {
				t.Fatalf("cleanRemoteTempPath(%q) error = %v, wantErr %v", tt.out, err, tt.wantErr)
			}
			if got != tt.want {
				t.Fatalf("cleanRemoteTempPath(%q) = %q, want %q", tt.out, got, tt.want)
			}
		})
	}
}
