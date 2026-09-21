package session

import (
	"context"
	"fmt"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/redis/go-redis/v9"
	"easyaiot/terminal/backend/log"
)

// ScanResult holds a page of SCAN results with cursor for pagination.
type ScanResult struct {
	Keys      []RedisKeyInfo `json:"keys"`
	Cursor    uint64         `json:"cursor"`
	ScanCount int            `json:"scanCount"`
}

// RedisKeyInfo holds metadata for a single Redis key.
type RedisKeyInfo struct {
	Name string `json:"name"`
	Type string `json:"type"`
	TTL  int64  `json:"ttl"`
}

// FieldEntry represents a hash field-value pair.
type FieldEntry struct {
	Field string `json:"field"`
	Value string `json:"value"`
}

// ScoredMember represents a sorted-set member with its score.
type ScoredMember struct {
	Score  float64 `json:"score"`
	Member  string  `json:"member"`
}

// RedisSession implements the Session interface for Redis connections using go-redis.
type RedisSession struct {
	baseSession
	client *redis.Client
	dbIdx  int
	closed bool
}

// NewRedisSession creates a new RedisSession with the given ID.
func NewRedisSession(id string) *RedisSession {
	return &RedisSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "redis",
			status:      StatusDisconnected,
		},
		dbIdx: 0,
	}
}

// Connect establishes a connection to the Redis server.
func (s *RedisSession) Connect(config ConnectionConfig) error {
	log.Writef("[RedisSession.Connect] id=%s, host=%s, port=%d", s.id, config.Host, config.Port)
	s.setStatus(StatusConnecting)

	if config.Name != "" {
		s.title = config.Name
	} else if config.RedisMode == "sentinel" {
		s.title = fmt.Sprintf("redis:%s", config.RedisMasterName)
	} else {
		s.title = fmt.Sprintf("redis:%s:%d", config.Host, config.Port)
	}

	var client *redis.Client
	if config.RedisMode == "sentinel" {
		addrs := make([]string, 0)
		for _, a := range strings.Split(config.RedisSentinels, ",") {
			if a = strings.TrimSpace(a); a != "" {
				addrs = append(addrs, a)
			}
		}
		if len(addrs) == 0 {
			s.setStatus(StatusError)
			return fmt.Errorf("redis sentinel: no sentinel addresses")
		}
		if config.RedisMasterName == "" {
			s.setStatus(StatusError)
			return fmt.Errorf("redis sentinel: master name required")
		}
		client = redis.NewFailoverClient(&redis.FailoverOptions{
			MasterName:       config.RedisMasterName,
			SentinelAddrs:    addrs,
			SentinelUsername: config.SentinelUser,
			SentinelPassword: config.SentinelPassword,
			Username:         config.User,
			Password:         config.Password,
			DB:               0,
		})
	} else {
		addr := fmt.Sprintf("%s:%d", config.Host, config.Port)
		client = redis.NewClient(&redis.Options{
			Addr:     addr,
			Username: config.User,
			Password: config.Password,
			DB:       0,
		})
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if _, err := client.Ping(ctx).Result(); err != nil {
		log.Writef("[RedisSession.Connect] PING failed: %v", err)
		client.Close()
		s.setStatus(StatusError)
		return fmt.Errorf("redis ping: %w", err)
	}

	s.mu.Lock()
	s.client = client
	s.mu.Unlock()

	log.Writef("[RedisSession.Connect] connected successfully")
	s.setStatus(StatusConnected)
	return nil
}

// Disconnect closes the Redis connection.
func (s *RedisSession) Disconnect() error {
	s.mu.Lock()
	if s.closed {
		s.mu.Unlock()
		return nil
	}
	s.closed = true
	s.mu.Unlock()

	if s.client != nil {
		s.client.Close()
	}
	s.setStatus(StatusDisconnected)
	return nil
}

// IsConnected returns true if the session is connected and the client is valid.
func (s *RedisSession) IsConnected() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.status == StatusConnected && s.client != nil
}

// Write is a no-op for Redis sessions (no interactive terminal I/O).
func (s *RedisSession) Write(data []byte) error { return nil }

// Resize is a no-op for Redis sessions (no terminal dimensions).
func (s *RedisSession) Resize(cols, rows int) error { return nil }

// Client returns the underlying go-redis client.
func (s *RedisSession) Client() *redis.Client {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.client
}

// DBIndex returns the current database index (0-15).
func (s *RedisSession) DBIndex() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.dbIdx
}

// Ping checks connectivity to the Redis server.
func (s *RedisSession) Ping() error {
	client := s.Client()
	if client == nil {
		return fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.Ping(ctx).Err()
}

// SwitchDB switches to the specified Redis database index (0-15).
func (s *RedisSession) SwitchDB(idx int) error {
	if idx < 0 || idx > 15 {
		return fmt.Errorf("invalid db index: %d (must be 0-15)", idx)
	}
	client := s.Client()
	if client == nil {
		return fmt.Errorf("not connected")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	pipe := client.Pipeline()
	pipe.Do(ctx, "SELECT", idx)
	pipe.Ping(ctx)
	if _, err := pipe.Exec(ctx); err != nil {
		log.Writef("[RedisSession.SwitchDB] failed to switch to db %d: %v", idx, err)
		return fmt.Errorf("switch db %d: %w", idx, err)
	}

	s.mu.Lock()
	s.dbIdx = idx
	s.mu.Unlock()
	return nil
}

// ScanKeys scans keys matching pattern with cursor-based pagination.
// Returns key metadata (name, type, TTL) via pipeline batching.
func (s *RedisSession) ScanKeys(pattern string, cursor uint64, count int64) (*ScanResult, error) {
	if count <= 0 {
		count = 100
	}
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	keys, nextCursor, err := client.Scan(ctx, cursor, pattern, count).Result()
	if err != nil {
		return nil, fmt.Errorf("scan: %w", err)
	}

	result := &ScanResult{
		Keys:      make([]RedisKeyInfo, 0, len(keys)),
		Cursor:    nextCursor,
		ScanCount: len(keys),
	}

	if len(keys) == 0 {
		return result, nil
	}

	// Batch TYPE + TTL via pipeline
	pipe := client.Pipeline()
	typeCmds := make([]*redis.StatusCmd, len(keys))
	ttlCmds := make([]*redis.DurationCmd, len(keys))
	for i, key := range keys {
		typeCmds[i] = pipe.Type(ctx, key)
		ttlCmds[i] = pipe.TTL(ctx, key)
	}
	_, err = pipe.Exec(ctx)
	if err != nil && err != redis.Nil {
		return nil, fmt.Errorf("scan pipeline: %w", err)
	}

	for i, key := range keys {
		t := typeCmds[i].Val()
		if t == "none" {
			continue
		}
		ttlVal := ttlCmds[i].Val()
		ttl := int64(-1)
		if ttlVal > 0 {
			ttl = int64(ttlVal.Seconds())
		} else if ttlVal == -2 {
			ttl = -2
		}
		result.Keys = append(result.Keys, RedisKeyInfo{
			Name: key,
			Type: t,
			TTL:  ttl,
		})
	}
	return result, nil
}

// GetKeyInfo returns metadata (type, TTL) for a single key.
func (s *RedisSession) GetKeyInfo(key string) (*RedisKeyInfo, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	pipe := client.Pipeline()
	typeCmd := pipe.Type(ctx, key)
	ttlCmd := pipe.TTL(ctx, key)
	_, err := pipe.Exec(ctx)
	if err != nil {
		return nil, fmt.Errorf("get key info: %w", err)
	}

	t := typeCmd.Val()
	if t == "none" {
		return nil, fmt.Errorf("key not found: %s", key)
	}
	ttlVal := ttlCmd.Val()
	ttl := int64(-1)
	if ttlVal > 0 {
		ttl = int64(ttlVal.Seconds())
	} else if ttlVal == -2 {
		ttl = -2
	}
	return &RedisKeyInfo{Name: key, Type: t, TTL: ttl}, nil
}

// DBSize returns the number of keys in the current database.
func (s *RedisSession) DBSize() (int64, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.DBSize(ctx).Result()
}

// KeyspaceInfo returns key counts for all databases via INFO keyspace.
// Returns a map of db index -> key count. Empty dbs are omitted by Redis.
func (s *RedisSession) KeyspaceInfo() (map[int]int64, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	info, err := client.Info(ctx, "keyspace").Result()
	if err != nil {
		return nil, err
	}

	result := make(map[int]int64)
	for _, line := range strings.Split(info, "\r\n") {
		if strings.HasPrefix(line, "db") {
			parts := strings.SplitN(line, ":", 2)
			if len(parts) != 2 {
				continue
			}
			var dbIdx int
			if _, scanErr := fmt.Sscanf(parts[0], "db%d", &dbIdx); scanErr != nil {
				continue
			}
			for _, pair := range strings.Split(parts[1], ",") {
				if kv := strings.SplitN(pair, "=", 2); len(kv) == 2 && kv[0] == "keys" {
					if n, parseErr := strconv.ParseInt(kv[1], 10, 64); parseErr == nil {
						result[dbIdx] = n
					}
				}
			}
		}
	}
	return result, nil
}

// DeleteKey deletes a key from Redis.
func (s *RedisSession) DeleteKey(key string) error {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.Del(ctx, key).Err()
}

// KeyExists returns true if the key exists in Redis.
func (s *RedisSession) KeyExists(key string) (bool, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	n, err := client.Exists(ctx, key).Result()
	return n > 0, err
}

// GetKeyTTL returns the TTL for a key in seconds.
func (s *RedisSession) GetKeyTTL(key string) (int64, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	d, err := client.TTL(ctx, key).Result()
	if err != nil {
		return -2, err
	}
	return int64(d.Seconds()), nil
}

// SetKeyTTL sets the TTL for a key in seconds.
func (s *RedisSession) SetKeyTTL(key string, seconds int64) error {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if seconds < 0 {
		return client.Persist(ctx, key).Err()
	}
	return client.Expire(ctx, key, time.Duration(seconds)*time.Second).Err()
}

// --- String operations ---

// GetString returns the string value of a key.
func (s *RedisSession) GetString(key string) (string, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.Get(ctx, key).Result()
}

// SetString sets a string value for a key.
func (s *RedisSession) SetString(key string, value string) error {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.Set(ctx, key, value, 0).Err()
}

// --- Hash operations ---

// GetHashAll returns all field-value pairs of a hash.
func (s *RedisSession) GetHashAll(key string) ([]FieldEntry, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	m, err := client.HGetAll(ctx, key).Result()
	if err != nil {
		return nil, err
	}
	entries := make([]FieldEntry, 0, len(m))
	for field, value := range m {
		entries = append(entries, FieldEntry{Field: field, Value: value})
	}
	sort.Slice(entries, func(i, j int) bool { return entries[i].Field < entries[j].Field })
	return entries, nil
}

// HashSet sets a field in a hash.
func (s *RedisSession) HashSet(key string, field string, value string) error {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.HSet(ctx, key, field, value).Err()
}

// HashDel deletes one or more fields from a hash.
func (s *RedisSession) HashDel(key string, fields []string) (int64, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.HDel(ctx, key, fields...).Result()
}

// --- List operations ---

// GetListRange returns elements from a list within the specified range.
func (s *RedisSession) GetListRange(key string, start int64, stop int64) ([]string, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.LRange(ctx, key, start, stop).Result()
}

// ListPush pushes values onto a list from the specified direction ("left" or "right").
func (s *RedisSession) ListPush(key string, direction string, values []string) (int64, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if direction == "left" {
		return client.LPush(ctx, key, values).Result()
	}
	return client.RPush(ctx, key, values).Result()
}

// ListPop pops a value from a list from the specified direction ("left" or "right").
func (s *RedisSession) ListPop(key string, direction string) (string, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if direction == "left" {
		return client.LPop(ctx, key).Result()
	}
	return client.RPop(ctx, key).Result()
}

// ListSet sets the value at an index in a list.
func (s *RedisSession) ListSet(key string, index int64, value string) error {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.LSet(ctx, key, index, value).Err()
}

// ListRemove removes elements from a list matching the value.
func (s *RedisSession) ListRemove(key string, value string, count int64) (int64, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.LRem(ctx, key, count, value).Result()
}

// --- Set operations ---

// GetSetAll returns all members of a set.
func (s *RedisSession) GetSetAll(key string) ([]string, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.SMembers(ctx, key).Result()
}

// SetAdd adds members to a set.
func (s *RedisSession) SetAdd(key string, members []string) (int64, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.SAdd(ctx, key, members).Result()
}

// SetRemove removes members from a set.
func (s *RedisSession) SetRemove(key string, members []string) (int64, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.SRem(ctx, key, members).Result()
}

// --- Sorted Set operations ---

// GetSortedSetRange returns members within a score range, with scores.
func (s *RedisSession) GetSortedSetRange(key string, min string, max string) ([]ScoredMember, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	opt := &redis.ZRangeBy{Min: min, Max: max}
	vals, err := client.ZRangeByScoreWithScores(ctx, key, opt).Result()
	if err != nil {
		return nil, err
	}

	members := make([]ScoredMember, len(vals))
	for i, v := range vals {
		members[i] = ScoredMember{Member: v.Member.(string), Score: v.Score}
	}
	return members, nil
}

// ZSetAdd adds members with scores to a sorted set.
func (s *RedisSession) ZSetAdd(key string, members []ScoredMember) (int64, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	zs := make([]redis.Z, len(members))
	for i, m := range members {
		zs[i] = redis.Z{Score: m.Score, Member: m.Member}
	}
	return client.ZAdd(ctx, key, zs...).Result()
}

// ZSetRemove removes members from a sorted set.
func (s *RedisSession) ZSetRemove(key string, members []string) (int64, error) {
	client := s.Client()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.ZRem(ctx, key, members).Result()
}
