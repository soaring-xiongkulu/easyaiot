//go:build windows
// +build windows

package session

import (
	"reflect"
	"testing"
)

func TestBuildWSLStartArgs(t *testing.T) {
	for _, tc := range []struct {
		name      string
		distro    string
		cwd       string
		startArgs []string
		want      []string
	}{
		{
			name:      "no cwd starts in linux home",
			distro:    "Ubuntu-24.04",
			cwd:       "",
			startArgs: nil,
			want:      []string{"-d", "Ubuntu-24.04", "--cd", "~"},
		},
		{
			name:      "explicit cwd skips home",
			distro:    "Ubuntu-24.04",
			cwd:       `C:\Users\me\project`,
			startArgs: nil,
			want:      []string{"-d", "Ubuntu-24.04"},
		},
		{
			name:      "shell integration args appended after cd",
			distro:    "Ubuntu-24.04",
			cwd:       "",
			startArgs: []string{"-e", "bash", "--rcfile", "/tmp/terminal-abc123"},
			want:      []string{"-d", "Ubuntu-24.04", "--cd", "~", "-e", "bash", "--rcfile", "/tmp/terminal-abc123"},
		},
		{
			name:      "explicit cwd with integration",
			distro:    "Debian",
			cwd:       `D:\work`,
			startArgs: []string{"-e", "env", "ZDOTDIR=/tmp/terminal-xyz", "zsh"},
			want:      []string{"-d", "Debian", "-e", "env", "ZDOTDIR=/tmp/terminal-xyz", "zsh"},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			got := buildWSLStartArgs(tc.distro, tc.cwd, tc.startArgs)
			if !reflect.DeepEqual(got, tc.want) {
				t.Fatalf("buildWSLStartArgs(%q, %q, %v) = %v, want %v", tc.distro, tc.cwd, tc.startArgs, got, tc.want)
			}
		})
	}
}
