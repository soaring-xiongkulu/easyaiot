package health

import (
	"encoding/json"
	"net/http"

	"easyaiot/post/internal/metrics"
	mqttbus "easyaiot/post/internal/mqtt"
)

// Deps for health endpoints.
type Deps struct {
	Ready *metrics.ReadyFlag
	Bus   *mqttbus.Bus
}

func (d *Deps) Register(mux *http.ServeMux) {
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})
	mux.HandleFunc("/readyz", func(w http.ResponseWriter, _ *http.Request) {
		mqttOK := d.Bus != nil && d.Bus.Connected()
		ready := d.Ready != nil && d.Ready.Ready() && mqttOK
		body := map[string]any{"ready": ready, "mqtt": mqttOK, "warmup": d.Ready != nil && d.Ready.Ready()}
		w.Header().Set("Content-Type", "application/json")
		if !ready {
			w.WriteHeader(http.StatusServiceUnavailable)
		}
		_ = json.NewEncoder(w).Encode(body)
	})
}
