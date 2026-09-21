package platform

import (
	"sort"
	"strings"
)

// fontFamily is one installed font family together with whether its font file
// flags itself as fixed-pitch (monospaced). Platform enumerators
// (getSystemFonts) return these; GetFontFamilies turns them into the picker
// list.
type fontFamily struct {
	Name   string
	IsMono bool
}

// presetFonts are well-known terminal/coding font families we surface in the
// picker whenever they are installed, EVEN IF their font file does not set the
// post-table isFixedPitch flag. Some popular fonts — notably Monaco and SF Mono
// on macOS — ship without that flag, so pure mono-detection silently drops them
// even though they render perfectly in a terminal. Matching is case-insensitive
// and only adds a preset when it is actually installed, so a broad
// cross-platform list is safe (a Mac simply won't have Consolas, etc.).
var presetFonts = []string{
	// macOS
	"Monaco", "Menlo", "SF Mono", "PT Mono", "Andale Mono", "Courier",
	// Windows
	"Consolas", "Cascadia Code", "Cascadia Mono", "Lucida Console", "Courier New",
	// Cross-platform / Linux
	"DejaVu Sans Mono", "Liberation Mono", "Ubuntu Mono", "Noto Sans Mono",
	"Fira Code", "FiraCode Nerd Font", "JetBrains Mono", "Source Code Pro",
	"Hack", "Inconsolata", "Roboto Mono", "IBM Plex Mono", "Meslo LG S",
	"Anonymous Pro", "Space Mono",
}

// GetFontFamilies returns the sorted, unique list of font families for the
// terminal font picker: every monospaced family installed on the system, plus
// any family from presetFonts that is installed regardless of its isFixedPitch
// flag (see presetFonts). Non-monospaced, non-preset families (e.g. Arial) are
// intentionally excluded to keep the list terminal-appropriate.
func GetFontFamilies() ([]string, error) {
	fams, err := getSystemFonts()
	if err != nil {
		return nil, err
	}

	// Index installed families case-insensitively. installed maps a lowercased
	// name to its canonical spelling (so the picker shows "SF Mono", not
	// whatever case a preset happened to use). monoSet marks families flagged
	// monospaced by at least one of their font files.
	installed := make(map[string]string, len(fams))
	monoSet := make(map[string]bool, len(fams))
	for _, f := range fams {
		if f.Name == "" {
			continue
		}
		lower := strings.ToLower(f.Name)
		if _, ok := installed[lower]; !ok {
			installed[lower] = f.Name
		}
		if f.IsMono {
			monoSet[lower] = true
		}
	}

	chosen := make(map[string]bool, len(monoSet)+len(presetFonts))
	var result []string

	// All monospaced families.
	for lower := range monoSet {
		result = append(result, installed[lower])
		chosen[lower] = true
	}
	// Union in installed preset families that weren't already flagged mono.
	for _, p := range presetFonts {
		lower := strings.ToLower(p)
		if canon, ok := installed[lower]; ok && !chosen[lower] {
			result = append(result, canon)
			chosen[lower] = true
		}
	}

	sort.Strings(result)
	return result, nil
}

// FontInfo is one entry in the terminal font picker: a family name together
// with whether it is monospaced. The frontend filters this client-side (keeps
// only IsMono entries in its "monospace only" view, or shows everything).
type FontInfo struct {
	Name   string
	IsMono bool
}

// GetAllFonts returns every font the picker should offer: the built-in bundled
// web font (JetBrains Mono Variable) pinned at index 0, followed by every
// installed system family. This is the single frontend data source — the app
// does NOT also expose a mono-only endpoint; filtering happens in the UI.
//
// IsMono is true when a family's font file sets isFixedPitch OR the family is
// an installed presetFonts entry whose file lacks that flag (Monaco / SF Mono
// etc.) — preserving the same "monospace view" content GetFontFamilies used to
// produce, while also letting the unchecked view surface non-mono families
// (e.g. CJK fonts) so a user can pick a Chinese fallback for the terminal.
func GetAllFonts() ([]FontInfo, error) {
	fams, err := getSystemFonts()
	if err != nil {
		return nil, err
	}

	presetSet := make(map[string]bool, len(presetFonts))
	for _, p := range presetFonts {
		presetSet[strings.ToLower(p)] = true
	}

	// The built-in font is bundled into the app as a web font, not registered
	// as a system font, so it never shows up in the enumeration. Synthesize it
	// as the terminal's default, pinned to the front of the list.
	result := []FontInfo{{Name: "JetBrains Mono Variable", IsMono: true}}

	seen := make(map[string]bool, len(fams)+1)
	seen["jetbrains mono variable"] = true // skip a same-named system font if any

	for _, f := range fams {
		if f.Name == "" {
			continue
		}
		lower := strings.ToLower(f.Name)
		if seen[lower] {
			continue
		}
		seen[lower] = true
		result = append(result, FontInfo{
			Name:   f.Name,
			IsMono: f.IsMono || presetSet[lower],
		})
	}

	// Keep the built-in entry at index 0, sort the remainder by name.
	tail := result[1:]
	sort.Slice(tail, func(i, j int) bool { return tail[i].Name < tail[j].Name })
	return result, nil
}
