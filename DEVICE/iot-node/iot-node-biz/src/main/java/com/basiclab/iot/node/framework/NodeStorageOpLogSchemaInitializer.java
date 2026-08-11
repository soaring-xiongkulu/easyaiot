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
 * 确保 node_storage_op_log 表存在（兼容无 Flyway 环境）
 */
@Component
@Slf4j
public class NodeStorageOpLogSchemaInitializer implements ApplicationRunner {

    @Resource
    private JdbcTemplate jdbcTemplate;

    @Override
    public void run(ApplicationArguments args) {
        try {
            ClassPathResource resource = new ClassPathResource("sql/node_storage_op_log.sql");
            if (!resource.exists()) {
                ensureMinimalTable();
                return;
            }
            String sql = StreamUtils.copyToString(resource.getInputStream(), StandardCharsets.UTF_8);
            executeStatements(sql);
            log.info("[NodeStorageOpLogSchemaInitializer] node_storage_op_log 表已就绪");
        } catch (Exception e) {
            log.warn("[NodeStorageOpLogSchemaInitializer] 初始化失败，尝试兜底建表: {}", e.getMessage());
            try {
                ensureMinimalTable();
            } catch (Exception ex) {
                log.error("[NodeStorageOpLogSchemaInitializer] 建表失败: {}", ex.getMessage());
            }
        }
    }

    private void executeStatements(String sql) {
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

    private void ensureMinimalTable() {
        executeStatements(
                "CREATE SEQUENCE IF NOT EXISTS public.node_storage_op_log_id_seq START WITH 1 INCREMENT BY 1;"
                        + "CREATE TABLE IF NOT EXISTS public.node_storage_op_log ("
                        + "id bigint DEFAULT nextval('public.node_storage_op_log_id_seq'::regclass) NOT NULL,"
                        + "node_id bigint,"
                        + "op_type character varying(32) NOT NULL,"
                        + "success boolean DEFAULT false,"
                        + "message character varying(1024),"
                        + "steps_json text,"
                        + "creator character varying(64),"
                        + "create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,"
                        + "updater character varying(64),"
                        + "update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,"
                        + "deleted smallint DEFAULT 0 NOT NULL,"
                        + "CONSTRAINT node_storage_op_log_pkey PRIMARY KEY (id)"
                        + ");"
                        + "CREATE INDEX IF NOT EXISTS idx_node_storage_op_log_node_time "
                        + "ON public.node_storage_op_log (node_id, create_time DESC) WHERE deleted = 0;"
        );
    }
}
