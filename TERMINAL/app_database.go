package main

import (
	"fmt"
	"sort"

	"easyaiot/terminal/backend/database"
	"easyaiot/terminal/backend/log"
	"easyaiot/terminal/backend/session"
)
// ── Database methods ──

func (a *App) dbSession(sessionID string) (*session.DatabaseSession, error) {
	s, ok := a.sessionManager.Get(sessionID)
	if !ok {
		log.Writef("[dbSession] session not found: %s", sessionID)
		return nil, fmt.Errorf("session not found: %s", sessionID)
	}
	ds, ok := s.(*session.DatabaseSession)
	if !ok {
		log.Writef("[dbSession] session is not a database session: %s (type=%s)", sessionID, s.Type())
		return nil, fmt.Errorf("session is not a database session: %s", sessionID)
	}
	return ds, nil
}

func (a *App) dbProvider(sessionID string) (*session.DatabaseSession, database.Provider, error) {
	ds, err := a.dbSession(sessionID)
	if err != nil {
		return nil, nil, err
	}
	p, err := database.NewProvider(ds.DBType())
	if err != nil {
		return nil, nil, err
	}
	return ds, p, nil
}

func (a *App) GetDatabases(sessionID string) ([]string, error) {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return nil, err
	}
	dbs, err := p.GetDatabases(ds.DB())
	if err != nil {
		log.Writef("[GetDatabases] failed: %v", err)
	}
	return dbs, err
}

func (a *App) GetTables(sessionID string, dbName string) ([]database.TableInfo, error) {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return nil, err
	}
	tables, err := p.GetTables(ds.DB(), dbName)
	if err != nil {
		log.Writef("[GetTables] failed: %v", err)
		return nil, err
	}
	sort.Slice(tables, func(i, j int) bool {
		return tables[i].Name < tables[j].Name
	})
	return tables, nil
}

func (a *App) GetTableSchema(sessionID string, dbName string, tableName string) (*database.SchemaResult, error) {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return nil, err
	}
	return p.GetTableSchema(ds.DB(), dbName, tableName)
}

func (a *App) CreateDatabase(sessionID string, dbName string) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.CreateDatabase(ds.DB(), dbName)
}

func (a *App) DropDatabase(sessionID string, dbName string) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.DropDatabase(ds.DB(), dbName)
}

func (a *App) CreateTable(sessionID string, dbName string, tableName string) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.CreateTable(ds.DB(), dbName, tableName)
}

func (a *App) DropTable(sessionID string, dbName string, tableName string) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.DropTable(ds.DB(), dbName, tableName)
}

func (a *App) DropView(sessionID string, dbName string, viewName string) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.DropView(ds.DB(), dbName, viewName)
}

func (a *App) TruncateTable(sessionID string, dbName string, tableName string) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.TruncateTable(ds.DB(), dbName, tableName)
}

func (a *App) ExecuteQuery(sessionID string, dbName string, sql string) (*database.QueryResult, error) {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return nil, err
	}
	return database.ExecuteQuery(p, ds.DB(), dbName, sql)
}

func (a *App) ExecuteStatement(sessionID string, dbName string, sql string) (*database.ExecResult, error) {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return nil, err
	}
	return database.ExecuteStatement(p, ds.DB(), dbName, sql)
}

func (a *App) DBDefaultTableQuery(sessionID string, dbName string, tableName string, limit int, offset int) (string, error) {
	_, p, err := a.dbProvider(sessionID)
	if err != nil {
		return "", err
	}
	if limit <= 0 {
		limit = 100
	}
	if offset < 0 {
		offset = 0
	}
	return p.DefaultTableQuery(dbName, tableName, limit, offset), nil
}

func (a *App) DBPagedTableQuery(sessionID string, dbName string, tableName string, limit int, offset int) (string, error) {
	_, p, err := a.dbProvider(sessionID)
	if err != nil {
		return "", err
	}
	return p.PagedTableQuery(dbName, tableName, limit, offset), nil
}

func (a *App) ExecuteSQLScript(sessionID string, dbName string, script string) (*database.ScriptResult, error) {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return nil, err
	}
	return database.ExecuteScript(p, ds.DB(), dbName, script)
}

func (a *App) DumpTable(sessionID string, dbName string, tableName string, withStructure bool, withData bool) (string, error) {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return "", err
	}
	return p.DumpTable(ds.DB(), dbName, tableName, database.DumpOptions{Structure: withStructure, Data: withData})
}

func (a *App) CopyTable(sessionID string, dbName string, tableName string, newTableName string) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.CopyTable(ds.DB(), dbName, tableName, newTableName)
}

func (a *App) DBInsertRow(sessionID string, dbName string, tableName string, values map[string]any) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.InsertRow(ds.DB(), dbName, tableName, values)
}

func (a *App) DBUpdateRow(sessionID string, dbName string, tableName string, set map[string]any, where map[string]any) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.UpdateRow(ds.DB(), dbName, tableName, set, where)
}

func (a *App) DBDeleteRow(sessionID string, dbName string, tableName string, where map[string]any) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.DeleteRow(ds.DB(), dbName, tableName, where)
}

func (a *App) AddColumn(sessionID string, dbName string, tableName string, col database.ColumnDef) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.AddColumn(ds.DB(), dbName, tableName, col)
}

func (a *App) ModifyColumn(sessionID string, dbName string, tableName string, col database.ColumnDef) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.ModifyColumn(ds.DB(), dbName, tableName, col)
}

func (a *App) DropColumn(sessionID string, dbName string, tableName string, colName string) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.DropColumn(ds.DB(), dbName, tableName, colName)
}

func (a *App) AddIndex(sessionID string, dbName string, tableName string, idx database.IndexDef) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.AddIndex(ds.DB(), dbName, tableName, idx)
}

func (a *App) DropIndexOp(sessionID string, dbName string, tableName string, idxName string, isPrimary bool, autoIncCols []string) error {
	ds, p, err := a.dbProvider(sessionID)
	if err != nil {
		return err
	}
	return p.DropIndex(ds.DB(), dbName, tableName, idxName, isPrimary, autoIncCols)
}

func (a *App) GetDBCapabilities(sessionID string) (database.DBCapabilities, error) {
	_, p, err := a.dbProvider(sessionID)
	if err != nil {
		return nil, err
	}
	return database.MergeCapabilities(p.GetCapabilities()), nil
}

// ── Redis methods ──

func (a *App) redisSession(sessionID string) (*session.RedisSession, error) {
	s, ok := a.sessionManager.Get(sessionID)
	if !ok {
		return nil, fmt.Errorf("session not found: %s", sessionID)
	}
	rs, ok := s.(*session.RedisSession)
	if !ok {
		return nil, fmt.Errorf("session is not a redis session: %s (type=%s)", sessionID, s.Type())
	}
	return rs, nil
}

func (a *App) RedisPing(sessionID string) error {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return err
	}
	return rs.Ping()
}

func (a *App) RedisSwitchDB(sessionID string, idx int) error {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return err
	}
	return rs.SwitchDB(idx)
}

func (a *App) RedisScanKeys(sessionID string, pattern string, cursor uint64, count int64) (*session.ScanResult, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return nil, err
	}
	return rs.ScanKeys(pattern, cursor, count)
}

func (a *App) RedisGetKeyInfo(sessionID string, key string) (*session.RedisKeyInfo, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return nil, err
	}
	return rs.GetKeyInfo(key)
}

func (a *App) RedisDBSize(sessionID string) (int64, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return 0, err
	}
	return rs.DBSize()
}

func (a *App) RedisKeyspaceInfo(sessionID string) (map[int]int64, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return nil, err
	}
	return rs.KeyspaceInfo()
}

func (a *App) RedisDeleteKey(sessionID string, key string) error {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return err
	}
	return rs.DeleteKey(key)
}

func (a *App) RedisKeyExists(sessionID string, key string) (bool, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return false, err
	}
	return rs.KeyExists(key)
}

func (a *App) RedisGetKeyTTL(sessionID string, key string) (int64, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return -2, err
	}
	return rs.GetKeyTTL(key)
}

func (a *App) RedisSetKeyTTL(sessionID string, key string, seconds int64) error {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return err
	}
	return rs.SetKeyTTL(key, seconds)
}

func (a *App) RedisGetString(sessionID string, key string) (string, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return "", err
	}
	return rs.GetString(key)
}

func (a *App) RedisSetString(sessionID string, key string, value string) error {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return err
	}
	return rs.SetString(key, value)
}

func (a *App) RedisGetHashAll(sessionID string, key string) ([]session.FieldEntry, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return nil, err
	}
	return rs.GetHashAll(key)
}

func (a *App) RedisHashSet(sessionID string, key string, field string, value string) error {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return err
	}
	return rs.HashSet(key, field, value)
}

func (a *App) RedisHashDel(sessionID string, key string, fields []string) (int64, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return 0, err
	}
	return rs.HashDel(key, fields)
}

func (a *App) RedisGetListRange(sessionID string, key string, start int64, stop int64) ([]string, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return nil, err
	}
	return rs.GetListRange(key, start, stop)
}

func (a *App) RedisListPush(sessionID string, key string, direction string, values []string) (int64, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return 0, err
	}
	return rs.ListPush(key, direction, values)
}

func (a *App) RedisListPop(sessionID string, key string, direction string) (string, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return "", err
	}
	return rs.ListPop(key, direction)
}

func (a *App) RedisListSet(sessionID string, key string, index int64, value string) error {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return err
	}
	return rs.ListSet(key, index, value)
}

func (a *App) RedisListRemove(sessionID string, key string, value string, count int64) (int64, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return 0, err
	}
	return rs.ListRemove(key, value, count)
}

func (a *App) RedisGetSetAll(sessionID string, key string) ([]string, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return nil, err
	}
	return rs.GetSetAll(key)
}

func (a *App) RedisSetAdd(sessionID string, key string, members []string) (int64, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return 0, err
	}
	return rs.SetAdd(key, members)
}

func (a *App) RedisSetRemove(sessionID string, key string, members []string) (int64, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return 0, err
	}
	return rs.SetRemove(key, members)
}

func (a *App) RedisGetSortedSetRange(sessionID string, key string, min string, max string) ([]session.ScoredMember, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return nil, err
	}
	return rs.GetSortedSetRange(key, min, max)
}

func (a *App) RedisZSetAdd(sessionID string, key string, members []session.ScoredMember) (int64, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return 0, err
	}
	return rs.ZSetAdd(key, members)
}

func (a *App) RedisZSetRemove(sessionID string, key string, members []string) (int64, error) {
	rs, err := a.redisSession(sessionID)
	if err != nil {
		return 0, err
	}
	return rs.ZSetRemove(key, members)
}

// ── MongoDB methods ──

func (a *App) mongoSession(sessionID string) (*session.MongoSession, error) {
	s, ok := a.sessionManager.Get(sessionID)
	if !ok {
		return nil, fmt.Errorf("session not found: %s", sessionID)
	}
	ms, ok := s.(*session.MongoSession)
	if !ok {
		return nil, fmt.Errorf("session is not a mongodb session: %s (type=%s)", sessionID, s.Type())
	}
	return ms, nil
}

func (a *App) MongoPing(sessionID string) error {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return err
	}
	return ms.Ping()
}

func (a *App) MongoListDatabases(sessionID string) ([]string, error) {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return nil, err
	}
	return ms.ListDatabases()
}

func (a *App) MongoListCollections(sessionID string, dbName string) ([]string, error) {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return nil, err
	}
	return ms.ListCollections(dbName)
}

func (a *App) MongoFind(sessionID string, dbName string, collection string, filterJSON string, skip int64, limit int64) (*session.MongoQueryResult, error) {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return nil, err
	}
	return ms.Find(dbName, collection, filterJSON, skip, limit)
}

func (a *App) MongoGetDocument(sessionID string, dbName string, collection string, docID string) (string, error) {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return "", err
	}
	return ms.GetDocument(dbName, collection, docID)
}

func (a *App) MongoInsertOne(sessionID string, dbName string, collection string, docJSON string) (string, error) {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return "", err
	}
	return ms.InsertOne(dbName, collection, docJSON)
}

func (a *App) MongoUpdateOne(sessionID string, dbName string, collection string, filterJSON string, updateJSON string) error {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return err
	}
	return ms.UpdateOne(dbName, collection, filterJSON, updateJSON)
}

func (a *App) MongoDeleteOne(sessionID string, dbName string, collection string, filterJSON string) error {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return err
	}
	return ms.DeleteOne(dbName, collection, filterJSON)
}

func (a *App) MongoListIndexes(sessionID string, dbName string, collection string) ([]session.MongoIndexInfo, error) {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return nil, err
	}
	return ms.ListIndexes(dbName, collection)
}

func (a *App) MongoCreateCollection(sessionID string, dbName string, collection string) error {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return err
	}
	return ms.CreateCollection(dbName, collection)
}

func (a *App) MongoDropCollection(sessionID string, dbName string, collection string) error {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return err
	}
	return ms.DropCollection(dbName, collection)
}

func (a *App) MongoDropDatabase(sessionID string, dbName string) error {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return err
	}
	return ms.DropDatabase(dbName)
}

func (a *App) MongoCreateIndex(sessionID string, dbName string, collection string, name string, keys []string, unique bool) error {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return err
	}
	return ms.CreateIndex(dbName, collection, name, keys, unique)
}

func (a *App) MongoDropIndex(sessionID string, dbName string, collection string, name string) error {
	ms, err := a.mongoSession(sessionID)
	if err != nil {
		return err
	}
	return ms.DropIndex(dbName, collection, name)
}

// ── Elasticsearch methods ──

func (a *App) esSession(sessionID string) (*session.ElasticsearchSession, error) {
	s, ok := a.sessionManager.Get(sessionID)
	if !ok {
		return nil, fmt.Errorf("session not found: %s", sessionID)
	}
	es, ok := s.(*session.ElasticsearchSession)
	if !ok {
		return nil, fmt.Errorf("session is not an elasticsearch session: %s (type=%s)", sessionID, s.Type())
	}
	return es, nil
}

func (a *App) EsPing(sessionID string) error {
	es, err := a.esSession(sessionID)
	if err != nil {
		return err
	}
	return es.Ping()
}

func (a *App) EsClusterInfo(sessionID string) (*session.EsClusterInfo, error) {
	es, err := a.esSession(sessionID)
	if err != nil {
		return nil, err
	}
	return es.ClusterInfo()
}

func (a *App) EsClusterHealth(sessionID string) (*session.EsClusterHealth, error) {
	es, err := a.esSession(sessionID)
	if err != nil {
		return nil, err
	}
	return es.ClusterHealth()
}

func (a *App) EsNodesStats(sessionID string) ([]session.EsNodeSummary, error) {
	es, err := a.esSession(sessionID)
	if err != nil {
		return nil, err
	}
	return es.NodesStats()
}

func (a *App) EsListIndices(sessionID string) ([]session.EsIndexInfo, error) {
	es, err := a.esSession(sessionID)
	if err != nil {
		return nil, err
	}
	return es.ListIndices()
}

func (a *App) EsGetMapping(sessionID string, index string) (string, error) {
	es, err := a.esSession(sessionID)
	if err != nil {
		return "", err
	}
	return es.GetMapping(index)
}

func (a *App) EsGetSettings(sessionID string, index string) (string, error) {
	es, err := a.esSession(sessionID)
	if err != nil {
		return "", err
	}
	return es.GetSettings(index)
}

func (a *App) EsSearch(sessionID string, index string, bodyJSON string, from int, size int) (*session.EsSearchResult, error) {
	es, err := a.esSession(sessionID)
	if err != nil {
		return nil, err
	}
	return es.Search(index, bodyJSON, from, size)
}

func (a *App) EsGetDoc(sessionID string, index string, id string) (string, error) {
	es, err := a.esSession(sessionID)
	if err != nil {
		return "", err
	}
	return es.GetDoc(index, id)
}

func (a *App) EsIndexDoc(sessionID string, index string, id string, docJSON string) (string, error) {
	es, err := a.esSession(sessionID)
	if err != nil {
		return "", err
	}
	return es.IndexDoc(index, id, docJSON)
}

func (a *App) EsUpdateDoc(sessionID string, index string, id string, docJSON string) error {
	es, err := a.esSession(sessionID)
	if err != nil {
		return err
	}
	return es.UpdateDoc(index, id, docJSON)
}

func (a *App) EsDeleteDoc(sessionID string, index string, id string) error {
	es, err := a.esSession(sessionID)
	if err != nil {
		return err
	}
	return es.DeleteDoc(index, id)
}

func (a *App) EsCreateIndex(sessionID string, index string, bodyJSON string) error {
	es, err := a.esSession(sessionID)
	if err != nil {
		return err
	}
	return es.CreateIndex(index, bodyJSON)
}

func (a *App) EsDeleteIndex(sessionID string, index string) error {
	es, err := a.esSession(sessionID)
	if err != nil {
		return err
	}
	return es.DeleteIndex(index)
}

func (a *App) EsOpenIndex(sessionID string, index string) error {
	es, err := a.esSession(sessionID)
	if err != nil {
		return err
	}
	return es.OpenIndex(index)
}

func (a *App) EsCloseIndex(sessionID string, index string) error {
	es, err := a.esSession(sessionID)
	if err != nil {
		return err
	}
	return es.CloseIndex(index)
}

func (a *App) EsRest(sessionID string, method string, path string, bodyJSON string) (*session.EsRestResult, error) {
	es, err := a.esSession(sessionID)
	if err != nil {
		return nil, err
	}
	return es.Rest(method, path, bodyJSON)
}
