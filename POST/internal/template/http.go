package template

import (
	"context"
	"encoding/json"
	"net/http"
	"strconv"
	"strings"
	"time"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/metrics"
)

// HTTPDeps wires template HTTP handlers.
type HTTPDeps struct {
	Cache      *Cache
	Store      *Store
	Sync       *SyncPublisher
	AdminToken string
	InstanceID string
}

func (d *HTTPDeps) auth(r *http.Request) bool {
	if d.AdminToken == "" {
		return true
	}
	tok := r.Header.Get("Authorization")
	if strings.HasPrefix(tok, "Bearer ") {
		tok = strings.TrimPrefix(tok, "Bearer ")
	}
	if tok == "" {
		tok = r.Header.Get("X-Admin-Token")
	}
	return tok == d.AdminToken
}

// RegisterRoutes mounts template management endpoints on mux.
func (d *HTTPDeps) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/v1/tasks/", d.handleTaskPath)
	mux.HandleFunc("/v1/admin/reload-running-tasks", d.handleReload)
}

func (d *HTTPDeps) handleTaskPath(w http.ResponseWriter, r *http.Request) {
	// /v1/tasks/{id}/template
	path := strings.TrimPrefix(r.URL.Path, "/v1/tasks/")
	parts := strings.Split(strings.Trim(path, "/"), "/")
	if len(parts) != 2 || parts[1] != "template" {
		http.NotFound(w, r)
		return
	}
	taskID, err := strconv.ParseInt(parts[0], 10, 64)
	if err != nil {
		http.Error(w, "invalid task_id", http.StatusBadRequest)
		return
	}
	if !d.auth(r) {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	switch r.Method {
	case http.MethodPut, http.MethodPost:
		d.handleUpsert(w, r, taskID)
	case http.MethodDelete:
		d.handleDelete(w, r, taskID)
	default:
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
	}
}

func (d *HTTPDeps) handleUpsert(w http.ResponseWriter, r *http.Request, taskID int64) {
	var tpl config.TaskTemplate
	if err := json.NewDecoder(r.Body).Decode(&tpl); err != nil {
		http.Error(w, "bad json: "+err.Error(), http.StatusBadRequest)
		return
	}
	if tpl.Schema == "" {
		tpl.Schema = contract.SchemaTaskTemplate
	}
	if tpl.Task.ID == 0 {
		tpl.Task.ID = taskID
	}
	if tpl.Task.ID != taskID {
		http.Error(w, "task_id mismatch", http.StatusBadRequest)
		return
	}
	if err := config.ValidateTaskTemplate(tpl); err != nil {
		http.Error(w, "invalid template: "+err.Error(), http.StatusBadRequest)
		return
	}
	exp, applied := d.Cache.UpsertVersioned(tpl)
	metrics.TemplateUpsert.WithLabelValues(d.InstanceID).Inc()
	if !applied {
		metrics.TemplateStale.WithLabelValues("upsert", d.InstanceID).Inc()
	}
	if applied && d.Sync != nil {
		d.Sync.PublishUpsert(tpl)
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"ok": true, "applied": applied, "task_id": taskID,
		"revision": tpl.Revision, "expires_at": exp.Format(time.RFC3339),
	})
}

func (d *HTTPDeps) handleDelete(w http.ResponseWriter, r *http.Request, taskID int64) {
	revision, _ := strconv.ParseInt(strings.TrimSpace(r.URL.Query().Get("revision")), 10, 64)
	applied := d.Cache.DeleteVersioned(taskID, revision)
	metrics.TemplateDelete.WithLabelValues(d.InstanceID).Inc()
	if !applied {
		metrics.TemplateStale.WithLabelValues("delete", d.InstanceID).Inc()
	}
	if applied && d.Sync != nil {
		d.Sync.PublishDelete(taskID, revision)
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "applied": applied, "task_id": taskID, "revision": revision})
}

func (d *HTTPDeps) handleReload(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if !d.auth(r) {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	if d.Store == nil {
		http.Error(w, "DATABASE_URL not configured", http.StatusServiceUnavailable)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 60*time.Second)
	defer cancel()
	n, err := Warmup(ctx, d.Store, d.Cache)
	if err != nil {
		metrics.WarmupError.WithLabelValues(d.InstanceID).Inc()
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "loaded": n})
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}
