package session

import (
	"fmt"
	"os"
	osUser "os/user"
	"path/filepath"
	"strings"
	"time"
)

// localFSOps provides reusable local filesystem operations for file-transfer
// session types (FTP, SMB, WebDAV, S3). Embed it and set localCwd before use.
type localFSOps struct {
	localCwd string
}

func newLocalFSOps() localFSOps {
	homeDir, _ := os.UserHomeDir()
	return localFSOps{localCwd: homeDir}
}

func (o *localFSOps) ListLocal(dir string) (FileListResult, error) {
	if dir == "" {
		dir = o.localCwd
	} else if !filepath.IsAbs(dir) {
		dir = filepath.Join(o.localCwd, dir)
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		return FileListResult{}, err
	}
	files := make([]FileItem, 0, len(entries))
	for _, e := range entries {
		fi, _ := e.Info()
		var size int64
		var mode os.FileMode
		var modTime time.Time
		if fi != nil {
			size = fi.Size()
			mode = fi.Mode()
			modTime = fi.ModTime()
		}
		owner := ""
		// Windows reports the owner as "COMPUTERNAME\user", verbose in the
		// owner column; keep only the user part (same nicing SFTP had before it
		// was folded into this shared helper).
		if currentUser, err := osUser.Current(); err == nil {
			if i := strings.LastIndexByte(currentUser.Username, '\\'); i >= 0 {
				owner = currentUser.Username[i+1:]
			} else {
				owner = currentUser.Username
			}
		}
		isDir := e.IsDir()
		if fi != nil && fi.Mode()&os.ModeSymlink != 0 {
			if target, err := os.Stat(filepath.Join(dir, e.Name())); err == nil {
				isDir = target.IsDir()
			}
		}
		isHidden := e.Name() != "" && e.Name()[0] == '.'
		if !isHidden {
			isHidden = isPathHidden(filepath.Join(dir, e.Name()))
		}
		files = append(files, FileItem{
			Name:     e.Name(),
			Size:     size,
			ModTime:  modTime.Format(time.RFC3339),
			Mode:     mode.String(),
			IsDir:    isDir,
			IsHidden: isHidden,
			Owner:    owner,
		})
	}
	return FileListResult{Files: files, Dir: dir}, nil
}

func (o *localFSOps) ListLocalDrives() ([]FileItem, error) {
	var drives []FileItem
	for _, letter := range "ABCDEFGHIJKLMNOPQRSTUVWXYZ" {
		root := string(letter) + ":\\"
		fi, err := os.Stat(root)
		if err != nil {
			continue
		}
		if fi.IsDir() {
			drives = append(drives, FileItem{
				Name:    root,
				Size:    0,
				ModTime: fi.ModTime().Format(time.RFC3339),
				Mode:    fi.Mode().String(),
				IsDir:   true,
			})
		}
	}
	return drives, nil
}

func (o *localFSOps) ChangeLocalDir(dir string) (FileListResult, error) {
	target := dir
	if !filepath.IsAbs(dir) {
		target = filepath.Join(o.localCwd, dir)
	}
	fi, err := os.Stat(target)
	if err != nil {
		return FileListResult{}, fmt.Errorf("no such directory: %s", target)
	}
	if !fi.IsDir() {
		return FileListResult{}, fmt.Errorf("not a directory: %s", target)
	}
	abs, _ := filepath.Abs(target)
	o.localCwd = abs
	return o.ListLocal(abs)
}

func (o *localFSOps) LocalRemove(p string, recursive bool) error {
	if !filepath.IsAbs(p) {
		p = filepath.Join(o.localCwd, p)
	}
	if recursive {
		return os.RemoveAll(p)
	}
	fi, err := os.Stat(p)
	if err != nil {
		return err
	}
	if fi.IsDir() {
		entries, err := os.ReadDir(p)
		if err != nil {
			return err
		}
		if len(entries) > 0 {
			return fmt.Errorf("directory not empty (%d items)", len(entries))
		}
	}
	return os.Remove(p)
}

func (o *localFSOps) LocalRename(oldName, newName string) error {
	old := oldName
	if !filepath.IsAbs(old) {
		old = filepath.Join(o.localCwd, old)
	}
	newPath := newName
	if !filepath.IsAbs(newPath) {
		newPath = filepath.Join(o.localCwd, newPath)
	}
	return os.Rename(old, newPath)
}

func (o *localFSOps) LocalMkdir(dir string) error {
	p := dir
	if !filepath.IsAbs(p) {
		p = filepath.Join(o.localCwd, p)
	}
	return os.MkdirAll(p, 0755)
}

func (o *localFSOps) LocalGetContent(localPath string) ([]byte, error) {
	p := localPath
	if !filepath.IsAbs(p) {
		p = filepath.Join(o.localCwd, p)
	}
	return os.ReadFile(p)
}

func (o *localFSOps) LocalPutContent(localPath string, content []byte) error {
	p := localPath
	if !filepath.IsAbs(p) {
		p = filepath.Join(o.localCwd, p)
	}
	if err := os.MkdirAll(filepath.Dir(p), 0755); err != nil {
		return err
	}
	return os.WriteFile(p, content, 0644)
}

func (o *localFSOps) LocalCopy(oldPath, newPath string) error {
	old := oldPath
	if !filepath.IsAbs(old) {
		old = filepath.Join(o.localCwd, old)
	}
	n := newPath
	if !filepath.IsAbs(n) {
		n = filepath.Join(o.localCwd, n)
	}
	return localCopyRecursive(old, n)
}

func (o *localFSOps) LocalMove(oldPath, newPath string) error {
	old := oldPath
	if !filepath.IsAbs(old) {
		old = filepath.Join(o.localCwd, old)
	}
	n := newPath
	if !filepath.IsAbs(n) {
		n = filepath.Join(o.localCwd, n)
	}
	return os.Rename(old, n)
}
