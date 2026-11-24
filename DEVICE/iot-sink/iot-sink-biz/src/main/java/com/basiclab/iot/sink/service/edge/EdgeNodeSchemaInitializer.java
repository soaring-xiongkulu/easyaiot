package com.basiclab.iot.sink.service.edge;

import com.baomidou.dynamic.datasource.toolkit.DynamicDataSourceContextHolder;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;

/**
 * iot-sink owns the edge telemetry landing schema in the VIDEO database.
 * VIDEO maps the same tables for management APIs but never consumes telemetry.
 */
@Slf4j
@Component
public class EdgeNodeSchemaInitializer implements ApplicationRunner {

    @Resource
    private JdbcTemplate jdbcTemplate;

    @Override
    public void run(ApplicationArguments args) {
        try {
            DynamicDataSourceContextHolder.push("video");
            jdbcTemplate.execute("CREATE TABLE IF NOT EXISTS edge_compute_node ("
                    + "id BIGSERIAL PRIMARY KEY,"
                    + "fingerprint VARCHAR(128) NOT NULL UNIQUE,"
                    + "name VARCHAR(128) NOT NULL,"
                    + "host VARCHAR(255),"
                    + "status VARCHAR(16) NOT NULL DEFAULT 'offline',"
                    + "enabled BOOLEAN NOT NULL DEFAULT TRUE,"
                    + "node_kind VARCHAR(32) NOT NULL DEFAULT 'edge_box',"
                    + "hardware_provider VARCHAR(64),"
                    + "soc_model VARCHAR(64),"
                    + "accelerator_type VARCHAR(32),"
                    + "accelerator_count INTEGER NOT NULL DEFAULT 0,"
                    + "runtime_target VARCHAR(128),"
                    + "runtime_version VARCHAR(64),"
                    + "agent_version VARCHAR(64),"
                    + "agent_port INTEGER NOT NULL DEFAULT 9100,"
                    + "max_task_count INTEGER NOT NULL DEFAULT 0,"
                    + "active_task_count INTEGER NOT NULL DEFAULT 0,"
                    + "mqtt_username VARCHAR(128) NOT NULL UNIQUE,"
                    + "mqtt_client_id VARCHAR(128) NOT NULL UNIQUE,"
                    + "agent_token VARCHAR(256) NOT NULL,"
                    + "cpu_percent DOUBLE PRECISION,"
                    + "mem_percent DOUBLE PRECISION,"
                    + "disk_percent DOUBLE PRECISION,"
                    + "temperature_c DOUBLE PRECISION,"
                    + "mem_used_bytes BIGINT,"
                    + "mem_total_bytes BIGINT,"
                    + "disk_used_bytes BIGINT,"
                    + "disk_total_bytes BIGINT,"
                    + "accelerator_info JSONB NOT NULL DEFAULT '[]'::jsonb,"
                    + "pipelines JSONB NOT NULL DEFAULT '[]'::jsonb,"
                    + "remote_access JSONB NOT NULL DEFAULT '{}'::jsonb,"
                    + "latest_payload JSONB NOT NULL DEFAULT '{}'::jsonb,"
                    + "last_message_id VARCHAR(128),"
                    + "last_heartbeat_at TIMESTAMPTZ,"
                    + "connected_at TIMESTAMPTZ,"
                    + "disconnected_at TIMESTAMPTZ,"
                    + "remark VARCHAR(500),"
                    + "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),"
                    + "updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
                    + ")");
            jdbcTemplate.execute("CREATE INDEX IF NOT EXISTS idx_edge_compute_node_status "
                    + "ON edge_compute_node(status, enabled)");
            jdbcTemplate.execute("CREATE INDEX IF NOT EXISTS idx_edge_compute_node_soc "
                    + "ON edge_compute_node(soc_model)");

            jdbcTemplate.execute("CREATE TABLE IF NOT EXISTS edge_compute_metric ("
                    + "id BIGSERIAL PRIMARY KEY,"
                    + "node_id BIGINT NOT NULL REFERENCES edge_compute_node(id) ON DELETE CASCADE,"
                    + "cpu_percent DOUBLE PRECISION,"
                    + "mem_percent DOUBLE PRECISION,"
                    + "disk_percent DOUBLE PRECISION,"
                    + "temperature_c DOUBLE PRECISION,"
                    + "active_tasks INTEGER,"
                    + "payload JSONB NOT NULL DEFAULT '{}'::jsonb,"
                    + "collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
                    + ")");
            jdbcTemplate.execute("CREATE INDEX IF NOT EXISTS idx_edge_compute_metric_node_time "
                    + "ON edge_compute_metric(node_id, collected_at DESC)");

            jdbcTemplate.execute("CREATE TABLE IF NOT EXISTS edge_compute_message ("
                    + "node_id BIGINT NOT NULL REFERENCES edge_compute_node(id) ON DELETE CASCADE,"
                    + "message_id VARCHAR(128) NOT NULL,"
                    + "message_type VARCHAR(32) NOT NULL,"
                    + "received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),"
                    + "PRIMARY KEY(node_id, message_id)"
                    + ")");
            jdbcTemplate.execute("CREATE INDEX IF NOT EXISTS idx_edge_compute_message_received "
                    + "ON edge_compute_message(received_at)");

            jdbcTemplate.execute("CREATE TABLE IF NOT EXISTS edge_compute_command ("
                    + "id BIGSERIAL PRIMARY KEY,"
                    + "command_id VARCHAR(64) NOT NULL UNIQUE,"
                    + "node_id BIGINT NOT NULL REFERENCES edge_compute_node(id) ON DELETE CASCADE,"
                    + "command VARCHAR(64) NOT NULL,"
                    + "request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,"
                    + "ack_payload JSONB,"
                    + "status VARCHAR(16) NOT NULL DEFAULT 'sent',"
                    + "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),"
                    + "ack_at TIMESTAMPTZ"
                    + ")");
            jdbcTemplate.execute("CREATE INDEX IF NOT EXISTS idx_edge_compute_command_node_time "
                    + "ON edge_compute_command(node_id, created_at DESC)");
            log.info("[EdgeNodeSchema] 边缘计算落库表已就绪（iot-video20）");
        } catch (Exception ex) {
            log.error("[EdgeNodeSchema] 初始化边缘计算落库表失败: {}", ex.getMessage(), ex);
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }
}
