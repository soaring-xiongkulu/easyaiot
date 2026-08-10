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
public class FacePersonRepository {

    private final JdbcTemplate jdbc;
    private final FaceEntryRepository faceEntryRepository;

    public List<Map<String, Object>> listByLibrary(int libraryId, String search, int page, int pageSize) {
        int offset = Math.max(0, (page - 1) * pageSize);
        StringBuilder sql = new StringBuilder("SELECT * FROM face_person WHERE library_id = ?");
        List<Object> args = new ArrayList<>();
        args.add(libraryId);
        if (search != null && !search.isBlank()) {
            sql.append(" AND (person_name ILIKE ? OR person_code ILIKE ?)");
            String like = "%" + search.trim() + "%";
            args.add(like);
            args.add(like);
        }
        sql.append(" ORDER BY id DESC LIMIT ? OFFSET ?");
        args.add(pageSize);
        args.add(offset);
        return jdbc.query(sql.toString(), this::mapPerson, args.toArray());
    }

    public long countByLibrary(int libraryId, String search) {
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM face_person WHERE library_id = ?");
        List<Object> args = new ArrayList<>();
        args.add(libraryId);
        if (search != null && !search.isBlank()) {
            sql.append(" AND (person_name ILIKE ? OR person_code ILIKE ?)");
            String like = "%" + search.trim() + "%";
            args.add(like);
            args.add(like);
        }
        Long count = jdbc.queryForObject(sql.toString(), Long.class, args.toArray());
        return count != null ? count : 0L;
    }

    public Optional<Map<String, Object>> findById(int personId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM face_person WHERE id = ?",
                this::mapPerson,
                personId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insert(int libraryId, String personName, String personCode, Integer coverEntryId, boolean isEnabled) {
        Integer id = jdbc.queryForObject(
                """
                INSERT INTO face_person (library_id, person_name, person_code, cover_entry_id, is_enabled, face_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 0, NOW(), NOW())
                RETURNING id
                """,
                Integer.class,
                libraryId, personName, personCode, coverEntryId, isEnabled
        );
        return id != null ? id : 0;
    }

    public void update(int personId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE face_person SET ");
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
        args.add(personId);
        jdbc.update(sql.toString(), args.toArray());
    }

    public void delete(int personId) {
        faceEntryRepository.deleteByPerson(personId);
        jdbc.update("DELETE FROM face_person WHERE id = ?", personId);
    }

    public int batchDelete(List<Integer> personIds) {
        if (personIds == null || personIds.isEmpty()) {
            return 0;
        }
        int deleted = 0;
        for (Integer id : personIds) {
            if (id != null) {
                delete(id);
                deleted++;
            }
        }
        return deleted;
    }

    public void refreshFaceCount(int personId) {
        int count = faceEntryRepository.countByPerson(personId);
        jdbc.update("UPDATE face_person SET face_count = ?, updated_at = NOW() WHERE id = ?", count, personId);
    }

    public Map<String, Object> enrichPerson(Map<String, Object> person, boolean includeEntries) {
        Map<String, Object> data = new LinkedHashMap<>(person);
        Integer coverEntryId = (Integer) person.get("cover_entry_id");
        if (coverEntryId != null) {
            faceEntryRepository.findById(coverEntryId)
                    .ifPresent(entry -> data.put("cover_image_url", entry.get("image_url")));
        }
        if (includeEntries) {
            Integer personId = (Integer) person.get("id");
            data.put("entries", faceEntryRepository.listByLibrary((Integer) person.get("library_id"), null).stream()
                    .filter(e -> personId.equals(e.get("person_id")))
                    .toList());
        }
        return data;
    }

    private Map<String, Object> mapPerson(ResultSet rs, int rowNum) throws SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("library_id", rs.getInt("library_id"));
        row.put("person_name", rs.getString("person_name"));
        row.put("person_code", rs.getString("person_code"));
        row.put("cover_entry_id", (Integer) rs.getObject("cover_entry_id"));
        row.put("is_enabled", rs.getBoolean("is_enabled"));
        row.put("face_count", rs.getInt("face_count"));
        if (rs.getTimestamp("created_at") != null) {
            row.put("created_at", rs.getTimestamp("created_at").toInstant().toString());
        }
        if (rs.getTimestamp("updated_at") != null) {
            row.put("updated_at", rs.getTimestamp("updated_at").toInstant().toString());
        }
        return row;
    }
}
