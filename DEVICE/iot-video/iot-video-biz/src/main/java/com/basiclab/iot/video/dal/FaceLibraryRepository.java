package com.basiclab.iot.video.dal;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Repository
@RequiredArgsConstructor
public class FaceLibraryRepository {

    private final JdbcTemplate jdbc;

    public List<Map<String, Object>> findEnabledByIds(List<Integer> ids) {
        if (ids == null || ids.isEmpty()) {
            return List.of();
        }
        String placeholders = String.join(",", ids.stream().map(id -> "?").toList());
        List<Object> args = new ArrayList<>(ids);
        return jdbc.query(
                "SELECT id, name, code, is_enabled FROM face_library WHERE id IN (" + placeholders + ") AND is_enabled = true ORDER BY id",
                (rs, rowNum) -> {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("id", rs.getInt("id"));
                    row.put("name", rs.getString("name"));
                    row.put("code", rs.getString("code"));
                    return row;
                },
                args.toArray()
        );
    }
}
