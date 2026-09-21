//go:build windows

package session

import "testing"

func TestSplitDomainUser(t *testing.T) {
	bs := string(rune(92))
	tests := []struct{ in, wantDomain, wantUser string }{
		{"", "", ""},
		{"zhanglq", "", "zhanglq"},
		{"CONTOSO" + bs + "zhanglq", "CONTOSO", "zhanglq"},
		{"WIN-DM8569S7RTE" + bs + "zhanglq", "WIN-DM8569S7RTE", "zhanglq"},
		{"a" + bs + "b" + bs + "c", "a" + bs + "b", "c"},
		{bs + "zhanglq", "", "zhanglq"},
	}
	for _, tc := range tests {
		domain, user := splitDomainUser(tc.in)
		if domain != tc.wantDomain || user != tc.wantUser {
			t.Errorf("splitDomainUser(%q) = (%q, %q), want (%q, %q)", tc.in, domain, user, tc.wantDomain, tc.wantUser)
		}
	}
}
