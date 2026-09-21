//go:build windows

package session

import (
	"os"

	terminalkrb5 "easyaiot/terminal/backend/krb5"
	"golang.org/x/crypto/ssh"
)

func kerberosGSSAPIClient() (ssh.GSSAPIClient, error) {
	// The Windows default is the current logon session's LSA cache. Explicit
	// FILE:/path values remain supported for MIT Kerberos installations.
	if usesWindowsLSACache(os.Getenv("KRB5CCNAME")) {
		return terminalkrb5.NewSSPIInitiatorClient()
	}
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
