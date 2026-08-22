package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/debug"
	"easyaiot/post/internal/engine"
	"easyaiot/post/internal/health"
	"easyaiot/post/internal/metrics"
	mqttbus "easyaiot/post/internal/mqtt"
	"easyaiot/post/internal/nacos"
	"easyaiot/post/internal/plugin"
	"easyaiot/post/internal/template"
)

func main() {
	cfg := config.Load()
	slog.SetDefault(slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo})))

	cache := template.NewCache(cfg.TaskCacheTTL)
	ready := &metrics.ReadyFlag{}

	var store *template.Store
	if cfg.DatabaseURL != "" {
		var err error
		store, err = template.OpenStore(cfg.DatabaseURL)
		if err != nil {
			slog.Error("warmup_db_open_failed", "err", err)
			metrics.WarmupError.WithLabelValues(cfg.InstanceID).Inc()
			os.Exit(1)
		}
		defer store.Close()
		ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		n, err := template.Warmup(ctx, store, cache)
		cancel()
		if err != nil {
			slog.Error("warmup_failed", "err", err)
			metrics.WarmupError.WithLabelValues(cfg.InstanceID).Inc()
			os.Exit(1)
		}
		slog.Info("warmup_ok", "tasks", n)
	} else {
		slog.Warn("DATABASE_URL empty; starting with empty cache (PUT required)")
	}

	bus := mqttbus.New(cfg)
	if err := bus.Connect(); err != nil {
		slog.Error("mqtt_connect_failed", "err", err)
		os.Exit(1)
	}
	defer bus.Close()

	ready.Set(true)

	// v1.9: register to Nacos only when ready (MQTT + warmup)
	var nacosReg *nacos.Registrar
	if cfg.NacosServer != "" {
		nacosReg = nacos.NewRegistrarFromEnv(cfg.HTTPAddr)
		if nacosReg != nil {
			if err := nacosReg.Register(); err != nil {
				slog.Error("nacos_register_failed", "err", err)
				// 有 Nacos 配置时注册失败 → not ready（多节点主路径）
				ready.Set(false)
				os.Exit(1)
			}
			defer nacosReg.Deregister()
		}
	}

	syncPub := &template.SyncPublisher{Bus: bus, Topic: cfg.TopicTaskSync, InstanceID: cfg.InstanceID}
	eng := engine.New(cfg, cache, bus)
	eng.Sync = syncPub

	// Infer shared subscription
	inferTopic := bus.ShareTopic(cfg.TopicInferEvent)
	if err := bus.Subscribe(inferTopic, 1, func(_ mqtt.Client, msg mqtt.Message) {
		eng.HandleInferJSON(msg.Payload())
	}); err != nil {
		slog.Error("subscribe_infer_failed", "err", err)
		os.Exit(1)
	}

	// Task sync (non-shared so every replica gets it)
	if err := bus.Subscribe(cfg.TopicTaskSync, 1, func(_ mqtt.Client, msg mqtt.Message) {
		template.ApplySync(cache, cfg.InstanceID, msg.Payload())
	}); err != nil {
		slog.Error("subscribe_sync_failed", "err", err)
		os.Exit(1)
	}

	go func() {
		t := time.NewTicker(30 * time.Second)
		defer t.Stop()
		for range t.C {
			cache.SweepExpired()
			plugin.SweepTrackState()
		}
	}()

	mux := http.NewServeMux()
	tplHTTP := &template.HTTPDeps{
		Cache: cache, Store: store, Sync: syncPub,
		AdminToken: cfg.AdminToken, InstanceID: cfg.InstanceID,
	}
	tplHTTP.RegisterRoutes(mux)
	(&health.Deps{Ready: ready, Bus: bus}).Register(mux)
	mux.Handle("/metrics", metrics.Handler())
	if cfg.DebugHTTP {
		(&debug.Handler{Engine: eng, Cache: cache}).Register(mux)
		slog.Info("debug_http_enabled")
	}

	srv := &http.Server{Addr: cfg.HTTPAddr, Handler: mux}
	go func() {
		slog.Info("http_listen", "addr", cfg.HTTPAddr, "instance", cfg.InstanceID)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			slog.Error("http_failed", "err", err)
			os.Exit(1)
		}
	}()

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = srv.Shutdown(ctx)
}
