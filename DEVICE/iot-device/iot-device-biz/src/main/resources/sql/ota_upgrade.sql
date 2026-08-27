-- =====================================================================
-- OTA 升级能力（四类包统一：软件包/固件包/APP包/PC包）
-- 统一出入口：管理侧 /packages + /versions；设备侧 /ota/check + /ota/report
-- 统一升级策略：状态机（未验证→测试中→已发布→已撤回）+ 全量/灰度发布 + 门禁链升级
-- 适用于 PostgreSQL，可重复执行
-- =====================================================================

-- ==================== 1. device_ota_pkg 扩展字段 ====================
ALTER TABLE public.device_ota_pkg ADD COLUMN IF NOT EXISTS file_size BIGINT; -- 文件大小（字节）
ALTER TABLE public.device_ota_pkg ADD COLUMN IF NOT EXISTS file_name VARCHAR(255); -- 原始文件名
ALTER TABLE public.device_ota_pkg ADD COLUMN IF NOT EXISTS changelog VARCHAR(2000); -- 更新说明
ALTER TABLE public.device_ota_pkg ADD COLUMN IF NOT EXISTS publish_strategy SMALLINT DEFAULT 0; -- 发布策略[0:全量,1:灰度]
ALTER TABLE public.device_ota_pkg ADD COLUMN IF NOT EXISTS gray_ladder SMALLINT DEFAULT 1; -- 灰度阶梯[1:设备级,2:产品级,3:全量]
ALTER TABLE public.device_ota_pkg ADD COLUMN IF NOT EXISTS product_identification VARCHAR(64); -- 适用产品标识（空=所有产品）
ALTER TABLE public.device_ota_pkg ADD COLUMN IF NOT EXISTS test_passed SMALLINT DEFAULT 0; -- 测试是否通过[0:否,1:是]
ALTER TABLE public.device_ota_pkg ADD COLUMN IF NOT EXISTS test_remark VARCHAR(500); -- 测试备注
ALTER TABLE public.device_ota_pkg ADD COLUMN IF NOT EXISTS test_by VARCHAR(64); -- 测试人
ALTER TABLE public.device_ota_pkg ADD COLUMN IF NOT EXISTS test_time TIMESTAMP; -- 测试时间
ALTER TABLE public.device_ota_pkg ADD COLUMN IF NOT EXISTS withdraw_reason VARCHAR(500); -- 撤回原因
ALTER TABLE public.device_ota_pkg ADD COLUMN IF NOT EXISTS withdraw_time TIMESTAMP; -- 撤回时间

COMMENT ON COLUMN public.device_ota_pkg.type IS '包类型[0:软件包,1:固件包,2:APP包,3:PC包]';
COMMENT ON COLUMN public.device_ota_pkg.status IS '状态[0:未验证,1:测试中,2:已发布,3:待发布,4:已撤回]';
COMMENT ON COLUMN public.device_ota_pkg.file_size IS '文件大小（字节）';
COMMENT ON COLUMN public.device_ota_pkg.file_name IS '原始文件名';
COMMENT ON COLUMN public.device_ota_pkg.changelog IS '更新说明';
COMMENT ON COLUMN public.device_ota_pkg.publish_strategy IS '发布策略[0:全量,1:灰度]';
COMMENT ON COLUMN public.device_ota_pkg.gray_ladder IS '灰度阶梯[1:设备级,2:产品级,3:全量]';
COMMENT ON COLUMN public.device_ota_pkg.product_identification IS '适用产品标识（空=所有产品）';
COMMENT ON COLUMN public.device_ota_pkg.test_passed IS '测试是否通过[0:否,1:是]';
COMMENT ON COLUMN public.device_ota_pkg.test_remark IS '测试备注';
COMMENT ON COLUMN public.device_ota_pkg.test_by IS '测试人';
COMMENT ON COLUMN public.device_ota_pkg.test_time IS '测试时间';
COMMENT ON COLUMN public.device_ota_pkg.withdraw_reason IS '撤回原因';
COMMENT ON COLUMN public.device_ota_pkg.withdraw_time IS '撤回时间';

-- ==================== 2. device_ota_version 设备版本档案 ====================
-- 一个产品在某设备版本号下的升级包绑定关系（软件包/固件包），设备检测升级时按档案命中
CREATE TABLE IF NOT EXISTS public.device_ota_version (
    id BIGINT NOT NULL,
    device_version VARCHAR(64) NOT NULL, -- 设备版本号
    product_identification VARCHAR(64) NOT NULL, -- 所属产品标识
    app_pkg_id BIGINT, -- 软件包ID（device_ota_pkg.id）
    os_pkg_id BIGINT, -- 固件包ID（device_ota_pkg.id）
    upgrade_mode SMALLINT DEFAULT 0, -- 升级方式[0:非强制升级,1:强制升级]
    remark VARCHAR(500), -- 升级描述
    created_by VARCHAR(64), -- 创建者
    created_time TIMESTAMP, -- 创建时间
    updated_by VARCHAR(64), -- 更新者
    updated_time TIMESTAMP, -- 更新时间
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    deleted SMALLINT DEFAULT 0 NOT NULL, -- 是否删除
    CONSTRAINT device_ota_version_pkey PRIMARY KEY (id)
);

-- 创建索引
CREATE UNIQUE INDEX IF NOT EXISTS uk_device_ota_version ON public.device_ota_version(tenant_id, product_identification, device_version) WHERE deleted = 0;
CREATE INDEX IF NOT EXISTS idx_device_ota_version_product ON public.device_ota_version(product_identification);
CREATE INDEX IF NOT EXISTS idx_device_ota_version_tenant ON public.device_ota_version(tenant_id);

-- 表注释
COMMENT ON TABLE public.device_ota_version IS '设备版本档案（产品+设备版本号 → 升级包绑定）';
COMMENT ON COLUMN public.device_ota_version.id IS '主键';
COMMENT ON COLUMN public.device_ota_version.device_version IS '设备版本号';
COMMENT ON COLUMN public.device_ota_version.product_identification IS '所属产品标识';
COMMENT ON COLUMN public.device_ota_version.app_pkg_id IS '软件包ID（device_ota_pkg.id）';
COMMENT ON COLUMN public.device_ota_version.os_pkg_id IS '固件包ID（device_ota_pkg.id）';
COMMENT ON COLUMN public.device_ota_version.upgrade_mode IS '升级方式[0:非强制升级,1:强制升级]';
COMMENT ON COLUMN public.device_ota_version.remark IS '升级描述';

-- 序列
CREATE SEQUENCE IF NOT EXISTS public.device_ota_version_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE MAXVALUE 2147483647 CACHE 1;
ALTER SEQUENCE public.device_ota_version_id_seq OWNED BY public.device_ota_version.id;
ALTER TABLE public.device_ota_version ALTER COLUMN id SET DEFAULT nextval('public.device_ota_version_id_seq'::regclass);

-- ==================== 3. device_ota_version_verify 测试白名单 ====================
CREATE TABLE IF NOT EXISTS public.device_ota_version_verify (
    id BIGINT NOT NULL,
    pkg_id BIGINT NOT NULL, -- 版本包ID（device_ota_pkg.id）
    device_identification VARCHAR(64) NOT NULL, -- 设备唯一标识
    device_name VARCHAR(255), -- 设备名称（冗余展示）
    status SMALLINT DEFAULT 1, -- 状态[1:有效,0:已移除]
    remark VARCHAR(255), -- 备注
    created_by VARCHAR(64), -- 创建者
    created_time TIMESTAMP, -- 创建时间
    updated_by VARCHAR(64), -- 更新者
    updated_time TIMESTAMP, -- 更新时间
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    deleted SMALLINT DEFAULT 0 NOT NULL, -- 是否删除
    CONSTRAINT device_ota_version_verify_pkey PRIMARY KEY (id)
);

-- 创建索引
CREATE UNIQUE INDEX IF NOT EXISTS uk_device_ota_version_verify ON public.device_ota_version_verify(pkg_id, device_identification) WHERE deleted = 0;
CREATE INDEX IF NOT EXISTS idx_device_ota_verify_device ON public.device_ota_version_verify(device_identification);
CREATE INDEX IF NOT EXISTS idx_device_ota_verify_tenant ON public.device_ota_version_verify(tenant_id);

-- 表注释
COMMENT ON TABLE public.device_ota_version_verify IS 'OTA 测试白名单（设备验证名单）';
COMMENT ON COLUMN public.device_ota_version_verify.id IS '主键';
COMMENT ON COLUMN public.device_ota_version_verify.pkg_id IS '版本包ID（device_ota_pkg.id）';
COMMENT ON COLUMN public.device_ota_version_verify.device_identification IS '设备唯一标识';
COMMENT ON COLUMN public.device_ota_version_verify.device_name IS '设备名称（冗余展示）';
COMMENT ON COLUMN public.device_ota_version_verify.status IS '状态[1:有效,0:已移除]';

-- 序列
CREATE SEQUENCE IF NOT EXISTS public.device_ota_version_verify_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE MAXVALUE 2147483647 CACHE 1;
ALTER SEQUENCE public.device_ota_version_verify_id_seq OWNED BY public.device_ota_version_verify.id;
ALTER TABLE public.device_ota_version_verify ALTER COLUMN id SET DEFAULT nextval('public.device_ota_version_verify_id_seq'::regclass);

-- ==================== 4. device_ota_version_publish 发布记录 ====================
CREATE TABLE IF NOT EXISTS public.device_ota_version_publish (
    id BIGINT NOT NULL,
    pkg_id BIGINT NOT NULL, -- 版本包ID（device_ota_pkg.id）
    publish_strategy SMALLINT DEFAULT 0, -- 发布策略[0:全量,1:灰度]
    gray_ladder SMALLINT DEFAULT 3, -- 灰度阶梯[1:设备级,2:产品级,3:全量]
    status SMALLINT DEFAULT 1, -- 状态[1:已发布,0:已撤销]
    publish_time TIMESTAMP, -- 发布时间
    withdraw_reason VARCHAR(500), -- 撤回原因
    withdraw_time TIMESTAMP, -- 撤回时间
    created_by VARCHAR(64), -- 创建者
    created_time TIMESTAMP, -- 创建时间
    updated_by VARCHAR(64), -- 更新者
    updated_time TIMESTAMP, -- 更新时间
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    deleted SMALLINT DEFAULT 0 NOT NULL, -- 是否删除
    CONSTRAINT device_ota_version_publish_pkey PRIMARY KEY (id)
);

-- 创建索引
CREATE UNIQUE INDEX IF NOT EXISTS uk_device_ota_version_publish ON public.device_ota_version_publish(pkg_id, status) WHERE deleted = 0;
CREATE INDEX IF NOT EXISTS idx_device_ota_publish_tenant ON public.device_ota_version_publish(tenant_id);

-- 表注释
COMMENT ON TABLE public.device_ota_version_publish IS 'OTA 发布记录（全量/灰度）';
COMMENT ON COLUMN public.device_ota_version_publish.id IS '主键';
COMMENT ON COLUMN public.device_ota_version_publish.pkg_id IS '版本包ID（device_ota_pkg.id）';
COMMENT ON COLUMN public.device_ota_version_publish.publish_strategy IS '发布策略[0:全量,1:灰度]';
COMMENT ON COLUMN public.device_ota_version_publish.gray_ladder IS '灰度阶梯[1:设备级,2:产品级,3:全量]';
COMMENT ON COLUMN public.device_ota_version_publish.status IS '状态[1:已发布,0:已撤销]';
COMMENT ON COLUMN public.device_ota_version_publish.publish_time IS '发布时间';
COMMENT ON COLUMN public.device_ota_version_publish.withdraw_reason IS '撤回原因';
COMMENT ON COLUMN public.device_ota_version_publish.withdraw_time IS '撤回时间';

-- 序列
CREATE SEQUENCE IF NOT EXISTS public.device_ota_version_publish_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE MAXVALUE 2147483647 CACHE 1;
ALTER SEQUENCE public.device_ota_version_publish_id_seq OWNED BY public.device_ota_version_publish.id;
ALTER TABLE public.device_ota_version_publish ALTER COLUMN id SET DEFAULT nextval('public.device_ota_version_publish_id_seq'::regclass);

-- ==================== 5. device_ota_version_gray_scope 灰度范围 ====================
CREATE TABLE IF NOT EXISTS public.device_ota_version_gray_scope (
    id BIGINT NOT NULL,
    publish_id BIGINT NOT NULL, -- 发布记录ID（device_ota_version_publish.id）
    pkg_id BIGINT NOT NULL, -- 版本包ID（device_ota_pkg.id）
    scope_type SMALLINT NOT NULL, -- 范围类型[1:设备,2:产品]
    scope_value VARCHAR(128) NOT NULL, -- 范围值（设备唯一标识/产品标识）
    created_by VARCHAR(64), -- 创建者
    created_time TIMESTAMP, -- 创建时间
    updated_by VARCHAR(64), -- 更新者
    updated_time TIMESTAMP, -- 更新时间
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    deleted SMALLINT DEFAULT 0 NOT NULL, -- 是否删除
    CONSTRAINT device_ota_version_gray_scope_pkey PRIMARY KEY (id)
);

-- 创建索引
CREATE UNIQUE INDEX IF NOT EXISTS uk_device_ota_gray_scope ON public.device_ota_version_gray_scope(publish_id, scope_type, scope_value) WHERE deleted = 0;
CREATE INDEX IF NOT EXISTS idx_device_ota_gray_pkg ON public.device_ota_version_gray_scope(pkg_id);
CREATE INDEX IF NOT EXISTS idx_device_ota_gray_tenant ON public.device_ota_version_gray_scope(tenant_id);

-- 表注释
COMMENT ON TABLE public.device_ota_version_gray_scope IS 'OTA 灰度范围';
COMMENT ON COLUMN public.device_ota_version_gray_scope.id IS '主键';
COMMENT ON COLUMN public.device_ota_version_gray_scope.publish_id IS '发布记录ID（device_ota_version_publish.id）';
COMMENT ON COLUMN public.device_ota_version_gray_scope.pkg_id IS '版本包ID（device_ota_pkg.id）';
COMMENT ON COLUMN public.device_ota_version_gray_scope.scope_type IS '范围类型[1:设备,2:产品]';
COMMENT ON COLUMN public.device_ota_version_gray_scope.scope_value IS '范围值（设备唯一标识/产品标识）';

-- 序列
CREATE SEQUENCE IF NOT EXISTS public.device_ota_version_gray_scope_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE MAXVALUE 2147483647 CACHE 1;
ALTER SEQUENCE public.device_ota_version_gray_scope_id_seq OWNED BY public.device_ota_version_gray_scope.id;
ALTER TABLE public.device_ota_version_gray_scope ALTER COLUMN id SET DEFAULT nextval('public.device_ota_version_gray_scope_id_seq'::regclass);

-- ==================== 6. device_ota_upgrade_record 升级记录（漏斗） ====================
CREATE TABLE IF NOT EXISTS public.device_ota_upgrade_record (
    id BIGINT NOT NULL,
    pkg_id BIGINT, -- 版本包ID（device_ota_pkg.id，可空）
    type SMALLINT, -- 包类型[0:软件包,1:固件包,2:APP包,3:PC包]
    device_identification VARCHAR(64) NOT NULL, -- 设备唯一标识
    device_name VARCHAR(255), -- 设备名称
    product_identification VARCHAR(64), -- 产品标识
    from_version VARCHAR(64), -- 升级前版本
    to_version VARCHAR(64), -- 升级目标版本
    channel SMALLINT DEFAULT 2, -- 通道[1:测试,2:正式]
    phase SMALLINT, -- 升级阶段[0:检测,1:命中,2:下载完成,3:下载失败,4:MD5校验失败,5:安装结果,6:启动成功]
    progress SMALLINT, -- 升级进度（0-100）
    success SMALLINT, -- 是否成功[0:否,1:是]
    error_code VARCHAR(64), -- 错误码
    error_msg VARCHAR(500), -- 错误信息
    cost_ms BIGINT, -- 升级耗时（毫秒）
    upgrade_time TIMESTAMP, -- 升级发生时间
    created_by VARCHAR(64), -- 创建者
    created_time TIMESTAMP, -- 创建时间
    updated_by VARCHAR(64), -- 更新者
    updated_time TIMESTAMP, -- 更新时间
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    deleted SMALLINT DEFAULT 0 NOT NULL, -- 是否删除
    CONSTRAINT device_ota_upgrade_record_pkey PRIMARY KEY (id)
);

-- 创建索引（唯一键保证同一设备同一类型同一目标版本同一阶段幂等上报）
CREATE UNIQUE INDEX IF NOT EXISTS uk_device_ota_upgrade_record ON public.device_ota_upgrade_record(tenant_id, type, device_identification, to_version, phase) WHERE deleted = 0;
CREATE INDEX IF NOT EXISTS idx_device_ota_record_pkg ON public.device_ota_upgrade_record(pkg_id);
CREATE INDEX IF NOT EXISTS idx_device_ota_record_device ON public.device_ota_upgrade_record(device_identification, type);
CREATE INDEX IF NOT EXISTS idx_device_ota_record_time ON public.device_ota_upgrade_record(created_time);
CREATE INDEX IF NOT EXISTS idx_device_ota_record_tenant ON public.device_ota_upgrade_record(tenant_id);

-- 表注释
COMMENT ON TABLE public.device_ota_upgrade_record IS 'OTA 升级记录（检测/命中/下载/校验/安装/启动 全链路）';
COMMENT ON COLUMN public.device_ota_upgrade_record.id IS '主键';
COMMENT ON COLUMN public.device_ota_upgrade_record.pkg_id IS '版本包ID（device_ota_pkg.id，可空）';
COMMENT ON COLUMN public.device_ota_upgrade_record.type IS '包类型[0:软件包,1:固件包,2:APP包,3:PC包]';
COMMENT ON COLUMN public.device_ota_upgrade_record.device_identification IS '设备唯一标识';
COMMENT ON COLUMN public.device_ota_upgrade_record.device_name IS '设备名称';
COMMENT ON COLUMN public.device_ota_upgrade_record.product_identification IS '产品标识';
COMMENT ON COLUMN public.device_ota_upgrade_record.from_version IS '升级前版本';
COMMENT ON COLUMN public.device_ota_upgrade_record.to_version IS '升级目标版本';
COMMENT ON COLUMN public.device_ota_upgrade_record.channel IS '通道[1:测试,2:正式]';
COMMENT ON COLUMN public.device_ota_upgrade_record.phase IS '升级阶段[0:检测,1:命中,2:下载完成,3:下载失败,4:MD5校验失败,5:安装结果,6:启动成功]';
COMMENT ON COLUMN public.device_ota_upgrade_record.progress IS '升级进度（0-100）';
COMMENT ON COLUMN public.device_ota_upgrade_record.success IS '是否成功[0:否,1:是]';
COMMENT ON COLUMN public.device_ota_upgrade_record.error_code IS '错误码';
COMMENT ON COLUMN public.device_ota_upgrade_record.error_msg IS '错误信息';
COMMENT ON COLUMN public.device_ota_upgrade_record.cost_ms IS '升级耗时（毫秒）';
COMMENT ON COLUMN public.device_ota_upgrade_record.upgrade_time IS '升级发生时间';

-- 序列
CREATE SEQUENCE IF NOT EXISTS public.device_ota_upgrade_record_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE MAXVALUE 2147483647 CACHE 1;
ALTER SEQUENCE public.device_ota_upgrade_record_id_seq OWNED BY public.device_ota_upgrade_record.id;
ALTER TABLE public.device_ota_upgrade_record ALTER COLUMN id SET DEFAULT nextval('public.device_ota_upgrade_record_id_seq'::regclass);
