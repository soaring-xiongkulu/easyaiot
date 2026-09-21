package container

import (
	"reflect"
	"testing"
)

func TestPSArgs(t *testing.T) {
	got := psArgs(RuntimeDocker, "")
	want := []string{"docker", "ps", "-a", "--format", "{{json .}}"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
}

func TestPSArgsNerdctlNamespace(t *testing.T) {
	got := psArgs(RuntimeNerdctl, "k8s.io")
	want := []string{"nerdctl", "--namespace", "k8s.io", "ps", "-a", "--format", "{{json .}}"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
}

func TestExecArgs(t *testing.T) {
	got := execArgs(RuntimeDocker, "", "abc123", "sh")
	want := []string{"docker", "exec", "-it", "abc123", "sh"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
}

func TestJoinShellCommand(t *testing.T) {
	got := JoinShellCommand([]string{"docker", "exec", "-it", "my'container", "sh"})
	want := `docker exec -it 'my'\''container' sh`
	if got != want {
		t.Fatalf("got %q want %q", got, want)
	}
}

func TestPSArgsWSLC(t *testing.T) {
	got := psArgs(RuntimeWSLC, "")
	want := []string{"wslc", "ps", "-a", "--format", "json"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
}

func TestImagesArgsWSLC(t *testing.T) {
	got := imagesArgs(RuntimeWSLC, "")
	want := []string{"wslc", "images", "--format", "json"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
}

func TestStatsArgsWSLC(t *testing.T) {
	got := statsArgs(RuntimeWSLC, "")
	want := []string{"wslc", "stats", "--format", "json"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
}

func TestActionArgsWSLCStart(t *testing.T) {
	got, err := actionArgs(RuntimeWSLC, "", "start", "abc123")
	if err != nil {
		t.Fatal(err)
	}
	want := []string{"wslc", "start", "abc123"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
}

func TestActionArgsWSLCStop(t *testing.T) {
	got, err := actionArgs(RuntimeWSLC, "", "stop", "abc123")
	if err != nil {
		t.Fatal(err)
	}
	want := []string{"wslc", "stop", "abc123"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
}

func TestActionArgsWSLCRm(t *testing.T) {
	got, err := actionArgs(RuntimeWSLC, "", "rm", "abc123")
	if err != nil {
		t.Fatal(err)
	}
	want := []string{"wslc", "rm", "abc123"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
}

func TestActionArgsWSLCUnsupported(t *testing.T) {
	for _, act := range []string{"restart", "pause", "unpause"} {
		if _, err := actionArgs(RuntimeWSLC, "", act, "abc123"); err == nil {
			t.Errorf("action %q should be unsupported for WSLC", act)
		}
	}
}

func TestDetectArgsWSLC(t *testing.T) {
	got := detectArgs(RuntimeWSLC)
	want := []string{"sh", "-c", "command -v wslc"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
}
