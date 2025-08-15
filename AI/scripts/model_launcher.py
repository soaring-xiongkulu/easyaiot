import sys
import os
import importlib.util
import json
from flask import Flask, request, jsonify

# 获取传递的参数
model_id = sys.argv[1] if len(sys.argv) > 1 else "default_model"
model_path = sys.argv[2] if len(sys.argv) > 2 else "."
port = int(sys.argv[3]) if len(sys.argv) > 3 else 5000

app = Flask(__name__)

# 动态加载模型
model = None
def load_model():
    global model
    try:
        # 尝试加载常见的模型文件
        model_files = ['model.py', 'predict.py', 'inference.py']
        for model_file in model_files:
            model_file_path = os.path.join(model_path, model_file)
            if os.path.exists(model_file_path):
                spec = importlib.util.spec_from_file_location("model_module", model_file_path)
                model_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(model_module)
                if hasattr(model_module, 'predict'):
                    model = model_module
                    return True
        return False
    except Exception as e:
        print(f"Model loading error: {e}")
        return False

# 加载模型
load_model()

@app.route("/predict", methods=["POST"])
def predict():
    global model
    try:
        data = request.get_json()
        if model and hasattr(model, 'predict'):
            # 调用实际的预测函数
            result = model.predict(data)
            return jsonify({"model_id": model_id, "result": result, "status": "success"})
        else:
            return jsonify({"model_id": model_id, "error": "Model not found or prediction function not implemented", "status": "error"}), 404
    except Exception as e:
        return jsonify({"model_id": model_id, "error": str(e), "status": "error"}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

@app.route("/info", methods=["GET"])
def info():
    return jsonify({
        "model_id": model_id,
        "service_status": "running"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)