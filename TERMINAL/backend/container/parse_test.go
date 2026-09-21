package container

import (
	"os"
	"testing"
)

func TestParseContainersDocker(t *testing.T) {
	raw, err := os.ReadFile("testdata/docker_ps.jsonl")
	if err != nil {
		t.Skip("golden file missing, run spike task")
	}
	list, err := ParseContainers(RuntimeDocker, raw)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) == 0 {
		t.Fatal("no containers parsed")
	}
	for _, c := range list {
		if c.ID == "" || c.Name == "" || c.Image == "" || c.State == "" {
			t.Fatalf("incomplete row: %+v", c)
		}
	}
}

// 单行坏数据不拖垮整列表
func TestParseContainersSkipsBadLine(t *testing.T) {
	out := []byte("{\"ID\":\"a1\",\"Image\":\"nginx\",\"Names\":\"web\",\"State\":\"running\",\"Status\":\"Up 1h\",\"Ports\":\"\",\"CreatedAt\":\"\"}\nnot-json\n")
	list, err := ParseContainers(RuntimeDocker, out)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 1 || list[0].Name != "web" {
		t.Fatalf("got %+v", list)
	}
}

// podman 的 Names 是数组
func TestParseContainersPodmanNamesArray(t *testing.T) {
	out := []byte("{\"ID\":\"b2\",\"Image\":\"docker.io/library/nginx:latest\",\"Names\":[\"web\",\"web-1\"],\"State\":\"running\",\"Status\":\"Up 2 hours\",\"Ports\":\"\",\"Created\":\"2026-07-20 09:30:12 +0800 CST\"}\n")
	list, err := ParseContainers(RuntimePodman, out)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 1 || list[0].Name != "web" {
		t.Fatalf("got %+v", list)
	}
}

// podman images 的 Names 同样是数组
func TestParseImagesPodmanNamesArray(t *testing.T) {
	out := []byte("{\"ID\":\"c3\",\"Names\":[\"docker.io/library/nginx:latest\",\"docker.io/library/nginx:1.27\"],\"Size\":\"192MB\",\"Created\":\"2026-07-20 09:30:12 +0800 CST\"}\n")
	list, err := ParseImages(RuntimePodman, out)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 1 || list[0].Repository != "docker.io/library/nginx:latest" {
		t.Fatalf("got %+v", list)
	}
}

// stats 的 Name/Names 也可能是数组
func TestParseStatsPodmanNamesArray(t *testing.T) {
	out := []byte("{\"ID\":\"d4\",\"Names\":[\"web\",\"web-1\"],\"CPUPerc\":\"0.50%\",\"MemUsage\":\"10MiB / 1GiB\",\"MemPerc\":\"1.00%\",\"NetIO\":\"1kB / 2kB\",\"BlockIO\":\"0B / 0B\"}\n")
	list, err := ParseStats(RuntimePodman, out)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 1 || list[0].Name != "web" {
		t.Fatalf("got %+v", list)
	}
}

// ── WSLC (OCI schema) ────────────────────────────────────────

func TestParseContainersWSLC(t *testing.T) {
	raw, err := os.ReadFile("testdata/wslc_ps.json")
	if err != nil {
		t.Skip("golden file missing")
	}
	list, err := ParseContainers(RuntimeWSLC, raw)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 3 {
		t.Fatalf("want 3 containers, got %d", len(list))
	}
	// State=2 → running
	if list[0].State != "running" {
		t.Errorf("container 0 state: want running, got %q", list[0].State)
	}
	if list[0].Name != "test" || list[0].Image != "nginx:latest" {
		t.Errorf("container 0 fields: %+v", list[0])
	}
	// State=3 → exited
	if list[2].State != "exited" {
		t.Errorf("container 2 state: want exited, got %q", list[2].State)
	}
	// Ports: BindingAddress + numeric Protocol
	if list[1].Ports != "127.0.0.1:18888->8888/tcp" {
		t.Errorf("container 1 ports: want 127.0.0.1:18888->8888/tcp, got %q", list[1].Ports)
	}
	// CreatedAt: Unix timestamp
	if list[0].CreatedAt == "" {
		t.Error("container 0 createdAt should not be empty")
	}
}

func TestParseContainersWSLCJSONArray(t *testing.T) {
	// Inline JSON array (not line-delimited)
	out := []byte(`[{"Id":"abc","Name":"web","Image":"nginx","State":2,"CreatedAt":1787571632,"Ports":[]}]`)
	list, err := ParseContainers(RuntimeWSLC, out)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 1 || list[0].State != "running" {
		t.Fatalf("got %+v", list)
	}
}

func TestParseImagesWSLC(t *testing.T) {
	raw, err := os.ReadFile("testdata/wslc_images.json")
	if err != nil {
		t.Skip("golden file missing")
	}
	list, err := ParseImages(RuntimeWSLC, raw)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 2 {
		t.Fatalf("want 2 images, got %d", len(list))
	}
	if list[0].Repository != "nginx" || list[0].Tag != "latest" {
		t.Errorf("image 0: %+v", list[0])
	}
	// Size is numeric bytes → human readable
	if list[0].Size == "" {
		t.Error("image 0 size should not be empty")
	}
}

func TestParseImagesWSLCJSONArray(t *testing.T) {
	out := []byte(`[{"Id":"x1","Repository":"redis","Tag":"7","Size":32000000,"CreatedAt":1786000000}]`)
	list, err := ParseImages(RuntimeWSLC, out)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 1 || list[0].Repository != "redis" {
		t.Fatalf("got %+v", list)
	}
}

// ── normalizeState ───────────────────────────────────────────

func TestNormalizeState(t *testing.T) {
	tests := []struct {
		state, status, want string
	}{
		// WSLC numeric codes
		{"0", "", "created"},
		{"1", "", "created"},
		{"2", "", "running"},
		{"3", "", "exited"},
		{"4", "", "paused"},
		{"5", "", "exited"},
		// Docker/Podman string states (passthrough)
		{"running", "", "running"},
		{"Running", "", "running"},
		{"exited", "", "exited"},
		{"Exited (0)", "", "exited"},
		{"paused", "", "paused"},
		{"created", "", "created"},
		// nerdctl: no State, derive from Status
		{"", "Up 2 hours", "running"},
		{"", "Exited (0) 5 min ago", "exited"},
		{"", "Paused", "paused"},
		// Unrecognized numeric → fall back to Status
		{"99", "Up 1h", "running"},
		{"99", "Exited (1)", "exited"},
		{"99", "", "99"},
	}
	for _, tt := range tests {
		got := normalizeState(tt.state, tt.status)
		if got != tt.want {
			t.Errorf("normalizeState(%q, %q) = %q, want %q", tt.state, tt.status, got, tt.want)
		}
	}
}

// ── formatPortObjects WSLC ──────────────────────────────────

func TestFormatPortObjectsWSLC(t *testing.T) {
	arr := []any{
		map[string]any{
			"BindingAddress": "0.0.0.0",
			"ContainerPort":  float64(8080),
			"HostPort":       float64(9090),
			"Protocol":       float64(6), // TCP
		},
	}
	got := formatPortObjects(arr)
	want := "0.0.0.0:9090->8080/tcp"
	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}
}

func TestFormatPortObjectsWSLCUDP(t *testing.T) {
	arr := []any{
		map[string]any{
			"ContainerPort": float64(53),
			"HostPort":      float64(5353),
			"Protocol":      float64(17), // UDP
		},
	}
	got := formatPortObjects(arr)
	want := "0.0.0.0:5353->53/udp"
	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}
}
