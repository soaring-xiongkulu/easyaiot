package com.basiclab.iot.video.dal;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class AlertRepository {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");
    private static final DateTimeFormatter WALL = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final JdbcTemplate jdbc;

    public long insertAlert(Map<String, Object> alertData, Long taskId, String taskName) {
        LocalDateTime alertTime = parseTime(alertData.get("time"));
        String information = alertData.get("information") != null ? String.valueOf(alertData.get("information")) : null;
        String imageUrl = firstString(alertData, "image_url", "imageUrl");
        Long id = jdbc.queryForObject(
                """
                INSERT INTO alert (
                  object, event, region, device_id, device_name, information, time,
                  image_path, image_url, record_path, task_id, task_name, task_type, correlation_id,
                  notification_sent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                Long.class,
                String.valueOf(alertData.get("object")),
                String.valueOf(alertData.get("event")),
                alertData.get("region") != null ? String.valueOf(alertData.get("region")) : null,
                String.valueOf(alertData.get("device_id")),
                String.valueOf(alertData.get("device_name")),
                information,
                Timestamp.valueOf(alertTime),
                alertData.get("image_path") != null ? String.valueOf(alertData.get("image_path")) : null,
                imageUrl,
                alertData.get("record_path") != null ? String.valueOf(alertData.get("record_path")) : null,
                taskId,
                taskName,
                alertData.get("task_type") != null ? String.valueOf(alertData.get("task_type")) : "realtime",
                firstString(alertData, "correlation_id", "correlationId"),
                false
        );
        return id != null ? id : 0L;
    }

    public Optional<Map<String, Object>> findById(long id) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "SELECT * FROM alert WHERE id = ?", id);
        if (rows.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(toApiMap(rows.get(0)));
    }

    public Map<String, Object> list(Map<String, String> args) {
        StringBuilder where = new StringBuilder();
        List<Object> params = new ArrayList<>();
        appendListFilters(where, params, args, true);

        long total = countWhere(where.toString(), params);

        String orderLimit = " ORDER BY time DESC";
        Integer pageSize = parsePositiveInt(args.get("pageSize"));
        if (pageSize != null) {
            int pageNo = parsePositiveInt(args.get("pageNo")) != null ? parsePositiveInt(args.get("pageNo")) : 1;
            int offset = Math.max(0, (pageNo - 1) * pageSize);
            orderLimit += " LIMIT ? OFFSET ?";
            List<Object> pageParams = new ArrayList<>(params);
            pageParams.add(pageSize);
            pageParams.add(offset);
            List<Map<String, Object>> rows = jdbc.queryForList(
                    "SELECT * FROM alert" + where + orderLimit, pageParams.toArray());
            return Map.of(
                    "alert_list", rows.stream().map(this::toApiMap).toList(),
                    "total", total
            );
        }

        List<Map<String, Object>> rows = jdbc.queryForList(
                "SELECT * FROM alert" + where + orderLimit, params.toArray());
        return Map.of(
                "alert_list", rows.stream().map(this::toApiMap).toList(),
                "total", (long) rows.size()
        );
    }

    public Map<String, Object> count(Map<String, String> args) {
        StringBuilder where = new StringBuilder();
        List<Object> params = new ArrayList<>();
        appendListFilters(where, params, args, true);

        String group = args.get("group");
        if (group != null && !group.isBlank()) {
            String groupExpr;
            switch (group.trim()) {
                case "date" -> groupExpr = "CAST(time AS date)";
                case "device" -> groupExpr = "device_id";
                case "object" -> groupExpr = "object";
                default -> {
                    return Map.of("count_list", List.of(), "total_count", 0);
                }
            }
            List<Map<String, Object>> grouped = jdbc.queryForList(
                    "SELECT " + groupExpr + " AS value, COUNT(*) AS count FROM alert"
                            + where + " GROUP BY " + groupExpr,
                    params.toArray());
            List<Map<String, Object>> countList = new ArrayList<>();
            long totalCount = 0;
            for (Map<String, Object> row : grouped) {
                Object value = row.get("value");
                if (value instanceof java.sql.Date d) {
                    value = d.toLocalDate().toString();
                }
                long c = ((Number) row.get("count")).longValue();
                totalCount += c;
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("value", value);
                item.put("count", c);
                countList.add(item);
            }
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("count_list", countList);
            out.put("total_count", totalCount);
            return out;
        }

        long total = countWhere(where.toString(), params);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("count_list", null);
        out.put("total_count", total);
        return out;
    }

    public List<Map<String, Object>> listByCorrelationId(String correlationId) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "SELECT * FROM alert WHERE correlation_id = ? ORDER BY id ASC",
                correlationId);
        return rows.stream().map(this::toApiMap).toList();
    }

    public long countAll() {
        Long n = jdbc.queryForObject("SELECT COUNT(*) FROM alert", Long.class);
        return n != null ? n : 0L;
    }

    public long countSince(LocalDateTime since) {
        Long n = jdbc.queryForObject(
                "SELECT COUNT(*) FROM alert WHERE time >= ?",
                Long.class,
                Timestamp.valueOf(since));
        return n != null ? n : 0L;
    }

    public int deleteAll() {
        Integer n = jdbc.queryForObject("SELECT COUNT(*) FROM alert", Integer.class);
        jdbc.update("DELETE FROM alert");
        return n != null ? n : 0;
    }

    public int deleteByObjectEquals(String taskName) {
        Integer n = jdbc.queryForObject(
                "SELECT COUNT(*) FROM alert WHERE object = ?",
                Integer.class,
                taskName);
        jdbc.update("DELETE FROM alert WHERE object = ?", taskName);
        return n != null ? n : 0;
    }

    public Optional<Map<String, Object>> findNearestPlayback(String deviceId, LocalDateTime alertTime, int timeRangeSec) {
        int extended = Math.max(timeRangeSec + 120, 300);
        LocalDateTime start = alertTime.minusSeconds(extended);
        LocalDateTime end = alertTime.plusSeconds(extended);
        List<Map<String, Object>> rows = jdbc.queryForList(
                """
                SELECT id, file_path, event_time, device_id, device_name, duration
                FROM playback
                WHERE device_id = ? AND event_time >= ? AND event_time <= ?
                ORDER BY ABS(EXTRACT(EPOCH FROM (event_time - ?::timestamp))) ASC
                LIMIT 5
                """,
                deviceId,
                Timestamp.valueOf(start),
                Timestamp.valueOf(end),
                Timestamp.valueOf(alertTime));
        if (rows.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(rows.get(0));
    }

    private long countWhere(String where, List<Object> params) {
        Long n = jdbc.queryForObject("SELECT COUNT(*) FROM alert" + where, Long.class, params.toArray());
        return n != null ? n : 0L;
    }

    private void appendListFilters(
            StringBuilder where,
            List<Object> params,
            Map<String, String> args,
            boolean requireImageUrl) {
        where.append(" WHERE 1=1");
        if (requireImageUrl) {
            where.append(" AND image_url IS NOT NULL AND TRIM(image_url) <> ''");
        }
        addEq(where, params, "object", args.get("object"));
        addEq(where, params, "event", args.get("event"));
        addEq(where, params, "device_id", args.get("device_id"));
        addEq(where, params, "task_type", args.get("task_type"));
        String correlation = firstNonBlank(args.get("correlation_id"), args.get("correlationId"));
        addEq(where, params, "correlation_id", correlation);
        if (args.get("task_id") != null && !args.get("task_id").isBlank()) {
            try {
                where.append(" AND task_id = ?");
                params.add(Long.parseLong(args.get("task_id").trim()));
            } catch (NumberFormatException ignored) {
                // skip invalid
            }
        }
        if (args.get("task_name") != null && !args.get("task_name").isBlank()) {
            where.append(" AND task_name ILIKE ?");
            params.add("%" + args.get("task_name").trim() + "%");
        }
        if (args.get("business_tags") != null && !args.get("business_tags").isBlank()) {
            for (String tag : args.get("business_tags").split(",")) {
                String t = tag.trim();
                if (!t.isEmpty()) {
                    where.append(" AND business_tags ILIKE ?");
                    params.add("%" + t + "%");
                }
            }
        }
        LocalDateTime begin = parseOptionalDateTime(args.get("begin_datetime"));
        if (begin != null) {
            where.append(" AND time >= ?");
            params.add(Timestamp.valueOf(begin));
        }
        LocalDateTime end = parseOptionalDateTime(args.get("end_datetime"));
        if (end != null) {
            where.append(" AND time <= ?");
            params.add(Timestamp.valueOf(end));
        }
    }

    private void addEq(StringBuilder where, List<Object> params, String column, String value) {
        if (value != null && !value.isBlank()) {
            where.append(" AND ").append(column).append(" = ?");
            params.add(value.trim());
        }
    }

    private Map<String, Object> toApiMap(Map<String, Object> row) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", row.get("id"));
        out.put("object", row.get("object"));
        out.put("event", row.get("event"));
        out.put("region", row.get("region"));
        out.put("device_id", row.get("device_id"));
        out.put("device_name", row.get("device_name"));
        out.put("image_path", row.get("image_path"));
        out.put("record_path", row.get("record_path"));
        out.put("task_id", row.get("task_id"));
        out.put("task_name", row.get("task_name"));
        out.put("edge_node_id", row.get("edge_node_id"));
        out.put("edge_node_name", row.get("edge_node_name"));
        out.put("edge_node_host", row.get("edge_node_host"));
        out.put("node_id", row.get("node_id"));
        out.put("information", parseJsonMaybe(row.get("information")));
        Object taskType = row.get("task_type");
        out.put("task_type", taskType != null && !String.valueOf(taskType).isBlank()
                ? String.valueOf(taskType) : "realtime");
        Object time = row.get("time");
        if (time instanceof Timestamp ts) {
            out.put("time", ts.toLocalDateTime().format(WALL));
        } else {
            out.put("time", time);
        }
        out.put("notify_users", parseJsonMaybe(row.get("notify_users")));
        out.put("channels", parseJsonMaybe(row.get("channels")));
        out.put("notification_sent", Boolean.TRUE.equals(row.get("notification_sent")));
        Object sentTime = row.get("notification_sent_time");
        if (sentTime instanceof Timestamp ts) {
            out.put("notification_sent_time", ts.toLocalDateTime().format(WALL));
        } else {
            out.put("notification_sent_time", null);
        }
        out.put("image_url", row.get("image_url") != null ? String.valueOf(row.get("image_url")) : "");
        out.put("business_tags", parseJsonList(row.get("business_tags")));
        out.put("correlation_id", row.get("correlation_id"));
        return out;
    }

    private Object parseJsonMaybe(Object raw) {
        if (raw == null) {
            return null;
        }
        if (!(raw instanceof String s)) {
            return raw;
        }
        String trimmed = s.trim();
        if (trimmed.isEmpty()) {
            return null;
        }
        if ((trimmed.startsWith("{") && trimmed.endsWith("}"))
                || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
            try {
                return new com.fasterxml.jackson.databind.ObjectMapper().readValue(trimmed, Object.class);
            } catch (Exception ignored) {
                return raw;
            }
        }
        return raw;
    }

    private List<Object> parseJsonList(Object raw) {
        Object parsed = parseJsonMaybe(raw);
        if (parsed instanceof List<?> list) {
            return new ArrayList<>(list);
        }
        return List.of();
    }

    private LocalDateTime parseTime(Object raw) {
        if (raw == null) {
            return LocalDateTime.now(SHANGHAI);
        }
        if (raw instanceof LocalDateTime ldt) {
            return ldt;
        }
        String s = String.valueOf(raw).trim();
        if (s.isEmpty()) {
            return LocalDateTime.now(SHANGHAI);
        }
        LocalDateTime parsed = parseOptionalDateTime(s);
        return parsed != null ? parsed : LocalDateTime.now(SHANGHAI);
    }

    private LocalDateTime parseOptionalDateTime(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        String s = raw.trim();
        for (String fmt : List.of(
                "yyyy-MM-dd HH:mm:ss",
                "yyyy-MM-dd HH:mm:ss.SSS",
                "yyyy-MM-dd'T'HH:mm:ss",
                "yyyy-MM-dd'T'HH:mm:ss.SSS")) {
            try {
                return LocalDateTime.parse(s.length() == 19 && s.contains(" ")
                        ? s.replace(" ", "T")
                        : s.contains(" ")
                        ? LocalDateTime.parse(s, DateTimeFormatter.ofPattern(fmt)).toString()
                        : s,
                        DateTimeFormatter.ISO_LOCAL_DATE_TIME);
            } catch (Exception ignored) {
                // try next
            }
            try {
                return LocalDateTime.parse(s, DateTimeFormatter.ofPattern(fmt));
            } catch (Exception ignored) {
                // try next
            }
        }
        try {
            return LocalDateTime.parse(s.replace(" ", "T"));
        } catch (Exception ignored) {
            return null;
        }
    }

    public int patchAlertsRecord(String deviceId, String eventTime, int duration, String filePath,
                                 boolean allowLocalPath) {
        if (deviceId == null || deviceId.isBlank() || eventTime == null || eventTime.isBlank()) {
            return 0;
        }
        if (filePath == null || filePath.isBlank()) {
            return 0;
        }
        boolean minioPath = filePath.startsWith("/api/v1/buckets/") && filePath.contains("/objects/download");
        if (!minioPath && !allowLocalPath) {
            return 0;
        }
        LocalDateTime begin = LocalDateTime.parse(eventTime.trim(), WALL);
        LocalDateTime legacyStart = begin.minusSeconds(Math.max(duration, 1));
        LocalDateTime end = begin.plusSeconds(Math.max(duration, 1));
        return jdbc.update(
                """
                UPDATE alert SET record_path = ?
                WHERE device_id = ?
                  AND time >= ? AND time <= ?
                  AND (record_path IS NULL OR TRIM(record_path) = '')
                """,
                filePath,
                deviceId,
                Timestamp.valueOf(legacyStart),
                Timestamp.valueOf(end)
        );
    }

    private Integer parsePositiveInt(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        try {
            int v = Integer.parseInt(raw.trim());
            return v > 0 ? v : null;
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static String firstString(Map<String, Object> data, String... keys) {
        for (String key : keys) {
            Object v = data.get(key);
            if (v != null && !String.valueOf(v).isBlank()) {
                return String.valueOf(v);
            }
        }
        return null;
    }

    private static String firstNonBlank(String a, String b) {
        if (a != null && !a.isBlank()) {
            return a;
        }
        if (b != null && !b.isBlank()) {
            return b;
        }
        return null;
    }
}
