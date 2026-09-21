package container

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
)

type LocalRunner struct{}

func NewLocalRunner() *LocalRunner { return &LocalRunner{} }

// candidateDirs 覆盖 macOS GUI PATH 缺失与 Linux 非常规安装位置。
var candidateDirs = []string{
	"/usr/local/bin", "/opt/homebrew/bin", "/snap/bin", "/usr/bin",
	`C:\Program Files\Docker\Docker\resources\bin`,
	`C:\Program Files\Rancher Desktop\resources\resources\win32\bin`,
	`C:\Windows\System32`,
}

func resolveBinary(name string) (string, error) {
	if p, err := exec.LookPath(name); err == nil {
		return p, nil
	}
	ext := ""
	if runtime.GOOS == "windows" {
		ext = ".exe"
	}
	for _, dir := range candidateDirs {
		p := filepath.Join(dir, name+ext)
		if st, err := os.Stat(p); err == nil && !st.IsDir() {
			return p, nil
		}
	}
	return "", fmt.Errorf("%s not found in PATH or candidate dirs", name)
}

// command 构造 *exec.Cmd；argv[0] 为运行时二进制时先解析全路径，
// "sh -c ..." 在 windows 上改写为 cmd /c。
func (r *LocalRunner) command(ctx context.Context, argv []string) (*exec.Cmd, error) {
	if argv[0] == "sh" && runtime.GOOS == "windows" {
		rest := argv[2:]
		// cmd 无 command 内建命令，command -v 用 where 替代
		if len(rest) == 1 && strings.HasPrefix(rest[0], "command -v ") {
			rest = []string{"where", strings.TrimPrefix(rest[0], "command -v ")}
		}
		argv = append([]string{"cmd", "/c"}, rest...)
	} else if argv[0] == "docker" || argv[0] == "podman" || argv[0] == "nerdctl" || argv[0] == "wslc" {
		p, err := resolveBinary(argv[0])
		if err != nil {
			return nil, err
		}
		argv[0] = p
	}
	cmd := exec.CommandContext(ctx, argv[0], argv[1:]...)
	setHideWindow(cmd)
	return cmd, nil
}

func (r *LocalRunner) Run(ctx context.Context, argv []string) ([]byte, error) {
	cmd, err := r.command(ctx, argv)
	if err != nil {
		return nil, err
	}
	out, err := cmd.Output()
	if err != nil {
		if ee, ok := err.(*exec.ExitError); ok && len(ee.Stderr) > 0 {
			return nil, fmt.Errorf("%s", strings.TrimSpace(string(ee.Stderr)))
		}
		return nil, err
	}
	return out, nil
}

type localLineStream struct {
	lines    chan string
	done     chan error
	cancel   context.CancelFunc
	cmd      *exec.Cmd
	once     sync.Once
	waitOnce sync.Once
	waitErr  error
}

func (s *localLineStream) Lines() <-chan string { return s.lines }

// Wait 缓存结果：Close 与消费者可并发/重复调用，均拿到同一真实退出状态。
func (s *localLineStream) Wait() error {
	s.waitOnce.Do(func() { s.waitErr = <-s.done })
	return s.waitErr
}

// Close 是尽力而为的清理：取消 + 杀进程 + 等回收，不向上传播 kill 产生的错误。
func (s *localLineStream) Close() error {
	s.once.Do(func() {
		s.cancel()
		if s.cmd.Process != nil {
			_ = s.cmd.Process.Kill()
		}
		_ = s.Wait()
	})
	return nil
}

func (r *LocalRunner) RunStream(ctx context.Context, argv []string) (LineStream, error) {
	ctx, cancel := context.WithCancel(ctx)
	cmd, err := r.command(ctx, argv)
	if err != nil {
		cancel()
		return nil, err
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		cancel()
		return nil, err
	}
	cmd.Stderr = nil // logs 的 stderr 与 stdout 同义时噪音大，丢弃
	if err := cmd.Start(); err != nil {
		cancel()
		return nil, err
	}
	s := &localLineStream{lines: make(chan string, 64), done: make(chan error, 1), cancel: cancel, cmd: cmd}
	go func() {
		sc := bufio.NewScanner(stdout)
		sc.Buffer(make([]byte, 0, 256*1024), 256*1024)
		for sc.Scan() {
			s.lines <- sc.Text()
		}
		close(s.lines)
		s.done <- cmd.Wait()
	}()
	return s, nil
}
