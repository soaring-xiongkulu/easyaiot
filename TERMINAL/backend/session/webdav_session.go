package session

import (
	"fmt"
	"io"
	"os"
	"path"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/studio-b12/gowebdav"
)

type WebDAVSession struct {
	baseSession
	localFSOps
	client    *gowebdav.Client
	cwd       string
	mu        sync.RWMutex
	transfers map[string]*TransferTask
	taskSeq   int64
}

func NewWebDAVSession(id string) *WebDAVSession {
	return &WebDAVSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "webdav",
			status:      StatusDisconnected,
		},
		localFSOps: newLocalFSOps(),
		cwd:        "/",
		transfers:  make(map[string]*TransferTask),
	}
}

func (s *WebDAVSession) Connect(config ConnectionConfig) error {
	s.setStatus(StatusConnecting)

	url := strings.TrimSuffix(config.Host, "/")
	s.title = fmt.Sprintf("%s@%s", config.User, url)

	client := gowebdav.NewClient(url, config.User, config.Password)
	if err := client.Connect(); err != nil {
		s.setStatus(StatusError)
		return fmt.Errorf("webdav connect: %w", err)
	}

	s.client = client
	s.cwd = "/"
	s.setStatus(StatusConnected)
	return nil
}

func (s *WebDAVSession) Write(data []byte) error  { return nil }
func (s *WebDAVSession) Resize(cols, rows int) error { return nil }

func (s *WebDAVSession) Disconnect() error {
	s.client = nil
	s.setStatus(StatusDisconnected)
	return nil
}

func (s *WebDAVSession) IsConnected() bool {
	return s.Status() == StatusConnected && s.client != nil
}

func (s *WebDAVSession) requireClient() error {
	if s.client == nil {
		return fmt.Errorf("WebDAV session not connected")
	}
	return nil
}

func (s *WebDAVSession) resolveRemote(p string) (string, error) {
	if p == "" {
		return s.cwd, nil
	}
	if path.IsAbs(p) {
		return p, nil
	}
	return path.Join(s.cwd, p), nil
}

func (s *WebDAVSession) nextTaskID(prefix string) string {
	return fmt.Sprintf("%s-%d", prefix, atomic.AddInt64(&s.taskSeq, 1))
}

func (s *WebDAVSession) ListRemote(dir string) (FileListResult, error) {
	if err := s.requireClient(); err != nil {
		return FileListResult{}, err
	}
	target, err := s.resolveRemote(dir)
	if err != nil {
		return FileListResult{}, err
	}
	entries, err := s.client.ReadDir(target)
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

func (s *WebDAVSession) ChangeRemoteDir(dir string) (FileListResult, error) {
	if err := s.requireClient(); err != nil {
		return FileListResult{}, err
	}
	target, err := s.resolveRemote(dir)
	if err != nil {
		return FileListResult{}, err
	}
	// ReadDir doubles as an existence + is-dir check, and gowebdav's
	// internal PROPFIND handles trailing-slash normalization that
	// Stat() does not (Apache mod_dav returns 301 for /dir without a
	// slash, which gowebdav treats as an error).
	entries, err := s.client.ReadDir(target)
	if err != nil {
		return FileListResult{}, err
	}
	s.mu.Lock()
	s.cwd = target
	s.mu.Unlock()
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

// Symlink is not supported: WebDAV has no link resource type.
func (s *WebDAVSession) Symlink(_, _ string) error {
	return fmt.Errorf("symlink is not supported by WebDAV")
}

func (s *WebDAVSession) MakeDir(dir string) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	p, err := s.resolveRemote(dir)
	if err != nil {
		return err
	}
	return s.client.Mkdir(p, 0755)
}

func (s *WebDAVSession) Remove(p string, recursive bool) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	target, err := s.resolveRemote(p)
	if err != nil {
		return err
	}
	if recursive {
		return s.client.RemoveAll(target)
	}
	fi, err := s.client.Stat(target)
	if err != nil {
		return err
	}
	if fi.IsDir() {
		entries, err := s.client.ReadDir(target)
		if err != nil {
			return err
		}
		if len(entries) > 0 {
			return fmt.Errorf("directory not empty (%d items)", len(entries))
		}
	}
	return s.client.Remove(target)
}

func (s *WebDAVSession) Rename(oldName, newName string) error {
	if err := s.requireClient(); err != nil {
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
	return s.client.Rename(old, n, false)
}

func (s *WebDAVSession) Chmod(p string, mode os.FileMode) error {
	return fmt.Errorf("WebDAV does not support chmod")
}

func (s *WebDAVSession) Copy(oldPath, newPath string) error {
	if err := s.requireClient(); err != nil {
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
	return s.client.Copy(old, n, false)
}

func (s *WebDAVSession) Move(oldPath, newPath string) error {
	return s.Rename(oldPath, newPath)
}

func (s *WebDAVSession) GetContent(remotePath string) ([]byte, error) {
	if err := s.requireClient(); err != nil {
		return nil, err
	}
	p, err := s.resolveRemote(remotePath)
	if err != nil {
		return nil, err
	}
	return s.client.Read(p)
}

func (s *WebDAVSession) PutContent(remotePath string, content []byte) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	p, err := s.resolveRemote(remotePath)
	if err != nil {
		return err
	}
	parentDir := path.Dir(p)
	if err := s.client.MkdirAll(parentDir, 0755); err != nil {
		return err
	}
	return s.client.Write(p, content, 0644)
}

func (s *WebDAVSession) Get(remotePath, localPath string, recursive bool) (string, error) {
	if err := s.requireClient(); err != nil {
		return "", err
	}
	rp, err := s.resolveRemote(remotePath)
	if err != nil {
		return "", err
	}
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

func (s *WebDAVSession) Put(localPath, remotePath string, recursive bool) (string, error) {
	if err := s.requireClient(); err != nil {
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

func (s *WebDAVSession) CancelTransfer(taskID string) error {
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

func (s *WebDAVSession) PauseTransfer(taskID string) error {
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

func (s *WebDAVSession) ResumeTransfer(taskID string) error {
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

// calcWebdavRemoteDirSize recursively sums up all file sizes under a remote WebDAV directory.
func (s *WebDAVSession) calcWebdavRemoteDirSize(remoteDir string) (int64, error) {
	var total int64
	entries, err := s.client.ReadDir(remoteDir)
	if err != nil {
		return 0, err
	}
	for _, e := range entries {
		if e.IsDir() {
			sub, err := s.calcWebdavRemoteDirSize(path.Join(remoteDir, e.Name()))
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

func (s *WebDAVSession) downloadDir(remoteDir, localDir string, task *TransferTask) error {
	// Calculate total size for progress tracking
	if task.loadTotal() <= 0 {
		if total, err := s.calcWebdavRemoteDirSize(remoteDir); err == nil {
			task.setTotal(total)
		}
	}
	if err := os.MkdirAll(localDir, 0755); err != nil {
		return err
	}
	entries, err := s.client.ReadDir(remoteDir)
	if err != nil {
		return err
	}
	for _, e := range entries {
		select {
		case <-task.ctx.Done():
			return task.ctx.Err()
		default:
		}
		rp := path.Join(remoteDir, e.Name())
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

func (s *WebDAVSession) downloadFile(task *TransferTask, remotePath, localPath string) error {
	// Get file size first for progress tracking
	if task.loadTotal() <= 0 {
		if fi, err := s.client.Stat(remotePath); err == nil {
			if fi.Size() > 0 {
				task.setTotal(fi.Size())
			}
		}
	}

	rc, err := s.client.ReadStream(remotePath)
	if err != nil {
		return err
	}
	defer rc.Close()
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
		n, e := rc.Read(buf)
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

func (s *WebDAVSession) uploadDir(localDir, remoteDir string, task *TransferTask) error {
	// Calculate total size for progress tracking
	if task.loadTotal() <= 0 {
		if total, err := calcLocalDirSize(localDir); err == nil {
			task.setTotal(total)
		}
	}

	if err := s.client.MkdirAll(remoteDir, 0755); err != nil {
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
		rp := path.Join(remoteDir, entry.Name())
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

func (s *WebDAVSession) uploadFile(task *TransferTask, localPath, remotePath string) error {
	src, err := os.Open(localPath)
	if err != nil {
		return err
	}
	defer src.Close()
	fi, err := src.Stat()
	if err != nil {
		return err
	}
	// Set total size from file stat for progress tracking
	if task.loadTotal() <= 0 && fi.Size() > 0 {
		task.setTotal(fi.Size())
	}
	pr, pw := io.Pipe()
	errCh := make(chan error, 1)
	go func() {
		errCh <- s.client.WriteStream(remotePath, pr, 0644)
	}()
	buf := make([]byte, 64*1024)
	totalWritten := int64(0)
	for {
		select {
		case <-task.ctx.Done():
			pw.CloseWithError(task.ctx.Err())
			return task.ctx.Err()
		default:
		}
		task.waitIfPaused()
		n, e := src.Read(buf)
		if n > 0 {
			if _, we := pw.Write(buf[:n]); we != nil {
				pw.CloseWithError(we)
				return we
			}
			totalWritten += int64(n)
			task.addProgress(int64(n))
			s.emitTransferProgress(task)
		}
		if e != nil {
			if e == io.EOF {
				pw.Close()
				break
			}
			pw.CloseWithError(e)
			return e
		}
	}
	return <-errCh
}

