import json
from ..system import get_db_connection

def log_training_step_service(training_id, step, operation, details, status):
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
    
    return {"id": log_id, "message": "Training log recorded successfully"}

def get_training_logs_service(training_id, page, per_page, offset):
    conn = get_db_connection()
    cur = conn.cursor()
    
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
    
    return {
        "logs": logs_list,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total
        }
    }

def get_current_training_step_service(training_id):
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
        return current_step
    
    return None