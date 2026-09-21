//go:build android

package sync

import (
	"encoding/hex"
	"fmt"

	"github.com/wailsapp/wails/v3/pkg/application"
	"github.com/zalando/go-keyring"
)

// keychainGet reads from the wails Android bridge secure storage
// (EncryptedSharedPreferences, AES256-GCM). Values are stored hex-encoded:
// the bridge passes strings via NewStringUTF (modified UTF-8), which can
// mangle non-BMP characters (emoji, some CJK extensions) — encoding guards
// against that. A missing key maps to keyring.ErrNotFound so desktop and
// mobile callers observe identical not-found semantics (e.g. GetPassword
// returning "").
func keychainGet(service, key string) (string, error) {
	raw, found, err := application.Android.SecureGet(key)
	if err != nil {
		return "", err
	}
	if !found {
		return "", keyring.ErrNotFound
	}
	v, err := hex.DecodeString(raw)
	if err != nil {
		return "", fmt.Errorf("secure storage: corrupt value: %w", err)
	}
	return string(v), nil
}

func keychainSet(service, key, value string) error {
	// service is ignored: the wails bridge stores everything in one
	// encrypted prefs file; our keys are already namespaced
	// ("conn/<id>", "ai-model/<id>", ...). Values are hex-encoded before
	// crossing the JNI bridge — see keychainGet.
	return application.Android.SecureSet(key, hex.EncodeToString([]byte(value)))
}

func keychainDelete(service, key string) error {
	// Deleting a missing key is a no-op success on Android (desktop
	// go-keyring returns ErrNotFound); all callers tolerate either.
	return application.Android.SecureDelete(key)
}
