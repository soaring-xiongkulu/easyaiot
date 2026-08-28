-- ============================================================
-- FLOW 工作流模块 —— iot-flow20 库 DDL
-- 说明：
--   * 流程模型/定义/实例/任务状态全部承载在 Flowable ACT_ 表（启动自动建表），
--     本库仅保存业务扩展表；
--   * 告警路由链路（route_rule / alert_record）与租户无关，使用 BaseDO；
--   * category / user_group / copy 属租户域，含 tenant_id 列。
-- 用法示例：
--   docker exec -i postgres-server psql -U postgres -d iot-flow20 < 本文件（可选，服务启动也可手工执行）
-- ============================================================

-- 告警 → 流程 路由规则
CREATE TABLE IF NOT EXISTS flow_alert_route_rule (
    id                      BIGSERIAL PRIMARY KEY,
    rule_name               VARCHAR(64)  NOT NULL,
    priority                INT          NOT NULL DEFAULT 0,
    process_definition_key  VARCHAR(64)  NOT NULL,
    match_conditions        TEXT         NOT NULL DEFAULT '[]',
    dedup_window_seconds    INT          NOT NULL DEFAULT 300,
    enabled                 BOOLEAN      NOT NULL DEFAULT TRUE,
    start_user_id           BIGINT,
    remark                  VARCHAR(500),
    creator                 VARCHAR(64)  DEFAULT '',
    create_time             TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updater                 VARCHAR(64)  DEFAULT '',
    update_time             TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    deleted                 SMALLINT     NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_flow_alert_route_rule_enabled ON flow_alert_route_rule (enabled, priority DESC);

-- 告警处理记录（责任闭环）
CREATE TABLE IF NOT EXISTS flow_alert_record (
    id                      BIGSERIAL PRIMARY KEY,
    alert_id                BIGINT       NOT NULL,
    alert_source            VARCHAR(32)  NOT NULL DEFAULT 'VIDEO_TASK',
    alert_snapshot          TEXT,
    process_instance_id     VARCHAR(64),
    process_definition_key  VARCHAR(64),
    process_instance_status INT          NOT NULL DEFAULT 1,
    current_task_name       VARCHAR(128),
    current_assignees       VARCHAR(500),
    finish_time             TIMESTAMP,
    creator                 VARCHAR(64)  DEFAULT '',
    create_time             TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updater                 VARCHAR(64)  DEFAULT '',
    update_time             TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    deleted                 SMALLINT     NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX IF NOT EXISTS uk_flow_alert_record_alert ON flow_alert_record (alert_id, process_definition_key, deleted);
CREATE INDEX IF NOT EXISTS idx_flow_alert_record_instance ON flow_alert_record (process_instance_id);

-- 流程分类
CREATE TABLE IF NOT EXISTS flow_category (
    id           BIGSERIAL PRIMARY KEY,
    name         VARCHAR(64)  NOT NULL,
    code         VARCHAR(64)  NOT NULL,
    status       SMALLINT     NOT NULL DEFAULT 0,
    sort         INT          NOT NULL DEFAULT 0,
    description  VARCHAR(500),
    tenant_id    BIGINT       NOT NULL DEFAULT 0,
    creator      VARCHAR(64)  DEFAULT '',
    create_time  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updater      VARCHAR(64)  DEFAULT '',
    update_time  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    deleted      SMALLINT     NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX IF NOT EXISTS uk_flow_category_code ON flow_category (code, tenant_id, deleted);

-- 审批用户组（候选人策略 USER_GROUP）
CREATE TABLE IF NOT EXISTS flow_user_group (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(64)  NOT NULL,
    description     VARCHAR(500),
    member_user_ids VARCHAR(2000) NOT NULL DEFAULT '[]',
    status          SMALLINT     NOT NULL DEFAULT 0,
    tenant_id       BIGINT       NOT NULL DEFAULT 0,
    creator         VARCHAR(64)  DEFAULT '',
    create_time     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updater         VARCHAR(64)  DEFAULT '',
    update_time     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    deleted         SMALLINT     NOT NULL DEFAULT 0
);

-- 抄送记录（任务抄送 / 抄送节点产出）
CREATE TABLE IF NOT EXISTS flow_copy (
    id                    BIGSERIAL PRIMARY KEY,
    process_instance_id   VARCHAR(64)  NOT NULL,
    process_instance_name VARCHAR(200),
    category              VARCHAR(64),
    task_id               VARCHAR(64),
    task_name             VARCHAR(128),
    activity_id           VARCHAR(64),
    start_user_id         BIGINT,
    reason                VARCHAR(500),
    user_id               BIGINT       NOT NULL,
    tenant_id             BIGINT       NOT NULL DEFAULT 0,
    creator               VARCHAR(64)  DEFAULT '',
    create_time           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updater               VARCHAR(64)  DEFAULT '',
    update_time           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    deleted               SMALLINT     NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_flow_copy_user ON flow_copy (user_id, create_time DESC);
CREATE INDEX IF NOT EXISTS idx_flow_copy_instance ON flow_copy (process_instance_id);
