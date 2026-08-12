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
 * 确保 nfs_cluster / nfs_cluster_bridge 表存在
 */
@Component
@Slf4j
public class NfsClusterSchemaInitializer implements ApplicationRunner {

    @Resource
    private JdbcTemplate jdbcTemplate;

    @Override
    public void run(ApplicationArguments args) {
        try {
            ClassPathResource resource = new ClassPathResource("sql/nfs_cluster.sql");
            if (!resource.exists()) {
                ensureMinimalTable();
                return;
            }
            String sql = StreamUtils.copyToString(resource.getInputStream(), StandardCharsets.UTF_8);
            executeStatements(sql);
            log.info("[NfsClusterSchemaInitializer] nfs_cluster 表已就绪");
        } catch (Exception e) {
            log.warn("[NfsClusterSchemaInitializer] 初始化失败，尝试兜底建表: {}", e.getMessage());
            try {
                ensureMinimalTable();
            } catch (Exception ex) {
                log.error("[NfsClusterSchemaInitializer] 建表失败: {}", ex.getMessage());
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
                "CREATE SEQUENCE IF NOT EXISTS public.nfs_cluster_id_seq START WITH 1 INCREMENT BY 1;"
                        + "CREATE TABLE IF NOT EXISTS public.nfs_cluster ("
                        + "id bigint DEFAULT nextval('public.nfs_cluster_id_seq'::regclass) NOT NULL,"
                        + "name character varying(128) NOT NULL,"
                        + "lane_key character varying(64) NOT NULL,"
                        + "control_plane_id bigint,"
                        + "primary_node_id bigint,"
                        + "standby_node_id bigint,"
                        + "mount_root character varying(256),"
                        + "nfs_export character varying(256),"
                        + "nfs_mount_opts character varying(128),"
                        + "is_active boolean DEFAULT false NOT NULL,"
                        + "status character varying(32) DEFAULT 'active',"
                        + "remark character varying(256),"
                        + "creator character varying(64),"
                        + "create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,"
                        + "updater character varying(64),"
                        + "update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,"
                        + "deleted smallint DEFAULT 0 NOT NULL,"
                        + "CONSTRAINT nfs_cluster_pkey PRIMARY KEY (id)"
                        + ");"
                        + "CREATE SEQUENCE IF NOT EXISTS public.nfs_cluster_bridge_id_seq START WITH 1 INCREMENT BY 1;"
                        + "CREATE TABLE IF NOT EXISTS public.nfs_cluster_bridge ("
                        + "id bigint DEFAULT nextval('public.nfs_cluster_bridge_id_seq'::regclass) NOT NULL,"
                        + "name character varying(128),"
                        + "source_cluster_id bigint NOT NULL,"
                        + "target_cluster_id bigint NOT NULL,"
                        + "source_rel_paths character varying(512),"
                        + "target_rel_path character varying(256),"
                        + "schedule_cron character varying(64),"
                        + "enabled boolean DEFAULT true NOT NULL,"
                        + "status character varying(32) DEFAULT 'idle',"
                        + "last_run_at timestamp without time zone,"
                        + "last_success boolean,"
                        + "last_message character varying(1024),"
                        + "creator character varying(64),"
                        + "create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,"
                        + "updater character varying(64),"
                        + "update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,"
                        + "deleted smallint DEFAULT 0 NOT NULL,"
                        + "CONSTRAINT nfs_cluster_bridge_pkey PRIMARY KEY (id)"
                        + ");"
        );
    }
}
