package store

import (
	"io"
	"os"
	"path/filepath"
	"time"
)

// atomicWriteFile writes data to path via a temp file in the same directory,
// fsyncs the file, then renames over the destination. On POSIX this is
// atomic and survives process kill or power loss between calls without
// leaving a half-written file at the target path.
//
// Fixes: STORE-03, STORE-09, STORE-10, STORE-12, STORE-19, STORE-21 (refs in
// .planning/audit/phase-2/TRIAGE.md).
func atomicWriteFile(path string, data []byte, perm os.FileMode) (err error) {
	dir := filepath.Dir(path)
	tmp, err := os.CreateTemp(dir, filepath.Base(path)+".tmp-*")
	if err != nil {
		return err
	}
	tmpName := tmp.Name()
	defer func() {
		if err != nil {
			_ = os.Remove(tmpName)
		}
	}()

	if _, err = tmp.Write(data); err != nil {
		tmp.Close()
		return err
	}
	if err = tmp.Sync(); err != nil {
		tmp.Close()
		return err
	}
	if err = tmp.Close(); err != nil {
		return err
	}
	if err = os.Chmod(tmpName, perm); err != nil {
		return err
	}
	return os.Rename(tmpName, path)
}

// quarantineCorrupt renames a corrupt JSON file aside so the next Save
// can proceed without losing the user's prior data to a silent overwrite.
// Returns the new path, or empty string if the rename was unnecessary.
//
// Fixes: STORE-09 (silent unmarshal-failure data wipe in 4 stores).
func quarantineCorrupt(path string) string {
	ts := time.Now().UTC().Format("20060102T150405")
	target := path + ".corrupt-" + ts
	if err := os.Rename(path, target); err != nil {
		return ""
	}
	return target
}

// copyFileWithoutSymlinks copies src to dst without following symlinks.
// If src is itself a symlink, the copy is skipped (returns nil). Used by
// SkillsStore to prevent symlink-following deletions.
//
// Fixes: STORE-02.
func copyFileWithoutSymlinks(src, dst string) error {
	srcInfo, err := os.Lstat(src)
	if err != nil {
		return err
	}
	if srcInfo.Mode()&os.ModeSymlink != 0 {
		// Refuse to copy symlinks to avoid traversing arbitrary paths.
		return nil
	}
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()

	out, err := os.OpenFile(dst, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, srcInfo.Mode().Perm())
	if err != nil {
		return err
	}
	defer out.Close()
	_, err = io.Copy(out, in)
	return err
}