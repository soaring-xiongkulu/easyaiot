package template

import (
	"strings"
	"testing"
)

func TestTaskDeviceIDsQueryUsesDeployedJoinColumn(t *testing.T) {
	if !strings.Contains(taskDeviceIDsQuery, "WHERE task_id = $1") {
		t.Fatalf("task-device query must use deployed algorithm_task_device.task_id column: %q", taskDeviceIDsQuery)
	}
	if strings.Contains(taskDeviceIDsQuery, "algorithm_task_id") {
		t.Fatalf("task-device query still references legacy algorithm_task_id column: %q", taskDeviceIDsQuery)
	}
}
