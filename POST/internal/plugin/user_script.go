package plugin

import (
	"fmt"
	"os"
	"strings"
	"time"

	"easyaiot/post/internal/pipeline"
)

// UserScript is a Phase2 builtin enrich plugin that POSTs Context to USER_SCRIPT_URL.
type UserScript struct {
	URL     string
	Timeout time.Duration
}

func (UserScript) Name() string { return "user_script" }
func (UserScript) Kinds() []pipeline.PluginKind {
	return []pipeline.PluginKind{pipeline.KindEnrich}
}

func (u UserScript) Process(ctx *pipeline.Context) (pipeline.PluginDelta, error) {
	url := strings.TrimSpace(u.URL)
	if url == "" {
		url = strings.TrimSpace(os.Getenv("USER_SCRIPT_URL"))
	}
	if url == "" {
		return pipeline.PluginDelta{}, fmt.Errorf("user_script: USER_SCRIPT_URL not configured")
	}
	timeout := u.Timeout
	if timeout <= 0 {
		timeout = 2 * time.Second
	}
	ext := ExternalHTTP{
		ID:      "user_script",
		BaseURL: url,
		Timeout: timeout,
	}
	return ext.Process(ctx)
}
