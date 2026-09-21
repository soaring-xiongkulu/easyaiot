package database

import (
	"context"
	"database/sql"
	"fmt"
	"net/url"
	"strings"
	"time"

	_ "github.com/microsoft/go-mssqldb"
)

type sqlserverProvider struct{}

func init() {
	Register("sqlserver", &sqlserverProvider{})
}

func (p *sqlserverProvider) DSN(host string, port int, user, password, dbName string, extraParams map[string]string) string {
	// A named instance ("server\instance") must not go into url.URL.Host:
	// url.URL.String() escapes the backslash to %5C and the driver's
	// url.Parse then rejects the DSN. The driver instead expects the
	// instance as the URL path (sqlserver://host/instance). With an
	// instance and no explicit port, omit the port so the driver resolves
	// the instance's dynamic port via SQL Browser (a forced 1433 would
	// bypass the Browser and almost always fail).
	u := &url.URL{Scheme: "sqlserver", User: url.UserPassword(user, password)}
	if server, instance, found := strings.Cut(host, `\`); found {
		u.Path = "/" + instance
		host = server
	} else if port <= 0 {
		port = 1433
	}
	if port > 0 {
		u.Host = fmt.Sprintf("%s:%d", host, port)
	} else {
		u.Host = host
	}
	q := u.Query()
	if dbName != "" {
		q.Set("database", dbName)
	}
	q.Set("encrypt", "disable")
	q.Set("dial timeout", "10")
	q.Set("connection timeout", "30")
	for k, v := range extraParams {
		q.Set(k, v)
	}
	u.RawQuery = q.Encode()
	return u.String()
}

func (p *sqlserverProvider) DriverName() string {
	return "sqlserver"
}

func (p *sqlserverProvider) Quote(name string) string {
	return "[" + strings.ReplaceAll(name, "]", "]]") + "]"
}

func (p *sqlserverProvider) PrepareExec(db execer, dbName string) error {
	if dbName == "" {
		return nil
	}
	_, err := db.ExecContext(context.Background(), fmt.Sprintf("USE %s", p.Quote(dbName)))
	return err
}

func (p *sqlserverProvider) DefaultTableQuery(dbName, tableName string, limit, offset int) string {
	return fmt.Sprintf(
		"SELECT * FROM %s ORDER BY (SELECT NULL) OFFSET %d ROWS FETCH NEXT %d ROWS ONLY",
		p.qualifiedTable(tableName), offset, limit,
	)
}

func (p *sqlserverProvider) PagedTableQuery(dbName, tableName string, limit, offset int) string {
	return fmt.Sprintf("SELECT * FROM %s ORDER BY (SELECT NULL) OFFSET %d ROWS FETCH NEXT %d ROWS ONLY", p.qualifiedTable(tableName), offset, limit)
}

func (p *sqlserverProvider) qualifiedTable(tableName string) string {
	return p.Quote(tableName)
}

// ── CRUD ──
//
// InsertRow/UpdateRow/DeleteRow go through execPrepared so that:
//   - USE [dbName] and the actual statement run on the same pooled conn
//     (DB-10, AUDIT-database-10). Previously each CRUD call issued a
//     `USE [db];\n...` multi-statement batch; the driver handles it but
//     the pool could still split work across conns for the trailing USE.
//   - context propagation is consistent with the other providers.
//
// withUse is intentionally not prepended here — execPrepared already calls
// PrepareExec, which issues USE [dbName] on the pinned connection.

func (p *sqlserverProvider) InsertRow(db *sql.DB, dbName, tableName string, values map[string]any) error {
	cols := sortedKeys(values)
	quotedCols := make([]string, len(cols))
	placeholders := make([]string, len(cols))
	args := make([]any, 0, len(cols))
	for i, c := range cols {
		quotedCols[i] = p.Quote(c)
		placeholders[i] = fmt.Sprintf("@p%d", i+1)
		args = append(args, values[c])
	}
	sql := fmt.Sprintf("INSERT INTO %s (%s) VALUES (%s)",
		p.qualifiedTable(tableName), strings.Join(quotedCols, ", "), strings.Join(placeholders, ", "))
	return execPrepared(p, db, dbName, sql, args)
}

func (p *sqlserverProvider) UpdateRow(db *sql.DB, dbName, tableName string, set, where map[string]any) error {
	args := make([]any, 0, len(set)+len(where))
	phIdx := 1

	setParts := make([]string, 0, len(set))
	for _, c := range sortedKeys(set) {
		if set[c] == nil {
			setParts = append(setParts, fmt.Sprintf("%s = NULL", p.Quote(c)))
		} else {
			setParts = append(setParts, fmt.Sprintf("%s = @p%d", p.Quote(c), phIdx))
			args = append(args, set[c])
			phIdx++
		}
	}

	whereParts := make([]string, 0, len(where))
	for _, c := range sortedKeys(where) {
		if where[c] == nil {
			whereParts = append(whereParts, fmt.Sprintf("%s IS NULL", p.Quote(c)))
		} else {
			whereParts = append(whereParts, fmt.Sprintf("%s = @p%d", p.Quote(c), phIdx))
			args = append(args, where[c])
			phIdx++
		}
	}

	sql := fmt.Sprintf("UPDATE %s SET %s", p.qualifiedTable(tableName), strings.Join(setParts, ", "))
	if len(whereParts) > 0 {
		sql += " WHERE " + strings.Join(whereParts, " AND ")
	}
	return execPrepared(p, db, dbName, sql, args)
}

func (p *sqlserverProvider) DeleteRow(db *sql.DB, dbName, tableName string, where map[string]any) error {
	args := make([]any, 0, len(where))
	phIdx := 1
	whereParts := make([]string, 0, len(where))
	for _, c := range sortedKeys(where) {
		if where[c] == nil {
			whereParts = append(whereParts, fmt.Sprintf("%s IS NULL", p.Quote(c)))
		} else {
			whereParts = append(whereParts, fmt.Sprintf("%s = @p%d", p.Quote(c), phIdx))
			args = append(args, where[c])
			phIdx++
		}
	}

	sql := fmt.Sprintf("DELETE FROM %s", p.qualifiedTable(tableName))
	if len(whereParts) > 0 {
		sql += " WHERE " + strings.Join(whereParts, " AND ")
	}
	return execPrepared(p, db, dbName, sql, args)
}

// ── Capabilities ──

func (p *sqlserverProvider) GetCapabilities() DBCapabilities {
	return DBCapabilities{
		"supportsOnUpdate":           false,
		"supportsCollation":          true,
		"supportsComment":            false,
		"autoIncrementForcesNotNull": true,
		"columnTypes":                sqlserverTypes,
		"intTypes":                   sqlserverIntTypes,
	}
}

// ── Schema discovery ──

func (p *sqlserverProvider) GetDatabases(db *sql.DB) ([]string, error) {
	results, err := queryStrings(db, `
		SELECT name FROM sys.databases
		WHERE name NOT IN ('master','tempdb','model','msdb')
		ORDER BY name`)
	if err != nil {
		return nil, err
	}
	names := make([]string, 0, len(results))
	for _, row := range results {
		names = append(names, row["name"])
	}
	return names, nil
}

func (p *sqlserverProvider) GetTables(db *sql.DB, dbName string) ([]TableInfo, error) {
	query := `
		SELECT t.name AS table_name, 'TABLE' AS type_desc,
		       ISNULL(CONVERT(nvarchar(4000), ep.value), '') AS table_comment
		FROM sys.tables t
		LEFT JOIN sys.extended_properties ep
		  ON ep.major_id = t.object_id AND ep.minor_id = 0 AND ep.name = N'MS_Description'
		WHERE t.is_ms_shipped = 0
		UNION ALL
		SELECT v.name AS table_name, 'VIEW' AS type_desc,
		       ISNULL(CONVERT(nvarchar(4000), ep.value), '') AS table_comment
		FROM sys.views v
		LEFT JOIN sys.extended_properties ep
		  ON ep.major_id = v.object_id AND ep.minor_id = 0 AND ep.name = N'MS_Description'
		WHERE v.is_ms_shipped = 0
		ORDER BY table_name`
	results, err := queryStrings(db, p.withUse(dbName, query))
	if err != nil {
		return nil, fmt.Errorf("get tables: %w", err)
	}
	infos := make([]TableInfo, 0, len(results))
	for _, row := range results {
		tp := "table"
		if row["type_desc"] == "VIEW" {
			tp = "view"
		}
		infos = append(infos, TableInfo{
			Name:    row["table_name"],
			Type:    tp,
			Comment: row["table_comment"],
		})
	}
	return infos, nil
}

func (p *sqlserverProvider) GetTableSchema(db *sql.DB, dbName, tableName string) (*SchemaResult, error) {
	colRows, err := queryStrings(db, p.withUse(dbName, `
		SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT,
		       CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
		FROM INFORMATION_SCHEMA.COLUMNS
		WHERE TABLE_NAME = @p1
		ORDER BY ORDINAL_POSITION`), tableName)
	if err != nil {
		return nil, fmt.Errorf("get columns: %w", err)
	}

	pkRows, err := queryStrings(db, p.withUse(dbName, `
		SELECT kcu.COLUMN_NAME
		FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
		JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
		  ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
		  AND tc.TABLE_NAME = kcu.TABLE_NAME
		WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
		  AND tc.TABLE_NAME = @p1`), tableName)
	pkCols := make(map[string]bool)
	if err == nil {
		for _, row := range pkRows {
			pkCols[row["COLUMN_NAME"]] = true
		}
	}

	columns := make([]ColumnInfo, 0, len(colRows))
	for _, row := range colRows {
		nullable := row["IS_NULLABLE"] == "YES"
		defVal := row["COLUMN_DEFAULT"]
		defaultType := "none"
		if defVal == "" {
			if nullable {
				defaultType = "null"
				defVal = "NULL"
			}
		} else {
			defVal = strings.Trim(defVal, "()")
			defaultType = "value"
		}

		dataType := row["DATA_TYPE"]
		typeStr := sqlserverFormatType(dataType, row["CHARACTER_MAXIMUM_LENGTH"], row["NUMERIC_PRECISION"], row["NUMERIC_SCALE"])

		columns = append(columns, ColumnInfo{
			Name:        row["COLUMN_NAME"],
			Type:        typeStr,
			Nullable:    nullable,
			DefaultVal:  defVal,
			DefaultType: defaultType,
			IsPrimary:   pkCols[row["COLUMN_NAME"]],
		})
	}

	idxRows, err := queryStrings(db, p.withUse(dbName, `
		SELECT i.name AS index_name, i.is_unique, i.is_primary_key, c.name AS column_name
		FROM sys.indexes i
		JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
		JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
		JOIN sys.tables t ON i.object_id = t.object_id
		WHERE t.name = @p1
		ORDER BY i.name, ic.key_ordinal`), tableName)
	if err != nil {
		return nil, fmt.Errorf("get indexes: %w", err)
	}

	idxMap := make(map[string]*IndexInfo)
	var idxOrder []string
	for _, row := range idxRows {
		name := row["index_name"]
		if _, ok := idxMap[name]; !ok {
			idxMap[name] = &IndexInfo{
				Name:      name,
				Columns:   []string{},
				Unique:    row["is_unique"] == "1" || row["is_unique"] == "true",
				IsPrimary: row["is_primary_key"] == "1" || row["is_primary_key"] == "true",
			}
			idxOrder = append(idxOrder, name)
		}
		idxMap[name].Columns = append(idxMap[name].Columns, row["column_name"])
	}

	indexes := make([]IndexInfo, 0, len(idxOrder))
	for _, name := range idxOrder {
		indexes = append(indexes, *idxMap[name])
	}

	return &SchemaResult{Columns: columns, Indexes: indexes}, nil
}

// ── DDL: Database ──

func (p *sqlserverProvider) CreateDatabase(db *sql.DB, dbName string) error {
	_, err := db.Exec(fmt.Sprintf("CREATE DATABASE %s", p.Quote(dbName)))
	return err
}

func (p *sqlserverProvider) DropDatabase(db *sql.DB, dbName string) error {
	_, _ = db.Exec(fmt.Sprintf("ALTER DATABASE %s SET SINGLE_USER WITH ROLLBACK IMMEDIATE", p.Quote(dbName)))
	_, err := db.Exec(fmt.Sprintf("DROP DATABASE %s", p.Quote(dbName)))
	return err
}

// ── DDL: Table ──

func (p *sqlserverProvider) CreateTable(db *sql.DB, dbName, tableName string) error {
	_, err := db.Exec(p.withUse(dbName, fmt.Sprintf("CREATE TABLE %s (id INT IDENTITY(1,1) PRIMARY KEY)", p.qualifiedTable(tableName))))
	return err
}

func (p *sqlserverProvider) DropTable(db *sql.DB, dbName, tableName string) error {
	_, err := db.Exec(p.withUse(dbName, fmt.Sprintf("DROP TABLE %s", p.qualifiedTable(tableName))))
	return err
}

func (p *sqlserverProvider) DropView(db *sql.DB, dbName, viewName string) error {
	_, err := db.Exec(p.withUse(dbName, fmt.Sprintf("DROP VIEW %s", p.qualifiedTable(viewName))))
	return err
}

func (p *sqlserverProvider) TruncateTable(db *sql.DB, dbName, tableName string) error {
	_, err := db.Exec(p.withUse(dbName, fmt.Sprintf("TRUNCATE TABLE %s", p.qualifiedTable(tableName))))
	return err
}

// CopyTable clones structure and data via SELECT INTO (no indexes/constraints).
func (p *sqlserverProvider) CopyTable(db *sql.DB, dbName, tableName, newTableName string) error {
	_, err := db.Exec(p.withUse(dbName, fmt.Sprintf("SELECT * INTO %s FROM %s", p.qualifiedTable(newTableName), p.qualifiedTable(tableName))))
	return err
}

// ── DDL: Column ──

func (p *sqlserverProvider) AddColumn(db *sql.DB, dbName, tableName string, col ColumnDef) error {
	_, err := db.Exec(p.withUse(dbName, p.buildColumnSQL("ADD", tableName, col)))
	return err
}

func (p *sqlserverProvider) ModifyColumn(db *sql.DB, dbName, tableName string, col ColumnDef) error {
	q := p.qualifiedTable
	stmts := []string{}

	stmts = append(stmts, fmt.Sprintf("ALTER TABLE %s ALTER COLUMN %s %s",
		q(tableName), p.Quote(col.Name), col.Type))

	if col.Nullable {
		stmts = append(stmts, fmt.Sprintf("ALTER TABLE %s ALTER COLUMN %s %s NULL",
			q(tableName), p.Quote(col.Name), col.Type))
	} else {
		stmts = append(stmts, fmt.Sprintf("ALTER TABLE %s ALTER COLUMN %s %s NOT NULL",
			q(tableName), p.Quote(col.Name), col.Type))
	}

	for _, s := range stmts {
		if _, err := db.Exec(p.withUse(dbName, s)); err != nil {
			return err
		}
	}
	return nil
}

func (p *sqlserverProvider) DropColumn(db *sql.DB, dbName, tableName, colName string) error {
	// Drop any default constraint bound to the column first.
	rows, err := db.Query(p.withUse(dbName, `
		SELECT dc.name
		FROM sys.default_constraints dc
		JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
		JOIN sys.tables t ON c.object_id = t.object_id
		WHERE t.name = @p1 AND c.name = @p2`), tableName, colName)
	if err != nil {
		return fmt.Errorf("find default constraints: %w", err)
	}
	defer rows.Close()

	var constraints []string
	for rows.Next() {
		var name string
		if err := rows.Scan(&name); err != nil {
			return err
		}
		constraints = append(constraints, name)
	}
	if err := rows.Err(); err != nil {
		return err
	}

	qt := p.qualifiedTable(tableName)
	for _, name := range constraints {
		if _, err := db.Exec(p.withUse(dbName, fmt.Sprintf("ALTER TABLE %s DROP CONSTRAINT %s", qt, p.Quote(name)))); err != nil {
			return fmt.Errorf("drop default constraint %s: %w", name, err)
		}
	}

	_, err = db.Exec(p.withUse(dbName, fmt.Sprintf("ALTER TABLE %s DROP COLUMN %s", qt, p.Quote(colName))))
	return err
}

// ── DDL: Index ──

func (p *sqlserverProvider) AddIndex(db *sql.DB, dbName, tableName string, idx IndexDef) error {
	q := p.Quote
	qt := p.qualifiedTable
	if idx.IsPrimary {
		cols := make([]string, len(idx.Columns))
		for i, c := range idx.Columns {
			cols[i] = q(c)
		}
		_, err := db.Exec(p.withUse(dbName, fmt.Sprintf("ALTER TABLE %s ADD PRIMARY KEY (%s)", qt(tableName), strings.Join(cols, ", "))))
		return err
	}
	uniqueStr := ""
	if idx.Unique {
		uniqueStr = "UNIQUE "
	}
	cols := make([]string, len(idx.Columns))
	for i, c := range idx.Columns {
		cols[i] = q(c)
	}
	_, err := db.Exec(p.withUse(dbName, fmt.Sprintf("CREATE %sINDEX %s ON %s (%s)", uniqueStr, q(idx.Name), qt(tableName), strings.Join(cols, ", "))))
	return err
}

func (p *sqlserverProvider) DropIndex(db *sql.DB, dbName, tableName, idxName string, isPrimary bool, autoIncCols []string) error {
	q := p.Quote
	qt := p.qualifiedTable
	if isPrimary {
		_, err := db.Exec(p.withUse(dbName, fmt.Sprintf("ALTER TABLE %s DROP CONSTRAINT %s", qt(tableName), q(idxName))))
		return err
	}
	_, err := db.Exec(p.withUse(dbName, fmt.Sprintf("DROP INDEX %s ON %s", q(idxName), qt(tableName))))
	return err
}

// ── Helpers ──

// withUse prepends a USE [dbName] statement to the query so that it
// always runs against the correct database, regardless of which connection
// the pool picks. This is the SQL Server equivalent of MySQL's
// SHOW FULL TABLES FROM `dbName` — both schema-discovery queries and
// parameterised CRUD use it because SQL Server's sys.* / INFORMATION_SCHEMA
// views are database-scoped.
func (p *sqlserverProvider) withUse(dbName, query string) string {
	if dbName == "" {
		return query
	}
	return fmt.Sprintf("USE %s;\n%s", p.Quote(dbName), query)
}

func (p *sqlserverProvider) buildColumnSQL(action, tableName string, col ColumnDef) string {
	q := p.Quote
	parts := []string{q(col.Name), col.Type}

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
			parts = append(parts, fmt.Sprintf("DEFAULT '%s'", strings.ReplaceAll(col.DefaultVal, "'", "''")))
		} else {
			parts = append(parts, "DEFAULT ''")
		}
	case "auto":
		parts = append(parts, "IDENTITY(1,1)")
	}

	return fmt.Sprintf("ALTER TABLE %s %s %s", p.qualifiedTable(tableName), action, strings.Join(parts, " "))
}

func sqlserverFormatType(dataType, charMaxLen, numericPrecision, numericScale string) string {
	switch strings.ToUpper(dataType) {
	case "VARCHAR", "NVARCHAR", "CHAR", "NCHAR", "VARBINARY", "BINARY":
		if charMaxLen != "" && charMaxLen != "-1" {
			return fmt.Sprintf("%s(%s)", dataType, charMaxLen)
		} else if charMaxLen == "-1" {
			return fmt.Sprintf("%s(MAX)", dataType)
		}
	case "DECIMAL", "NUMERIC":
		if numericPrecision != "" && numericScale != "" {
			return fmt.Sprintf("%s(%s,%s)", dataType, numericPrecision, numericScale)
		} else if numericPrecision != "" {
			return fmt.Sprintf("%s(%s)", dataType, numericPrecision)
		}
	}
	return dataType
}

var sqlserverTypes = []string{
	"BIT",
	"TINYINT", "SMALLINT", "INT", "BIGINT",
	"FLOAT", "REAL", "DECIMAL(10,2)", "NUMERIC(10,2)", "MONEY", "SMALLMONEY",
	"CHAR(1)", "VARCHAR(255)", "VARCHAR(MAX)", "NVARCHAR(255)", "NVARCHAR(MAX)",
	"TEXT", "NTEXT",
	"BINARY(1)", "VARBINARY(255)", "VARBINARY(MAX)",
	"DATE", "TIME", "DATETIME", "DATETIME2", "SMALLDATETIME", "DATETIMEOFFSET",
	"UNIQUEIDENTIFIER",
}

var sqlserverIntTypes = []string{
	"TINYINT", "SMALLINT", "INT", "BIGINT",
}

func (p *sqlserverProvider) DumpTable(db *sql.DB, dbName, tableName string, opts DumpOptions) (string, error) {
	ctx := context.Background()
	conn, err := db.Conn(ctx)
	if err != nil {
		return "", err
	}
	defer conn.Close()

	if err := p.PrepareExec(conn, dbName); err != nil {
		return "", err
	}

	var b strings.Builder
	quotedTable := p.Quote(tableName)

	if opts.Structure {
		createSQL, derr := sqlserverCreateTableSQL(conn, dbName, tableName, quotedTable)
		if derr != nil {
			return "", derr
		}
		b.WriteString("--\n-- Structure for ")
		b.WriteString(tableName)
		b.WriteString("\n--\nDROP TABLE IF EXISTS ")
		b.WriteString(quotedTable)
		b.WriteString(";\n")
		b.WriteString(createSQL)
		if !strings.HasSuffix(createSQL, ";") {
			b.WriteByte(';')
		}
		b.WriteString("\n\n")
	}

	if opts.Data {
		cols, colTypes, derr := sqlserverTableColumns(conn, dbName, tableName)
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
					b.WriteString(dumpSqlserverValue(v, colTypes[i]))
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

// sqlserverCreateTableSQL builds a CREATE TABLE statement from INFORMATION_SCHEMA.
func sqlserverCreateTableSQL(conn *sql.Conn, dbName, tableName, quotedTable string) (string, error) {
	rows, err := conn.QueryContext(context.Background(), `
		SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT,
		       CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
		FROM INFORMATION_SCHEMA.COLUMNS
		WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
		ORDER BY ORDINAL_POSITION`, dbName, tableName)
	if err != nil {
		return "", err
	}
	defer rows.Close()

	var b strings.Builder
	b.WriteString("CREATE TABLE ")
	b.WriteString(quotedTable)
	b.WriteString(" (\n")
	first := true
	for rows.Next() {
		var name, dataType, isNullable string
		var colDefault sql.NullString
		var charMaxLen, numPrec, numScale sql.NullString
		if err := rows.Scan(&name, &dataType, &isNullable, &colDefault, &charMaxLen, &numPrec, &numScale); err != nil {
			return "", err
		}
		if !first {
			b.WriteString(",\n")
		}
		first = false
		b.WriteString("  [")
		b.WriteString(name)
		b.WriteString("] ")
		b.WriteString(sqlserverFormatType(dataType, charMaxLen.String, numPrec.String, numScale.String))
		if colDefault.Valid && colDefault.String != "" {
			b.WriteString(" DEFAULT ")
			b.WriteString(colDefault.String)
		}
		if strings.ToUpper(isNullable) == "NO" {
			b.WriteString(" NOT NULL")
		} else {
			b.WriteString(" NULL")
		}
	}
	if err := rows.Err(); err != nil {
		return "", err
	}
	b.WriteString("\n)")
	return b.String(), nil
}

// sqlserverTableColumns returns column names and raw type tokens.
func sqlserverTableColumns(conn *sql.Conn, dbName, tableName string) ([]string, []string, error) {
	rows, err := conn.QueryContext(context.Background(), `
		SELECT COLUMN_NAME, DATA_TYPE
		FROM INFORMATION_SCHEMA.COLUMNS
		WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
		ORDER BY ORDINAL_POSITION`, dbName, tableName)
	if err != nil {
		return nil, nil, err
	}
	defer rows.Close()
	var names, types []string
	for rows.Next() {
		var name, ty string
		if err := rows.Scan(&name, &ty); err != nil {
			return nil, nil, err
		}
		names = append(names, name)
		types = append(types, strings.ToUpper(ty))
	}
	return names, types, rows.Err()
}

// dumpSqlserverValue renders a scanned cell as a T-SQL literal. Unicode text
// uses the N'..' prefix so nvarchar columns keep non-ASCII; varbinary becomes
// a bare 0x.. literal (T-SQL has no _binary keyword).
func dumpSqlserverValue(v any, typeToken string) string {
	if v == nil {
		return "NULL"
	}
	switch val := v.(type) {
	case []byte:
		return "0x" + hexLower(val)
	case string:
		return "N'" + strings.ReplaceAll(val, "'", "''") + "'"
	case bool:
		if val {
			return "1"
		}
		return "0"
	case time.Time:
		return "'" + val.Format("2006-01-02 15:04:05.999999") + "'"
	default:
		return scanToString(v)
	}
}
