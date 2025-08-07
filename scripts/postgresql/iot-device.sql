-- public.device definition

-- Drop table

-- DROP TABLE public.device;

CREATE TABLE public.device (
	id int8 NOT NULL, -- id
	did varchar(20) NOT NULL, -- 设备唯一标识
	"name" varchar(50) NULL, -- 设备名称
	description varchar(100) NULL, -- 设备描述
	enabled_status varchar(10) NULL, -- 设备状态： ENABLE:启用 || DISABLE:禁用
	connect_status varchar(10) NULL, -- 连接状态 :    OFFLINE:离线 || ONLINE:在线
	pid varchar(20) NOT NULL, -- 产品唯一标识
	create_by varchar(10) NULL, -- 创建者
	create_time timestamp DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
	update_by varchar(10) NULL, -- 更新者
	update_time timestamp DEFAULT CURRENT_TIMESTAMP NULL, -- 更新时间
	remark varchar(100) NULL, -- 备注
	device_version varchar(10) NULL, -- 设备版本号
	device_sn varchar(20) NOT NULL, -- 设备sn号
	ip_address varchar(20) NULL, -- IP地址
	mac_address varchar(20) NULL, -- MAC地址
	active_status int2 DEFAULT 0 NULL, -- 激活状态 0:未激活 1:已激活
	"extension" text NULL, -- 扩展json
	activated_time timestamp NULL, -- 激活时间
	last_online_time timestamp NULL, -- 最后上线时间
	parent_did varchar(20) NULL, -- 子设备关联网关的设备唯一标识
	device_type varchar NULL, -- 支持以下两种产品类型¶•COMMON：普通产品，需直连设备。¶•GATEWAY：网关产品，可挂载子设备。¶•SUBSET：子设备。
	latitude numeric(10, 7) NULL, -- 纬度
	longitude numeric(10, 7) NULL, -- 经度
	location_name varchar(500) NULL, -- 设备所在位置
	province_code varchar(50) NULL, -- 省,直辖市编码
	city_code varchar(50) NULL, -- 市编码
	region_code varchar(50) NULL, -- 区县
	tenant_id int8 NULL, -- 租户ID
	product_name varchar(50) NULL, -- 产品名称
	is_shadow int2 NULL, -- 是否启用设备影子(0=禁用，1=启用)
	things_model_value json NULL, -- 物模型值
	product_type_id int8 NULL, -- 产品类型ID
	product_type_name varchar(100) NULL, -- 产品类型名称
	group_id int8 NULL, -- 分组ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_52" PRIMARY KEY (id)
);
COMMENT ON TABLE public.device IS '设备表';

-- Column comments

COMMENT ON COLUMN public.device.id IS 'id';
COMMENT ON COLUMN public.device.did IS '设备唯一标识';
COMMENT ON COLUMN public.device."name" IS '设备名称';
COMMENT ON COLUMN public.device.description IS '设备描述';
COMMENT ON COLUMN public.device.enabled_status IS '设备状态： ENABLE:启用 || DISABLE:禁用';
COMMENT ON COLUMN public.device.connect_status IS '连接状态 :    OFFLINE:离线 || ONLINE:在线';
COMMENT ON COLUMN public.device.pid IS '产品唯一标识';
COMMENT ON COLUMN public.device.create_by IS '创建者';
COMMENT ON COLUMN public.device.create_time IS '创建时间';
COMMENT ON COLUMN public.device.update_by IS '更新者';
COMMENT ON COLUMN public.device.update_time IS '更新时间';
COMMENT ON COLUMN public.device.remark IS '备注';
COMMENT ON COLUMN public.device.device_version IS '设备版本号';
COMMENT ON COLUMN public.device.device_sn IS '设备sn号';
COMMENT ON COLUMN public.device.ip_address IS 'IP地址';
COMMENT ON COLUMN public.device.mac_address IS 'MAC地址';
COMMENT ON COLUMN public.device.active_status IS '激活状态 0:未激活 1:已激活';
COMMENT ON COLUMN public.device."extension" IS '扩展json';
COMMENT ON COLUMN public.device.activated_time IS '激活时间';
COMMENT ON COLUMN public.device.last_online_time IS '最后上线时间';
COMMENT ON COLUMN public.device.parent_did IS '子设备关联网关的设备唯一标识';
COMMENT ON COLUMN public.device.device_type IS '支持以下两种产品类型
•COMMON：普通产品，需直连设备。
•GATEWAY：网关产品，可挂载子设备。
•SUBSET：子设备。';
COMMENT ON COLUMN public.device.latitude IS '纬度';
COMMENT ON COLUMN public.device.longitude IS '经度';
COMMENT ON COLUMN public.device.location_name IS '设备所在位置';
COMMENT ON COLUMN public.device.province_code IS '省,直辖市编码';
COMMENT ON COLUMN public.device.city_code IS '市编码';
COMMENT ON COLUMN public.device.region_code IS '区县';
COMMENT ON COLUMN public.device.tenant_id IS '租户ID';
COMMENT ON COLUMN public.device.product_name IS '产品名称';
COMMENT ON COLUMN public.device.is_shadow IS '是否启用设备影子(0=禁用，1=启用)';
COMMENT ON COLUMN public.device.things_model_value IS '物模型值';
COMMENT ON COLUMN public.device.product_type_id IS '产品类型ID';
COMMENT ON COLUMN public.device.product_type_name IS '产品类型名称';
COMMENT ON COLUMN public.device.group_id IS '分组ID';
COMMENT ON COLUMN public.device.deleted IS '是否删除';


-- public.device_group definition

-- Drop table

-- DROP TABLE public.device_group;

CREATE TABLE public.device_group (
	id int8 NOT NULL, -- 设备ID
	group_name varchar NOT NULL, -- 分组ID
	create_by varchar(10) NULL, -- 创建者
	create_time timestamp DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
	update_by varchar(10) NULL, -- 更新者
	update_time timestamp DEFAULT CURRENT_TIMESTAMP NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL -- 是否删除
);
COMMENT ON TABLE public.device_group IS '设备分组表';

-- Column comments

COMMENT ON COLUMN public.device_group.id IS '设备ID';
COMMENT ON COLUMN public.device_group.group_name IS '分组ID';
COMMENT ON COLUMN public.device_group.create_by IS '创建者';
COMMENT ON COLUMN public.device_group.create_time IS '创建时间';
COMMENT ON COLUMN public.device_group.update_by IS '更新者';
COMMENT ON COLUMN public.device_group.update_time IS '更新时间';
COMMENT ON COLUMN public.device_group.tenant_id IS '租户ID';
COMMENT ON COLUMN public.device_group.deleted IS '是否删除';


-- public.device_log definition

-- Drop table

-- DROP TABLE public.device_log;

CREATE TABLE public.device_log (
	id int8 NOT NULL, -- id
	did varchar NULL, -- 设备唯一标识
	file_url varchar NULL, -- 文件地址
	upload_time timestamp NULL, -- 上传时间
	file_name varchar NULL, -- 文件名称
	file_size int8 NULL, -- 文件大小
	remark varchar NULL, -- 备注
	status int2 NULL, -- 状态[0:成功, 1:未开始, 2:上传中, 3:失败]
	created_by varchar NULL, -- 创建者
	created_time timestamp NULL, -- 创建时间
	updated_by varchar NULL, -- 更新者
	updated_time timestamp NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT device_log_file_pkey PRIMARY KEY (id)
);
COMMENT ON TABLE public.device_log IS '设备日志表';

-- Column comments

COMMENT ON COLUMN public.device_log.id IS 'id';
COMMENT ON COLUMN public.device_log.did IS '设备唯一标识';
COMMENT ON COLUMN public.device_log.file_url IS '文件地址';
COMMENT ON COLUMN public.device_log.upload_time IS '上传时间';
COMMENT ON COLUMN public.device_log.file_name IS '文件名称';
COMMENT ON COLUMN public.device_log.file_size IS '文件大小';
COMMENT ON COLUMN public.device_log.remark IS '备注';
COMMENT ON COLUMN public.device_log.status IS '状态[0:成功, 1:未开始, 2:上传中, 3:失败]';
COMMENT ON COLUMN public.device_log.created_by IS '创建者';
COMMENT ON COLUMN public.device_log.created_time IS '创建时间';
COMMENT ON COLUMN public.device_log.updated_by IS '更新者';
COMMENT ON COLUMN public.device_log.updated_time IS '更新时间';
COMMENT ON COLUMN public.device_log.tenant_id IS '租户ID';
COMMENT ON COLUMN public.device_log.deleted IS '是否删除';


-- public.device_topic definition

-- Drop table

-- DROP TABLE public.device_topic;

CREATE TABLE public.device_topic (
	id int8 NOT NULL, -- id
	did varchar(100) NOT NULL, -- 设备标识
	"type" varchar(255) NULL, -- 类型(0:基础Topic,1:自定义Topic)
	topic varchar(100) NULL, -- topic
	publisher varchar(255) NULL, -- 发布者
	subscriber varchar(255) NULL, -- 订阅者
	create_by varchar(64) NULL, -- 创建者
	create_time timestamp(6) NOT NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新者
	update_time timestamp(6) NOT NULL, -- 更新时间
	remark varchar(500) NULL, -- 备注
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	tenant_id int8 NULL, -- 租户ID
	CONSTRAINT "_copy_47" PRIMARY KEY (id)
);
COMMENT ON TABLE public.device_topic IS '设备Topic数据表';

-- Column comments

COMMENT ON COLUMN public.device_topic.id IS 'id';
COMMENT ON COLUMN public.device_topic.did IS '设备标识';
COMMENT ON COLUMN public.device_topic."type" IS '类型(0:基础Topic,1:自定义Topic)';
COMMENT ON COLUMN public.device_topic.topic IS 'topic';
COMMENT ON COLUMN public.device_topic.publisher IS '发布者';
COMMENT ON COLUMN public.device_topic.subscriber IS '订阅者';
COMMENT ON COLUMN public.device_topic.create_by IS '创建者';
COMMENT ON COLUMN public.device_topic.create_time IS '创建时间';
COMMENT ON COLUMN public.device_topic.update_by IS '更新者';
COMMENT ON COLUMN public.device_topic.update_time IS '更新时间';
COMMENT ON COLUMN public.device_topic.remark IS '备注';
COMMENT ON COLUMN public.device_topic.deleted IS '是否删除';
COMMENT ON COLUMN public.device_topic.tenant_id IS '租户ID';


-- public.ota_packages definition

-- Drop table

-- DROP TABLE public.ota_packages;

CREATE TABLE public.ota_packages (
	id int8 NOT NULL, -- 主键
	app_id varchar(64) NOT NULL, -- 应用ID
	package_name varchar(100) NOT NULL, -- 包名称
	package_type int2 NOT NULL, -- 升级包类型(0:软件包、1:固件包)
	product_identification varchar(100) NOT NULL, -- 产品标识
	"version" varchar(255) NOT NULL, -- 升级包版本号
	file_location varchar(255) NOT NULL, -- 升级包的位置
	status int2 NOT NULL, -- 状态
	description varchar(255) NULL, -- 升级包功能描述
	custom_info text NULL, -- 自定义信息
	remark varchar(255) NULL, -- 描述
	created_by int8 NULL, -- 创建人
	created_time timestamp(6) NOT NULL, -- 创建时间
	updated_by int8 NULL, -- 更新人
	updated_time timestamp(6) NOT NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_42" PRIMARY KEY (id)
);
CREATE INDEX idx_app_id ON public.ota_packages USING btree (app_id);
COMMENT ON INDEX public.idx_app_id IS '应用ID';
CREATE INDEX idx_product_identification ON public.ota_packages USING btree (product_identification);
COMMENT ON INDEX public.idx_product_identification IS '产品标识';
CREATE INDEX idx_version ON public.ota_packages USING btree (version);
COMMENT ON INDEX public.idx_version IS '升级包版本号';
COMMENT ON TABLE public.ota_packages IS 'OTA升级包表';

-- Column comments

COMMENT ON COLUMN public.ota_packages.id IS '主键';
COMMENT ON COLUMN public.ota_packages.app_id IS '应用ID';
COMMENT ON COLUMN public.ota_packages.package_name IS '包名称';
COMMENT ON COLUMN public.ota_packages.package_type IS '升级包类型(0:软件包、1:固件包)';
COMMENT ON COLUMN public.ota_packages.product_identification IS '产品标识';
COMMENT ON COLUMN public.ota_packages."version" IS '升级包版本号';
COMMENT ON COLUMN public.ota_packages.file_location IS '升级包的位置';
COMMENT ON COLUMN public.ota_packages.status IS '状态';
COMMENT ON COLUMN public.ota_packages.description IS '升级包功能描述';
COMMENT ON COLUMN public.ota_packages.custom_info IS '自定义信息';
COMMENT ON COLUMN public.ota_packages.remark IS '描述';
COMMENT ON COLUMN public.ota_packages.created_by IS '创建人';
COMMENT ON COLUMN public.ota_packages.created_time IS '创建时间';
COMMENT ON COLUMN public.ota_packages.updated_by IS '更新人';
COMMENT ON COLUMN public.ota_packages.updated_time IS '更新时间';
COMMENT ON COLUMN public.ota_packages.tenant_id IS '租户ID';
COMMENT ON COLUMN public.ota_packages.deleted IS '是否删除';


-- public.ota_records definition

-- Drop table

-- DROP TABLE public.ota_records;

CREATE TABLE public.ota_records (
	id int8 NOT NULL, -- 主键
	task_id int8 NOT NULL, -- 任务ID，关联ota_upgrade_tasks表
	did varchar(100) NOT NULL, -- 设备标识
	upgrade_status int2 NOT NULL, -- 升级状态(0:待升级、1:升级中、2:升级成功、3:升级失败)
	progress int2 NOT NULL, -- 升级进度（百分比）
	error_code varchar(100) NULL, -- 错误代码
	error_message varchar(255) NULL, -- 错误信息
	start_time timestamp(6) NULL, -- 升级开始时间
	end_time timestamp(6) NULL, -- 升级结束时间
	success_details text NULL, -- 升级成功详细信息
	failure_details text NULL, -- 升级失败详细信息
	log_details text NULL, -- 升级过程日志
	remark varchar(255) NULL, -- 描述
	created_time timestamp(6) NOT NULL, -- 记录创建时间
	created_by int8 NULL, -- 创建人
	updated_by int8 NULL, -- 更新人
	updated_time timestamp(6) NOT NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_44" PRIMARY KEY (id)
);
CREATE INDEX idx_device_identification ON public.ota_records USING btree (did);
CREATE INDEX idx_task_id ON public.ota_records USING btree (task_id);
CREATE UNIQUE INDEX idx_task_id_device_identification ON public.ota_records USING btree (task_id, did);
COMMENT ON TABLE public.ota_records IS 'OTA升级记录表';

-- Column comments

COMMENT ON COLUMN public.ota_records.id IS '主键';
COMMENT ON COLUMN public.ota_records.task_id IS '任务ID，关联ota_upgrade_tasks表';
COMMENT ON COLUMN public.ota_records.did IS '设备标识';
COMMENT ON COLUMN public.ota_records.upgrade_status IS '升级状态(0:待升级、1:升级中、2:升级成功、3:升级失败)';
COMMENT ON COLUMN public.ota_records.progress IS '升级进度（百分比）';
COMMENT ON COLUMN public.ota_records.error_code IS '错误代码';
COMMENT ON COLUMN public.ota_records.error_message IS '错误信息';
COMMENT ON COLUMN public.ota_records.start_time IS '升级开始时间';
COMMENT ON COLUMN public.ota_records.end_time IS '升级结束时间';
COMMENT ON COLUMN public.ota_records.success_details IS '升级成功详细信息';
COMMENT ON COLUMN public.ota_records.failure_details IS '升级失败详细信息';
COMMENT ON COLUMN public.ota_records.log_details IS '升级过程日志';
COMMENT ON COLUMN public.ota_records.remark IS '描述';
COMMENT ON COLUMN public.ota_records.created_time IS '记录创建时间';
COMMENT ON COLUMN public.ota_records.created_by IS '创建人';
COMMENT ON COLUMN public.ota_records.updated_by IS '更新人';
COMMENT ON COLUMN public.ota_records.updated_time IS '更新时间';
COMMENT ON COLUMN public.ota_records.tenant_id IS '租户ID';
COMMENT ON COLUMN public.ota_records.deleted IS '是否删除';


-- public.ota_tasks definition

-- Drop table

-- DROP TABLE public.ota_tasks;

CREATE TABLE public.ota_tasks (
	id int8 NOT NULL, -- 主键
	upgrade_id int8 NOT NULL, -- 升级包ID，关联ota_upgrades表
	task_name varchar(100) NOT NULL, -- 任务名称
	task_status int2 NOT NULL, -- 任务状态(0:待发布、1:进行中、2:已完成、3:已取消)
	scheduled_time timestamp(6) NULL, -- 计划执行时间
	description varchar(255) NULL, -- 任务描述
	remark varchar(255) NULL, -- 描述
	created_by int8 NULL, -- 创建人
	created_time timestamp(6) NOT NULL, -- 创建时间
	updated_by int8 NULL, -- 更新人
	updated_time timestamp(6) NOT NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_43" PRIMARY KEY (id)
);
CREATE INDEX idx_upgrade_id ON public.ota_tasks USING btree (upgrade_id);
COMMENT ON INDEX public.idx_upgrade_id IS '升级包ID';
COMMENT ON TABLE public.ota_tasks IS 'OTA升级任务表';

-- Column comments

COMMENT ON COLUMN public.ota_tasks.id IS '主键';
COMMENT ON COLUMN public.ota_tasks.upgrade_id IS '升级包ID，关联ota_upgrades表';
COMMENT ON COLUMN public.ota_tasks.task_name IS '任务名称';
COMMENT ON COLUMN public.ota_tasks.task_status IS '任务状态(0:待发布、1:进行中、2:已完成、3:已取消)';
COMMENT ON COLUMN public.ota_tasks.scheduled_time IS '计划执行时间';
COMMENT ON COLUMN public.ota_tasks.description IS '任务描述';
COMMENT ON COLUMN public.ota_tasks.remark IS '描述';
COMMENT ON COLUMN public.ota_tasks.created_by IS '创建人';
COMMENT ON COLUMN public.ota_tasks.created_time IS '创建时间';
COMMENT ON COLUMN public.ota_tasks.updated_by IS '更新人';
COMMENT ON COLUMN public.ota_tasks.updated_time IS '更新时间';
COMMENT ON COLUMN public.ota_tasks.tenant_id IS '租户ID';
COMMENT ON COLUMN public.ota_tasks.deleted IS '是否删除';


-- public.product definition

-- Drop table

-- DROP TABLE public.product;

CREATE TABLE public.product (
	id int8 NOT NULL, -- id
	template_code varchar(100) NULL, -- 模板code
	"name" varchar(255) NOT NULL, -- 产品名称
	pid varchar(100) NOT NULL, -- 产品唯一标识
	manufacturer_name varchar(255) NOT NULL, -- 厂商名称 :支持中文、英文大小写、数字、下划线和中划线
	model varchar(255) NOT NULL, -- 产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线
	data_format varchar(255) NOT NULL, -- 数据格式，默认为JSON无需修改。
	protocol_type varchar(255) NOT NULL, -- 设备接入平台的协议类型，默认为MQTT无需修改。
	enabled_status int2 NOT NULL, -- 状态(字典值：0启用  1停用)
	remark varchar(255) NULL, -- 产品描述
	create_by varchar(64) NULL, -- 创建者
	create_time timestamp(6) DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新者
	update_time timestamp(6) NULL, -- 更新时间
	auth_mode varchar(255) NULL, -- 认证方式
	user_name varchar(255) NULL, -- 用户名
	"password" varchar(255) NULL, -- 密码
	connector varchar(255) NULL, -- 连接实例
	sign_key varchar(255) NULL, -- 签名密钥
	encrypt_method int4 NULL, -- 协议加密方式 0：不加密 1：SM4加密 2：AES加密
	encrypt_key varchar(255) NULL, -- 加密密钥
	encrypt_vector varchar(255) NULL, -- 加密向量
	tenant_id int8 NULL, -- 租户ID
	product_type_id int8 NULL, -- 产品类型ID
	product_type_name varchar(100) NULL, -- 产品类型名称
	manufacturer_code varchar(50) NOT NULL, -- 厂商Code:支持英文大小写，数字，下划线和中划线
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_113" PRIMARY KEY (id)
);
COMMENT ON TABLE public.product IS '产品表';

-- Column comments

COMMENT ON COLUMN public.product.id IS 'id';
COMMENT ON COLUMN public.product.template_code IS '模板code';
COMMENT ON COLUMN public.product."name" IS '产品名称';
COMMENT ON COLUMN public.product.pid IS '产品唯一标识';
COMMENT ON COLUMN public.product.manufacturer_name IS '厂商名称 :支持中文、英文大小写、数字、下划线和中划线';
COMMENT ON COLUMN public.product.model IS '产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线';
COMMENT ON COLUMN public.product.data_format IS '数据格式，默认为JSON无需修改。';
COMMENT ON COLUMN public.product.protocol_type IS '设备接入平台的协议类型，默认为MQTT无需修改。';
COMMENT ON COLUMN public.product.enabled_status IS '状态(字典值：0启用  1停用)';
COMMENT ON COLUMN public.product.remark IS '产品描述';
COMMENT ON COLUMN public.product.create_by IS '创建者';
COMMENT ON COLUMN public.product.create_time IS '创建时间';
COMMENT ON COLUMN public.product.update_by IS '更新者';
COMMENT ON COLUMN public.product.update_time IS '更新时间';
COMMENT ON COLUMN public.product.auth_mode IS '认证方式';
COMMENT ON COLUMN public.product.user_name IS '用户名';
COMMENT ON COLUMN public.product."password" IS '密码';
COMMENT ON COLUMN public.product.connector IS '连接实例';
COMMENT ON COLUMN public.product.sign_key IS '签名密钥';
COMMENT ON COLUMN public.product.encrypt_method IS '协议加密方式 0：不加密 1：SM4加密 2：AES加密';
COMMENT ON COLUMN public.product.encrypt_key IS '加密密钥';
COMMENT ON COLUMN public.product.encrypt_vector IS '加密向量';
COMMENT ON COLUMN public.product.tenant_id IS '租户ID';
COMMENT ON COLUMN public.product.product_type_id IS '产品类型ID';
COMMENT ON COLUMN public.product.product_type_name IS '产品类型名称';
COMMENT ON COLUMN public.product.manufacturer_code IS '厂商Code:支持英文大小写，数字，下划线和中划线';
COMMENT ON COLUMN public.product.deleted IS '是否删除';


-- public.product_commands definition

-- Drop table

-- DROP TABLE public.product_commands;

CREATE TABLE public.product_commands (
	id int8 NOT NULL, -- 命令id
	service_id int8 NOT NULL, -- 服务ID
	"name" varchar(255) NOT NULL, -- 指示命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。¶支持英文大小写、数字及下划线，长度[2,50]。¶
	description varchar(255) NULL, -- 命令描述。
	create_by varchar(64) NULL, -- 创建者
	create_time timestamp(6) NOT NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新者
	update_time timestamp(6) NOT NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_40" PRIMARY KEY (id)
);
CREATE INDEX service_id ON public.product_commands USING btree (service_id);
COMMENT ON INDEX public.service_id IS '服务ID';
COMMENT ON TABLE public.product_commands IS '产品模型设备服务命令表';

-- Column comments

COMMENT ON COLUMN public.product_commands.id IS '命令id';
COMMENT ON COLUMN public.product_commands.service_id IS '服务ID';
COMMENT ON COLUMN public.product_commands."name" IS '指示命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。
支持英文大小写、数字及下划线，长度[2,50]。
';
COMMENT ON COLUMN public.product_commands.description IS '命令描述。';
COMMENT ON COLUMN public.product_commands.create_by IS '创建者';
COMMENT ON COLUMN public.product_commands.create_time IS '创建时间';
COMMENT ON COLUMN public.product_commands.update_by IS '更新者';
COMMENT ON COLUMN public.product_commands.update_time IS '更新时间';
COMMENT ON COLUMN public.product_commands.tenant_id IS '租户ID';
COMMENT ON COLUMN public.product_commands.deleted IS '是否删除';


-- public.product_commands_requests definition

-- Drop table

-- DROP TABLE public.product_commands_requests;

CREATE TABLE public.product_commands_requests (
	id int8 NOT NULL, -- id
	service_id int8 NOT NULL, -- 服务ID
	commands_id int8 NOT NULL, -- 命令ID
	"datatype" varchar(255) NOT NULL, -- 指示数据类型。取值范围：string、int、decimal¶
	enumlist varchar(255) NULL, -- 指示枚举值。¶如开关状态status可有如下取值¶"enumList" : ["OPEN","CLOSE"]¶目前本字段是非功能性字段，仅起到描述作用。建议准确定义。¶
	max varchar(255) NULL, -- 指示最大值。¶仅当dataType为int、decimal时生效，逻辑小于等于。
	maxlength varchar(255) NULL, -- 指示字符串长度。¶仅当dataType为string时生效。
	min varchar(255) NULL, -- 指示最小值。¶仅当dataType为int、decimal时生效，逻辑大于等于。
	parameter_description varchar(255) NULL, -- 命令中参数的描述，不影响实际功能，可配置为空字符串""。
	parameter_name varchar(255) NULL, -- 命令中参数的名字。
	required varchar(255) NOT NULL, -- 指示本条属性是否必填，取值为0或1，默认取值1（必填）。¶目前本字段是非功能性字段，仅起到描述作用。
	step varchar(255) NULL, -- 指示步长。
	unit varchar(255) NULL, -- 指示单位。¶取值根据参数确定，如：¶•温度单位：“C”或“K”¶•百分比单位：“%”¶•压强单位：“Pa”或“kPa”¶
	create_by varchar(64) NULL, -- 创建者
	create_time timestamp(6) NOT NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新者
	update_time timestamp(6) NOT NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_39" PRIMARY KEY (id)
);
CREATE INDEX commands_id ON public.product_commands_requests USING btree (commands_id);
CREATE INDEX service_id_copy_3 ON public.product_commands_requests USING btree (service_id);
COMMENT ON TABLE public.product_commands_requests IS '产品模型设备下发服务命令属性表';

-- Column comments

COMMENT ON COLUMN public.product_commands_requests.id IS 'id';
COMMENT ON COLUMN public.product_commands_requests.service_id IS '服务ID';
COMMENT ON COLUMN public.product_commands_requests.commands_id IS '命令ID';
COMMENT ON COLUMN public.product_commands_requests."datatype" IS '指示数据类型。取值范围：string、int、decimal
';
COMMENT ON COLUMN public.product_commands_requests.enumlist IS '指示枚举值。
如开关状态status可有如下取值
"enumList" : ["OPEN","CLOSE"]
目前本字段是非功能性字段，仅起到描述作用。建议准确定义。
';
COMMENT ON COLUMN public.product_commands_requests.max IS '指示最大值。
仅当dataType为int、decimal时生效，逻辑小于等于。';
COMMENT ON COLUMN public.product_commands_requests.maxlength IS '指示字符串长度。
仅当dataType为string时生效。';
COMMENT ON COLUMN public.product_commands_requests.min IS '指示最小值。
仅当dataType为int、decimal时生效，逻辑大于等于。';
COMMENT ON COLUMN public.product_commands_requests.parameter_description IS '命令中参数的描述，不影响实际功能，可配置为空字符串""。';
COMMENT ON COLUMN public.product_commands_requests.parameter_name IS '命令中参数的名字。';
COMMENT ON COLUMN public.product_commands_requests.required IS '指示本条属性是否必填，取值为0或1，默认取值1（必填）。
目前本字段是非功能性字段，仅起到描述作用。';
COMMENT ON COLUMN public.product_commands_requests.step IS '指示步长。';
COMMENT ON COLUMN public.product_commands_requests.unit IS '指示单位。
取值根据参数确定，如：
•温度单位：“C”或“K”
•百分比单位：“%”
•压强单位：“Pa”或“kPa”
';
COMMENT ON COLUMN public.product_commands_requests.create_by IS '创建者';
COMMENT ON COLUMN public.product_commands_requests.create_time IS '创建时间';
COMMENT ON COLUMN public.product_commands_requests.update_by IS '更新者';
COMMENT ON COLUMN public.product_commands_requests.update_time IS '更新时间';
COMMENT ON COLUMN public.product_commands_requests.tenant_id IS '租户ID';
COMMENT ON COLUMN public.product_commands_requests.deleted IS '是否删除';


-- public.product_commands_response definition

-- Drop table

-- DROP TABLE public.product_commands_response;

CREATE TABLE public.product_commands_response (
	id int8 NOT NULL, -- id
	commands_id int8 NOT NULL, -- 命令ID
	service_id int8 NULL, -- 服务ID
	"datatype" varchar(255) NOT NULL, -- 指示数据类型。取值范围：string、int、decimal¶
	enumlist varchar(255) NULL, -- 指示枚举值。¶如开关状态status可有如下取值¶"enumList" : ["OPEN","CLOSE"]¶目前本字段是非功能性字段，仅起到描述作用。建议准确定义。¶
	max varchar(255) NULL, -- 指示最大值。¶仅当dataType为int、decimal时生效，逻辑小于等于。
	maxlength varchar(255) NULL, -- 指示字符串长度。¶仅当dataType为string时生效。
	min varchar(255) NULL, -- 指示最小值。¶仅当dataType为int、decimal时生效，逻辑大于等于。
	parameter_description varchar(255) NULL, -- 命令中参数的描述，不影响实际功能，可配置为空字符串""。
	parameter_name varchar(255) NULL, -- 命令中参数的名字。
	required varchar(255) NOT NULL, -- 指示本条属性是否必填，取值为0或1，默认取值1（必填）。¶目前本字段是非功能性字段，仅起到描述作用。
	step varchar(255) NULL, -- 指示步长。
	unit varchar(255) NULL, -- 指示单位。¶取值根据参数确定，如：¶•温度单位：“C”或“K”¶•百分比单位：“%”¶•压强单位：“Pa”或“kPa”¶
	create_by varchar(64) NULL, -- 创建者
	create_time timestamp(6) NOT NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新者
	update_time timestamp(6) NOT NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_38" PRIMARY KEY (id)
);
CREATE INDEX commands_id_copy_1 ON public.product_commands_response USING btree (commands_id);
CREATE INDEX service_id_copy_2 ON public.product_commands_response USING btree (service_id);
COMMENT ON TABLE public.product_commands_response IS '产品模型设备响应服务命令属性表';

-- Column comments

COMMENT ON COLUMN public.product_commands_response.id IS 'id';
COMMENT ON COLUMN public.product_commands_response.commands_id IS '命令ID';
COMMENT ON COLUMN public.product_commands_response.service_id IS '服务ID';
COMMENT ON COLUMN public.product_commands_response."datatype" IS '指示数据类型。取值范围：string、int、decimal
';
COMMENT ON COLUMN public.product_commands_response.enumlist IS '指示枚举值。
如开关状态status可有如下取值
"enumList" : ["OPEN","CLOSE"]
目前本字段是非功能性字段，仅起到描述作用。建议准确定义。
';
COMMENT ON COLUMN public.product_commands_response.max IS '指示最大值。
仅当dataType为int、decimal时生效，逻辑小于等于。';
COMMENT ON COLUMN public.product_commands_response.maxlength IS '指示字符串长度。
仅当dataType为string时生效。';
COMMENT ON COLUMN public.product_commands_response.min IS '指示最小值。
仅当dataType为int、decimal时生效，逻辑大于等于。';
COMMENT ON COLUMN public.product_commands_response.parameter_description IS '命令中参数的描述，不影响实际功能，可配置为空字符串""。';
COMMENT ON COLUMN public.product_commands_response.parameter_name IS '命令中参数的名字。';
COMMENT ON COLUMN public.product_commands_response.required IS '指示本条属性是否必填，取值为0或1，默认取值1（必填）。
目前本字段是非功能性字段，仅起到描述作用。';
COMMENT ON COLUMN public.product_commands_response.step IS '指示步长。';
COMMENT ON COLUMN public.product_commands_response.unit IS '指示单位。
取值根据参数确定，如：
•温度单位：“C”或“K”
•百分比单位：“%”
•压强单位：“Pa”或“kPa”
';
COMMENT ON COLUMN public.product_commands_response.create_by IS '创建者';
COMMENT ON COLUMN public.product_commands_response.create_time IS '创建时间';
COMMENT ON COLUMN public.product_commands_response.update_by IS '更新者';
COMMENT ON COLUMN public.product_commands_response.update_time IS '更新时间';
COMMENT ON COLUMN public.product_commands_response.tenant_id IS '租户ID';
COMMENT ON COLUMN public.product_commands_response.deleted IS '是否删除';


-- public.product_event definition

-- Drop table

-- DROP TABLE public.product_event;

CREATE TABLE public.product_event (
	id bigserial NOT NULL, -- id
	event_name varchar(255) NOT NULL, -- 事件名称
	event_code varchar(255) NOT NULL, -- 事件code
	event_type varchar(255) NOT NULL, -- 事件类型。¶INFO_EVENT_TYPE：信息。¶ALERT_EVENT_TYPE：告警。¶ERROR_EVENT_TYPE：故障
	template_code varchar(255) NULL, -- 模板code
	pid varchar(255) NULL, -- 产品唯一标识
	enabled_status varchar(10) DEFAULT '0' NULL, -- 状态(字典值：0启用  1停用)
	description varchar(255) NULL, -- 描述
	create_by varchar(64) NULL, -- 创建者
	create_time timestamp(6) DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新者
	update_time timestamp(6) NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT product_event_pkey PRIMARY KEY (id)
);
COMMENT ON TABLE public.product_event IS '产品模型事件表';

-- Column comments

COMMENT ON COLUMN public.product_event.id IS 'id';
COMMENT ON COLUMN public.product_event.event_name IS '事件名称';
COMMENT ON COLUMN public.product_event.event_code IS '事件code';
COMMENT ON COLUMN public.product_event.event_type IS '事件类型。
INFO_EVENT_TYPE：信息。
ALERT_EVENT_TYPE：告警。
ERROR_EVENT_TYPE：故障';
COMMENT ON COLUMN public.product_event.template_code IS '模板code';
COMMENT ON COLUMN public.product_event.pid IS '产品唯一标识';
COMMENT ON COLUMN public.product_event.enabled_status IS '状态(字典值：0启用  1停用)';
COMMENT ON COLUMN public.product_event.description IS '描述';
COMMENT ON COLUMN public.product_event.create_by IS '创建者';
COMMENT ON COLUMN public.product_event.create_time IS '创建时间';
COMMENT ON COLUMN public.product_event.update_by IS '更新者';
COMMENT ON COLUMN public.product_event.update_time IS '更新时间';
COMMENT ON COLUMN public.product_event.tenant_id IS '租户ID';
COMMENT ON COLUMN public.product_event.deleted IS '是否删除';


-- public.product_event_response definition

-- Drop table

-- DROP TABLE public.product_event_response;

CREATE TABLE public.product_event_response (
	id int8 NOT NULL, -- id
	event_id int8 NOT NULL, -- 事件id
	service_id int8 NULL, -- 服务ID
	"datatype" varchar(255) NOT NULL, -- 指示数据类型。取值范围：string、int、decimal
	enumlist varchar(255) NULL, -- 指示枚举值。¶如开关状态status可有如下取值¶"enumList" : ["OPEN","CLOSE"]¶目前本字段是非功能性字段，仅起到描述作用。建议准确定义。
	max varchar(255) NULL, -- 指示最大值。¶仅当dataType为int、decimal时生效，逻辑小于等于。
	maxlength varchar(255) NULL, -- 指示字符串长度。¶仅当dataType为string时生效。
	min varchar(255) NULL, -- 指示最小值。¶仅当dataType为int、decimal时生效，逻辑大于等于。
	parameter_description varchar(255) NULL, -- 命令中参数的描述，不影响实际功能，可配置为空字符串""。
	parameter_name varchar(255) NULL, -- 命令中参数的名字。
	required varchar(255) NOT NULL, -- 指示本条属性是否必填，取值为0或1，默认取值1（必填）。¶目前本字段是非功能性字段，仅起到描述作用。
	step varchar(255) NULL, -- 指示步长。
	unit varchar(255) NULL, -- 指示单位。¶取值根据参数确定，如：¶•温度单位：“C”或“K”¶•百分比单位：“%”¶•压强单位：“Pa”或“kPa”
	create_by varchar(64) NULL, -- 创建者
	create_time timestamp(6) DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新者
	update_time timestamp(6) NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT product_commands_response_copy1_pkey PRIMARY KEY (id)
);
CREATE INDEX commands_id_copy_1_copy1 ON public.product_event_response USING btree (event_id);
CREATE INDEX service_id_copy_2_copy1 ON public.product_event_response USING btree (service_id);
COMMENT ON TABLE public.product_event_response IS '产品模型事件响应表';

-- Column comments

COMMENT ON COLUMN public.product_event_response.id IS 'id';
COMMENT ON COLUMN public.product_event_response.event_id IS '事件id';
COMMENT ON COLUMN public.product_event_response.service_id IS '服务ID';
COMMENT ON COLUMN public.product_event_response."datatype" IS '指示数据类型。取值范围：string、int、decimal';
COMMENT ON COLUMN public.product_event_response.enumlist IS '指示枚举值。
如开关状态status可有如下取值
"enumList" : ["OPEN","CLOSE"]
目前本字段是非功能性字段，仅起到描述作用。建议准确定义。';
COMMENT ON COLUMN public.product_event_response.max IS '指示最大值。
仅当dataType为int、decimal时生效，逻辑小于等于。';
COMMENT ON COLUMN public.product_event_response.maxlength IS '指示字符串长度。
仅当dataType为string时生效。';
COMMENT ON COLUMN public.product_event_response.min IS '指示最小值。
仅当dataType为int、decimal时生效，逻辑大于等于。';
COMMENT ON COLUMN public.product_event_response.parameter_description IS '命令中参数的描述，不影响实际功能，可配置为空字符串""。';
COMMENT ON COLUMN public.product_event_response.parameter_name IS '命令中参数的名字。';
COMMENT ON COLUMN public.product_event_response.required IS '指示本条属性是否必填，取值为0或1，默认取值1（必填）。
目前本字段是非功能性字段，仅起到描述作用。';
COMMENT ON COLUMN public.product_event_response.step IS '指示步长。';
COMMENT ON COLUMN public.product_event_response.unit IS '指示单位。
取值根据参数确定，如：
•温度单位：“C”或“K”
•百分比单位：“%”
•压强单位：“Pa”或“kPa”';
COMMENT ON COLUMN public.product_event_response.create_by IS '创建者';
COMMENT ON COLUMN public.product_event_response.create_time IS '创建时间';
COMMENT ON COLUMN public.product_event_response.update_by IS '更新者';
COMMENT ON COLUMN public.product_event_response.update_time IS '更新时间';
COMMENT ON COLUMN public.product_event_response.tenant_id IS '租户ID';
COMMENT ON COLUMN public.product_event_response.deleted IS '是否删除';


-- public.product_properties definition

-- Drop table

-- DROP TABLE public.product_properties;

CREATE TABLE public.product_properties (
	id int8 NOT NULL, -- id
	property_name varchar(255) NOT NULL, -- 功能名称
	property_code varchar(255) NOT NULL, -- 属性code
	"datatype" varchar(255) NOT NULL, -- 指示数据类型：取值范围：string、int、decimal（float和double都可以使用此类型）、DateTime、jsonObject上报数据时，复杂类型数据格式如下：¶•DateTime:yyyyMMdd’T’HHmmss’Z’如:20151212T121212Z•jsonObject：自定义json结构体，平台不理解只透传
	description varchar(255) NULL, -- 属性描述，不影响实际功能，可配置为空字符串""。
	enumlist varchar(255) NULL, -- 指示枚举值:如开关状态status可有如下取值"enumList" : ["OPEN","CLOSE"]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。
	max varchar(255) NULL, -- 指示最大值。支持长度不超过50的数字。仅当dataType为int、decimal时生效，逻辑小于等于。
	maxlength int8 NULL, -- 指示字符串长度。仅当dataType为string、DateTime时生效。
	"method" varchar(255) NULL, -- 指示访问模式。R:可读；W:可写；E属性值更改时上报数据取值范围：R、RW、RE、RWE
	min varchar(255) NULL, -- 指示最小值。支持长度不超过50的数字。仅当dataType为int、decimal时生效，逻辑大于等于。
	required int4 NULL, -- 指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。(字典值link_product_isRequired：0非必填 1必填)
	step int4 NULL, -- 指示步长。
	unit varchar(255) NULL, -- 指示单位。支持长度不超过50。¶取值根据参数确定，如：¶•温度单位：“C”或“K”¶•百分比单位：“%”¶•压强单位：“Pa”或“kPa”
	create_by varchar(64) NULL, -- 创建者
	create_time timestamp DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新者
	update_time timestamp NULL, -- 更新时间
	template_code varchar(100) NULL, -- 模版code
	pid varchar(100) NULL, -- 产品唯一标识
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_37" PRIMARY KEY (id)
);
COMMENT ON TABLE public.product_properties IS '产品模型属性表';

-- Column comments

COMMENT ON COLUMN public.product_properties.id IS 'id';
COMMENT ON COLUMN public.product_properties.property_name IS '功能名称';
COMMENT ON COLUMN public.product_properties.property_code IS '属性code';
COMMENT ON COLUMN public.product_properties."datatype" IS '指示数据类型：取值范围：string、int、decimal（float和double都可以使用此类型）、DateTime、jsonObject上报数据时，复杂类型数据格式如下：
•DateTime:yyyyMMdd’T’HHmmss’Z’如:20151212T121212Z•jsonObject：自定义json结构体，平台不理解只透传';
COMMENT ON COLUMN public.product_properties.description IS '属性描述，不影响实际功能，可配置为空字符串""。';
COMMENT ON COLUMN public.product_properties.enumlist IS '指示枚举值:如开关状态status可有如下取值"enumList" : ["OPEN","CLOSE"]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。';
COMMENT ON COLUMN public.product_properties.max IS '指示最大值。支持长度不超过50的数字。仅当dataType为int、decimal时生效，逻辑小于等于。';
COMMENT ON COLUMN public.product_properties.maxlength IS '指示字符串长度。仅当dataType为string、DateTime时生效。';
COMMENT ON COLUMN public.product_properties."method" IS '指示访问模式。R:可读；W:可写；E属性值更改时上报数据取值范围：R、RW、RE、RWE';
COMMENT ON COLUMN public.product_properties.min IS '指示最小值。支持长度不超过50的数字。仅当dataType为int、decimal时生效，逻辑大于等于。';
COMMENT ON COLUMN public.product_properties.required IS '指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。(字典值link_product_isRequired：0非必填 1必填)';
COMMENT ON COLUMN public.product_properties.step IS '指示步长。';
COMMENT ON COLUMN public.product_properties.unit IS '指示单位。支持长度不超过50。
取值根据参数确定，如：
•温度单位：“C”或“K”
•百分比单位：“%”
•压强单位：“Pa”或“kPa”';
COMMENT ON COLUMN public.product_properties.create_by IS '创建者';
COMMENT ON COLUMN public.product_properties.create_time IS '创建时间';
COMMENT ON COLUMN public.product_properties.update_by IS '更新者';
COMMENT ON COLUMN public.product_properties.update_time IS '更新时间';
COMMENT ON COLUMN public.product_properties.template_code IS '模版code';
COMMENT ON COLUMN public.product_properties.pid IS '产品唯一标识';
COMMENT ON COLUMN public.product_properties.tenant_id IS '租户ID';
COMMENT ON COLUMN public.product_properties.deleted IS '是否删除';


-- public.product_services definition

-- Drop table

-- DROP TABLE public.product_services;

CREATE TABLE public.product_services (
	id int8 NOT NULL, -- 服务id
	service_code varchar(255) NOT NULL, -- 服务编码:支持英文大小写、数字、下划线和中划线
	service_name varchar(255) NOT NULL, -- 服务名称
	template_code varchar(100) NULL, -- 产品模版标识
	pid varchar(100) NULL, -- 产品标识
	status varchar(10) NOT NULL, -- 状态(字典值：0启用  1停用)
	description varchar(255) NULL, -- 服务的描述信息:文本描述，不影响实际功能，可配置为空字符串""。¶
	create_by varchar(64) NULL, -- 创建者
	create_time timestamp(6) NOT NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新者
	update_time timestamp(6) NOT NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_36" PRIMARY KEY (id)
);
COMMENT ON TABLE public.product_services IS '产品模型服务表';

-- Column comments

COMMENT ON COLUMN public.product_services.id IS '服务id';
COMMENT ON COLUMN public.product_services.service_code IS '服务编码:支持英文大小写、数字、下划线和中划线';
COMMENT ON COLUMN public.product_services.service_name IS '服务名称';
COMMENT ON COLUMN public.product_services.template_code IS '产品模版标识';
COMMENT ON COLUMN public.product_services.pid IS '产品标识';
COMMENT ON COLUMN public.product_services.status IS '状态(字典值：0启用  1停用)';
COMMENT ON COLUMN public.product_services.description IS '服务的描述信息:文本描述，不影响实际功能，可配置为空字符串""。
';
COMMENT ON COLUMN public.product_services.create_by IS '创建者';
COMMENT ON COLUMN public.product_services.create_time IS '创建时间';
COMMENT ON COLUMN public.product_services.update_by IS '更新者';
COMMENT ON COLUMN public.product_services.update_time IS '更新时间';
COMMENT ON COLUMN public.product_services.tenant_id IS '租户ID';
COMMENT ON COLUMN public.product_services.deleted IS '是否删除';


-- public.product_template definition

-- Drop table

-- DROP TABLE public.product_template;

CREATE TABLE public.product_template (
	id int8 NOT NULL, -- id
	app_id varchar(64) NOT NULL, -- 应用ID
	template_code varchar(100) NOT NULL, -- 产品模版标识
	template_name varchar(255) NOT NULL, -- 产品模板名称:自定义，支持中文、英文大小写、数字、下划线和中划线
	status varchar(10) NOT NULL, -- 状态(字典值：启用  停用)
	remark varchar(255) NULL, -- 产品模型模板描述
	create_by varchar(64) NULL, -- 创建者
	create_time timestamp(6) NOT NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新者
	update_time timestamp(6) NOT NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_35" PRIMARY KEY (id)
);
COMMENT ON TABLE public.product_template IS '产品模板表';

-- Column comments

COMMENT ON COLUMN public.product_template.id IS 'id';
COMMENT ON COLUMN public.product_template.app_id IS '应用ID';
COMMENT ON COLUMN public.product_template.template_code IS '产品模版标识';
COMMENT ON COLUMN public.product_template.template_name IS '产品模板名称:自定义，支持中文、英文大小写、数字、下划线和中划线';
COMMENT ON COLUMN public.product_template.status IS '状态(字典值：启用  停用)';
COMMENT ON COLUMN public.product_template.remark IS '产品模型模板描述';
COMMENT ON COLUMN public.product_template.create_by IS '创建者';
COMMENT ON COLUMN public.product_template.create_time IS '创建时间';
COMMENT ON COLUMN public.product_template.update_by IS '更新者';
COMMENT ON COLUMN public.product_template.update_time IS '更新时间';
COMMENT ON COLUMN public.product_template.tenant_id IS '租户ID';
COMMENT ON COLUMN public.product_template.deleted IS '是否删除';


-- public.product_type definition

-- Drop table

-- DROP TABLE public.product_type;

CREATE TABLE public.product_type (
	id int8 NOT NULL, -- id
	"name" varchar(255) NOT NULL, -- 名称
	sort int8 NULL, -- 排序序号
	parent_id varchar(64) NULL, -- 父级ID
	create_by varchar(10) NULL, -- 创建者
	create_time timestamp DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
	update_by varchar(10) NULL, -- 更新者
	update_time timestamp DEFAULT CURRENT_TIMESTAMP NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT product_type_pkey PRIMARY KEY (id)
);
COMMENT ON TABLE public.product_type IS '产品分类表';

-- Column comments

COMMENT ON COLUMN public.product_type.id IS 'id';
COMMENT ON COLUMN public.product_type."name" IS '名称';
COMMENT ON COLUMN public.product_type.sort IS '排序序号';
COMMENT ON COLUMN public.product_type.parent_id IS '父级ID';
COMMENT ON COLUMN public.product_type.create_by IS '创建者';
COMMENT ON COLUMN public.product_type.create_time IS '创建时间';
COMMENT ON COLUMN public.product_type.update_by IS '更新者';
COMMENT ON COLUMN public.product_type.update_time IS '更新时间';
COMMENT ON COLUMN public.product_type.tenant_id IS '租户ID';
COMMENT ON COLUMN public.product_type.deleted IS '是否删除';


-- public.protocol definition

-- Drop table

-- DROP TABLE public.protocol;

CREATE TABLE public.protocol (
	id int8 NOT NULL, -- id
	app_id varchar(64) NOT NULL, -- 应用ID
	pid varchar(100) NOT NULL, -- 产品标识
	protocol_name varchar(255) NULL, -- 协议名称
	protocol_code varchar(255) NULL, -- 协议标识
	protocol_version varchar(255) NULL, -- 协议版本
	protocol_type varchar(255) NULL, -- 协议类型 ：mqtt || coap || modbus || http
	protocol_voice varchar(255) NULL, -- 协议语言
	class_name varchar(255) NULL, -- 类名
	file_path varchar(255) NULL, -- 文件地址
	"content" text NULL, -- 内容
	status varchar(10) NOT NULL, -- 状态(字典值：0启用  1停用)
	create_by varchar(64) NULL, -- 创建者
	create_time timestamp(6) NOT NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新者
	update_time timestamp(6) NOT NULL, -- 更新时间
	remark varchar(500) NULL, -- 备注
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_34" PRIMARY KEY (id)
);
COMMENT ON TABLE public.protocol IS '协议信息表';

-- Column comments

COMMENT ON COLUMN public.protocol.id IS 'id';
COMMENT ON COLUMN public.protocol.app_id IS '应用ID';
COMMENT ON COLUMN public.protocol.pid IS '产品标识';
COMMENT ON COLUMN public.protocol.protocol_name IS '协议名称';
COMMENT ON COLUMN public.protocol.protocol_code IS '协议标识';
COMMENT ON COLUMN public.protocol.protocol_version IS '协议版本';
COMMENT ON COLUMN public.protocol.protocol_type IS '协议类型 ：mqtt || coap || modbus || http';
COMMENT ON COLUMN public.protocol.protocol_voice IS '协议语言';
COMMENT ON COLUMN public.protocol.class_name IS '类名';
COMMENT ON COLUMN public.protocol.file_path IS '文件地址';
COMMENT ON COLUMN public.protocol."content" IS '内容';
COMMENT ON COLUMN public.protocol.status IS '状态(字典值：0启用  1停用)';
COMMENT ON COLUMN public.protocol.create_by IS '创建者';
COMMENT ON COLUMN public.protocol.create_time IS '创建时间';
COMMENT ON COLUMN public.protocol.update_by IS '更新者';
COMMENT ON COLUMN public.protocol.update_time IS '更新时间';
COMMENT ON COLUMN public.protocol.remark IS '备注';
COMMENT ON COLUMN public.protocol.tenant_id IS '租户ID';
COMMENT ON COLUMN public.protocol.deleted IS '是否删除';


-- public."rule" definition

-- Drop table

-- DROP TABLE public."rule";

CREATE TABLE public."rule" (
	id int8 NOT NULL, -- 主键
	app_id varchar(64) NOT NULL, -- 应用ID
	rule_code varchar(100) NOT NULL, -- 规则标识
	rule_name varchar(255) NOT NULL, -- 规则名称
	job_code varchar(255) NOT NULL, -- 任务标识
	status varchar(10) NOT NULL, -- 状态(字典值：0启用  1停用)
	triggering int2 NULL, -- 触发机制（0:全部，1:任意一个）
	remark varchar(255) NULL, -- 规则描述，可以为空
	create_by varchar(64) NULL, -- 创建人
	create_time timestamp(6) NOT NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新人
	update_time timestamp(6) NOT NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_22" PRIMARY KEY (id)
);
COMMENT ON TABLE public."rule" IS '规则信息表';

-- Column comments

COMMENT ON COLUMN public."rule".id IS '主键';
COMMENT ON COLUMN public."rule".app_id IS '应用ID';
COMMENT ON COLUMN public."rule".rule_code IS '规则标识';
COMMENT ON COLUMN public."rule".rule_name IS '规则名称';
COMMENT ON COLUMN public."rule".job_code IS '任务标识';
COMMENT ON COLUMN public."rule".status IS '状态(字典值：0启用  1停用)';
COMMENT ON COLUMN public."rule".triggering IS '触发机制（0:全部，1:任意一个）';
COMMENT ON COLUMN public."rule".remark IS '规则描述，可以为空';
COMMENT ON COLUMN public."rule".create_by IS '创建人';
COMMENT ON COLUMN public."rule".create_time IS '创建时间';
COMMENT ON COLUMN public."rule".update_by IS '更新人';
COMMENT ON COLUMN public."rule".update_time IS '更新时间';
COMMENT ON COLUMN public."rule".tenant_id IS '租户ID';
COMMENT ON COLUMN public."rule".deleted IS '是否删除';


-- public.rule_alarm definition

-- Drop table

-- DROP TABLE public.rule_alarm;

CREATE TABLE public.rule_alarm (
	id int8 NOT NULL, -- 规则告警ID
	rule_id int8 NULL, -- 规则ID
	rule_alarm_name varchar(255) NULL, -- 告警规则名称
	rule_alarm_status int4 NULL, -- 告警状态0 未启动  1运行中
	rule_alarm_remark varchar(255) NULL, -- 告警规则描述
	rule_level int4 NULL, -- 告警级别
	notice_type int4 NULL, -- 通知方式
	create_by varchar(64) NULL, -- 创建人
	create_time timestamp(6) NOT NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新人
	update_time timestamp(6) NOT NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_21" PRIMARY KEY (id)
);
COMMENT ON TABLE public.rule_alarm IS '规则告警表';

-- Column comments

COMMENT ON COLUMN public.rule_alarm.id IS '规则告警ID';
COMMENT ON COLUMN public.rule_alarm.rule_id IS '规则ID';
COMMENT ON COLUMN public.rule_alarm.rule_alarm_name IS '告警规则名称';
COMMENT ON COLUMN public.rule_alarm.rule_alarm_status IS '告警状态0 未启动  1运行中';
COMMENT ON COLUMN public.rule_alarm.rule_alarm_remark IS '告警规则描述';
COMMENT ON COLUMN public.rule_alarm.rule_level IS '告警级别';
COMMENT ON COLUMN public.rule_alarm.notice_type IS '通知方式';
COMMENT ON COLUMN public.rule_alarm.create_by IS '创建人';
COMMENT ON COLUMN public.rule_alarm.create_time IS '创建时间';
COMMENT ON COLUMN public.rule_alarm.update_by IS '更新人';
COMMENT ON COLUMN public.rule_alarm.update_time IS '更新时间';
COMMENT ON COLUMN public.rule_alarm.tenant_id IS '租户ID';
COMMENT ON COLUMN public.rule_alarm.deleted IS '是否删除';


-- public.rule_alarm_list definition

-- Drop table

-- DROP TABLE public.rule_alarm_list;

CREATE TABLE public.rule_alarm_list (
	id int8 NOT NULL, -- 主键
	alarm_time timestamp(6) NULL, -- 告警时间
	alarm_name varchar(255) NULL, -- 告警名称
	alarm_level int4 NULL, -- 告警级别
	alarm_describe varchar(255) NULL, -- 告警描述
	processing_result int4 NULL, -- 处理结果 0 未处理 1已处理
	processing_opinions varchar(255) NULL, -- 处理意见
	alarm_content varchar(500) NULL, -- 告警内容
	processing_people varchar(64) NULL, -- 处理人
	processing_time timestamp(6) NULL, -- 处理时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_20" PRIMARY KEY (id)
);
COMMENT ON TABLE public.rule_alarm_list IS '告警列表';

-- Column comments

COMMENT ON COLUMN public.rule_alarm_list.id IS '主键';
COMMENT ON COLUMN public.rule_alarm_list.alarm_time IS '告警时间';
COMMENT ON COLUMN public.rule_alarm_list.alarm_name IS '告警名称';
COMMENT ON COLUMN public.rule_alarm_list.alarm_level IS '告警级别';
COMMENT ON COLUMN public.rule_alarm_list.alarm_describe IS '告警描述';
COMMENT ON COLUMN public.rule_alarm_list.processing_result IS '处理结果 0 未处理 1已处理';
COMMENT ON COLUMN public.rule_alarm_list.processing_opinions IS '处理意见';
COMMENT ON COLUMN public.rule_alarm_list.alarm_content IS '告警内容';
COMMENT ON COLUMN public.rule_alarm_list.processing_people IS '处理人';
COMMENT ON COLUMN public.rule_alarm_list.processing_time IS '处理时间';
COMMENT ON COLUMN public.rule_alarm_list.tenant_id IS '租户ID';
COMMENT ON COLUMN public.rule_alarm_list.deleted IS '是否删除';


-- public.rule_conditions definition

-- Drop table

-- DROP TABLE public.rule_conditions;

CREATE TABLE public.rule_conditions (
	id int8 NOT NULL, -- 主键
	rule_id int8 NOT NULL, -- 规则ID
	condition_type int2 NOT NULL, -- 条件类型(0:匹配设备触发、1:指定设备触发、2:按策略定时触发)
	did varchar(2000) NULL, -- 设备标识(匹配设备设备类型存储一个产品下所有的设备标识逗号分隔，指定设备触发存储指定的设备标识)
	pid varchar(100) NULL, -- 产品标识
	service_id int8 NULL, -- 服务ID
	properties_id int8 NULL, -- 属性ID
	comparison_mode varchar(255) NULL, -- 比较模式¶<¶<=¶>¶>=¶==¶!=¶in¶between
	comparison_value varchar(255) NULL, -- 比较值¶¶between类型传值例子  [10,15] 必须是两位，且数字不能重复¶判断数据是否处于一个离散的取值范围内，例如输入[1,2,3,4]，取值范围是1、2、3、4四个值，如果比较值类型为float(double)，两个float（double）型数值相差在0.000001范围内即为相等
	create_by varchar(64) NULL, -- 创建人
	create_time timestamp(6) NOT NULL, -- 创建时间
	update_by varchar(64) NULL, -- 更新人
	update_time timestamp(6) NOT NULL, -- 更新时间
	tenant_id int8 NULL, -- 租户ID
	deleted int2 DEFAULT 0 NOT NULL, -- 是否删除
	CONSTRAINT "_copy_19" PRIMARY KEY (id)
);
COMMENT ON TABLE public.rule_conditions IS '规则条件表';

-- Column comments

COMMENT ON COLUMN public.rule_conditions.id IS '主键';
COMMENT ON COLUMN public.rule_conditions.rule_id IS '规则ID';
COMMENT ON COLUMN public.rule_conditions.condition_type IS '条件类型(0:匹配设备触发、1:指定设备触发、2:按策略定时触发)';
COMMENT ON COLUMN public.rule_conditions.did IS '设备标识(匹配设备设备类型存储一个产品下所有的设备标识逗号分隔，指定设备触发存储指定的设备标识)';
COMMENT ON COLUMN public.rule_conditions.pid IS '产品标识';
COMMENT ON COLUMN public.rule_conditions.service_id IS '服务ID';
COMMENT ON COLUMN public.rule_conditions.properties_id IS '属性ID';
COMMENT ON COLUMN public.rule_conditions.comparison_mode IS '比较模式
<
<=
>
>=
==
!=
in
between';
COMMENT ON COLUMN public.rule_conditions.comparison_value IS '比较值

between类型传值例子  [10,15] 必须是两位，且数字不能重复
判断数据是否处于一个离散的取值范围内，例如输入[1,2,3,4]，取值范围是1、2、3、4四个值，如果比较值类型为float(double)，两个float（double）型数值相差在0.000001范围内即为相等';
COMMENT ON COLUMN public.rule_conditions.create_by IS '创建人';
COMMENT ON COLUMN public.rule_conditions.create_time IS '创建时间';
COMMENT ON COLUMN public.rule_conditions.update_by IS '更新人';
COMMENT ON COLUMN public.rule_conditions.update_time IS '更新时间';
COMMENT ON COLUMN public.rule_conditions.tenant_id IS '租户ID';
COMMENT ON COLUMN public.rule_conditions.deleted IS '是否删除';
