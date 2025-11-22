"""
测试脚本 - 用于快速测试模型服务是否能正常启动
使用默认参数，加载本地的 yolo11n.pt 模型

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 全局变量
model = None
model_loaded = False
model_path = None


def load_model(model_path):
    """加载模型"""
    global model, model_loaded
    
    try:
        logger.info(f"开始加载模型: {model_path}")
        
        # 检查模型文件是否存在
        if not os.path.exists(model_path):
            logger.error(f"模型文件不存在: {model_path}")
            return False
        
        # 加载YOLO模型
        try:
            from ultralytics import YOLO
            model = YOLO(model_path)
            logger.info("✅ YOLO模型加载成功")
            model_loaded = True
            return True
        except ImportError:
            logger.error("❌ 未安装ultralytics库，请运行: pip install ultralytics")
            return False
        except Exception as e:
            logger.error(f"❌ YOLO模型加载失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        logger.error(f"❌ 加载模型失败: {str(e)}")
        import traceback
        traceback.print_exc()
        model_loaded = False
        return False


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model_loaded,
        'model_path': model_path
    })


@app.route('/inference', methods=['POST'])
def inference():
    """推理接口（测试用）"""
    global model, model_loaded
    
    if not model_loaded or model is None:
        return jsonify({
            'code': 500,
            'msg': '模型未加载'
        }), 500
    
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'msg': '未找到文件，请使用POST请求上传图片文件'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'code': 400,
                'msg': '未选择文件'
            }), 400
        
        # 获取推理参数（使用默认值）
        conf_thres = float(request.form.get('conf_thres', 0.25))
        iou_thres = float(request.form.get('iou_thres', 0.45))
        
        # 保存临时文件
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        file.save(temp_file.name)
        temp_file.close()
        
        try:
            # 执行推理
            logger.info(f"开始推理: {file.filename}, conf={conf_thres}, iou={iou_thres}")
            results = model.predict(
                temp_file.name,
                conf=conf_thres,
                iou=iou_thres,
                verbose=False
            )
            
            # 处理结果
            predictions = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    predictions.append({
                        'class': int(box.cls.item()),
                        'class_name': result.names[int(box.cls.item())],
                        'confidence': float(box.conf.item()),
                        'bbox': box.xyxy.tolist()[0]
                    })
            
            # 保存结果图片
            result_path = temp_file.name.replace(os.path.splitext(temp_file.name)[1], '_result.jpg')
            results[0].save(filename=result_path)
            
            logger.info(f"推理成功，检测到 {len(predictions)} 个目标")
            
            return jsonify({
                'code': 0,
                'msg': '推理成功',
                'data': {
                    'predictions': predictions,
                    'result_image_path': result_path,
                    'count': len(predictions)
                }
            })
                
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            except:
                pass
                
    except Exception as e:
        logger.error(f"推理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'msg': f'推理失败: {str(e)}'
        }), 500


@app.route('/test', methods=['GET'])
def test():
    """简单的测试接口"""
    return jsonify({
        'code': 0,
        'msg': '服务运行正常',
        'model_loaded': model_loaded,
        'model_path': model_path
    })


def main():
    """主函数"""
    global model_path
    
    # 获取模型路径（默认使用当前目录下的yolo11n.pt）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, 'yolo11n.pt')
    
    logger.info("=" * 60)
    logger.info("🚀 开始测试模型服务")
    logger.info("=" * 60)
    logger.info(f"📁 脚本目录: {script_dir}")
    logger.info(f"📦 模型路径: {model_path}")
    
    # 检查模型文件是否存在
    if not os.path.exists(model_path):
        logger.error(f"❌ 模型文件不存在: {model_path}")
        logger.error("💡 请确保 yolo11n.pt 文件位于 services 目录下")
        sys.exit(1)
    
    # 加载模型
    logger.info("📥 正在加载模型...")
    if not load_model(model_path):
        logger.error("❌ 模型加载失败，退出")
        sys.exit(1)
    
    # 启动Flask服务
    host = '0.0.0.0'
    port = 8888  # 使用8888端口避免与主服务冲突
    
    logger.info("=" * 60)
    logger.info(f"✅ 模型服务启动成功")
    logger.info(f"🌐 服务地址: http://localhost:{port}")
    logger.info(f"📊 健康检查: http://localhost:{port}/health")
    logger.info(f"🧪 测试接口: http://localhost:{port}/test")
    logger.info(f"🔮 推理接口: http://localhost:{port}/inference")
    logger.info("=" * 60)
    logger.info("💡 使用示例:")
    logger.info(f"   curl -X GET http://localhost:{port}/test")
    logger.info(f"   curl -X POST -F 'file=@your_image.jpg' http://localhost:{port}/inference")
    logger.info("=" * 60)
    
    try:
        app.run(host=host, port=port, threaded=True, debug=False)
    except KeyboardInterrupt:
        logger.info("\n收到中断信号，正在关闭服务...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

