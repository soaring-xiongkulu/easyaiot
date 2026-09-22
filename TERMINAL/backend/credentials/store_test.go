package credentials

import (
	"errors"
	"sync"
	"testing"
)

type fakeKeychain struct {
	mu    sync.Mutex
	store map[string]string
}

func newFakeKeychain() *fakeKeychain { return &fakeKeychain{store: map[string]string{}} }
func (f *fakeKeychain) Get(key string) (string, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	if v, ok := f.store[key]; ok {
		return v, nil
	}
	return "", ErrKeychainNotFound
}
func (f *fakeKeychain) Set(key, value string) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.store[key] = value
	return nil
}
func (f *fakeKeychain) Delete(key string) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	delete(f.store, key)
	return nil
}

// transientKeychain reports a non-notfound error on reads, simulating e.g. a
// temporarily denied macOS keychain permission.
type transientKeychain struct{}

func (transientKeychain) Get(string) (string, error)  { return "", errors.New("keychain temporarily unavailable") }
func (transientKeychain) Set(string, string) error    { return nil }
func (transientKeychain) Delete(string) error         { return nil }

func TestSetupKeychainMode(t *testing.T) {
	dir := t.TempDir()
	kc := newFakeKeychain()
	s := New(dir, kc)
	if err := s.Setup(ModeKeychain, ""); err != nil {
		t.Fatalf("Setup: %v", err)
	}
	st := s.Status()
	if st.Mode != ModeKeychain || !st.Unlocked || st.NeedsSetup || st.KeychainLost {
		t.Fatalf("status = %+v", st)
	}
	// Round-trip encrypt/decrypt.
	enc, err := s.Encrypt("pw")
	if err != nil {
		t.Fatalf("Encrypt: %v", err)
	}
	got, err := s.Decrypt(enc)
	if err != nil || got != "pw" {
		t.Fatalf("Decrypt = %q, %v", got, err)
	}
	// Key persisted to keychain-key/<hash>.
	if len(kc.store["keychain-key/"+s.DirHash()]) == 0 {
		t.Fatalf("keychain key not persisted")
	}
}

func TestSetupMasterPasswordThenUnlock(t *testing.T) {
	dir := t.TempDir()
	kc := newFakeKeychain()
	s := New(dir, kc)
	if err := s.Setup(ModeMasterPassword, "hunter2"); err != nil {
		t.Fatalf("Setup: %v", err)
	}
	// A fresh store (simulating restart) must unlock from cached key.
	s2 := New(dir, kc)
	if err := s2.AutoUnlock(); err != nil {
		t.Fatalf("AutoUnlock: %v", err)
	}
	if !s2.Status().Unlocked {
		t.Fatalf("expected auto-unlock from cached key")
	}
	// After losing the cache, Unlock with the password re-derives the key.
	s3 := New(dir, kc)
	_ = kc.Delete("master-key/" + s3.DirHash())
	if err := s3.AutoUnlock(); err != nil {
		t.Fatalf("AutoUnlock: %v", err)
	}
	if s3.Status().Unlocked {
		t.Fatalf("expected locked after cache cleared")
	}
	if err := s3.Unlock("hunter2"); err != nil {
		t.Fatalf("Unlock: %v", err)
	}
	if !s3.Status().Unlocked {
		t.Fatalf("expected unlocked after Unlock")
	}
}

func TestAutoUnlockKeychainLost(t *testing.T) {
	dir := t.TempDir()
	kc := newFakeKeychain()
	s := New(dir, kc)
	_ = s.Setup(ModeKeychain, "")
	// Simulate a fresh machine: meta exists but keychain key is gone.
	_ = kc.Delete("keychain-key/" + s.DirHash())
	s2 := New(dir, kc)
	if err := s2.AutoUnlock(); err != nil {
		t.Fatalf("AutoUnlock: %v", err)
	}
	if !s2.Status().KeychainLost {
		t.Fatalf("expected KeychainLost, got %+v", s2.Status())
	}
}

func TestEncryptWhenLockedFails(t *testing.T) {
	dir := t.TempDir()
	kc := newFakeKeychain()
	s := New(dir, kc)
	_ = s.Setup(ModeMasterPassword, "pw")
	_ = kc.Delete("master-key/" + s.DirHash())
	s2 := New(dir, kc)
	_ = s2.AutoUnlock() // locked
	if _, err := s2.Encrypt("x"); err == nil {
		t.Fatalf("Encrypt should fail when locked")
	}
}
