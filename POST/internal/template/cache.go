package template

import (
	"sync"
	"time"

	"easyaiot/post/internal/config"
)

// Entry is a cached task template with expiry.
type Entry struct {
	Template  config.TaskTemplate
	ExpiresAt time.Time
	ByDevice  map[string][]config.Region
}

// Cache is an in-process TTL map (no Redis).
type Cache struct {
	mu        sync.RWMutex
	ttl       time.Duration
	m         map[int64]*Entry
	versions  map[int64]int64
	tombstone map[int64]bool
}

func NewCache(ttl time.Duration) *Cache {
	return &Cache{
		ttl: ttl, m: make(map[int64]*Entry), versions: make(map[int64]int64),
		tombstone: make(map[int64]bool),
	}
}

func (c *Cache) Upsert(tpl config.TaskTemplate) time.Time {
	exp, _ := c.UpsertVersioned(tpl)
	return exp
}

func (c *Cache) UpsertVersioned(tpl config.TaskTemplate) (time.Time, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	exp := time.Now().Add(c.ttl)
	id := tpl.Task.ID
	if current, ok := c.versions[id]; ok {
		if tpl.Revision < current || (tpl.Revision == current && c.tombstone[id]) {
			return exp, false
		}
	}
	c.m[id] = &Entry{
		Template:  tpl,
		ExpiresAt: exp,
		ByDevice:  config.RegionsByDevice(tpl.Regions),
	}
	c.versions[id] = tpl.Revision
	delete(c.tombstone, id)
	return exp, true
}

func (c *Cache) Delete(taskID int64) {
	c.DeleteVersioned(taskID, c.Version(taskID))
}

func (c *Cache) DeleteVersioned(taskID int64, revision int64) bool {
	c.mu.Lock()
	defer c.mu.Unlock()
	if current, ok := c.versions[taskID]; ok && revision < current {
		return false
	}
	delete(c.m, taskID)
	c.versions[taskID] = revision
	c.tombstone[taskID] = true
	return true
}

func (c *Cache) Version(taskID int64) int64 {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.versions[taskID]
}

func (c *Cache) Get(taskID int64) (*Entry, bool) {
	c.mu.RLock()
	e, ok := c.m[taskID]
	c.mu.RUnlock()
	if !ok {
		return nil, false
	}
	if time.Now().After(e.ExpiresAt) {
		c.mu.Lock()
		if cur, ok2 := c.m[taskID]; ok2 && time.Now().After(cur.ExpiresAt) {
			delete(c.m, taskID)
		}
		c.mu.Unlock()
		return nil, false
	}
	return e, true
}

func (c *Cache) Touch(taskID int64) bool {
	c.mu.Lock()
	defer c.mu.Unlock()
	e, ok := c.m[taskID]
	if !ok {
		return false
	}
	if time.Now().After(e.ExpiresAt) {
		delete(c.m, taskID)
		return false
	}
	e.ExpiresAt = time.Now().Add(c.ttl)
	return true
}

func (c *Cache) RegionsForDevice(taskID int64, deviceID string) ([]config.Region, bool) {
	e, ok := c.Get(taskID)
	if !ok {
		return nil, false
	}
	return e.ByDevice[deviceID], true
}

func (c *Cache) Len() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return len(c.m)
}

// SweepExpired removes expired entries.
func (c *Cache) SweepExpired() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	n := 0
	now := time.Now()
	for id, e := range c.m {
		if now.After(e.ExpiresAt) {
			delete(c.m, id)
			n++
		}
	}
	return n
}
