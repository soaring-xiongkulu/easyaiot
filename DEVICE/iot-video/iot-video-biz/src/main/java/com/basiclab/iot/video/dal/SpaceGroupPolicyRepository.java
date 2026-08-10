package com.basiclab.iot.video.dal;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class SpaceGroupPolicyRepository {

    private final JdbcTemplate jdbc;

    public Optional<Map<String, Object>> find(String groupType, String groupKey) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM space_group_save_policy WHERE group_type = ? AND group_key = ? LIMIT 1",
                (rs, rowNum) -> policyRow(rs),
                groupType, groupKey
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public void upsertSnapSaveTime(String groupType, String groupKey, int saveTime) {
        jdbc.update(
                """
                INSERT INTO space_group_save_policy (group_type, group_key, snap_save_time, record_save_time)
                VALUES (?, ?, ?, 1)
                ON CONFLICT (group_type, group_key)
                DO UPDATE SET snap_save_time = EXCLUDED.snap_save_time, updated_at = NOW()
                """,
                groupType, groupKey, saveTime
        );
    }

    public void upsertRecordSaveTime(String groupType, String groupKey, int saveTime) {
        jdbc.update(
                """
                INSERT INTO space_group_save_policy (group_type, group_key, snap_save_time, record_save_time)
                VALUES (?, ?, 1, ?)
                ON CONFLICT (group_type, group_key)
                DO UPDATE SET record_save_time = EXCLUDED.record_save_time, updated_at = NOW()
                """,
                groupType, groupKey, saveTime
        );
    }

    public int syncNonCustomSnapSpaces(String groupType, String groupKey, int saveTime) {
        return jdbc.update(
                """
                UPDATE snap_space s SET save_time = ?, updated_at = NOW()
                FROM device d
                WHERE s.device_id = d.id
                  AND COALESCE(s.save_time_custom, false) = false
                  AND (
                    (LOWER(?) = 'nvr' AND d.nvr_id::text = ?)
                    OR (LOWER(?) = 'gb28181' AND d.source ILIKE 'gb28181://' || ? || '%')
                  )
                """,
                saveTime, groupType, groupKey, groupType, groupKey
        );
    }

    public int syncNonCustomRecordSpaces(String groupType, String groupKey, int saveTime) {
        return jdbc.update(
                """
                UPDATE record_space s SET save_time = ?, updated_at = NOW()
                FROM device d
                WHERE s.device_id = d.id
                  AND COALESCE(s.save_time_custom, false) = false
                  AND (
                    (LOWER(?) = 'nvr' AND d.nvr_id::text = ?)
                    OR (LOWER(?) = 'gb28181' AND d.source ILIKE 'gb28181://' || ? || '%')
                  )
                """,
                saveTime, groupType, groupKey, groupType, groupKey
        );
    }

    private static Map<String, Object> policyRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("group_type", rs.getString("group_type"));
        row.put("group_key", rs.getString("group_key"));
        row.put("snap_save_time", rs.getInt("snap_save_time"));
        row.put("record_save_time", rs.getInt("record_save_time"));
        return row;
    }
}
