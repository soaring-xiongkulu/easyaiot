package update

// UpdateAsset is one downloadable release artifact. Candidates are returned
// ordered by preference (primary update source first, then the fallback
// mirror), so downloaders can simply try them in order.
type UpdateAsset struct {
	Name   string `json:"name"`   // filename, e.g. terminal-linux-amd64-v1.9.2.tar.gz
	URL    string `json:"url"`    // direct download URL
	SHA256 string `json:"sha256"` // expected sha256 hex from checksums.txt; "" when unknown
	Source string `json:"source"` // "github" | "gitee"
}

// UpdateInfo is the result returned to the frontend.
type UpdateInfo struct {
	HasUpdate  bool          `json:"hasUpdate"`
	Current    string        `json:"current"`
	Latest     string        `json:"latest"`
	ReleaseURL string        `json:"releaseUrl"`
	Changelog  string        `json:"changelog"`
	Assets     []UpdateAsset `json:"assets"`
}

// Progress is a single update-progress event emitted to the frontend.
type Progress struct {
	Phase    string  `json:"phase"` // "downloading" | "verifying" | "applying" | "error"
	Received int64   `json:"received"`
	Total    int64   `json:"total"` // -1 when unknown
	Percent  float64 `json:"percent"`
	Message  string  `json:"message,omitempty"`
}
