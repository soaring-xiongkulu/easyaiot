package session

import (
	"bufio"
	"bytes"
	"context"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestParseLsLongListing(t *testing.T) {
	out := "total 24\n" +
		"drwxr-xr-x  2 root root 4096 Jan 12 09:30 .\n" +
		"drwxr-xr-x 14 root root 4096 Jan 12 09:30 ..\n" +
		"-rw-r--r--  1 ys ys 1234 Feb  3 10:20 file.txt\n" +
		"drwxr-xr-x  3 root root 4096 Jan 12 09:30 a dir with spaces\n" +
		"lrwxrwxrwx  1 root root    7 Jan 12 09:30 link -> target\n" +
		"Welcome to the device!\n" +
		"-rwxr-xr-x 1 admin admin 99 Dec 25 2019 old.sh\n"
	entries := parseLsLongListing(out)
	// "." and ".." are intentionally dropped (the frontend synthesizes ".."),
	// banner noise is skipped.
	if len(entries) != 4 {
		t.Fatalf("expected 4 entries, got %d: %+v", len(entries), entries)
	}
	f := entries[0]
	if f.Name != "file.txt" || f.Size != 1234 || f.Owner != "ys" || f.Group != "ys" {
		t.Errorf("file.txt wrong: %+v", f)
	}
	if f.ModTime.Month() != time.February || f.ModTime.Day() != 3 || f.ModTime.Minute() != 20 {
		t.Errorf("file.txt modtime wrong: %+v", f.ModTime)
	}
	if entries[1].Name != "a dir with spaces" {
		t.Errorf("spaces name wrong: %+v", entries[1])
	}
	l := entries[2]
	if l.Name != "link" || !strings.HasPrefix(l.Mode, "l") || l.Size != 7 {
		t.Errorf("symlink wrong: %+v", l)
	}
}

func TestParseLsLineISODate(t *testing.T) {
	// toybox / ISO date format
	e, ok := parseLsLine("drwxrwx--x 2 root root 4096 2020-01-01 10:00 data")
	if !ok {
		t.Fatal("ISO line not parsed")
	}
	if e.Name != "data" || e.Size != 4096 || e.Owner != "root" || e.Group != "root" {
		t.Errorf("ISO entry wrong: %+v", e)
	}
	if e.ModTime.Year() != 2020 || e.ModTime.Month() != time.January {
		t.Errorf("ISO modtime wrong: %+v", e.ModTime)
	}
}

func TestParseLsLineYearForm(t *testing.T) {
	e, ok := parseLsLine("-rw-r--r-- 1 root root 512 Jan  5  2018 old.log")
	if !ok {
		t.Fatal("year-form line not parsed")
	}
	if e.Name != "old.log" || e.Size != 512 {
		t.Errorf("year-form entry wrong: %+v", e)
	}
	if e.ModTime.Year() != 2018 {
		t.Errorf("year-form modtime wrong: %+v", e.ModTime)
	}
}

func TestParseLsLineACLAndRejects(t *testing.T) {
	if _, ok := parseLsLine("-rw-r--r--+ 1 root root 10 Jan 1 10:00 acl.txt"); !ok {
		t.Error("ACL mode (+ suffix) line should parse")
	}
	if _, ok := parseLsLine(""); ok {
		t.Error("empty line should not parse")
	}
	if _, ok := parseLsLine("total 12"); ok {
		t.Error("total line should not parse")
	}
	if _, ok := parseLsLine("random banner text"); ok {
		t.Error("banner noise should not parse")
	}
}

func TestParseLsLineHidden(t *testing.T) {
	e, ok := parseLsLine("-rw------- 1 root root 88 Mar 9 23:59 .ssh_config")
	if !ok || e.Name != ".ssh_config" {
		t.Fatalf("hidden file wrong: %+v ok=%v", e, ok)
	}
}

func TestScpDirectiveName(t *testing.T) {
	if got := scpDirectiveName("C0644 123 file name.txt"); got != "file name.txt" {
		t.Errorf("C name wrong: %q", got)
	}
	if got := scpDirectiveName("D0755 0 subdir"); got != "subdir" {
		t.Errorf("D name wrong: %q", got)
	}
	if got := scpDirectiveName("E"); got != "" {
		t.Errorf("E should have no name: %q", got)
	}
}

func TestSanitizeScpName(t *testing.T) {
	if got := sanitizeScpName("bad\nname\r.txt"); got != "badname.txt" {
		t.Errorf("sanitize wrong: %q", got)
	}
	if got := sanitizeScpName("normal.txt"); got != "normal.txt" {
		t.Errorf("sanitize wrong: %q", got)
	}
}

// --- symlink creation / navigation commands ----------------------------------

func TestScpSymlinkCommand(t *testing.T) {
	cases := []struct {
		target, link, want string
	}{
		{"target", "link", "ln -s 'target' 'link'"},
		{"target dir", "my link", "ln -s 'target dir' 'my link'"},
		{"/a/b/../c", "/home/u/l", "ln -s '/a/b/../c' '/home/u/l'"},
		{"it's", "link", "ln -s 'it'\\''s' 'link'"},
	}
	for _, c := range cases {
		if got := scpSymlinkCommand(c.target, c.link); got != c.want {
			t.Errorf("scpSymlinkCommand(%q, %q) = %q, want %q", c.target, c.link, got, c.want)
		}
	}
}

// ChangeRemoteDir must report the PHYSICAL directory (pwd -P), so entering a
// directory symlink lands on its real target — matching SFTP's RealPath and
// the WSL backend's readlink fallback.
func TestScpChangeDirCommand(t *testing.T) {
	cases := []struct{ target, want string }{
		{"/home/u", "cd '/home/u' 2>/dev/null && pwd -P"},
		{"/my dir", "cd '/my dir' 2>/dev/null && pwd -P"},
	}
	for _, c := range cases {
		if got := scpChangeDirCommand(c.target); got != c.want {
			t.Errorf("scpChangeDirCommand(%q) = %q, want %q", c.target, got, c.want)
		}
	}
}

// --- Tree-walk per-file tracking ---------------------------------------------
//
// The scp tree walkers run over an exec channel, so there is no in-process
// remote to serve a tree like the SFTP tests' pkg/sftp server. Instead the
// walkers are driven directly with a fake scpProtoConn: the "remote" side is
// a scripted byte stream (directives + file bodies for downloads) or a
// scripted ack stream (uploads), and the client's writes are collected in a
// buffer for inspection.

// newFakeScpConn builds an scpProtoConn over in-memory buffers. stdout is
// what the client reads (scripted remote output); the client's writes land in
// the returned buffer (acks on downloads, directives+data on uploads).
func newFakeScpConn(stdout []byte) (*scpProtoConn, *bytes.Buffer) {
	stdin := &bytes.Buffer{}
	return &scpProtoConn{
		stdout: bufio.NewReader(bytes.NewReader(stdout)),
		stdin:  stdin,
	}, stdin
}

// newScpTreeTask builds a started TransferTask for walker tests.
func newScpTreeTask(localRoot, remoteRoot string) *TransferTask {
	task := &TransferTask{
		ID:         "t1",
		Type:       "download",
		LocalPath:  localRoot,
		RemotePath: remoteRoot,
		Status:     "running",
	}
	task.start()
	return task
}

// TestScpFetchTreePerFileTracking drives the download walker end to end with
// a scripted remote stream: root directory, nested subdirectories, files at
// both levels, then termination. Asserts files land in the right local places
// and per-file accounting is correct.
func TestScpFetchTreePerFileTracking(t *testing.T) {
	root := t.TempDir()
	script := "" +
		"D0755 0 src\n" +
		"C0644 3 a.txt\n" + "AAA\x00" +
		"D0755 0 sub\n" +
		"C0644 1 f.txt\n" + "C\x00" +
		"D0755 0 deeper\n" +
		"C0644 2 g.txt\n" + "GG\x00" + "E\n" +
		"E\n" +
		"C0644 2 b.txt\n" + "BB\x00" + "E\n" +
		"E\n"
	c, _ := newFakeScpConn([]byte(script))

	s := NewSCPSession("test-scp")
	task := newScpTreeTask(root, "/remote/src")
	if err := s.fetchTree(c, "/remote/src", root, task); err != nil {
		t.Fatalf("fetchTree: %v", err)
	}
	b, err := os.ReadFile(filepath.Join(root, "a.txt"))
	if err != nil || string(b) != "AAA" {
		t.Fatalf("a.txt = %q, err %v", b, err)
	}
	b, _ = os.ReadFile(filepath.Join(root, "sub", "f.txt"))
	if string(b) != "C" {
		t.Fatalf("sub/f.txt = %q", b)
	}
	b, _ = os.ReadFile(filepath.Join(root, "sub", "deeper", "g.txt"))
	if string(b) != "GG" {
		t.Fatalf("sub/deeper/g.txt = %q", b)
	}
	b, _ = os.ReadFile(filepath.Join(root, "b.txt"))
	if string(b) != "BB" {
		t.Fatalf("b.txt = %q", b)
	}
	if task.CompletedFiles != 4 {
		t.Fatalf("CompletedFiles = %d, want 4", task.CompletedFiles)
	}
	if got := task.loadProgress(); got != 8 {
		t.Fatalf("progress = %d, want 8", got)
	}
}

// TestScpFetchTreeSkipsFilesOnRetrySkipList: files on the task's skip list
// are drained (protocol stream stays in sync) and counted as done without
// being written locally.
func TestScpFetchTreeSkipsFilesOnRetrySkipList(t *testing.T) {
	root := t.TempDir()
	script := "" +
		"D0755 0 src\n" +
		"C0644 3 a.txt\n" + "AAA\x00" +
		"C0644 2 b.txt\n" + "BB\x00" +
		"D0755 0 sub\n" +
		"C0644 1 c.txt\n" + "C\x00" + "E\n" +
		"E\n" +
		"E\n"
	c, _ := newFakeScpConn([]byte(script))

	s := NewSCPSession("test-scp")
	task := newScpTreeTask(root, "/remote/src")
	task.SetSkip([]string{"a.txt", "sub/c.txt"})
	if err := s.fetchTree(c, "/remote/src", root, task); err != nil {
		t.Fatalf("fetchTree: %v", err)
	}
	if _, err := os.Stat(filepath.Join(root, "a.txt")); !os.IsNotExist(err) {
		t.Fatalf("skipped a.txt should not have been created (err=%v)", err)
	}
	if _, err := os.Stat(filepath.Join(root, "sub", "c.txt")); !os.IsNotExist(err) {
		t.Fatalf("skipped sub/c.txt should not have been created (err=%v)", err)
	}
	b, _ := os.ReadFile(filepath.Join(root, "b.txt"))
	if string(b) != "BB" {
		t.Fatalf("b.txt = %q", b)
	}
	if task.CompletedFiles != 3 {
		t.Fatalf("CompletedFiles = %d, want 3 (skipped files count as done)", task.CompletedFiles)
	}
	if len(task.FailedFiles) != 0 {
		t.Fatalf("FailedFiles = %v, want empty", task.FailedFiles)
	}
}

// TestScpFetchTreeContinuesAfterPerFileFailure: a file whose local create
// fails (a directory occupies its path) is recorded in FailedFiles and the
// walk continues with the remaining siblings.
func TestScpFetchTreeContinuesAfterPerFileFailure(t *testing.T) {
	root := t.TempDir()
	// A directory at b.txt blocks os.Create for that entry.
	if err := os.MkdirAll(filepath.Join(root, "b.txt"), 0o755); err != nil {
		t.Fatal(err)
	}
	script := "" +
		"D0755 0 src\n" +
		"C0644 1 a.txt\n" + "A\x00" +
		"C0644 2 b.txt\n" + "BB\x00" +
		"C0644 1 c.txt\n" + "C\x00" + "E\n" +
		"E\n"
	c, _ := newFakeScpConn([]byte(script))

	s := NewSCPSession("test-scp")
	task := newScpTreeTask(root, "/remote/src")
	if err := s.fetchTree(c, "/remote/src", root, task); err != nil {
		t.Fatalf("fetchTree: %v", err)
	}
	if _, err := os.Stat(filepath.Join(root, "c.txt")); err != nil {
		t.Fatalf("walk should have continued past b.txt to c.txt: %v", err)
	}
	if task.CompletedFiles != 2 {
		t.Fatalf("CompletedFiles = %d, want 2 (failure must not abort walk)", task.CompletedFiles)
	}
	if len(task.FailedFiles) != 1 || task.FailedFiles[0].Path != "b.txt" {
		t.Fatalf("FailedFiles = %v, want one entry for b.txt", task.FailedFiles)
	}
	if task.loadProgress() != 2 { // a.txt + c.txt bytes only
		t.Fatalf("progress = %d, want 2", task.loadProgress())
	}
}

// TestScpFetchTreeCancelAbortsWalk: cancellation surfaces from the walker.
func TestScpFetchTreeCancelAbortsWalk(t *testing.T) {
	root := t.TempDir()
	script := "" +
		"D0755 0 src\n" +
		"C0644 3 a.txt\n" + "AAA\x00" + "E\n"
	c, _ := newFakeScpConn([]byte(script))

	s := NewSCPSession("test-scp")
	task := newScpTreeTask(root, "/remote/src")
	task.cancel() // cancelled before the walk starts
	if err := s.fetchTree(c, "/remote/src", root, task); err != context.Canceled {
		t.Fatalf("err = %v, want context.Canceled", err)
	}
}

// TestScpSendTreePerFileTracking drives the upload walker with a fake
// connection whose stdout is a stream of acks. Asserts the directives and
// file data written by the client and the per-file accounting.
func TestScpSendTreePerFileTracking(t *testing.T) {
	root := t.TempDir()
	os.MkdirAll(filepath.Join(root, "sub"), 0o755)
	os.WriteFile(filepath.Join(root, "a.txt"), []byte("AAA"), 0o644)
	os.WriteFile(filepath.Join(root, "sub", "c.txt"), []byte("C"), 0o644)

	acks := bytes.Repeat([]byte{0}, 16)
	c, stdin := newFakeScpConn(acks)

	s := NewSCPSession("test-scp")
	task := newScpTreeTask(root, "/remote/out")
	if err := s.sendTreeEntries(c, root, "/remote/out", task); err != nil {
		t.Fatalf("sendTreeEntries: %v", err)
	}
	sent := stdin.String()
	if !strings.Contains(sent, "D0755 0 sub\n") {
		t.Fatalf("missing D directive for sub: %q", sent)
	}
	if !strings.Contains(sent, "C0644 3 a.txt\nAAA\x00") {
		t.Fatalf("missing a.txt directive+data: %q", sent)
	}
	if !strings.Contains(sent, "C0644 1 c.txt\nC\x00") {
		t.Fatalf("missing sub/c.txt directive+data: %q", sent)
	}
	if strings.Count(sent, "E\n") != 1 {
		t.Fatalf("E count = %d, want 1", strings.Count(sent, "E\n"))
	}
	if task.CompletedFiles != 2 {
		t.Fatalf("CompletedFiles = %d, want 2", task.CompletedFiles)
	}
	if got := task.loadProgress(); got != 4 {
		t.Fatalf("progress = %d, want 4", got)
	}
}

// TestScpSendTreeSkipsFilesOnRetrySkipList: skipped files produce no
// directive at all and still count as done.
func TestScpSendTreeSkipsFilesOnRetrySkipList(t *testing.T) {
	root := t.TempDir()
	os.MkdirAll(filepath.Join(root, "sub"), 0o755)
	os.WriteFile(filepath.Join(root, "a.txt"), []byte("AAA"), 0o644)
	os.WriteFile(filepath.Join(root, "sub", "c.txt"), []byte("C"), 0o644)

	acks := bytes.Repeat([]byte{0}, 16)
	c, stdin := newFakeScpConn(acks)

	s := NewSCPSession("test-scp")
	task := newScpTreeTask(root, "/remote/out")
	task.SetSkip([]string{"a.txt"})
	if err := s.sendTreeEntries(c, root, "/remote/out", task); err != nil {
		t.Fatalf("sendTreeEntries: %v", err)
	}
	sent := stdin.String()
	if strings.Contains(sent, "a.txt") {
		t.Fatalf("skipped a.txt must not produce a directive: %q", sent)
	}
	if !strings.Contains(sent, "C0644 1 c.txt\nC\x00") {
		t.Fatalf("missing sub/c.txt directive+data: %q", sent)
	}
	if task.CompletedFiles != 2 {
		t.Fatalf("CompletedFiles = %d, want 2 (skip counts as done)", task.CompletedFiles)
	}
	if len(task.FailedFiles) != 0 {
		t.Fatalf("FailedFiles = %v, want empty", task.FailedFiles)
	}
}

// TestScpSendTreeAbortsOnStreamDesync: when the remote sink rejects a file's
// directive the stream is desynced, the failed file is recorded and the walk
// aborts with the stream-lost error (a.txt is never attempted).
func TestScpSendTreeAbortsOnStreamDesync(t *testing.T) {
	root := t.TempDir()
	os.MkdirAll(filepath.Join(root, "sub"), 0o755)
	os.WriteFile(filepath.Join(root, "a.txt"), []byte("AAA"), 0o644)
	os.WriteFile(filepath.Join(root, "sub", "c.txt"), []byte("C"), 0o644)

	// ack for the D directive, then a fatal error for c.txt's C directive.
	stdout := append([]byte{0, 0, 0}, []byte("\x02permission denied\n")...)
	c, stdin := newFakeScpConn(stdout)

	s := NewSCPSession("test-scp")
	task := newScpTreeTask(root, "/remote/out")
	err := s.sendTreeEntries(c, root, "/remote/out", task)
	var lost *scpStreamLostError
	if !errors.As(err, &lost) {
		t.Fatalf("err = %v, want scpStreamLostError", err)
	}
	if len(task.FailedFiles) != 1 || task.FailedFiles[0].Path != "sub/c.txt" {
		t.Fatalf("FailedFiles = %v, want one entry for sub/c.txt", task.FailedFiles)
	}
	if task.CompletedFiles != 1 {
		t.Fatalf("CompletedFiles = %d, want 1 (a.txt finished before the desync)", task.CompletedFiles)
	}
	sent := stdin.String()
	if !strings.Contains(sent, "AAA\x00") {
		t.Fatalf("a.txt should have completed before the desync: %q", sent)
	}
	if strings.Contains(sent, "c.txt\nC") {
		t.Fatalf("c.txt data must not be sent after its directive was rejected: %q", sent)
	}
}

// scpRetryCapability mirrors the app-layer transferRetry interface so the
// session package can assert, at compile time, that *SCPSession satisfies it
// alongside *SFTPSession.
var scpRetryCapability = []interface {
	RetryTransfer(spec TransferSpec, skipCompleted []string) (string, error)
	DismissTransfer(taskID string) error
}{(*SCPSession)(nil), (*SFTPSession)(nil)}

// TestScpRetryTransferDispatchGuard: with no live connection both routes are
// guarded by requireConnected; the dispatch wiring itself (recursive ->
// startSCPTree with the skip list, single file -> Get/Put) mirrors the SFTP
// implementation verified end-to-end by TestRetryTransferSkipsCompletedFiles.
func TestScpRetryTransferDispatchGuard(t *testing.T) {
	s := NewSCPSession("test-scp")
	if _, err := s.RetryTransfer(TransferSpec{Type: "download", LocalPath: "l", RemotePath: "r", Recursive: true}, []string{"a.txt"}); err == nil {
		t.Fatal("recursive retry without a connection must fail")
	}
	if _, err := s.RetryTransfer(TransferSpec{Type: "upload", LocalPath: "l", RemotePath: "r"}, nil); err == nil {
		t.Fatal("single-file retry without a connection must fail")
	}
}

// TestScpDismissTransfer: a retained task can be dropped from the map.
func TestScpDismissTransfer(t *testing.T) {
	s := NewSCPSession("test-scp")
	task := newScpTreeTask("l", "r")
	s.mu.Lock()
	s.transfers[task.ID] = task
	s.mu.Unlock()
	if err := s.DismissTransfer(task.ID); err != nil {
		t.Fatalf("dismiss: %v", err)
	}
	s.mu.RLock()
	_, kept := s.transfers[task.ID]
	s.mu.RUnlock()
	if kept {
		t.Fatal("dismissed task still present")
	}
}
