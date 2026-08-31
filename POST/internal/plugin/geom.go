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
	if hitMode == "any_corner" || hitMode == "any" || hitMode == "all" {
		return [][2]float64{
			{x1, y1}, {x2, y1}, {x2, y2}, {x1, y2}, {cx, cy},
		}
	}
	if hitMode == "bottom_center" || hitMode == "bottom" {
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
	return detectionMatchesRegion(det, region, fw, fh, hitMode, 0.5)
}

func detectionMatchesRegion(
	det contract.Detection,
	region config.Region,
	fw, fh int,
	hitMode string,
	minOverlapRatio float64,
) bool {
	poly := scalePoints(region.Points, fw, fh)
	if len(poly) < 3 {
		return false
	}
	switch hitMode {
	case "any_intersection":
		rect, ok := normalizedRect(det.BBox)
		return ok && polygonIntersectsRect(poly, rect)
	case "overlap_ratio":
		ratio, ok := bboxPolygonOverlapRatio(det.BBox, poly)
		return ok && ratio+geomEps >= minOverlapRatio
	case "fully_inside":
		ratio, ok := bboxPolygonOverlapRatio(det.BBox, poly)
		return ok && ratio >= 1-geomEps
	}
	for _, pt := range samplePoints(det.BBox, hitMode) {
		if pointInPolygon(pt[0], pt[1], poly) {
			return true
		}
	}
	return false
}

type rectBounds struct {
	minX float64
	minY float64
	maxX float64
	maxY float64
}

func normalizedRect(bbox [4]float64) (rectBounds, bool) {
	r := rectBounds{
		minX: math.Min(bbox[0], bbox[2]),
		minY: math.Min(bbox[1], bbox[3]),
		maxX: math.Max(bbox[0], bbox[2]),
		maxY: math.Max(bbox[1], bbox[3]),
	}
	return r, r.maxX-r.minX > geomEps && r.maxY-r.minY > geomEps
}

func bboxPolygonOverlapRatio(bbox [4]float64, poly [][2]float64) (float64, bool) {
	rect, ok := normalizedRect(bbox)
	if !ok {
		return 0, false
	}
	triangles, ok := triangulateSimplePolygon(poly)
	if !ok {
		return 0, false
	}
	intersectionArea := 0.0
	for _, triangle := range triangles {
		clipped := clipPolygonToRect(triangle[:], rect)
		intersectionArea += math.Abs(signedPolygonArea(clipped))
	}
	bboxArea := (rect.maxX - rect.minX) * (rect.maxY - rect.minY)
	ratio := intersectionArea / bboxArea
	return math.Max(0, math.Min(1, ratio)), true
}

func polygonIntersectsRect(poly [][2]float64, rect rectBounds) bool {
	for _, pt := range rectCorners(rect) {
		if pointInPolygon(pt[0], pt[1], poly) {
			return true
		}
	}
	for _, pt := range poly {
		if pointInRect(pt, rect) {
			return true
		}
	}
	rectPts := rectCorners(rect)
	for i := range poly {
		p1 := poly[i]
		p2 := poly[(i+1)%len(poly)]
		for j := range rectPts {
			q1 := rectPts[j]
			q2 := rectPts[(j+1)%len(rectPts)]
			if segmentsIntersect(p1, p2, q1, q2) {
				return true
			}
		}
	}
	return false
}

func rectCorners(rect rectBounds) [][2]float64 {
	return [][2]float64{
		{rect.minX, rect.minY},
		{rect.maxX, rect.minY},
		{rect.maxX, rect.maxY},
		{rect.minX, rect.maxY},
	}
}

func pointInRect(pt [2]float64, rect rectBounds) bool {
	return pt[0] >= rect.minX-geomEps && pt[0] <= rect.maxX+geomEps &&
		pt[1] >= rect.minY-geomEps && pt[1] <= rect.maxY+geomEps
}

func segmentsIntersect(a, b, c, d [2]float64) bool {
	o1 := orientation(a, b, c)
	o2 := orientation(a, b, d)
	o3 := orientation(c, d, a)
	o4 := orientation(c, d, b)
	if o1 != o2 && o3 != o4 {
		return true
	}
	return (o1 == 0 && pointOnSegment(c[0], c[1], a[0], a[1], b[0], b[1], geomEps)) ||
		(o2 == 0 && pointOnSegment(d[0], d[1], a[0], a[1], b[0], b[1], geomEps)) ||
		(o3 == 0 && pointOnSegment(a[0], a[1], c[0], c[1], d[0], d[1], geomEps)) ||
		(o4 == 0 && pointOnSegment(b[0], b[1], c[0], c[1], d[0], d[1], geomEps))
}

func orientation(a, b, c [2]float64) int {
	cross := (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
	if cross > geomEps {
		return 1
	}
	if cross < -geomEps {
		return -1
	}
	return 0
}

func signedPolygonArea(poly [][2]float64) float64 {
	if len(poly) < 3 {
		return 0
	}
	doubleArea := 0.0
	for i := range poly {
		j := (i + 1) % len(poly)
		doubleArea += poly[i][0]*poly[j][1] - poly[j][0]*poly[i][1]
	}
	return doubleArea / 2
}

func cleanPolygon(poly [][2]float64) [][2]float64 {
	cleaned := make([][2]float64, 0, len(poly))
	for _, pt := range poly {
		if len(cleaned) == 0 || math.Hypot(pt[0]-cleaned[len(cleaned)-1][0], pt[1]-cleaned[len(cleaned)-1][1]) > geomEps {
			cleaned = append(cleaned, pt)
		}
	}
	if len(cleaned) > 1 && math.Hypot(cleaned[0][0]-cleaned[len(cleaned)-1][0], cleaned[0][1]-cleaned[len(cleaned)-1][1]) <= geomEps {
		cleaned = cleaned[:len(cleaned)-1]
	}
	return cleaned
}

// triangulateSimplePolygon uses ear clipping so overlap area remains correct for concave regions.
func triangulateSimplePolygon(poly [][2]float64) ([][3][2]float64, bool) {
	poly = cleanPolygon(poly)
	if len(poly) < 3 {
		return nil, false
	}
	area := signedPolygonArea(poly)
	if math.Abs(area) <= geomEps {
		return nil, false
	}
	orientationSign := 1.0
	if area < 0 {
		orientationSign = -1
	}
	indices := make([]int, len(poly))
	for i := range indices {
		indices[i] = i
	}
	triangles := make([][3][2]float64, 0, len(poly)-2)
	for len(indices) > 3 {
		earFound := false
		for pos := range indices {
			prev := indices[(pos-1+len(indices))%len(indices)]
			curr := indices[pos]
			next := indices[(pos+1)%len(indices)]
			a, b, c := poly[prev], poly[curr], poly[next]
			cross := (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
			if orientationSign*cross <= geomEps {
				continue
			}
			containsVertex := false
			for _, idx := range indices {
				if idx == prev || idx == curr || idx == next {
					continue
				}
				if pointInTriangle(poly[idx], a, b, c) {
					containsVertex = true
					break
				}
			}
			if containsVertex {
				continue
			}
			triangles = append(triangles, [3][2]float64{a, b, c})
			indices = append(indices[:pos], indices[pos+1:]...)
			earFound = true
			break
		}
		if !earFound {
			return nil, false
		}
	}
	triangles = append(triangles, [3][2]float64{poly[indices[0]], poly[indices[1]], poly[indices[2]]})
	return triangles, true
}

func pointInTriangle(p, a, b, c [2]float64) bool {
	d1 := triangleCross(p, a, b)
	d2 := triangleCross(p, b, c)
	d3 := triangleCross(p, c, a)
	hasNegative := d1 < -geomEps || d2 < -geomEps || d3 < -geomEps
	hasPositive := d1 > geomEps || d2 > geomEps || d3 > geomEps
	return !(hasNegative && hasPositive)
}

func triangleCross(p, a, b [2]float64) float64 {
	return (p[0]-b[0])*(a[1]-b[1]) - (a[0]-b[0])*(p[1]-b[1])
}

func clipPolygonToRect(poly [][2]float64, rect rectBounds) [][2]float64 {
	type boundary struct {
		inside    func([2]float64) bool
		intersect func([2]float64, [2]float64) [2]float64
	}
	boundaries := []boundary{
		{
			inside: func(p [2]float64) bool { return p[0] >= rect.minX-geomEps },
			intersect: func(a, b [2]float64) [2]float64 {
				return verticalIntersection(a, b, rect.minX)
			},
		},
		{
			inside: func(p [2]float64) bool { return p[0] <= rect.maxX+geomEps },
			intersect: func(a, b [2]float64) [2]float64 {
				return verticalIntersection(a, b, rect.maxX)
			},
		},
		{
			inside: func(p [2]float64) bool { return p[1] >= rect.minY-geomEps },
			intersect: func(a, b [2]float64) [2]float64 {
				return horizontalIntersection(a, b, rect.minY)
			},
		},
		{
			inside: func(p [2]float64) bool { return p[1] <= rect.maxY+geomEps },
			intersect: func(a, b [2]float64) [2]float64 {
				return horizontalIntersection(a, b, rect.maxY)
			},
		},
	}
	out := append([][2]float64(nil), poly...)
	for _, edge := range boundaries {
		if len(out) == 0 {
			break
		}
		input := out
		out = nil
		prev := input[len(input)-1]
		prevInside := edge.inside(prev)
		for _, curr := range input {
			currInside := edge.inside(curr)
			if currInside {
				if !prevInside {
					out = append(out, edge.intersect(prev, curr))
				}
				out = append(out, curr)
			} else if prevInside {
				out = append(out, edge.intersect(prev, curr))
			}
			prev, prevInside = curr, currInside
		}
	}
	return out
}

func verticalIntersection(a, b [2]float64, x float64) [2]float64 {
	if math.Abs(b[0]-a[0]) <= geomEps {
		return [2]float64{x, a[1]}
	}
	t := (x - a[0]) / (b[0] - a[0])
	return [2]float64{x, a[1] + t*(b[1]-a[1])}
}

func horizontalIntersection(a, b [2]float64, y float64) [2]float64 {
	if math.Abs(b[1]-a[1]) <= geomEps {
		return [2]float64{a[0], y}
	}
	t := (y - a[1]) / (b[1] - a[1])
	return [2]float64{a[0] + t*(b[0]-a[0]), y}
}

func regionAppliesToModel(regionIDs []int64, modelID *int64) bool {
	if len(regionIDs) == 0 {
		return true
	}
	if modelID == nil {
		return false
	}
	for _, id := range regionIDs {
		if id == *modelID {
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
