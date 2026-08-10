# VIDEO Java test media

Phase -1 不提交大体积 mp4。Phase 0+ 可按需复用 `tools/runtime_parity/fetch_parity_media.py` 的思路，将媒体下载到本目录。

建议：

1. 使用 Intel sample 或仓内已有测试片段（经 safe_fsops 拷贝策略）
2. 在 manifest case 元数据中声明 `needs_runtime` 与媒体路径
3. 禁止将 golden 与大媒体混进 runtime-parity 目录
