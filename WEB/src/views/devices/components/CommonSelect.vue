<template>
  <Select
    :value="props.value"
    :placeholder="placeholderText"
    :options="list"
    @focus="getList"
    @popup-scroll="handlePopupScroll"
    @change="handleClickChange"
  />
</template>

<script setup lang="ts">
import {Select} from 'ant-design-vue';
import {defineEmits, defineExpose, defineProps, reactive, ref} from 'vue';

defineExpose({
  getSelectData,
});
const props = defineProps({
  value: {
    type: String || null,
    default: '',
  },
  placeholderText: {
    type: String,
    default: '请选择',
  },
  id: {
    type: String,
    default: '',
  },
  listFunc: {
    type: Function,
  },
  defaultValue: {
    type: Object,
    default: () => {
      return {label: '全部', value: ''};
    },
  },
});
const emits = defineEmits(['update:value']);

const list = ref([props.defaultValue]);
const deviceParams = reactive({
  pageSize: 10,
  page: 1,
});

// 下拉框下拉加载
function handlePopupScroll(event) {
  const {scrollHeight, scrollTop, clientHeight} = event.target;
  if (scrollHeight - scrollTop === clientHeight) {
    deviceParams.pageSize += 10;
    getList();
  }
}

async function getList() {
  const {data} = await props.listFunc(deviceParams);
  const tempList = data.map((item) => {
    return {
      label: item.name,
      value: item.id.id,
      id: item.id,
    };
  });
  const tempValue = props.defaultValue;
  list.value = Object.keys(tempValue).length > 0 ? [tempValue] : [];
  list.value = [...list.value, ...tempList];
}

function handleClickChange(value) {
  //console.log('update:value', value);
  emits('update:value', value);
}

function getSelectData(key: string) {
  //console.log('key', key);
  return list.value.filter((item) => item.value === key)[0].id;
}
</script>
