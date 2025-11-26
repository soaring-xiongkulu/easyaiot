import { useMessage } from '@/hooks/web/useMessage';

const { createMessage } = useMessage();

export function copyText(value, text) {
  const input = document.createElement('input');
  input.value = value;
  document.body.appendChild(input);
  input.select();
  document.execCommand('copy');
  document.body.removeChild(input);
  createMessage.success(`${text}复制成功`);
}
