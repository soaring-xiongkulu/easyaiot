package store

import (
	"archive/zip"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"
)

// skillsListCacheTTL bounds how long a merged List result is reused before
// the next call forces a re-scan. Combined with explicit invalidation on
// every mutator, this coalesces the rapid re-reads triggered by per-token
// AI / terminal code while still being correct on disk mutation.
const skillsListCacheTTL = 2 * time.Second

// skills 采用「目录式」存储：每个 skill 是 skills/<dir>/SKILL.md（可带 references/、scripts/）。
// 内容与存在性以目录为真相源；enabled/sortOrder/locked/origin 等用户偏好存 prefs.json。
const (
	skillsDirName   = "skills"
	skillPrefsFile  = "skills.json"
	skillEntryFile  = "SKILL.md"
	systemDirName   = ".system"
	referencesDir   = "references"
	scriptsDir      = "scripts"
	maxSkillFileLen = 256 * 1024 // 单个 skill 文本文件读取上限
)

var skillNameRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]*$`)

// SkillMeta 是一个 skill 暴露给前端的完整视图（目录扫描 + 偏好合并后的结果）。
type SkillMeta struct {
	Name           string `json:"name"`           // = frontmatter.name，唯一键（源:目录）
	Description    string `json:"description"`    // L1 索引内容（源:目录）
	IsSystem       bool   `json:"isSystem"`       // 是否在 .system/（源:目录）
	Origin         string `json:"origin"`         // created | imported，仅展示/筛选（源:prefs）
	Locked         bool   `json:"locked"`         // 锁定态（源:prefs）
	Enabled        bool   `json:"enabled"`        // 是否进 L1/补全/识别（源:prefs）
	SortOrder      int    `json:"sortOrder"`      // 列表排序（源:prefs）
	Dir            string `json:"dir"`            // 存储目录名，可 ≠ name（源:目录）
	Path           string `json:"path"`           // skill 目录的绝对路径（源:目录）
	HasReferences  bool   `json:"hasReferences"`  // 是否文件夹型（有 references/）（源:目录）
	ScriptCount    int    `json:"scriptCount"`    // scripts/ 文件数（源:目录）
	ModelInvocable bool   `json:"modelInvocable"` // = !disable-model-invocation（源:目录）
	CreatedModel   string `json:"createdModel"`   // 写作时面向的模型（源:目录 frontmatter，可空）
	CreatedAt      string `json:"createdAt"`      // RFC3339（源:prefs）
	Version        int    `json:"version"`        // 版本号（源:prefs）
}

// skillPref 是 prefs.json 里每个 skill 的用户偏好条目（按 name 关联）。
type skillPref struct {
	Name      string `json:"name"`
	Origin    string `json:"origin"`
	Locked    bool   `json:"locked"`
	Enabled   bool   `json:"enabled"`
	SortOrder int    `json:"sortOrder"`
	CreatedAt string `json:"createdAt"`
	Version   int    `json:"version"`
}

type skillPrefsData struct {
	Version int         `json:"version"`
	Prefs   []skillPref `json:"prefs"`
}

// SkillsStore 管理 skills 目录扫描与偏好持久化。configDir 由 app.go 传入（~/.../Terminal）。
type SkillsStore struct {
	configDir string

	// listCache holds the merged result of the most recent List call. F-107:
	// re-scanning the whole skills tree (every SKILL.md + references/ +
	// scripts/ probe) per call is wasteful when the frontend polls.
	listMu      sync.Mutex
	listCache   []SkillMeta
	listCachedAt time.Time
}

func NewSkillsStore(configDir string) *SkillsStore {
	return &SkillsStore{configDir: configDir}
}

// invalidateListCache clears the cached List result. Mutators call this
// before returning so the next List re-scans.
func (s *SkillsStore) invalidateListCache() {
	s.listMu.Lock()
	s.listCache = nil
	s.listCachedAt = time.Time{}
	s.listMu.Unlock()
}

func (s *SkillsStore) skillsRoot() string { return filepath.Join(s.configDir, skillsDirName) }
func (s *SkillsStore) prefsPath() string  { return filepath.Join(s.skillsRoot(), skillPrefsFile) }

// ---- frontmatter 解析（极简，只取平铺的 name/description/disable-model-invocation/created-model）----

type skillFrontmatter struct {
	name         string
	description  string
	argumentHint string
	disableInv   bool
	createdModel string
}

// parseFrontmatter 从 SKILL.md 全文里抽出 YAML frontmatter 的几个平铺字段与正文。
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

// ---- 偏好读写（prefs.json，源于用户偏好）----

func (s *SkillsStore) loadPrefs() (skillPrefsData, error) {
	bytes, err := os.ReadFile(s.prefsPath())
	if err != nil {
		if os.IsNotExist(err) {
			return skillPrefsData{Version: 1, Prefs: []skillPref{}}, nil
		}
		return skillPrefsData{}, err
	}
	var data skillPrefsData
	if err := json.Unmarshal(bytes, &data); err != nil {
		return skillPrefsData{}, err
	}
	if data.Version == 0 {
		data.Version = 1
	}
	return data, nil
}

func (s *SkillsStore) savePrefs(data skillPrefsData) error {
	if err := os.MkdirAll(s.skillsRoot(), 0755); err != nil {
		return err
	}
	bytes, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	// Atomic write (tmp + rename): concurrent List callers all scan the
	// same dir and converge on identical prefs, so racing saves are safe
	// — readers must not see a half-written file though.
	return atomicWriteFile(s.prefsPath(), bytes, 0600)
}

// ---- 目录扫描（B1，内容/存在性以目录为真相源）----

// scanDir 扫描一个根目录下的 skill 子目录，isSystem 标记它们是否来自 .system/。
func scanDir(root string, isSystem bool) []SkillMeta {
	out := []SkillMeta{}
	entries, err := os.ReadDir(root)
	if err != nil {
		return out
	}
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		dir := e.Name()
		if strings.HasPrefix(dir, ".") {
			continue // 跳过 .system 等隐藏目录（.system 单独扫）
		}
		skillDir := filepath.Join(root, dir)
		mdPath := filepath.Join(skillDir, skillEntryFile)
		content, err := readCapped(mdPath)
		if err != nil {
			continue // 无 SKILL.md 或读失败 → 跳过，不 panic
		}
		fm, _ := parseFrontmatter(content)
		if fm.name == "" || fm.description == "" {
			continue // 缺必填字段 → 跳过
		}
		if !skillNameRe.MatchString(fm.name) {
			continue
		}
		meta := SkillMeta{
			Name:           fm.name,
			Description:    fm.description,
			IsSystem:       isSystem,
			Dir:            dir,
			Path:           skillDir,
			ModelInvocable: !fm.disableInv,
			CreatedModel:   fm.createdModel,
			HasReferences:  dirHasFiles(filepath.Join(skillDir, referencesDir)),
			ScriptCount:    countFiles(filepath.Join(skillDir, scriptsDir)),
		}
		out = append(out, meta)
	}
	return out
}

// List 返回所有 skill（合并目录扫描与偏好），按 sortOrder、name 排序。
// 走内存缓存：同一进程内 2 秒内的重复 List 跳过目录扫描与 SKILL.md 文件读取。
func (s *SkillsStore) List() ([]SkillMeta, error) {
	s.listMu.Lock()
	if s.listCache != nil && time.Since(s.listCachedAt) < skillsListCacheTTL {
		cached := s.listCache
		s.listMu.Unlock()
		out := make([]SkillMeta, len(cached))
		copy(out, cached)
		return out, nil
	}
	s.listMu.Unlock()

	metas, err := s.scanAndMerge()
	if err != nil {
		return nil, err
	}

	s.listMu.Lock()
	s.listCache = metas
	s.listCachedAt = time.Now()
	s.listMu.Unlock()

	out := make([]SkillMeta, len(metas))
	copy(out, metas)
	return out, nil
}

// scanAndMerge performs the full directory scan + pref merge + orphan prune.
func (s *SkillsStore) scanAndMerge() ([]SkillMeta, error) {
	root := s.skillsRoot()
	metas := scanDir(root, false)
	metas = append(metas, scanDir(filepath.Join(root, systemDirName), true)...)

	prefs, err := s.loadPrefs()
	if err != nil {
		return nil, err
	}
	prefMap := map[string]skillPref{}
	for _, p := range prefs.Prefs {
		prefMap[p.Name] = p
	}

	changed := false
	for i := range metas {
		m := &metas[i]
		p, ok := prefMap[m.Name]
		if !ok {
			// 目录新增但无偏好记录 → 用默认值补齐（enabled=true）
			p = skillPref{
				Name:      m.Name,
				Origin:    "imported",
				Locked:    !m.IsSystem, // 默认锁定，防误改；system 始终视为锁定
				Enabled:   true,
				SortOrder: len(prefMap) + i,
				CreatedAt: nowRFC3339(),
				Version:   1,
			}
			prefMap[m.Name] = p
			prefs.Prefs = append(prefs.Prefs, p)
			changed = true
		}
		m.Origin = p.Origin
		m.Locked = p.Locked || m.IsSystem // 系统 skill 恒锁
		m.Enabled = p.Enabled
		m.SortOrder = p.SortOrder
		m.CreatedAt = p.CreatedAt
		m.Version = p.Version
	}

	// 清理孤儿偏好项（目录已不存在）
	present := map[string]bool{}
	for _, m := range metas {
		present[m.Name] = true
	}
	kept := prefs.Prefs[:0]
	for _, p := range prefs.Prefs {
		if present[p.Name] {
			kept = append(kept, p)
		} else {
			changed = true
		}
	}
	prefs.Prefs = kept

	if changed {
		_ = s.savePrefs(prefs) // 尽力持久化补齐/清理，失败不阻塞列表返回
	}

	sort.SliceStable(metas, func(i, j int) bool {
		if metas[i].SortOrder != metas[j].SortOrder {
			return metas[i].SortOrder < metas[j].SortOrder
		}
		return metas[i].Name < metas[j].Name
	})
	return metas, nil
}

// ---- 用户偏好修改（B2）----

func (s *SkillsStore) setPref(name string, fn func(p *skillPref)) error {
	prefs, err := s.loadPrefs()
	if err != nil {
		return err
	}
	found := false
	for i := range prefs.Prefs {
		if prefs.Prefs[i].Name == name {
			fn(&prefs.Prefs[i])
			found = true
			break
		}
	}
	if !found {
		return fmt.Errorf("skill %q not found", name)
	}
	if err := s.savePrefs(prefs); err != nil {
		return err
	}
	s.invalidateListCache()
	return nil
}

func (s *SkillsStore) SetEnabled(name string, enabled bool) error {
	return s.setPref(name, func(p *skillPref) { p.Enabled = enabled })
}

func (s *SkillsStore) SetLocked(name string, locked bool) error {
	return s.setPref(name, func(p *skillPref) { p.Locked = locked })
}

func (s *SkillsStore) SetSortOrder(name string, order int) error {
	return s.setPref(name, func(p *skillPref) { p.SortOrder = order })
}

func (s *SkillsStore) SetOrigin(name string, origin string) error {
	return s.setPref(name, func(p *skillPref) { p.Origin = origin })
}

// GetBody 读取指定 skill 的 SKILL.md 正文（不含 frontmatter）。
func (s *SkillsStore) GetBody(name string) (string, error) {
	metas, err := s.List()
	if err != nil {
		return "", err
	}
	var dir string
	var isSystem bool
	for _, m := range metas {
		if m.Name == name {
			dir = m.Dir
			isSystem = m.IsSystem
			break
		}
	}
	if dir == "" {
		return "", fmt.Errorf("skill %q not found", name)
	}
	root := s.skillsRoot()
	if isSystem {
		root = filepath.Join(root, systemDirName)
	}
	content, err := readCapped(filepath.Join(root, dir, skillEntryFile))
	if err != nil {
		return "", err
	}
	_, body := parseFrontmatter(content)
	return body, nil
}

// GetSkillFile 读取 skill 目录内的子文件（L2.5 reference，阶段二用）。
func (s *SkillsStore) GetSkillFile(name, relPath string) (string, error) {
	metas, err := s.List()
	if err != nil {
		return "", err
	}
	var dir string
	for _, m := range metas {
		if m.Name == name {
			dir = m.Dir
			break
		}
	}
	if dir == "" {
		return "", fmt.Errorf("skill %q not found", name)
	}
	clean := filepath.Clean(relPath)
	if strings.HasPrefix(clean, "..") || filepath.IsAbs(clean) {
		return "", fmt.Errorf("path not allowed: %s", relPath)
	}
	allowed := []string{".md", ".sh", ".bash", ".py", ".txt", ".json", ".yaml", ".yml"}
	ok := false
	for _, ext := range allowed {
		if strings.HasSuffix(strings.ToLower(clean), ext) {
			ok = true
			break
		}
	}
	if !ok {
		return "", fmt.Errorf("file type not allowed: %s", relPath)
	}
	root := s.skillsRoot()
	absPath := filepath.Join(root, dir, clean)
	return readCapped(absPath)
}

// SkillFileList 列出一个 skill 的 references/ 与 scripts/ 下的相对路径（供 use_skill 组装资源清单）。
type SkillFileList struct {
	References []string `json:"references"`
	Scripts    []string `json:"scripts"`
}

// ListSkillFiles 返回指定 skill 的 references/ 与 scripts/ 相对路径列表（仅目录内，防穿越）。
func (s *SkillsStore) ListSkillFiles(name string) (SkillFileList, error) {
	metas, err := s.List()
	if err != nil {
		return SkillFileList{}, err
	}
	var dir string
	for _, m := range metas {
		if m.Name == name {
			dir = m.Dir
			break
		}
	}
	if dir == "" {
		return SkillFileList{}, fmt.Errorf("skill %q not found", name)
	}
	list := func(sub string) []string {
		out := []string{}
		base := filepath.Join(s.skillsRoot(), dir, sub)
		entries, err := os.ReadDir(base)
		if err != nil {
			return out
		}
		for _, e := range entries {
			if !e.IsDir() {
				out = append(out, sub+"/"+e.Name())
			}
		}
		return out
	}
	return SkillFileList{References: list(referencesDir), Scripts: list(scriptsDir)}, nil
}

// Delete 删除指定 skill 的目录与偏好记录。
func (s *SkillsStore) Delete(name string) error {
	metas, err := s.List()
	if err != nil {
		return err
	}
	var dir string
	for _, m := range metas {
		if m.Name == name {
			dir = m.Dir
			break
		}
	}
	if dir == "" {
		return fmt.Errorf("skill %q not found", name)
	}
	skillDir := filepath.Join(s.skillsRoot(), dir)
	// Refuse to traverse symlinks: an imported skill that points outside the
	// skills root must not be followed by RemoveAll. STORE-02.
	if err := assertNoSymlinks(skillDir); err != nil {
		return err
	}
	if err := os.RemoveAll(skillDir); err != nil {
		return err
	}
	// 清理偏好
	if err := s.setPref(name, func(p *skillPref) {
		// 标记删除（调用方负责清理孤儿项，List 做）
	}); err != nil {
		return err
	}
	s.invalidateListCache()
	return nil
}

// ---- 工具函数 ----

func readCapped(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()
	limited := io.LimitReader(f, maxSkillFileLen)
	b, err := io.ReadAll(limited)
	if err != nil {
		return "", err
	}
	return string(b), nil
}

func dirHasFiles(dir string) bool {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return false
	}
	return len(entries) > 0
}

func countFiles(dir string) int {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return 0
	}
	count := 0
	for _, e := range entries {
		if !e.IsDir() && !strings.HasPrefix(e.Name(), ".") {
			count++
		}
	}
	return count
}

func nowRFC3339() string { return time.Now().UTC().Format(time.RFC3339) }

func assembleSkillMD(name, description, body string) string {
	return fmt.Sprintf("---\nname: %s\ndescription: %s\n---\n\n%s", name, description, body)
}

func copyFile(src, dst string) error {
	// Refuse to follow symlinks during import: STORE-02.
	srcInfo, err := os.Lstat(src)
	if err != nil {
		return err
	}
	if srcInfo.Mode()&os.ModeSymlink != 0 {
		return fmt.Errorf("refusing to copy symlink: %s", src)
	}
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	if err := os.MkdirAll(filepath.Dir(dst), 0755); err != nil {
		return err
	}
	out, err := os.OpenFile(dst, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, srcInfo.Mode().Perm())
	if err != nil {
		return err
	}
	defer out.Close()
	_, err = io.Copy(out, in)
	return err
}

// assertNoSymlinks walks dir (Lstat, not Stat) and returns an error if any
// entry is a symlink. Used to gate destructive operations like Delete /
// importToDir so we never follow an attacker-controlled link out of the
// skills root. STORE-02.
func assertNoSymlinks(dir string) error {
	return filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.Mode()&os.ModeSymlink != 0 {
			return fmt.Errorf("refusing to traverse symlink in skill directory: %s", path)
		}
		return nil
	})
}

// copyDir duplicates src into dst. os.CopyFS (Go 1.23+) replaces the previous
// filepath.Walk + per-file os.Lstat/Open/Create loop, which paid an extra
// Lstat and a fresh open/create pair for every file. STORE-02 safety is
// preserved by the pre-check: os.CopyFS follows symlinks, so the explicit
// assertNoSymlinks walk must run first.
func copyDir(src, dst string) error {
	if err := assertNoSymlinks(src); err != nil {
		return err
	}
	return os.CopyFS(dst, os.DirFS(src))
}

// ---- 导入（B3）----

// ImportFromDir 将一个 skill 目录（含 SKILL.md）完整拷入 skills/<dir>/，返回导入的 skill name。
func (s *SkillsStore) ImportFromDir(srcDir string) (string, error) {
	mdPath := filepath.Join(srcDir, skillEntryFile)
	content, err := readCapped(mdPath)
	if err != nil {
		return "", fmt.Errorf("SKILL.md not found in %s: %w", srcDir, err)
	}
	fm, _ := parseFrontmatter(content)
	if fm.name == "" || fm.description == "" {
		return "", fmt.Errorf("SKILL.md missing name or description")
	}
	if !skillNameRe.MatchString(fm.name) {
		return "", fmt.Errorf("invalid skill name: %s", fm.name)
	}
	dstDir := filepath.Join(s.skillsRoot(), fm.name)
	return fm.name, s.importToDir(srcDir, dstDir, fm.name)
}

// ImportFromZip 接受一个 zip 文件路径，提取首层含 SKILL.md 的子目录并导入。
func (s *SkillsStore) ImportFromZip(zipPath string) (string, error) {
	r, err := zip.OpenReader(zipPath)
	if err != nil {
		return "", fmt.Errorf("open zip: %w", err)
	}
	defer r.Close()

	// 先找 SKILL.md 的位置
	type entry struct{ name, dir string }
	entries := []entry{}
	for _, f := range r.File {
		if f.FileInfo().IsDir() {
			continue
		}
		parts := strings.SplitN(f.Name, "/", 2)
		dir := parts[0]
		base := filepath.Base(f.Name)
		if strings.EqualFold(base, skillEntryFile) {
			entries = append(entries, entry{name: f.Name, dir: dir})
		}
	}
	if len(entries) == 0 {
		return "", fmt.Errorf("no SKILL.md found in zip")
	}
	// 用第一个 SKILL.md 的目录作为 skill 根
	root := entries[0].dir
	mdEntry := entries[0]

	// 读 SKILL.md 内容
	rcReal, err := r.Open(mdEntry.name)
	if err != nil {
		return "", fmt.Errorf("open SKILL.md in zip: %w", err)
	}
	defer rcReal.Close()
	b, err := io.ReadAll(io.LimitReader(rcReal, maxSkillFileLen))
	if err != nil {
		return "", fmt.Errorf("read SKILL.md content: %w", err)
	}
	fm, _ := parseFrontmatter(string(b))
	if fm.name == "" || fm.description == "" {
		return "", fmt.Errorf("SKILL.md missing name or description")
	}
	if !skillNameRe.MatchString(fm.name) {
		return "", fmt.Errorf("invalid skill name: %s", fm.name)
	}

	// 解压到临时目录，再整体拷入
	tmpDir, err := os.MkdirTemp("", "terminal-skill-import-")
	if err != nil {
		return "", fmt.Errorf("create temp dir: %w", err)
	}
	defer os.RemoveAll(tmpDir)

	for _, f := range r.File {
		if f.FileInfo().IsDir() {
			continue
		}
		rel := strings.TrimPrefix(f.Name, root+"/")
		if rel == f.Name {
			rel = filepath.Base(f.Name)
		}
		target := filepath.Join(tmpDir, rel)
		if err := os.MkdirAll(filepath.Dir(target), 0755); err != nil {
			return "", fmt.Errorf("mkdir: %w", err)
		}
		rc, err := f.Open()
		if err != nil {
			return "", fmt.Errorf("open zip entry: %w", err)
		}
		out, err := os.Create(target)
		if err != nil {
			rc.Close()
			return "", fmt.Errorf("create: %w", err)
		}
		_, err = io.Copy(out, rc)
		rc.Close()
		out.Close()
		if err != nil {
			return "", fmt.Errorf("copy: %w", err)
		}
	}

	dstDir := filepath.Join(s.skillsRoot(), fm.name)
	return fm.name, s.importToDir(tmpDir, dstDir, fm.name)
}

func (s *SkillsStore) importToDir(src, dst, name string) error {
	// 若目标已存在，允许覆盖（由调用方确认冲突策略）
	if err := os.RemoveAll(dst); err != nil {
		return fmt.Errorf("remove existing: %w", err)
	}
	if err := os.MkdirAll(dst, 0755); err != nil {
		return err
	}
	if err := copyDir(src, dst); err != nil {
		os.RemoveAll(dst)
		return fmt.Errorf("copy: %w", err)
	}
	// 写偏好
	prefs, err := s.loadPrefs()
	if err != nil {
		return err
	}
	found := false
	for i := range prefs.Prefs {
		if prefs.Prefs[i].Name == name {
			prefs.Prefs[i].Origin = "imported"
			prefs.Prefs[i].Locked = true
			prefs.Prefs[i].Enabled = true
			prefs.Prefs[i].CreatedAt = nowRFC3339()
			prefs.Prefs[i].Version++
			found = true
			break
		}
	}
	if !found {
		prefs.Prefs = append(prefs.Prefs, skillPref{
			Name:      name,
			Origin:    "imported",
			Locked:    true,
			Enabled:   true,
			SortOrder: len(prefs.Prefs),
			CreatedAt: nowRFC3339(),
			Version:   1,
		})
	}
	if err := s.savePrefs(prefs); err != nil {
		return err
	}
	s.invalidateListCache()
	return nil
}

// CreateSkill 从 name/description/body 创建单文件 skill（origin=created, locked=false）。
func (s *SkillsStore) CreateSkill(name, description, body string) error {
	if !skillNameRe.MatchString(name) {
		return fmt.Errorf("invalid skill name: %s", name)
	}
	if description == "" {
		return fmt.Errorf("description is required")
	}
	skillDir := filepath.Join(s.skillsRoot(), name)
	if err := os.MkdirAll(skillDir, 0755); err != nil {
		return err
	}
	mdPath := filepath.Join(skillDir, skillEntryFile)
	content := assembleSkillMD(name, description, body)
	if err := os.WriteFile(mdPath, []byte(content), 0644); err != nil {
		return err
	}
	prefs, err := s.loadPrefs()
	if err != nil {
		return err
	}
	found := false
	for i := range prefs.Prefs {
		if prefs.Prefs[i].Name == name {
			prefs.Prefs[i].Origin = "created"
			prefs.Prefs[i].Locked = false
			prefs.Prefs[i].Enabled = true
			prefs.Prefs[i].CreatedAt = nowRFC3339()
			prefs.Prefs[i].Version++
			found = true
			break
		}
	}
	if !found {
		prefs.Prefs = append(prefs.Prefs, skillPref{
			Name:      name,
			Origin:    "created",
			Locked:    false,
			Enabled:   true,
			SortOrder: len(prefs.Prefs),
			CreatedAt: nowRFC3339(),
			Version:   1,
		})
	}
	if err := s.savePrefs(prefs); err != nil {
		return err
	}
	s.invalidateListCache()
	return nil
}

// SaveSkill 覆盖已有 skill 的正文（仅限未锁定项）。
func (s *SkillsStore) SaveSkill(name, description, body string) error {
	metas, err := s.List()
	if err != nil {
		return err
	}
	var meta SkillMeta
	found := false
	for _, m := range metas {
		if m.Name == name {
			meta = m
			found = true
			break
		}
	}
	if !found {
		return fmt.Errorf("skill %q not found", name)
	}
	if meta.Locked {
		return fmt.Errorf("skill %q is locked", name)
	}
	skillDir := filepath.Join(s.skillsRoot(), meta.Dir)
	mdPath := filepath.Join(skillDir, skillEntryFile)
	content := assembleSkillMD(name, description, body)
	if err := os.WriteFile(mdPath, []byte(content), 0644); err != nil {
		return err
	}
	return s.setPref(name, func(p *skillPref) {
		p.Version++
		p.CreatedAt = nowRFC3339()
	})
}
