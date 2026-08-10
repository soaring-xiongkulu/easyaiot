package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.domain.DeviceDirectoryRow;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class DeviceDirectoryRepository {

    private static final String SELECT_COLUMNS = """
            id, name, parent_id, description, sort_order, snap_save_time, record_save_time, created_at, updated_at
            """;

    private final JdbcTemplate jdbc;

    private static final RowMapper<DeviceDirectoryRow> ROW_MAPPER = new RowMapper<>() {
        @Override
        public DeviceDirectoryRow mapRow(ResultSet rs, int rowNum) throws SQLException {
            DeviceDirectoryRow row = new DeviceDirectoryRow();
            row.setId(rs.getInt("id"));
            row.setName(rs.getString("name"));
            int parentId = rs.getInt("parent_id");
            row.setParentId(rs.wasNull() ? null : parentId);
            row.setDescription(rs.getString("description"));
            row.setSortOrder(rs.getInt("sort_order"));
            row.setSnapSaveTime(rs.getInt("snap_save_time"));
            row.setRecordSaveTime(rs.getInt("record_save_time"));
            Timestamp createdAt = rs.getTimestamp("created_at");
            row.setCreatedAt(createdAt != null ? createdAt.toInstant() : null);
            Timestamp updatedAt = rs.getTimestamp("updated_at");
            row.setUpdatedAt(updatedAt != null ? updatedAt.toInstant() : null);
            return row;
        }
    };

    public List<DeviceDirectoryRow> findByParentId(Integer parentId) {
        if (parentId == null) {
            return jdbc.query(
                    "SELECT " + SELECT_COLUMNS + " FROM device_directory WHERE parent_id IS NULL ORDER BY sort_order, id",
                    ROW_MAPPER
            );
        }
        return jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM device_directory WHERE parent_id = ? ORDER BY sort_order, id",
                ROW_MAPPER,
                parentId
        );
    }

    public Optional<DeviceDirectoryRow> findById(int id) {
        List<DeviceDirectoryRow> rows = jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM device_directory WHERE id = ?",
                ROW_MAPPER,
                id
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public Optional<DeviceDirectoryRow> findByNameAndParentId(String name, Integer parentId) {
        if (parentId == null) {
            List<DeviceDirectoryRow> rows = jdbc.query(
                    """
                    SELECT %s FROM device_directory
                    WHERE name = ? AND parent_id IS NULL
                    LIMIT 1
                    """.formatted(SELECT_COLUMNS),
                    ROW_MAPPER,
                    name
            );
            return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
        }
        List<DeviceDirectoryRow> rows = jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM device_directory WHERE name = ? AND parent_id = ? LIMIT 1",
                ROW_MAPPER,
                name,
                parentId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public List<DeviceDirectoryRow> findAllByName(String name) {
        return jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM device_directory WHERE name = ? ORDER BY sort_order, id",
                ROW_MAPPER,
                name
        );
    }

    public List<DeviceDirectoryRow> findAll() {
        return jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM device_directory ORDER BY sort_order, id",
                ROW_MAPPER
        );
    }

    public Optional<DeviceDirectoryRow> findDefaultRoot() {
        List<DeviceDirectoryRow> rows = jdbc.query(
                """
                SELECT %s FROM device_directory
                WHERE name = ? AND parent_id IS NULL
                LIMIT 1
                """.formatted(SELECT_COLUMNS),
                ROW_MAPPER,
                "默认分组"
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insert(DeviceDirectoryRow row) {
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(connection -> {
            PreparedStatement ps = connection.prepareStatement(
                    """
                    INSERT INTO device_directory (name, parent_id, description, sort_order, snap_save_time, record_save_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    Statement.RETURN_GENERATED_KEYS
            );
            ps.setString(1, row.getName());
            if (row.getParentId() == null) {
                ps.setNull(2, java.sql.Types.INTEGER);
            } else {
                ps.setInt(2, row.getParentId());
            }
            ps.setString(3, row.getDescription());
            ps.setInt(4, row.getSortOrder());
            ps.setInt(5, row.getSnapSaveTime());
            ps.setInt(6, row.getRecordSaveTime());
            return ps;
        }, keyHolder);
        Number key = keyHolder.getKey();
        return key != null ? key.intValue() : 0;
    }

    public void update(DeviceDirectoryRow row) {
        jdbc.update(
                """
                UPDATE device_directory
                SET name = ?, parent_id = ?, description = ?, sort_order = ?,
                    snap_save_time = ?, record_save_time = ?, updated_at = NOW()
                WHERE id = ?
                """,
                row.getName(),
                row.getParentId(),
                row.getDescription(),
                row.getSortOrder(),
                row.getSnapSaveTime(),
                row.getRecordSaveTime(),
                row.getId()
        );
    }

    public void delete(int id) {
        jdbc.update("DELETE FROM device_directory WHERE id = ?", id);
    }

    public long countChildren(int id) {
        Long count = jdbc.queryForObject(
                "SELECT COUNT(*) FROM device_directory WHERE parent_id = ?",
                Long.class,
                id
        );
        return count != null ? count : 0L;
    }

    public long countDevices(int directoryId) {
        Long count = jdbc.queryForObject(
                "SELECT COUNT(*) FROM device WHERE directory_id = ?",
                Long.class,
                directoryId
        );
        return count != null ? count : 0L;
    }

    public int ensureDefaultDirectory() {
        return findDefaultRoot().map(DeviceDirectoryRow::getId).orElseGet(() -> {
            DeviceDirectoryRow row = new DeviceDirectoryRow();
            row.setName("默认分组");
            row.setDescription("未手动分组的摄像头（含直连与国标）");
            row.setSortOrder(-1000);
            return insert(row);
        });
    }

    public void updateSaveTime(int directoryId, String column, int value) {
        jdbc.update("UPDATE device_directory SET " + column + " = ?, updated_at = NOW() WHERE id = ?", value, directoryId);
    }
}
