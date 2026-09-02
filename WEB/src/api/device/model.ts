import {defHttp} from '@/utils/http/axios';

enum Api {
  Model = '/model',
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

// ================= 模型家族（版本管理）接口 =================
/** 同族全部版本 + 训练指标（mAP50/样本数），供版本管理抽屉使用 */
export const getModelFamily = (modelId: number) => {
  return commonApi('get', `${Api.Model}/${modelId}/family`);
};

/** 激活家族内指定版本：对外（推理/算法任务/接力标注）默认使用该版本 */
export const activateModelFamilyVersion = (modelId: number) => {
  return commonApi('post', `${Api.Model}/${modelId}/family/activate`);
};

export const getModelClasses = (modelId) => {
  return commonApi('get', `${Api.Model}/${modelId}/classes`);
};

/** 兼容 defHttp 解包前后多种响应结构 */
export function parseModelClassPayload(resp: any): { classNames: string[]; selectedClassNames: string[] } {
  if (!resp) {
    return { classNames: [], selectedClassNames: [] };
  }
  let payload = resp;
  if (resp.code === 0 && resp.data) {
    payload = resp.data;
  } else if (resp.data?.class_names || resp.data?.classNames) {
    payload = resp.data;
  }
  const classNames = payload.classNames ?? payload.class_names ?? [];
  const selected = payload.selectedClassNames ?? payload.selected_class_names ?? classNames;
  const normalized = Array.isArray(classNames) ? classNames.map(String) : [];
  const normalizedSelected = Array.isArray(selected) && selected.length > 0
    ? selected.map(String)
    : normalized;
  return { classNames: normalized, selectedClassNames: normalizedSelected };
}

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
      // 勿手动写 multipart/form-data（缺 boundary）；由 axios 根据 FormData 自动设置
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
    }
  });
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
    // 再次兜底：确保 FormData 不被按 JSON 处理
    transformRequest: [(data, headers) => {
      if (typeof FormData !== 'undefined' && data instanceof FormData) {
        if ((headers as any)?.delete) {
          (headers as any).delete('Content-Type');
          (headers as any).delete('content-type');
        } else if (headers) {
          delete (headers as Record<string, any>)['Content-Type'];
          delete (headers as Record<string, any>)['content-type'];
        }
      }
      return data;
    }],
    // 推理请求（尤其视频）可能需要较长时间，避免默认10秒超时
    timeout: 10 * 60 * 1000,
    headers: {
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
    }
  }, {
    isTransformResponse: false
  });
};

export const stopRtspInference = (payload: {
  device_id?: string;
  record_id?: number;
  stop_all?: boolean;
}) => {
  return defHttp.post({
    url: `${Api.InferenceTask}/inference/rtsp/stop`,
    data: payload,
    headers: {
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
    transformRequest: [(data, headers) => {
      if (typeof FormData !== 'undefined' && data instanceof FormData) {
        if ((headers as any)?.delete) {
          (headers as any).delete('Content-Type');
          (headers as any).delete('content-type');
        } else if (headers) {
          delete (headers as Record<string, any>)['Content-Type'];
          delete (headers as Record<string, any>)['content-type'];
        }
      }
      return data;
    }],
    headers: {
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
    // 上传较大视频文件时需要更长超时
    timeout: 10 * 60 * 1000,
    headers: {
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
  // 禁用 transformResponse 以获取完整响应对象（包含 code、msg、data）
  return commonApi('post', `${Api.DeployService}/batch/start`, {data: {service_name: serviceName}}, {}, false);
};

export const batchStopDeployService = (serviceName) => {
  // 禁用 transformResponse 以获取完整响应对象（包含 code、msg、data）
  return commonApi('post', `${Api.DeployService}/batch/stop`, {data: {service_name: serviceName}}, {}, false);
};

export const batchRestartDeployService = (serviceName) => {
  // 禁用 transformResponse 以获取完整响应对象（包含 code、msg、data）
  return commonApi('post', `${Api.DeployService}/batch/restart`, {data: {service_name: serviceName}}, {}, false);
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

// ================= 姿态分析接口 =================
const poseFormPost = (url: string, formData: FormData) => {
  return defHttp.post({
    url,
    data: formData,
    transformRequest: [(data, headers) => {
      if (typeof FormData !== 'undefined' && data instanceof FormData) {
        if ((headers as any)?.delete) {
          (headers as any).delete('Content-Type');
          (headers as any).delete('content-type');
        } else if (headers) {
          delete (headers as Record<string, any>)['Content-Type'];
          delete (headers as Record<string, any>)['content-type'];
        }
      }
      return data;
    }],
    timeout: 10 * 60 * 1000,
    headers: {
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
    },
  }, {
    isTransformResponse: false,
  });
};

/** 图片姿态估计（同步） */
export const posePredict = (modelId: number, formData: FormData) => {
  return poseFormPost(`/model/pose/${modelId}/predict`, formData);
};

/** 视频姿态估计（异步），返回 jobId */
export const posePredictVideo = (modelId: number, formData: FormData) => {
  return poseFormPost(`/model/pose/${modelId}/predict-video`, formData);
};

/** 查询姿态视频任务进度 */
export const poseVideoProgress = (jobId: string) => {
  return defHttp.get({
    url: `/model/pose/progress/${jobId}`,
    timeout: 10 * 60 * 1000,
    headers: {
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
    },
  }, {
    isTransformResponse: false,
  });
};

/** 下载姿态输出视频 */
export const poseOutputVideo = (filename: string) => {
  return defHttp.get({
    url: `/model/pose/output/${encodeURIComponent(filename)}`,
    responseType: 'blob',
    timeout: 10 * 60 * 1000,
    headers: {
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
    },
  }, {
    isTransformResponse: false,
  });
};

/** 启动摄像头姿态 RTSP 推流 */
export const poseRtspStart = (modelId: number, formData: FormData) => {
  return poseFormPost(`/model/pose/${modelId}/rtsp/start`, formData);
};

/** 停止姿态 RTSP 推流 */
export const poseRtspStop = (payload: {
  device_id?: string;
  record_id?: number;
  stop_all?: boolean;
}) => {
  return defHttp.post({
    url: '/model/pose/rtsp/stop',
    data: payload,
    headers: {
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
    },
  }, {
    isTransformResponse: false,
  });
};

/** 获取可用姿态模型列表 */
export const getPoseModels = () => {
  return commonApi('get', '/model/pose/models');
};
