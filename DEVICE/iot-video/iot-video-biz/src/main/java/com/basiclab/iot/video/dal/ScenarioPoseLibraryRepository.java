package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.support.JsonFields;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Repository
@RequiredArgsConstructor
public class ScenarioPoseLibraryRepository {

    private final JdbcTemplate jdbc;

    public List<Map<String, Object>> list(String search, Boolean isEnabled) {
        StringBuilder sql = new StringBuilder("SELECT * FROM scenario_pose_library WHERE 1=1");
        List<Object> args = new ArrayList<>();
        if (search != null && !search.isBlank()) {
            sql.append(" AND (name ILIKE ? OR code ILIKE ?)");
            String like = "%" + search.trim() + "%";
            args.add(like);
            args.add(like);
        }
        if (isEnabled != null) {
            sql.append(" AND is_enabled = ?");
            args.add(isEnabled);
        }
        sql.append(" ORDER BY id DESC");
        return jdbc.query(sql.toString(), this::mapLibrary, args.toArray());
    }

    public Optional<Map<String, Object>> findById(int libraryId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM scenario_pose_library WHERE id = ?",
                this::mapLibrary,
                libraryId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insert(String name, String code, String sceneCategory, String businessTagsJson,
                      String description, double similarityThreshold, String matchMode,
                      String intentEvent, String intentObject, String alertLevel, boolean isEnabled) {
        Integer id = jdbc.queryForObject(
                """
                INSERT INTO scenario_pose_library (
                  name, code, scene_category, business_tags, description,
                  similarity_threshold, match_mode, intent_event, intent_object,
                  alert_level, is_enabled, entry_count, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NOW(), NOW())
                RETURNING id
                """,
                Integer.class,
                name, code, sceneCategory, businessTagsJson, description,
                similarityThreshold, matchMode, intentEvent, intentObject,
                alertLevel, isEnabled
        );
        return id != null ? id : 0;
    }

    public void update(int libraryId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE scenario_pose_library SET ");
        List<Object> args = new ArrayList<>();
        int i = 0;
        for (Map.Entry<String, Object> entry : fields.entrySet()) {
            if (i++ > 0) {
                sql.append(", ");
            }
            sql.append(entry.getKey()).append(" = ?");
            args.add(entry.getValue());
        }
        sql.append(", updated_at = NOW() WHERE id = ?");
        args.add(libraryId);
        jdbc.update(sql.toString(), args.toArray());
    }

    public void delete(int libraryId) {
        jdbc.update("DELETE FROM scenario_pose_library WHERE id = ?", libraryId);
    }

    public void refreshEntryCount(int libraryId) {
        jdbc.update(
                """
                UPDATE scenario_pose_library SET entry_count = (
                  SELECT COUNT(*) FROM scenario_pose_entry WHERE library_id = ?
                ), updated_at = NOW() WHERE id = ?
                """,
                libraryId, libraryId
        );
    }

    public int countEntries(int libraryId) {
        Long count = jdbc.queryForObject(
                "SELECT COUNT(*) FROM scenario_pose_entry WHERE library_id = ?",
                Long.class,
                libraryId
        );
        return count != null ? count.intValue() : 0;
    }

    public String generateCode() {
        for (int i = 0; i < 20; i++) {
            String code = UUID.randomUUID().toString().replace("-", "").substring(0, 12).toUpperCase();
            Long count = jdbc.queryForObject(
                    "SELECT COUNT(*) FROM scenario_pose_library WHERE code = ?",
                    Long.class,
                    code
            );
            if (count == null || count == 0) {
                return code;
            }
        }
        throw new IllegalStateException("无法生成唯一的场景姿态库编码");
    }

    private Map<String, Object> mapLibrary(ResultSet rs, int rowNum) throws SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("name", rs.getString("name"));
        row.put("code", rs.getString("code"));
        row.put("scene_category", rs.getString("scene_category"));
        row.put("business_tags", JsonFields.parseJsonList(rs.getString("business_tags")));
        row.put("description", rs.getString("description"));
        row.put("similarity_threshold", rs.getDouble("similarity_threshold"));
        row.put("match_mode", rs.getString("match_mode"));
        row.put("intent_event", rs.getString("intent_event"));
        row.put("intent_object", rs.getString("intent_object"));
        row.put("alert_level", rs.getString("alert_level"));
        row.put("is_enabled", rs.getBoolean("is_enabled"));
        row.put("entry_count", rs.getInt("entry_count"));
        if (rs.getTimestamp("created_at") != null) {
            row.put("created_at", rs.getTimestamp("created_at").toInstant().toString());
        }
        if (rs.getTimestamp("updated_at") != null) {
            row.put("updated_at", rs.getTimestamp("updated_at").toInstant().toString());
        }
        return row;
    }
}
