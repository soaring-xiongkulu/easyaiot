package session

import "testing"

func TestANSIStripperRemovesCharacterSetDesignation(t *testing.T) {
	tests := []struct {
		name string
		in   string
		want string
	}{
		{"G0 ASCII", "Type help\x1b(B for instructions", "Type help for instructions"},
		{"G1 ASCII", "root\x1b)B@host", "root@host"},
		{"all SCS introducers", "a\x1b(B\x1b)B\x1b*B\x1b+B\x1b-B\x1b.B\x1b/Bb", "ab"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var stripper ansiStripper
			if got := string(stripper.Strip([]byte(tt.in))); got != tt.want {
				t.Fatalf("Strip(%q) = %q, want %q", tt.in, got, tt.want)
			}
		})
	}
}

func TestANSIStripperCharacterSetDesignationAcrossChunks(t *testing.T) {
	tests := []struct {
		name   string
		chunks []string
	}{
		{"split after ESC", []string{"root\x1b", "(B@host"}},
		{"split after introducer", []string{"root\x1b(", "B@host"}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var stripper ansiStripper
			var got []byte
			for _, chunk := range tt.chunks {
				got = append(got, stripper.Strip([]byte(chunk))...)
			}
			if string(got) != "root@host" {
				t.Fatalf("stripped chunks = %q, want %q", got, "root@host")
			}
		})
	}
}
