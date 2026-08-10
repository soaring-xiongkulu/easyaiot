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
public class MediaAlgorithmRepository {

    private final JdbcTemplate jdbc;

    public List<Map<String, Object>> listTaskServices(int taskId) {
        return jdbc.query(
                "SELECT * FROM algorithm_model_service WHERE task_id = ? ORDER BY sort_order, id",
                (rs, rowNum) -> taskServiceRow(rs),
                taskId
        );
    }

    public Optional<Map<String, Object>> findTaskService(int serviceId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM algorithm_model_service WHERE id = ?",
                (rs, rowNum) -> taskServiceRow(rs),
                serviceId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insertTaskService(int taskId, Map<String, Object> fields) {
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(con -> {
            PreparedStatement ps = con.prepareStatement(
                    """
                    INSERT INTO algorithm_model_service (
                        task_id, service_name, service_url, service_type, model_id, threshold,
                        request_method, request_headers, request_body_template, timeout, is_enabled, sort_order
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    Statement.RETURN_GENERATED_KEYS
            );
            int i = 1;
            ps.setInt(i++, taskId);
            ps.setString(i++, str(fields.get("service_name")));
            ps.setString(i++, str(fields.get("service_url")));
            ps.setString(i++, str(fields.get("service_type")));
            setNullableInt(ps, i++, fields.get("model_id"));
            setNullableDouble(ps, i++, fields.get("threshold"));
            ps.setString(i++, strOr(fields.get("request_method"), "POST"));
            ps.setString(i++, str(fields.get("request_headers")));
            ps.setString(i++, str(fields.get("request_body_template")));
            ps.setInt(i++, intOr(fields.get("timeout"), 30));
            ps.setBoolean(i++, boolOr(fields.get("is_enabled"), true));
            ps.setInt(i, intOr(fields.get("sort_order"), 0));
            return ps;
        }, keyHolder);
        Number key = keyHolder.getKey();
        return key != null ? key.intValue() : 0;
    }

    public void updateTaskService(int serviceId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE algorithm_model_service SET updated_at = NOW()");
        List<Object> args = new ArrayList<>();
        for (Map.Entry<String, Object> entry : fields.entrySet()) {
            sql.append(", ").append(entry.getKey()).append(" = ?");
            args.add(entry.getValue());
        }
        sql.append(" WHERE id = ?");
        args.add(serviceId);
        jdbc.update(sql.toString(), args.toArray());
    }

    public void deleteTaskService(int serviceId) {
        jdbc.update("DELETE FROM algorithm_model_service WHERE id = ?", serviceId);
    }

    public List<Map<String, Object>> listRegionServices(int regionId) {
        return jdbc.query(
                "SELECT * FROM region_model_service WHERE region_id = ? ORDER BY sort_order, id",
                (rs, rowNum) -> regionServiceRow(rs),
                regionId
        );
    }

    public Optional<Map<String, Object>> findRegionService(int serviceId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM region_model_service WHERE id = ?",
                (rs, rowNum) -> regionServiceRow(rs),
                serviceId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insertRegionService(int regionId, Map<String, Object> fields) {
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(con -> {
            PreparedStatement ps = con.prepareStatement(
                    """
                    INSERT INTO region_model_service (
                        region_id, service_name, service_url, service_type, model_id, threshold,
                        request_method, request_headers, request_body_template, timeout, is_enabled, sort_order
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    Statement.RETURN_GENERATED_KEYS
            );
            int i = 1;
            ps.setInt(i++, regionId);
            ps.setString(i++, str(fields.get("service_name")));
            ps.setString(i++, str(fields.get("service_url")));
            ps.setString(i++, str(fields.get("service_type")));
            setNullableInt(ps, i++, fields.get("model_id"));
            setNullableDouble(ps, i++, fields.get("threshold"));
            ps.setString(i++, strOr(fields.get("request_method"), "POST"));
            ps.setString(i++, str(fields.get("request_headers")));
            ps.setString(i++, str(fields.get("request_body_template")));
            ps.setInt(i++, intOr(fields.get("timeout"), 30));
            ps.setBoolean(i++, boolOr(fields.get("is_enabled"), true));
            ps.setInt(i, intOr(fields.get("sort_order"), 0));
            return ps;
        }, keyHolder);
        Number key = keyHolder.getKey();
        return key != null ? key.intValue() : 0;
    }

    public void updateRegionService(int serviceId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE region_model_service SET updated_at = NOW()");
        List<Object> args = new ArrayList<>();
        for (Map.Entry<String, Object> entry : fields.entrySet()) {
            sql.append(", ").append(entry.getKey()).append(" = ?");
            args.add(entry.getValue());
        }
        sql.append(" WHERE id = ?");
        args.add(serviceId);
        jdbc.update(sql.toString(), args.toArray());
    }

    public void deleteRegionService(int serviceId) {
        jdbc.update("DELETE FROM region_model_service WHERE id = ?", serviceId);
    }

    private static Map<String, Object> taskServiceRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = serviceCommon(rs);
        row.put("task_id", rs.getInt("task_id"));
        return row;
    }

    private static Map<String, Object> regionServiceRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = serviceCommon(rs);
        row.put("region_id", rs.getInt("region_id"));
        return row;
    }

    private static Map<String, Object> serviceCommon(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("service_name", rs.getString("service_name"));
        row.put("service_url", rs.getString("service_url"));
        row.put("service_type", rs.getString("service_type"));
        row.put("model_id", JdbcValues.getInteger(rs, "model_id"));
        row.put("threshold", JdbcValues.getDouble(rs, "threshold"));
        row.put("request_method", rs.getString("request_method"));
        row.put("request_headers", rs.getString("request_headers"));
        row.put("request_body_template", rs.getString("request_body_template"));
        row.put("timeout", JdbcValues.getInteger(rs, "timeout"));
        row.put("is_enabled", Boolean.TRUE.equals(JdbcValues.getBoolean(rs, "is_enabled")));
        row.put("sort_order", JdbcValues.getInteger(rs, "sort_order"));
        return row;
    }

    private static String str(Object v) {
        return v == null ? null : String.valueOf(v).trim();
    }

    private static String strOr(Object v, String d) {
        String s = str(v);
        return s == null || s.isEmpty() ? d : s;
    }

    private static int intOr(Object v, int d) {
        if (v == null) {
            return d;
        }
        return v instanceof Number n ? n.intValue() : Integer.parseInt(String.valueOf(v));
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
            ps.setInt(index, v instanceof Number n ? n.intValue() : Integer.parseInt(String.valueOf(v)));
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
