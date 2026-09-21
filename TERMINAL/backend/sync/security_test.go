//go:build !android

package sync

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

// TestCompareLocalWithRepo_WrongKeyReturnsError was folded into
// TestSync_WrongPasswordSetsPasswordMismatchStatus: the wrong-key abort is
// now the verifyDecryption guard inside Sync() itself.

// TestSync_WrongPasswordSetsPasswordMismatchStatus drives Sync() with an
// encKey that cannot open the existing ciphertext and asserts the on-disk
// status record reflects the password_mismatch outcome (not a generic
// "failed").
func TestSync_WrongPasswordSetsPasswordMismatchStatus(t *testing.T) {
	s, repoPath := initLocalRepoWithBareRemote(t)

	realKey := DeriveKey("correct-password", []byte("0123456789abcdef"))
	srcDir := t.TempDir()
	if err := os.WriteFile(filepath.Join(srcDir, "connections.json"),
		[]byte(`{"connections":[]}`), 0600); err != nil {
		t.Fatalf("write src: %v", err)
	}
	if err := EncryptConfigFiles(srcDir, repoPath, realKey, nil, nil); err != nil {
		t.Fatalf("encrypt: %v", err)
	}

	// Store the WRONG derived key in the keychain so Sync() loads the wrong
	// encKey and hits the compareLocalWithRepo decrypt-fail path.
	if err := s.keychain.StoreEncryptionKey(
		DeriveKey("WRONG-password", []byte("0123456789abcdef")),
	); err != nil {
		t.Fatalf("store wrong key: %v", err)
	}

	if _, err := s.Sync(); err == nil {
		t.Fatal("Sync() with wrong key returned nil error — expected password_mismatch")
	}

	loaded, err := s.configStore.Load()
	if err != nil {
		t.Fatalf("reload config: %v", err)
	}
	if loaded.LastSyncStatus != "password_mismatch" {
		t.Errorf("LastSyncStatus = %q, want %q", loaded.LastSyncStatus, "password_mismatch")
	}
}

// TestChangePassword_RewritesSaltAndReencryptsFiles is the SYNC-P1-6
// regression guard: changing the master password must (a) replace the salt
// in .sync-salt so PBKDF2 work cannot amortize across old + new keys, and
// (b) re-encrypt every repo file so the new key decrypts them and the old
// key does not.
func TestChangePassword_RewritesSaltAndReencryptsFiles(t *testing.T) {
	s, repoPath := initLocalRepoWithBareRemote(t)

	oldSalt := []byte("0123456789abcdef")
	oldKey := DeriveKey("old-pass", oldSalt)

	srcDir := t.TempDir()
	seed := map[string]string{
		"connections.json":   `{"connections":[{"id":"c1","name":"n"}]}`,
		"ai.json":            `{"maxTurns":20}`,
		"quickCommands.json": `[{"name":"q1","cmd":"ls"}]`,
		"identities.json":    `{"identities":[{"id":"i1","name":"prod"}]}`,
		"proxies.json":       `{"proxies":[{"id":"p1","name":"vpn"}]}`,
	}
	for name, body := range seed {
		if err := os.WriteFile(filepath.Join(srcDir, name), []byte(body), 0600); err != nil {
			t.Fatalf("write seed %s: %v", name, err)
		}
	}
	if err := EncryptConfigFiles(srcDir, repoPath, oldKey, nil, nil); err != nil {
		t.Fatalf("encrypt with oldKey: %v", err)
	}
	if err := WriteSaltFile(repoPath, oldSalt); err != nil {
		t.Fatalf("write old salt: %v", err)
	}

	preFiles := map[string][]byte{}
	for name := range seed {
		b, err := os.ReadFile(filepath.Join(repoPath, name))
		if err != nil {
			t.Fatalf("read pre %s: %v", name, err)
		}
		preFiles[name] = b
	}

	if err := s.ChangePassword("old-pass", "new-pass"); err != nil {
		t.Fatalf("ChangePassword: %v", err)
	}

	gotSalt, err := ReadSaltFile(repoPath)
	if err != nil {
		t.Fatalf("read salt after rotation: %v", err)
	}
	if string(gotSalt) == string(oldSalt) {
		t.Fatal(".sync-salt unchanged after ChangePassword — SYNC-P1-6 regression (PBKDF2 work could amortize)")
	}

	// Every repo file must decrypt with the NEW key.
	newKey := DeriveKey("new-pass", gotSalt)
	dstDir := t.TempDir()
	if err := DecryptConfigFiles(repoPath, dstDir, newKey, nil); err != nil {
		t.Fatalf("decrypt with newKey: %v", err)
	}
	for name, want := range seed {
		got, err := os.ReadFile(filepath.Join(dstDir, name))
		if err != nil {
			t.Fatalf("read decrypted %s: %v", name, err)
		}
		var gw, ww interface{}
		if err := json.Unmarshal(got, &gw); err != nil {
			t.Fatalf("parse decrypted %s: %v", name, err)
		}
		if err := json.Unmarshal([]byte(want), &ww); err != nil {
			t.Fatalf("parse seed %s: %v", name, err)
		}
		gj, _ := json.Marshal(gw)
		wj, _ := json.Marshal(ww)
		if string(gj) != string(wj) {
			t.Errorf("decrypted %s = %s, want %s", name, gj, wj)
		}
	}

	// And must NOT decrypt with the OLD key — proves rotation re-encrypted.
	for name := range seed {
		ct, err := os.ReadFile(filepath.Join(repoPath, name))
		if err != nil {
			t.Fatalf("read %s: %v", name, err)
		}
		if _, err := decryptBytes(string(ct), oldKey); err == nil {
			t.Errorf("%s still decryptable with oldKey — ChangePassword did not re-encrypt", name)
		}
	}

	// Ciphertext bytes must actually differ from the pre-rotation snapshot.
	for name, pre := range preFiles {
		post, err := os.ReadFile(filepath.Join(repoPath, name))
		if err != nil {
			t.Fatalf("read post %s: %v", name, err)
		}
		if string(pre) == string(post) {
			t.Errorf("%s ciphertext unchanged after ChangePassword", name)
		}
	}
}
