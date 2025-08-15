-- Delete已存在的表（如果存在）
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS devices CASCADE;
DROP TABLE IF EXISTS data_records CASCADE;
DROP TABLE IF EXISTS api_logs CASCADE;
DROP TABLE IF EXISTS training_logs CASCADE;
DROP TABLE IF EXISTS model_services CASCADE;
DROP TABLE IF EXISTS existing_models CASCADE;

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
    operation TEXT NOT NULL,
    log_message TEXT,
    details JSONB,
    status VARCHAR(20) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建训练日志索引
CREATE INDEX IF NOT EXISTS idx_training_logs_training_id ON training_logs(training_id);
CREATE INDEX IF NOT EXISTS idx_training_logs_step ON training_logs(step);
CREATE INDEX IF NOT EXISTS idx_training_logs_status ON training_logs(status);

-- 创建模型服务表
CREATE TABLE IF NOT EXISTS model_services (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(100) UNIQUE NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_path TEXT,
    service_url VARCHAR(255),
    status VARCHAR(20) DEFAULT 'stopped',
    port INTEGER,
    pid INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建模型服务索引
CREATE INDEX IF NOT EXISTS idx_model_services_model_id ON model_services(model_id);
CREATE INDEX IF NOT EXISTS idx_model_services_status ON model_services(status);

-- 创建已存在模型表（用于存储可选择部署的模型）
CREATE TABLE IF NOT EXISTS existing_models (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(100) UNIQUE NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_description TEXT,
    model_path VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建已存在模型索引
CREATE INDEX IF NOT EXISTS idx_existing_models_model_id ON existing_models(model_id);