package com.basiclab.iot.video.dal;

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
public class FaceEntryRepository {

    private final JdbcTemplate jdbc;

    public List<Map<String, Object>> listByLibrary(int libraryId, String search) {
        StringBuilder sql = new StringBuilder("SELECT * FROM face_entry WHERE library_id = ?");
        List<Object> args = new ArrayList<>();
        args.add(libraryId);
        if (search != null && !search.isBlank()) {
            sql.append(" AND (person_name ILIKE ? OR person_code ILIKE ? OR remark ILIKE ?)");
            String like = "%" + search.trim() + "%";
            args.add(like);
            args.add(like);
            args.add(like);
        }
        sql.append(" ORDER BY id DESC");
        return jdbc.query(sql.toString(), this::mapEntry, args.toArray());
    }

    public Optional<Map<String, Object>> findById(int entryId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM face_entry WHERE id = ?",
                this::mapEntry,
                entryId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insert(int libraryId, Integer personId, String personName, String personCode,
                      String imagePath, String imageUrl, String remark, boolean isEnabled) {
        Integer id = jdbc.queryForObject(
                """
                INSERT INTO face_entry (library_id, person_id, person_name, person_code, image_path, image_url, remark, is_enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
                RETURNING id
                """,
                Integer.class,
                libraryId, personId, personName, personCode, imagePath, imageUrl, remark, isEnabled
        );
        return id != null ? id : 0;
    }

    public void update(int entryId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE face_entry SET ");
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
        jdbc.update("DELETE FROM face_entry WHERE id = ?", entryId);
    }

    public void deleteByPerson(int personId) {
        jdbc.update("DELETE FROM face_entry WHERE person_id = ?", personId);
    }

    public int countByPerson(int personId) {
        Long count = jdbc.queryForObject("SELECT COUNT(*) FROM face_entry WHERE person_id = ?", Long.class, personId);
        return count != null ? count.intValue() : 0;
    }

    private Map<String, Object> mapEntry(ResultSet rs, int rowNum) throws SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("library_id", rs.getInt("library_id"));
        row.put("person_id", (Integer) rs.getObject("person_id"));
        row.put("person_name", rs.getString("person_name"));
        row.put("person_code", rs.getString("person_code"));
        row.put("image_path", rs.getString("image_path"));
        row.put("image_url", rs.getString("image_url"));
        row.put("milvus_id", rs.getString("milvus_id"));
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
