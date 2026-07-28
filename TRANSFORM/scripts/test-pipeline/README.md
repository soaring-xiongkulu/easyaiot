# TRANSFORM 全链路流水线测试

目标：**本机没有默认 TRANSFORM 时也能一键跑通业务流程**（自动拉起本机默认 + mock，再投喂验渠道）。

## 一键

```bash
cd TRANSFORM/scripts/test-pipeline
cp -n env.example .env   # 按需改 Kafka/PG

# 推荐：本机没有也会自动拉起，并跑 DATA/ALERT/FACE 业务
bash run_all.sh
# 等同
bash run_all.sh --mode full --count 1
```

仓库入口：

```bash
bash TRANSFORM/scripts/test_full_pipeline.sh
```

## 会自动做什么

| 步骤 | 行为 |
|------|------|
| 00 预检 | Kafka/PG、建 Topic、尽量建表、确保 jar |
| ensure-local | `:48096` 没有 → 自动 `java -jar` 拉起本机默认 |
| ensure-mock | `:18080` 没有 → 自动启 MES/ERP/WMS mock |
| 03/04 | 心跳 + 集群 API / PING |
| 06 业务 | 模拟 iot-sink 投喂 → Outbox → ERP/MES/HTTP/WMS |
| 05 清理 | 清 mock/旁路；**默认保留**自动拉起的本机默认 |

`count>=2` 时再起 `count-1` 个旁路实例（端口 `48110+`，不覆盖本机默认）。

## 常用参数

```bash
bash run_all.sh --count 2                 # 本机 + 1 旁路
bash run_all.sh --skip-business           # 只验部署/心跳
bash run_all.sh --cleanup-local           # 结束后也停掉自动拉起的本机默认
bash run_all.sh --no-cleanup              # 全部保留
```

## 前置

只需本机 **Kafka + PostgreSQL**（库表脚本会尽量自动执行）。  
不需要事先启动 TRANSFORM / mock / iot-sink。
