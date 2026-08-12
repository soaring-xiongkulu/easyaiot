package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.support.SpaceNodeSupport;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class RecordSpaceRepository {

    private static final String LIST_SQL = """
            SELECT s.*, d.directory_id, d.nvr_id, d.source AS device_source,
                   dd.record_save_time AS directory_save_time
            FROM record_space s
            LEFT JOIN device d ON d.id = s.device_id
            LEFT JOIN device_directory dd ON dd.id = d.directory_id
            WHERE s.device_id IS NOT NULL
              AND d.nvr_id IS NULL
              AND (d.source IS NULL OR d.source NOT ILIKE 'gb28181://%%')
            """;

    private final JdbcTemplate jdbc;

    public long countDirectSpaces() {
        Long total = jdbc.queryForObject(
                """
                SELECT COUNT(*) FROM record_space s
                LEFT JOIN device d ON d.id = s.device_id
                WHERE d.nvr_id IS NULL
                  AND (d.source IS NULL OR d.source NOT ILIKE 'gb28181://%')
                """,
                Long.class
        );
        return total != null ? total : 0L;
    }

    public List<Map<String, Object>> listRootNodes(int pageNo, int pageSize) {
        List<Map<String, Object>> nodes = jdbc.query(LIST_SQL, (rs, rowNum) ->
                SpaceNodeSupport.buildSpaceNode(rs, "record_space", 1));
        nodes.sort(SpaceNodeSupport.spaceNameComparator());
        return SpaceNodeSupport.paginate(nodes, pageNo, pageSize);
    }

    public long countAllRootNodes() {
        return jdbc.query(LIST_SQL, (rs, rowNum) ->
                SpaceNodeSupport.buildSpaceNode(rs, "record_space", 1)).size();
    }

    public Optional<Map<String, Object>> findById(int spaceId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM record_space WHERE id = ?",
                (rs, rowNum) -> spaceDetailRow(rs),
                spaceId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public Optional<Map<String, Object>> findByDeviceId(String deviceId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM record_space WHERE device_id = ? LIMIT 1",
                (rs, rowNum) -> spaceDetailRow(rs),
                deviceId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public void updateFields(int spaceId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE record_space SET updated_at = NOW()");
        List<Object> args = new ArrayList<>();
        for (Map.Entry<String, Object> entry : fields.entrySet()) {
            sql.append(", ").append(entry.getKey()).append(" = ?");
            args.add(entry.getValue());
        }
        sql.append(" WHERE id = ?");
        args.add(spaceId);
        jdbc.update(sql.toString(), args.toArray());
    }

    public void delete(int spaceId) {
        jdbc.update("DELETE FROM record_space WHERE id = ?", spaceId);
    }

    public int updateSaveTimeForDirectory(int directoryId, int saveTimeHours) {
        return jdbc.update(
                """
                UPDATE record_space s
                SET save_time = ?, updated_at = NOW()
                FROM device d
                WHERE s.device_id = d.id
                  AND d.directory_id = ?
                  AND COALESCE(s.save_time_custom, false) = false
                """,
                saveTimeHours,
                directoryId
        );
    }

    public List<Map<String, Object>> listAllSpaces() {
        return jdbc.query("SELECT * FROM record_space", (rs, rowNum) -> spaceDetailRow(rs));
    }

    private static Map<String, Object> spaceDetailRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("space_name", rs.getString("space_name"));
        row.put("space_code", rs.getString("space_code"));
        row.put("bucket_name", rs.getString("bucket_name"));
        row.put("save_mode", rs.getInt("save_mode"));
        row.put("save_time", rs.getInt("save_time"));
        row.put("save_time_custom", rs.getBoolean("save_time_custom"));
        row.put("description", rs.getString("description"));
        row.put("device_id", rs.getString("device_id"));
        row.put("created_at", rs.getTimestamp("created_at") != null ? rs.getTimestamp("created_at").toInstant().toString() : null);
        row.put("updated_at", rs.getTimestamp("updated_at") != null ? rs.getTimestamp("updated_at").toInstant().toString() : null);
        return row;
    }
}
