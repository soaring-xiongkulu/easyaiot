package com.basiclab.iot.node.framework;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.util.StreamUtils;

import javax.annotation.Resource;
import java.nio.charset.StandardCharsets;

/**
 * 确保 edge_node 表存在（兼容无 Flyway 环境）
 */
@Component
@Slf4j
public class EdgeNodeSchemaInitializer implements ApplicationRunner {

    @Resource
    private JdbcTemplate jdbcTemplate;

    @Override
    public void run(ApplicationArguments args) {
        try {
            ClassPathResource resource = new ClassPathResource("sql/edge_node.sql");
            if (!resource.exists()) {
                log.warn("[EdgeNodeSchemaInitializer] 未找到 classpath:sql/edge_node.sql，跳过建表");
                ensureMinimalTable();
                return;
            }
            String sql = StreamUtils.copyToString(resource.getInputStream(), StandardCharsets.UTF_8);
            executeStatements(sql);
            log.info("[EdgeNodeSchemaInitializer] edge_node 表已就绪");
        } catch (Exception e) {
            log.warn("[EdgeNodeSchemaInitializer] 初始化 edge_node 失败，尝试兜底建表: {}", e.getMessage());
            try {
                ensureMinimalTable();
                log.info("[EdgeNodeSchemaInitializer] edge_node 兜底建表成功");
            } catch (Exception ex) {
                log.error("[EdgeNodeSchemaInitializer] edge_node 建表失败（可手动执行 sql/edge_node.sql）: {}",
                        ex.getMessage());
            }
        }
    }

    private void executeStatements(String sql) {
        // DO $$ ... $$ 匿名块内含分号，不能按 ; 粗暴拆分
        String[] parts = sql.split(";(?=(?:[^$]*\\$\\$[^$]*\\$\\$)*[^$]*$)");
        for (String stmt : parts) {
            String trimmed = stmt.trim();
            if (trimmed.isEmpty()) {
                continue;
            }
            String withoutLineComments = trimmed.replaceAll("(?m)^\\s*--.*$", "").trim();
            if (withoutLineComments.isEmpty()) {
                continue;
            }
            jdbcTemplate.execute(withoutLineComments);
        }
    }

    /** SQL 资源缺失时的最小可用结构，保证 /node/edge/page 不再 500 */
    private void ensureMinimalTable() {
        executeStatements(
                "CREATE SEQUENCE IF NOT EXISTS public.edge_node_id_seq START WITH 1 INCREMENT BY 1;"
                        + "CREATE TABLE IF NOT EXISTS public.edge_node ("
                        + "id bigint DEFAULT nextval('public.edge_node_id_seq'::regclass) NOT NULL,"
                        + "compute_node_id bigint NOT NULL,"
                        + "name character varying(128),"
                        + "host character varying(128),"
                        + "status character varying(16) DEFAULT 'offline',"
                        + "fingerprint character varying(128),"
                        + "mqtt_client_id character varying(128),"
                        + "mqtt_username character varying(128),"
                        + "agent_version character varying(64),"
                        + "node_role character varying(32),"
                        + "max_task_count integer DEFAULT 1,"
                        + "active_task_count integer DEFAULT 0,"
                        + "ceph_mount_ready boolean DEFAULT false,"
                        + "last_heartbeat_at timestamp without time zone,"
                        + "enabled boolean DEFAULT true,"
                        + "remark character varying(512),"
                        + "tags jsonb,"
                        + "creator character varying(64),"
                        + "create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,"
                        + "updater character varying(64),"
                        + "update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,"
                        + "deleted smallint DEFAULT 0 NOT NULL,"
                        + "CONSTRAINT edge_node_pkey PRIMARY KEY (id)"
                        + ");"
                        + "CREATE UNIQUE INDEX IF NOT EXISTS uk_edge_node_compute_node "
                        + "ON public.edge_node (compute_node_id) WHERE (deleted = 0);"
        );
    }

}
