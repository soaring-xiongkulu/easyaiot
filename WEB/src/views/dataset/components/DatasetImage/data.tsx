import {FormProps} from '@/components/Table';
import {BasicColumn} from '@/components/Table/src/types/table';

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '图片名称',
      dataIndex: 'name',
      width: 120,
    },
    // 新增数据集类型列
    {
      title: '数据集类型',
      dataIndex: 'usageType',
      width: 100,
    },
    // 新增标注状态列
    {
      title: '标注状态',
      dataIndex: 'completed',
      width: 100,
    },
    {
      title: '图片地址',
      dataIndex: 'path',
      width: 120,
    },
    // ... 其他列保持不变 ...
    {
      width: 90,
      title: '操作',
      dataIndex: 'action',
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: {span: 6},
    schemas: [
      {
        field: `name`,
        label: `图片名称`,
        component: 'Input',
      },
      // 新增搜索条件
      {
        field: `usageType`,
        label: `数据集类型`,
        component: 'Select',
        componentProps: {
          options: [
            {label: '全部', value: 0},
            {label: '训练集', value: 1},
            {label: '验证集', value: 2},
            {label: '测试集', value: 3},
          ],
        },
      },
      {
        field: `completed`,
        label: `标注状态`,
        component: 'Select',
        componentProps: {
          options: [
            {label: '全部', value: -1},
            {label: '待标注', value: 0},
            {label: '已标注', value: 1},
          ],
        },
      },
    ],
  };
}
