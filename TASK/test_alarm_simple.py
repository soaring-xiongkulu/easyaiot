#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的告警接收服务器 - 用于测试TASK模块的告警回调功能
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/api/alarm/callback/<task_id>', methods=['POST'])
def receive_alarm(task_id):
    """接收告警回调"""
    try:
        data = request.get_json()
        
        print("\n" + "="*80)
        print(f"🚨 收到告警回调 - TaskID: {task_id}")
        print("="*80)
        print(f"时间戳: {data.get('timestamp')}")
        print(f"告警类型: {data.get('alarmType')}")
        print(f"区域名称: {data.get('regionName')}")
        print(f"\n检测结果:")
        
        for idx, det in enumerate(data.get('detections', []), 1):
            class_name = det.get('class_name', 'unknown')
            confidence = det.get('confidence', 0)
            centerX = det.get('centerX', 0)
            centerY = det.get('centerY', 0)
            bbox = det.get('bbox', [])
            
            print(f"  [{idx}] {class_name} - 置信度: {confidence:.2f}")
            print(f"      位置: ({centerX}, {centerY})")
            print(f"      边界框: {bbox}")
        
        print("="*80 + "\n")
        
        return jsonify({
            "code": 200,
            "message": "告警接收成功",
            "taskId": task_id
        }), 200
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return jsonify({
            "code": 500,
            "message": f"Error: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("\n🎯 告警接收服务器启动中...")
    print("📡 监听地址: http://localhost:5000")
    print("📥 接收端点: /api/alarm/callback/{task_id}\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
