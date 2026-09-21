package session

import (
	"bufio"
	"context"
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

	"github.com/pkg/sftp"
	"easyaiot/terminal/backend/utils"
	"golang.org/x/crypto/ssh"
)

type SFTPSession struct {
	baseSession
	localFSOps // Windows-local pane, shared with FTP/SMB/WebDAV/S3/WSL
	sshClient  *ssh.Client
	sftpClient *sftp.Client
	cwd        string
	mu         sync.RWMutex
	transfers  map[string]*TransferTask
	taskSeq    int64
	sem        chan struct{} // concurrency limiter, nil = unlimited

	// UID/GID -> name cache read from the remote /etc/passwd and /etc/group
	// (issue #702). Loaded once on Connect; a missing/unreadable entry falls
	// back to the numeric id.
	userMapOnce sync.Once
	userMap     map[int]string
	groupMap    map[int]string
}

func NewSFTPSession(id string) *SFTPSession {
	return &SFTPSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "sftp",
			status:      StatusDisconnected,
		},
		localFSOps: newLocalFSOps(),
		cwd:        "/",
		transfers:  make(map[string]*TransferTask),
	}
}

// SetMaxConcurrency limits concurrent file transfers. n <= 0 means unlimited.
func (s *SFTPSession) SetMaxConcurrency(n int) {
	if n > 0 {
		s.sem = make(chan struct{}, n)
	}
}

// fileSessionKeepAliveInterval keeps NAT/firewall mappings alive and lets the
// server's ClientAliveInterval see traffic (SFTP/SCP dropped after short idle
// periods). Send-only, mirroring SSHSession.startKeepAlive.
const fileSessionKeepAliveInterval = 60 * time.Second

func startFileSessionKeepAlive(client *ssh.Client, sess func() SessionStatus) {
	ticker := time.NewTicker(fileSessionKeepAliveInterval)
	defer ticker.Stop()
	for range ticker.C {
		if client == nil || sess() != StatusConnected {
			return
		}
		_, _, _ = client.SendRequest("keepalive@openssh.com", false, nil)
	}
}

func (s *SFTPSession) Connect(config ConnectionConfig) error {
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

	sc, err := sftp.NewClient(client)
	if err != nil {
		// subsystem 启动失败：若是协议流被污染(登录脚本打印)，像 MobaXterm 那样
		// fallback 到 exec sftp-server 并跳过噪声；仍失败再抛可操作提示。
		sc2, ferr := trySFTPExecFallback(client, err)
		if ferr == nil {
			sc = sc2
		} else {
			client.Close()
			s.setStatus(StatusError)
			return fmt.Errorf("sftp client: %w", hintSFTPStartupError(err, ferr))
		}
	}

	go func() {
		_ = client.Wait()
		s.Disconnect()
	}()

	s.sshClient = client
	go startFileSessionKeepAlive(client, s.Status)
	s.sftpClient = sc
	// Preload remote user/group name maps so list owners show names, not numbers.
	s.loadUserGroupMaps()
	if wd, err := sc.Getwd(); err == nil {
		s.cwd = wd
	}
	s.setStatus(StatusConnected)

	return nil
}

// isSFTPStreamPolluted 判断错误是否为“SFTP 协议流被服务器输出污染”那一类。
func isSFTPStreamPolluted(err error) bool {
	if err == nil {
		return false
	}
	msg := err.Error()
	return strings.Contains(msg, "packet too long") ||
		strings.Contains(msg, "message too long") ||
		strings.Contains(msg, "version packet")
}

// sftpServerPaths 是各发行版 sftp-server 二进制的常见位置。
// 逗号分隔的 shell 表达式：找到第一个存在的就 exec 它。
var sftpServerPaths = []string{
	"/usr/libexec/sftp-server",     // RHEL/CentOS/Fedora、macOS
	"/usr/lib/openssh/sftp-server", // Debian/Ubuntu
	"/usr/lib/ssh/sftp-server",     // Arch、SUSE
	"/usr/libexec/openssh/sftp-server",
	"/usr/lib/sftp-server",
}

// sftpFallbackMarker 是插在噪声与 SFTP 协议流之间的唯一分隔标记。
// 登录脚本的打印发生在 marker 之前，客户端读到 marker 后丢弃前面全部垃圾，
// 再把干净的剩余流交给 SFTP 解析——这样无论 profile/bashrc/BASH_ENV/~/.ssh/rc
// 怎么打印都不影响。
const sftpFallbackMarker = "__TERMINAL_SFTP_BEGIN__"

// buildSFTPExecCommand 生成一条 shell 命令：先在 PATH 与常见路径里找到 sftp-server，
// 打印 marker，然后 exec 它接管 stdio。找不到则以非零码退出。
func buildSFTPExecCommand() string {
	// 候选：先查 PATH，再逐个常见绝对路径。
	candidates := append([]string{"$(command -v sftp-server 2>/dev/null)"}, sftpServerPaths...)
	var b strings.Builder
	b.WriteString("s=''; for p in ")
	b.WriteString(strings.Join(candidates, " "))
	b.WriteString("; do if [ -x \"$p\" ]; then s=\"$p\"; break; fi; done; ")
	b.WriteString("[ -n \"$s\" ] || exit 127; ")
	// marker 后紧跟换行，printf 到 stdout；随后 exec 覆盖当前进程，之后 stdout 全是 SFTP 协议。
	b.WriteString("printf '" + sftpFallbackMarker + "\\n'; exec \"$s\"")
	return b.String()
}

// trySFTPExecFallback 在 subsystem 方式失败(且属于协议流被污染)时，
// 改为 exec sftp-server，并跳过 stdout 上 marker 之前的全部噪声，
// 再用管道接管，绕过被登录脚本污染的协议流。
func trySFTPExecFallback(client *ssh.Client, subsystemErr error) (*sftp.Client, error) {
	if !isSFTPStreamPolluted(subsystemErr) {
		return nil, subsystemErr
	}
	sess, err := client.NewSession()
	if err != nil {
		return nil, fmt.Errorf("fallback new session: %w", err)
	}
	stdin, err := sess.StdinPipe()
	if err != nil {
		sess.Close()
		return nil, fmt.Errorf("fallback stdin: %w", err)
	}
	stdoutRaw, err := sess.StdoutPipe()
	if err != nil {
		sess.Close()
		return nil, fmt.Errorf("fallback stdout: %w", err)
	}
	if err := sess.Start(buildSFTPExecCommand()); err != nil {
		sess.Close()
		return nil, fmt.Errorf("fallback exec sftp-server: %w", err)
	}
	// 跳过 marker 之前的全部噪声，把游标停在 SFTP 协议第一个字节。
	clean := bufio.NewReader(stdoutRaw)
	if err := skipToMarker(clean, sftpFallbackMarker); err != nil {
		sess.Close()
		return nil, fmt.Errorf("fallback marker: %w", err)
	}
	sc, err := sftp.NewClientPipe(clean, stdin)
	if err != nil {
		sess.Close()
		return nil, fmt.Errorf("fallback sftp handshake: %w", err)
	}
	return sc, nil
}

// skipToMarker 从 r 逐行读，丢弃直到读到含 marker 的那一行为止（含该行）。
// 之后 r 的读游标停在 marker 行的换行符之后，即 SFTP 协议流起点。
func skipToMarker(r *bufio.Reader, marker string) error {
	for {
		line, err := r.ReadString('\n')
		if strings.Contains(line, marker) {
			return nil
		}
		if err != nil {
			return utils.UserErr("sftp_start_marker_missing")
		}
	}
}

// hintSFTPStartupError 把 sftp 子系统启动失败的底层错误翻成可操作的提示。
// 最常见的是 packet too long：SSH 通了、认证也过了，但服务器登录脚本
// (/etc/profile、~/.bashrc、~/.ssh/rc 等) 在非交互会话里往 stdout 打印了内容，
// 污染了 SFTP 协议流。subErr 是 subsystem 方式的原始错误，fbErr 是 exec fallback
// 的失败原因(便于诊断到底卡在哪一步)。
func hintSFTPStartupError(subErr, fbErr error) error {
	if isSFTPStreamPolluted(subErr) {
		// Full remediation guidance lives in the i18n template
		// (backendErrors.sftp_subsystem_polluted); only the raw subsystem /
		// fallback errors are passed through as template args.
		if fbErr == nil {
			return utils.UserErr("sftp_subsystem_polluted", subErr.Error(), "")
		}
		return utils.UserErr("sftp_subsystem_polluted", subErr.Error(), fbErr.Error())
	}
	if fbErr != nil {
		return fbErr
	}
	return subErr
}

func (s *SFTPSession) Write(data []byte) error {
	return nil
}

func (s *SFTPSession) Resize(cols, rows int) error {
	return nil
}

func (s *SFTPSession) Disconnect() error {
	if s.sftpClient != nil {
		s.sftpClient.Close()
	}
	if s.sshClient != nil {
		s.sshClient.Close()
	}
	s.setStatus(StatusDisconnected)
	return nil
}

func (s *SFTPSession) IsConnected() bool {
	return s.Status() == StatusConnected
}

// FileItem represents a file entry returned to the frontend.
type FileItem struct {
	Name     string `json:"name"`
	Size     int64  `json:"size"`
	ModTime  string `json:"modTime"`
	Mode     string `json:"mode"`
	IsDir    bool   `json:"isDir"`
	IsHidden bool   `json:"isHidden"`
	Owner    string `json:"owner"`
	Group    string `json:"group"`
}

// FileListResult wraps files + current directory for a list response.
type FileListResult struct {
	Files []FileItem `json:"files"`
	Dir   string     `json:"dir"`
}

// TransferTask tracks an ongoing file transfer. Directory transfers carry
// per-file state (FileCount / CompletedFiles / FailedFiles / fileState) so the
// UI can show per-file progress and a retry can skip completed files.
type TransferTask struct {
	ID         string
	Type       string // "upload" | "download"
	LocalPath  string
	RemotePath string
	Progress   atomic.Int64
	Total      int64  // write via setTotal, read via loadTotal (guarded by fileMu)
	Status     string // "pending" | "running" | "paused" | "done" | "error" | "cancelled"

	CurrentFile    string        // first in-flight file (display)
	FileCount      int           // total files in a directory transfer (0 = single file)
	CompletedFiles int
	FailedFiles    []FileFailure

	// skip lists relative paths already transferred in a previous attempt
	// (retry checkpoint). nil = transfer everything.
	skip   map[string]bool
	fileMu sync.RWMutex

	ctx     context.Context
	cancel  context.CancelFunc
	// paused is read by transfer worker goroutines (waitIfPaused) and written
	// by the frontend-driven Pause/Resume entry points on other goroutines, so
	// it is an atomic rather than a plain bool (was a data race).
	paused  atomic.Bool
	pauseCh chan struct{}
}

func (t *TransferTask) addProgress(n int64) { t.Progress.Add(n) }
func (t *TransferTask) loadProgress() int64 { return t.Progress.Load() }
func (t *TransferTask) setProgress(v int64) { t.Progress.Store(v) }
func (t *TransferTask) setTotal(v int64)    { t.fileMu.Lock(); t.Total = v; t.fileMu.Unlock() }
func (t *TransferTask) loadTotal() int64    { t.fileMu.RLock(); defer t.fileMu.RUnlock(); return t.Total }
func (t *TransferTask) setFileCount(n int)  { t.fileMu.Lock(); t.FileCount = n; t.fileMu.Unlock() }
func (t *TransferTask) fileCount() int      { t.fileMu.RLock(); defer t.fileMu.RUnlock(); return t.FileCount }
func (t *TransferTask) completedCount() int { t.fileMu.Lock(); defer t.fileMu.Unlock(); return t.CompletedFiles }

func (t *TransferTask) SetSkip(rels []string) {
	t.fileMu.Lock()
	t.skip = make(map[string]bool, len(rels))
	for _, r := range rels {
		t.skip[r] = true
	}
	t.fileMu.Unlock()
}

func (t *TransferTask) shouldSkip(rel string) bool {
	t.fileMu.Lock()
	defer t.fileMu.Unlock()
	return t.skip != nil && t.skip[rel]
}

func (t *TransferTask) beginFile(rel string) {
	t.fileMu.Lock()
	t.CurrentFile = rel
	t.fileMu.Unlock()
}

func (t *TransferTask) finishFile(rel string) {
	t.fileMu.Lock()
	t.CompletedFiles++
	if t.CurrentFile == rel {
		t.CurrentFile = ""
	}
	t.fileMu.Unlock()
}

func (t *TransferTask) failFile(rel string, err error) {
	t.fileMu.Lock()
	t.FailedFiles = append(t.FailedFiles, FileFailure{Path: rel, Error: err.Error()})
	if t.CurrentFile == rel {
		t.CurrentFile = ""
	}
	t.fileMu.Unlock()
}

func (t *TransferTask) clearCurrent(rel string) {
	t.fileMu.Lock()
	if t.CurrentFile == rel {
		t.CurrentFile = ""
	}
	t.fileMu.Unlock()
}

func (t *TransferTask) start() {
	t.ctx, t.cancel = context.WithCancel(context.Background())
	t.pauseCh = make(chan struct{})
}

func (t *TransferTask) done() {
	if t.cancel != nil {
		t.cancel()
	}
}

func (t *TransferTask) setPaused(v bool) { t.paused.Store(v) }
func (t *TransferTask) isPaused() bool   { return t.paused.Load() }

func (t *TransferTask) waitIfPaused() {
	for {
		if t.isPaused() {
			select {
			case <-t.pauseCh:
				continue
			case <-t.ctx.Done():
				return
			}
		}
		return
	}
}

func (s *SFTPSession) nextTaskID(prefix string) string {
	return fmt.Sprintf("%s-%d", prefix, atomic.AddInt64(&s.taskSeq, 1))
}

// --- UID/GID -> name resolution (issue #702) --------------------------------
// A remote listing only yields numeric UID/GID, so owners render as "1000".
// Translate them to names by reading the remote /etc/passwd and /etc/group
// over SFTP once, cached for this connection. Unreadable or unresolved entries
// fall back to the numeric value.

func (s *SFTPSession) loadUserGroupMaps() {
	s.userMapOnce.Do(func() {
		users := map[int]string{}
		groups := map[int]string{}
		if s.sftpClient != nil {
			if data := s.readRemoteText("/etc/passwd"); data != nil {
				parseLinuxNameMap(data, users, 2)
			}
			if data := s.readRemoteText("/etc/group"); data != nil {
				parseLinuxNameMap(data, groups, 2)
			}
		}
		s.userMap = users
		s.groupMap = groups
	})
}

// readRemoteText reads a small remote file over SFTP, returning nil on failure.
func (s *SFTPSession) readRemoteText(p string) []byte {
	f, err := s.sftpClient.Open(p)
	if err != nil {
		return nil
	}
	defer f.Close()
	data, err := io.ReadAll(f)
	if err != nil {
		return nil
	}
	return data
}

// parseLinuxNameMap parses `/etc/passwd`-style lines (`name:x:<id>:...`) into
// an id->name map. `idIndex` points at the numeric id field.
func parseLinuxNameMap(data []byte, out map[int]string, idIndex int) {
	for _, line := range strings.Split(string(data), "\n") {
		parts := strings.Split(line, ":")
		if len(parts) < idIndex+1 || parts[0] == "" {
			continue
		}
		id, err := strconv.Atoi(parts[idIndex])
		if err != nil || id < 0 {
			continue
		}
		if _, exists := out[id]; !exists {
			out[id] = parts[0]
		}
	}
}

func (s *SFTPSession) resolveOwnerGroup(fi os.FileInfo) (string, string) {
	stat, ok := fi.Sys().(*sftp.FileStat)
	if !ok {
		return "", ""
	}
	owner := ""
	// UID/GID 0 is root, so resolve unconditionally (a > 0 guard would hide it).
	if name, ok := s.userMap[int(stat.UID)]; ok {
		owner = name
	} else {
		owner = fmt.Sprintf("%d", stat.UID)
	}
	group := ""
	if name, ok := s.groupMap[int(stat.GID)]; ok {
		group = name
	} else {
		group = fmt.Sprintf("%d", stat.GID)
	}
	return owner, group
}

// --- Public API methods (called from app.go Wails bindings) ---

func (s *SFTPSession) requireClient() error {
	if s.sftpClient == nil {
		return fmt.Errorf("SFTP session not connected")
	}
	return nil
}

func (s *SFTPSession) ListRemote(dir string) (FileListResult, error) {
	type outcome struct {
		res FileListResult
		err error
	}
	ch := make(chan outcome, 1)
	go func() {
		res, err := s.listRemoteUnlocked(dir)
		ch <- outcome{res, err}
	}()
	select {
	case out := <-ch:
		return out.res, out.err
	case <-time.After(25 * time.Second):
		return FileListResult{}, fmt.Errorf("list remote timeout")
	}
}

func (s *SFTPSession) listRemoteUnlocked(dir string) (FileListResult, error) {
	if err := s.requireClient(); err != nil {
		return FileListResult{}, err
	}
	if dir == "" {
		dir = s.cwd
	} else if !path.IsAbs(dir) {
		dir = path.Join(s.cwd, dir)
	}
	infos, err := s.sftpClient.ReadDir(dir)
	if err != nil {
		return FileListResult{}, err
	}
	files := make([]FileItem, 0, len(infos))
	for _, fi := range infos {
		owner, group := s.resolveOwnerGroup(fi)
		isDir := fi.IsDir()
		if fi.Mode()&os.ModeSymlink != 0 {
			if target, err := s.sftpClient.Stat(path.Join(dir, fi.Name())); err == nil {
				isDir = target.IsDir()
			}
		}
		isHidden := fi.Name() != "" && fi.Name()[0] == '.'
		if stat, ok := fi.Sys().(*sftp.FileStat); ok {
			for _, ext := range stat.Extended {
				if ext.ExtType == "win32-file-attributes" {
					if attrs, err := strconv.ParseInt(ext.ExtData, 0, 32); err == nil {
						isHidden = attrs&0x2 != 0 // FILE_ATTRIBUTE_HIDDEN
					}
				}
			}
		}
		files = append(files, FileItem{
			Name:     fi.Name(),
			Size:     fi.Size(),
			ModTime:  fi.ModTime().Format(time.RFC3339),
			Mode:     fi.Mode().String(),
			IsDir:    isDir,
			IsHidden: isHidden,
			Owner:    owner,
			Group:    group,
		})
	}
	return FileListResult{Files: files, Dir: dir}, nil
}

func (s *SFTPSession) ChangeRemoteDir(dir string) (FileListResult, error) {
	if err := s.requireClient(); err != nil {
		return FileListResult{}, err
	}
	target := dir
	if !path.IsAbs(dir) {
		target = path.Join(s.cwd, dir)
	}
	fi, err := s.sftpClient.Stat(target)
	if err != nil {
		return FileListResult{}, fmt.Errorf("no such directory: %s", target)
	}
	if !fi.IsDir() {
		return FileListResult{}, fmt.Errorf("not a directory: %s", target)
	}
	real, _ := s.sftpClient.RealPath(target)
	s.mu.Lock()
	s.cwd = real
	s.mu.Unlock()
	return s.ListRemote(real)
}

func (s *SFTPSession) MakeDir(dir string) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	p := dir
	if !path.IsAbs(p) {
		p = path.Join(s.cwd, p)
	}
	return s.sftpClient.Mkdir(p)
}

// Symlink creates a symbolic link on the remote server (SFTP SSH_FXP_SYMLINK).
// The link path resolves against the session cwd; the target is stored
// verbatim (a relative target resolves against the link's own directory).
func (s *SFTPSession) Symlink(target, linkPath string) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	if !path.IsAbs(linkPath) {
		linkPath = path.Join(s.cwd, linkPath)
	}
	return s.sftpClient.Symlink(target, linkPath)
}

func (s *SFTPSession) Remove(p string, recursive bool) error {
	// Deletes always go through the shell `rm -rf` fast path (much faster for
	// large trees), falling back to SFTP recursive removal when no shell is
	// available. `recursive` is kept only for the FS interface contract;
	// `rm -rf` is always recursive.
	if err := s.requireClient(); err != nil {
		return err
	}
	if !path.IsAbs(p) {
		p = path.Join(s.cwd, p)
	}
	p = path.Clean(p)
	if p == "/" || p == "." || p == "" {
		return fmt.Errorf("refusing to delete path: %s", p)
	}
	if s.sshClient != nil {
		session, err := s.sshClient.NewSession()
		if err != nil {
			// Fall back to SFTP remove.
			return s.rmRecursive(p)
		}
		defer session.Close()
		cmd := "rm -rf -- " + shellEscape(p)
		if runErr := session.Run(cmd); runErr != nil {
			// Some servers lack a shell rm; fall back to SFTP.
			if fe := s.rmRecursive(p); fe != nil {
				return fmt.Errorf("quick delete failed (%v); sftp fallback: %w", runErr, fe)
			}
		}
		return nil
	}
	return s.rmRecursive(p)
}

func (s *SFTPSession) Rename(oldName, newName string) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	old := oldName
	if !path.IsAbs(old) {
		old = path.Join(s.cwd, old)
	}
	newPath := newName
	if !path.IsAbs(newPath) {
		newPath = path.Join(s.cwd, newPath)
	}
	return s.sftpClient.Rename(old, newPath)
}

func (s *SFTPSession) Chmod(p string, mode os.FileMode) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	if !path.IsAbs(p) {
		p = path.Join(s.cwd, p)
	}
	return s.sftpClient.Chmod(p, mode)
}

func (s *SFTPSession) Get(remotePath, localPath string, recursive bool) (string, error) {
	if err := s.requireClient(); err != nil {
		return "", err
	}
	rp := remotePath
	if !path.IsAbs(rp) {
		rp = path.Join(s.cwd, rp)
	}
	lp := localPath
	if !filepath.IsAbs(lp) {
		lp = filepath.Join(s.localCwd, lp)
	}
	if recursive {
		return s.startDirTransfer("download", lp, rp, nil)
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

func (s *SFTPSession) Put(localPath, remotePath string, recursive bool) (string, error) {
	if err := s.requireClient(); err != nil {
		return "", err
	}
	lp := localPath
	if !filepath.IsAbs(lp) {
		lp = filepath.Join(s.localCwd, lp)
	}
	rp := remotePath
	if !path.IsAbs(rp) {
		rp = path.Join(s.cwd, rp)
	}
	if recursive {
		return s.startDirTransfer("upload", lp, rp, nil)
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

// startDirTransfer launches a recursive upload/download with per-file tracking
// and an optional retry skip-list. The returned task stays in s.transfers when
// it fails (retryable); it is removed when done or cancelled.
func (s *SFTPSession) startDirTransfer(tfType, lp, rp string, skip []string) (string, error) {
	var total int64
	var err error
	if tfType == "download" {
		total, err = s.dirSizeRemote(rp)
	} else {
		total, err = s.dirSizeLocal(lp)
	}
	if err != nil {
		return "", err
	}
	task := &TransferTask{
		ID:         s.nextTaskID(map[bool]string{true: "dl", false: "ul"}[tfType == "download"]),
		Type:       tfType,
		LocalPath:  lp,
		RemotePath: rp,
		Status:     "running",
	}
	task.setTotal(total)
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
			derr = s.downloadDir(rp, lp, task)
		} else {
			derr = s.uploadDir(lp, rp, task)
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
			// Walk-level failure (e.g. root ReadDir) with nothing attempted.
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

// PutContent writes raw content directly to a remote file via SFTP.
func (s *SFTPSession) PutContent(remotePath string, content []byte) error {
	type outcome struct{ err error }
	ch := make(chan outcome, 1)
	go func() {
		ch <- outcome{s.putContentUnlocked(remotePath, content)}
	}()
	select {
	case out := <-ch:
		return out.err
	case <-time.After(25 * time.Second):
		return fmt.Errorf("write remote content timeout")
	}
}

func (s *SFTPSession) putContentUnlocked(remotePath string, content []byte) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	rp := remotePath
	if !path.IsAbs(rp) {
		rp = path.Join(s.cwd, rp)
	}
	// Ensure parent directory exists
	parentDir := path.Dir(rp)
	if err := s.sftpClient.MkdirAll(parentDir); err != nil {
		return err
	}
	f, err := s.sftpClient.Create(rp)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.Write(content)
	return err
}

// GetContent reads the full content of a remote file.
// Like ListRemote, it is bounded by a timeout: a wedged connection (remote
// stall, half-open TCP) must surface an error instead of hanging the caller
// — the external-editor open path blocks the UI on this call.
func (s *SFTPSession) GetContent(remotePath string) ([]byte, error) {
	type outcome struct {
		b   []byte
		err error
	}
	ch := make(chan outcome, 1)
	go func() {
		b, err := s.getContentUnlocked(remotePath)
		ch <- outcome{b, err}
	}()
	select {
	case out := <-ch:
		return out.b, out.err
	case <-time.After(25 * time.Second):
		return nil, fmt.Errorf("read remote content timeout")
	}
}

func (s *SFTPSession) getContentUnlocked(remotePath string) ([]byte, error) {
	if err := s.requireClient(); err != nil {
		return nil, err
	}
	rp := remotePath
	if !path.IsAbs(rp) {
		rp = path.Join(s.cwd, rp)
	}
	f, err := s.sftpClient.Open(rp)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return io.ReadAll(f)
}

// shellEscape returns a safely single-quoted string for shell commands.
func shellEscape(str string) string {
	return "'" + strings.ReplaceAll(str, "'", "'\\''") + "'"
}

// Copy copies a file or directory on the remote server.
// Tries shell cp -r first (zero data transfer on Linux), falls back to
// SFTP-level copy for servers without cp (Windows, etc.).
func (s *SFTPSession) Copy(oldPath, newPath string) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	old := oldPath
	if !path.IsAbs(old) {
		old = path.Join(s.cwd, old)
	}
	n := newPath
	if !path.IsAbs(n) {
		n = path.Join(s.cwd, n)
	}
	// Try shell cp -r first (server-side copy, zero data transfer)
	session, err := s.sshClient.NewSession()
	if err != nil {
		return err
	}
	err = session.Run(fmt.Sprintf("cp -r -- %s %s", shellEscape(old), shellEscape(n)))
	session.Close()
	if err == nil {
		return nil
	}
	// Fallback: SFTP-level copy (compatible with Windows and servers without cp)
	return s.sftpCopy(old, n)
}

// sftpCopy copies a file or directory using SFTP operations only.
// Works on any SFTP server regardless of the remote shell environment.
func (s *SFTPSession) sftpCopy(oldPath, newPath string) error {
	srcInfo, err := s.sftpClient.Stat(oldPath)
	if err != nil {
		return err
	}
	if srcInfo.IsDir() {
		return s.sftpCopyDir(oldPath, newPath)
	}
	return s.sftpCopyFile(oldPath, newPath)
}

func (s *SFTPSession) sftpCopyFile(oldPath, newPath string) error {
	src, err := s.sftpClient.Open(oldPath)
	if err != nil {
		return err
	}
	defer src.Close()

	parentDir := path.Dir(newPath)
	if err := s.sftpClient.MkdirAll(parentDir); err != nil {
		return err
	}

	dst, err := s.sftpClient.Create(newPath)
	if err != nil {
		return err
	}
	defer dst.Close()

	_, err = io.Copy(dst, src)
	return err
}

func (s *SFTPSession) sftpCopyDir(oldPath, newPath string) error {
	if err := s.sftpClient.MkdirAll(newPath); err != nil {
		return err
	}
	entries, err := s.sftpClient.ReadDir(oldPath)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		oldEntry := path.Join(oldPath, entry.Name())
		newEntry := path.Join(newPath, entry.Name())
		if entry.IsDir() {
			if err := s.sftpCopyDir(oldEntry, newEntry); err != nil {
				return err
			}
		} else {
			if err := s.sftpCopyFile(oldEntry, newEntry); err != nil {
				return err
			}
		}
	}
	return nil
}

// Move moves a file or directory on the remote server.
// Tries SFTP Rename first (atomic, server-side), falls back to shell mv.
func (s *SFTPSession) Move(oldPath, newPath string) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	old := oldPath
	if !path.IsAbs(old) {
		old = path.Join(s.cwd, old)
	}
	n := newPath
	if !path.IsAbs(n) {
		n = path.Join(s.cwd, n)
	}
	// Try SFTP native rename first (same filesystem, zero data transfer)
	if err := s.sftpClient.Rename(old, n); err == nil {
		return nil
	}
	// Fallback: shell mv handles cross-filesystem moves
	session, err := s.sshClient.NewSession()
	if err != nil {
		return err
	}
	defer session.Close()
	return session.Run(fmt.Sprintf("mv -- %s %s", shellEscape(old), shellEscape(n)))
}

// RetryTransfer (re)starts a transfer from a frontend-held checkpoint. For
// recursive transfers, files listed in skipCompleted (paths relative to the
// transfer root, '/'-separated) are counted as done without re-transferring.
func (s *SFTPSession) RetryTransfer(spec TransferSpec, skipCompleted []string) (string, error) {
	if err := s.requireClient(); err != nil {
		return "", err
	}
	if spec.Recursive {
		if spec.Type == "download" {
			return s.startDirTransfer("download", spec.LocalPath, spec.RemotePath, skipCompleted)
		}
		return s.startDirTransfer("upload", spec.LocalPath, spec.RemotePath, skipCompleted)
	}
	if spec.Type == "download" {
		return s.Get(spec.RemotePath, spec.LocalPath, false)
	}
	return s.Put(spec.LocalPath, spec.RemotePath, false)
}

// DismissTransfer drops a retained (failed) task from the transfers map.
func (s *SFTPSession) DismissTransfer(taskID string) error {
	s.mu.Lock()
	delete(s.transfers, taskID)
	s.mu.Unlock()
	return nil
}

// CancelTransfer cancels an ongoing transfer task.
func (s *SFTPSession) CancelTransfer(taskID string) error {
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

// PauseTransfer pauses an ongoing transfer task.
func (s *SFTPSession) PauseTransfer(taskID string) error {
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
func (s *SFTPSession) ResumeTransfer(taskID string) error {
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

// --- Recursive helpers ---

// localCopyRecursive copies files and directories on the local filesystem.
func localCopyRecursive(src, dst string) error {
	si, err := os.Stat(src)
	if err != nil {
		return err
	}
	if si.IsDir() {
		if err := os.MkdirAll(dst, si.Mode()); err != nil {
			return err
		}
		entries, err := os.ReadDir(src)
		if err != nil {
			return err
		}
		for _, entry := range entries {
			if err := localCopyRecursive(filepath.Join(src, entry.Name()), filepath.Join(dst, entry.Name())); err != nil {
				return err
			}
		}
		return nil
	}
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	out, err := os.OpenFile(dst, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, si.Mode())
	if err != nil {
		return err
	}
	defer out.Close()
	_, err = io.Copy(out, in)
	return err
}

func (s *SFTPSession) rmRecursive(p string) error {
	fi, err := s.sftpClient.Stat(p)
	if err != nil {
		return err
	}
	if fi.IsDir() {
		infos, err := s.sftpClient.ReadDir(p)
		if err != nil {
			return err
		}
		for _, info := range infos {
			childPath := path.Join(p, info.Name())
			if err := s.rmRecursive(childPath); err != nil {
				return err
			}
		}
		return s.sftpClient.RemoveDirectory(p)
	}
	return s.sftpClient.Remove(p)
}

func (s *SFTPSession) dirSizeRemote(dir string) (int64, error) {
	infos, err := s.sftpClient.ReadDir(dir)
	if err != nil {
		return 0, err
	}
	var total int64
	for _, fi := range infos {
		if fi.IsDir() {
			sz, err := s.dirSizeRemote(path.Join(dir, fi.Name()))
			if err != nil {
				return 0, err
			}
			total += sz
		} else {
			total += fi.Size()
		}
	}
	return total, nil
}

func (s *SFTPSession) dirSizeLocal(dir string) (int64, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return 0, err
	}
	var total int64
	for _, e := range entries {
		if e.IsDir() {
			sz, err := s.dirSizeLocal(filepath.Join(dir, e.Name()))
			if err != nil {
				return 0, err
			}
			total += sz
		} else {
			fi, err := e.Info()
			if err != nil {
				return 0, err
			}
			total += fi.Size()
		}
	}
	return total, nil
}

// --- Transfer methods ---

func (s *SFTPSession) startTransfer(task *TransferTask) {
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

		// Acquire concurrency slot
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

		var src io.Reader
		var dst io.Writer

		if task.Type == "download" {
			remoteFile, e := s.sftpClient.Open(task.RemotePath)
			if e != nil {
				s.emitTransferEvent(task, e)
				return
			}
			defer remoteFile.Close()
			fi, _ := remoteFile.Stat()
			if fi != nil {
				task.setTotal(fi.Size())
			}
			src = remoteFile
			localFile, e := os.Create(task.LocalPath)
			if e != nil {
				s.emitTransferEvent(task, e)
				return
			}
			defer localFile.Close()
			dst = localFile
		} else {
			localFile, e := os.Open(task.LocalPath)
			if e != nil {
				s.emitTransferEvent(task, e)
				return
			}
			defer localFile.Close()
			fi, _ := localFile.Stat()
			if fi != nil {
				task.setTotal(fi.Size())
			}
			src = localFile
			remoteFile, e := s.sftpClient.Create(task.RemotePath)
			if e != nil {
				s.emitTransferEvent(task, e)
				return
			}
			defer remoteFile.Close()
			dst = remoteFile
		}

		buf := make([]byte, 64*1024)
		for {
			select {
			case <-task.ctx.Done():
				task.Status = "cancelled"
				s.emitTransferComplete(task)
				removeTask()
				return
			default:
			}
			task.waitIfPaused()
			select {
			case <-task.ctx.Done():
				task.Status = "cancelled"
				s.emitTransferComplete(task)
				removeTask()
				return
			default:
			}
			n, e := src.Read(buf)
			if n > 0 {
				dst.Write(buf[:n])
				task.addProgress(int64(n))
				s.emitTransferProgress(task)
			}
			if e == io.EOF {
				break
			}
			if e != nil {
				s.emitTransferEvent(task, e)
				return
			}
		}
		task.Status = "done"
		s.emitTransferComplete(task)
		removeTask()
	}()
}

// dirEntry2 is one file scheduled for transfer inside a directory task.
type dirEntry2 struct{ lp, rp, rel string }

// relPath returns p relative to root with '/' separators; "" if equal.
func relPath(p, root string) string {
	r := strings.TrimPrefix(p, root)
	return strings.TrimPrefix(r, "/")
}

func (s *SFTPSession) walkRemoteForDownload(remoteDir, localDir string, task *TransferTask, out *[]dirEntry2) error {
	select {
	case <-task.ctx.Done():
		return task.ctx.Err()
	default:
	}
	if err := os.MkdirAll(localDir, 0755); err != nil {
		return err
	}
	infos, err := s.sftpClient.ReadDir(remoteDir)
	if err != nil {
		return err
	}
	for _, fi := range infos {
		rp := path.Join(remoteDir, fi.Name())
		lp := filepath.Join(localDir, fi.Name())
		if fi.IsDir() {
			if err := s.walkRemoteForDownload(rp, lp, task, out); err != nil {
				return err
			}
		} else {
			*out = append(*out, dirEntry2{lp: lp, rp: rp, rel: relPath(rp, task.RemotePath)})
		}
	}
	return nil
}

func (s *SFTPSession) walkLocalForUpload(localDir, remoteDir string, task *TransferTask, out *[]dirEntry2) error {
	select {
	case <-task.ctx.Done():
		return task.ctx.Err()
	default:
	}
	if err := s.sftpClient.MkdirAll(remoteDir); err != nil {
		return err
	}
	entries, err := os.ReadDir(localDir)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		lp := filepath.Join(localDir, entry.Name())
		rp := path.Join(remoteDir, entry.Name())
		if entry.IsDir() {
			if err := s.walkLocalForUpload(lp, rp, task, out); err != nil {
				return err
			}
		} else {
			*out = append(*out, dirEntry2{lp: lp, rp: rp, rel: relPath(rp, task.RemotePath)})
		}
	}
	return nil
}

func (s *SFTPSession) downloadDir(remoteDir, localDir string, task *TransferTask) error {
	var files []dirEntry2
	if err := s.walkRemoteForDownload(remoteDir, localDir, task, &files); err != nil {
		if task.ctx.Err() != nil {
			return task.ctx.Err()
		}
		task.failFile(relPath(remoteDir, task.RemotePath), err)
		return nil // recorded as a failed entry; task finalizes with status error
	}
	s.runTransferPool(task, files, "download")
	return nil
}

func (s *SFTPSession) uploadDir(localDir, remoteDir string, task *TransferTask) error {
	var files []dirEntry2
	if err := s.walkLocalForUpload(localDir, remoteDir, task, &files); err != nil {
		if task.ctx.Err() != nil {
			return task.ctx.Err()
		}
		task.failFile(relPath(remoteDir, task.RemotePath), err)
		return nil // recorded as a failed entry; task finalizes with status error
	}
	s.runTransferPool(task, files, "upload")
	return nil
}

// transferDirEntry transfers one file of a directory task while holding a
// concurrency slot, released via defer so a panic cannot leak the slot. The
// acquire is cancellable: a worker blocked on the semaphore returns without
// transferring when the task is cancelled.
func (s *SFTPSession) transferDirEntry(task *TransferTask, e dirEntry2, tfType string) {
	if s.sem != nil {
		select {
		case s.sem <- struct{}{}:
			defer func() { <-s.sem }()
		case <-task.ctx.Done():
			return
		}
	}
	s.emitFileStart(task, e.rel, filepath.Base(e.rel))
	task.beginFile(e.rel)
	err := s.transferFile(task, e.lp, e.rp, tfType)
	if err != nil && task.ctx.Err() != nil {
		task.clearCurrent(e.rel) // cancelled mid-file: not a file failure
	} else if err != nil {
		task.failFile(e.rel, err)
		s.emitFileFailed(task, e.rel, err)
	} else {
		task.finishFile(e.rel)
		s.emitFileDone(task, e.rel)
	}
	s.emitTransferProgress(task)
}

// runTransferPool processes files through a bounded worker pool. Bounded by
// the connection's SftpMaxConcurrency (its semaphore); defaults to 4 workers
// when the session has no semaphore set.
func (s *SFTPSession) runTransferPool(task *TransferTask, files []dirEntry2, tfType string) {
	task.setFileCount(len(files))
	if len(files) == 0 {
		return
	}
	workers := 4
	if s.sem != nil {
		workers = cap(s.sem)
	}
	if workers > len(files) {
		workers = len(files)
	}
	ch := make(chan dirEntry2)
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for e := range ch {
				if task.ctx.Err() != nil {
					continue // cancelled: drain without transferring
				}
				task.waitIfPaused()
				if task.shouldSkip(e.rel) {
					task.beginFile(e.rel)
					task.finishFile(e.rel)
					continue
				}
				s.transferDirEntry(task, e, tfType)
			}
		}()
	}
feed:
	for _, f := range files {
		select {
		case ch <- f:
		case <-task.ctx.Done():
			break feed
		}
	}
	close(ch)
	wg.Wait()
}

func (s *SFTPSession) transferFile(task *TransferTask, localPath, remotePath, tfType string) error {
	if tfType == "download" {
		src, err := s.sftpClient.Open(remotePath)
		if err != nil {
			return err
		}
		defer src.Close()
		dst, err := os.Create(localPath)
		if err != nil {
			return err
		}
		defer dst.Close()
		buf := make([]byte, 64*1024)
		for {
			select {
			case <-task.ctx.Done():
				return task.ctx.Err()
			default:
			}
			task.waitIfPaused()
			n, e := src.Read(buf)
			if n > 0 {
				dst.Write(buf[:n])
				task.addProgress(int64(n))
				s.emitTransferProgress(task)
			}
			if e != nil {
				break
			}
		}
	} else {
		src, err := os.Open(localPath)
		if err != nil {
			return err
		}
		defer src.Close()
		dst, err := s.sftpClient.Create(remotePath)
		if err != nil {
			return err
		}
		defer dst.Close()
		buf := make([]byte, 64*1024)
		for {
			select {
			case <-task.ctx.Done():
				return task.ctx.Err()
			default:
			}
			task.waitIfPaused()
			n, e := src.Read(buf)
			if n > 0 {
				dst.Write(buf[:n])
				task.addProgress(int64(n))
				s.emitTransferProgress(task)
			}
			if e != nil {
				break
			}
		}
	}
	return nil
}

