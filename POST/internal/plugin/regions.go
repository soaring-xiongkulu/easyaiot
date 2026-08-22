package plugin

import (
	"sort"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/pipeline"
)

func activePolygonRegions(ctx *pipeline.Context) []config.Region {
	modelSet := unionModelIDs(ctx.Event.ModelIDs, ctx.Task.ModelIDs)
	var active []config.Region
	for _, r := range ctx.Regions {
		if !r.IsEnabled {
			continue
		}
		rt := r.RegionType
		if rt == "" {
			rt = "polygon"
		}
		if rt == "line" {
			continue
		}
		if rt != "polygon" && rt != "rectangle" {
			continue
		}
		if len(r.Points) < 3 {
			continue
		}
		if len(r.ModelIDs) > 0 && !intersects(r.ModelIDs, modelSet) {
			continue
		}
		active = append(active, r)
	}
	sort.SliceStable(active, func(i, j int) bool {
		return active[i].SortOrder < active[j].SortOrder
	})
	return active
}

func activeLineRegions(ctx *pipeline.Context) []config.Region {
	modelSet := unionModelIDs(ctx.Event.ModelIDs, ctx.Task.ModelIDs)
	var active []config.Region
	for _, r := range ctx.Regions {
		if !r.IsEnabled {
			continue
		}
		if r.RegionType != "line" {
			continue
		}
		if len(r.Points) < 2 {
			continue
		}
		if len(r.ModelIDs) > 0 && !intersects(r.ModelIDs, modelSet) {
			continue
		}
		active = append(active, r)
	}
	sort.SliceStable(active, func(i, j int) bool {
		return active[i].SortOrder < active[j].SortOrder
	})
	return active
}
