package importer

import (
	"archive/zip"
	"bytes"
	"testing"
	"unicode/utf16"

	"golang.org/x/text/encoding/simplifiedchinese"
	"golang.org/x/text/transform"
)

func xshellZIP() []byte {
	var buf bytes.Buffer
	zw := zip.NewWriter(&buf)
	w, _ := zw.Create("Xshell/Sessions/prod/web.xsh")
	w.Write([]byte("[CONNECTION]\nProtocol=SSH\nHost=10.0.0.9\nPort=22\n[CONNECTION:AUTHENTICATION]\nUserName=admin\nUserKey=\n"))
	zw.Close()
	return buf.Bytes()
}

// utf16le encodes s as UTF-16LE with a BOM, matching Xshell 8's .xsh content.
func utf16le(s string) []byte {
	u := utf16.Encode([]rune(s))
	b := make([]byte, 2+2*len(u))
	b[0], b[1] = 0xFF, 0xFE
	for i, v := range u {
		b[2+2*i] = byte(v)
		b[3+2*i] = byte(v >> 8)
	}
	return b
}

// gbk encodes a UTF-8 string to GBK bytes, matching Chinese-locale ZIP names.
func gbk(s string) string {
	b, _, _ := transform.Bytes(simplifiedchinese.GBK.NewEncoder(), []byte(s))
	return string(b)
}

// xshellChineseZIP builds a ZIP whose entry name is GBK-encoded (UTF-8 flag
// unset) and whose content is UTF-16LE — the shape Xshell 8 writes on a Chinese
// Windows install.
func xshellChineseZIP() []byte {
	var buf bytes.Buffer
	zw := zip.NewWriter(&buf)
	fh := &zip.FileHeader{Name: "Xshell/" + gbk("文件服务器") + "/172.22.1.146.xsh", Method: zip.Deflate}
	fh.NonUTF8 = true
	w, _ := zw.CreateHeader(fh)
	w.Write(utf16le("[CONNECTION]\nProtocol=SSH\nHost=172.22.1.146\nPort=22\n[CONNECTION:AUTHENTICATION]\nUserName=root\nUserKey=\n"))
	zw.Close()
	return buf.Bytes()
}

func TestParseXshell(t *testing.T) {
	res, err := parseXshell(xshellZIP())
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if len(res.Connections) != 1 {
		t.Fatalf("expected 1 connection, got %d", len(res.Connections))
	}
	c := res.Connections[0]
	if c.Type != "ssh" || c.Host != "10.0.0.9" || c.Port != 22 || c.User != "admin" {
		t.Fatalf("bad mapping: %+v", c)
	}
	if c.Name != "web" {
		t.Fatalf("expected name web, got %q", c.Name)
	}
	if len(res.Groups) != 1 || res.Groups[0].Name != "prod" {
		t.Fatalf("expected 1 group prod, got %+v", res.Groups)
	}
	if c.GroupId == nil || *c.GroupId != res.Groups[0].ID {
		t.Fatalf("connection not assigned to prod group: %+v", c)
	}
}

func TestParseXshellUTF16ContentGBKName(t *testing.T) {
	res, err := parseXshell(xshellChineseZIP())
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if len(res.Connections) != 1 {
		t.Fatalf("expected 1 connection, got %d", len(res.Connections))
	}
	c := res.Connections[0]
	if c.Type != "ssh" || c.Host != "172.22.1.146" || c.Port != 22 || c.User != "root" {
		t.Fatalf("bad mapping: %+v", c)
	}
	if c.Name != "172.22.1.146" {
		t.Fatalf("expected name 172.22.1.146, got %q", c.Name)
	}
	if len(res.Groups) != 1 || res.Groups[0].Name != "文件服务器" {
		t.Fatalf("expected group 文件服务器, got %+v", res.Groups)
	}
	if c.GroupId == nil || *c.GroupId != res.Groups[0].ID {
		t.Fatalf("connection not assigned to 文件服务器 group: %+v", c)
	}
}

func TestDecodeBytes(t *testing.T) {
	if got := decodeBytes(utf16le("[CONNECTION]")); got != "[CONNECTION]" {
		t.Fatalf("utf16le: %q", got)
	}
	if got := decodeBytes([]byte("plain ascii")); got != "plain ascii" {
		t.Fatalf("ascii: %q", got)
	}
	if got := decodeBytes([]byte(gbk("文件服务器"))); got != "文件服务器" {
		t.Fatalf("gbk: %q", got)
	}
}
