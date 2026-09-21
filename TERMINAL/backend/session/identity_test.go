package session

import (
	"reflect"
	"testing"
)

func TestMaterializeIdentityPassword(t *testing.T) {
	resolve := func(id string) (Identity, bool) {
		if id == "id-1" {
			return Identity{ID: "id-1", Name: "prod", Username: "root", AuthType: "password", Password: "s3cret"}, true
		}
		return Identity{}, false
	}
	cfg := ConnectionConfig{ID: "c1", Host: "10.0.0.5", User: "ignored", AuthType: "identity", IdentityId: "id-1"}
	got, err := MaterializeIdentity(cfg, resolve)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got.User != "root" || got.AuthType != "password" || got.Password != "s3cret" {
		t.Fatalf("bad materialization: %+v", got)
	}
}

func TestMaterializeIdentityKey(t *testing.T) {
	resolve := func(id string) (Identity, bool) {
		return Identity{ID: "id-2", Username: "git", AuthType: "key", KeyPath: "/home/git/.ssh/id_ed25519", Password: "pp"}, true
	}
	cfg := ConnectionConfig{User: "ignored", AuthType: "identity", IdentityId: "id-2"}
	got, err := MaterializeIdentity(cfg, resolve)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got.User != "git" || got.AuthType != "key" || got.KeyPath != "/home/git/.ssh/id_ed25519" || got.Password != "pp" {
		t.Fatalf("bad materialization: %+v", got)
	}
}

func TestMaterializeIdentityPassthrough(t *testing.T) {
	cfg := ConnectionConfig{User: "alice", AuthType: "password", Password: "x"}
	got, err := MaterializeIdentity(cfg, nil)
	if err != nil || !reflect.DeepEqual(got, cfg) {
		t.Fatalf("non-identity should pass through unchanged: %+v err=%v", got, err)
	}
}

func TestMaterializeIdentityMissing(t *testing.T) {
	cfg := ConnectionConfig{AuthType: "identity", IdentityId: "nope"}
	if _, err := MaterializeIdentity(cfg, func(string) (Identity, bool) { return Identity{}, false }); err == nil {
		t.Fatal("expected error for missing identity")
	}
}
