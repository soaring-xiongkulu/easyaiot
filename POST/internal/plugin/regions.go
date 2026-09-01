package plugin

import (
	"sort"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/pipeline"
)

func activePolygonRegions(ctx *pipeline.Context) []config.Region {
	return activePolygonRegionsForModel(ctx, nil, false)
}

func activePolygonRegionsForDetection(ctx *pipeline.Context, modelID *int64) []config.Region {
	return activePolygonRegionsForModel(ctx, modelID, true)
}

func activePolygonRegionsForModel(ctx *pipeline.Context, modelID *int64, filterModel bool) []config.Region {
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
		if filterModel && !regionAppliesToModel(r.ModelIDs, modelID) {
			continue
		}
		active = append(active, r)
	}
	sort.SliceStable(active, func(i, j int) bool {
		if active[i].SortOrder == active[j].SortOrder {
			return active[i].ID < active[j].ID
		}
		return active[i].SortOrder < active[j].SortOrder
	})
	return active
}

func activeLineRegions(ctx *pipeline.Context) []config.Region {
	return activeLineRegionsForModel(ctx, nil, false)
}

func activeLineRegionsForDetection(ctx *pipeline.Context, modelID *int64) []config.Region {
	return activeLineRegionsForModel(ctx, modelID, true)
}

func activeLineRegionsForModel(ctx *pipeline.Context, modelID *int64, filterModel bool) []config.Region {
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
		if filterModel && !regionAppliesToModel(r.ModelIDs, modelID) {
			continue
		}
		active = append(active, r)
	}
	sort.SliceStable(active, func(i, j int) bool {
		if active[i].SortOrder == active[j].SortOrder {
			return active[i].ID < active[j].ID
		}
		return active[i].SortOrder < active[j].SortOrder
	})
	return active
}
