package session

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestKerberosConfigPathFromEnvironment(t *testing.T) {
	path := filepath.Join(t.TempDir(), "krb5.conf")
	if err := os.WriteFile(path, []byte("[libdefaults]\n default_realm = EXAMPLE.COM\n"), 0600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("KRB5_CONFIG", path)
	got, err := kerberosConfigPath()
	if err != nil {
		t.Fatalf("kerberosConfigPath() error = %v", err)
	}
	if got != path {
		t.Fatalf("kerberosConfigPath() = %q, want %q", got, path)
	}
}

func TestKerberosConfigPathRejectsMissingEnvironmentFile(t *testing.T) {
	path := filepath.Join(t.TempDir(), "missing.conf")
	t.Setenv("KRB5_CONFIG", path)
	if _, err := kerberosConfigPath(); err == nil || !strings.Contains(err.Error(), "KRB5_CONFIG") {
		t.Fatalf("kerberosConfigPath() error = %v, want KRB5_CONFIG error", err)
	}
}

func TestKerberosCachePathFromEnvironment(t *testing.T) {
	path := filepath.Join(t.TempDir(), "krb5cc")
	if err := os.WriteFile(path, []byte("cache"), 0600); err != nil {
		t.Fatal(err)
	}
	for _, value := range []string{path, "FILE:" + path} {
		t.Run(value, func(t *testing.T) {
			t.Setenv("KRB5CCNAME", value)
			got, cleanup, err := kerberosCachePath()
			if err != nil {
				t.Fatalf("kerberosCachePath() error = %v", err)
			}
			if got != path {
				t.Fatalf("kerberosCachePath() = %q, want %q", got, path)
			}
			cleanup()
		})
	}
}

func TestKerberosCachePathRejectsUnsupportedType(t *testing.T) {
	t.Setenv("KRB5CCNAME", "KEYRING:session")
	if _, _, err := kerberosCachePath(); err == nil || !strings.Contains(err.Error(), "unsupported") {
		t.Fatalf("kerberosCachePath() error = %v, want unsupported cache error", err)
	}
}

func TestUsesWindowsLSACache(t *testing.T) {
	tests := []struct {
		value string
		want  bool
	}{
		{"", true},
		{"MSLSA:", true},
		{"mslsa:", true},
		{" MSLSA: ", true},
		{"FILE:C:\\tmp\\krb5cc", false},
		{"C:\\tmp\\krb5cc", false},
	}
	for _, tt := range tests {
		if got := usesWindowsLSACache(tt.value); got != tt.want {
			t.Errorf("usesWindowsLSACache(%q) = %v, want %v", tt.value, got, tt.want)
		}
	}
}

func TestKerberosTarget(t *testing.T) {
	tests := []struct {
		host  string
		realm string
		want  string
	}{
		{"192.0.2.10", "example.com", "192.0.2.10@example.com"},
		{"192.0.2.10", "  EXAMPLE.COM  ", "192.0.2.10@EXAMPLE.COM"},
		{"[2001:db8::10]", "example.com", "2001:db8::10@example.com"},
		{"192.0.2.10", "", "192.0.2.10"},
		{"server.example.com", "", "server.example.com"},
		{"server.invalid", "EXAMPLE.COM", "server.invalid"},
	}
	for _, tt := range tests {
		if got := kerberosTarget(tt.host, tt.realm); got != tt.want {
			t.Errorf("kerberosTarget(%q, %q) = %q, want %q", tt.host, tt.realm, got, tt.want)
		}
	}
}
