import {defHttp} from '@/utils/http/axios';

enum Api {
  Model = '/model',
  Train = '/model/train',
  TrainTask = '/model/train_task',
  InferenceTask = '/model/inference_task',
  Export = '/model/export',
  DeployService = '/model/deploy_service',
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

// ================= 模型训练任务接口 =================
export const getTrainTaskPage = (params) => {
  return commonApi('get', `${Api.TrainTask}/list`, {params});
};

export const getTrainTaskDetail = (recordId) => {
  return commonApi('get', `${Api.TrainTask}/${recordId}`);
};

export const publishTrainTask = (recordId: number) => {
  return commonApi('post', `${Api.TrainTask}/publish/${recordId}`);
};

// ================= 模型训练接口 =================
export const startTrain = (modelId) => {
  return commonApi('post', `${Api.Train}/${modelId}/train`);
};

export const stopTrain = (modelId) => {
  return commonApi('post', `${Api.Train}/${modelId}/train/stop`);
};

export const getTrainStatus = (modelId) => {
  return commonApi('get', `${Api.Train}/${modelId}/train/status`);
};

export const getTrainLogs = (modelId, taskId) => {
  return commonApi('get', `${Api.Train}/${modelId}/train/${taskId}/logs`);
};

// ================= 模型推理任务接口 =================
export const getInferenceTasks = (params) => {
  return commonApi('get', `${Api.InferenceTask}/list`, {params});
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

export const getInferenceRecords = (params) => {
  return commonApi('get', Api.InferenceTask, {params});
};

export const getInferenceTaskDetail = (recordId) => {
  return commonApi('get', `${Api.InferenceTask}/detail/${recordId}`);
};

export const deleteInferenceRecord = (recordId) => {
  return commonApi('delete', `${Api.InferenceTask}/${recordId}`);
};

export const runInference = (modelId, formData) => {
  return defHttp.post({
    url: `${Api.InferenceTask}/${modelId}/inference/run`,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
    }
  }, {
    isTransformResponse: false
  });
};

// 集群推理接口（模型服务接口）
export const runClusterInference = (modelId, formData) => {
  return defHttp.post({
    url: `/model/cluster/${modelId}/inference/run`,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
    }
  }, {
    isTransformResponse: false
  });
};

export const streamInferenceProgress = (recordId: number) => {
  return new EventSource(`${Api.InferenceTask}/${recordId}/stream?token=${localStorage.getItem('jwt_token')}`);
};

// ================= 导出接口优化 =================
export const exportModel = (modelId, format, params) => {
  // 后端路径: /model/export/<model_id>/export/<format>
  return commonApi('post', `${Api.Export}/${modelId}/export/${format}`, {data: params});
};

export const downloadExportedModel = (exportId) => {
  // 下载文件需要返回blob，不使用transformResponse
  return defHttp.get({
    url: `${Api.Export}/download/${exportId}`,
    responseType: 'blob',
    headers: {
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
    }
  }, {
    isTransformResponse: false
  });
};

export const deleteExportedModel = (exportId) => {
  return commonApi('delete', `${Api.Export}/delete/${exportId}`);
};

export const getExportModelList = (params) => {
  return commonApi('get', `${Api.Export}/list`, {params});
};

export const getExportStatus = (taskIdOrExportId: string | number) => {
  return commonApi('get', `${Api.Export}/status/${taskIdOrExportId}`);
};

export const uploadInputFile = (formData: FormData) => {
  return defHttp.post({
    url: `${Api.InferenceTask}/upload_input`,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
    }
  });
};

// 下载模型文件
export const downloadModel = (modelId, modelPath) => {
  // 如果 modelPath 是完整的 URL，直接使用
  if (modelPath && (modelPath.startsWith('http://') || modelPath.startsWith('https://'))) {
    return modelPath;
  }
  // 如果是相对路径，构建完整的下载 URL
  if (modelPath && modelPath.startsWith('/')) {
    // 获取基础 URL
    const baseUrl = window.location.origin;
    return `${baseUrl}${modelPath}`;
  }
  // 如果没有路径，使用模型 ID 下载接口
  return `${Api.Model}/${modelId}/download`;
};

// ================= 模型部署服务接口 =================
export const getDeployServicePage = (params) => {
  return commonApi('get', `${Api.DeployService}/list`, {params});
};

export const deployModel = (params) => {
  // 部署操作可能需要较长时间（安装依赖、创建服务等），设置超时为5分钟
  return defHttp.post(
    {
      url: `${Api.DeployService}/deploy`,
      data: params,
      timeout: 5 * 60 * 1000, // 5分钟超时
      headers: {
        'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
      },
    },
    {
      isTransformResponse: true,
    },
  );
};

export const startDeployService = (serviceId) => {
  return commonApi('post', `${Api.DeployService}/${serviceId}/start`);
};

export const stopDeployService = (serviceId) => {
  return commonApi('post', `${Api.DeployService}/${serviceId}/stop`);
};

export const restartDeployService = (serviceId) => {
  return commonApi('post', `${Api.DeployService}/${serviceId}/restart`);
};

export const getDeployServiceLogs = (serviceId, params) => {
  return commonApi('get', `${Api.DeployService}/${serviceId}/logs`, {params});
};

export const deleteDeployService = (serviceId) => {
  return commonApi('post', `${Api.DeployService}/${serviceId}/delete`);
};

// 批量操作接口（按service_name）
export const batchStartDeployService = (serviceName) => {
  return commonApi('post', `${Api.DeployService}/batch/start`, {data: {service_name: serviceName}});
};

export const batchStopDeployService = (serviceName) => {
  return commonApi('post', `${Api.DeployService}/batch/stop`, {data: {service_name: serviceName}});
};

export const batchRestartDeployService = (serviceName) => {
  return commonApi('post', `${Api.DeployService}/batch/restart`, {data: {service_name: serviceName}});
};

// 获取service_name的所有副本详情
export const getDeployServiceReplicas = (serviceName, pageNo?: number, pageSize?: number) => {
  const params: any = { service_name: serviceName };
  if (pageNo !== undefined && pageNo !== null) {
    params.pageNo = pageNo;
  }
  if (pageSize !== undefined && pageSize !== null) {
    params.pageSize = pageSize;
  }
  return commonApi('get', `${Api.DeployService}/replicas`, {params}, {}, false);
};

// ================= 排序器管理接口 =================
export const getSorter = (serviceName) => {
  return commonApi('get', `${Api.DeployService}/sorter`, {params: {service_name: serviceName}});
};

export const startSorter = (serviceName) => {
  return commonApi('post', `${Api.DeployService}/sorter/${serviceName}/start`);
};

export const stopSorter = (serviceName) => {
  return commonApi('post', `${Api.DeployService}/sorter/${serviceName}/stop`);
};

export const restartSorter = (serviceName) => {
  return commonApi('post', `${Api.DeployService}/sorter/${serviceName}/restart`);
};

export const getSorterLogs = (serviceName, params) => {
  return commonApi('get', `${Api.DeployService}/sorter/${serviceName}/logs`, {params});
};

// ================= 抽帧器管理接口 =================
export const getExtractor = (cameraName) => {
  return commonApi('get', `${Api.DeployService}/extractor/${cameraName}`);
};

export const getExtractorList = (params) => {
  return commonApi('get', `${Api.DeployService}/extractor/list`, {params});
};

export const startExtractor = (cameraName) => {
  return commonApi('post', `${Api.DeployService}/extractor/${cameraName}/start`);
};

export const stopExtractor = (cameraName) => {
  return commonApi('post', `${Api.DeployService}/extractor/${cameraName}/stop`);
};

export const restartExtractor = (cameraName) => {
  return commonApi('post', `${Api.DeployService}/extractor/${cameraName}/restart`);
};

export const enableExtractor = (cameraName) => {
  return commonApi('post', `${Api.DeployService}/extractor/${cameraName}/enable`);
};

export const disableExtractor = (cameraName) => {
  return commonApi('post', `${Api.DeployService}/extractor/${cameraName}/disable`);
};

export const getExtractorLogs = (cameraName, params) => {
  return commonApi('get', `${Api.DeployService}/extractor/${cameraName}/logs`, {params});
};

