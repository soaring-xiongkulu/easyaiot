package plugin

import (
	"strings"
	"time"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/pipeline"
)

// BuiltinNames are always resolved in-process (never via external HTTP).
var BuiltinNames = map[string]struct{}{
	"region_gate":       {},
	"default_pass":      {},
	"user_script":       {},
	"line_cross":        {},
	"region_enter_exit": {},
	"dwell_timer":       {},
	"headcount_gate":    {},
}

// IsBuiltin reports whether plugin id is a platform builtin.
func IsBuiltin(id string) bool {
	_, ok := BuiltinNames[id]
	return ok
}

// NewRegistry builds builtin registry (optionally with configured user_script).
func NewRegistry(cfg config.Config) pipeline.Registry {
	reg := pipeline.Registry{
		"region_gate":       RegionGate{},
		"default_pass":      DefaultPass{},
		"line_cross":        LineCross{},
		"region_enter_exit": RegionEnterExit{},
		"dwell_timer":       DwellTimer{},
		"headcount_gate":    HeadcountGate{},
	}
	timeout := cfg.PluginHTTPTimeout
	if timeout <= 0 {
		timeout = 2 * time.Second
	}
	reg["user_script"] = UserScript{URL: cfg.UserScriptURL, Timeout: timeout}
	return reg
}

// Builtin returns the default registry without env-specific URLs (tests / replay).
func Builtin() pipeline.Registry {
	return NewRegistry(config.Config{})
}

// Resolve picks a plugin for a pipeline step.
// Builtin registry first; otherwise non-empty endpoint → ExternalHTTP; else nil.
func Resolve(reg pipeline.Registry, step config.PipelineStep, httpTimeout time.Duration) pipeline.Plugin {
	if p := reg[step.Plugin]; p != nil {
		return p
	}
	ep := strings.TrimSpace(step.Endpoint)
	if ep == "" {
		return nil
	}
	if httpTimeout <= 0 {
		httpTimeout = 2 * time.Second
	}
	return NewExternalFromStep(step.Plugin, ep, step.Version, httpTimeout)
}
