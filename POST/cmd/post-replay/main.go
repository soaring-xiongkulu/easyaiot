package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"time"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/maplegacy"
	"easyaiot/post/internal/pipeline"
	"easyaiot/post/internal/plugin"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "usage: post-replay <event.json> [template.json]\n")
		os.Exit(2)
	}
	raw, err := os.ReadFile(os.Args[1])
	if err != nil {
		fatal(err)
	}
	var ev contract.InferEvent
	if err := json.Unmarshal(raw, &ev); err != nil {
		fatal(err)
	}
	_ = ev.Validate()

	task := config.TaskConfig{ID: ev.TaskID, TaskName: ev.TaskName, TaskType: ev.TaskType, ModelIDs: ev.ModelIDs}
	var regions []config.Region
	if len(os.Args) >= 3 {
		traw, err := os.ReadFile(os.Args[2])
		if err != nil {
			fatal(err)
		}
		var tpl config.TaskTemplate
		if err := json.Unmarshal(traw, &tpl); err != nil {
			fatal(err)
		}
		task = tpl.Task
		regions = tpl.Regions
		// filter by device
		var filtered []config.Region
		for _, r := range regions {
			if r.DeviceID == ev.DeviceID || r.DeviceID == "" {
				filtered = append(filtered, r)
			}
		}
		regions = filtered
	}

	reg := plugin.Builtin()
	timeout := cfgTimeout()
	res := pipeline.RunWith(pipeline.Options{
		Registry: reg,
		Resolve: func(step config.PipelineStep) pipeline.Plugin {
			return plugin.Resolve(reg, step, timeout)
		},
		Debug: true,
	}, ev, task, regions)
	out := map[string]any{
		"result":      string(res.Decision),
		"drop_reason": res.DropReason,
		"trace":       res.Trace,
	}
	if res.Decision == pipeline.DecisionPass && res.Context != nil {
		out["alert_payload"] = maplegacy.ToAlertNotification(res.Context)
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	_ = enc.Encode(out)
	if res.Decision == pipeline.DecisionDrop {
		os.Exit(1)
	}
}

func fatal(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}

func cfgTimeout() time.Duration {
	ms := 2000
	if v := os.Getenv("PLUGIN_HTTP_TIMEOUT_MS"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			ms = n
		}
	}
	return time.Duration(ms) * time.Millisecond
}
