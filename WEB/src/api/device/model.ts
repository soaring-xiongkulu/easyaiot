import {defHttp} from '@/utils/http/axios';

enum Api {
  Model = '/model',
  Training = '/model/training',
  InferenceTask = '/model/inference_task',
  Inference = '/model/inference',
  Export = '/model/export',
  InferenceRecord = '/model/inference/inference_records',
}

const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url, params = {}, headers = {}, isTransformResponse = true) => {
  // 设置认证头
  const authHeader = {'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')};

  return defHttp[method](
    {
      url,
      headers: {
        ...authHeader,
        ...headers,
      },
      ...params,
    },
    {
      isTransformResponse: isTransformResponse,
    },
  );
};

// ================= 模型管理接口 =================
export const getModelPage = (params) => {
  return commonApi('get', `${Api.Model}/list`, {params});
};

export const createModel = (params) => {
  return commonApi('post', `${Api.Model}/create`, {data: params});
};

export const updateModel = (params) => {
  return commonApi('put', `${Api.Model}/${params["id"]}/update`, {data: params});
};

export const deleteModel = (modelId) => {
  return commonApi('post', `${Api.Model}/${modelId}/delete`);
};

export const getModelDetail = (modelId) => {
  return commonApi('get', `${Api.Model}/${modelId}`);
};

export const getModelInferenceTasks = (modelId, params) => {
  return commonApi('get', `${Api.Model}/${modelId}/inference_tasks`, {params});
};

// 模型发布接口
export const publishModel = (modelId, params) => {
  return commonApi('post', `${Api.Model}/${modelId}/publish`, {data: params});
};

// 模型OTA检测接口
export const otaCheck = (params) => {
  return commonApi('get', `${Api.Model}/ota_check`, {params});
};

// 模型文件上传接口 (特殊处理)
export const uploadModelFile = (formData: FormData) => {
  return defHttp.post({
    url: `${Api.Model}/upload`,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
    }
  });
};

// ================= 训练管理接口 =================
export const startTraining = (modelId, params) => {
  return commonApi('post', `${Api.Training}/${modelId}/train`, {data: params});
};

export const stopTraining = (modelId) => {
  return commonApi('post', `${Api.Training}/${modelId}/train/stop`);
};

export const getTrainingStatus = (modelId) => {
  return commonApi('get', `${Api.Training}/${modelId}/train/status`);
};

// ================= 训练记录管理接口 =================
export const getInferenceTaskPage = (params) => {
  return commonApi('get', `${Api.InferenceTask}/list`, {params});
};

export const getTrainingDetail = (recordId) => {
  return commonApi('get', `${Api.InferenceTask}/${recordId}`);
};

export const createInferenceTask = (params) => {
  return commonApi('post', `${Api.InferenceTask}/create`, {data: params});
};

export const updateInferenceTask = (recordId, params) => {
  return commonApi('post', `${Api.InferenceTask}/update/${recordId}`, {data: params});
};

export const deleteInferenceTask = (recordId) => {
  return commonApi('delete', `${Api.InferenceTask}/delete/${recordId}`);
};

export const publishInferenceTask = (recordId: number) => {
  return commonApi('post', `${Api.InferenceTask}/publish/${recordId}`);
};

export const getTrainingLogs = (modelId, taskId) => {
  return commonApi('get', `${Api.Training}/${modelId}/train/${taskId}/logs`);
};

// ================= 推理记录管理接口 =================
export const createInferenceTask = (params) => {
  return commonApi('post', Api.InferenceRecord,{data: params},{'Content-Type': 'application/json'});
};

export const updateInferenceTask = (recordId, params) => {
  return commonApi('put',`${Api.InferenceRecord}/${recordId}`,{data: params},{'Content-Type': 'application/json'});
};

export const getInferenceTasks = (params) => {
  return commonApi('get', Api.InferenceRecord, {params});
};

export const getInferenceTaskDetail = (recordId) => {
  return commonApi('get', `${Api.InferenceRecord}/${recordId}`);
};

export const deleteInferenceRecord = (recordId) => {
  return commonApi('delete', `${Api.InferenceRecord}/${recordId}`);
};

// ================= 推理执行接口 =================
export const runInference = (modelId, formData) => {
  return commonApi('post',`${Api.Inference}/${modelId}/inference/run`,{data: formData},{'Content-Type': 'multipart/form-data'});
};

// ================= 流式推理进度接口 =================
export const streamInferenceProgress = (recordId: number) => {
  return new EventSource(`${Api.InferenceRecord}/${recordId}/stream?token=${localStorage.getItem('jwt_token')}`);
};

// ================= 导出接口优化 =================
export const exportModel = (modelId, format, params) => {
  return commonApi('post', `${Api.Export}/model/${modelId}/export/${format}`, {data: params});
};

export const downloadExportedModel = (exportId) => {
  return commonApi('get', `${Api.Export}/download/${exportId}`);
};

export const deleteExportedModel = (exportId) => {
  return commonApi('delete', `${Api.Export}/delete/${exportId}`);
};

export const getExportModelList = (params) => {
  return commonApi('get', `${Api.Export}/list`, {params});
};

export const getExportStatus = (exportId) => {
  return commonApi('get', `${Api.Export}/status/${exportId}`);
};

