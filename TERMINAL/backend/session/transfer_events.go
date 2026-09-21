package session

import (
	"path"
	"path/filepath"
	"sync"
	"time"
)

// TransferEventSink is installed by the App layer at startup. File-transfer
// backends publish progress through it as Wails events ("sftp:transfer")
// instead of embedding OSC-633 sequences into the terminal data stream.
var TransferEventSink func(sessionID string, payload map[string]any)

// FileFailure records one file that failed inside a directory transfer.
type FileFailure struct {
	Path  string `json:"path"`
	Error string `json:"error"`
}

const progressMinInterval = 100 * time.Millisecond

var (
	progressMu   sync.Mutex
	progressLast = map[string]time.Time{}
)

func transferDisplayName(task *TransferTask) string {
	if task.Type == "download" {
		return path.Base(task.RemotePath)
	}
	return filepath.Base(task.LocalPath)
}

func (s *baseSession) emitTransferPayload(payload map[string]any) {
	if TransferEventSink == nil {
		return
	}
	payload["type"] = "sftp:transfer"
	payload["sessionId"] = s.id
	TransferEventSink(s.id, payload)
}

func (s *baseSession) emitTransferStart(task *TransferTask) {
	s.emitTransferPayload(map[string]any{
		"taskId": task.ID, "event": "start", "tfType": task.Type,
		"name": transferDisplayName(task), "total": task.loadTotal(),
		"localPath": task.LocalPath, "remotePath": task.RemotePath,
		"fileCount": task.fileCount(),
	})
}

func (s *baseSession) emitTransferProgress(task *TransferTask) {
	progressMu.Lock()
	last, ok := progressLast[task.ID]
	now := time.Now()
	if ok && now.Sub(last) < progressMinInterval {
		progressMu.Unlock()
		return
	}
	progressLast[task.ID] = now
	progressMu.Unlock()
	s.emitTransferProgressForced(task)
}

// emitTransferProgressForced bypasses the throttle (final updates).
func (s *baseSession) emitTransferProgressForced(task *TransferTask) {
	s.emitTransferPayload(map[string]any{
		"taskId": task.ID, "event": "progress",
		"progress": task.loadProgress(), "total": task.loadTotal(),
	})
}

func (s *baseSession) emitTransferComplete(task *TransferTask) {
	progressMu.Lock()
	delete(progressLast, task.ID)
	progressMu.Unlock()
	payload := map[string]any{
		"taskId": task.ID, "event": "complete", "status": task.Status,
	}
	task.fileMu.RLock()
	if task.FileCount > 0 || task.FailedFiles != nil {
		payload["failedFiles"] = task.FailedFiles
		payload["completedFiles"] = task.CompletedFiles
		payload["fileCount"] = task.FileCount
	}
	task.fileMu.RUnlock()
	s.emitTransferPayload(payload)
}

// emitTransferPaused reports that a transfer was paused. Unlike the old
// "complete" + status "paused" event this never looks finished to the UI.
func (s *baseSession) emitTransferPaused(task *TransferTask) {
	s.emitTransferPayload(map[string]any{
		"taskId": task.ID, "event": "paused",
	})
}

// emitTransferResumed reports that a paused transfer is running again.
func (s *baseSession) emitTransferResumed(task *TransferTask) {
	s.emitTransferPayload(map[string]any{
		"taskId": task.ID, "event": "resumed",
	})
}

// emitTransferEvent reports a task-level error (event "complete", status "error").
func (s *baseSession) emitTransferEvent(task *TransferTask, err error) {
	task.Status = "error"
	s.emitTransferPayload(map[string]any{
		"taskId": task.ID, "event": "complete", "status": "error", "error": err.Error(),
	})
}

// --- Per-file events (directory transfers) ---

func (s *baseSession) emitFileStart(task *TransferTask, rel, display string) {
	s.emitTransferPayload(map[string]any{
		"taskId": task.ID, "event": "file-start", "file": rel, "name": display,
		"completedFiles": task.completedCount(), "fileCount": task.fileCount(),
	})
}

func (s *baseSession) emitFileDone(task *TransferTask, rel string) {
	s.emitTransferPayload(map[string]any{
		"taskId": task.ID, "event": "file-done", "file": rel,
		"completedFiles": task.completedCount(), "fileCount": task.fileCount(),
	})
}

func (s *baseSession) emitFileFailed(task *TransferTask, rel string, err error) {
	s.emitTransferPayload(map[string]any{
		"taskId": task.ID, "event": "file-failed", "file": rel, "error": err.Error(),
		"completedFiles": task.completedCount(), "fileCount": task.fileCount(),
	})
}
