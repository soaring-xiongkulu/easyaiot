import {BasicColumn} from '@/components/Table/src/types/table';

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '视频地址',
      dataIndex: 'videoPath',
      width: 120,
    },
    {
      title: '封面地址',
      dataIndex: 'coverPath',
      width: 120,
    },
    {
      title: '描述',
      dataIndex: 'description',
      width: 120,
    },
    {
      width: 90,
      title: '操作',
      dataIndex: 'action',
    },
  ];
}
