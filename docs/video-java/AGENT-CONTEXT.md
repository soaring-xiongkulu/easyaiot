# VIDEO Java — Agent Context

- **程序：** VIDEO Python → Java 等价替换  
- **文档根：** `docs/video-java/`  
- **栈与结构：** [STACK.md](./STACK.md)（开题锁定，审查前勿擅自换 Boot 3 / 非 DEVICE 生态）  
- **计划：** [PLAN.md](./PLAN.md)  
- **交接：** [HANDOFF.md](./HANDOFF.md)  
- **纪律：** [EXECUTION.md](./EXECUTION.md)  
- **测试场：** [testbed/README.md](./testbed/README.md)  

## 环境

| | |
|--|--|
| Oracle | `F:/acme` + `VIDEO/`（Python） |
| Candidate | worktree `feat/video-java`（审查通过后创建） |
| 参照方法论 | `docs/runtime-parity/`（只读参照，**门禁勿混用**） |

## 硬约束

1. 完成定义 = certify 等价，不是「服务起来」。  
2. 不重写 RUNTIME / ffmpeg / SRS / ZLM / AI。  
3. 先测后改；红清单驱动。  
4. 估时按 case，不类比 runtime-parity 墙钟、不空喊人月。  

## 当前状态

**有条件通过（2026-08-10）。** §9.1 六条已写入 STACK/PLAN。  
**停：等开工指令后再做 Phase -1。** Phase -1 绿之前不开 Phase 0 业务搬迁。
