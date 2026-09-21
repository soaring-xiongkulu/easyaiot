package importer

import (
	"archive/zip"
	"bytes"
	"encoding/binary"
	"io"
	"path"
	"strconv"
	"strings"
	"unicode/utf16"
	"unicode/utf8"

	"easyaiot/terminal/backend/session"
	"golang.org/x/text/encoding/simplifiedchinese"
	"golang.org/x/text/transform"
)

var xshellProtocolToType = map[string]string{
	"SSH": "ssh", "SFTP": "sftp", "TELNET": "telnet", "RDP": "rdp", "SERIAL": "serial",
}

func parseXshell(data []byte) (*ImportResult, error) {
	zr, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
	if err != nil {
		return nil, err
	}
	res := &ImportResult{}
	pathMap := map[string]string{}
	for _, f := range zr.File {
		// Chinese-locale Xshell writes ZIP entry names as GBK (the UTF-8 flag is
		// unset), so recover the raw bytes and decode them rather than trusting f.Name.
		name := decodeBytes([]byte(f.Name))
		if !strings.HasSuffix(strings.ToLower(name), ".xsh") {
			continue
		}
		rc, err := f.Open()
		if err != nil {
			continue
		}
		raw, err := io.ReadAll(rc)
		rc.Close()
		if err != nil {
			continue
		}
		conn, ok := parseXshellXSH(name, decodeBytes(raw))
		if !ok {
			res.Warnings = append(res.Warnings, "skipped unsupported/encrypted session: "+name)
			continue
		}
		// Group path = the entry's directory, minus the Xshell/ (or Xshell/Sessions/)
		// prefix. The .xsh filename is the connection name, not a group.
		dir := path.Dir(strings.ReplaceAll(name, "\\", "/"))
		dir = strings.TrimPrefix(dir, "Xshell/Sessions/")
		dir = strings.TrimPrefix(dir, "Xshell/")
		segs := splitNonEmpty(dir, "/")
		if gid := ensureGroupPath(segs, pathMap, &res.Groups, newGroupID); gid != nil {
			conn.GroupId = gid
		}
		res.Connections = append(res.Connections, conn)
	}
	return res, nil
}

// decodeBytes decodes text with a BOM/encoding sniff, shared by the third-party
// importers: BOM → UTF-16LE/BE or UTF-8, else UTF-8 if valid, else GBK. Xshell 8
// writes .xsh content as UTF-16 (LE with BOM); older versions and Chinese-locale
// filenames are GBK; ASCII/UTF-8 pass through unchanged. MobaXterm .mxtsessions
// on a Chinese locale is GBK.
func decodeBytes(raw []byte) string {
	if len(raw) >= 2 {
		switch {
		case raw[0] == 0xFF && raw[1] == 0xFE: // UTF-16LE
			return decodeUTF16(raw[2:], binary.LittleEndian)
		case raw[0] == 0xFE && raw[1] == 0xFF: // UTF-16BE
			return decodeUTF16(raw[2:], binary.BigEndian)
		}
	}
	if len(raw) >= 3 && raw[0] == 0xEF && raw[1] == 0xBB && raw[2] == 0xBF { // UTF-8 BOM
		return string(raw[3:])
	}
	if utf8.Valid(raw) {
		return string(raw)
	}
	return decodeGBK(raw)
}

func decodeUTF16(b []byte, order binary.ByteOrder) string {
	u := make([]uint16, len(b)/2)
	for i := range u {
		u[i] = order.Uint16(b[2*i:])
	}
	return string(utf16.Decode(u))
}

func decodeGBK(b []byte) string {
	s, _, _ := transform.String(simplifiedchinese.GBK.NewDecoder(), string(b))
	return s
}

func splitNonEmpty(s, sep string) []string {
	parts := strings.Split(s, sep)
	var out []string
	for _, p := range parts {
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}

func parseXshellXSH(name string, text string) (session.ConnectionConfig, bool) {
	proto := iniVal(text, "CONNECTION", "Protocol")
	typ, ok := xshellProtocolToType[strings.ToUpper(proto)]
	if !ok {
		return session.ConnectionConfig{}, false
	}
	host := iniVal(text, "CONNECTION", "Host")
	port, _ := strconv.Atoi(iniVal(text, "CONNECTION", "Port"))
	if port == 0 {
		port = defaultPort(typ)
	}
	user := iniVal(text, "CONNECTION:AUTHENTICATION", "UserName")
	userKey := iniVal(text, "CONNECTION:AUTHENTICATION", "UserKey")
	conn := session.ConnectionConfig{
		ID:   newConnectionID(),
		Name: path.Base(strings.TrimSuffix(name, ".xsh")),
		Type: typ, Host: host, Port: port, User: user,
	}
	if typ == "ssh" || typ == "sftp" {
		if user == "" {
			conn.User = "root"
		}
		if userKey != "" {
			conn.AuthType = "key"
			conn.KeyPath = userKey
		} else {
			conn.AuthType = "password"
		}
	}
	return conn, true
}

func defaultPort(typ string) int {
	switch typ {
	case "ssh", "sftp":
		return 22
	case "telnet":
		return 23
	case "rdp":
		return 3389
	}
	return 0
}

// iniVal extracts a `Key=` value from a naive `[Section]` block. Minimal INI
// handling: sections start a line with '['; keys are `Key=Value`.
func iniVal(text, section, key string) string {
	inSection := false
	prefix := key + "="
	for _, line := range strings.Split(text, "\n") {
		line = strings.TrimSpace(strings.TrimRight(line, "\r"))
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			inSection = strings.EqualFold(strings.Trim(line, "[]"), section)
			continue
		}
		if !inSection {
			continue
		}
		if strings.HasPrefix(line, prefix) {
			return strings.TrimSpace(line[len(prefix):])
		}
	}
	return ""
}
