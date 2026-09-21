package database

import (
	"context"
	"database/sql"
	"fmt"
	"strings"

	"github.com/go-sql-driver/mysql"
)

type mysqlProvider struct{}

func init() {
	Register("mysql", &mysqlProvider{})
}

func (p *mysqlProvider) DSN(host string, port int, user, password, dbName string, extraParams map[string]string) string {
	if port <= 0 {
		port = 3306
	}
	cfg := mysql.NewConfig()
	cfg.User = user
	cfg.Passwd = password
	cfg.Net = "tcp"
	cfg.Addr = fmt.Sprintf("%s:%d", host, port)
	cfg.DBName = dbName
	cfg.Params = map[string]string{
		"charset":      "utf8mb4",
		"parseTime":    "true",
		"loc":          "Local",
		"timeout":      "10s",
		"readTimeout":  "10s",
		"writeTimeout": "10s",
	}
	for k, v := range extraParams {
		cfg.Params[k] = v
	}
	return cfg.FormatDSN()
}

func (p *mysqlProvider) DriverName() string {
	return "mysql"
}

func (p *mysqlProvider) Quote(name string) string {
	q, _ := SafeMyIdent(name)
	return q
}

func (p *mysqlProvider) PrepareExec(db execer, dbName string) error {
	if dbName == "" {
		return nil
	}
	q, err := SafeMyIdent(dbName)
	if err != nil {
		return err
	}
	_, err = db.ExecContext(context.Background(), "USE "+q)
	return err
}

func (p *mysqlProvider) DefaultTableQuery(dbName, tableName string, limit, offset int) string {
	if offset > 0 {
		return fmt.Sprintf("SELECT * FROM %s LIMIT %d OFFSET %d", p.Quote(tableName), limit, offset)
	}
	return fmt.Sprintf("SELECT * FROM %s LIMIT %d", p.Quote(tableName), limit)
}

func (p *mysqlProvider) PagedTableQuery(dbName, tableName string, limit, offset int) string {
	return fmt.Sprintf("SELECT * FROM %s LIMIT %d OFFSET %d", p.Quote(tableName), limit, offset)
}

func (p *mysqlProvider) InsertRow(db *sql.DB, dbName, tableName string, values map[string]any) error {
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

func (p *mysqlProvider) UpdateRow(db *sql.DB, dbName, tableName string, set, where map[string]any) error {
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

func (p *mysqlProvider) DeleteRow(db *sql.DB, dbName, tableName string, where map[string]any) error {
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

func (p *mysqlProvider) GetCapabilities() DBCapabilities {
	return DBCapabilities{
		"columnTypes": mysqlTypes,
		"intTypes":    mysqlIntTypes,
	}
}

// ── Schema discovery ──

func (p *mysqlProvider) GetDatabases(db *sql.DB) ([]string, error) {
	results, err := queryStrings(db, "SHOW DATABASES")
	if err != nil {
		return nil, err
	}
	names := make([]string, 0, len(results))
	for _, row := range results {
		names = append(names, row["Database"])
	}
	return names, nil
}

func (p *mysqlProvider) GetTables(db *sql.DB, dbName string) ([]TableInfo, error) {
	results, err := queryStrings(db,
		`SELECT TABLE_NAME, TABLE_TYPE, IFNULL(TABLE_COMMENT, '') AS TABLE_COMMENT
		 FROM information_schema.TABLES
		 WHERE TABLE_SCHEMA = ?
		 ORDER BY TABLE_NAME`, dbName)
	if err != nil {
		return nil, fmt.Errorf("get tables: %w", err)
	}
	infos := make([]TableInfo, 0, len(results))
	for _, row := range results {
		tp := "table"
		if row["TABLE_TYPE"] == "VIEW" {
			tp = "view"
		}
		infos = append(infos, TableInfo{
			Name:    row["TABLE_NAME"],
			Type:    tp,
			Comment: row["TABLE_COMMENT"],
		})
	}
	return infos, nil
}

func (p *mysqlProvider) GetTableSchema(db *sql.DB, dbName, tableName string) (*SchemaResult, error) {
	qDb, err := SafeMyIdent(dbName)
	if err != nil {
		return nil, err
	}
	qTbl, err := SafeMyIdent(tableName)
	if err != nil {
		return nil, err
	}
	colRows, err := queryStrings(db, "SHOW FULL COLUMNS FROM "+qDb+"."+qTbl)
	if err != nil {
		return nil, fmt.Errorf("get columns: %w", err)
	}

	columns := make([]ColumnInfo, 0, len(colRows))
	for _, row := range colRows {
		nullable := strings.EqualFold(row["Null"], "YES")
		isPrimary := row["Key"] == "PRI"
		extra := strings.ToLower(row["Extra"])
		onUpdate := strings.Contains(extra, "on update")

		defVal := row["Default"]
		defaultType := "none"
		if strings.Contains(extra, "auto_increment") {
			defaultType = "auto"
		} else if defVal == "NULL" || (defVal == "" && nullable) {
			defaultType = "null"
			defVal = "NULL"
		} else if defVal != "" {
			defaultType = "value"
		}

		columns = append(columns, ColumnInfo{
			Name:        row["Field"],
			Type:        row["Type"],
			Nullable:    nullable,
			DefaultVal:  defVal,
			DefaultType: defaultType,
			IsPrimary:   isPrimary,
			Comment:     row["Comment"],
			Collation:   row["Collation"],
			OnUpdate:    onUpdate,
		})
	}

	idxRows, err := queryStrings(db, "SHOW INDEX FROM "+qDb+"."+qTbl)
	if err != nil {
		return nil, fmt.Errorf("get indexes: %w", err)
	}

	idxMap := make(map[string]*IndexInfo)
	var idxOrder []string
	for _, row := range idxRows {
		name := row["Key_name"]
		if _, ok := idxMap[name]; !ok {
			idxMap[name] = &IndexInfo{
				Name:      name,
				Columns:   []string{},
				Unique:    row["Non_unique"] == "0",
				IsPrimary: name == "PRIMARY",
			}
			idxOrder = append(idxOrder, name)
		}
		idxMap[name].Columns = append(idxMap[name].Columns, row["Column_name"])
	}

	indexes := make([]IndexInfo, 0, len(idxOrder))
	for _, name := range idxOrder {
		indexes = append(indexes, *idxMap[name])
	}

	return &SchemaResult{Columns: columns, Indexes: indexes}, nil
}

// ── DDL: Database ──

func (p *mysqlProvider) CreateDatabase(db *sql.DB, dbName string) error {
	q, err := SafeMyIdent(dbName)
	if err != nil {
		return err
	}
	_, err = db.Exec("CREATE DATABASE " + q)
	return err
}

func (p *mysqlProvider) DropDatabase(db *sql.DB, dbName string) error {
	q, err := SafeMyIdent(dbName)
	if err != nil {
		return err
	}
	_, err = db.Exec("DROP DATABASE " + q)
	return err
}

// mysqlUseDB acquires a dedicated connection and issues USE against it.
// All DDL helpers below return this conn so the subsequent DDL runs on the
// same physical connection (the database/sql pool might otherwise hand out
// different connections for USE and DDL, racing the session state).
func (p *mysqlProvider) mysqlUseDB(db *sql.DB, dbName string) (*sql.Conn, error) {
	conn, err := db.Conn(context.Background())
	if err != nil {
		return nil, err
	}
	if dbName != "" {
		q, err := SafeMyIdent(dbName)
		if err != nil {
			conn.Close()
			return nil, err
		}
		if _, err := conn.ExecContext(context.Background(), "USE "+q); err != nil {
			conn.Close()
			return nil, err
		}
	}
	return conn, nil
}

// ── DDL: Table ──

func (p *mysqlProvider) CreateTable(db *sql.DB, dbName, tableName string) error {
	conn, err := p.mysqlUseDB(db, dbName)
	if err != nil {
		return err
	}
	defer conn.Close()
	qTbl, err := SafeMyIdent(tableName)
	if err != nil {
		return err
	}
	_, err = conn.ExecContext(context.Background(), "CREATE TABLE "+qTbl+" (id INT AUTO_INCREMENT PRIMARY KEY)")
	return err
}

func (p *mysqlProvider) DropTable(db *sql.DB, dbName, tableName string) error {
	conn, err := p.mysqlUseDB(db, dbName)
	if err != nil {
		return err
	}
	defer conn.Close()
	qTbl, err := SafeMyIdent(tableName)
	if err != nil {
		return err
	}
	_, err = conn.ExecContext(context.Background(), "DROP TABLE "+qTbl)
	return err
}

func (p *mysqlProvider) DropView(db *sql.DB, dbName, viewName string) error {
	conn, err := p.mysqlUseDB(db, dbName)
	if err != nil {
		return err
	}
	defer conn.Close()
	qView, err := SafeMyIdent(viewName)
	if err != nil {
		return err
	}
	_, err = conn.ExecContext(context.Background(), "DROP VIEW "+qView)
	return err
}

func (p *mysqlProvider) TruncateTable(db *sql.DB, dbName, tableName string) error {
	conn, err := p.mysqlUseDB(db, dbName)
	if err != nil {
		return err
	}
	defer conn.Close()
	qTbl, err := SafeMyIdent(tableName)
	if err != nil {
		return err
	}
	_, err = conn.ExecContext(context.Background(), "TRUNCATE TABLE "+qTbl)
	return err
}

// CopyTable clones structure via CREATE TABLE ... LIKE and bulk-copies rows
// with INSERT ... SELECT, both native server-side statements.
func (p *mysqlProvider) CopyTable(db *sql.DB, dbName, tableName, newTableName string) error {
	conn, err := p.mysqlUseDB(db, dbName)
	if err != nil {
		return err
	}
	defer conn.Close()
	qSrc, err := SafeMyIdent(tableName)
	if err != nil {
		return err
	}
	qDst, err := SafeMyIdent(newTableName)
	if err != nil {
		return err
	}
	if _, err := conn.ExecContext(context.Background(), "CREATE TABLE "+qDst+" LIKE "+qSrc); err != nil {
		return err
	}
	if _, err := conn.ExecContext(context.Background(), "INSERT INTO "+qDst+" SELECT * FROM "+qSrc); err != nil {
		// Keep the empty clone so the user can inspect it; report the copy error.
		return err
	}
	return nil
}

// ── DDL: Column ──

func (p *mysqlProvider) AddColumn(db *sql.DB, dbName, tableName string, col ColumnDef) error {
	conn, err := p.mysqlUseDB(db, dbName)
	if err != nil {
		return err
	}
	defer conn.Close()
	sql := p.buildColumnSQL("ADD COLUMN", tableName, col)
	_, err = conn.ExecContext(context.Background(), sql)
	return err
}

func (p *mysqlProvider) ModifyColumn(db *sql.DB, dbName, tableName string, col ColumnDef) error {
	conn, err := p.mysqlUseDB(db, dbName)
	if err != nil {
		return err
	}
	defer conn.Close()
	sql := p.buildColumnSQL("MODIFY COLUMN", tableName, col)
	_, err = conn.ExecContext(context.Background(), sql)
	return err
}

func (p *mysqlProvider) DropColumn(db *sql.DB, dbName, tableName, colName string) error {
	conn, err := p.mysqlUseDB(db, dbName)
	if err != nil {
		return err
	}
	defer conn.Close()
	_, err = conn.ExecContext(context.Background(), fmt.Sprintf("ALTER TABLE %s DROP COLUMN %s", p.Quote(tableName), p.Quote(colName)))
	return err
}

// ── DDL: Index ──

func (p *mysqlProvider) AddIndex(db *sql.DB, dbName, tableName string, idx IndexDef) error {
	conn, err := p.mysqlUseDB(db, dbName)
	if err != nil {
		return err
	}
	defer conn.Close()

	q := p.Quote
	var sql string
	if idx.IsPrimary {
		cols := make([]string, len(idx.Columns))
		for i, c := range idx.Columns {
			cols[i] = q(c)
		}
		sql = fmt.Sprintf("ALTER TABLE %s ADD PRIMARY KEY (%s)", q(tableName), strings.Join(cols, ", "))
	} else {
		uniqueStr := ""
		if idx.Unique {
			uniqueStr = "UNIQUE "
		}
		cols := make([]string, len(idx.Columns))
		for i, c := range idx.Columns {
			cols[i] = q(c)
		}
		sql = fmt.Sprintf("CREATE %sINDEX %s ON %s (%s)", uniqueStr, q(idx.Name), q(tableName), strings.Join(cols, ", "))
	}
	_, err = conn.ExecContext(context.Background(), sql)
	return err
}

func (p *mysqlProvider) DropIndex(db *sql.DB, dbName, tableName, idxName string, isPrimary bool, autoIncCols []string) error {
	conn, err := p.mysqlUseDB(db, dbName)
	if err != nil {
		return err
	}
	defer conn.Close()
	q := p.Quote
	if isPrimary {
		sql, err := p.buildDropPK(conn, tableName, autoIncCols)
		if err != nil {
			return err
		}
		_, err = conn.ExecContext(context.Background(), sql)
		return err
	}
	_, err = conn.ExecContext(context.Background(), fmt.Sprintf("DROP INDEX %s ON %s", q(idxName), q(tableName)))
	return err
}

// ── SQL builders ──

func (p *mysqlProvider) buildColumnSQL(action, tableName string, col ColumnDef) string {
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
			parts = append(parts, fmt.Sprintf("DEFAULT '%s'", strings.ReplaceAll(col.DefaultVal, "'", "''")))
		} else {
			parts = append(parts, "DEFAULT ''")
		}
	case "auto":
		parts = append(parts, "AUTO_INCREMENT")
	}

	if col.OnUpdate {
		parts = append(parts, "ON UPDATE CURRENT_TIMESTAMP")
	}

	if col.Comment != "" {
		parts = append(parts, fmt.Sprintf("COMMENT '%s'", strings.ReplaceAll(col.Comment, "'", "''")))
	}

	if col.Collation != "" {
		parts = append(parts, "COLLATE "+col.Collation)
	}

	return fmt.Sprintf("ALTER TABLE %s %s %s", q(tableName), action, strings.Join(parts, " "))
}

// buildDropPK handles AUTO_INCREMENT columns that must be modified before dropping PK.
func (p *mysqlProvider) buildDropPK(conn *sql.Conn, tableName string, autoIncCols []string) (string, error) {
	q := p.Quote
	if len(autoIncCols) > 0 {
		rows, err := conn.QueryContext(context.Background(), fmt.Sprintf("SHOW FULL COLUMNS FROM %s", q(tableName)))
		if err != nil {
			return "", fmt.Errorf("get columns for PK drop: %w", err)
		}
		defer rows.Close()

		cols, err := rows.Columns()
		if err != nil {
			return "", fmt.Errorf("get columns for PK drop: %w", err)
		}

		colTypes := make(map[string]string)
		for rows.Next() {
			values := make([]any, len(cols))
			valuePtrs := make([]any, len(cols))
			for i := range values {
				valuePtrs[i] = &values[i]
			}
			if err := rows.Scan(valuePtrs...); err != nil {
				return "", fmt.Errorf("scan columns for PK drop: %w", err)
			}
			row := make(map[string]string, len(cols))
			for i, col := range cols {
				row[col] = scanToString(values[i])
			}
			colTypes[row["Field"]] = row["Type"]
		}
		if err := rows.Err(); err != nil {
			return "", fmt.Errorf("iterate columns for PK drop: %w", err)
		}

		var modParts []string
		for _, c := range autoIncCols {
			ct, ok := colTypes[c]
			if !ok {
				ct = "INT"
			}
			modParts = append(modParts, fmt.Sprintf("MODIFY COLUMN %s %s NOT NULL", q(c), ct))
		}
		return fmt.Sprintf("ALTER TABLE %s %s, DROP PRIMARY KEY", q(tableName), strings.Join(modParts, ", ")), nil
	}
	return fmt.Sprintf("ALTER TABLE %s DROP PRIMARY KEY", q(tableName)), nil
}

var mysqlTypes = []string{
	"TINYINT", "TINYINT(4)",
	"SMALLINT", "SMALLINT(6)",
	"MEDIUMINT", "MEDIUMINT(9)",
	"INT", "INT(11)",
	"INTEGER", "INTEGER(11)",
	"BIGINT", "BIGINT(20)",
	"FLOAT", "FLOAT(10,2)",
	"DOUBLE", "DOUBLE(10,2)",
	"DECIMAL", "DECIMAL(10,2)",
	"CHAR", "CHAR(1)",
	"VARCHAR", "VARCHAR(255)",
	"TINYTEXT", "TEXT", "MEDIUMTEXT", "LONGTEXT",
	"BLOB", "TINYBLOB", "MEDIUMBLOB", "LONGBLOB",
	"DATE", "DATETIME", "TIMESTAMP", "TIME", "YEAR",
	"ENUM", "SET", "JSON", "BOOLEAN", "BOOL",
}

var mysqlIntTypes = []string{
	"INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT", "MEDIUMINT",
}

// binaryColumnTypes are MySQL types whose values should be emitted as hex
// _binary literals rather than quoted strings.
var mysqlBinaryTypes = map[string]bool{
	"BLOB": true, "TINYBLOB": true, "MEDIUMBLOB": true, "LONGBLOB": true,
	"BINARY": true, "VARBINARY": true,
}

func (p *mysqlProvider) DumpTable(db *sql.DB, dbName, tableName string, opts DumpOptions) (string, error) {
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
		createStmt, kind, derr := showCreateStatement(conn, dbName, tableName, quotedTable)
		if derr != nil {
			return "", derr
		}
		b.WriteString("--\n-- Structure for ")
		b.WriteString(tableName)
		b.WriteString("\n--\nDROP " + kind + " IF EXISTS " + quotedTable + ";\n")
		b.WriteString(createStmt)
		b.WriteString(";\n\n")
	}

	if opts.Data {
		cols, colTypes, derr := tableColumns(conn, dbName, tableName, quotedTable)
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
					b.WriteString(dumpMysqlValue(v, colTypes[i]))
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

// tableKind returns "TABLE" or "VIEW" for the given name by querying
// information_schema; defaults to TABLE on error. Scoped to the schema so a
// name shared across databases resolves to the right object.
func tableKind(conn *sql.Conn, dbName, tableName string) string {
	var t string
	err := conn.QueryRowContext(context.Background(),
		"SELECT TABLE_TYPE FROM information_schema.tables WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? LIMIT 1", dbName, tableName).Scan(&t)
	if err == nil && strings.HasPrefix(t, "VIEW") {
		return "VIEW"
	}
	return "TABLE"
}

// showCreateStatement returns the CREATE TABLE/VIEW statement (without trailing ;)
// and the object kind ("TABLE" or "VIEW").
func showCreateStatement(conn *sql.Conn, dbName, tableName, quotedTable string) (string, string, error) {
	kind := tableKind(conn, dbName, tableName)
	row := conn.QueryRowContext(context.Background(), "SHOW CREATE "+kind+" "+quotedTable)
	if kind == "VIEW" {
		var name, createSQL, charset, collation string
		if err := row.Scan(&name, &createSQL, &charset, &collation); err != nil {
			return "", kind, err
		}
		return createSQL, kind, nil
	}
	var name, createSQL string
	if err := row.Scan(&name, &createSQL); err != nil {
		return "", kind, err
	}
	return createSQL, kind, nil
}

// tableColumns returns column names and their uppercased type tokens.
// TABLE_SCHEMA is filtered because information_schema is global — without it,
// a name shared across schemas mixes in foreign columns and the SELECT below
// fails with "Unknown column".
func tableColumns(conn *sql.Conn, dbName, tableName, quotedTable string) ([]string, []string, error) {
	rows, err := conn.QueryContext(context.Background(),
		"SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.columns WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION", dbName, tableName)
	if err != nil {
		return nil, nil, err
	}
	defer rows.Close()
	var names, types []string
	for rows.Next() {
		var n, ty string
		if err := rows.Scan(&n, &ty); err != nil {
			return nil, nil, err
		}
		names = append(names, n)
		types = append(types, strings.ToUpper(ty))
	}
	return names, types, rows.Err()
}

// dumpMysqlValue renders a scanned cell value into a SQL literal. Binary-typed
// columns are emitted as _binary 0x.. literals; everything else goes through
// quoteSQLValue.
func dumpMysqlValue(v any, typeToken string) string {
	if v == nil {
		return "NULL"
	}
	if mysqlBinaryTypes[typeToken] {
		if b, ok := v.([]byte); ok {
			return quoteSQLValue(b)
		}
	}
	return quoteSQLValue(v)
}
