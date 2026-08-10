package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.support.SpaceNodeSupport;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

@Repository
@RequiredArgsConstructor
public class SnapSpaceRepository {

    private static final String LIST_SQL = """
            SELECT s.*, d.directory_id, d.nvr_id, d.source AS device_source,
                   dd.snap_save_time AS directory_save_time
            FROM snap_space s
            LEFT JOIN device d ON d.id = s.device_id
            LEFT JOIN device_directory dd ON dd.id = d.directory_id
            WHERE s.device_id IS NOT NULL
              AND d.nvr_id IS NULL
              AND (d.source IS NULL OR d.source NOT ILIKE 'gb28181://%%')
            """;

    private final JdbcTemplate jdbc;

    public long count() {
        Long total = jdbc.queryForObject(
                """
                SELECT COUNT(*) FROM snap_space s
                LEFT JOIN device d ON d.id = s.device_id
                WHERE s.device_id IS NOT NULL
                  AND d.nvr_id IS NULL
                  AND (d.source IS NULL OR d.source NOT ILIKE 'gb28181://%%')
                """,
                Long.class
        );
        return total != null ? total : 0L;
    }

    public List<Map<String, Object>> listRootNodes(int pageNo, int pageSize) {
        List<Map<String, Object>> nodes = jdbc.query(LIST_SQL, (rs, rowNum) -> {
            Map<String, Object> node = SpaceNodeSupport.buildSpaceNode(rs, "snap_space", 1);
            node.put("task_count", 0);
            return node;
        });
        nodes.sort(SpaceNodeSupport.spaceNameComparator());
        return SpaceNodeSupport.paginate(nodes, pageNo, pageSize);
    }
}
