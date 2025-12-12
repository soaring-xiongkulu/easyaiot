#!/usr/bin/env python3
"""
删除DEVICE服务所有数据库表的脚本

使用方法:
    python drop_import_tables.py [--env=环境名] [--confirm]

参数:
    --env: 指定环境配置文件，例如: --env=prod 会加载 .env.prod，默认加载 .env
    --confirm: 跳过交互式确认，直接执行删除操作（谨慎使用）

示例:
    python drop_import_tables.py                    # 交互式确认
    python drop_import_tables.py --confirm          # 跳过确认直接执行
    python drop_import_tables.py --env=prod         # 使用指定环境配置并交互式确认

说明:
    - 如果不提供 --confirm 参数，脚本会显示将要删除的表列表，并交互式询问确认
    - 提供 --confirm 参数会跳过交互式确认，直接执行删除操作
    - 建议在非交互式环境中使用 --confirm 参数
    - 脚本会处理以下数据库：
      * ruoyi-vue-pro20
      * iot-device20
      * iot-message20
    - 脚本使用SQLAlchemy直接执行SQL，不需要psql命令

警告: 此操作会永久删除所有数据，无法恢复，请谨慎使用！
"""
import argparse
import os
import sys
import subprocess
import re
from urllib.parse import urlparse
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# 依赖检查和自动安装
def check_and_install_dependencies():
    """检查并自动安装必要的依赖包"""
    required_packages = {
        'dotenv': 'python-dotenv',
        'sqlalchemy': 'sqlalchemy',
        'psycopg2': 'psycopg2-binary'
    }
    
    missing_packages = []
    
    # 检查每个依赖
    for module_name, package_name in required_packages.items():
        try:
            if module_name == 'dotenv':
                __import__('dotenv')
            elif module_name == 'psycopg2':
                __import__('psycopg2')
            else:
                __import__(module_name)
        except ImportError:
            missing_packages.append((module_name, package_name))
    
    # 如果有缺失的包，尝试自动安装
    if missing_packages:
        package_names = [pkg for _, pkg in missing_packages]
        print(f"⚠️  检测到缺少以下依赖包: {', '.join(package_names)}")
        print("正在尝试自动安装...")
        
        try:
            # 使用清华镜像源加速安装
            pip_args = [
                sys.executable, '-m', 'pip', 'install',
                '--index-url', 'https://pypi.tuna.tsinghua.edu.cn/simple',
                '--quiet', '--upgrade'
            ] + package_names
            
            result = subprocess.run(
                pip_args,
                check=True,
                capture_output=True,
                text=True
            )
            
            print(f"✅ 成功安装依赖包: {', '.join(package_names)}")
            print("正在重新加载模块...")
            
            # 重新导入模块（清除导入缓存）
            for module_name, _ in missing_packages:
                if module_name in sys.modules:
                    del sys.modules[module_name]
        
        except subprocess.CalledProcessError as e:
            print(f"❌ 自动安装失败")
            if e.stderr:
                print(f"错误信息: {e.stderr}")
            print(f"\n💡 请手动安装依赖包:")
            print(f"   pip install {' '.join(package_names)}")
            print(f"\n   或使用清华镜像源:")
            print(f"   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple {' '.join(package_names)}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 安装过程中发生错误: {str(e)}")
            print(f"\n💡 请手动安装依赖包:")
            print(f"   pip install {' '.join(package_names)}")
            sys.exit(1)

# 在导入之前检查和安装依赖
check_and_install_dependencies()

# 现在可以安全导入
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# 要处理的数据库列表
DATABASES = [
    "ruoyi-vue-pro20",
    "iot-device20",
    "iot-message20"
]

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='删除DEVICE服务所有数据库表')
    parser.add_argument('--env', type=str, default='', 
                       help='指定环境配置文件，例如: --env=prod 会加载 .env.prod，默认加载 .env')
    parser.add_argument('--confirm', action='store_true',
                       help='跳过交互式确认，直接执行删除操作（谨慎使用）')
    return parser.parse_args()

# 加载环境变量配置文件
def load_env_file(env_name=''):
    if env_name:
        env_file = f'.env.{env_name}'
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"✅ 已加载配置文件: {env_file}")
        else:
            print(f"⚠️  配置文件 {env_file} 不存在，尝试加载默认 .env 文件")
            if os.path.exists('.env'):
                load_dotenv('.env')
                print(f"✅ 已加载默认配置文件: .env")
            else:
                print(f"❌ 默认配置文件 .env 也不存在")
                sys.exit(1)
    else:
        if os.path.exists('.env'):
            load_dotenv('.env')
            print(f"✅ 已加载默认配置文件: .env")
        else:
            print(f"⚠️  默认配置文件 .env 不存在，尝试使用环境变量")

# 获取所有表名
def get_all_tables(engine):
    """获取数据库中所有表名"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return tables

# 交互式确认
def interactive_confirm_all_databases(db_tables_map):
    """交互式确认删除操作"""
    print(f"\n⚠️  警告: 即将处理以下 {len(db_tables_map)} 个数据库:")
    total_tables = 0
    for db_name, tables in db_tables_map.items():
        table_count = len(tables)
        total_tables += table_count
        print(f"   - {db_name}: {table_count} 个表")
        if table_count > 0 and table_count <= 10:
            for i, table in enumerate(tables, 1):
                print(f"     {i}. {table}")
        elif table_count > 10:
            for i, table in enumerate(tables[:5], 1):
                print(f"     {i}. {table}")
            print(f"     ... 还有 {table_count - 5} 个表")
    
    print(f"\n总计: {total_tables} 个表将被删除")
    print("\n⚠️  此操作会永久删除所有数据，无法恢复！")
    print("\n请确认是否继续删除操作？")
    
    while True:
        try:
            response = input("输入 'yes' 或 'y' 确认执行，输入 'no' 或 'n' 取消: ").strip().lower()
            if response in ['yes', 'y']:
                return True
            elif response in ['no', 'n']:
                print("❌ 操作已取消")
                return False
            else:
                print("⚠️  请输入 'yes'/'y' 或 'no'/'n'")
        except KeyboardInterrupt:
            print("\n\n❌ 操作已取消（用户中断）")
            return False
        except EOFError:
            print("\n\n❌ 操作已取消（输入结束）")
            return False

# 删除所有表
def drop_all_tables(engine, db_name):
    """删除指定数据库中的所有表"""
    try:
        # 获取所有表名
        tables = get_all_tables(engine)
        
        if not tables:
            print(f"ℹ️  数据库 '{db_name}' 中没有表需要删除")
            return True
        
        print(f"\n正在删除数据库 '{db_name}' 中的 {len(tables)} 个表...\n")
        
        # 使用事务执行删除
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            try:
                # 禁用外键约束检查（PostgreSQL）
                conn.execute(text("SET session_replication_role = 'replica';"))
                
                # 删除所有表（使用CASCADE确保删除依赖关系）
                for table in tables:
                    try:
                        conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE;'))
                        print(f"✅ 已删除表: {table}")
                    except Exception as e:
                        print(f"⚠️  删除表 {table} 时出错: {str(e)}")
                
                # 重新启用外键约束检查
                conn.execute(text("SET session_replication_role = 'origin';"))
                
                # 提交事务
                trans.commit()
                print(f"\n✅ 成功删除数据库 '{db_name}' 中的所有表！")
                return True
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"\n❌ 删除表时发生错误: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"❌ 连接数据库时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# 从DATABASE_URL解析连接信息
def parse_database_url(database_url):
    """从DATABASE_URL解析数据库连接信息"""
    # 转换postgres://为postgresql://
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # 强制使用localhost作为数据库主机
    database_url = re.sub(r'@[^:/]+', '@localhost', database_url)
    
    parsed = urlparse(database_url)
    
    return {
        'user': parsed.username or 'postgres',
        'password': parsed.password or '',
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/') if parsed.path else 'postgres'
    }

# 检查数据库是否存在
def check_database_exists(db_info, db_name):
    """检查数据库是否存在"""
    try:
        # 连接到postgres数据库检查
        db_url_for_check = f"postgresql://{db_info['user']}:{db_info['password']}@{db_info['host']}:{db_info['port']}/postgres"
        engine = create_engine(db_url_for_check, pool_pre_ping=True)
        
        with engine.connect() as conn:
            result = conn.execute(text(
                f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"
            ))
            exists = result.fetchone() is not None
        engine.dispose()
        return exists
    except Exception as e:
        print(f"⚠️  检查数据库 '{db_name}' 是否存在时出错: {str(e)}")
        return False

# 解析SQL文件为语句列表
def parse_sql_file(sql_file_path):
    """解析SQL文件，返回SQL语句列表"""
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除注释和空行
        lines = content.split('\n')
        cleaned_lines = []
        in_multiline_comment = False
        
        for line in lines:
            # 处理多行注释 /* ... */
            if '/*' in line:
                in_multiline_comment = True
                line = line[:line.index('/*')]
            if '*/' in line:
                in_multiline_comment = False
                line = line[line.index('*/') + 2:]
            
            if in_multiline_comment:
                continue
            
            # 移除单行注释 --
            if '--' in line:
                line = line[:line.index('--')]
            
            # 移除psql元命令
            if line.strip().startswith('\\'):
                continue
            
            cleaned_lines.append(line)
        
        # 合并为完整内容并分割SQL语句
        full_content = '\n'.join(cleaned_lines)
        
        # 按分号分割SQL语句（但要注意字符串中的分号）
        statements = []
        current = []
        in_string = False
        string_char = None
        
        for char in full_content:
            current.append(char)
            
            if char in ("'", '"') and (len(current) == 1 or current[-2] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
            
            if not in_string and char == ';':
                stmt = ''.join(current).strip()
                if stmt and not re.match(r'^\s*(DROP\s+DATABASE|CREATE\s+DATABASE)', stmt, re.IGNORECASE):
                    statements.append(stmt)
                current = []
        
        # 处理最后一个语句（如果没有分号结尾）
        if current:
            stmt = ''.join(current).strip()
            if stmt and not re.match(r'^\s*(DROP\s+DATABASE|CREATE\s+DATABASE)', stmt, re.IGNORECASE):
                statements.append(stmt)
        
        return [s for s in statements if s]
        
    except Exception as e:
        print(f"⚠️  解析SQL文件时出错: {str(e)}")
        return []

# 导入SQL文件
def import_sql_file(engine, sql_file_path, target_database):
    """使用SQLAlchemy直接执行SQL文件"""
    if not os.path.exists(sql_file_path):
        print(f"⚠️  SQL文件不存在: {sql_file_path}")
        print(f"💡 将跳过导入步骤，仅删除表")
        return False
    
    print(f"\n正在导入SQL文件: {sql_file_path}")
    print(f"目标数据库: {target_database}\n")
    
    # 解析SQL文件
    statements = parse_sql_file(sql_file_path)
    
    if not statements:
        print("⚠️  SQL文件中没有有效的SQL语句")
        return False
    
    print(f"📝 找到 {len(statements)} 条SQL语句，开始执行...\n")
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                executed_count = 0
                error_count = 0
                
                for i, statement in enumerate(statements, 1):
                    try:
                        # 跳过空语句
                        if not statement.strip():
                            continue
                        
                        # 执行SQL语句
                        conn.execute(text(statement))
                        executed_count += 1
                        
                        # 每100条语句显示一次进度
                        if executed_count % 100 == 0:
                            print(f"   已执行 {executed_count}/{len(statements)} 条语句...")
                        
                    except Exception as e:
                        error_count += 1
                        # 只显示前10个错误，避免输出过多
                        if error_count <= 10:
                            error_msg = str(e).split('\n')[0]  # 只取第一行错误信息
                            print(f"⚠️  执行第 {i} 条语句时出错: {error_msg}")
                        elif error_count == 11:
                            print(f"⚠️  ... 还有更多错误，将不再显示")
                
                # 提交事务
                trans.commit()
                
                print(f"\n✅ SQL文件导入完成！")
                print(f"   成功执行: {executed_count} 条语句")
                if error_count > 0:
                    print(f"   执行失败: {error_count} 条语句")
                    return False
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"\n❌ 导入SQL文件时发生错误: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"❌ 连接数据库执行SQL时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # 解析命令行参数
    args = parse_args()
    
    # 加载环境变量
    load_env_file(args.env)
    
    # 获取数据库URL（优先从环境变量，如果没有则尝试从其他环境变量构建）
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        # 尝试从单独的环境变量构建
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '5432')
        db_user = os.environ.get('DB_USER', 'postgres')
        db_password = os.environ.get('DB_PASSWORD', 'iot45722414822')
        
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/postgres"
        print(f"⚠️  DATABASE_URL环境变量未设置，使用单独的环境变量构建连接")
    
    # 转换postgres://为postgresql://（SQLAlchemy要求）
    database_url_for_sqlalchemy = database_url.replace("postgres://", "postgresql://", 1)
    
    # 强制使用localhost作为数据库主机
    database_url_for_sqlalchemy = re.sub(r'@[^:/]+', '@localhost', database_url_for_sqlalchemy)
    
    # 解析数据库连接信息
    db_info = parse_database_url(database_url)
    
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print(f"\n📊 数据库连接信息:")
    # 隐藏密码显示
    safe_url = database_url_for_sqlalchemy.split('@')[1] if '@' in database_url_for_sqlalchemy else database_url_for_sqlalchemy
    print(f"   数据库: {safe_url}")
    print(f"   将处理的数据库:")
    for db_name in DATABASES:
        print(f"     - {db_name}")
    print()
    
    # 收集所有数据库的表信息（用于确认）
    db_tables_map = {}
    engines = {}
    
    for db_name in DATABASES:
        # 检查数据库是否存在
        if not check_database_exists(db_info, db_name):
            print(f"⚠️  数据库 '{db_name}' 不存在，将跳过")
            continue
        
        # 创建数据库引擎
        try:
            db_url_for_db = re.sub(r'/([^/]+)(\?|$)', f'/{db_name}\\2', database_url_for_sqlalchemy)
            engine = create_engine(db_url_for_db, pool_pre_ping=True)
            
            # 测试连接
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # 获取表列表
            tables = get_all_tables(engine)
            db_tables_map[db_name] = tables
            engines[db_name] = engine
            
        except Exception as e:
            print(f"⚠️  连接数据库 '{db_name}' 失败: {str(e)}")
            continue
    
    if not engines:
        print("❌ 没有可用的数据库连接")
        sys.exit(1)
    
    print("✅ 数据库连接成功\n")
    
    # 如果没有通过命令行确认，则进行交互式确认
    if not args.confirm:
        if not interactive_confirm_all_databases(db_tables_map):
            sys.exit(0)
    
    # 处理每个数据库
    success_count = 0
    total_count = len(engines)
    
    for db_name, engine in engines.items():
        print(f"\n{'='*50}")
        print(f"处理数据库: {db_name}")
        print(f"{'='*50}")
        
        # 删除所有表
        drop_success = drop_all_tables(engine, db_name)
        if drop_success:
            success_count += 1
        else:
            print(f"❌ 删除数据库 '{db_name}' 的表失败")
        
        # 关闭引擎连接
        engine.dispose()
    
    print(f"\n{'='*50}")
    if success_count == total_count:
        print(f"✅ 所有操作完成！成功处理 {success_count}/{total_count} 个数据库")
        sys.exit(0)
    else:
        print(f"⚠️  部分操作完成：成功 {success_count}/{total_count} 个数据库")
        sys.exit(1)

if __name__ == '__main__':
    main()

