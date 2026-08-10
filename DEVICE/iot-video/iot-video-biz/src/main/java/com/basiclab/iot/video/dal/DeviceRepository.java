package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.domain.DeviceRow;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class DeviceRepository {

    private static final String SELECT_COLUMNS = """
            id, name, source, rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream,
            stream, ip, port, username, mac, manufacturer, model, firmware_version,
            serial_number, hardware_id, support_move, support_zoom, nvr_id, nvr_channel,
            rtsp_direct, channel_online, connection_status, enable_forward, directory_id,
            longitude, latitude, altitude, address, location_source, location_updated_at, heading
            """;

    private final JdbcTemplate jdbc;

    private static final RowMapper<DeviceRow> ROW_MAPPER = new RowMapper<>() {
        @Override
        public DeviceRow mapRow(ResultSet rs, int rowNum) throws SQLException {
            DeviceRow row = new DeviceRow();
            row.setId(rs.getString("id"));
            row.setName(rs.getString("name"));
            row.setSource(rs.getString("source"));
            row.setRtmpStream(rs.getString("rtmp_stream"));
            row.setHttpStream(rs.getString("http_stream"));
            row.setAiRtmpStream(rs.getString("ai_rtmp_stream"));
            row.setAiHttpStream(rs.getString("ai_http_stream"));
            int stream = rs.getInt("stream");
            row.setStream(rs.wasNull() ? null : stream);
            row.setIp(rs.getString("ip"));
            int port = rs.getInt("port");
            row.setPort(rs.wasNull() ? null : port);
            row.setUsername(rs.getString("username"));
            row.setMac(rs.getString("mac"));
            row.setManufacturer(rs.getString("manufacturer"));
            row.setModel(rs.getString("model"));
            row.setFirmwareVersion(rs.getString("firmware_version"));
            row.setSerialNumber(rs.getString("serial_number"));
            row.setHardwareId(rs.getString("hardware_id"));
            row.setSupportMove((Boolean) rs.getObject("support_move"));
            row.setSupportZoom((Boolean) rs.getObject("support_zoom"));
            int nvrId = rs.getInt("nvr_id");
            row.setNvrId(rs.wasNull() ? null : nvrId);
            row.setNvrChannel(rs.getInt("nvr_channel"));
            row.setRtspDirect(rs.getString("rtsp_direct"));
            row.setChannelOnline((Boolean) rs.getObject("channel_online"));
            row.setConnectionStatus(rs.getString("connection_status"));
            row.setEnableForward((Boolean) rs.getObject("enable_forward"));
            int directoryId = rs.getInt("directory_id");
            row.setDirectoryId(rs.wasNull() ? null : directoryId);
            row.setLongitude((Double) rs.getObject("longitude"));
            row.setLatitude((Double) rs.getObject("latitude"));
            row.setAltitude((Double) rs.getObject("altitude"));
            row.setAddress(rs.getString("address"));
            row.setLocationSource(rs.getString("location_source"));
            Timestamp locationUpdatedAt = rs.getTimestamp("location_updated_at");
            row.setLocationUpdatedAt(locationUpdatedAt != null ? locationUpdatedAt.toInstant() : null);
            row.setHeading((Double) rs.getObject("heading"));
            return row;
        }
    };

    public Optional<String> findPasswordById(String id) {
        List<String> rows = jdbc.query(
                "SELECT password FROM device WHERE id = ?",
                (rs, rowNum) -> rs.getString("password"),
                id
        );
        return rows.isEmpty() ? Optional.empty() : Optional.ofNullable(rows.get(0));
    }

    public Optional<DeviceRow> findById(String id) {
        List<DeviceRow> rows = jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM device WHERE id = ?",
                ROW_MAPPER,
                id
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public List<DeviceRow> list(int pageNo, int pageSize, String search) {
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        String like = search != null && !search.isBlank() ? "%" + search.trim() + "%" : null;
        if (like != null) {
            return jdbc.query(
                    """
                    SELECT %s FROM device
                    WHERE name ILIKE ? OR model ILIKE ? OR serial_number ILIKE ?
                       OR manufacturer ILIKE ? OR ip ILIKE ?
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                    """.formatted(SELECT_COLUMNS),
                    ROW_MAPPER,
                    like, like, like, like, like, pageSize, offset
            );
        }
        return jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM device ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                ROW_MAPPER,
                pageSize,
                offset
        );
    }

    public void updateEnableForward(String id, boolean enableForward) {
        jdbc.update("UPDATE device SET enable_forward = ? WHERE id = ?", enableForward, id);
    }

    public List<DeviceRow> findByEnableForwardTrue() {
        return jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM device WHERE enable_forward = TRUE ORDER BY id",
                ROW_MAPPER
        );
    }

    public long count(String search) {
        String like = search != null && !search.isBlank() ? "%" + search.trim() + "%" : null;
        if (like != null) {
            Long total = jdbc.queryForObject(
                    """
                    SELECT COUNT(*) FROM device
                    WHERE name ILIKE ? OR model ILIKE ? OR serial_number ILIKE ?
                       OR manufacturer ILIKE ? OR ip ILIKE ?
                    """,
                    Long.class,
                    like, like, like, like, like
            );
            return total != null ? total : 0L;
        }
        Long total = jdbc.queryForObject("SELECT COUNT(*) FROM device", Long.class);
        return total != null ? total : 0L;
    }

    public boolean existsById(String id) {
        Long count = jdbc.queryForObject("SELECT COUNT(*) FROM device WHERE id = ?", Long.class, id);
        return count != null && count > 0;
    }

    public Optional<DeviceRow> findFirstByRtmpStreamLike(String pattern) {
        List<DeviceRow> rows = jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM device WHERE rtmp_stream ILIKE ? LIMIT 1",
                ROW_MAPPER,
                "%" + pattern + "%"
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public void insert(DeviceRow row) {
        jdbc.update(
                """
                INSERT INTO device (
                    id, name, source, rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream, stream,
                    ip, port, username, password, mac, manufacturer, model, firmware_version, serial_number,
                    hardware_id, support_move, support_zoom, nvr_id, nvr_channel, rtsp_direct, channel_online,
                    connection_status, enable_forward, directory_id, longitude, latitude, altitude, address,
                    location_source, location_updated_at, heading
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                row.getId(),
                row.getName(),
                row.getSource(),
                row.getRtmpStream(),
                row.getHttpStream(),
                row.getAiRtmpStream(),
                row.getAiHttpStream(),
                row.getStream(),
                row.getIp(),
                row.getPort(),
                row.getUsername(),
                null,
                row.getMac(),
                row.getManufacturer(),
                row.getModel(),
                row.getFirmwareVersion(),
                row.getSerialNumber(),
                row.getHardwareId(),
                row.getSupportMove(),
                row.getSupportZoom(),
                row.getNvrId(),
                row.getNvrChannel(),
                row.getRtspDirect(),
                row.getChannelOnline(),
                row.getConnectionStatus(),
                row.getEnableForward(),
                row.getDirectoryId(),
                row.getLongitude(),
                row.getLatitude(),
                row.getAltitude(),
                row.getAddress(),
                row.getLocationSource(),
                row.getLocationUpdatedAt() != null ? Timestamp.from(row.getLocationUpdatedAt()) : null,
                row.getHeading()
        );
    }

    public void delete(String id) {
        jdbc.update("DELETE FROM device WHERE id = ?", id);
    }

    public List<DeviceRow> listByDirectory(int directoryId, int pageNo, int pageSize, String search) {
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        String like = search != null && !search.isBlank() ? "%" + search.trim() + "%" : null;
        if (like != null) {
            return jdbc.query(
                    """
                    SELECT %s FROM device
                    WHERE directory_id = ?
                      AND (name ILIKE ? OR model ILIKE ? OR serial_number ILIKE ?
                           OR manufacturer ILIKE ? OR ip ILIKE ?)
                    ORDER BY updated_at DESC LIMIT ? OFFSET ?
                    """.formatted(SELECT_COLUMNS),
                    ROW_MAPPER,
                    directoryId, like, like, like, like, like, pageSize, offset
            );
        }
        return jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM device WHERE directory_id = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                ROW_MAPPER,
                directoryId,
                pageSize,
                offset
        );
    }

    public long countByDirectory(int directoryId, String search) {
        String like = search != null && !search.isBlank() ? "%" + search.trim() + "%" : null;
        if (like != null) {
            Long total = jdbc.queryForObject(
                    """
                    SELECT COUNT(*) FROM device
                    WHERE directory_id = ?
                      AND (name ILIKE ? OR model ILIKE ? OR serial_number ILIKE ?
                           OR manufacturer ILIKE ? OR ip ILIKE ?)
                    """,
                    Long.class,
                    directoryId, like, like, like, like, like
            );
            return total != null ? total : 0L;
        }
        Long total = jdbc.queryForObject(
                "SELECT COUNT(*) FROM device WHERE directory_id = ?",
                Long.class,
                directoryId
        );
        return total != null ? total : 0L;
    }

    public List<DeviceRow> listForMap(Integer directoryId, boolean hasLocationOnly) {
        StringBuilder sql = new StringBuilder("SELECT " + SELECT_COLUMNS + " FROM device WHERE 1=1");
        List<Object> args = new java.util.ArrayList<>();
        if (directoryId != null) {
            sql.append(" AND directory_id = ?");
            args.add(directoryId);
        }
        if (hasLocationOnly) {
            sql.append(" AND longitude IS NOT NULL AND latitude IS NOT NULL");
        }
        sql.append(" ORDER BY updated_at DESC");
        return jdbc.query(sql.toString(), ROW_MAPPER, args.toArray());
    }

    public List<DeviceRow> listByDirectoryId(int directoryId) {
        return jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM device WHERE directory_id = ? ORDER BY updated_at DESC",
                ROW_MAPPER,
                directoryId
        );
    }

    public List<String> listIdsByDirectoryIds(List<Integer> directoryIds) {
        if (directoryIds == null || directoryIds.isEmpty()) {
            return List.of();
        }
        String placeholders = String.join(",", directoryIds.stream().map(id -> "?").toList());
        List<String> ids = new ArrayList<>();
        LinkedHashSet<String> seen = new LinkedHashSet<>();
        jdbc.query(
                "SELECT id FROM device WHERE directory_id IN (" + placeholders + ") ORDER BY updated_at DESC",
                rs -> {
                    String id = rs.getString("id");
                    if (id != null && seen.add(id)) {
                        ids.add(id);
                    }
                },
                directoryIds.toArray()
        );
        return ids;
    }

    public void updateDirectoryId(String deviceId, Integer directoryId) {
        jdbc.update("UPDATE device SET directory_id = ?, updated_at = NOW() WHERE id = ?", directoryId, deviceId);
    }

    public void updateLocation(
            String deviceId,
            Double longitude,
            Double latitude,
            Double altitude,
            String address,
            Double heading,
            String locationSource
    ) {
        jdbc.update(
                """
                UPDATE device SET longitude = ?, latitude = ?, altitude = ?, address = ?, heading = ?,
                                  location_source = ?, location_updated_at = NOW(), updated_at = NOW()
                WHERE id = ?
                """,
                longitude,
                latitude,
                altitude,
                address,
                heading,
                locationSource,
                deviceId
        );
    }

    public void updateFields(String deviceId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE device SET ");
        List<Object> args = new java.util.ArrayList<>();
        int i = 0;
        for (Map.Entry<String, Object> entry : fields.entrySet()) {
            if (i++ > 0) {
                sql.append(", ");
            }
            sql.append(entry.getKey()).append(" = ?");
            args.add(entry.getValue());
        }
        sql.append(", updated_at = NOW() WHERE id = ?");
        args.add(deviceId);
        jdbc.update(sql.toString(), args.toArray());
    }
}
