package com.basiclab.iot.video.support;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class SpaceNodeSupport {

    private SpaceNodeSupport() {
    }

    public static List<Map<String, Object>> paginate(List<Map<String, Object>> nodes, int pageNo, int pageSize) {
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        if (offset >= nodes.size()) {
            return List.of();
        }
        int end = Math.min(nodes.size(), offset + pageSize);
        return nodes.subList(offset, end);
    }

    public static List<Map<String, Object>> rootBreadcrumbs() {
        List<Map<String, Object>> crumbs = new ArrayList<>();
        Map<String, Object> root = new LinkedHashMap<>();
        root.put("key", "root");
        root.put("name", "全部空间");
        crumbs.add(root);
        return crumbs;
    }

    public static Map<String, Object> buildSpaceNode(
            ResultSet rs,
            String spaceTable,
            int directorySaveTimeDefault
    ) throws SQLException {
        Map<String, Object> data = new LinkedHashMap<>();
        int id = rs.getInt("id");
        data.put("id", id);
        data.put("space_name", rs.getString("space_name"));
        data.put("space_code", rs.getString("space_code"));
        data.put("bucket_name", rs.getString("bucket_name"));
        data.put("save_mode", JdbcValues.getInteger(rs, "save_mode"));
        data.put("save_time", JdbcValues.getInteger(rs, "save_time"));
        data.put("save_time_custom", Boolean.TRUE.equals(JdbcValues.getBoolean(rs, "save_time_custom")));
        data.put("description", rs.getString("description"));
        data.put("device_id", rs.getString("device_id"));
        data.put("created_at", formatInstant(rs.getTimestamp("created_at")));
        data.put("updated_at", formatInstant(rs.getTimestamp("updated_at")));

        Integer directoryId = JdbcValues.getInteger(rs, "directory_id");
        int directorySaveTime = JdbcValues.getInteger(rs, "directory_save_time") != null
                ? JdbcValues.getInteger(rs, "directory_save_time")
                : directorySaveTimeDefault;
        data.put("directory_id", directoryId);
        data.put("directory_save_time", directorySaveTime);
        data.put("group_save_time", null);

        boolean saveTimeCustom = Boolean.TRUE.equals(JdbcValues.getBoolean(rs, "save_time_custom"));
        int saveTime = JdbcValues.getInteger(rs, "save_time") != null ? JdbcValues.getInteger(rs, "save_time") : 1;
        data.put("effective_save_time", saveTimeCustom ? saveTime : saveTime);

        data.put("node_type", "space");
        data.put("node_key", "space_" + id);
        data.put("name", data.get("space_name") != null ? data.get("space_name") : "");
        data.put("device_kind", resolveDeviceKind(rs));
        return data;
    }

    public static Comparator<Map<String, Object>> spaceNameComparator() {
        return Comparator
                .comparing((Map<String, Object> m) -> String.valueOf(m.getOrDefault("space_name", "")))
                .thenComparing(m -> ((Number) m.getOrDefault("id", 0)).intValue());
    }

    private static String resolveDeviceKind(ResultSet rs) throws SQLException {
        Object nvrId = rs.getObject("nvr_id");
        if (nvrId != null) {
            return "nvr_channel";
        }
        String source = rs.getString("device_source");
        if (source != null && source.toLowerCase().startsWith("gb28181://")) {
            return "gb28181";
        }
        return "direct";
    }

    private static String formatInstant(Timestamp ts) {
        if (ts == null) {
            return null;
        }
        Instant instant = ts.toInstant();
        return instant.toString();
    }
}
