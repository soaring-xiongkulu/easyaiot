import 'uno.css';
import 'ant-design-vue/dist/reset.css';
import '@/design/index.less';
import 'virtual:svg-icons-register';
import { createApp, defineComponent, h, ref } from 'vue';
import { App as AntApp, ConfigProvider, Button, Select, Alert } from 'ant-design-vue';
import zhCN from 'ant-design-vue/es/locale/zh_CN';
import { createRouter, createWebHistory } from 'vue-router';
import { setupStore } from '@/store';
import { initAppConfigStore } from '@/logics/initAppConfig';
import { setupI18n } from '@/locales/setupI18n';
import { registerGlobComp } from '@/components/registerGlobComp';
import { setupGlobDirectives } from '@/directives';
import { AppProvider } from '@/components/Application';
import Tasks from '@/views/camera/components/AlgorithmTask/index.vue';

const Root = defineComponent({ setup() {
  const camera = ref('regression-a'); const result = ref(''); const busy = ref(false);
  async function scenario(kind: string) {
    busy.value = true;
    try {
      const response = await fetch('/dev-api/video/regression/scenario', { method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({device_id:camera.value,kind}) });
      const body = await response.json();
      result.value = body.msg;
    } catch(e) { result.value=String(e); } finally { busy.value=false; }
  }
  return () => h(ConfigProvider, {locale:zhCN}, {default:()=>h(AntApp,{}, {default:()=>h(AppProvider,{}, {default:()=>h('main',{style:'padding:16px;min-height:100vh;background:#f1f5f9'},[
    h(Alert,{type:'info',showIcon:true,message:'本地隔离回归：真实业务组件 / VIDEO 数据模型与 API / POST 引擎。摄像头画面和推理输入为测试夹具，外部平台查询为固定参考数据。'}),
    h(Tasks),
    h('aside',{style:'position:fixed;bottom:12px;left:12px;z-index:4000;padding:10px;background:#fff;border:1px solid #93c5fd;border-radius:8px;max-width:560px;box-shadow:0 3px 12px #0002'},[
      h('strong','测试输入（仅隔离环境） '),h(Select,{value:camera.value,'onUpdate:value':(v:string)=>camera.value=v,style:'width:145px',options:[{value:'regression-a',label:'正门摄像头'},{value:'regression-b',label:'后门摄像头'}]}),
      ...[['cross','模拟穿越'],['cross_reverse','模拟反向'],['enter_exit','模拟进出'],['crowd','模拟聚集'],['dwell','模拟逗留'],['conflict','模拟版本冲突'],['fail_save','模拟保存失败']].map(([kind,label])=>h(Button,{size:'small',loading:busy.value,onClick:()=>scenario(kind)},()=>label)),
      h('div',{role:'status',style:'max-width:520px;font-size:12px;color:#475569'},result.value),
    ]),
  ])})})});
} });

async function start() {
  const app=createApp(Root); setupStore(app); initAppConfigStore(); registerGlobComp(app); setupGlobDirectives(app); await setupI18n(app);
  app.use(createRouter({history:createWebHistory(),routes:[{path:'/:pathMatch(.*)*',component:Root}]}));
  app.mount('#app');
}
void start();
