package database

import (
	"strings"
	"testing"
)

// TestSafeMyIdent covers MySQL identifier quoting and rejection cases.
// Backtick escape relies on doubling; any name containing NUL, path
// separators (.., /, \) or longer than 128 bytes must be rejected so that
// user input cannot break out of the quoted form.
func TestSafeMyIdent(t *testing.T) {
	cases := []struct {
		name    string
		input   string
		wantErr bool
		want    string
	}{
		{"plain", "users", false, "`users`"},
		{"underscore_digits", "user_2024", false, "`user_2024`"},
		{"backtick injection", "`; DROP TABLE users; --", false, "```; DROP TABLE users; --`"},
		{"only backtick escaped", "`", false, "````"},
		{"empty", "", true, ""},
		{"nul byte", "foo\x00bar", true, ""},
		{"path traversal dot", "../etc/passwd", true, ""},
		{"path traversal slash", "/etc/passwd", true, ""},
		{"path traversal backslash", "..\\windows\\system32", true, ""},
		{"too long", strings.Repeat("a", 129), true, ""},
		{"at length cap", strings.Repeat("a", 128), false, "`" + strings.Repeat("a", 128) + "`"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got, err := SafeMyIdent(tc.input)
			if (err != nil) != tc.wantErr {
				t.Fatalf("err = %v, wantErr = %v", err, tc.wantErr)
			}
			if !tc.wantErr && got != tc.want {
				t.Errorf("SafeMyIdent(%q) = %q, want %q", tc.input, got, tc.want)
			}
		})
	}
}

// TestSafePgIdent covers Postgres / rqlite identifier quoting.
// Identical rules to SafeMyIdent except the escape character is `"`.
func TestSafePgIdent(t *testing.T) {
	cases := []struct {
		name    string
		input   string
		wantErr bool
		want    string
	}{
		{"plain", "users", false, `"users"`},
		{"double-quote injection", `x"; DROP TABLE users; --`, false, `"x""; DROP TABLE users; --"`},
		{"only double quote escaped", `"`, false, `""""`},
		{"empty", "", true, ""},
		{"nul byte", "pg\x00table", true, ""},
		{"path traversal", "../../etc/passwd", true, ""},
		{"too long", strings.Repeat("a", 200), true, ""},
		{"schema qualified", "public.users", false, `"public.users"`},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got, err := SafePgIdent(tc.input)
			if (err != nil) != tc.wantErr {
				t.Fatalf("err = %v, wantErr = %v", err, tc.wantErr)
			}
			if !tc.wantErr && got != tc.want {
				t.Errorf("SafePgIdent(%q) = %q, want %q", tc.input, got, tc.want)
			}
		})
	}
}

// TestSafeDefaultLiteral verifies the whitelist for SET DEFAULT literals.
// Allowed: NULL, booleans, CURRENT_*, LOCALTIME*, numeric literals, and
// simple 'single-quoted' strings without embedded quotes.
// Everything else (function calls, statements, expressions) must be rejected.
func TestSafeDefaultLiteral(t *testing.T) {
	cases := []struct {
		input   string
		wantErr bool
		desc    string
	}{
		{"NULL", false, "null"},
		{"TRUE", false, "true literal"},
		{"FALSE", false, "false literal"},
		{"42", false, "integer"},
		{"-3.14", false, "signed decimal"},
		{"+0", false, "signed zero"},
		{"'hello'", false, "single-quoted string"},
		{"'a''b'", true, "embedded quote in string (rejected)"},
		{"CURRENT_TIMESTAMP", false, "timestamp keyword"},
		{"CURRENT_DATE", false, "date keyword"},
		{"CURRENT_TIME", false, "time keyword"},
		{"CURRENT_TIMESTAMP(6)", false, "timestamp with precision"},
		{"LOCALTIMESTAMP", false, "localtimestamp keyword"},
		{"LOCALTIME", false, "localtime keyword"},
		{"bad(); DROP TABLE users; --", true, "raw SQL injection"},
		{"NOW()", true, "function call"},
		{"user_input", true, "bare identifier"},
		{"", true, "empty"},
		{"   ", true, "whitespace only"},
		{"'unterminated", true, "unterminated string"},
	}
	for _, tc := range cases {
		t.Run(tc.desc, func(t *testing.T) {
			_, err := SafeDefaultLiteral(tc.input)
			if (err != nil) != tc.wantErr {
				t.Errorf("SafeDefaultLiteral(%q): err=%v, wantErr=%v", tc.input, err, tc.wantErr)
			}
		})
	}
}

// TestSafeIdentRoundTrip checks that a valid identifier round-trips
// through both SafeMyIdent and SafePgIdent without losing bytes. This
// guards against future regressions where escaping might collapse
// characters we want to preserve.
func TestSafeIdentRoundTrip(t *testing.T) {
	inputs := []string{"users", "user_2024", "weird name", "tab\tname", "newline\nname"}
	for _, in := range inputs {
		t.Run("mysql/"+in, func(t *testing.T) {
			got, err := SafeMyIdent(in)
			if err != nil {
				t.Fatalf("SafeMyIdent(%q): %v", in, err)
			}
			if !strings.Contains(got, in) {
				t.Errorf("SafeMyIdent(%q) = %q lost original bytes", in, got)
			}
		})
		t.Run("pg/"+in, func(t *testing.T) {
			got, err := SafePgIdent(in)
			if err != nil {
				t.Fatalf("SafePgIdent(%q): %v", in, err)
			}
			if !strings.Contains(got, in) {
				t.Errorf("SafePgIdent(%q) = %q lost original bytes", in, got)
			}
		})
	}
}