import {defHttp} from '@/utils/http/axios';

enum Api {
  Dataset = '/dataset',
  DatasetImage = '/dataset/image',
  DatasetTag = '/dataset/tag',
  DatasetTask = '/dataset/task',
  DatasetTaskResult = '/dataset/task-result',
  DatasetTaskUser = '/dataset/task-user',
  DatasetVideo = '/dataset/video',
  Warehouse = '/warehouse',
  WarehouseDataset = '/warehouse/dataset',
  DatasetFrameTask = '/dataset/frame-task',
}

const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url, params = {}, headers = {}, isTransformResponse = true) => {
  defHttp.setHeader({'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')});

  return defHttp[method](
    {
      url,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
        ...headers,
      },
      ...params,
    },
    {
      isTransformResponse: isTransformResponse,
    },
  );
};

// 新增类型定义
interface AutoLabelModelReqVO {
  modelServiceId: string;
}

interface DatasetSplitReqVO {
  trainRatio: number;
  valRatio: number;
  testRatio: number;
}

// 数据集
export const createDataset = (params) => {
  return commonApi('post', Api.Dataset + '/create', {params});
};

export const updateDataset = (params) => {
  return commonApi('put', Api.Dataset + '/update', {params});
};

export const deleteDataset = (id) => {
  return commonApi('delete', `${Api.Dataset}/delete?id=${id}`);
};

export const getDataset = (params) => {
  return commonApi('get', Api.Dataset + '/get', {params});
};

export const getDatasetPage = (params) => {
  return commonApi('get', Api.Dataset + '/page', {params}, {}, false);
};

export const exportDatasetExcel = (params) => {
  return commonApi('get', Api.Dataset + '/export-excel', {params});
};

// 修改后的接口实现
export const setAutoLabelModel = (datasetId, params: AutoLabelModelReqVO) => {
  return commonApi('post', `${Api.Dataset}/${datasetId}/set-auto-label-model`, {
    params: {...params}
  });
};

export const autoLabel = (datasetId) => {
  return commonApi('post', `${Api.Dataset}/${datasetId}/auto-label`);
};

export const splitDataset = (datasetId, params: DatasetSplitReqVO) => {
  return commonApi('post', `${Api.Dataset}/${datasetId}/split`, {
    params: {...params}
  });
};

export const resetDataset = (datasetId) => {
  return commonApi('post', `${Api.Dataset}/${datasetId}/reset`);
};

// 图片数据集
export const createDatasetImage = (params) => {
  return commonApi('post', Api.DatasetImage + '/create', {params});
};

export const updateDatasetImage = (params) => {
  return commonApi('put', Api.DatasetImage + '/update', {params});
};

export const deleteDatasetImage = (params) => {
  return commonApi('delete', Api.DatasetImage + '/delete', {params});
};

export const deleteDatasetImages = (ids) => {
  return commonApi('delete', `${Api.DatasetImage}/batchDelete/${ids}`);
};

export const getDatasetImage = (params) => {
  return commonApi('get', Api.DatasetImage + '/get', {params});
};

export const getDatasetImagePage = (params) => {
  return commonApi('get', Api.DatasetImage + '/page', {params});
};

export const exportDatasetImageExcel = (params) => {
  return commonApi('get', Api.DatasetImage + '/export-excel', {params});
};

export const checkSyncCondition = (datasetId) => {
  return commonApi('get', `${Api.DatasetImage}/${datasetId}/check-sync-condition`);
};

export const syncToMinio = (datasetId) => {
  return commonApi('post', `${Api.DatasetImage}/${datasetId}/sync-to-minio`);
};

// 数据集标签
export const createDatasetTag = (params) => {
  return commonApi('post', Api.DatasetTag + '/create', {params});
};

export const updateDatasetTag = (params) => {
  return commonApi('put', Api.DatasetTag + '/update', {params});
};

export const deleteDatasetTag = (id) => {
  return commonApi('delete', `${Api.DatasetTag}/delete?id=${id}`);
};

export const getDatasetTag = (params) => {
  return commonApi('get', Api.DatasetTag + '/get', {params});
};

export const getDatasetTagPage = (params) => {
  return commonApi('get', Api.DatasetTag + '/page', {params});
};

export const exportDatasetTagExcel = (params) => {
  return commonApi('get', Api.DatasetTag + '/export-excel', {params});
};

// 图片上传接口
export const uploadDatasetImage = (formData: FormData) => {
  return defHttp.post({
    url: `${Api.DatasetImage}/upload`,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
    }
  });
};

// 标注任务
export const createDatasetTask = (params) => {
  return commonApi('post', Api.DatasetTask + '/create', {params});
};

export const updateDatasetTask = (params) => {
  return commonApi('put', Api.DatasetTask + '/update', {params});
};

export const deleteDatasetTask = (id) => {
  return commonApi('delete', `${Api.DatasetTask}/delete?id=${id}`);
};

export const getDatasetTask = (params) => {
  return commonApi('get', Api.DatasetTask + '/get', {params});
};

export const getDatasetTaskPage = (params) => {
  return commonApi('get', Api.DatasetTask + '/page', {params});
};

export const exportDatasetTaskExcel = (params) => {
  return commonApi('get', Api.DatasetTask + '/export-excel', {params});
};

// 标注任务结果
export const createDatasetTaskResult = (params) => {
  return commonApi('post', Api.DatasetTaskResult + '/create', {params});
};

export const updateDatasetTaskResult = (params) => {
  return commonApi('put', Api.DatasetTaskResult + '/update', {params});
};

export const deleteDatasetTaskResult = (id) => {
  return commonApi('delete', `${Api.DatasetTaskResult}/delete?id=${id}`);
};

export const getDatasetTaskResult = (params) => {
  return commonApi('get', Api.DatasetTaskResult + '/get', {params});
};

export const getDatasetTaskResultPage = (params) => {
  return commonApi('get', Api.DatasetTaskResult + '/page', {params});
};

export const exportDatasetTaskResultExcel = (params) => {
  return commonApi('get', Api.DatasetTaskResult + '/export-excel', {params});
};

// 标注任务用户
export const createDatasetTaskUser = (params) => {
  return commonApi('post', Api.DatasetTaskUser + '/create', {params});
};

export const updateDatasetTaskUser = (params) => {
  return commonApi('put', Api.DatasetTaskUser + '/update', {params});
};

export const deleteDatasetTaskUser = (id) => {
  return commonApi('delete', `${Api.DatasetTaskUser}/delete?id=${id}`);
};

export const getDatasetTaskUser = (params) => {
  return commonApi('get', Api.DatasetTaskUser + '/get', {params});
};

export const getDatasetTaskUserPage = (params) => {
  return commonApi('get', Api.DatasetTaskUser + '/page', {params});
};

export const exportDatasetTaskUserExcel = (params) => {
  return commonApi('get', Api.DatasetTaskUser + '/export-excel', {params});
};

// 视频数据集
export const createDatasetVideo = (params) => {
  return commonApi('post', Api.DatasetVideo + '/create', {params});
};

export const updateDatasetVideo = (params) => {
  return commonApi('put', Api.DatasetVideo + '/update', {params});
};

export const deleteDatasetVideo = (id) => {
  return commonApi('delete', `${Api.DatasetVideo}/delete?id=${id}`);
};

export const getDatasetVideo = (params) => {
  return commonApi('get', Api.DatasetVideo + '/get', {params});
};

export const getDatasetVideoPage = (params) => {
  return commonApi('get', Api.DatasetVideo + '/page', {params});
};

export const exportDatasetVideoExcel = (params) => {
  return commonApi('get', Api.DatasetVideo + '/export-excel', {params});
};

// 数据仓
export const createWarehouse = (params) => {
  return commonApi('post', Api.Warehouse + '/create', {params});
};

export const updateWarehouse = (params) => {
  return commonApi('put', Api.Warehouse + '/update', {params});
};

export const deleteWarehouse = (id) => {
  return commonApi('delete', `${Api.Warehouse}/delete?id=${id}`);
};

export const getWarehouse = (params) => {
  return commonApi('get', Api.Warehouse + '/get', {params});
};

export const getWarehousePage = (params) => {
  return commonApi('get', Api.Warehouse + '/page', {params});
};

export const exportWarehouseExcel = (params) => {
  return commonApi('get', Api.Warehouse + '/export-excel', {params});
};

// 数据仓数据集关联
export const createWarehouseDataset = (params) => {
  return commonApi('post', Api.WarehouseDataset + '/create', {params});
};

export const updateWarehouseDataset = (params) => {
  return commonApi('put', Api.WarehouseDataset + '/update', {params});
};

export const deleteWarehouseDataset = (id) => {
  return commonApi('delete', `${Api.WarehouseDataset}/delete?id=${id}`);
};

export const getWarehouseDataset = (params) => {
  return commonApi('get', Api.WarehouseDataset + '/get', {params});
};

export const getWarehouseDatasetPage = (params) => {
  return commonApi('get', Api.WarehouseDataset + '/page', {params});
};

export const exportWarehouseDatasetExcel = (params) => {
  return commonApi('get', Api.WarehouseDataset + '/export-excel', {params});
};

// 视频流帧捕获
export const createDatasetFrameTask = (params) => {
  return commonApi('post', Api.DatasetFrameTask + '/create', {params});
};

export const updateDatasetFrameTask = (params) => {
  return commonApi('put', Api.DatasetFrameTask + '/update', {params});
};

export const deleteDatasetFrameTask = (id) => {
  return commonApi('delete', `${Api.DatasetFrameTask}/delete?id=${id}`);
};

export const getDatasetFrameTask = (params) => {
  return commonApi('get', Api.DatasetFrameTask + '/get', {params});
};

export const getDatasetFrameTaskPage = (params) => {
  return commonApi('get', Api.DatasetFrameTask + '/page', {params});
};

export const exportDatasetFrameTaskExcel = (params) => {
  return commonApi('get', Api.DatasetFrameTask + '/export-excel', {params});
};
