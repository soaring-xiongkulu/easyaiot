<template>
  <BasicModal @register="register" title="属性历史数据" width="50%" @cancel="handleCancel" @ok="handleSubmit">
    <BasicTable @register="registerTable">
      <template #form-custom1>
        <RadioGroup v-model:value="currentTime" @change="handleChange">
          <RadioButton v-for="(item, index) in timeList" :key="index" :value="item.value">{{
              item.label
            }}
          </RadioButton>
        </RadioGroup>
      </template>
      <template #form-custom>
        <RangePicker
          :key="rangePickerKey"
          v-model="customTime"
          :show-time="true"
          :disabled-date="disabledDate"
          format="YYYY-MM-DD HH:mm:ss"
          @focus="handleClickFocus"
          @calendar-change="calendarPriceRangeChange"
          @change="handleClickChange"
        />
      </template>
    </BasicTable>
  </BasicModal>
</template>

<script lang="ts" setup name="Detail">
import {BasicModal, useModalInner} from '@/components/Modal';
import {BasicTable, useTable} from '@/components/Table';
import {detailColumns, detailSearchSchema} from '../tableData';
import {getDevicethingmodelsHistory} from '@/api/device/devices';
import {reactive, ref} from 'vue';
import moment from 'moment';
import {RadioButton, RadioGroup, RangePicker} from 'ant-design-vue';
import {useRoute} from "vue-router";

const route = useRoute()

const state = reactive({
  unit: '',
  deviceIdentification: '',
  identifier: '',
});

const currentTime = ref<number>(1);
const rangePickerKey = ref<any>(new Date());
const timeList = ref([
  {label: '1小时', value: 1},
  {label: '12小时', value: 12},
  {label: '24小时', value: 24},
  {label: '7天', value: 168},
  {label: '30天', value: 720},
]);
const customTime = ref<any>([]);
const selectPriceDate = ref<any>('');

function getTime() {
  const hour = 60 * 60 * 1000 * currentTime.value;
  const lastUpdateTimeTo = new Date(new Date()).getTime();
  return [lastUpdateTimeTo - hour, lastUpdateTimeTo];
}

function handleChange() {
  if (currentTime.value !== 0) {
    rangePickerKey.value = new Date();
  }
  reload();
}

const params = ref({
  identifier: '',
});

const [register, {closeModal}] = useModalInner(({data}) => {
  // alert(JSON.stringify(data));
  //{"ts":1716447766149,"propertyCode":"humidity","propertyName":"湿度","datatype":"INT","dataValue":"63","key":"d9cfb8de8e5d4aa8a96a6d74ba7e6a8c"}
  setColumns([
    ...detailColumns(),
    {
      title: data.propertyName,
      dataIndex: 'dataValue',
    },
  ]);
  state.unit = data['unit'];
  //console.log('data', data);
  params.value = {
    identifier: data.propertyCode,
  };
  //console.log(params.value);
  state.deviceIdentification = route.params.deviceIdentification + '';
  state.identifier = data.propertyCode;

  reload({
    searchInfo: {
      deviceIdentification: route.params.deviceIdentification,
      identifier: data.propertyCode,
    },
  });
});

const [registerTable, {setColumns, reload}] = useTable({
  resizeHeightOffset: 16,
  api: getDevicethingmodelsHistory,
  formConfig: detailSearchSchema(),
  useSearchForm: true,
  bordered: true,
  showIndexColumn: false,
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  beforeFetch({deviceIdentification, identifier, ...ext}) {
    const tableParams = {
      deviceIdentification: state.deviceIdentification,
      identifier: state.identifier,
      ...ext,
    };
    if (currentTime.value === 0) {
      tableParams.startTime = Date.parse(customTime.value[0]);
      tableParams.endTime = Date.parse(customTime.value[1]);
    } else {
      const result = getTime();
      tableParams.startTime = result[0];
      tableParams.endTime = result[1];
    }
    return tableParams;
  },
  // 立即发起请求
  immediate: false,
});

function handleClickFocus() {
  currentTime.value = 0;
}

/**
 * 获取手动选择的时间段起始值
 */
function calendarPriceRangeChange(date) {
  selectPriceDate.value = date[0];
}

//根据选择的开始时间/结束时间，动态渲染要禁用的日期
function disabledDate(current) {
  if (!selectPriceDate.value) return false;
  return (
    current < moment(selectPriceDate.value).subtract(90, 'days') ||
    current > moment(selectPriceDate.value).add(90, 'days')
  );
}

function handleClickChange(dates) {
  //选择完时间 清空限制
  customTime.value = dates;
  reload();
}

const handleSubmit = () => {
  currentTime.value = 0;
  customTime.value = [];
  closeModal();
  reload({
    page: 1,
  });
};

const handleCancel = () => {
  closeModal();
  reload({
    page: 1,
  });
};
</script>

<style lang="less" scoped>
::v-deep.ant-picker-range {
  width: 390px;
}
</style>
