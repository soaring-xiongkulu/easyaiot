-- 删除所有表（如果存在）
DROP TABLE IF EXISTS wvp_user_api_key;
DROP TABLE IF EXISTS wvp_common_region;
DROP TABLE IF EXISTS wvp_common_group;
DROP TABLE IF EXISTS wvp_user_role;
DROP TABLE IF EXISTS wvp_user;
DROP TABLE IF EXISTS wvp_cloud_record;
DROP TABLE IF EXISTS wvp_stream_push;
DROP TABLE IF EXISTS wvp_stream_proxy;
DROP TABLE IF EXISTS wvp_platform_region;
DROP TABLE IF EXISTS wvp_platform_group;
DROP TABLE IF EXISTS wvp_platform_channel;
DROP TABLE IF EXISTS wvp_platform;
DROP TABLE IF EXISTS wvp_media_server;
DROP TABLE IF EXISTS wvp_record_plan_item;
DROP TABLE IF EXISTS wvp_record_plan;
DROP TABLE IF EXISTS wvp_device_channel;
DROP TABLE IF EXISTS wvp_device_mobile_position;
DROP TABLE IF EXISTS wvp_device_alarm;
DROP TABLE IF EXISTS wvp_device;

-- 创建表结构
CREATE TABLE wvp_device (
                            id SERIAL PRIMARY KEY,
                            device_id VARCHAR(50) NOT NULL,
                            name VARCHAR(255),
                            manufacturer VARCHAR(255),
                            model VARCHAR(255),
                            firmware VARCHAR(255),
                            transport VARCHAR(50),
                            stream_mode VARCHAR(50),
                            on_line BOOLEAN DEFAULT false,
                            register_time VARCHAR(50),
                            keepalive_time VARCHAR(50),
                            ip VARCHAR(50),
                            create_time VARCHAR(50),
                            update_time VARCHAR(50),
                            port INTEGER,
                            expires INTEGER,
                            subscribe_cycle_for_catalog INTEGER DEFAULT 0,
                            subscribe_cycle_for_mobile_position INTEGER DEFAULT 0,
                            mobile_position_submission_interval INTEGER DEFAULT 5,
                            subscribe_cycle_for_alarm INTEGER DEFAULT 0,
                            host_address VARCHAR(50),
                            charset VARCHAR(50),
                            ssrc_check BOOLEAN DEFAULT false,
                            geo_coord_sys VARCHAR(50),
                            media_server_id VARCHAR(50) DEFAULT 'auto',
                            custom_name VARCHAR(255),
                            sdp_ip VARCHAR(50),
                            local_ip VARCHAR(50),
                            password VARCHAR(255),
                            as_message_channel BOOLEAN DEFAULT false,
                            heart_beat_interval INTEGER,
                            heart_beat_count INTEGER,
                            position_capability INTEGER,
                            broadcast_push_after_ack BOOLEAN DEFAULT false,
                            server_id VARCHAR(50),
                            CONSTRAINT uk_device_device UNIQUE (device_id)
);

CREATE TABLE wvp_device_alarm (
                                  id SERIAL PRIMARY KEY,
                                  device_id VARCHAR(50) NOT NULL,
                                  channel_id VARCHAR(50) NOT NULL,
                                  alarm_priority VARCHAR(50),
                                  alarm_method VARCHAR(50),
                                  alarm_time VARCHAR(50),
                                  alarm_description VARCHAR(255),
                                  longitude DOUBLE PRECISION,
                                  latitude DOUBLE PRECISION,
                                  alarm_type VARCHAR(50),
                                  create_time VARCHAR(50) NOT NULL
);

CREATE TABLE wvp_device_mobile_position (
                                            id SERIAL PRIMARY KEY,
                                            device_id VARCHAR(50) NOT NULL,
                                            channel_id VARCHAR(50) NOT NULL,
                                            device_name VARCHAR(255),
                                            time VARCHAR(50),
                                            longitude DOUBLE PRECISION,
                                            latitude DOUBLE PRECISION,
                                            altitude DOUBLE PRECISION,
                                            speed DOUBLE PRECISION,
                                            direction DOUBLE PRECISION,
                                            report_source VARCHAR(50),
                                            create_time VARCHAR(50)
);

CREATE TABLE wvp_device_channel (
                                    id SERIAL PRIMARY KEY,
                                    device_id VARCHAR(50),
                                    name VARCHAR(255),
                                    manufacturer VARCHAR(50),
                                    model VARCHAR(50),
                                    owner VARCHAR(50),
                                    civil_code VARCHAR(50),
                                    block VARCHAR(50),
                                    address VARCHAR(50),
                                    parental INTEGER,
                                    parent_id VARCHAR(50),
                                    safety_way INTEGER,
                                    register_way INTEGER,
                                    cert_num VARCHAR(50),
                                    certifiable INTEGER,
                                    err_code INTEGER,
                                    end_time VARCHAR(50),
                                    secrecy INTEGER,
                                    ip_address VARCHAR(50),
                                    port INTEGER,
                                    password VARCHAR(255),
                                    status VARCHAR(50),
                                    longitude DOUBLE PRECISION,
                                    latitude DOUBLE PRECISION,
                                    ptz_type INTEGER,
                                    position_type INTEGER,
                                    room_type INTEGER,
                                    use_type INTEGER,
                                    supply_light_type INTEGER,
                                    direction_type INTEGER,
                                    resolution VARCHAR(255),
                                    business_group_id VARCHAR(255),
                                    download_speed VARCHAR(255),
                                    svc_space_support_mod INTEGER,
                                    svc_time_support_mode INTEGER,
                                    create_time VARCHAR(50) NOT NULL,
                                    update_time VARCHAR(50) NOT NULL,
                                    sub_count INTEGER,
                                    stream_id VARCHAR(255),
                                    has_audio BOOLEAN DEFAULT false,
                                    gps_time VARCHAR(50),
                                    stream_identification VARCHAR(50),
                                    channel_type INTEGER DEFAULT 0 NOT NULL,
                                    gb_device_id VARCHAR(50),
                                    gb_name VARCHAR(255),
                                    gb_manufacturer VARCHAR(255),
                                    gb_model VARCHAR(255),
                                    gb_owner VARCHAR(255),
                                    gb_civil_code VARCHAR(255),
                                    gb_block VARCHAR(255),
                                    gb_address VARCHAR(255),
                                    gb_parental INTEGER,
                                    gb_parent_id VARCHAR(255),
                                    gb_safety_way INTEGER,
                                    gb_register_way INTEGER,
                                    gb_cert_num VARCHAR(50),
                                    gb_certifiable INTEGER,
                                    gb_err_code INTEGER,
                                    gb_end_time VARCHAR(50),
                                    gb_secrecy INTEGER,
                                    gb_ip_address VARCHAR(50),
                                    gb_port INTEGER,
                                    gb_password VARCHAR(50),
                                    gb_status VARCHAR(50),
                                    gb_longitude DOUBLE PRECISION,
                                    gb_latitude DOUBLE PRECISION,
                                    gb_business_group_id VARCHAR(50),
                                    gb_ptz_type INTEGER,
                                    gb_position_type INTEGER,
                                    gb_room_type INTEGER,
                                    gb_use_type INTEGER,
                                    gb_supply_light_type INTEGER,
                                    gb_direction_type INTEGER,
                                    gb_resolution VARCHAR(255),
                                    gb_download_speed VARCHAR(255),
                                    gb_svc_space_support_mod INTEGER,
                                    gb_svc_time_support_mode INTEGER,
                                    record_plan_id INTEGER,
                                    data_type INTEGER NOT NULL,
                                    data_device_id INTEGER NOT NULL,
                                    gps_speed DOUBLE PRECISION,
                                    gps_altitude DOUBLE PRECISION,
                                    gps_direction DOUBLE PRECISION,
                                    CONSTRAINT uk_wvp_unique_channel UNIQUE (gb_device_id)
);

CREATE INDEX idx_wvp_device_channel_data_type ON wvp_device_channel(data_type);
CREATE INDEX idx_wvp_device_channel_data_device_id ON wvp_device_channel(data_device_id);

CREATE TABLE wvp_media_server (
                                  id VARCHAR(255) PRIMARY KEY,
                                  ip VARCHAR(50),
                                  hook_ip VARCHAR(50),
                                  sdp_ip VARCHAR(50),
                                  stream_ip VARCHAR(50),
                                  http_port INTEGER,
                                  http_ssl_port INTEGER,
                                  rtmp_port INTEGER,
                                  rtmp_ssl_port INTEGER,
                                  rtp_proxy_port INTEGER,
                                  rtsp_port INTEGER,
                                  rtsp_ssl_port INTEGER,
                                  flv_port INTEGER,
                                  flv_ssl_port INTEGER,
                                  ws_flv_port INTEGER,
                                  ws_flv_ssl_port INTEGER,
                                  auto_config BOOLEAN DEFAULT false,
                                  secret VARCHAR(50),
                                  type VARCHAR(50) DEFAULT 'zlm',
                                  rtp_enable BOOLEAN DEFAULT false,
                                  rtp_port_range VARCHAR(50),
                                  send_rtp_port_range VARCHAR(50),
                                  record_assist_port INTEGER,
                                  default_server BOOLEAN DEFAULT false,
                                  create_time VARCHAR(50),
                                  update_time VARCHAR(50),
                                  hook_alive_interval INTEGER,
                                  record_path VARCHAR(255),
                                  record_day INTEGER DEFAULT 7,
                                  transcode_suffix VARCHAR(255),
                                  server_id VARCHAR(50),
                                  CONSTRAINT uk_media_server_unique_ip_http_port UNIQUE (ip, http_port, server_id)
);

CREATE TABLE wvp_platform (
                              id SERIAL PRIMARY KEY,
                              enable BOOLEAN DEFAULT false,
                              name VARCHAR(255),
                              server_gb_id VARCHAR(50),
                              server_gb_domain VARCHAR(50),
                              server_ip VARCHAR(50),
                              server_port INTEGER,
                              device_gb_id VARCHAR(50),
                              device_ip VARCHAR(50),
                              device_port VARCHAR(50),
                              username VARCHAR(255),
                              password VARCHAR(50),
                              expires VARCHAR(50),
                              keep_timeout VARCHAR(50),
                              transport VARCHAR(50),
                              civil_code VARCHAR(50),
                              manufacturer VARCHAR(255),
                              model VARCHAR(255),
                              address VARCHAR(255),
                              character_set VARCHAR(50),
                              ptz BOOLEAN DEFAULT false,
                              rtcp BOOLEAN DEFAULT false,
                              status BOOLEAN DEFAULT false,
                              catalog_group INTEGER,
                              register_way INTEGER,
                              secrecy INTEGER,
                              create_time VARCHAR(50),
                              update_time VARCHAR(50),
                              as_message_channel BOOLEAN DEFAULT false,
                              catalog_with_platform INTEGER DEFAULT 1,
                              catalog_with_group INTEGER DEFAULT 1,
                              catalog_with_region INTEGER DEFAULT 1,
                              auto_push_channel BOOLEAN DEFAULT true,
                              send_stream_ip VARCHAR(50),
                              server_id VARCHAR(50),
                              CONSTRAINT uk_platform_unique_server_gb_id UNIQUE (server_gb_id)
);

CREATE TABLE wvp_platform_channel (
                                      id SERIAL PRIMARY KEY,
                                      platform_id INTEGER,
                                      device_channel_id INTEGER,
                                      custom_device_id VARCHAR(50),
                                      custom_name VARCHAR(255),
                                      custom_manufacturer VARCHAR(50),
                                      custom_model VARCHAR(50),
                                      custom_owner VARCHAR(50),
                                      custom_civil_code VARCHAR(50),
                                      custom_block VARCHAR(50),
                                      custom_address VARCHAR(50),
                                      custom_parental INTEGER,
                                      custom_parent_id VARCHAR(50),
                                      custom_safety_way INTEGER,
                                      custom_register_way INTEGER,
                                      custom_cert_num VARCHAR(50),
                                      custom_certifiable INTEGER,
                                      custom_err_code INTEGER,
                                      custom_end_time VARCHAR(50),
                                      custom_secrecy INTEGER,
                                      custom_ip_address VARCHAR(50),
                                      custom_port INTEGER,
                                      custom_password VARCHAR(255),
                                      custom_status VARCHAR(50),
                                      custom_longitude DOUBLE PRECISION,
                                      custom_latitude DOUBLE PRECISION,
                                      custom_ptz_type INTEGER,
                                      custom_position_type INTEGER,
                                      custom_room_type INTEGER,
                                      custom_use_type INTEGER,
                                      custom_supply_light_type INTEGER,
                                      custom_direction_type INTEGER,
                                      custom_resolution VARCHAR(255),
                                      custom_business_group_id VARCHAR(255),
                                      custom_download_speed VARCHAR(255),
                                      custom_svc_space_support_mod INTEGER,
                                      custom_svc_time_support_mode INTEGER,
                                      CONSTRAINT uk_platform_gb_channel_platform_id_catalog_id_device_channel_id UNIQUE (platform_id, device_channel_id),
                                      CONSTRAINT uk_platform_gb_channel_device_id UNIQUE (custom_device_id)
);

CREATE TABLE wvp_platform_group (
                                    id SERIAL PRIMARY KEY,
                                    platform_id INTEGER,
                                    group_id INTEGER,
                                    CONSTRAINT uk_wvp_platform_group_platform_id_group_id UNIQUE (platform_id, group_id)
);

CREATE TABLE wvp_platform_region (
                                     id SERIAL PRIMARY KEY,
                                     platform_id INTEGER,
                                     region_id INTEGER,
                                     CONSTRAINT uk_wvp_platform_region_platform_id_group_id UNIQUE (platform_id, region_id)
);

CREATE TABLE wvp_stream_proxy (
                                  id SERIAL PRIMARY KEY,
                                  type VARCHAR(50),
                                  app VARCHAR(255),
                                  stream VARCHAR(255),
                                  src_url VARCHAR(255),
                                  timeout INTEGER,
                                  ffmpeg_cmd_key VARCHAR(255),
                                  rtsp_type VARCHAR(50),
                                  media_server_id VARCHAR(50),
                                  enable_audio BOOLEAN DEFAULT false,
                                  enable_mp4 BOOLEAN DEFAULT false,
                                  pulling BOOLEAN DEFAULT false,
                                  enable BOOLEAN DEFAULT false,
                                  enable_remove_none_reader BOOLEAN DEFAULT false,
                                  create_time VARCHAR(50),
                                  name VARCHAR(255),
                                  update_time VARCHAR(50),
                                  stream_key VARCHAR(255),
                                  server_id VARCHAR(50),
                                  enable_disable_none_reader BOOLEAN DEFAULT false,
                                  relates_media_server_id VARCHAR(50),
                                  CONSTRAINT uk_stream_proxy_app_stream UNIQUE (app, stream)
);

CREATE TABLE wvp_stream_push (
                                 id SERIAL PRIMARY KEY,
                                 app VARCHAR(255),
                                 stream VARCHAR(255),
                                 create_time VARCHAR(50),
                                 media_server_id VARCHAR(50),
                                 server_id VARCHAR(50),
                                 push_time VARCHAR(50),
                                 status BOOLEAN DEFAULT false,
                                 update_time VARCHAR(50),
                                 pushing BOOLEAN DEFAULT false,
                                 self BOOLEAN DEFAULT false,
                                 start_offline_push BOOLEAN DEFAULT true,
                                 CONSTRAINT uk_stream_push_app_stream UNIQUE (app, stream)
);

CREATE TABLE wvp_cloud_record (
                                  id SERIAL PRIMARY KEY,
                                  app VARCHAR(255),
                                  stream VARCHAR(255),
                                  call_id VARCHAR(255),
                                  start_time BIGINT,
                                  end_time BIGINT,
                                  media_server_id VARCHAR(50),
                                  server_id VARCHAR(50),
                                  file_name VARCHAR(255),
                                  folder VARCHAR(500),
                                  file_path VARCHAR(500),
                                  collect BOOLEAN DEFAULT false,
                                  file_size BIGINT,
                                  time_len BIGINT
);

CREATE TABLE wvp_user (
                          id SERIAL PRIMARY KEY,
                          username VARCHAR(255),
                          password VARCHAR(255),
                          role_id INTEGER,
                          create_time VARCHAR(50),
                          update_time VARCHAR(50),
                          push_key VARCHAR(50),
                          CONSTRAINT uk_user_username UNIQUE (username)
);

CREATE TABLE wvp_user_role (
                               id SERIAL PRIMARY KEY,
                               name VARCHAR(50),
                               authority VARCHAR(50),
                               create_time VARCHAR(50),
                               update_time VARCHAR(50)
);

CREATE TABLE wvp_common_group (
                                  id SERIAL PRIMARY KEY,
                                  device_id VARCHAR(50) NOT NULL,
                                  name VARCHAR(255) NOT NULL,
                                  parent_id INTEGER,
                                  parent_device_id VARCHAR(50) DEFAULT NULL,
                                  business_group VARCHAR(50) NOT NULL,
                                  create_time VARCHAR(50) NOT NULL,
                                  update_time VARCHAR(50) NOT NULL,
                                  civil_code VARCHAR(50) DEFAULT NULL,
                                  CONSTRAINT uk_common_group_device_platform UNIQUE (device_id)
);

CREATE TABLE wvp_common_region (
                                   id SERIAL PRIMARY KEY,
                                   device_id VARCHAR(50) NOT NULL,
                                   name VARCHAR(255) NOT NULL,
                                   parent_id INTEGER,
                                   parent_device_id VARCHAR(50) DEFAULT NULL,
                                   create_time VARCHAR(50) NOT NULL,
                                   update_time VARCHAR(50) NOT NULL,
                                   CONSTRAINT uk_common_region_device_id UNIQUE (device_id)
);

CREATE TABLE wvp_record_plan (
                                 id SERIAL PRIMARY KEY,
                                 snap BOOLEAN DEFAULT false,
                                 name VARCHAR(255) NOT NULL,
                                 create_time VARCHAR(50),
                                 update_time VARCHAR(50)
);

CREATE TABLE wvp_record_plan_item (
                                      id SERIAL PRIMARY KEY,
                                      start INTEGER,
                                      stop INTEGER,
                                      week_day INTEGER,
                                      plan_id INTEGER,
                                      create_time VARCHAR(50),
                                      update_time VARCHAR(50)
);

CREATE TABLE wvp_user_api_key (
                                  id SERIAL PRIMARY KEY,
                                  user_id BIGINT,
                                  app VARCHAR(255),
                                  api_key TEXT,
                                  expired_at BIGINT,
                                  remark VARCHAR(255),
                                  enable BOOLEAN DEFAULT true,
                                  create_time VARCHAR(50),
                                  update_time VARCHAR(50)
);

-- 插入初始数据
INSERT INTO wvp_user (id, username, password, role_id, create_time, update_time, push_key)
VALUES (1, 'admin', '21232f297a57a5a743894a0e4a801fc3', 1, '2021-04-13 14:14:57', '2021-04-13 14:14:57', '3e80d1762a324d5b0ff636e0bd16f1e3');

INSERT INTO wvp_user_role (id, name, authority, create_time, update_time)
VALUES (1, 'admin', '0', '2021-04-13 14:14:57', '2021-04-13 14:14:57');

-- 后续结构更新（一条一条执行）
ALTER TABLE wvp_media_server ADD COLUMN IF NOT EXISTS transcode_suffix VARCHAR(255);
ALTER TABLE wvp_media_server ADD COLUMN IF NOT EXISTS type VARCHAR(50) DEFAULT 'zlm';
ALTER TABLE wvp_media_server ADD COLUMN IF NOT EXISTS flv_port INTEGER;
ALTER TABLE wvp_media_server ADD COLUMN IF NOT EXISTS flv_ssl_port INTEGER;
ALTER TABLE wvp_media_server ADD COLUMN IF NOT EXISTS ws_flv_port INTEGER;
ALTER TABLE wvp_media_server ADD COLUMN IF NOT EXISTS ws_flv_ssl_port INTEGER;
ALTER TABLE wvp_device_channel ADD COLUMN IF NOT EXISTS data_type INTEGER NOT NULL DEFAULT 0;
ALTER TABLE wvp_device_channel ADD COLUMN IF NOT EXISTS data_device_id INTEGER NOT NULL DEFAULT 0;
ALTER TABLE wvp_stream_proxy ADD COLUMN IF NOT EXISTS relates_media_server_id VARCHAR(50);
ALTER TABLE wvp_device ADD COLUMN IF NOT EXISTS heart_beat_interval INTEGER;
ALTER TABLE wvp_device ADD COLUMN IF NOT EXISTS heart_beat_count INTEGER;
ALTER TABLE wvp_device ADD COLUMN IF NOT EXISTS position_capability INTEGER;
ALTER TABLE wvp_device ADD COLUMN IF NOT EXISTS server_id VARCHAR(50);
ALTER TABLE wvp_media_server ADD COLUMN IF NOT EXISTS server_id VARCHAR(50);
ALTER TABLE wvp_stream_proxy ADD COLUMN IF NOT EXISTS server_id VARCHAR(50);
ALTER TABLE wvp_cloud_record ADD COLUMN IF NOT EXISTS server_id VARCHAR(50);
ALTER TABLE wvp_platform ADD COLUMN IF NOT EXISTS server_id VARCHAR(50);
ALTER TABLE wvp_device_channel ADD COLUMN IF NOT EXISTS gps_speed DOUBLE PRECISION;
ALTER TABLE wvp_device_channel ADD COLUMN IF NOT EXISTS gps_altitude DOUBLE PRECISION;
ALTER TABLE wvp_device_channel ADD COLUMN IF NOT EXISTS gps_direction DOUBLE PRECISION;