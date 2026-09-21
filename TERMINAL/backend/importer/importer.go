package importer

import (
	"fmt"
	"os"
	"path/filepath"
)

// Parse reads the source file and dispatches to the matching provider. Providers
// return groups/connections with freshly generated ids and restored group paths.
// OpenSSH uses the default ~/.ssh/config when no path is given; DBeaver
// auto-detects its default workspace when no path is given.
func Parse(format, srcPath string, opts ParseOptions) (*ImportResult, error) {
	if format == FormatOpenSSH && srcPath == "" {
		srcPath = defaultSSHConfigPath()
	}
	if format == FormatDBeaver && srcPath == "" {
		// parseDBeaver resolves the platform-default workspace itself; pass a
		// sentinel so the generic ReadFile below is skipped.
		return parseDBeaver("", opts)
	}
	data, err := os.ReadFile(srcPath)
	if err != nil {
		return nil, err
	}
	switch format {
	case FormatUniterm:
		return parseUniterm(data, opts)
	case FormatXshell:
		return parseXshell(data)
	case FormatMobaXterm:
		return parseMobaXterm(data)
	case FormatWindTerm:
		return parseWindTerm(data, srcPath, opts)
	case FormatSecureCRT:
		return parseSecureCRT(data)
	case FormatOpenSSH:
		return parseOpenSSH(data)
	case FormatDBeaver:
		return parseDBeaver(srcPath, opts)
	case FormatNavicat:
		return parseNavicat(srcPath, ParseOptions{})
	default:
		return nil, fmt.Errorf("unknown import format %q", format)
	}
}

// defaultSSHConfigPath returns the platform default OpenSSH config location.
func defaultSSHConfigPath() string {
	home, err := os.UserHomeDir()
	if err != nil || home == "" {
		return ".ssh/config"
	}
	return filepath.Join(home, ".ssh", "config")
}
