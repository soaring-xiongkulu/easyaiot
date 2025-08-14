-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建设备表
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'offline',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建数据记录表
CREATE TABLE IF NOT EXISTS data_records (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_data_records_device_id ON data_records(device_id);
CREATE INDEX IF NOT EXISTS idx_data_records_created_at ON data_records(created_at);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);

-- 创建API调用日志表
CREATE TABLE IF NOT EXISTS api_logs (
    id SERIAL PRIMARY KEY,
    api_endpoint VARCHAR(255) NOT NULL,
    request_method VARCHAR(10) NOT NULL,
    request_data JSONB,
    response_data JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建训练日志表
CREATE TABLE IF NOT EXISTS training_logs (
    id SERIAL PRIMARY KEY,
    training_id VARCHAR(100) NOT NULL,
    step INTEGER NOT NULL,
    operation TEXT NOT NOT,
    details JSONB,
    status VARCHAR(20) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建训练日志索引
CREATE INDEX IF NOT EXISTS idx_training_logs_training_id ON training_logs(training_id);
CREATE INDEX IF NOT EXISTS idx_training_logs_step ON training_logs(step);
CREATE INDEX IF NOT EXISTS idx_training_logs_status ON training_logs(status);
