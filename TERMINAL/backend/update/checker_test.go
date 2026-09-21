package update

import (
	"testing"
)

func TestVersionGreater(t *testing.T) {
	cases := []struct {
		latest, current string
		want            bool
	}{
		{"v1.9.2", "v1.9.1", true},
		{"1.10.0", "1.9.9", true},
		{"v1.9.2", "v1.9.2", false},
		{"1.9.1", "1.9.2", false},
		{"2.0.0", "1.9.9", true},
		{"1.9.0-rc1", "1.8.0", true},
		{"1.9.0-rc1", "1.9.0-rc2", false},
		{"1.9.0-rc2", "1.9.0-rc1", true},
		{"1.9.0", "1.9.0-rc2", true}, // release outranks prerelease
		{"1.9.0-rc1", "1.9.0", false},
		{"1.9.0+build5", "1.9.0", false}, // build metadata ignored
	}
	for _, c := range cases {
		if got := versionGreater(c.latest, c.current); got != c.want {
			t.Errorf("versionGreater(%q, %q) = %v, want %v", c.latest, c.current, got, c.want)
		}
	}
}

func TestShouldUpdate(t *testing.T) {
	if !shouldUpdate("dev", "v1.9.2") {
		t.Error("dev builds should always report an update")
	}
	if shouldUpdate("v1.9.2", "dev") {
		t.Error("non-dev build newer than dev should not report an update")
	}
	if shouldUpdate("v1.9.2", "v1.9.2") {
		t.Error("same version should not report an update")
	}
}

func TestParseChecksums(t *testing.T) {
	data := []byte("" +
		"aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899  terminal-linux-amd64-v1.9.2.tar.gz\n" +
		"ffeeddccbbaa00112233445566778899ffeeddccbbaa00112233445566778899 *terminal-windows-amd64-portable-v1.9.2.zip\n" +
		"not-a-hash file.txt\n")
	sums := parseChecksums(data)
	if got := sums["terminal-linux-amd64-v1.9.2.tar.gz"]; got != "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899" {
		t.Errorf("unexpected checksum: %q", got)
	}
	if got := sums["terminal-windows-amd64-portable-v1.9.2.zip"]; got != "ffeeddccbbaa00112233445566778899ffeeddccbbaa00112233445566778899" {
		t.Errorf("star-prefixed name not parsed: %q", got)
	}
	if _, ok := sums["file.txt"]; ok {
		t.Error("invalid hash line should be skipped")
	}
}

func TestClassifyAsset(t *testing.T) {
	cases := []struct {
		name string
		want string
	}{
		{"terminal-windows-amd64-installer-v1.9.2.exe", "installer"},
		{"terminal-windows-arm64-portable-v1.9.2.zip", "portable"},
		{"terminal-darwin-arm64-v1.9.2.zip", "portable"},
		{"terminal-linux-amd64-v1.9.2.tar.gz", "binary-tar.gz"},
		{"terminal-darwin-arm64-v1.9.2.dmg", "other"},
		{"terminal-linux-amd64-v1.9.2.deb", "other"},
		{"terminal-linux-amd64-v1.9.2.rpm", "other"},
	}
	for _, c := range cases {
		if got := classifyAsset(c.name); got != c.want {
			t.Errorf("classifyAsset(%q) = %q, want %q", c.name, got, c.want)
		}
	}
}

func TestAssetMatchesPlatform(t *testing.T) {
	cases := []struct {
		os, arch, name string
		want           bool
	}{
		{"darwin", "arm64", "terminal-darwin-arm64-v1.9.2.zip", true},
		{"darwin", "arm64", "terminal-darwin-amd64-v1.9.2.zip", false},
		{"linux", "amd64", "terminal-linux-amd64-v1.9.2.tar.gz", true},
		{"linux", "arm64", "terminal-linux-amd64-v1.9.2.tar.gz", false},
		{"windows", "amd64", "terminal-windows-amd64-portable-v1.9.2.zip", true},
		{"windows", "arm64", "terminal-windows-amd64-portable-v1.9.2.zip", false},
		{"freebsd", "amd64", "terminal-linux-amd64-v1.9.2.tar.gz", false},
		// The terminal- prefix anchors the match; a name that merely contains
		// "<os>-<arch>-" must not match.
		{"windows", "amd64", "other-terminal-windows-amd64-portable-v1.9.2.zip", false},
		{"windows", "amd64", "checksums.txt", false},
	}
	for _, c := range cases {
		if got := assetMatchesPlatform(c.os, c.arch, c.name); got != c.want {
			t.Errorf("assetMatchesPlatform(%q, %q, %q) = %v, want %v", c.os, c.arch, c.name, got, c.want)
		}
	}
}

func TestCandidatesForOrdering(t *testing.T) {
	rels := map[string]*release{
		"github": {Assets: []releaseAsset{
			{Name: "terminal-windows-amd64-portable-v1.9.2.zip", BrowserDownloadURL: "https://github.com/portable.zip"},
			{Name: "terminal-windows-amd64-installer-v1.9.2.exe", BrowserDownloadURL: "https://github.com/installer.exe"},
			{Name: "terminal-darwin-amd64-v1.9.2.dmg", BrowserDownloadURL: "https://github.com/x.dmg"},
		}},
		"gitee": {Assets: []releaseAsset{
			{Name: "terminal-windows-amd64-portable-v1.9.2.zip", BrowserDownloadURL: "https://gitee.com/portable.zip"},
			{Name: "terminal-windows-amd64-installer-v1.9.2.exe", BrowserDownloadURL: "https://gitee.com/installer.exe"},
		}},
	}
	sums := map[string]string{"terminal-windows-amd64-installer-v1.9.2.exe": "hash1"}

	// Installer channel: installer kind first, primary source (github) first.
	got := candidatesFor("windows", "amd64", ChannelInstaller, "github", rels, sums)
	if len(got) != 4 {
		t.Fatalf("want 4 candidates, got %d: %+v", len(got), got)
	}
	if got[0].Name != "terminal-windows-amd64-installer-v1.9.2.exe" || got[0].Source != "github" {
		t.Errorf("first candidate should be github installer, got %+v", got[0])
	}
	if got[0].SHA256 != "hash1" {
		t.Errorf("sha256 not attached: %+v", got[0])
	}
	if got[1].Source != "gitee" || got[1].Kind() != "installer" {
		t.Errorf("second candidate should be gitee installer, got %+v", got[1])
	}
	// Portable channel: no installer candidates at all.
	got = candidatesFor("windows", "amd64", ChannelPortable, "github", rels, sums)
	if len(got) != 2 {
		t.Fatalf("want 2 portable candidates, got %d: %+v", len(got), got)
	}
	if got[0].Kind() != "portable" || got[1].Kind() != "portable" {
		t.Errorf("portable channel must only return portable assets: %+v", got)
	}
	// Gitee primary flips the ordering.
	got = candidatesFor("windows", "amd64", ChannelPortable, "gitee", rels, sums)
	if got[0].Source != "gitee" || got[1].Source != "github" {
		t.Errorf("gitee primary should come first, got %+v", got)
	}
	// darwin: the .zip is the update payload (dmg is "other").
	rels["github"].Assets = append(rels["github"].Assets,
		releaseAsset{Name: "terminal-darwin-amd64-v1.9.2.zip", BrowserDownloadURL: "https://github.com/darwin.zip"})
	got = candidatesFor("darwin", "amd64", ChannelPortable, "github", rels, sums)
	if len(got) != 1 || got[0].Name != "terminal-darwin-amd64-v1.9.2.zip" {
		t.Errorf("darwin portable should match only the .zip asset, got %+v", got)
	}
	// linux: the bare-binary tar.gz is the update payload (deb/rpm are "other").
	rels["github"].Assets = append(rels["github"].Assets,
		releaseAsset{Name: "terminal-linux-amd64-v1.9.2.tar.gz", BrowserDownloadURL: "https://github.com/linux.tar.gz"},
		releaseAsset{Name: "terminal-linux-amd64-v1.9.2.deb", BrowserDownloadURL: "https://github.com/linux.deb"})
	got = candidatesFor("linux", "amd64", ChannelPortable, "github", rels, sums)
	if len(got) != 1 || got[0].Name != "terminal-linux-amd64-v1.9.2.tar.gz" {
		t.Errorf("linux portable should match only the .tar.gz asset, got %+v", got)
	}
}

// Kind mirrors classifyAsset for test assertions.
func (a UpdateAsset) Kind() string { return classifyAsset(a.Name) }
