import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import './styles.css';

type DeviceStatus = 'online' | 'warning' | 'offline';
type DeviceType = string;

interface Device {
  id: string;
  name: string;
  type: DeviceType;
  status: DeviceStatus;
  position: [number, number, number];
  value: number;
  unit: string;
  label: string;
  updated: string;
  mesh?: THREE.Object3D;
  tag?: HTMLElement;
  binding?: { sourceId: string; sourceName: string; protocol: string; point: string };
  building?: string;
  floor?: number;
}

interface TwinProject {
  key: string; name: string; subtitle: string; sceneTitle: string; overview: string;
  focusLabels: [string, string, string]; metrics: [string, string, string, string];
  loadLabels: [string, string, string]; devices: Device[];
  palette: { background:number; fog:number; ground:number; road:number; building:number; roof:number; window:number; accent:string };
}

const palettes = {
  industrial: { background:0x151b21, fog:0x202933, ground:0x343b40, road:0x171b1f, building:0x737b80, roof:0x394148, window:0x64b7ca, accent:'#ff9e42' },
  campus: { background:0xb9dff2, fog:0xdceef5, ground:0x6f9f58, road:0xd7cbb8, building:0xb87251, roof:0xe8dfcf, window:0x73b9d2, accent:'#2f9c69' },
  port: { background:0x071528, fog:0x102944, ground:0x29343f, road:0x182431, building:0x465767, roof:0x202c38, window:0x4cb7d3, accent:'#ff6b35' },
  energy: { background:0xc88646, fog:0xe8b46e, ground:0x9a6237, road:0x6b4a34, building:0xd7d1c2, roof:0x80786e, window:0x375f84, accent:'#ffd45b' },
};

const industrialDevices: Device[] = [
  { id: 'AIR-01', name: '一号空压机', type: '生产设备', status: 'online', position: [-20, 3.2, -6], value: 0.72, unit: 'MPa', label: '出口压力', updated: '刚刚' },
  { id: 'CNC-07', name: '七号加工中心', type: '生产设备', status: 'online', position: [-9, 2.6, -4], value: 86.4, unit: '%', label: '设备负载', updated: '刚刚' },
  { id: 'PMP-03', name: '循环水泵 P03', type: '能源设备', status: 'warning', position: [8, 2.6, 1], value: 78.6, unit: '°C', label: '轴承温度', updated: '2 秒前' },
  { id: 'TRF-01', name: '园区主变压器', type: '能源设备', status: 'online', position: [26, 3.5, -12], value: 68.2, unit: '%', label: '当前负载', updated: '刚刚' },
  { id: 'ENV-04', name: '东区环境站', type: '环境传感', status: 'online', position: [30, 4.5, 10], value: 32, unit: 'μg/m³', label: 'PM2.5', updated: '5 秒前' },
  { id: 'CAM-12', name: '南门摄像机', type: '安防设备', status: 'offline', position: [-2, 5.5, 22], value: 0, unit: 'Mbps', label: '视频码率', updated: '8 分钟前' },
  { id: 'PV-02', name: '二号光伏阵列', type: '能源设备', status: 'online', position: [9, 6.4, -17], value: 186, unit: 'kW', label: '实时功率', updated: '刚刚' },
  { id: 'GAS-06', name: '六号燃气探头', type: '环境传感', status: 'online', position: [18, 4.2, 8], value: 2.1, unit: '%LEL', label: '燃气浓度', updated: '3 秒前' }
];

const projects: Record<string, TwinProject> = {
  industrial: { key:'industrial', name:'临港智造园', subtitle:'LINGANG INDUSTRIAL DIGITAL TWIN', sceneTitle:'园区运行态势', overview:'园区概览', focusLabels:['生产区','能源站','南门'], metrics:['接入设备','在线率','今日用电','未处理告警'], loadLabels:['生产设备','暖通系统','照明系统'], devices:industrialDevices, palette:palettes.industrial },
  campus: { key:'campus', name:'未来科技大学', subtitle:'FUTURE CAMPUS DIGITAL TWIN', sceneTitle:'校园运行态势', overview:'校园概览', focusLabels:['教学区','生活区','体育场'], metrics:['接入终端','在线率','今日人流','安全事件'], loadLabels:['智慧教室','宿舍用能','公共照明'], palette:palettes.campus, devices:[
    {id:'CLS-A12',name:'A12智慧教室',type:'教学空间',status:'online',position:[-20,5,-8],value:86,unit:'人',label:'在室人数',updated:'刚刚'},
    {id:'LIB-01',name:'图书馆环境站',type:'环境传感',status:'online',position:[4,7,-12],value:24.6,unit:'°C',label:'室内温度',updated:'刚刚'},
    {id:'LAB-03',name:'三号实验楼',type:'实验设施',status:'warning',position:[22,6,-8],value:1180,unit:'ppm',label:'CO₂浓度',updated:'2 秒前'},
    {id:'DOR-08',name:'八号学生公寓',type:'生活设施',status:'online',position:[22,8,10],value:312,unit:'kW',label:'实时用电',updated:'刚刚'},
    {id:'GYM-02',name:'体育馆人流计',type:'公共设施',status:'online',position:[-19,5,11],value:428,unit:'人',label:'场馆人数',updated:'3 秒前'},
    {id:'CAM-W05',name:'西门摄像机',type:'安防设备',status:'offline',position:[-33,5,19],value:0,unit:'Mbps',label:'视频码率',updated:'6 分钟前'},
    {id:'CHG-06',name:'六号充电站',type:'能源设备',status:'online',position:[8,2,20],value:74,unit:'%',label:'使用率',updated:'刚刚'},
    {id:'WTR-01',name:'景观湖水质站',type:'环境传感',status:'online',position:[-4,2,7],value:7.2,unit:'pH',label:'酸碱度',updated:'5 秒前'}
  ]},
  port: { key:'port', name:'东海智慧港', subtitle:'EAST SEA SMART PORT DIGITAL TWIN', sceneTitle:'港口作业态势', overview:'港区概览', focusLabels:['集装箱区','泊位区','堆场'], metrics:['接入设施','在线率','今日吞吐','作业告警'], loadLabels:['岸桥设备','场桥设备','无人集卡'], palette:palettes.port, devices:[
    {id:'QC-01',name:'一号岸桥',type:'装卸设备',status:'online',position:[-24,12,-8],value:31,unit:'箱/h',label:'装卸效率',updated:'刚刚'},
    {id:'QC-03',name:'三号岸桥',type:'装卸设备',status:'warning',position:[-8,12,-8],value:67.8,unit:'°C',label:'电机温度',updated:'2 秒前'},
    {id:'RTG-12',name:'十二号场桥',type:'堆场设备',status:'online',position:[17,7,-10],value:82,unit:'%',label:'作业负载',updated:'刚刚'},
    {id:'AGV-28',name:'无人集卡 28',type:'运输设备',status:'online',position:[10,2,8],value:68,unit:'%',label:'剩余电量',updated:'刚刚'},
    {id:'BTH-02',name:'二号泊位',type:'泊位设施',status:'online',position:[-25,2,15],value:11.2,unit:'m',label:'当前水深',updated:'4 秒前'},
    {id:'MET-01',name:'港区气象站',type:'环境传感',status:'online',position:[28,6,15],value:7.8,unit:'m/s',label:'瞬时风速',updated:'3 秒前'},
    {id:'CAM-G07',name:'七号闸口相机',type:'安防设备',status:'offline',position:[33,5,22],value:0,unit:'Mbps',label:'视频码率',updated:'4 分钟前'},
    {id:'YRD-04',name:'四号冷链堆场',type:'仓储设施',status:'online',position:[25,3,4],value:-18.2,unit:'°C',label:'冷柜温度',updated:'刚刚'}
  ]},
  energy: { key:'energy', name:'西北零碳能源基地', subtitle:'NET-ZERO ENERGY DIGITAL TWIN', sceneTitle:'新能源运行态势', overview:'基地概览', focusLabels:['光伏区','风电区','储能站'], metrics:['发电单元','可用率','今日发电','运行告警'], loadLabels:['光伏阵列','风力机组','储能系统'], palette:palettes.energy, devices:[
    {id:'PV-A01',name:'A区光伏阵列',type:'光伏系统',status:'online',position:[-22,3,-10],value:6.8,unit:'MW',label:'实时功率',updated:'刚刚'},
    {id:'PV-B06',name:'B区六号逆变器',type:'光伏系统',status:'warning',position:[-8,3,3],value:71.4,unit:'°C',label:'模块温度',updated:'2 秒前'},
    {id:'WT-03',name:'三号风力机组',type:'风电系统',status:'online',position:[17,14,-12],value:3.2,unit:'MW',label:'实时功率',updated:'刚刚'},
    {id:'WT-07',name:'七号风力机组',type:'风电系统',status:'online',position:[29,14,2],value:12.6,unit:'m/s',label:'轮毂风速',updated:'刚刚'},
    {id:'ESS-01',name:'一号储能舱',type:'储能系统',status:'online',position:[16,4,15],value:78,unit:'%',label:'SOC',updated:'3 秒前'},
    {id:'TRF-02',name:'二号升压站',type:'输变电系统',status:'online',position:[-5,4,18],value:96.8,unit:'%',label:'变换效率',updated:'刚刚'},
    {id:'MET-08',name:'八号气象站',type:'环境传感',status:'offline',position:[32,5,19],value:0,unit:'W/m²',label:'辐照度',updated:'9 分钟前'},
    {id:'GRID-01',name:'并网计量点',type:'输变电系统',status:'online',position:[0,5,24],value:18.6,unit:'MW',label:'上网功率',updated:'刚刚'}
  ]}
};
const projectKey = new URLSearchParams(location.search).get('project') || 'industrial';
const activeProject = projects[projectKey] || projects.industrial;
const editMode = new URLSearchParams(location.search).get('mode') === 'edit';
document.body.dataset.project = activeProject.key;
document.body.dataset.mode = editMode ? 'edit' : 'preview';
const devices = activeProject.devices;
const warningDevice = devices.find(d=>d.status==='warning') || devices[0];
const offlineDevice = devices.find(d=>d.status==='offline') || devices[1];

const statusName: Record<DeviceStatus, string> = { online: '正常', warning: '预警', offline: '离线' };
const statusColor: Record<DeviceStatus, number> = { online: 0x4ee6a8, warning: 0xffbd5b, offline: 0xff6b70 };

document.querySelector<HTMLDivElement>('#app')!.innerHTML = `
  <div class="shell">
    <header class="topbar">
      <div class="brand"><span class="brand-mark"><i></i><i></i><i></i></span><div><strong>${activeProject.name}</strong><small>${activeProject.subtitle}</small></div></div>
      <div class="site-status"><span class="pulse"></span>${editMode ? '编辑模式 · 设备绑定可用' : '数据链路正常'} <b>·</b> <span id="clock"></span></div>
      <div class="header-actions"><button class="icon-btn" id="fullscreen" title="全屏">⛶</button><div class="user"><span>运</span><div>园区运维员<small>综合管理中心</small></div></div></div>
    </header>
    <main class="workspace">
      <section class="scene-wrap">
        <div id="scene"></div>
        <div id="labels"></div>
        <div class="scene-title"><span>LIVE</span><div><h1>${activeProject.sceneTitle}</h1><p>实时空间感知 · 设备状态映射</p></div></div>
        <div class="scene-toolbar">
          <button data-view="overview" class="active">全景</button><button data-view="production">${activeProject.focusLabels[0]}</button><button data-view="energy">${activeProject.focusLabels[1]}</button><button data-view="gate">${activeProject.focusLabels[2]}</button>
        </div>
        <div class="floor-toolbar"><select id="building-select" aria-label="选择建筑"></select><button id="explode-floors">展开模式</button><select id="floor-select" aria-label="选择楼层"><option value="all">整栋</option></select><button id="enter-floor">进入楼层</button><button id="exit-floor">返回园区</button></div>
        <aside class="floor-stack-panel" id="floor-stack-panel"><div class="floor-stack-head"><span>EXPLODED VIEW</span><strong id="floor-stack-title">建筑楼层</strong><small>点击楼层进入运维场景</small></div><div id="floor-stack-list"></div></aside>
        <div class="compass"><span>N</span><i></i></div>
        <div class="scene-help">拖拽旋转 · 滚轮缩放 · 点击设备查看详情</div>
      </section>
      <aside class="left-panel panel">
        <div class="panel-head"><div><span class="eyebrow">OVERVIEW</span><h2>${activeProject.overview}</h2></div><span class="live-chip">实时</span></div>
        <div class="metrics">
          <article><span class="metric-icon cyan">⌁</span><div><small>${activeProject.metrics[0]}</small><strong>128</strong><em>台</em></div></article>
          <article><span class="metric-icon green">✓</span><div><small>${activeProject.metrics[1]}</small><strong id="online-rate">98.4</strong><em>%</em></div></article>
          <article><span class="metric-icon amber">⚡</span><div><small>${activeProject.metrics[2]}</small><strong>24.8</strong><em>MWh</em></div></article>
          <article><span class="metric-icon red">!</span><div><small>${activeProject.metrics[3]}</small><strong>3</strong><em>条</em></div></article>
        </div>
        <section class="mini-section"><div class="section-title"><h3>实时能耗</h3><span>今日</span></div><div class="power-number"><strong id="power-total">1,842</strong><span>kW</span><small>较昨日同期 <b>↓ 6.2%</b></small></div><svg id="power-chart" viewBox="0 0 300 92" preserveAspectRatio="none"><defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#38d9c5" stop-opacity=".38"/><stop offset="1" stop-color="#38d9c5" stop-opacity="0"/></linearGradient></defs><path class="area"/><path class="line"/></svg><div class="chart-axis"><span>08:00</span><span>12:00</span><span>16:00</span><span>现在</span></div></section>
        <section class="mini-section grow"><div class="section-title"><h3>系统负载</h3><span>实时</span></div><div class="loads"><div><label>${activeProject.loadLabels[0]} <b>72%</b></label><span><i style="width:72%"></i></span></div><div><label>${activeProject.loadLabels[1]} <b>46%</b></label><span><i style="width:46%"></i></span></div><div><label>${activeProject.loadLabels[2]} <b>31%</b></label><span><i style="width:31%"></i></span></div></div></section>
      </aside>
      <aside class="right-panel panel">
        <div class="panel-head"><div><span class="eyebrow">OPERATIONS</span><h2>设备与告警</h2></div><button class="filter-btn" id="filter-btn">筛选</button></div>
        <div class="tabs"><button class="active" data-filter="all">全部 <b>8</b></button><button data-filter="warning">异常 <b>2</b></button><button data-filter="online">在线 <b>6</b></button></div>
        <div class="device-list" id="device-list"></div>
        <section class="alerts"><div class="section-title"><h3>实时告警</h3><button id="all-alerts">查看全部 →</button></div>
          <article data-device="${warningDevice.id}"><span class="alert-dot critical"></span><div><strong>${warningDevice.label}超过预警阈值</strong><p>${warningDevice.name} · ${warningDevice.type}</p><time>14:32:08</time></div><b>高</b></article>
          <article data-device="${offlineDevice.id}"><span class="alert-dot medium"></span><div><strong>设备通讯中断</strong><p>${offlineDevice.name} · ${offlineDevice.type}</p><time>14:26:41</time></div><b>中</b></article>
        </section>
      </aside>
      <div class="bottom-stats">
        <div><span>环境温度</span><strong id="ambient-temp">26.4<small>°C</small></strong></div><i></i><div><span>空气质量</span><strong>优 <small>AQI 32</small></strong></div><i></i><div><span>光伏发电</span><strong id="pv-power">186<small>kW</small></strong></div><i></i><div><span>碳减排</span><strong>4.28<small>tCO₂</small></strong></div>
      </div>
    </main>
    <aside class="detail-drawer" id="detail-drawer"><button class="close" id="close-detail">×</button><span class="eyebrow">DEVICE DETAIL</span><h2 id="detail-name"></h2><p class="device-code" id="detail-code"></p><div class="detail-status" id="detail-status"></div><div class="detail-value"><span id="detail-label"></span><strong id="detail-value"></strong></div><div class="detail-meta"><div><span>所属系统</span><b id="detail-type"></b></div><div><span>数据更新</span><b id="detail-updated"></b></div><div><span>数据绑定</span><b id="detail-binding">未绑定</b></div></div><button class="primary-action">${editMode ? '绑定数据源' : '进入设备驾驶舱'}</button></aside>
    ${editMode ? `<aside class="editor-dock">
      <div class="editor-head"><div><span>数字孪生编辑器</span><strong>设备与数据绑定</strong></div><span class="draft">草稿自动保存</span></div>
      <div class="editor-hint">先在三维场景或楼层设备清单中选择对象，再配置设备数据源。</div>
      <section class="floor-ops" id="floor-ops"><div><span>当前范围</span><strong id="floor-context">园区全部设备</strong></div><div class="floor-kpis"><span>设备 <b id="floor-total">0</b></span><span>在线 <b id="floor-online">0</b></span><span>告警 <b id="floor-warning">0</b></span><span>未绑定 <b id="floor-unbound">0</b></span></div><div class="floor-device-list" id="floor-device-list"></div></section>
      <label>当前对象<input id="bind-object" readonly placeholder="请选择场景对象" /></label>
      <label>设备类型<select id="bind-kind"><option value="sensor">传感器</option><option value="camera">摄像头</option><option value="plc">PLC / 边缘网关</option></select></label>
      <label>接入设备<select id="bind-source"><option value="">请选择设备</option><option value="TEMP-001">温湿度传感器 TEMP-001</option><option value="ELEC-07">智能电表 ELEC-07</option><option value="CAM-12">南门球机 CAM-12</option><option value="PLC-L2">二号产线 PLC-L2</option></select></label>
      <label>协议<select id="bind-protocol"><option>MQTT</option><option>Modbus TCP</option><option>OPC UA</option><option>GB28181</option><option>ONVIF</option></select></label>
      <label>数据点位<input id="bind-point" placeholder="如 telemetry.temperature" /></label>
      <div class="binding-preview" id="binding-preview"><span>实时预览</span><strong>等待绑定</strong><small>选择设备后验证数据链路</small></div>
      <div class="editor-actions"><button id="unbind-device">解除绑定</button><button class="save-binding" id="save-binding">保存绑定</button></div>
    </aside>` : ''}
    <div class="toast" id="toast"></div>
  </div>`;

const sceneHost = document.querySelector<HTMLDivElement>('#scene')!;
const labelsHost = document.querySelector<HTMLDivElement>('#labels')!;
const scene = new THREE.Scene();
const palette = activeProject.palette;
scene.background = new THREE.Color(palette.background);
scene.fog = new THREE.FogExp2(palette.fog, activeProject.key === 'campus' ? 0.006 : 0.01);
const camera = new THREE.PerspectiveCamera(38, sceneHost.clientWidth / sceneHost.clientHeight, 0.1, 300);
camera.position.set(48, 42, 52);
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(sceneHost.clientWidth, sceneHost.clientHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
sceneHost.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0, 0);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.minDistance = 24;
controls.maxDistance = 105;
controls.maxPolarAngle = Math.PI * 0.47;

scene.add(new THREE.HemisphereLight(activeProject.key === 'port' ? 0x7db7df : 0xfff1d2, palette.ground, activeProject.key === 'campus' ? 3.3 : 2.4));
const sun = new THREE.DirectionalLight(activeProject.key === 'energy' ? 0xffc36b : 0xffffff, activeProject.key === 'campus' ? 4.2 : 3.2);
sun.position.set(-25, 55, 35);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -55; sun.shadow.camera.right = 55; sun.shadow.camera.top = 55; sun.shadow.camera.bottom = -55;
scene.add(sun);

const park = new THREE.Group();
scene.add(park);
interface BuildingModel { name:string; group:THREE.Group; floors:THREE.Mesh[]; base:[number,number,number] }
const buildingModels: BuildingModel[] = [];
const mat = (color: number, roughness = .7, metalness = .08) => new THREE.MeshStandardMaterial({ color, roughness, metalness });
const box = (name: string, size: [number, number, number], pos: [number, number, number], material: THREE.Material, parent = park) => {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material); mesh.name = name; mesh.position.set(...pos); mesh.castShadow = true; mesh.receiveShadow = true; parent.add(mesh); return mesh;
};

// Ground, roads and subtle grid
box('园区地块', [76, .5, 58], [0, -.3, 0], mat(palette.ground));
box('纵向主路', [10, .08, 58], [0, .01, 0], mat(palette.road));
box('横向主路', [76, .08, 8], [0, .02, 15], mat(palette.road));
for (let z = -27; z < 28; z += 5) box('道路标线', [.14, .02, 2.2], [0, .08, z], mat(0xcbd5b7));
for (let x = -34; x < 35; x += 5) box('道路标线', [2.2, .02, .14], [x, .09, 15], mat(0xcbd5b7));
const grid = new THREE.GridHelper(76, 38, palette.window, palette.road); grid.position.y = .02; (grid.material as THREE.Material).opacity=.13; (grid.material as THREE.Material).transparent=true; park.add(grid);

function building(name: string, x: number, z: number, w: number, d: number, h: number, color: number) {
  const group = new THREE.Group(); group.name = name;
  const floorCount = Math.max(2, Math.round(h / 2.4));
  const floorHeight = h / floorCount;
  const floors: THREE.Mesh[] = [];
  for (let level=0; level<floorCount; level++) {
    const floor = box(`${name}-${level+1}层`, [w, floorHeight-.12, d], [0, level*floorHeight+floorHeight/2, 0], mat(level%2 ? color : new THREE.Color(color).offsetHSL(0,0,.035).getHex(), .62, .18), group);
    floor.userData = { building:name, floor:level+1, originY:floor.position.y };
    floors.push(floor);
    box(`${name}-${level+1}层楼板`, [w+.18,.1,d+.18], [0,level*floorHeight+.05,0], mat(palette.roof,.5,.2), group);
  }
  box(`${name}-屋顶`, [w + .7, .35, d + .7], [0, h + .18, 0], mat(palette.roof, .45, .35), group);
  const windowMat = mat(palette.window, .25, .4);
  for (let px = -w / 2 + 2; px < w / 2 - 1; px += 3.4) box('窗', [1.7, 1.1, .12], [px, h * .58, d / 2 + .07], windowMat, group);
  for (let rz = -d / 2 + 2; rz < d / 2 - 1; rz += 4) box('屋顶采光带', [w * .72, .08, 1], [0, h + .4, rz], mat(0x79a9a1, .3, .25), group);
  group.position.set(x, 0, z); park.add(group); buildingModels.push({name,group,floors,base:[x,0,z]}); return group;
}

if (activeProject.key === 'industrial') {
  building('智能制造中心', -19, -8, 26, 17, 8, 0x62746e);
  building('精密加工中心', 13, -11, 17, 20, 6, 0x566963);
  building('仓储物流中心', 22, 8, 20, 10, 5, 0x4d605a);
  building('综合管理中心', -20, 8, 17, 10, 7, 0x627873);
  for (let x = 7; x <= 19; x += 4) for (let z = -18; z <= -5; z += 4) {
    const panel = box('光伏板', [3.2, .15, 2.2], [x, 6.65, z], mat(0x164b50, .22, .6)); panel.rotation.x = -.12;
  }
  for (const x of [8, 14, 20]) {
    const tank = new THREE.Mesh(new THREE.CylinderGeometry(2.1, 2.1, 6, 28), mat(0x778a84, .36, .55)); tank.position.set(x, 3, 5); tank.castShadow = true; park.add(tank);
    const top = new THREE.Mesh(new THREE.SphereGeometry(2.08, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), mat(0x778a84, .36, .55)); top.position.set(x, 6, 5); park.add(top);
  }
} else if (activeProject.key === 'campus') {
  building('第一教学楼', -20, -9, 23, 14, 9, 0x627b75);
  building('图书馆', 5, -12, 16, 16, 11, 0x506f6a);
  building('实验中心', 24, -9, 16, 13, 9, 0x61736f);
  building('学生公寓', 23, 9, 18, 13, 12, 0x556d67);
  building('体育馆', -20, 10, 20, 14, 7, 0x48645d);
  const lake = new THREE.Mesh(new THREE.CircleGeometry(5, 40), new THREE.MeshStandardMaterial({color:0x17645f,roughness:.18,metalness:.2})); lake.rotation.x=-Math.PI/2; lake.position.set(-5,.08,7); park.add(lake);
  box('运动场', [18,.12,9], [-19,.12,20], mat(0x2f7254));
} else if (activeProject.key === 'port') {
  building('港区综合调度中心', 24, 10, 18, 11, 7, 0x526b68);
  building('冷链仓储中心', 24, -7, 19, 12, 6, 0x4a6564);
  for(let x=-28;x<13;x+=5) for(let z=-13;z<8;z+=4) box('集装箱',[4.1,2.2,2.2],[x,1.1,z],mat(((x+z)%3===0)?0x9b5b32:((x+z)%2===0)?0x315f69:0x7b3d34,.62,.3));
  for(const x of [-25,-10]) { box('岸桥立柱',[1,12,1],[x,6,-16],mat(0x607873,.4,.5)); box('岸桥横梁',[10,.7,.8],[x,11.5,-16],mat(0x607873,.4,.5)); }
  box('海面',[76,.15,13],[0,.02,23],mat(0x123f46,.18,.25));
  box('货轮船体',[27,2.5,6],[-18,1.3,23],mat(0x394c4c,.4,.45));
} else {
  building('储能电站', 17, 14, 18, 9, 6, 0x526965);
  building('升压站', -6, 18, 15, 9, 7, 0x556e69);
  for(let x=-31;x<7;x+=5) for(let z=-20;z<12;z+=5) { const panel=box('光伏阵列',[4.2,.15,2.8],[x,.9,z],mat(0x164b50,.2,.68)); panel.rotation.x=-.18; }
  for(const [x,z] of [[16,-14],[29,-3],[19,2],[31,12]] as [number,number][]) {
    const mast=new THREE.Mesh(new THREE.CylinderGeometry(.25,.55,13,12),mat(0x81938f,.35,.62)); mast.position.set(x,6.5,z); park.add(mast);
    const hub=new THREE.Group(); hub.position.set(x,13,z); for(let i=0;i<3;i++){const blade=box('风机叶片',[.22,7,.45],[0,3.2,0],mat(0xc1d3cd,.35,.45),hub); blade.rotation.z=i*Math.PI*2/3;} park.add(hub);
  }
}

// Trees, lights, gate and boundary
for (const [x, z] of [[-34,-23],[-34,-15],[-34,-7],[-34,1],[-34,9],[34,-23],[34,-15],[34,-7],[34,1],[34,9],[-30,25],[-22,25],[22,25],[30,25]] as [number,number][]) {
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(.14,.2,1.7,8), mat(0x5b4935)); trunk.position.set(x,.85,z); park.add(trunk);
  const crown = new THREE.Mesh(new THREE.IcosahedronGeometry(1.05,1), mat(0x276451)); crown.position.set(x,2.2,z); crown.castShadow=true; park.add(crown);
}
box('南门门岗', [5, 2.8, 3], [-8, 1.4, 26], mat(0x596e68));
box('园区门楣', [13, .8, .8], [0, 4.6, 27], mat(0x2d5c53, .5, .35));
box('门柱左', [.8, 4.6, .8], [-6, 2.3, 27], mat(0x60746e)); box('门柱右', [.8, 4.6, .8], [6, 2.3, 27], mat(0x60746e));
for (let x=-37; x<=37; x+=4) { box('围栏', [.08,1.3,.08], [x,.65,-28.7], mat(0x47615a,.45,.45)); box('围栏', [.08,1.3,.08], [x,.65,28.7], mat(0x47615a,.45,.45)); }

// Map every logical device into the nearest building and a deterministic floor.
// This association drives floor isolation, device counts and binding workflows.
devices.forEach((device,index) => {
  const nearest = buildingModels.reduce((best,current) => {
    const bd=Math.hypot(device.position[0]-best.base[0],device.position[2]-best.base[2]);
    const cd=Math.hypot(device.position[0]-current.base[0],device.position[2]-current.base[2]);
    return cd<bd?current:best;
  },buildingModels[0]);
  device.building=nearest.name;
  device.floor=(index%nearest.floors.length)+1;
});

// Device markers and HTML tags
const deviceTargets: THREE.Object3D[] = [];
devices.forEach(device => {
  const group = new THREE.Group(); group.position.set(...device.position); group.userData.device = device;
  const core = new THREE.Mesh(new THREE.SphereGeometry(.34, 16, 12), new THREE.MeshBasicMaterial({ color: statusColor[device.status] }));
  const ring = new THREE.Mesh(new THREE.RingGeometry(.55, .7, 28), new THREE.MeshBasicMaterial({ color: statusColor[device.status], transparent: true, opacity: .55, side: THREE.DoubleSide })); ring.rotation.x = -Math.PI / 2;
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(.025,.12,2.2,10,1,true), new THREE.MeshBasicMaterial({ color: statusColor[device.status], transparent: true, opacity: .18 })); beam.position.y = 1.1;
  core.userData.device = device; ring.userData.device = device; group.add(core, ring, beam); park.add(group); device.mesh = group; deviceTargets.push(core, ring);
  const tag = document.createElement('button'); tag.className = `device-tag ${device.status}`; tag.innerHTML = `<i></i><span>${device.name}</span><b>${device.value}${device.unit}</b>`; tag.onclick = () => selectDevice(device,true); labelsHost.appendChild(tag); device.tag = tag;
});

let selected: Device | null = null;
const bindingKey = `easyaiot:twin-bindings:${activeProject.key}`;
try {
  const saved = JSON.parse(localStorage.getItem(bindingKey) || '{}');
  devices.forEach(device => { if (saved[device.id]) device.binding = saved[device.id]; });
} catch { /* invalid local draft is ignored */ }

function selectDevice(device: Device, openDetail = false) {
  selected = device;
  document.querySelectorAll('.device-row').forEach(el => el.classList.toggle('selected', (el as HTMLElement).dataset.id === device.id));
  devices.forEach(d => d.tag?.classList.toggle('selected', d.id === device.id));
  const drawer = document.querySelector('#detail-drawer')!; if (!editMode && openDetail) drawer.classList.add('open');
  document.querySelector('#detail-name')!.textContent = device.name;
  document.querySelector('#detail-code')!.textContent = `${device.id} · ${device.position.map(v => v.toFixed(1)).join(', ')}`;
  const status = document.querySelector('#detail-status')!; status.className = `detail-status ${device.status}`; status.textContent = `● ${statusName[device.status]}`;
  document.querySelector('#detail-label')!.textContent = device.label;
  document.querySelector('#detail-value')!.textContent = `${device.value} ${device.unit}`;
  document.querySelector('#detail-type')!.textContent = device.type;
  document.querySelector('#detail-updated')!.textContent = device.updated;
  document.querySelector('#detail-binding')!.textContent = device.binding ? `${device.binding.sourceName} · ${device.binding.protocol}` : '未绑定';
  if (editMode) {
    (document.querySelector('#bind-object') as HTMLInputElement).value = `${device.name} (${device.id})`;
    const source = document.querySelector('#bind-source') as HTMLSelectElement;
    const protocol = document.querySelector('#bind-protocol') as HTMLSelectElement;
    const point = document.querySelector('#bind-point') as HTMLInputElement;
    source.value = device.binding?.sourceId || '';
    protocol.value = device.binding?.protocol || 'MQTT';
    point.value = device.binding?.point || '';
    updateBindingPreview();
    renderFloorOps();
  }
}

function renderDevices(filter: string = 'all') {
  const visible = devices.filter(d => filter === 'all' || d.status === filter);
  document.querySelector('#device-list')!.innerHTML = visible.map(d => `<button class="device-row ${selected?.id === d.id ? 'selected' : ''}" data-id="${d.id}"><span class="status-icon ${d.status}">${d.type.includes('能源') || d.type.includes('电') || d.type.includes('光伏') ? '⚡' : d.type === '安防设备' ? '◉' : d.type === '环境传感' ? '⌁' : '⌘'}</span><div><strong>${d.name}</strong><small>${d.id} · ${d.label}</small></div><em class="${d.status}">${statusName[d.status]}</em><b>${d.value}<small>${d.unit}</small></b></button>`).join('');
  document.querySelectorAll<HTMLElement>('.device-row').forEach(row => row.onclick = () => selectDevice(devices.find(d => d.id === row.dataset.id)!,true));
}
renderDevices();

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
let pointerStart={x:0,y:0};
renderer.domElement.addEventListener('pointerdown',event=>{pointerStart={x:event.clientX,y:event.clientY};});
renderer.domElement.addEventListener('pointerup', event => {
  if ((event as PointerEvent).button !== 0) return;
  if(Math.hypot(event.clientX-pointerStart.x,event.clientY-pointerStart.y)>5)return;
  const rect = renderer.domElement.getBoundingClientRect(); mouse.set(((event.clientX-rect.left)/rect.width)*2-1, -((event.clientY-rect.top)/rect.height)*2+1);
  raycaster.setFromCamera(mouse,camera); const hit = raycaster.intersectObjects(deviceTargets,false)[0]; if (hit?.object.userData.device) selectDevice(hit.object.userData.device,true);
});

const views: Record<string, { position: [number,number,number], target: [number,number,number] }> = {
  overview: { position: [48,42,52], target: [0,0,0] }, production: { position: [-8,20,28], target: [-14,2,-7] }, energy: { position: [31,17,25], target: [15,2,3] }, gate: { position: [4,12,43], target: [0,2,24] }
};
let cameraTween: { start:number, from:THREE.Vector3, to:THREE.Vector3, targetFrom:THREE.Vector3, targetTo:THREE.Vector3 } | null = null;
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(btn => btn.onclick = () => {
  document.querySelectorAll('[data-view]').forEach(el => el.classList.remove('active')); btn.classList.add('active');
  const v = views[btn.dataset.view!]; cameraTween = { start: performance.now(), from: camera.position.clone(), to: new THREE.Vector3(...v.position), targetFrom: controls.target.clone(), targetTo: new THREE.Vector3(...v.target) };
});

const buildingSelect = document.querySelector('#building-select') as HTMLSelectElement;
const floorSelect = document.querySelector('#floor-select') as HTMLSelectElement;
buildingSelect.innerHTML = buildingModels.map((b,i)=>`<option value="${i}">${b.name}</option>`).join('');
let floorsExploded = false;
let singleFloorMode = false;
let activeFloorNumber: number | null = null;
function activeBuilding() { return buildingModels[Number(buildingSelect.value) || 0]; }
function scopedDevices() {
  if (!singleFloorMode || activeFloorNumber===null) return devices;
  return devices.filter(device=>device.building===activeBuilding().name && device.floor===activeFloorNumber);
}
function renderFloorOps() {
  if (!editMode) return;
  const scoped=scopedDevices();
  const context=document.querySelector('#floor-context');
  if(context) context.textContent=singleFloorMode?`${activeBuilding().name} · ${activeFloorNumber} 层`:'园区全部设备';
  const totals:Record<string,number>={
    'floor-total':scoped.length,
    'floor-online':scoped.filter(d=>d.status==='online').length,
    'floor-warning':scoped.filter(d=>d.status!=='online').length,
    'floor-unbound':scoped.filter(d=>!d.binding).length,
  };
  Object.entries(totals).forEach(([id,value])=>{const el=document.querySelector(`#${id}`);if(el)el.textContent=String(value);});
  const list=document.querySelector('#floor-device-list');
  if(!list)return;
  list.innerHTML=scoped.length?scoped.map(d=>`<button data-floor-device="${d.id}" class="${selected?.id===d.id?'active':''}"><i class="${d.status}"></i><span><strong>${d.name}</strong><small>${d.type} · ${d.label}</small></span><em>${d.binding?'已绑定':'待绑定'}</em></button>`).join(''):'<p>该楼层暂未配置设备</p>';
  list.querySelectorAll<HTMLElement>('[data-floor-device]').forEach(row=>row.onclick=()=>selectDevice(devices.find(d=>d.id===row.dataset.floorDevice)!,false));
}
function syncFloorOptions() {
  const model = activeBuilding();
  floorSelect.innerHTML = '<option value="all">整栋</option>' + model.floors.map((_,i)=>`<option value="${i}">${i+1} 层</option>`).join('');
}
function renderFloorStack() {
  const panel=document.querySelector('#floor-stack-panel')!;
  panel.classList.toggle('open',floorsExploded);
  if(!floorsExploded)return;
  const model=activeBuilding();
  document.querySelector('#floor-stack-title')!.textContent=model.name;
  const list=document.querySelector('#floor-stack-list')!;
  list.innerHTML=[...model.floors].reverse().map((_,reverseIndex)=>{
    const floor=model.floors.length-reverseIndex;
    const items=devices.filter(d=>d.building===model.name&&d.floor===floor);
    const alarms=items.filter(d=>d.status!=='online').length;
    return `<button data-open-floor="${floor}"><span><b>${floor}F</b><i>${floor} 层</i></span><em>设备 ${items.length}</em><em class="${alarms?'alarm':''}">${alarms?`异常 ${alarms}`:'运行正常'}</em><strong>进入 →</strong></button>`;
  }).join('');
  list.querySelectorAll<HTMLElement>('[data-open-floor]').forEach(row=>row.onclick=()=>enterFloor(Number(row.dataset.openFloor)-1));
}
syncFloorOptions();
renderFloorOps();
buildingSelect.onchange = () => { exitFloor(); syncFloorOptions(); };
function exitFloor() {
  singleFloorMode=false;
  activeFloorNumber=null;
  buildingModels.forEach(model=>{ model.group.visible=true; model.group.children.forEach(child=>child.visible=true); model.floors.forEach(f=>f.position.y=f.userData.originY); });
  devices.forEach(device=>{if(device.mesh){device.mesh.visible=true;device.mesh.position.set(...device.position);}});
  floorsExploded=false;
  document.querySelector('#explode-floors')!.textContent='展开模式';
  renderFloorStack();
  cameraTween={start:performance.now(),from:camera.position.clone(),to:new THREE.Vector3(48,42,52),targetFrom:controls.target.clone(),targetTo:new THREE.Vector3(0,0,0)};
  renderFloorOps();
}
document.querySelector('#explode-floors')!.addEventListener('click',()=>{
  if(singleFloorMode) exitFloor();
  const model=activeBuilding(); floorsExploded=!floorsExploded;
  buildingModels.forEach(other=>{other.group.visible=other===model || !floorsExploded;});
  model.group.children.forEach(child=>child.visible=!floorsExploded||model.floors.includes(child as THREE.Mesh));
  model.floors.forEach((floor,i)=>floor.position.y=floor.userData.originY+(floorsExploded?i*3.4:0));
  devices.forEach(device=>{if(device.mesh){device.mesh.visible=!floorsExploded||device.building===model.name;if(floorsExploded&&device.building===model.name){const floor=model.floors[(device.floor||1)-1];device.mesh.position.y=floor.position.y+1;}}});
  document.querySelector('#explode-floors')!.textContent=floorsExploded?'普通模式':'展开模式';
  cameraTween={start:performance.now(),from:camera.position.clone(),to:new THREE.Vector3(model.base[0]+29,27,model.base[2]+32),targetFrom:controls.target.clone(),targetTo:new THREE.Vector3(model.base[0],8,model.base[2])};
  renderFloorStack();
});
function enterFloor(index:number) {
  const model=activeBuilding();
  floorSelect.value=String(index);
  singleFloorMode=true; activeFloorNumber=index+1; buildingModels.forEach(other=>other.group.visible=other===model);
  model.group.children.forEach(child=>child.visible=false); model.floors[index].visible=true;
  const floorY=model.floors[index].userData.originY; model.floors[index].position.y=floorY;
  devices.forEach(device=>{if(device.mesh){device.mesh.visible=device.building===model.name&&device.floor===activeFloorNumber;if(device.mesh.visible)device.mesh.position.y=floorY+1;}});
  cameraTween={start:performance.now(),from:camera.position.clone(),to:new THREE.Vector3(model.base[0]+15,floorY+10,model.base[2]+16),targetFrom:controls.target.clone(),targetTo:new THREE.Vector3(model.base[0],floorY,model.base[2])};
  toast(`已进入 ${model.name} · ${index+1} 层`);
  selected=null; renderFloorOps();
  document.querySelector('#floor-stack-panel')!.classList.remove('open');
}
document.querySelector('#enter-floor')!.addEventListener('click',()=>enterFloor(floorSelect.value==='all'?0:Number(floorSelect.value)));
document.querySelector('#exit-floor')!.addEventListener('click',exitFloor);

function updateLabels() {
  devices.forEach(d => { if (!d.tag || !d.mesh) return; const p = new THREE.Vector3(); d.mesh.getWorldPosition(p); p.y += 1; p.project(camera); const inScope=!singleFloorMode||(d.building===activeBuilding().name&&d.floor===activeFloorNumber); const visible = inScope&&d.mesh.visible&&p.z < 1 && Math.abs(p.x) < 1.2 && Math.abs(p.y) < 1.2; d.tag.style.display = visible ? 'flex' : 'none'; d.tag.style.transform = `translate(-50%,-100%) translate(${(p.x*.5+.5)*sceneHost.clientWidth}px,${(-p.y*.5+.5)*sceneHost.clientHeight}px)`; });
}

function animate(time: number) {
  requestAnimationFrame(animate); controls.update();
  devices.forEach((d,i) => { if (!d.mesh) return; const ring = d.mesh.children[1] as THREE.Mesh; const scale = 1 + (Math.sin(time*.0025+i)*.12+.12); ring.scale.setScalar(scale); });
  if (cameraTween) { const t = Math.min((time-cameraTween.start)/900,1); const e = 1-Math.pow(1-t,3); camera.position.lerpVectors(cameraTween.from,cameraTween.to,e); controls.target.lerpVectors(cameraTween.targetFrom,cameraTween.targetTo,e); if(t===1) cameraTween=null; }
  updateLabels(); renderer.render(scene,camera);
}
requestAnimationFrame(animate);

function updateChart() {
  const values = Array.from({length: 20}, (_,i) => 38 + Math.sin(i*.55)*9 + Math.random()*8 + i*.5);
  const points = values.map((v,i) => `${i/(values.length-1)*300},${88-v}`).join(' ');
  document.querySelector<SVGPathElement>('#power-chart .line')!.setAttribute('d', `M${points.replaceAll(' ', ' L')}`);
  document.querySelector<SVGPathElement>('#power-chart .area')!.setAttribute('d', `M0,92 L${points.replaceAll(' ', ' L')} L300,92 Z`);
}
updateChart();

setInterval(() => {
  devices.filter(d => d.status !== 'offline').forEach(d => { const swing = d.unit === 'kW' ? 3 : d.unit === '%' ? 1.2 : .3; d.value = Math.max(0, +(d.value + (Math.random()-.5)*swing).toFixed(d.unit === 'kW' ? 0 : 1)); if(d.tag) d.tag.querySelector('b')!.textContent = `${d.value}${d.unit}`; });
  document.querySelector('#power-total')!.textContent = Math.round(1835 + Math.random()*24).toLocaleString();
  document.querySelector('#ambient-temp')!.innerHTML = `${(26.1+Math.random()*.6).toFixed(1)}<small>°C</small>`;
  const featured = devices.find(d=>d.unit==='kW' || d.unit==='MW') || devices[0];
  document.querySelector('#pv-power')!.innerHTML = `${featured.value}<small>${featured.unit}</small>`;
  const activeFilter = document.querySelector<HTMLButtonElement>('.tabs button.active')!.dataset.filter!; renderDevices(activeFilter);
  if(selected) selectDevice(selected);
}, 2500);

setInterval(updateChart, 8000);
function updateClock() { document.querySelector('#clock')!.textContent = new Intl.DateTimeFormat('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date()).replaceAll('/','-'); }
updateClock(); setInterval(updateClock,1000);

document.querySelectorAll<HTMLButtonElement>('.tabs button').forEach(btn => btn.onclick = () => { document.querySelectorAll('.tabs button').forEach(el=>el.classList.remove('active')); btn.classList.add('active'); renderDevices(btn.dataset.filter); });
document.querySelector('#close-detail')!.addEventListener('click',()=>document.querySelector('#detail-drawer')!.classList.remove('open'));
document.querySelectorAll<HTMLElement>('.alerts article').forEach(a => a.onclick=()=>selectDevice(devices.find(d=>d.id===a.dataset.device)!,true));
document.querySelector('#fullscreen')!.addEventListener('click',()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen());
const toast = (message:string) => { const el=document.querySelector('#toast')!; el.textContent=message; el.classList.add('show'); setTimeout(()=>el.classList.remove('show'),2200); };
document.querySelector('#filter-btn')!.addEventListener('click',()=>toast('筛选条件已展开：状态 · 系统 · 区域'));
document.querySelector('#all-alerts')!.addEventListener('click',()=>toast('当前共有 3 条未处理告警'));
document.querySelector('.primary-action')!.addEventListener('click',()=> {
  if (editMode) document.querySelector('.editor-dock')?.classList.add('attention');
  toast(editMode ? '请在右侧完成设备数据源绑定' : '设备驾驶舱接口已预留');
});

function updateBindingPreview() {
  if (!editMode) return;
  const preview = document.querySelector('#binding-preview')!;
  const source = document.querySelector('#bind-source') as HTMLSelectElement;
  const point = document.querySelector('#bind-point') as HTMLInputElement;
  preview.innerHTML = source.value
    ? `<span>链路验证通过</span><strong>${source.options[source.selectedIndex].text}</strong><small>${(document.querySelector('#bind-protocol') as HTMLSelectElement).value} · ${point.value || '待配置点位'}</small>`
    : '<span>实时预览</span><strong>等待绑定</strong><small>选择设备后验证数据链路</small>';
}

if (editMode) {
  ['bind-source','bind-protocol','bind-point'].forEach(id => document.querySelector(`#${id}`)?.addEventListener('input', updateBindingPreview));
  document.querySelector('#save-binding')?.addEventListener('click', () => {
    if (!selected) return toast('请先选择一个三维对象');
    const source = document.querySelector('#bind-source') as HTMLSelectElement;
    if (!source.value) return toast('请选择需要绑定的设备');
    const point = (document.querySelector('#bind-point') as HTMLInputElement).value.trim();
    if (!point) return toast('请填写数据点位');
    selected.binding = { sourceId:source.value, sourceName:source.options[source.selectedIndex].text, protocol:(document.querySelector('#bind-protocol') as HTMLSelectElement).value, point };
    localStorage.setItem(bindingKey, JSON.stringify(Object.fromEntries(devices.filter(d=>d.binding).map(d=>[d.id,d.binding]))));
    selectDevice(selected); toast('设备绑定已保存');
  });
  document.querySelector('#unbind-device')?.addEventListener('click', () => {
    if (!selected?.binding) return toast('当前对象尚未绑定');
    delete selected.binding;
    localStorage.setItem(bindingKey, JSON.stringify(Object.fromEntries(devices.filter(d=>d.binding).map(d=>[d.id,d.binding]))));
    selectDevice(selected); toast('已解除设备绑定');
  });
}

window.addEventListener('resize',()=>{ camera.aspect=sceneHost.clientWidth/sceneHost.clientHeight; camera.updateProjectionMatrix(); renderer.setSize(sceneHost.clientWidth,sceneHost.clientHeight); });
