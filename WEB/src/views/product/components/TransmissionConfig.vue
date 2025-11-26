<template>
  <div class="transmission-detail">
    <Table :columns="columns" :data-source="state.tableData" :pagination="false" size="small" />
  </div>
</template>
<script lang="ts" setup>
  import { ref, defineComponent, h, onMounted, watch, reactive } from 'vue';
  import { Table } from 'ant-design-vue';
  const props = defineProps({
    detail: {
      type: Object,
      require: true,
      default: () => ({}),
    },
  });

  const state = reactive({
    tableData: [],
  });

  const columns: ColumnProps[] = [
    {
      title: '接入协议',
      dataIndex: 'transportType',
    },
  ];

  function setTableData(detail) {
    state.tableData.push({
      transportType: detail.transportType,
    });
    //console.log('state.tableData ...', state.tableData);
  }

  onMounted(() => {
    setTableData(props.detail);
  });
</script>

<style lang="less" scoped>
  .transmission-detail {
    border: 1px solid #f0f0f0;
    width: 100%;
    overflow: hidden;
    border-radius: 2px;
    border-bottom: none;
  }
</style>
