package session

import (
	"fmt"
	"testing"
)

// TestPauseResumeEvents checks the dedicated paused/resumed event payloads.
func TestPauseResumeEvents(t *testing.T) {
	var events []string
	TransferEventSink = func(sid string, p map[string]any) {
		if sid != "s1" {
			t.Fatalf("sessionId = %q, want s1", sid)
		}
		events = append(events, p["event"].(string))
	}
	defer func() { TransferEventSink = nil }()

	s := &baseSession{id: "s1", sessionType: "sftp", status: StatusConnected}
	task := &TransferTask{ID: "t1", Type: "download", Status: "running"}
	task.start()
	defer task.done()

	task.Status = "paused"
	s.emitTransferPaused(task)
	task.Status = "running"
	s.emitTransferResumed(task)

	if len(events) != 2 || events[0] != "paused" || events[1] != "resumed" {
		t.Fatalf("events = %v, want [paused resumed]", events)
	}
}

// pauseResumer matches the Pause/Resume surface shared by the transfer
// backends under test.
type pauseResumer interface {
	PauseTransfer(taskID string) error
	ResumeTransfer(taskID string) error
}

// putTransferTask registers task in a session's transfers map so the
// Pause/Resume entry points can find it.
func putTransferTask(s any, task *TransferTask) {
	switch v := s.(type) {
	case *SFTPSession:
		v.mu.Lock()
		v.transfers[task.ID] = task
		v.mu.Unlock()
	case *SCPSession:
		v.mu.Lock()
		v.transfers[task.ID] = task
		v.mu.Unlock()
	default:
		panic(fmt.Sprintf("putTransferTask: unsupported session %T", s))
	}
}

// TestPauseResumeTransferLifecycle drives PauseTransfer/ResumeTransfer through
// both backends: pausing must emit the dedicated "paused" event (not a fake
// "complete"), resuming must emit "resumed", and resuming a task that is not
// paused (e.g. already done) must fail without emitting anything.
func TestPauseResumeTransferLifecycle(t *testing.T) {
	for _, tc := range []struct {
		name string
		sess pauseResumer
	}{
		{"sftp", NewSFTPSession("s1")},
		{"scp", NewSCPSession("s2")},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var events []string
			TransferEventSink = func(sid string, p map[string]any) {
				events = append(events, p["event"].(string))
			}
			defer func() { TransferEventSink = nil }()

			task := &TransferTask{ID: "t-live", Type: "download", Status: "running"}
			task.start()
			defer task.done()
			putTransferTask(tc.sess, task)

			// Pause: honest "paused" event, status flipped, no fake "complete".
			if err := tc.sess.PauseTransfer("t-live"); err != nil {
				t.Fatalf("PauseTransfer: %v", err)
			}
			if task.Status != "paused" {
				t.Fatalf("status after pause = %q, want paused", task.Status)
			}
			if len(events) != 1 || events[0] != "paused" {
				t.Fatalf("events after pause = %v, want [paused]", events)
			}

			// Resume: back to running with a "resumed" event.
			if err := tc.sess.ResumeTransfer("t-live"); err != nil {
				t.Fatalf("ResumeTransfer: %v", err)
			}
			if task.Status != "running" {
				t.Fatalf("status after resume = %q, want running", task.Status)
			}
			if len(events) != 2 || events[1] != "resumed" {
				t.Fatalf("events after resume = %v, want [..., resumed]", events)
			}

			// Resuming a finished task must be rejected and stay silent.
			task.Status = "done"
			events = nil
			if err := tc.sess.ResumeTransfer("t-live"); err == nil {
				t.Fatal("ResumeTransfer on done task: want error, got nil")
			}
			if task.Status != "done" {
				t.Fatalf("status after rejected resume = %q, want done", task.Status)
			}
			if len(events) != 0 {
				t.Fatalf("rejected resume emitted %v, want none", events)
			}
		})
	}
}
