package metrics

import (
	"net/http"
	"sync/atomic"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	InferTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "post_infer_total", Help: "Infer events received",
	}, []string{"kind", "instance"})

	PassTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "post_pass_total", Help: "Custom post pass count",
	}, []string{"instance"})

	DropTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "post_drop_total", Help: "Custom post drop count",
	}, []string{"reason", "instance"})

	PluginLatency = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "post_plugin_latency_ms", Help: "Plugin latency ms",
		Buckets: []float64{0.1, 0.5, 1, 2, 5, 10, 25, 50, 100},
	}, []string{"plugin"})

	CacheMiss = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "post_task_cache_miss_total", Help: "Task template cache miss",
	}, []string{"instance"})

	TemplateUpsert = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "post_task_template_upsert_total", Help: "Template upserts",
	}, []string{"instance"})

	TemplateDelete = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "post_task_template_delete_total", Help: "Template deletes",
	}, []string{"instance"})

	SyncApply = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "post_task_sync_apply_total", Help: "Task sync applied",
	}, []string{"op", "instance"})

	WarmupError = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "post_warmup_error_total", Help: "Warmup errors",
	}, []string{"instance"})

	MQTTPublishError = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "post_mqtt_publish_error_total", Help: "MQTT publish errors",
	}, []string{"topic"})
)

// Handler returns Prometheus HTTP handler.
func Handler() http.Handler { return promhttp.Handler() }

// ReadyFlag tracks readiness.
type ReadyFlag struct{ v atomic.Bool }

func (r *ReadyFlag) Set(ok bool) { r.v.Store(ok) }
func (r *ReadyFlag) Ready() bool { return r.v.Load() }
