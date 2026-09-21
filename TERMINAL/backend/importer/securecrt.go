package importer

import (
	"encoding/xml"
	"strconv"
	"strings"

	"easyaiot/terminal/backend/session"
)

type secureCRTNode struct {
	XMLName xml.Name        `xml:"key"`
	Name    string          `xml:"name,attr"`
	Strings []secureCRTVal  `xml:"string"`
	Dwords  []secureCRTVal  `xml:"dword"`
	Keys    []secureCRTNode `xml:"key"`
}

type secureCRTVal struct {
	Name  string `xml:"name,attr"`
	Value string `xml:",chardata"`
}

var secureCRTProtoToType = map[string]string{
	"SSH2": "ssh", "SSH1": "ssh", "Telnet": "telnet", "Serial": "serial", "RDP": "rdp",
}

func parseSecureCRT(data []byte) (*ImportResult, error) {
	var root secureCRTNode
	if err := xml.Unmarshal(data, &root); err != nil {
		return nil, err
	}
	res := &ImportResult{}
	pathMap := map[string]string{}
	var walk func(n secureCRTNode, ancestors []string)
	walk = func(n secureCRTNode, ancestors []string) {
		proto := nodeStr(n, "Protocol Name")
		host := nodeStr(n, "Hostname")
		if proto != "" && host != "" {
			if typ, ok := secureCRTProtoToType[proto]; ok {
				port := nodeDword(n, "[SSH2] Port")
				if port == 0 {
					port = nodeDword(n, "Port")
				}
				if port == 0 {
					port = defaultPort(typ)
				}
				user := nodeStr(n, "Username")
				if user == "" && typ == "ssh" {
					user = "root"
				}
				conn := session.ConnectionConfig{
					ID: newConnectionID(), Name: n.Name, Type: typ, Host: host, Port: port, User: user,
				}
				if typ == "ssh" {
					conn.AuthType = "password"
				}
				if gid := ensureGroupPath(ancestors, pathMap, &res.Groups, newGroupID); gid != nil {
					conn.GroupId = gid
				}
				res.Connections = append(res.Connections, conn)
			} else {
				res.Warnings = append(res.Warnings, "skipped SecureCRT protocol "+proto)
			}
		}
		for _, child := range n.Keys {
			walk(child, append(ancestors, n.Name))
		}
	}
	// Sessions may be the document root itself, or a child node (e.g. wrapped
	// in a <key name="Config"> container). Support both.
	sessions := root.Keys
	if root.Name != "Sessions" {
		sessions = nil
		for _, child := range root.Keys {
			if child.Name == "Sessions" {
				sessions = child.Keys
				break
			}
		}
	}
	for _, sess := range sessions {
		walk(sess, nil)
	}
	return res, nil
}

func nodeStr(n secureCRTNode, name string) string {
	for _, s := range n.Strings {
		if s.Name == name {
			return strings.TrimSpace(s.Value)
		}
	}
	return ""
}

func nodeDword(n secureCRTNode, name string) int {
	for _, d := range n.Dwords {
		if d.Name == name {
			v, _ := strconv.Atoi(strings.TrimSpace(d.Value))
			return v
		}
	}
	return 0
}
