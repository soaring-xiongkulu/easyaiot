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
	mu  sync.RWMutex
	ttl time.Duration
	m   map[int64]*Entry
}

func NewCache(ttl time.Duration) *Cache {
	return &Cache{ttl: ttl, m: make(map[int64]*Entry)}
}

func (c *Cache) Upsert(tpl config.TaskTemplate) time.Time {
	c.mu.Lock()
	defer c.mu.Unlock()
	exp := time.Now().Add(c.ttl)
	id := tpl.Task.ID
	c.m[id] = &Entry{
		Template:  tpl,
		ExpiresAt: exp,
		ByDevice:  config.RegionsByDevice(tpl.Regions),
	}
	return exp
}

func (c *Cache) Delete(taskID int64) {
	c.mu.Lock()
	defer c.mu.Unlock()
	delete(c.m, taskID)
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
