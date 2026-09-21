//go:build !windows && !darwin

package platform

import (
	"os/exec"
	"strings"
)

// getSystemFonts enumerates installed font families via fontconfig, tagging
// each with whether it is monospaced. GetFontFamilies turns this into the
// picker list (all monospaced families, plus installed presets). We query the
// full family list (so presets like Monaco can be matched even when fontconfig
// doesn't classify them as mono) and separately the mono-only set to set the
// flag.
func getSystemFonts() ([]fontFamily, error) {
	all, err := fcListFamilies("")
	if err != nil {
		return nil, err
	}

	monoSet := make(map[string]bool)
	if mono, err := fcListFamilies(":spacing=mono"); err == nil {
		for _, name := range mono {
			monoSet[strings.ToLower(name)] = true
		}
	}

	families := make([]fontFamily, 0, len(all))
	for _, name := range all {
		families = append(families, fontFamily{
			Name:   name,
			IsMono: monoSet[strings.ToLower(name)],
		})
	}
	return families, nil
}

// fcListFamilies runs `fc-list <filter> family` and returns the unique family
// names. An empty filter lists every installed family.
func fcListFamilies(filter string) ([]string, error) {
	out, err := exec.Command("fc-list", filter, "family").Output()
	if err != nil {
		return nil, err
	}

	seen := make(map[string]bool)
	var families []string
	for _, line := range strings.Split(string(out), "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		// fc-list outputs comma-separated family names per line.
		for _, name := range strings.Split(line, ",") {
			name = strings.TrimSpace(name)
			if name == "" || seen[name] {
				continue
			}
			seen[name] = true
			families = append(families, name)
		}
	}
	return families, nil
}
