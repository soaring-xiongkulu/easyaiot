package database

import (
	"context"
	"database/sql"
	"fmt"
	"net"
	"net/url"
	"strconv"
	"strings"
	"time"

	_ "github.com/sijms/go-ora/v2"
)

type oracleProvider struct{}

func init() {
	Register("oracle", &oracleProvider{})
}

func (p *oracleProvider) DSN(host string, port int, user, password, dbName string, extraParams map[string]string) string {
	if port <= 0 {
		port = 1521
	}
	u := &url.URL{
		Scheme: "oracle",
		User:   url.UserPassword(user, password),
		Host:   net.JoinHostPort(host, strconv.Itoa(port)),
		Path:   "/" + dbName,
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

func (p *oracleProvider) DriverName() string {
	return "oracle"
}

func (p *oracleProvider) Quote(name string) string {
	return `"` + strings.ReplaceAll(name, `"`, `""`) + `"`
}

func (p *oracleProvider) PrepareExec(db execer, dbName string) error {
	if dbName == "" {
		return nil
	}
	_, err := db.ExecContext(context.Background(), fmt.Sprintf("ALTER SESSION SET CURRENT_SCHEMA = %s", p.Quote(dbName)))
	return err
}

func (p *oracleProvider) DefaultTableQuery(dbName, tableName string, limit, offset int) string {
	return fmt.Sprintf(
		"SELECT * FROM %s OFFSET %d ROWS FETCH NEXT %d ROWS ONLY",
		p.Quote(tableName), offset, limit,
	)
}

func (p *oracleProvider) PagedTableQuery(dbName, tableName string, limit, offset int) string {
	last := offset + limit
	return fmt.Sprintf("SELECT * FROM (SELECT t.*, ROWNUM rn FROM %s t WHERE ROWNUM <= %d) WHERE rn > %d", p.Quote(tableName), last, offset)
}

func (p *oracleProvider) InsertRow(db *sql.DB, dbName, tableName string, values map[string]any) error {
	cols := sortedKeys(values)
	quotedCols := make([]string, len(cols))
	placeholders := make([]string, len(cols))
	args := make([]any, 0, len(cols))
	for i, c := range cols {
		quotedCols[i] = p.Quote(c)
		placeholders[i] = fmt.Sprintf(":%d", i+1)
		args = append(args, values[c])
	}
	sql := fmt.Sprintf("INSERT INTO %s (%s) VALUES (%s)",
		p.Quote(tableName), strings.Join(quotedCols, ", "), strings.Join(placeholders, ", "))
	return execPrepared(p, db, dbName, sql, args)
}

func (p *oracleProvider) UpdateRow(db *sql.DB, dbName, tableName string, set, where map[string]any) error {
	args := make([]any, 0, len(set)+len(where))
	phIdx := 1

	setParts := make([]string, 0, len(set))
	for _, c := range sortedKeys(set) {
		if set[c] == nil {
			setParts = append(setParts, fmt.Sprintf("%s = NULL", p.Quote(c)))
		} else {
			setParts = append(setParts, fmt.Sprintf("%s = :%d", p.Quote(c), phIdx))
			args = append(args, set[c])
			phIdx++
		}
	}

	whereParts := make([]string, 0, len(where))
	for _, c := range sortedKeys(where) {
		if where[c] == nil {
			whereParts = append(whereParts, fmt.Sprintf("%s IS NULL", p.Quote(c)))
		} else {
			whereParts = append(whereParts, fmt.Sprintf("%s = :%d", p.Quote(c), phIdx))
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

func (p *oracleProvider) DeleteRow(db *sql.DB, dbName, tableName string, where map[string]any) error {
	args := make([]any, 0, len(where))
	phIdx := 1
	whereParts := make([]string, 0, len(where))
	for _, c := range sortedKeys(where) {
		if where[c] == nil {
			whereParts = append(whereParts, fmt.Sprintf("%s IS NULL", p.Quote(c)))
		} else {
			whereParts = append(whereParts, fmt.Sprintf("%s = :%d", p.Quote(c), phIdx))
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

func (p *oracleProvider) GetCapabilities() DBCapabilities {
	return DBCapabilities{
		"supportsAutoIncrement":      false,
		"supportsOnUpdate":           false,
		"supportsCollation":          false,
		"supportsCreateDatabase":     false,
		"autoIncrementForcesNotNull": false,
		"columnTypes":                oracleTypes,
		"intTypes":                   oracleIntTypes,
	}
}

// ── Schema discovery ──

func (p *oracleProvider) GetDatabases(db *sql.DB) ([]string, error) {
	results, err := queryStrings(db, "SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') AS CURRENT_SCHEMA FROM DUAL")
	if err != nil {
		return nil, err
	}
	if len(results) == 0 || results[0]["CURRENT_SCHEMA"] == "" {
		return []string{}, nil
	}
	return []string{results[0]["CURRENT_SCHEMA"]}, nil
}

func (p *oracleProvider) GetTables(db *sql.DB, dbName string) ([]TableInfo, error) {
	owner, err := p.resolveSchema(db, dbName)
	if err != nil {
		return nil, err
	}
	results, err := queryStrings(db, `
		SELECT o.object_name, o.object_type, NVL(c.comments, '') AS comments
		FROM all_objects o
		LEFT JOIN all_tab_comments c
		  ON c.owner = o.owner AND c.table_name = o.object_name
		WHERE o.owner = :1
		  AND o.object_type IN ('TABLE', 'VIEW')
		  AND o.object_name NOT LIKE 'BIN$%'
		ORDER BY o.object_name`, strings.ToUpper(owner))
	if err != nil {
		return nil, fmt.Errorf("get tables: %w", err)
	}
	infos := make([]TableInfo, 0, len(results))
	for _, row := range results {
		tp := "table"
		if row["OBJECT_TYPE"] == "VIEW" {
			tp = "view"
		}
		infos = append(infos, TableInfo{
			Name:    row["OBJECT_NAME"],
			Type:    tp,
			Comment: row["COMMENTS"],
		})
	}
	return infos, nil
}

func (p *oracleProvider) GetTableSchema(db *sql.DB, dbName, tableName string) (*SchemaResult, error) {
	owner, err := p.resolveSchema(db, dbName)
	if err != nil {
		return nil, err
	}
	owner = strings.ToUpper(owner)
	table := p.dictionaryTableName(tableName)

	colRows, err := queryStrings(db, `
		SELECT c.column_name, c.data_type, c.data_length, c.data_precision, c.data_scale, c.nullable, c.data_default,
		       NVL(cc.comments, '') AS comments
		FROM all_tab_columns c
		LEFT JOIN all_col_comments cc
		  ON cc.owner = c.owner AND cc.table_name = c.table_name AND cc.column_name = c.column_name
		WHERE c.owner = :1 AND c.table_name = :2
		ORDER BY c.column_id`, owner, table)
	if err != nil {
		return nil, fmt.Errorf("get columns: %w", err)
	}

	pkCols, err := p.primaryColumns(db, owner, table)
	if err != nil {
		return nil, fmt.Errorf("get primary keys: %w", err)
	}

	columns := make([]ColumnInfo, 0, len(colRows))
	for _, row := range colRows {
		nullable := row["NULLABLE"] == "Y"
		defVal := strings.TrimSpace(row["DATA_DEFAULT"])
		defaultType := "none"
		if defVal == "" && nullable {
			defaultType = "null"
			defVal = "NULL"
		} else if strings.EqualFold(defVal, "NULL") {
			defaultType = "null"
		} else if defVal != "" {
			defaultType = "value"
		}
		columns = append(columns, ColumnInfo{
			Name:        row["COLUMN_NAME"],
			Type:        oracleColumnType(row),
			Nullable:    nullable,
			DefaultVal:  defVal,
			DefaultType: defaultType,
			IsPrimary:   pkCols[row["COLUMN_NAME"]],
			Comment:     row["COMMENTS"],
		})
	}

	indexes, err := p.indexes(db, owner, table)
	if err != nil {
		return nil, fmt.Errorf("get indexes: %w", err)
	}

	return &SchemaResult{Columns: columns, Indexes: indexes}, nil
}

// ── DDL: Database ──

func (p *oracleProvider) CreateDatabase(db *sql.DB, dbName string) error {
	return fmt.Errorf("oracle provider does not support CREATE DATABASE; create users or schemas outside Terminal")
}

func (p *oracleProvider) DropDatabase(db *sql.DB, dbName string) error {
	return fmt.Errorf("oracle provider does not support DROP DATABASE; drop users or schemas outside Terminal")
}

// ── DDL: Table ──

func (p *oracleProvider) CreateTable(db *sql.DB, dbName, tableName string) error {
	_, err := db.Exec(p.createTableSQL(dbName, tableName))
	return err
}

func (p *oracleProvider) DropTable(db *sql.DB, dbName, tableName string) error {
	_, err := db.Exec(fmt.Sprintf("DROP TABLE %s", p.qualifiedTable(dbName, tableName)))
	return err
}

func (p *oracleProvider) DropView(db *sql.DB, dbName, viewName string) error {
	_, err := db.Exec(fmt.Sprintf("DROP VIEW %s", p.qualifiedTable(dbName, viewName)))
	return err
}

func (p *oracleProvider) TruncateTable(db *sql.DB, dbName, tableName string) error {
	_, err := db.Exec(fmt.Sprintf("TRUNCATE TABLE %s", p.qualifiedTable(dbName, tableName)))
	return err
}

// CopyTable clones structure and data via CREATE TABLE AS SELECT (no
// constraints/indexes, like the other providers' quick copies).
func (p *oracleProvider) CopyTable(db *sql.DB, dbName, tableName, newTableName string) error {
	owner, err := p.resolveSchema(db, dbName)
	if err != nil {
		return err
	}
	_, err = db.Exec(fmt.Sprintf("CREATE TABLE %s AS SELECT * FROM %s", p.Quote(newTableName), p.qualifiedTable(owner, tableName)))
	return err
}

// ── DDL: Column ──

func (p *oracleProvider) AddColumn(db *sql.DB, dbName, tableName string, col ColumnDef) error {
	if _, err := db.Exec(p.buildColumnSQL("ADD", p.qualifiedTable(dbName, tableName), col)); err != nil {
		return err
	}
	if col.Comment != "" {
		_, err := db.Exec(p.commentOnColumnSQL(dbName, tableName, col.Name, col.Comment))
		return err
	}
	return nil
}

func (p *oracleProvider) ModifyColumn(db *sql.DB, dbName, tableName string, col ColumnDef) error {
	table := p.qualifiedTable(dbName, tableName)
	stmts := []string{p.buildColumnSQL("MODIFY", table, col)}
	if col.Comment != "" {
		stmts = append(stmts, p.commentOnColumnSQL(dbName, tableName, col.Name, col.Comment))
	}
	for _, stmt := range stmts {
		if _, err := db.Exec(stmt); err != nil {
			return err
		}
	}
	return nil
}

func (p *oracleProvider) DropColumn(db *sql.DB, dbName, tableName, colName string) error {
	_, err := db.Exec(fmt.Sprintf("ALTER TABLE %s DROP COLUMN %s", p.qualifiedTable(dbName, tableName), p.Quote(colName)))
	return err
}

// ── DDL: Index ──

func (p *oracleProvider) AddIndex(db *sql.DB, dbName, tableName string, idx IndexDef) error {
	cols := make([]string, len(idx.Columns))
	for i, c := range idx.Columns {
		cols[i] = p.Quote(c)
	}
	if idx.IsPrimary {
		_, err := db.Exec(fmt.Sprintf("ALTER TABLE %s ADD PRIMARY KEY (%s)", p.qualifiedTable(dbName, tableName), strings.Join(cols, ", ")))
		return err
	}
	uniqueStr := ""
	if idx.Unique {
		uniqueStr = "UNIQUE "
	}
	_, err := db.Exec(fmt.Sprintf("CREATE %sINDEX %s ON %s (%s)", uniqueStr, p.Quote(idx.Name), p.qualifiedTable(dbName, tableName), strings.Join(cols, ", ")))
	return err
}

func (p *oracleProvider) DropIndex(db *sql.DB, dbName, tableName, idxName string, isPrimary bool, autoIncCols []string) error {
	if isPrimary {
		_, err := db.Exec(fmt.Sprintf("ALTER TABLE %s DROP PRIMARY KEY", p.qualifiedTable(dbName, tableName)))
		return err
	}
	_, err := db.Exec(fmt.Sprintf("DROP INDEX %s", p.qualifiedIndex(dbName, idxName)))
	return err
}

// ── SQL builders ──

func (p *oracleProvider) buildColumnSQL(action, tableName string, col ColumnDef) string {
	if !strings.Contains(tableName, `"`) {
		tableName = p.Quote(tableName)
	}
	var parts []string
	parts = append(parts, p.Quote(col.Name), col.Type)

	if col.Nullable {
		parts = append(parts, "NULL")
	} else {
		parts = append(parts, "NOT NULL")
	}

	switch col.DefaultType {
	case "null":
		parts = append(parts, "DEFAULT NULL")
	case "value":
		parts = append(parts, "DEFAULT "+oracleDefaultValue(col.DefaultVal))
	}

	return fmt.Sprintf("ALTER TABLE %s %s %s", tableName, action, strings.Join(parts, " "))
}

func (p *oracleProvider) createTableSQL(dbName, tableName string) string {
	return fmt.Sprintf("CREATE TABLE %s (%s NUMBER PRIMARY KEY)", p.qualifiedTable(dbName, tableName), p.Quote("ID"))
}

func (p *oracleProvider) dictionaryTableName(tableName string) string {
	return tableName
}

func (p *oracleProvider) commentOnColumnSQL(dbName, tableName, colName, comment string) string {
	return fmt.Sprintf("COMMENT ON COLUMN %s.%s IS '%s'",
		p.qualifiedTable(dbName, tableName), p.Quote(colName), strings.ReplaceAll(comment, "'", "''"))
}

func (p *oracleProvider) qualifiedTable(dbName, tableName string) string {
	if dbName == "" {
		return p.Quote(tableName)
	}
	return p.Quote(dbName) + "." + p.Quote(tableName)
}

func (p *oracleProvider) qualifiedIndex(dbName, indexName string) string {
	if dbName == "" {
		return p.Quote(indexName)
	}
	return p.Quote(dbName) + "." + p.Quote(indexName)
}

func (p *oracleProvider) resolveSchema(db *sql.DB, dbName string) (string, error) {
	if dbName != "" {
		return dbName, nil
	}
	dbs, err := p.GetDatabases(db)
	if err != nil {
		return "", err
	}
	if len(dbs) == 0 {
		return "", nil
	}
	return dbs[0], nil
}

func (p *oracleProvider) primaryColumns(db *sql.DB, owner, tableName string) (map[string]bool, error) {
	rows, err := queryStrings(db, `
		SELECT cols.column_name
		FROM all_constraints cons
		JOIN all_cons_columns cols
		  ON cols.owner = cons.owner
		 AND cols.constraint_name = cons.constraint_name
		 AND cols.table_name = cons.table_name
		WHERE cons.owner = :1
		  AND cons.table_name = :2
		  AND cons.constraint_type = 'P'`, owner, tableName)
	if err != nil {
		return nil, err
	}
	cols := make(map[string]bool, len(rows))
	for _, row := range rows {
		cols[row["COLUMN_NAME"]] = true
	}
	return cols, nil
}

func (p *oracleProvider) indexes(db *sql.DB, owner, tableName string) ([]IndexInfo, error) {
	rows, err := queryStrings(db, `
		SELECT NVL(cons.constraint_name, idx.index_name) AS index_name,
		       idx.uniqueness,
		       col.column_name,
		       CASE WHEN cons.constraint_type = 'P' THEN 'Y' ELSE 'N' END AS is_primary
		FROM all_indexes idx
		JOIN all_ind_columns col
		  ON col.index_owner = idx.owner
		 AND col.index_name = idx.index_name
		 AND col.table_owner = idx.table_owner
		 AND col.table_name = idx.table_name
		LEFT JOIN all_constraints cons
		  ON cons.owner = idx.table_owner
		 AND cons.table_name = idx.table_name
		 AND cons.index_owner = idx.owner
		 AND cons.index_name = idx.index_name
		 AND cons.constraint_type = 'P'
		WHERE idx.table_owner = :1
		  AND idx.table_name = :2
		ORDER BY index_name, col.column_position`, owner, tableName)
	if err != nil {
		return nil, err
	}

	idxMap := make(map[string]*IndexInfo)
	var idxOrder []string
	for _, row := range rows {
		name := row["INDEX_NAME"]
		if _, ok := idxMap[name]; !ok {
			idxMap[name] = &IndexInfo{
				Name:      name,
				Columns:   []string{},
				Unique:    row["UNIQUENESS"] == "UNIQUE",
				IsPrimary: row["IS_PRIMARY"] == "Y",
			}
			idxOrder = append(idxOrder, name)
		}
		idxMap[name].Columns = append(idxMap[name].Columns, row["COLUMN_NAME"])
	}

	indexes := make([]IndexInfo, 0, len(idxOrder))
	for _, name := range idxOrder {
		indexes = append(indexes, *idxMap[name])
	}
	return indexes, nil
}

func oracleDefaultValue(defaultVal string) string {
	if defaultVal == "" {
		return "''"
	}
	upper := strings.ToUpper(strings.TrimSpace(defaultVal))
	if upper == "NULL" || strings.HasPrefix(upper, "TO_") || strings.Contains(upper, "(") || upper == "SYSDATE" || upper == "SYSTIMESTAMP" {
		return defaultVal
	}
	return "'" + strings.ReplaceAll(defaultVal, "'", "''") + "'"
}

func oracleColumnType(row map[string]string) string {
	dataType := row["DATA_TYPE"]
	switch dataType {
	case "CHAR", "VARCHAR2", "NCHAR", "NVARCHAR2", "RAW":
		if row["DATA_LENGTH"] != "" {
			return fmt.Sprintf("%s(%s)", dataType, row["DATA_LENGTH"])
		}
	case "NUMBER":
		precision := row["DATA_PRECISION"]
		scale := row["DATA_SCALE"]
		if precision != "" {
			if scale != "" && scale != "0" {
				return fmt.Sprintf("NUMBER(%s,%s)", precision, scale)
			}
			return fmt.Sprintf("NUMBER(%s)", precision)
		}
	}
	return dataType
}

var oracleTypes = []string{
	"NUMBER", "NUMBER(10)", "NUMBER(10,2)",
	"FLOAT", "BINARY_FLOAT", "BINARY_DOUBLE",
	"CHAR(1)", "VARCHAR2(255)", "NCHAR(1)", "NVARCHAR2(255)",
	"CLOB", "NCLOB", "BLOB", "RAW(16)",
	"DATE", "TIMESTAMP", "TIMESTAMP WITH TIME ZONE", "TIMESTAMP WITH LOCAL TIME ZONE",
}

var oracleIntTypes = []string{
	"NUMBER",
}

func (p *oracleProvider) DumpTable(db *sql.DB, dbName, tableName string, opts DumpOptions) (string, error) {
	ctx := context.Background()
	conn, err := db.Conn(ctx)
	if err != nil {
		return "", err
	}
	defer conn.Close()

	if err := p.PrepareExec(conn, dbName); err != nil {
		return "", err
	}
	// DBMS_METADATA.GET_DDL returns a CLOB; raise LONG so the full text is
	// returned in the SELECT rather than truncated.
	_, _ = conn.ExecContext(ctx, "ALTER SESSION SET LONG = 100000000")

	owner, err := p.resolveSchema(db, dbName)
	if err != nil {
		return "", err
	}

	var b strings.Builder
	quotedTable := p.Quote(tableName)

	if opts.Structure {
		kind := oracleTableKind(conn, owner, tableName)
		var createSQL string
		err := conn.QueryRowContext(ctx,
			"SELECT DBMS_METADATA.GET_DDL(?, ?, ?) FROM DUAL",
			strings.ToUpper(kind), strings.ToUpper(tableName), strings.ToUpper(owner)).Scan(&createSQL)
		if err != nil {
			return "", err
		}
		b.WriteString("--\n-- Structure for ")
		b.WriteString(tableName)
		b.WriteString("\n--\nDROP " + kind + " IF EXISTS " + quotedTable + ";\n")
		b.WriteString(createSQL)
		b.WriteString(";\n\n")
	}

	if opts.Data {
		cols, colTypes, derr := oracleTableColumns(conn, owner, tableName)
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
					b.WriteString(dumpOracleValue(v, colTypes[i]))
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

// oracleTableKind returns "TABLE" or "VIEW" by querying all_objects.
func oracleTableKind(conn *sql.Conn, owner, tableName string) string {
	var t string
	err := conn.QueryRowContext(context.Background(),
		"SELECT object_type FROM all_objects WHERE owner = ? AND object_name = ? AND object_type IN ('TABLE','VIEW')",
		strings.ToUpper(owner), strings.ToUpper(tableName)).Scan(&t)
	if err == nil && t == "VIEW" {
		return "VIEW"
	}
	return "TABLE"
}

// oracleTableColumns returns column names and types for a table.
func oracleTableColumns(conn *sql.Conn, owner, tableName string) ([]string, []string, error) {
	rows, err := conn.QueryContext(context.Background(),
		`SELECT column_name, data_type || DECODE(data_length, 0, '', '(' || data_length || ')')
		 FROM all_tab_columns WHERE owner = ? AND table_name = ? ORDER BY column_id`,
		strings.ToUpper(owner), strings.ToUpper(tableName))
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
		types = append(types, ty)
	}
	return names, types, rows.Err()
}

// dumpOracleValue renders a scanned cell as an Oracle literal. BLOBs become
// HEXTORAW('..'); timestamps use TIMESTAMP '..' for reliability against NLS.
func dumpOracleValue(v any, typeToken string) string {
	if v == nil {
		return "NULL"
	}
	switch val := v.(type) {
	case []byte:
		return "HEXTORAW('" + hexLower(val) + "')"
	case string:
		return quotedString(val)
	case bool:
		if val {
			return "1"
		}
		return "0"
	case time.Time:
		return "TIMESTAMP '" + val.Format("2006-01-02 15:04:05.999999") + "'"
	default:
		return scanToString(v)
	}
}
