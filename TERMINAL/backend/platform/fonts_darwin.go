//go:build darwin

package platform

import (
	"os"
	"path/filepath"
	"strings"
)

// macFontDirs lists the standard macOS font install locations, in the same
// precedence order the system itself uses (user > local machine > system).
// User-installed fonts (Font Book's default "for me only" scope, e.g. a
// double-clicked .ttf/.otf with "Install Font") land in ~/Library/Fonts,
// which unlike Windows requires no registry/plist bookkeeping to discover —
// it's just a directory to walk.
func macFontDirs() []string {
	var dirs []string
	if home, err := os.UserHomeDir(); err == nil {
		dirs = append(dirs, filepath.Join(home, "Library", "Fonts"))
	}
	dirs = append(dirs,
		"/Library/Fonts",
		"/System/Library/Fonts",
		"/System/Library/Fonts/Supplemental",
	)
	return dirs
}

// getSystemFonts enumerates font families by walking the standard macOS font
// directories directly and parsing each TTF/OTF/TTC file's name table, the same
// binary format handled on Windows (see fonts_ttf.go). It returns every family
// found together with its isFixedPitch flag; GetFontFamilies decides which ones
// end up in the picker (all monospaced families, plus installed presets).
//
// This intentionally does not shell out to `fc-list` (fontconfig): macOS does
// not ship fontconfig by default, so on a stock machine that binary doesn't
// exist and every call here would fail, silently falling back to the
// frontend's tiny hardcoded FONT_OPTIONS list — which is exactly what caused
// a user-installed font (in ~/Library/Fonts) to never show up in the picker
// even though other apps could see and use it fine.
func getSystemFonts() ([]fontFamily, error) {
	var families []fontFamily
	seen := make(map[string]bool)
	var firstErr error
	scanned := false

	for _, dir := range macFontDirs() {
		entries, err := os.ReadDir(dir)
		if err != nil {
			// A given font dir may not exist (e.g. no user Fonts folder ever
			// created); that's normal, not an error condition, as long as at
			// least one directory scans successfully.
			if firstErr == nil {
				firstErr = err
			}
			continue
		}
		scanned = true

		for _, entry := range entries {
			if entry.IsDir() {
				continue
			}
			ext := strings.ToLower(filepath.Ext(entry.Name()))
			if ext != ".ttf" && ext != ".otf" && ext != ".ttc" {
				continue
			}

			path := filepath.Join(dir, entry.Name())
			family, isMono, err := parseFont(path)
			if err != nil || family == "" {
				continue
			}
			if seen[family] {
				continue
			}
			seen[family] = true
			families = append(families, fontFamily{Name: family, IsMono: isMono})
		}
	}

	if !scanned && firstErr != nil {
		return nil, firstErr
	}
	return families, nil
}

// readFontFile reads a font file from disk for parsing.
func readFontFile(path string) ([]byte, error) {
	return os.ReadFile(path)
}
