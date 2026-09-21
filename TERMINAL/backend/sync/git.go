package sync

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/config"
	"github.com/go-git/go-git/v5/plumbing"
	"github.com/go-git/go-git/v5/plumbing/object"
	githttp "github.com/go-git/go-git/v5/plumbing/transport/http"
	gittransport "github.com/go-git/go-git/v5/plumbing/transport"
)

type GitRepo struct {
	repo     *git.Repository
	repoPath string
}

type SyncDirection int

const (
	SyncNone    SyncDirection = iota
	SyncPush
	SyncPull
	SyncConflict
)

// CloneOrOpen opens the repo at repoPath, or clones it from the given URL.
func CloneOrOpen(repoPath, repoURL, branch, username, token string) (*GitRepo, error) {
	repo, err := git.PlainOpen(repoPath)
	if err == nil {
		return &GitRepo{repo: repo, repoPath: repoPath}, nil
	}

	if !errors.Is(err, git.ErrRepositoryNotExists) && !os.IsNotExist(err) {
		return nil, fmt.Errorf("open repo: %w", err)
	}

	if err := os.MkdirAll(filepath.Dir(repoPath), 0755); err != nil {
		return nil, fmt.Errorf("create parent dir: %w", err)
	}

	refName := plumbing.NewBranchReferenceName(branch)
	am := buildAuth(username, token)
	repo, err = git.PlainClone(repoPath, false, &git.CloneOptions{
		URL:           repoURL,
		Auth:          am,
		ReferenceName: refName,
		SingleBranch:  true,
	})
	if err != nil {
		if errors.Is(err, gittransport.ErrEmptyRemoteRepository) {
			return initEmpty(repoPath, repoURL)
		}
		return nil, fmt.Errorf("clone: %w", err)
	}

	return &GitRepo{repo: repo, repoPath: repoPath}, nil
}

func initEmpty(repoPath, repoURL string) (*GitRepo, error) {
	repo, err := git.PlainInit(repoPath, false)
	if err != nil {
		return nil, fmt.Errorf("init: %w", err)
	}
	mainRef := plumbing.NewBranchReferenceName("main")
	if err := repo.Storer.SetReference(plumbing.NewSymbolicReference(plumbing.HEAD, mainRef)); err != nil {
		return nil, fmt.Errorf("set HEAD to main: %w", err)
	}
	if _, err := repo.CreateRemote(&config.RemoteConfig{
		Name: "origin",
		URLs: []string{repoURL},
		Fetch: []config.RefSpec{
			config.RefSpec("+refs/heads/*:refs/remotes/origin/*"),
		},
	}); err != nil {
		return nil, fmt.Errorf("create remote: %w", err)
	}
	return &GitRepo{repo: repo, repoPath: repoPath}, nil
}

// StageAndCommit stages all files and creates a commit. Returns true if committed.
func (g *GitRepo) StageAndCommit(msg string) (bool, error) {
	wt, err := g.repo.Worktree()
	if err != nil {
		return false, fmt.Errorf("worktree: %w", err)
	}

	status, err := wt.Status()
	if err != nil {
		return false, fmt.Errorf("status: %w", err)
	}
	if status.IsClean() {
		return false, nil
	}

	// Whitelist the synced config files (single source of truth in
	// synced_files.go) plus repo metadata, so stray files dropped in
	// the sync repo (e.g. an SSH key) are NOT committed plaintext
	// (SYNC-P1-9).
	commitWhitelist := append(syncedFiles[:len(syncedFiles):len(syncedFiles)], ".sync-salt", "README.md")
	for _, name := range commitWhitelist {
		if _, err := os.Stat(filepath.Join(g.repoPath, name)); err != nil {
			continue
		}
		if _, err := wt.Add(name); err != nil {
			return false, fmt.Errorf("add %s: %w", name, err)
		}
	}

	_, err = wt.Commit(msg, &git.CommitOptions{
		Author: &object.Signature{
			Name:  "Terminal",
			Email: "terminal@local",
			When:  time.Now(),
		},
	})
	if err != nil {
		return false, fmt.Errorf("commit: %w", err)
	}
	return true, nil
}

func (g *GitRepo) Push(username, token string) error {
	err := g.repo.Push(&git.PushOptions{Auth: buildAuth(username, token)})
	if errors.Is(err, git.NoErrAlreadyUpToDate) {
		return nil
	}
	return err
}

func (g *GitRepo) Pull(username, token string) error {
	wt, err := g.repo.Worktree()
	if err != nil {
		return fmt.Errorf("worktree: %w", err)
	}
	return wt.Pull(&git.PullOptions{Auth: buildAuth(username, token), SingleBranch: true})
}

func (g *GitRepo) Fetch(username, token string) error {
	err := g.repo.Fetch(&git.FetchOptions{Auth: buildAuth(username, token), Force: true})
	if errors.Is(err, git.NoErrAlreadyUpToDate) {
		return nil
	}
	return err
}

// ReadRemoteFile reads a file from the remote tracking branch without touching the worktree.
func (g *GitRepo) ReadRemoteFile(branch, filePath string) ([]byte, error) {
	remoteRef, err := g.repo.Reference(
		plumbing.NewRemoteReferenceName("origin", branch), true,
	)
	if err != nil {
		return nil, err
	}
	commit, err := g.repo.CommitObject(remoteRef.Hash())
	if err != nil {
		return nil, err
	}
	tree, err := commit.Tree()
	if err != nil {
		return nil, err
	}
	file, err := tree.File(filePath)
	if err != nil {
		return nil, err
	}
	content, err := file.Contents()
	if err != nil {
		return nil, err
	}
	return []byte(content), nil
}

// BranchHeads is the resolved state of the sync branch after a fetch.
// A nil Local means HEAD is still unborn (no commits yet); a nil Remote
// means the remote branch does not exist (empty repository).
type BranchHeads struct {
	Local  *plumbing.Hash
	Remote *plumbing.Hash
}

// ResolveBranchHeads returns the local HEAD hash and the origin/<branch>
// hash without assuming either exists.
func (g *GitRepo) ResolveBranchHeads(branch string) (BranchHeads, error) {
	var heads BranchHeads

	localRef, err := g.repo.Head()
	if err != nil {
		if err != plumbing.ErrReferenceNotFound {
			return heads, fmt.Errorf("local head: %w", err)
		}
		// Unborn HEAD — no local commits yet.
	} else {
		h := localRef.Hash()
		heads.Local = &h
	}

	remoteRef, err := g.repo.Reference(
		plumbing.NewRemoteReferenceName("origin", branch), true,
	)
	if err != nil {
		if err != plumbing.ErrReferenceNotFound {
			return heads, fmt.Errorf("remote ref: %w", err)
		}
	} else {
		h := remoteRef.Hash()
		heads.Remote = &h
	}

	return heads, nil
}

// MergeBase returns the best common ancestor of the two commits, or nil
// when they share no history.
func (g *GitRepo) MergeBase(a, b plumbing.Hash) (*plumbing.Hash, error) {
	ca, err := g.repo.CommitObject(a)
	if err != nil {
		return nil, fmt.Errorf("commit %s: %w", a, err)
	}
	cb, err := g.repo.CommitObject(b)
	if err != nil {
		return nil, fmt.Errorf("commit %s: %w", b, err)
	}
	bases, err := ca.MergeBase(cb)
	if err != nil {
		return nil, fmt.Errorf("merge base: %w", err)
	}
	if len(bases) == 0 {
		return nil, nil
	}
	h := bases[0].Hash
	return &h, nil
}

// CommitTime returns the committer timestamp of the given commit.
func (g *GitRepo) CommitTime(h plumbing.Hash) (time.Time, error) {
	commit, err := g.repo.CommitObject(h)
	if err != nil {
		return time.Time{}, fmt.Errorf("commit %s: %w", h, err)
	}
	return commit.Committer.When, nil
}

// ExtractCommitFiles writes the synced config files as committed at hash
// into destDir. The extracted files are still encrypted — the caller
// decrypts them. Files absent from that commit's tree are skipped.
func (g *GitRepo) ExtractCommitFiles(hash plumbing.Hash, destDir string) error {
	commit, err := g.repo.CommitObject(hash)
	if err != nil {
		return fmt.Errorf("commit %s: %w", hash, err)
	}
	tree, err := commit.Tree()
	if err != nil {
		return fmt.Errorf("tree: %w", err)
	}
	if err := os.MkdirAll(destDir, 0755); err != nil {
		return err
	}
	for _, name := range syncedFiles {
		file, err := tree.File(name)
		if err != nil {
			// Not present in this commit (e.g. the merge base predates
			// the file) — nothing to extract.
			continue
		}
		content, err := file.Contents()
		if err != nil {
			return fmt.Errorf("read %s: %w", name, err)
		}
		if err := os.WriteFile(filepath.Join(destDir, name), []byte(content), 0600); err != nil {
			return fmt.Errorf("write %s: %w", name, err)
		}
	}
	return nil
}

// PushToBranch pushes the current HEAD to the specified remote branch.
func (g *GitRepo) PushToBranch(branch, username, token string) error {
	srcRef := plumbing.NewBranchReferenceName(branch)
	err := g.repo.Push(&git.PushOptions{
		Auth: buildAuth(username, token),
		RefSpecs: []config.RefSpec{
			config.RefSpec(fmt.Sprintf("%s:refs/heads/%s", srcRef, branch)),
		},
	})
	if errors.Is(err, git.NoErrAlreadyUpToDate) {
		return nil
	}
	return err
}

// ResetToRemote resets local HEAD to match remote branch.
func (g *GitRepo) ResetToRemote(branch string) error {
	wt, err := g.repo.Worktree()
	if err != nil {
		return fmt.Errorf("worktree: %w", err)
	}
	remoteRef, err := g.repo.Reference(
		plumbing.NewRemoteReferenceName("origin", branch), true,
	)
	if err != nil {
		return fmt.Errorf("remote ref: %w", err)
	}
	return wt.Reset(&git.ResetOptions{
		Commit: remoteRef.Hash(),
		Mode:   git.HardReset,
	})
}

// TestConnection verifies the repo URL is reachable.
func TestConnection(repoURL, username, token string) error {
	remote := git.NewRemote(nil, &config.RemoteConfig{
		Name: "origin",
		URLs: []string{repoURL},
	})
	_, err := remote.List(&git.ListOptions{Auth: buildAuth(username, token)})
	if err != nil {
		return fmt.Errorf("remote unreachable: %w", err)
	}
	return nil
}

func buildAuth(username, token string) gittransport.AuthMethod {
	return &githttp.BasicAuth{
		Username: username,
		Password: token,
	}
}
