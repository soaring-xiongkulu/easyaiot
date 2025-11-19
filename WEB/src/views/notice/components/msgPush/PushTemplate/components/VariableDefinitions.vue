<!-- 模板内容-变量列表 -->
<template>
  <div class="table-wrapper">
    <Table :columns="columns" :data-source="dataSource" bordered :pagination="false">
      <template #bodyCell="{ column, record }">
        <span v-if="column.dataIndex === 'id'">
          {{ record[column.dataIndex] }}
        </span>
        <template v-if="column.dataIndex === 'name'">
          <Input
            v-model:value="record.name"
            :class="!record.name || record.name.length > 64 ? 'has-error' : ''"
          />
          <!-- antd useForm 无table表单校验 手动添加校验 -->
          <div class="error-text" v-show="!record.name || record.name.length > 64">
            <span v-show="!record.name"> 该字段是必填字段 </span>
            <span v-show="record.name.length > 64"> 最多可输入64个字符 </span>
          </div>
        </template>
        <Select
          v-if="column.dataIndex === 'type'"
          v-model:value="record.type"
          @change="handleTypeChange(record)"
          :options="typeData"
        />

        <template v-if="column.dataIndex === 'format'">
          <span v-if="record.type === 'string'">
            {{ record.format }}
          </span>
          <Select v-if="record.type === 'date'" v-model:value="record.format" :options="dateData" />
          <Input v-if="record.type === 'double'" v-model:value="record.format">
            <template #suffix>
              <Tooltip title="格式为：%.xf x代表数字保留的小数位数。当x=0时,代表格式为整数">
                <Icon icon="ph:warning-circle-light" />
              </Tooltip>
            </template>
          </Input>
        </template>
      </template>
    </Table>
  </div>
</template>

<script setup lang="ts">
  import { PropType, computed, watch } from 'vue';
  import { Table, Select, Input, Tooltip } from 'ant-design-vue';
  import Icon from '@/components/Icon/index';

  interface IVariable {
    id: string;
    name: string;
    type: string;
    format: string;
  }

  type Emits = {
    (e: 'update:variableDefinitions', data: IVariable[]): void;
  };
  const emit = defineEmits<Emits>();

  const props = defineProps({
    variableDefinitions: {
      type: Array as PropType<IVariable[]>,
      default: () => [],
    },
  });

  const typeData = [
    { value: 'string', label: '字符串' },
    { value: 'date', label: '时间' },
    { value: 'double', label: '数字' },
  ];

  const dateData = [
    { value: 'x', label: 'timestamp' },
    { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
    { value: 'YYYY-MM-DD HH:mm:ss', label: 'YYYY-MM-DD HH:mm:ss' },
  ];

  const columns = [
    {
      title: '变量',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '名称',
      dataIndex: 'name',
      width: 160,
    },
    {
      title: '类型',
      dataIndex: 'type',
      // width: 160,
    },
    {
      title: '格式',
      dataIndex: 'format',
      width: 150,
    },
  ];

  const dataSource = computed({
    get: () => {
      return props.variableDefinitions;
    },
    set: (val) => emit('update:variableDefinitions', val),
  });

  watch(
    () => dataSource.value,
    (val) => {
      emit('update:variableDefinitions', val);
    },
    { deep: true },
  );

  const handleTypeChange = (record: IVariable) => {
    switch (record.type) {
      case 'string':
        record.format = '%s';
        break;
      case 'date':
        record.format = 'timestamp';
        break;
      case 'double':
        record.format = '%.2f';
        break;
    }
  };
</script>

<style lang="less" scoped>
  .table-wrapper {
    .has-error {
      border-color: rgb(255 77 79);

      &:focus {
        border-right-width: 1px !important;
        border-color: rgb(255 120 117);
        outline: 0;
        box-shadow: 0 0 0 2px rgb(255 77 79 / 20%);
      }
    }

    .error-text {
      color: rgb(255 77 79);
      font-size: 12px;
    }
  }
</style>
