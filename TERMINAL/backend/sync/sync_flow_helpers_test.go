package sync

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/config"
	"github.com/go-git/go-git/v5/plumbing"
	"github.com/zalando/go-keyring"
)

// initLocalRepoWithBareRemote stands up a normal git repo at repoPath, plus a
// bare repo at remotePath used as the "origin". Returns a SyncService whose
// config.RepoURL points at the bare repo via file:// so CloneOrOpen succeeds
// without touching the network and Push has somewhere to land.
func initLocalRepoWithBareRemote(t *testing.T) (*SyncService, string) {
	t.Helper()
	keyring.MockInit()

	configDir := t.TempDir()
	repoPath := filepath.Join(configDir, "sync-repo")
	remotePath := filepath.Join(configDir, "remote.git")
	if err := os.MkdirAll(repoPath, 0755); err != nil {
		t.Fatalf("mkdir repo: %v", err)
	}
	if err := os.MkdirAll(remotePath, 0755); err != nil {
		t.Fatalf("mkdir remote: %v", err)
	}

	bare, err := git.PlainInit(remotePath, true)
	if err != nil {
		t.Fatalf("init bare: %v", err)
	}
	// Align both HEADs with config.Branch ("main") — PlainInit defaults to
	// master, which would desync every branch reference in the flow tests.
	if err := bare.Storer.SetReference(
		plumbing.NewSymbolicReference(plumbing.HEAD, plumbing.NewBranchReferenceName("main")),
	); err != nil {
		t.Fatalf("set bare HEAD: %v", err)
	}

	work, err := git.PlainInit(repoPath, false)
	if err != nil {
		t.Fatalf("init work: %v", err)
	}
	if err := work.Storer.SetReference(
		plumbing.NewSymbolicReference(plumbing.HEAD, plumbing.NewBranchReferenceName("main")),
	); err != nil {
		t.Fatalf("set work HEAD: %v", err)
	}
	if _, err := work.CreateRemote(&config.RemoteConfig{
		Name: "origin",
		URLs: []string{remotePath},
		Fetch: []config.RefSpec{
			config.RefSpec("+refs/heads/*:refs/remotes/origin/*"),
		},
	}); err != nil {
		t.Fatalf("create remote: %v", err)
	}

	s := &SyncService{
		configDir:   configDir,
		repoPath:    repoPath,
		keychain:    NewKeychain(),
		configStore: NewSyncConfigStore(configDir),
		ready:       make(chan struct{}),
	}
	close(s.ready)
	cfg := SyncConfig{
		RepoURL:  remotePath,
		Branch:   "main",
		Username: "u",
	}
	if err := s.configStore.Save(cfg); err != nil {
		t.Fatalf("save config: %v", err)
	}
	return s, repoPath
}
