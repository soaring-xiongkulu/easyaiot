package session

import (
	"database/sql"
	"errors"
	"fmt"
	"sync"
	"time"

	"easyaiot/terminal/backend/database"
	"easyaiot/terminal/backend/log"
)

type DatabaseSession struct {
	baseSession
	db     *sql.DB
	dbType string
	closed bool

	// Cross-database support (PostgreSQL): the PG protocol binds one
	// connection to a single database and has no USE, so requests naming a
	// different database are served by a lazily-opened pool whose DSN carries
	// that database. Other engines share the main pool.
	poolMu        sync.Mutex
	cfg           *ConnectionConfig
	dbPools       map[string]*sql.DB
	defaultDBName string
	defaultDBOnce sync.Once
}

func NewDatabaseSession(id string) *DatabaseSession {
	return &DatabaseSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "database",
			status:      StatusDisconnected,
		},
	}
}

func (s *DatabaseSession) Connect(config ConnectionConfig) error {
	log.Writef("[DatabaseSession.Connect] id=%s, dbType=%s, host=%s, port=%d, user=%s, dbName=%s",
		s.id, config.DBType, config.Host, config.Port, config.User, config.DBName)

	s.setStatus(StatusConnecting)

	s.dbType = config.DBType

	if config.Name != "" {
		s.title = config.Name
	} else {
		s.title = fmt.Sprintf("%s:%s@%s:%d", config.DBType, config.User, config.Host, config.Port)
	}

	dsn, err := database.BuildDSN(config.DBType, config.Host, config.User, config.Password, config.DBName, config.DBParams, config.Port)
	if err != nil {
		log.Writef("[DatabaseSession.Connect] BuildDSN failed: %v", err)
		s.setStatus(StatusError)
		return err
	}
	log.Writef("[DatabaseSession.Connect] DSN built, opening database...")

	db, err := database.NewDB(config.DBType, dsn)
	if err != nil {
		log.Writef("[DatabaseSession.Connect] NewDB failed: %v", err)
		s.setStatus(StatusError)
		return err
	}

	db.SetMaxOpenConns(5)
	db.SetMaxIdleConns(2)
	db.SetConnMaxLifetime(5 * time.Minute)

	log.Writef("[DatabaseSession.Connect] db opened, pinging...")

	if err := db.Ping(); err != nil {
		log.Writef("[DatabaseSession.Connect] Ping failed: %v", err)
		db.Close()
		s.setStatus(StatusError)
		return fmt.Errorf("ping %s: %w", config.DBType, err)
	}

	log.Writef("[DatabaseSession.Connect] ping OK, connected successfully")
	s.db = db
	s.cfg = &config
	s.setStatus(StatusConnected)
	return nil
}

func (s *DatabaseSession) Disconnect() error {
	s.mu.Lock()
	if s.closed {
		s.mu.Unlock()
		return nil
	}
	s.closed = true
	s.mu.Unlock()

	if s.db != nil {
		s.db.Close()
	}
	s.poolMu.Lock()
	for _, db := range s.dbPools {
		db.Close()
	}
	s.dbPools = nil
	s.poolMu.Unlock()
	s.setStatus(StatusDisconnected)
	return nil
}

func (s *DatabaseSession) IsConnected() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.status == StatusConnected && s.db != nil
}

func (s *DatabaseSession) Write(data []byte) error {
	return nil
}

func (s *DatabaseSession) Resize(cols, rows int) error {
	return nil
}

// DB returns the underlying database/sql connection (used by Wails bindings).
func (s *DatabaseSession) DB() *sql.DB {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.db
}

// DBFor returns the pool that serves dbName. PostgreSQL only: a database
// other than the one the main pool connected to gets a lazily-created
// dedicated pool, because the protocol offers no way to switch databases on
// an open connection. Every other engine (and every empty/unmatched-name
// case) shares the main pool — MySQL switches via USE in its PrepareExec,
// the rest are single-database.
func (s *DatabaseSession) DBFor(dbName string) (*sql.DB, error) {
	if dbName == "" || dbName == s.defaultDB() {
		return s.DB(), nil
	}
	s.poolMu.Lock()
	defer s.poolMu.Unlock()
	if s.closed {
		return nil, errors.New("session closed")
	}
	if db, ok := s.dbPools[dbName]; ok {
		return db, nil
	}
	cfg := s.cfg
	if cfg == nil {
		return s.DB(), nil
	}
	dsn, err := database.BuildDSN(cfg.DBType, cfg.Host, cfg.User, cfg.Password, dbName, cfg.DBParams, cfg.Port)
	if err != nil {
		return nil, err
	}
	db, err := database.NewDB(cfg.DBType, dsn)
	if err != nil {
		return nil, fmt.Errorf("open database %s: %w", dbName, err)
	}
	db.SetMaxOpenConns(2)
	db.SetMaxIdleConns(1)
	db.SetConnMaxLifetime(5 * time.Minute)
	if err := db.Ping(); err != nil {
		db.Close()
		return nil, fmt.Errorf("connect database %s: %w", dbName, err)
	}
	if s.dbPools == nil {
		s.dbPools = map[string]*sql.DB{}
	}
	s.dbPools[dbName] = db
	return db, nil
}

// defaultDB names the database the main pool is bound to: the configured
// name, or — when the config left it empty — the server-side answer
// (lib/pq falls back to the user name), resolved once and cached.
func (s *DatabaseSession) defaultDB() string {
	if s.cfg != nil && s.cfg.DBName != "" {
		return s.cfg.DBName
	}
	s.defaultDBOnce.Do(func() {
		if s.dbType != "postgres" {
			return
		}
		db := s.DB()
		if db == nil {
			return
		}
		var name string
		if err := db.QueryRow("SELECT current_database()").Scan(&name); err == nil {
			s.defaultDBName = name
		}
	})
	return s.defaultDBName
}

// DBType returns the database type string.
func (s *DatabaseSession) DBType() string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.dbType
}
