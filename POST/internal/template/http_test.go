package template

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"
	"time"
)

func templateHandler(token string) (*HTTPDeps, *http.ServeMux) {
	deps := &HTTPDeps{Cache: NewCache(time.Minute), AdminToken: token, InstanceID: "test"}
	mux := http.NewServeMux()
	deps.RegisterRoutes(mux)
	return deps, mux
}

func TestTemplateHTTPRejectsPathBodyTaskMismatch(t *testing.T) {
	deps, mux := templateHandler("")
	req := httptest.NewRequest(http.MethodPut, "/v1/tasks/7/template", strings.NewReader(
		`{"schema":"post_task_template.v1","revision":2,"task":{"id":8},"regions":[]}`,
	))
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)
	if rr.Code != http.StatusBadRequest || !strings.Contains(rr.Body.String(), "task_id mismatch") {
		t.Fatalf("status=%d body=%s", rr.Code, rr.Body.String())
	}
	if deps.Cache.Len() != 0 {
		t.Fatal("mismatched template reached cache")
	}
}

func TestTemplateHTTPDefaultsMissingBodyTaskIDToPath(t *testing.T) {
	deps, mux := templateHandler("")
	req := httptest.NewRequest(http.MethodPut, "/v1/tasks/7/template", strings.NewReader(
		`{"revision":2,"task":{"task_name":"task"},"regions":[]}`,
	))
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)
	if rr.Code != http.StatusOK {
		t.Fatalf("status=%d body=%s", rr.Code, rr.Body.String())
	}
	entry, ok := deps.Cache.Get(7)
	if !ok || entry.Template.Task.ID != 7 || entry.Template.Schema != "post_task_template.v1" {
		t.Fatalf("cached=%#v", entry)
	}
}

func TestTemplateHTTPRequiresConfiguredAdminToken(t *testing.T) {
	_, mux := templateHandler("secret")
	for _, auth := range []string{"", "Bearer wrong"} {
		req := httptest.NewRequest(http.MethodPut, "/v1/tasks/7/template", strings.NewReader(
			`{"revision":1,"task":{"id":7},"regions":[]}`,
		))
		if auth != "" {
			req.Header.Set("Authorization", auth)
		}
		rr := httptest.NewRecorder()
		mux.ServeHTTP(rr, req)
		if rr.Code != http.StatusUnauthorized {
			t.Fatalf("auth=%q status=%d", auth, rr.Code)
		}
	}
}

func TestTemplateHTTPReportsStaleUpsertWithoutReplacingCache(t *testing.T) {
	deps, mux := templateHandler("")
	deps.Cache.UpsertVersioned(testTemplate(7, 5))
	req := httptest.NewRequest(http.MethodPut, "/v1/tasks/7/template", strings.NewReader(
		`{"revision":4,"task":{"id":7,"task_name":"stale"},"regions":[]}`,
	))
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)
	var body map[string]any
	if err := json.Unmarshal(rr.Body.Bytes(), &body); err != nil {
		t.Fatal(err)
	}
	if rr.Code != http.StatusOK || body["applied"] != false {
		t.Fatalf("status=%d body=%#v", rr.Code, body)
	}
	entry, _ := deps.Cache.Get(7)
	if entry.Template.Revision != 5 {
		t.Fatalf("stale update replaced revision: %#v", entry.Template)
	}
}

func TestTemplateHTTPDeleteHonorsRevisionAndLeavesTombstone(t *testing.T) {
	deps, mux := templateHandler("")
	deps.Cache.UpsertVersioned(testTemplate(7, 5))

	for _, tc := range []struct {
		revision string
		applied  bool
	}{
		{"4", false},
		{"5", true},
	} {
		req := httptest.NewRequest(http.MethodDelete, "/v1/tasks/7/template?revision="+tc.revision, nil)
		rr := httptest.NewRecorder()
		mux.ServeHTTP(rr, req)
		var body map[string]any
		if err := json.Unmarshal(rr.Body.Bytes(), &body); err != nil {
			t.Fatal(err)
		}
		if body["applied"] != tc.applied {
			t.Fatalf("revision=%s body=%#v", tc.revision, body)
		}
	}
	if _, ok := deps.Cache.Get(7); ok || deps.Cache.Version(7) != 5 {
		t.Fatal("delete did not preserve the version tombstone")
	}
}

func TestTemplateHTTPRejectsBadPathJSONAndMethod(t *testing.T) {
	_, mux := templateHandler("")
	cases := []struct {
		method string
		path   string
		body   string
		want   int
	}{
		{http.MethodPut, "/v1/tasks/not-a-number/template", `{}`, http.StatusBadRequest},
		{http.MethodPut, "/v1/tasks/7/template", `{bad`, http.StatusBadRequest},
		{http.MethodGet, "/v1/tasks/7/template", ``, http.StatusMethodNotAllowed},
		{http.MethodPut, "/v1/tasks/7/other", `{}`, http.StatusNotFound},
	}
	for _, tc := range cases {
		req := httptest.NewRequest(tc.method, tc.path, strings.NewReader(tc.body))
		rr := httptest.NewRecorder()
		mux.ServeHTTP(rr, req)
		if rr.Code != tc.want {
			t.Fatalf("%s %s: got %d want %d", tc.method, tc.path, rr.Code, tc.want)
		}
	}
}

func TestTemplateHTTPRejectsInvalidRegionGateWithoutReplacingCache(t *testing.T) {
	deps, mux := templateHandler("")
	current := testTemplate(7, 5)
	current.Task.TaskName = "current"
	deps.Cache.UpsertVersioned(current)

	for _, body := range []string{
		`{"revision":6,"task":{"id":7,"pipeline":[{"plugin":"region_gate","params":{"hit_mode":"unknown"}}]},"regions":[]}`,
		`{"revision":6,"task":{"id":7,"pipeline":[{"plugin":"region_gate","params":{"hit_mode":"overlap_ratio","min_overlap_ratio":0}}]},"regions":[]}`,
		`{"revision":6,"task":{"id":7,"pipeline":[{"plugin":"region_gate","params":{"hit_mode":"overlap_ratio","min_overlap_ratio":"0.5"}}]},"regions":[]}`,
	} {
		req := httptest.NewRequest(http.MethodPut, "/v1/tasks/7/template", strings.NewReader(body))
		rr := httptest.NewRecorder()
		mux.ServeHTTP(rr, req)
		if rr.Code != http.StatusBadRequest || !strings.Contains(rr.Body.String(), "invalid template") {
			t.Fatalf("status=%d body=%s", rr.Code, rr.Body.String())
		}
		entry, _ := deps.Cache.Get(7)
		if entry.Template.Revision != 5 || entry.Template.Task.TaskName != "current" {
			t.Fatalf("invalid update replaced live cache: %#v", entry.Template)
		}
	}
}

func TestTemplateHTTPAcceptsNewAndLegacyRegionHitModes(t *testing.T) {
	_, mux := templateHandler("")
	for index, mode := range []string{
		"center", "bottom_center", "any_intersection", "overlap_ratio", "fully_inside",
		"any_corner", "any", "all", "bottom",
	} {
		body := `{"revision":` + strconv.Itoa(index+1) + `,"task":{"id":7,"pipeline":[{"plugin":"region_gate","params":{"hit_mode":"` + mode + `","min_overlap_ratio":0.5}}]},"regions":[]}`
		req := httptest.NewRequest(http.MethodPut, "/v1/tasks/7/template", strings.NewReader(body))
		rr := httptest.NewRecorder()
		mux.ServeHTTP(rr, req)
		if rr.Code != http.StatusOK {
			t.Fatalf("mode=%s status=%d body=%s", mode, rr.Code, rr.Body.String())
		}
	}
}

func TestTemplateHTTPValidatesRegionLevelHitConfig(t *testing.T) {
	_, mux := templateHandler("")
	for _, body := range []string{
		`{"revision":1,"task":{"id":7},"regions":[{"id":1,"device_id":"cam","region_name":"r","region_type":"polygon","points":[],"hit_mode":"unknown"}]}`,
		`{"revision":1,"task":{"id":7},"regions":[{"id":1,"device_id":"cam","region_name":"r","region_type":"polygon","points":[],"hit_mode":"overlap_ratio","min_overlap_ratio":0}]}`,
	} {
		req := httptest.NewRequest(http.MethodPut, "/v1/tasks/7/template", strings.NewReader(body))
		rr := httptest.NewRecorder()
		mux.ServeHTTP(rr, req)
		if rr.Code != http.StatusBadRequest {
			t.Fatalf("status=%d body=%s", rr.Code, rr.Body.String())
		}
	}
}
