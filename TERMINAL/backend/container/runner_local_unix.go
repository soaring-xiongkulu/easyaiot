//go:build !windows

package container

import (
	"context"
	"os"
	"os/exec"
	"sync"

	"github.com/creack/pty"
)

func setHideWindow(_ *exec.Cmd) {}

type localPTY struct {
	cmd  *exec.Cmd
	ptmx *os.File
	data chan []byte
	mu   sync.Mutex
	once sync.Once
}

func (r *LocalRunner) RunPTY(_ context.Context, argv []string, cols, rows int) (PTYStream, error) {
	if p, err := resolveBinary(argv[0]); err == nil {
		argv[0] = p
	}
	cmd := exec.Command(argv[0], argv[1:]...)
	ws := &pty.Winsize{Cols: uint16(cols), Rows: uint16(rows)}
	ptmx, err := pty.StartWithSize(cmd, ws)
	if err != nil {
		return nil, err
	}
	p := &localPTY{cmd: cmd, ptmx: ptmx, data: make(chan []byte, 32)}
	go func() {
		buf := make([]byte, 4096)
		for {
			n, err := ptmx.Read(buf)
			if n > 0 {
				cp := make([]byte, n)
				copy(cp, buf[:n])
				p.data <- cp
			}
			if err != nil {
				close(p.data)
				return
			}
		}
	}()
	return p, nil
}

func (p *localPTY) Data() <-chan []byte { return p.data }
func (p *localPTY) Write(b []byte) error {
	p.mu.Lock()
	defer p.mu.Unlock()
	_, err := p.ptmx.Write(b)
	return err
}
func (p *localPTY) Resize(cols, rows int) error {
	return pty.Setsize(p.ptmx, &pty.Winsize{Cols: uint16(cols), Rows: uint16(rows)})
}
func (p *localPTY) Close() error {
	var err error
	p.once.Do(func() {
		_ = p.ptmx.Close()
		if p.cmd.Process != nil {
			_ = p.cmd.Process.Kill()
		}
		err = p.cmd.Wait()
	})
	return err
}
