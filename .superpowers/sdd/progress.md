# Progress — Phase FR（行为对等）

HTTP 面 FR-W* 已齐。行为波次：

| 包 | Status | Commit |
|----|--------|--------|
| FR-B1 post-process sink | DONE | `13c505d` |
| FR-B2 MinIO | DONE | `09a0051` |
| FR-B3 snap_task sched | DONE | `57abb40` |
| FR-B4 remote node | DONE | `3913267` |
| **FR-B5** face/plate | **DONE** | `34667aa` |
| FR-B6 camera hardware | DONE | `e1ed889` |
| FR-B7 ticket + rollback | DONE | |
| FR-B8 SF cluster health | DONE | `ccd187e` |
| **FR-B9** inference + match alerts | **DONE** | `59c4d5e` |
| **FR-B10** patrol/SSE + audio_talk + match MinIO + pose match-test | **DONE** | `6a5ff12` |
| **FR-B11** GB28181 目录同步 + Nacos 进程切换演练 | **DONE** | `430faaa` |
| **FR-B12** 目录 JSON 同步 + FlightHub/大华 NVR | **DONE** | `a1d2997` |
| **FR-B13** 媒体节点池 + Ceph allocate | **DONE** | `9384f9b` |
| **FR-B14** resolve 只读接线 + post_process 远程 worker | **DONE** | `012974a` |
| **FR-B15** DVR Kafka consumer + services 处置表 | **DONE** | `68f6811` |
| **FR-B16** Snap Kafka consumer + 契约回归脚手架 | **DONE** | `8b71d4b` |
| **FR-B17** 全量路由 method-aware 薄契约探针 | **DONE** | `1d593bf` |
| **FR-B18** 收口 FR-B17 六条探针 fail | **DONE** | `db905fd` |
| **FR-B19** P0/P1 字段级 JSON 契约抽样 | **DONE** | `d995a7f` |
| **FR-B20** 14 前缀字段抽样扩面 | **DONE** | `ca78c53` |
| **FR-B21** GET 信封自动矩阵 + 信封缺口修复 | **DONE** | `0649efe` |
| **FR-B22** 深字段扩面 + HANDOFF/soak checklist | **DONE** | `d605e2c` |
| **FR-B23** 本地 Kafka+MinIO soak + deep skip 清除 | **DONE** | `6dda749` |
| **FR-B28** GET keys-matrix 基线（41 映射 / 59 envelope-only） | **DONE** | `5fed768` |
| **FR-B29** keys-matrix 扩面 + 8 deferred 清除 | **DONE** | `5514689` |
| **FR-B30** Snap/record 存储用量真 MinIO + GAP/HANDOFF 收口 | **DONE** | `54407fe` |
| **FR-B31** POST/PUT mutating-matrix + storage cleanup MinIO 对齐 | **DONE** | (see branch) |
| **FR-B32** cleanup 真删除 E2E + 6 非 JSON GET content-type 探针 | **DONE** | `3692313` |
| **FR-B33** POST keys-matrix 16 样本 + camera register 缺键修复 | **DONE** | `3e7d48f` |
| **FR-B34** POST keys-matrix 42 样本 + directory/auto-enroll 修复 | **DONE** | (this commit) |
| **FR-B35** POST keys-matrix 63 样本 + audio_talk 覆盖 | **DONE** | (prior) |
| **FR-B36** POST keys-matrix 131 样本 + inventoried POST 109/112 | **DONE** | (this commit) |
| **FR-B37** multipart 成功探针 + certify bucket S3 名修复 | **DONE** | (this commit) |
| **FR-B38** plate image_url MinIO + face entry 无模型诚实 400 | **DONE** | (this commit) |
| **FR-B39** HTTP 400/404 中央映射 + plate update 带图 | **DONE** | (this commit) |
| **FR-B40** contract_regression 39×404 假阳性收口 | **DONE** | (this commit) |
| **FR-B41** face_rec.onnx + face entry 成功路径 local | **DONE** | (this commit) |

COMPLETE 仍禁止，直至行为缺口可勾选或产品签字豁免 + **prod** soak checklist 有证据（local-only ≠ prod 绿）。
