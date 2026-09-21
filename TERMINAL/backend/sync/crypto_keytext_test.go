package sync

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

// TestSyncBoundaryNormalizesKeyText is the keyText-specific regression guard for
// the enc:v1: opacity bug (#711): an inline private-key text (authType "keyText",
// keyContent) is encrypted locally as enc:v1:, so sync must normalize it back to
// plaintext on push (the whole file is protected solely by the sync key at rest
// in the repo) and re-encrypt it on pull. Without this, the literal enc:v1:
// prefix would travel to other devices (issue #720 follow-up).
func TestSyncBoundaryNormalizesKeyText(t *testing.T) {
	key := make([]byte, 32)
	repoDir := t.TempDir()
	dstDir := t.TempDir()
	srcDir := t.TempDir()

	write := func(dir, name, content string) {
		t.Helper()
		if err := os.WriteFile(filepath.Join(dir, name), []byte(content), 0600); err != nil {
			t.Fatalf("write %s: %v", name, err)
		}
	}

	write(srcDir, "connections.json", `{"connections":[{"id":"c1","authType":"keyText","keyContent":"enc:v1:fake-CONNKEY","password":"pp"}]}`)
	write(srcDir, "identities.json", `{"identities":[{"id":"i1","authType":"keyText","keyContent":"enc:v1:fake-IDKEY"}]}`)
	write(srcDir, "proxies.json", `{"proxies":[]}`)
	write(srcDir, "settings.json", `{"ai":{"models":[]}}`)

	if err := EncryptConfigFiles(srcDir, repoDir, key, nil, fakePS{}); err != nil {
		t.Fatalf("encrypt: %v", err)
	}

	// The repo copy must carry plaintext key content (protected only by the key).
	assertField := func(file string, decrypt bool, idx int, field, want string) {
		t.Helper()
		raw, err := os.ReadFile(file)
		if err != nil {
			t.Fatalf("read %s: %v", file, err)
		}
		var content []byte = raw
		// The repo copy is the whole file encrypted with the sync key; the dst
		// copy is plaintext JSON (only secret fields re-encrypted as enc:v1:).
		if decrypt {
			pt, err := decryptBytes(string(raw), key)
			if err != nil {
				t.Fatalf("decrypt %s: %v", file, err)
			}
			content = pt
		}
		var wrapper struct {
			Connections []map[string]interface{} `json:"connections"`
			Identities  []map[string]interface{} `json:"identities"`
		}
		if err := json.Unmarshal(content, &wrapper); err != nil {
			t.Fatalf("parse %s: %v", file, err)
		}
		var list []map[string]interface{}
		switch idx {
		case 0:
			list = wrapper.Connections
		default:
			list = wrapper.Identities
		}
		if len(list) == 0 {
			t.Fatalf("no entries in %s", file)
		}
		if got := list[0][field]; got != want {
			t.Fatalf("%s %s = %v, want %q", file, field, got, want)
		}
	}

	assertField(filepath.Join(repoDir, "connections.json"), true, 0, "keyContent", "CONNKEY")
	assertField(filepath.Join(repoDir, "identities.json"), true, 1, "keyContent", "IDKEY")

	// Pull must re-encrypt key content back to enc:v1: under the local key.
	if err := DecryptConfigFiles(repoDir, dstDir, key, fakePS{}); err != nil {
		t.Fatalf("decrypt: %v", err)
	}
	assertField(filepath.Join(dstDir, "connections.json"), false, 0, "keyContent", "enc:v1:fake-CONNKEY")
	assertField(filepath.Join(dstDir, "identities.json"), false, 1, "keyContent", "enc:v1:fake-IDKEY")
}