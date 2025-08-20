# EasyAIoT (DeepCore AI Cloud Platform)
### My vision is for this system to be accessible worldwide, achieving truly zero barriers to AI. Everyone should experience the benefits of AI, not just a privileged few.
<div align="center">
    <img src=".image/logo.png" width="30%" height="30%" alt="EasyAIoT">
</div>

## 🌟 Some Thoughts on the Project
#### I believe no single programming language excels at everything. However, when three programming languages are combined, EasyAIoT will become unparalleled – and it happens that I possess this unique trait.
#### Java is suitable for platform development but not for network or AI programming. Python excels at network and AI programming but is less ideal for high-performance task execution. C++ is great for high-performance tasks but struggles with the domains of the other two. EasyAIoT envisions employing trilingual hybrid coding to build an AIoT platform that is challenging to implement, but incredibly easy to use.
![EasyAIoT Platform Architecture.jpg](.image/iframe2.jpg)
#### EasyAIoT is not actually one project; it is five distinct projects.
#### What's the benefit? Suppose you are on a resource-constrained device (like an RK3588). You can extract and independently deploy just one of those projects. Therefore, while this project appears to be a cloud platform, it simultaneously functions as an edge platform.

### 🌟 Genuine open source is rare. If you find this project useful, please star it before leaving - your support means everything to us!(In an era where fake open-source projects are rampant, this project stands out as an exception.)

## 🎯 Application Scenarios
![Application Scenarios.png](.image/适用场景.png)

## 🛠️ Solutions
<div>
  <img src=".image/解决方案1.png" alt="Solution 1" width="49%" style="margin-right: 10px">
  <img src=".image/解决方案2.png" alt="Solution 2" width="49%">
</div>

## 🧩 Project Structure
EasyAIoT consists of five core projects:
- **WEB Module**: Frontend management interface based on Vue
- **DEVICE Module**: Java-based device management module responsible for IoT device access and management
- **VIDEO Module**: Python-based video processing module responsible for video stream processing and transmission
- **AI Module**: Python-based artificial intelligence processing module responsible for video analysis and AI algorithm execution
- **TASK Module**: C++-based high-performance task processing module responsible for compute-intensive task execution

## ☁️ EasyAIoT = AI + IoT = Cloud-Edge Integrated Solution
Supports thousands of vertical scenarios with customizable AI models and algorithm development. 

Deep integration empowers intelligent vision for everything: EasyAIoT constructs an efficient access and management network for IoT devices (especially massive cameras). We deeply integrate real-time streaming technology with cutting-edge AI to create a unified service core. This solution not only enables interoperability across heterogeneous devices but also deeply integrates HD video streams with powerful AI analytics engines, giving surveillance systems "intelligent eyes" – accurately enabling facial recognition, abnormal behavior analysis, risk personnel monitoring, and perimeter intrusion detection.

![EasyAIoT Platform Architecture](.image/iframe1.jpg)

## ⚠️ Disclaimer

EasyAIoT is an open-source learning project unrelated to commercial activities. Users must comply with laws and regulations and refrain from illegal activities. If EasyAIoT discovers user violations, it will cooperate with authorities and report to government agencies. Users bear full legal responsibility for illegal actions and shall compensate third parties for damages caused by usage. All EasyAIoT-related resources are used at the user's own risk.

## 📚 Official Documentation
- Documentation: http://pro.basiclab.top:9988/

## 🎮 Demo Environment
- Demo URL: http://pro.basiclab.top:8888/
- Username: admin
- Password: admin123

## 🔓 Open Source Edition (Completely Free, Welcome to Use)
- **Positioning**: Lightweight, user-friendly, and technology-driven
- **Use Cases**: Ideal for personal learning and small-to-medium-sized projects
- **Maintenance Commitment**: The open-source version fully meets the business needs of most companies with no feature limitations. It will continue to be actively maintained—rest assured.

## 🏢 PRO Edition (Priced at roughly one month's salary of a typical developer)
Expands upon the open-source edition with enterprise-oriented features and performance optimizations.

**Use Cases**:
- Meets the business and stability requirements of medium-to-large-scale projects.

**Key Extended Features Include**:
- **NVR Module**: Supports edge recording devices (e.g., police body cameras, vehicle dashcams, drones) .
- **Model Hub**: Offers expanded pre-trained model selections.
- **Vertical-Specific Solutions**: Tailored solutions for industries such as transportation, security, industrial, healthcare, logistics, and education.
- **SIP Protocol**: Supports standard SIP protocol communication.
- **Cluster Deployment for Models**: Enables large-scale model cluster deployment.
- **Online Custom Operator Development**: Supports online custom operator development.
- **GPU Resource Partitioning**: Fine-grained GPU resource allocation management.
- **Camera PTZ Control**: Remote control of camera angles and positioning.
- **Cloud Video Storage**: Cloud-based video recording storage and management.
- **Batch Keyframe Extraction & Analysis**: Supports intelligent analysis via batch video keyframe extraction.
- **AI Alerting**: AI-driven real-time alerting system with abnormal behavior detection and automatic alert.
- **Lingering Detection**: Intelligently detects prolonged human presence in specific areas to identify abnormal behavior.
- **People Counting**: Real-time statistics on personnel counts in monitored areas, generating data reports.
- **Person Tracking**: Continuous cross-camera tracking of target individuals with trajectory recording.
- **OCR Text Recognition**: Extracts and recognizes text from images/videos.
- **Vehicle Recognition**: Identifies multiple vehicle types (e.g., cars, trucks, buses, motorcycles).
- **License Plate Recognition**: Accurately identifies license plate information across multiple plate types.

**Technical Support?**:  
- One year of technical support included. After purchasing a license, project-related questions will be answered one-on-one (covers basic technical issues, not custom development—please note).

**Invoice Provided?**: 
- Official invoices available.

## ⚙️ Project Repositories
- Gitee: https://gitee.com/soaring-xiongkulu/easyaiot
- Github: https://github.com/soaring-xiongkulu/easyaiot

## 🛠️ Technology Stack
### Frontend
- **Core Framework**: Vue 3.3.8
- **Development Language**: TypeScript 5.2.2
- **Build Tool**: Vite 4.5.0
- **UI Component Library**: Ant Design Vue 4.0.7
- **State Management**: Pinia 2.1.7
- **Routing**: Vue Router 4.2.5
- **HTTP Client**: Axios/Alova 1.6.1
- **CSS**: UnoCSS 0.57.3
- **Package Manager**: pnpm 9.0.4

### Backend
- **DEVICE Module Framework**: 
  - Spring Boot 2.7.18
  - Spring Boot Starter Security
  - Gateway
  - SkyWalking
  - OpenFeign
  - Sentinel
  - Nacos
  - Kafka
  - TDEngine
  - MyBatis-Plus
  - PostgreSQL
- **AI Module Framework**：
  - Python 3.11+
  - Flask
  - Flask-Cors
  - Flask-Migrate
  - Flask-SQLAlchemy
  - OpenCV (cv2)
  - Pillow (PIL.Image)
  - Ultralytics
  - Psycopg2-Binary
- **VIDEO Module Framework**：
  - Python 3.11+
  - WSDiscovery
  - Netifaces
  - Onvif-Zeep
  - Pyserial
  - Paho_Mqtt
  - Flask
  - Flask-Cors
  - Flask-Migrate
  - Flask-SQLAlchemy
  - Psycopg2-Binary
- **TASK Module Framework**：
  - C++17
  - Opencv2
  - Httplib
  - Json
  - Librknn
  - Minio-Cpp
  - Mk-Media
  - RGA
  - Logging
  - Queue
  - Thread

## 📸 Screenshots
<div>
  <img src=".image/banner/banner1001.png" alt="Screenshot 1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1009.jpg" alt="Screenshot 2" width="49%">
</div>
<div>
  <img src=".image/banner/banner1006.jpg" alt="Screenshot 3" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1010.jpg" alt="Screenshot 4" width="49%">
</div>
<div>
  <img src=".image/banner/banner1015.png" alt="Screenshot 5" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1016.jpg" alt="Screenshot 6" width="49%">
</div>
<div>
  <img src=".image/banner/banner1007.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1008.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1013.jpg" alt="Screenshot 9" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1014.png" alt="Screenshot 10" width="49%">
</div>
<div>
  <img src=".image/banner/banner1011.jpg" alt="Screenshot 11" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1012.jpg" alt="Screenshot 12" width="49%">
</div>
<div>
  <img src=".image/banner/banner1003.png" alt="Screenshot 13" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1004.png" alt="Screenshot 14" width="49%">
</div>
<div>
  <img src=".image/banner/banner1005.png" alt="Screenshot 15" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1002.png" alt="Screenshot 16" width="49%">
</div>

## 📞 Contact Information
### WeChat (Join Knowledge Planet for technical discussions):
<p><img src=".image/联系方式.jpg" alt="Contact QR Code" width="30%"></p>

### Knowledge Planet:
- Voluntarily join with payment for consultations, resource access, and entry into WeChat technical groups.
- Students may sponsor any amount to join both the WeChat technical group and Knowledge Planet. [Though not a bright pearl, I aspire to be fertile soil that nurtures new sprouts into pillars.]
<p>  
<img src=".image/知识星球.jpg" alt="Knowledge Planet" width="30%">  
</p>

## 💰 Sponsorship
<div>
    <img src=".image/微信支付.jpg" alt="WeChat Pay" width="30%" height="30%">
    <img src=".image/支付宝支付.jpg" alt="Alipay" width="30%" height="10%">
</div>

## 🙏 Acknowledgements
Thanks to the following contributors for code, feedback, donations, and support (in no particular order):
- shup 派大星 棒槌 憨憨 一往无前 文艺小青年 lion 汪汪队立大功 春生 二群主 hao_chen yuer629 kong 岁月静好 Kunkka 李江峰 左耳向右 Chao. 火
- Mr.LuCkY 泓 i 放学丶别走 Kosho 小菜鸟先飞 追溯未来-_- 贵阳王老板 kevin 青衫 贾仁超 Lee ㏒灵韵№  Fae wcj 碎碎念. 怒放de生命
- 蓝速传媒 Dorky TAT 北街 Achieve_Xu  NicholasLD 墨白 童年 take your time or 城市稻草人 小小白

## 📄 Open Source License
[MIT LICENSE](LICENSE)

## ©️ Copyright Notice
EasyAIoT follows the [MIT LICENSE](LICENSE). Commercial use is permitted provided original author/copyright information is retained.
