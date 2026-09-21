package importer

import (
	"strconv"
	"strings"

	"easyaiot/terminal/backend/session"
)

var mobaTypeToType = map[string]string{
	"109": "ssh", "98": "telnet", "91": "rdp", "128": "vnc", "131": "serial",
}

func parseMobaXterm(data []byte) (*ImportResult, error) {
	res := &ImportResult{}
	pathMap := map[string]string{}
	text := decodeBytes(data)
	section := ""
	subRep := ""
	for _, line := range strings.Split(text, "\n") {
		line = strings.TrimSpace(strings.TrimRight(line, "\r"))
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			section = strings.Trim(line, "[]")
			subRep = ""
			continue
		}
		if !strings.HasPrefix(section, "Bookmarks") {
			continue
		}
		eq := strings.Index(line, "=")
		if eq < 0 {
			continue
		}
		name := strings.TrimSpace(line[:eq])
		value := strings.TrimSpace(line[eq+1:])
		if name == "SubRep" {
			subRep = value
			continue
		}
		if !strings.HasPrefix(value, "#") {
			continue
		}
		rest := strings.TrimPrefix(value, "#")
		typeEnd := strings.Index(rest, "#")
		if typeEnd < 0 {
			continue
		}
		code := rest[:typeEnd]
		typ, ok := mobaTypeToType[code]
		if !ok {
			res.Warnings = append(res.Warnings, "skipped MobaXterm type "+code)
			continue
		}
		payload := rest[typeEnd+1:]
		// payload is `<subtype>%<host>%<port>%<username>%...`; subtype sits at fields[0].
		fields := strings.Split(payload, "%")
		host, portStr, user := "", "", ""
		if len(fields) > 1 && fields[1] != "-1" {
			host = fields[1]
		}
		if len(fields) > 2 {
			portStr = fields[2]
		}
		if len(fields) > 3 && fields[3] != "-1" {
			user = fields[3]
		}
		port, _ := strconv.Atoi(portStr)
		if port == 0 {
			port = defaultPort(typ)
		}
		conn := session.ConnectionConfig{
			ID: newConnectionID(), Name: name, Type: typ, Host: host, Port: port, User: user,
		}
		if typ == "ssh" {
			conn.AuthType = "password"
			if conn.User == "" {
				conn.User = "root"
			}
		}
		segs := splitNonEmpty(strings.ReplaceAll(subRep, "\\", "/"), "/")
		if gid := ensureGroupPath(segs, pathMap, &res.Groups, newGroupID); gid != nil {
			conn.GroupId = gid
		}
		res.Connections = append(res.Connections, conn)
	}
	return res, nil
}
