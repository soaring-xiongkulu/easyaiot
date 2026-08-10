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
import java.util.List;
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
}
