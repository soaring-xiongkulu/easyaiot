package container

import "testing"

// 编译期接口合规断言：SSHRunner 必须实现冻结的 Runner 接口。
var _ Runner = (*SSHRunner)(nil)

// JoinShellCommand 已在 Task 2 测；这里测 detectArgs 经 shell 的形态。
func TestDetectArgs(t *testing.T) {
	got := JoinShellCommand(detectArgs(RuntimePodman))
	want := "sh -c 'command -v podman'"
	if got != want {
		t.Fatalf("got %q want %q", got, want)
	}
}
