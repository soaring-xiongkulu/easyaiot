package log

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

var (
	mu   sync.Mutex
	file *os.File
)

func Init() error {
	mu.Lock()
	defer mu.Unlock()

	if file != nil {
		return nil
	}

	dir := filepath.Dir(logPath())
	if err := os.MkdirAll(dir, 0755); err != nil {
		return err
	}

	f, err := os.OpenFile(logPath(), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	file = f
	return nil
}

func Close() {
	mu.Lock()
	defer mu.Unlock()
	if file != nil {
		file.Close()
		file = nil
	}
}

func Writef(format string, args ...interface{}) {
	mu.Lock()
	defer mu.Unlock()

	msg := fmt.Sprintf(format, args...)
	line := fmt.Sprintf("%s %s\n", time.Now().Format("2006-01-02 15:04:05.000"), msg)

	if file != nil {
		file.WriteString(line)
		file.Sync()
	}
}
