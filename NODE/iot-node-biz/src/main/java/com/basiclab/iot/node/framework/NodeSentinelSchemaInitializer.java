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

@Component
@Slf4j
public class NodeSentinelSchemaInitializer implements ApplicationRunner {

    @Resource
    private JdbcTemplate jdbcTemplate;

    @Override
    public void run(ApplicationArguments args) {
        try {
            ClassPathResource resource = new ClassPathResource("sql/node_sentinel_snapshot.sql");
            if (!resource.exists()) {
                log.warn("[NodeSentinelSchemaInitializer] 未找到 sql/node_sentinel_snapshot.sql");
                return;
            }
            String sql = StreamUtils.copyToString(resource.getInputStream(), StandardCharsets.UTF_8);
            for (String stmt : sql.split(";")) {
                String trimmed = stmt.trim();
                if (!trimmed.isEmpty()) {
                    jdbcTemplate.execute(trimmed);
                }
            }
            log.info("[NodeSentinelSchemaInitializer] node_sentinel_snapshot 表已就绪");
            runSqlFile("sql/node_sentinel_snapshot_migration.sql");
            runSqlFile("sql/node_sentinel_remediate_log.sql");
            runSqlFile("sql/node_functions_column.sql");
        } catch (Exception e) {
            log.error("[NodeSentinelSchemaInitializer] 建表失败: {}", e.getMessage());
        }
    }

    private void runSqlFile(String path) {
        try {
            ClassPathResource resource = new ClassPathResource(path);
            if (!resource.exists()) {
                return;
            }
            String sql = StreamUtils.copyToString(resource.getInputStream(), StandardCharsets.UTF_8);
            for (String stmt : sql.split(";")) {
                String trimmed = stmt.trim();
                if (!trimmed.isEmpty()) {
                    jdbcTemplate.execute(trimmed);
                }
            }
            log.info("[NodeSentinelSchemaInitializer] {} 已执行", path);
        } catch (Exception e) {
            log.warn("[NodeSentinelSchemaInitializer] {} 执行跳过: {}", path, e.getMessage());
        }
    }
}
