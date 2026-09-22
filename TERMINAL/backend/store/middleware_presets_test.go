package store

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"easyaiot/terminal/backend/session"
)

// newTestConnectionStore builds a store over a fresh temp dir with the same
// fake cipher the other store tests use, so password-bearing presets save.
func newTestConnectionStore(t *testing.T) (*ConnectionStore, string) {
	t.Helper()
	dir := t.TempDir()
	cs := &ConnectionStore{configDir: dir, passwordStore: fakeCipherStore{}}
	return cs, dir
}

func TestEnsureMiddlewarePresetsSeedsGroupAndConnections(t *testing.T) {
	cs, dir := newTestConnectionStore(t)

	changed, err := EnsureMiddlewarePresets(dir, cs, "zh-CN")
	if err != nil {
		t.Fatalf("EnsureMiddlewarePresets: %v", err)
	}
	if !changed {
		t.Fatal("fresh seed reported no change")
	}

	data, err := cs.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}

	foundGroup := false
	for _, g := range data.Groups {
		if g.ID == MiddlewarePresetGroupID {
			foundGroup = true
			if g.Name != "EasyAIoT 中间件" {
				t.Errorf("group name = %q, want localized zh-CN name", g.Name)
			}
		}
	}
	if !foundGroup {
		t.Fatal("preset group not seeded")
	}

	presets := MiddlewarePresets()
	byID := map[string]session.ConnectionConfig{}
	for _, c := range data.Connections {
		byID[c.ID] = c
	}
	for _, p := range presets {
		c, ok := byID[p.ID]
		if !ok {
			t.Errorf("preset %q not seeded", p.ID)
			continue
		}
		if c.GroupId == nil || *c.GroupId != MiddlewarePresetGroupID {
			t.Errorf("preset %q groupId = %v, want preset group", p.ID, c.GroupId)
		}
	}
	if len(byID) < len(presets) {
		t.Errorf("connection count = %d, want >= %d", len(byID), len(presets))
	}

	// Marker written → subsequent calls are no-ops even after the user
	// deletes the whole group.
	if err := os.Remove(filepath.Join(dir, "connections.json")); err != nil {
		t.Fatalf("remove store: %v", err)
	}
	if changed, err := EnsureMiddlewarePresets(dir, cs, "zh-CN"); err != nil || changed {
		t.Fatalf("second Ensure: changed=%v err=%v — marker not honored", changed, err)
	}
	if _, err := os.Stat(filepath.Join(dir, "connections.json")); !os.IsNotExist(err) {
		t.Error("connections.json resurrected after deletion — marker not honored")
	}
}

func TestEnsureMiddlewarePresetsPreservesUserEdits(t *testing.T) {
	cs, dir := newTestConnectionStore(t)

	// Simulate a user who already created their own connection under the
	// deterministic preset ID (e.g. via sync) with a custom host.
	gid := MiddlewarePresetGroupID
	mine := session.ConnectionConfig{
		ID: MiddlewarePresetIDPrefix + "postgres", Name: "My PG", Type: "database",
		Host: "10.0.0.9", Port: 5432, AuthType: "password", GroupId: &gid,
	}
	if err := cs.Save(session.ConnectionStoreData{
		Groups:      []session.ConnectionGroup{{ID: MiddlewarePresetGroupID, Name: "renamed"}},
		Connections: []session.ConnectionConfig{mine},
	}); err != nil {
		t.Fatalf("Save: %v", err)
	}

	if _, err := EnsureMiddlewarePresets(dir, cs, ""); err != nil {
		t.Fatalf("EnsureMiddlewarePresets: %v", err)
	}
	data, _ := cs.Load()
	for _, c := range data.Connections {
		if c.ID == mine.ID {
			if c.Host != "10.0.0.9" || c.Name != "My PG" {
				t.Errorf("user-edited preset overwritten: %+v", c)
			}
		}
	}
	for _, g := range data.Groups {
		if g.ID == MiddlewarePresetGroupID && g.Name != "renamed" {
			t.Errorf("user-renamed group overwritten: %q", g.Name)
		}
	}
}

// A marker older than MiddlewarePresetsVersion means the deployment seeded an
// earlier roster: existing preset entries must be re-authored from the current
// roster (credentials included) while user-created connections stay untouched.
// Regression for deployments that seeded before presets carried passwords and
// were then stuck with connections that could never authenticate.
func TestEnsureMiddlewarePresetsRefreshesStaleRosterOnVersionBump(t *testing.T) {
	if MiddlewarePresetsVersion <= 1 {
		t.Fatal("test requires MiddlewarePresetsVersion bumped past the password-less v1 roster")
	}
	cs, dir := newTestConnectionStore(t)

	gid := MiddlewarePresetGroupID
	stale := session.ConnectionConfig{
		ID: MiddlewarePresetIDPrefix + "rustfs-s3", Name: "RustFS (S3)", Type: "s3",
		Host: "http://host.docker.internal:9000", Port: 9000, AuthType: "password",
		User: "minioadmin", GroupId: &gid, // v1-era entry: no password, no region
	}
	own := session.ConnectionConfig{
		ID: "user-own-host", Name: "My server", Type: "database",
		Host: "10.0.0.9", Port: 5432, AuthType: "password",
		User: "admin", Password: "keepme", GroupId: &gid,
	}
	if err := cs.Save(session.ConnectionStoreData{
		Groups:      []session.ConnectionGroup{{ID: MiddlewarePresetGroupID, Name: "EasyAIoT Middleware"}},
		Connections: []session.ConnectionConfig{stale, own},
	}); err != nil {
		t.Fatalf("Save: %v", err)
	}
	if err := os.WriteFile(filepath.Join(dir, middlewarePresetsMarker), []byte(`{"version":1}`), 0644); err != nil {
		t.Fatalf("write stale marker: %v", err)
	}

	changed, err := EnsureMiddlewarePresets(dir, cs, "")
	if err != nil {
		t.Fatalf("EnsureMiddlewarePresets: %v", err)
	}
	if !changed {
		t.Fatal("version-bump refresh reported no change")
	}

	data, err := cs.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	byID := map[string]session.ConnectionConfig{}
	for _, c := range data.Connections {
		byID[c.ID] = c
	}
	healed, ok := byID[stale.ID]
	if !ok {
		t.Fatal("stale preset dropped by refresh")
	}
	if healed.Password == "" {
		t.Error("stale preset still has no password after roster refresh")
	}
	if healed.S3Region != "us-east-1" {
		t.Errorf("refreshed preset s3Region = %q, want roster value", healed.S3Region)
	}
	if got, ok := byID[own.ID]; !ok {
		t.Error("user-created connection dropped")
	} else if got.Password == "" || got.Host != "10.0.0.9" {
		t.Errorf("user-created connection altered by refresh: %+v", got)
	}

	// The marker is rewritten to the current version, so the next start is a
	// no-op again (user edits between bumps stay sticky).
	b, err := os.ReadFile(filepath.Join(dir, middlewarePresetsMarker))
	if err != nil {
		t.Fatalf("read marker: %v", err)
	}
	var m middlewarePresetMarkerData
	if err := json.Unmarshal(b, &m); err != nil || m.Version != MiddlewarePresetsVersion {
		t.Errorf("marker version = %d (%v), want %d", m.Version, err, MiddlewarePresetsVersion)
	}
}

func TestMiddlewarePresetsHostOverride(t *testing.T) {
	t.Setenv("EASYAIOT_MIDDLEWARE_HOST", "192.168.1.10")
	t.Setenv("EASYAIOT_POSTGRES_HOST", "db.internal")

	for _, p := range MiddlewarePresets() {
		switch p.ID {
		case MiddlewarePresetIDPrefix + "postgres":
			if p.Host != "db.internal" {
				t.Errorf("postgres host = %q, want per-service override", p.Host)
			}
		case MiddlewarePresetIDPrefix + "redis":
			if p.Host != "192.168.1.10" {
				t.Errorf("redis host = %q, want global override", p.Host)
			}
		case MiddlewarePresetIDPrefix + "nacos":
			if p.Host != "http://192.168.1.10:8848/nacos" {
				t.Errorf("nacos url = %q", p.Host)
			}
		case MiddlewarePresetIDPrefix + "rustfs-s3":
			if p.Host != "http://192.168.1.10:9000" {
				t.Errorf("s3 endpoint = %q", p.Host)
			}
		}
	}
}

func TestMiddlewarePresetsURLBaseOverride(t *testing.T) {
	t.Setenv("EASYAIOT_MIDDLEWARE_HOST", "")
	t.Setenv("EASYAIOT_NACOS_HOST", "http://10.0.0.5:28848")
	for _, p := range MiddlewarePresets() {
		if p.ID == MiddlewarePresetIDPrefix+"nacos" && p.Host != "http://10.0.0.5:28848/nacos" {
			t.Errorf("nacos url = %q, want base-URL override kept intact", p.Host)
		}
	}
}

// A full-URL override that already includes the service path must not get it
// appended a second time (.../nacos/nacos 404s).
func TestMiddlewarePresetsURLFullOverrideNoPathDuplication(t *testing.T) {
	t.Setenv("EASYAIOT_MIDDLEWARE_HOST", "")
	t.Setenv("EASYAIOT_NACOS_HOST", "http://10.0.0.5:28848/nacos/")
	for _, p := range MiddlewarePresets() {
		if p.ID == MiddlewarePresetIDPrefix+"nacos" && p.Host != "http://10.0.0.5:28848/nacos" {
			t.Errorf("nacos url = %q, want full-URL override without duplicated path", p.Host)
		}
	}
}
