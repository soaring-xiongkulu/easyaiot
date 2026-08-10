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
public class PlateEntryRepository {

    private final JdbcTemplate jdbc;

    public List<Map<String, Object>> listByLibrary(int libraryId, String search, int page, int pageSize) {
        int offset = Math.max(0, (page - 1) * pageSize);
        StringBuilder sql = new StringBuilder("SELECT * FROM plate_entry WHERE library_id = ?");
        List<Object> args = new ArrayList<>();
        args.add(libraryId);
        if (search != null && !search.isBlank()) {
            sql.append(" AND (plate_no ILIKE ? OR owner_name ILIKE ? OR remark ILIKE ?)");
            String like = "%" + search.trim() + "%";
            args.add(like);
            args.add(like);
            args.add(like);
        }
        sql.append(" ORDER BY id DESC LIMIT ? OFFSET ?");
        args.add(pageSize);
        args.add(offset);
        return jdbc.query(sql.toString(), this::mapEntry, args.toArray());
    }

    public long countByLibrary(int libraryId, String search) {
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM plate_entry WHERE library_id = ?");
        List<Object> args = new ArrayList<>();
        args.add(libraryId);
        if (search != null && !search.isBlank()) {
            sql.append(" AND (plate_no ILIKE ? OR owner_name ILIKE ? OR remark ILIKE ?)");
            String like = "%" + search.trim() + "%";
            args.add(like);
            args.add(like);
            args.add(like);
        }
        Long count = jdbc.queryForObject(sql.toString(), Long.class, args.toArray());
        return count != null ? count : 0L;
    }

    public Optional<Map<String, Object>> findById(int entryId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM plate_entry WHERE id = ?",
                this::mapEntry,
                entryId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insert(int libraryId, String plateNo, String plateColor, String ownerName,
                      String ownerPhone, String imagePath, String imageUrl, String remark, boolean isEnabled) {
        Integer id = jdbc.queryForObject(
                """
                INSERT INTO plate_entry (library_id, plate_no, plate_color, owner_name, owner_phone, image_path, image_url, remark, is_enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
                RETURNING id
                """,
                Integer.class,
                libraryId, plateNo, plateColor, ownerName, ownerPhone, imagePath, imageUrl, remark, isEnabled
        );
        return id != null ? id : 0;
    }

    public void update(int entryId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE plate_entry SET ");
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
        jdbc.update("DELETE FROM plate_entry WHERE id = ?", entryId);
    }

    public int batchDelete(List<Integer> entryIds) {
        if (entryIds == null || entryIds.isEmpty()) {
            return 0;
        }
        int deleted = 0;
        for (Integer id : entryIds) {
            if (id != null) {
                delete(id);
                deleted++;
            }
        }
        return deleted;
    }

    public Optional<Map<String, Object>> findByPlateNo(int libraryId, String plateNo) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM plate_entry WHERE library_id = ? AND UPPER(REPLACE(plate_no, ' ', '')) = ? AND is_enabled = true LIMIT 1",
                this::mapEntry,
                libraryId, plateNo.toUpperCase().replace(" ", "")
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    private Map<String, Object> mapEntry(ResultSet rs, int rowNum) throws SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("library_id", rs.getInt("library_id"));
        row.put("plate_no", rs.getString("plate_no"));
        row.put("plate_color", rs.getString("plate_color"));
        row.put("owner_name", rs.getString("owner_name"));
        row.put("owner_phone", rs.getString("owner_phone"));
        row.put("image_path", rs.getString("image_path"));
        row.put("image_url", rs.getString("image_url"));
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
