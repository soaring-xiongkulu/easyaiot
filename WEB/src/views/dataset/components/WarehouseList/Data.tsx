// WarehouseColumns.ts
import { BasicColumn, FormProps } from "@/components/Table";
import { Tag } from "ant-design-vue";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '数据仓ID',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '数据仓名称',
      dataIndex: 'name',
      width: 120,
    },
    {
      title: '关联数据集数量',
      dataIndex: 'datasetCount',
      width: 100,
      customRender: ({ record }) => {
        return record.datasets?.length || 0;
      }
    },
    {
      title: '描述',
      dataIndex: 'description',
      width: 180,
    },
    {
      title: '同步状态',
      dataIndex: 'syncStatus',
      width: 100,
      customRender: ({ text }) => {
        const statusMap = {
          0: { text: '未同步', color: 'default' },
          1: { text: '同步中', color: 'processing' },
          2: { text: '已完成', color: 'success' },
          3: { text: '部分失败', color: 'warning' },
          4: { text: '失败', color: 'error' },
        };
        const status = statusMap[text] || statusMap[0];
        return <Tag color={status.color}>{status.text}</Tag>;
      },
    },
    {
      width: 160,
      title: '操作',
      dataIndex: 'action',
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: { span: 6 },
    schemas: [
      {
        field: `name`,
        label: `数据仓名称`,
        component: 'Input',
      },
      {
        field: `syncStatus`,
        label: `同步状态`,
        component: 'Select',
        componentProps: {
          options: [
            { label: '未同步', value: 0 },
            { label: '同步中', value: 1 },
            { label: '已完成', value: 2 },
            { label: '部分失败', value: 3 },
            { label: '失败', value: 4 },
          ],
        },
      },
    ],
  };
}
