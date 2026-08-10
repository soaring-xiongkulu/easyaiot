package com.basiclab.iot.video.dal;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Map;

@Repository
@RequiredArgsConstructor
public class PlaybackRepository {

    private final JdbcTemplate jdbc;

    public long count(String deviceId, String search) {
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM playback WHERE 1=1");
        List<Object> args = buildFilters(sql, deviceId, search);
        Long total = jdbc.queryForObject(sql.toString(), Long.class, args.toArray());
        return total != null ? total : 0L;
    }

    public List<Map<String, Object>> list(int pageNo, int pageSize, String deviceId, String search) {
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        StringBuilder sql = new StringBuilder(
                "SELECT id, file_path, event_time, device_id, device_name, duration, "
                        + "thumbnail_path, file_size, created_at, updated_at FROM playback WHERE 1=1"
        );
        List<Object> args = buildFilters(sql, deviceId, search);
        sql.append(" ORDER BY event_time DESC LIMIT ? OFFSET ?");
        args.add(pageSize);
        args.add(offset);
        return jdbc.queryForList(sql.toString(), args.toArray());
    }

    private List<Object> buildFilters(StringBuilder sql, String deviceId, String search) {
        List<Object> args = new java.util.ArrayList<>();
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append(" AND device_id = ?");
            args.add(deviceId.trim());
        }
        if (search != null && !search.isBlank()) {
            String like = "%" + search.trim() + "%";
            sql.append(" AND (device_name ILIKE ? OR device_id ILIKE ? OR file_path ILIKE ?)");
            args.add(like);
            args.add(like);
            args.add(like);
        }
        return args;
    }
}
