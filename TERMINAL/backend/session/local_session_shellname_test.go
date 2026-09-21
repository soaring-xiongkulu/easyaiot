//go:build windows
// +build windows

package session

import "testing"

// shellName must disambiguate the three common Windows bash.exe flavors by
// install path: Git for Windows, Cygwin and MSYS2 all ship a binary with the
// same basename, and a bare "bash" tab title tells the user nothing.
func TestShellNameDisambiguatesBashFlavors(t *testing.T) {
	cases := []struct {
		path string
		want string
	}{
		{`C:\Program Files\Git\bin\bash.exe`, "Git Bash"},
		{`C:\Users\me\scoop\apps\git\current\bin\bash.exe`, "Git Bash"},
		{`C:\ProgramData\chocolatey\bin\bash.exe`, "Git Bash"},
		{`C:\cygwin64\bin\bash.exe`, "Cygwin bash"},
		{`D:\tools\cygwin\bin\bash.exe`, "Cygwin bash"},
		{`C:\msys64\usr\bin\bash.exe`, "MSYS2 bash"},
		{`C:\tools\msys32\usr\bin\bash.exe`, "MSYS2 bash"},
		// Unknown bash installs keep the historical basename label.
		{`E:\custom\bash.exe`, "bash"},
		// Non-bash shells keep the basename label.
		{`C:\Windows\System32\cmd.exe`, "cmd"},
		{`C:\Program Files\PowerShell\7\pwsh.exe`, "pwsh"},
		{`C:\Windows\System32\bash.exe`, "bash"},
	}
	for _, tc := range cases {
		if got := shellName(tc.path); got != tc.want {
			t.Errorf("shellName(%q) = %q, want %q", tc.path, got, tc.want)
		}
	}
}
