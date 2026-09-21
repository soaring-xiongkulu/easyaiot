package database


// ── Shared types ──

type TableInfo struct {
	Name    string `json:"name"`
	Type    string `json:"type"` // "table" or "view"
	Comment string `json:"comment"`
}

type ColumnInfo struct {
	Name        string `json:"name"`
	Type        string `json:"type"`
	Nullable    bool   `json:"nullable"`
	DefaultVal  string `json:"defaultVal"`
	DefaultType string `json:"defaultType"` // "none" | "null" | "value" | "auto"
	IsPrimary   bool   `json:"isPrimary"`
	Comment     string `json:"comment"`
	Collation   string `json:"collation"`
	OnUpdate    bool   `json:"onUpdate"`
}

type IndexInfo struct {
	Name      string   `json:"name"`
	Columns   []string `json:"columns"`
	Unique    bool     `json:"unique"`
	IsPrimary bool     `json:"isPrimary"`
}

type SchemaResult struct {
	Columns []ColumnInfo `json:"columns"`
	Indexes []IndexInfo  `json:"indexes"`
}

// ColumnDef is the structured input for adding or modifying a column.
type ColumnDef struct {
	Name        string `json:"name"`
	Type        string `json:"type"`
	Nullable    bool   `json:"nullable"`
	DefaultVal  string `json:"defaultVal"`
	DefaultType string `json:"defaultType"` // "none" | "null" | "value" | "auto"
	Comment     string `json:"comment"`
	Collation   string `json:"collation"`
	OnUpdate    bool   `json:"onUpdate"`
}

// IndexDef is the structured input for creating an index.
type IndexDef struct {
	Name      string   `json:"name"`
	Columns   []string `json:"columns"`
	Unique    bool     `json:"unique"`
	IsPrimary bool     `json:"isPrimary"`
}

// DBCapabilities describes the features supported by a database type.
// Providers return only the fields they override; unset fields use defaults.
type DBCapabilities map[string]any

// Default capability values, using MySQL as the baseline.
// Providers only need to return fields that differ from MySQL.
var defaultDBCapabilities = DBCapabilities{
	"supportsAutoIncrement":      true,
	"supportsOnUpdate":           true,
	"supportsCollation":          true,
	"supportsComment":            true,
	"supportsModifyColumn":       true,
	"supportsPrimaryKey":         true,
	"supportsCreateDatabase":     true,
	"autoIncrementForcesNotNull": true,
	"columnTypes":                []string{},
	"intTypes":                   []string{},
}

// MergeCapabilities merges provider overrides into the default config.
func MergeCapabilities(overrides DBCapabilities) DBCapabilities {
	merged := make(DBCapabilities, len(defaultDBCapabilities)+len(overrides))
	for k, v := range defaultDBCapabilities {
		merged[k] = v
	}
	for k, v := range overrides {
		merged[k] = v
	}
	return merged
}
