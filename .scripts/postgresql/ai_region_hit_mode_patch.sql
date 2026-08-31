-- Existing ruoyi-vue-pro20 database patch: algorithm task region hit-mode dictionary.
-- Idempotent: safe to execute repeatedly.
BEGIN;

INSERT INTO public.system_dict_type (
    id, name, type, status, remark, creator, create_time, updater, update_time, deleted, deleted_time
)
SELECT nextval('public.system_dict_type_seq'),
       'AI 区域命中模式', 'ai_region_hit_mode', 0,
       '算法任务区域事件过滤的可选命中方式', 'admin', now(), 'admin', now(), 0,
       timestamp '1970-01-01 00:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM public.system_dict_type
    WHERE type = 'ai_region_hit_mode' AND deleted = 0
);

INSERT INTO public.system_dict_data (
    id, sort, label, value, dict_type, status, color_type, css_class, remark,
    creator, create_time, updater, update_time, deleted
)
SELECT nextval('public.system_dict_data_seq'), seed.sort, seed.label, seed.value,
       'ai_region_hit_mode', 0, seed.color_type, '', seed.remark,
       'admin', now(), 'admin', now(), 0
FROM (VALUES
    (1, '中心点', 'center', 'primary', '检测框中心点位于区域内'),
    (2, '底边中点', 'bottom_center', 'success', '检测框底边中点位于区域内'),
    (3, '任意交集', 'any_intersection', 'warning', '检测框与区域存在交集或边界接触'),
    (4, '区域内面积达到阈值', 'overlap_ratio', 'primary', '检测框区域内面积比例达到任务阈值'),
    (5, '完全位于区域内', 'fully_inside', 'danger', '检测框完全位于区域内')
) AS seed(sort, label, value, color_type, remark)
WHERE NOT EXISTS (
    SELECT 1 FROM public.system_dict_data existing
    WHERE existing.dict_type = 'ai_region_hit_mode'
      AND existing.value = seed.value
      AND existing.deleted = 0
);

COMMIT;
