package importer

import (
	"crypto/rand"
	"encoding/base64"
	"strconv"
	"time"
)

// newConnectionID / newGroupID generate unique ids matching the frontend's
// `conn-<ts>-<rand>` / `grp-<ts>-<rand>` convention. Exact charset need not
// match the frontend; uniqueness (crypto/rand) is what matters.
func newConnectionID() string { return newID("conn") }
func newGroupID() string     { return newID("grp") }

func newID(prefix string) string {
	b := make([]byte, 6)
	_, _ = rand.Read(b)
	return prefix + "-" + strconv.FormatInt(time.Now().UnixMilli(), 10) +
		"-" + base64.RawURLEncoding.EncodeToString(b)
}
