//go:build windows

package platform

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"golang.org/x/sys/windows/registry"
)

// getSystemFonts enumerates font families from both the machine-wide
// registry/font store and the per-user one, returning each family with its
// isFixedPitch flag (GetFontFamilies decides the final picker list). Windows 10
// 1809+ allows installing a font without admin rights ("Install for me only" /
// double-click a .ttf preview and hit Install as a standard user), which
// writes to HKCU + %LOCALAPPDATA%\Microsoft\Windows\Fonts instead of HKLM +
// C:\Windows\Fonts. Other apps see such fonts via the GDI/DirectWrite system
// font enumeration APIs, which cover both scopes; our hand-rolled registry
// walk needs to check both explicitly or it silently misses user-installed
// fonts (https://github.com/ys-ll/uniterm/issues/145).
func getSystemFonts() ([]fontFamily, error) {
	var families []fontFamily
	var firstErr error

	if fam, err := readFontFamilies(registry.LOCAL_MACHINE, `SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts`, `C:\Windows\Fonts`); err != nil {
		firstErr = err
	} else {
		families = append(families, fam...)
	}

	// Per-user scope is optional: on systems/setups where nothing was ever
	// installed at user scope this key simply doesn't exist, which is normal
	// and not reported as an error as long as the machine-wide scan above
	// found something.
	if userFontDir := userFontsDir(); userFontDir != "" {
		if fam, err := readFontFamilies(registry.CURRENT_USER, `Software\Microsoft\Windows NT\CurrentVersion\Fonts`, userFontDir); err == nil {
			families = append(families, fam...)
		}
	}

	if len(families) == 0 && firstErr != nil {
		return nil, firstErr
	}
	return families, nil
}

// userFontsDir returns the per-user font install directory, or "" if
// %LOCALAPPDATA% isn't set (unexpected, but avoids a bogus relative path).
func userFontsDir() string {
	local := os.Getenv("LOCALAPPDATA")
	if local == "" {
		return ""
	}
	return filepath.Join(local, "Microsoft", "Windows", "Fonts")
}

// readFontFamilies reads one Fonts registry key (HKLM or HKCU) and resolves
// each value against fontDir, returning the family names found in that scope
// together with their isFixedPitch flag.
func readFontFamilies(root registry.Key, keyPath, fontDir string) ([]fontFamily, error) {
	key, err := registry.OpenKey(root, keyPath, registry.QUERY_VALUE)
	if err != nil {
		return nil, fmt.Errorf("open registry: %w", err)
	}
	defer key.Close()

	names, err := key.ReadValueNames(-1)
	if err != nil {
		return nil, fmt.Errorf("read value names: %w", err)
	}

	var families []fontFamily
	seen := make(map[string]bool)

	for _, name := range names {
		val, _, err := key.GetStringValue(name)
		if err != nil {
			continue
		}

		path := resolveFontPath(val, fontDir)
		if path == "" {
			continue
		}

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

	return families, nil
}

func resolveFontPath(val, fontDir string) string {
	// Absolute path
	if strings.Contains(val, `:\`) {
		if _, err := os.Stat(val); err == nil {
			return val
		}
		return ""
	}

	// Relative to fontDir
	path := val
	if !filepath.IsAbs(val) {
		path = filepath.Join(fontDir, val)
	}
	if _, err := os.Stat(path); err == nil {
		return path
	}
	return ""
}

// readFontFile reads a font file from disk for parsing.
func readFontFile(path string) ([]byte, error) {
	return os.ReadFile(path)
}
