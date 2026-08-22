package template

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log/slog"
	"strings"
	"time"

	_ "github.com/lib/pq"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
)

// Store loads running task templates from the business DB (warmup / reload only).
type Store struct {
	db *sql.DB
}

func OpenStore(databaseURL string) (*Store, error) {
	databaseURL = config.NormalizePostgresURL(databaseURL)
	if strings.TrimSpace(databaseURL) == "" {
		return nil, fmt.Errorf("DATABASE_URL empty")
	}
	db, err := sql.Open("postgres", databaseURL)
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(4)
	db.SetConnMaxLifetime(time.Minute)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		_ = db.Close()
		return nil, err
	}
	return &Store{db: db}, nil
}

func (s *Store) Close() error {
	if s == nil || s.db == nil {
		return nil
	}
	return s.db.Close()
}

// LoadRunningTemplates loads run_status=running tasks into snapshots.
func (s *Store) LoadRunningTemplates(ctx context.Context) ([]config.TaskTemplate, error) {
	rows, err := s.db.QueryContext(ctx, `
		SELECT id, task_name, task_type, COALESCE(model_ids,''), COALESCE(post_pipeline,''),
		       COALESCE(post_process_script,''), COALESCE(alert_event_enabled,false)
		FROM algorithm_task
		WHERE run_status = 'running'`)
	if err != nil {
		// post_pipeline may be missing on older DBs — retry without it
		if strings.Contains(err.Error(), "post_pipeline") {
			return s.loadRunningWithoutPipeline(ctx)
		}
		return nil, err
	}
	defer rows.Close()

	var out []config.TaskTemplate
	for rows.Next() {
		var id int64
		var name, taskType, modelIDsRaw, pipelineRaw, script string
		var alertEnabled bool
		if err := rows.Scan(&id, &name, &taskType, &modelIDsRaw, &pipelineRaw, &script, &alertEnabled); err != nil {
			return nil, err
		}
		tpl, err := s.buildTemplate(ctx, id, name, taskType, modelIDsRaw, pipelineRaw, script)
		if err != nil {
			slog.Warn("warmup_skip_task", "task_id", id, "err", err)
			continue
		}
		out = append(out, tpl)
	}
	return out, rows.Err()
}

func (s *Store) loadRunningWithoutPipeline(ctx context.Context) ([]config.TaskTemplate, error) {
	rows, err := s.db.QueryContext(ctx, `
		SELECT id, task_name, task_type, COALESCE(model_ids,''), COALESCE(post_process_script,'')
		FROM algorithm_task WHERE run_status = 'running'`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []config.TaskTemplate
	for rows.Next() {
		var id int64
		var name, taskType, modelIDsRaw, script string
		if err := rows.Scan(&id, &name, &taskType, &modelIDsRaw, &script); err != nil {
			return nil, err
		}
		tpl, err := s.buildTemplate(ctx, id, name, taskType, modelIDsRaw, "", script)
		if err != nil {
			continue
		}
		out = append(out, tpl)
	}
	return out, rows.Err()
}

func (s *Store) buildTemplate(ctx context.Context, id int64, name, taskType, modelIDsRaw, pipelineRaw, script string) (config.TaskTemplate, error) {
	deviceIDs, err := s.taskDeviceIDs(ctx, id)
	if err != nil {
		return config.TaskTemplate{}, err
	}
	regions, err := s.loadRegions(ctx, deviceIDs)
	if err != nil {
		return config.TaskTemplate{}, err
	}
	var modelIDs []int64
	_ = json.Unmarshal([]byte(nullJSONArray(modelIDsRaw)), &modelIDs)
	var steps []config.PipelineStep
	if strings.TrimSpace(pipelineRaw) != "" {
		_ = json.Unmarshal([]byte(pipelineRaw), &steps)
	}
	return config.TaskTemplate{
		Schema: contract.SchemaTaskTemplate,
		Task: config.TaskConfig{
			ID: id, TaskName: name, TaskType: taskType,
			ModelIDs: modelIDs, Pipeline: steps, PostProcessScript: script,
			AlertEvent: "检测告警",
		},
		Regions: regions,
	}, nil
}

func (s *Store) taskDeviceIDs(ctx context.Context, taskID int64) ([]string, error) {
	rows, err := s.db.QueryContext(ctx, `
		SELECT device_id FROM algorithm_task_device WHERE algorithm_task_id = $1`, taskID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var ids []string
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			return nil, err
		}
		ids = append(ids, id)
	}
	return ids, rows.Err()
}

func (s *Store) loadRegions(ctx context.Context, deviceIDs []string) ([]config.Region, error) {
	if len(deviceIDs) == 0 {
		return nil, nil
	}
	// build IN clause
	args := make([]any, len(deviceIDs))
	placeholders := make([]string, len(deviceIDs))
	for i, id := range deviceIDs {
		args[i] = id
		placeholders[i] = fmt.Sprintf("$%d", i+1)
	}
	q := fmt.Sprintf(`
		SELECT id, device_id, region_name, COALESCE(region_type,'polygon'), points,
		       COALESCE(is_enabled,true), COALESCE(sort_order,0), COALESCE(model_ids,'')
		FROM device_detection_region
		WHERE device_id IN (%s) AND COALESCE(is_enabled,true) = true`, strings.Join(placeholders, ","))
	rows, err := s.db.QueryContext(ctx, q, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []config.Region
	for rows.Next() {
		var r config.Region
		var pointsRaw, modelRaw string
		if err := rows.Scan(&r.ID, &r.DeviceID, &r.RegionName, &r.RegionType, &pointsRaw, &r.IsEnabled, &r.SortOrder, &modelRaw); err != nil {
			return nil, err
		}
		r.Points = normalizePoints(pointsRaw)
		_ = json.Unmarshal([]byte(nullJSONArray(modelRaw)), &r.ModelIDs)
		out = append(out, r)
	}
	return out, rows.Err()
}

func normalizePoints(raw string) []config.Point {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return nil
	}
	var pts []config.Point
	if err := json.Unmarshal([]byte(raw), &pts); err == nil && len(pts) > 0 {
		return pts
	}
	// try [][]float64
	var arr [][]float64
	if err := json.Unmarshal([]byte(raw), &arr); err == nil {
		for _, a := range arr {
			if len(a) >= 2 {
				pts = append(pts, config.Point{X: a[0], Y: a[1]})
			}
		}
	}
	return pts
}

func nullJSONArray(s string) string {
	s = strings.TrimSpace(s)
	if s == "" {
		return "[]"
	}
	return s
}

// Warmup loads running tasks into cache. Returns count.
func Warmup(ctx context.Context, store *Store, cache *Cache) (int, error) {
	if store == nil {
		return 0, fmt.Errorf("store nil")
	}
	tpls, err := store.LoadRunningTemplates(ctx)
	if err != nil {
		return 0, err
	}
	for _, t := range tpls {
		cache.Upsert(t)
	}
	return len(tpls), nil
}
