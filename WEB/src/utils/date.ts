/**
 * 获取时间，带格式
 * @param {Object} params
 * @param {Number} params.timestamp - 时间戳，可传/不穿，默认为当前时间
 * @param {String} params.format - 获取的时间格式，注意中间以空格切分“日期”和“时间”
 *                               - yyyy-MM-dd HH:mm:ss
 *                               - yyyy-MM-dd
 *                               - ...自定义
 */
export function getDate({ timestamp = null, format = 'yyyy-MM-dd HH:mm:ss' } = {}) {
  const addZero = (num, len = 2) => `0${num}`.slice(-len);
  try {
    let formatDate = '';
    const date = timestamp ? new Date(timestamp) : new Date();
    const objData = {};
    objData.yyyy = date.getFullYear();
    objData.MM = addZero(date.getMonth() + 1);
    objData.dd = addZero(date.getDate());
    objData.HH = addZero(date.getHours());
    objData.mm = addZero(date.getMinutes());
    objData.ss = addZero(date.getSeconds());

    format.split(' ').forEach((time) => {
      formatDate = formatDate.length ? formatDate + ' ' : formatDate;
      // 匹配非英文字母
      const other = time.match(/[^A-Za-z]+/g);
      // 匹配非其他字符
      time.match(/[A-Za-z]+/g).forEach((str, key) => {
        formatDate += `${objData[str]}${other[key] || ''}`;
      });
    });
    return formatDate;
  } catch (e) {
    //console.log(e);
  }
}
