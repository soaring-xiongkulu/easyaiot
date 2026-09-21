//go:build windows
// +build windows

package session

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"
)

// The wsl.localhost 9P share reports Linux symlinks as plain, unstattable
// files, so symlink entries must be corrected from `ls -lAn` output while
// ordinary entries only pick up owner/group.

func TestApplyLsEnrichment(t *testing.T) {
	// UNC-derived listing: symlinks come through as anonymous plain files.
	files := []FileItem{
		{Name: "flink", Size: 0, ModTime: "", Mode: "----------", IsDir: false},
		{Name: "dlink", Size: 0, ModTime: "", Mode: "----------", IsDir: false},
		{Name: "real.txt", Size: 3, ModTime: "2026-09-10T12:00:00+08:00", Mode: "-rw-r--r--", IsDir: false},
		{Name: "not-in-ls", Size: 1, Mode: "-rw-r--r--", IsDir: false},
	}
	users := map[int]string{1000: "me"}
	groups := map[int]string{1000: "me"}
	symDirs := map[string]bool{"dlink": true}

	mt := time.Date(2026, time.September, 10, 12, 1, 0, 0, time.UTC)
	applyLsEnrichment(files, []lsEntry{
		{Name: "real.txt", Mode: "-rw-r--r--", Size: 3, Owner: "1000", Group: "1000", ModTime: mt},
		{Name: "flink", Mode: "lrwxrwxrwx", Size: 9, Owner: "1000", Group: "1000", ModTime: mt},
		{Name: "dlink", Mode: "lrwxrwxrwx", Size: 4, Owner: "1000", Group: "1000", ModTime: mt},
		{Name: "sub2", Mode: "drwxr-xr-x", Size: 4096, Owner: "1000", Group: "1000", ModTime: mt},
	}, symDirs, users, groups)

	// Symlinks take mode/size/mtime/dir-ness from ls.
	if files[0].Mode != "lrwxrwxrwx" || files[0].Size != 9 || files[0].IsDir {
		t.Errorf("flink wrong: %+v", files[0])
	}
	if files[1].Mode != "lrwxrwxrwx" || !files[1].IsDir {
		t.Errorf("dlink (dir symlink) wrong: %+v", files[1])
	}
	if files[0].Owner != "me" || files[0].Group != "me" {
		t.Errorf("flink owner/group wrong: %+v", files[0])
	}
	// Ordinary entries keep their UNC-derived fields, gain owner/group only.
	if files[2].Mode != "-rw-r--r--" || files[2].Size != 3 || files[2].Owner != "me" {
		t.Errorf("real.txt wrong: %+v", files[2])
	}
	// Entries absent from ls stay untouched.
	if files[3].Owner != "" || files[3].Mode != "-rw-r--r--" {
		t.Errorf("not-in-ls should be untouched: %+v", files[3])
	}
}

// The batched "which symlinks point at directories" probe script. It must be
// free of shell variables: wsl.exe re-quotes argv inside double quotes, so
// $n/$p/$((...)) would be expanded to nothing by the login shell before sh
// ever sees the script (this broke the dir detection in production once).
func TestTestDirScript(t *testing.T) {
	got := testDirScript([]string{"/a b", "/c'd"})
	want := "if [ -d '/a b' ]; then echo '1 d'; fi; if [ -d '/c'\\''d' ]; then echo '2 d'; fi"
	if got != want {
		t.Errorf("testDirScript = %q, want %q", got, want)
	}
	if got := testDirScript(nil); got != "" {
		t.Errorf("testDirScript(nil) = %q, want empty", got)
	}
}

// The symlink-target probe must fail for non-links: `readlink` without -f
// errors out, so the whole chain only prints a target for actual symlinks.
func TestReadlinkFollowScript(t *testing.T) {
	got := readlinkFollowScript("/tmp/my link")
	want := "readlink '/tmp/my link' >/dev/null && readlink -f '/tmp/my link'"
	if got != want {
		t.Errorf("readlinkFollowScript = %q, want %q", got, want)
	}
}

func TestParseWslSymDirReply(t *testing.T) {
	paths := []string{"a", "b", "c"}
	got := parseSymDirReply("1 d\n2 f\nnoise\n3 d\n0 d\n99 d\nx\n", paths)
	want := map[string]bool{"a": true, "c": true}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("parseSymDirReply = %v, want %v", got, want)
	}
}

// /mnt Windows-drive mounts are denied through the wsl.localhost share (the
// drive→WSL→drive loopback), so any failure there gets the "use the local
// pane" guidance instead of the raw 9P error.
func TestWSLShareError(t *testing.T) {
	s := &WSLFileSession{distro: "Ubuntu"}
	cases := []struct {
		dir      string
		wantHint bool
	}{
		{"/mnt", true},
		{"/mnt/c", true},
		{"/mnt/c/Users", true},
		{"/home/user", false},
	}
	for _, c := range cases {
		raw := fmt.Errorf("read //wsl.localhost/Ubuntu%s: Incorrect function.", c.dir)
		err := s.shareError(c.dir, raw)
		if c.wantHint && !strings.Contains(err.Error(), "local pane") {
			t.Errorf("shareError(%q) = %q, want local-pane guidance", c.dir, err)
		}
		if !c.wantHint && err != raw {
			t.Errorf("shareError(%q) should pass through raw error, got %q", c.dir, err)
		}
	}
}

// wslTestDistro returns a usable WSL distro for integration tests, skipping
// the test when none is installed (docker-desktop internals don't count).
func wslTestDistro(t *testing.T) string {
	t.Helper()
	out, err := exec.Command("wsl.exe", "-l", "-q").Output()
	if err != nil {
		t.Skipf("wsl.exe not usable: %v", err)
	}
	for _, name := range strings.Split(strings.ReplaceAll(string(out), "\x00", ""), "\n") {
		name = strings.TrimSpace(name)
		if name != "" && !strings.HasPrefix(name, "docker-") {
			return name
		}
	}
	t.Skip("no non-docker WSL distro installed")
	return ""
}

// ChangeRemoteDir must fall back to the link's real target when a directory
// symlink cannot be traversed through the wsl.localhost share (the 9P
// redirector reports the link as a non-dir reparse point).
func TestWSLChangeRemoteDirSymlinkFallback(t *testing.T) {
	distro := wslTestDistro(t)
	wsl := func(script string) {
		t.Helper()
		if out, err := exec.Command("wsl.exe", "-d", distro, "--", "sh", "-c", script).CombinedOutput(); err != nil {
			t.Fatalf("wsl %q: %v: %s", script, err, out)
		}
	}
	dir := fmt.Sprintf("/tmp/terminal-symtest-%d", time.Now().UnixNano())
	wsl(fmt.Sprintf("mkdir -p %s/real && echo hi > %s/real/inside.txt && ln -sfn %s/real %s/dlink", dir, dir, dir, dir))
	defer exec.Command("wsl.exe", "-d", distro, "--", "rm", "-rf", dir).Run()

	s := &WSLFileSession{
		baseSession: baseSession{sessionType: "wsl-file"},
		distro:      distro,
		root:        "//wsl.localhost/" + distro,
		cwd:         dir,
	}
	res, err := s.ChangeRemoteDir("dlink")
	if err != nil {
		t.Fatalf("ChangeRemoteDir(dlink) failed: %v", err)
	}
	if want := dir + "/real"; res.Dir != want {
		t.Errorf("resolved dir = %q, want %q", res.Dir, want)
	}
	found := false
	for _, f := range res.Files {
		if f.Name == "inside.txt" {
			found = true
		}
	}
	if !found {
		t.Errorf("target listing missing inside.txt: %+v", res.Files)
	}
}

// File content operations must follow symlinks to their real targets: the
// wsl.localhost share cannot traverse links, but the target itself is
// reachable, so open/edit/save through a file symlink should just work.
func TestWSLContentThroughFileSymlink(t *testing.T) {
	distro := wslTestDistro(t)
	wsl := func(script string) {
		t.Helper()
		if out, err := exec.Command("wsl.exe", "-d", distro, "--", "sh", "-c", script).CombinedOutput(); err != nil {
			t.Fatalf("wsl %q: %v: %s", script, err, out)
		}
	}
	dir := fmt.Sprintf("/tmp/terminal-symtest-%d", time.Now().UnixNano())
	wsl(fmt.Sprintf("mkdir -p %s && printf hi > %s/real.txt && ln -sf %s/real.txt %s/flink && ln -sf %s/gone.txt %s/dangling",
		dir, dir, dir, dir, dir, dir))
	defer exec.Command("wsl.exe", "-d", distro, "--", "rm", "-rf", dir).Run()

	s := &WSLFileSession{
		baseSession: baseSession{sessionType: "wsl-file"},
		distro:      distro,
		root:        "//wsl.localhost/" + distro,
		cwd:         dir,
	}

	got, err := s.GetContent("flink")
	if err != nil {
		t.Fatalf("GetContent(flink) failed: %v", err)
	}
	if string(got) != "hi" {
		t.Errorf("GetContent(flink) = %q, want %q", got, "hi")
	}

	if err := s.PutContent("flink", []byte("bye")); err != nil {
		t.Fatalf("PutContent(flink) failed: %v", err)
	}
	if got, _ := s.GetContent("real.txt"); string(got) != "bye" {
		t.Errorf("write through symlink missed the target: real.txt = %q, want %q", got, "bye")
	}

	// A dangling link has no target to fall back to — surface a clear error
	// rather than the raw 9P "cannot be resolved" wording.
	if _, err := s.GetContent("dangling"); err == nil {
		t.Error("GetContent(dangling) should fail")
	}
}

// ListRemote must classify symlinks: dir targets are directories (navigable
// via double-click), file targets stay files. Regression: the test -d probe
// silently returned "file" for everything once wsl.exe arg re-quoting
// expanded the script's shell variables to nothing.
func TestWSLListRemoteSymlinkTypes(t *testing.T) {
	distro := wslTestDistro(t)
	wsl := func(script string) {
		t.Helper()
		if out, err := exec.Command("wsl.exe", "-d", distro, "--", "sh", "-c", script).CombinedOutput(); err != nil {
			t.Fatalf("wsl %q: %v: %s", script, err, out)
		}
	}
	dir := fmt.Sprintf("/tmp/terminal-symtest-%d", time.Now().UnixNano())
	wsl(fmt.Sprintf("mkdir -p %s/sub && ln -sfn %s/sub %s/dlink && printf hi > %s/sub/inside.txt && ln -sf %s/sub/inside.txt %s/flink",
		dir, dir, dir, dir, dir, dir))
	defer exec.Command("wsl.exe", "-d", distro, "--", "rm", "-rf", dir).Run()

	s := &WSLFileSession{
		baseSession: baseSession{sessionType: "wsl-file"},
		distro:      distro,
		root:        "//wsl.localhost/" + distro,
		cwd:         dir,
	}
	res, err := s.ListRemote(dir)
	if err != nil {
		t.Fatalf("ListRemote failed: %v", err)
	}
	byName := map[string]FileItem{}
	for _, f := range res.Files {
		byName[f.Name] = f
	}
	dl, ok := byName["dlink"]
	if !ok {
		t.Fatal("dlink missing from listing")
	}
	if !dl.IsDir {
		t.Errorf("dlink should be a directory: mode=%q isDir=%v", dl.Mode, dl.IsDir)
	}
	if !strings.HasPrefix(dl.Mode, "l") {
		t.Errorf("dlink mode should mark a symlink, got %q", dl.Mode)
	}
	fl, ok := byName["flink"]
	if !ok {
		t.Fatal("flink missing from listing")
	}
	if fl.IsDir {
		t.Errorf("flink should not be a directory: mode=%q isDir=%v", fl.Mode, fl.IsDir)
	}
	if !strings.HasPrefix(fl.Mode, "l") {
		t.Errorf("flink mode should mark a symlink, got %q", fl.Mode)
	}
}

// Entering a directory symlink must land on its canonical target and keep
// navigating from there: the 9P redirector can Stat the link itself (following
// the final component) but fails to open any path crossing it ("The directory
// name is invalid"), so cwd must never hold an unresolved link path.
func TestWSLChangeRemoteDirIntoSymlinkThenChild(t *testing.T) {
	distro := wslTestDistro(t)
	wsl := func(script string) {
		t.Helper()
		if out, err := exec.Command("wsl.exe", "-d", distro, "--", "sh", "-c", script).CombinedOutput(); err != nil {
			t.Fatalf("wsl %q: %v: %s", script, err, out)
		}
	}
	dir := fmt.Sprintf("/tmp/terminal-symtest-%d", time.Now().UnixNano())
	// Relative link target on purpose: readlink -f must canonicalize it.
	wsl(fmt.Sprintf("mkdir -p '%s/real/sub' && printf hi > '%s/real/sub/inside.txt' && ln -sfn real '%s/af'", dir, dir, dir))
	defer exec.Command("wsl.exe", "-d", distro, "--", "rm", "-rf", dir).Run()

	s := &WSLFileSession{
		baseSession: baseSession{sessionType: "wsl-file"},
		distro:      distro,
		root:        "//wsl.localhost/" + distro,
		cwd:         dir,
	}
	res, err := s.ChangeRemoteDir("af")
	if err != nil {
		t.Fatalf("ChangeRemoteDir(af) failed: %v", err)
	}
	if want := dir + "/real"; res.Dir != want || s.cwd != want {
		t.Errorf("entering af: dir=%q cwd=%q, want %q", res.Dir, s.cwd, want)
	}
	// The child must be reachable from the canonical cwd (no link mid-path).
	res2, err := s.ChangeRemoteDir("sub")
	if err != nil {
		t.Fatalf("ChangeRemoteDir(sub) failed: %v", err)
	}
	if want := dir + "/real/sub"; res2.Dir != want {
		t.Errorf("child dir = %q, want %q", res2.Dir, want)
	}
	found := false
	for _, f := range res2.Files {
		if f.Name == "inside.txt" {
			found = true
		}
	}
	if !found {
		t.Errorf("listing missing inside.txt: %+v", res2.Files)
	}
}

// A symlink whose target lives on a mounted drive (e.g. a sysroot under
// /mnt/c) must enter the mapped local-drive view: the share itself cannot
// open any path into /mnt, with or without the link on the way.
func TestWSLChangeRemoteDirSymlinkToMntTarget(t *testing.T) {
	distro := wslTestDistro(t)
	tmp := os.TempDir()
	vol := filepath.VolumeName(tmp)
	if len(vol) != 2 || vol[1] != ':' {
		t.Skipf("TempDir %q is not on a drive letter", tmp)
	}
	posixTarget := "/mnt/" + strings.ToLower(vol[:1]) + filepath.ToSlash(tmp[2:]) + fmt.Sprintf("/terminal-mnt-linkto-%d", time.Now().UnixNano())
	localTarget := filepath.FromSlash(posixTarget[len("/mnt/x"):])
	localTarget = vol + `\` + strings.TrimPrefix(localTarget, `\`)
	if err := os.MkdirAll(filepath.Join(localTarget, "sub"), 0o755); err != nil {
		t.Fatalf("MkdirAll: %v", err)
	}
	if err := os.WriteFile(filepath.Join(localTarget, "sub", "inside.txt"), []byte("hi"), 0o644); err != nil {
		t.Fatalf("seed file: %v", err)
	}
	defer os.RemoveAll(localTarget)

	linkDir := fmt.Sprintf("/tmp/terminal-mnt-link-%d", time.Now().UnixNano())
	if out, err := exec.Command("wsl.exe", "-d", distro, "--", "sh", "-c",
		fmt.Sprintf("mkdir -p '%s' && ln -sfn '%s' '%s/af'", linkDir, posixTarget, linkDir)).CombinedOutput(); err != nil {
		t.Fatalf("wsl: %v: %s", err, out)
	}
	defer exec.Command("wsl.exe", "-d", distro, "--", "rm", "-rf", linkDir).Run()

	s := &WSLFileSession{
		baseSession: baseSession{sessionType: "wsl-file"},
		distro:      distro,
		root:        "//wsl.localhost/" + distro,
		cwd:         linkDir,
	}
	res, err := s.ChangeRemoteDir("af")
	if err != nil {
		t.Fatalf("ChangeRemoteDir(af) failed: %v", err)
	}
	if res.Dir != posixTarget || s.cwd != posixTarget {
		t.Errorf("entering af: dir=%q cwd=%q, want %q", res.Dir, s.cwd, posixTarget)
	}
	res2, err := s.ChangeRemoteDir("sub")
	if err != nil {
		t.Fatalf("ChangeRemoteDir(sub) failed: %v", err)
	}
	if want := posixTarget + "/sub"; res2.Dir != want {
		t.Errorf("child dir = %q, want %q", res2.Dir, want)
	}
	found := false
	for _, f := range res2.Files {
		if f.Name == "inside.txt" {
			found = true
		}
	}
	if !found {
		t.Errorf("listing missing inside.txt: %+v", res2.Files)
	}
}

// A cwd that still holds an unresolved link (restored cache / history from an
// older session) must not poison child navigation or content reads: the share
// cannot open any path crossing a link, mid-path included, so change-dir and
// content ops heal the path via `readlink -f` before giving up.
func TestWSLMidPathLinkHealing(t *testing.T) {
	distro := wslTestDistro(t)
	wsl := func(script string) {
		t.Helper()
		if out, err := exec.Command("wsl.exe", "-d", distro, "--", "sh", "-c", script).CombinedOutput(); err != nil {
			t.Fatalf("wsl %q: %v: %s", script, err, out)
		}
	}
	dir := fmt.Sprintf("/tmp/terminal-symtest-%d", time.Now().UnixNano())
	wsl(fmt.Sprintf("mkdir -p '%s/real/lib' && printf hi > '%s/real/lib/inside.txt' && printf yo > '%s/real/notes.txt' && ln -sfn real '%s/af'", dir, dir, dir, dir))
	defer exec.Command("wsl.exe", "-d", distro, "--", "rm", "-rf", dir).Run()

	s := &WSLFileSession{
		baseSession: baseSession{sessionType: "wsl-file"},
		distro:      distro,
		root:        "//wsl.localhost/" + distro,
		cwd:         dir + "/af", // the link path itself, as a stale cwd would be
	}
	// Content reads under the stale link path must heal the same way.
	if b, err := s.GetContent("notes.txt"); err != nil || string(b) != "yo" {
		t.Errorf("GetContent(notes.txt) = %q, %v; want %q", b, err, "yo")
	}
	res, err := s.ChangeRemoteDir("lib")
	if err != nil {
		t.Fatalf("ChangeRemoteDir(lib) failed: %v", err)
	}
	if want := dir + "/real/lib"; res.Dir != want || s.cwd != want {
		t.Errorf("healed dir=%q cwd=%q, want %q", res.Dir, s.cwd, want)
	}
	found := false
	for _, f := range res.Files {
		if f.Name == "inside.txt" {
			found = true
		}
	}
	if !found {
		t.Errorf("listing missing inside.txt: %+v", res.Files)
	}
}

// The wsl.exe invocation that creates a symbolic link inside the distro (the
// wsl.localhost UNC share cannot create Linux links).
func TestWSLSymlinkCmd(t *testing.T) {
	cmd := wslSymlinkCmd("Ubuntu-22.04", "/home/u/target", "/home/u/link")
	want := []string{"wsl.exe", "-d", "Ubuntu-22.04", "--", "ln", "-s", "/home/u/target", "/home/u/link"}
	if !reflect.DeepEqual(cmd.Args, want) {
		t.Errorf("wslSymlinkCmd args = %v, want %v", cmd.Args, want)
	}
}

// /mnt/<drive>/... paths are the local Windows drive reached through WSL, so
// they map to the plain local path when the first segment is a single, existing
// drive letter; anything else (non-drive mounts, missing drives) stays on the
// 9P share path.
func TestWSLMountLocalPath(t *testing.T) {
	absent := ""
	for _, letter := range "ABCDEFGHIJKLMNOPQRSTUVWXYZ" {
		if _, err := os.Stat(string(letter) + `:\`); err != nil {
			absent = string(letter)
			break
		}
	}
	cases := []struct {
		posix string
		want  string
		ok    bool
	}{
		{"/mnt/c", `C:\`, true},
		{"/mnt/C", `C:\`, true},
		{"/mnt/c/Users", `C:\Users`, true},
		{"/mnt", "", false},
		{"/mnt/wsl", "", false},
		{"/mnt/cfoo", "", false},
		{"/home/user", "", false},
	}
	if absent != "" {
		cases = append(cases, struct {
			posix string
			want  string
			ok    bool
		}{"/mnt/" + strings.ToLower(absent), "", false})
	}
	for _, c := range cases {
		got, ok := wslMountLocalPath(c.posix)
		if ok != c.ok || got != c.want {
			t.Errorf("wslMountLocalPath(%q) = %q, %v; want %q, %v", c.posix, got, ok, c.want, c.ok)
		}
	}
}

// ListRemote on /mnt itself is a synthesized view of the local drive letters
// (the 9P share denies the mountpoint), so navigation / -> /mnt -> /mnt/c is
// seamless.
func TestWSLListMntRoot(t *testing.T) {
	s := &WSLFileSession{distro: "Ubuntu"}
	res, err := s.ListRemote("/mnt")
	if err != nil {
		t.Fatalf("ListRemote(/mnt) failed: %v", err)
	}
	if res.Dir != "/mnt" {
		t.Errorf("Dir = %q, want /mnt", res.Dir)
	}
	want := map[string]bool{}
	if drives, err := s.ListLocalDrives(); err == nil {
		for _, d := range drives {
			want[strings.ToLower(d.Name[:1])] = true
		}
	}
	if len(want) == 0 {
		t.Skip("no local drives found")
	}
	got := map[string]bool{}
	for _, f := range res.Files {
		if !f.IsDir {
			t.Errorf("drive entry %q should be a directory: %+v", f.Name, f)
		}
		got[f.Name] = true
	}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("listing = %v, want %v", got, want)
	}
}

// Entering /mnt/c lands on the local drive: the listing matches the real C:\
// contents and the cwd is the POSIX mount path.
func TestWSLChangeRemoteDirMnt(t *testing.T) {
	if _, err := os.Stat(`C:\`); err != nil {
		t.Skip("no C: drive")
	}
	s := &WSLFileSession{distro: "Ubuntu", root: "//wsl.localhost/Ubuntu"}
	res, err := s.ChangeRemoteDir("/mnt/c")
	if err != nil {
		t.Fatalf("ChangeRemoteDir(/mnt/c) failed: %v", err)
	}
	if res.Dir != "/mnt/c" {
		t.Errorf("Dir = %q, want /mnt/c", res.Dir)
	}
	if s.cwd != "/mnt/c" {
		t.Errorf("cwd = %q, want /mnt/c", s.cwd)
	}
	local, err := os.ReadDir(`C:\`)
	if err != nil {
		t.Fatalf("ReadDir(C:\\) failed: %v", err)
	}
	if len(res.Files) != len(local) {
		t.Errorf("listing has %d entries, C:\\ has %d", len(res.Files), len(local))
	}
}

// Content operations under /mnt/<drive> hit the real local file, so editing a
// file seen in the WSL pane edits the Windows copy.
func TestWSLContentMappedMnt(t *testing.T) {
	tmp := os.TempDir()
	vol := filepath.VolumeName(tmp)
	if len(vol) != 2 || vol[1] != ':' {
		t.Skipf("TempDir %q is not on a drive letter", tmp)
	}
	posix := "/mnt/" + strings.ToLower(vol[:1]) + filepath.ToSlash(tmp[2:]) + "/terminal-mnt-test.txt"
	local := filepath.Join(tmp, "terminal-mnt-test.txt")
	defer os.Remove(local)

	if err := os.WriteFile(local, []byte("hi"), 0o644); err != nil {
		t.Fatalf("seed file: %v", err)
	}
	s := &WSLFileSession{distro: "Ubuntu", root: "//wsl.localhost/Ubuntu"}
	got, err := s.GetContent(posix)
	if err != nil {
		t.Fatalf("GetContent(%q) failed: %v", posix, err)
	}
	if string(got) != "hi" {
		t.Errorf("GetContent = %q, want %q", got, "hi")
	}
	if err := s.PutContent(posix, []byte("bye")); err != nil {
		t.Fatalf("PutContent failed: %v", err)
	}
	if b, err := os.ReadFile(local); err != nil || string(b) != "bye" {
		t.Errorf("PutContent missed the local file: %q, %v", b, err)
	}
}

// A download from /mnt/<drive> copies between two local paths and reports the
// POSIX mount path as the task's remote path.
func TestWSLGetMappedMnt(t *testing.T) {
	tmp, err := os.MkdirTemp("", "terminal-mnt-dl-*")
	if err != nil {
		t.Fatalf("MkdirTemp: %v", err)
	}
	defer os.RemoveAll(tmp)
	vol := filepath.VolumeName(tmp)
	if len(vol) != 2 || vol[1] != ':' {
		t.Skipf("temp dir %q is not on a drive letter", tmp)
	}
	posix := "/mnt/" + strings.ToLower(vol[:1]) + filepath.ToSlash(tmp[2:])
	src := filepath.Join(tmp, "in.txt")
	if err := os.WriteFile(src, []byte("payload"), 0o644); err != nil {
		t.Fatalf("seed file: %v", err)
	}

	s := &WSLFileSession{
		baseSession: baseSession{sessionType: "wsl-file"},
		distro:      "Ubuntu",
		root:        "//wsl.localhost/Ubuntu",
		localFSOps:  newLocalFSOps(),
		transfers:   map[string]*TransferTask{},
	}
	dst := filepath.Join(tmp, "out.txt")
	id, err := s.Get(posix+"/in.txt", dst, false)
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	// The task deletes itself on completion; read it right away.
	s.mu.Lock()
	task := s.transfers[id]
	s.mu.Unlock()
	if task == nil || task.RemotePath != posix+"/in.txt" {
		t.Errorf("task RemotePath = %q, want %q", taskRemotePath(task), posix+"/in.txt")
	}
	out := dst
	deadline := time.Now().Add(10 * time.Second)
	for {
		if b, rerr := os.ReadFile(out); rerr == nil {
			if string(b) != "payload" {
				t.Fatalf("copied content = %q, want %q", b, "payload")
			}
			break
		}
		if time.Now().After(deadline) {
			t.Fatalf("copy never produced %s", out)
		}
		time.Sleep(20 * time.Millisecond)
	}
}

func taskRemotePath(t *TransferTask) string {
	if t == nil {
		return ""
	}
	return t.RemotePath
}

// A symlink created inside the distro on a mounted drive is an LX reparse
// point the Windows side cannot resolve, so the mapped-path Stat fails.
// Entering it must fall back to `readlink -f` and continue at the link's real
// target, matching the share-side symlink fallback.
func TestWSLChangeRemoteDirMntSymlinkFallback(t *testing.T) {
	distro := wslTestDistro(t)
	tmp := os.TempDir()
	vol := filepath.VolumeName(tmp)
	if len(vol) != 2 || vol[1] != ':' {
		t.Skipf("TempDir %q is not on a drive letter", tmp)
	}
	posixTmp := "/mnt/" + strings.ToLower(vol[:1]) + filepath.ToSlash(tmp[2:])
	base := fmt.Sprintf("%s/terminal-mnt-sym-%d", posixTmp, time.Now().UnixNano())
	wsl := func(script string) {
		t.Helper()
		if out, err := exec.Command("wsl.exe", "-d", distro, "--", "sh", "-c", script).CombinedOutput(); err != nil {
			t.Fatalf("wsl %q: %v: %s", script, err, out)
		}
	}
	// Relative link target on purpose: readlink -f must canonicalize it.
	wsl(fmt.Sprintf("mkdir -p '%s/real' && printf hi > '%s/real/inside.txt' && ln -s real '%s/dlink'", base, base, base))
	defer os.RemoveAll(filepath.Join(tmp, filepath.Base(base)))

	s := &WSLFileSession{
		baseSession: baseSession{sessionType: "wsl-file"},
		distro:      distro,
		root:        "//wsl.localhost/" + distro,
		cwd:         base,
	}
	res, err := s.ChangeRemoteDir("dlink")
	if err != nil {
		t.Fatalf("ChangeRemoteDir(dlink) failed: %v", err)
	}
	if want := base + "/real"; res.Dir != want {
		t.Errorf("resolved dir = %q, want %q", res.Dir, want)
	}
	found := false
	for _, f := range res.Files {
		if f.Name == "inside.txt" {
			found = true
		}
	}
	if !found {
		t.Errorf("target listing missing inside.txt: %+v", res.Files)
	}
}
