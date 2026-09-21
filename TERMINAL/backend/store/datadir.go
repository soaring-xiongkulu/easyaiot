package store

// DataDir is the result of resolving the config data directory at startup.
type DataDir struct {
	Path     string
	Type     string
	FirstRun bool
	Upgrade  bool
}
