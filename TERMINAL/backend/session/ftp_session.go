package session

import (
	"crypto/tls"
	"fmt"
	"io"
	"os"
	"path"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/jlaffaye/ftp"
)

type FTPSession struct {
	baseSession
	localFSOps
	conn      *ftp.ServerConn
	cwd       string
	mu        sync.RWMutex
	transfers map[string]*TransferTask
	taskSeq   int64
	connMu    sync.Mutex // serialize data transfer operations (FTP is not concurrent)
}

func NewFTPSession(id string) *FTPSession {
	return &FTPSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "ftp",
			status:      StatusDisconnected,
		},
		localFSOps: newLocalFSOps(),
		cwd:        "/",
		transfers:  make(map[string]*TransferTask),
	}
}

func (s *FTPSession) Connect(config ConnectionConfig) error {
	s.setStatus(StatusConnecting)
	s.title = fmt.Sprintf("%s@%s", config.User, config.Host)

	addr := fmt.Sprintf("%s:%d", config.Host, config.Port)
	if config.Port <= 0 {
		addr = fmt.Sprintf("%s:21", config.Host)
	}

	encryption := config.FtpEncryption
	if encryption == "" {
		encryption = "none"
	}

	tlsConfig := &tls.Config{
		InsecureSkipVerify: config.FtpSkipVerify,
	}

	var conn *ftp.ServerConn
	var err error

	switch encryption {
	case "required":
		conn, err = ftp.Dial(addr,
			ftp.DialWithTimeout(30*time.Second),
			ftp.DialWithExplicitTLS(tlsConfig),
		)
		if err != nil {
			s.setStatus(StatusError)
			return fmt.Errorf("ftp dial (TLS required): %w", err)
		}
	case "auto":
		conn, err = ftp.Dial(addr,
			ftp.DialWithTimeout(30*time.Second),
			ftp.DialWithExplicitTLS(tlsConfig),
		)
		if err != nil {
			// Fall back to plain FTP
			conn, err = ftp.Dial(addr, ftp.DialWithTimeout(30*time.Second))
		}
	default: // "none"
		conn, err = ftp.Dial(addr, ftp.DialWithTimeout(30*time.Second))
	}

	if err != nil {
		s.setStatus(StatusError)
		return fmt.Errorf("ftp dial: %w", err)
	}

	if err := conn.Login(config.User, config.Password); err != nil {
		conn.Quit()
		s.setStatus(StatusError)
		return fmt.Errorf("ftp login: %w", err)
	}

	s.conn = conn
	s.cwd = "/"
	s.setStatus(StatusConnected)
	// One-shot session log warning when the user has opted in to
	// InsecureSkipVerify. Surfaces the MITM risk in the session feed so
	// it can't be silently enabled by a forgotten checkbox.
	if config.FtpSkipVerify && encryption != "none" {
		s.emitData([]byte("\x1b[33m[FTP TLS verify disabled - connection is vulnerable to MITM]\x1b[0m\r\n"))
	}
	return nil
}

func (s *FTPSession) Write(data []byte) error {
	return nil
}

func (s *FTPSession) Resize(cols, rows int) error {
	return nil
}

func (s *FTPSession) Disconnect() error {
	// Serialize close against in-flight data transfers and ChangeRemoteDir
	// (which also touches s.conn without holding connMu — see SESSION-15).
	// Without connMu here, ftp.ServerConn.Quit() can race a concurrent
	// Stor/Retr and panic inside the FTP library.
	s.connMu.Lock()
	defer s.connMu.Unlock()
	if s.conn != nil {
		s.conn.Quit()
		s.conn = nil
	}
	s.setStatus(StatusDisconnected)
	return nil
}

func (s *FTPSession) IsConnected() bool {
	return s.Status() == StatusConnected && s.conn != nil
}

// --- Internal helpers ---

func (s *FTPSession) nextTaskID(prefix string) string {
	return fmt.Sprintf("%s-%d", prefix, atomic.AddInt64(&s.taskSeq, 1))
}

func (s *FTPSession) requireClient() error {
	if s.conn == nil {
		return fmt.Errorf("FTP session not connected")
	}
	return nil
}

func (s *FTPSession) requireConn() (*ftp.ServerConn, error) {
	if s.conn == nil {
		return nil, fmt.Errorf("FTP session not connected")
	}
	return s.conn, nil
}

// --- Public API methods ---

func (s *FTPSession) ListRemote(dir string) (FileListResult, error) {
	if err := s.requireClient(); err != nil {
		return FileListResult{}, err
	}
	s.connMu.Lock()
	defer s.connMu.Unlock()
	if dir == "" {
		dir = s.cwd
	} else if !path.IsAbs(dir) {
		dir = path.Join(s.cwd, dir)
	}
	entries, err := s.conn.List(dir)
	if err != nil {
		return FileListResult{}, err
	}
	files := make([]FileItem, 0, len(entries))
	for _, e := range entries {
		isDir := e.Type == ftp.EntryTypeFolder
		modTime := ""
		if !e.Time.IsZero() {
			modTime = e.Time.Format(time.RFC3339)
		}
		files = append(files, FileItem{
			Name:    e.Name,
			Size:    int64(e.Size),
			ModTime: modTime,
			Mode:    ftpEntryMode(e),
			IsDir:   isDir,
		})
	}
	return FileListResult{Files: files, Dir: dir}, nil
}

func ftpEntryMode(e *ftp.Entry) string {
	switch e.Type {
	case ftp.EntryTypeFolder:
		return "drwxr-xr-x"
	case ftp.EntryTypeLink:
		return "Lrwxrwxrwx"
	default:
		return "-rw-r--r--"
	}
}

func (s *FTPSession) ChangeRemoteDir(dir string) (FileListResult, error) {
	if err := s.requireClient(); err != nil {
		return FileListResult{}, err
	}
	target := dir
	if !path.IsAbs(dir) {
		target = path.Join(s.cwd, dir)
	}
	// Validate directory exists by listing it — must hold connMu because
	// the FTP control connection is not concurrent-safe (SESSION-15).
	s.connMu.Lock()
	entries, err := s.conn.List(target)
	s.connMu.Unlock()
	if err != nil {
		return FileListResult{}, fmt.Errorf("no such directory: %s", target)
	}
	s.mu.Lock()
	s.cwd = target
	s.mu.Unlock()
	files := make([]FileItem, 0, len(entries))
	for _, e := range entries {
		isDir := e.Type == ftp.EntryTypeFolder
		modTime := ""
		if !e.Time.IsZero() {
			modTime = e.Time.Format(time.RFC3339)
		}
		files = append(files, FileItem{
			Name:    e.Name,
			Size:    int64(e.Size),
			ModTime: modTime,
			Mode:    ftpEntryMode(e),
			IsDir:   isDir,
		})
	}
	return FileListResult{Files: files, Dir: target}, nil
}


// Symlink is not supported: the FTP protocol has no link semantics.
func (s *FTPSession) Symlink(_, _ string) error {
	return fmt.Errorf("symlink is not supported by FTP")
}

func (s *FTPSession) MakeDir(dir string) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	s.connMu.Lock()
	defer s.connMu.Unlock()
	p := dir
	if !path.IsAbs(p) {
		p = path.Join(s.cwd, p)
	}
	return s.conn.MakeDir(p)
}

func (s *FTPSession) Remove(p string, recursive bool) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	s.connMu.Lock()
	defer s.connMu.Unlock()
	if !path.IsAbs(p) {
		p = path.Join(s.cwd, p)
	}
	if recursive {
		return s.rmRecursive(p)
	}
	// Try file deletion first; if that fails (e.g. it's a directory), try RemoveDir
	err := s.conn.Delete(p)
	if err == nil {
		return nil
	}
	// Not a plain file — check if it's an empty directory
	entries, listErr := s.conn.List(p)
	if listErr == nil && len(entries) > 0 {
		return fmt.Errorf("directory not empty (%d items), use recursive=true", len(entries))
	}
	return s.conn.RemoveDir(p)
}

func (s *FTPSession) Rename(oldName, newName string) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	s.connMu.Lock()
	defer s.connMu.Unlock()
	old := oldName
	if !path.IsAbs(old) {
		old = path.Join(s.cwd, old)
	}
	newPath := newName
	if !path.IsAbs(newPath) {
		newPath = path.Join(s.cwd, newPath)
	}
	return s.conn.Rename(old, newPath)
}

func (s *FTPSession) Chmod(p string, mode os.FileMode) error {
	return fmt.Errorf("FTP does not support chmod")
}

func (s *FTPSession) Get(remotePath, localPath string, recursive bool) (string, error) {
	if err := s.requireClient(); err != nil {
		return "", err
	}
	rp := remotePath
	if !path.IsAbs(rp) {
		rp = path.Join(s.cwd, rp)
	}
	lp := localPath
	if !filepath.IsAbs(lp) {
		lp = filepath.Join(s.localCwd, lp)
	}
	if recursive {
		total, err := s.dirSizeRemote(rp)
		if err != nil {
			return "", err
		}
		task := &TransferTask{
			ID:         s.nextTaskID("dl"),
			Type:       "download",
			LocalPath:  lp,
			RemotePath: rp,
			Total:      total,
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
			if err := s.downloadDir(rp, lp, task); err != nil {
				s.emitTransferEvent(task, err)
				return
			}
			task.Status = "done"
			s.emitTransferComplete(task)
		}()
		return task.ID, nil
	}
	task := &TransferTask{
		ID:         s.nextTaskID("dl"),
		Type:       "download",
		LocalPath:  lp,
		RemotePath: rp,
		Status:     "pending",
	}
	s.startTransfer(task)
	return task.ID, nil
}

func (s *FTPSession) Put(localPath, remotePath string, recursive bool) (string, error) {
	if err := s.requireClient(); err != nil {
		return "", err
	}
	lp := localPath
	if !filepath.IsAbs(lp) {
		lp = filepath.Join(s.localCwd, lp)
	}
	rp := remotePath
	if !path.IsAbs(rp) {
		rp = path.Join(s.cwd, rp)
	}
	if recursive {
		total, err := s.dirSizeLocal(lp)
		if err != nil {
			return "", err
		}
		task := &TransferTask{
			ID:         s.nextTaskID("ul"),
			Type:       "upload",
			LocalPath:  lp,
			RemotePath: rp,
			Total:      total,
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
			if err := s.uploadDir(lp, rp, task); err != nil {
				s.emitTransferEvent(task, err)
				return
			}
			task.Status = "done"
			s.emitTransferComplete(task)
		}()
		return task.ID, nil
	}
	task := &TransferTask{
		ID:         s.nextTaskID("ul"),
		Type:       "upload",
		LocalPath:  lp,
		RemotePath: rp,
		Status:     "pending",
	}
	s.startTransfer(task)
	return task.ID, nil
}

// PutContent writes raw content directly to a remote file via FTP.
func (s *FTPSession) PutContent(remotePath string, content []byte) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	rp := remotePath
	if !path.IsAbs(rp) {
		rp = path.Join(s.cwd, rp)
	}
	// Ensure parent directory exists
	parentDir := path.Dir(rp)
	if err := s.mkdirAllRemote(parentDir); err != nil {
		return err
	}
	reader := strings.NewReader(string(content))
	return s.conn.Stor(rp, reader)
}

// GetContent reads the full content of a remote file via FTP.
func (s *FTPSession) GetContent(remotePath string) ([]byte, error) {
	if err := s.requireClient(); err != nil {
		return nil, err
	}
	s.connMu.Lock()
	defer s.connMu.Unlock()
	rp := remotePath
	if !path.IsAbs(rp) {
		rp = path.Join(s.cwd, rp)
	}
	r, err := s.conn.Retr(rp)
	if err != nil {
		return nil, err
	}
	defer r.Close()
	return io.ReadAll(r)
}

// Copy copies a remote file via FTP (download + re-upload — FTP has no server-side copy).
func (s *FTPSession) Copy(oldPath, newPath string) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	s.connMu.Lock()
	defer s.connMu.Unlock()
	old := oldPath
	if !path.IsAbs(old) {
		old = path.Join(s.cwd, old)
	}
	n := newPath
	if !path.IsAbs(n) {
		n = path.Join(s.cwd, n)
	}
	// FTP cannot copy directories via Retr, check first
	if _, listErr := s.conn.List(old); listErr == nil {
		return fmt.Errorf("cannot copy directory via FTP: %s", old)
	}
	// Download
	r, err := s.conn.Retr(old)
	if err != nil {
		return err
	}
	defer r.Close()
	data, err := io.ReadAll(r)
	if err != nil {
		return err
	}
	// Create parent directories for destination
	parentDir := path.Dir(n)
	if err := s.mkdirAllRemote(parentDir); err != nil {
		return err
	}
	// Upload
	return s.conn.Stor(n, strings.NewReader(string(data)))
}

// Move moves a remote file via FTP Rename (server-side, no data transfer).
func (s *FTPSession) Move(oldPath, newPath string) error {
	return s.Rename(oldPath, newPath)
}

// mkdirAllRemote creates intermediate directories as needed.
func (s *FTPSession) mkdirAllRemote(dir string) error {
	if dir == "/" || dir == "." || dir == "" {
		return nil
	}
	// Try to list the directory; if it fails, create parent then this one
	_, err := s.conn.List(dir)
	if err == nil {
		return nil // already exists
	}
	// Create parent first
	if err := s.mkdirAllRemote(path.Dir(dir)); err != nil {
		return err
	}
	return s.conn.MakeDir(dir)
}

// CancelTransfer cancels an ongoing transfer task.
func (s *FTPSession) CancelTransfer(taskID string) error {
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

// PauseTransfer pauses an ongoing transfer task.
func (s *FTPSession) PauseTransfer(taskID string) error {
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

// ResumeTransfer resumes a paused transfer task.
func (s *FTPSession) ResumeTransfer(taskID string) error {
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

// --- Recursive helpers ---

func (s *FTPSession) rmRecursive(p string) error {
	entries, err := s.conn.List(p)
	if err != nil {
		// Not a directory or cannot list; try deleting as file
		return s.conn.Delete(p)
	}
	for _, e := range entries {
		childPath := path.Join(p, e.Name)
		if e.Type == ftp.EntryTypeFolder {
			if err := s.rmRecursive(childPath); err != nil {
				return err
			}
		} else {
			if err := s.conn.Delete(childPath); err != nil {
				return err
			}
		}
	}
	return s.conn.RemoveDir(p)
}

func (s *FTPSession) dirSizeRemote(dir string) (int64, error) {
	entries, err := s.conn.List(dir)
	if err != nil {
		return 0, err
	}
	var total int64
	for _, e := range entries {
		if e.Type == ftp.EntryTypeFolder {
			sz, err := s.dirSizeRemote(path.Join(dir, e.Name))
			if err != nil {
				return 0, err
			}
			total += sz
		} else {
			total += int64(e.Size)
		}
	}
	return total, nil
}

func (s *FTPSession) dirSizeLocal(dir string) (int64, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return 0, err
	}
	var total int64
	for _, e := range entries {
		if e.IsDir() {
			sz, err := s.dirSizeLocal(filepath.Join(dir, e.Name()))
			if err != nil {
				return 0, err
			}
			total += sz
		} else {
			fi, err := e.Info()
			if err != nil {
				return 0, err
			}
			total += fi.Size()
		}
	}
	return total, nil
}

// --- Transfer methods ---

func (s *FTPSession) startTransfer(task *TransferTask) {
	task.start()
	s.mu.Lock()
	s.transfers[task.ID] = task
	s.mu.Unlock()
	go func() {
		defer func() {
			task.done()
			s.mu.Lock()
			delete(s.transfers, task.ID)
			s.mu.Unlock()
		}()

		task.Status = "running"
		s.emitTransferStart(task)

		// FTP control connection: serialize data transfers
		s.connMu.Lock()
		defer s.connMu.Unlock()

		var err error
		if task.Type == "download" {
			resp, e := s.conn.Retr(task.RemotePath)
			if e != nil {
				s.emitTransferEvent(task, e)
				return
			}
			defer resp.Close()

			fi, e := s.conn.FileSize(task.RemotePath)
			if e == nil && fi > 0 {
				task.setTotal(fi)
			}

			localFile, e := os.Create(task.LocalPath)
			if e != nil {
				s.emitTransferEvent(task, e)
				return
			}
			defer localFile.Close()

			_, err = io.Copy(localFile, &progressReader{r: resp, task: task, s: s})
		} else {
			localFile, e := os.Open(task.LocalPath)
			if e != nil {
				s.emitTransferEvent(task, e)
				return
			}
			defer localFile.Close()

			fi, _ := localFile.Stat()
			if fi != nil {
				task.setTotal(fi.Size())
			}

			err = s.conn.Stor(task.RemotePath, &progressReader{r: localFile, task: task, s: s})
		}

		if err != nil {
			s.emitTransferEvent(task, err)
			return
		}
		task.Status = "done"
		s.emitTransferComplete(task)
	}()
}

type progressReader struct {
	r    io.Reader
	task *TransferTask
	s    *FTPSession
}

func (pr *progressReader) Read(p []byte) (int, error) {
	pr.task.waitIfPaused()
	n, err := pr.r.Read(p)
	if n > 0 {
		pr.task.addProgress(int64(n))
		pr.s.emitTransferProgress(pr.task)
	}
	return n, err
}

// --- Recursive transfer ---

func (s *FTPSession) downloadDir(remoteDir, localDir string, task *TransferTask) error {
	select {
	case <-task.ctx.Done():
		return task.ctx.Err()
	default:
	}
	if err := os.MkdirAll(localDir, 0755); err != nil {
		return err
	}
	entries, err := s.conn.List(remoteDir)
	if err != nil {
		return err
	}
	for _, e := range entries {
		rp := path.Join(remoteDir, e.Name)
		lp := filepath.Join(localDir, e.Name)
		if e.Type == ftp.EntryTypeFolder {
			if err := s.downloadDir(rp, lp, task); err != nil {
				return err
			}
		} else {
			if err := s.transferFile(task, lp, rp, "download"); err != nil {
				return err
			}
		}
	}
	return nil
}

func (s *FTPSession) uploadDir(localDir, remoteDir string, task *TransferTask) error {
	select {
	case <-task.ctx.Done():
		return task.ctx.Err()
	default:
	}
	if err := s.mkdirAllRemote(remoteDir); err != nil {
		return err
	}
	entries, err := os.ReadDir(localDir)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		rp := path.Join(remoteDir, entry.Name())
		lp := filepath.Join(localDir, entry.Name())
		if entry.IsDir() {
			if err := s.uploadDir(lp, rp, task); err != nil {
				return err
			}
		} else {
			if err := s.transferFile(task, lp, rp, "upload"); err != nil {
				return err
			}
		}
	}
	return nil
}

func (s *FTPSession) transferFile(task *TransferTask, localPath, remotePath, tfType string) error {
	if tfType == "download" {
		resp, err := s.conn.Retr(remotePath)
		if err != nil {
			return err
		}
		defer resp.Close()
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
			n, e := resp.Read(buf)
			if n > 0 {
				dst.Write(buf[:n])
				task.addProgress(int64(n))
				s.emitTransferProgress(task)
			}
			if e != nil {
				break
			}
		}
	} else {
		src, err := os.Open(localPath)
		if err != nil {
			return err
		}
		defer src.Close()
		pr, pw := io.Pipe()
		doneCh := make(chan error, 1)
		go func() {
			doneCh <- s.conn.Stor(remotePath, pr)
		}()
		buf := make([]byte, 64*1024)
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
				_, we := pw.Write(buf[:n])
				if we != nil {
					pw.Close()
					return we
				}
				task.addProgress(int64(n))
				s.emitTransferProgress(task)
			}
			if e != nil {
				break
			}
		}
		pw.Close()
		// Wait for Stor to complete
		if err := <-doneCh; err != nil {
			return err
		}
	}
	return nil
}

