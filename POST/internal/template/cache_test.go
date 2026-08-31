package template

import (
	"testing"
	"time"

	"easyaiot/post/internal/config"
)

func testTemplate(taskID, revision int64) config.TaskTemplate {
	return config.TaskTemplate{
		Schema:   "post_task_template.v1",
		Revision: revision,
		Task:     config.TaskConfig{ID: taskID, TaskName: "task"},
	}
}

func TestCacheRejectsStaleUpsert(t *testing.T) {
	cache := NewCache(time.Minute)
	if _, applied := cache.UpsertVersioned(testTemplate(1, 3)); !applied {
		t.Fatal("initial upsert not applied")
	}
	if _, applied := cache.UpsertVersioned(testTemplate(1, 2)); applied {
		t.Fatal("stale upsert applied")
	}
	entry, ok := cache.Get(1)
	if !ok || entry.Template.Revision != 3 {
		t.Fatalf("unexpected cache entry: %#v", entry)
	}
}

func TestCacheDeleteTombstonePreventsResurrection(t *testing.T) {
	cache := NewCache(time.Minute)
	cache.UpsertVersioned(testTemplate(1, 3))
	if !cache.DeleteVersioned(1, 4) {
		t.Fatal("delete not applied")
	}
	if _, applied := cache.UpsertVersioned(testTemplate(1, 3)); applied {
		t.Fatal("stale template resurrected deleted task")
	}
	if _, ok := cache.Get(1); ok {
		t.Fatal("deleted task is present")
	}
	if _, applied := cache.UpsertVersioned(testTemplate(1, 5)); !applied {
		t.Fatal("newer template not applied")
	}
}

func TestCacheDeleteTombstoneRejectsEqualRevisionUpsert(t *testing.T) {
	cache := NewCache(time.Minute)
	cache.UpsertVersioned(testTemplate(1, 4))
	if !cache.DeleteVersioned(1, 4) {
		t.Fatal("equal revision delete not applied")
	}
	if _, applied := cache.UpsertVersioned(testTemplate(1, 4)); applied {
		t.Fatal("equal revision upsert resurrected a tombstoned task")
	}
	if _, ok := cache.Get(1); ok {
		t.Fatal("tombstoned task is present")
	}
}

func TestCacheEqualRevisionUpsertIsIdempotentForLiveEntry(t *testing.T) {
	cache := NewCache(time.Minute)
	if _, applied := cache.UpsertVersioned(testTemplate(1, 4)); !applied {
		t.Fatal("initial upsert not applied")
	}
	tpl := testTemplate(1, 4)
	tpl.Task.TaskName = "refreshed"
	if _, applied := cache.UpsertVersioned(tpl); !applied {
		t.Fatal("equal revision refresh should be idempotently applied")
	}
	entry, ok := cache.Get(1)
	if !ok || entry.Template.Task.TaskName != "refreshed" {
		t.Fatalf("equal revision refresh not visible: %#v", entry)
	}
}

func TestCacheRejectsRevisionZeroAfterPositiveRevision(t *testing.T) {
	cache := NewCache(time.Minute)
	cache.UpsertVersioned(testTemplate(1, 2))
	if _, applied := cache.UpsertVersioned(testTemplate(1, 0)); applied {
		t.Fatal("legacy revision zero replaced a versioned template")
	}
	if cache.DeleteVersioned(1, 0) {
		t.Fatal("legacy revision zero deleted a versioned template")
	}
}

func TestCacheRegionsRemainIsolatedByTaskAndDevice(t *testing.T) {
	cache := NewCache(time.Minute)
	for _, taskID := range []int64{1, 2} {
		tpl := testTemplate(taskID, 1)
		tpl.Regions = []config.Region{{
			ID: taskID * 10, DeviceID: "shared-cam", RegionName: tpl.Task.TaskName,
			RegionType: "polygon", IsEnabled: true,
		}}
		cache.UpsertVersioned(tpl)
	}
	one, _ := cache.RegionsForDevice(1, "shared-cam")
	two, _ := cache.RegionsForDevice(2, "shared-cam")
	if len(one) != 1 || one[0].ID != 10 || len(two) != 1 || two[0].ID != 20 {
		t.Fatalf("cross-task region leak: task1=%#v task2=%#v", one, two)
	}
}
