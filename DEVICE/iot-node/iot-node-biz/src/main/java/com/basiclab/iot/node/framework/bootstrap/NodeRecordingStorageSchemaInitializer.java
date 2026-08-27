package com.basiclab.iot.node.framework.bootstrap;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;

/**
 * 为既有 iot-node 数据库幂等补齐录像存储模式字段。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class NodeRecordingStorageSchemaInitializer {

    private final JdbcTemplate jdbcTemplate;

    @PostConstruct
    public void initialize() {
        try {
            jdbcTemplate.execute("ALTER TABLE compute_node "
                    + "ADD COLUMN IF NOT EXISTS recording_storage_mode VARCHAR(20) NOT NULL DEFAULT 'central_shared'");
            jdbcTemplate.execute("ALTER TABLE compute_node "
                    + "ADD COLUMN IF NOT EXISTS recording_storage_state VARCHAR(20) NOT NULL DEFAULT 'active'");
            jdbcTemplate.execute("ALTER TABLE compute_node "
                    + "ADD COLUMN IF NOT EXISTS recording_storage_generation BIGINT NOT NULL DEFAULT 1");
            jdbcTemplate.execute("ALTER TABLE compute_node "
                    + "ADD COLUMN IF NOT EXISTS media_public_url VARCHAR(500)");
            jdbcTemplate.execute("ALTER TABLE compute_node "
                    + "ADD COLUMN IF NOT EXISTS recording_storage_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP");
            jdbcTemplate.execute("ALTER TABLE compute_node "
                    + "ADD COLUMN IF NOT EXISTS recording_storage_error VARCHAR(500)");
            jdbcTemplate.update("UPDATE compute_node SET recording_storage_mode = 'central_shared' "
                    + "WHERE recording_storage_mode IS NULL OR TRIM(recording_storage_mode) = ''");
            jdbcTemplate.update("UPDATE compute_node SET recording_storage_state = 'active' "
                    + "WHERE recording_storage_state IS NULL OR TRIM(recording_storage_state) = ''");
            jdbcTemplate.update("UPDATE compute_node SET recording_storage_generation = 1 "
                    + "WHERE recording_storage_generation IS NULL OR recording_storage_generation < 1");
        } catch (Exception e) {
            // 启动阶段保留服务可诊断性；后续访问新增字段会明确暴露数据库权限/迁移问题。
            log.error("初始化 compute_node 录像存储字段失败: {}", e.getMessage(), e);
        }
    }
}
