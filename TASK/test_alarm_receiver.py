"""
测试告警回调接收服务器
模拟DEVICE后端接收TASK模块的告警回调
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# 记录收到的告警
alarm_history = []

@app.route('/api/alarm/callback/<int:task_id>', methods=['POST'])
def receive_alarm(task_id):
    """接收告警回调"""
    try:
        data = request.get_json()
        
        # 添加接收时间
        data['received_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        alarm_history.append(data)
        
        # 打印告警信息
        print("\n" + "="*60)
        print(f"📢 收到告警回调 - Task ID: {task_id}")
        print("="*60)
        print(f"时间戳: {data.get('timestamp', 'N/A')}")
        print(f"区域ID: {data.get('region_id', 'N/A')}")
        print(f"检测数量: {data.get('detection_count', 0)}")
        
        # 打印每个检测对象
        detections = data.get('detections', [])
        for i, det in enumerate(detections, 1):
            print(f"\n  [{i}] {det.get('class_name', 'Unknown')}")
            print(f"      置信度: {det.get('confidence', 0):.2%}")
            print(f"      位置: {det.get('bbox', [])}")
            print(f"      在报警区域内: {'是' if det.get('in_region') else '否'}")
        
        print("="*60 + "\n")
        
        # 返回成功响应
        return jsonify({
            "status": "success",
            "message": "Alarm received successfully",
            "task_id": task_id,
            "detection_count": len(detections)
        }), 200
        
    except Exception as e:
        print(f"❌ 接收告警失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/alarm/history', methods=['GET'])
def get_alarm_history():
    """查询告警历史"""
    return jsonify({
        "total": len(alarm_history),
        "alarms": alarm_history
    }), 200


@app.route('/api/alarm/clear', methods=['POST'])
def clear_alarm_history():
    """清空告警历史"""
    alarm_history.clear()
    return jsonify({
        "status": "success",
        "message": "Alarm history cleared"
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "TASK Alarm Receiver",
        "timestamp": datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 TASK告警接收测试服务器")
    print("="*60)
    print("监听地址: http://localhost:5000")
    print("回调接口: POST /api/alarm/callback/<task_id>")
    print("告警历史: GET  /api/alarm/history")
    print("清空历史: POST /api/alarm/clear")
    print("健康检查: GET  /health")
    print("="*60 + "\n")
    
    # 启动服务器
    app.run(host='0.0.0.0', port=5000, debug=True)

测试告警回调接收服务器
模拟DEVICE后端接收TASK模块的告警回调
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# 记录收到的告警
alarm_history = []

@app.route('/api/alarm/callback/<int:task_id>', methods=['POST'])
def receive_alarm(task_id):
    """接收告警回调"""
    try:
        data = request.get_json()
        
        # 添加接收时间
        data['received_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        alarm_history.append(data)
        
        # 打印告警信息
        print("\n" + "="*60)
        print(f"📢 收到告警回调 - Task ID: {task_id}")
        print("="*60)
        print(f"时间戳: {data.get('timestamp', 'N/A')}")
        print(f"区域ID: {data.get('region_id', 'N/A')}")
        print(f"检测数量: {data.get('detection_count', 0)}")
        
        # 打印每个检测对象
        detections = data.get('detections', [])
        for i, det in enumerate(detections, 1):
            print(f"\n  [{i}] {det.get('class_name', 'Unknown')}")
            print(f"      置信度: {det.get('confidence', 0):.2%}")
            print(f"      位置: {det.get('bbox', [])}")
            print(f"      在报警区域内: {'是' if det.get('in_region') else '否'}")
        
        print("="*60 + "\n")
        
        # 返回成功响应
        return jsonify({
            "status": "success",
            "message": "Alarm received successfully",
            "task_id": task_id,
            "detection_count": len(detections)
        }), 200
        
    except Exception as e:
        print(f"❌ 接收告警失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/alarm/history', methods=['GET'])
def get_alarm_history():
    """查询告警历史"""
    return jsonify({
        "total": len(alarm_history),
        "alarms": alarm_history
    }), 200


@app.route('/api/alarm/clear', methods=['POST'])
def clear_alarm_history():
    """清空告警历史"""
    alarm_history.clear()
    return jsonify({
        "status": "success",
        "message": "Alarm history cleared"
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "TASK Alarm Receiver",
        "timestamp": datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 TASK告警接收测试服务器")
    print("="*60)
    print("监听地址: http://localhost:5000")
    print("回调接口: POST /api/alarm/callback/<task_id>")
    print("告警历史: GET  /api/alarm/history")
    print("清空历史: POST /api/alarm/clear")
    print("健康检查: GET  /health")
    print("="*60 + "\n")
    
    # 启动服务器
    app.run(host='0.0.0.0', port=5000, debug=True)

 
测试告警回调接收服务器
模拟DEVICE后端接收TASK模块的告警回调
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# 记录收到的告警
alarm_history = []

@app.route('/api/alarm/callback/<int:task_id>', methods=['POST'])
def receive_alarm(task_id):
    """接收告警回调"""
    try:
        data = request.get_json()
        
        # 添加接收时间
        data['received_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        alarm_history.append(data)
        
        # 打印告警信息
        print("\n" + "="*60)
        print(f"📢 收到告警回调 - Task ID: {task_id}")
        print("="*60)
        print(f"时间戳: {data.get('timestamp', 'N/A')}")
        print(f"区域ID: {data.get('region_id', 'N/A')}")
        print(f"检测数量: {data.get('detection_count', 0)}")
        
        # 打印每个检测对象
        detections = data.get('detections', [])
        for i, det in enumerate(detections, 1):
            print(f"\n  [{i}] {det.get('class_name', 'Unknown')}")
            print(f"      置信度: {det.get('confidence', 0):.2%}")
            print(f"      位置: {det.get('bbox', [])}")
            print(f"      在报警区域内: {'是' if det.get('in_region') else '否'}")
        
        print("="*60 + "\n")
        
        # 返回成功响应
        return jsonify({
            "status": "success",
            "message": "Alarm received successfully",
            "task_id": task_id,
            "detection_count": len(detections)
        }), 200
        
    except Exception as e:
        print(f"❌ 接收告警失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/alarm/history', methods=['GET'])
def get_alarm_history():
    """查询告警历史"""
    return jsonify({
        "total": len(alarm_history),
        "alarms": alarm_history
    }), 200


@app.route('/api/alarm/clear', methods=['POST'])
def clear_alarm_history():
    """清空告警历史"""
    alarm_history.clear()
    return jsonify({
        "status": "success",
        "message": "Alarm history cleared"
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "TASK Alarm Receiver",
        "timestamp": datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 TASK告警接收测试服务器")
    print("="*60)
    print("监听地址: http://localhost:5000")
    print("回调接口: POST /api/alarm/callback/<task_id>")
    print("告警历史: GET  /api/alarm/history")
    print("清空历史: POST /api/alarm/clear")
    print("健康检查: GET  /health")
    print("="*60 + "\n")
    
    # 启动服务器
    app.run(host='0.0.0.0', port=5000, debug=True)

测试告警回调接收服务器
模拟DEVICE后端接收TASK模块的告警回调
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# 记录收到的告警
alarm_history = []

@app.route('/api/alarm/callback/<int:task_id>', methods=['POST'])
def receive_alarm(task_id):
    """接收告警回调"""
    try:
        data = request.get_json()
        
        # 添加接收时间
        data['received_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        alarm_history.append(data)
        
        # 打印告警信息
        print("\n" + "="*60)
        print(f"📢 收到告警回调 - Task ID: {task_id}")
        print("="*60)
        print(f"时间戳: {data.get('timestamp', 'N/A')}")
        print(f"区域ID: {data.get('region_id', 'N/A')}")
        print(f"检测数量: {data.get('detection_count', 0)}")
        
        # 打印每个检测对象
        detections = data.get('detections', [])
        for i, det in enumerate(detections, 1):
            print(f"\n  [{i}] {det.get('class_name', 'Unknown')}")
            print(f"      置信度: {det.get('confidence', 0):.2%}")
            print(f"      位置: {det.get('bbox', [])}")
            print(f"      在报警区域内: {'是' if det.get('in_region') else '否'}")
        
        print("="*60 + "\n")
        
        # 返回成功响应
        return jsonify({
            "status": "success",
            "message": "Alarm received successfully",
            "task_id": task_id,
            "detection_count": len(detections)
        }), 200
        
    except Exception as e:
        print(f"❌ 接收告警失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/alarm/history', methods=['GET'])
def get_alarm_history():
    """查询告警历史"""
    return jsonify({
        "total": len(alarm_history),
        "alarms": alarm_history
    }), 200


@app.route('/api/alarm/clear', methods=['POST'])
def clear_alarm_history():
    """清空告警历史"""
    alarm_history.clear()
    return jsonify({
        "status": "success",
        "message": "Alarm history cleared"
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "TASK Alarm Receiver",
        "timestamp": datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 TASK告警接收测试服务器")
    print("="*60)
    print("监听地址: http://localhost:5000")
    print("回调接口: POST /api/alarm/callback/<task_id>")
    print("告警历史: GET  /api/alarm/history")
    print("清空历史: POST /api/alarm/clear")
    print("健康检查: GET  /health")
    print("="*60 + "\n")
    
    # 启动服务器
    app.run(host='0.0.0.0', port=5000, debug=True)

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 