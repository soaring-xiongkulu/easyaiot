package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	stdsync "sync"
	"time"

	"github.com/mattn/go-ieproxy"
	"easyaiot/terminal/backend/session"
	"easyaiot/terminal/backend/store"
)

// llmProxy is the Proxy function for the shared LLM transport. It resolves
// the OS system proxy (Windows registry / macOS system config, including PAC
// scripts) and falls back to the HTTP_PROXY/HTTPS_PROXY environment
// variables — http.ProxyFromEnvironment alone misses users who enable
// "system proxy" mode in tools like Clash, which never sets env vars.
// ieproxy caches the system config on first read, so refresh it periodically
// via ReloadConf to pick up toggles made while the app is running.
// ReloadConf is not goroutine-safe, so all access is serialized here.
const llmProxyRefreshInterval = 30 * time.Second

var (
	llmProxyMu      stdsync.Mutex
	llmProxyFn      func(*http.Request) (*url.URL, error)
	llmProxyRefresh time.Time
)

func llmProxy(req *http.Request) (*url.URL, error) {
	llmProxyMu.Lock()
	defer llmProxyMu.Unlock()
	if llmProxyFn == nil || time.Since(llmProxyRefresh) >= llmProxyRefreshInterval {
		ieproxy.ReloadConf()
		llmProxyFn = ieproxy.GetProxyFunc()
		llmProxyRefresh = time.Now()
	}
	return llmProxyFn(req)
}

// llmDirectClient returns the package-level client for the "direct" proxy
// selection. Proxy is deliberately nil: direct means bypassing the system
// proxy AND the HTTP(S)_PROXY env vars. Separate from the system-proxy pool
// so both connection caches stay warm independently.
var (
	llmDirectOnce   stdsync.Once
	llmDirectShared *http.Client
)

func llmDirectClient() *http.Client {
	llmDirectOnce.Do(func() {
		llmDirectShared = &http.Client{Transport: &http.Transport{
			MaxIdleConns:          100,
			MaxIdleConnsPerHost:   8,
			IdleConnTimeout:       90 * time.Second,
			TLSHandshakeTimeout:   10 * time.Second,
			ResponseHeaderTimeout: 30 * time.Second,
			ExpectContinueTimeout: 2 * time.Second,
		}}
	})
	return llmDirectShared
}

// llmHTTPClient returns the App-wide *http.Client used by every
// LLM-bound call. F-208: hoisted here so three back-to-back
// ChatCompletion calls reuse the same TCP+TLS connection instead of
// paying a fresh handshake each time. FetchModels uses a shorter
// timeout via a derived client (see FetchModels).
func (a *App) llmHTTPClient() *http.Client {
	a.httpClientOnce.Do(func() {
		tr := &http.Transport{
			Proxy:                 llmProxy,
			MaxIdleConns:          100,
			MaxIdleConnsPerHost:   8,
			IdleConnTimeout:       90 * time.Second,
			TLSHandshakeTimeout:   10 * time.Second,
			ResponseHeaderTimeout: 30 * time.Second,
			ExpectContinueTimeout: 2 * time.Second,
		}
		a.httpClient = &http.Client{Transport: tr}
	})
	return a.httpClient
}

// injectCacheControl adds ephemeral cache_control breakpoints on the
// static system prompt and tools array so Anthropic's prompt caching
// beta actually caches them across turns. Without this the
// prompt-caching-2024-07-31 header is sent but the request body has
// no breakpoints, so every turn re-ships and re-bills the static
// prefix (~3 KB in typical Claude Code sessions). F-303.
func injectCacheControl(reqBody map[string]interface{}) {
	if sys, ok := reqBody["system"].(string); ok && sys != "" {
		reqBody["system"] = []map[string]interface{}{{
			"type":          "text",
			"text":          sys,
			"cache_control": map[string]string{"type": "ephemeral"},
		}}
	}
	if tools, ok := reqBody["tools"].([]interface{}); ok && len(tools) > 0 {
		if last, ok := tools[len(tools)-1].(map[string]interface{}); ok {
			last["cache_control"] = map[string]string{"type": "ephemeral"}
		}
	}
}

// ChatCompletion streams the Anthropic API response via SSE, emitting Wails
// events for each token while collecting the full message. It returns the
// complete message JSON when the stream ends (backward-compatible).
func (a *App) ChatCompletion(apiKey, baseURL, model string, requestJSON string, protocol string, userAgent string, proxyID string) (string, error) {
	// Parse the incoming request body (always Anthropic format from frontend)
	var reqBody map[string]interface{}
	if err := json.Unmarshal([]byte(requestJSON), &reqBody); err != nil {
		return "", fmt.Errorf("invalid request JSON: %w", err)
	}

	if userAgent == "" {
		userAgent = "Terminal"
	}

	client, err := a.llmClientFor(proxyID)
	if err != nil {
		return "", err
	}

	switch protocol {
	case "openai":
		return a.chatCompletionOpenAI(apiKey, baseURL, model, reqBody, userAgent, client)
	case "responses":
		return a.chatCompletionResponses(apiKey, baseURL, model, reqBody, userAgent, client)
	}
	return a.chatCompletionAnthropic(apiKey, baseURL, model, reqBody, userAgent, client)
}

// llmClientFor returns the HTTP client for the model's proxy selection:
// an empty reference dials direct, session.ProxyIDSystem uses the shared
// system-proxy client (see llmProxy), and a saved proxy ID builds a client
// routed through that proxy (F-208 connection reuse applies per client).
func (a *App) llmClientFor(proxyID string) (*http.Client, error) {
	switch proxyID {
	case "":
		return llmDirectClient(), nil
	case session.ProxyIDSystem:
		return a.llmHTTPClient(), nil
	}
	resolve, err := a.proxyResolver()
	if err != nil {
		return nil, err
	}
	p, ok := resolve(proxyID)
	if !ok {
		return nil, fmt.Errorf("referenced proxy not found or disabled: %s", proxyID)
	}
	return llmHTTPClientFor(&p), nil
}

// llmHTTPClientFor returns an *http.Client whose transport routes through the
// given upstream proxy (HTTP CONNECT for https URLs, SOCKS5 natively).
func llmHTTPClientFor(proxy *session.SocksProxy) *http.Client {
	tr := &http.Transport{
		Proxy: func(*http.Request) (*url.URL, error) {
			return proxyTransportURL(proxy)
		},
		MaxIdleConns:          100,
		MaxIdleConnsPerHost:   8,
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:   10 * time.Second,
		ResponseHeaderTimeout: 30 * time.Second,
		ExpectContinueTimeout: 2 * time.Second,
	}
	return &http.Client{Transport: tr}
}

// proxyTransportURL renders a saved SOCKS5/HTTP proxy as a proxy URL for
// http.Transport. http.Transport natively speaks SOCKS5 via the socks5 scheme.
func proxyTransportURL(p *session.SocksProxy) (*url.URL, error) {
	u := &url.URL{Scheme: p.Kind, Host: net.JoinHostPort(p.Host, strconv.Itoa(p.Port))}
	if p.User != "" {
		u.User = url.UserPassword(p.User, p.Pass)
	}
	return u, nil
}

// chatCompletionAnthropic handles the native Anthropic Messages API with SSE streaming.
func (a *App) chatCompletionAnthropic(apiKey, baseURL, model string, reqBody map[string]interface{}, userAgent string, client *http.Client) (string, error) {
	reqBody["stream"] = true

	modifiedJSON, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("marshal modified request: %w", err)
	}

	// Anthropic base URL conventionally omits /v1 (client appends /v1/messages).
	// Tolerate legacy configs that already include the /v1 suffix.
	base := strings.TrimRight(baseURL, "/")
	var url string
	if strings.HasSuffix(base, "/v1") {
		url = base + "/messages"
	} else {
		url = base + "/v1/messages"
	}

	ctx, cancel := context.WithTimeout(context.Background(), 600*time.Second)
	defer cancel()

	// F-308: atomic pointer swap so overlapping ChatCompletion calls
	// don't clobber each other's cancel function.
	myCancel := cancel
	a.chatCancel.Store(&myCancel)
	defer func() {
		a.chatCancel.CompareAndSwap(&myCancel, nil)
	}()

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(modifiedJSON))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("x-api-key", apiKey)
	req.Header.Set("anthropic-version", "2023-06-01")
	req.Header.Set("anthropic-beta", "prompt-caching-2024-07-31")
	req.Header.Set("User-Agent", userAgent)

	// Use the shared client so this path honors the same system/env proxy
	// resolution and connection pool as the OpenAI/Responses paths.
	res, err := client.Do(req)
	if err != nil {
		if ctx.Err() == context.DeadlineExceeded {
			return "", fmt.Errorf("AI_REQUEST_TIMEOUT")
		}
		return "", err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		// F-305: cap error-body reads at 64 KiB.
		body, _ := io.ReadAll(io.LimitReader(res.Body, 64*1024))
		return "", fmt.Errorf("HTTP %d: %s", res.StatusCode, string(body))
	}

	var contentBlocks []map[string]interface{}
	var currentBlock map[string]interface{}
	var messageRole string
	var usage map[string]interface{}
	currentBlockIndex := -1

	scanner := bufio.NewScanner(res.Body)
	scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)

	for scanner.Scan() {
		line := scanner.Text()
		if !strings.HasPrefix(line, "data: ") {
			continue
		}
		dataStr := line[6:]

		var event map[string]interface{}
		if err := json.Unmarshal([]byte(dataStr), &event); err != nil {
			continue
		}

		eventType, _ := event["type"].(string)

		switch eventType {
		case "message_start":
			if msg, ok := event["message"].(map[string]interface{}); ok {
				messageRole, _ = msg["role"].(string)
			}

		case "content_block_start":
			currentBlockIndex++
			if block, ok := event["content_block"].(map[string]interface{}); ok {
				currentBlock = block
				a.emit("ai:block_start", map[string]interface{}{
					"index":         currentBlockIndex,
					"content_block": block,
				})
			}

		case "content_block_delta":
			delta, _ := event["delta"].(map[string]interface{})
			deltaType, _ := delta["type"].(string)

			if deltaType == "text_delta" {
				text, _ := delta["text"].(string)
				if currentBlock != nil {
					if currentBlock["text"] == nil {
						currentBlock["text"] = ""
					}
					currentBlock["text"] = currentBlock["text"].(string) + text
				}
				a.emit("ai:token", map[string]interface{}{
					"text":  text,
					"index": currentBlockIndex,
				})
			}
			if deltaType == "input_json_delta" && currentBlock != nil {
				partial, _ := delta["partial_json"].(string)
				if currentBlock["input"] == nil || fmt.Sprintf("%T", currentBlock["input"]) != "string" {
					currentBlock["input"] = ""
				}
				if s, ok := currentBlock["input"].(string); ok {
					currentBlock["input"] = s + partial
				}
			}

		case "content_block_stop":
			if currentBlock != nil {
				if blockType, _ := currentBlock["type"].(string); blockType == "tool_use" {
					if inputStr, ok := currentBlock["input"].(string); ok && inputStr != "" {
						var inputObj map[string]interface{}
						if err := json.Unmarshal([]byte(inputStr), &inputObj); err == nil {
							currentBlock["input"] = inputObj
						}
					}
				}
				contentBlocks = append(contentBlocks, currentBlock)
				currentBlock = nil
			}

		case "message_delta":
			if u, ok := event["usage"].(map[string]interface{}); ok {
				usage = u
			}
			if delta, ok := event["delta"].(map[string]interface{}); ok {
				if stopReason, ok := delta["stop_reason"].(string); ok {
					a.emit("ai:done", map[string]interface{}{
						"message": map[string]interface{}{
							"role":    messageRole,
							"content": contentBlocks,
						},
						"usage":       usage,
						"stop_reason": stopReason,
					})
				}
			}

		case "message_stop":
			fullMessage := map[string]interface{}{
				"role":    messageRole,
				"content": contentBlocks,
			}
			resultJSON, err := json.Marshal(fullMessage)
			if err != nil {
				return "", fmt.Errorf("marshal full message: %w", err)
			}
			return string(resultJSON), nil

		case "error":
			errData, _ := event["error"].(map[string]interface{})
			errMsg, _ := errData["message"].(string)
			return "", fmt.Errorf("stream error: %s", errMsg)
		}
	}

	if err := scanner.Err(); err != nil {
		return "", err
	}

	if len(contentBlocks) > 0 {
		fullMessage := map[string]interface{}{
			"role":    messageRole,
			"content": contentBlocks,
		}
		resultJSON, _ := json.Marshal(fullMessage)
		return string(resultJSON), nil
	}

	return "", fmt.Errorf("stream ended without message_stop")
}

// marshalAnthropicFinalMessage encodes a final message using a pooled
// *bytes.Buffer to avoid per-turn allocator churn in heavy sessions.
func marshalAnthropicFinalMessage(msg map[string]interface{}) ([]byte, error) {
	buf := finalMsgPool.Get().(*bytes.Buffer)
	buf.Reset()
	defer finalMsgPool.Put(buf)
	enc := json.NewEncoder(buf)
	if err := enc.Encode(msg); err != nil {
		return nil, err
	}
	// json.Encoder always appends a trailing newline; trim it.
	out := buf.Bytes()
	if n := len(out); n > 0 && out[n-1] == '\n' {
		out = out[:n-1]
	}
	return out, nil
}

func anthropicToolToOpenAI(t map[string]interface{}) map[string]interface{} {
	return map[string]interface{}{
		"type": "function",
		"function": map[string]interface{}{
			"name":        t["name"],
			"description": t["description"],
			"parameters":  t["input_schema"],
		},
	}
}

// convertAnthropicMessageToOpenAI converts one Anthropic-format message to OpenAI format.
func convertAnthropicMessageToOpenAI(msg map[string]interface{}) []map[string]interface{} {
	role, _ := msg["role"].(string)
	content := msg["content"]

	var results []map[string]interface{}

	switch role {
	case "user":
		out := map[string]interface{}{"role": "user"}
		if contentStr, ok := content.(string); ok {
			out["content"] = contentStr
		} else if contentBlocks, ok := content.([]interface{}); ok {
			for _, block := range contentBlocks {
				if b, ok := block.(map[string]interface{}); ok {
					if bType, _ := b["type"].(string); bType == "text" {
						out["content"] = b["text"]
					}
					if bType, _ := b["type"].(string); bType == "tool_result" {
						toolMsg := map[string]interface{}{
							"role":         "tool",
							"tool_call_id": b["tool_use_id"],
							"content":      toString(b["content"]),
						}
						results = append(results, toolMsg)
					}
				}
			}
		}
		// Emit tool messages first, then any text user message. An OpenAI-format
		// assistant message with tool_calls must be immediately followed by the
		// matching tool messages; a user text block placed before them triggers a
		// 400 "insufficient tool messages following tool_calls" error.
		if _, hasContent := out["content"]; hasContent {
			results = append(results, out)
		}

	case "assistant":
		out := map[string]interface{}{"role": "assistant"}
		var toolCalls []map[string]interface{}
		if contentStr, ok := content.(string); ok {
			out["content"] = contentStr
		} else if contentBlocks, ok := content.([]interface{}); ok {
			for _, block := range contentBlocks {
				if b, ok := block.(map[string]interface{}); ok {
					if bType, _ := b["type"].(string); bType == "text" {
						out["content"] = b["text"]
					}
					if bType, _ := b["type"].(string); bType == "tool_use" {
						argsStr := "{}"
						if input, ok := b["input"]; ok {
							argsBytes, _ := json.Marshal(input)
							argsStr = string(argsBytes)
						}
						toolCalls = append(toolCalls, map[string]interface{}{
							"id":   b["id"],
							"type": "function",
							"function": map[string]interface{}{
								"name":      b["name"],
								"arguments": argsStr,
							},
						})
					}
				}
			}
		}
		if len(toolCalls) > 0 {
			out["tool_calls"] = toolCalls
		}
		results = append([]map[string]interface{}{out}, results...)

	default:
		out := map[string]interface{}{"role": role}
		if contentStr, ok := content.(string); ok {
			out["content"] = contentStr
		}
		results = append([]map[string]interface{}{out}, results...)
	}

	return results
}

func toString(v interface{}) string {
	switch val := v.(type) {
	case string:
		return val
	default:
		b, _ := json.Marshal(v)
		return string(b)
	}
}

// chatCompletionOpenAI converts the Anthropic-format request to OpenAI,
// calls the OpenAI Chat Completions API with SSE streaming, and converts
// the response back to Anthropic format so the frontend sees no difference.
func (a *App) chatCompletionOpenAI(apiKey, baseURL, model string, reqBody map[string]interface{}, userAgent string, client *http.Client) (string, error) {
	url := strings.TrimRight(baseURL, "/") + "/chat/completions"

	// --- Build OpenAI-format request body ---
	openaiBody := map[string]interface{}{
		"model":      model,
		"stream":     true,
		"max_tokens": reqBody["max_tokens"],
	}

	// Convert tools
	if tools, ok := reqBody["tools"].([]interface{}); ok {
		var oaiTools []map[string]interface{}
		for _, t := range tools {
			if tm, ok := t.(map[string]interface{}); ok {
				oaiTools = append(oaiTools, anthropicToolToOpenAI(tm))
			}
		}
		if len(oaiTools) > 0 {
			openaiBody["tools"] = oaiTools
		}
	}

	// Convert messages + system
	var oaiMessages []map[string]interface{}
	if system, ok := reqBody["system"].(string); ok && system != "" {
		oaiMessages = append(oaiMessages, map[string]interface{}{
			"role":    "system",
			"content": system,
		})
	}
	if msgs, ok := reqBody["messages"].([]interface{}); ok {
		for _, m := range msgs {
			if mm, ok := m.(map[string]interface{}); ok {
				converted := convertAnthropicMessageToOpenAI(mm)
				oaiMessages = append(oaiMessages, converted...)
			}
		}
	}
	openaiBody["messages"] = oaiMessages

	requestJSON, err := json.Marshal(openaiBody)
	if err != nil {
		return "", fmt.Errorf("marshal openai request: %w", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 600*time.Second)
	defer cancel()

	// F-308: register our cancel in the App-level pointer and only
	// clear it on the way out if no one replaced us. The previous code
	// stored a single context.CancelFunc under a mutex and unconditionally
	// nil'd it on defer; when two ChatCompletion calls overlapped, call A's
	// defer wiped call B's cancel and CancelChatStream became a no-op for B.
	myCancel := cancel
	a.chatCancel.Store(&myCancel)
	defer func() {
		// CAS the slot back to nil, but only if it still points at our
		// own cancel — a newer call may have already taken over the slot.
		a.chatCancel.CompareAndSwap(&myCancel, nil)
	}()

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(requestJSON))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("User-Agent", userAgent)

	res, err := client.Do(req)
	if err != nil {
		if ctx.Err() == context.DeadlineExceeded {
			return "", fmt.Errorf("AI_REQUEST_TIMEOUT")
		}
		return "", err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		// F-305: cap the error-body read at 64 KiB so a hostile or
		// buggy upstream returning a multi-GB error body can't OOM
		// the Go process.
		body, _ := io.ReadAll(io.LimitReader(res.Body, 64*1024))
		return "", fmt.Errorf("HTTP %d: %s", res.StatusCode, string(body))
	}

	// --- Parse OpenAI SSE stream, emit Anthropic-format events ---
	var contentBlocks []map[string]interface{}
	var currentBlock map[string]interface{}
	var messageRole = "assistant"
	currentBlockIndex := -1
	activeToolCalls := make(map[int]map[string]interface{}) // index -> accumulating tool_call
	// F-307: per-block text and input buffers so accumulation is O(n)
	// instead of O(n²) string concat per token. Flushed to the block
	// map on content_block_stop / finish_reason.
	var currentTextBuf, currentInputBuf bytes.Buffer
	// Per-tool input buffer so each tool_call's argument concat stays
	// O(n). Keyed by the tool's index — multiple tool_calls can run
	// in parallel (one per idx).
	toolInputBufs := make(map[int]*bytes.Buffer)

	scanner := bufio.NewScanner(res.Body)
	scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)

	flushCurrentTextBlock := func() {
		if currentBlock == nil {
			return
		}
		if t, _ := currentBlock["type"].(string); t == "text" && currentTextBuf.Len() > 0 {
			currentBlock["text"] = currentTextBuf.String()
		}
		contentBlocks = append(contentBlocks, currentBlock)
		currentBlock = nil
		currentTextBuf.Reset()
	}

	// Emit message_start at the beginning
	// F-320: typed payload (frontend reads event.message.role).
	a.emit("ai:message_start", aiMessageStartEvent{
		Role: "assistant",
	})

	for scanner.Scan() {
		line := scanner.Text()
		if !strings.HasPrefix(line, "data: ") {
			continue
		}
		dataStr := line[6:]

		if strings.TrimSpace(dataStr) == "[DONE]" {
			// Emit content_block_stop for any open block
			if currentBlock != nil {
				flushCurrentTextBlock()
				a.emit("ai:content_block_stop", aiContentBlockStopEvent{
					Index: currentBlockIndex,
				})
			}
			// Close any open tool_use blocks
			for idx, tc := range activeToolCalls {
				contentBlocks = append(contentBlocks, tc)
				a.emit("ai:content_block_stop", aiContentBlockStopEvent{
					Index: idx,
				})
			}
			activeToolCalls = make(map[int]map[string]interface{})

			// Emit message_delta and message_stop
			// F-320: typed payload.
			a.emit("ai:done", aiDoneEvent{
				Message: map[string]interface{}{
					"role":    messageRole,
					"content": contentBlocks,
				},
				StopReason: "end_turn",
			})

			fullMessage := map[string]interface{}{
				"role":    messageRole,
				"content": contentBlocks,
			}
			resultJSON, _ := json.Marshal(fullMessage)
			return string(resultJSON), nil
		}

		var ev openaiStreamEvent
		if err := json.Unmarshal([]byte(dataStr), &ev); err != nil {
			continue
		}
		if len(ev.Choices) == 0 {
			continue
		}
		choice := ev.Choices[0]
		delta := choice.Delta

		// Handle text content
		if delta.Content != "" {
			if currentBlock == nil || currentBlock["type"] != "text" {
				// Close previous block if any
				if currentBlock != nil {
					flushCurrentTextBlock()
					a.emit("ai:content_block_stop", aiContentBlockStopEvent{
						Index: currentBlockIndex,
					})
				}
				currentBlockIndex++
				currentBlock = map[string]interface{}{
					"type": "text",
					"text": "",
				}
				currentTextBuf.Reset()
				// F-320: typed payload.
				a.emit("ai:block_start", aiBlockStartEvent{
					Index:        currentBlockIndex,
					ContentBlock: currentBlock,
				})
			}
			currentTextBuf.WriteString(delta.Content)
			// F-320: typed struct + dropped unused fields — see
			// chatCompletionAnthropic for rationale.
			a.emit("ai:token", aiTokenEvent{
				Text:  delta.Content,
				Index: currentBlockIndex,
			})
		}

		// Handle tool_calls in delta
		for _, tc := range delta.ToolCalls {
			if tc.Index == nil {
				continue
			}
			idx := *tc.Index

			if _, exists := activeToolCalls[idx]; !exists {
				// Close current text block if open
				if currentBlock != nil {
					flushCurrentTextBlock()
					a.emit("ai:content_block_stop", aiContentBlockStopEvent{
						Index: currentBlockIndex,
					})
				}
				currentBlockIndex++
				activeToolCalls[idx] = map[string]interface{}{
					"type":  "tool_use",
					"id":    tc.ID,
					"name":  "",
					"input": "",
				}
				// F-320: typed payload.
				a.emit("ai:block_start", aiBlockStartEvent{
					Index: currentBlockIndex,
					ContentBlock: map[string]interface{}{
						"type": "tool_use",
						"id":   tc.ID,
					},
				})
			}

			atc := activeToolCalls[idx]
			if tc.Function.Name != "" {
				atc["name"] = tc.Function.Name
			}
			if args := tc.Function.Arguments; args != "" {
				// F-307: append to a per-tool *bytes.Buffer instead of
				// string concat (O(n²) over a long tool-args stream).
				buf, ok := toolInputBufs[idx]
				if !ok {
					buf = &bytes.Buffer{}
					toolInputBufs[idx] = buf
				}
				buf.WriteString(args)
				// F-320: typed payload.
				a.emit("ai:input_json_delta", aiInputJsonDeltaEvent{
					PartialJSON: args,
				})
			}
		}

		// Handle finish_reason on the choice level
		finishReason := choice.FinishReason
		if finishReason != "" && finishReason != "null" {
			// Close any open text block
			if currentBlock != nil {
				flushCurrentTextBlock()
				a.emit("ai:content_block_stop", aiContentBlockStopEvent{
					Index: currentBlockIndex,
				})
			}
			// Close tool_use blocks and parse their input JSON
			for idx, tc := range activeToolCalls {
				// F-307: prefer the per-tool buffer over the
				// possibly-empty tc["input"] string.
				if buf, ok := toolInputBufs[idx]; ok && buf.Len() > 0 {
					inputStr := buf.String()
					var inputObj map[string]interface{}
					if err := json.Unmarshal([]byte(inputStr), &inputObj); err == nil {
						tc["input"] = inputObj
					} else {
						tc["input"] = inputStr
					}
				} else if inputStr, ok := tc["input"].(string); ok && inputStr != "" {
					var inputObj map[string]interface{}
					if err := json.Unmarshal([]byte(inputStr), &inputObj); err == nil {
						tc["input"] = inputObj
					}
				}
				contentBlocks = append(contentBlocks, tc)
				a.emit("ai:content_block_stop", aiContentBlockStopEvent{
					Index: idx,
				})
			}
			activeToolCalls = make(map[int]map[string]interface{})
			toolInputBufs = nil
			currentInputBuf.Reset()

			stopReason := "end_turn"
			if finishReason == "tool_calls" {
				stopReason = "tool_use"
			} else if finishReason == "length" {
				stopReason = "max_tokens"
			} else if finishReason == "stop" {
				stopReason = "end_turn"
			}

			// F-320: typed payload.
			a.emit("ai:done", aiDoneEvent{
				Message: map[string]interface{}{
					"role":    messageRole,
					"content": contentBlocks,
				},
				StopReason: stopReason,
			})

			fullMessage := map[string]interface{}{
				"role":    messageRole,
				"content": contentBlocks,
			}
			resultJSON, _ := json.Marshal(fullMessage)
			return string(resultJSON), nil
		}
	}

	if err := scanner.Err(); err != nil {
		return "", err
	}

	if len(contentBlocks) > 0 || len(activeToolCalls) > 0 {
		for _, tc := range activeToolCalls {
			contentBlocks = append(contentBlocks, tc)
		}
		fullMessage := map[string]interface{}{
			"role":    messageRole,
			"content": contentBlocks,
		}
		resultJSON, _ := json.Marshal(fullMessage)
		return string(resultJSON), nil
	}

	return "", fmt.Errorf("stream ended without completion")
}

// anthropicToolToResponses converts an Anthropic tool definition to the
// Responses API function format (flat, unlike Chat Completions' nested form).
func anthropicToolToResponses(t map[string]interface{}) map[string]interface{} {
	return map[string]interface{}{
		"type":        "function",
		"name":        t["name"],
		"description": t["description"],
		"parameters":  t["input_schema"],
	}
}

// convertAnthropicMessageToResponses converts one Anthropic-format message to
// Responses API input items. Text turns become message items with
// input_text/output_text; tool_use becomes function_call; tool_result becomes
// function_call_output.
func convertAnthropicMessageToResponses(msg map[string]interface{}) []map[string]interface{} {
	role, _ := msg["role"].(string)
	content := msg["content"]

	var results []map[string]interface{}

	textType := "input_text"
	if role == "assistant" {
		textType = "output_text"
	}

	if contentStr, ok := content.(string); ok {
		if contentStr != "" {
			results = append(results, map[string]interface{}{
				"role": role,
				"content": []map[string]interface{}{
					{"type": textType, "text": contentStr},
				},
			})
		}
		return results
	}

	contentBlocks, ok := content.([]interface{})
	if !ok {
		return results
	}

	var textParts []map[string]interface{}
	for _, block := range contentBlocks {
		b, ok := block.(map[string]interface{})
		if !ok {
			continue
		}
		switch b["type"] {
		case "text":
			if txt, _ := b["text"].(string); txt != "" {
				textParts = append(textParts, map[string]interface{}{"type": textType, "text": txt})
			}
		case "tool_use":
			argsStr := "{}"
			if input, ok := b["input"]; ok {
				argsBytes, _ := json.Marshal(input)
				argsStr = string(argsBytes)
			}
			results = append(results, map[string]interface{}{
				"type":      "function_call",
				"call_id":   b["id"],
				"name":      b["name"],
				"arguments": argsStr,
			})
		case "tool_result":
			results = append(results, map[string]interface{}{
				"type":    "function_call_output",
				"call_id": b["tool_use_id"],
				"output":  toString(b["content"]),
			})
		}
	}

	if len(textParts) > 0 {
		msgItem := map[string]interface{}{"role": role, "content": textParts}
		if role == "assistant" {
			results = append([]map[string]interface{}{msgItem}, results...)
		} else {
			results = append(results, msgItem)
		}
	}

	return results
}

// chatCompletionResponses converts the Anthropic-format request to the OpenAI
// Responses API, calls /responses with SSE streaming, and converts the response
// events back to Anthropic-format events so the frontend sees no difference.
// Stateless: full history is sent as `input` each turn; reasoning items are ignored.
func (a *App) chatCompletionResponses(apiKey, baseURL, model string, reqBody map[string]interface{}, userAgent string, client *http.Client) (string, error) {
	url := strings.TrimRight(baseURL, "/") + "/responses"

	// --- Build Responses-format request body ---
	respBody := map[string]interface{}{
		"model":  model,
		"stream": true,
	}
	if mt, ok := reqBody["max_tokens"]; ok {
		respBody["max_output_tokens"] = mt
	}
	if system, ok := reqBody["system"].(string); ok && system != "" {
		respBody["instructions"] = system
	}

	if tools, ok := reqBody["tools"].([]interface{}); ok {
		var respTools []map[string]interface{}
		for _, t := range tools {
			if tm, ok := t.(map[string]interface{}); ok {
				respTools = append(respTools, anthropicToolToResponses(tm))
			}
		}
		if len(respTools) > 0 {
			respBody["tools"] = respTools
		}
	}

	var input []map[string]interface{}
	if msgs, ok := reqBody["messages"].([]interface{}); ok {
		for _, m := range msgs {
			if mm, ok := m.(map[string]interface{}); ok {
				input = append(input, convertAnthropicMessageToResponses(mm)...)
			}
		}
	}
	respBody["input"] = input

	requestJSON, err := json.Marshal(respBody)
	if err != nil {
		return "", fmt.Errorf("marshal responses request: %w", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 600*time.Second)
	defer cancel()

	// F-308: register our cancel in the App-level pointer and only
	// clear it on the way out if no one replaced us. The previous code
	// stored a single context.CancelFunc under a mutex and unconditionally
	// nil'd it on defer; when two ChatCompletion calls overlapped, call A's
	// defer wiped call B's cancel and CancelChatStream became a no-op for B.
	myCancel := cancel
	a.chatCancel.Store(&myCancel)
	defer func() {
		// CAS the slot back to nil, but only if it still points at our
		// own cancel — a newer call may have already taken over the slot.
		a.chatCancel.CompareAndSwap(&myCancel, nil)
	}()

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(requestJSON))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("User-Agent", userAgent)

	res, err := client.Do(req)
	if err != nil {
		if ctx.Err() == context.DeadlineExceeded {
			return "", fmt.Errorf("AI_REQUEST_TIMEOUT")
		}
		return "", err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		// F-305: cap the error-body read at 64 KiB so a hostile or
		// buggy upstream returning a multi-GB error body can't OOM
		// the Go process.
		body, _ := io.ReadAll(io.LimitReader(res.Body, 64*1024))
		return "", fmt.Errorf("HTTP %d: %s", res.StatusCode, string(body))
	}

	// --- Parse Responses SSE stream, emit Anthropic-format events ---
	var contentBlocks []map[string]interface{}
	// Map Responses output_index -> our content block index / accumulating block.
	blockByOutputIdx := make(map[int]map[string]interface{})
	idxByOutputIdx := make(map[int]int)
	nextBlockIndex := 0
	// F-307: parallel maps of *bytes.Buffer so text/input accumulation
	// is O(n) instead of O(n²) string concat per token. Outputs may run
	// in parallel (different output_index) so a single shared buffer
	// doesn't work — keep one per output_index.
	textBufs := make(map[int]*bytes.Buffer)
	inputBufs := make(map[int]*bytes.Buffer)

	scanner := bufio.NewScanner(res.Body)
	scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)

	// F-320: typed payload.
	a.emit("ai:message_start", aiMessageStartEvent{
		Role: "assistant",
	})

	finish := func(stopReason string) (string, error) {
		fullMessage := map[string]interface{}{
			"role":    "assistant",
			"content": contentBlocks,
		}
		resultJSON, err := json.Marshal(fullMessage)
		if err != nil {
			return "", fmt.Errorf("marshal final message: %w", err)
		}
		// F-320: typed payload with json.RawMessage so the
		// already-marshaled message bytes pass through untouched.
		a.emit("ai:done", struct {
			Message    json.RawMessage `json:"message"`
			StopReason string          `json:"stop_reason"`
		}{
			Message:    json.RawMessage(resultJSON),
			StopReason: stopReason,
		})
		return string(resultJSON), nil
	}

	for scanner.Scan() {
		line := scanner.Text()
		if !strings.HasPrefix(line, "data: ") {
			continue
		}
		dataStr := line[6:]
		if strings.TrimSpace(dataStr) == "[DONE]" {
			continue
		}

		var ev responsesStreamEvent
		if err := json.Unmarshal([]byte(dataStr), &ev); err != nil {
			continue
		}

		switch ev.Type {
		case "response.output_item.added":
			var item responsesStreamItem
			if err := json.Unmarshal(ev.Item, &item); err != nil {
				continue
			}
			switch item.Type {
			case "message":
				block := map[string]interface{}{"type": "text", "text": ""}
				blockByOutputIdx[ev.OutputIndex] = block
				idxByOutputIdx[ev.OutputIndex] = nextBlockIndex
				// F-320: typed payload.
				a.emit("ai:block_start", aiBlockStartEvent{
					Index:        nextBlockIndex,
					ContentBlock: block,
				})
				nextBlockIndex++
			case "function_call":
				block := map[string]interface{}{
					"type":  "tool_use",
					"id":    item.CallID,
					"name":  item.Name,
					"input": "",
				}
				blockByOutputIdx[ev.OutputIndex] = block
				idxByOutputIdx[ev.OutputIndex] = nextBlockIndex
				// F-320: typed payload.
				a.emit("ai:block_start", aiBlockStartEvent{
					Index: nextBlockIndex,
					ContentBlock: map[string]interface{}{
						"type": "tool_use",
						"id":   item.CallID,
						"name": item.Name,
					},
				})
				nextBlockIndex++
			}

		case "response.output_text.delta":
			block := blockByOutputIdx[ev.OutputIndex]
			if block == nil {
				continue
			}
			if ev.Delta == "" {
				continue
			}
			// F-307: append to per-block *bytes.Buffer instead of
			// O(n²) string concatenation. Flushed on output_item.done.
			buf, ok := textBufs[ev.OutputIndex]
			if !ok {
				buf = &bytes.Buffer{}
				textBufs[ev.OutputIndex] = buf
			}
			buf.WriteString(ev.Delta)
			// F-320: typed struct + dropped unused fields — see
			// chatCompletionAnthropic for rationale.
			a.emit("ai:token", aiTokenEvent{
				Text:  ev.Delta,
				Index: idxByOutputIdx[ev.OutputIndex],
			})

		case "response.function_call_arguments.delta":
			block := blockByOutputIdx[ev.OutputIndex]
			if block == nil {
				continue
			}
			if ev.Delta == "" {
				continue
			}
			buf, ok := inputBufs[ev.OutputIndex]
			if !ok {
				buf = &bytes.Buffer{}
				inputBufs[ev.OutputIndex] = buf
			}
			buf.WriteString(ev.Delta)
			// F-320: typed payload.
			a.emit("ai:input_json_delta", aiInputJsonDeltaEvent{
				PartialJSON: ev.Delta,
			})

		case "response.output_item.done":
			block := blockByOutputIdx[ev.OutputIndex]
			if block == nil {
				continue
			}
			// F-307: flush per-block buffers once into the block map.
			if buf, ok := textBufs[ev.OutputIndex]; ok {
				if buf.Len() > 0 {
					block["text"] = buf.String()
				}
				delete(textBufs, ev.OutputIndex)
			}
			if buf, ok := inputBufs[ev.OutputIndex]; ok {
				if buf.Len() > 0 {
					inputStr := buf.String()
					if block["type"] == "tool_use" {
						var inputObj map[string]interface{}
						if json.Unmarshal([]byte(inputStr), &inputObj) == nil {
							block["input"] = inputObj
						} else {
							block["input"] = map[string]interface{}{}
						}
					} else {
						block["input"] = inputStr
					}
				}
				delete(inputBufs, ev.OutputIndex)
			}
			contentBlocks = append(contentBlocks, block)
			// F-320: typed payload.
			a.emit("ai:content_block_stop", aiContentBlockStopEvent{
				Index: idxByOutputIdx[ev.OutputIndex],
			})
			delete(blockByOutputIdx, ev.OutputIndex)

		case "response.completed":
			stopReason := "end_turn"
			for _, b := range contentBlocks {
				if b["type"] == "tool_use" {
					stopReason = "tool_use"
					break
				}
			}
			return finish(stopReason)

		case "response.failed", "error":
			// Marshal the typed event back out for the error message; the
			// caller doesn't need the original map shape.
			body, _ := json.Marshal(ev)
			return "", fmt.Errorf("responses stream error: %s", string(body))
		}
	}

	if err := scanner.Err(); err != nil {
		return "", err
	}

	if len(contentBlocks) > 0 {
		return finish("end_turn")
	}

	return "", fmt.Errorf("stream ended without completion")
}

// CancelChatStream cancels the currently active ChatCompletion stream.
func (a *App) CancelChatStream() {
	if c := a.chatCancel.Load(); c != nil {
		(*c)()
	}
}

// ModelInfo represents a model entry from the /v1/models response.
type ModelInfo struct {
	ID          string `json:"id"`
	DisplayName string `json:"display_name"`
}

// FetchModels fetches the available model list. openai/responses hit an
// OpenAI-compatible /models endpoint with a Bearer token; anthropic hits
// /v1/models with the x-api-key + anthropic-version headers, mirroring
// chatCompletionAnthropic's URL and auth handling.
func (a *App) FetchModels(apiKey, baseURL, protocol string, proxyID string) ([]ModelInfo, error) {
	base := strings.TrimRight(baseURL, "/")

	var url string
	if protocol == "anthropic" {
		// Base URL conventionally omits /v1; tolerate legacy configs with it.
		if strings.HasSuffix(base, "/v1") {
			url = base + "/models"
		} else {
			url = base + "/v1/models"
		}
	} else {
		url = base + "/models"
	}

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	if protocol == "anthropic" {
		req.Header.Set("x-api-key", apiKey)
		req.Header.Set("anthropic-version", "2023-06-01")
	} else {
		req.Header.Set("Authorization", "Bearer "+apiKey)
	}
	req.Header.Set("User-Agent", "Terminal")

	// F-208: share the same transport as the LLM clients so the model
	// list call also benefits from the keep-alive pool; the request
	// itself carries its own deadline via the per-request context —
	// generous enough to cover a slow first proxy handshake.
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	req = req.WithContext(ctx)
	client, err := a.llmClientFor(proxyID)
	if err != nil {
		return nil, err
	}
	res, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return nil, err
	}

	if res.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP %d: %s", res.StatusCode, string(body))
	}

	var result struct {
		Data []ModelInfo `json:"data"`
	}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to parse models response: %w", err)
	}
	return result.Data, nil
}


// SkillsStore methods

func (a *App) ListSkills() ([]store.SkillMeta, error) {
	if a.skillsStore == nil {
		return nil, fmt.Errorf("skills store not initialized")
	}
	return a.skillsStore.List()
}

func (a *App) GetSkillBody(name string) (string, error) {
	if a.skillsStore == nil {
		return "", fmt.Errorf("skills store not initialized")
	}
	return a.skillsStore.GetBody(name)
}

func (a *App) GetSkillFile(name, relPath string) (string, error) {
	if a.skillsStore == nil {
		return "", fmt.Errorf("skills store not initialized")
	}
	return a.skillsStore.GetSkillFile(name, relPath)
}

func (a *App) ListSkillFiles(name string) (store.SkillFileList, error) {
	if a.skillsStore == nil {
		return store.SkillFileList{}, fmt.Errorf("skills store not initialized")
	}
	return a.skillsStore.ListSkillFiles(name)
}

func (a *App) SetSkillEnabled(name string, enabled bool) error {
	if a.skillsStore == nil {
		return fmt.Errorf("skills store not initialized")
	}
	return a.skillsStore.SetEnabled(name, enabled)
}

func (a *App) SetSkillLocked(name string, locked bool) error {
	if a.skillsStore == nil {
		return fmt.Errorf("skills store not initialized")
	}
	return a.skillsStore.SetLocked(name, locked)
}

func (a *App) SetSkillSortOrder(name string, order int) error {
	if a.skillsStore == nil {
		return fmt.Errorf("skills store not initialized")
	}
	return a.skillsStore.SetSortOrder(name, order)
}

func (a *App) DeleteSkill(name string) error {
	if a.skillsStore == nil {
		return fmt.Errorf("skills store not initialized")
	}
	return a.skillsStore.Delete(name)
}

func (a *App) ImportSkillFromDir(srcDir string) (string, error) {
	if a.skillsStore == nil {
		return "", fmt.Errorf("skills store not initialized")
	}
	return a.skillsStore.ImportFromDir(srcDir)
}

func (a *App) ImportSkillFromZip(zipPath string) (string, error) {
	if a.skillsStore == nil {
		return "", fmt.Errorf("skills store not initialized")
	}
	return a.skillsStore.ImportFromZip(zipPath)
}

func (a *App) CreateSkill(name, description, body string) error {
	if a.skillsStore == nil {
		return fmt.Errorf("skills store not initialized")
	}
	return a.skillsStore.CreateSkill(name, description, body)
}

func (a *App) SaveSkill(name, description, body string) error {
	if a.skillsStore == nil {
		return fmt.Errorf("skills store not initialized")
	}
	return a.skillsStore.SaveSkill(name, description, body)
}

// RecentStore methods

// F-320: typed payloads for the ai:* Wails events. Replacing the
// per-token `map[string]interface{}` literal with a fixed struct saves
// the alloc per event; the json.Marshal on the Wails side now writes
// the same JSON shape (lowercase keys) so the frontend contract is
// unchanged.
type aiTokenEvent struct {
	Text  string `json:"text"`
	Index int    `json:"index"`
}

type aiBlockStartEvent struct {
	Index        int                    `json:"index"`
	ContentBlock map[string]interface{} `json:"content_block"`
}

type aiContentBlockStopEvent struct {
	Index int `json:"index"`
}

type aiInputJsonDeltaEvent struct {
	PartialJSON string `json:"partial_json"`
}

type aiMessageStartEvent struct {
	Role string `json:"role"`
}

type aiDoneEvent struct {
	Message    map[string]interface{} `json:"message"`
	Usage      map[string]interface{} `json:"usage,omitempty"`
	StopReason string                 `json:"stop_reason"`
}

var finalMsgPool = stdsync.Pool{
	New: func() any {
		b := &bytes.Buffer{}
		b.Grow(4 * 1024)
		return b
	},
}

// F-306: typed SSE shapes for OpenAI Chat Completions. Only the few
// fields the loop reads (delta.content, delta.tool_calls[], choice.finish_reason)
// get decoded; the rest is discarded by the json decoder.
type openaiDeltaToolCall struct {
	Index    *int   `json:"index,omitempty"`
	ID       string `json:"id,omitempty"`
	Function struct {
		Name      string `json:"name,omitempty"`
		Arguments string `json:"arguments,omitempty"`
	} `json:"function"`
}

type openaiStreamDelta struct {
	Content   string                `json:"content"`
	ToolCalls []openaiDeltaToolCall `json:"tool_calls"`
}

type openaiStreamChoice struct {
	Delta        openaiStreamDelta `json:"delta"`
	FinishReason string            `json:"finish_reason"`
}

type openaiStreamEvent struct {
	Choices []openaiStreamChoice `json:"choices"`
}

// F-306: typed SSE shapes for OpenAI Responses events. The wrapper
// captures the discriminator + output_index; nested item fields are
// decoded lazily per branch so we skip the ~99% of fields the loop
// discards.
type responsesStreamItem struct {
	Type   string `json:"type"`
	CallID string `json:"call_id"`
	Name   string `json:"name"`
}

type responsesStreamEvent struct {
	Type        string          `json:"type"`
	OutputIndex int             `json:"output_index"`
	Item        json.RawMessage `json:"item"`
	Delta       string          `json:"delta"`
}

