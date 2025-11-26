import { FormProps } from '@/components/Table';
import { BasicColumn } from '@/components/Table/src/types/table';
import { Tooltip } from 'ant-design-vue';
import { CopyOutlined } from '@ant-design/icons-vue';
import { copyText } from '@/utils/copyText';

import type { DescItem } from '@/components/Description';

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '名称',
      dataIndex: 'label',
    },
    {
      title: '状态',
      dataIndex: 'root',
    },
  ];
}
export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 70,
    baseColProps: {
      span: 6,
    },
    schemas: [
      {
        field: `productName`,
        label: `规则名称`,
        component: 'Input',
      },
      {
        field: `model`,
        label: `规则型号`,
        component: 'Input',
      },
      {
        field: `manufacturerName`,
        label: `规则描述`,
        component: 'Input',
      },
    ],
  };
}

export const detailSchmea = (): DescItem[] => {
  return [
    {
      field: 'id',
      label: '规则链ID',
      span: 3,
      render(val) {
        console.log(val);
        return (
          <div>
            {val}
            <Tooltip title="复制规则链ID">
              <CopyOutlined
                class="app-iconify cursor-pointer ml-5px"
                onClick={() => copyText(val, '规则链ID')}
              />
            </Tooltip>
          </div>
        );
      },
    },
    {
      field: 'label',
      label: '名称',
    },
    {
      field: 'disabled',
      label: '状态',
      render(val) {
        return val ? '禁用' : '启用';
      },
    },
  ];
};
