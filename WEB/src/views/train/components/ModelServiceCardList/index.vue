<template>
  <div class="model-card-list-wrapper p-2">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm" @reset="handleSubmit"/>
    </div>
    <div class="p-2 bg-white">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 2, xs: 1, sm: 2, md: 4, lg: 4, xl: 6, xxl: 6 }"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div
              style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;"
            >
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">
                模型服务列表
              </span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem style="padding: 0;
                background: #FFFFFF;
                box-shadow: 0px 0px 4px 0px rgba(24, 24, 24, 0.1);
                height: 100%;
                transition: all 0.3s;
            }">
              <div class="model-card">
                <!-- 模型卡片头部 -->
                <div class="model-header">
                  <h6 class="model-title">
                    <a>{{ item.model_name }}</a>
                  </h6>
                  <div class="model-id">ID: {{ item.model_id }}</div>
                </div>

                <!-- 模型信息区域 -->
                <div class="model-info">
                  <div class="info-row">
                    <span class="info-label">版本：</span>
                    <span class="info-value">{{ item.model_version }}</span>
                  </div>
                  <div class="info-row">
                    <span class="info-label">创建时间：</span>
                    <span class="info-value">{{ formatDate(item.created_at) }}</span>
                  </div>
                  <div class="info-row">
                    <span class="info-label">存储路径：</span>
                    <span class="info-value truncate">{{
                        shortenPath(item.minio_model_path)
                      }}</span>
                  </div>
                </div>

                <!-- 状态区域 -->
                <div class="status-section">
                  <Tag :color="item.status === 'running' ? 'green' : 'red'">
                    {{ item.status === 'running' ? '运行中' : '已停止' }}
                  </Tag>

                  <div class="resource-usage">
                    <div class="usage-row">
                      <span>CPU：</span>
                      <Progress
                        :percent="item.cpu_usage || 0"
                        :stroke-color="getUsageColor(item.cpu_usage)"
                        size="small"
                        :showInfo="false"
                      />
                    </div>
                    <div class="usage-row">
                      <span>内存：</span>
                      <Progress
                        :percent="item.memory_usage || 0"
                        :stroke-color="getUsageColor(item.memory_usage)"
                        size="small"
                        :showInfo="false"
                      />
                    </div>
                  </div>
                </div>

                <!-- 操作按钮区域 -->
                <div class="btns">
                  <div class="btn" @click="handleView(item)">
                    <img
                      src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAABDpJREFUWEetV0FyWkcQff0VK1VKFningFOFbgAnAJ3A+ATGVQHJ2ZicAHQCS7sEVGVyAqETgE4gfAKziABXFmZjWQViXqpHf74+X4MEOOyomd/zpvu91z2CDX6pGlM716gBeA0gG4boQ9AXojcPcDH+UwarhJZVNsX3vDhkkXOcUZB64tsBBD0Q59c76E2OZeLbvxaATIU5Ci41EIkegca4JRf6X9cMUBBBEUQRDwF2BOhcNeXvOJC1AKSr/KQpNwaN8akcPZaB3bcsyC1yCFASBRT+LPAtvHElWhnAr1WW5sAZgcGoKXvrlG63zCyeoSiCutxxZnA9RX7SlsnKANIH/ACiTKI2asnJOgDcXgUi2+haEAaN4akcrQQgZL3WPmum2Bu3V2O4D+TuIYuBQRfE5HqGvaUAlO3G2LQVGNZwk/T7QPxywK7ywhjsLwDYPWRWiHeBQdkrM6I9bMmbTdIf/8aVU4ByBCDzG2sM8D5iK6BG0hFBT4gGgdzcoPT5VM7/BwBnIEoazwJIV9kAULeBibYB2k7f2TJT02180aXrKZ4rc78bQCjnGZEXTXtgoPqGAcrjhFGEXOiqfkct2f/ew6PziMmwJc/F1UNv7qtvpsr3BGoEjkdN+SOS1CGzW3NcUjCgoLc1x/k/p9J7CmCmQuXXBwKdUVNeiXM3Tce/LeknA2SqvNT6G6LoyuKsF0A3SVZtRmq5BC6uPPGSfqIAqAGHTXkgyXj9fev6nbXcuSWT2m0ufgFf2ZIXlkyFX/QWPoKtW/9UmamdH1GAQYmComYjXtbM78zxFprRyM4lSrHB/jhRwxcVvjOCY2/9iTpo2+1HX6p9XHDx4nxTAJZkzpsXDKNKlaZKtDFs3ne/KND9Ztv7ZwYnPh65bZkDqpqKcbVJ1OU8MnOMhaA9/GvRAXcrLAeCl0rQsMPpjNAftSS/TAmu3PF+IhHRwuYQN5r4mtlCftmY5YaRYIaLq/ZDJSmgGJ8WQFrmx5tDkgfpKs8AlAj0v02xv6kTRvJL+ImzYlvrJNmszOI9HBgI0Pi6g/NlM96SFqxu2/W1cwvA9ehlNUyAsGc8ZTgJMrssWveLr1kAWuvZM3xa5geR/VZYlgCv4zNeuKadt68O6GSpQ8zPN8gZYztsTgcQM0M+OcxE7ud4oD06Obkm0+pmvAAoWMO5fxt4BaDGE0zxykfQCECkbY/kVmgwuTmQU1mGDxVryUpcGnRubnGyjLwRgHib1FltY7aHs4XemlPsPzU/LjSgdcqQzIp9MRF1Nz/OidrnFabnxZnwzt10/J48Zjx6uJLsp68oIYiaz91TjZjMgcYqh1s1JW/ijEcDkTjiD+ioA2YPmZ0a6NOsEKpgsfVqyg3aj9XbxyXvDDDbRt02qMd+ChDQAaYTLBk+niKvNwPuo/QBX+pLKHpougMFfRKdmxk+bkrUOLD/AJnzscretOw/AAAAAElFTkSuQmCC"
                      alt=""
                    >
                    <span>详情</span>
                  </div>

                  <div class="btn" @click="toggleServiceStatus(item)">
                    <img
                      :src="item.status === 'running' ?
                        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAABDpJREFUWEetV0FyWkcQff0VK1VKFningFOFbgAnAJ3A+ATGVQHJ2ZicAHQCS7sEVGVyAqETgE4gfAKziABXFmZjWQViXqpHf74+X4MEOOyomd/zpvu91z2CDX6pGlM716gBeA0gG4boQ9AXojcPcDH+UwarhJZVNsX3vDhkkXOcUZB64tsBBD0Q59c76E2OZeLbvxaATIU5Ci41EIkegca4JRf6X9cMUBBBEUQRDwF2BOhcNeXvOJC1AKSr/KQpNwaN8akcPZaB3bcsyC1yCFASBRT+LPAtvHElWhnAr1WW5sAZgcGoKXvrlG63zCyeoSiCutxxZnA9RX7SlsnKANIH/ACiTKI2asnJOgDcXgUi2+haEAaN4akcrQQgZL3WPmum2Bu3V2O4D+TuIYuBQRfE5HqGvaUAlO3G2LQVGNZwk/T7QPxywK7ywhjsLwDYPWRWiHeBQdkrM6I9bMmbTdIf/8aVU4ByBCDzG2sM8D5iK6BG0hFBT4gGgdzcoPT5VM7/BwBnIEoazwJIV9kAULeBibYB2k7f2TJT02180aXrKZ4rc78bQCjnGZEXTXtgoPqGAcrjhFGEXOiqfkct2f/ew6PziMmwJc/F1UNv7qtvpsr3BGoEjkdN+SOS1CGzW3NcUjCgoLc1x/k/p9J7CmCmQuXXBwKdUVNeiXM3Tce/LeknA2SqvNT6G6LoyuKsF0A3SVZtRmq5BC6uPPGSfqIAqAGHTXkgyXj9fev6nbXcuSWT2m0ufgFf2ZIXlkyFX/QWPoKtW/9UmamdH1GAQYmComYjXtbM78zxFprRyM4lSrHB/jhRwxcVvjOCY2/9iTpo2+1HX6p9XHDx4nxTAJZkzpsXDKNKlaZKtDFs3ne/KND9Ztv7ZwYnPh65bZkDqpqKcbVJ1OU8MnOMhaA9/GvRAXcrLAeCl0rQsMPpjNAftSS/TAmu3PF+IhHRwuYQN5r4mtlCftmY5YaRYIaLq/ZDJSmgGJ8WQFrmx5tDkgfpKs8AlAj0v02xv6kTRvJL+ImzYlvrJNmszOI9HBgI0Pi6g/NlM96SFqxu2/W1cwvA9ehlNUyAsGc8ZTgJMrssWveLr1kAWuvZM3xa5geR/VZYlgCv4zNeuKdt68O6GSpQ8zPN8gZYztsTgcQM0M+OcxE7ud4oD06Obkm0+pmvAAoWMO5fxt4BaDGE0zxykfQCECkbY/kVmgwuTmQU1mGDxVryUpcGnRubnGyjLwRgHib1FltY7aHs4XemlPsPzU/LjSgdcqQzIp9MRF1Nz/OidrnFabnxZnwzt10/J48Zjx6uJLsp68oIYiaz91TjZjMgcYqh1s1JW/ijEcDkTjiD+ioA2YPmZ0a6NOsEKpgsfVqyg3aj9XbxyXvDDDbRt02qMd+ChDQAaYTLBk+niKvNwPuo/QBX+pLKHpougMFfRKdmxk+bkrUOLD/AJnzscretOw/AAAAAElFTkSuQmCC' :
                        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAABDpJREFUWEetV0FyWkcQff0VK1VKFningFOFbgAnAJ3A+ATGVQHJ2ZicAHQCS7sEVGVyAqETgE4gfAKziABXFmZjWQViXqpHf74+X4MEOOyomd/zpvu91z2CDX6pGlM716gBeA0gG4boQ9AXojcPcDH+UwarhJZVNsX3vDhkkXOcUZB64tsBBD0Q59c76E2OZeLbvxaATIU5Ci41EIkegca4JRf6X9cMUBBBEUQRDwF2BOhcNeXvOJC1AKSr/KQpNwaN8akcPZaB3bcsyC1yCFASBRT+LPAtvHElWhnAr1WW5sAZgcGoKXvrlG63zCyeoSiCutxxZnA9RX7SlsnKANIH/ACiTKI2asnJOgDcXgUi2+haEAaN4akcrQQgZL3WPmum2Bu3V2O4D+TuIYuBQRfE5HqGvaUAlO3G2LQVGNZwk/T7QPxywK7ywhjsLwDYPWRWiHeBQdkrM6I9bMmbTdIf/8aVU4ByBCDzG2sM8D5iK6BG0hFBT4gGgdzcoPT5VM7/BwBnIEoazwJIV9kAULeBibYB2k7f2TJT02180aXrKZ4rc78bQCjnGZEXTXtgoPqGAcrjhFGEXOiqfkct2f/ew6PziMmwJc/F1UNv7qtvpsr3BGoEjkdN+SOS1CGzW3NcUjCgoLc1x/k/p9J7CmCmQuXXBwKdUVNeiXM3Tce/LeknA2SqvNT6G6LoyuKsF0A3SVZtRmq5BC6uPPGSfqIAqAGHTXkgyXj9fev6nbXcuSWT2m0ufgFf2ZIXlkyFX/QWPoKtW/9UmamdH1GAQYmComYjXtbM78zxFprRyM4lSrHB/jhRwxcVvjOCY2/9iTpo2+1HX6p9XHDx4nxTAJZkzpsXDKNKlaZKtDFs3ne/KND9Ztv7ZwYnPh65bZkDqpqKcbVJ1OU8MnOMhaA9/GvRAXcrLAeCl0rQsMPpjNAftSS/TAmu3PF+IhHRwuYQN5r4mtlCftmY5YaRYIaLq/ZDJSmgGJ8WQFrmx5tDkgfpKs8AlAj0v02xv6kTRvJL+ImzYlvrJNmszOI9HBgI0Pi6g/NlM96SFqxu2/W1cwvA9ehlNUyAsGc8ZTgJMrssWveLr1kAWuvZM3xa5geR/VZYlgCv4zNeuKdt68O6GSpQ8zPN8gZYztsTgcQM0M+OcxE7ud4oD06Obkm0+pmvAAoWMO5fxt4BaDGE0zxykfQCECkbY/kVmgwuTmQU1mGDxVryUpcGnRubnGyjLwRgHib1FltY7aHs4XemlPsPzU/LjSgdcqQzIp9MRF1Nz/OidrnFabnxZnwzt10/J48Zjx6uJLsp68oIYaz91TjZjMgcYqh1s1JW/ijEcDkTjiD+ioA2YPmZ0a6NOsEKpgsfVqyg3aj9XbxyXvDDDbRt02qMd+ChDQAaYTLBk+niKvNwPuo/QBX+pLKHpougMFfRKdmxk+bkrUOLD/AJnzscretOw/AAAAAElFTkSuQmCC'"
                      alt=""
                    >
                    <span>{{ item.status === 'running' ? '停止' : '启动' }}</span>
                  </div>
                </div>
              </div>
            </ListItem>
          </template>
        </List>
      </Spin>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, reactive, ref} from 'vue';
import {List, Progress, Spin, Tag} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {useMessage} from '@/hooks/web/useMessage';
import {startTrain, stopTrain} from '@/api/device/model';

const ListItem = List.Item;
const {createMessage} = useMessage();

// 组件接收参数
const props = defineProps({
  // 请求API的参数
  params: propTypes.object.def({}),
  // API函数
  api: propTypes.func,
});

// 暴露内部方法
const emit = defineEmits(['getMethod', 'view', 'toggleStatus']);

// 数据状态
const data = ref([]);
const state = reactive({
  loading: true,
});

// 表单
const [registerForm, {validate}] = useForm({
  schemas: [
    {
      field: 'model_name',
      label: '模型名称',
      component: 'Input',
    },
    {
      field: 'status',
      label: '状态',
      component: 'Select',
      componentProps: {
        options: [
          {label: '全部', value: ''},
          {label: '运行中', value: 'running'},
          {label: '已停止', value: 'stopped'},
        ],
      },
    },
  ],
  labelWidth: 80,
  baseColProps: {span: 6},
  actionColOptions: {span: 18},
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

// 表单提交
async function handleSubmit() {
  const formData = await validate();
  await fetch(formData);
}

// 自动请求并暴露内部方法
onMounted(() => {
  fetch();
  emit('getMethod', fetch);
});

// 获取数据
async function fetch(p = {}) {
  try {
    state.loading = true;
    const {api, params} = props;
    if (api && isFunction(api)) {
      const res = await api({...params, ...p});
      data.value = res.data.list || res.data;
      total.value = res.data.total || res.data.length;
    }
  } catch (error) {
    console.error('获取模型服务失败:', error);
    createMessage.error('获取模型服务失败');
  } finally {
    state.loading = false;
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
};

// 缩短路径显示
const shortenPath = (path) => {
  if (!path) return '-';
  if (path.length <= 30) return path;
  return `${path.substring(0, 15)}...${path.substring(path.length - 15)}`;
};

// 根据使用率获取颜色
const getUsageColor = (percent) => {
  if (!percent) return '#d9d9d9';
  if (percent < 50) return '#52c41a';
  if (percent < 80) return '#faad14';
  return '#ff4d4f';
};

// 切换服务状态
const toggleServiceStatus = async (item) => {
  try {
    state.loading = true;
    if (item.status === 'running') {
      await stopTrain(item.model_id);
      createMessage.success('服务已停止');
    } else {
      await startTrain(item.model_id); // 这里调用了 startTrain
      createMessage.success('服务已启动');
    }
    await fetch();
  } catch (error) {
    console.error('操作失败:', error);
    createMessage.error(`操作失败: ${error.message}`);
  } finally {
    state.loading = false;
  }
};

// 查看详情
const handleView = (item) => {
  emit('view', item);
};

// 分页相关
const page = ref(1);
const pageSize = ref(18);
const total = ref(0);
const paginationProp = ref({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize,
  current: page,
  total,
  showTotal: (total: number) => `总 ${total} 条`,
  onChange: pageChange,
  onShowSizeChange: pageSizeChange,
});

function pageChange(p: number, pz: number) {
  page.value = p;
  pageSize.value = pz;
  fetch();
}

function pageSizeChange(_current, size: number) {
  pageSize.value = size;
  fetch();
}
</script>

<style lang="less" scoped>
.model-card-list-wrapper {
  :deep(.ant-list-header) {
    border: 0;
  }
}

.model-card {
  padding: 15px;

  .model-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid #f0f0f0;

    .model-title {
      font-size: 18px;
      font-weight: 600;
      line-height: 1.36em;
      color: #181818;
      margin: 0;
    }

    .model-id {
      font-size: 12px;
      color: #666;
    }
  }

  .model-info {
    margin-bottom: 15px;

    .info-row {
      display: flex;
      margin-bottom: 8px;
      font-size: 14px;

      .info-label {
        color: #666;
        min-width: 70px;
      }

      .info-value {
        flex: 1;
        color: #333;
      }

      .truncate {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }

  .status-section {
    margin-bottom: 15px;

    .resource-usage {
      margin-top: 10px;

      .usage-row {
        display: flex;
        align-items: center;
        margin-bottom: 8px;

        span {
          width: 50px;
          font-size: 13px;
          color: #666;
        }

        .ant-progress {
          flex: 1;
        }
      }
    }
  }

  .btns {
    display: flex;
    justify-content: space-between;
    padding-top: 10px;
    border-top: 1px solid #f0f0f0;

    .btn {
      display: flex;
      flex-direction: column;
      align-items: center;
      cursor: pointer;
      padding: 5px 10px;
      border-radius: 4px;
      transition: background-color 0.3s;

      &:hover {
        background-color: #f5f5f5;
      }

      img {
        width: 20px;
        height: 20px;
        margin-bottom: 5px;
      }

      span {
        font-size: 13px;
        color: #666;
      }
    }
  }
}
</style>
