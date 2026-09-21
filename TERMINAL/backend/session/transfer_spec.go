package session

// TransferSpec describes one transfer request for (re)starting a task. It is
// the App-boundary shape for retry: the frontend holds the checkpoint
// (which files finished) and passes the original request back.
type TransferSpec struct {
	Type       string `json:"type"`       // "upload" | "download"
	LocalPath  string `json:"localPath"`
	RemotePath string `json:"remotePath"`
	Recursive  bool   `json:"recursive"`
}
