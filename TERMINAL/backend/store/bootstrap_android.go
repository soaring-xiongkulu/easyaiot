//go:build android

package store

import "github.com/wailsapp/wails/v3/pkg/application"

// androidFilesDir is a var so device tests can stub the bridge call. The real
// implementation asks the wails Android bridge for the app's private internal
// files directory (WailsBridge.getStoragePath → Context.getFilesDir()).
var androidFilesDir = application.Android.StoragePath

// DefaultDataDir returns <app files dir>/Terminal. There is no
// $HOME/$XDG_CONFIG_HOME inside the Android app sandbox.
func DefaultDataDir() (string, error) {
	dd, err := resolveAndroidDataDir(androidFilesDir())
	if err != nil {
		return "", err
	}
	return dd.Path, nil
}

// ResolveDataDir on Android always uses the default app dir: no bootstrap.json
// indirection (portable/custom data-dir modes are meaningless in a sandbox),
// no first-run/upgrade probing. The dir is created eagerly by
// resolveAndroidDataDir so store constructors can rely on it.
func ResolveDataDir() (DataDir, error) {
	return resolveAndroidDataDir(androidFilesDir())
}

// WriteBootstrap is a no-op on Android (no bootstrap pointer file exists).
func WriteBootstrap(kind, customDir string) error { return nil }
