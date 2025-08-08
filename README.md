# EasyAIoT（深度智核AI云平台）

<div align="center">
    <img src=".image/logo.png" width="30%" height="30%" alt="EasyAIoT">
</div>

## EasyAIoT = AI + IoT = 云边一体化解决方案
### 支持上千种垂直场景，支持AI模型定制化和AI算法定制化开发
#### 深度融合，赋能万物智视：EasyAIoT 构筑了物联网设备（尤其是海量摄像头）的高效接入与管控网络。我们深度融合流媒体实时传输技术与前沿人工智能（AI），打造一体化服务核心。这套方案不仅打通了异构设备的互联互通，更将高清视频流与强大的AI解析引擎深度集成，赋予监控系统“智能之眼”——精准实现人脸识别、异常行为分析、风险人员布控及周界入侵检测

![EasyAIoT平台架构.jpg](.image/EasyAIoT平台架构.jpg)

## 免责声明：

EasyAIoT是一个开源学习项目，与商业行为无关。用户在使用该项目时，应遵循法律法规，不得进行非法活动。如果EasyAIoT发现用户有违法行为，将会配合相关机关进行调查并向政府部门举报。用户因非法行为造成的任何法律责任均由用户自行承担，如因用户使用造成第三方损害的，用户应当依法予以赔偿。使用EasyAIoT所有相关资源均由用户自行承担风险.

## 演示环境（开源版暂不提供演示环境，因为还没写完）
云平台演示：http://pro.basiclab.top:8888
账号：admin
密码：admin123

边缘平台演示：http://234604e8d1b148c2.pro.rknn.net:8088
账号：admin
密码：admin123

## 技术栈

### 前端
- **核心框架**：Vue 3.3.8
- **开发语言**：TypeScript 5.2.2
- **构建工具**：Vite 4.5.0
- **UI组件库**：Ant Design Vue 4.0.7
- **状态管理**：Pinia 2.1.7
- **路由**：Vue Router 4.2.5
- **HTTP客户端**：Axios/Alova 1.6.1
- **CSS**：UnoCSS 0.57.3
- **包管理器**：pnpm 9.0.4

### 后端
- **核心框架**：Spring Boot 2.7.18
- **安全框架**：Spring Boot Starter Security
- **数据操作**：MyBatis-Plus
- **数据库**：PostgreSQL


## 部署安装
##### 后端程序打包
```
mvn clean package -Dmaven.test.skip=true
```
##### 启动MQTT服务端
```
# 端口：8885，Topic：device/data/#
nohup java -server -Xms512m -Xmx1024m -Djava.io.tmpdir=/var/tmp -Duser.timezone=Asia/Shanghai -jar iot-things*.jar --spring.profiles.active=dev  >iot-things.log &
```
##### 后端业务部署
```
nohup java -server -Xms512m -Xmx1024m -Djava.io.tmpdir=/var/tmp -Duser.timezone=Asia/Shanghai -jar iot-device*.jar --spring.profiles.active=dev  >iot-device.log &
nohup java -server -Xms512m -Xmx1024m -Djava.io.tmpdir=/var/tmp -Duser.timezone=Asia/Shanghai -jar iot-gateway*.jar --spring.profiles.active=dev  >iot-gateway.log &
nohup java -server -Xms512m -Xmx1024m -Djava.io.tmpdir=/var/tmp -Duser.timezone=Asia/Shanghai -jar iot-infra*.jar --spring.profiles.active=dev  >iot-infra.log &
nohup java -server -Xms512m -Xmx1024m -Djava.io.tmpdir=/var/tmp -Duser.timezone=Asia/Shanghai -jar iot-system*.jar --spring.profiles.active=dev  >iot-system.log &
```
##### 前端部署
```
pnpm install
pnpm dev
```

## 深度智核AI云平台【开源版】
<div>
  <img src=".image/banner/banner1001.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1002.png" alt="图片1" width="49%">
</div>
<div>
  <img src=".image/banner/banner1003.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1004.png" alt="图片1" width="49%">
</div>
<div>
  <img src=".image/banner/banner1005.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1006.png" alt="图片1" width="49%">
</div>

## 深度智核AI边缘平台【商业版】
<div>
  <img src=".image/banner/banner99.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner100.png" alt="图片1" width="49%">
</div>
<div>
  <img src=".image/banner/banner69.png" alt="图片1" width="49%">
  <img src=".image/banner/ai-box.gif" alt="图片1" width="49%">
</div>
<div>
  <img src=".image/banner/banner60.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner61.png" alt="图片1" width="49%">
</div>
<div>
  <img src=".image/banner/banner66.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner63.png" alt="图片1" width="49%">
</div>
<div>
  <img src=".image/banner/banner64.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner67.png" alt="图片1" width="49%">
</div>
<div>
  <img src=".image/banner/banner65.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner62.png" alt="图片1" width="49%">
</div>

## 深度智核AI云平台【商业版】
<div>
    <img src=".image/banner/banner1.png" alt="图片1" width="49%" style="margin-right: 10px">
    <img src=".image/banner/banner3.png" alt="图片2" width="49%" style="margin-right: 10px">
</div>
<div>
    <img src=".image/banner/banner2.png" alt="图片1" width="49%">
    <img src=".image/banner/banner4.png" alt="图片2" width="49%" style="margin-right: 10px">
</div>
<div>
  <img src=".image/banner/banner31.png" alt="图片2" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner8.png" alt="图片2" width="49%">
</div>
<div>
  <img src=".image/banner/banner33.png" alt="图片3" width="49%">
<img src=".image/banner/banner45.png" alt="图片2" width="49%" style="margin-right: 10px">
</div>
<div>
  <img src=".image/banner/banner51.png" alt="图片2" width="49%">
  <img src=".image/banner/banner46.png" alt="图片2" width="49%">
</div>
<div>
  <img src=".image/banner/banner47.png" alt="图片2" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner48.png" alt="图片2" width="49%">
</div>
<div>
  <img src=".image/banner/banner34.png" alt="图片3" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner3.png" alt="图片3" width="49%">
</div>
<div>
  <img src=".image/banner/banner50.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner35.png" alt="图片2" width="49%">
</div>
<div>
  <img src=".image/banner/banner70.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner71.png" alt="图片2" width="49%">
</div>
<div>
  <img src=".image/banner/banner72.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner73.png" alt="图片2" width="49%">
</div>
<div>
  <img src=".image/banner/banner78.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner79.png" alt="图片2" width="49%">
</div>
<div>
  <img src=".image/banner/banner74.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner75.png" alt="图片2" width="49%">
</div>
<div>
  <img src=".image/banner/banner76.png" alt="图片1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner77.png" alt="图片2" width="49%">
</div>

## 联系方式
### 邮箱：
andywebjava@163.com(本项目相关问题请走issue流程，否则恕不邮件答复)
### 微信号（技术交流请加入知识星球）：
<p><img src=".image/联系方式.jpg" alt="联系方式" width="30%"></p>

### 知识星球：
也可以自愿有偿加入知识星球咨询、获取资料以及加入微信技术群：
<p>
<img src=".image/知识星球.jpg" alt="知识星球" width="30%">
</p>

## 打赏赞助
<div>
    <img src=".image/微信支付.jpg" alt="微信支付" width="30%" height="30%">
    <img src=".image/支付宝支付.jpg" alt="支付宝支付" width="30%" height="10%">
</div>

## 致谢
感谢以下各位对本项目包括但不限于代码贡献、问题反馈、资金捐赠等各种方式的支持！以下排名不分先后：
- shup

## 开源协议
[MIT LICENSE](LICENSE)

## 版权使用说明
EasyAIoT开源平台遵循 [MIT LICENSE](LICENSE) 协议。 允许商业使用，但务必保留类作者、Copyright 信息。