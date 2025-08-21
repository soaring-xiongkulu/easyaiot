import { defHttp } from '@/utils/http/axios';

enum Api {
  Project = '/project',
  Training = '/training',
  Inference = '/inference',
  Image = '/image',
  Export = '/export',
  Dataset = '/dataset',
  Annotation = '/annotation',
  Camera = '/camera'
}

const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url: string, params = {}, headers = {}, isTransformResponse = true) => {
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

// ======================== 项目管理接口 ========================
export const createProject = (params: { name: string; description?: string }) => {
  return commonApi('post', Api.Project + '/create', { params });
};

export const deleteProject = (projectId: number) => {
  return commonApi('delete', `${Api.Project}/${projectId}/delete`);
};

// ======================== 训练管理接口 ========================
interface TrainingParams {
  epochs?: number;
  model_arch?: string;
  img_size?: number;
  batch_size?: number;
  use_gpu?: boolean;
}

export const startTraining = (projectId: number, params: TrainingParams) => {
  return commonApi('post', `${Api.Training}/project/${projectId}/train`, { params });
};

export const stopTraining = (projectId: number) => {
  return commonApi('post', `${Api.Training}/project/${projectId}/train/stop`);
};

export const getTrainingStatus = (projectId: number) => {
  return commonApi('get', `${Api.Training}/project/${projectId}/train/status`);
};

// ======================== 推理管理接口 ========================
export const runInference = (projectId: number, formData: FormData) => {
  return defHttp.post({
    url: `${Api.Inference}/project/${projectId}/inference/run`,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
    }
  });
};

// ======================== 图片管理接口 ========================
export const deleteImage = (projectId: number, imageId: number) => {
  return commonApi('post', `${Api.Image}/project/${projectId}/image/${imageId}/delete`);
};

export const deleteSelectedImages = (projectId: number, imageIds: number[]) => {
  return commonApi('post', `${Api.Image}/project/${projectId}/delete_selected_images`, {
    params: { image_ids: JSON.stringify(imageIds) }
  });
};

export const deleteUnannotatedImages = (projectId: number) => {
  return commonApi('post', `${Api.Image}/project/${projectId}/delete_unannotated_images`);
};

export const uploadImages = (projectId: number, formData: FormData) => {
  return defHttp.post({
    url: `${Api.Image}/project/${projectId}/upload_images`,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
    }
  });
};

// ======================== 导出管理接口 ========================
export const exportModel = (projectId: number, format: 'onnx' | 'torchscript') => {
  return commonApi('post', `${Api.Export}/project/${projectId}/export/${format}`);
};

export const downloadFile = (filename: string) => {
  return commonApi('get', `${Api.Export}/download/${filename}`, {}, {}, false);
};

// ======================== 数据集管理接口 ========================
interface DatasetAssignment {
  image_ids: number[];
  dataset_type: string;
}

export const updateDatasetAssignment = (projectId: number, params: DatasetAssignment) => {
  return commonApi('post', `${Api.Dataset}/project/${projectId}/dataset/update`, { params });
};

export const autoAssignDataset = (projectId: number) => {
  return commonApi('post', `${Api.Dataset}/project/${projectId}/dataset/auto_assign`);
};

export const downloadDataset = (projectId: number) => {
  return commonApi('get', `${Api.Dataset}/project/${projectId}/dataset/download`, {}, {}, false);
};

// ======================== 标注管理接口 ========================
export interface Label {
  id?: number;
  name: string;
  color: string;
}

export interface Annotation {
  id?: number;
  label_id: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

export const getLabels = (projectId: number) => {
  return commonApi('get', `${Api.Annotation}/project/${projectId}/labels`);
};

export const createLabel = (projectId: number, params: Label) => {
  return commonApi('post', `${Api.Annotation}/project/${projectId}/labels/create`, { params });
};

export const updateLabel = (projectId: number, labelId: number, params: Label) => {
  return commonApi('post', `${Api.Annotation}/project/${projectId}/labels/${labelId}/update`, { params });
};

export const deleteLabel = (projectId: number, labelId: number) => {
  return commonApi('post', `${Api.Annotation}/project/${projectId}/labels/${labelId}/delete`);
};

export const getImageAnnotations = (imageId: number) => {
  return commonApi('get', `${Api.Annotation}/image/${imageId}/annotations`);
};

export const saveAnnotations = (imageId: number, annotations: Annotation[]) => {
  return commonApi('post', `${Api.Annotation}/image/${imageId}/annotations/save`, {
    params: { annotations }
  });
};

// ======================== 摄像头管理接口 ========================
interface RtspParams {
  rtsp_url: string;
  interval?: number;
  max_count?: number;
}

interface OnvifParams {
  device_ip: string;
  device_port: string;
  username: string;
  password: string;
  profile_token: string;
  interval?: number;
  max_count?: number;
}

export const startRtspCapture = (projectId: number, params: RtspParams) => {
  return commonApi('post', `${Api.Camera}/project/${projectId}/rtsp/start`, { params });
};

export const stopRtspCapture = (projectId: number) => {
  return commonApi('post', `${Api.Camera}/project/${projectId}/rtsp/stop`);
};

export const getRtspStatus = (projectId: number) => {
  return commonApi('get', `${Api.Camera}/project/${projectId}/rtsp/status`);
};

export const discoverOnvifDevices = () => {
  return commonApi('get', `${Api.Camera}/onvif/discover`);
};

export const getOnvifProfiles = (deviceIp: string, devicePort: string, params: { username: string; password: string }) => {
  return commonApi('post', `${Api.Camera}/onvif/${deviceIp}/${devicePort}/profiles`, { params });
};

export const startOnvifCapture = (projectId: number, params: OnvifParams) => {
  return commonApi('post', `${Api.Camera}/project/${projectId}/onvif/start`, { params });
};

export const stopOnvifCapture = (projectId: number, profileToken: string) => {
  return commonApi('post', `${Api.Camera}/project/${projectId}/onvif/stop`, {
    params: { profile_token: profileToken }
  });
};

export const getOnvifStatus = (projectId: number, profileToken: string) => {
  return commonApi('post', `${Api.Camera}/project/${projectId}/onvif/status`, {
    params: { profile_token: profileToken }
  });
};
