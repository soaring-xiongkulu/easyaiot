package importer

import "testing"

func TestParseOpenSSH(t *testing.T) {
	data := []byte("Host web\n  HostName 10.0.0.7\n  User root\n  Port 2222\n  IdentityFile ~/.ssh/id_ed25519\n")
	res, err := parseOpenSSH(data)
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	c := res.Connections[0]
	if c.Type != "ssh" || c.Host != "10.0.0.7" || c.User != "root" || c.Port != 2222 || c.AuthType != "key" {
		t.Fatalf("mapping wrong: %+v", c)
	}
}
