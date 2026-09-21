package session

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/pem"
	"os"
	"path/filepath"
	"testing"

	"golang.org/x/crypto/ssh"
)

// newEncryptedKeyFile writes an ed25519 private key protected by passphrase to
// a new temp file and returns its path. Mirrors the "秘钥加密码" scenario from
// issue #647: an SSH private key that requires a passphrase to decrypt.
func newEncryptedKeyFile(t *testing.T, passphrase string) string {
	t.Helper()
	_, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("generate key: %v", err)
	}
	block, err := ssh.MarshalPrivateKeyWithPassphrase(priv, "terminal-test", []byte(passphrase))
	if err != nil {
		t.Fatalf("marshal encrypted key: %v", err)
	}
	path := filepath.Join(t.TempDir(), "id_ed25519")
	if err := os.WriteFile(path, pem.EncodeToMemory(block), 0600); err != nil {
		t.Fatalf("write key: %v", err)
	}
	return path
}

// newKeyText returns an ed25519 private key in PEM text form. When passphrase is
// non-empty the key is encrypted (the "keyText + passphrase" scenario); otherwise
// it is plaintext. Mirrors inline private-key text for authType "keyText" (#720).
func newKeyText(t *testing.T, passphrase string) string {
	t.Helper()
	_, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("generate key: %v", err)
	}
	var block *pem.Block
	if passphrase != "" {
		block, err = ssh.MarshalPrivateKeyWithPassphrase(priv, "terminal-test", []byte(passphrase))
	} else {
		block, err = ssh.MarshalPrivateKey(priv, "terminal-test")
	}
	if err != nil {
		t.Fatalf("marshal key: %v", err)
	}
	return string(pem.EncodeToMemory(block))
}

// TestBuildAuthMethods locks in the behavior that SFTP and monitor sessions rely
// on for "key + passphrase" authentication. Before the fix both built their auth
// methods inline and decoded the key with ssh.ParsePrivateKey (no passphrase), so
// an encrypted key could never authenticate — exactly the issue #647 report.
func TestBuildAuthMethods(t *testing.T) {
	keyPath := newEncryptedKeyFile(t, "secret-pass")
	keyText := newKeyText(t, "")
	encKeyText := newKeyText(t, "secret-pass")

	cases := []struct {
		name    string
		config  ConnectionConfig
		wantErr bool
	}{
		{"encrypted key + correct passphrase", ConnectionConfig{AuthType: "key", KeyPath: keyPath, Password: "secret-pass"}, false},
		{"encrypted key + no passphrase", ConnectionConfig{AuthType: "key", KeyPath: keyPath}, true},
		{"encrypted key + wrong passphrase", ConnectionConfig{AuthType: "key", KeyPath: keyPath, Password: "wrong"}, true},
		{"keyText plain content", ConnectionConfig{AuthType: "keyText", KeyContent: keyText}, false},
		{"keyText encrypted + correct passphrase", ConnectionConfig{AuthType: "keyText", KeyContent: encKeyText, Password: "secret-pass"}, false},
		{"keyText encrypted + wrong passphrase", ConnectionConfig{AuthType: "keyText", KeyContent: encKeyText, Password: "wrong"}, true},
		{"keyText empty content", ConnectionConfig{AuthType: "keyText"}, true},
		{"plain password", ConnectionConfig{AuthType: "password", Password: "pw"}, false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			methods, err := buildAuthMethods(tc.config)
			if tc.wantErr {
				if err == nil {
					t.Fatalf("buildAuthMethods() error = nil, want error")
				}
				return
			}
			if err != nil {
				t.Fatalf("buildAuthMethods() error = %v", err)
			}
			if len(methods) == 0 {
				t.Fatalf("buildAuthMethods() returned 0 methods, want > 0")
			}
		})
	}
}

// TestMakeSSHAuthMethodsKeyText locks in that the interactive SSH entrypoint —
// shared by direct SSH sessions, tunnels (tunnel_forward/tunnel_service), mosh,
// connection testing and dialSSHTCP — parses inline keyText the same way it does
// a key file, instead of silently skipping it. makeSSHAuthMethods only appends a
// public-key method when parseAuthKeySigner succeeds (keyText isn't a recognized
// case elsewhere), so a valid keyText must yield exactly one method and invalid
// content must yield zero — proving keyText is wired into the shared entrypoint.
// This is what makes keyText portable across the whole connect surface (#720).
func TestMakeSSHAuthMethodsKeyText(t *testing.T) {
	cases := []struct {
		name      string
		config    ConnectionConfig
		wantCount int
	}{
		{"valid plain keyText", ConnectionConfig{AuthType: "keyText", KeyContent: newKeyText(t, "")}, 1},
		{"valid encrypted keyText + passphrase", ConnectionConfig{AuthType: "keyText", KeyContent: newKeyText(t, "pp"), Password: "pp"}, 1},
		{"invalid keyText content", ConnectionConfig{AuthType: "keyText", KeyContent: "not a pem key"}, 0},
		{"empty keyText", ConnectionConfig{AuthType: "keyText"}, 0},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			methods, err := makeSSHAuthMethods(tc.config, nil)
			if err != nil {
				t.Fatalf("makeSSHAuthMethods() error = %v", err)
			}
			if got := len(methods); got != tc.wantCount {
				t.Fatalf("makeSSHAuthMethods() returned %d methods, want %d", got, tc.wantCount)
			}
		})
	}
}

func TestKerberosDoesNotFallBackToKeyboardInteractive(t *testing.T) {
	configPath := filepath.Join(t.TempDir(), "missing-krb5.conf")
	t.Setenv("KRB5_CONFIG", configPath)
	kb := func(string, string, []string, []bool) ([]string, error) {
		t.Fatal("keyboard-interactive callback must not be used for Kerberos auth")
		return nil, nil
	}

	methods, err := makeSSHAuthMethods(ConnectionConfig{AuthType: "kerberos", Host: "server.example.com"}, kb)
	if err == nil {
		t.Fatal("makeSSHAuthMethods() error = nil, want missing Kerberos config error")
	}
	if len(methods) != 0 {
		t.Fatalf("makeSSHAuthMethods() returned %d fallback methods, want 0", len(methods))
	}
}

func TestAgentDoesNotFallBackToKeyboardInteractive(t *testing.T) {
	t.Setenv("SSH_AUTH_SOCK", "")
	kb := func(string, string, []string, []bool) ([]string, error) {
		t.Fatal("keyboard-interactive callback must not be used for agent auth")
		return nil, nil
	}

	if _, err := makeSSHAuthMethods(ConnectionConfig{AuthType: "agent"}, kb); err == nil {
		t.Fatal("makeSSHAuthMethods() error = nil, want missing SSH_AUTH_SOCK error")
	}
}
