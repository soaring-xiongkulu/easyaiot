package database

import (
	"context"
	"database/sql"
	"fmt"
	"net/url"
	"strings"

	_ "github.com/rqlite/gorqlite/stdlib"
)

type rqliteProvider struct{}

func init() {
	Register("rqlite", &rqliteProvider{})
}

func (p *rqliteProvider) DSN(host string, port int, user, password, dbName string, extraParams map[string]string) string {
	addr := host
	if port > 0 {
		addr = fmt.Sprintf("%s:%d", host, port)
	}
	u := &url.URL{Scheme: "http", Host: addr}
	if user != "" || password != "" {
		u.User = url.UserPassword(user, password)
	}
	if len(extraParams) > 0 {
		q := u.Query()
		for k, v := range extraParams {
			q.Set(k, v)
		}
		u.RawQuery = q.Encode()
	}
	return u.String()
}

func (p *rqliteProvider) DriverName() string {
	return "rqlite"
}

func (p *rqliteProvider) Quote(name string) string {
	q, _ := SafePgIdent(name)
	return q
}

func (p *rqliteProvider) PrepareExec(db execer, dbName string) error {
	return nil
}

func (p *rqliteProvider) DefaultTableQuery(dbName, tableName string, limit, offset int) string {
	if offset > 0 {
		return fmt.Sprintf("SELECT * FROM %s LIMIT %d OFFSET %d", p.Quote(tableName), limit, offset)
	}
	return fmt.Sprintf("SELECT * FROM %s LIMIT %d", p.Quote(tableName), limit)
}

func (p *rqliteProvider) PagedTableQuery(dbName, tableName string, limit, offset int) string {
	return fmt.Sprintf("SELECT * FROM %s LIMIT %d OFFSET %d", p.Quote(tableName), limit, offset)
}

func (p *rqliteProvider) InsertRow(db *sql.DB, dbName, tableName string, values map[string]any) error {
	cols := sortedKeys(values)
	quotedCols := make([]string, len(cols))
	placeholders := make([]string, len(cols))
	args := make([]any, 0, len(cols))
	for i, c := range cols {
		quotedCols[i] = p.Quote(c)
		placeholders[i] = "?"
		args = append(args, values[c])
	}
	sql := fmt.Sprintf("INSERT INTO %s (%s) VALUES (%s)",
		p.Quote(tableName), strings.Join(quotedCols, ", "), strings.Join(placeholders, ", "))
	return execPrepared(p, db, dbName, sql, args)
}

func (p *rqliteProvider) UpdateRow(db *sql.DB, dbName, tableName string, set, where map[string]any) error {
	args := make([]any, 0, len(set)+len(where))
	phIdx := 1

	setParts := make([]string, 0, len(set))
	for _, c := range sortedKeys(set) {
		if set[c] == nil {
			setParts = append(setParts, fmt.Sprintf("%s = NULL", p.Quote(c)))
		} else {
			setParts = append(setParts, fmt.Sprintf("%s = ?", p.Quote(c)))
			args = append(args, set[c])
			phIdx++
		}
	}

	whereParts := make([]string, 0, len(where))
	for _, c := range sortedKeys(where) {
		if where[c] == nil {
			whereParts = append(whereParts, fmt.Sprintf("%s IS NULL", p.Quote(c)))
		} else {
			whereParts = append(whereParts, fmt.Sprintf("%s = ?", p.Quote(c)))
			args = append(args, where[c])
			phIdx++
		}
	}

	sql := fmt.Sprintf("UPDATE %s SET %s", p.Quote(tableName), strings.Join(setParts, ", "))
	if len(whereParts) > 0 {
		sql += " WHERE " + strings.Join(whereParts, " AND ")
	}
	return execPrepared(p, db, dbName, sql, args)
}

func (p *rqliteProvider) DeleteRow(db *sql.DB, dbName, tableName string, where map[string]any) error {
	args := make([]any, 0, len(where))
	phIdx := 1
	whereParts := make([]string, 0, len(where))
	for _, c := range sortedKeys(where) {
		if where[c] == nil {
			whereParts = append(whereParts, fmt.Sprintf("%s IS NULL", p.Quote(c)))
		} else {
			whereParts = append(whereParts, fmt.Sprintf("%s = ?", p.Quote(c)))
			args = append(args, where[c])
			phIdx++
		}
	}

	sql := fmt.Sprintf("DELETE FROM %s", p.Quote(tableName))
	if len(whereParts) > 0 {
		sql += " WHERE " + strings.Join(whereParts, " AND ")
	}
	return execPrepared(p, db, dbName, sql, args)
}

func (p *rqliteProvider) GetCapabilities() DBCapabilities {
	return DBCapabilities{
		"supportsOnUpdate":       false,
		"supportsCollation":      false,
		"supportsComment":        false,
		"supportsModifyColumn":   false,
		"supportsPrimaryKey":     false,
		"supportsCreateDatabase": false,
		"columnTypes":            rqliteTypes,
		"intTypes":               rqliteIntTypes,
	}
}

// ── Schema discovery ──

func (p *rqliteProvider) GetDatabases(db *sql.DB) ([]string, error) {
	return []string{"main"}, nil
}

func (p *rqliteProvider) GetTables(db *sql.DB, dbName string) ([]TableInfo, error) {
	results, err := queryStrings(db, "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view')")
	if err != nil {
		return nil, fmt.Errorf("get tables: %w", err)
	}
	infos := make([]TableInfo, 0, len(results))
	for _, row := range results {
		name := row["name"]
		if name == "sqlite_sequence" {
			continue
		}
		tp := strings.ToLower(row["type"])
		infos = append(infos, TableInfo{Name: name, Type: tp})
	}
	return infos, nil
}

func (p *rqliteProvider) GetTableSchema(db *sql.DB, dbName, tableName string) (*SchemaResult, error) {
	q := p.Quote
	colRows, err := queryStrings(db, fmt.Sprintf("PRAGMA table_info(%s)", q(tableName)))
	if err != nil {
		return nil, fmt.Errorf("get columns: %w", err)
	}

	columns := make([]ColumnInfo, 0, len(colRows))
	for _, row := range colRows {
		nullable := row["notnull"] == "0"
		isPrimary := row["pk"] != "" && row["pk"] != "0"
		defVal := row["dflt_value"]
		defaultType := "none"
		if defVal == "" && nullable {
			defaultType = "null"
			defVal = "NULL"
		} else if defVal == "NULL" {
			defaultType = "null"
		} else if defVal != "" {
			defaultType = "value"
		}
		columns = append(columns, ColumnInfo{
			Name:        row["name"],
			Type:        row["type"],
			Nullable:    nullable,
			DefaultVal:  defVal,
			DefaultType: defaultType,
			IsPrimary:   isPrimary,
		})
	}

	// Detect AUTOINCREMENT by checking sqlite_sequence
	seqRows, err := queryStrings(db, "SELECT name FROM sqlite_sequence WHERE name = ?", tableName)
	if err == nil && len(seqRows) > 0 {
		for i := range columns {
			if columns[i].IsPrimary && strings.Contains(strings.ToUpper(columns[i].Type), "INT") {
				columns[i].DefaultType = "auto"
			}
		}
	}

	idxRows, err := queryStrings(db, fmt.Sprintf("PRAGMA index_list(%s)", q(tableName)))
	if err != nil {
		return nil, fmt.Errorf("get indexes: %w", err)
	}

	indexes := make([]IndexInfo, 0)
	for _, idx := range idxRows {
		info := IndexInfo{
			Name:   idx["name"],
			Unique: idx["unique"] == "1",
		}
		colRows, err := queryStrings(db, fmt.Sprintf("PRAGMA index_info(%s)", q(idx["name"])))
		if err == nil {
			for _, c := range colRows {
				info.Columns = append(info.Columns, c["name"])
			}
		}
		indexes = append(indexes, info)
	}

	return &SchemaResult{Columns: columns, Indexes: indexes}, nil
}

// ── DDL: Database ──

func (p *rqliteProvider) CreateDatabase(db *sql.DB, dbName string) error {
	return fmt.Errorf("rqlite does not support CREATE DATABASE")
}

func (p *rqliteProvider) DropDatabase(db *sql.DB, dbName string) error {
	return fmt.Errorf("rqlite does not support DROP DATABASE")
}

// ── DDL: Table ──

func (p *rqliteProvider) CreateTable(db *sql.DB, dbName, tableName string) error {
	q := p.Quote
	_, err := db.Exec(fmt.Sprintf("CREATE TABLE %s (id INTEGER PRIMARY KEY AUTOINCREMENT)", q(tableName)))
	return err
}

func (p *rqliteProvider) DropTable(db *sql.DB, dbName, tableName string) error {
	q := p.Quote
	_, err := db.Exec(fmt.Sprintf("DROP TABLE %s", q(tableName)))
	return err
}

func (p *rqliteProvider) DropView(db *sql.DB, dbName, viewName string) error {
	q := p.Quote
	_, err := db.Exec(fmt.Sprintf("DROP VIEW %s", q(viewName)))
	return err
}

func (p *rqliteProvider) TruncateTable(db *sql.DB, dbName, tableName string) error {
	q := p.Quote
	_, err := db.Exec(fmt.Sprintf("DELETE FROM %s", q(tableName)))
	return err
}

// CopyTable has no native clone in SQLite/rqlite; replay the DumpTable output
// (structure + INSERTs) with the destination name substituted for the source.
func (p *rqliteProvider) CopyTable(db *sql.DB, dbName, tableName, newTableName string) error {
	dump, err := p.DumpTable(db, dbName, tableName, DumpOptions{Structure: true, Data: true})
	if err != nil {
		return err
	}
	stmts := SplitScript(dump)
	ctx := context.Background()
	for _, st := range stmts {
		// Skip the DROP guard emitted by DumpTable — the destination must be
		// created fresh or fail loudly if it already exists.
		if strings.HasPrefix(strings.ToUpper(st.SQL), "DROP ") {
			continue
		}
		// The CREATE and INSERT statements reference the source table name;
		// rename the first occurrence (CREATE "...name") and the INSERT target.
		sqlStr := renameLeadingTableRef(st.SQL, tableName, newTableName)
		if _, err := db.ExecContext(ctx, sqlStr); err != nil {
			return err
		}
	}
	return nil
}

// renameLeadingTableRef rewrites the quoted source table name that follows the
// leading CREATE TABLE / INSERT INTO keyword of a dump statement.
func renameLeadingTableRef(stmt, oldName, newName string) string {
	q := strings.Index(stmt, `"`)
	if q >= 0 {
		quotedOld := `"` + oldName + `"`
		if strings.Contains(stmt, quotedOld) {
			return strings.Replace(stmt, quotedOld, `"`+newName+`"`, 1)
		}
	}
	return stmt
}

// ── DDL: Column ──

func (p *rqliteProvider) AddColumn(db *sql.DB, dbName, tableName string, col ColumnDef) error {
	if col.DefaultType == "auto" {
		return fmt.Errorf("rqlite only supports AUTOINCREMENT on INTEGER PRIMARY KEY columns at table creation time; use CREATE TABLE instead")
	}
	q := p.Quote
	var parts []string
	parts = append(parts, q(col.Name), col.Type)

	if col.Nullable {
		parts = append(parts, "NULL")
	} else {
		parts = append(parts, "NOT NULL")
	}

	switch col.DefaultType {
	case "null":
		parts = append(parts, "DEFAULT NULL")
	case "value":
		if col.DefaultVal != "" {
			parts = append(parts, "DEFAULT "+col.DefaultVal)
		} else {
			parts = append(parts, "DEFAULT ''")
		}
	}

	sql := fmt.Sprintf("ALTER TABLE %s ADD COLUMN %s", q(tableName), strings.Join(parts, " "))
	_, err := db.Exec(sql)
	return err
}

func (p *rqliteProvider) ModifyColumn(db *sql.DB, dbName, tableName string, col ColumnDef) error {
	return fmt.Errorf("rqlite does not support MODIFY COLUMN; rebuild the table instead")
}

func (p *rqliteProvider) DropColumn(db *sql.DB, dbName, tableName, colName string) error {
	q := p.Quote
	_, err := db.Exec(fmt.Sprintf("ALTER TABLE %s DROP COLUMN %s", q(tableName), q(colName)))
	return err
}

// ── DDL: Index ──

func (p *rqliteProvider) AddIndex(db *sql.DB, dbName, tableName string, idx IndexDef) error {
	q := p.Quote
	if idx.IsPrimary {
		return fmt.Errorf("rqlite does not support adding PRIMARY KEY after table creation")
	}
	uniqueStr := ""
	if idx.Unique {
		uniqueStr = "UNIQUE "
	}
	cols := make([]string, len(idx.Columns))
	for i, c := range idx.Columns {
		cols[i] = q(c)
	}
	_, err := db.Exec(fmt.Sprintf("CREATE %sINDEX %s ON %s (%s)", uniqueStr, q(idx.Name), q(tableName), strings.Join(cols, ", ")))
	return err
}

func (p *rqliteProvider) DropIndex(db *sql.DB, dbName, tableName, idxName string, isPrimary bool, autoIncCols []string) error {
	if isPrimary {
		return fmt.Errorf("rqlite does not support dropping PRIMARY KEY")
	}
	_, err := db.Exec(fmt.Sprintf("DROP INDEX %s", p.Quote(idxName)))
	return err
}

var rqliteTypes = []string{
	"INTEGER", "INT", "BIGINT", "SMALLINT", "TINYINT",
	"REAL", "DOUBLE", "FLOAT",
	"DECIMAL", "DECIMAL(10,2)",
	"NUMERIC", "NUMERIC(10,2)",
	"CHAR", "CHAR(1)",
	"VARCHAR", "VARCHAR(255)",
	"TEXT", "BLOB",
	"DATE", "DATETIME", "TIMESTAMP", "TIME",
	"BOOLEAN", "JSON",
}

var rqliteIntTypes = []string{
	"INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT",
}

func (p *rqliteProvider) DumpTable(db *sql.DB, dbName, tableName string, opts DumpOptions) (string, error) {
	ctx := context.Background()
	conn, err := db.Conn(ctx)
	if err != nil {
		return "", err
	}
	defer conn.Close()

	var b strings.Builder
	quotedTable := p.Quote(tableName)

	if opts.Structure {
		var createSQL string
		kind := tableKindSQLite(conn, tableName)
		err := conn.QueryRowContext(ctx,
			"SELECT sql FROM sqlite_master WHERE type=? AND name=? AND name NOT LIKE 'sqlite_%' LIMIT 1",
			kind, tableName).Scan(&createSQL)
		if err != nil && err != sql.ErrNoRows {
			return "", err
		}
		if createSQL != "" {
			b.WriteString("--\n-- Structure for ")
			b.WriteString(tableName)
			b.WriteString("\n--\nDROP ")
			if kind == "view" {
				b.WriteString("VIEW")
			} else {
				b.WriteString("TABLE")
			}
			b.WriteString(" IF EXISTS ")
			b.WriteString(quotedTable)
			b.WriteString(";\n")
			b.WriteString(createSQL)
			if !strings.HasSuffix(createSQL, ";") {
				b.WriteByte(';')
			}
			b.WriteString("\n\n")
		}
	}

	if opts.Data {
		cols, derr := sqliteTableColumns(conn, tableName, quotedTable)
		if derr != nil {
			return "", derr
		}
		if len(cols) > 0 {
			b.WriteString("--\n-- Data for ")
			b.WriteString(tableName)
			b.WriteString("\n--\n")
			colList := make([]string, len(cols))
			for i, c := range cols {
				colList[i] = p.Quote(c)
			}
			prefix := "INSERT INTO " + quotedTable + " (" + strings.Join(colList, ", ") + ") VALUES "

			rows, err := conn.QueryContext(ctx, "SELECT "+strings.Join(colList, ", ")+" FROM "+quotedTable)
			if err != nil {
				return "", err
			}
			defer rows.Close()

			for rows.Next() {
				vals := make([]any, len(cols))
				ptrs := make([]any, len(cols))
				for i := range vals {
					ptrs[i] = &vals[i]
				}
				if err := rows.Scan(ptrs...); err != nil {
					return "", err
				}
				b.WriteString(prefix)
				b.WriteByte('(')
				for i, v := range vals {
					if i > 0 {
						b.WriteString(", ")
					}
					b.WriteString(dumpRqliteValue(v))
				}
				b.WriteString(");\n")
			}
			if err := rows.Err(); err != nil {
				return "", err
			}
			b.WriteByte('\n')
		}
	}

	return b.String(), nil
}

// tableKindSQLite returns "table" or "view" from sqlite_master.
func tableKindSQLite(conn *sql.Conn, tableName string) string {
	var t string
	err := conn.QueryRowContext(context.Background(),
		"SELECT type FROM sqlite_master WHERE name=? AND name NOT LIKE 'sqlite_%' LIMIT 1", tableName).Scan(&t)
	if err == nil && t == "view" {
		return "view"
	}
	return "table"
}

// sqliteTableColumns returns column names via PRAGMA table_info.
func sqliteTableColumns(conn *sql.Conn, tableName, quotedTable string) ([]string, error) {
	rows, err := conn.QueryContext(context.Background(), "PRAGMA table_info("+quotedTable+")")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var cols []string
	for rows.Next() {
		var cid int
		var name, ctype string
		var notnull int
		var dflt sql.NullString
		var pk int
		if err := rows.Scan(&cid, &name, &ctype, &notnull, &dflt, &pk); err != nil {
			return nil, err
		}
		cols = append(cols, name)
	}
	return cols, rows.Err()
}

// dumpRqliteValue renders a scanned cell as a SQLite literal. Blobs become
// x'..' hex literals; booleans and numbers pass through; everything else is
// a quoted string.
func dumpRqliteValue(v any) string {
	if v == nil {
		return "NULL"
	}
	switch val := v.(type) {
	case []byte:
		return "x'" + hexLower(val) + "'"
	case string:
		return quotedString(val)
	case bool:
		if val {
			return "1"
		}
		return "0"
	default:
		return scanToString(v)
	}
}
