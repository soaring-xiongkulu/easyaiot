# EasyAIoT (DeepAI Hub Cloud Platform)

<div align="center">
    <img src=".image/logo.png" width="30%" height="30%" alt="EasyAIoT">
</div>

## EasyAIoT = AI + IoT = Cloud-Edge Integration Solution
### Supports thousands of vertical scenarios, customizable AI models and algorithm development
#### Deep integration empowers intelligent vision: EasyAIoT establishes an efficient access and management network for IoT devices (especially massive cameras). We deeply integrate real-time streaming technology with cutting-edge AI to create a unified service core. This solution not only enables interconnection of heterogeneous devices but also seamlessly integrates HD video streams with powerful AI analytics engines, granting surveillance systems "intelligent vision"—accurately achieving facial recognition, abnormal behavior analysis, high-risk personnel monitoring, and perimeter intrusion detection.

![EasyAIoT Platform Architecture.jpg](.image/EasyAIoT平台架构.jpg)

## Disclaimer:

EasyAIoT is an open-source learning project with no commercial affiliation. Users must comply with laws and regulations and refrain from illegal activities. If EasyAIoT discovers any unlawful user behavior, it will cooperate with authorities in investigations and report to government agencies. Users bear full legal responsibility for any violations. If user actions cause harm to third parties, users shall provide compensation as required by law. All resources related to EasyAIoT are used at the user's own risk.

## Frontend Project URL
- Gitee: https://gitee.com/soaring-xiongkulu/easyaiot-web
- Github: https://github.com/soaring-xiongkulu/easyaiot-web

### Backend
- **Core Framework**: Spring Boot 2.7.18
- **Security**: Spring Boot Starter Security
- **ORM**: MyBatis-Plus
- **Database**: PostgreSQL

## Deployment
```
mvn clean package -Dmaven.test.skip=true
```
##### Start MQTT Server
```
# Port：8885，Topic：device/data/#
nohup java -server -Xms512m -Xmx1024m -Djava.io.tmpdir=/var/tmp -Duser.timezone=Asia/Shanghai -jar iot-things*.jar --spring.profiles.active=dev  >iot-things.log &
```
##### Package Backend
```
nohup java -server -Xms512m -Xmx1024m -Djava.io.tmpdir=/var/tmp -Duser.timezone=Asia/Shanghai -jar iot-device*.jar --spring.profiles.active=dev  >iot-device.log &
nohup java -server -Xms512m -Xmx1024m -Djava.io.tmpdir=/var/tmp -Duser.timezone=Asia/Shanghai -jar iot-gateway*.jar --spring.profiles.active=dev  >iot-gateway.log &
nohup java -server -Xms512m -Xmx1024m -Djava.io.tmpdir=/var/tmp -Duser.timezone=Asia/Shanghai -jar iot-infra*.jar --spring.profiles.active=dev  >iot-infra.log &
nohup java -server -Xms512m -Xmx1024m -Djava.io.tmpdir=/var/tmp -Duser.timezone=Asia/Shanghai -jar iot-system*.jar --spring.profiles.active=dev  >iot-system.log &
```
##### Deploy Backend Services
```
pnpm install
pnpm dev
```

## DeepAI Hub Cloud Platform [Open-source Edition]
<div>
  <img src=".image/banner/banner1001.png" alt="Image1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1002.png" alt="Image2" width="49%">
</div>
<div>
  <img src=".image/banner/banner1003.png" alt="Image3" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1004.png" alt="Image4" width="49%">
</div>
<div>
  <img src=".image/banner/banner1005.png" alt="Image5" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1006.png" alt="Image6" width="49%">
</div>

## Contact
### Email:
andywebjava@163.com (For project issues, please use GitHub Issues)
### WeChat (Join Knowledge Planet for technical exchange):
<p><img src=".image/联系方式.jpg" alt="Contact QR" width="30%"></p>

### Knowledge Planet:
Voluntary paid membership for technical consultation, resources, and WeChat group access:
<p><img src=".image/知识星球.jpg" alt="Knowledge Planet" width="30%"></p>

## Sponsorship
<div>
    <img src=".image/微信支付.jpg" alt="WeChat Pay" width="30%">
    <img src=".image/支付宝支付.jpg" alt="Alipay" width="30%">
</div>

## Acknowledgements
Thanks to the following contributors for code, feedback, donations, etc. (In random order):
- shup

## Open Source License
[MIT LICENSE](LICENSE)

## Copyright Notice
EasyAIoT open-source platform follows [MIT LICENSE](LICENSE). Commercial use is permitted provided original author and copyright information are retained.