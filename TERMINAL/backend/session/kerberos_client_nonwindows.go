//go:build !windows

package session

import (
	terminalkrb5 "easyaiot/terminal/backend/krb5"
	"golang.org/x/crypto/ssh"
)

func kerberosGSSAPIClient() (ssh.GSSAPIClient, error) {
	configPath, err := kerberosConfigPath()
	if err != nil {
		return nil, err
	}
	cachePath, cleanup, err := kerberosCachePath()
	if err != nil {
		return nil, err
	}
	defer cleanup()
	return terminalkrb5.NewInitiatorClientWithCache(configPath, cachePath)
}
