CREATE TABLE IF NOT EXISTS infra_platform_branding (
    id BIGINT PRIMARY KEY,
    platform_name VARCHAR(100),
    platform_logo_file_id BIGINT,
    dashboard_title VARCHAR(100),
    login_name VARCHAR(100),
    login_logo_file_id BIGINT,
    login_form_title VARCHAR(100),
    login_bg_light_file_id BIGINT,
    login_bg_dark_file_id BIGINT,
    default_platform_name VARCHAR(100),
    default_platform_logo_file_id BIGINT,
    default_dashboard_title VARCHAR(100),
    default_login_name VARCHAR(100),
    default_login_logo_file_id BIGINT,
    default_login_form_title VARCHAR(100),
    default_login_bg_light_file_id BIGINT,
    default_login_bg_dark_file_id BIGINT,
    creator VARCHAR(64) DEFAULT '',
    create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updater VARCHAR(64) DEFAULT '',
    update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted SMALLINT NOT NULL DEFAULT 0,
    CONSTRAINT infra_platform_branding_singleton CHECK (id = 1)
);

-- 兼容已创建的品牌配置表；default_* 仅允许通过数据库维护，前端接口不会写入。
ALTER TABLE infra_platform_branding ADD COLUMN IF NOT EXISTS default_platform_name VARCHAR(100);
ALTER TABLE infra_platform_branding ADD COLUMN IF NOT EXISTS default_platform_logo_file_id BIGINT;
ALTER TABLE infra_platform_branding ADD COLUMN IF NOT EXISTS default_dashboard_title VARCHAR(100);
ALTER TABLE infra_platform_branding ADD COLUMN IF NOT EXISTS default_login_name VARCHAR(100);
ALTER TABLE infra_platform_branding ADD COLUMN IF NOT EXISTS default_login_logo_file_id BIGINT;
ALTER TABLE infra_platform_branding ADD COLUMN IF NOT EXISTS default_login_form_title VARCHAR(100);
ALTER TABLE infra_platform_branding ADD COLUMN IF NOT EXISTS default_login_bg_light_file_id BIGINT;
ALTER TABLE infra_platform_branding ADD COLUMN IF NOT EXISTS default_login_bg_dark_file_id BIGINT;

-- 与 MyBatis-Plus 的逻辑删除值（0/1）保持一致；兼容已由早期脚本创建的 BOOLEAN 列。
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'infra_platform_branding'
          AND column_name = 'deleted'
          AND data_type = 'boolean'
    ) THEN
        ALTER TABLE infra_platform_branding ALTER COLUMN deleted DROP DEFAULT;
        ALTER TABLE infra_platform_branding
            ALTER COLUMN deleted TYPE SMALLINT USING CASE WHEN deleted THEN 1 ELSE 0 END;
        ALTER TABLE infra_platform_branding ALTER COLUMN deleted SET DEFAULT 0;
    END IF;
END $$;

COMMENT ON TABLE infra_platform_branding IS '全平台唯一品牌配置表';
COMMENT ON COLUMN infra_platform_branding.platform_logo_file_id IS '平台 Logo 对应 infra_file.id，空值使用内置默认图片';
COMMENT ON COLUMN infra_platform_branding.login_logo_file_id IS '登录 Logo 对应 infra_file.id，空值使用内置默认图片';
COMMENT ON COLUMN infra_platform_branding.login_bg_light_file_id IS '浅色登录背景对应 infra_file.id，空值使用内置默认图片';
COMMENT ON COLUMN infra_platform_branding.login_bg_dark_file_id IS '深色登录背景对应 infra_file.id，空值使用内置默认图片';
COMMENT ON COLUMN infra_platform_branding.default_platform_name IS '数据库维护的平台名称初始值，空值使用改造前内置默认值';
COMMENT ON COLUMN infra_platform_branding.default_platform_logo_file_id IS '数据库维护的平台 Logo 初始文件 ID，空值使用改造前内置默认图片';
COMMENT ON COLUMN infra_platform_branding.default_dashboard_title IS '数据库维护的大屏标题初始值，空值使用改造前内置默认值';
COMMENT ON COLUMN infra_platform_branding.default_login_name IS '数据库维护的登录页名称初始值，空值使用改造前内置默认值';
COMMENT ON COLUMN infra_platform_branding.default_login_logo_file_id IS '数据库维护的登录 Logo 初始文件 ID，空值使用改造前内置默认图片';
COMMENT ON COLUMN infra_platform_branding.default_login_form_title IS '数据库维护的登录表单标题初始值，空值使用改造前内置默认值';
COMMENT ON COLUMN infra_platform_branding.default_login_bg_light_file_id IS '数据库维护的浅色登录背景初始文件 ID，空值使用改造前内置默认图片';
COMMENT ON COLUMN infra_platform_branding.default_login_bg_dark_file_id IS '数据库维护的深色登录背景初始文件 ID，空值使用改造前内置默认图片';
