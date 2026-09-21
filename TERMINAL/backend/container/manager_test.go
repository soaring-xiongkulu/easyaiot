package container

import "testing"

// connectLocalOrSkip 连接本机 docker；环境无可用运行时时跳过而非失败。
func connectLocalOrSkip(t *testing.T, m *Manager, id string) {
	t.Helper()
	if err := m.ConnectLocal(id, RuntimeDocker, ""); err != nil {
		t.Skipf("container runtime not available: %v", err)
	}
}

func TestManagerProviderMissing(t *testing.T) {
	m := NewManager()
	if _, err := m.Provider("nope"); err == nil {
		t.Fatal("expected error for unknown id")
	}
}

func TestManagerLocalLifecycle(t *testing.T) {
	m := NewManager()
	connectLocalOrSkip(t, m, "c1")
	if _, err := m.Provider("c1"); err != nil {
		t.Fatal(err)
	}
	m.Disconnect("c1")
	if _, err := m.Provider("c1"); err == nil {
		t.Fatal("expected error after disconnect")
	}
}

func TestManagerDoubleConnectLocal(t *testing.T) {
	m := NewManager()
	connectLocalOrSkip(t, m, "c1")
	defer m.Disconnect("c1")
	if err := m.ConnectLocal("c1", RuntimeDocker, ""); err != nil {
		t.Fatal(err)
	}
	if _, err := m.Provider("c1"); err != nil {
		t.Fatal(err)
	}
}

func TestManagerSetNamespace(t *testing.T) {
	m := NewManager()
	connectLocalOrSkip(t, m, "c1")
	defer m.Disconnect("c1")
	if err := m.SetNamespace("c1", "k8s.io"); err != nil {
		t.Fatal(err)
	}
	p, err := m.Provider("c1")
	if err != nil {
		t.Fatal(err)
	}
	if p.Namespace() != "k8s.io" {
		t.Fatalf("expected namespace k8s.io, got %q", p.Namespace())
	}
	if err := m.SetNamespace("nope", "k8s.io"); err == nil {
		t.Fatal("expected error for unknown id")
	}
}
