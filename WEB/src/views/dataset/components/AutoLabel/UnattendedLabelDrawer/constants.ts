import { SETUP_FORM_LABEL_COL, SETUP_FORM_WRAPPER_COL } from '@/views/node/utils/constants';

export { SETUP_FORM_LABEL_COL, SETUP_FORM_WRAPPER_COL };

export const COPY = {
  drawerTitle: '无人值守扩充',
  drawerDesc: '选择摄像头抽帧任务，由模型自动打标并写入当前数据集',
  tabs: { config: '任务配置', monitor: '运行监控' },
  steps: {
    model: { title: '标注模型', desc: '模型与检测类别' },
    cameras: { title: '摄像头', desc: '本数据集抽帧任务' },
    deploy: { title: '运行方式', desc: '本机或集群调度' },
  },
  model: {
    originFilter: '模型来源',
    originAll: '全部可用',
    empty: '暂无带权重的模型',
    hint: '支持任意来源检测模型；选定后优先 YOLO 自动打标，无需人工逐张标注。',
    label: '标注模型',
  },
  cameras: {
    empty: '请先在「数据来源 → 视频流抽帧」中创建任务',
    hint: '每路抽帧任务对应一个摄像头/场景；集群模式按负载分发到多台节点。',
    selectAll: '全选',
    goFrameTasks: '去配置抽帧任务',
  },
  deploy: {
    execution: '执行方式',
    duration: '运行时长（小时）',
    interval: '抽帧间隔（秒）',
    annotatedOnly: '仅保留有标注图片',
    annotatedOnlyHint:
      '开启后，未检测到目标的抽帧图片会自动从数据集中删除；关闭后保留为待标注图片。',
    autoExport: '结束后自动划分用途并打包导出',
    scheduleHint: '集群模式需节点已挂载 Ceph、已分发 auto_label Worker。',
    nodeSync: '节点管理',
    start: '启动无人值守扩充',
  },
  footer: {
    close: '关闭',
    minimize: '收起',
    prev: '上一步',
    next: '下一步',
    pause: '暂停',
    resume: '继续',
    cancel: '取消任务',
    cancelConfirm: '确认取消？已写入数据集的标注将保留。',
  },
  monitor: {
    empty: '暂无运行中的无人值守任务，完成配置后点击启动。',
    progress: '执行进度',
    metrics: '运行指标',
    subtasks: '摄像头子任务',
    logs: '运行日志',
    paused: '任务已暂停',
    cancelled: '任务已取消',
    failed: '任务执行失败',
    completed: '无人值守扩充已完成，请刷新图片列表查看新标注',
  },
} as const;

export const EXECUTION_MODE_OPTIONS = [
  { label: '本机运行', value: 'local' as const },
  { label: '集群多节点', value: 'cluster' as const },
];
