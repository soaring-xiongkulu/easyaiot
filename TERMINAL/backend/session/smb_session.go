package session

import (
	"context"
	"fmt"
	"io"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/cloudsoda/go-smb2"
)

type SMBSession struct {
	baseSession
	localFSOps
	conn      *smb2.Session
	share     *smb2.Share
	cwd       string
	mu        sync.RWMutex
	transfers map[string]*TransferTask
	taskSeq   int64
}

func NewSMBSession(id string) *SMBSession {
	return &SMBSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "smb",
			status:      StatusDisconnected,
		},
		localFSOps: newLocalFSOps(),
		cwd:        "/",
		transfers:  make(map[string]*TransferTask),
	}
}

func (s *SMBSession) Connect(config ConnectionConfig) error {
	s.setStatus(StatusConnecting)
	s.title = fmt.Sprintf("%s@%s", config.User, config.Host)

	port := config.Port
	if port <= 0 {
		port = 445
	}
	addr := net.JoinHostPort(config.Host, strconv.Itoa(port))

	conn, err := net.DialTimeout("tcp", addr, 30*time.Second)
	if err != nil {
		s.setStatus(StatusError)
		return fmt.Errorf("smb dial: %w", err)
	}

	d := &smb2.Dialer{
		Initiator: &smb2.NTLMInitiator{
			User:     config.User,
			Password: config.Password,
			Domain:   config.SmbDomain,
		},
	}

	smbConn, err := d.DialConn(context.Background(), conn, addr)
	if err != nil {
		conn.Close()
		s.setStatus(StatusError)
		return fmt.Errorf("smb handshake: %w", err)
	}

	// Always start at share list root. If a share was specified, the frontend
	// will auto-navigate into it after the initial listing.
	s.conn = smbConn
	s.cwd = "/"
	s.setStatus(StatusConnected)
	return nil
}

func (s *SMBSession) Write(data []byte) error  { return nil }
func (s *SMBSession) Resize(cols, rows int) error { return nil }

func (s *SMBSession) Disconnect() error {
	if s.share != nil {
		s.share.Umount()
		s.share = nil
	}
	if s.conn != nil {
		s.conn.Logoff()
		s.conn = nil
	}
	s.cwd = "/"
	s.setStatus(StatusDisconnected)
	return nil
}

func (s *SMBSession) IsConnected() bool {
	return s.Status() == StatusConnected && s.conn != nil
}

func (s *SMBSession) requireShare() error {
	if s.share == nil {
		return fmt.Errorf("SMB session not connected")
	}
	return nil
}

// smbDir returns the parent directory for an SMB path.
func smbDir(p string) string {
	p = strings.TrimSuffix(p, "/")
	i := strings.LastIndex(p, "/")
	if i < 0 {
		return ""
	}
	return p[:i]
}

// smbJoin joins two SMB path elements with a forward slash.
func smbJoin(base, p string) string {
	if base == "" {
		return p
	}
	return base + "/" + p
}

// smbInternal converts a frontend/internal path (with share prefix) to the raw
// SMB path used by the share's ReadDir/Open/etc. methods.
// E.g. "/sharename/dir/file" → "dir/file", "/sharename" → ""
func (s *SMBSession) smbInternal(p string) string {
	p = strings.TrimPrefix(p, "/")
	if p == "" {
		return ""
	}
	// Find the first segment (share name) and strip it
	idx := strings.Index(p, "/")
	if idx < 0 {
		// p is just the share name → share root
		return ""
	}
	// Return everything after the share name
	return p[idx+1:]
}

func (s *SMBSession) resolveRemote(p string) (string, error) {
	// "" means "list current directory" (used by refresh).
	if p == "" {
		return s.cwd, nil
	}
	return p, nil
}

func (s *SMBSession) nextTaskID(prefix string) string {
	return fmt.Sprintf("%s-%d", prefix, atomic.AddInt64(&s.taskSeq, 1))
}

func (s *SMBSession) readRemoteFile(remotePath string) ([]byte, error) {
	f, err := s.share.Open(remotePath)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return io.ReadAll(f)
}

func (s *SMBSession) writeRemoteFile(remotePath string, content []byte) error {
	f, err := s.share.Create(remotePath)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.Write(content)
	return err
}

func (s *SMBSession) mkdirAllRemote(dir string) error {
	if dir == "" || dir == "." || dir == "/" {
		return nil
	}
	fi, err := s.share.Stat(dir)
	if err == nil && fi.IsDir() {
		return nil
	}
	if err := s.mkdirAllRemote(smbDir(dir)); err != nil {
		return err
	}
	return s.share.Mkdir(dir, 0755)
}

// listShares returns all available shares as directory entries.
func (s *SMBSession) listShares() (FileListResult, error) {
	if s.conn == nil {
		return FileListResult{}, fmt.Errorf("SMB session not connected")
	}
	names, err := s.conn.ListSharenames()
	if err != nil {
		return FileListResult{}, fmt.Errorf("smb list shares: %w", err)
	}
	files := make([]FileItem, 0, len(names))
	for _, name := range names {
		files = append(files, FileItem{
			Name:  name,
			Size:  0,
			Mode:  "drwxr-xr-x",
			IsDir: true,
		})
	}
	return FileListResult{Files: files, Dir: "/"}, nil
}

func (s *SMBSession) ListRemote(dir string) (FileListResult, error) {
	// No share mounted: show share list at root
	if s.share == nil {
		if s.conn == nil {
			return FileListResult{}, fmt.Errorf("SMB session not connected")
		}
		return s.listShares()
	}

	target, err := s.resolveRemote(dir)
	if err != nil {
		return FileListResult{}, err
	}
	internal := s.smbInternal(target)
	entries, err := s.share.ReadDir(internal)
	if err != nil {
		return FileListResult{}, err
	}
	files := make([]FileItem, 0, len(entries))
	for _, e := range entries {
		modTime := ""
		if !e.ModTime().IsZero() {
			modTime = e.ModTime().Format(time.RFC3339)
		}
		files = append(files, FileItem{
			Name:    e.Name(),
			Size:    e.Size(),
			ModTime: modTime,
			Mode:    e.Mode().String(),
			IsDir:   e.IsDir(),
		})
	}
	return FileListResult{Files: files, Dir: target}, nil
}

func (s *SMBSession) ChangeRemoteDir(dir string) (FileListResult, error) {
	// No share mounted yet: navigating into a share name mounts it
	if s.share == nil {
		if s.conn == nil {
			return FileListResult{}, fmt.Errorf("SMB session not connected")
		}
		shareName := strings.TrimPrefix(dir, "/")
		if shareName == "" || shareName == "/" {
			return s.listShares()
		}
		share, err := s.conn.Mount(shareName)
		if err != nil {
			return FileListResult{}, fmt.Errorf("smb mount share %s: %w", shareName, err)
		}
		s.share = share
		s.cwd = "/" + shareName
		return s.ListRemote("")
	}

	target, err := s.resolveRemote(dir)
	if err != nil {
		return FileListResult{}, err
	}

	// "/" from inside a share → go back to share list
	if target == "/" {
		s.share.Umount()
		s.share = nil
		s.cwd = "/"
		return s.listShares()
	}

	// Navigate up: handle going from share root back to share list
	if dir == ".." {
		// If at share root (cwd is "/sharename" or ""), unmount and list shares
		cwdTrimmed := strings.TrimPrefix(strings.TrimSuffix(s.cwd, "/"), "/")
		if cwdTrimmed == "" || !strings.Contains(cwdTrimmed, "/") {
			// At share root, go back to share list
			s.share.Umount()
			s.share = nil
			s.cwd = "/"
			return s.listShares()
		}
		// Navigate to parent directory
		parent := smbDir(target)
		if parent == "" {
			parent = ""
		}
		s.mu.Lock()
		s.cwd = parent
		s.mu.Unlock()
		return s.ListRemote(parent)
	}

	// Root directory: skip Stat (SMB can't stat empty path)
	internal := s.smbInternal(target)
	if internal != "" {
		fi, err := s.share.Stat(internal)
		if err != nil {
			return FileListResult{}, fmt.Errorf("no such directory: %s", target)
		}
		if !fi.IsDir() {
			return FileListResult{}, fmt.Errorf("not a directory: %s", target)
		}
	}
	s.mu.Lock()
	s.cwd = target
	s.mu.Unlock()
	return s.ListRemote(target)
}

// Symlink is not supported: the SMB client library does not expose reparse
// point creation.
func (s *SMBSession) Symlink(_, _ string) error {
	return fmt.Errorf("symlink is not supported by SMB")
}

func (s *SMBSession) MakeDir(dir string) error {
	if err := s.requireShare(); err != nil {
		return err
	}
	p, err := s.resolveRemote(dir)
	if err != nil {
		return err
	}
	return s.share.Mkdir(s.smbInternal(p), 0755)
}

func (s *SMBSession) Remove(p string, recursive bool) error {
	if err := s.requireShare(); err != nil {
		return err
	}
	target, err := s.resolveRemote(p)
	if err != nil {
		return err
	}
	internal := s.smbInternal(target)
	if recursive {
		return s.share.RemoveAll(internal)
	}
	fi, err := s.share.Stat(internal)
	if err != nil {
		return err
	}
	if fi.IsDir() {
		entries, err := s.share.ReadDir(internal)
		if err != nil {
			return err
		}
		if len(entries) > 0 {
			return fmt.Errorf("directory not empty (%d items)", len(entries))
		}
	}
	return s.share.Remove(internal)
}

func (s *SMBSession) Rename(oldName, newName string) error {
	if err := s.requireShare(); err != nil {
		return err
	}
	old, err := s.resolveRemote(oldName)
	if err != nil {
		return err
	}
	n, err := s.resolveRemote(newName)
	if err != nil {
		return err
	}
	return s.share.Rename(s.smbInternal(old), s.smbInternal(n))
}

func (s *SMBSession) Chmod(p string, mode os.FileMode) error {
	if err := s.requireShare(); err != nil {
		return err
	}
	target, err := s.resolveRemote(p)
	if err != nil {
		return err
	}
	return s.share.Chmod(s.smbInternal(target), mode)
}

func (s *SMBSession) Copy(oldPath, newPath string) error {
	if err := s.requireShare(); err != nil {
		return err
	}
	old, err := s.resolveRemote(oldPath)
	if err != nil {
		return err
	}
	n, err := s.resolveRemote(newPath)
	if err != nil {
		return err
	}
	oldInternal := s.smbInternal(old)
	fi, err := s.share.Stat(oldInternal)
	if err != nil {
		return err
	}
	if fi.IsDir() {
		return fmt.Errorf("cannot copy directory via SMB: %s", old)
	}
	data, err := s.readRemoteFile(oldInternal)
	if err != nil {
		return err
	}
	return s.writeRemoteFile(s.smbInternal(n), data)
}

func (s *SMBSession) Move(oldPath, newPath string) error {
	return s.Rename(oldPath, newPath)
}

func (s *SMBSession) GetContent(remotePath string) ([]byte, error) {
	if err := s.requireShare(); err != nil {
		return nil, err
	}
	p, err := s.resolveRemote(remotePath)
	if err != nil {
		return nil, err
	}
	return s.readRemoteFile(s.smbInternal(p))
}

func (s *SMBSession) PutContent(remotePath string, content []byte) error {
	if err := s.requireShare(); err != nil {
		return err
	}
	p, err := s.resolveRemote(remotePath)
	if err != nil {
		return err
	}
	internal := s.smbInternal(p)
	parentDir := smbDir(internal)
	if err := s.mkdirAllRemote(parentDir); err != nil {
		return err
	}
	return s.writeRemoteFile(internal, content)
}

func (s *SMBSession) Get(remotePath, localPath string, recursive bool) (string, error) {
	if err := s.requireShare(); err != nil {
		return "", err
	}
	rp, err := s.resolveRemote(remotePath)
	if err != nil {
		return "", err
	}
	rp = s.smbInternal(rp)
	lp := localPath
	if !filepath.IsAbs(lp) {
		lp = filepath.Join(s.localCwd, lp)
	}
	task := &TransferTask{
		ID:         s.nextTaskID("dl"),
		Type:       "download",
		LocalPath:  lp,
		RemotePath: rp,
		Status:     "running",
	}
	task.start()
	s.mu.Lock()
	s.transfers[task.ID] = task
	s.mu.Unlock()
	s.emitTransferStart(task)
	go func() {
		defer func() {
			task.done()
			s.mu.Lock()
			delete(s.transfers, task.ID)
			s.mu.Unlock()
		}()
		var err error
		if recursive {
			err = s.downloadDir(rp, lp, task)
		} else {
			err = s.downloadFile(task, rp, lp)
		}
		if err != nil {
			s.emitTransferEvent(task, err)
			return
		}
		task.Status = "done"
		s.emitTransferComplete(task)
	}()
	return task.ID, nil
}

func (s *SMBSession) Put(localPath, remotePath string, recursive bool) (string, error) {
	if err := s.requireShare(); err != nil {
		return "", err
	}
	lp := localPath
	if !filepath.IsAbs(lp) {
		lp = filepath.Join(s.localCwd, lp)
	}
	rp, err := s.resolveRemote(remotePath)
	if err != nil {
		return "", err
	}
	rp = s.smbInternal(rp)
	task := &TransferTask{
		ID:         s.nextTaskID("ul"),
		Type:       "upload",
		LocalPath:  lp,
		RemotePath: rp,
		Status:     "running",
	}
	task.start()
	s.mu.Lock()
	s.transfers[task.ID] = task
	s.mu.Unlock()
	s.emitTransferStart(task)
	go func() {
		defer func() {
			task.done()
			s.mu.Lock()
			delete(s.transfers, task.ID)
			s.mu.Unlock()
		}()
		var err error
		if recursive {
			err = s.uploadDir(lp, rp, task)
		} else {
			err = s.uploadFile(task, lp, rp)
		}
		if err != nil {
			s.emitTransferEvent(task, err)
			return
		}
		task.Status = "done"
		s.emitTransferComplete(task)
	}()
	return task.ID, nil
}

func (s *SMBSession) CancelTransfer(taskID string) error {
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

func (s *SMBSession) PauseTransfer(taskID string) error {
	s.mu.Lock()
	task, ok := s.transfers[taskID]
	s.mu.Unlock()
	if !ok {
		return fmt.Errorf("task not found: %s", taskID)
	}
	task.setPaused(true)
	task.Status = "paused"
	s.emitTransferComplete(task)
	return nil
}

func (s *SMBSession) ResumeTransfer(taskID string) error {
	s.mu.Lock()
	task, ok := s.transfers[taskID]
	s.mu.Unlock()
	if !ok {
		return fmt.Errorf("task not found: %s", taskID)
	}
	task.setPaused(false)
	task.Status = "running"
	close(task.pauseCh)
	task.pauseCh = make(chan struct{})
	s.emitTransferStart(task)
	return nil
}

// calcSmbRemoteDirSize recursively sums up all file sizes under a remote SMB directory.
func (s *SMBSession) calcSmbRemoteDirSize(remoteDir string) (int64, error) {
	var total int64
	entries, err := s.share.ReadDir(remoteDir)
	if err != nil {
		return 0, err
	}
	for _, e := range entries {
		if e.IsDir() {
			sub, err := s.calcSmbRemoteDirSize(smbJoin(remoteDir, e.Name()))
			if err != nil {
				return 0, err
			}
			total += sub
		} else {
			total += e.Size()
		}
	}
	return total, nil
}

func (s *SMBSession) downloadDir(remoteDir, localDir string, task *TransferTask) error {
	// Calculate total size for progress tracking
	if task.loadTotal() <= 0 {
		if total, err := s.calcSmbRemoteDirSize(remoteDir); err == nil {
			task.setTotal(total)
		}
	}

	if err := os.MkdirAll(localDir, 0755); err != nil {
		return err
	}
	entries, err := s.share.ReadDir(remoteDir)
	if err != nil {
		return err
	}
	for _, e := range entries {
		select {
		case <-task.ctx.Done():
			return task.ctx.Err()
		default:
		}
		rp := smbJoin(remoteDir, e.Name())
		lp := filepath.Join(localDir, e.Name())
		if e.IsDir() {
			if err := s.downloadDir(rp, lp, task); err != nil {
				return err
			}
		} else {
			if err := s.downloadFile(task, rp, lp); err != nil {
				return err
			}
		}
	}
	return nil
}

func (s *SMBSession) downloadFile(task *TransferTask, remotePath, localPath string) error {
	// Get file size first for progress tracking
	if task.loadTotal() <= 0 {
		if fi, err := s.share.Stat(remotePath); err == nil {
			if fi.Size() > 0 {
				task.setTotal(fi.Size())
			}
		}
	}

	f, err := s.share.Open(remotePath)
	if err != nil {
		return err
	}
	defer f.Close()
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
		n, e := f.Read(buf)
		if n > 0 {
			dst.Write(buf[:n])
			task.addProgress(int64(n))
			s.emitTransferProgress(task)
		}
		if e != nil {
			if e == io.EOF {
				return nil
			}
			return e
		}
	}
}

func (s *SMBSession) uploadDir(localDir, remoteDir string, task *TransferTask) error {
	// Calculate total size for progress tracking
	if task.loadTotal() <= 0 {
		if total, err := calcLocalDirSize(localDir); err == nil {
			task.setTotal(total)
		}
	}

	if err := s.mkdirAllRemote(remoteDir); err != nil {
		return err
	}
	entries, err := os.ReadDir(localDir)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		select {
		case <-task.ctx.Done():
			return task.ctx.Err()
		default:
		}
		lp := filepath.Join(localDir, entry.Name())
		rp := remoteDir + "/" + entry.Name()
		if entry.IsDir() {
			if err := s.uploadDir(lp, rp, task); err != nil {
				return err
			}
		} else {
			if err := s.uploadFile(task, lp, rp); err != nil {
				return err
			}
		}
	}
	return nil
}

func (s *SMBSession) uploadFile(task *TransferTask, localPath, remotePath string) error {
	// Get local file size first for progress tracking
	if task.loadTotal() <= 0 {
		if fi, err := os.Stat(localPath); err == nil {
			if fi.Size() > 0 {
				task.setTotal(fi.Size())
			}
		}
	}

	src, err := os.Open(localPath)
	if err != nil {
		return err
	}
	defer src.Close()
	dst, err := s.share.Create(remotePath)
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
			if _, we := dst.Write(buf[:n]); we != nil {
				return we
			}
			task.addProgress(int64(n))
			s.emitTransferProgress(task)
		}
		if e != nil {
			if e == io.EOF {
				return nil
			}
			return e
		}
	}
}

