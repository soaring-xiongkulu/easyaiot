package session

import (
	"fmt"
	"net"
	"os"
	"os/exec"
	"os/user"
	"path/filepath"
	"runtime"
	"strings"

	"golang.org/x/crypto/ssh"
)

func kerberosConfigPath() (string, error) {
	if path := os.Getenv("KRB5_CONFIG"); path != "" {
		if fileExists(path) {
			return path, nil
		}
		return "", fmt.Errorf("KRB5_CONFIG file does not exist: %s", path)
	}
	paths := []string{"/etc/krb5.conf", "/etc/krb5/krb5.conf"}
	if runtime.GOOS == "windows" {
		paths = []string{`C:\ProgramData\MIT\Kerberos5\krb5.ini`}
	}
	for _, path := range paths {
		if fileExists(path) {
			return path, nil
		}
	}
	return "", fmt.Errorf("Kerberos configuration not found; set KRB5_CONFIG")
}

func kerberosCachePath() (string, func(), error) {
	if value := os.Getenv("KRB5CCNAME"); value != "" {
		path := value
		switch {
		case strings.HasPrefix(path, "FILE:"):
			path = strings.TrimPrefix(path, "FILE:")
		case strings.HasPrefix(path, "DIR:"):
			path = filepath.Join(strings.TrimPrefix(path, "DIR:"), "tkt")
		case strings.Contains(path, ":"):
			if runtime.GOOS == "darwin" && strings.HasPrefix(path, "API:") {
				return exportDarwinCredentialCache()
			}
			return "", nil, fmt.Errorf("unsupported KRB5CCNAME cache type: %s", strings.SplitN(path, ":", 2)[0])
		}
		if fileExists(path) {
			return path, func() {}, nil
		}
		return "", nil, fmt.Errorf("KRB5CCNAME cache does not exist: %s", path)
	}
	if runtime.GOOS == "darwin" {
		return exportDarwinCredentialCache()
	}

	current, err := user.Current()
	if err != nil {
		return "", nil, fmt.Errorf("resolve current user for Kerberos cache: %w", err)
	}
	var path string
	if runtime.GOOS == "windows" {
		name := current.Username
		if idx := strings.LastIndexByte(name, '\\'); idx >= 0 {
			name = name[idx+1:]
		}
		home, err := os.UserHomeDir()
		if err != nil {
			return "", nil, fmt.Errorf("resolve home directory for Kerberos cache: %w", err)
		}
		path = filepath.Join(home, "krb5cc_"+name)
	} else {
		path = "/tmp/krb5cc_" + current.Uid
	}
	if !fileExists(path) {
		return "", nil, fmt.Errorf("Kerberos credential cache not found; run kinit or set KRB5CCNAME")
	}
	return path, func() {}, nil
}

// exportDarwinCredentialCache converts macOS's default API credential cache
// into the FILE format understood by gokrb5. kcc reads the current default
// cache, so no principal or secret is passed on the command line.
func exportDarwinCredentialCache() (string, func(), error) {
	file, err := os.CreateTemp("", "terminal-krb5cc-*")
	if err != nil {
		return "", nil, fmt.Errorf("create temporary Kerberos cache: %w", err)
	}
	path := file.Name()
	if err := file.Close(); err != nil {
		os.Remove(path)
		return "", nil, fmt.Errorf("close temporary Kerberos cache: %w", err)
	}
	// kcc expects to create the destination itself.
	if err := os.Remove(path); err != nil {
		return "", nil, fmt.Errorf("prepare temporary Kerberos cache: %w", err)
	}
	output, err := exec.Command("/usr/bin/kcc", "copy_cred_cache", path).CombinedOutput()
	if err != nil {
		os.Remove(path)
		detail := strings.TrimSpace(string(output))
		if detail != "" {
			return "", nil, fmt.Errorf("Kerberos credential cache unavailable; run kinit (%s)", detail)
		}
		return "", nil, fmt.Errorf("Kerberos credential cache unavailable; run kinit: %w", err)
	}
	if err := os.Chmod(path, 0600); err != nil {
		os.Remove(path)
		return "", nil, fmt.Errorf("secure temporary Kerberos cache: %w", err)
	}
	return path, func() { _ = os.Remove(path) }, nil
}

func fileExists(path string) bool {
	info, err := os.Stat(path)
	return err == nil && !info.IsDir()
}

func kerberosTarget(host, realm string) string {
	realm = strings.TrimSpace(realm)
	ipHost := strings.Trim(host, "[]")
	if net.ParseIP(ipHost) != nil {
		if realm != "" {
			return ipHost + "@" + realm
		}
		return ipHost
	}
	// Keep the user-supplied DNS name. Reverse DNS is not trusted by default,
	// matching OpenSSH's GSSAPITrustDNS=no behavior.
	return host
}

func usesWindowsLSACache(value string) bool {
	value = strings.TrimSpace(value)
	return value == "" || strings.EqualFold(value, "MSLSA:") || strings.EqualFold(value, "MSLSA")
}

func kerberosAuthMethod(host, realm string) (ssh.AuthMethod, error) {
	client, err := kerberosGSSAPIClient()
	if err != nil {
		return nil, err
	}
	return ssh.GSSAPIWithMICAuthMethod(client, kerberosTarget(host, realm)), nil
}

func kerberosAuthMethodWithCleanup(host, realm string) (ssh.AuthMethod, func(), error) {
	client, err := kerberosGSSAPIClient()
	if err != nil {
		return nil, nil, err
	}
	return ssh.GSSAPIWithMICAuthMethod(client, kerberosTarget(host, realm)), func() {
		_ = client.DeleteSecContext()
	}, nil
}
