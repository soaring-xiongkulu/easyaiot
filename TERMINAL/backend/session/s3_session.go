package session

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"path"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"

	"github.com/rhnvrm/simples3"
)

type S3Session struct {
	baseSession
	localFSOps
	s3        *simples3.S3
	bucket    string
	cwd       string
	mu        sync.RWMutex
	transfers map[string]*TransferTask
	taskSeq   int64
}

func NewS3Session(id string) *S3Session {
	return &S3Session{
		baseSession: baseSession{
			id:          id,
			sessionType: "s3",
			status:      StatusDisconnected,
		},
		localFSOps: newLocalFSOps(),
		cwd:        "/",
		transfers:  make(map[string]*TransferTask),
	}
}

func (s *S3Session) Connect(config ConnectionConfig) error {
	s.setStatus(StatusConnecting)
	if config.S3Bucket != "" {
		s.title = fmt.Sprintf("s3://%s", config.S3Bucket)
	} else {
		s.title = config.Host
	}

	s3Client := simples3.New(config.S3Region, config.User, config.Password)
	s3Client.Endpoint = strings.TrimSuffix(config.Host, "/")
	// S3URLStyle="" or "virtual" uses virtual-hosted URLs
	// (https://bucket.endpoint/key) — required by Alibaba Cloud OSS, Tencent
	// COS and Huawei OBS, which reject path-style requests with
	// "SecondLevelDomainForbidden" (issue #452). "path" keeps the legacy
	// path-style (https://endpoint/bucket/key) for AWS S3 and MinIO.
	if config.S3URLStyle != "path" {
		s3Client.SetVirtualHostedStyle(true)
	}

	s.s3 = s3Client
	s.bucket = config.S3Bucket
	s.cwd = "/"
	s.setStatus(StatusConnected)
	return nil
}

func (s *S3Session) Write(data []byte) error  { return nil }
func (s *S3Session) Resize(cols, rows int) error { return nil }

func (s *S3Session) Disconnect() error {
	s.s3 = nil
	s.bucket = ""
	s.setStatus(StatusDisconnected)
	return nil
}

func (s *S3Session) IsConnected() bool {
	return s.Status() == StatusConnected && s.s3 != nil
}

func (s *S3Session) requireClient() error {
	if s.s3 == nil {
		return fmt.Errorf("S3 session not connected")
	}
	return nil
}

func (s *S3Session) resolveRemote(p string) (string, error) {
	if p == "" {
		return s.cwd, nil
	}
	if path.IsAbs(p) {
		return p, nil
	}
	return path.Join(s.cwd, p), nil
}

func (s *S3Session) s3Key(p string) string {
	// S3 keys don't start with "/", they're relative to the bucket root.
	p = strings.TrimPrefix(p, "/")
	// Bucket root: path equals the bucket name → empty key
	if s.bucket != "" && p == s.bucket {
		return ""
	}
	// Strip bucket name prefix from subdirectory paths (e.g. "mybucket/dir" → "dir")
	if s.bucket != "" {
		bucketPrefix := s.bucket + "/"
		p = strings.TrimPrefix(p, bucketPrefix)
	}
	return p
}

func (s *S3Session) nextTaskID(prefix string) string {
	return fmt.Sprintf("%s-%d", prefix, atomic.AddInt64(&s.taskSeq, 1))
}

func (s *S3Session) ListRemote(dir string) (FileListResult, error) {
	if err := s.requireClient(); err != nil {
		return FileListResult{}, err
	}

	// If no bucket specified, list all buckets
	if s.bucket == "" {
		resp, err := s.s3.ListBuckets(simples3.ListBucketsInput{})
		if err != nil {
			return FileListResult{}, err
		}
		files := make([]FileItem, 0, len(resp.Buckets))
		for _, b := range resp.Buckets {
			files = append(files, FileItem{
				Name:    b.Name,
				Size:    0,
				ModTime: b.CreationDate.Format("2006-01-02T15:04:05Z"),
				Mode:    "drwxr-xr-x",
				IsDir:   true,
			})
		}
		return FileListResult{Files: files, Dir: "/"}, nil
	}

	target, err := s.resolveRemote(dir)
	if err != nil {
		return FileListResult{}, err
	}

	prefix := s.s3Key(target)
	if prefix != "" && !strings.HasSuffix(prefix, "/") {
		prefix += "/"
	}

	input := simples3.ListInput{
		Bucket:    s.bucket,
		Prefix:    prefix,
		Delimiter: "/",
	}
	resp, err := s.s3.List(input)
	if err != nil {
		return FileListResult{}, err
	}

	files := make([]FileItem, 0, len(resp.Objects)+len(resp.CommonPrefixes))

	// Process common prefixes (directories)
	for _, pfx := range resp.CommonPrefixes {
		name := strings.TrimPrefix(pfx, prefix)
		name = strings.TrimSuffix(name, "/")
		if name == "" {
			continue
		}
		files = append(files, FileItem{
			Name:    name,
			Size:    0,
			ModTime: "",
			Mode:    "drwxr-xr-x",
			IsDir:   true,
		})
	}

	// Process objects (files and directory markers)
	for _, obj := range resp.Objects {
		name := strings.TrimPrefix(obj.Key, prefix)
		if name == "" || strings.HasSuffix(name, "/") {
			// Skip the directory itself or directory marker objects
			continue
		}
		files = append(files, FileItem{
			Name:    name,
			Size:    obj.Size,
			ModTime: obj.LastModified,
			Mode:    "-rw-r--r--",
			IsDir:   false,
		})
	}

	return FileListResult{Files: files, Dir: target}, nil
}

func (s *S3Session) ChangeRemoteDir(dir string) (FileListResult, error) {
	if err := s.requireClient(); err != nil {
		return FileListResult{}, err
	}
	target, err := s.resolveRemote(dir)
	if err != nil {
		return FileListResult{}, err
	}

	// ── Bucket list level ──
	if s.bucket == "" {
		if target == "/" {
			return s.ListRemote("/") // refresh bucket list
		}
		// Enter a bucket
		bucketName := strings.TrimPrefix(target, "/")
		s.mu.Lock()
		s.bucket = bucketName
		s.cwd = "/" + bucketName
		s.mu.Unlock()
		return s.ListRemote("/" + bucketName)
	}

	// ── Inside a bucket ──
	bucketRoot := "/" + s.bucket

	// "/" inside a bucket means the bucket list root
	if target == "/" {
		s.mu.Lock()
		s.bucket = ""
		s.cwd = "/"
		s.mu.Unlock()
		return s.ListRemote("/")
	}

	// Navigate to bucket root via breadcrumb or direct path
	if target == bucketRoot {
		s.mu.Lock()
		s.cwd = bucketRoot
		s.mu.Unlock()
		return s.ListRemote(bucketRoot)
	}

	// ".." navigation within the bucket
	if dir == ".." {
		parent := path.Dir(s.cwd)
		s.mu.Lock()
		s.cwd = parent
		s.mu.Unlock()
		return s.ListRemote(parent)
	}

	// Validate directory exists by listing it
	prefix := s.s3Key(target)
	if prefix != "" && !strings.HasSuffix(prefix, "/") {
		prefix += "/"
	}
	input := simples3.ListInput{
		Bucket:    s.bucket,
		Prefix:    prefix,
		Delimiter: "/",
		MaxKeys:   1,
	}
	resp, err := s.s3.List(input)
	if err != nil {
		return FileListResult{}, fmt.Errorf("no such directory: %s", target)
	}
	if len(resp.Objects) == 0 && len(resp.CommonPrefixes) == 0 && prefix != "" {
		// Could be a "virtual" directory (no marker object). Allow it.
	}

	s.mu.Lock()
	s.cwd = target
	s.mu.Unlock()
	return s.ListRemote(target)
}

// Symlink is not supported: object storage has no links.
func (s *S3Session) Symlink(_, _ string) error {
	return fmt.Errorf("symlink is not supported by S3")
}

func (s *S3Session) MakeDir(dir string) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	p, err := s.resolveRemote(dir)
	if err != nil {
		return err
	}
	key := s.s3Key(p)
	if key != "" && !strings.HasSuffix(key, "/") {
		key += "/"
	}
	// Create an empty directory marker object
	input := simples3.UploadInput{
		Bucket:      s.bucket,
		ObjectKey:   key,
		ContentType: "application/x-directory",
		Body:        bytes.NewReader([]byte{}),
	}
	_, err = s.s3.FilePut(input)
	return err
}

func (s *S3Session) Remove(p string, recursive bool) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	target, err := s.resolveRemote(p)
	if err != nil {
		return err
	}

	key := s.s3Key(target)

	if recursive {
		// List all objects with this prefix and delete them
		prefix := key
		if prefix != "" && !strings.HasSuffix(prefix, "/") {
			prefix += "/"
		}
		input := simples3.ListInput{
			Bucket: s.bucket,
			Prefix: prefix,
		}
		resp, err := s.s3.List(input)
		if err != nil {
			return err
		}
		for _, obj := range resp.Objects {
			if err := s.s3.FileDelete(simples3.DeleteInput{
				Bucket:    s.bucket,
				ObjectKey: obj.Key,
			}); err != nil {
				return err
			}
		}
		// Also delete the prefix marker object if it exists
		s.s3.FileDelete(simples3.DeleteInput{
			Bucket:    s.bucket,
			ObjectKey: key,
		})
		// And the directory marker
		if key != "" {
			s.s3.FileDelete(simples3.DeleteInput{
				Bucket:    s.bucket,
				ObjectKey: key + "/",
			})
		}
		return nil
	}

	// Non-recursive: try file first, then directory marker
	err = s.s3.FileDelete(simples3.DeleteInput{
		Bucket:    s.bucket,
		ObjectKey: key,
	})
	if err == nil {
		return nil
	}

	// Try with trailing slash (directory marker)
	if key != "" {
		err2 := s.s3.FileDelete(simples3.DeleteInput{
			Bucket:    s.bucket,
			ObjectKey: key + "/",
		})
		if err2 == nil {
			// Check if directory with this prefix has any contents
			prefix := key + "/"
			input := simples3.ListInput{
				Bucket:    s.bucket,
				Prefix:    prefix,
				Delimiter: "/",
				MaxKeys:   1,
			}
			resp, _ := s.s3.List(input)
			if len(resp.Objects) > 0 || len(resp.CommonPrefixes) > 0 {
				// Re-create the directory marker since it had contents
				s.s3.FilePut(simples3.UploadInput{
					Bucket:      s.bucket,
					ObjectKey:   prefix,
					ContentType: "application/x-directory",
					Body:        bytes.NewReader([]byte{}),
				})
				return fmt.Errorf("directory not empty")
			}
			return nil
		}
	}
	return err
}

func (s *S3Session) Rename(oldName, newName string) error {
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

	oldKey := s.s3Key(old)
	newKey := s.s3Key(n)

	// Check if source is a directory
	isDir := false
	prefix := oldKey
	if prefix != "" && !strings.HasSuffix(prefix, "/") {
		prefix += "/"
	}
	input := simples3.ListInput{
		Bucket:    s.bucket,
		Prefix:    prefix,
		MaxKeys:   1,
	}
	resp, err := s.s3.List(input)
	if err != nil {
		return err
	}
	if len(resp.Objects) > 0 {
		// Has contents, treat as directory
		isDir = true
	}

	if isDir {
		// Rename all objects with this prefix
		listInput := simples3.ListInput{
			Bucket: s.bucket,
			Prefix: prefix,
		}
		listResp, err := s.s3.List(listInput)
		if err != nil {
			return err
		}
		newPrefix := newKey
		if newPrefix != "" && !strings.HasSuffix(newPrefix, "/") {
			newPrefix += "/"
		}
		for _, obj := range listResp.Objects {
			suffix := strings.TrimPrefix(obj.Key, oldKey)
			if strings.HasPrefix(suffix, "/") {
				suffix = strings.TrimPrefix(suffix, "/")
			}
			newObjKey := newPrefix + suffix
			if _, err := s.s3.CopyObject(simples3.CopyObjectInput{
				SourceBucket: s.bucket,
				SourceKey:    obj.Key,
				DestBucket:   s.bucket,
				DestKey:      newObjKey,
			}); err != nil {
				return err
			}
			if err := s.s3.FileDelete(simples3.DeleteInput{
				Bucket:    s.bucket,
				ObjectKey: obj.Key,
			}); err != nil {
				return err
			}
		}
		return nil
	}

	// File rename: copy + delete
	if _, err := s.s3.CopyObject(simples3.CopyObjectInput{
		SourceBucket: s.bucket,
		SourceKey:    oldKey,
		DestBucket:   s.bucket,
		DestKey:      newKey,
	}); err != nil {
		return err
	}
	return s.s3.FileDelete(simples3.DeleteInput{
		Bucket:    s.bucket,
		ObjectKey: oldKey,
	})
}

func (s *S3Session) Chmod(p string, mode os.FileMode) error {
	return fmt.Errorf("S3 does not support chmod")
}

func (s *S3Session) Copy(oldPath, newPath string) error {
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

	oldKey := s.s3Key(old)
	newKey := s.s3Key(n)

	// Check if source is a directory
	isDir := false
	prefix := oldKey
	if prefix != "" && !strings.HasSuffix(prefix, "/") {
		prefix += "/"
	}
	input := simples3.ListInput{
		Bucket:    s.bucket,
		Prefix:    prefix,
		MaxKeys:   1,
	}
	resp, err := s.s3.List(input)
	if err != nil {
		return err
	}
	if len(resp.Objects) > 0 {
		isDir = true
	}

	if isDir {
		// Copy all objects with this prefix
		listInput := simples3.ListInput{
			Bucket: s.bucket,
			Prefix: prefix,
		}
		listResp, err := s.s3.List(listInput)
		if err != nil {
			return err
		}
		newPrefix := newKey
		if newPrefix != "" && !strings.HasSuffix(newPrefix, "/") {
			newPrefix += "/"
		}
		for _, obj := range listResp.Objects {
			suffix := strings.TrimPrefix(obj.Key, oldKey)
			if strings.HasPrefix(suffix, "/") {
				suffix = strings.TrimPrefix(suffix, "/")
			}
			newObjKey := newPrefix + suffix
			if _, err := s.s3.CopyObject(simples3.CopyObjectInput{
				SourceBucket: s.bucket,
				SourceKey:    obj.Key,
				DestBucket:   s.bucket,
				DestKey:      newObjKey,
			}); err != nil {
				return err
			}
		}
		return nil
	}

	_, err = s.s3.CopyObject(simples3.CopyObjectInput{
		SourceBucket: s.bucket,
		SourceKey:    oldKey,
		DestBucket:   s.bucket,
		DestKey:      newKey,
	})
	return err
}

func (s *S3Session) Move(oldPath, newPath string) error {
	return s.Rename(oldPath, newPath)
}

func (s *S3Session) GetContent(remotePath string) ([]byte, error) {
	if err := s.requireClient(); err != nil {
		return nil, err
	}
	p, err := s.resolveRemote(remotePath)
	if err != nil {
		return nil, err
	}
	rc, err := s.s3.FileDownload(simples3.DownloadInput{
		Bucket:    s.bucket,
		ObjectKey: s.s3Key(p),
	})
	if err != nil {
		return nil, err
	}
	defer rc.Close()
	return io.ReadAll(rc)
}

func (s *S3Session) PutContent(remotePath string, content []byte) error {
	if err := s.requireClient(); err != nil {
		return err
	}
	p, err := s.resolveRemote(remotePath)
	if err != nil {
		return err
	}
	input := simples3.UploadInput{
		Bucket:      s.bucket,
		ObjectKey:   s.s3Key(p),
		ContentType: "application/octet-stream",
		Body:        bytes.NewReader(content),
	}
	_, err = s.s3.FilePut(input)
	return err
}

func (s *S3Session) Get(remotePath, localPath string, recursive bool) (string, error) {
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

func (s *S3Session) Put(localPath, remotePath string, recursive bool) (string, error) {
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

func (s *S3Session) CancelTransfer(taskID string) error {
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

func (s *S3Session) PauseTransfer(taskID string) error {
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

func (s *S3Session) ResumeTransfer(taskID string) error {
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

// calcRemoteDirSize recursively sums up all object sizes under a remote directory prefix.
func (s *S3Session) calcRemoteDirSize(remoteDir string) (int64, error) {
	var total int64
	prefix := s.s3Key(remoteDir)
	if prefix != "" && !strings.HasSuffix(prefix, "/") {
		prefix += "/"
	}
	input := simples3.ListInput{
		Bucket:    s.bucket,
		Prefix:    prefix,
		Delimiter: "/",
	}
	resp, err := s.s3.List(input)
	if err != nil {
		return 0, err
	}
	for _, obj := range resp.Objects {
		name := strings.TrimPrefix(obj.Key, prefix)
		if name == "" || strings.HasSuffix(name, "/") {
			continue
		}
		total += obj.Size
	}
	for _, pfx := range resp.CommonPrefixes {
		dirName := strings.TrimPrefix(pfx, prefix)
		dirName = strings.TrimSuffix(dirName, "/")
		subSize, err := s.calcRemoteDirSize(path.Join(remoteDir, dirName))
		if err != nil {
			return 0, err
		}
		total += subSize
	}
	return total, nil
}

// calcLocalDirSize recursively sums up all file sizes under a local directory.
func calcLocalDirSize(localDir string) (int64, error) {
	var total int64
	entries, err := os.ReadDir(localDir)
	if err != nil {
		return 0, err
	}
	for _, entry := range entries {
		lp := filepath.Join(localDir, entry.Name())
		if entry.IsDir() {
			subSize, err := calcLocalDirSize(lp)
			if err != nil {
				return 0, err
			}
			total += subSize
		} else {
			fi, err := entry.Info()
			if err != nil {
				return 0, err
			}
			total += fi.Size()
		}
	}
	return total, nil
}

func (s *S3Session) downloadDir(remoteDir, localDir string, task *TransferTask) error {
	// Calculate total size for progress tracking
	if task.loadTotal() <= 0 {
		if total, err := s.calcRemoteDirSize(remoteDir); err == nil {
			task.setTotal(total)
		}
	}

	if err := os.MkdirAll(localDir, 0755); err != nil {
		return err
	}

	prefix := s.s3Key(remoteDir)
	if prefix != "" && !strings.HasSuffix(prefix, "/") {
		prefix += "/"
	}
	input := simples3.ListInput{
		Bucket:    s.bucket,
		Prefix:    prefix,
		Delimiter: "/",
	}
	resp, err := s.s3.List(input)
	if err != nil {
		return err
	}

	// Download files
	for _, obj := range resp.Objects {
		select {
		case <-task.ctx.Done():
			return task.ctx.Err()
		default:
		}
		name := strings.TrimPrefix(obj.Key, prefix)
		if name == "" || strings.HasSuffix(name, "/") {
			continue
		}
		lp := filepath.Join(localDir, name)
		if err := s.downloadFile(task, path.Join(remoteDir, name), lp); err != nil {
			return err
		}
	}

	// Recurse into common prefixes
	for _, pfx := range resp.CommonPrefixes {
		select {
		case <-task.ctx.Done():
			return task.ctx.Err()
		default:
		}
		dirName := strings.TrimPrefix(pfx, prefix)
		dirName = strings.TrimSuffix(dirName, "/")
		rp := path.Join(remoteDir, dirName)
		lp := filepath.Join(localDir, dirName)
		if err := s.downloadDir(rp, lp, task); err != nil {
			return err
		}
	}

	return nil
}

func (s *S3Session) downloadFile(task *TransferTask, remotePath, localPath string) error {
	// Get file size first for progress tracking
	if task.loadTotal() <= 0 {
		details, err := s.s3.FileDetails(simples3.DetailsInput{
			Bucket:    s.bucket,
			ObjectKey: s.s3Key(remotePath),
		})
		if err == nil && details.ContentLength != "" {
			if size, parseErr := strconv.ParseInt(details.ContentLength, 10, 64); parseErr == nil {
				task.setTotal(size)
			}
		}
	}

	rc, err := s.s3.FileDownload(simples3.DownloadInput{
		Bucket:    s.bucket,
		ObjectKey: s.s3Key(remotePath),
	})
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

func (s *S3Session) uploadDir(localDir, remoteDir string, task *TransferTask) error {
	// Calculate total size for progress tracking
	if task.loadTotal() <= 0 {
		if total, err := calcLocalDirSize(localDir); err == nil {
			task.setTotal(total)
		}
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

func (s *S3Session) uploadFile(task *TransferTask, localPath, remotePath string) error {
	data, err := os.ReadFile(localPath)
	if err != nil {
		return err
	}

	// Detect content type from extension
	contentType := "application/octet-stream"
	switch strings.ToLower(filepath.Ext(localPath)) {
	case ".txt":
		contentType = "text/plain"
	case ".html", ".htm":
		contentType = "text/html"
	case ".css":
		contentType = "text/css"
	case ".js":
		contentType = "application/javascript"
	case ".json":
		contentType = "application/json"
	case ".xml":
		contentType = "application/xml"
	case ".png":
		contentType = "image/png"
	case ".jpg", ".jpeg":
		contentType = "image/jpeg"
	case ".gif":
		contentType = "image/gif"
	case ".svg":
		contentType = "image/svg+xml"
	case ".pdf":
		contentType = "application/pdf"
	case ".zip":
		contentType = "application/zip"
	}

	_, err = s.s3.FilePut(simples3.UploadInput{
		Bucket:      s.bucket,
		ObjectKey:   s.s3Key(remotePath),
		ContentType: contentType,
		Body:        bytes.NewReader(data),
	})
	if err == nil {
		task.addProgress(int64(len(data)))
		if task.loadTotal() == 0 {
			task.setTotal(int64(len(data)))
		}
		s.emitTransferProgress(task)
	}
	return err
}

