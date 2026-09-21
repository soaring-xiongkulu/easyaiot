//go:build windows || darwin

package platform

import "testing"

// buildNameTable assembles a minimal 'name' table with the given Name ID 1
// records so parseNameTable can be exercised without a real font file.
func buildNameTable(recs []nameRecord) []byte {
	const headerLen = 6
	recDirLen := len(recs) * 12
	storageStart := headerLen + recDirLen

	var storage []byte
	dir := make([]byte, 0, recDirLen)
	for _, r := range recs {
		off := len(storage)
		storage = append(storage, r.data...)
		dir = append(dir,
			byte(r.platformID>>8), byte(r.platformID),
			byte(r.encodingID>>8), byte(r.encodingID),
			byte(r.languageID>>8), byte(r.languageID),
			0, 1, // name ID 1 (family)
			byte(len(r.data)>>8), byte(len(r.data)),
			byte(off>>8), byte(off),
		)
	}

	out := make([]byte, 0, storageStart+len(storage))
	out = append(out,
		0, 0, // format
		byte(len(recs)>>8), byte(len(recs)),
		byte(storageStart>>8), byte(storageStart),
	)
	out = append(out, dir...)
	out = append(out, storage...)
	return out
}

type nameRecord struct {
	platformID uint16
	encodingID uint16
	languageID uint16
	data       []byte
}

func utf16BE(s string) []byte {
	var b []byte
	for _, r := range s {
		b = append(b, byte(r>>8), byte(r))
	}
	return b
}

// Monaco (and other legacy macOS system fonts) expose their family name only in
// the Macintosh (platform 1) record. parseNameTable must fall back to it.
func TestParseNameTableMacRomanFallback(t *testing.T) {
	data := buildNameTable([]nameRecord{
		{platformID: 1, encodingID: 0, languageID: 0, data: []byte("Monaco")},
	})
	if got := parseNameTable(data, 0); got != "Monaco" {
		t.Fatalf("parseNameTable = %q, want %q", got, "Monaco")
	}
}

// Regression guard for the CJK bug: a font that carries BOTH an ASCII Mac name
// (record first) AND a localized Windows name (e.g. 隶书/幼圆) must surface the
// localized name, never the Mac ASCII one. The Mac Roman branch is fallback
// only and must not return early.
func TestParseNameTableLocalizedWinsOverMacRoman(t *testing.T) {
	data := buildNameTable([]nameRecord{
		{platformID: 1, encodingID: 0, languageID: 0, data: []byte("YouYuan")},
		{platformID: 3, encodingID: 1, languageID: 0x0804, data: utf16BE("幼圆")},
	})
	if got := parseNameTable(data, 0); got != "幼圆" {
		t.Fatalf("parseNameTable = %q, want %q", got, "幼圆")
	}
}

// An English-only Windows font keeps returning its ASCII family name.
func TestParseNameTableAsciiWindowsName(t *testing.T) {
	data := buildNameTable([]nameRecord{
		{platformID: 3, encodingID: 1, languageID: 0x0409, data: utf16BE("Consolas")},
	})
	if got := parseNameTable(data, 0); got != "Consolas" {
		t.Fatalf("parseNameTable = %q, want %q", got, "Consolas")
	}
}
