import {defHttp} from '@/utils/http/axios';

enum Api {
  Packages = '/packages',
  Versions = '/versions',
}

const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url, params = {}, headers = {}) => {
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
      isTransformResponse: true,
    },
  );
};

// ==================== 版本包 ====================

export const fetchPkgList = (params) => {
  return commonApi('get', Api.Packages, {params});
};

export const addOtaApp = (params) => {
  return commonApi('post', Api.Packages + "/add", {params});
};

export const updateOtaApp = (params) => {
  return commonApi('put', Api.Packages, {params});
};

export const deleteOtaApp = (packageId) => {
  return commonApi('delete', `${Api.Packages}/${packageId}`);
};

//提交测试（未验证 → 测试中）
export const submitTestPackage = (packageId) => {
  return commonApi('post', Api.Packages + `/submit-test?packageId=${packageId}`);
};

//录入测试结果 {id, passed, remark}
export const testResultPackage = (params) => {
  return commonApi('post', Api.Packages + '/test-result', {params});
};

//发布版本包 {id, skipVerify, publishStrategy, grayLadder, grayScopes:[{scopeType, scopeValue}]}
export const publishPackage = (params) => {
  return commonApi('post', Api.Packages + '/publish', {params});
};

//扩大灰度范围 {id, grayScopes}
export const expandGrayPackage = (params) => {
  return commonApi('post', Api.Packages + '/expand-gray', {params});
};

//灰度升阶 {id, targetLadder, grayScopes}
export const promoteGrayPackage = (params) => {
  return commonApi('post', Api.Packages + '/promote-gray', {params});
};

//撤回发布 {id, reason}
export const withdrawPackage = (params) => {
  return commonApi('post', Api.Packages + '/withdraw', {params});
};

//获取当前灰度范围 [{scopeType, scopeTypeName, scopeValue}]
export const fetchGrayScopes = (pkgId) => {
  return commonApi('get', `${Api.Packages}/${pkgId}/gray-scopes`);
};

//升级统计（漏斗+健康度+升阶建议） {checkHitCount, launchOkCount, coverage, successRate, funnel:[{phase, phaseName, deviceCount}], errorTops:[{errorCode, count}], suggestPromote, nextLadder}
export const fetchUpgradeStats = (pkgId) => {
  return commonApi('get', `${Api.Packages}/${pkgId}/upgrade-stats`);
};

//升级记录分页列表
export const fetchUpgradeRecords = (params) => {
  return commonApi('get', Api.Packages + '/upgrade-records', {params});
};

//根据包类型获取版本列表（旧接口保留）
export const fetchVersionListByType = (type) => {
  return commonApi('get', `${Api.Packages}/versions/${type}`);
};

// ==================== 设备版本档案 ====================

//档案分页列表
export const fetchVersionList = (params) => {
  return commonApi('get', Api.Versions, {params});
};

export const addVersion = (params) => {
  return commonApi('post', Api.Versions, {params});
};

export const updateVersion = (params) => {
  return commonApi('put', Api.Versions, {params});
};

export const deleteVersion = (id) => {
  return commonApi('delete', `${Api.Versions}/${id}`);
};

// ==================== 测试白名单 ====================

//白名单分页列表
export const fetchWhiteList = (params) => {
  return commonApi('get', Api.Versions + '/white-list', {params});
};

//白名单分组统计（按产品）[{productIdentification, productName, deviceCount}]
export const fetchWhiteGroupList = (params) => {
  return commonApi('get', Api.Versions + '/white-group-list', {params});
};

//批量添加测试白名单设备 {pkgId, deviceIdentificationList:[]}
export const batchAddDeviceTestList = (params) => {
  return commonApi('post', Api.Versions + '/batch-add-device-test-list', {params});
};

//删除白名单记录 ids:[]
export const deleteOtaVerification = (ids) => {
  return commonApi('post', Api.Versions + '/verification/delete', {params: ids});
};
