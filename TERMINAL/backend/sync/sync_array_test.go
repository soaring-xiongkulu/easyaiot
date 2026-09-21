package sync

import (
	"os"
	"path/filepath"
	"testing"
)

// Regression tests: favorites.json is a top-level JSON array (unlike every
// other synced file, which is an object). The comparison and empty-dir probe
// paths must not assume every synced file unmarshals into a map.

func writeFileSync(t *testing.T, dir, name, content string) {
	t.Helper()
	if err := os.WriteFile(filepath.Join(dir, name), []byte(content), 0600); err != nil {
		t.Fatalf("write %s: %v", name, err)
	}
}

// TestCompareConfigFilesHandlesArrayFiles verifies array-shaped synced files
// (favorites.json) compare correctly: identical content is equal regardless of
// key-order/whitespace, different content is a difference, and a missing file
// equals an explicitly empty one (both mean "no data").
func TestCompareConfigFilesHandlesArrayFiles(t *testing.T) {
	base := t.TempDir()
	local := filepath.Join(base, "local")
	remote := filepath.Join(base, "remote")
	for _, d := range []string{local, remote} {
		if err := os.MkdirAll(d, 0755); err != nil {
			t.Fatalf("mkdir: %v", err)
		}
	}

	name := filepath.Join("favorites.json")

	t.Run("identical arrays are equal", func(t *testing.T) {
		writeFileSync(t, local, "favorites.json", `["a","b"]`)
		writeFileSync(t, remote, "favorites.json", "[\n  \"a\",\n  \"b\"\n]")
		same, err := compareConfigFiles(filepath.Join(local, name), filepath.Join(remote, name), nil, nil)
		if err != nil {
			t.Fatalf("compare: %v", err)
		}
		if !same {
			t.Fatal("identical favorites arrays reported as different")
		}
	})

	t.Run("different arrays differ and order matters", func(t *testing.T) {
		writeFileSync(t, local, "favorites.json", `["a","b"]`)
		writeFileSync(t, remote, "favorites.json", `["b","a"]`)
		same, err := compareConfigFiles(filepath.Join(local, name), filepath.Join(remote, name), nil, nil)
		if err != nil {
			t.Fatalf("compare: %v", err)
		}
		if same {
			t.Fatal("differently ordered favorites arrays reported as equal")
		}
	})

	t.Run("missing file equals empty array", func(t *testing.T) {
		if err := os.Remove(filepath.Join(local, "favorites.json")); err != nil {
			t.Fatalf("remove local: %v", err)
		}
		writeFileSync(t, remote, "favorites.json", `[]`)
		same, err := compareConfigFiles(filepath.Join(local, name), filepath.Join(remote, name), nil, nil)
		if err != nil {
			t.Fatalf("compare: %v", err)
		}
		if !same {
			t.Fatal("missing favorites.json vs empty array reported as different")
		}
	})
}

// TestIsConfigDirEmptyArrayFiles verifies the first-sync empty probe treats an
// empty favorites array as "no data" but a non-empty one as real data.
func TestIsConfigDirEmptyArrayFiles(t *testing.T) {
	dir := t.TempDir()

	writeFileSync(t, dir, "favorites.json", `[]`)
	if !isConfigDirEmpty(dir) {
		t.Fatal("dir with only an empty favorites array should be empty")
	}

	writeFileSync(t, dir, "favorites.json", `["conn-1"]`)
	if isConfigDirEmpty(dir) {
		t.Fatal("dir with a non-empty favorites array should not be empty")
	}
}
