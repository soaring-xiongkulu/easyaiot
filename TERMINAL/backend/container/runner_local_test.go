package container

import (
	"context"
	"runtime"
	"testing"
	"time"
)

func TestLocalRunnerRun(t *testing.T) {
	r := NewLocalRunner()
	var out []byte
	var err error
	if runtime.GOOS == "windows" {
		out, err = r.Run(context.Background(), []string{"cmd", "/c", "echo", "hello"})
	} else {
		out, err = r.Run(context.Background(), []string{"echo", "hello"})
	}
	if err != nil {
		t.Fatal(err)
	}
	if string(out) == "" {
		t.Fatal("empty output")
	}
}

func TestResolveBinaryNotFound(t *testing.T) {
	if _, err := resolveBinary("definitely-not-exist-bin-xyz"); err == nil {
		t.Fatal("expected error")
	}
}

func TestLocalLineStreamWaitCloseNoDeadlock(t *testing.T) {
	r := NewLocalRunner()
	var argv []string
	if runtime.GOOS == "windows" {
		argv = []string{"cmd", "/c", "echo", "hi"}
	} else {
		argv = []string{"echo", "hi"}
	}
	stream, err := r.RunStream(context.Background(), argv)
	if err != nil {
		t.Fatal(err)
	}
	for range stream.Lines() {
	}
	done := make(chan struct{})
	go func() {
		defer close(done)
		err1 := stream.Wait()
		err2 := stream.Wait()
		if err1 != err2 {
			t.Errorf("Wait not idempotent: %v vs %v", err1, err2)
		}
		_ = stream.Close()
	}()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("deadlock")
	}
}
