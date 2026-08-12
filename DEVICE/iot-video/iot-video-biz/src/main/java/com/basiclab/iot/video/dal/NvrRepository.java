package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.domain.NvrRow;
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
import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class NvrRepository {

    private static final String SELECT_COLUMNS = """
            id, ip, port, username, password, name, model, vendor, serial_number, firmware_version,
            device_type, mac, scheme, rtsp_url, source, rtsp_template, rtsp_port
            """;

    private final JdbcTemplate jdbc;

    private static final RowMapper<NvrRow> ROW_MAPPER = new RowMapper<>() {
        @Override
        public NvrRow mapRow(ResultSet rs, int rowNum) throws SQLException {
            NvrRow row = new NvrRow();
            row.setId(rs.getInt("id"));
            row.setIp(rs.getString("ip"));
            row.setPort(rs.getInt("port"));
            row.setUsername(rs.getString("username"));
            row.setPassword(rs.getString("password"));
            row.setName(rs.getString("name"));
            row.setModel(rs.getString("model"));
            row.setVendor(rs.getString("vendor"));
            row.setSerialNumber(rs.getString("serial_number"));
            row.setFirmwareVersion(rs.getString("firmware_version"));
            row.setDeviceType(rs.getString("device_type"));
            row.setMac(rs.getString("mac"));
            row.setScheme(rs.getString("scheme"));
            row.setRtspUrl(rs.getString("rtsp_url"));
            row.setSource(rs.getString("source"));
            row.setRtspTemplate(rs.getString("rtsp_template"));
            int rtspPort = rs.getInt("rtsp_port");
            row.setRtspPort(rs.wasNull() ? null : rtspPort);
            return row;
        }
    };

    public List<NvrRow> listAll() {
        return jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM nvr ORDER BY ip, id",
                ROW_MAPPER
        );
    }

    public Optional<NvrRow> findById(int id) {
        List<NvrRow> rows = jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM nvr WHERE id = ?",
                ROW_MAPPER,
                id
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public Optional<NvrRow> findByIpAndPort(String ip, int port) {
        List<NvrRow> rows = jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM nvr WHERE ip = ? AND port = ?",
                ROW_MAPPER,
                ip,
                port
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insert(NvrRow row) {
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(connection -> {
            PreparedStatement ps = connection.prepareStatement(
                    """
                    INSERT INTO nvr (ip, port, username, password, name, model, vendor, serial_number,
                                     firmware_version, device_type, mac, scheme, rtsp_url, source, rtsp_template, rtsp_port)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    Statement.RETURN_GENERATED_KEYS
            );
            ps.setString(1, row.getIp());
            ps.setInt(2, row.getPort() != null ? row.getPort() : 80);
            ps.setString(3, row.getUsername());
            ps.setString(4, row.getPassword());
            ps.setString(5, row.getName());
            ps.setString(6, row.getModel());
            ps.setString(7, row.getVendor());
            ps.setString(8, row.getSerialNumber());
            ps.setString(9, row.getFirmwareVersion());
            ps.setString(10, row.getDeviceType());
            ps.setString(11, row.getMac());
            ps.setString(12, row.getScheme());
            ps.setString(13, row.getRtspUrl());
            ps.setString(14, row.getSource());
            ps.setString(15, row.getRtspTemplate());
            if (row.getRtspPort() == null) {
                ps.setNull(16, java.sql.Types.SMALLINT);
            } else {
                ps.setInt(16, row.getRtspPort());
            }
            return ps;
        }, keyHolder);
        Number key = keyHolder.getKey();
        return key != null ? key.intValue() : 0;
    }

    public void update(NvrRow row) {
        jdbc.update(
                """
                UPDATE nvr SET username = ?, password = ?, name = ?, model = ?, vendor = ?,
                               serial_number = ?, firmware_version = ?, device_type = ?, mac = ?,
                               scheme = ?, rtsp_url = ?, source = ?, rtsp_template = ?, rtsp_port = ?,
                               updated_at = NOW()
                WHERE id = ?
                """,
                row.getUsername(),
                row.getPassword(),
                row.getName(),
                row.getModel(),
                row.getVendor(),
                row.getSerialNumber(),
                row.getFirmwareVersion(),
                row.getDeviceType(),
                row.getMac(),
                row.getScheme(),
                row.getRtspUrl(),
                row.getSource(),
                row.getRtspTemplate(),
                row.getRtspPort(),
                row.getId()
        );
    }

    public void delete(int id) {
        jdbc.update("DELETE FROM nvr WHERE id = ?", id);
    }

    public long countCameras(int nvrId) {
        Long count = jdbc.queryForObject(
                "SELECT COUNT(*) FROM device WHERE nvr_id = ?",
                Long.class,
                nvrId
        );
        return count != null ? count : 0L;
    }

    public java.util.Map<String, Integer> buildIpIndex() {
        java.util.Map<String, Integer> index = new java.util.LinkedHashMap<>();
        for (NvrRow nvr : listAll()) {
            String ip = nvr.getIp() != null ? nvr.getIp().strip() : "";
            if (!ip.isEmpty() && nvr.getId() != null) {
                index.put(ip, nvr.getId());
            }
        }
        return index;
    }
}
