import { defHttp } from '@/utils/http/axios';

enum Api {
  Model = '/model',
  ModelTraining = '/model/training',
  ModelExport = '/model/export',
  TrainingRecord = '/training/record',
  Inference = '/inference',
  Export = '/export',
  OtaCheck = '/api/model/ota_check',
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

// 模型管理接口
export const getModelPage = (params) => {
  return commonApi('get', Api.Model, {params}, {}, false);
};

export const createModel = (params) => {
  return commonApi('post', Api.Model + '/create', {params});
};

export const deleteModel = (id) => {
  return commonApi('post', `${Api.Model}/${id}/delete`);
};

export const getModelDetail = (modelId) => {
  return commonApi('get', `${Api.Model}/${modelId}`);
};

// 模型发布接口
export const publishModel = (modelId: number, params) => {
  return commonApi('post', `${Api.Model}/${modelId}/publish`, {params});
};

// 模型训练接口
export const startTraining = (modelId: number, params) => {
  return commonApi('post', `${Api.ModelTraining}/${modelId}/train`, {params});
};

export const stopTraining = (modelId: number) => {
  return commonApi('post', `${Api.ModelTraining}/${modelId}/train/stop`);
};

export const getTrainingStatus = (modelId: number) => {
  return commonApi('get', `${Api.ModelTraining}/${modelId}/train/status`);
};

// 模型推理接口
export const runInference = (modelId: number, formData: FormData) => {
  return defHttp.post({
    url: `${Api.Inference}/run`,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
    },
    params: { model_id: modelId }
  });
};

// 模型导出接口
export const exportModel = (modelId: number, format: string, params) => {
  return commonApi('post', `${Api.ModelExport}/${modelId}/export/${format}`, {params});
};

export const downloadExport = (exportId: number) => {
  return commonApi('get', `${Api.Export}/download/${exportId}`);
};

// 模型OTA检测接口
export const otaCheck = (params) => {
  return commonApi('get', Api.OtaCheck, {params});
};

// 模型训练记录管理
export const getTrainingRecordPage = (params) => {
  return commonApi('get', Api.TrainingRecord, {params}, {}, false);
};

export const deleteTrainingRecord = (recordId: number) => {
  return commonApi('delete', `${Api.TrainingRecord}/${recordId}`);
};

export const getModelTrainingRecords = (modelId: number, params) => {
  return commonApi('get', `${Api.Model}/${modelId}/training_records`, {params});
};

// 训练记录创建和更新
export const createTrainingRecord = (params) => {
  return commonApi('post', Api.TrainingRecord + '/create', {params});
};

export const updateTrainingRecord = (recordId: number, params) => {
  return commonApi('post', `${Api.TrainingRecord}/update/${recordId}`, {params});
};
