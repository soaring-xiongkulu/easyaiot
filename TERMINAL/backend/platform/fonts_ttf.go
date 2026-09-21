//go:build windows || darwin

package platform

import "fmt"

// parseFont reads a TTF/OTF/TTC font file and returns (familyName, isMonospace, error).
func parseFont(path string) (string, bool, error) {
	data, err := readFontFile(path)
	if err != nil {
		return "", false, err
	}

	// For .ttc files, use the first sub-font's table directory.
	tableDirOffset := 0
	tag := tag4(data, 0)
	if tag == "ttcf" {
		if len(data) < 16 {
			return "", false, fmt.Errorf("ttc too small")
		}
		offset := u32(data, 12)
		if int(offset)+12 > len(data) {
			return "", false, fmt.Errorf("ttc offset out of range")
		}
		tableDirOffset = int(offset)
		tag = tag4(data, tableDirOffset)
	}

	// Validate font file
	if tag != "true" && tag != "\x00\x01\x00\x00" && tag != "OTTO" {
		return "", false, nil // not a supported font, skip silently
	}

	numTables := int(u16(data, tableDirOffset+4))
	if numTables <= 0 || numTables > 200 {
		return "", false, fmt.Errorf("invalid numTables")
	}

	var nameOffset uint32
	var postOffset, os2Offset, cmapOffset uint32

	for i := 0; i < numTables; i++ {
		off := tableDirOffset + 12 + i*16
		if off+16 > len(data) {
			break
		}
		tableTag := tag4(data, off)
		tableOffset := u32(data, off+8)

		switch tableTag {
		case "name":
			nameOffset = tableOffset
		case "post":
			postOffset = tableOffset
		case "OS/2":
			os2Offset = tableOffset
		case "cmap":
			cmapOffset = tableOffset
		}
	}

	if nameOffset == 0 {
		return "", false, fmt.Errorf("name table not found")
	}

	// Exclude symbol/icon fonts (Wingdings, Font Awesome, etc.).
	if os2Offset != 0 && int(os2Offset)+32 <= len(data) {
		familyClass := u16(data, int(os2Offset)+30)
		if familyClass>>8 == 12 {
			return "", false, nil
		}
	}
	if cmapOffset != 0 && hasWindowsSymbolCmap(data, int(cmapOffset)) {
		return "", false, nil
	}

	// Determine monospaced-ness from the post table's isFixedPitch flag. Unlike
	// the symbol/invalid skips above, a non-monospaced font is still a valid
	// pick candidate: return it with isMono=false and let the caller decide
	// (GetFontFamilies unions in preset families like Monaco that render fine in
	// a terminal but ship without the isFixedPitch flag). Returning early here
	// would drop those fonts before they can be matched.
	isMono := postOffset != 0 && int(postOffset)+16 <= len(data) && u32(data, int(postOffset)+12) != 0

	// Read font family name from name table (Name ID 1)
	family := parseNameTable(data, int(nameOffset))
	return family, isMono, nil
}

// hasWindowsSymbolCmap checks whether the cmap table's (platform 3, encoding 0)
// subtable is present — the Windows convention for identifying symbol fonts.
func hasWindowsSymbolCmap(data []byte, cmapOffset int) bool {
	if cmapOffset+4 > len(data) {
		return false
	}
	numTables := int(u16(data, cmapOffset+2))
	if numTables <= 0 || numTables > 100 {
		return false
	}
	for i := 0; i < numTables; i++ {
		recOff := cmapOffset + 4 + i*8
		if recOff+8 > len(data) {
			break
		}
		platformID := u16(data, recOff)
		encodingID := u16(data, recOff+2)
		if platformID == 3 && encodingID == 0 {
			return true
		}
	}
	return false
}

// parseNameTable returns the font family name (Name ID 1) from the name table.
func parseNameTable(data []byte, offset int) string {
	if offset+6 > len(data) {
		return ""
	}

	count := int(u16(data, offset+2))
	storageOffset := offset + int(u16(data, offset+4))
	if count > 500 || storageOffset > len(data) {
		return ""
	}

	var fallback string
	for i := 0; i < count; i++ {
		recOff := offset + 6 + i*12
		if recOff+12 > len(data) {
			break
		}
		platformID := u16(data, recOff)
		encodingID := u16(data, recOff+2)
		nameID := u16(data, recOff+6)
		recLen := int(u16(data, recOff+8))
		recOffset := int(u16(data, recOff+10))

		if nameID != 1 {
			continue
		}

		strOff := storageOffset + recOffset
		if strOff+recLen > len(data) {
			continue
		}
		raw := data[strOff : strOff+recLen]

		if platformID == 3 && encodingID == 1 {
			name := decodeUTF16BE(raw)
			if name == "" {
				continue
			}
			// Prefer localized names (non-ASCII) over English ones.
			if hasNonASCII(name) {
				return name
			}
			if fallback == "" {
				fallback = name
			}
			continue
		}

		// Legacy Macintosh record (platform 1, Mac Roman). Some macOS system
		// fonts — notably Monaco — expose their family ONLY here and carry no
		// Windows (platform 3) record at all, so without this they parse to an
		// empty name and get dropped. Keep it strictly as a fallback and never
		// return early: a font that also has a localized Windows name (e.g. the
		// CJK families 隶书/幼圆) must still surface that name via the branch
		// above, not its ASCII Mac name.
		if platformID == 1 && encodingID == 0 {
			if fallback == "" {
				fallback = decodeMacRoman(raw)
			}
		}
	}

	return fallback
}

func hasNonASCII(s string) bool {
	for _, r := range s {
		if r > 127 {
			return true
		}
	}
	return false
}

func decodeUTF16BE(data []byte) string {
	if len(data)%2 != 0 {
		return ""
	}
	runes := make([]rune, len(data)/2)
	for i := 0; i < len(data); i += 2 {
		runes[i/2] = rune(u16(data, i))
	}
	return string(runes)
}

func decodeMacRoman(data []byte) string {
	runes := make([]rune, len(data))
	for i, b := range data {
		runes[i] = macRomanTable[b]
	}
	return string(runes)
}

// macRomanTable maps the Mac OS Roman character set to Unicode code points.
var macRomanTable = [256]rune{
	0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
	0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
	0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,
	0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F,
	0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27,
	0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
	0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37,
	0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F,
	0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47,
	0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F,
	0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57,
	0x58, 0x59, 0x5A, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F,
	0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67,
	0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6F,
	0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77,
	0x78, 0x79, 0x7A, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F,
	0xC4, 0xC5, 0xC7, 0xC9, 0xD1, 0xD6, 0xDC, 0xE1,
	0xE0, 0xE2, 0xE4, 0xE3, 0xE5, 0xE7, 0xE9, 0xE8,
	0xEA, 0xEB, 0xED, 0xEC, 0xEE, 0xEF, 0xF1, 0xF3,
	0xF2, 0xF4, 0xF6, 0xF5, 0xFA, 0xF9, 0xFB, 0xFC,
	0x2020, 0xB0, 0xA2, 0xA3, 0xA7, 0x2022, 0xB6, 0xDF,
	0xAE, 0xA9, 0x2122, 0xB4, 0xA8, 0x2260, 0xC6, 0xD8,
	0x221E, 0xB1, 0x2264, 0x2265, 0xA5, 0xB5, 0x2202, 0x2211,
	0x220F, 0x03C0, 0x222B, 0xAA, 0xBA, 0x03A9, 0xE6, 0xF8,
	0xBF, 0xA1, 0xAC, 0x221A, 0x0192, 0x2248, 0x2206, 0xAB,
	0xBB, 0x2026, 0xA0, 0xC0, 0xC3, 0xD5, 0x0152, 0x0153,
	0x2013, 0x2014, 0x201C, 0x201D, 0x2018, 0x2019, 0xF7,
	0x25CA, 0xFF, 0x0178, 0x2044, 0x20AC, 0x2039, 0x203A,
	0xFB01, 0xFB02, 0x2021, 0xB7, 0x201A, 0x201E, 0x2030,
	0xC2, 0xCA, 0xC1, 0xCB, 0xC8, 0xCD, 0xCE, 0xCF,
	0xCC, 0xD3, 0xD4, 0xF8FF, 0xD2, 0xDA, 0xDB, 0xD9,
}

// Binary parsing helpers
func tag4(data []byte, off int) string {
	if off+4 > len(data) {
		return ""
	}
	return string(data[off : off+4])
}

func u16(data []byte, off int) uint16 {
	return uint16(data[off])<<8 | uint16(data[off+1])
}

func u32(data []byte, off int) uint32 {
	return uint32(data[off])<<24 | uint32(data[off+1])<<16 | uint32(data[off+2])<<8 | uint32(data[off+3])
}
