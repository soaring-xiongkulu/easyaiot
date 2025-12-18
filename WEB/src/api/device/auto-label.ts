import { defHttp } from '@/utils/http/axios';

enum Api {
  AutoLabel = '/dev-api/ai/dataset',  // Python后端路径
  AIService = '/model/deploy_service',
}

const commonApi = (
  method: 'get' | 'post' | 'delete' | 'put',
  url: string,
  params = {},
  headers = {},
  isTransformResponse = true,
) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

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

// 启动自动化标注任务
export const startAutoLabel = (datasetId: number, params: any) => {
  return commonApi('post', `${Api.AutoLabel}/${datasetId}/auto-label/start`, { params });
};

// 获取自动化标注任务
export const getAutoLabelTask = (datasetId: number, taskId: number) => {
  return commonApi('get', `${Api.AutoLabel}/${datasetId}/auto-label/task/${taskId}`);
};

// 获取自动化标注任务列表
export const listAutoLabelTasks = (datasetId: number, params: any) => {
  return commonApi('get', `${Api.AutoLabel}/${datasetId}/auto-label/tasks`, { params });
};

// 导出标注数据集
export const exportLabeledDataset = (datasetId: number, params: any) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  
  return defHttp.post(
    {
      url: `${Api.AutoLabel}/${datasetId}/auto-label/export`,
      data: params,
      responseType: 'blob', // 重要：设置为blob以接收文件
    },
    {
      isTransformResponse: false,
    },
  );
};

// 获取AI服务列表
export const getAIServiceList = (params = {}) => {
  return commonApi('get', `${Api.AIService}/list`, { params }, {}, false);
};

// 单张图片AI标注
export const labelSingleImage = (datasetId: number, imageId: number, params: any) => {
  return commonApi('post', `${Api.AutoLabel}/${datasetId}/auto-label/image/${imageId}`, { params });
};

// 视频抽帧
export const extractFramesFromVideo = (datasetId: number, formData: FormData) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  
  return defHttp.post(
    {
      url: `${Api.AutoLabel}/${datasetId}/extract-frames`,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    },
    {
      isTransformResponse: true,
    },
  );
};

// 导入labelme数据集
export const importLabelmeDataset = (datasetId: number, formData: FormData) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  
  return defHttp.post(
    {
      url: `${Api.AutoLabel}/${datasetId}/import-labelme`,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    },
    {
      isTransformResponse: true,
    },
  );
};
