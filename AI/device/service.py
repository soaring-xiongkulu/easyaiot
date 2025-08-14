import psycopg2
from psycopg2.extras import RealDictCursor

# 添加导入config模块
from config import DB_CONFIG

def get_db_connection():
    """
    获取数据库连接
    """
    try:
        connection = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        return connection
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def execute_query(query, params=None):
    """
    执行查询语句
    """
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        result = cursor.fetchall()
        return result
    except Exception as e:
        print(f"查询执行失败: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute_update(query, params=None):
    """
    执行更新语句
    """
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        print(f"更新执行失败: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()