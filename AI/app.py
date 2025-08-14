from flask import Flask, request, jsonify
import psycopg2
import os
from minio import Minio
from minio.error import S3Error

app = Flask(__name__)

# Minio配置
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'http://iot.basiclab.top:9000')
MINIO_USER = os.environ.get('MINIO_USER', 'minio_root')
MINIO_PASSWORD = os.environ.get('MINIO_PASSWORD', 'minio_123456')

# 初始化Minio客户端
minio_client = Minio(
    MINIO_ENDPOINT.replace('http://', '').replace('https://', ''),
    access_key=MINIO_USER,
    secret_key=MINIO_PASSWORD,
    secure=MINIO_ENDPOINT.startswith('https://')
)

# 数据库配置
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'aiot_db')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

@app.route('/')
def index():
    return jsonify({"message": "AI Service is running", "service": "ai-service"})

@app.route('/api/devices', methods=['GET'])
def get_devices():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, device_id, name, description, status FROM devices;')
        devices = cur.fetchall()
        cur.close()
        conn.close()
        
        devices_list = []
        for device in devices:
            devices_list.append({
                'id': device[0],
                'device_id': device[1],
                'name': device[2],
                'description': device[3],
                'status': device[4]
            })
        
        return jsonify(devices_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices', methods=['POST'])
def create_device():
    try:
        data = request.get_json()
        device_id = data['device_id']
        name = data['name']
        description = data.get('description', '')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO devices (device_id, name, description) VALUES (%s, %s, %s) RETURNING id;',
            (device_id, name, description)
        )
        device_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"id": device_id, "message": "Device created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 健康检查端点，供Nacos进行健康检查
@app.route('/health', methods=['GET'])
def health_check():
    try:
        # 检查数据库连接
        conn = get_db_connection()
        conn.close()
        
        # 检查Minio连接
        minio_client.bucket_exists('healthcheck')
        
        return jsonify({"status": "UP"}), 200
    except Exception as e:
        return jsonify({"status": "DOWN", "error": str(e)}), 500

# 记录训练步骤日志
@app.route('/api/training/log', methods=['POST'])
def log_training_step():
    try:
        data = request.get_json()
        training_id = data['training_id']
        step = data['step']
        operation = data['operation']
        details = data.get('details', {})
        status = data.get('status', 'running')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO training_logs (training_id, step, operation, details, status) VALUES (%s, %s, %s, %s, %s) RETURNING id;',
            (training_id, step, operation, json.dumps(details), status)
        )
        log_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"id": log_id, "message": "Training log recorded successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 查询训练日志
@app.route('/api/training/<training_id>/logs', methods=['GET'])
def get_training_logs(training_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        
        # 查询总数
        cur.execute('SELECT COUNT(*) FROM training_logs WHERE training_id = %s;', (training_id,))
        total = cur.fetchone()[0]
        
        # 查询日志记录
        cur.execute('''SELECT id, training_id, step, operation, details, status, created_at, updated_at 
                      FROM training_logs 
                      WHERE training_id = %s 
                      ORDER BY step ASC, created_at ASC 
                      LIMIT %s OFFSET %s;''', (training_id, per_page, offset))
        logs = cur.fetchall()
        cur.close()
        conn.close()
        
        logs_list = []
        for log in logs:
            logs_list.append({
                'id': log[0],
                'training_id': log[1],
                'step': log[2],
                'operation': log[3],
                'details': log[4],
                'status': log[5],
                'created_at': log[6].isoformat() if log[6] else None,
                'updated_at': log[7].isoformat() if log[7] else None
            })
        
        return jsonify({
            "logs": logs_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取训练当前步骤
@app.route('/api/training/<training_id>/current', methods=['GET'])
def get_current_training_step(training_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''SELECT step, operation, details, status, created_at 
                      FROM training_logs 
                      WHERE training_id = %s 
                      ORDER BY step DESC, created_at DESC 
                      LIMIT 1;''', (training_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            current_step = {
                'step': result[0],
                'operation': result[1],
                'details': result[2],
                'status': result[3],
                'timestamp': result[4].isoformat() if result[4] else None
            }
            return jsonify(current_step), 200
        else:
            return jsonify({"message": "No training logs found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)