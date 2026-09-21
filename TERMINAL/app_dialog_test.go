package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestExpandDialogDir(t *testing.T) {
	home, err := os.UserHomeDir()
	if err != nil || home == "" {
		t.Skip("no home directory")
	}
	tmp := t.TempDir()
	file := filepath.Join(tmp, "a.txt")
	if err := os.WriteFile(file, []byte("x"), 0644); err != nil {
		t.Fatal(err)
	}

	tests := []struct {
		name string
		in   string
		want string
	}{
		{"empty", "", ""},
		{"tilde", "~", home},
		{"existing absolute dir", tmp, tmp},
		{"missing dir", filepath.Join(tmp, "nope"), ""},
		{"file is not a dir", file, ""},
		{"relative is rejected", "some/dir", ""},
		{"tilde to missing dir", "~/definitely-not-a-real-dir-9f3a", ""},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := expandDialogDir(tt.in); got != tt.want {
				t.Errorf("expandDialogDir(%q) = %q, want %q", tt.in, got, tt.want)
			}
		})
	}
}

// resolveDialogDir must never hand the picker a path it will silently ignore:
// the first existing candidate wins and everything else lands on home.
func TestResolveDialogDir(t *testing.T) {
	home, err := os.UserHomeDir()
	if err != nil || home == "" {
		t.Skip("no home directory")
	}
	tmp := t.TempDir()
	missing := filepath.Join(tmp, "nope")

	if got := resolveDialogDir(); got != home {
		t.Errorf("no candidates = %q, want home %q", got, home)
	}
	if got := resolveDialogDir(missing); got != home {
		t.Errorf("missing candidate = %q, want home %q", got, home)
	}
	if got := resolveDialogDir(missing, tmp); got != tmp {
		t.Errorf("fallback candidate = %q, want %q", got, tmp)
	}
	if got := resolveDialogDir(tmp, home); got != tmp {
		t.Errorf("first candidate should win, got %q, want %q", got, tmp)
	}
}

func TestHasHiddenSegment(t *testing.T) {
	tests := []struct {
		in   string
		want bool
	}{
		{"/Users/han", false},
		{"/Users/han/.ssh", true},
		{"/Users/han/.kube/cache", true},
		{"/Users/han/Documents", false},
		{"", false},
		{"/", false},
		// A trailing "." segment is the current directory, not a hidden name.
		{"/Users/han/.", false},
	}
	for _, tt := range tests {
		if got := hasHiddenSegment(tt.in); got != tt.want {
			t.Errorf("hasHiddenSegment(%q) = %v, want %v", tt.in, got, tt.want)
		}
	}
}

func TestFirstArg(t *testing.T) {
	if got := firstArg(nil); got != "" {
		t.Errorf("firstArg(nil) = %q, want empty", got)
	}
	if got := firstArg([]string{"~/.ssh"}); got != "~/.ssh" {
		t.Errorf("firstArg = %q, want ~/.ssh", got)
	}
	if got := firstArg([]string{"a", "b"}); got != "a" {
		t.Errorf("firstArg = %q, want a", got)
	}
}
