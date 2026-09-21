package session

import (
	"database/sql"
	"fmt"
	"time"

	"easyaiot/terminal/backend/database"
	"easyaiot/terminal/backend/log"
)

type DatabaseSession struct {
	baseSession
	db     *sql.DB
	dbType string
	closed bool
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

// DBType returns the database type string.
func (s *DatabaseSession) DBType() string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.dbType
}
