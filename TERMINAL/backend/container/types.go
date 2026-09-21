package container

type Runtime string

const (
	RuntimeDocker  Runtime = "docker"
	RuntimePodman  Runtime = "podman"
	RuntimeNerdctl Runtime = "nerdctl"
	RuntimeWSLC    Runtime = "wslc"
)

func (r Runtime) Bin() string { return string(r) }
func (r Runtime) Valid() bool {
	return r == RuntimeDocker || r == RuntimePodman || r == RuntimeNerdctl || r == RuntimeWSLC
}

type Container struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	Image     string `json:"image"`
	State     string `json:"state"`  // running / exited / paused / ...
	Status    string `json:"status"` // 人类可读，如 "Up 5 days"
	Ports     string `json:"ports"`
	CreatedAt string `json:"createdAt"`
}

type PortMapping struct {
	HostIP        string `json:"hostIp,omitempty"`
	HostPort      string `json:"hostPort"`
	ContainerPort string `json:"containerPort"`
	Protocol      string `json:"protocol"`
}

type Mount struct {
	Source      string `json:"source"`
	Destination string `json:"destination"`
	RW          bool   `json:"rw"`
}

type ContainerDetail struct {
	ID            string        `json:"id"`
	Name          string        `json:"name"`
	Image         string        `json:"image"`
	State         string        `json:"state"`
	Status        string        `json:"status"`
	StartedAt     string        `json:"startedAt"`
	FinishedAt    string        `json:"finishedAt"`
	ExitCode      *int          `json:"exitCode"`
	OOMKilled     bool          `json:"oomKilled"`
	Pid           int           `json:"pid"`
	RestartPolicy string        `json:"restartPolicy"`
	Entrypoint    string        `json:"entrypoint"`
	Command       string        `json:"command"`
	WorkDir       string        `json:"workDir"`
	User          string        `json:"user"`
	NetworkMode   string        `json:"networkMode"`
	IP            string        `json:"ip"`
	Gateway       string        `json:"gateway"`
	Ports         []PortMapping `json:"ports"`
	Mounts        []Mount       `json:"mounts"`
	Env           []string      `json:"env"`
}

// InspectResult: 归一化详情 + inspect 原文（前端 JSON tab 展示用）
type InspectResult struct {
	Detail ContainerDetail `json:"detail"`
	Raw    string          `json:"raw"`
}

type Image struct {
	ID         string `json:"id"`
	Repository string `json:"repository"`
	Tag        string `json:"tag"`
	Size       string `json:"size"`
	CreatedAt  string `json:"createdAt"`
}

type Stats struct {
	ID         string `json:"id"`
	Name       string `json:"name"`
	CPUPercent string `json:"cpuPercent"`
	MemUsage   string `json:"memUsage"`
	MemPercent string `json:"memPercent"`
	NetIO      string `json:"netIO"`
	BlockIO    string `json:"blockIO"`
}

type CreateOptions struct {
	Image   string        `json:"image"`
	Name    string        `json:"name"`
	Ports   []PortMapping `json:"ports"`
	Volumes []string      `json:"volumes"` // "host:container" 原文
	Env     []string      `json:"env"`     // "KEY=VAL" 原文
	Restart string        `json:"restart"` // no/always/unless-stopped/on-failure
	Command []string      `json:"command"`
}
