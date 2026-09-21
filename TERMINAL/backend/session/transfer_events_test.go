package session

import (
	"strings"
	"testing"
	"time"
)

func TestEmitTransferEventsUseSink(t *testing.T) {
	var got []map[string]any
	TransferEventSink = func(sid string, payload map[string]any) {
		if sid != "s1" {
			t.Fatalf("sessionId = %q, want s1", sid)
		}
		got = append(got, payload)
	}
	defer func() { TransferEventSink = nil }()

	s := &baseSession{id: "s1", sessionType: "sftp", status: StatusConnected}
	task := &TransferTask{ID: "dl-1", Type: "download", RemotePath: "/a/b.txt", LocalPath: `C:\x\b.txt`, Status: "running", Total: 10}
	s.emitTransferStart(task)
	s.emitTransferProgress(task)
	task.Status = "done"
	s.emitTransferComplete(task)

	if len(got) != 3 {
		t.Fatalf("got %d events, want 3", len(got))
	}
	start := got[0]
	if start["event"] != "start" || start["taskId"] != "dl-1" || start["sessionId"] != "s1" || start["name"] != "b.txt" {
		t.Fatalf("bad start payload: %v", start)
	}
	if _, ok := start["sessionId"]; !ok {
		t.Fatal("payload must carry sessionId")
	}
	if !strings.Contains(start["type"].(string), "sftp:transfer") {
		t.Fatalf("payload must carry type sftp:transfer, got %v", start["type"])
	}
	complete := got[2]
	if complete["status"] != "done" {
		t.Fatalf("bad complete payload: %v", complete)
	}
}

func TestProgressThrottle(t *testing.T) {
	var n int
	TransferEventSink = func(sid string, payload map[string]any) {
		if payload["event"] == "progress" {
			n++
		}
	}
	defer func() { TransferEventSink = nil }()
	progressLast = map[string]time.Time{} // reset

	s := &baseSession{id: "s1", sessionType: "sftp", status: StatusConnected}
	task := &TransferTask{ID: "dl-2", Type: "download", RemotePath: "/a", Total: 100}
	s.emitTransferProgress(task)
	s.emitTransferProgress(task) // within 100ms — dropped
	s.emitTransferProgressForced(task)
	if n != 2 {
		t.Fatalf("progress events = %d, want 2 (first + forced)", n)
	}
}
