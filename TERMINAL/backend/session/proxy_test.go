package session

import "testing"

func TestProxyIsActive(t *testing.T) {
	on := true
	off := false
	cases := []struct {
		name string
		p    Proxy
		want bool
	}{
		{"nil enabled counts as active", Proxy{ID: "p1"}, true},
		{"explicit true", Proxy{ID: "p1", Enabled: &on}, true},
		{"explicit false", Proxy{ID: "p1", Enabled: &off}, false},
	}
	for _, tc := range cases {
		if got := tc.p.IsActive(); got != tc.want {
			t.Errorf("%s: IsActive() = %v, want %v", tc.name, got, tc.want)
		}
	}
}
