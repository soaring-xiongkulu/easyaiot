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

@Repository
@RequiredArgsConstructor
public class ScenarioPoseEntryRepository {

    private final JdbcTemplate jdbc;

    public List<Map<String, Object>> listByLibrary(int libraryId, String search) {
        StringBuilder sql = new StringBuilder("SELECT * FROM scenario_pose_entry WHERE library_id = ?");
        List<Object> args = new ArrayList<>();
        args.add(libraryId);
        if (search != null && !search.isBlank()) {
            sql.append(" AND name ILIKE ?");
            args.add("%" + search.trim() + "%");
        }
        sql.append(" ORDER BY id DESC");
        return jdbc.query(sql.toString(), this::mapEntry, args.toArray());
    }

    public List<Map<String, Object>> listEnabledByLibrary(int libraryId) {
        return jdbc.query(
                "SELECT * FROM scenario_pose_entry WHERE library_id = ? AND is_enabled = true ORDER BY id",
                this::mapEntry,
                libraryId
        );
    }

    public List<String> listImagePathsByLibrary(int libraryId) {
        return jdbc.query(
                "SELECT image_path FROM scenario_pose_entry WHERE library_id = ? AND image_path IS NOT NULL",
                (rs, rowNum) -> rs.getString("image_path"),
                libraryId
        );
    }

    public Optional<Map<String, Object>> findById(int entryId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM scenario_pose_entry WHERE id = ?",
                this::mapEntry,
                entryId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insert(int libraryId, String name, String sourceType, String imagePath, String imageUrl,
                      String keypointsJson, String featureVectorJson, String extraRulesJson,
                      String remark, boolean isEnabled) {
        Integer id = jdbc.queryForObject(
                """
                INSERT INTO scenario_pose_entry (
                  library_id, name, source_type, image_path, image_url,
                  keypoints, feature_vector, keypoint_visibility_min,
                  extra_rules, remark, is_enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 0.3, ?, ?, ?, NOW(), NOW())
                RETURNING id
                """,
                Integer.class,
                libraryId, name, sourceType, imagePath, imageUrl,
                keypointsJson, featureVectorJson, extraRulesJson, remark, isEnabled
        );
        return id != null ? id : 0;
    }

    public void update(int entryId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE scenario_pose_entry SET ");
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
        args.add(entryId);
        jdbc.update(sql.toString(), args.toArray());
    }

    public void delete(int entryId) {
        jdbc.update("DELETE FROM scenario_pose_entry WHERE id = ?", entryId);
    }

    private Map<String, Object> mapEntry(ResultSet rs, int rowNum) throws SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("library_id", rs.getInt("library_id"));
        row.put("name", rs.getString("name"));
        row.put("source_type", rs.getString("source_type"));
        row.put("image_path", rs.getString("image_path"));
        row.put("image_url", rs.getString("image_url"));
        row.put("keypoints", JsonFields.parseJsonObject(rs.getString("keypoints")));
        row.put("feature_vector", JsonFields.parseJsonObject(rs.getString("feature_vector")));
        row.put("keypoint_visibility_min", rs.getDouble("keypoint_visibility_min"));
        row.put("extra_rules", JsonFields.parseJsonObject(rs.getString("extra_rules")));
        row.put("remark", rs.getString("remark"));
        row.put("is_enabled", rs.getBoolean("is_enabled"));
        if (rs.getTimestamp("created_at") != null) {
            row.put("created_at", rs.getTimestamp("created_at").toInstant().toString());
        }
        if (rs.getTimestamp("updated_at") != null) {
            row.put("updated_at", rs.getTimestamp("updated_at").toInstant().toString());
        }
        return row;
    }
}
