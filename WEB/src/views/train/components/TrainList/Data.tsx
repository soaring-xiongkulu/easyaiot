import {BasicColumn, FormProps} from '@/components/Table';
import {Progress, Tag} from 'ant-design-vue';

const getGradientColor = (percent) => {
  const hue = 120 * (1 - percent/100);
  return `hsl(${hue}, 80%, 45%)`;
};

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '任务ID',
      dataIndex: 'id',
      width: 100,
    },
    {
      title: '数据集URL',
      dataIndex: 'dataset_path',
      width: 200,
    },
    {
      title: '模型配置',
      dataIndex: 'hyperparameters',
      width: 200,
      customRender: ({ text }) => {
        if (!text) return '--';

        // 1. 兼容字符串/对象转换
        let configObj;
        try {
          configObj = typeof text === 'string' ? JSON.parse(text) : text;
        } catch {
          return <Tag color="#8c8c8c">配置异常</Tag>; // 中性灰错误提示[6](@ref)
        }

        // 2. 低饱和度稳重配色（大地色系+莫兰迪灰）
        const colorMap = {
          epochs: '#8A9B6E',     // 橄榄绿灰（自然沉稳）[7,8](@ref)
          model_arch: '#7B6BA8',  // 灰紫色（降低明度）[3](@ref)
          img_size: '#9E9E9E',    // 中灰色（替代跳跃色）[4](@ref)
          batch_size: '#A68B62',   // 深卡其（大地色调）[8](@ref)
          use_gpu: '#5D7092',     // 灰蓝色（冷调平衡）[8](@ref)
          default: '#86909C'      // 中性灰（未匹配项）[6](@ref)
        };

        // 3. 固定展示字段及顺序
        const displayKeys = ['epochs', 'model_arch', 'img_size', 'batch_size', 'use_gpu'];

        return (
          <div class="flex flex-wrap gap-1">
            {displayKeys.map(key => {
              if (configObj.hasOwnProperty(key)) {
                const color = colorMap[key] || colorMap.default;
                return (
                  <Tag
                    class="m-0 rounded-sm font-normal whitespace-nowrap"
                    style={{
                      background: `${color}15`, // 15%透明度背景
                      color: color,
                      border: `1px solid ${color}30`, // 30%透明度边框
                      padding: '2px 6px',       // 增加内边距提升可读性
                      fontSize: '12px'          // 固定字体大小
                    }}
                  >
                    {key}: <span style={{ opacity: 0.9 }}>{String(configObj[key])}</span>
                  </Tag>
                );
              }
              return null;
            })}
          </div>
        );
      }
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      width: 120,
      responsive: ['md'] // 只在中等及以上屏幕显示
    },
    {
      title: '训练进度',
      dataIndex: 'progress',
      width: 140,
      align: 'center',
      customRender: ({ record }) => {
        const progress = record.progress || 0;

        // 动态文字颜色（保持原逻辑）
        const getTextColor = (percent) => percent > 75 ? '#ffffff' : '#000000A6';

        return (
          <div class="progress-container" style={{ position: 'relative' }}>
            <Progress
              percent={progress}
              strokeColor={getGradientColor(progress)}
              strokeWidth={12}
              strokeLinecap="butt"
              showInfo={false}
              class="dynamic-progress"
            />
            <div
              class="progress-text"
              style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                fontWeight: 600,
                fontSize: '14px',
                color: getTextColor(progress),
                textShadow: progress > 75
                  ? '0 0 2px rgba(0,0,0,0.7)'
                  : '0 0 1px rgba(255,255,255,0.8)'
              }}
            >
              {progress}%
            </div>
          </div>
        );
      }
    },
    {
      title: '当前状态',
      dataIndex: 'status',
      width: 90,
      customRender: ({ record }) => {
        // 状态映射配置
        const statusConfig = {
          idle: { color: '#d9d9d9', text: '等待开始', icon: 'clock-circle' },
          preparing: { color: '#13c2c2', text: '准备中', icon: 'loading' },
          training: { color: '#52c41a', text: `训练中 (${record.progress || 0}%)`, icon: 'sync' },
          completed: { color: '#1890ff', text: '已完成', icon: 'check-circle' },
          stopped: { color: '#faad14', text: '已停止', icon: 'pause-circle' },
          error: { color: '#f5222d', text: '失败', icon: 'close-circle' }
        };

        const config = statusConfig[record.status] || {
          color: 'default',
          text: record.status,
          icon: 'question-circle'
        };

        return (
          <div class="items-center">
            <a-icon type={config.icon} style={{ color: config.color}} />
            <Tag color={config.color}>
              {config.text}
            </Tag>
          </div>
        );
      }
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 90,
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: {span: 6},
    schemas: [
      {
        field: 'status',
        label: '状态',
        component: 'Select',
        componentProps: {
          options: [
            {label: '全部', value: ''},
            {label: '运行中', value: 'running'},
            {label: '已完成', value: 'completed'},
            {label: '失败', value: 'failed'},
            {label: '已停止', value: 'stopped'},
          ],
        },
      },
    ],
  };
}
