package update

import (
	"archive/tar"
	"archive/zip"
	"compress/gzip"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"easyaiot/terminal/backend/log"
)

// downloadHTTPClient tolerates large assets: no overall timeout, but bounded
// connect/TLS phases. Callers own their cancellation semantics.
var (
	downloadClientOnce sync.Once
	downloadClient     *http.Client
)

func downloadHTTPClient() *http.Client {
	downloadClientOnce.Do(func() {
		transport := http.DefaultTransport.(*http.Transport).Clone()
		transport.TLSHandshakeTimeout = 20 * time.Second
		downloadClient = &http.Client{
			Transport: transport,
			Timeout:   0, // stream large assets without an overall deadline
		}
	})
	return downloadClient
}

// updateCacheDir returns (and creates) the per-user staging directory for
// update downloads.
func updateCacheDir() (string, error) {
	dir, err := os.UserCacheDir()
	if err != nil {
		return "", err
	}
	dir = filepath.Join(dir, "Terminal", "updates")
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", err
	}
	return dir, nil
}

// parseChecksums parses a GNU `sha256sum`-style checksums.txt into
// filename → lowercase hex digest.
func parseChecksums(data []byte) map[string]string {
	sums := map[string]string{}
	for _, line := range strings.Split(string(data), "\n") {
		fields := strings.Fields(line)
		if len(fields) < 2 {
			continue
		}
		hash := strings.ToLower(fields[0])
		name := strings.TrimPrefix(fields[len(fields)-1], "*")
		if len(hash) != 64 {
			continue
		}
		if _, err := hex.DecodeString(hash); err != nil {
			continue
		}
		sums[name] = hash
	}
	return sums
}

// Download tries each candidate in order until one downloads and verifies.
// Progress is reported through onProgress (may be nil).
func (m *Manager) Download(candidates []UpdateAsset, onProgress func(Progress)) (*PendingUpdate, error) {
	m.Clear()
	var lastErr error
	for i, cand := range candidates {
		log.Writef("[update] trying candidate %d/%d: %s (%s)", i+1, len(candidates), cand.Name, cand.Source)
		pend, err := m.downloadOne(cand, onProgress)
		if err == nil {
			return pend, nil
		}
		lastErr = err
		log.Writef("[update] candidate failed: %v", err)
	}
	if lastErr == nil {
		lastErr = errors.New("no download candidates")
	}
	return nil, lastErr
}

func (m *Manager) downloadOne(cand UpdateAsset, onProgress func(Progress)) (*PendingUpdate, error) {
	root, err := updateCacheDir()
	if err != nil {
		return nil, err
	}
	stage, err := os.MkdirTemp(root, "stage-*")
	if err != nil {
		return nil, err
	}
	cleanup := func() { _ = os.RemoveAll(stage) }

	filePath := filepath.Join(stage, filepath.Base(cand.Name))
	if err := downloadToFile(cand.URL, filePath, cand.Name, onProgress); err != nil {
		cleanup()
		return nil, fmt.Errorf("download %s: %w", cand.Name, err)
	}

	if cand.SHA256 != "" {
		if onProgress != nil {
			onProgress(Progress{Phase: "verifying", Total: -1, Message: cand.Name})
		}
		got, err := sha256File(filePath)
		if err != nil {
			cleanup()
			return nil, fmt.Errorf("hash %s: %w", cand.Name, err)
		}
		if !strings.EqualFold(got, cand.SHA256) {
			log.Writef("[update] sha256 mismatch for %s: got %s want %s", cand.Name, got, cand.SHA256)
			cleanup()
			return nil, fmt.Errorf("sha256 mismatch for %s", cand.Name)
		}
		log.Writef("[update] sha256 verified for %s", cand.Name)
	}

	pend := &PendingUpdate{
		Asset:    cand,
		Kind:     classifyAsset(cand.Name),
		StageDir: stage,
		FilePath: filePath,
	}

	// Extract payloads now so Apply() only performs the replacement.
	switch pend.Kind {
	case "portable":
		pend.NewBinary, err = extractPortableZip(stage, filePath)
	case "binary-tar.gz":
		pend.NewBinary, err = extractTarGzBinary(stage, filePath)
	case "installer":
		// nothing to extract; the downloaded installer is the payload
	}
	if err != nil {
		cleanup()
		return nil, fmt.Errorf("extract %s: %w", cand.Name, err)
	}

	m.setPending(pend)
	return pend, nil
}

// downloadToFile streams url into dest, emitting progress when onProgress is
// set. Non-200 responses are errors (the fallback loop then tries the mirror).
// An overall 30-minute deadline bounds stalled connections.
func downloadToFile(url, dest, label string, onProgress func(Progress)) error {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return err
	}
	req.Header.Set("User-Agent", "Terminal")

	resp, err := downloadHTTPClient().Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("unexpected status: %d", resp.StatusCode)
	}

	out, err := os.Create(dest)
	if err != nil {
		return err
	}
	defer out.Close()

	var received int64
	total := resp.ContentLength
	if total <= 0 {
		total = -1
	}
	buf := make([]byte, 64*1024)
	for {
		n, rerr := resp.Body.Read(buf)
		if n > 0 {
			if _, werr := out.Write(buf[:n]); werr != nil {
				return werr
			}
			received += int64(n)
			if onProgress != nil {
				p := Progress{Phase: "downloading", Received: received, Total: total, Message: label}
				if total > 0 {
					p.Percent = float64(received) / float64(total) * 100
				}
				onProgress(p)
			}
		}
		if rerr == io.EOF {
			break
		}
		if rerr != nil {
			return rerr
		}
	}
	return nil
}

func sha256File(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()
	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", err
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

// extractTarGzBinary extracts the first regular file from a .tar.gz payload
// (CI packages the bare executable at the archive root) and returns its path.
func extractTarGzBinary(stage, tarPath string) (string, error) {
	f, err := os.Open(tarPath)
	if err != nil {
		return "", err
	}
	defer f.Close()
	gz, err := gzip.NewReader(f)
	if err != nil {
		return "", err
	}
	defer gz.Close()
	tr := tar.NewReader(gz)

	var binaryPath string
	for {
		hdr, err := tr.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return "", err
		}
		if hdr.Typeflag != tar.TypeReg {
			continue
		}
		name := filepath.Base(hdr.Name)
		if strings.EqualFold(name, "terminal") || strings.EqualFold(name, "terminal.exe") {
			binaryPath = filepath.Join(stage, name)
			out, err := os.OpenFile(binaryPath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0755)
			if err != nil {
				return "", err
			}
			if _, err := io.Copy(out, tr); err != nil {
				out.Close()
				return "", err
			}
			out.Close()
			break
		}
	}
	if binaryPath == "" {
		return "", fmt.Errorf("no executable found in %s", tarPath)
	}
	return binaryPath, nil
}

// extractPortableZip extracts the Windows portable zip: Terminal.exe plus the
// plugins/ directory (VcXsrv). Returns the extracted exe path.
func extractPortableZip(stage, zipPath string) (string, error) {
	zr, err := zip.OpenReader(zipPath)
	if err != nil {
		return "", err
	}
	defer zr.Close()

	var binaryPath string
	for _, f := range zr.File {
		if f.FileInfo().IsDir() {
			continue
		}
		base := filepath.Base(f.Name)
		dest := filepath.Join(stage, f.Name)
		// archive/zip names use forward slashes; guard against traversal.
		if strings.Contains(f.Name, "..") {
			continue
		}
		// "terminal.exe" is the Windows payload; a bare "terminal" covers the
		// macOS zip and the executable inside a fallback .app-bundle zip.
		if strings.EqualFold(base, "terminal.exe") || strings.EqualFold(base, "terminal") {
			binaryPath = dest
		}
		if err := os.MkdirAll(filepath.Dir(dest), 0755); err != nil {
			return "", err
		}
		rc, err := f.Open()
		if err != nil {
			return "", err
		}
		out, err := os.OpenFile(dest, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0755)
		if err != nil {
			rc.Close()
			return "", err
		}
		_, err = io.Copy(out, rc)
		rc.Close()
		out.Close()
		if err != nil {
			return "", err
		}
	}
	if binaryPath == "" {
		return "", fmt.Errorf("terminal executable not found in %s", zipPath)
	}
	return binaryPath, nil
}
