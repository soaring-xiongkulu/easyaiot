package importer

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"crypto/sha1"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"golang.org/x/crypto/blowfish"
)

// dbeaverEncryptFile mirrors DBeaver's local credential encryption so tests can
// build a real credentials-config.json: AES-128-CBC with the built-in key and a
// zero IV, where the first plaintext block is the file's random IV.
func dbeaverEncryptFile(t *testing.T, payload []byte) []byte {
	t.Helper()
	block, err := aes.NewCipher(dbeaverAesKey)
	if err != nil {
		t.Fatal(err)
	}
	fileIV := bytes.Repeat([]byte{0xAB}, block.BlockSize())
	plain := append(append([]byte{}, fileIV...), payload...)
	pad := block.BlockSize() - len(plain)%block.BlockSize()
	plain = append(plain, bytes.Repeat([]byte{byte(pad)}, pad)...)
	out := make([]byte, len(plain))
	cipher.NewCBCEncrypter(block, make([]byte, block.BlockSize())).CryptBlocks(out, plain)
	return out
}

// dbeaverEncryptV11 mirrors Navicat v11's Blowfish password scheme for tests.
func dbeaverEncryptV11(t *testing.T, plaintext string) string {
	t.Helper()
	sum := sha1.Sum([]byte("3DC5CA39"))
	bf, err := blowfish.NewCipher(sum[:])
	if err != nil {
		t.Fatal(err)
	}
	iv := bytes.Repeat([]byte{0xFF}, blowfish.BlockSize)
	cv := make([]byte, blowfish.BlockSize)
	bf.Encrypt(cv, iv)

	src := []byte(plaintext)
	var out []byte
	full := len(src) / blowfish.BlockSize * blowfish.BlockSize
	for off := 0; off < full; off += blowfish.BlockSize {
		block := make([]byte, blowfish.BlockSize)
		for i := range block {
			block[i] = src[off+i] ^ cv[i]
		}
		ct := make([]byte, blowfish.BlockSize)
		bf.Encrypt(ct, block)
		out = append(out, ct...)
		next := make([]byte, blowfish.BlockSize)
		copy(next, ct)
		for i := range next {
			next[i] ^= cv[i]
		}
		bf.Encrypt(cv, next)
	}
	if rem := len(src) % blowfish.BlockSize; rem != 0 {
		cv2 := make([]byte, blowfish.BlockSize)
		bf.Encrypt(cv2, cv)
		for i := 0; i < rem; i++ {
			out = append(out, src[full+i]^cv2[i])
		}
	}
	return strings.ToUpper(hex.EncodeToString(out))
}

// dbeaverEncryptV12 mirrors Navicat v12+ NCX password encryption for tests.
func dbeaverEncryptV12(t *testing.T, plaintext string) string {
	t.Helper()
	block, err := aes.NewCipher(navicatNcxKey)
	if err != nil {
		t.Fatal(err)
	}
	src := []byte(plaintext)
	pad := block.BlockSize() - len(src)%block.BlockSize()
	src = append(src, bytes.Repeat([]byte{byte(pad)}, pad)...)
	out := make([]byte, len(src))
	cipher.NewCBCEncrypter(block, navicatNcxIV).CryptBlocks(out, src)
	return strings.ToUpper(hex.EncodeToString(out))
}

func TestParseDBeaver(t *testing.T) {
	dir := t.TempDir()
	sources := map[string]any{
		"connections": map[string]any{
			"mysql-prod": map[string]any{
				"name":     "MySQL Prod",
				"provider": "mysql",
				"folder":   "Company/Prod",
				"configuration": map[string]any{
					"host": "10.0.0.10", "port": "3307", "database": "app", "user": "admin",
				},
			},
			"pg-dev": map[string]any{
				"name":     "PG Dev",
				"provider": "postgresql",
				"configuration": map[string]any{
					"host": "10.0.0.20", "port": 5433, "database": "devdb",
				},
			},
			"sqlite-x": map[string]any{
				"name":         "Unsupported",
				"provider":     "sqlite",
				"configuration": map[string]any{"host": "", "database": "/tmp/x.db"},
			},
		},
	}
	sourcesJSON, _ := json.Marshal(sources)
	creds := map[string]dbeaverCredentials{
		"mysql-prod": func() dbeaverCredentials {
			var c dbeaverCredentials
			c.Conn.User = "admin"
			c.Conn.Password = "p@ss-mysql"
			return c
		}(),
		"pg-dev": func() dbeaverCredentials {
			var c dbeaverCredentials
			c.Conn.User = "pguser"
			c.Conn.Password = "secret-pg"
			return c
		}(),
	}
	credsJSON, _ := json.Marshal(creds)

	if err := os.WriteFile(filepath.Join(dir, "data-sources.json"), sourcesJSON, 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "credentials-config.json"), dbeaverEncryptFile(t, credsJSON), 0600); err != nil {
		t.Fatal(err)
	}

	res, err := parseDBeaver(dir, ParseOptions{})
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if len(res.Connections) != 2 {
		t.Fatalf("expected 2 connections, got %d", len(res.Connections))
	}
	byName := map[string]int{}
	for i, c := range res.Connections {
		byName[c.Name] = i
	}
	mp := res.Connections[byName["MySQL Prod"]]
	if mp.Type != "database" || mp.DBType != "mysql" || mp.Host != "10.0.0.10" || mp.Port != 3307 ||
		mp.DBName != "app" || mp.User != "admin" || mp.Password != "p@ss-mysql" {
		t.Fatalf("mysql-prod mapping wrong: %+v", mp)
	}
	if mp.GroupId == nil || groupPathFor(res.Groups, *mp.GroupId) != "Company/Prod" {
		t.Fatalf("mysql-prod group wrong: %+v", mp.GroupId)
	}
	pg := res.Connections[byName["PG Dev"]]
	if pg.DBType != "postgres" || pg.Port != 5433 || pg.User != "pguser" || pg.Password != "secret-pg" {
		t.Fatalf("pg-dev mapping wrong: %+v", pg)
	}
}

func TestParseDBeaverUndecryptableCredentials(t *testing.T) {
	dir := t.TempDir()
	sources := `{"connections":{"c1":{"name":"C1","provider":"mysql","configuration":{"host":"h","port":"3306"}}}}`
	if err := os.WriteFile(filepath.Join(dir, "data-sources.json"), []byte(sources), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "credentials-config.json"), []byte("garbage-garbage-garbage-garbage"), 0600); err != nil {
		t.Fatal(err)
	}
	res, err := parseDBeaver(dir, ParseOptions{})
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if len(res.Connections) != 1 || res.Connections[0].Password != "" {
		t.Fatalf("expected connection with empty password, got %+v", res.Connections)
	}
	if len(res.Warnings) == 0 {
		t.Fatalf("expected a warning about undecryptable credentials")
	}
}

func TestNavicatPasswordV12(t *testing.T) {
	enc := dbeaverEncryptV12(t, "s3cret")
	got, err := navicatDecryptPassword(enc)
	if err != nil || got != "s3cret" {
		t.Fatalf("v12 roundtrip: got %q err %v", got, err)
	}
}

func TestNavicatPasswordV11(t *testing.T) {
	enc := dbeaverEncryptV11(t, "old-pass")
	got, err := navicatDecryptPassword(enc)
	if err != nil || got != "old-pass" {
		t.Fatalf("v11 roundtrip: got %q err %v", got, err)
	}
}

func TestParseNavicat(t *testing.T) {
	ncx := `<Root>
<Connection ConnectionName="Local MySQL" ConnType="MYSQL" Host="127.0.0.1" Port="3306" Database="shop" UserName="root" Password="` + dbeaverEncryptV12(t, "root-pw") + `"/>
<Connection ConnectionName="Team PG" ConnType="POSTGRESQL" Host="db.corp" Port="5432" Database="analytics" UserName="analyst" Password="` + dbeaverEncryptV11(t, "pg-pw") + `" Folder="Corp"/>
<Connection ConnectionName="Bad Type" ConnType="SQLITE" Host="x" Port="0"/>
</Root>`
	path := filepath.Join(t.TempDir(), "connections.ncx")
	if err := os.WriteFile(path, []byte(ncx), 0600); err != nil {
		t.Fatal(err)
	}
	res, err := parseNavicat(path, ParseOptions{})
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if len(res.Connections) != 2 {
		t.Fatalf("expected 2 connections, got %d", len(res.Connections))
	}
	my := res.Connections[0]
	if my.DBType != "mysql" || my.Host != "127.0.0.1" || my.Port != 3306 || my.DBName != "shop" ||
		my.User != "root" || my.Password != "root-pw" {
		t.Fatalf("mysql mapping wrong: %+v", my)
	}
	pg := res.Connections[1]
	if pg.DBType != "postgres" || pg.User != "analyst" || pg.Password != "pg-pw" {
		t.Fatalf("pg mapping wrong: %+v", pg)
	}
	if pg.GroupId == nil || groupPathFor(res.Groups, *pg.GroupId) != "Corp" {
		t.Fatalf("pg group wrong: %+v", pg.GroupId)
	}
}
