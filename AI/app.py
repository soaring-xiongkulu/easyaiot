import json

from flask import Flask
from train.routes import train_bp
from export.routes import export_bp
from model.routes import model_bp
app = Flask(__name__)

app.register_blueprint(train_bp, url_prefix='/train')
app.register_blueprint(export_bp, url_prefix='/export')
app.register_blueprint(model_bp, url_prefix='/model')

@app.route('/')
def index_route():
    return "欢迎访问EasyAIoT平台"

# 健康检查端点，供Nacos进行健康检查
@app.route('/health', methods=['GET'])
def health():
    return health_check()

def health_check():
    """
    健康检查方法实现
    返回服务的健康状态
    """
    response = {
        "status": "healthy",
        "service": "AI-module"
    }
    return json.dumps(response, ensure_ascii=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
