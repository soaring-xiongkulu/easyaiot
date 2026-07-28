# TRANSFORM 业务流程 E2E 测试

用 Python 脚本验证：

1. **多渠道打通**：sink Kafka → Outbox → party(MES/ERP/WMS) + http webhook
2. **横向扩容**：消费/投递约定 Group 成员可见，压测并行投递
3. **自愈再推**：坏地址失败 → 修复规则 → outbox/dlq 再推成功

详细手工步骤与用例矩阵见：[`../../docs/07-流程测试设计与详细步骤.md`](../../docs/07-流程测试设计与详细步骤.md)。

## 最快看见价值（无需启动 iot-sink）

环境只要有 **Kafka + PostgreSQL + Java**（本仓库常见 docker 中间件即可），**不要**启 DEVICE/iot-sink：

```bash
cd TRANSFORM/scripts/e2e
bash run_value_demo.sh
```

脚本会：初始化库 → 启 mock(MES/ERP/WMS) → 启 transform-runtime → **用 `simulate_iot_sink.py` 同款逻辑向真实 sink Topic 投喂** → 打印价值报告。

仅投喂（runtime/mock 已起）：

```bash
python simulate_iot_sink.py          # 工厂全场景写 Kafka
python demo_value.py                 # 精选 3 条故事 + 链路断言 + 报告
```

## 前置

| 组件 | 说明 |
|------|------|
| Kafka | `KAFKA_BOOTSTRAP`，含 sink / deliver Topic |
| PostgreSQL | 库 `iot-transform20` 已建表 |
| transform-runtime | 默认 `http://127.0.0.1:48096`，role=`full` |
| Python 3.10+ | `pip install -r requirements.txt` |

## 快速开始

```bash
cd TRANSFORM/scripts/e2e
cp env.example .env   # 按环境改
pip install -r requirements.txt

# 终端 A：仅 mock（run_all 也会自动拉起）
python mock_receiver.py --port 18080

# 终端 B：一键跑全套
python run_all.py

# 或分步
python 01_channels.py
python 02_horizontal_scale.py --expect-members 1 --batch 20
python 03_self_heal.py
```

## 横向扩容复测（推荐）

1. 先跑 `02_horizontal_scale.py --expect-members 1`
2. 再启第二个 `transform-runtime`（同 Kafka/DB，改端口如 48097）
3. 再跑 `02_horizontal_scale.py --expect-members 2`

消费 Group `transform.kafka.consume.device` 的 `member_count` 应变为 2。

## 脚本说明

| 文件 | 作用 |
|------|------|
| `common.py` | API / Kafka / 合同种子 / 等待断言 |
| `mock_receiver.py` | 模拟 MES/ERP/WMS/Webhook（`:18080`） |
| `01_channels.py` | DATA→ERP、ALERT→MES+HTTP、VIDEO_META→WMS |
| `02_horizontal_scale.py` | Group 成员 + 压测增量 |
| `03_self_heal.py` | 坏地址失败 → 修复 → 再推 |
| `run_all.py` | 自动启 mock 并串跑 01→03 |

## 断言要点

- Outbox 状态进入 `SENT` / `DELIVERED`
- mock `/events/{eventId}` 能看到对应渠道（`party-erp` / `party-mes` / `http-webhook` / `party-wms`）
- 坏路径返回 404 后 outbox 为 `FAILED`/`DEAD`，修复合同并 `POST /transform/outbox/{id}/replay` 后可达 MES
