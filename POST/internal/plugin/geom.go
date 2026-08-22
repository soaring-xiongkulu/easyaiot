package plugin

import (
	"math"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
)

const geomEps = 1e-6

func samplePoints(bbox [4]float64, hitMode string) [][2]float64 {
	x1, y1, x2, y2 := bbox[0], bbox[1], bbox[2], bbox[3]
	cx, cy := (x1+x2)/2, (y1+y2)/2
	if hitMode == "any_corner" {
		return [][2]float64{
			{x1, y1}, {x2, y1}, {x2, y2}, {x1, y2}, {cx, cy},
		}
	}
	if hitMode == "bottom_center" {
		return [][2]float64{{cx, y2}}
	}
	return [][2]float64{{cx, cy}}
}

func scalePoints(pts []config.Point, fw, fh int) [][2]float64 {
	if len(pts) == 0 {
		return nil
	}
	normalized := true
	for _, p := range pts {
		if p.X < 0 || p.X > 1 || p.Y < 0 || p.Y > 1 {
			normalized = false
			break
		}
	}
	out := make([][2]float64, len(pts))
	for i, p := range pts {
		if normalized && fw > 0 && fh > 0 {
			out[i] = [2]float64{p.X * float64(fw), p.Y * float64(fh)}
		} else {
			out[i] = [2]float64{p.X, p.Y}
		}
	}
	return out
}

func pointInPolygon(x, y float64, poly [][2]float64) bool {
	if len(poly) < 3 {
		return false
	}
	if onBoundary(x, y, poly) {
		return true
	}
	inside := false
	n := len(poly)
	j := n - 1
	for i := 0; i < n; i++ {
		xi, yi := poly[i][0], poly[i][1]
		xj, yj := poly[j][0], poly[j][1]
		if ((yi > y) != (yj > y)) && (x < (xj-xi)*(y-yi)/(yj-yi+1e-12)+xi) {
			inside = !inside
		}
		j = i
	}
	return inside
}

func onBoundary(x, y float64, poly [][2]float64) bool {
	n := len(poly)
	j := n - 1
	for i := 0; i < n; i++ {
		if pointOnSegment(x, y, poly[j][0], poly[j][1], poly[i][0], poly[i][1], geomEps) {
			return true
		}
		j = i
	}
	return false
}

func pointOnSegment(px, py, x1, y1, x2, y2, eps float64) bool {
	cross := (px-x1)*(y2-y1) - (py-y1)*(x2-x1)
	if math.Abs(cross) > eps*math.Max(1, math.Hypot(x2-x1, y2-y1)) {
		return false
	}
	dot := (px-x1)*(x2-x1) + (py-y1)*(y2-y1)
	if dot < -eps {
		return false
	}
	len2 := (x2-x1)*(x2-x1) + (y2-y1)*(y2-y1)
	return dot <= len2+eps
}

// lineSide returns +1 (left of p0→p1), -1 (right), or 0 (on line).
func lineSide(x, y, x0, y0, x1, y1 float64) int {
	cross := (x1-x0)*(y-y0) - (y1-y0)*(x-x0)
	if cross > geomEps {
		return 1
	}
	if cross < -geomEps {
		return -1
	}
	return 0
}

func crossedSide(prev, curr int, direction string) bool {
	if prev == 0 || curr == 0 || prev == curr {
		return false
	}
	switch direction {
	case "a_to_b":
		return prev > 0 && curr < 0
	case "b_to_a":
		return prev < 0 && curr > 0
	default:
		return true
	}
}

func detectionPoint(det contract.Detection, hitMode string) [2]float64 {
	pts := samplePoints(det.BBox, hitMode)
	if len(pts) == 0 {
		return [2]float64{}
	}
	return pts[0]
}

func detectionInRegion(det contract.Detection, region config.Region, fw, fh int, hitMode string) bool {
	poly := scalePoints(region.Points, fw, fh)
	if len(poly) < 3 {
		return false
	}
	for _, pt := range samplePoints(det.BBox, hitMode) {
		if pointInPolygon(pt[0], pt[1], poly) {
			return true
		}
	}
	return false
}

func unionModelIDs(a, b []int64) map[int64]struct{} {
	out := map[int64]struct{}{}
	for _, id := range a {
		out[id] = struct{}{}
	}
	for _, id := range b {
		out[id] = struct{}{}
	}
	return out
}

func intersects(regionIDs []int64, set map[int64]struct{}) bool {
	if len(set) == 0 {
		return false
	}
	for _, id := range regionIDs {
		if _, ok := set[id]; ok {
			return true
		}
	}
	return false
}

func appendUniqueID(ids []int64, id int64) []int64 {
	for _, x := range ids {
		if x == id {
			return ids
		}
	}
	return append(ids, id)
}

func appendUniqueStr(ss []string, s string) []string {
	for _, x := range ss {
		if x == s {
			return ss
		}
	}
	return append(ss, s)
}

func classAllowed(className string, allow []string) bool {
	if len(allow) == 0 {
		return true
	}
	for _, c := range allow {
		if c == className {
			return true
		}
	}
	return false
}
