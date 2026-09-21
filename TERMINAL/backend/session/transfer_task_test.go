package session

import (
	"errors"
	"sync"
	"testing"
)

func TestTransferTaskFileState(t *testing.T) {
	task := &TransferTask{ID: "dl-1", Type: "download"}
	task.SetSkip([]string{"already/done.txt"})
	if !task.shouldSkip("already/done.txt") || task.shouldSkip("other.txt") {
		t.Fatal("skip set mismatch")
	}
	task.setFileCount(3)
	if task.fileCount() != 3 {
		t.Fatal("fileCount")
	}
	task.beginFile("a.txt")
	task.finishFile("a.txt")
	task.failFile("b.txt", errors.New("denied"))
	if task.completedCount() != 1 {
		t.Fatalf("completed = %d", task.completedCount())
	}
	if len(task.FailedFiles) != 1 || task.FailedFiles[0].Path != "b.txt" || task.FailedFiles[0].Error != "denied" {
		t.Fatalf("FailedFiles = %v", task.FailedFiles)
	}
}

func TestTransferTaskConcurrentProgress(t *testing.T) {
	task := &TransferTask{ID: "dl-2"}
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 1000; j++ {
				task.addProgress(1)
			}
		}()
	}
	wg.Wait()
	if task.loadProgress() != 8000 {
		t.Fatalf("progress = %d, want 8000", task.loadProgress())
	}
}
