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
predict_function = None

def load_model():
    global model, predict_function
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
                    predict_function = getattr(model_module, 'predict')
                    print(f"Model loaded successfully from {model_file}")
                    return True
        # 如果在常见文件中找不到，尝试直接加载.pt文件（YOLO模型）
        import glob
        pt_files = glob.glob(os.path.join(model_path, "*.pt"))
        if pt_files:
            from ultralytics import YOLO
            model = YOLO(pt_files[0])
            # 创建一个predict函数
            def yolo_predict(data):
                # 根据YOLO模型的要求处理输入数据
                if isinstance(data, dict) and 'image' in data:
                    results = model(data['image'])
                else:
                    results = model(data)
                # 处理结果，确保返回可JSON序列化的数据
                if hasattr(results, '__iter__'):
                    return [r.tojson() if hasattr(r, 'tojson') else str(r) for r in results]
                else:
                    return results.tojson() if hasattr(results, 'tojson') else str(results)
            predict_function = yolo_predict
            print(f"YOLO Model loaded successfully from {pt_files[0]}")
            return True
            
        # 尝试加载ONNX模型
        onnx_files = glob.glob(os.path.join(model_path, "*.onnx"))
        if onnx_files:
            # 加载ONNX模型
            import onnxruntime as ort
            model = ort.InferenceSession(onnx_files[0])
            
            # 创建一个predict函数
            def onnx_predict(data):
                # 处理ONNX模型推理
                if isinstance(data, dict):
                    # 如果输入是字典格式，提取输入数据
                    inputs = {}
                    for i, input_info in enumerate(model.get_inputs()):
                        input_name = input_info.name
                        if input_name in data:
                            inputs[input_name] = data[input_name]
                        elif f"input_{i}" in data:
                            inputs[input_name] = data[f"input_{i}"]
                        else:
                            # 如果没有匹配的输入名称，使用第一个输入
                            inputs[input_name] = list(data.values())[0] if data else None
                            break
                else:
                    # 如果输入不是字典，假设是单个输入
                    input_name = model.get_inputs()[0].name
                    inputs = {input_name: data}
                
                # 运行推理
                results = model.run(None, inputs)
                
                # 处理结果，确保返回可JSON序列化的数据
                if len(results) == 1:
                    result = results[0]
                    # 如果结果是numpy数组，转换为列表
                    if hasattr(result, 'tolist'):
                        return result.tolist()
                    else:
                        return result
                else:
                    processed_results = []
                    for r in results:
                        if hasattr(r, 'tolist'):
                            processed_results.append(r.tolist())
                        else:
                            processed_results.append(r)
                    return processed_results
                    
            predict_function = onnx_predict
            print(f"ONNX Model loaded successfully from {onnx_files[0]}")
            return True
            
        print("No suitable model file found")
        return False
    except Exception as e:
        print(f"Model loading error: {e}")
        return False

# 加载模型
if not load_model():
    print("Warning: Failed to load model. Service will start but prediction will not work.")

@app.route("/predict", methods=["POST"])
def predict():
    global model, predict_function
    try:
        data = request.get_json()
        if model and predict_function:
            # 调用实际的预测函数
            result = predict_function(data)
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
        "service_status": "running",
        "model_loaded": model is not None
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)