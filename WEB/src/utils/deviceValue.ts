const NUMERIC_TEXT = /^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i;

export function normalizeDecimalPlaces(value: unknown): number | undefined {
  if (value == null || value === '') return undefined;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return undefined;
  return Math.max(0, Math.min(10, Math.trunc(parsed)));
}

/**
 * 格式化设备解析值：配置小数位时严格按位数展示；未配置时仅清理常见二进制浮点尾差。
 * 非数值内容（布尔值、枚举、原始报文等）保持原样。
 */
export function formatDeviceValue(value: unknown, decimalPlaces?: unknown): string {
  if (value == null || value === '') return '--';
  if (typeof value === 'boolean') return String(value);

  const text = String(value).trim();
  if (!NUMERIC_TEXT.test(text)) return text || '--';

  const numeric = Number(text);
  if (!Number.isFinite(numeric)) return text;

  const digits = normalizeDecimalPlaces(decimalPlaces);
  if (digits != null) {
    // 避免将超过 JS 安全整数范围的 INT64 文本转换后失真。
    if (!text.includes('.') && !/[eE]/.test(text) && !Number.isSafeInteger(numeric)) {
      return digits === 0 ? text : `${text}.${'0'.repeat(digits)}`;
    }
    return numeric.toFixed(digits);
  }

  // 整数文本可能超过 Number 的安全整数范围，不做无谓转换。
  if (!text.includes('.') && !/[eE]/.test(text)) return text;
  const normalized = Number.parseFloat(numeric.toPrecision(15));
  return Object.is(normalized, -0) ? '0' : String(normalized);
}
