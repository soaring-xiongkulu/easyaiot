package database

import (
	"net/url"
	"strings"
	"testing"
)

// TestSqlserverDSN covers DSN building for plain hosts and named instances
// (issue: host containing "\" must not end up in url.URL.Host, where
// url.URL.String() escapes it to %5C and the driver's url.Parse rejects it
// as an invalid URL escape).
func TestSqlserverDSN(t *testing.T) {
	cases := []struct {
		name         string
		host         string
		port         int
		wantHost     string // expected u.Host in the parsed DSN
		wantInstance string // expected u.Path ("/instance") or ""
		wantRawQuery string // substring that must appear in RawQuery
		noPort       bool   // DSN must not carry an explicit port
	}{
		{
			name:         "plain host with default port",
			host:         "localhost",
			port:         0,
			wantHost:     "localhost:1433",
			wantInstance: "",
			wantRawQuery: "database=mydb",
		},
		{
			name:         "plain host with explicit port",
			host:         "db.example.com",
			port:         11433,
			wantHost:     "db.example.com:11433",
			wantInstance: "",
			wantRawQuery: "database=mydb",
		},
		{
			name:         "named instance without port omits port for SQL Browser",
			host:         `localhost\SQLEXPRESS`,
			port:         0,
			wantHost:     "localhost",
			wantInstance: "/SQLEXPRESS",
			wantRawQuery: "database=mydb",
			noPort:       true,
		},
		{
			name:         "named instance with explicit port keeps port",
			host:         `192.168.1.5\SQL2019`,
			port:         21433,
			wantHost:     "192.168.1.5:21433",
			wantInstance: "/SQL2019",
			wantRawQuery: "database=mydb",
		},
	}

	p := &sqlserverProvider{}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			dsn := p.DSN(tc.host, tc.port, "sa", "secret", "mydb", nil)
			u, err := url.Parse(dsn)
			if err != nil {
				t.Fatalf("driver-side url.Parse failed on DSN %q: %v", dsn, err)
			}
			if u.Scheme != "sqlserver" {
				t.Errorf("scheme = %q, want sqlserver", u.Scheme)
			}
			if u.Host != tc.wantHost {
				t.Errorf("host = %q, want %q", u.Host, tc.wantHost)
			}
			if u.Path != tc.wantInstance {
				t.Errorf("path = %q, want %q", u.Path, tc.wantInstance)
			}
			if !strings.Contains(u.RawQuery, tc.wantRawQuery) {
				t.Errorf("raw query %q does not contain %q", u.RawQuery, tc.wantRawQuery)
			}
			if tc.noPort && strings.Contains(u.Host, ":") {
				t.Errorf("DSN %q must omit port for browser resolution", dsn)
			}
			if got, ok := u.User.Password(); !ok || got != "secret" {
				t.Errorf("password not preserved")
			}
		})
	}
}
