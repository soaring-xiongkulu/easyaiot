package k8s

import "testing"

func TestParseServerAddr(t *testing.T) {
	cases := []struct {
		in   string
		host string
		port int
		bad  bool
	}{
		{"https://foo:6443", "foo", 6443, false},
		{"https://foo:6443/path", "foo", 6443, false},
		{"https://foo", "foo", 443, false},
		{"http://foo", "foo", 80, false},
		{"https://1.2.3.4:8443", "1.2.3.4", 8443, false},
		{"https://[::1]:6443", "::1", 6443, false},
		{"", "", 0, true},
		{"https://", "", 0, true},
		{"foo:6443", "", 0, true}, // 缺 scheme，url.Parse 把 "foo" 当 scheme
		{"ftp://foo", "", 0, true},
	}
	for _, c := range cases {
		host, port, err := ParseServerAddr(c.in)
		if c.bad {
			if err == nil {
				t.Errorf("ParseServerAddr(%q): want error, got host=%q port=%d", c.in, host, port)
			}
			continue
		}
		if err != nil {
			t.Errorf("ParseServerAddr(%q): unexpected err %v", c.in, err)
			continue
		}
		if host != c.host || port != c.port {
			t.Errorf("ParseServerAddr(%q) = (%q,%d); want (%q,%d)", c.in, host, port, c.host, c.port)
		}
	}
}
