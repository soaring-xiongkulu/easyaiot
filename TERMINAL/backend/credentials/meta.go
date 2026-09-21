package credentials

import (
	"encoding/base64"
	"encoding/json"
	"os"
	"path/filepath"
)

const metaFileName = "credentials.meta"

const (
	ModeKeychain       = "keychain"
	ModeMasterPassword = "master-password"
)

// Meta is the on-disk shape of credentials.meta: plaintext JSON holding the
// encryption mode and (master-password mode only) the PBKDF2 salt.
type Meta struct {
	Mode string
	Salt []byte
}

type metaJSON struct {
	Mode string `json:"mode"`
	Salt string `json:"salt,omitempty"`
}

// MetaPath returns the path of credentials.meta inside dataDir.
func MetaPath(dataDir string) string { return filepath.Join(dataDir, metaFileName) }

// ReadMeta reads credentials.meta. Returns (nil, nil) when the file does not exist.
func ReadMeta(dataDir string) (*Meta, error) {
	data, err := os.ReadFile(MetaPath(dataDir))
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	var mj metaJSON
	if err := json.Unmarshal(data, &mj); err != nil {
		return nil, err
	}
	m := &Meta{Mode: mj.Mode}
	if mj.Salt != "" {
		salt, err := base64.StdEncoding.DecodeString(mj.Salt)
		if err != nil {
			return nil, err
		}
		m.Salt = salt
	}
	return m, nil
}

// WriteMeta writes credentials.meta (base64-encodes the salt).
func WriteMeta(dataDir string, m *Meta) error {
	mj := metaJSON{Mode: m.Mode}
	if len(m.Salt) > 0 {
		mj.Salt = base64.StdEncoding.EncodeToString(m.Salt)
	}
	data, err := json.Marshal(mj)
	if err != nil {
		return err
	}
	return os.WriteFile(MetaPath(dataDir), data, 0600)
}
