package config

import "testing"

func TestNormalizePostgresURLAddsSSLDisable(t *testing.T) {
	got := NormalizePostgresURL("postgresql://postgres:x@localhost:5432/iot-video20")
	want := "postgresql://postgres:x@localhost:5432/iot-video20?sslmode=disable"
	if got != want {
		t.Fatalf("got %q want %q", got, want)
	}
}

func TestNormalizePostgresURLKeepsExistingSSLMode(t *testing.T) {
	in := "postgresql://postgres:x@localhost:5432/iot-video20?sslmode=require"
	if got := NormalizePostgresURL(in); got != in {
		t.Fatalf("got %q want unchanged", got)
	}
}

func TestNormalizePostgresURLKeywordDSN(t *testing.T) {
	got := NormalizePostgresURL("host=localhost user=postgres dbname=iot-video20")
	if got != "host=localhost user=postgres dbname=iot-video20 sslmode=disable" {
		t.Fatalf("got %q", got)
	}
}
