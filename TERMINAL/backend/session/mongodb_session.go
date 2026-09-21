package session

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"easyaiot/terminal/backend/log"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// MongoIndexInfo holds metadata for a MongoDB index.
type MongoIndexInfo struct {
	Name   string   `json:"name"`
	Keys   []string `json:"keys"`
	Type   string   `json:"type"`
	Unique bool     `json:"unique"`
}

// MongoQueryResult holds paginated find results as raw JSON documents.
type MongoQueryResult struct {
	Documents []string `json:"documents"`
	Total     int64    `json:"total"`
	Skip      int64    `json:"skip"`
	Limit     int64    `json:"limit"`
}

// MongoSession implements the Session interface for MongoDB connections.
type MongoSession struct {
	baseSession
	client *mongo.Client
	closed bool
}

// NewMongoSession creates a new MongoSession with the given ID.
func NewMongoSession(id string) *MongoSession {
	return &MongoSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "mongodb",
			status:      StatusDisconnected,
		},
	}
}

// Connect establishes a connection to the MongoDB server.
func (s *MongoSession) Connect(config ConnectionConfig) error {
	log.Writef("[MongoSession.Connect] id=%s, host=%s, port=%d", s.id, config.Host, config.Port)
	s.setStatus(StatusConnecting)

	if config.Name != "" {
		s.title = config.Name
	} else {
		s.title = fmt.Sprintf("mongodb:%s:%d", config.Host, config.Port)
	}

	uri := buildMongoURI(config)
	log.Writef("[MongoSession.Connect] connecting to %s:%d", config.Host, config.Port)

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(uri))
	if err != nil {
		log.Writef("[MongoSession.Connect] connect failed: %v", err)
		s.setStatus(StatusError)
		return fmt.Errorf("mongodb connect %s:%d: %w", config.Host, config.Port, err)
	}

	// Ping to verify connectivity
	if err := client.Ping(ctx, nil); err != nil {
		log.Writef("[MongoSession.Connect] PING failed: %v", err)
		client.Disconnect(context.Background())
		s.setStatus(StatusError)
		return fmt.Errorf("mongodb ping %s:%d: %w", config.Host, config.Port, err)
	}

	s.mu.Lock()
	s.client = client
	s.mu.Unlock()

	log.Writef("[MongoSession.Connect] connected successfully")
	s.setStatus(StatusConnected)
	return nil
}

// buildMongoURI constructs a MongoDB connection URI from config fields.
func buildMongoURI(config ConnectionConfig) string {
	host := config.Host
	if host == "" {
		host = "127.0.0.1"
	}
	port := config.Port
	if port == 0 {
		port = 27017
	}

	uri := "mongodb://"
	if config.User != "" && config.Password != "" {
		uri += fmt.Sprintf("%s:%s@", config.User, config.Password)
	}
	uri += fmt.Sprintf("%s:%d", host, port)

	// Default database
	if config.DBName != "" {
		uri += "/" + config.DBName
	}
	uri += "?authSource=admin"

	// Append extra params
	if config.DBParams != "" {
		uri += "&" + config.DBParams
	}

	return uri
}

// Disconnect closes the MongoDB connection.
func (s *MongoSession) Disconnect() error {
	s.mu.Lock()
	if s.closed {
		s.mu.Unlock()
		return nil
	}
	s.closed = true
	s.mu.Unlock()

	if s.client != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		s.client.Disconnect(ctx)
	}
	s.setStatus(StatusDisconnected)
	return nil
}

// IsConnected returns true if the session is connected and the client is valid.
func (s *MongoSession) IsConnected() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.status == StatusConnected && s.client != nil
}

// Write is a no-op for MongoDB sessions (no interactive terminal I/O).
func (s *MongoSession) Write(data []byte) error { return nil }

// Resize is a no-op for MongoDB sessions (no terminal dimensions).
func (s *MongoSession) Resize(cols, rows int) error { return nil }

// Client returns the underlying mongo-go-driver client.
func (s *MongoSession) Client() *mongo.Client {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.client
}

// Ping checks connectivity to the MongoDB server.
func (s *MongoSession) Ping() error {
	client := s.Client()
	if client == nil {
		return fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return client.Ping(ctx, nil)
}

// ── Browsing ──

// ListDatabases returns the names of all non-system databases.
func (s *MongoSession) ListDatabases() ([]string, error) {
	client := s.Client()
	if client == nil {
		return nil, fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	dbs, err := client.ListDatabaseNames(ctx, bson.D{})
	if err != nil {
		return nil, fmt.Errorf("list databases: %w", err)
	}
	return dbs, nil
}

// ListCollections returns the names of all collections in a database.
func (s *MongoSession) ListCollections(dbName string) ([]string, error) {
	client := s.Client()
	if client == nil {
		return nil, fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	db := client.Database(dbName)
	cols, err := db.ListCollectionNames(ctx, bson.D{})
	if err != nil {
		return nil, fmt.Errorf("list collections for %s: %w", dbName, err)
	}
	return cols, nil
}

// ── Querying ──

// Find executes a find query with filter, projection, skip, and limit.
// Returns documents as JSON strings.
func (s *MongoSession) Find(dbName, collection, filterJSON string, skip, limit int64) (*MongoQueryResult, error) {
	client := s.Client()
	if client == nil {
		return nil, fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if limit <= 0 {
		limit = 100
	}

	var filter bson.M
	if filterJSON != "" && filterJSON != "{}" {
		if err := bson.UnmarshalExtJSON([]byte(filterJSON), true, &filter); err != nil {
			return nil, fmt.Errorf("invalid filter JSON: %w", err)
		}
	}

	coll := client.Database(dbName).Collection(collection)

	opts := options.Find().SetSkip(skip).SetLimit(limit)
	cursor, err := coll.Find(ctx, fixObjectIDFilter(filter), opts)
	if err != nil {
		return nil, fmt.Errorf("find: %w", err)
	}
	defer cursor.Close(ctx)

	var docs []bson.M
	if err := cursor.All(ctx, &docs); err != nil {
		return nil, fmt.Errorf("cursor read: %w", err)
	}

	// Count total matching documents
	total, err := coll.CountDocuments(ctx, filter)
	if err != nil {
		total = int64(len(docs))
	}

	// Marshal each document to JSON string
	result := &MongoQueryResult{
		Documents: make([]string, 0, len(docs)),
		Total:     total,
		Skip:      skip,
		Limit:     limit,
	}
	for _, doc := range docs {
		// Convert _id to string representation
		if id, ok := doc["_id"]; ok {
			if oid, ok2 := id.(primitive.ObjectID); ok2 {
				doc["_id"] = oid.Hex()
			} else {
				doc["_id"] = fmt.Sprintf("%v", id)
			}
		}
		jsonBytes, err := json.Marshal(doc)
		if err != nil {
			continue
		}
		result.Documents = append(result.Documents, string(jsonBytes))
	}

	return result, nil
}

// GetDocument retrieves a single document by its _id.
func (s *MongoSession) GetDocument(dbName, collection, docID string) (string, error) {
	client := s.Client()
	if client == nil {
		return "", fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	coll := client.Database(dbName).Collection(collection)

	oid, err := primitive.ObjectIDFromHex(docID)
	if err != nil {
		return "", fmt.Errorf("invalid document ID: %w", err)
	}

	var doc bson.M
	if err := coll.FindOne(ctx, bson.D{{Key: "_id", Value: oid}}).Decode(&doc); err != nil {
		return "", fmt.Errorf("find document: %w", err)
	}

	if id, ok := doc["_id"]; ok {
		if oid, ok2 := id.(primitive.ObjectID); ok2 {
			doc["_id"] = oid.Hex()
		} else {
			doc["_id"] = fmt.Sprintf("%v", id)
		}
	}
	jsonBytes, err := json.Marshal(doc)
	if err != nil {
		return "", fmt.Errorf("marshal document: %w", err)
	}
	return string(jsonBytes), nil
}

// fixObjectIDFilter converts string _id values in a filter to ObjectID.
func fixObjectIDFilter(filter bson.M) bson.M {
	if idVal, ok := filter["_id"]; ok {
		if idStr, ok := idVal.(string); ok {
			if oid, err := primitive.ObjectIDFromHex(idStr); err == nil {
				filter["_id"] = oid
			}
		}
	}
	return filter
}

// ── Writing ──

// InsertOne inserts a document and returns the inserted ID as a string.
func (s *MongoSession) InsertOne(dbName, collection, docJSON string) (string, error) {
	client := s.Client()
	if client == nil {
		return "", fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	var doc bson.M
	if err := bson.UnmarshalExtJSON([]byte(docJSON), true, &doc); err != nil {
		return "", fmt.Errorf("invalid document JSON: %w", err)
	}

	coll := client.Database(dbName).Collection(collection)
	result, err := coll.InsertOne(ctx, doc)
	if err != nil {
		return "", fmt.Errorf("insert: %w", err)
	}

	return fmt.Sprintf("%v", result.InsertedID), nil
}

// UpdateOne updates a single document matching the filter.
func (s *MongoSession) UpdateOne(dbName, collection, filterJSON, updateJSON string) error {
	client := s.Client()
	if client == nil {
		return fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	var filter bson.M
	if err := bson.UnmarshalExtJSON([]byte(filterJSON), true, &filter); err != nil {
		return fmt.Errorf("invalid filter JSON: %w", err)
	}

	var update bson.M
	if err := bson.UnmarshalExtJSON([]byte(updateJSON), true, &update); err != nil {
		return fmt.Errorf("invalid update JSON: %w", err)
	}

	coll := client.Database(dbName).Collection(collection)
	result, err := coll.UpdateOne(ctx, fixObjectIDFilter(filter), bson.M{"$set": update})
	if err != nil {
		return fmt.Errorf("update: %w", err)
	}
	if result.MatchedCount == 0 {
		return fmt.Errorf("no document matched the filter")
	}
	return nil
}

// DeleteOne deletes a single document matching the filter.
func (s *MongoSession) DeleteOne(dbName, collection, filterJSON string) error {
	client := s.Client()
	if client == nil {
		return fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	var filter bson.M
	if err := bson.UnmarshalExtJSON([]byte(filterJSON), true, &filter); err != nil {
		return fmt.Errorf("invalid filter JSON: %w", err)
	}

	coll := client.Database(dbName).Collection(collection)
	result, err := coll.DeleteOne(ctx, fixObjectIDFilter(filter))
	if err != nil {
		return fmt.Errorf("delete: %w", err)
	}
	if result.DeletedCount == 0 {
		return fmt.Errorf("no document matched the filter")
	}
	return nil
}

// ── Indexes ──

// ListIndexes returns all indexes for a collection.
func (s *MongoSession) ListIndexes(dbName, collection string) ([]MongoIndexInfo, error) {
	client := s.Client()
	if client == nil {
		return nil, fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	coll := client.Database(dbName).Collection(collection)
	cursor, err := coll.Indexes().List(ctx)
	if err != nil {
		return nil, fmt.Errorf("list indexes: %w", err)
	}
	defer cursor.Close(ctx)

	var indexes []MongoIndexInfo
	for cursor.Next(ctx) {
		var raw bson.M
		if err := cursor.Decode(&raw); err != nil {
			continue
		}

		info := MongoIndexInfo{}
		if name, ok := raw["name"].(string); ok {
			info.Name = name
		}
		if key, ok := raw["key"].(bson.M); ok {
			for field, dir := range key {
				dirStr := fmt.Sprintf("%v", dir)
				keyStr := field
				if dirStr == "-1" {
					keyStr = field + " (desc)"
				}
				info.Keys = append(info.Keys, keyStr)
			}
		}
		if unique, ok := raw["unique"].(bool); ok {
			info.Unique = unique
		}
		info.Type = "ascending"
		indexes = append(indexes, info)
	}

	return indexes, nil
}

// CreateIndex creates an index on a collection.
func (s *MongoSession) CreateIndex(dbName, collection, name string, keys []string, unique bool) error {
	client := s.Client()
	if client == nil {
		return fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Build index keys: each key is "field" or "-field" for descending
	var doc bson.D
	for _, k := range keys {
		dir := int32(1)
		f := k
		if len(k) > 0 && k[0] == '-' {
			dir = -1
			f = k[1:]
		}
		doc = append(doc, bson.E{Key: f, Value: dir})
	}

	idx := mongo.IndexModel{
		Keys:    doc,
		Options: options.Index().SetName(name).SetUnique(unique),
	}
	_, err := client.Database(dbName).Collection(collection).Indexes().CreateOne(ctx, idx)
	return err
}

// DropIndex drops an index from a collection.
func (s *MongoSession) DropIndex(dbName, collection, name string) error {
	client := s.Client()
	if client == nil {
		return fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	_, err := client.Database(dbName).Collection(collection).Indexes().DropOne(ctx, name)
	return err
}

// ── DDL ──

// CreateCollection creates a new collection in the specified database.
func (s *MongoSession) CreateCollection(dbName, collection string) error {
	client := s.Client()
	if client == nil {
		return fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	return client.Database(dbName).CreateCollection(ctx, collection)
}

// DropCollection drops a collection from the specified database.
func (s *MongoSession) DropCollection(dbName, collection string) error {
	client := s.Client()
	if client == nil {
		return fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	return client.Database(dbName).Collection(collection).Drop(ctx)
}

// DropDatabase drops the specified database.
func (s *MongoSession) DropDatabase(dbName string) error {
	client := s.Client()
	if client == nil {
		return fmt.Errorf("not connected")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	return client.Database(dbName).Drop(ctx)
}
