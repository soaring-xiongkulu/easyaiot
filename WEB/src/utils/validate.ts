/**
 * 座机号+手机号校验
 * @param value
 * @returns {boolean}
 */
export const phoneRegEx = (value: string) => {
  const phone = new RegExp(
    '^(((\\+86)|(\\+86-))|((86)|(86\\-))|((0086)|(0086\\-)))?1[3|5|7|8|9]\\d{9}$',
  );
  const mobile = /(0[0-9]{2,3})([2-9][0-9]{6,7})+([0-9]{8,11})?$/;
  return phone.test(value) || mobile.test(value);
};
/**
 * 密码强度校验 必须至少包含大小写英文和数字
 * @param value
 * @returns {boolean}
 */
export const passwordRegEx = (value: string) => {
  const password = new RegExp(/^\S*(?=\S{8,})(?=\S*\d)(?=\S*[A-Z])(?=\S*[a-z])\S*$/);
  return password.test(value);
};
/**
 * 判断是否为正确的IP地址
 */
export const testIP = (value: string) => {
  const ip =
    /^([0-9]|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.([0-9]|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.([0-9]|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.([0-9]|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])$/;
  return ip.test(value);
};
