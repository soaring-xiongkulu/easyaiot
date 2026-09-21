package importer

import "testing"

func TestParseSecureCRT(t *testing.T) {
	data := []byte(`<key name="Sessions"><key name="prod"><key name="web"><string name="Protocol Name">SSH2</string><string name="Hostname">10.0.0.6</string><string name="Username">root</string><dword name="Port">22</dword></key></key></key>`)
	res, err := parseSecureCRT(data)
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if len(res.Connections) != 1 {
		t.Fatalf("expected 1 connection, got %d", len(res.Connections))
	}
	c := res.Connections[0]
	if c.Type != "ssh" || c.Host != "10.0.0.6" || c.User != "root" {
		t.Fatalf("mapping wrong: %+v", c)
	}
	if len(res.Groups) != 1 {
		t.Fatalf("expected 1 group (prod), got %d", len(res.Groups))
	}
}
