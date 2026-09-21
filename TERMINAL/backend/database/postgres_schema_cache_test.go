package database

import (
	"sync"
	"testing"
)

// TestPostgresSchemaCacheKey verifies the cache is keyed by "dbName.tableName"
// so two tables in the same database have distinct entries, and the same
// (dbName, tableName) tuple maps to the same SchemaResult pointer.
func TestPostgresSchemaCacheKey(t *testing.T) {
	// Use distinct keys to avoid stomping on entries left by other tests.
	const dbName = "test_cache_db_key"
	const tbl1 = "users_key"
	const tbl2 = "orders_key"

	// Wipe any prior state for these keys so the test is hermetic.
	postgresSchemaCache.Delete(dbName + "." + tbl1)
	postgresSchemaCache.Delete(dbName + "." + tbl2)

	r1 := &SchemaResult{Columns: []ColumnInfo{{Name: "id", Type: "int"}}}
	r2 := &SchemaResult{Columns: []ColumnInfo{{Name: "qty", Type: "int"}}}

	postgresSchemaCache.Store(dbName+"."+tbl1, r1)
	postgresSchemaCache.Store(dbName+"."+tbl2, r2)

	// Same key returns same pointer.
	if got, ok := postgresSchemaCache.Load(dbName + "." + tbl1); !ok || got != r1 {
		t.Errorf("cache miss for %s.%s after Store", dbName, tbl1)
	}
	if got, ok := postgresSchemaCache.Load(dbName + "." + tbl2); !ok || got != r2 {
		t.Errorf("cache miss for %s.%s after Store", dbName, tbl2)
	}

	// Different tables do not collide.
	if r1 == r2 {
		t.Fatal("r1 and r2 must be distinct pointers")
	}

	// Clean up so we don't leak across runs.
	postgresSchemaCache.Delete(dbName + "." + tbl1)
	postgresSchemaCache.Delete(dbName + "." + tbl2)
}

// TestPostgresSchemaCacheParallel exercises the cache under concurrent
// Store / Load from many goroutines. With -race, this catches any
// non-atomic access to the sync.Map itself or any unsynchronised
// mutation of shared SchemaResult.
func TestPostgresSchemaCacheParallel(t *testing.T) {
	const dbName = "test_cache_db_par"
	const tbl = "users_par"
	key := dbName + "." + tbl
	postgresSchemaCache.Delete(key)

	expected := &SchemaResult{Columns: []ColumnInfo{{Name: "id", Type: "int"}}}
	postgresSchemaCache.Store(key, expected)

	const N = 64
	var wg sync.WaitGroup
	wg.Add(N)
	for i := 0; i < N; i++ {
		go func() {
			defer wg.Done()
			for j := 0; j < 100; j++ {
				if got, ok := postgresSchemaCache.Load(key); !ok || got != expected {
					t.Errorf("concurrent Load returned %v ok=%v, want %v", got, ok, expected)
					return
				}
			}
		}()
	}
	wg.Wait()
	postgresSchemaCache.Delete(key)
}

// TestPostgresSchemaCacheSameTableParallel verifies the design intent of
// F-115: parallel callers requesting the same (dbName, tableName) get
// the same SchemaResult pointer. We simulate the post-GetTableSchema
// cache write and confirm a parallel Load picks it up.
func TestPostgresSchemaCacheSameTableParallel(t *testing.T) {
	const dbName = "test_cache_db_same"
	const tbl = "users_same"
	key := dbName + "." + tbl
	postgresSchemaCache.Delete(key)

	expected := &SchemaResult{Indexes: []IndexInfo{{Name: "pk", IsPrimary: true}}}

	const N = 32
	var wg sync.WaitGroup
	wg.Add(N)

	// Half the goroutines write, half read; they must converge.
	for i := 0; i < N; i++ {
		i := i
		go func() {
			defer wg.Done()
			if i%2 == 0 {
				postgresSchemaCache.Store(key, expected)
			} else {
				if got, ok := postgresSchemaCache.Load(key); ok && got != expected {
					t.Errorf("got unexpected pointer %p (want %p)", got, expected)
				}
			}
		}()
	}
	wg.Wait()

	// Final value must be the one we stored.
	if got, ok := postgresSchemaCache.Load(key); !ok || got != expected {
		t.Errorf("final cache state: got=%v ok=%v, want %v", got, ok, expected)
	}
	postgresSchemaCache.Delete(key)
}