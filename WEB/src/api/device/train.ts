import { defHttp } from '@/utils/http/axios';

// 训练服务API路径常量
const TrainApi = {
  // 训练任务
  Start: '/train/start',
  Status: '/train/status',
  Log: '/train/log',
  Logs: '/train/logs',
  CurrentStep: '/train/current_step',
  Config: '/train/config',
  List: '/train/list',
  // 模型服务
  Model: '/model',
  Deploy: '/model/deploy',
  ModelStatus: '/model/status',
  ModelList: '/model/list',
  StartModel: '/model/start',
  StopModel: '/model/stop',
  ModelDetail: '/model/detail',
  // 模型导出
  Export: '/export',
  ExportModel: '/export/model',
  DownloadModel: '/export/download'
};

// 通用API请求封装
const commonApi = (method, url, params = {}, headers = {}, isTransformResponse = true) => {
  // 设置认证头部
  defHttp.setHeader({
    'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
  });

  return defHttp[method](
    {
      url,
      headers: {
        ignoreCancelToken: true,
        ...headers
      },
      ...params
    },
    {
      isTransformResponse
    }
  );
};

/**************** 训练任务管理接口 ****************/
export const startTraining = (params) => {
  return commonApi('post', TrainApi.Start, { data: params });
};

export const getTrainingStatus = (taskId) => {
  return commonApi('get', `${TrainApi.Status}/${taskId}`);
};

export const logTrainingStep = (params) => {
  return commonApi('post', TrainApi.Log, { data: params });
};

export const getTrainingLogs = (trainingId, params) => {
  return commonApi('get', `${TrainApi.Logs}/${trainingId}`, { params });
};

export const getCurrentTrainingStep = (trainingId) => {
  return commonApi('get', `${TrainApi.CurrentStep}/${trainingId}`);
};

export const getTrainingConfig = (trainingId) => {
  return commonApi('get', `${TrainApi.Config}/${trainingId}`);
};

export const updateTrainingStatus = (trainingId, status) => {
  return commonApi('put', `${TrainApi.Status}/${trainingId}`, { data: { status } });
};

export const listTrainings = (params) => {
  return commonApi('get', TrainApi.List, { params });
};

export const deleteTraining = (taskId) => {
  return commonApi('delete', `${TrainApi.Status}/${taskId}`);
};

/**************** 模型服务管理接口 ****************/
export const getModelService = (modelId) => {
  return commonApi('get', `${TrainApi.Model}/${modelId}`);
};

export const deployModel = (params) => {
  return commonApi('post', TrainApi.Deploy, { data: params });
};

export const checkModelServiceStatus = (modelId) => {
  return commonApi('get', `${TrainApi.ModelStatus}/${modelId}`);
};

export const listModelServices = () => {
  return commonApi('get', TrainApi.ModelList);
};

export const startModelService = (modelId) => {
  return commonApi('post', `${TrainApi.StartModel}/${modelId}`);
};

export const stopModelService = (modelId) => {
  return commonApi('post', `${TrainApi.StopModel}/${modelId}`);
};

export const deleteModelService = (modelId) => {
  return commonApi('delete', `${TrainApi.Model}/${modelId}`);
};

export const getModelServiceDetail = (modelId) => {
  return commonApi('get', `${TrainApi.ModelDetail}/${modelId}`);
};

/**************** 模型导出管理接口 ****************/
export const exportModel = (params) => {
  return commonApi('post', TrainApi.ExportModel, { data: params });
};

export const downloadModel = (modelId) => {
  return commonApi('get', `${TrainApi.DownloadModel}/${modelId}`, {
    responseType: 'blob'
  });
};

export const listExportedModels = () => {
  return commonApi('get', TrainApi.Export);
};

export const deleteExportedModel = (modelId) => {
  return commonApi('delete', `${TrainApi.Export}/${modelId}`);
};

export const downloadExportedModel = (modelId) => {
  return commonApi('get', `${TrainApi.DownloadModel}/${modelId}`, {
    responseType: 'blob'
  });
};
