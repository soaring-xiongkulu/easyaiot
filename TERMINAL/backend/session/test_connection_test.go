package session

// Regression tests for the "database" connection test dispatch. redis /
// mongodb / elasticsearch are stored as type "database" with a dbType field,
// so ProbeConnection must route them to their dedicated probes instead of
// falling through to the SQL provider registry (which would fail with
// "unsupported database type: ...").

import (
	"strings"
	"testing"
)

func TestProbeConnectionDatabaseDispatchesByDBType(t *testing.T) {
	// 127.0.0.1:1 is a closed port, so each probe fails fast with a dial
	// error. The assertion is about WHICH probe ran, not connectivity.
	cases := []struct {
		name   string
		dbType string
		port   int
	}{
		{"redis", "redis", 6379},
		{"mongodb", "mongodb", 27017},
		{"elasticsearch", "elasticsearch", 9200},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			config := ConnectionConfig{
				Type:   "database",
				DBType: tc.dbType,
				Host:   "127.0.0.1",
				Port:   1,
			}
			_, err := ProbeConnection(config)
			if err == nil {
				t.Fatalf("expected error probing closed port")
			}
			if strings.Contains(err.Error(), "unsupported database type") {
				t.Fatalf("dbType %q was not dispatched to its dedicated probe: %v", tc.dbType, err)
			}
			if !strings.Contains(err.Error(), tc.dbType) {
				t.Fatalf("error should mention the probed database type %q, got: %v", tc.dbType, err)
			}
		})
	}
}
