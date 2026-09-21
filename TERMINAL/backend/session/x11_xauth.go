package session

import (
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"os"
	"strings"
)

// xauthFamilies — see xauth(1).
const (
	xauthFamilyLocal    uint16 = 0
	xauthFamilyWildcard uint16 = 65535
)

const xauthProtocolMIT = "MIT-MAGIC-COOKIE-1"

// LookupCookie reads the MIT-MAGIC-COOKIE-1 cookie for `display` from the
// xauthority file at `xauthPath`. Returns os.ErrNotExist when the file or
// matching entry is missing; returns a descriptive error when only an
// unsupported protocol (e.g. XDM-AUTHORIZATION-1) is present. Wildcard-family
// (65535) and local-family (0) entries both match a local DISPLAY.
func LookupCookie(xauthPath, display string) (proto string, cookie []byte, err error) {
	if xauthPath == "" {
		return "", nil, os.ErrNotExist
	}
	f, err := os.Open(xauthPath)
	if err != nil {
		return "", nil, err
	}
	defer f.Close()

	_, _, _, perr := ParseDisplay(display)
	if perr != nil {
		return "", nil, perr
	}
	dispStr := displayNumberString(display)

	var bestCookie []byte
	var bestProto string
	entryIdx := 0
	for {
		family, addr, num, name, data, err := readXauthEntry(f)
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			return "", nil, fmt.Errorf("xauth parse: %w", err)
		}
		matches := xauthEntryMatches(family, addr, num, display, dispStr)
		if !matches {
			entryIdx++
			continue
		}
		if name != xauthProtocolMIT {
			entryIdx++
			continue
		}
		bestCookie = data
		bestProto = name
		break
	}
	if bestCookie == nil {
		return "", nil, os.ErrNotExist
	}
	return bestProto, bestCookie, nil
}

// displayNumberString returns the display number portion of a DISPLAY
// string, e.g. ":5.1" → "5", "localhost:0" → "0". Used to match xauth
// entries whose "number" field is the display number as ASCII.
func displayNumberString(display string) string {
	if i := strings.LastIndex(display, ":"); i >= 0 {
		display = display[i+1:]
	}
	if i := strings.Index(display, "."); i >= 0 {
		display = display[:i]
	}
	return display
}

func xauthEntryMatches(family uint16, addr, num, display, dispStr string) bool {
	// An empty display number in the xauth entry is a wildcard: it matches
	// any display. XWayland (mutter/GDM) writes entries with an empty
	// display number, relying on libXau to treat "" as match-all.
	if num != "" && num != dispStr {
		return false
	}
	switch family {
	case xauthFamilyWildcard:
		return true
	case xauthFamilyLocal:
		// FamilyLocal matches "local" DISPLAYs: ":N", "unix:N", XQuartz path.
		return strings.HasPrefix(display, ":") || strings.HasPrefix(display, "unix:") || strings.HasPrefix(display, "/")
	default:
		// FamilyInternet / FamilyInternet6: addr must equal host part of DISPLAY.
		host := ""
		if i := strings.LastIndex(display, ":"); i >= 0 {
			host = display[:i]
		}
		return host == addr
	}
}

// readXauthEntry reads one xauthority entry from r. On EOF it returns
// io.EOF. Malformed input returns a descriptive error.
func readXauthEntry(r io.Reader) (family uint16, addr, num, name string, data []byte, err error) {
	read16 := func() (uint16, error) {
		var v uint16
		if e := binary.Read(r, binary.BigEndian, &v); e != nil {
			return 0, e
		}
		return v, nil
	}
	readField := func() (string, error) {
		n, e := read16()
		if e != nil {
			return "", e
		}
		buf := make([]byte, n)
		if _, e := io.ReadFull(r, buf); e != nil {
			return "", e
		}
		return string(buf), nil
	}
	readBytes := func() ([]byte, error) {
		n, e := read16()
		if e != nil {
			return nil, e
		}
		buf := make([]byte, n)
		if _, e := io.ReadFull(r, buf); e != nil {
			return nil, e
		}
		return buf, nil
	}
	family, err = read16()
	if err != nil {
		if errors.Is(err, io.EOF) {
			return 0, "", "", "", nil, io.EOF
		}
		return 0, "", "", "", nil, err
	}
	if addr, err = readField(); err != nil {
		return 0, "", "", "", nil, err
	}
	if num, err = readField(); err != nil {
		return 0, "", "", "", nil, err
	}
	if name, err = readField(); err != nil {
		return 0, "", "", "", nil, err
	}
	if data, err = readBytes(); err != nil {
		return 0, "", "", "", nil, err
	}
	return family, addr, num, name, data, nil
}
