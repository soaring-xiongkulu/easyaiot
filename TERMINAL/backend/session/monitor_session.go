package session

import (
	"encoding/json"
	"fmt"
	"math"
	"net"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"golang.org/x/crypto/ssh"
)

type cpuSample struct{ total, idle uint64 }
type netSample struct{ rx, tx uint64 }

// Monitor metrics poll interval in seconds. Network byte rates are computed
// from deltas over this window and divided by it to yield bytes/second.
const performancePollSec = 3

type monitorState struct {
	lastCpuTotal  uint64
	lastCpuIdle   uint64
	lastCpuUser   uint64
	lastCpuSystem uint64
	lastCpuIowait uint64
	lastNetRx     uint64
	lastNetTx     uint64
	hasPrev       bool

	// Per-core and per-interface deltas for the expandable detail lists.
	lastPerCpu       map[int]cpuSample
	lastNetPerIface  map[string]netSample

	// Separate counters for collectProcesses so overview mode
	// (performance + processes each tick) cannot corrupt deltas.
	lastProcCpuTotal uint64
	lastProcCpuIdle  uint64
	hasProcPrev      bool
}

type PortInfo struct {
	Protocol  string `json:"protocol"`
	LocalAddr string `json:"localAddr"`
	State     string `json:"state"`
	Process   string `json:"process"`
}

type DiskInfo struct {
	Name       string `json:"name"`
	Type       string `json:"type"`
	Size       string `json:"size"`
	MountPoint string `json:"mountPoint"`
	Used       string `json:"used"`
	Total      string `json:"total"`
	Usage      int    `json:"usage"`
	Media      string `json:"media"`
	FSType     string `json:"fsType"`
	UUID       string `json:"uuid"`
	Vendor     string `json:"vendor"`
	Model      string `json:"model"`
}

type dfEntry struct{ Used, Total, Mount string; Usage int }

type NetCardInfo struct {
	Name       string   `json:"name"`
	State      string   `json:"state"`
	MAC        string   `json:"mac"`
	Speed      string   `json:"speed"`
	Type       string   `json:"type"`
	BondMaster string   `json:"bondMaster"`
	BondSlaves []string `json:"bondSlaves"`
	IPAddrs    []string `json:"ipAddrs"`
}

type MonitorSession struct {
	baseSession
	client    *ssh.Client
	config    ConnectionConfig
	ticker    *time.Ticker
	quit      chan struct{}
	quitOnce  sync.Once
	state     monitorState
	activeTab string
	paused    bool
	mu        sync.RWMutex
}

func NewMonitorSession(id string) *MonitorSession {
	return &MonitorSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "monitor",
			status:      StatusDisconnected,
		},
		quit:      make(chan struct{}),
		activeTab: "performance",
	}
}

func (s *MonitorSession) SetActiveTab(tab string) {
	s.mu.Lock()
	s.activeTab = tab
	s.mu.Unlock()
}

func (s *MonitorSession) SetPaused(paused bool) {
	s.mu.Lock()
	s.paused = paused
	s.mu.Unlock()
}

func (s *MonitorSession) IsPaused() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.paused
}

func (s *MonitorSession) ActiveTab() string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.activeTab
}

func (s *MonitorSession) Connect(config ConnectionConfig) error {
	s.setStatus(StatusConnecting)
	s.config = config
	s.title = fmt.Sprintf("%s@%s", config.User, config.Host)

	authMethods, cleanup, err := buildAuthMethodsWithCleanup(config)
	if err != nil {
		s.setStatus(StatusError)
		return err
	}
	defer cleanup()

	clientConfig := &ssh.ClientConfig{
		User:            config.User,
		Auth:            authMethods,
		Timeout:         30 * time.Second,
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
		Config: sshAlgorithms(),
	}

	addr := net.JoinHostPort(config.Host, strconv.Itoa(config.Port))
	client, err := dialSSHTCP(addr, clientConfig, config.Proxy)
	if err != nil {
		s.setStatus(StatusError)
		return fmt.Errorf("ssh dial: %w", err)
	}

	s.client = client
	s.setStatus(StatusConnected)

	go s.pushSystemInfo()

	s.ticker = time.NewTicker(performancePollSec * time.Second)
	go s.pollLoop()

	return nil
}

func (s *MonitorSession) pushSystemInfo() {
	info := s.collectSystemInfo()
	if info != nil {
		data, _ := json.Marshal(map[string]interface{}{
			"type":   "system",
			"system": info,
		})
		s.emitData(data)
	}
}

func (s *MonitorSession) collectSystemInfo() map[string]interface{} {
	session, err := s.client.NewSession()
	if err != nil {
		return nil
	}
	defer session.Close()

	script := `cat /etc/os-release 2>/dev/null | grep -E '^(PRETTY_NAME|VERSION_ID)=' || true; echo "---"; uname -r; echo "---"; hostname; echo "---"; readlink -f /etc/localtime 2>/dev/null | sed 's|/usr/share/zoneinfo/||' || date +%Z; echo "---"; uname -m; echo "---"; cat /proc/cpuinfo 2>/dev/null | grep 'model name' | head -1 || true; echo "---"; nproc; echo "---"; cat /proc/cpuinfo 2>/dev/null | grep 'cpu MHz' | head -1 || true; echo "---"; awk '/MemTotal:/{print $2}' /proc/meminfo; echo "---"; df -h / 2>/dev/null | awk 'NR==2{print $2}'; echo "---"; ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+'; echo "---"; cat /proc/uptime 2>/dev/null | awk '{print int($1)}'; echo "---"; whoami 2>/dev/null || true; echo "---"; date +%s`
	out, err := session.CombinedOutput(script)
	if err != nil {
		return nil
	}

	parts := strings.Split(string(out), "---")
	osInfo := strings.TrimSpace(safeIndex(parts, 0))
	kernel := strings.TrimSpace(safeIndex(parts, 1))
	hostname := strings.TrimSpace(safeIndex(parts, 2))
	timezone := strings.TrimSpace(safeIndex(parts, 3))
	arch := strings.TrimSpace(safeIndex(parts, 4))
	cpuModel := strings.TrimSpace(safeIndex(parts, 5))
	cpuModel = strings.TrimPrefix(cpuModel, "model name\t:")
	cpuModel = strings.TrimSpace(cpuModel)
	coresStr := strings.TrimSpace(safeIndex(parts, 6))
	cores, _ := strconv.Atoi(coresStr)
	cpuFreq := strings.TrimSpace(safeIndex(parts, 7))
	cpuFreq = strings.TrimPrefix(cpuFreq, "cpu MHz\t:")
	cpuFreq = strings.TrimSpace(cpuFreq)
	memTotalKBStr := strings.TrimSpace(safeIndex(parts, 8))
	memTotalKB, _ := strconv.ParseFloat(memTotalKBStr, 64)
	diskTotal := strings.TrimSpace(safeIndex(parts, 9))
	localIP := strings.TrimSpace(safeIndex(parts, 10))
	uptimeSecStr := strings.TrimSpace(safeIndex(parts, 11))
	uptimeSec, _ := strconv.ParseInt(uptimeSecStr, 10, 64)
	loginUser := strings.TrimSpace(safeIndex(parts, 12))
	epochSecStr := strings.TrimSpace(safeIndex(parts, 13))
	epochSec, _ := strconv.ParseInt(epochSecStr, 10, 64)

	osName := "Linux"
	versionID := ""
	for _, line := range strings.Split(osInfo, "\n") {
		if strings.HasPrefix(line, "PRETTY_NAME=") {
			osName = strings.Trim(strings.TrimPrefix(line, "PRETTY_NAME="), `"`)
		}
		if strings.HasPrefix(line, "VERSION_ID=") {
			versionID = strings.Trim(strings.TrimPrefix(line, "VERSION_ID="), `"`)
		}
	}

	return map[string]interface{}{
		"os":        osName,
		"version":   versionID,
		"kernel":    kernel,
		"hostname":  hostname,
		"timezone":  timezone,
		"arch":      arch,
		"cpuModel":  cpuModel,
		"cores":     cores,
		"cpuFreq":   cpuFreq,
		"memTotal":  roundFloat(memTotalKB/1024/1024, 2),
		"diskTotal": diskTotal,
		"localIP":   localIP,
		"uptimeSec": uptimeSec,
		"user":      loginUser,
		"epochSec":  epochSec,
	}
}

func safeIndex(arr []string, idx int) string {
	if idx < len(arr) {
		return arr[idx]
	}
	return ""
}

func (s *MonitorSession) pollLoop() {
	sysTicks := 0
	for {
		select {
		case <-s.quit:
			return
		case <-s.ticker.C:
			s.mu.RLock()
			tab := s.activeTab
			paused := s.paused
			s.mu.RUnlock()

			switch tab {
			case "performance":
				if !paused {
					s.collectPerformance()
				}
			case "processes":
				if !paused {
					s.collectProcesses()
				}
			case "overview":
				// Compact sidebar: gauges/network + process list in one poll tick.
				if !paused {
					s.collectPerformance()
					s.collectProcesses()
				}
			}

			// System info is otherwise one-shot at connect; refresh it
			// periodically (every 30s) so uptime and the other identity fields
			// keep updating instead of freezing.
			sysTicks++
			if sysTicks%(30/performancePollSec) == 0 {
				s.pushSystemInfo()
			}
		}
	}
}

func (s *MonitorSession) collectPerformance() {
	session, err := s.client.NewSession()
	if err != nil {
		return
	}
	defer session.Close()

	script := `exec 2>/dev/null
cpu_line=$(head -1 /proc/stat)
cpu_user=$(echo "$cpu_line" | awk '{print $2+$3}')
cpu_system=$(echo "$cpu_line" | awk '{print $4}')
cpu_idle=$(echo "$cpu_line" | awk '{print $5}')
cpu_iowait=$(echo "$cpu_line" | awk '{print $6}')
cpu_total=$(echo "$cpu_line" | awk '{print $2+$3+$4+$5+$6+$7+$8+$9}')

mem_total=$(awk '/MemTotal:/{print $2}' /proc/meminfo)
mem_avail=$(awk '/MemAvailable:/{print $2}' /proc/meminfo)
[ -z "$mem_avail" ] && mem_avail=$(awk '/MemFree:/{print $2}' /proc/meminfo)
mem_cached=$(awk '/^Cached:/{print $2}' /proc/meminfo)
[ -z "$mem_cached" ] && mem_cached=0
mem_buffers=$(awk '/^Buffers:/{print $2}' /proc/meminfo)
[ -z "$mem_buffers" ] && mem_buffers=0
swap_total=$(awk '/SwapTotal:/{print $2}' /proc/meminfo)
swap_free=$(awk '/SwapFree:/{print $2}' /proc/meminfo)
[ -z "$swap_total" ] && swap_total=0
[ -z "$swap_free" ] && swap_free=0

disk_total=$(df -h / | awk 'NR==2{print $2}')
disk_used=$(df -h / | awk 'NR==2{print $3}')
disk_usage=$(df -h / | awk 'NR==2{gsub(/%/,""); print $5}')

# Sum all non-lo interfaces
net_rx=$(awk '/^[ ]*[^ ]+:/ && !/lo:/{rx+=$2; tx+=$10} END{print rx+0}' /proc/net/dev)
net_tx=$(awk '/^[ ]*[^ ]+:/ && !/lo:/{rx+=$2; tx+=$10} END{print tx+0}' /proc/net/dev)
[ -z "$net_rx" ] && net_rx=0
[ -z "$net_tx" ] && net_tx=0

handles=$(awk '{print $1}' /proc/sys/fs/file-nr)
[ -z "$handles" ] && handles=0

proc_count=$(ps -e | wc -l)
proc_count=$((proc_count > 0 ? proc_count - 1 : 0))

cores=$(nproc || echo 1)

loadavg=$(cat /proc/loadavg 2>/dev/null | awk '{print $1,$2,$3}')
[ -z "$loadavg" ] && loadavg="0 0 0"

printf '{"cpu_total":%s,"cpu_idle":%s,"cpu_user":%s,"cpu_system":%s,"cpu_iowait":%s,"cores":%s,"processes":%s,"mem_total":%s,"mem_avail":%s,"mem_cached":%s,"mem_buffers":%s,"swap_total":%s,"swap_free":%s,"disk_total":"%s","disk_used":"%s","disk_usage":%s,"net_rx":%s,"net_tx":%s,"handles":%s,"load1":%s,"load5":%s,"load15":%s}\n' \
  "$cpu_total" "$cpu_idle" "$cpu_user" "$cpu_system" "$cpu_iowait" "$cores" "$proc_count" \
  "$mem_total" "$mem_avail" "$mem_cached" "$mem_buffers" \
  "$swap_total" "$swap_free" \
  "${disk_total:-}" "${disk_used:-}" "${disk_usage:-0}" \
  "$net_rx" "$net_tx" "$handles" \
  $loadavg
echo "---CORE---"
grep '^cpu[0-9]' /proc/stat || true
echo "---NET---"
awk 'NR>2{split($1,a,":"); n=a[1]; if(n!="lo") print n,$2,$10}' /proc/net/dev
`

	out, err := session.Output(script)
	if err != nil {
		return
	}

	// Peel off the "--CORE--"/"--NET--" detail sections so the leading JSON
	// can be unmarshalled on its own.
	outStr := string(out)
	corePart := ""
	netPart := ""
	if idx := strings.Index(outStr, "---CORE---"); idx >= 0 {
		rest := outStr[idx:]
		corePart = rest[len("---CORE---"):]
		out = []byte(outStr[:idx])
		if idx2 := strings.Index(rest, "---NET---"); idx2 >= 0 {
			corePart = rest[len("---CORE---"):idx2]
			netPart = rest[idx2+len("---NET---"):]
		}
	}

	type rawMetrics struct {
		CpuTotal   uint64  `json:"cpu_total"`
		CpuIdle    uint64  `json:"cpu_idle"`
		CpuUser    uint64  `json:"cpu_user"`
		CpuSystem  uint64  `json:"cpu_system"`
		CpuIowait  uint64  `json:"cpu_iowait"`
		Cores      int     `json:"cores"`
		Processes  int     `json:"processes"`
		MemTotal   uint64  `json:"mem_total"`
		MemAvail   uint64  `json:"mem_avail"`
		MemCached  uint64  `json:"mem_cached"`
		MemBuffers uint64  `json:"mem_buffers"`
		SwapTotal  uint64  `json:"swap_total"`
		SwapFree   uint64  `json:"swap_free"`
		DiskTotal  string  `json:"disk_total"`
		DiskUsed   string  `json:"disk_used"`
		DiskUsage  int     `json:"disk_usage"`
		NetRx      uint64  `json:"net_rx"`
		NetTx      uint64  `json:"net_tx"`
		Handles    uint64  `json:"handles"`
		Load1      float64 `json:"load1"`
		Load5      float64 `json:"load5"`
		Load15     float64 `json:"load15"`
	}

	var m rawMetrics
	if err := json.Unmarshal(out, &m); err != nil {
		return
	}

	// CPU usage: need delta between two samples (guard against uint64 underflow)
	cpuUsage := 0.0
	cpuUserPct := 0.0
	cpuSystemPct := 0.0
	cpuIowaitPct := 0.0
	if s.state.hasPrev {
		if totalDiff, ok := uintDelta(m.CpuTotal, s.state.lastCpuTotal); ok && totalDiff > 0 {
			if idleDiff, ok := uintDelta(m.CpuIdle, s.state.lastCpuIdle); ok {
				cpuUsage = clampPct((float64(totalDiff) - float64(idleDiff)) / float64(totalDiff) * 100)
			}
			if userDiff, ok := uintDelta(m.CpuUser, s.state.lastCpuUser); ok {
				cpuUserPct = clampPct(float64(userDiff) / float64(totalDiff) * 100)
			}
			if sysDiff, ok := uintDelta(m.CpuSystem, s.state.lastCpuSystem); ok {
				cpuSystemPct = clampPct(float64(sysDiff) / float64(totalDiff) * 100)
			}
			if ioDiff, ok := uintDelta(m.CpuIowait, s.state.lastCpuIowait); ok {
				cpuIowaitPct = clampPct(float64(ioDiff) / float64(totalDiff) * 100)
			}
		}
	}

	// Network rate (bytes per second, over the poll interval)
	netRxRate := uint64(0)
	netTxRate := uint64(0)
	if s.state.hasPrev {
		if m.NetRx >= s.state.lastNetRx {
			netRxRate = uint64(math.Round(float64(m.NetRx-s.state.lastNetRx) / performancePollSec))
		}
		if m.NetTx >= s.state.lastNetTx {
			netTxRate = uint64(math.Round(float64(m.NetTx-s.state.lastNetTx) / performancePollSec))
		}
	}

	memTotalGB := float64(m.MemTotal) / 1024 / 1024
	memUsedGB := float64(m.MemTotal-m.MemAvail) / 1024 / 1024
	memFreeGB := float64(m.MemAvail) / 1024 / 1024
	memUsage := 0.0
	if m.MemTotal > 0 {
		memUsage = float64(m.MemTotal-m.MemAvail) / float64(m.MemTotal) * 100
	}
	memCachedGB := float64(m.MemCached) / 1024 / 1024
	memBuffersGB := float64(m.MemBuffers) / 1024 / 1024

	swapTotalGB := float64(m.SwapTotal) / 1024 / 1024
	swapUsedGB := float64(m.SwapTotal-m.SwapFree) / 1024 / 1024
	swapUsage := 0.0
	if m.SwapTotal > 0 {
		swapUsage = float64(m.SwapTotal-m.SwapFree) / float64(m.SwapTotal) * 100
	}

	// "Total CPU" style metric ≈ usage × cores (as HexHub shows)
	cpuTotalPct := cpuUsage
	if m.Cores > 0 {
		cpuTotalPct = cpuUsage * float64(m.Cores)
	}

	payload := map[string]interface{}{
		"type": "performance",
		"cpu": map[string]interface{}{
			"usage":     roundFloat(cpuUsage, 1),
			"total":     roundFloat(cpuTotalPct, 1),
			"user":      roundFloat(cpuUserPct, 1),
			"system":    roundFloat(cpuSystemPct, 1),
			"iowait":    roundFloat(cpuIowaitPct, 1),
			"cores":     m.Cores,
			"processes": m.Processes,
			"handles":   m.Handles,
			"load1":     roundFloat(m.Load1, 2),
			"load5":     roundFloat(m.Load5, 2),
			"load15":    roundFloat(m.Load15, 2),
		},
		"memory": map[string]interface{}{
			"total":   roundFloat(memTotalGB, 2),
			"used":    roundFloat(memUsedGB, 2),
			"free":    roundFloat(memFreeGB, 2),
			"usage":   roundFloat(memUsage, 1),
			"cached":  roundFloat(memCachedGB, 2),
			"buffers": roundFloat(memBuffersGB, 2),
		},
		"swap": map[string]interface{}{
			"total": roundFloat(swapTotalGB, 2),
			"used":  roundFloat(swapUsedGB, 2),
			"usage": roundFloat(swapUsage, 1),
		},
		"disk": map[string]interface{}{
			"total": m.DiskTotal,
			"used":  m.DiskUsed,
			"usage": m.DiskUsage,
		},
		"network": map[string]interface{}{
			"rx":      netRxRate,
			"tx":      netTxRate,
			"rxTotal": m.NetRx,
			"txTotal": m.NetTx,
		},
	}

	if cpus := s.computePerCore(corePart); len(cpus) > 0 {
		payload["cpus"] = cpus
	}
	if nets := s.computePerNic(netPart); len(nets) > 0 {
		payload["nets"] = nets
	}

	jsonData, _ := json.Marshal(payload)
	s.emitData(jsonData)

	// Save state for next delta calculation
	s.state.lastCpuTotal = m.CpuTotal
	s.state.lastCpuIdle = m.CpuIdle
	s.state.lastCpuUser = m.CpuUser
	s.state.lastCpuSystem = m.CpuSystem
	s.state.lastCpuIowait = m.CpuIowait
	s.state.lastNetRx = m.NetRx
	s.state.lastNetTx = m.NetTx
	s.state.hasPrev = true
}

// computePerCore turns the "---CORE---" subsection (one /proc/stat cpuN line
// per core) into per-core usage percentages using delta-with-previous-sample.
func (s *MonitorSession) computePerCore(corePart string) []map[string]interface{} {
	if s.state.lastPerCpu == nil {
		s.state.lastPerCpu = map[int]cpuSample{}
	}
	next := map[int]cpuSample{}
	usage := map[int]float64{}
	for _, line := range strings.Split(corePart, "\n") {
		line = strings.TrimSpace(line)
		if !strings.HasPrefix(line, "cpu") {
			continue
		}
		f := strings.Fields(line)
		if len(f) < 9 {
			continue
		}
		core, err := strconv.Atoi(strings.TrimPrefix(f[0], "cpu"))
		if err != nil {
			continue
		}
		var total uint64
		for i := 1; i <= 8; i++ {
			n, _ := strconv.ParseUint(f[i], 10, 64)
			total += n
		}
		idle, _ := strconv.ParseUint(f[4], 10, 64)
		if prev, ok := s.state.lastPerCpu[core]; ok && total >= prev.total {
			if diff := total - prev.total; diff > 0 {
				idleDiff := uint64(0)
				if idle >= prev.idle {
					idleDiff = idle - prev.idle
				}
				if idleDiff > diff {
					idleDiff = diff
				}
				usage[core] = clampPct(float64(diff-idleDiff) / float64(diff) * 100)
			}
		}
		next[core] = cpuSample{total: total, idle: idle}
	}
	s.state.lastPerCpu = next

	keys := make([]int, 0, len(usage))
	for k := range usage {
		keys = append(keys, k)
	}
	sort.Ints(keys)
	result := make([]map[string]interface{}, 0, len(keys))
	for _, k := range keys {
		result = append(result, map[string]interface{}{"core": k, "usage": roundFloat(usage[k], 1)})
	}
	return result
}

// computePerNic turns the "---NET---" subsection ("name rx rx tx") into
// per-interface byte counters and rates, skipping loopback.
func (s *MonitorSession) computePerNic(netPart string) []map[string]interface{} {
	if s.state.lastNetPerIface == nil {
		s.state.lastNetPerIface = map[string]netSample{}
	}
	type netStats struct {
		rateRx, rateTx, rxTotal, txTotal uint64
	}
	items := map[string]netStats{}
	next := map[string]netSample{}
	for _, line := range strings.Split(netPart, "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		f := strings.Fields(line)
		if len(f) < 3 {
			continue
		}
		name := f[0]
		rx, _ := strconv.ParseUint(f[1], 10, 64)
		tx, _ := strconv.ParseUint(f[2], 10, 64)
		rateRx, rateTx := uint64(0), uint64(0)
		if prev, ok := s.state.lastNetPerIface[name]; ok {
			if rx >= prev.rx {
				rateRx = uint64(math.Round(float64(rx-prev.rx) / performancePollSec))
			}
			if tx >= prev.tx {
				rateTx = uint64(math.Round(float64(tx-prev.tx) / performancePollSec))
			}
		}
		next[name] = netSample{rx: rx, tx: tx}
		items[name] = netStats{rateRx: rateRx, rateTx: rateTx, rxTotal: rx, txTotal: tx}
	}
	s.state.lastNetPerIface = next

	// Stable order: sort NIC names alphabetically for the detail list.
	names := make([]string, 0, len(items))
	for n := range items {
		names = append(names, n)
	}
	sort.Strings(names)
	result := make([]map[string]interface{}, 0, len(names))
	for _, name := range names {
		st := items[name]
		result = append(result, map[string]interface{}{
			"name": name, "rx": st.rateRx, "tx": st.rateTx, "rxTotal": st.rxTotal, "txTotal": st.txTotal,
		})
	}
	return result
}

func (s *MonitorSession) collectProcesses() {
	session, err := s.client.NewSession()
	if err != nil {
		return
	}
	defer session.Close()

	script := `exec 2>/dev/null
cpu_line=$(head -1 /proc/stat)
cpu_total=$(echo "$cpu_line" | awk '{print $2+$3+$4+$5+$6+$7+$8+$9}')
cpu_idle=$(echo "$cpu_line" | awk '{print $5}')
mem_total=$(awk '/MemTotal:/{print $2}' /proc/meminfo)
mem_avail=$(awk '/MemAvailable:/{print $2}' /proc/meminfo)
[ -z "$mem_avail" ] && mem_avail=$(awk '/MemFree:/{print $2}' /proc/meminfo)
mem_cached=$(awk '/^Cached:/{print $2}' /proc/meminfo)
[ -z "$mem_cached" ] && mem_cached=0
mem_buffers=$(awk '/^Buffers:/{print $2}' /proc/meminfo)
[ -z "$mem_buffers" ] && mem_buffers=0
loadavg=$(cat /proc/loadavg 2>/dev/null | awk '{print $1,$2,$3}')
[ -z "$loadavg" ] && loadavg="0 0 0"
proc_count=$(ps -e | wc -l)
proc_count=$((proc_count > 0 ? proc_count - 1 : 0))
cores=$(nproc || echo 1)
ps -eo pid,ppid,user,stat,pcpu,pmem,comm,args --sort=-pcpu | tail -n +2 | head -30 || true
echo "---SUMMARY---"
printf '{"cpu_total":%s,"cpu_idle":%s,"cores":%s,"proc_count":%s,"mem_total":%s,"mem_avail":%s,"mem_cached":%s,"mem_buffers":%s,"load1":%s,"load5":%s,"load15":%s}\n' \
  "$cpu_total" "$cpu_idle" "$cores" "$proc_count" \
  "$mem_total" "$mem_avail" "$mem_cached" "$mem_buffers" \
  $loadavg`

	out, err := session.Output(script)
	if err != nil {
		return
	}

	output := string(out)
	parts := strings.Split(output, "---SUMMARY---\n")
	procPart := strings.TrimSpace(parts[0])

	// Parse summary
	summary := map[string]interface{}{}
	if len(parts) > 1 {
		summaryJSON := strings.TrimSpace(parts[1])
		var rawSummary struct {
			CpuTotal   uint64  `json:"cpu_total"`
			CpuIdle    uint64  `json:"cpu_idle"`
			Cores      int     `json:"cores"`
			ProcCount  int     `json:"proc_count"`
			MemTotal   uint64  `json:"mem_total"`
			MemAvail   uint64  `json:"mem_avail"`
			MemCached  uint64  `json:"mem_cached"`
			MemBuffers uint64  `json:"mem_buffers"`
			Load1      float64 `json:"load1"`
			Load5      float64 `json:"load5"`
			Load15     float64 `json:"load15"`
		}
		if err := json.Unmarshal([]byte(summaryJSON), &rawSummary); err == nil {
			// Use dedicated process-tab counters — never touch performance state.
			cpuUsage := 0.0
			if s.state.hasProcPrev {
				if totalDiff, ok := uintDelta(rawSummary.CpuTotal, s.state.lastProcCpuTotal); ok && totalDiff > 0 {
					if idleDiff, ok := uintDelta(rawSummary.CpuIdle, s.state.lastProcCpuIdle); ok {
						cpuUsage = clampPct((float64(totalDiff) - float64(idleDiff)) / float64(totalDiff) * 100)
					}
				}
			}

			memTotalGB := float64(rawSummary.MemTotal) / 1024 / 1024
			memUsedGB := float64(rawSummary.MemTotal-rawSummary.MemAvail) / 1024 / 1024
			memFreeGB := float64(rawSummary.MemAvail) / 1024 / 1024
			memUsage := 0.0
			if rawSummary.MemTotal > 0 {
				memUsage = float64(rawSummary.MemTotal-rawSummary.MemAvail) / float64(rawSummary.MemTotal) * 100
			}

			summary["cpu"] = map[string]interface{}{
				"usage":     roundFloat(cpuUsage, 1),
				"cores":     rawSummary.Cores,
				"processes": rawSummary.ProcCount,
				"load1":     roundFloat(rawSummary.Load1, 2),
				"load5":     roundFloat(rawSummary.Load5, 2),
				"load15":    roundFloat(rawSummary.Load15, 2),
			}
			summary["memory"] = map[string]interface{}{
				"total":   roundFloat(memTotalGB, 2),
				"used":    roundFloat(memUsedGB, 2),
				"free":    roundFloat(memFreeGB, 2),
				"usage":   roundFloat(memUsage, 1),
				"cached":  roundFloat(float64(rawSummary.MemCached)/1024/1024, 2),
				"buffers": roundFloat(float64(rawSummary.MemBuffers)/1024/1024, 2),
			}

			s.state.lastProcCpuTotal = rawSummary.CpuTotal
			s.state.lastProcCpuIdle = rawSummary.CpuIdle
			s.state.hasProcPrev = true
		}
	}

	// Parse processes
	processes := []map[string]interface{}{}
	for _, line := range strings.Split(procPart, "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) < 8 {
			continue
		}
		pid, _ := strconv.Atoi(parts[0])
		ppid, _ := strconv.Atoi(parts[1])
		cpu, _ := strconv.ParseFloat(parts[4], 64)
		mem, _ := strconv.ParseFloat(parts[5], 64)
		processes = append(processes, map[string]interface{}{
			"pid":   pid,
			"ppid":  ppid,
			"user":  parts[2],
			"state": parts[3],
			"cpu":   cpu,
			"mem":   mem,
			"name":  parts[6],
			"cmd":   strings.Join(parts[7:], " "),
		})
	}

	payload := map[string]interface{}{
		"type":      "processes",
		"processes": processes,
	}
	if len(summary) > 0 {
		payload["summary"] = summary
	}

	jsonData, _ := json.Marshal(payload)
	s.emitData(jsonData)
}

func (s *MonitorSession) GetProcessDetail(pid int) (map[string]interface{}, error) {
	session, err := s.client.NewSession()
	if err != nil {
		return nil, err
	}
	defer session.Close()

	script := fmt.Sprintf(`exec 2>/dev/null
PID=%d

# Basic info from status
cat /proc/$PID/status 2>/dev/null | grep -E '^(Pid|PPid|Name|State|Threads|VmRSS|VmSize|VmPeak|VmData|VmStk|VmExe|VmLib|voluntary_ctxt_switches|nonvoluntary_ctxt_switches):' || true
echo "---EXE---"
readlink -f /proc/$PID/exe 2>/dev/null || echo '-'
echo "---CWD---"
readlink -f /proc/$PID/cwd 2>/dev/null || echo '-'
echo "---CMDLINE---"
cat /proc/$PID/cmdline 2>/dev/null | tr '\0' ' '
echo "---FD---"
total=0; files=0; sockets=0; pipes=0; anons=0; devs=0; others=0
for fd in /proc/$PID/fd/[0-9]*; do
    [ -L "$fd" ] || continue
    target=$(readlink "$fd" 2>/dev/null)
    total=$((total + 1))
    case "$target" in
        socket:*) sockets=$((sockets + 1)) ;;
        pipe:*) pipes=$((pipes + 1)) ;;
        anon_inode:*) anons=$((anons + 1)) ;;
        /dev/*) devs=$((devs + 1)) ;;
        /*) files=$((files + 1)) ;;
        *) others=$((others + 1)) ;;
    esac
done
printf '{"total":%%d,"files":%%d,"sockets":%%d,"pipes":%%d,"anons":%%d,"devs":%%d,"others":%%d}\n' $total $files $sockets $pipes $anons $devs $others
echo "---IO---"
cat /proc/$PID/io 2>/dev/null | grep -E '^(rchar|wchar|syscr|syscw|read_bytes|write_bytes):' || true
echo "---CPU---"
awk '{print $14+$15}' /proc/$PID/stat 2>/dev/null || echo '0'
echo "---STARTTIME---"
start_epoch=$(stat -c %%Y /proc/$PID 2>/dev/null)
date -d "@$start_epoch" "+%%Y-%%m-%%d %%H:%%M:%%S" 2>/dev/null || echo '-'`, pid)

	out, err := session.Output(script)
	if err != nil {
		return nil, fmt.Errorf("query process detail: %w", err)
	}

	output := string(out)
	sections := strings.Split(output, "---EXE---\n")
	statusPart := strings.TrimSpace(sections[0])
	rest := ""
	if len(sections) > 1 {
		rest = sections[1]
	}

	result := map[string]interface{}{
		"pid": pid,
	}

	// Parse status
	for _, line := range strings.Split(statusPart, "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, ":", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.TrimSpace(parts[0])
		val := strings.TrimSpace(parts[1])
		switch key {
		case "Pid":
			result["pid"], _ = strconv.Atoi(val)
		case "PPid":
			result["ppid"], _ = strconv.Atoi(val)
		case "Name":
			result["name"] = val
		case "State":
			result["state"] = val
		case "Threads":
			result["threads"], _ = strconv.Atoi(val)
		case "VmRSS":
			result["vmRss"] = val
		case "VmSize":
			result["vmSize"] = val
		case "VmPeak":
			result["vmPeak"] = val
		case "VmData":
			result["vmData"] = val
		case "VmStk":
			result["vmStk"] = val
		case "VmExe":
			result["vmExe"] = val
		case "VmLib":
			result["vmLib"] = val
		case "voluntary_ctxt_switches":
			result["voluntaryCtxSwitches"], _ = strconv.Atoi(val)
		case "nonvoluntary_ctxt_switches":
			result["nonvoluntaryCtxSwitches"], _ = strconv.Atoi(val)
		}
	}

	// Parse rest sections
	if rest != "" {
		sections2 := strings.Split(rest, "---CWD---\n")
		result["exe"] = strings.TrimSpace(strings.Split(sections2[0], "---CMDLINE---")[0])

		if len(sections2) > 1 {
			sections3 := strings.Split(sections2[1], "---CMDLINE---\n")
			result["cwd"] = strings.TrimSpace(sections3[0])

			if len(sections3) > 1 {
				sections4 := strings.Split(sections3[1], "---FD---\n")
				result["cmdline"] = strings.TrimSpace(sections4[0])

				if len(sections4) > 1 {
					sections5 := strings.Split(sections4[1], "---IO---\n")
					fdJSON := strings.TrimSpace(sections5[0])
					var fdStats map[string]interface{}
					_ = json.Unmarshal([]byte(fdJSON), &fdStats)
					result["fd"] = fdStats

					if len(sections5) > 1 {
						sections6 := strings.Split(sections5[1], "---CPU---\n")
						ioPart := strings.TrimSpace(sections6[0])
						io := map[string]interface{}{}
						for _, line := range strings.Split(ioPart, "\n") {
							line = strings.TrimSpace(line)
							if line == "" {
								continue
							}
							parts := strings.SplitN(line, ":", 2)
							if len(parts) == 2 {
								io[strings.TrimSpace(parts[0])], _ = strconv.ParseUint(strings.TrimSpace(parts[1]), 10, 64)
							}
						}
						result["io"] = io

						if len(sections6) > 1 {
							sections7 := strings.Split(sections6[1], "---STARTTIME---\n")
							cpuTicksStr := strings.TrimSpace(sections7[0])
							result["cpuTicks"], _ = strconv.ParseUint(cpuTicksStr, 10, 64)

							if len(sections7) > 1 {
								result["startTime"] = strings.TrimSpace(sections7[1])
							}
						}
					}
				}
			}
		}
	}

	return result, nil
}
func (s *MonitorSession) KillProcess(pid int, signal string) error {
	session, err := s.client.NewSession()
	if err != nil {
		return err
	}
	defer session.Close()

	var cmd string
	switch signal {
	case "KILL":
		cmd = fmt.Sprintf("kill -9 %d", pid)
	case "TERM":
		cmd = fmt.Sprintf("kill -15 %d", pid)
	case "HUP":
		cmd = fmt.Sprintf("kill -1 %d", pid)
	case "INT":
		cmd = fmt.Sprintf("kill -2 %d", pid)
	default:
		cmd = fmt.Sprintf("kill %d", pid)
	}

	return session.Run(cmd)
}

// parsePortProcess converts ss output like users:(("nginx",pid=1001,fd=6),("nginx",pid=1002,fd=6))
// into "1001/nginx, 1002/nginx"
func parsePortProcess(raw string) string {
	if raw == "" || raw == "-" {
		return "-"
	}
	// Match "name",pid=123
	re := regexp.MustCompile(`"([^"]+)",pid=(\d+)`)
	matches := re.FindAllStringSubmatch(raw, -1)
	if len(matches) == 0 {
		return raw
	}
	seen := map[string]bool{}
	var parts []string
	for _, m := range matches {
		if len(m) < 3 {
			continue
		}
		name := m[1]
		pid := m[2]
		key := pid + "/" + name
		if !seen[key] {
			seen[key] = true
			parts = append(parts, pid+"/"+name)
		}
	}
	if len(parts) == 0 {
		return raw
	}
	return strings.Join(parts, ", ")
}

// collectMounts recursively gathers all unique non-empty mountpoints from lsblk JSON devices.
func collectMounts(devs []map[string]interface{}) []string {
	seen := map[string]bool{}
	var mounts []string
	var walk func([]map[string]interface{})
	walk = func(ds []map[string]interface{}) {
		for _, dev := range ds {
			if mp, ok := dev["mountpoint"].(string); ok && mp != "" && !seen[mp] {
				seen[mp] = true
				mounts = append(mounts, mp)
			}
			if children, ok := dev["children"].([]interface{}); ok {
				childMaps := make([]map[string]interface{}, 0, len(children))
				for _, c := range children {
					if cm, ok := c.(map[string]interface{}); ok {
						childMaps = append(childMaps, cm)
					}
				}
				walk(childMaps)
			}
		}
	}
	walk(devs)
	return mounts
}

func (s *MonitorSession) GetPorts() ([]PortInfo, error) {
	session, err := s.client.NewSession()
	if err != nil {
		return nil, err
	}
	defer session.Close()

	script := `exec 2>/dev/null
if command -v ss >/dev/null 2>&1; then
    ss -tulnp | tail -n +2
else
    netstat -tulnp 2>/dev/null | tail -n +2
fi`
	out, err := session.Output(script)
	if err != nil {
		return nil, err
	}

	var ports []PortInfo
	lines := strings.Split(string(out), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		fields := strings.Fields(line)
		if len(fields) < 4 {
			continue
		}
		var protocol, localAddr, state, process string
		if fields[0] == "tcp" || fields[0] == "udp" || fields[0] == "tcp6" || fields[0] == "udp6" {
			protocol = fields[0]
			state = fields[1]
			if len(fields) >= 6 {
				localAddr = fields[4]
				if len(fields) >= 7 {
					process = parsePortProcess(fields[6])
				}
			}
		} else {
			state = fields[0]
			if len(fields) >= 4 {
				localAddr = fields[3]
			}
			if len(fields) >= 5 {
				processField := fields[len(fields)-1]
				if idx := strings.Index(processField, `"`); idx >= 0 {
					endIdx := strings.Index(processField[idx+1:], `"`)
					if endIdx >= 0 {
						process = processField[idx+1 : idx+1+endIdx]
					}
				} else {
					process = processField
				}
			}
			// Infer protocol from state and address
			isUDP := state == "UNCONN"
			if strings.Contains(localAddr, ":") && !strings.Contains(localAddr, ".") && !strings.HasPrefix(localAddr, "[::]") {
				if isUDP {
					protocol = "udp6"
				} else {
					protocol = "tcp6"
				}
			} else if strings.HasPrefix(localAddr, "[::]") {
				if isUDP {
					protocol = "udp6"
				} else {
					protocol = "tcp6"
				}
			} else {
				if isUDP {
					protocol = "udp"
				} else {
					protocol = "tcp"
				}
			}
		}
		if localAddr == "" {
			continue
		}
		ports = append(ports, PortInfo{
			Protocol:  protocol,
			LocalAddr: localAddr,
			State:     state,
			Process:   process,
		})
	}
	return ports, nil
}

// parseLsblkPairsDisks parses the flat KEY="value" output of `lsblk -P`, used
// on old lsblk releases that lack -J/--json (e.g. CentOS 7). Unlike the plain
// column view, every field keeps its key, so a multi-word MODEL or an empty
// MOUNTPOINT can no longer nudge a neighbouring token into the mount-point
// column (which previously surfaced "QEMU"/"1" as fake mounts for sr0/vda/vdc).
// Returns nil when the output is not in pairs form (ancient lsblk fell back to
// plain columns); the caller then retries with column parsing.
func parseLsblkPairsDisks(out string, mountUsage map[string]struct{ Used, Total string; Usage int }) []DiskInfo {
	var disks []DiskInfo
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		matches := lsblkPairRe.FindAllStringSubmatch(line, -1)
		if len(matches) == 0 {
			return nil
		}
		col := make(map[string]string, len(matches))
		for _, m := range matches {
			if len(m) == 3 {
				// Trim the key: `[^=]+` also captures the space separating pairs,
				// so a later key like " TYPE" must be reduced to "TYPE".
				col[strings.TrimSpace(m[1])] = m[2]
			}
		}
		name := col["NAME"]
		if name == "" {
			continue
		}
		sizeBytes, _ := strconv.ParseUint(col["SIZE"], 10, 64)
		media := "-"
		switch col["TYPE"] {
		case "rom":
			media = "ROM"
		default:
			if col["ROTA"] == "1" {
				media = "HDD"
			} else if col["ROTA"] == "0" {
				media = "SSD"
			}
		}
		disk := DiskInfo{
			Name:       name,
			Type:       col["TYPE"],
			Size:       formatBytes(sizeBytes),
			Model:      strings.TrimSpace(col["MODEL"]),
			MountPoint: col["MOUNTPOINT"],
			Media:      media,
		}
		if mp := disk.MountPoint; mp != "" {
			if u, ok := mountUsage[mp]; ok {
				disk.Used = u.Used
				disk.Total = u.Total
				disk.Usage = u.Usage
			}
		}
		disks = append(disks, disk)
	}
	return disks
}

// lsblkPairRe matches one KEY="value" pair in lsblk -P output. The value may
// contain spaces (e.g. a multi-word MODEL) and escaped quotes, which is exactly
// the case -P exists to keep unambiguous.
var lsblkPairRe = regexp.MustCompile(`([^=]+)="((?:[^"\\]|\\.)*)"`)

// parseAddrText parses the legacy `ip addr show` text output (no -j) into an
// ifname -> [ip...] map, matching the shape of `ip -j addr show`. Interface
// headers start at column 0; inet/inet6 lines are indented, so indentation is
// used to attach each address to its interface. Used only when the JSON
// address output is unavailable.
func parseAddrText(out string) map[string][]string {
	addrMap := map[string][]string{}
	cur := ""
	for _, line := range strings.Split(out, "\n") {
		trimmed := strings.TrimSpace(line)
		if trimmed == "" {
			continue
		}
		if !strings.HasPrefix(line, " ") && !strings.HasPrefix(line, "\t") {
			// Interface header, e.g. "2: eth0: <BROADCAST,MULTICAST,UP,...>"
			parts := strings.SplitN(trimmed, ":", 3)
			if len(parts) >= 2 {
				cur = strings.TrimSpace(parts[1])
			}
			continue
		}
		if cur == "" {
			continue
		}
		f := strings.Fields(trimmed)
		if len(f) >= 2 && (strings.HasPrefix(trimmed, "inet ") || strings.HasPrefix(trimmed, "inet6 ")) {
			// f[1] is "addr/prefix"; strip the prefix to match the JSON "local" field.
			ip := strings.SplitN(f[1], "/", 2)[0]
			addrMap[cur] = append(addrMap[cur], ip)
		}
	}
	return addrMap
}

func (s *MonitorSession) GetDisks() ([]DiskInfo, error) {
	// Run lsblk and df in a single shell script to avoid extra SSH round-trips.
	// df only queries paths that actually have a mountpoint.
	session, err := s.client.NewSession()
	if err != nil {
		return nil, err
	}
	script := `lsblk -J -b -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL,ROTA,FSTYPE,UUID,VENDOR 2>/dev/null
echo "__SPLIT__"
mp=$(lsblk -n -o MOUNTPOINT 2>/dev/null | grep -v '^$' | sort -u | tr '\n' ' ')
[ -n "$mp" ] && df -h $mp 2>/dev/null`
	out, err := session.Output(script)
	session.Close()

	parts := strings.Split(string(out), "__SPLIT__")
	var jsonOut, dfOut []byte
	if len(parts) > 0 {
		jsonOut = []byte(strings.TrimSpace(parts[0]))
	}
	if len(parts) > 1 {
		dfOut = []byte(strings.TrimSpace(parts[1]))
	}

	mountUsage := map[string]struct{ Used, Total string; Usage int }{}
	dfByDev := map[string]dfEntry{}
	for _, line := range strings.Split(string(dfOut), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "Filesystem") {
			continue
		}
		fields := strings.Fields(line)
		if len(fields) >= 6 {
			mount := fields[5]
			usageStr := strings.TrimSuffix(fields[4], "%")
			usage, _ := strconv.Atoi(usageStr)
			mountUsage[mount] = struct{ Used, Total string; Usage int }{
				Used:  fields[2],
				Total: fields[1],
				Usage: usage,
			}
			devName := fields[0]
			if idx := strings.LastIndex(devName, "/"); idx >= 0 {
				devName = devName[idx+1:]
			}
			dfByDev[devName] = dfEntry{Used: fields[2], Total: fields[1], Usage: usage, Mount: mount}
		}
	}

	var disks []DiskInfo

	// Parse JSON output
	var lsblkJSON struct {
		BlockDevices []map[string]interface{} `json:"blockdevices"`
	}
	if err == nil && json.Unmarshal(jsonOut, &lsblkJSON) == nil {
		var walk func(devs []map[string]interface{}, depth int)
		walk = func(devs []map[string]interface{}, depth int) {
				for _, dev := range devs {
					name, _ := dev["name"].(string)
					devType, _ := dev["type"].(string)

					var sizeBytes uint64
					switch s := dev["size"].(type) {
					case float64:
						sizeBytes = uint64(s)
					case string:
						sizeBytes, _ = strconv.ParseUint(s, 10, 64)
					}

					var mount string
					switch mp := dev["mountpoint"].(type) {
					case string:
						if mp != "" {
							mount = mp
						}
					}

					var model string
					switch m := dev["model"].(type) {
					case string:
						if m != "" {
							model = m
						}
					}

					media := "-"
					if devType == "rom" {
						media = "ROM"
					} else {
						switch r := dev["rota"].(type) {
						case bool:
							if r {
								media = "HDD"
							} else {
								media = "SSD"
							}
						case string:
							if r == "1" || r == "true" {
								media = "HDD"
							} else if r == "0" || r == "false" {
								media = "SSD"
							}
						case float64:
							if r != 0 {
								media = "HDD"
							} else {
								media = "SSD"
							}
						}
					}

					var fsType, uuid, vendor string
					if v, ok := dev["fstype"].(string); ok && v != "" {
						fsType = v
					}
					if v, ok := dev["uuid"].(string); ok && v != "" {
						uuid = v
					}
					if v, ok := dev["vendor"].(string); ok && v != "" {
						vendor = v
					}

					disk := DiskInfo{
						Name:       strings.Repeat("  ", depth) + name,
						Type:       devType,
						Size:       formatBytes(sizeBytes),
						Media:      media,
						FSType:     fsType,
						UUID:       uuid,
						Vendor:     vendor,
						Model:      model,
					}
					// Prefer df (authoritative) for mount point + usage: lsblk JSON can
					// leave mountpoint empty for filesystems mounted directly on a disk.
					if d, ok := dfByDev[name]; ok {
						disk.MountPoint = d.Mount
						disk.Used = d.Used
						disk.Total = d.Total
						disk.Usage = d.Usage
					} else if mount != "" {
						disk.MountPoint = mount
						disk.Used = mountUsage[mount].Used
						disk.Total = mountUsage[mount].Total
						disk.Usage = mountUsage[mount].Usage
					}
					disks = append(disks, disk)

					if children, ok := dev["children"].([]interface{}); ok {
						childMaps := make([]map[string]interface{}, 0, len(children))
						for _, c := range children {
							if cm, ok := c.(map[string]interface{}); ok {
								childMaps = append(childMaps, cm)
							}
						}
						walk(childMaps, depth+1)
					}
				}
			}
			walk(lsblkJSON.BlockDevices, 0)
			return disks, nil
		}

	// Fallback to text parsing
	session2, err := s.client.NewSession()
	if err != nil {
		return nil, err
	}
	defer session2.Close()
	out2, err := session2.Output(`lsblk -P -b -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL,ROTA 2>/dev/null || lsblk -P -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL,ROTA 2>/dev/null || lsblk -b -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL,ROTA 2>/dev/null || lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL,ROTA 2>/dev/null`)
	if err != nil {
		return nil, err
	}

	// Old lsblk (<2.30) can't emit JSON, so prefer the stable -P pairs form.
	// The column loop below is only a last resort for pre-2.22 lsblk without -P.
	if flat := parseLsblkPairsDisks(string(out2), mountUsage); len(flat) > 0 {
		return flat, nil
	}

	lines := strings.Split(string(out2), "\n")
	var headers []string
	for i, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		fields := strings.Fields(line)
		if i == 0 {
			headers = fields
			continue
		}
		rawName := fields[0]
		depth := 0
		trimmedName := rawName
		for strings.HasPrefix(trimmedName, "|") || strings.HasPrefix(trimmedName, "-") || strings.HasPrefix(trimmedName, "\\") || strings.HasPrefix(trimmedName, " ") {
			if strings.HasPrefix(trimmedName, " ") {
				trimmedName = strings.TrimPrefix(trimmedName, " ")
			} else {
				trimmedName = trimmedName[1:]
				if strings.HasPrefix(trimmedName, "-") {
					trimmedName = trimmedName[1:]
				}
			}
			depth++
		}
		if len(fields) > 0 {
			fields[0] = trimmedName
		}
		colMap := map[string]string{}
		for j, h := range headers {
			if j < len(fields) {
				colMap[h] = fields[j]
			} else {
				colMap[h] = ""
			}
		}
		sizeBytes, _ := strconv.ParseUint(colMap["SIZE"], 10, 64)
		sizeStr := formatBytes(sizeBytes)
		media := "-"
		if colMap["TYPE"] == "rom" {
			media = "ROM"
		} else if colMap["ROTA"] == "1" {
			media = "HDD"
		} else if colMap["ROTA"] == "0" {
			media = "SSD"
		}
		mount := colMap["MOUNTPOINT"]
		usage := mountUsage[mount]
		disk := DiskInfo{
			Name:       strings.Repeat("  ", depth) + colMap["NAME"],
			Type:       colMap["TYPE"],
			Size:       sizeStr,
			Model:      colMap["MODEL"],
			MountPoint: mount,
			Media:      media,
		}
		if mount != "" {
			disk.Used = usage.Used
			disk.Total = usage.Total
			disk.Usage = usage.Usage
		}
		disks = append(disks, disk)
	}
	return disks, nil
}

func (s *MonitorSession) GetNetworkCards() ([]NetCardInfo, error) {
	session, err := s.client.NewSession()
	if err != nil {
		return nil, err
	}
	defer session.Close()

	script := `exec 2>/dev/null
if ip -j link show >/dev/null 2>&1; then
    echo "---LINKJSON---"
    ip -j link show
else
    echo "---LINKTEXT---"
    ip link show
fi
echo "---ADDRJSON---"
ip -j addr show 2>/dev/null || echo "[]"
echo "---ADDRTEXT---"
ip addr show
echo "---BOND---"
for f in /proc/net/bonding/*; do
    [ -f "$f" ] || continue
    echo "---BONDNAME---$(basename "$f")"
    cat "$f"
done
echo "---SPEED---"
for iface in $(ls /sys/class/net/ 2>/dev/null); do
    val=$(cat /sys/class/net/$iface/speed 2>/dev/null || echo -1)
    echo "$iface $val"
done
echo "---KIND---"
for d in /sys/class/net/*; do
    iface=$(basename "$d")
    [ "$iface" = "lo" ] && continue
    is_virt=0
    readlink -f "$d" | grep -q '/devices/virtual/net/' && is_virt=1
    has_dev=0; [ -L "$d/device" ] && has_dev=1
    if [ "$is_virt" -eq 0 ] && [ "$has_dev" -eq 1 ]; then
        kind=Physical
    elif [ "$is_virt" -eq 1 ] && [ -d "$d/bridge" ]; then
        kind=Bridge
    elif [ -f "$d/bonding/mode" ]; then
        kind=Bond
    else
        kind=Virtual
    fi
    echo "$iface $kind"
done`

	out, err := session.Output(script)
	if err != nil {
		return nil, err
	}

	output := string(out)
	sections := strings.Split(output, "---LINKJSON---\n")
	if len(sections) == 1 {
		sections = strings.Split(output, "---LINKTEXT---\n")
	}
	if len(sections) < 2 {
		return []NetCardInfo{}, nil
	}

	linkPart := strings.TrimSpace(sections[1])
	rest := ""
	if idx := strings.Index(linkPart, "---ADDRJSON---"); idx >= 0 {
		rest = linkPart[idx:]
		linkPart = strings.TrimSpace(linkPart[:idx])
	}

	// Parse bond info
	bondMasters := map[string][]string{}
	bondSlaves := map[string]string{}
	if rest != "" {
		bondSections := strings.Split(rest, "---BOND---\n")
		if len(bondSections) > 1 {
			for _, bs := range strings.Split(bondSections[1], "---BONDNAME---") {
				bs = strings.TrimSpace(bs)
				if bs == "" {
					continue
				}
				lines := strings.SplitN(bs, "\n", 2)
				bondName := strings.TrimSpace(lines[0])
				var slaves []string
				if len(lines) > 1 {
					for _, line := range strings.Split(lines[1], "\n") {
						line = strings.TrimSpace(line)
						if strings.HasPrefix(line, "Slave Interface:") {
							slave := strings.TrimSpace(strings.TrimPrefix(line, "Slave Interface:"))
							slaves = append(slaves, slave)
							bondSlaves[slave] = bondName
						}
					}
				}
				bondMasters[bondName] = slaves
			}
		}
	}

	// Parse addresses. The ADDRJSON section carries `ip -j addr show`; on hosts
	// whose ip lacks -j (e.g. CentOS 7) the script echoes "[]" there, so we also
	// collect the ADDRTEXT section (`ip addr show`) and fall back to it.
	var addrData []map[string]interface{}
	var addrTextPart string
	if rest != "" {
		addrSections := strings.Split(rest, "---ADDRJSON---\n")
		if len(addrSections) > 1 {
			addrPart := strings.TrimSpace(addrSections[1])
			if idx := strings.Index(addrPart, "---ADDRTEXT---"); idx >= 0 {
				addrTextPart = addrPart[idx+len("---ADDRTEXT---"):]
				if idx2 := strings.Index(addrTextPart, "---BOND---"); idx2 >= 0 {
					addrTextPart = strings.TrimSpace(addrTextPart[:idx2])
				}
				addrPart = strings.TrimSpace(addrPart[:idx])
			} else if idx := strings.Index(addrPart, "---BOND---"); idx >= 0 {
				addrPart = strings.TrimSpace(addrPart[:idx])
			}
			_ = json.Unmarshal([]byte(addrPart), &addrData)
		}
	}
	addrMap := map[string][]string{}
	for _, iface := range addrData {
		ifName, _ := iface["ifname"].(string)
		if ifName == "" {
			continue
		}
		addrs, _ := iface["addr_info"].([]interface{})
		for _, a := range addrs {
			ai, _ := a.(map[string]interface{})
			if ai == nil {
				continue
			}
			ip, _ := ai["local"].(string)
			if ip != "" {
				addrMap[ifName] = append(addrMap[ifName], ip)
			}
		}
	}
	if len(addrMap) == 0 && addrTextPart != "" {
		addrMap = parseAddrText(addrTextPart)
	}

	// Parse speed info
	speedMap := map[string]int{}
	if rest != "" {
		if idx := strings.Index(rest, "---SPEED---"); idx >= 0 {
			for _, line := range strings.Split(strings.TrimSpace(rest[idx+11:]), "\n") {
				fields := strings.Fields(line)
				if len(fields) == 2 {
					if val, err := strconv.Atoi(fields[1]); err == nil {
						speedMap[fields[0]] = val
					}
				}
			}
		}
	}

	// Parse kind info
	kindMap := map[string]string{}
	if rest != "" {
		if idx := strings.Index(rest, "---KIND---"); idx >= 0 {
			for _, line := range strings.Split(strings.TrimSpace(rest[idx+10:]), "\n") {
				fields := strings.Fields(line)
				if len(fields) == 2 {
					kindMap[fields[0]] = fields[1]
				}
			}
		}
	}

	// Parse link info
	var cards []NetCardInfo
	if strings.HasPrefix(linkPart, "[") {
		var linkData []map[string]interface{}
		if err := json.Unmarshal([]byte(linkPart), &linkData); err == nil {
			for _, iface := range linkData {
				name, _ := iface["ifname"].(string)
				if name == "" {
					continue
				}
				state, _ := iface["operstate"].(string)
				mac, _ := iface["address"].(string)
				linkType, _ := iface["link_type"].(string)
				speed := "-"
				if speedVal, ok := speedMap[name]; ok && speedVal > 0 {
					speed = fmt.Sprintf("%d Mbps", speedVal)
				}
				ifType := kindMap[name]
				if ifType == "" {
					if linkType == "loopback" {
						ifType = "Loopback"
					} else {
						ifType = "Virtual"
					}
				}
				card := NetCardInfo{
					Name:       name,
					State:      state,
					MAC:        mac,
					Speed:      speed,
					Type:       ifType,
					BondMaster: bondSlaves[name],
					BondSlaves: bondMasters[name],
					IPAddrs:    addrMap[name],
				}
				cards = append(cards, card)
			}
		}
	} else {
		// Text format fallback. Detail lines are indented, headers are not, so the
		// leading-whitespace test must run against the raw line BEFORE trimming;
		// otherwise an indented `link/ether`/`inet` detail line is trimmed flat and
		// misparsed as a brand-new interface header (producing junk cards on the
		// old `ip` output that CentOS 7 emits).
		var currentCard *NetCardInfo
		for _, line := range strings.Split(linkPart, "\n") {
			isDetail := strings.HasPrefix(line, " ") || strings.HasPrefix(line, "\t")
			line = strings.TrimSpace(line)
			if line == "" {
				continue
			}
			if !isDetail {
				if currentCard != nil {
					cards = append(cards, *currentCard)
				}
				parts := strings.SplitN(line, ":", 3)
				if len(parts) >= 2 {
					name := strings.TrimSpace(parts[1])
					ifType := kindMap[name]
					if ifType == "" {
						if strings.Contains(line, "loopback") {
							ifType = "Loopback"
						} else {
							ifType = "Virtual"
						}
					}
					currentCard = &NetCardInfo{
						Name:    name,
						State:   "UNKNOWN",
						Speed:   "-",
						Type:    ifType,
						IPAddrs: addrMap[name],
					}
					if len(parts) >= 3 && strings.Contains(parts[2], "UP") {
						currentCard.State = "UP"
					}
					currentCard.BondMaster = bondSlaves[name]
					currentCard.BondSlaves = bondMasters[name]
				}
			} else if currentCard != nil {
				if strings.Contains(line, "link/ether") {
					fields := strings.Fields(line)
					if len(fields) >= 2 {
						currentCard.MAC = fields[1]
					}
				}
				if strings.Contains(line, "state ") {
					stateIdx := strings.Index(line, "state ")
					if stateIdx >= 0 {
						stateVal := strings.Fields(line[stateIdx+6:])
						if len(stateVal) > 0 {
							currentCard.State = strings.ToUpper(stateVal[0])
						}
					}
				}
			}
		}
		if currentCard != nil {
			cards = append(cards, *currentCard)
		}
	}
	return cards, nil
}

func roundFloat(v float64, prec int) float64 {
	p := math.Pow(10, float64(prec))
	return math.Round(v*p) / p
}

// uintDelta returns cur-prev when counters moved forward; false on wrap/reset.
func uintDelta(cur, prev uint64) (uint64, bool) {
	if cur < prev {
		return 0, false
	}
	return cur - prev, true
}

func clampPct(v float64) float64 {
	if math.IsNaN(v) || math.IsInf(v, 0) {
		return 0
	}
	if v < 0 {
		return 0
	}
	if v > 100 {
		return 100
	}
	return v
}

func formatBytes(bytes uint64) string {
	if bytes == 0 {
		return "0 B"
	}
	const k = 1024
	sizes := []string{"B", "KB", "MB", "GB", "TB"}
	i := 0
	f := float64(bytes)
	for f >= k && i < len(sizes)-1 {
		f /= k
		i++
	}
	return fmt.Sprintf("%.1f %s", f, sizes[i])
}

func (s *MonitorSession) Write(data []byte) error {
	return nil
}

func (s *MonitorSession) Disconnect() error {
	s.quitOnce.Do(func() {
		close(s.quit)
	})
	if s.ticker != nil {
		s.ticker.Stop()
	}
	if s.client != nil {
		s.client.Close()
	}
	s.setStatus(StatusDisconnected)
	return nil
}

func (s *MonitorSession) Resize(cols, rows int) error {
	return nil
}

func (s *MonitorSession) IsConnected() bool {
	return s.Status() == StatusConnected
}

// --- Services / PCI devices / hardware health (systemctl, lspci, ipmitool, lm-sensors) ---

type ServiceInfo struct {
	Name        string `json:"name"`
	Load        string `json:"load"`
	Active      string `json:"active"`
	Sub         string `json:"sub"`
	Description string `json:"description"`
	Enabled     string `json:"enabled"`
}

// DeviceInfo is one row of the hardware devices tab. lshw is the primary
// source (PCI + USB + NVMe disks); lspci is the fallback (PCI only). Category
// is a display grouping key ("processor", "memory", "storage", "network",
// "display", "bus", "other") localized in the frontend.
type DeviceInfo struct {
	Category string `json:"category"`
	ID       string `json:"id"`
	Class    string `json:"class"`
	Vendor   string `json:"vendor"`
	Product  string `json:"product"`
	Driver   string `json:"driver"`
	Serial   string `json:"serial"`
	Capacity string `json:"capacity"`
	Rev      string `json:"rev"`
}

type SensorInfo struct {
	Name   string `json:"name"`
	Value  string `json:"value"`
	Unit   string `json:"unit"`
	Status string `json:"status"`
	Source string `json:"source"`
}

type FruInfo struct {
	Product      string `json:"product"`
	Manufacturer string `json:"manufacturer"`
	Serial       string `json:"serial"`
	PartNumber   string `json:"partNumber"`
}

// HardwareSensors is the readings half: IPMI sensor list.
type HardwareSensors struct {
	Sensors []SensorInfo `json:"sensors"`
	HasIpmi bool         `json:"hasIpmi"`
}

// unitLineRe splits one `systemctl list-units --no-legend` row into
// UNIT LOAD ACTIVE SUB and a DESCRIPTION that may contain spaces or be empty.
var unitLineRe = regexp.MustCompile(`^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(.*)$`)

// parseSystemctlUnits parses `systemctl list-units --type=service --all
// --no-legend --no-pager` output.
func parseSystemctlUnits(out string) []ServiceInfo {
	var services []ServiceInfo
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimRight(line, " \t\r")
		if strings.TrimSpace(line) == "" {
			continue
		}
		m := unitLineRe.FindStringSubmatch(line)
		if m == nil {
			continue
		}
		services = append(services, ServiceInfo{
			Name:        m[1],
			Load:        m[2],
			Active:      m[3],
			Sub:         m[4],
			Description: m[5],
		})
	}
	return services
}

// parseSystemctlUnitFiles parses `systemctl list-unit-files --no-legend`
// output into a unit -> state map. The trailing VENDOR-PRESET column present
// on newer systemd is ignored.
func parseSystemctlUnitFiles(out string) map[string]string {
	states := map[string]string{}
	for _, line := range strings.Split(out, "\n") {
		fields := strings.Fields(strings.TrimSpace(line))
		if len(fields) < 2 {
			continue
		}
		states[fields[0]] = fields[1]
	}
	return states
}

// parseLspciMm parses `lspci -mm` output:
// slot "class" "vendor" "device" [-rNN] ["subvendor" "subdevice"]
func parseLspciMm(out string) []DeviceInfo {
	var devices []DeviceInfo
	revRe := regexp.MustCompile(`-r(\S+)`)
	quotedRe := regexp.MustCompile(`"([^"]*)"`)
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimRight(line, " \t\r")
		if strings.TrimSpace(line) == "" {
			continue
		}
		slot := line
		if i := strings.IndexAny(slot, " \t"); i >= 0 {
			slot = slot[:i]
		}
		q := quotedRe.FindAllStringSubmatch(line, -1)
		if len(q) < 3 {
			continue
		}
		rev := ""
		if m := revRe.FindStringSubmatch(line); m != nil {
			rev = m[1]
		}
		devices = append(devices, DeviceInfo{
			Category: deviceCategory(q[0][1]),
			ID:       slot,
			Class:    q[0][1],
			Vendor:   q[1][1],
			Product:  q[2][1],
			Rev:      rev,
		})
	}
	return devices
}

// parseLspciText parses plain `lspci` output:
// slot Class: Vendor Device... (rev NN). Used when -mm is unavailable.
func parseLspciText(out string) []DeviceInfo {
	var devices []DeviceInfo
	revRe := regexp.MustCompile(`\(rev ([^)]+)\)`)
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimRight(line, " \t\r")
		if strings.TrimSpace(line) == "" {
			continue
		}
		slot := line
		if i := strings.IndexAny(slot, " \t"); i >= 0 {
			slot = slot[:i]
		}
		rest := strings.TrimSpace(strings.TrimPrefix(line, slot))
		head, tail, found := strings.Cut(rest, ": ")
		if !found {
			continue
		}
		rev := ""
		if m := revRe.FindStringSubmatch(tail); m != nil {
			rev = m[1]
		}
		tail = strings.TrimSpace(revRe.ReplaceAllString(tail, ""))
		vendor, device, _ := strings.Cut(tail, " ")
		devices = append(devices, DeviceInfo{
			Category: deviceCategory(strings.TrimSpace(head)),
			ID:       slot,
			Class:    strings.TrimSpace(head),
			Vendor:   vendor,
			Product:  strings.TrimSpace(device),
			Rev:      rev,
		})
	}
	return devices
}

// deviceCategory maps a device class (lshw class or lspci class text) to a
// display grouping key. Keyword order matters: storage keywords are checked
// first so "Non-Volatile memory controller" lands in storage, not memory.
func deviceCategory(cls string) string {
	c := strings.ToLower(cls)
	switch {
	case strings.Contains(c, "disk"), strings.Contains(c, "storage"),
		strings.Contains(c, "volume"), strings.Contains(c, "tape"),
		strings.Contains(c, "sata"), strings.Contains(c, "nvme"),
		strings.Contains(c, "non-volatile"), strings.Contains(c, "sas"),
		strings.Contains(c, "scsi"), strings.Contains(c, "ide"):
		return "storage"
	case strings.Contains(c, "memory"), strings.Contains(c, "dimm"), strings.Contains(c, "ram"):
		return "memory"
	case strings.Contains(c, "network"), strings.Contains(c, "ethernet"),
		strings.Contains(c, "wireless"), strings.Contains(c, "wifi"),
		strings.Contains(c, "modem"), strings.Contains(c, "fibre"),
		strings.Contains(c, "communicat"):
		return "network"
	case strings.Contains(c, "display"), strings.Contains(c, "vga"),
		strings.Contains(c, "3d"), strings.Contains(c, "audio"),
		strings.Contains(c, "multimedia"), strings.Contains(c, "sound"):
		return "display"
	case strings.Contains(c, "processor"), strings.Contains(c, "cpu"):
		return "processor"
	case strings.Contains(c, "bridge"), strings.Contains(c, "bus"),
		strings.Contains(c, "usb"):
		return "bus"
	default:
		return "other"
	}
}

// parseLshwDevices flattens the full `lshw -json` hardware tree into one
// device table, in tree order, without filtering by bus type. Every node
// becomes a row: businfo (or logical name / id) as ID, description as class,
// plus vendor/product/driver/serial/capacity/revision when present. Capacity
// is only formatted as bytes for classes whose size is measured in bytes
// (disk/memory/volume); for other classes lshw "size" has other units (Hz
// for processors, and so on). Returns nil when the output is not valid JSON
// so the caller can fall back to lspci.
func parseLshwDevices(out string) []DeviceInfo {
	trimmed := strings.TrimSpace(out)
	if trimmed == "" || trimmed[0] != '{' {
		return nil
	}
	var root map[string]interface{}
	if err := json.Unmarshal([]byte(trimmed), &root); err != nil {
		return nil
	}
	var devices []DeviceInfo
	var walk func(node map[string]interface{})
	walk = func(node map[string]interface{}) {
		dev := DeviceInfo{}
		cls, _ := node["class"].(string)
		dev.Category = deviceCategory(cls)
		if cls == "disk" || cls == "volume" {
			// Disks read better by device name: nvme0n1, /dev/sda.
			if ln := lshwFirstLogical(node); ln != "" {
				dev.ID = ln
			} else if bi, ok := node["businfo"].(string); ok {
				dev.ID = bi
			}
		} else if bi, ok := node["businfo"].(string); ok && bi != "" {
			dev.ID = bi
		} else if ln := lshwFirstLogical(node); ln != "" {
			dev.ID = ln
		} else if id, ok := node["id"].(string); ok {
			dev.ID = id
		}
		if desc, ok := node["description"].(string); ok && desc != "" {
			dev.Class = desc
		} else if c, ok := node["class"].(string); ok {
			dev.Class = c
		}
		if v, ok := node["vendor"].(string); ok {
			dev.Vendor = v
		}
		if p, ok := node["product"].(string); ok {
			dev.Product = p
		}
		if s, ok := node["serial"].(string); ok {
			dev.Serial = s
		}
		if ver, ok := node["version"].(string); ok {
			dev.Rev = ver
		}
		if cfg, ok := node["configuration"].(map[string]interface{}); ok {
			if drv, ok := cfg["driver"].(string); ok {
				dev.Driver = drv
			}
		}
		if size, ok := node["size"].(float64); ok && size > 0 {
			switch node["class"] {
			case "disk", "memory", "volume":
				dev.Capacity = formatBytes(uint64(size))
			}
		}
		devices = append(devices, dev)
		if children, ok := node["children"].([]interface{}); ok {
			for _, c := range children {
				if cm, ok := c.(map[string]interface{}); ok {
					walk(cm)
				}
			}
		}
	}
	walk(root)
	return devices
}

// lshwFirstLogical returns the first logical name of a node (lshw emits
// "logicalname" as a string or an array of strings).
func lshwFirstLogical(node map[string]interface{}) string {
	switch ln := node["logicalname"].(type) {
	case string:
		return ln
	case []interface{}:
		if len(ln) > 0 {
			if s, ok := ln[0].(string); ok {
				return s
			}
		}
	}
	return ""
}

// parseIpmitoolSensors parses `ipmitool sensor list` output. Each line is
// pipe-separated: Name | Value | Units | Status | States | thresholds...
func parseIpmitoolSensors(out string) []SensorInfo {
	var sensors []SensorInfo
	for _, line := range strings.Split(out, "\n") {
		if strings.TrimSpace(line) == "" || !strings.Contains(line, "|") {
			continue
		}
		parts := strings.Split(line, "|")
		if len(parts) < 4 {
			continue
		}
		sensors = append(sensors, SensorInfo{
			Name:   strings.TrimSpace(parts[0]),
			Value:  strings.TrimSpace(parts[1]),
			Unit:   strings.TrimSpace(parts[2]),
			Status: strings.TrimSpace(parts[3]),
			Source: "ipmi",
		})
	}
	return sensors
}

// parseIpmiFru parses `ipmitool fru print` output key/value pairs, picking
// the product identity fields (falling back to the board fields). Returns
// nil when nothing matches.
func parseIpmiFru(out string) *FruInfo {
	var pProd, pMan, pSer, pPart, bProd, bMan, bSer, bPart string
	for _, line := range strings.Split(out, "\n") {
		key, value, found := strings.Cut(line, ":")
		if !found {
			continue
		}
		key = strings.TrimSpace(key)
		value = strings.TrimSpace(value)
		if value == "" {
			continue
		}
		switch key {
		case "Product Name":
			pProd = value
		case "Product Manufacturer":
			pMan = value
		case "Product Serial":
			pSer = value
		case "Product Part Number":
			pPart = value
		case "Board Product":
			bProd = value
		case "Board Manufacturer":
			bMan = value
		case "Board Serial":
			bSer = value
		case "Board Part Number":
			bPart = value
		}
	}
	fru := &FruInfo{
		Product:      pProd,
		Manufacturer: pMan,
		Serial:       pSer,
		PartNumber:   pPart,
	}
	if fru.Product == "" {
		fru.Product = bProd
	}
	if fru.Manufacturer == "" {
		fru.Manufacturer = bMan
	}
	if fru.Serial == "" {
		fru.Serial = bSer
	}
	if fru.PartNumber == "" {
		fru.PartNumber = bPart
	}
	if fru.Product == "" && fru.Manufacturer == "" && fru.Serial == "" && fru.PartNumber == "" {
		return nil
	}
	return fru
}

// LanField is one ordered key/value row of `ipmitool lan print` output.
type LanField struct {
	Key   string `json:"key"`
	Value string `json:"value"`
}

// parseIpmiLan parses `ipmitool lan print <channel>` output. Every line is
// "Key : Value"; continuation lines (empty key, as in the Auth Type block)
// and empty values are skipped. Field order is preserved for display.
func parseIpmiLan(out string) []LanField {
	var fields []LanField
	for _, line := range strings.Split(out, "\n") {
		key, value, found := strings.Cut(line, ":")
		if !found {
			continue
		}
		key = strings.TrimSpace(key)
		value = strings.TrimSpace(value)
		if key == "" || value == "" {
			continue
		}
		fields = append(fields, LanField{Key: key, Value: value})
	}
	return fields
}

// standardLanKeys are the network fields shown on the hardware info card,
// in display order; everything else in `lan print` output is dropped.
var standardLanKeys = []string{
	"IP Address",
	"Subnet Mask",
	"MAC Address",
	"Default Gateway IP",
}

// standardLanFields filters parsed lan output down to the standard keys and
// reorders them for display. Missing keys are simply absent.
func standardLanFields(fields []LanField) []LanField {
	byKey := make(map[string]string, len(fields))
	for _, f := range fields {
		if _, seen := byKey[f.Key]; !seen {
			byKey[f.Key] = f.Value
		}
	}
	var out []LanField
	for _, key := range standardLanKeys {
		if v, ok := byKey[key]; ok {
			out = append(out, LanField{Key: key, Value: v})
		}
	}
	return out
}

// parseSystemctlShow parses `systemctl show <unit>` key=value lines.
func parseSystemctlShow(out string) map[string]string {
	props := map[string]string{}
	for _, line := range strings.Split(out, "\n") {
		key, value, found := strings.Cut(line, "=")
		if !found {
			continue
		}
		props[key] = value
	}
	return props
}

var serviceActionWhitelist = map[string]bool{
	"start": true, "stop": true, "restart": true, "enable": true, "disable": true,
}

func validServiceAction(action string) bool {
	return serviceActionWhitelist[action]
}

// validUnitName rejects anything but the characters a systemd unit name may
// contain, so a hostile name cannot escape the shell command.
var unitNameRe = regexp.MustCompile(`^[A-Za-z0-9@._\-]+$`)

func validUnitName(name string) bool {
	return unitNameRe.MatchString(name)
}

// Service log viewer limits: the frontend picks a history size (100..2000)
// and the backend clamps it so a hostile/buggy value cannot request the
// whole journal.
const (
	defaultLogLines = 200
	maxLogLines     = 2000
)

// clampLogLines normalizes the requested history size for journalctl -n.
func clampLogLines(n int) int {
	if n <= 0 {
		return defaultLogLines
	}
	if n > maxLogLines {
		return maxLogLines
	}
	return n
}

// GetServiceLogs tails the last N lines of a unit's journal. journalctl is
// tried as the connected user first, then with `sudo -n` (same NOPASSWD
// convention as ServiceAction) because unprivileged users often cannot read
// system units' logs. Missing journalctl or both permission paths failing
// yields an empty string rather than an error.
func (s *MonitorSession) GetServiceLogs(name string, lines int) (string, error) {
	if !validUnitName(name) {
		return "", fmt.Errorf("invalid unit name: %s", name)
	}
	n := clampLogLines(lines)
	session, err := s.client.NewSession()
	if err != nil {
		return "", err
	}
	defer session.Close()

	script := fmt.Sprintf(`exec 2>/dev/null
if command -v journalctl >/dev/null 2>&1; then
    out=$(journalctl -u %s -n %d --no-pager --no-host -o short-iso) || \
    out=$(sudo -n journalctl -u %s -n %d --no-pager --no-host -o short-iso) || true
    echo "$out"
fi
exit 0`, name, n, name, n)
	out, err := session.Output(script)
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(out)), nil
}

// GetServices lists systemd services with their unit-file enablement state.
// Both systemctl calls run in one SSH round-trip; `|| true` keeps the script
// exit status clean when systemctl is missing entirely (non-systemd hosts),
// which surfaces as an empty list.
func (s *MonitorSession) GetServices() ([]ServiceInfo, error) {
	session, err := s.client.NewSession()
	if err != nil {
		return nil, err
	}
	defer session.Close()

	script := `exec 2>/dev/null
systemctl list-units --type=service --all --no-legend --no-pager || true
echo "__SPLIT__"
systemctl list-unit-files --type=service --no-legend || true`
	out, err := session.Output(script)
	if err != nil {
		return nil, err
	}

	parts := strings.Split(string(out), "__SPLIT__")
	services := parseSystemctlUnits(safeIndex(parts, 0))
	states := parseSystemctlUnitFiles(safeIndex(parts, 1))
	for i := range services {
		if state, ok := states[services[i].Name]; ok {
			services[i].Enabled = state
		}
	}
	return services, nil
}

// GetServiceDetail returns the raw `systemctl show <unit>` properties.
func (s *MonitorSession) GetServiceDetail(name string) (map[string]string, error) {
	if !validUnitName(name) {
		return nil, fmt.Errorf("invalid unit name: %s", name)
	}
	session, err := s.client.NewSession()
	if err != nil {
		return nil, err
	}
	defer session.Close()

	out, err := session.Output(fmt.Sprintf("systemctl show %s --no-pager 2>/dev/null || true", name))
	if err != nil {
		return nil, err
	}
	return parseSystemctlShow(string(out)), nil
}

// ServiceAction runs `sudo -n systemctl <action> <name>` on the remote host.
// The unit name and action are strictly validated; the combined output is
// returned as the error message so permission problems (sudo without a
// NOPASSWD rule, missing root) reach the frontend instead of being swallowed.
func (s *MonitorSession) ServiceAction(name, action string) error {
	if !validUnitName(name) {
		return fmt.Errorf("invalid unit name: %s", name)
	}
	if !validServiceAction(action) {
		return fmt.Errorf("invalid action: %s", action)
	}
	session, err := s.client.NewSession()
	if err != nil {
		return err
	}
	defer session.Close()

	out, err := session.CombinedOutput(fmt.Sprintf("sudo -n systemctl %s %s", action, name))
	if err != nil {
		msg := strings.TrimSpace(string(out))
		if msg == "" {
			msg = err.Error()
		}
		return fmt.Errorf("%s %s: %s", action, name, msg)
	}
	return nil
}

// GetDevices lists the full hardware device table. `lshw -json` is the
// primary source (one flattened row per tree node: PCI, USB, disks, memory,
// CPU, ...); `lspci` is the fallback (PCI only) for hosts without lshw. Both
// run in one SSH round-trip, separated by a __SPLIT__ marker.
func (s *MonitorSession) GetDevices() ([]DeviceInfo, error) {
	session, err := s.client.NewSession()
	if err != nil {
		return nil, err
	}
	defer session.Close()

	script := `exec 2>/dev/null
if command -v lshw >/dev/null 2>&1; then
    lshw -json 2>/dev/null
    echo "__SPLIT__"
fi
if command -v lspci >/dev/null 2>&1; then
    lspci -mm || lspci
fi
exit 0`
	out, err := session.Output(script)
	if err != nil {
		return nil, err
	}

	parts := strings.SplitN(string(out), "__SPLIT__", 2)
	lshwOut := ""
	lspciOut := ""
	if len(parts) == 2 {
		// lshw ran; lspci output (if any) is in the second part.
		lshwOut = parts[0]
		lspciOut = parts[1]
	} else {
		// lshw missing: the whole output is lspci.
		lspciOut = parts[0]
	}
	if devices := parseLshwDevices(lshwOut); len(devices) > 0 {
		return devices, nil
	}
	if devices := parseLspciMm(lspciOut); len(devices) > 0 {
		return devices, nil
	}
	return parseLspciText(lspciOut), nil
}

// GetHardwareFru collects the IPMI FRU product identity. A missing ipmitool
// leaves a nil result instead of failing the call. Scripts end with an
// explicit `exit 0` so "tool not found" degrades to empty data rather than
// an error (the trailing `command -v && echo` would otherwise exit 1).
func (s *MonitorSession) GetHardwareFru() (*FruInfo, error) {
	session, err := s.client.NewSession()
	if err != nil {
		return nil, err
	}
	defer session.Close()

	script := `exec 2>/dev/null
if command -v ipmitool >/dev/null 2>&1; then
    ipmitool fru print || true
fi
exit 0`
	out, err := session.Output(script)
	if err != nil {
		return nil, err
	}
	return parseIpmiFru(string(out)), nil
}

// GetHardwareLan collects the standard BMC network fields from
// `ipmitool lan print` (IP address, MAC, gateway, ...). Non-standard fields
// are filtered out; a missing ipmitool leaves an empty result.
func (s *MonitorSession) GetHardwareLan() ([]LanField, error) {
	session, err := s.client.NewSession()
	if err != nil {
		return nil, err
	}
	defer session.Close()

	script := `exec 2>/dev/null
if command -v ipmitool >/dev/null 2>&1; then
    ipmitool lan print 1 || ipmitool lan print || true
fi
exit 0`
	out, err := session.Output(script)
	if err != nil {
		return nil, err
	}
	return standardLanFields(parseIpmiLan(string(out))), nil
}

// GetHardwareSensors collects IPMI sensor readings via `ipmitool sensor
// list`. A missing ipmitool leaves an empty result (hasIpmi false) instead of
// failing the call.
func (s *MonitorSession) GetHardwareSensors() (*HardwareSensors, error) {
	session, err := s.client.NewSession()
	if err != nil {
		return nil, err
	}
	defer session.Close()

	script := `exec 2>/dev/null
if command -v ipmitool >/dev/null 2>&1; then
    echo "===HAS==="
    ipmitool sensor list || true
fi
exit 0`
	out, err := session.Output(script)
	if err != nil {
		return nil, err
	}

	text := string(out)
	res := &HardwareSensors{
		HasIpmi: strings.Contains(text, "===HAS==="),
	}
	if res.HasIpmi {
		res.Sensors = parseIpmitoolSensors(text[strings.Index(text, "===HAS===")+len("===HAS==="):])
	}
	return res, nil
}
