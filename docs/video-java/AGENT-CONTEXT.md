# VIDEO Java — Agent Context

- **程序：** VIDEO Python → Java **完整功能替换**（Phase FR）  
- **文档根：** `docs/video-java/`  
- **现行方案：** [PLAN_FULL_REPLACEMENT.md](./PLAN_FULL_REPLACEMENT.md)  
- **唯一进度表：** [FULL_REPLACEMENT_GAP.md](./FULL_REPLACEMENT_GAP.md)  
- **栈：** [STACK.md](./STACK.md)  
- **交接：** [HANDOFF.md](./HANDOFF.md)  
- **纪律：** [EXECUTION.md](./EXECUTION.md)  
- **历史切片计划（只读）：** [PLAN.md](./PLAN.md)

## 环境

| | |
|--|--|
| Oracle（只读） | `VIDEO/_retired_python_video/`；可选 `F:/acme/VIDEO` |
| Candidate | worktree `F:/acme/.worktrees/video-java` · `feat/video-java` |
| 薄烟雾 | `python tools/video_java/certify.py --phase 0` |

## 硬约束

1. 完成定义 = 缺口表域级 ✅，**不是** CERTIFY 全绿 / COMPLETE / 长观察。  
2. 门禁只留防回归薄烟雾；扩面用契约测 + 路由 diff。  
3. 禁止再堆 CLOSE/EVID；禁止整域标 migrated（除非缺口表该域全 ✅）。  
4. 不重写 RUNTIME / ffmpeg / SRS / ZLM / AI。  
5. KPI = 缩小 ≈265→29 路由差。

## 当前状态

**Phase FR 进行中。** FR-B28 keys-matrix 已绿（41 映射 / 59 envelope-only）；完整替换未完成。  
下一包：见 HANDOFF §9。
