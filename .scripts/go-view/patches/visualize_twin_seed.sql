-- 数字孪生演示项目（可重复执行）
BEGIN;

DELETE FROM public.visualize_project WHERE id BETWEEN 9321 AND 9324;

INSERT INTO public.visualize_project
  (id, project_name, project_type, state, index_image, remarks, content, editor_ref,
   tenant_id, creator, updater, deleted)
VALUES
  (9321, '临港智造园数字孪生', 'twin', 1, '/resource/visualize-demo/twin-industrial-cover.svg',
   '工业园区建筑、能源站、设备遥测与告警联动', NULL, 'industrial', 1, 'admin', 'admin', 0),
  (9322, '未来科技大学数字孪生', 'twin', 1, '/resource/visualize-demo/twin-campus-cover.svg',
   '教学楼、图书馆、公寓、场馆与校园物联设施', NULL, 'campus', 1, 'admin', 'admin', 0),
  (9323, '东海智慧港数字孪生', 'twin', 1, '/resource/visualize-demo/twin-port-cover.svg',
   '泊位、岸桥、集装箱堆场、无人集卡与港区气象', NULL, 'port', 1, 'admin', 'admin', 0),
  (9324, '西北零碳能源基地数字孪生', 'twin', 1, '/resource/visualize-demo/twin-energy-cover.svg',
   '光伏、风电、储能、升压站与并网运行态势', NULL, 'energy', 1, 'admin', 'admin', 0);

SELECT setval('public.visualize_project_seq', GREATEST((SELECT COALESCE(MAX(id), 1) FROM public.visualize_project), 1));
COMMIT;
