package store

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestAIConfigStore_MigrateFromSettings(t *testing.T) {
	dir := t.TempDir()
	ss := &SettingsStore{configDir: dir}
	acs, err := NewAIConfigStore(dir)
	if err != nil {
		t.Fatalf("NewAIConfigStore: %v", err)
	}

	// Seed settings.json with a user model (plaintext key: no password store
	// wired, matching the pre-unlock state).
	settings := defaultSettings()
	settings.AI.Models[0].APIKey = "sk-user-key"
	if err := ss.Save(settings); err != nil {
		t.Fatalf("seed settings: %v", err)
	}

	if err := acs.MigrateFromSettingsIfNeeded(settings); err != nil {
		t.Fatalf("migrate: %v", err)
	}

	cfg, err := acs.Load()
	if err != nil {
		t.Fatalf("load migrated config: %v", err)
	}
	if len(cfg.Models) != 1 || cfg.Models[0].APIKey != "sk-user-key" {
		t.Fatalf("migrated models: %+v", cfg.Models)
	}
	if cfg.MaxTurns == nil || *cfg.MaxTurns != defaultMaxTurns {
		t.Fatalf("migrated maxTurns: %v", cfg.MaxTurns)
	}

	// The settings.json copy must stay intact for rollback compatibility.
	after, err := ss.Load()
	if err != nil {
		t.Fatalf("reload settings: %v", err)
	}
	if len(after.AI.Models) != 1 || after.AI.Models[0].APIKey != "sk-user-key" {
		t.Fatalf("settings.json AI copy was mutated by migration: %+v", after.AI.Models)
	}

	// Idempotent: a second migration is a no-op (file already exists).
	settings2 := defaultSettings()
	settings2.AI.Models[0].Name = "changed"
	if err := acs.MigrateFromSettingsIfNeeded(settings2); err != nil {
		t.Fatalf("second migrate: %v", err)
	}
	cfg2, _ := acs.Load()
	if cfg2.Models[0].Name != "Default" {
		t.Fatalf("second migration overwrote ai.json: %+v", cfg2.Models[0])
	}
}

func TestAIConfigStore_RoundTripEncryption(t *testing.T) {
	dir := t.TempDir()
	acs, err := NewAIConfigStore(dir)
	if err != nil {
		t.Fatalf("NewAIConfigStore: %v", err)
	}
	ps := fakePasswordStore{prefix: "enc:v1:test:"}
	acs.SetPasswordStore(ps)

	cfg := AIStoreData{MaxTurns: intPtr(7), Models: []AIModelConfig{{
		ID: "m1", Name: "Prod", APIKey: "sk-live", BaseURL: "https://x", Model: "m", Protocol: "anthropic",
	}}}
	if err := acs.Save(cfg); err != nil {
		t.Fatalf("save: %v", err)
	}

	// Raw file must not contain the plaintext key.
	raw, err := os.ReadFile(filepath.Join(dir, "ai.json"))
	if err != nil {
		t.Fatalf("read raw: %v", err)
	}
	var rawCfg AIStoreData
	if err := json.Unmarshal(raw, &rawCfg); err != nil {
		t.Fatalf("parse raw ai.json: %v", err)
	}
	if rawCfg.Models[0].APIKey != "enc:v1:test:sk-live" {
		t.Fatalf("apiKey not stored encrypted: %q", rawCfg.Models[0].APIKey)
	}

	got, err := acs.Load()
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if got.Models[0].APIKey != "sk-live" {
		t.Fatalf("roundtrip key mismatch: %q", got.Models[0].APIKey)
	}
	if got.MaxTurns == nil || *got.MaxTurns != 7 {
		t.Fatalf("roundtrip maxTurns: %v", got.MaxTurns)
	}
}

