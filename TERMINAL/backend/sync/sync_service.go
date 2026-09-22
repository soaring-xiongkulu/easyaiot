package sync

import (
	"bytes"
	"context"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"easyaiot/terminal/backend/utils"
	"github.com/go-git/go-git/v5/plumbing"
	ggittransport "github.com/go-git/go-git/v5/plumbing/transport"
)

var ErrWrongSyncPassword = errors.New("WRONG_SYNC_PASSWORD")

type SyncService struct {
	// configDir holds sync *metadata* — sync-config.json and the local
	// sync-repo clone. It is fixed to the OS user-config dir and is
	// independent of the migratable data directory.
	configDir string
	// dataDir is the resolved config data directory whose config files
	// (connections.json, …) are encrypted to / decrypted
	// from the sync repo.
	dataDir     string
	repoPath    string
	keychain    *Keychain
	configStore *SyncConfigStore
	// passwordStore normalizes in-place encrypted fields (enc:v1:) to plaintext
	// on upload and back to enc:v1: on download. It is the credential store,
	// wired in after startup. nil until set; sync degrades to carrying fields
	// through opaque (best-effort) when it is absent.
	passwordStore PasswordStore
	mu            sync.Mutex

	// ready is closed by NewSyncService() once the disk-touching
	// init (UserConfigDir → MkdirAll → NewKeychain → NewSyncConfigStore)
	// has finished. Callers that arrive during the brief startup window
	// can wait on Ready() with a short timeout (F-407).
	ready     chan struct{}
	readyOnce sync.Once
}

type SyncResult struct {
	Direction SyncDirection `json:"direction"`
	Message   string        `json:"message"`
	Conflict  *ConflictInfo `json:"conflict,omitempty"`
}

type ConflictInfo struct {
	LocalTime  time.Time `json:"localTime"`
	RemoteTime time.Time `json:"remoteTime"`
}

func NewSyncService(dataDir string) (*SyncService, error) {
	cfgDir, err := os.UserConfigDir()
	if err != nil {
		return nil, err
	}
	metaDir := filepath.Join(cfgDir, "Terminal")
	if err := os.MkdirAll(metaDir, 0755); err != nil {
		return nil, err
	}

	s := &SyncService{
		configDir:   metaDir,
		dataDir:     dataDir,
		repoPath:    filepath.Join(metaDir, "sync-repo"),
		keychain:    NewKeychain(),
		configStore: NewSyncConfigStore(metaDir),
		ready:       make(chan struct{}),
	}
	s.readyOnce.Do(func() { close(s.ready) })
	return s, nil
}

// NewSyncServiceAsync returns a SyncService whose disk-touching init
// (UserConfigDir / MkdirAll / NewKeychain) runs on a background
// goroutine. F-407: macOS Security framework keychain IPC + the
// PBKDF2 600k iterations probe can take 50–500ms+ on first launch —
// doing it synchronously inside wails.OnStartup blocks the first
// paint of the main window.
//
// Callers should `Ready()` (with a short timeout) before invoking
// service methods; otherwise methods may fail with
// ErrSyncNotInitialized until init completes.
func NewSyncServiceAsync(dataDir string) (*SyncService, context.Context) {
	s := &SyncService{ready: make(chan struct{})}
	initDone, cancel := context.WithCancel(context.Background())
	go func() {
		defer s.readyOnce.Do(func() { close(s.ready) })
		cfg, err := os.UserConfigDir()
		if err != nil {
			return
		}
		metaDir := filepath.Join(cfg, "Terminal")
		if err := os.MkdirAll(metaDir, 0755); err != nil {
			return
		}
		s.configDir = metaDir
		s.dataDir = dataDir
		s.repoPath = filepath.Join(metaDir, "sync-repo")
		s.keychain = NewKeychain()
		s.configStore = NewSyncConfigStore(metaDir)
		cancel()
	}()
	return s, initDone
}

// Ready returns a channel closed once init has finished. Pair with
// a short timeout in callers that race startup (F-407).
func (s *SyncService) Ready() <-chan struct{} {
	return s.ready
}

// SetPasswordStore wires the credential store so sync can normalize enc:v1:
// fields to plaintext on upload and back on download.
func (s *SyncService) SetPasswordStore(ps PasswordStore) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.passwordStore = ps
}

// requireUnlocked refuses sync when the credential store is wired but locked.
// A nil store means no credential store was wired (test-only path) and is not
// an error; production always wires it via SetPasswordStore. Callers must hold
// s.mu.
func (s *SyncService) requireUnlocked() error {
	if s.passwordStore == nil {
		return nil
	}
	if !s.passwordStore.Unlocked() {
		return utils.UserErr("vault_locked")
	}
	return nil
}

// GetConfig returns the current sync configuration.
func (s *SyncService) GetConfig() (SyncConfig, error) {
	return s.configStore.Load()
}

// SaveConfig persists sync configuration and stores the token if provided.
func (s *SyncService) SaveConfig(config SyncConfig, token string) error {
	if token != "" {
		if err := s.keychain.SetGitToken(token); err != nil {
			return fmt.Errorf("store token: %w", err)
		}
	}
	return s.configStore.Save(config)
}

func (s *SyncService) getToken() string {
	token, _ := s.keychain.GetGitToken()
	return token
}

// Sync runs a full sync cycle: clone/open → fetch → three-way content
// analysis → commit/pull/push → decrypt.
//
// The remote state is fetched BEFORE anything is committed locally: the
// old commit-then-fetch order turned "not pulled yet" into a local commit
// on a stale head, so two machines used alternately diverged and hit the
// conflict dialog on every open. Content is then analyzed three-way
// (local data dir vs merge base vs remote head) so that "merely out of
// date" is a silent pull and only a genuine both-sides edit surfaces the
// conflict dialog.
func (s *SyncService) Sync() (*SyncResult, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if err := s.requireUnlocked(); err != nil {
		return nil, err
	}

	config, err := s.configStore.Load()
	if err != nil {
		return nil, fmt.Errorf("load config: %w", err)
	}
	if config.RepoURL == "" {
		return nil, fmt.Errorf("sync not configured: repo URL not set")
	}

	encKey, err := s.keychain.GetEncryptionKey()
	if err != nil {
		return nil, fmt.Errorf("encryption key: %w", err)
	}

	username := config.Username
	token := s.getToken()

	// 1. Clone or open repo.
	repo, err := CloneOrOpen(s.repoPath, config.RepoURL, config.Branch, username, token)
	if err != nil {
		s.updateLastSyncResult("failed", fmt.Sprintf("open repo: %v", err))
		return nil, fmt.Errorf("open repo: %w", err)
	}

	// SYNC-P1-11: a key that cannot open the existing ciphertext (wrong
	// master password, corrupted blob) must abort the sync before any
	// locally-derived ciphertext can be pushed over the only good copy.
	if repoHasFiles(s.repoPath) {
		if err := verifyDecryption(s.repoPath, encKey); err != nil {
			s.updateLastSyncResult("password_mismatch", err.Error())
			return nil, err
		}
	}

	// 2. Fetch on a truly empty remote returns ErrEmptyRemoteRepository —
	// treat as "remote has no branch yet", not as an error.
	if err := repo.Fetch(username, token); err != nil {
		if !errors.Is(err, ggittransport.ErrEmptyRemoteRepository) {
			s.updateLastSyncResult("failed", fmt.Sprintf("fetch: %v", err))
			return nil, fmt.Errorf("fetch: %w", err)
		}
	}

	heads, err := repo.ResolveBranchHeads(config.Branch)
	if err != nil {
		s.updateLastSyncResult("failed", fmt.Sprintf("resolve heads: %v", err))
		return nil, fmt.Errorf("resolve heads: %w", err)
	}

	// 3. Bootstrap cases.
	if heads.Local == nil && heads.Remote == nil {
		// Nothing anywhere: publish the local config as the initial commit.
		return s.pushLocalConfig(repo, encKey, username, token)
	}
	if heads.Local == nil {
		// Fresh local repo — adopt the remote silently.
		if err := repo.ResetToRemote(config.Branch); err != nil {
			s.updateLastSyncResult("failed", fmt.Sprintf("reset: %v", err))
			return nil, fmt.Errorf("reset: %w", err)
		}
		if err := DecryptConfigFiles(s.repoPath, s.dataDir, encKey, s.passwordStore); err != nil {
			s.updateLastSyncResult("failed", fmt.Sprintf("decrypt files: %v", err))
			return nil, fmt.Errorf("decrypt files: %w", err)
		}
		s.updateLastSyncResult("success", "")
		return &SyncResult{Direction: SyncPull, Message: "配置已下载"}, nil
	}
	if heads.Remote == nil {
		// The remote branch does not exist (wiped or force-emptied) —
		// re-publish the local config on top of it.
		return s.pushLocalConfig(repo, encKey, username, token)
	}

	// 4. Heads in sync — only local data drift can require a push.
	if *heads.Local == *heads.Remote {
		same, err := s.dataMatchesCommit(repo, encKey, *heads.Local)
		if err != nil {
			s.updateLastSyncResult("failed", err.Error())
			return nil, err
		}
		if same {
			s.updateLastSyncResult("success", "")
			return &SyncResult{Message: "已是最新"}, nil
		}
		return s.pushLocalConfig(repo, encKey, username, token)
	}

	// 5. Heads diverged or fast-forwardable — three-way content analysis
	// against the merge base, so "only the remote moved" is a silent pull
	// and only a genuine both-sides edit surfaces the conflict dialog.
	base, err := repo.MergeBase(*heads.Local, *heads.Remote)
	if err != nil {
		s.updateLastSyncResult("failed", fmt.Sprintf("merge base: %v", err))
		return nil, fmt.Errorf("merge base: %w", err)
	}

	baseDir, cleanupBase, err := s.decryptCommitToDir(repo, encKey, base)
	if err != nil {
		s.updateLastSyncResult("failed", err.Error())
		return nil, err
	}
	defer cleanupBase()
	remoteDir, cleanupRemote, err := s.decryptCommitToDir(repo, encKey, heads.Remote)
	if err != nil {
		s.updateLastSyncResult("failed", err.Error())
		return nil, err
	}
	defer cleanupRemote()

	localChanged, err := dirsDiffer(s.dataDir, baseDir, s.keychain, s.passwordStore)
	if err != nil {
		s.updateLastSyncResult("failed", err.Error())
		return nil, err
	}
	remoteChanged, err := dirsDiffer(remoteDir, baseDir, nil, nil)
	if err != nil {
		s.updateLastSyncResult("failed", err.Error())
		return nil, err
	}

	switch {
	case !localChanged && !remoteChanged:
		// Content identical on both sides, heads diverged anyway (e.g.
		// re-encrypt noise from older builds) — heal the history
		// silently; no data changes.
		if err := repo.ResetToRemote(config.Branch); err != nil {
			s.updateLastSyncResult("failed", fmt.Sprintf("reset: %v", err))
			return nil, fmt.Errorf("reset: %w", err)
		}
		s.updateLastSyncResult("success", "")
		return &SyncResult{Message: "已是最新"}, nil

	case localChanged && !remoteChanged:
		// Only the local content is newer. Re-anchor the clone on the
		// remote head and publish the local content as one commit on top
		// of it, so the push is a fast-forward (any unpushed local
		// commits are squashed — they were never shared).
		if err := repo.ResetToRemote(config.Branch); err != nil {
			s.updateLastSyncResult("failed", fmt.Sprintf("reset: %v", err))
			return nil, fmt.Errorf("reset: %w", err)
		}
		return s.pushLocalConfig(repo, encKey, username, token)

	case !localChanged && remoteChanged:
		// Only the remote moved — silent pull.
		if err := repo.ResetToRemote(config.Branch); err != nil {
			s.updateLastSyncResult("failed", fmt.Sprintf("reset: %v", err))
			return nil, fmt.Errorf("reset: %w", err)
		}
		if err := DecryptConfigFiles(s.repoPath, s.dataDir, encKey, s.passwordStore); err != nil {
			s.updateLastSyncResult("failed", fmt.Sprintf("decrypt files: %v", err))
			return nil, fmt.Errorf("decrypt files: %w", err)
		}
		s.updateLastSyncResult("success", "")
		return &SyncResult{Direction: SyncPull, Message: "配置已下载"}, nil

	default:
		// Both sides changed content since the merge base — a genuine
		// conflict; let the user pick a direction.
		localTime, err := repo.CommitTime(*heads.Local)
		if err != nil {
			s.updateLastSyncResult("failed", err.Error())
			return nil, err
		}
		remoteTime, err := repo.CommitTime(*heads.Remote)
		if err != nil {
			s.updateLastSyncResult("failed", err.Error())
			return nil, err
		}
		s.updateLastSyncResult("conflict", "")
		return &SyncResult{
			Direction: SyncConflict,
			Conflict: &ConflictInfo{
				LocalTime:  localTime,
				RemoteTime: remoteTime,
			},
		}, nil
	}
}

// pushLocalConfig encrypts the local config into the repo, commits it on
// top of the current HEAD and pushes.
func (s *SyncService) pushLocalConfig(repo *GitRepo, encKey []byte, username, token string) (*SyncResult, error) {
	if err := EncryptConfigFiles(s.dataDir, s.repoPath, encKey, s.keychain, s.passwordStore); err != nil {
		s.updateLastSyncResult("failed", fmt.Sprintf("encrypt files: %v", err))
		return nil, fmt.Errorf("encrypt files: %w", err)
	}
	if _, err := repo.StageAndCommit(commitMsg("Terminal config sync")); err != nil {
		s.updateLastSyncResult("failed", fmt.Sprintf("commit: %v", err))
		return nil, fmt.Errorf("commit: %w", err)
	}
	if err := repo.Push(username, token); err != nil {
		s.updateLastSyncResult("failed", fmt.Sprintf("push: %v", err))
		return nil, fmt.Errorf("push: %w", err)
	}
	s.updateLastSyncResult("success", "")
	return &SyncResult{Direction: SyncPush, Message: "配置已上传"}, nil
}

// dataMatchesCommit compares the local config dir with the config as
// committed at hash. A decrypt error is surfaced, not swallowed
// (SYNC-P1-11).
func (s *SyncService) dataMatchesCommit(repo *GitRepo, encKey []byte, hash plumbing.Hash) (bool, error) {
	dir, cleanup, err := s.decryptCommitToDir(repo, encKey, &hash)
	if err != nil {
		return false, err
	}
	defer cleanup()
	same, err := compareConfigDirs(s.dataDir, dir, s.keychain, s.passwordStore)
	if err != nil {
		return false, err
	}
	return same, nil
}

// decryptCommitToDir extracts the synced files as committed at hash and
// decrypts them into a fresh temp dir. A nil hash yields an empty dir
// (nothing committed at that side). The caller owns cleanup via the
// returned function.
func (s *SyncService) decryptCommitToDir(repo *GitRepo, encKey []byte, hash *plumbing.Hash) (string, func(), error) {
	cipherDir, err := os.MkdirTemp("", "sync-cipher-")
	if err != nil {
		return "", nil, err
	}
	plainDir, err := os.MkdirTemp("", "sync-plain-")
	if err != nil {
		os.RemoveAll(cipherDir)
		return "", nil, err
	}
	cleanup := func() {
		os.RemoveAll(cipherDir)
		os.RemoveAll(plainDir)
	}
	if hash != nil {
		if err := repo.ExtractCommitFiles(*hash, cipherDir); err != nil {
			cleanup()
			return "", nil, err
		}
		if err := DecryptConfigFiles(cipherDir, plainDir, encKey, nil); err != nil {
			cleanup()
			return "", nil, fmt.Errorf("decrypt commit: %w", err)
		}
	}
	return plainDir, cleanup, nil
}

// dirsDiffer reports whether the two decrypted config directories differ.
func dirsDiffer(a, b string, kc *Keychain, ps PasswordStore) (bool, error) {
	same, err := compareConfigDirs(a, b, kc, ps)
	if err != nil {
		return false, err
	}
	return !same, nil
}

// ResolveConflict handles a conflict by forcing push or reset.
func (s *SyncService) ResolveConflict(useLocal bool) (*SyncResult, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if err := s.requireUnlocked(); err != nil {
		return nil, err
	}

	config, err := s.configStore.Load()
	if err != nil {
		return nil, fmt.Errorf("load config: %w", err)
	}
	username := config.Username
	token := s.getToken()

	repo, err := CloneOrOpen(s.repoPath, config.RepoURL, config.Branch, username, token)
	if err != nil {
		return nil, fmt.Errorf("open repo: %w", err)
	}

	encKey, err := s.keychain.GetEncryptionKey()
	if err != nil {
		return nil, fmt.Errorf("encryption key: %w", err)
	}

	// SYNC-P1-11: same guard as Sync — a key that cannot open the
	// existing ciphertext must abort before anything is pushed.
	if repoHasFiles(s.repoPath) {
		if err := verifyDecryption(s.repoPath, encKey); err != nil {
			s.updateLastSyncResult("password_mismatch", err.Error())
			return nil, err
		}
	}

	// Learn the remote state first — same ordering rule as Sync.
	if err := repo.Fetch(username, token); err != nil {
		if !errors.Is(err, ggittransport.ErrEmptyRemoteRepository) {
			return nil, fmt.Errorf("fetch: %w", err)
		}
	}
	heads, err := repo.ResolveBranchHeads(config.Branch)
	if err != nil {
		return nil, fmt.Errorf("resolve heads: %w", err)
	}

	if useLocal {
		// Re-anchor the clone on the remote head and publish the local
		// content as one commit on top of it. The push is then a
		// fast-forward — force-pushing here orphaned the other machines'
		// heads and made them conflict again on their next open, creating
		// an endless resolve-conflict ping-pong.
		if heads.Remote != nil {
			if err := repo.ResetToRemote(config.Branch); err != nil {
				return nil, fmt.Errorf("reset: %w", err)
			}
		}
		if err := EncryptConfigFiles(s.dataDir, s.repoPath, encKey, s.keychain, s.passwordStore); err != nil {
			return nil, fmt.Errorf("encrypt files: %w", err)
		}
		if _, err := repo.StageAndCommit(commitMsg("Terminal config sync (resolve conflict)")); err != nil {
			return nil, fmt.Errorf("commit: %w", err)
		}
		if err := repo.Push(username, token); err != nil {
			return nil, fmt.Errorf("push: %w", err)
		}
		s.updateLastSyncResult("success", "")
		return &SyncResult{Direction: SyncPush, Message: "已用本地配置覆盖远端"}, nil
	}

	if heads.Remote != nil {
		if err := repo.ResetToRemote(config.Branch); err != nil {
			return nil, fmt.Errorf("reset: %w", err)
		}
	}
	if err := DecryptConfigFiles(s.repoPath, s.dataDir, encKey, s.passwordStore); err != nil {
		return nil, fmt.Errorf("decrypt files: %w", err)
	}

	s.updateLastSyncResult("success", "")
	return &SyncResult{Direction: SyncPull, Message: "已用远端配置覆盖本地"}, nil
}

// TestConnection verifies the repo is reachable with stored credentials.
func (s *SyncService) TestConnection() error {
	config, err := s.configStore.Load()
	if err != nil {
		return fmt.Errorf("load config: %w", err)
	}
	if config.RepoURL == "" {
		return utils.UserErr("repo_not_configured")
	}
	username := config.Username
	token := s.getToken()
	return TestConnection(config.RepoURL, username, token)
}

func (s *SyncService) updateLastSyncResult(status string, errMsg string) {
	config, _ := s.configStore.Load()
	config.LastSyncAt = time.Now()
	config.LastSyncStatus = status
	config.LastSyncError = errMsg
	_ = s.configStore.Save(config)
}

// IsAutoSyncEnabled returns whether auto sync is enabled and configured.
func (s *SyncService) IsAutoSyncEnabled() bool {
	config, _ := s.configStore.Load()
	return config.AutoSync && config.RepoURL != ""
}

// RepoPath returns the local git repo path.
func (s *SyncService) RepoPath() string {
	return s.repoPath
}

// PasswordStore returns the keychain as a PasswordStore for connection store integration.
func (s *SyncService) PasswordStore() *Keychain {
	return s.keychain
}

// ConfigureRepo sets up a new or existing sync repository.
func (s *SyncService) ConfigureRepo(repoURL, username, token, masterPassword string) (*SyncResult, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if err := s.requireUnlocked(); err != nil {
		return nil, err
	}

	repo, err := CloneOrOpen(s.repoPath, repoURL, "main", username, token)
	if err != nil {
		return nil, fmt.Errorf("clone/open repo: %w", err)
	}

	// Check if remote has .sync-salt
	salt, err := ReadSaltFile(s.repoPath)
	if err != nil {
		return nil, fmt.Errorf("read salt: %w", err)
	}

	var encKey []byte
	if salt != nil {
		// Existing repo: verify password, then compare remote vs local
		encKey = DeriveKey(masterPassword, salt)
		if err := verifyDecryption(s.repoPath, encKey); err != nil {
			return nil, utils.UserErr("master_password_mismatch")
		}

		if err := s.keychain.StoreEncryptionKey(encKey); err != nil {
			return nil, fmt.Errorf("store encryption key: %w", err)
		}

		// Decrypt remote to temp dir for comparison
		tmpDir, err := os.MkdirTemp("", "sync-compare")
		if err != nil {
			return nil, fmt.Errorf("create temp dir: %w", err)
		}
		defer os.RemoveAll(tmpDir)

		if err := DecryptConfigFiles(s.repoPath, tmpDir, encKey, nil); err != nil {
			return nil, fmt.Errorf("decrypt remote for comparison: %w", err)
		}

		localEmpty := isConfigDirEmpty(s.dataDir)
		remoteEmpty := isConfigDirEmpty(tmpDir)

		if localEmpty {
			// Local has no config — pull remote to local
			if err := DecryptConfigFiles(s.repoPath, s.dataDir, encKey, s.passwordStore); err != nil {
				return nil, fmt.Errorf("decrypt files: %w", err)
			}
			cfg := SyncConfig{
				RepoURL:  repoURL,
				Branch:   "main",
				Username: username,
			}
			if token != "" {
				_ = s.keychain.SetGitToken(token)
			}
			_ = s.configStore.Save(cfg)
			s.updateLastSyncResult("success", "")
			return &SyncResult{Direction: SyncPull, Message: "仓库配置成功，已从远端同步配置"}, nil
		}
		if !remoteEmpty {
			// Both have data — compare
			same, err := compareConfigDirs(s.dataDir, tmpDir, s.keychain, s.passwordStore)
			if err != nil {
				return nil, fmt.Errorf("compare configs: %w", err)
			}
			if !same {
				cfg := SyncConfig{
					RepoURL:  repoURL,
					Branch:   "main",
					Username: username,
				}
				if token != "" {
					_ = s.keychain.SetGitToken(token)
				}
				_ = s.configStore.Save(cfg)
				localTime := getConfigModTime(s.dataDir)
				remoteTime := getConfigModTime(tmpDir)
				s.updateLastSyncResult("conflict", "")
				return &SyncResult{
					Direction: SyncConflict,
					Message:   "本地和远端配置不一致，请选择覆盖方向",
					Conflict: &ConflictInfo{
						LocalTime:  localTime,
						RemoteTime: remoteTime,
					},
				}, nil
			}
			// Same — save config then return, no need to re-encrypt/push
			cfg := SyncConfig{
				RepoURL:  repoURL,
				Branch:   "main",
				Username: username,
			}
			if token != "" {
				_ = s.keychain.SetGitToken(token)
			}
			_ = s.configStore.Save(cfg)
			if err := DecryptConfigFiles(s.repoPath, s.dataDir, encKey, s.passwordStore); err != nil {
				return nil, fmt.Errorf("decrypt files: %w", err)
			}
			s.updateLastSyncResult("success", "")
			return &SyncResult{Message: "仓库配置成功"}, nil
		}
		// Remote is empty — fall through to encrypt and push below
	} else {
		// New repo: generate salt, derive key
		salt, err = GenerateSalt()
		if err != nil {
			return nil, fmt.Errorf("generate salt: %w", err)
		}
		encKey = DeriveKey(masterPassword, salt)
		if err := WriteSaltFile(s.repoPath, salt); err != nil {
			return nil, fmt.Errorf("write salt: %w", err)
		}

		if err := s.keychain.StoreEncryptionKey(encKey); err != nil {
			return nil, fmt.Errorf("store encryption key: %w", err)
		}
	}

	// Encrypt and push local config
	if err := EncryptConfigFiles(s.dataDir, s.repoPath, encKey, s.keychain, s.passwordStore); err != nil {
		return nil, fmt.Errorf("encrypt files: %w", err)
	}

	if _, err := repo.StageAndCommit(commitMsg("Terminal config sync")); err != nil {
		return nil, fmt.Errorf("commit: %w", err)
	}

	if err := repo.PushToBranch("main", username, token); err != nil {
		// Pull first then push
		if pullErr := repo.Pull(username, token); pullErr == nil {
			if pushErr := repo.PushToBranch("main", username, token); pushErr != nil {
				return nil, fmt.Errorf("push: %w", pushErr)
			}
		} else {
			return nil, fmt.Errorf("push: %w", err)
		}
	}

	cfg := SyncConfig{
		RepoURL:  repoURL,
		Branch:   "main",
		Username: username,
	}
	if token != "" {
		if err := s.keychain.SetGitToken(token); err != nil {
			return nil, fmt.Errorf("store token: %w", err)
		}
	}
	if err := s.configStore.Save(cfg); err != nil {
		return nil, fmt.Errorf("save config: %w", err)
	}

	// Decrypt remote files to local
	if err := DecryptConfigFiles(s.repoPath, s.dataDir, encKey, s.passwordStore); err != nil {
		return nil, fmt.Errorf("decrypt files: %w", err)
	}

	s.updateLastSyncResult("success", "")
	return &SyncResult{Direction: SyncPush, Message: "仓库配置成功"}, nil
}

// getConfigModTime returns the latest modification time of config files in a directory.
func getConfigModTime(dir string) time.Time {
	var latest time.Time
	for _, name := range []string{"connections.json", "settings.json", "quickCommands.json", "tunnels.json", "identities.json", "proxies.json"} {
		info, err := os.Stat(filepath.Join(dir, name))
		if err != nil {
			continue
		}
		if info.ModTime().After(latest) {
			latest = info.ModTime()
		}
	}
	return latest
}

// isConfigDirEmpty returns true if the config dir has no meaningful data.
// Counts every synced JSON — not only connections — so a user with settings
// / quick-commands but no connections is not treated as "empty" and silently
// overwritten on first sync (SYNC-P0-1). Uses syncedFiles rather than every
// persisted JSON. favorites.json is an array file: only a non-empty array
// counts as data.
func isConfigDirEmpty(dir string) bool {
	for _, name := range syncedFiles {
		v, err := readJSONValue(filepath.Join(dir, name))
		if err != nil {
			// Unparseable or unreadable — treat as non-empty so the
			// user's data is never silently nuked.
			return false
		}
		if v != nil {
			return false
		}
	}
	return true
}

// compareConfigDirs compares two decrypted config directories.
// localDir is the local config directory; remoteDir is the decrypted remote copy.
// Legacy empty passwords are backfilled from keychain and enc:v1: fields are
// normalized to plaintext on the local side before comparison so both sides
// are comparable.
func compareConfigDirs(localDir, remoteDir string, kc *Keychain, ps PasswordStore) (bool, error) {
	for _, name := range syncedFiles {
		same, err := compareConfigFiles(filepath.Join(localDir, name), filepath.Join(remoteDir, name), kc, ps)
		if err != nil {
			return false, err
		}
		if !same {
			return false, nil
		}
	}
	return true, nil
}

// readJSONValue decodes a config file into a generic JSON value. Most synced
// files are objects, but favorites.json is a top-level array, so the value
// must not be assumed to be a map. A missing file and explicitly empty
// wrappers ({}, [], null) all normalize to nil — they all mean "no data" and
// must compare equal to each other.
func readJSONValue(path string) (interface{}, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	if len(bytes.TrimSpace(data)) == 0 {
		return nil, nil
	}
	var v interface{}
	if err := json.Unmarshal(data, &v); err != nil {
		return nil, err
	}
	switch t := v.(type) {
	case map[string]interface{}:
		if len(t) == 0 {
			return nil, nil
		}
	case []interface{}:
		if len(t) == 0 {
			return nil, nil
		}
	}
	return v, nil
}

// compareConfigFiles compares two config files after normalizing the local side
// (backfill legacy keychain passwords, decrypt enc:v1: fields) so both sides
// are plaintext. JSON is re-marshaled via json.MarshalIndent so Go's
// encoding/json sorts map keys deterministically before byte comparison —
// prevents spurious diffs from non-deterministic key ordering. Array files
// (favorites.json) keep their order, which is meaningful, and carry no
// encrypted fields, so normalization applies to objects only.
func compareConfigFiles(localPath, remotePath string, kc *Keychain, ps PasswordStore) (bool, error) {
	localVal, err := readJSONValue(localPath)
	if err != nil {
		return false, fmt.Errorf("parse local %s: %w", localPath, err)
	}
	remoteVal, err := readJSONValue(remotePath)
	if err != nil {
		return false, fmt.Errorf("parse remote %s: %w", remotePath, err)
	}

	if obj, ok := localVal.(map[string]interface{}); ok {
		// Backfill legacy empty passwords from keychain, then decrypt any
		// enc:v1: fields to plaintext, so the local side is comparable to
		// the remote copy.
		backfillFromKeychain(obj, kc)
		decryptFieldsInPlace(obj, ps)
	}

	localNorm, err := json.MarshalIndent(localVal, "", "  ")
	if err != nil {
		return false, fmt.Errorf("marshal local: %w", err)
	}
	remoteNorm, err := json.MarshalIndent(remoteVal, "", "  ")
	if err != nil {
		return false, fmt.Errorf("marshal remote: %w", err)
	}
	return string(localNorm) == string(remoteNorm), nil
}

func backfillFromKeychain(obj map[string]interface{}, kc *Keychain) {
	if kc == nil {
		return
	}
	// Backfill connection passwords
	if conns, ok := obj["connections"].([]interface{}); ok {
		for _, c := range conns {
			if cm, ok := c.(map[string]interface{}); ok {
				if cm["authType"] != "password" {
					continue
				}
				pw, _ := cm["password"].(string)
				if pw == "" {
					if id, ok := cm["id"].(string); ok {
						if kcPw, err := kc.GetPassword(id); err == nil && kcPw != "" {
							cm["password"] = kcPw
						}
					}
				}
			}
		}
	}
}

// VerifySyncPassword validates credentials against the remote and verifies the
// password can decrypt the remote config. username and token are the new values
// from the form; token may be empty to keep the stored one.
func (s *SyncService) VerifySyncPassword(password, username, token string) error {
	config, err := s.configStore.Load()
	if err != nil {
		return fmt.Errorf("load config: %w", err)
	}
	if config.RepoURL == "" {
		return fmt.Errorf("no repo configured")
	}

	if token == "" {
		token = s.getToken()
	}

	// 1. Verify the new credentials can reach the remote
	if err := TestConnection(config.RepoURL, username, token); err != nil {
		return fmt.Errorf("cannot reach remote: %w", err)
	}

	// 2. Open repo and fetch latest encrypted files with validated credentials
	repo, err := CloneOrOpen(s.repoPath, config.RepoURL, config.Branch, username, token)
	if err != nil {
		return fmt.Errorf("open repo: %w", err)
	}
	_ = repo.Fetch(username, token)

	// 3. Derive or load key and verify it can decrypt the remote config
	salt, err := ReadSaltFile(s.repoPath)
	if err != nil {
		return fmt.Errorf("read salt: %w", err)
	}
	if salt == nil {
		return utils.UserErr("salt_missing")
	}

	var key []byte
	if password == "" {
		key, err = s.keychain.GetEncryptionKey()
		if err != nil {
			return ErrWrongSyncPassword
		}
	} else {
		key = DeriveKey(password, salt)
	}

	encrypted, err := repo.ReadRemoteFile(config.Branch, "connections.json")
	if err != nil {
		encrypted, err = os.ReadFile(filepath.Join(s.repoPath, "connections.json"))
		if err != nil {
			return ErrWrongSyncPassword
		}
	}

	if _, err := decryptBytes(string(encrypted), key); err != nil {
		return ErrWrongSyncPassword
	}
	return nil
}

// ChangePassword re-encrypts all synced files with a new master password
// and a fresh random salt. A new salt is required so PBKDF2 work cannot be
// amortized across old and new passwords (SYNC-P1-6). The repo's existing
// ciphertext is decrypted with the old key and re-encrypted with the new
// key via a temp-then-rename pattern, so a crash mid-rotation leaves the
// repo decryptable with the old key.
func (s *SyncService) ChangePassword(oldPassword, newPassword string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	config, err := s.configStore.Load()
	if err != nil {
		return fmt.Errorf("load config: %w", err)
	}
	if config.RepoURL == "" {
		return fmt.Errorf("no repo configured")
	}

	oldSalt, err := ReadSaltFile(s.repoPath)
	if err != nil {
		return fmt.Errorf("read salt: %w", err)
	}
	if oldSalt == nil {
		return utils.UserErr("salt_missing")
	}

	// Verify old password can decrypt the repo.
	oldKey := DeriveKey(oldPassword, oldSalt)
	if err := verifyDecryption(s.repoPath, oldKey); err != nil {
		return utils.UserErr("current_password_mismatch")
	}

	// Fresh 16-byte salt via crypto/rand (SYNC-P1-6).
	newSalt, err := GenerateSalt()
	if err != nil {
		return fmt.Errorf("generate new salt: %w", err)
	}
	newKey := DeriveKey(newPassword, newSalt)
	if err := s.keychain.StoreEncryptionKey(newKey); err != nil {
		return fmt.Errorf("store new encryption key: %w", err)
	}

	// Re-encrypt every existing repo ciphertext: decrypt with oldKey,
	// re-encrypt with newKey, atomic rename. A crash before the rename
	// leaves the original ciphertext intact and decryptable with oldKey.
	for _, name := range syncedFiles {
		srcPath := filepath.Join(s.repoPath, name)
		ciphertext, err := os.ReadFile(srcPath)
		if err != nil {
			if os.IsNotExist(err) {
				continue
			}
			return fmt.Errorf("read %s: %w", name, err)
		}
		plaintext, err := decryptBytes(string(ciphertext), oldKey)
		if err != nil {
			return fmt.Errorf("decrypt %s: %w", name, err)
		}
		encoded, err := encryptBytes(plaintext, newKey)
		if err != nil {
			return fmt.Errorf("encrypt %s: %w", name, err)
		}
		tmpPath := srcPath + ".tmp"
		if err := os.WriteFile(tmpPath, []byte(encoded), 0600); err != nil {
			os.Remove(tmpPath)
			return fmt.Errorf("write %s.tmp: %w", name, err)
		}
		if err := os.Rename(tmpPath, srcPath); err != nil {
			os.Remove(tmpPath)
			return fmt.Errorf("rename %s: %w", name, err)
		}
	}

	// Atomic swap of .sync-salt.
	saltPath := filepath.Join(s.repoPath, ".sync-salt")
	saltTmp := saltPath + ".tmp"
	if err := os.WriteFile(saltTmp, []byte(hex.EncodeToString(newSalt)), 0600); err != nil {
		os.Remove(saltTmp)
		return fmt.Errorf("write .sync-salt.tmp: %w", err)
	}
	if err := os.Rename(saltTmp, saltPath); err != nil {
		os.Remove(saltTmp)
		return fmt.Errorf("rename .sync-salt: %w", err)
	}

	username := config.Username
	token := s.getToken()

	repo, err := CloneOrOpen(s.repoPath, config.RepoURL, config.Branch, username, token)
	if err != nil {
		return fmt.Errorf("open repo: %w", err)
	}

	if _, err := repo.StageAndCommit(commitMsg("Terminal config sync (change password)")); err != nil {
		return fmt.Errorf("commit: %w", err)
	}

	if err := repo.Push(username, token); err != nil {
		return fmt.Errorf("push: %w", err)
	}

	return nil
}

// DeleteRepo removes the local sync repo and credentials.
func (s *SyncService) DeleteRepo() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if err := os.RemoveAll(s.repoPath); err != nil {
		return fmt.Errorf("remove repo: %w", err)
	}

	_ = s.keychain.Delete("encryption-key")
	_ = s.keychain.Delete("git-token")

	return s.configStore.Save(SyncConfig{Branch: "main"})
}

// commitMsg builds a commit message. Hostname and user identity are
// intentionally NOT included — the sync repo is often shared across
// devices and machines, and leaking os.Hostname() to a public-by-mistake
// repo is a privacy regression (SYNC-P1-4).
func commitMsg(action string) string {
	return fmt.Sprintf("%s | %s", action, time.Now().Format(time.RFC3339))
}

// repoHasFiles returns true if the repo directory contains encrypted config files.
func repoHasFiles(repoPath string) bool {
	for _, name := range syncedFiles {
		if _, err := os.Stat(filepath.Join(repoPath, name)); os.IsNotExist(err) {
			return false
		}
	}
	return true
}

// verifyDecryption checks that the given key can decrypt the remote config files.
func verifyDecryption(repoPath string, key []byte) error {
	connPath := filepath.Join(repoPath, "connections.json")
	if _, err := os.Stat(connPath); os.IsNotExist(err) {
		return nil
	}
	tmpDir, err := os.MkdirTemp("", "sync-verify")
	if err != nil {
		return err
	}
	defer os.RemoveAll(tmpDir)
	return DecryptConfigFiles(repoPath, tmpDir, key, nil)
}
