package importer

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/sha1"
	"encoding/hex"
	"encoding/xml"
	"errors"
	"fmt"
	"os"
	"strconv"
	"strings"

	"easyaiot/terminal/backend/session"
	"golang.org/x/crypto/blowfish"
)

// FormatNavicat imports Navicat connections from a .ncx export file
// (File → Export Connections with "Export password" checked).
const FormatNavicat = "navicat"

// navicatNcxKey / navicatNcxIV are Navicat v12+'s fixed export-file key pair.
var (
	navicatNcxKey = []byte("libcckeylibcckey")
	navicatNcxIV  = []byte("libcciv libcciv ")
)

// navicatConnType maps NCX ConnType values directly onto uniterm database
// targets (config type + dbType + default port).
var navicatConnType = map[string]connTarget{
	"MYSQL":      {Type: "database", DBType: "mysql", Port: 3306},
	"MARIADB":    {Type: "database", DBType: "mysql", Port: 3306},
	"POSTGRESQL": {Type: "database", DBType: "postgres", Port: 5432},
	"MSSQL":      {Type: "database", DBType: "sqlserver", Port: 1433},
	"ORACLE":     {Type: "database", DBType: "oracle", Port: 1521},
	"MONGODB":    {Type: "mongodb", Port: 27017},
	"REDIS":      {Type: "redis", Port: 6379},
}

// navicatConn is one <Connection .../> element of an .ncx export. The format
// keeps every field as XML attributes.
type navicatConn struct {
	ConnectionName string `xml:"ConnectionName,attr"`
	ConnType       string `xml:"ConnType,attr"`
	Host           string `xml:"Host,attr"`
	Port           string `xml:"Port,attr"`
	Database       string `xml:"Database,attr"`
	UserName       string `xml:"UserName,attr"`
	Password       string `xml:"Password,attr"`
	Folder         string `xml:"Folder,attr"`
}

// parseNavicat imports connections from a Navicat .ncx export file. Passwords
// are decrypted with the v12+ AES scheme, falling back to the v11 Blowfish
// variant for older exports.
func parseNavicat(srcPath string, _ ParseOptions) (*ImportResult, error) {
	raw, err := os.ReadFile(srcPath)
	if err != nil {
		return nil, err
	}

	// .ncx files may be UTF-16 encoded; convert to UTF-8 before XML decode.
	raw = normalizeNavicatEncoding(raw)

	var root struct {
		Conns []navicatConn `xml:"Connection"`
	}
	if err := xml.Unmarshal(raw, &root); err != nil {
		return nil, fmt.Errorf("parse .ncx: %w", err)
	}
	if len(root.Conns) == 0 {
		return nil, errors.New("no <Connection> entries found; is this an exported .ncx file?")
	}

	res := &ImportResult{}
	pathMap := map[string]string{}
	newGroup := func() string { return newGroupID() }

	for _, c := range root.Conns {
		tgt, ok := navicatConnType[strings.ToUpper(strings.TrimSpace(c.ConnType))]
		if !ok {
			if c.ConnType != "" {
				res.Warnings = append(res.Warnings, fmt.Sprintf("%s: unsupported connection type %q, skipped", c.ConnectionName, c.ConnType))
			}
			continue
		}
		conn := session.ConnectionConfig{
			ID:       newConnectionID(),
			Name:     firstNonEmpty(c.ConnectionName, c.Host),
			Type:     tgt.Type,
			DBType:   tgt.DBType,
			Host:     c.Host,
			DBName:   c.Database,
			User:     c.UserName,
			AuthType: "password",
		}
		if p, err := strconv.Atoi(strings.TrimSpace(c.Port)); err == nil && p > 0 {
			conn.Port = p
		} else {
			conn.Port = tgt.Port
		}
		if c.Password != "" {
			pwd, err := navicatDecryptPassword(c.Password)
			if err != nil {
				res.Warnings = append(res.Warnings, fmt.Sprintf("%s: password could not be decrypted, left empty", c.ConnectionName))
			} else {
				conn.Password = pwd
			}
		}
		if c.Folder != "" {
			conn.GroupId = ensureGroupPath([]string{c.Folder}, pathMap, &res.Groups, newGroup)
		}
		res.Connections = append(res.Connections, conn)
	}
	return res, nil
}

// utf16BOM is the U+FEFF byte-order mark appearing at the start of a decoded
// UTF-16 string.
const utf16BOM = "\ufeff"

// normalizeNavicatEncoding converts UTF-16 (LE or BE, with BOM) .ncx content to
// UTF-8; anything else is returned unchanged.
func normalizeNavicatEncoding(raw []byte) []byte {
	if len(raw) >= 2 {
		if raw[0] == 0xFF && raw[1] == 0xFE {
			return []byte(strings.TrimPrefix(runesFromUTF16LE(raw[2:]), utf16BOM))
		}
		if raw[0] == 0xFE && raw[1] == 0xFF {
			return []byte(strings.TrimPrefix(runesFromUTF16BE(raw[2:]), utf16BOM))
		}
	}
	return raw
}

func runesFromUTF16LE(b []byte) string {
	var sb strings.Builder
	for i := 0; i+1 < len(b); i += 2 {
		sb.WriteRune(rune(uint16(b[i]) | uint16(b[i+1])<<8))
	}
	return sb.String()
}

func runesFromUTF16BE(b []byte) string {
	var sb strings.Builder
	for i := 0; i+1 < len(b); i += 2 {
		sb.WriteRune(rune(uint16(b[i])<<8 | uint16(b[i+1])))
	}
	return sb.String()
}

// navicatDecryptPassword tries the v12+ AES-128-CBC scheme first (uppercase hex
// ciphertext), then the v11 Blowfish-based variant used by older exports.
func navicatDecryptPassword(cipherHex string) (string, error) {
	s := strings.TrimSpace(cipherHex)
	if v12, err := navicatDecryptV12(s); err == nil {
		return v12, nil
	}
	return navicatDecryptV11(s)
}

// navicatDecryptV12 decrypts Navicat v12+ passwords: AES-128-CBC with the fixed
// libcckey/libcciv pair over PKCS#7-padded plaintext, uppercase hex encoded.
func navicatDecryptV12(s string) (string, error) {
	data, err := hex.DecodeString(strings.ToLower(s))
	if err != nil {
		return "", err
	}
	block, err := aes.NewCipher(navicatNcxKey)
	if err != nil {
		return "", err
	}
	if len(data) == 0 || len(data)%block.BlockSize() != 0 {
		return "", errors.New("invalid ciphertext length")
	}
	plain := make([]byte, len(data))
	cipher.NewCBCDecrypter(block, navicatNcxIV).CryptBlocks(plain, data)
	plain, err = pkcs7Unpad(plain, block.BlockSize())
	if err != nil {
		return "", err
	}
	return string(plain), nil
}

// navicatDecryptV11 decrypts Navicat v11 passwords: Blowfish-ECB with the
// SHA-1 of "3DC5CA39" as key, in a CBC-like XOR feedback mode whose IV is the
// encryption of 0xFFFFFFFFFFFFFFFF.
func navicatDecryptV11(s string) (string, error) {
	data, err := hex.DecodeString(strings.ToLower(s))
	if err != nil {
		return "", err
	}
	sum := sha1.Sum([]byte("3DC5CA39"))
	bf, err := blowfish.NewCipher(sum[:])
	if err != nil {
		return "", err
	}
	iv := make([]byte, blowfish.BlockSize)
	for i := range iv {
		iv[i] = 0xFF
	}
	cv := make([]byte, blowfish.BlockSize)
	bf.Encrypt(cv, iv)

	plain := make([]byte, 0, len(data))
	for off := 0; off+blowfish.BlockSize <= len(data); off += blowfish.BlockSize {
		block := make([]byte, blowfish.BlockSize)
		bf.Decrypt(block, data[off:off+blowfish.BlockSize])
		for i := range block {
			block[i] ^= cv[i]
		}
		plain = append(plain, block...)
		next := make([]byte, blowfish.BlockSize)
		copy(next, data[off:off+blowfish.BlockSize])
		for i := range next {
			next[i] ^= cv[i]
		}
		bf.Encrypt(cv, next)
	}
	if rem := len(data) % blowfish.BlockSize; rem != 0 {
		cv2 := make([]byte, blowfish.BlockSize)
		bf.Encrypt(cv2, cv)
		tail := make([]byte, rem)
		for i := 0; i < rem; i++ {
			tail[i] = data[len(data)-rem+i] ^ cv2[i]
		}
		plain = append(plain, tail...)
	}
	return strings.TrimRight(string(plain), "\x00"), nil
}

// pkcs7Unpad strips PKCS#7 padding, mirroring the windterm importer.
func pkcs7Unpad(data []byte, blockSize int) ([]byte, error) {
	if len(data) == 0 || len(data)%blockSize != 0 {
		return nil, errors.New("invalid padded data length")
	}
	n := data[len(data)-1]
	if n == 0 || int(n) > blockSize || int(n) > len(data) {
		return nil, errors.New("invalid padding")
	}
	for _, b := range data[len(data)-int(n):] {
		if b != n {
			return nil, errors.New("invalid padding bytes")
		}
	}
	return data[:len(data)-int(n)], nil
}
