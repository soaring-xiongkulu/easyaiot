# VIDEO模块部署文档

## 1. 环境要求

- Python 3.11+
- pip包管理工具
- 支持的数据库（如 PostgreSQL）
- 可选：Docker（用于容器化部署）

## 2. 安装依赖

在项目根目录下，使用以下命令安装所需的Python依赖包：

```bash
pip install -r AI/requirements.txt
```

### 依赖说明

- `Flask==2.3.2`: Web框架
- `Flask-SQLAlchemy==3.0.5`: 数据库ORM工具
- `ultralytics==8.0.113`: YOLOv8目标检测模型
- `opencv-python==4.8.0.74`: 图像处理库
- `Pillow==10.0.0`: Python图像处理库
- `python-dotenv==1.0.0`: 环境变量加载工具
- `PyYAML==6.0.1`: YAML文件解析库
- `requests==2.31.0`: HTTP请求库
- `psycopg2-binary==2.9.9`: PostgreSQL数据库适配器
- `nacos-sdk-python==2.0.9`: Nacos服务发现和配置管理SDK
- `minio==7.2.0`: MinIO对象存储客户端
- `python-magic==0.4.27`: 文件类型识别库
- `numpy==1.26.4`: 数值计算库

## 3. 环境配置

创建 `.env` 文件并配置以下环境变量：

```env
# Flask配置
FLASK_APP=app.py
FLASK_ENV=production

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/dbname

# Nacos配置
NACOS_SERVER=localhost:8848
NACOS_NAMESPACE=your_namespace

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
```


## 4. 启动应用

### 直接运行

```bash
cd AI
flask run --host=0.0.0.0 --port=5000
```


### 使用Gunicorn部署（推荐生产环境）

首先安装Gunicorn：

```bash
pip install gunicorn
```


然后启动应用：

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```


### Docker部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY AI/requirements.txt .
RUN pip install -r requirements.txt

COPY VIDEO/ .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```


构建并运行容器：

```bash
docker build -t video-module .
docker run -p 5000:5000 ai-module
```


## 5. 服务验证

启动后，可以通过以下方式验证服务是否正常运行：

```bash
curl http://localhost:5000/health
```

如果返回健康状态，则表示服务已成功启动。
