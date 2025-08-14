/**
 * @description: 请求间隔
 */
export enum RequestHttpIntervalEnum {
  // 秒
  SECOND = 'second',
  // 分
  MINUTE = 'minute',
  // 时
  HOUR = 'hour',
  // 天
  DAY = 'day'
}

/**
 * @description: Request result set
 */
export enum ResultEnum {
  SUCCESS = 0,
  ERROR = -1,
  TIMEOUT = 400,
  UNAUTHORIZED = 401,
  INTERNAL_SERVER_ERROR = 500,
  TYPE = 'success',
  SERVER_ERROR = 500,
  SERVER_FORBIDDEN = 403,
  NOT_FOUND = 404,
}

/**
 * @description: request method
 */
export enum RequestEnum {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  DELETE = 'DELETE',
}

/**
 * @description:  contentType
 */
export enum ContentTypeEnum {
  // json
  JSON = 'application/json;charset=UTF-8',
  // form-data qs
  FORM_URLENCODED = 'application/x-www-form-urlencoded;charset=UTF-8',
  // form-data  upload
  FORM_DATA = 'multipart/form-data;charset=UTF-8',
}

/**
 * @description: 请求头部类型
 */
export enum RequestBodyEnum {
  NONE = 'none',
  FORM_DATA = 'form-data',
  X_WWW_FORM_URLENCODED = 'x-www-form-urlencoded',
  JSON = 'json',
  XML = 'xml'
}

// 请求主体类型
export enum RequestContentTypeEnum {
  // 普通请求
  DEFAULT = 0,
  // SQL请求
  SQL = 1
}

// 数据相关
export enum RequestDataTypeEnum {
  // 静态数据
  STATIC = 0,
  // 请求数据
  AJAX = 1,
  // 数据池
  Pond = 2
}

/**
 * @description: 请求方法
 */
export enum RequestHttpEnum {
  GET = 'get',
  POST = 'post',
  PATCH = 'patch',
  PUT = 'put',
  DELETE = 'delete'
}
