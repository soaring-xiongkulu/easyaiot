from flask import Flask
app = Flask(__name__)
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
    return {
        "status": "healthy",
        "service": "AI-module"
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)