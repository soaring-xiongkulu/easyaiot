import {BasicColumn, FormProps} from "@/components/Table";
import {Progress, Tag} from "ant-design-vue";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '数据集编码',
      dataIndex: 'datasetCode',
      width: 90,
    },
    {
      title: '数据集名称',
      dataIndex: 'name',
      width: 90,
    },
    {
      title: '标注进度',
      dataIndex: 'annotationProgress',
      width: 90,
      customRender: ({ record }) => {
        // 计算进度百分比
        const total = record.totalImages || 0;
        const annotated = record.annotatedImages || 0;
        const percent = total ? Math.round((annotated / total) * 100) : 0;

        // 根据进度选择颜色
        let strokeColor = '#52c41a'; // 绿色
        if (percent < 30) strokeColor = '#ff4d4f'; // 红色
        else if (percent < 70) strokeColor = '#faad14'; // 黄色

        return (
          <div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
              <span>{annotated}/{total}</span>
              <span>{percent}%</span>
            </div>
            <Progress
              percent={percent}
              strokeColor={strokeColor}
              size="small"
              showInfo={false}
            />
          </div>
        );
      }
    },
    {
      title: '封面地址',
      dataIndex: 'coverPath',
      width: 90,
    },
    {
      title: '数据集类型',
      dataIndex: 'datasetType',
      width: 90,
      customRender: ({text}) => {
        if (text === null) {
          return '--';
        }
        return text == 0 ? '图片' : '文本';
      },
    },
    {
      title: '数据集状态',
      dataIndex: 'audit',
      width: 90,
      customRender: ({text}) => {
        if (text === null) {
          return '--';
        }
        return text == 0 ? <Tag color="blue">待审核</Tag> : text == 1 ?
          <Tag color="green">审核通过</Tag> : <Tag color="red">审核驳回</Tag>;
      },
    },
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
        label: `数据集名称`,
        component: 'Input',
      },
    ],
  };
}
