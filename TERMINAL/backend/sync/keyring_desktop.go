//go:build !android

package sync

import "github.com/zalando/go-keyring"

func keychainGet(service, key string) (string, error) {
	return keyring.Get(service, key)
}

func keychainSet(service, key, value string) error {
	return keyring.Set(service, key, value)
}

func keychainDelete(service, key string) error {
	return keyring.Delete(service, key)
}
