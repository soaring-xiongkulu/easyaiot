package container

import (
	"bufio"
	"bytes"
	"context"
	"fmt"
	"io"
	"strings"
	"sync"

	"golang.org/x/crypto/ssh"
)

type SSHRunner struct {
	client *ssh.Client
}

func NewSSHRunner(client *ssh.Client) *SSHRunner { return &SSHRunner{client: client} }
func (r *SSHRunner) Client() *ssh.Client         { return r.client }

func (r *SSHRunner) Run(_ context.Context, argv []string) ([]byte, error) {
	sess, err := r.client.NewSession()
	if err != nil {
		return nil, err
	}
	defer sess.Close()
	var stdout, stderr bytes.Buffer
	sess.Stdout = &stdout
	sess.Stderr = &stderr
	if err := sess.Run(JoinShellCommand(argv)); err != nil {
		if msg := strings.TrimSpace(stderr.String()); msg != "" {
			return nil, fmt.Errorf("%s", msg)
		}
		return nil, err
	}
	return stdout.Bytes(), nil
}

type sshLineStream struct {
	lines    chan string
	done     chan error
	sess     *ssh.Session
	once     sync.Once
	waitOnce sync.Once
	waitErr  error
}

func (s *sshLineStream) Lines() <-chan string { return s.lines }

// Wait 缓存结果：Close 与消费者可并发/重复调用，均拿到同一真实退出状态。
func (s *sshLineStream) Wait() error {
	s.waitOnce.Do(func() { s.waitErr = <-s.done })
	return s.waitErr
}

// Close 尽力而为：关闭会话（远端进程随之终止）并等回收，不传播错误。
func (s *sshLineStream) Close() error {
	s.once.Do(func() {
		_ = s.sess.Close()
		_ = s.Wait()
	})
	return nil
}

func (r *SSHRunner) RunStream(_ context.Context, argv []string) (LineStream, error) {
	sess, err := r.client.NewSession()
	if err != nil {
		return nil, err
	}
	stdout, err := sess.StdoutPipe()
	if err != nil {
		sess.Close()
		return nil, err
	}
	if err := sess.Start(JoinShellCommand(argv)); err != nil {
		sess.Close()
		return nil, err
	}
	s := &sshLineStream{lines: make(chan string, 64), done: make(chan error, 1), sess: sess}
	go func() {
		sc := bufio.NewScanner(stdout)
		sc.Buffer(make([]byte, 0, 256*1024), 256*1024)
		for sc.Scan() {
			s.lines <- sc.Text()
		}
		close(s.lines)
		s.done <- sess.Wait()
	}()
	return s, nil
}

type sshPTY struct {
	sess  *ssh.Session
	stdin io.Writer
	data  chan []byte
	mu    sync.Mutex
	once  sync.Once
}

func (r *SSHRunner) RunPTY(_ context.Context, argv []string, cols, rows int) (PTYStream, error) {
	sess, err := r.client.NewSession()
	if err != nil {
		return nil, err
	}
	modes := ssh.TerminalModes{ssh.ECHO: 1, ssh.TTY_OP_ISPEED: 14400, ssh.TTY_OP_OSPEED: 14400}
	if err := sess.RequestPty("xterm-256color", rows, cols, modes); err != nil {
		sess.Close()
		return nil, err
	}
	stdin, err := sess.StdinPipe()
	if err != nil {
		sess.Close()
		return nil, err
	}
	stdout, err := sess.StdoutPipe()
	if err != nil {
		sess.Close()
		return nil, err
	}
	if err := sess.Start(JoinShellCommand(argv)); err != nil {
		sess.Close()
		return nil, err
	}
	p := &sshPTY{sess: sess, stdin: stdin, data: make(chan []byte, 32)}
	go func() {
		buf := make([]byte, 4096)
		for {
			n, err := stdout.Read(buf)
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

func (p *sshPTY) Data() <-chan []byte { return p.data }
func (p *sshPTY) Write(b []byte) error {
	p.mu.Lock()
	defer p.mu.Unlock()
	_, err := p.stdin.Write(b)
	return err
}
func (p *sshPTY) Resize(cols, rows int) error { return p.sess.WindowChange(rows, cols) }
func (p *sshPTY) Close() error {
	var err error
	p.once.Do(func() { err = p.sess.Close() })
	return err
}
