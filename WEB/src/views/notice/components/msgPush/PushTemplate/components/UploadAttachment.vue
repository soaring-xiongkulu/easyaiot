<template>
  <div class="upload-attachment-warpper">
    <div class="uaw-list">
      <div class="uaw-item" v-for="(item, index) in dataSource" :key="index">
        <Input v-model:value="item.fileName" />
        <Upload name="file" :show-upload-list="false" @change="handleUploadFile($event, index)">
          <Button>
            <UploadOutlined />
          </Button>
        </Upload>
        <Icon icon="material-symbols:delete-outline-sharp" @click="handleDelete" />
      </div>
    </div>
    <div class="uaw-add" @click="handleAdd" v-if="dataSource.length == 0">
      <Icon icon="material-symbols:add" /> 添加</div
    >
  </div>
</template>
<script lang="ts" setup>
  import { Upload, Input, Button } from 'ant-design-vue';
  import { UploadOutlined } from '@ant-design/icons-vue';
  import { PropType, computed, ref } from 'vue';
  import Icon from '@/components/Icon/index';
  import { messageFileUpload } from '/@/api/modules/notice';
  import { useMessage } from '/@/hooks/web/useMessage';

  type Emits = {
    (e: 'update:attachment', data: any[]): void;
  };
  const { createMessage } = useMessage();
  const emit = defineEmits<Emits>();
  const props = defineProps({
    attachment: {
      type: Array as PropType<any[]>,
      default: () => [],
    },
  });
  const uploadLoading = ref(false);

  const dataSource = computed({
    get: () => props.attachment,
    set: (val) => emit('update:attachment', val),
  });

  const handleDelete = (id: number) => {
    const idx = dataSource.value.findIndex((f) => f.id === id);
    dataSource.value.splice(idx, 1);
  };

  const handleUploadFile = async (info, index) => {
    try {
      if (info.file.status === 'uploading') {
        uploadLoading.value = true;
        return;
      }
      if (info.file.status === 'error') {
        if (info.file.size > 1048576 * 50) {
          createMessage.warning('文件不能超过50MB');
          uploadLoading.value = false;
          return;
        }
        const formData = new FormData();
        formData.append('file', info.file.originFileObj);
        const ret = await messageFileUpload(formData);
        dataSource.value[index].filePath = ret.filePath;
        dataSource.value[index].fileName = ret.fileName;
        uploadLoading.value = false;
      }
    }catch (error) {
    console.error(error)
      console.log(error);
    }
  };

  const handleAdd = () => {
    dataSource.value.push({
      id: dataSource.value.length,
      filePath: '',
      fileName: '',
    });
  };
</script>
<style lang="less" scoped>
  .uaw-item {
    display: flex;
    align-items: center;
    margin-bottom: 5px;
    .app-iconify {
      margin-left: 10px;
    }
    & > input {
      border-right: none;
      border-top-right-radius: 0;
      border-bottom-right-radius: 0;
    }
    .ant-btn {
      border-top-left-radius: 0;
      border-bottom-left-radius: 0;
    }
    & > span {
      background-color: #f9fafa;
    }
  }
</style>
