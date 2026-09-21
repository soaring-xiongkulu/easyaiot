package log

import (
	"path/filepath"
	"runtime"
	"testing"
)

func TestLogPathEndsWithLogName(t *testing.T) {
	got := logPath()
	if filepath.Base(got) != "terminal.log" {
		t.Errorf("logPath() = %q, want base name terminal.log", got)
	}
	if runtime.GOOS != "android" && !filepath.IsAbs(got) {
		t.Errorf("desktop logPath() = %q, want absolute", got)
	}
}
