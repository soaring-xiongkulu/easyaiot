import { reactive } from 'vue';

export const rulesRef = reactive({
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  deviceId: [{ required: true, message: '请选择设备配置', trigger: 'change' }],
  newDeviceProfileTitle: [{ required: true, message: '请输入设备配置名称', trigger: 'change' }],
});
