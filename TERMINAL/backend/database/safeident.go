package database

import (
	"errors"
	"fmt"
	"strings"
)

// SafeMyIdent returns the MySQL identifier with backticks escaped (doubled)
// and rejects names containing NUL bytes, dot-segments, or excessive length.
// Addresses AUDIT-database-01 / AUDIT-database-02 (SQL injection via dbName
// and Quote on MySQL).
func SafeMyIdent(name string) (string, error) {
	if err := identValidate(name); err != nil {
		return "", err
	}
	return "`" + strings.ReplaceAll(name, "`", "``") + "`", nil
}

// SafePgIdent returns the Postgres / rqlite identifier with double-quotes
// escaped (doubled). Addresses AUDIT-database-03 and AUDIT-database-05.
func SafePgIdent(name string) (string, error) {
	if err := identValidate(name); err != nil {
		return "", err
	}
	return `"` + strings.ReplaceAll(name, `"`, `""`) + `"`, nil
}

// SafeDefaultLiteral validates a literal value suitable for embedding in a
// `DEFAULT` clause. Only number / string / NULL / CURRENT_* / boolean
// literals are accepted; everything else is rejected to prevent injection
// into `ALTER TABLE ... SET DEFAULT %s` (AUDIT-database-04).
func SafeDefaultLiteral(v string) (string, error) {
	v = strings.TrimSpace(v)
	if v == "" {
		return "", errors.New("empty DEFAULT literal")
	}
	upper := strings.ToUpper(v)
	switch {
	case upper == "NULL",
		upper == "TRUE",
		upper == "FALSE",
		upper == "CURRENT_TIMESTAMP",
		upper == "CURRENT_DATE",
		upper == "CURRENT_TIME",
		strings.HasPrefix(upper, "CURRENT_TIMESTAMP("),
		strings.HasPrefix(upper, "LOCALTIMESTAMP"),
		strings.HasPrefix(upper, "LOCALTIME"):
		return v, nil
	}
	// Numeric literal: digits + optional decimal + optional sign.
	isNum := true
	for i, r := range v {
		if r == '+' || r == '-' || r == '.' {
			continue
		}
		if r < '0' || r > '9' {
			isNum = false
			break
		}
		_ = i
	}
	if isNum {
		return v, nil
	}
	// String literal: 'foo' (single quotes doubled).
	if v[0] == '\'' && v[len(v)-1] == '\'' {
		// no embedded unescaped quotes
		if !strings.Contains(v[1:len(v)-1], "'") {
			return v, nil
		}
	}
	return "", fmt.Errorf("unsafe DEFAULT literal: %s", v)
}

// identValidate rejects names that are empty, contain path-traversal
// segments, NUL bytes, or are absurdly long (MySQL limit is 64, Postgres
// 63; we pick 128 as a generous cap covering schema-qualified forms).
func identValidate(name string) error {
	if name == "" {
		return errors.New("empty identifier")
	}
	if len(name) > 128 {
		return errors.New("identifier too long")
	}
	if strings.ContainsRune(name, 0) {
		return errors.New("identifier contains NUL")
	}
	if strings.Contains(name, "..") || strings.ContainsAny(name, "/\\") {
		return errors.New("identifier contains path separator")
	}
	return nil
}