package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.support.JdbcValues;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class DetectionRegionRepository {

    private final JdbcTemplate jdbc;

    public List<Map<String, Object>> listByTaskId(int taskId) {
        return jdbc.query(
                "SELECT * FROM detection_region WHERE task_id = ? ORDER BY sort_order, id",
                (rs, rowNum) -> regionRow(rs),
                taskId
        );
    }

    public Optional<Map<String, Object>> findById(int regionId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM detection_region WHERE id = ?",
                (rs, rowNum) -> regionRow(rs),
                regionId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insert(Map<String, Object> fields) {
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(con -> {
            PreparedStatement ps = con.prepareStatement(
                    """
                    INSERT INTO detection_region (
                        task_id, region_name, region_type, points, image_id,
                        algorithm_type, algorithm_model_id, algorithm_threshold, algorithm_enabled,
                        color, opacity, is_enabled, sort_order
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    Statement.RETURN_GENERATED_KEYS
            );
            int i = 1;
            ps.setInt(i++, intVal(fields.get("task_id")));
            ps.setString(i++, str(fields.get("region_name")));
            ps.setString(i++, strOr(fields.get("region_type"), "polygon"));
            ps.setString(i++, str(fields.get("points")));
            setNullableInt(ps, i++, fields.get("image_id"));
            ps.setString(i++, str(fields.get("algorithm_type")));
            setNullableInt(ps, i++, fields.get("algorithm_model_id"));
            setNullableDouble(ps, i++, fields.get("algorithm_threshold"));
            ps.setBoolean(i++, boolOr(fields.get("algorithm_enabled"), true));
            ps.setString(i++, strOr(fields.get("color"), "#FF5252"));
            ps.setDouble(i++, doubleOr(fields.get("opacity"), 0.3));
            ps.setBoolean(i++, boolOr(fields.get("is_enabled"), true));
            ps.setInt(i, intOr(fields.get("sort_order"), 0));
            return ps;
        }, keyHolder);
        Number key = keyHolder.getKey();
        return key != null ? key.intValue() : 0;
    }

    public void updateFields(int regionId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE detection_region SET updated_at = NOW()");
        List<Object> args = new ArrayList<>();
        for (Map.Entry<String, Object> entry : fields.entrySet()) {
            sql.append(", ").append(entry.getKey()).append(" = ?");
            args.add(entry.getValue());
        }
        sql.append(" WHERE id = ?");
        args.add(regionId);
        jdbc.update(sql.toString(), args.toArray());
    }

    public void delete(int regionId) {
        jdbc.update("DELETE FROM detection_region WHERE id = ?", regionId);
    }

    private static Map<String, Object> regionRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("task_id", rs.getInt("task_id"));
        row.put("region_name", rs.getString("region_name"));
        row.put("region_type", rs.getString("region_type"));
        row.put("points", rs.getString("points"));
        row.put("image_id", JdbcValues.getInteger(rs, "image_id"));
        row.put("algorithm_type", rs.getString("algorithm_type"));
        row.put("algorithm_model_id", JdbcValues.getInteger(rs, "algorithm_model_id"));
        row.put("algorithm_threshold", JdbcValues.getDouble(rs, "algorithm_threshold"));
        row.put("algorithm_enabled", Boolean.TRUE.equals(JdbcValues.getBoolean(rs, "algorithm_enabled")));
        row.put("color", rs.getString("color"));
        row.put("opacity", JdbcValues.getDouble(rs, "opacity"));
        row.put("is_enabled", Boolean.TRUE.equals(JdbcValues.getBoolean(rs, "is_enabled")));
        row.put("sort_order", JdbcValues.getInteger(rs, "sort_order"));
        row.put("created_at", rs.getTimestamp("created_at") != null ? rs.getTimestamp("created_at").toInstant().toString() : null);
        row.put("updated_at", rs.getTimestamp("updated_at") != null ? rs.getTimestamp("updated_at").toInstant().toString() : null);
        return row;
    }

    private static String str(Object v) {
        return v == null ? null : String.valueOf(v).trim();
    }

    private static String strOr(Object v, String d) {
        String s = str(v);
        return s == null || s.isEmpty() ? d : s;
    }

    private static int intVal(Object v) {
        return v instanceof Number n ? n.intValue() : Integer.parseInt(String.valueOf(v));
    }

    private static int intOr(Object v, int d) {
        return v == null ? d : intVal(v);
    }

    private static double doubleOr(Object v, double d) {
        if (v == null) {
            return d;
        }
        return v instanceof Number n ? n.doubleValue() : Double.parseDouble(String.valueOf(v));
    }

    private static boolean boolOr(Object v, boolean d) {
        if (v == null) {
            return d;
        }
        if (v instanceof Boolean b) {
            return b;
        }
        return Boolean.parseBoolean(String.valueOf(v));
    }

    private static void setNullableInt(PreparedStatement ps, int index, Object v) throws java.sql.SQLException {
        if (v == null) {
            ps.setObject(index, null);
        } else {
            ps.setInt(index, intVal(v));
        }
    }

    private static void setNullableDouble(PreparedStatement ps, int index, Object v) throws java.sql.SQLException {
        if (v == null) {
            ps.setObject(index, null);
        } else {
            ps.setDouble(index, v instanceof Number n ? n.doubleValue() : Double.parseDouble(String.valueOf(v)));
        }
    }
}
