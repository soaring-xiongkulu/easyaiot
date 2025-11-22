import {FormSchema} from '@/components/Table';

export const getFormConfig = (): FormSchema[] => {
  return [
    {
      field: 'name',
      label: '模型名称',
      component: 'Input',
      componentProps: {
        placeholder: '请输入模型名称',
      },
    },
    {
      field: 'version',
      label: '模型版本',
      component: 'Input',
      componentProps: {
        placeholder: '请输入模型版本',
      },
    },
  ];
};

