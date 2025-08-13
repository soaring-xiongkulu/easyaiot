from flask import Flask
from train.routes import train_bp
from export.routes import export_bp
import os

def create_app():
    app = Flask(__name__)
    
    # 注册蓝图
    app.register_blueprint(train_bp, url_prefix='/train')
    app.register_blueprint(export_bp, url_prefix='/export')
    
    @app.route('/')
    def index():
        return {
            "message": "YOLOv8 Training and Export Service",
            "endpoints": {
                "train": "/train",
                "export": "/export"
            }
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)