package store

import (
	"io"
	"os"
	"regexp"
	"strings"
	"time"
)

// Shared markdown-store helpers used by commands_store.go (formerly shared
// with skills_store.go): name validation, minimal frontmatter parsing,
// size-capped file reads and RFC3339 timestamps.

const maxStoreFileLen = 256 * 1024 // 单个文本文件读取上限

var skillNameRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]*$`)

type skillFrontmatter struct {
	name         string
	description  string
	argumentHint string
	disableInv   bool
	createdModel string
}

// parseFrontmatter 从 md 全文里抽出 YAML frontmatter 的几个平铺字段与正文。
// 只支持 `key: value` 平铺写法（社区 SKILL.md 的 name/description 均如此），不做完整 YAML。
func parseFrontmatter(content string) (fm skillFrontmatter, body string) {
	body = content
	trimmed := strings.TrimLeft(content, " \t\r\n")
	if !strings.HasPrefix(trimmed, "---") {
		return fm, body
	}
	rest := strings.TrimPrefix(trimmed, "---")
	rest = strings.TrimLeft(rest, "\r\n")
	end := strings.Index(rest, "\n---")
	if end < 0 {
		return fm, body
	}
	block := rest[:end]
	body = strings.TrimLeft(rest[end+len("\n---"):], "\r\n")

	var curKey string
	for _, raw := range strings.Split(block, "\n") {
		line := strings.TrimRight(raw, "\r")
		if strings.TrimSpace(line) == "" {
			continue
		}
		// 折叠标量续行（description 常用 > 或 | 多行）：非 key: 行且有缩进则拼到上一个 key
		if (strings.HasPrefix(line, "  ") || strings.HasPrefix(line, "\t")) && curKey != "" {
			seg := strings.TrimSpace(line)
			if curKey == "description" {
				if fm.description != "" {
					fm.description += " "
				}
				fm.description += seg
			}
			continue
		}
		idx := strings.Index(line, ":")
		if idx < 0 {
			continue
		}
		key := strings.TrimSpace(line[:idx])
		val := strings.TrimSpace(line[idx+1:])
		val = strings.Trim(val, `"'`)
		curKey = key
		switch key {
		case "name":
			fm.name = val
		case "description":
			// 值可能是 > / | 折叠标记，续行在后续缩进行拼接
			if val != ">" && val != "|" && val != ">-" && val != "|-" {
				fm.description = val
			}
		case "argument-hint":
			fm.argumentHint = val
		case "disable-model-invocation":
			fm.disableInv = val == "true"
		case "created-model", "createdModel":
			fm.createdModel = val
		}
	}
	return fm, body
}

func readCapped(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()
	limited := io.LimitReader(f, maxStoreFileLen)
	b, err := io.ReadAll(limited)
	if err != nil {
		return "", err
	}
	return string(b), nil
}

func nowRFC3339() string { return time.Now().UTC().Format(time.RFC3339) }
