package session

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"easyaiot/terminal/backend/log"
)

// EsIndexInfo holds cat/indices row fields used by the UI.
type EsIndexInfo struct {
	Name      string `json:"name"`
	Health    string `json:"health"`
	Status    string `json:"status"`
	DocsCount int64  `json:"docsCount"`
	StoreSize string `json:"storeSize"`
	Pri       int    `json:"pri"`
	Rep       int    `json:"rep"`
}

// EsClusterHealth is a trimmed _cluster/health payload.
type EsClusterHealth struct {
	ClusterName         string `json:"clusterName"`
	Status              string `json:"status"`
	NumberOfNodes       int    `json:"numberOfNodes"`
	NumberOfDataNodes   int    `json:"numberOfDataNodes"`
	ActivePrimaryShards int    `json:"activePrimaryShards"`
	ActiveShards        int    `json:"activeShards"`
	RelocatingShards    int    `json:"relocatingShards"`
	InitializingShards  int    `json:"initializingShards"`
	UnassignedShards    int    `json:"unassignedShards"`
}

// EsClusterInfo is a trimmed GET / response.
type EsClusterInfo struct {
	Name        string `json:"name"`
	ClusterName string `json:"clusterName"`
	ClusterUUID string `json:"clusterUUID"`
	Version     string `json:"version"`
	Tagline     string `json:"tagline"`
}

// EsNodeSummary is a trimmed cat/nodes row.
type EsNodeSummary struct {
	Name        string `json:"name"`
	IP          string `json:"ip"`
	NodeRole    string `json:"nodeRole"`
	HeapPercent string `json:"heapPercent"`
	RamPercent  string `json:"ramPercent"`
	CPU         string `json:"cpu"`
	Load1m      string `json:"load1m"`
	Master      string `json:"master"`
}

// EsSearchResult holds search hits as raw JSON source documents (with _id/_index/_score injected).
type EsSearchResult struct {
	Hits  []string `json:"hits"`
	Total int64    `json:"total"`
	From  int      `json:"from"`
	Size  int      `json:"size"`
	Took  int      `json:"took"`
}

// EsRestResult is the generic REST console response.
type EsRestResult struct {
	Status int    `json:"status"`
	Body   string `json:"body"`
}

// ElasticsearchSession implements Session for Elasticsearch / OpenSearch REST.
type ElasticsearchSession struct {
	baseSession
	httpClient *http.Client
	baseURL    string
	authHeader string
	closed     bool
}

// NewElasticsearchSession creates a disconnected ES session.
func NewElasticsearchSession(id string) *ElasticsearchSession {
	return &ElasticsearchSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "elasticsearch",
			status:      StatusDisconnected,
		},
	}
}

// Connect probes the cluster with GET / and stores the HTTP client.
func (s *ElasticsearchSession) Connect(config ConnectionConfig) error {
	log.Writef("[ElasticsearchSession.Connect] id=%s, host=%s, port=%d, ssl=%v", s.id, config.Host, config.Port, config.EsUseSSL)
	s.setStatus(StatusConnecting)

	if config.Name != "" {
		s.title = config.Name
	} else {
		s.title = fmt.Sprintf("elasticsearch:%s:%d", config.Host, config.Port)
	}

	host := config.Host
	if host == "" {
		host = "127.0.0.1"
	}
	port := config.Port
	if port == 0 {
		port = 9200
	}
	scheme := "http"
	if config.EsUseSSL {
		scheme = "https"
	}
	prefix := strings.TrimSuffix(config.EsPathPrefix, "/")
	if prefix != "" && !strings.HasPrefix(prefix, "/") {
		prefix = "/" + prefix
	}

	transport := &http.Transport{
		Proxy: http.ProxyFromEnvironment,
		DialContext: (&net.Dialer{
			Timeout:   10 * time.Second,
			KeepAlive: 30 * time.Second,
		}).DialContext,
		TLSHandshakeTimeout: 10 * time.Second,
		MaxIdleConns:        20,
		IdleConnTimeout:     90 * time.Second,
	}
	if config.EsUseSSL {
		transport.TLSClientConfig = &tls.Config{
			InsecureSkipVerify: config.EsSkipVerify, //nolint:gosec // intentional user opt-in
		}
	}
	client := &http.Client{
		Timeout:   60 * time.Second,
		Transport: transport,
	}

	s.mu.Lock()
	s.closed = false
	s.httpClient = client
	s.baseURL = fmt.Sprintf("%s://%s:%d%s", scheme, host, port, prefix)
	s.authHeader = buildEsAuthHeader(config)
	s.mu.Unlock()

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	if _, err := s.doRequest(ctx, http.MethodGet, "/", nil); err != nil {
		s.setStatus(StatusError)
		return fmt.Errorf("elasticsearch connect: %w", err)
	}

	log.Writef("[ElasticsearchSession.Connect] connected successfully")
	s.setStatus(StatusConnected)
	return nil
}

func buildEsAuthHeader(config ConnectionConfig) string {
	// Auth type reuses the shared `authType` field: 'password'(basic) | 'apikey'.
	authType := strings.ToLower(strings.TrimSpace(config.AuthType))
	if authType == "apikey" {
		key := strings.TrimSpace(config.Password)
		if key == "" {
			return ""
		}
		// Accept either already-encoded key or id:api_key form.
		if strings.Contains(key, ":") {
			key = base64.StdEncoding.EncodeToString([]byte(key))
		}
		return "ApiKey " + key
	}
	if config.User != "" {
		token := base64.StdEncoding.EncodeToString([]byte(config.User + ":" + config.Password))
		return "Basic " + token
	}
	return ""
}

// Disconnect releases the HTTP client.
func (s *ElasticsearchSession) Disconnect() error {
	s.mu.Lock()
	if s.closed {
		s.mu.Unlock()
		return nil
	}
	s.closed = true
	s.httpClient = nil
	s.mu.Unlock()
	s.setStatus(StatusDisconnected)
	return nil
}

// IsConnected reports whether the session is usable.
func (s *ElasticsearchSession) IsConnected() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.status == StatusConnected && s.httpClient != nil && !s.closed
}

func (s *ElasticsearchSession) Write(data []byte) error  { return nil }
func (s *ElasticsearchSession) Resize(cols, rows int) error { return nil }

func (s *ElasticsearchSession) client() (*http.Client, string, string, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	if s.closed || s.httpClient == nil || s.status != StatusConnected {
		return nil, "", "", fmt.Errorf("not connected")
	}
	return s.httpClient, s.baseURL, s.authHeader, nil
}

func (s *ElasticsearchSession) doRequest(ctx context.Context, method, path string, body []byte) ([]byte, error) {
	client, base, auth, err := s.client()
	if err != nil {
		// Allow connect-time probe before StatusConnected.
		s.mu.RLock()
		client = s.httpClient
		base = s.baseURL
		auth = s.authHeader
		closed := s.closed
		s.mu.RUnlock()
		if closed || client == nil || base == "" {
			return nil, fmt.Errorf("not connected")
		}
	}

	if !strings.HasPrefix(path, "/") {
		path = "/" + path
	}
	u := base + path
	var reader io.Reader
	if body != nil {
		reader = bytes.NewReader(body)
	}
	req, err := http.NewRequestWithContext(ctx, method, u, reader)
	if err != nil {
		return nil, err
	}
	if auth != "" {
		req.Header.Set("Authorization", auth)
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	req.Header.Set("Accept", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(io.LimitReader(resp.Body, 64<<20)) // 64 MiB cap
	if err != nil {
		return nil, err
	}
	if resp.StatusCode >= 400 {
		msg := strings.TrimSpace(string(data))
		if msg == "" {
			msg = resp.Status
		}
		return data, fmt.Errorf("elasticsearch %s %s: %s", method, path, msg)
	}
	return data, nil
}

// Ping checks cluster reachability.
func (s *ElasticsearchSession) Ping() error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_, err := s.doRequest(ctx, http.MethodGet, "/", nil)
	return err
}

// ClusterInfo returns GET / summary.
func (s *ElasticsearchSession) ClusterInfo() (*EsClusterInfo, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	data, err := s.doRequest(ctx, http.MethodGet, "/", nil)
	if err != nil {
		return nil, err
	}
	var raw map[string]any
	if err := json.Unmarshal(data, &raw); err != nil {
		return nil, err
	}
	info := &EsClusterInfo{
		Name:        asString(raw["name"]),
		ClusterName: asString(raw["cluster_name"]),
		ClusterUUID: asString(raw["cluster_uuid"]),
		Tagline:     asString(raw["tagline"]),
	}
	if v, ok := raw["version"].(map[string]any); ok {
		info.Version = asString(v["number"])
	}
	return info, nil
}

// ClusterHealth returns GET /_cluster/health.
func (s *ElasticsearchSession) ClusterHealth() (*EsClusterHealth, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	data, err := s.doRequest(ctx, http.MethodGet, "/_cluster/health", nil)
	if err != nil {
		return nil, err
	}
	var raw map[string]any
	if err := json.Unmarshal(data, &raw); err != nil {
		return nil, err
	}
	return &EsClusterHealth{
		ClusterName:         asString(raw["cluster_name"]),
		Status:              asString(raw["status"]),
		NumberOfNodes:       asInt(raw["number_of_nodes"]),
		NumberOfDataNodes:   asInt(raw["number_of_data_nodes"]),
		ActivePrimaryShards: asInt(raw["active_primary_shards"]),
		ActiveShards:        asInt(raw["active_shards"]),
		RelocatingShards:    asInt(raw["relocating_shards"]),
		InitializingShards:  asInt(raw["initializing_shards"]),
		UnassignedShards:    asInt(raw["unassigned_shards"]),
	}, nil
}

// NodesStats returns a trimmed cat/nodes listing.
func (s *ElasticsearchSession) NodesStats() ([]EsNodeSummary, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	path := "/_cat/nodes?format=json&h=name,ip,node.role,heap.percent,ram.percent,cpu,load_1m,master"
	data, err := s.doRequest(ctx, http.MethodGet, path, nil)
	if err != nil {
		return nil, err
	}
	var rows []map[string]string
	if err := json.Unmarshal(data, &rows); err != nil {
		return nil, err
	}
	out := make([]EsNodeSummary, 0, len(rows))
	for _, r := range rows {
		out = append(out, EsNodeSummary{
			Name:        r["name"],
			IP:          r["ip"],
			NodeRole:    r["node.role"],
			HeapPercent: r["heap.percent"],
			RamPercent:  r["ram.percent"],
			CPU:         r["cpu"],
			Load1m:      r["load_1m"],
			Master:      r["master"],
		})
	}
	return out, nil
}

// ListIndices returns cat/indices rows (excluding system indices is left to the UI filter).
func (s *ElasticsearchSession) ListIndices() ([]EsIndexInfo, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	path := "/_cat/indices?format=json&h=index,health,status,docs.count,store.size,pri,rep&s=index:asc"
	data, err := s.doRequest(ctx, http.MethodGet, path, nil)
	if err != nil {
		return nil, err
	}
	var rows []map[string]string
	if err := json.Unmarshal(data, &rows); err != nil {
		return nil, err
	}
	out := make([]EsIndexInfo, 0, len(rows))
	for _, r := range rows {
		docs, _ := strconv.ParseInt(r["docs.count"], 10, 64)
		pri, _ := strconv.Atoi(r["pri"])
		rep, _ := strconv.Atoi(r["rep"])
		out = append(out, EsIndexInfo{
			Name:      r["index"],
			Health:    r["health"],
			Status:    r["status"],
			DocsCount: docs,
			StoreSize: r["store.size"],
			Pri:       pri,
			Rep:       rep,
		})
	}
	return out, nil
}

// GetMapping returns mapping JSON for an index.
func (s *ElasticsearchSession) GetMapping(index string) (string, error) {
	if index == "" {
		return "", fmt.Errorf("index required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	data, err := s.doRequest(ctx, http.MethodGet, "/"+url.PathEscape(index)+"/_mapping", nil)
	if err != nil {
		return "", err
	}
	return prettyJSON(data), nil
}

// GetSettings returns settings JSON for an index.
func (s *ElasticsearchSession) GetSettings(index string) (string, error) {
	if index == "" {
		return "", fmt.Errorf("index required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	data, err := s.doRequest(ctx, http.MethodGet, "/"+url.PathEscape(index)+"/_settings", nil)
	if err != nil {
		return "", err
	}
	return prettyJSON(data), nil
}

// Search runs POST /{index}/_search with an optional DSL body.
func (s *ElasticsearchSession) Search(index, bodyJSON string, from, size int) (*EsSearchResult, error) {
	if index == "" {
		return nil, fmt.Errorf("index required")
	}
	if size <= 0 {
		size = 50
	}
	if from < 0 {
		from = 0
	}

	bodyMap := map[string]any{}
	if strings.TrimSpace(bodyJSON) != "" {
		if err := json.Unmarshal([]byte(bodyJSON), &bodyMap); err != nil {
			return nil, fmt.Errorf("invalid search body JSON: %w", err)
		}
	}
	bodyMap["from"] = from
	bodyMap["size"] = size
	payload, err := json.Marshal(bodyMap)
	if err != nil {
		return nil, err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()
	data, err := s.doRequest(ctx, http.MethodPost, "/"+url.PathEscape(index)+"/_search", payload)
	if err != nil {
		return nil, err
	}

	var raw struct {
		Took int `json:"took"`
		Hits struct {
			Total any `json:"total"`
			Hits  []struct {
				Index  string          `json:"_index"`
				ID     string          `json:"_id"`
				Score  *float64        `json:"_score"`
				Source json.RawMessage `json:"_source"`
			} `json:"hits"`
		} `json:"hits"`
	}
	if err := json.Unmarshal(data, &raw); err != nil {
		return nil, err
	}

	total := parseEsTotal(raw.Hits.Total)
	hits := make([]string, 0, len(raw.Hits.Hits))
	for _, h := range raw.Hits.Hits {
		doc := map[string]any{}
		if len(h.Source) > 0 && string(h.Source) != "null" {
			_ = json.Unmarshal(h.Source, &doc)
		}
		doc["_id"] = h.ID
		doc["_index"] = h.Index
		if h.Score != nil {
			doc["_score"] = *h.Score
		}
		b, _ := json.Marshal(doc)
		hits = append(hits, string(b))
	}

	return &EsSearchResult{
		Hits:  hits,
		Total: total,
		From:  from,
		Size:  size,
		Took:  raw.Took,
	}, nil
}

// GetDoc fetches a document by id.
func (s *ElasticsearchSession) GetDoc(index, id string) (string, error) {
	if index == "" || id == "" {
		return "", fmt.Errorf("index and id required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	path := fmt.Sprintf("/%s/_doc/%s", url.PathEscape(index), url.PathEscape(id))
	data, err := s.doRequest(ctx, http.MethodGet, path, nil)
	if err != nil {
		return "", err
	}
	var raw map[string]any
	if err := json.Unmarshal(data, &raw); err != nil {
		return "", err
	}
	src, _ := raw["_source"].(map[string]any)
	if src == nil {
		src = map[string]any{}
	}
	src["_id"] = asString(raw["_id"])
	src["_index"] = asString(raw["_index"])
	b, err := json.MarshalIndent(src, "", "  ")
	if err != nil {
		return string(data), nil
	}
	return string(b), nil
}

// IndexDoc creates or replaces a document. Empty id uses auto-generated id (POST).
func (s *ElasticsearchSession) IndexDoc(index, id, docJSON string) (string, error) {
	if index == "" {
		return "", fmt.Errorf("index required")
	}
	body, err := normalizeEsDocBody(docJSON)
	if err != nil {
		return "", err
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	var path string
	method := http.MethodPost
	if id != "" {
		method = http.MethodPut
		path = fmt.Sprintf("/%s/_doc/%s", url.PathEscape(index), url.PathEscape(id))
	} else {
		path = fmt.Sprintf("/%s/_doc", url.PathEscape(index))
	}
	data, err := s.doRequest(ctx, method, path, body)
	if err != nil {
		return "", err
	}
	var raw map[string]any
	if err := json.Unmarshal(data, &raw); err != nil {
		return "", err
	}
	return asString(raw["_id"]), nil
}

// UpdateDoc partially updates a document via _update.
func (s *ElasticsearchSession) UpdateDoc(index, id, docJSON string) error {
	if index == "" || id == "" {
		return fmt.Errorf("index and id required")
	}
	doc, err := normalizeEsDocBody(docJSON)
	if err != nil {
		return err
	}
	var src any
	if err := json.Unmarshal(doc, &src); err != nil {
		return err
	}
	payload, err := json.Marshal(map[string]any{"doc": src})
	if err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	path := fmt.Sprintf("/%s/_update/%s", url.PathEscape(index), url.PathEscape(id))
	_, err = s.doRequest(ctx, http.MethodPost, path, payload)
	return err
}

// DeleteDoc deletes a document by id.
func (s *ElasticsearchSession) DeleteDoc(index, id string) error {
	if index == "" || id == "" {
		return fmt.Errorf("index and id required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	path := fmt.Sprintf("/%s/_doc/%s", url.PathEscape(index), url.PathEscape(id))
	_, err := s.doRequest(ctx, http.MethodDelete, path, nil)
	return err
}

// CreateIndex creates an index with optional body JSON.
func (s *ElasticsearchSession) CreateIndex(index, bodyJSON string) error {
	if index == "" {
		return fmt.Errorf("index required")
	}
	var body []byte
	if strings.TrimSpace(bodyJSON) != "" {
		if !json.Valid([]byte(bodyJSON)) {
			return fmt.Errorf("invalid index body JSON")
		}
		body = []byte(bodyJSON)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	_, err := s.doRequest(ctx, http.MethodPut, "/"+url.PathEscape(index), body)
	return err
}

// DeleteIndex deletes an index.
func (s *ElasticsearchSession) DeleteIndex(index string) error {
	if index == "" {
		return fmt.Errorf("index required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	_, err := s.doRequest(ctx, http.MethodDelete, "/"+url.PathEscape(index), nil)
	return err
}

// OpenIndex opens a closed index.
func (s *ElasticsearchSession) OpenIndex(index string) error {
	if index == "" {
		return fmt.Errorf("index required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	_, err := s.doRequest(ctx, http.MethodPost, "/"+url.PathEscape(index)+"/_open", nil)
	return err
}

// CloseIndex closes an index.
func (s *ElasticsearchSession) CloseIndex(index string) error {
	if index == "" {
		return fmt.Errorf("index required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	_, err := s.doRequest(ctx, http.MethodPost, "/"+url.PathEscape(index)+"/_close", nil)
	return err
}

// Rest executes an arbitrary REST request for the Dev Tools console.
func (s *ElasticsearchSession) Rest(method, path, bodyJSON string) (*EsRestResult, error) {
	method = strings.ToUpper(strings.TrimSpace(method))
	if method == "" {
		method = http.MethodGet
	}
	path = strings.TrimSpace(path)
	if path == "" {
		path = "/"
	}
	if !strings.HasPrefix(path, "/") {
		path = "/" + path
	}
	var body []byte
	if strings.TrimSpace(bodyJSON) != "" {
		body = []byte(bodyJSON)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	client, base, auth, err := s.client()
	if err != nil {
		return nil, err
	}
	u := base + path
	var reader io.Reader
	if body != nil {
		reader = bytes.NewReader(body)
	}
	req, err := http.NewRequestWithContext(ctx, method, u, reader)
	if err != nil {
		return nil, err
	}
	if auth != "" {
		req.Header.Set("Authorization", auth)
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	req.Header.Set("Accept", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(io.LimitReader(resp.Body, 64<<20))
	if err != nil {
		return nil, err
	}
	return &EsRestResult{
		Status: resp.StatusCode,
		Body:   prettyJSON(data),
	}, nil
}

func normalizeEsDocBody(docJSON string) ([]byte, error) {
	trimmed := strings.TrimSpace(docJSON)
	if trimmed == "" {
		return []byte("{}"), nil
	}
	var m map[string]any
	if err := json.Unmarshal([]byte(trimmed), &m); err != nil {
		return nil, fmt.Errorf("invalid document JSON: %w", err)
	}
	delete(m, "_id")
	delete(m, "_index")
	delete(m, "_score")
	delete(m, "_type")
	return json.Marshal(m)
}

func prettyJSON(data []byte) string {
	var buf bytes.Buffer
	if err := json.Indent(&buf, data, "", "  "); err != nil {
		return string(data)
	}
	return buf.String()
}

func parseEsTotal(v any) int64 {
	switch t := v.(type) {
	case float64:
		return int64(t)
	case map[string]any:
		return int64(asInt(t["value"]))
	default:
		return 0
	}
}

func asString(v any) string {
	switch t := v.(type) {
	case string:
		return t
	case float64:
		return strconv.FormatFloat(t, 'f', -1, 64)
	case bool:
		return strconv.FormatBool(t)
	case nil:
		return ""
	default:
		b, _ := json.Marshal(t)
		return string(b)
	}
}

func asInt(v any) int {
	switch t := v.(type) {
	case float64:
		return int(t)
	case int:
		return t
	case int64:
		return int(t)
	case string:
		n, _ := strconv.Atoi(t)
		return n
	default:
		return 0
	}
}
