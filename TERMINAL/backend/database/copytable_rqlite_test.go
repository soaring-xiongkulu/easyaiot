package database

import "testing"

func TestRenameLeadingTableRef_Create(t *testing.T) {
	stmt := `CREATE TABLE "users" ("id" INTEGER, "name" TEXT)`
	got := renameLeadingTableRef(stmt, "users", "users_copy")
	want := `CREATE TABLE "users_copy" ("id" INTEGER, "name" TEXT)`
	if got != want {
		t.Fatalf("got %q, want %q", got, want)
	}
}

func TestRenameLeadingTableRef_InsertKeepsColumnRef(t *testing.T) {
	// The INSERT target is renamed; a same-named value elsewhere is untouched.
	stmt := `INSERT INTO "users" ("id", "name") VALUES (1, 'x "users" y')`
	got := renameLeadingTableRef(stmt, "users", "users_copy")
	want := `INSERT INTO "users_copy" ("id", "name") VALUES (1, 'x "users" y')`
	if got != want {
		t.Fatalf("got %q, want %q", got, want)
	}
}

func TestRenameLeadingTableRef_NoMatch(t *testing.T) {
	stmt := `CREATE TABLE "other" ("id" INTEGER)`
	if got := renameLeadingTableRef(stmt, "users", "users_copy"); got != stmt {
		t.Fatalf("expected unchanged, got %q", got)
	}
}
