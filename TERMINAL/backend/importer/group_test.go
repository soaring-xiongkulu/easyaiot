package importer

import (
	"testing"

	"easyaiot/terminal/backend/session"
)

func TestEnsureGroupPathReusesSamePath(t *testing.T) {
	pathMap := map[string]string{}
	var groups []session.ConnectionGroup
	a := ensureGroupPath([]string{"prod", "web"}, pathMap, &groups, newGroupID)
	b := ensureGroupPath([]string{"prod", "web"}, pathMap, &groups, newGroupID)
	if a == nil || b == nil || *a != *b {
		t.Fatalf("same path should reuse group: %v vs %v", a, b)
	}
	if len(groups) != 2 { // prod + web
		t.Fatalf("expected 2 groups, got %d", len(groups))
	}
}

func TestMergeImportedReusesExistingByPath(t *testing.T) {
	existing := session.ConnectionStoreData{
		Groups: []session.ConnectionGroup{{ID: "g1", Name: "prod"}},
	}
	imported := session.ConnectionStoreData{
		Groups: []session.ConnectionGroup{
			{ID: "ig1", Name: "prod"},
			{ID: "ig2", Name: "web", ParentId: strptr("ig1")},
		},
		Connections: []session.ConnectionConfig{
			{ID: "c1", Name: "srv", Type: "ssh", Host: "10.0.0.1", Port: 22, GroupId: strptr("ig2")},
		},
	}
	merged := MergeImported(existing, imported)
	if len(merged.Groups) != 2 { // prod reused, web added
		t.Fatalf("expected 2 groups, got %d: %+v", len(merged.Groups), merged.Groups)
	}
	c := merged.Connections[0]
	if c.GroupId == nil || *c.GroupId != "ig2" {
		t.Fatalf("connection groupId should stay on imported web group, got %v", c.GroupId)
	}
	var web session.ConnectionGroup
	for _, g := range merged.Groups {
		if g.Name == "web" {
			web = g
		}
	}
	if web.ParentId == nil || *web.ParentId != "g1" {
		t.Fatalf("web parent should be g1, got %v", web.ParentId)
	}
}

func strptr(s string) *string { return &s }
