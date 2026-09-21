package session

import (
	"bufio"
	"bytes"
	"errors"
	"fmt"
	"io"
	"net"
	"os"
	"path"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"golang.org/x/crypto/ssh"
)

// SCPSession implements the fileTransferSession contract over the legacy SCP
// protocol (OpenSSH scp.c) for hosts that do not provide an SFTP subsystem —
// embedded devices, network gear, hardened servers, etc.
//
// File transfers speak the SCP sink/source directive protocol over exec
// channels (exec "scp -t"/"scp -f"); browsing and metadata operations run
// through one-shot shell commands (ls/mv/rm/chmod/cp), parsed on the client
// side. No subsystem and no sftp-server binary are required, only the remote
// scp binary, which ships with essentially every OpenSSH/dropbear install.
type SCPSession struct {
	baseSession
	localFSOps
	sshClient *ssh.Client
	cwd       string
	mu        sync.RWMutex
	transfers map[string]*TransferTask
	taskSeq   int64
	sem       chan struct{} // concurrency limiter, nil = unlimited
}

func NewSCPSession(id string) *SCPSession {
	return &SCPSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "scp",
			status:      StatusDisconnected,
		},
		localFSOps: newLocalFSOps(),
		cwd:        "/",
		transfers:  make(map[string]*TransferTask),
	}
}

// SetMaxConcurrency limits concurrent file transfers. n <= 0 means unlimited.
func (s *SCPSession) SetMaxConcurrency(n int) {
	if n > 0 {
		s.sem = make(chan struct{}, n)
	}
}

func (s *SCPSession) Connect(config ConnectionConfig) error {
	s.setStatus(StatusConnecting)
	s.title = fmt.Sprintf("%s@%s", config.User, config.Host)

	authMethods, cleanup, err := buildAuthMethodsWithCleanup(config)
	if err != nil {
		s.setStatus(StatusError)
		return err
	}
	defer cleanup()

	clientConfig := &ssh.ClientConfig{
		User:            config.User,
		Auth:            authMethods,
		Timeout:         30 * time.Second,
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
		Config:          sshAlgorithms(),
	}

	addr := net.JoinHostPort(config.Host, strconv.Itoa(config.Port))
	client, err := dialSSHTCP(addr, clientConfig, config.Proxy)
	if err != nil {
		s.setStatus(StatusError)
		return fmt.Errorf("ssh dial: %w", err)
	}

	go func() {
		_ = client.Wait()
		s.Disconnect()
	}()

	s.mu.Lock()
	s.sshClient = client
	s.mu.Unlock()
	go startFileSessionKeepAlive(client, s.Status)

	// Resolve the login home directory as the initial remote cwd. Login
	// banners may print before it, so take the last non-empty line.
	if out, err := s.runCommand("pwd", 15*time.Second); err == nil {
		if wd := lastNonEmptyLine(out); wd != "" {
			s.mu.Lock()
			s.cwd = wd
			s.mu.Unlock()
		}
	}
	s.setStatus(StatusConnected)
	return nil
}

func (s *SCPSession) Write(data []byte) error { return nil }

func (s *SCPSession) Resize(cols, rows int) error { return nil }

func (s *SCPSession) Disconnect() error {
	s.mu.Lock()
	if s.sshClient != nil {
		s.sshClient.Close()
		s.sshClient = nil
	}
	s.mu.Unlock()
	s.setStatus(StatusDisconnected)
	return nil
}

func (s *SCPSession) IsConnected() bool {
	return s.Status() == StatusConnected && s.getClient() != nil
}

// --- Connection helpers ---

func (s *SCPSession) getClient() *ssh.Client {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.sshClient
}

func (s *SCPSession) requireConnected() error {
	if s.getClient() == nil {
		return fmt.Errorf("SCP session not connected")
	}
	return nil
}

func (s *SCPSession) getCwd() string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.cwd
}

func (s *SCPSession) setCwd(dir string) {
	s.mu.Lock()
	s.cwd = dir
	s.mu.Unlock()
}

func lastNonEmptyLine(out string) string {
	lines := strings.Split(out, "\n")
	for i := len(lines) - 1; i >= 0; i-- {
		if l := strings.TrimSpace(lines[i]); l != "" {
			return l
		}
	}
	return ""
}

// execOutcome is passed through a buffered channel so a timed-out command's
// goroutine can complete without touching shared state (no leaks, no races).
type execOutcome struct {
	out string
	err error
}

// runCommand runs a one-shot remote shell command and returns its stdout
// (stderr is discarded — banners and MOTD noise must not pollute parsed
// output). If the command exceeds timeout the channel is killed and a
// timeout error returned.
func (s *SCPSession) runCommand(cmd string, timeout time.Duration) (string, error) {
	client := s.getClient()
	if client == nil {
		return "", fmt.Errorf("SCP session not connected")
	}
	sess, err := client.NewSession()
	if err != nil {
		return "", err
	}
	ch := make(chan execOutcome, 1)
	go func() {
		out, runErr := sess.Output(cmd)
		ch <- execOutcome{out: string(out), err: runErr}
	}()
	select {
	case oc := <-ch:
		return oc.out, oc.err
	case <-time.After(timeout):
		sess.Close()
		return "", fmt.Errorf("command timeout: %s", cmd)
	}
}

// --- Remote listing (shell `ls -la` parse) ---

// lsEntry is one parsed `ls -la` line.
type lsEntry struct {
	Name    string
	Mode    string // 10-char permission string, e.g. "-rw-r--r--"
	Size    int64
	ModTime time.Time
	Owner   string
	Group   string
}

// parseLsLongListing parses the output of `ls -la` into entries, skipping the
// "total" line and any banner noise a login script may print before it.
// Handles GNU/BSD ("Jan  2 15:04" / "Jan  2  2019") and ISO/toybox
// ("2020-01-01 10:00") time formats, names containing spaces, and symlinks
// ("name -> target").
func parseLsLongListing(output string) []lsEntry {
	var entries []lsEntry
	for _, line := range strings.Split(output, "\n") {
		line = strings.TrimRight(line, "\r")
		if line == "" || strings.HasPrefix(line, "total ") {
			continue
		}
		if e, ok := parseLsLine(line); ok {
			entries = append(entries, e)
		}
	}
	return entries
}

// parseLsLine parses a single `ls -la` line. Layout:
//
//	mode nlink owner group size DATE name...
//
// where DATE is either three tokens (month day time-or-year) or two tokens
// (ISO date time). Everything after DATE is the (possibly space-containing)
// name, with an optional " -> target" suffix for symlinks.
func parseLsLine(line string) (lsEntry, bool) {
	var e lsEntry
	rest := strings.TrimSpace(line)

	// Mode: single token, 10-11 chars (trailing '+' possible for ACLs).
	i := strings.IndexAny(rest, " \t")
	if i < 0 {
		return e, false
	}
	mode := rest[:i]
	if len(mode) < 10 || len(mode) > 11 {
		return e, false
	}
	rest = strings.TrimSpace(rest[i+1:])

	// nlink, owner, group, size — fixed 4 numeric/name tokens.
	fields := make([]string, 0, 4)
	for k := 0; k < 4; k++ {
		j := strings.IndexAny(rest, " \t")
		if j < 0 {
			return e, false
		}
		fields = append(fields, rest[:j])
		rest = strings.TrimSpace(rest[j+1:])
	}
	if _, err := strconv.Atoi(fields[0]); err != nil {
		return e, false // not a link count — banner noise
	}
	size, err := strconv.ParseInt(fields[3], 10, 64)
	if err != nil {
		return e, false
	}
	e.Mode = mode
	e.Owner = fields[1]
	e.Group = fields[2]
	e.Size = size

	// Date: two or three tokens depending on format.
	toks := strings.Fields(rest)
	var nameStart int
	switch {
	case len(toks) >= 2 && isISODate(toks[0]):
		nameStart = 2
	case len(toks) >= 4 && isLsMonth(toks[0]):
		nameStart = 3
	default:
		return e, false
	}
	e.ModTime = parseLsDate(toks[:nameStart])

	// Positionally skip the date tokens; what remains is the name, which may
	// itself contain spaces.
	name := trimLeftSpaceRunes(rest)
	for k := 0; k < nameStart; k++ {
		j := strings.IndexAny(name, " \t")
		if j < 0 {
			return e, false
		}
		name = trimLeftSpaceRunes(name[j+1:])
	}
	// Strip symlink target.
	if idx := strings.Index(name, " -> "); idx >= 0 {
		name = name[:idx]
	}
	name = strings.TrimSuffix(strings.TrimSuffix(name, "\r"), "\n")
	if name == "" || name == "." || name == ".." {
		return e, false
	}
	e.Name = name
	return e, true
}

func trimLeftSpaceRunes(s string) string {
	return strings.TrimLeft(s, " \t")
}

func isISODate(tok string) bool {
	if len(tok) != 10 || tok[4] != '-' || tok[7] != '-' {
		return false
	}
	for i, c := range tok {
		if i == 4 || i == 7 {
			continue
		}
		if c < '0' || c > '9' {
			return false
		}
	}
	return true
}

func isLsMonth(tok string) bool {
	switch tok {
	case "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec":
		return true
	}
	return false
}

// parseLsDate builds a time from the date tokens consumed by parseLsLine.
// "Jan  2 15:04" uses the current year (ls convention: shifted back one year
// when that lands more than six months in the future); "Jan  2  2019" and
// ISO dates carry their own year.
func parseLsDate(toks []string) time.Time {
	now := time.Now()
	if len(toks) == 2 {
		// ISO "YYYY-MM-DD HH:MM"
		if t, err := time.ParseInLocation("2006-01-02 15:04", toks[0]+" "+toks[1], time.Local); err == nil {
			return t
		}
		return time.Time{}
	}
	if len(toks) != 3 {
		return time.Time{}
	}
	day, _ := strconv.Atoi(toks[1])
	month := monthIndex(toks[0])
	// Third token: clock time (recent entries) or year (older ones).
	if t, err := time.ParseInLocation("15:04", toks[2], time.Local); err == nil {
		cand := time.Date(now.Year(), time.Month(month), day, t.Hour(), t.Minute(), 0, 0, time.Local)
		if cand.After(now.Add(6 * 30 * 24 * time.Hour)) {
			cand = cand.AddDate(-1, 0, 0)
		}
		return cand
	}
	if year, err := strconv.Atoi(toks[2]); err == nil {
		return time.Date(year, time.Month(month), day, 0, 0, 0, 0, time.Local)
	}
	return time.Time{}
}

func monthIndex(m string) int {
	for i, name := range []string{"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"} {
		if name == m {
			return i + 1
		}
	}
	return 1
}

// resolveSymlinkDirs determines, for a batch of symlink paths, which ones
// point at directories — one shell round-trip instead of one per entry.
func (s *SCPSession) resolveSymlinkDirs(paths []string, timeout time.Duration) map[string]bool {
	out := make(map[string]bool)
	if len(paths) == 0 {
		return out
	}
	var b strings.Builder
	b.WriteString("n=0; for p in")
	for _, p := range paths {
		b.WriteString(" " + shellEscape(p))
	}
	b.WriteString("; do n=$((n+1)); if [ -d \"$p\" ]; then echo \"$n d\"; else echo \"$n f\"; fi; done")
	res, err := s.runCommand(b.String(), timeout)
	if err != nil {
		return out
	}
	for _, line := range strings.Split(res, "\n") {
		f := strings.Fields(line)
		if len(f) != 2 {
			continue
		}
		idx, err := strconv.Atoi(f[0])
		if err != nil || idx < 1 || idx > len(paths) {
			continue
		}
		if f[1] == "d" {
			out[paths[idx-1]] = true
		}
	}
	return out
}

func (s *SCPSession) ListRemote(dir string) (FileListResult, error) {
	if err := s.requireConnected(); err != nil {
		return FileListResult{}, err
	}
	if dir == "" {
		dir = s.getCwd()
	} else if !path.IsAbs(dir) {
		dir = path.Join(s.getCwd(), dir)
	}
	out, err := s.runCommand("ls -la "+shellEscape(dir), 25*time.Second)
	if err != nil {
		return FileListResult{}, err
	}
	parsed := parseLsLongListing(out)
	files := make([]FileItem, 0, len(parsed))

	// Resolve which symlinks point at directories (single round-trip) so
	// symlinked directories are navigable like in the SFTP backend.
	var symlinks []string
	for _, e := range parsed {
		if strings.HasPrefix(e.Mode, "l") {
			symlinks = append(symlinks, path.Join(dir, e.Name))
		}
	}
	symDirs := s.resolveSymlinkDirs(symlinks, 15*time.Second)

	for _, e := range parsed {
		isDir := strings.HasPrefix(e.Mode, "d")
		if strings.HasPrefix(e.Mode, "l") && symDirs[path.Join(dir, e.Name)] {
			isDir = true
		}
		files = append(files, FileItem{
			Name:     e.Name,
			Size:     e.Size,
			ModTime:  e.ModTime.Format(time.RFC3339),
			Mode:     e.Mode,
			IsDir:    isDir,
			IsHidden: strings.HasPrefix(e.Name, "."),
			Owner:    e.Owner,
			Group:    e.Group,
		})
	}
	return FileListResult{Files: files, Dir: dir}, nil
}

// scpChangeDirCommand builds the shell command entering dir and printing its
// physical path: pwd -P resolves directory symlinks to their real target, so
// entering a link lands on the target itself — matching SFTP's RealPath and
// the WSL backend's readlink fallback (a plain pwd would keep the link path).
func scpChangeDirCommand(target string) string {
	return "cd " + shellEscape(target) + " 2>/dev/null && pwd -P"
}

func (s *SCPSession) ChangeRemoteDir(dir string) (FileListResult, error) {
	if err := s.requireConnected(); err != nil {
		return FileListResult{}, err
	}
	target := dir
	if !path.IsAbs(dir) {
		target = path.Join(s.getCwd(), dir)
	}
	out, err := s.runCommand(scpChangeDirCommand(target), 15*time.Second)
	if err != nil || lastNonEmptyLine(out) == "" {
		return FileListResult{}, fmt.Errorf("no such directory: %s", target)
	}
	real := lastNonEmptyLine(out)
	s.setCwd(real)
	return s.ListRemote(real)
}

// --- Remote metadata operations (shell) ---

func (s *SCPSession) MakeDir(dir string) error {
	if err := s.requireConnected(); err != nil {
		return err
	}
	p := dir
	if !path.IsAbs(p) {
		p = path.Join(s.getCwd(), p)
	}
	_, err := s.runCommand("mkdir "+shellEscape(p), 15*time.Second)
	return err
}

// scpSymlinkCommand builds the shell command creating a symbolic link.
func scpSymlinkCommand(target, linkPath string) string {
	return fmt.Sprintf("ln -s %s %s", shellEscape(target), shellEscape(linkPath))
}

// Symlink creates a symbolic link on the remote host via `ln -s`. The link
// path resolves against the session cwd; the target is stored verbatim (a
// relative target resolves against the link's own directory).
func (s *SCPSession) Symlink(target, linkPath string) error {
	if err := s.requireConnected(); err != nil {
		return err
	}
	p := linkPath
	if !path.IsAbs(p) {
		p = path.Join(s.getCwd(), p)
	}
	_, err := s.runCommand(scpSymlinkCommand(target, p), 15*time.Second)
	return err
}

func (s *SCPSession) mkdirAllRemote(dir string) error {
	if dir == "/" || dir == "." || dir == "" {
		return nil
	}
	_, err := s.runCommand("mkdir -p "+shellEscape(dir), 30*time.Second)
	return err
}

func (s *SCPSession) Remove(p string, recursive bool) error {
	if err := s.requireConnected(); err != nil {
		return err
	}
	if !path.IsAbs(p) {
		p = path.Join(s.getCwd(), p)
	}
	p = path.Clean(p)
	if p == "/" || p == "." || p == "" {
		return fmt.Errorf("refusing to delete path: %s", p)
	}
	_, err := s.runCommand("rm -rf -- "+shellEscape(p), 5*time.Minute)
	return err
}

func (s *SCPSession) Rename(oldName, newName string) error {
	if err := s.requireConnected(); err != nil {
		return err
	}
	old := oldName
	if !path.IsAbs(old) {
		old = path.Join(s.getCwd(), old)
	}
	newPath := newName
	if !path.IsAbs(newPath) {
		newPath = path.Join(s.getCwd(), newPath)
	}
	_, err := s.runCommand("mv -- "+shellEscape(old)+" "+shellEscape(newPath), 5*time.Minute)
	return err
}

func (s *SCPSession) Chmod(p string, mode os.FileMode) error {
	if err := s.requireConnected(); err != nil {
		return err
	}
	if !path.IsAbs(p) {
		p = path.Join(s.getCwd(), p)
	}
	_, err := s.runCommand(fmt.Sprintf("chmod %o %s", mode.Perm(), shellEscape(p)), 15*time.Second)
	return err
}

// Copy copies a remote file or directory via shell `cp -r` (server-side, no
// data transfer through the client).
func (s *SCPSession) Copy(oldPath, newPath string) error {
	if err := s.requireConnected(); err != nil {
		return err
	}
	old := oldPath
	if !path.IsAbs(old) {
		old = path.Join(s.getCwd(), old)
	}
	n := newPath
	if !path.IsAbs(n) {
		n = path.Join(s.getCwd(), n)
	}
	_, err := s.runCommand("cp -r -- "+shellEscape(old)+" "+shellEscape(n), 5*time.Minute)
	return err
}

// Move moves a remote file or directory via shell `mv` (handles renames and
// cross-filesystem moves).
func (s *SCPSession) Move(oldPath, newPath string) error {
	return s.Rename(oldPath, newPath)
}

// --- SCP protocol (transfer engine) -----------------------------------------
// Implemented per OpenSSH scp.c: the source (remote "scp -f") waits for one
// NUL, then emits "C<mode> <size> <name>\n" / "D<mode> 0 <name>\n" / "E\n"
// directives, each acked with a NUL; file data is followed by a NUL which the
// receiver acks. The sink (remote "scp -t") sends an initial NUL and acks
// every directive. Error lines are "\1<msg>\n" (continue) and "\2<msg>\n"
// (fatal).

type scpProtoConn struct {
	stdout *bufio.Reader
	stdin  io.Writer
	stderr io.Writer
	sess   *ssh.Session
}

// readProtoLine reads one newline-terminated directive line. Remote error
// lines ("\1<msg>\n" / "\2<msg>\n") are returned as scpProtoError.
type scpProtoError struct {
	msg   string
	fatal bool
}

func (e *scpProtoError) Error() string { return e.msg }

func (c *scpProtoConn) readLine() (string, error) {
	line, err := c.stdout.ReadString('\n')
	if err != nil {
		return "", fmt.Errorf("scp: lost connection: %w", err)
	}
	line = strings.TrimRight(line, "\n")
	if len(line) > 0 && (line[0] == '\x01' || line[0] == '\x02') {
		return "", &scpProtoError{msg: strings.TrimSpace(line[1:]), fatal: line[0] == '\x02'}
	}
	return line, nil
}

// ack sends a NUL and verifies the remote reply is a NUL (source direction:
// the remote scp -f reads acks via response(); it replies nothing on this
// channel, so this only writes).
func (c *scpProtoConn) ack() error {
	_, err := c.stdin.Write([]byte{0})
	return err
}

// waitAck reads the sink's reply to a directive: a single NUL, or an error
// line. Used on the upload direction.
func (c *scpProtoConn) waitAck() error {
	var b [1]byte
	if _, err := io.ReadFull(c.stdout, b[:]); err != nil {
		return fmt.Errorf("scp: lost connection: %w", err)
	}
	switch b[0] {
	case 0:
		return nil
	case '\x01', '\x02':
		line, err := c.stdout.ReadString('\n')
		if err != nil {
			return fmt.Errorf("scp: lost connection: %w", err)
		}
		return &scpProtoError{msg: strings.TrimSpace(line), fatal: b[0] == '\x02'}
	default:
		return fmt.Errorf("scp: protocol error: unexpected reply 0x%02x", b[0])
	}
}

// scpExec starts the remote scp process in the requested mode and returns a
// protocol connection. The session is the caller's to close.
func (s *SCPSession) scpExec(mode string, remotePath string) (*scpProtoConn, error) {
	client := s.getClient()
	if client == nil {
		return nil, fmt.Errorf("SCP session not connected")
	}
	sess, err := client.NewSession()
	if err != nil {
		return nil, err
	}
	stdin, err := sess.StdinPipe()
	if err != nil {
		sess.Close()
		return nil, err
	}
	stdout, err := sess.StdoutPipe()
	if err != nil {
		sess.Close()
		return nil, err
	}
	if err := sess.Start(fmt.Sprintf("scp -%s %s", mode, shellEscape(remotePath))); err != nil {
		sess.Close()
		return nil, err
	}
	return &scpProtoConn{stdout: bufio.NewReaderSize(stdout, 64*1024), stdin: stdin, sess: sess}, nil
}

// scpFetchFile downloads one remote file via the scp source protocol,
// streaming its bytes into w. task (nil for content reads) enables
// cancellation and pause; sizeCb receives the file size when the C directive
// arrives, progressCb each transferred chunk.
func (s *SCPSession) scpFetchFile(remotePath string, w io.Writer, task *TransferTask, sizeCb func(int64), progressCb func(int64)) error {
	c, err := s.scpExec("f", remotePath)
	if err != nil {
		return err
	}
	defer c.sess.Close()
	// scp -f waits for one NUL before sending directives (scp.c main:
	// `if (fflag) { (void) response(); source(...); }`).
	if err := c.ack(); err != nil {
		return err
	}
	for {
		line, err := c.readLine()
		if err != nil {
			return err
		}
		if line == "" {
			continue
		}
		switch line[0] {
		case 'T': // times (only sent with -p, ack and ignore for safety)
			if err := c.ack(); err != nil {
				return err
			}
			continue
		case 'C':
			if err := c.receiveFileBody(line, w, task, sizeCb, progressCb); err != nil {
				return err
			}
			if err := c.ack(); err != nil {
				return err
			}
			return nil
		case 'D':
			return fmt.Errorf("scp: %s is a directory (use recursive download)", remotePath)
		default:
			return fmt.Errorf("scp: protocol error: unexpected directive %q", line)
		}
	}
}

// receiveFileBody handles a C directive line: acks it, streams exactly size
// bytes into w (in pause/cancel-aware chunks when task is non-nil), and
// consumes the trailing NUL. Does NOT send the post-file ack — callers do
// that once they know the file is fully consumed.
func (c *scpProtoConn) receiveFileBody(line string, w io.Writer, task *TransferTask, sizeCb func(int64), progressCb func(int64)) error {
	// C<mode> <size> <name>
	fields := strings.SplitN(line[1:], " ", 3)
	if len(fields) != 3 {
		return fmt.Errorf("scp: protocol error: bad file directive %q", line)
	}
	size, err := strconv.ParseInt(fields[1], 10, 64)
	if err != nil {
		return fmt.Errorf("scp: protocol error: bad size in %q", line)
	}
	if size < 0 {
		return fmt.Errorf("scp: protocol error: negative size in %q", line)
	}
	if sizeCb != nil {
		sizeCb(size)
	}
	if err := c.ack(); err != nil {
		return err
	}
	buf := make([]byte, 64*1024)
	remaining := size
	for remaining > 0 {
		if task != nil {
			select {
			case <-task.ctx.Done():
				return task.ctx.Err()
			default:
			}
			task.waitIfPaused()
		}
		chunk := int64(len(buf))
		if remaining < chunk {
			chunk = remaining
		}
		n, rerr := io.ReadFull(c.stdout, buf[:chunk])
		if n > 0 {
			if _, werr := w.Write(buf[:n]); werr != nil {
				return werr
			}
			if progressCb != nil {
				progressCb(int64(n))
			}
			remaining -= int64(n)
		}
		if rerr != nil {
			return fmt.Errorf("scp: transfer failed: %w", rerr)
		}
	}
	var term [1]byte
	if _, err := io.ReadFull(c.stdout, term[:]); err != nil {
		return fmt.Errorf("scp: lost connection: %w", err)
	}
	return nil
}

// scpFetchTree downloads a remote directory tree via "scp -rf". The first D
// directive (the requested directory itself) maps onto localRoot; nested
// entries are placed beneath it, mirroring the SFTP backend's downloadDir
// semantics (contents copied INTO localRoot).
func (s *SCPSession) scpFetchTree(remoteDir, localRoot string, task *TransferTask) error {
	c, err := s.scpExec("rf", remoteDir)
	if err != nil {
		return err
	}
	defer c.sess.Close()
	if err := c.ack(); err != nil {
		return err
	}
	return s.fetchTree(c, remoteDir, localRoot, task)
}

// fetchTree drives the "scp -rf" directive walk on an already-open protocol
// connection. Split from scpFetchTree so tests can drive the walker with a
// fake connection. Per-file tracking: skipped files (retry checkpoint) have
// their body consumed and count as done; a file that fails is recorded in
// FailedFiles and the walk continues with the next sibling.
func (s *SCPSession) fetchTree(c *scpProtoConn, remoteDir, localRoot string, task *TransferTask) error {
	var stack []string  // current local directory path per open D directive
	var rstack []string // current remote directory path per open D directive
	cur := localRoot
	rcur := remoteDir
	first := true
	for {
		if err := task.ctx.Err(); err != nil {
			return err
		}
		task.waitIfPaused()
		line, err := c.readLine()
		if err != nil {
			return err
		}
		if line == "" {
			continue
		}
		switch line[0] {
		case 'T': // times (only sent with -p, ack and ignore for safety)
			if err := c.ack(); err != nil {
				return err
			}
		case 'D':
			name := scpDirectiveName(line)
			if name == "" {
				return fmt.Errorf("scp: protocol error: bad dir directive %q", line)
			}
			dir := path.Join(cur, name)
			rdir := path.Join(rcur, name)
			if first {
				// The requested directory itself: its content lands in localRoot.
				dir = localRoot
				rdir = remoteDir
				first = false
			}
			if err := os.MkdirAll(dir, 0o755); err != nil {
				return err
			}
			stack = append(stack, cur)
			rstack = append(rstack, rcur)
			cur, rcur = dir, rdir
			if err := c.ack(); err != nil {
				return err
			}
		case 'E':
			// OpenSSH "scp -f -r" sends exactly one E per D (including the root
			// D), so the E that closes the root directory terminates the
			// transfer. Returning on the empty stack right after popping keeps
			// that final E from falling through to a read that hits EOF.
			if len(stack) == 0 {
				return nil // already at root: nothing left to close
			}
			cur = stack[len(stack)-1]
			rcur = rstack[len(rstack)-1]
			stack = stack[:len(stack)-1]
			rstack = rstack[:len(rstack)-1]
			if len(stack) == 0 {
				return nil // tree complete
			}
			if err := c.ack(); err != nil {
				return err
			}
		case 'C':
			name := scpDirectiveName(line)
			local := path.Join(cur, name)
			rel := relPath(path.Join(rcur, name), task.RemotePath)
			if err := s.fetchTreeFile(c, line, local, rel, name, task); err != nil {
				return err
			}
		default:
			return fmt.Errorf("scp: protocol error: unexpected directive %q", line)
		}
	}
}

// fetchTreeFile transfers one C directive inside a tree download with per-file
// tracking. Skipped files (retry checkpoint) have their body consumed to keep
// the protocol stream in sync and count as done without re-transferring; a
// file whose local create fails is recorded in FailedFiles and the walk
// continues (the body is drained so siblings still transfer). A failure while
// reading the body desynchronizes the stream and aborts the walk.
func (s *SCPSession) fetchTreeFile(c *scpProtoConn, line, local, rel, name string, task *TransferTask) error {
	if task.shouldSkip(rel) {
		if err := c.receiveFileBody(line, io.Discard, task, nil, nil); err != nil {
			return err
		}
		if err := c.ack(); err != nil {
			return err
		}
		task.beginFile(rel)
		task.finishFile(rel)
		return nil
	}
	s.emitFileStart(task, rel, name)
	task.beginFile(rel)
	f, err := os.Create(local)
	if err != nil {
		task.failFile(rel, err)
		s.emitFileFailed(task, rel, err)
		// Drain this file's body so siblings can still transfer.
		if derr := c.receiveFileBody(line, io.Discard, task, nil, nil); derr != nil {
			return derr
		}
		if aerr := c.ack(); aerr != nil {
			return aerr
		}
		s.emitTransferProgress(task)
		return nil
	}
	rerr := c.receiveFileBody(line, f, task, nil, func(n int64) {
		task.addProgress(n)
		s.emitTransferProgress(task)
	})
	f.Close()
	if rerr != nil {
		if task.ctx.Err() != nil {
			task.clearCurrent(rel) // cancelled mid-file: not a file failure
			return rerr
		}
		task.failFile(rel, rerr)
		s.emitFileFailed(task, rel, rerr)
		return rerr // body partially consumed: the stream is out of sync
	}
	if err := c.ack(); err != nil {
		return err
	}
	task.finishFile(rel)
	s.emitFileDone(task, rel)
	s.emitTransferProgress(task)
	return nil
}

// scpDirectiveName extracts the trailing name from a C/D directive line.
func scpDirectiveName(line string) string {
	fields := strings.SplitN(line[1:], " ", 3)
	if len(fields) != 3 {
		return ""
	}
	return fields[2]
}

// scpStreamLostError marks a failure after which the scp protocol stream on
// the exec channel can no longer be resynchronized (lost connection, bad ack,
// partial file body). Tree walks must abort on it; sibling files cannot
// proceed.
type scpStreamLostError struct{ err error }

func (e *scpStreamLostError) Error() string { return e.err.Error() }
func (e *scpStreamLostError) Unwrap() error { return e.err }

// scpSendFile uploads one local file to remotePath (the full destination
// path) over "scp -t".
func (s *SCPSession) scpSendFile(localPath, remotePath string, task *TransferTask, progressCb func(int64)) error {
	c, err := s.scpExec("t", remotePath)
	if err != nil {
		return err
	}
	defer c.sess.Close()
	if err := c.waitAck(); err != nil {
		return err
	}
	return c.sendFileBody(localPath, filepath.Base(remotePath), task, progressCb)
}

// sendFileBody writes the C directive + data + NUL for one local file,
// waiting for the sink's acks.
func (c *scpProtoConn) sendFileBody(localPath, remoteName string, task *TransferTask, progressCb func(int64)) error {
	f, err := os.Open(localPath)
	if err != nil {
		return err
	}
	defer f.Close()
	fi, err := f.Stat()
	if err != nil {
		return err
	}
	return c.sendOpenedFile(f, fi.Size(), remoteName, task, progressCb)
}

// sendOpenedFile writes the C directive + data + NUL for an already-open
// local file, waiting for the sink's acks. Once the directive is written the
// protocol stream is committed to this file's bytes, so every later failure
// (lost connection, bad ack, local read error) is wrapped in
// scpStreamLostError — the walk cannot continue past a desynced stream.
func (c *scpProtoConn) sendOpenedFile(f *os.File, size int64, remoteName string, task *TransferTask, progressCb func(int64)) error {
	directive := fmt.Sprintf("C%04o %d %s\n", 0o644, size, sanitizeScpName(remoteName))
	if _, err := c.stdin.Write([]byte(directive)); err != nil {
		return &scpStreamLostError{err}
	}
	if err := c.waitAck(); err != nil {
		return &scpStreamLostError{err}
	}
	buf := make([]byte, 64*1024)
	for {
		select {
		case <-task.ctx.Done():
			return &scpStreamLostError{task.ctx.Err()}
		default:
		}
		task.waitIfPaused()
		n, rerr := f.Read(buf)
		if n > 0 {
			if _, werr := c.stdin.Write(buf[:n]); werr != nil {
				return &scpStreamLostError{werr}
			}
			if progressCb != nil {
				progressCb(int64(n))
			}
		}
		if rerr == io.EOF {
			break
		}
		if rerr != nil {
			return &scpStreamLostError{rerr}
		}
	}
	if _, err := c.stdin.Write([]byte{0}); err != nil {
		return &scpStreamLostError{err}
	}
	if err := c.waitAck(); err != nil {
		return &scpStreamLostError{err}
	}
	return nil
}

// scpSendTree uploads a local directory tree into remoteDir (which must
// exist; callers mkdir -p it first), using D/E directives for subdirectories
// like the local scp client does.
func (s *SCPSession) scpSendTree(localDir, remoteDir string, task *TransferTask) error {
	c, err := s.scpExec("rt", remoteDir)
	if err != nil {
		return err
	}
	defer c.sess.Close()
	if err := c.waitAck(); err != nil {
		return err
	}
	return s.sendTreeEntries(c, localDir, remoteDir, task)
}

// sendTreeEntries walks the local tree and streams each entry over the open
// protocol connection, with per-file tracking: skipped files (retry
// checkpoint) count as done without writing anything; a file that fails to
// open locally is recorded in FailedFiles and the walk continues (nothing was
// written to the stream); a protocol failure aborts the walk.
func (s *SCPSession) sendTreeEntries(c *scpProtoConn, localDir, remoteDir string, task *TransferTask) error {
	entries, err := os.ReadDir(localDir)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		if err := task.ctx.Err(); err != nil {
			return err
		}
		task.waitIfPaused()
		local := filepath.Join(localDir, entry.Name())
		remote := path.Join(remoteDir, entry.Name())
		rel := relPath(remote, task.RemotePath)
		if entry.IsDir() {
			directive := fmt.Sprintf("D%04o 0 %s\n", 0o755, sanitizeScpName(entry.Name()))
			if _, err := c.stdin.Write([]byte(directive)); err != nil {
				return fmt.Errorf("scp: lost connection: %w", err)
			}
			if err := c.waitAck(); err != nil {
				return err
			}
			if err := s.sendTreeEntries(c, local, remote, task); err != nil {
				return err
			}
			if _, err := c.stdin.Write([]byte("E\n")); err != nil {
				return fmt.Errorf("scp: lost connection: %w", err)
			}
			if err := c.waitAck(); err != nil {
				return err
			}
		} else {
			if err := s.sendTreeFile(c, local, rel, entry.Name(), task); err != nil {
				return err
			}
		}
	}
	return nil
}

// sendTreeFile uploads one file inside a tree upload with per-file tracking.
// Local-side failures (open/stat) keep the protocol stream in sync, so the
// walk continues with the next sibling after recording the failure.
func (s *SCPSession) sendTreeFile(c *scpProtoConn, localPath, rel, name string, task *TransferTask) error {
	if task.shouldSkip(rel) {
		task.beginFile(rel)
		task.finishFile(rel)
		return nil
	}
	s.emitFileStart(task, rel, name)
	task.beginFile(rel)
	err := c.sendFileBody(localPath, name, task, func(n int64) {
		task.addProgress(n)
		s.emitTransferProgress(task)
	})
	if err != nil {
		if task.ctx.Err() != nil {
			task.clearCurrent(rel) // cancelled mid-file: not a file failure
			return err
		}
		task.failFile(rel, err)
		s.emitFileFailed(task, rel, err)
		var lost *scpStreamLostError
		if errors.As(err, &lost) {
			return err // stream desynced: abort the walk
		}
		s.emitTransferProgress(task)
		return nil // local-side failure: continue with siblings
	}
	task.finishFile(rel)
	s.emitFileDone(task, rel)
	s.emitTransferProgress(task)
	return nil
}

// sanitizeScpName strips newline/CR characters from file names embedded in
// directive lines — a trailing newline would corrupt the protocol framing.
func sanitizeScpName(name string) string {
	return strings.NewReplacer("\n", "", "\r", "").Replace(name)
}

// --- Local size helpers ---

// dirStatsRemote returns the recursive byte total and file count of a remote
// directory tree (one `ls -la` round trip per directory).
func (s *SCPSession) dirStatsRemote(dir string) (int64, int, error) {
	out, err := s.runCommand("ls -la "+shellEscape(dir), 25*time.Second)
	if err != nil {
		return 0, 0, err
	}
	var total int64
	var files int
	for _, e := range parseLsLongListing(out) {
		if strings.HasPrefix(e.Mode, "d") {
			sz, n, err := s.dirStatsRemote(path.Join(dir, e.Name))
			if err != nil {
				return 0, 0, err
			}
			total += sz
			files += n
		} else {
			total += e.Size
			files++
		}
	}
	return total, files, nil
}

// dirStatsLocal returns the recursive byte total and file count of a local
// directory tree.
func (s *SCPSession) dirStatsLocal(dir string) (int64, int, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return 0, 0, err
	}
	var total int64
	var files int
	for _, e := range entries {
		if e.IsDir() {
			sz, n, err := s.dirStatsLocal(filepath.Join(dir, e.Name()))
			if err != nil {
				return 0, 0, err
			}
			total += sz
			files += n
		} else {
			fi, err := e.Info()
			if err != nil {
				return 0, 0, err
			}
			total += fi.Size()
			files++
		}
	}
	return total, files, nil
}

// --- Public transfer API (called from app.go Wails bindings) ---

func (s *SCPSession) Get(remotePath, localPath string, recursive bool) (string, error) {
	if err := s.requireConnected(); err != nil {
		return "", err
	}
	rp := remotePath
	if !path.IsAbs(rp) {
		rp = path.Join(s.getCwd(), rp)
	}
	lp := localPath
	if !filepath.IsAbs(lp) {
		lp = filepath.Join(s.localCwd, lp)
	}
	if recursive {
		return s.startSCPTree("download", lp, rp, nil)
	}
	task := &TransferTask{
		ID:         s.nextTaskID("dl"),
		Type:       "download",
		LocalPath:  lp,
		RemotePath: rp,
		Status:     "pending",
	}
	s.startTransfer(task)
	return task.ID, nil
}

func (s *SCPSession) Put(localPath, remotePath string, recursive bool) (string, error) {
	if err := s.requireConnected(); err != nil {
		return "", err
	}
	lp := localPath
	if !filepath.IsAbs(lp) {
		lp = filepath.Join(s.localCwd, lp)
	}
	rp := remotePath
	if !path.IsAbs(rp) {
		rp = path.Join(s.getCwd(), rp)
	}
	if recursive {
		return s.startSCPTree("upload", lp, rp, nil)
	}
	task := &TransferTask{
		ID:         s.nextTaskID("ul"),
		Type:       "upload",
		LocalPath:  lp,
		RemotePath: rp,
		Status:     "pending",
	}
	s.startTransfer(task)
	return task.ID, nil
}

// startSCPTree launches a recursive upload/download with per-file tracking
// and an optional retry skip-list, mirroring SFTP's startDirTransfer. The scp
// protocol streams a whole tree over one exec channel, so files transfer
// sequentially inside the walk (no worker pool). The returned task is
// retained in s.transfers on failure (retryable); it is removed when done or
// cancelled.
func (s *SCPSession) startSCPTree(tfType, lp, rp string, skip []string) (string, error) {
	var total int64
	var files int
	var err error
	if tfType == "download" {
		total, files, err = s.dirStatsRemote(rp)
	} else {
		total, files, err = s.dirStatsLocal(lp)
	}
	if err != nil {
		return "", err
	}
	if tfType == "upload" {
		if err := s.mkdirAllRemote(rp); err != nil {
			return "", err
		}
	}
	task := &TransferTask{
		ID:         s.nextTaskID(map[bool]string{true: "dl", false: "ul"}[tfType == "download"]),
		Type:       tfType,
		LocalPath:  lp,
		RemotePath: rp,
		Status:     "running",
	}
	task.setTotal(total)
	task.setFileCount(files)
	if len(skip) > 0 {
		task.SetSkip(skip)
	}
	task.start()
	s.mu.Lock()
	s.transfers[task.ID] = task
	s.mu.Unlock()
	s.emitTransferStart(task)
	go func() {
		defer task.done()
		var derr error
		if tfType == "download" {
			derr = s.scpFetchTree(rp, lp, task)
		} else {
			derr = s.scpSendTree(lp, rp, task)
		}
		task.fileMu.RLock()
		failed := task.FailedFiles
		task.fileMu.RUnlock()
		if task.ctx.Err() != nil {
			// Cancelled takes precedence over any per-file failures.
			task.Status = "cancelled"
			s.emitTransferComplete(task)
			s.mu.Lock()
			delete(s.transfers, task.ID)
			s.mu.Unlock()
			return
		}
		if derr != nil && len(failed) == 0 {
			// Walk-level failure (e.g. tree scan) with nothing attempted.
			task.Status = "error"
			s.emitTransferEvent(task, derr)
			return // kept in s.transfers for retry
		}
		if len(failed) > 0 {
			task.Status = "error"
			s.emitTransferComplete(task)
			return // kept for retry
		}
		task.Status = "done"
		s.emitTransferProgressForced(task)
		s.emitTransferComplete(task)
		s.mu.Lock()
		delete(s.transfers, task.ID)
		s.mu.Unlock()
	}()
	return task.ID, nil
}

func (s *SCPSession) startTransfer(task *TransferTask) {
	task.start()
	s.mu.Lock()
	s.transfers[task.ID] = task
	s.mu.Unlock()
	go func() {
		// The task is deleted from s.transfers only when done or cancelled;
		// on error it is retained so a later retry can resume it.
		removeTask := func() {
			s.mu.Lock()
			delete(s.transfers, task.ID)
			s.mu.Unlock()
		}
		defer task.done()
		task.Status = "running"
		s.emitTransferStart(task)

		if s.sem != nil {
			select {
			case s.sem <- struct{}{}:
				defer func() { <-s.sem }()
			case <-task.ctx.Done():
				task.Status = "cancelled"
				s.emitTransferComplete(task)
				removeTask()
				return
			}
		}

		var err error
		if task.Type == "download" {
			localFile, e := os.Create(task.LocalPath)
			if e != nil {
				s.emitTransferEvent(task, e)
				return
			}
			defer localFile.Close()
			err = s.scpFetchFile(task.RemotePath, localFile, task,
				func(size int64) { task.setTotal(size) },
				func(n int64) {
					task.addProgress(n)
					s.emitTransferProgress(task)
				})
		} else {
			fi, e := os.Stat(task.LocalPath)
			if e != nil {
				s.emitTransferEvent(task, e)
				return
			}
			task.setTotal(fi.Size())
			err = s.scpSendFile(task.LocalPath, task.RemotePath, task, func(n int64) {
				task.addProgress(n)
				s.emitTransferProgress(task)
			})
		}
		if err != nil {
			if task.ctx.Err() != nil {
				task.Status = "cancelled"
				s.emitTransferComplete(task)
				removeTask()
				return
			}
			s.emitTransferEvent(task, err)
			return // retained in s.transfers for retry
		}
		task.Status = "done"
		s.emitTransferComplete(task)
		removeTask()
	}()
}

// PutContent writes raw content directly to a remote file via the SCP sink
// protocol; the parent directory is created as needed (mirrors PutContent of
// the SFTP backend).
func (s *SCPSession) PutContent(remotePath string, content []byte) error {
	if err := s.requireConnected(); err != nil {
		return err
	}
	rp := remotePath
	if !path.IsAbs(rp) {
		rp = path.Join(s.getCwd(), rp)
	}
	if err := s.mkdirAllRemote(path.Dir(rp)); err != nil {
		return err
	}
	c, err := s.scpExec("t", rp)
	if err != nil {
		return err
	}
	defer c.sess.Close()
	if err := c.waitAck(); err != nil {
		return err
	}
	directive := fmt.Sprintf("C%04o %d %s\n", 0o644, len(content), sanitizeScpName(path.Base(rp)))
	if _, err := c.stdin.Write([]byte(directive)); err != nil {
		return fmt.Errorf("scp: lost connection: %w", err)
	}
	if err := c.waitAck(); err != nil {
		return err
	}
	if _, err := c.stdin.Write(content); err != nil {
		return fmt.Errorf("scp: lost connection: %w", err)
	}
	if _, err := c.stdin.Write([]byte{0}); err != nil {
		return fmt.Errorf("scp: lost connection: %w", err)
	}
	return c.waitAck()
}

// GetContent reads the full content of a remote file via the scp source
// protocol. Bounded by a timeout like the SFTP backend: the external-editor
// open path blocks the UI on this call.
func (s *SCPSession) GetContent(remotePath string) ([]byte, error) {
	type outcome struct {
		b   []byte
		err error
	}
	if err := s.requireConnected(); err != nil {
		return nil, err
	}
	rp := remotePath
	if !path.IsAbs(rp) {
		rp = path.Join(s.getCwd(), rp)
	}
	ch := make(chan outcome, 1)
	go func() {
		var buf bytes.Buffer
		err := s.scpFetchFile(rp, &buf, nil, nil, nil)
		ch <- outcome{b: buf.Bytes(), err: err}
	}()
	select {
	case out := <-ch:
		if out.err != nil {
			return nil, out.err
		}
		return out.b, nil
	case <-time.After(25 * time.Second):
		return nil, fmt.Errorf("read remote content timeout")
	}
}

// --- Transfer task bookkeeping (same contract as the other backends) ---

func (s *SCPSession) nextTaskID(prefix string) string {
	return fmt.Sprintf("%s-%d", prefix, atomic.AddInt64(&s.taskSeq, 1))
}

// RetryTransfer (re)starts a transfer from a frontend-held checkpoint. For
// recursive transfers, files listed in skipCompleted (paths relative to the
// transfer root, '/'-separated) are counted as done without re-transferring.
// Same contract as SFTPSession.RetryTransfer: *SCPSession satisfies the
// app-layer transferRetry capability interface.
func (s *SCPSession) RetryTransfer(spec TransferSpec, skipCompleted []string) (string, error) {
	if err := s.requireConnected(); err != nil {
		return "", err
	}
	if spec.Recursive {
		if spec.Type == "download" {
			return s.startSCPTree("download", spec.LocalPath, spec.RemotePath, skipCompleted)
		}
		return s.startSCPTree("upload", spec.LocalPath, spec.RemotePath, skipCompleted)
	}
	if spec.Type == "download" {
		return s.Get(spec.RemotePath, spec.LocalPath, false)
	}
	return s.Put(spec.LocalPath, spec.RemotePath, false)
}

// DismissTransfer drops a retained (failed) task from the transfers map.
func (s *SCPSession) DismissTransfer(taskID string) error {
	s.mu.Lock()
	delete(s.transfers, taskID)
	s.mu.Unlock()
	return nil
}

func (s *SCPSession) CancelTransfer(taskID string) error {
	s.mu.Lock()
	task, ok := s.transfers[taskID]
	s.mu.Unlock()
	if !ok {
		return fmt.Errorf("task not found: %s", taskID)
	}
	if task.cancel != nil {
		task.cancel()
	}
	return nil
}

func (s *SCPSession) PauseTransfer(taskID string) error {
	s.mu.Lock()
	task, ok := s.transfers[taskID]
	s.mu.Unlock()
	if !ok {
		return fmt.Errorf("task not found: %s", taskID)
	}
	task.setPaused(true)
	task.Status = "paused"
	s.emitTransferPaused(task)
	return nil
}

// ResumeTransfer resumes a paused transfer task. It is rejected unless the
// task is actually paused ("task not active"), so a stale or finished task
// cannot be resumed into a bogus running state.
func (s *SCPSession) ResumeTransfer(taskID string) error {
	s.mu.Lock()
	task, ok := s.transfers[taskID]
	s.mu.Unlock()
	if !ok {
		return fmt.Errorf("task not found: %s", taskID)
	}
	if task.Status != "paused" {
		return fmt.Errorf("task not active: %s", taskID)
	}
	task.setPaused(false)
	task.Status = "running"
	close(task.pauseCh)
	task.pauseCh = make(chan struct{})
	s.emitTransferResumed(task)
	return nil
}
