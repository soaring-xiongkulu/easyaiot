package session

import "encoding/json"

// K8s exec WebSocket channel numbers (v4.channel.k8s.io).
const (
	execChStdin  byte = 0
	execChStdout byte = 1
	execChStderr byte = 2
	execChResize byte = 3
	execChError  byte = 4
)

func encodeStdin(data []byte) []byte {
	out := make([]byte, 0, len(data)+1)
	out = append(out, execChStdin)
	out = append(out, data...)
	return out
}

func encodeResize(cols, rows int) ([]byte, error) {
	b, err := json.Marshal(struct {
		Width  int `json:"Width"`
		Height int `json:"Height"`
	}{Width: cols, Height: rows})
	if err != nil {
		return nil, err
	}
	out := make([]byte, 0, len(b)+1)
	out = append(out, execChResize)
	out = append(out, b...)
	return out, nil
}

func decodeFrame(msg []byte) (byte, []byte, bool) {
	if len(msg) == 0 {
		return 0, nil, false
	}
	return msg[0], msg[1:], true
}
