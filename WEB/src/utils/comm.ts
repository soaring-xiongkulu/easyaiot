import { cloneDeep, isArray } from 'lodash-es';
import { useMessage } from '@/hooks/web/useMessage';

const { createMessage } = useMessage();

/**
 * 静态图片资源处理
 * @param path {String} 路径
 */
export const getImage = (path: string) => {
  return '/iot/images' + path;
};

/**
 * Select过滤
 * @param value 过滤值
 * @param option
 * @param key
 */
export const filterSelectNode = (value: string, option: any, key = 'label'): boolean => {
  return option[key]?.includes(value);
};
// cron 表达式

export const CronRegEx = new RegExp(
  '^\\s*($|#|\\w+\\s*=|(\\?|\\*|(?:[0-5]?\\d)(?:(?:-|\\/|\\,)(?:[0-5]?\\d))?(?:,(?:[0-5]?\\d)(?:(?:-|\\/|\\,)(?:[0-5]?\\d))?)*)\\s+(\\?|\\*|(?:[0-5]?\\d)(?:(?:-|\\/|\\,)(?:[0-5]?\\d))?(?:,(?:[0-5]?\\d)(?:(?:-|\\/|\\,)(?:[0-5]?\\d))?)*)\\s+(\\?|\\*|(?:[01]?\\d|2[0-3])(?:(?:-|\\/|\\,)(?:[01]?\\d|2[0-3]))?(?:,(?:[01]?\\d|2[0-3])(?:(?:-|\\/|\\,)(?:[01]?\\d|2[0-3]))?)*)\\s+(\\?|\\*|(?:0?[1-9]|[12]\\d|3[01])(?:(?:-|\\/|\\,)(?:0?[1-9]|[12]\\d|3[01]))?(?:,(?:0?[1-9]|[12]\\d|3[01])(?:(?:-|\\/|\\,)(?:0?[1-9]|[12]\\d|3[01]))?)*)\\s+(\\?|\\*|(?:[1-9]|1[012])(?:(?:-|\\/|\\,)(?:[1-9]|1[012]))?(?:L|W)?(?:,(?:[1-9]|1[012])(?:(?:-|\\/|\\,)(?:[1-9]|1[012]))?(?:L|W)?)*|\\?|\\*|(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(?:(?:-)(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC))?(?:,(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(?:(?:-)(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC))?)*)\\s+(\\?|\\*|(?:[0-6])(?:(?:-|\\/|\\,|#)(?:[0-6]))?(?:L)?(?:,(?:[0-6])(?:(?:-|\\/|\\,|#)(?:[0-6]))?(?:L)?)*|\\?|\\*|(?:MON|TUE|WED|THU|FRI|SAT|SUN)(?:(?:-)(?:MON|TUE|WED|THU|FRI|SAT|SUN))?(?:,(?:MON|TUE|WED|THU|FRI|SAT|SUN)(?:(?:-)(?:MON|TUE|WED|THU|FRI|SAT|SUN))?)*)(|\\s)+(\\?|\\*|(?:|\\d{4})(?:(?:-|\\/|\\,)(?:|\\d{4}))?(?:,(?:|\\d{4})(?:(?:-|\\/|\\,)(?:|\\d{4}))?)*))$',
);
export const isCron = (value: string) => CronRegEx.test(value);

export const LocalStore = {
  set(key: string, data: any) {
    localStorage.setItem(key, typeof data === 'string' ? data : JSON.stringify(data));
  },
  get(key: string) {
    const dataStr = localStorage.getItem(key);
    try {
      if (dataStr) {
        const data = JSON.parse(dataStr);
        return data && typeof data === 'object' ? data : dataStr;
      } else {
        return dataStr;
      }
    } catch (e) {
      return dataStr;
    }
  },
  remove(key: string) {
    localStorage.removeItem(key);
  },
  removeAll() {
    localStorage.clear();
  },
};

/**
 * 生成随机数
 * @param length
 * @returns
 */
export const randomString = (length?: number) => {
  const tempLength = length || 32;
  const chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678';
  const maxPos = chars.length;
  let pwd = '';
  for (let i = 0; i < tempLength; i += 1) {
    pwd += chars.charAt(Math.floor(Math.random() * maxPos));
  }
  return pwd;
};

export const treeFilter = (data: any[], value: any, key = 'name'): any[] => {
  if (!data) return [];

  return data.filter((item) => {
    if (item.children && item.children.length) {
      item.children = treeFilter(item.children || [], value, key);
      return !!item.children.length;
    } else {
      return item[key] === value;
    }
  });
};

/**
 * 通过子节点获取上级相应数据
 * @param data 树形数据
 * @param search 搜索值
 * @param searchKey 搜索key
 * @param returnKey 返回key
 */
export const openKeysByTree = (
  data: any[],
  search: any,
  searchKey = 'id',
  returnKey = 'id',
): any[] => {
  if (!data || (data && !isArray(data))) return [];
  const cloneData = cloneDeep(data);
  const filterTree = treeFilter(cloneData, search, searchKey);
  const openKeys: any[] = [];

  const findKey = (treeData: any[]) => {
    for (let i = 0; i < treeData.length; i++) {
      const item = treeData[i];
      openKeys.push(item[returnKey]);
      if (item.children && item.children.length) {
        findKey(item.children);
      }
    }
  };

  findKey(filterTree);
  return openKeys;
};

/**
 * 仅提示一次的message
 * @param msg 消息内容
 * @param type 消息类型
 */
export const onlyMessage = (msg: string, type: 'success' | 'error' | 'warning' = 'success') => {
  return createMessage[type](msg);
};
