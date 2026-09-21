package sync

import (
	"encoding/base64"
	"os"
	"path/filepath"
	"testing"

	"github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/plumbing/object"
)

// initTestRepo creates a local git repo at repoPath with a single initial commit.
// Returns a GitRepo wrapping the freshly-initialized repo so callers can drive
// StageAndCommit exactly the way SyncService does in production.
func initTestRepo(t *testing.T, repoPath string) *GitRepo {
	t.Helper()
	if err := os.MkdirAll(repoPath, 0755); err != nil {
		t.Fatalf("mkdir repo: %v", err)
	}
	repo, err := git.PlainInit(repoPath, false)
	if err != nil {
		t.Fatalf("git init: %v", err)
	}
	wt, err := repo.Worktree()
	if err != nil {
		t.Fatalf("worktree: %v", err)
	}
	// Seed an empty README so HEAD exists and IsClean() is sane.
	readme := filepath.Join(repoPath, "README.md")
	if err := os.WriteFile(readme, []byte("# test\n"), 0644); err != nil {
		t.Fatalf("write readme: %v", err)
	}
	if _, err := wt.Add("README.md"); err != nil {
		t.Fatalf("add readme: %v", err)
	}
	if _, err := wt.Commit("init", &git.CommitOptions{
		Author: &object.Signature{Name: "test", Email: "t@t"},
	}); err != nil {
		t.Fatalf("commit init: %v", err)
	}
	return &GitRepo{repo: repo, repoPath: repoPath}
}

// TestStageAndCommitWhitelist verifies SYNC-P1-9: StageAndCommit only stages
// the synced config files (syncedFiles, shared with encrypt/decrypt/compare)
// plus the repo metadata files .sync-salt and README.md — never wt.Add(".").
// A stray file representing an SSH key (id_rsa) dropped into the sync dir
// must NOT be committed plaintext.
//
// tunnels.json is an explicit regression guard: it was missing from the old
// hand-written commit whitelist, so tunnel changes were encrypted into the
// repo but never committed or synced.
func TestStageAndCommitWhitelist(t *testing.T) {
	repoPath := t.TempDir()
	g := initTestRepo(t, repoPath)

	// Whitelisted files — should be staged. The list mirrors the
	// exact names StageAndCommit iterates over.
	whitelisted := map[string]string{
		".sync-salt": base64.StdEncoding.EncodeToString([]byte("0123456789abcdef")),
		"README.md":  "# sync repo\n",
	}
	for _, name := range syncedFiles {
		whitelisted[name] = "{}"
	}
	for name, content := range whitelisted {
		if err := os.WriteFile(filepath.Join(repoPath, name), []byte(content), 0600); err != nil {
			t.Fatalf("write %s: %v", name, err)
		}
	}

	// Stray files — must NOT be staged. Models an attacker dropping
	// ~/.ssh/id_rsa into the sync directory, plus the local-only store
	// files that must never ride along into the sync repo.
	stray := map[string]string{
		"id_rsa":           "-----BEGIN RSA PRIVATE KEY-----\nMOCK\n-----END RSA PRIVATE KEY-----",
		"secret.txt":       "internal passwords",
		"notes.md":         "echo pwned",
		"backup.tgz":       "binary",
		"ai-sessions.json": `[]`,
		"skills.json":      `[]`,
	}
	for name, content := range stray {
		if err := os.WriteFile(filepath.Join(repoPath, name), []byte(content), 0600); err != nil {
			t.Fatalf("write %s: %v", name, err)
		}
	}

	committed, err := g.StageAndCommit("test whitelist")
	if err != nil {
		t.Fatalf("StageAndCommit: %v", err)
	}
	if !committed {
		t.Fatalf("expected commit=true (whitelisted files present)")
	}

	wt, err := g.repo.Worktree()
	if err != nil {
		t.Fatalf("worktree: %v", err)
	}
	// Stray files MUST stay untracked — never appear in the index with a
	// staged/modified/deleted code. The whitelist leaves them on disk; we
	// only need to prove they did not get staged.
	status, err := wt.Status()
	if err != nil {
		t.Fatalf("status: %v", err)
	}
	for strayName := range stray {
		if fileStatus, ok := status[strayName]; ok && fileStatus.Worktree != git.Untracked {
			t.Errorf("stray file %s reached worktree status %q — must remain Untracked", strayName, fileStatus.Worktree)
		}
	}

	// Walk the latest commit's tree and assert the stray files are absent.
	head, err := g.repo.Head()
	if err != nil {
		t.Fatalf("head: %v", err)
	}
	commit, err := g.repo.CommitObject(head.Hash())
	if err != nil {
		t.Fatalf("commit object: %v", err)
	}
	tree, err := commit.Tree()
	if err != nil {
		t.Fatalf("tree: %v", err)
	}
	for strayName := range stray {
		if _, err := tree.File(strayName); err == nil {
			t.Errorf("stray file %s was committed plaintext — SYNC-P1-9 regression", strayName)
		}
	}
	for wantName := range whitelisted {
		if _, err := tree.File(wantName); err != nil {
			t.Errorf("whitelisted file %s missing from commit", wantName)
		}
	}
}

// TestStageAndCommitIgnoresUnknownDirEntries — even nested junk under the
// repo path must not be staged. Defends against a future maintainer who
// might try to widen the whitelist by accident.
func TestStageAndCommitIgnoresUnknownDirEntries(t *testing.T) {
	repoPath := t.TempDir()
	g := initTestRepo(t, repoPath)

	subdir := filepath.Join(repoPath, "subdir")
	if err := os.MkdirAll(subdir, 0755); err != nil {
		t.Fatalf("mkdir subdir: %v", err)
	}
	if err := os.WriteFile(filepath.Join(subdir, "evil.pem"), []byte("PEM"), 0600); err != nil {
		t.Fatalf("write evil: %v", err)
	}
	if err := os.WriteFile(filepath.Join(repoPath, "connections.json"), []byte(`{"c":[]}`), 0600); err != nil {
		t.Fatalf("write conn: %v", err)
	}

	committed, err := g.StageAndCommit("narrow whitelist")
	if err != nil {
		t.Fatalf("StageAndCommit: %v", err)
	}
	if !committed {
		t.Fatalf("expected commit=true")
	}

	head, err := g.repo.Head()
	if err != nil {
		t.Fatalf("head: %v", err)
	}
	commit, err := g.repo.CommitObject(head.Hash())
	if err != nil {
		t.Fatalf("commit: %v", err)
	}
	tree, err := commit.Tree()
	if err != nil {
		t.Fatalf("tree: %v", err)
	}
	if _, err := tree.File("subdir/evil.pem"); err == nil {
		t.Errorf("nested stray file subdir/evil.pem was committed — whitelist is too wide")
	}
}