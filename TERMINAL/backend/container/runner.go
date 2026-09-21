package container

import "context"

// LineStream 是 logs -f / pull 这类流式命令的行通道。
type LineStream interface {
	Lines() <-chan string
	Wait() error
	Close() error
}

// PTYStream 是 exec 终端的双工通道。
type PTYStream interface {
	Data() <-chan []byte
	Write(p []byte) error
	Resize(cols, rows int) error
	Close() error
}

type Runner interface {
	Run(ctx context.Context, argv []string) ([]byte, error)
	RunStream(ctx context.Context, argv []string) (LineStream, error)
	RunPTY(ctx context.Context, argv []string, cols, rows int) (PTYStream, error)
}
