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
public class PlateLibraryRepository {

    private final JdbcTemplate jdbc;

    public List<Map<String, Object>> findEnabledByIds(List<Integer> ids) {
        if (ids == null || ids.isEmpty()) {
            return List.of();
        }
        String placeholders = String.join(",", ids.stream().map(id -> "?").toList());
        List<Object> args = new ArrayList<>(ids);
        return jdbc.query(
                "SELECT id, name, code, business_tags, is_enabled FROM plate_library WHERE id IN (" + placeholders + ") AND is_enabled = true ORDER BY id",
                (rs, rowNum) -> {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("id", rs.getInt("id"));
                    row.put("name", rs.getString("name"));
                    row.put("code", rs.getString("code"));
                    row.put("business_tags", rs.getString("business_tags"));
                    return row;
                },
                args.toArray()
        );
    }

    public List<Map<String, Object>> list(String search, Boolean isEnabled) {
        StringBuilder sql = new StringBuilder("SELECT * FROM plate_library WHERE 1=1");
        List<Object> args = new ArrayList<>();
        if (search != null && !search.isBlank()) {
            sql.append(" AND (name ILIKE ? OR code ILIKE ? OR description ILIKE ?)");
            String like = "%" + search.trim() + "%";
            args.add(like);
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
                "SELECT * FROM plate_library WHERE id = ?",
                this::mapLibrary,
                libraryId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insert(String name, String code, String businessTagsJson, String description, boolean isEnabled) {
        Integer id = jdbc.queryForObject(
                """
                INSERT INTO plate_library (name, code, business_tags, description, is_enabled, plate_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 0, NOW(), NOW())
                RETURNING id
                """,
                Integer.class,
                name, code, businessTagsJson, description, isEnabled
        );
        return id != null ? id : 0;
    }

    public void update(int libraryId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE plate_library SET ");
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
        jdbc.update("DELETE FROM plate_library WHERE id = ?", libraryId);
    }

    public void refreshPlateCount(int libraryId) {
        jdbc.update(
                """
                UPDATE plate_library SET plate_count = (
                  SELECT COUNT(*) FROM plate_entry WHERE library_id = ?
                ), updated_at = NOW() WHERE id = ?
                """,
                libraryId, libraryId
        );
    }

    public String generateCode() {
        for (int i = 0; i < 20; i++) {
            String code = UUID.randomUUID().toString().replace("-", "").substring(0, 12).toUpperCase();
            Long count = jdbc.queryForObject("SELECT COUNT(*) FROM plate_library WHERE code = ?", Long.class, code);
            if (count == null || count == 0) {
                return code;
            }
        }
        throw new IllegalStateException("无法生成唯一的车牌库编码");
    }

    private Map<String, Object> mapLibrary(ResultSet rs, int rowNum) throws SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("name", rs.getString("name"));
        row.put("code", rs.getString("code"));
        row.put("business_tags", JsonFields.parseJsonList(rs.getString("business_tags")));
        row.put("description", rs.getString("description"));
        row.put("is_enabled", rs.getBoolean("is_enabled"));
        row.put("plate_count", rs.getInt("plate_count"));
        if (rs.getTimestamp("created_at") != null) {
            row.put("created_at", rs.getTimestamp("created_at").toInstant().toString());
        }
        if (rs.getTimestamp("updated_at") != null) {
            row.put("updated_at", rs.getTimestamp("updated_at").toInstant().toString());
        }
        return row;
    }
}
