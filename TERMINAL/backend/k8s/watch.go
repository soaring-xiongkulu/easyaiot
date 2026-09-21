package k8s

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

// WatchEvent 是 apiserver 推给我们的原始事件（object 保持 JSON 原文）。
type WatchEvent struct {
	Type   string          `json:"type"`
	Object json.RawMessage `json:"object"`
}

// startWatchStream 建立 watch 连接并在后台 goroutine 里逐行读取，
// 每收到一条 event 调 cb；stream 结束（EOF/错误/context 取消）时调 onEnd。
// 本函数立即返回，后台读循环由 goroutine 承担。
//
// onReconnect (可空) 在每次 transport 失败触发的重连前调用一次，让上层发一个
// 轻量的「reconnecting」事件而不必动 maps；onEnd 只在终端结束（context 取消 / 干净 EOF）
// 时调用一次，负责真正的清理。这样 StopWatch 在重连退避期间仍能找到 handle 并
// 取消，apiserver 抖动期间也不再每 1s/2s/4s/… 抢 manager mutex + EventsEmit (F-404)。
//
// On non-context errors the goroutine reconnects with exponential
// backoff (1s, 2s, 4s, 8s, max 30s) so an apiserver bounce does not
// silently kill the watch (K8S-02).
func startWatchStream(ctx context.Context, client *http.Client, base, path string,
	cb func(WatchEvent), onEnd func(error), onReconnect func(error), done chan struct{}) error {

	if !strings.HasPrefix(path, "/") {
		return fmt.Errorf("path must start with /: %q", path)
	}
	go runWatchLoop(ctx, client, base, path, cb, onEnd, onReconnect, done)
	return nil
}

func runWatchLoop(ctx context.Context, client *http.Client, base, path string,
	cb func(WatchEvent), onEnd func(error), onReconnect func(error), done chan struct{}) {
	defer close(done)
	backoff := time.Second
	const maxBackoff = 30 * time.Second
	for {
		err := runOneWatch(ctx, client, base, path, cb)
		if ctx.Err() != nil {
			onEnd(ctx.Err())
			return
		}
		if err == nil {
			// Clean EOF (server closed the stream). Surface once and stop —
			// the original contract is "stream ended → onEnd then exit".
			// An apiserver bounce shows up as a non-nil err and triggers
			// the backoff branch below (K8S-02).
			onEnd(nil)
			return
		}
		// Transport / scanner error — likely apiserver bounce. Surface a
		// transient reconnect signal (if wired) and back off; onEnd is
		// reserved for the terminal case so the manager doesn't drop the
		// handle from its map on every reconnect attempt (F-404).
		if onReconnect != nil {
			onReconnect(err)
		}
		select {
		case <-ctx.Done():
			return
		case <-time.After(backoff):
		}
		if backoff < maxBackoff {
			backoff *= 2
			if backoff > maxBackoff {
				backoff = maxBackoff
			}
		}
	}
}

func runOneWatch(ctx context.Context, client *http.Client, base, path string,
	cb func(WatchEvent)) error {
	req, err := http.NewRequestWithContext(ctx, "GET", base+path, nil)
	if err != nil {
		return err
	}
	req.Header.Set("Accept", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	if resp.StatusCode >= 400 {
		body := make([]byte, 512)
		n, _ := resp.Body.Read(body)
		resp.Body.Close()
		return fmt.Errorf("watch HTTP %d: %s", resp.StatusCode, string(body[:n]))
	}
	defer resp.Body.Close()
	scanner := bufio.NewScanner(resp.Body)
	// F-412: most watch lines are < 2 KiB; start at 4 KiB and let
	// bufio.Scanner grow on demand up to 4 MiB. The previous 64 KiB
	// initial cap pinned ~80 MiB across 20 watches even on idle clusters.
	scanner.Buffer(make([]byte, 0, 4*1024), 4*1024*1024)
	for scanner.Scan() {
		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}
		var ev WatchEvent
		if err := json.Unmarshal(line, &ev); err != nil {
			continue
		}
		cb(ev)
	}
	return scanner.Err()
}
