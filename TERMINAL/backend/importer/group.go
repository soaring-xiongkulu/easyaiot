package importer

import (
	"strings"

	"easyaiot/terminal/backend/session"
)

// ensureGroupPath find-or-creates a nested group for `path` (ordered ancestor→leaf
// names). pathMap keys are slash-joined full paths → group id, so the same path
// within one import collapses to one group. Returns a pointer to the leaf group
// id, or nil when path is empty.
func ensureGroupPath(path []string, pathMap map[string]string, groups *[]session.ConnectionGroup, newGroup func() string) *string {
	if len(path) == 0 {
		return nil
	}
	key := strings.Join(path, "/")
	if id, ok := pathMap[key]; ok {
		return &id
	}
	var parentID *string
	if len(path) > 1 {
		parentID = ensureGroupPath(path[:len(path)-1], pathMap, groups, newGroup)
	}
	id := newGroup()
	*groups = append(*groups, session.ConnectionGroup{ID: id, Name: path[len(path)-1], ParentId: parentID})
	pathMap[key] = id
	return &id
}

// groupPathFor returns the slash-joined path of a group id by walking ParentId
// within `groups`.
func groupPathFor(groups []session.ConnectionGroup, id string) string {
	byID := map[string]session.ConnectionGroup{}
	for _, g := range groups {
		byID[g.ID] = g
	}
	var segs []string
	cur := id
	for {
		g, ok := byID[cur]
		if !ok {
			break
		}
		segs = append(segs, g.Name)
		if g.ParentId == nil {
			break
		}
		cur = *g.ParentId
	}
	for i, j := 0, len(segs)-1; i < j; i, j = i+1, j-1 {
		segs[i], segs[j] = segs[j], segs[i]
	}
	return strings.Join(segs, "/")
}

// MergeImported merges imported groups/connections into existing, reusing an
// existing group when a full path matches (cross-import dedup). Connections with
// a groupId pointing at a merged group are re-pointed at the existing group id.
func MergeImported(existing, imported session.ConnectionStoreData) session.ConnectionStoreData {
	pathMap := map[string]string{}
	for _, g := range existing.Groups {
		pathMap[groupPathFor(existing.Groups, g.ID)] = g.ID
	}
	idRemap := map[string]string{} // imported id -> final id
	out := session.ConnectionStoreData{
		Groups:      append([]session.ConnectionGroup{}, existing.Groups...),
		Connections: append([]session.ConnectionConfig{}, existing.Connections...),
	}
	for _, g := range imported.Groups {
		path := groupPathFor(imported.Groups, g.ID)
		if existingID, ok := pathMap[path]; ok {
			idRemap[g.ID] = existingID
			continue
		}
		if g.ParentId != nil {
			if pid, ok := idRemap[*g.ParentId]; ok {
				g.ParentId = &pid
			}
		}
		out.Groups = append(out.Groups, g)
		idRemap[g.ID] = g.ID
		pathMap[path] = g.ID
	}
	for _, c := range imported.Connections {
		if c.GroupId != nil {
			if gid, ok := idRemap[*c.GroupId]; ok {
				c.GroupId = &gid
			}
		}
		out.Connections = append(out.Connections, c)
	}
	return out
}
