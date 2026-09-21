package container

import (
	"os"
	"strings"
	"testing"
)

func TestParseInspectDocker(t *testing.T) {
	raw, err := os.ReadFile("testdata/docker_inspect.json")
	if err != nil {
		t.Skip("golden file missing, run spike task")
	}
	d, err := ParseInspect(RuntimeDocker, raw)
	if err != nil {
		t.Fatal(err)
	}
	if d.ID == "" || d.Image == "" || d.State == "" {
		t.Fatalf("incomplete detail: %+v", d)
	}
}

// 合成样本验证字段映射与 Name 去斜杠
func TestParseInspectSynthetic(t *testing.T) {
	raw := []byte(`[{
		"Id": "3f8b2c1a9e77",
		"Name": "/web",
		"Config": {"Image": "nginx:latest", "Cmd": ["nginx","-g","daemon off;"], "Entrypoint": ["/entrypoint.sh"], "Env": ["A=1","B=2"], "WorkingDir": "/app", "User": "nginx"},
		"State": {"Status": "running", "OOMKilled": false, "ExitCode": 0, "StartedAt": "2026-07-20T01:30:12Z", "FinishedAt": "0001-01-01T00:00:00Z", "Pid": 1234},
		"HostConfig": {"NetworkMode": "bridge", "RestartPolicy": {"Name": "always"}, "Binds": ["/data:/usr/share/nginx/html:ro"]},
		"NetworkSettings": {"IPAddress": "172.17.0.2", "Gateway": "172.17.0.1", "Ports": {"80/tcp": [{"HostIp":"0.0.0.0","HostPort":"8080"}], "443/tcp": null}},
		"Mounts": [{"Source": "/data", "Destination": "/usr/share/nginx/html", "RW": false}]
	}]`)
	d, err := ParseInspect(RuntimeDocker, raw)
	if err != nil {
		t.Fatal(err)
	}
	if d.Name != "web" || d.User != "nginx" || d.RestartPolicy != "always" || d.IP != "172.17.0.2" {
		t.Fatalf("got %+v", d)
	}
	if len(d.Env) != 2 || len(d.Mounts) != 1 || d.Mounts[0].RW {
		t.Fatalf("got %+v", d)
	}
	// 443/tcp 为 null（暴露未发布）应跳过
	if len(d.Ports) != 1 || d.Ports[0].HostPort != "8080" || d.Ports[0].ContainerPort != "80" || d.Ports[0].Protocol != "tcp" {
		t.Fatalf("ports: %+v", d.Ports)
	}
	if !strings.Contains(d.Command, "nginx") {
		t.Fatalf("command: %q", d.Command)
	}
}

func TestParseNamespaces(t *testing.T) {
	// nerdctl namespace ls 表格输出（ spike 校准；兼容 NAME 表头行）
	out := "NAME        CONTAINERS    IMAGES    VOLUMES\ndefault     2             5         0\nk8s.io      30            60        0\n"
	ns := ParseNamespaces([]byte(out))
	if len(ns) != 2 || ns[0] != "default" || ns[1] != "k8s.io" {
		t.Fatalf("got %v", ns)
	}
}
