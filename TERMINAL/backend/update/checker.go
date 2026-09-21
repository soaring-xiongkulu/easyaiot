package update

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"

	"easyaiot/terminal/backend/log"
)

// release mirrors the GitHub/Gitee release payload subset. Both APIs expose
// the same shape: tag_name, body and an assets list of
// {name, browser_download_url}.
type release struct {
	TagName string         `json:"tag_name"`
	Body    string         `json:"body"`
	Assets  []releaseAsset `json:"assets"`
}

type releaseAsset struct {
	Name               string `json:"name"`
	BrowserDownloadURL string `json:"browser_download_url"`
}

type cacheEntry struct {
	Release   release   `json:"release"`
	Source    string    `json:"source"`
	Timestamp time.Time `json:"timestamp"`
	// ETag captured from the API response so a follow-up call inside the
	// disk-cache TTL window can send If-None-Match and let the host answer
	// 304 Not Modified, skipping the body decode entirely (F-409).
	ETag string `json:"etag,omitempty"`
}

func normalizeVersion(v string) string {
	return strings.TrimPrefix(strings.TrimSpace(v), "v")
}

// parseSemver splits a version string into its numeric core parts and its
// optional pre-release identifiers, following SemVer 2.0.0. Build metadata
// (anything after '+') is discarded because it does not affect precedence.
func parseSemver(v string) (core []int, pre []string) {
	v = normalizeVersion(v)
	if idx := strings.Index(v, "+"); idx >= 0 {
		v = v[:idx]
	}
	var prePart string
	if idx := strings.Index(v, "-"); idx >= 0 {
		prePart = v[idx+1:]
		v = v[:idx]
	}
	for _, p := range strings.Split(v, ".") {
		n, _ := strconv.Atoi(p)
		core = append(core, n)
	}
	if prePart != "" {
		pre = strings.Split(prePart, ".")
	}
	return core, pre
}

// comparePre compares two pre-release identifier slices per SemVer 2.0.0 §11.4.
// Returns -1, 0, or 1. A version WITHOUT a pre-release has higher precedence
// than one WITH a pre-release; callers must handle that case before calling.
func comparePre(a, b []string) int {
	for i := 0; i < len(a) || i < len(b); i++ {
		if i >= len(a) {
			return -1
		}
		if i >= len(b) {
			return 1
		}
		an, aErr := strconv.Atoi(a[i])
		bn, bErr := strconv.Atoi(b[i])
		aNumeric := aErr == nil
		bNumeric := bErr == nil
		switch {
		case aNumeric && bNumeric:
			if an != bn {
				if an < bn {
					return -1
				}
				return 1
			}
		case aNumeric && !bNumeric:
			return -1
		case !aNumeric && bNumeric:
			return 1
		default:
			if a[i] != b[i] {
				if a[i] < b[i] {
					return -1
				}
				return 1
			}
		}
	}
	return 0
}

func versionGreater(latest, current string) bool {
	lc, lp := parseSemver(latest)
	cc, cp := parseSemver(current)
	for i := 0; i < len(lc) || i < len(cc); i++ {
		var ln, cn int
		if i < len(lc) {
			ln = lc[i]
		}
		if i < len(cc) {
			cn = cc[i]
		}
		if ln > cn {
			return true
		}
		if ln < cn {
			return false
		}
	}
	// Core versions equal: a version without a pre-release outranks one with.
	if len(lp) == 0 && len(cp) == 0 {
		return false
	}
	if len(lp) == 0 {
		return true
	}
	if len(cp) == 0 {
		return false
	}
	return comparePre(lp, cp) > 0
}

func shouldUpdate(current, latest string) bool {
	if current == "dev" {
		return true
	}
	return versionGreater(latest, current)
}

const cacheTTL = 5 * time.Minute

// sharedClient is a package-level *http.Client with keep-alive enabled.
// Reusing it avoids the per-call TCP+TLS handshake to api.github.com /
// gitee.com on every Check() (F-409).
var (
	sharedClientOnce sync.Once
	sharedClient     *http.Client
)

func sharedHTTPClient() *http.Client {
	sharedClientOnce.Do(func() {
		sharedClient = &http.Client{Timeout: 10 * time.Second}
	})
	return sharedClient
}

func cachePath(source string) string {
	dir, err := os.UserConfigDir()
	if err != nil {
		return ""
	}
	return filepath.Join(dir, "Terminal", "update_cache_"+source+".json")
}

func loadCache(source string) *cacheEntry {
	path := cachePath(source)
	if path == "" {
		return nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	var entry cacheEntry
	if err := json.Unmarshal(data, &entry); err != nil {
		return nil
	}
	if time.Since(entry.Timestamp) > cacheTTL {
		return nil
	}
	return &entry
}

func saveCache(source string, entry *cacheEntry) {
	path := cachePath(source)
	if path == "" {
		return
	}
	os.MkdirAll(filepath.Dir(path), 0755)
	data, _ := json.Marshal(entry)
	_ = os.WriteFile(path, data, 0600)
}

// sourceAPIURL returns the latest-release API endpoint for a source.
// TERMINAL_UPDATE_API_BASE overrides the API base for both sources — used by
// the local end-to-end autotest (autotest_update.go) and by self-hosted
// mirror setups; production builds leave it unset. The base must serve a
// GitHub-style GET <base>/releases/latest payload.
func sourceAPIURL(source string) string {
	if base := os.Getenv("TERMINAL_UPDATE_API_BASE"); base != "" {
		return strings.TrimRight(base, "/") + "/releases/latest"
	}
	if source == "gitee" {
		return "https://gitee.com/api/v5/repos/ys-l/uniterm/releases/latest"
	}
	return "https://api.github.com/repos/ys-ll/uniterm/releases/latest"
}

// sourceReleaseURL returns the human-facing release page for a source.
func sourceReleaseURL(source string) string {
	if source == "gitee" {
		return "https://gitee.com/ys-l/uniterm/releases/latest"
	}
	return "https://github.com/ys-ll/uniterm/releases/latest"
}

// fetchRelease fetches the latest release from a source, honouring the
// per-source disk cache + ETag/304 protocol.
func fetchRelease(source string) (*release, error) {
	apiURL := sourceAPIURL(source)

	if cached := loadCache(source); cached != nil {
		log.Writef("[update] returning disk-cached release, source=%s, age=%s", source, time.Since(cached.Timestamp))
		return &cached.Release, nil
	}

	log.Writef("[update] fetching latest release, source=%s", source)

	req, err := http.NewRequest("GET", apiURL, nil)
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("User-Agent", "Terminal")
	if prev := loadCache(source); prev != nil && prev.ETag != "" {
		req.Header.Set("If-None-Match", prev.ETag)
	}

	resp, err := sharedHTTPClient().Do(req)
	if err != nil {
		log.Writef("[update] api request error: %v", err)
		return nil, fmt.Errorf("api request: %w", err)
	}
	defer resp.Body.Close()

	// 304: nothing changed since our cached ETag. Refresh the timestamp so
	// the disk TTL window slides forward and reuse the cached payload.
	if resp.StatusCode == http.StatusNotModified {
		if prev := loadCache(source); prev != nil {
			prev.Timestamp = time.Now()
			saveCache(source, prev)
			return &prev.Release, nil
		}
		return nil, fmt.Errorf("unexpected status: 304 (no prior cache)")
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status: %d", resp.StatusCode)
	}

	var rel release
	if err := json.NewDecoder(resp.Body).Decode(&rel); err != nil {
		log.Writef("[update] decode error: %v", err)
		return nil, fmt.Errorf("decode response: %w", err)
	}

	log.Writef("[update] latest=%s, assets=%d (source=%s)", rel.TagName, len(rel.Assets), source)

	saveCache(source, &cacheEntry{
		Release:   rel,
		Source:    source,
		Timestamp: time.Now(),
		ETag:      resp.Header.Get("ETag"),
	})

	return &rel, nil
}

func otherSource(source string) string {
	if source == "gitee" {
		return "github"
	}
	return "gitee"
}

// fetchChecksums downloads checksums.txt from the given release (if present)
// and parses it into name → sha256. Returns an empty map when unavailable.
func fetchChecksums(rel *release) map[string]string {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	for _, a := range rel.Assets {
		if a.Name != "checksums.txt" {
			continue
		}
		req, err := http.NewRequestWithContext(ctx, "GET", a.BrowserDownloadURL, nil)
		if err != nil {
			continue
		}
		req.Header.Set("User-Agent", "Terminal")
		resp, err := downloadHTTPClient().Do(req)
		if err != nil || resp.StatusCode != http.StatusOK {
			if resp != nil {
				resp.Body.Close()
			}
			log.Writef("[update] checksums fetch failed: %v", err)
			continue
		}
		data, err := io.ReadAll(resp.Body)
		resp.Body.Close()
		if err != nil {
			continue
		}
		sums := parseChecksums(data)
		log.Writef("[update] parsed %d checksums", len(sums))
		return sums
	}
	return map[string]string{}
}

// classifyAsset buckets an asset name by its update payload kind. Any .zip is
// treated as portable (Windows portable zip and the macOS bare-binary zip);
// .dmg/.deb/.rpm are manual-install artifacts and land in "other".
func classifyAsset(name string) string {
	switch {
	case strings.Contains(name, "-installer-") && strings.HasSuffix(name, ".exe"):
		return "installer"
	case strings.HasSuffix(name, ".zip"):
		return "portable"
	case strings.HasSuffix(name, ".tar.gz"):
		return "binary-tar.gz"
	}
	return "other"
}

// assetMatchesPlatform reports whether the asset targets the given OS/arch.
// Asset names are anchored to the terminal-<os>-<arch>- prefix.
func assetMatchesPlatform(osName, arch, name string) bool {
	switch osName {
	case "windows", "linux", "darwin":
	default:
		return false
	}
	return strings.HasPrefix(name, "terminal-"+osName+"-"+arch+"-")
}

// kindPreference returns the asset kinds usable for a channel, best first.
func kindPreference(ch Channel) []string {
	switch ch {
	case ChannelInstaller:
		return []string{"installer", "portable"}
	case ChannelPortable:
		return []string{"portable", "binary-tar.gz"}
	default:
		return nil
	}
}

// candidatesFor orders the updateable assets for a platform and channel:
// preferred kind first, and within each kind the primary source's asset
// before the fallback mirror's.
func candidatesFor(osName, arch string, ch Channel, primary string, rels map[string]*release, sums map[string]string) []UpdateAsset {
	var out []UpdateAsset
	for _, kind := range kindPreference(ch) {
		for _, src := range []string{primary, otherSource(primary)} {
			rel, ok := rels[src]
			if !ok {
				continue
			}
			for _, a := range rel.Assets {
				if classifyAsset(a.Name) != kind || !assetMatchesPlatform(osName, arch, a.Name) {
					continue
				}
				out = append(out, UpdateAsset{
					Name:   a.Name,
					URL:    a.BrowserDownloadURL,
					SHA256: sums[a.Name],
					Source: src,
				})
			}
		}
	}
	return out
}

// Check compares the current version against the latest release from the given
// source. When an update is available it also collects downloadable assets for
// the current platform from BOTH sources (primary first, fallback mirror
// second) so the downloader can fail over automatically.
func Check(currentVersion, source string) (*UpdateInfo, error) {
	if source == "" {
		source = "github"
	}

	log.Writef("[update] Check called, current=%s, source=%s", currentVersion, source)

	primary, err := fetchRelease(source)
	if err != nil {
		// The preferred source is unreachable — fail the whole check over to
		// the mirror instead of erroring out.
		if rel2, err2 := fetchRelease(otherSource(source)); err2 == nil {
			log.Writef("[update] %s failed (%v); using %s", source, err, otherSource(source))
			source = otherSource(source)
			primary = rel2
		} else {
			return nil, err
		}
	}

	result := UpdateInfo{
		Current:    currentVersion,
		Latest:     primary.TagName,
		ReleaseURL: sourceReleaseURL(source),
		Changelog:  primary.Body,
		HasUpdate:  shouldUpdate(currentVersion, primary.TagName),
	}

	if !result.HasUpdate {
		return &result, nil
	}

	// Collect assets from both sources: primary first, then the mirror. The
	// mirror fetch is capped at 3s so a blocked source (e.g. GitHub behind
	// the GFW when Gitee is primary) never stalls the check response; the
	// goroutine still finishes in the background and warms the disk cache.
	other := otherSource(source)
	rels := map[string]*release{source: primary}
	mirrorCh := make(chan *release, 1)
	go func() {
		rel2, err := fetchRelease(other)
		if err == nil {
			mirrorCh <- rel2
		} else {
			mirrorCh <- nil
		}
	}()
	select {
	case rel2 := <-mirrorCh:
		if rel2 != nil {
			rels[other] = rel2
		}
	case <-time.After(3 * time.Second):
		log.Writef("[update] %s release fetch still in flight; continuing without it", other)
	}

	// Checksums: prefer the primary source's checksums.txt, fall back to the
	// mirror's. Either may be absent on older releases.
	sums := fetchChecksums(primary)
	if len(sums) == 0 {
		if rel2, ok := rels[otherSource(source)]; ok {
			sums = fetchChecksums(rel2)
		}
	}

	result.Assets = candidatesFor(runtime.GOOS, runtime.GOARCH, DetectChannel(), source, rels, sums)
	log.Writef("[update] %d candidate asset(s) for channel %s", len(result.Assets), DetectChannel())

	return &result, nil
}
