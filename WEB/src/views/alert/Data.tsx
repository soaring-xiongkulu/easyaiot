import {BasicColumn, FormProps} from "@/components/Table";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '设备ID',
      dataIndex: 'device_id',
      width: 120,
    },
    {
      title: '设备名称',
      dataIndex: 'device_name',
      width: 120,
    },
    {
      title: '告警时间',
      dataIndex: 'time',
      width: 120,
    },
    {
      title: '告警事件',
      dataIndex: 'event',
      width: 120,
    },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      width: 100,
      customRender: ({text}) => {
        if (!text) {
          return '实时';
        }
        // 兼容 'snap' 和 'snapshot' 两种值
        if (text === 'snap' || text === 'snapshot') {
          return '抓拍';
        } else if (text === 'realtime') {
          return '实时';
        }
        return text;
      },
    },
    {
      title: '告警对象',
      dataIndex: 'object',
      width: 120,
    },
    {
      title: '检测区域',
      dataIndex: 'region',
      width: 120,
      customRender: ({text}) => {
        if (text === null) {
          return '不限区域';
        }
        return text;
      },
    },
    {
      width: 120,
      title: '操作',
      dataIndex: 'action',
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 120,
    baseColProps: {span: 6},
    schemas: [
      {
        field: `object`,
        label: `告警对象`,
        component: 'Select',
        componentProps: {
          options: [
            {value: null, label: '全部'},
            {value: "人", label: "人"},
            {value: "自行车", label: "自行车"},
            {value: "汽车", label: "汽车"},
            {value: "摩托车", label: "摩托车"},
            {value: "飞机", label: "飞机"},
            {value: "公共汽车", label: "公共汽车"},
            {value: "火车", label: "火车"},
            {value: "卡车", label: "卡车"},
            {value: "船", label: "船"},
            {value: "交通灯", label: "交通灯"},
            {value: "消防栓", label: "消防栓"},
            {value: "停车标志", label: "停车标志"},
            {value: "停车收费表", label: "停车收费表"},
            {value: "长凳", label: "长凳"},
            {value: "鸟", label: "鸟"},
            {value: "猫", label: "猫"},
            {value: "狗", label: "狗"},
            {value: "马", label: "马"},
            {value: "羊", label: "羊"},
            {value: "母牛", label: "母牛"},
            {value: "大象", label: "大象"},
            {value: "熊", label: "熊"},
            {value: "斑马", label: "斑马"},
            {value: "长颈鹿", label: "长颈鹿"},
            {value: "背包", label: "背包"},
            {value: "雨伞", label: "雨伞"},
            {value: "手提包", label: "手提包"},
            {value: "领带", label: "领带"},
            {value: "手提箱", label: "手提箱"},
            {value: "飞盘", label: "飞盘"},
            {value: "滑雪板", label: "滑雪板"},
            {value: "运动用球", label: "运动用球"},
            {value: "风筝", label: "风筝"},
            {value: "棒球棍", label: "棒球棍"},
            {value: "棒球手套", label: "棒球手套"},
            {value: "滑板", label: "滑板"},
            {value: "冲浪板", label: "冲浪板"},
            {value: "网球拍", label: "网球拍"},
            {value: "瓶子", label: "瓶子"},
            {value: "酒杯", label: "酒杯"},
            {value: "杯子", label: "杯子"},
            {value: "叉", label: "叉"},
            {value: "刀", label: "刀"},
            {value: "勺子", label: "勺子"},
            {value: "碗", label: "碗"},
            {value: "香蕉", label: "香蕉"},
            {value: "苹果", label: "苹果"},
            {value: "三明治", label: "三明治"},
            {value: "橙子", label: "橙子"},
            {value: "西兰花", label: "西兰花"},
            {value: "胡萝卜", label: "胡萝卜"},
            {value: "热狗", label: "热狗"},
            {value: "披萨", label: "披萨"},
            {value: "甜甜圈", label: "甜甜圈"},
            {value: "糕饼", label: "糕饼"},
            {value: "椅子", label: "椅子"},
            {value: "沙发", label: "沙发"},
            {value: "盆栽植物", label: "盆栽植物"},
            {value: "床", label: "床"},
            {value: "餐桌", label: "餐桌"},
            {value: "马桶", label: "马桶"},
            {value: "显示器", label: "显示器"},
            {value: "笔记本电脑", label: "笔记本电脑"},
            {value: "鼠标", label: "鼠标"},
            {value: "遥控器", label: "遥控器"},
            {value: "键盘", label: "键盘"},
            {value: "手机", label: "手机"},
            {value: "微波炉", label: "微波炉"},
            {value: "烤箱", label: "烤箱"},
            {value: "烤面包机", label: "烤面包机"},
            {value: "洗手池", label: "洗手池"},
            {value: "冰箱", label: "冰箱"},
            {value: "书", label: "书"},
            {value: "时钟", label: "时钟"},
            {value: "花瓶", label: "花瓶"},
            {value: "剪刀", label: "剪刀"},
            {value: "泰迪熊", label: "泰迪熊"},
            {value: "吹风机", label: "吹风机"},
            {value: "牙刷", label: "牙刷"},
          ]
        }
      },
      {
        field: `event`,
        label: `告警事件`,
        component: 'Select',
        componentProps: {
          options: [
            {value: null, label: '全部'},
            {value: "行人检测", label: "行人检测"},
          ]
        }
      },
      {
        field: '[begin_datetime, end_datetime]',
        label: '告警时间',
        component: 'RangePicker',
        componentProps: {
          format: 'YYYY-MM-DD HH:mm:ss',
          placeholder: ['开始时间', '结束时间'],
          showTime: { format: 'HH:mm:ss' },
        },
      },
    ]
  }
}
