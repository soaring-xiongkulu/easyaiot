#!/usr/bin/env python3
"""
导入DEVICE服务数据库表结构的脚本

使用方法:
    python import_tables.py [--env=环境名] [--confirm]

参数:
    --env: 指定环境配置文件，例如: --env=prod 会加载 .env.prod，默认加载 .env
    --confirm: 跳过交互式确认，直接执行导入操作（谨慎使用）

示例:
    python import_tables.py                    # 交互式确认
    python import_tables.py --confirm          # 跳过确认直接执行
    python import_tables.py --env=prod         # 使用指定环境配置并交互式确认

说明:
    - 如果不提供 --confirm 参数，脚本会显示将要导入的SQL文件列表，并交互式询问确认
    - 提供 --confirm 参数会跳过交互式确认，直接执行导入操作
    - 建议在非交互式环境中使用 --confirm 参数
    - 脚本会处理以下数据库：
      * ruoyi-vue-pro20 -> ruoyi-vue-pro10.sql
      * iot-device20 -> iot-device10.sql
      * iot-message20 -> iot-message10.sql
    - SQL文件路径: 项目根目录/.scripts/postgresql/
    - 脚本使用psql命令导入SQL文件，需要PostgreSQL客户端工具

警告: 此操作会导入表结构，如果表已存在可能会报错！
"""
import argparse
import os
import sys
import subprocess
import re
from urllib.parse import urlparse
from dotenv import load_dotenv

# 依赖检查和自动安装
def check_and_install_dependencies():
    """检查并自动安装必要的依赖包"""
    required_packages = {
        'dotenv': 'python-dotenv'
    }
    
    missing_packages = []
    
    # 检查每个依赖
    for module_name, package_name in required_packages.items():
        try:
            if module_name == 'dotenv':
                __import__('dotenv')
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

# 数据库和SQL文件映射
DB_SQL_MAP = {
    "ruoyi-vue-pro20": "ruoyi-vue-pro10.sql",
    "iot-device20": "iot-device10.sql",
    "iot-message20": "iot-message10.sql"
}

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='导入DEVICE服务数据库表结构')
    parser.add_argument('--env', type=str, default='', 
                       help='指定环境配置文件，例如: --env=prod 会加载 .env.prod，默认加载 .env')
    parser.add_argument('--confirm', action='store_true',
                       help='跳过交互式确认，直接执行导入操作（谨慎使用）')
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
        # 使用PGPASSWORD环境变量传递密码
        env = os.environ.copy()
        if db_info['password']:
            env['PGPASSWORD'] = db_info['password']
        
        # 使用psql检查数据库是否存在
        psql_cmd = [
            'psql',
            '-h', db_info['host'],
            '-p', str(db_info['port']),
            '-U', db_info['user'],
            '-d', 'postgres',
            '-tc', f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"
        ]
        
        result = subprocess.run(
            psql_cmd,
            env=env,
            capture_output=True,
            text=True,
            check=False
        )
        
        return result.returncode == 0 and result.stdout.strip() == '1'
    except FileNotFoundError:
        print(f"⚠️  未找到psql命令，无法检查数据库 '{db_name}' 是否存在")
        return False
    except Exception as e:
        print(f"⚠️  检查数据库 '{db_name}' 是否存在时出错: {str(e)}")
        return False

# 检查psql命令是否可用
def check_psql_available():
    """检查psql命令是否可用"""
    try:
        result = subprocess.run(
            ['psql', '--version'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, None
    except FileNotFoundError:
        return False, None

# 交互式确认
def interactive_confirm(sql_files_map):
    """交互式确认导入操作"""
    print(f"\n⚠️  警告: 即将导入以下 {len(sql_files_map)} 个数据库的SQL文件:")
    for db_name, sql_file_path in sql_files_map.items():
        exists_mark = "✓" if os.path.exists(sql_file_path) else "✗ (不存在)"
        print(f"   {exists_mark} {db_name} -> {os.path.basename(sql_file_path)}")
    
    print("\n⚠️  此操作会导入表结构，如果表已存在可能会报错！")
    print("\n请确认是否继续导入操作？")
    
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

# 导入SQL文件
def import_sql_file(db_info, sql_file_path, target_database):
    """使用psql命令导入SQL文件"""
    if not os.path.exists(sql_file_path):
        print(f"❌ SQL文件不存在: {sql_file_path}")
        return False
    
    print(f"\n正在导入SQL文件: {sql_file_path}")
    print(f"目标数据库: {target_database}\n")
    
    # 构建psql命令
    # 使用PGPASSWORD环境变量传递密码，避免在命令行中暴露
    env = os.environ.copy()
    if db_info['password']:
        env['PGPASSWORD'] = db_info['password']
    
    # 构建psql连接字符串
    # 格式: psql -h host -p port -U user -d database -f sql_file
    psql_cmd = [
        'psql',
        '-h', db_info['host'],
        '-p', str(db_info['port']),
        '-U', db_info['user'],
        '-d', target_database,
        '-f', sql_file_path,
        '-q'  # 安静模式，只显示错误
    ]
    
    try:
        result = subprocess.run(
            psql_cmd,
            env=env,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print("✅ SQL文件导入成功！")
            return True
        else:
            # 检查是否只是警告（某些SQL文件可能包含警告但实际执行成功）
            error_output = result.stderr
            if error_output:
                # 过滤掉常见的非致命错误
                lines = error_output.split('\n')
                fatal_errors = [line for line in lines 
                              if line and 'ERROR' in line.upper() 
                              and 'already exists' not in line.lower()
                              and 'does not exist' not in line.lower()]
                
                if fatal_errors:
                    print(f"⚠️  SQL文件导入时出现错误:")
                    for error in fatal_errors[:10]:  # 显示前10个错误
                        print(f"   {error}")
                    return False
                else:
                    print("✅ SQL文件导入完成（可能有警告，但已忽略）")
                    return True
            else:
                print("✅ SQL文件导入成功！")
                return True
                
    except FileNotFoundError:
        print("❌ 错误: 未找到psql命令")
        print("💡 请确保已安装PostgreSQL客户端工具")
        print("   安装方法:")
        print("     Ubuntu/Debian: sudo apt-get install postgresql-client")
        print("     CentOS/RHEL:   sudo yum install postgresql")
        return False
    except Exception as e:
        print(f"❌ 导入SQL文件时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # 解析命令行参数
    args = parse_args()
    
    # 加载环境变量
    load_env_file(args.env)
    
    # 检查psql是否可用
    psql_available, psql_version = check_psql_available()
    if not psql_available:
        print("❌ 错误: 未找到psql命令")
        print("💡 请确保已安装PostgreSQL客户端工具")
        print("   安装方法:")
        print("     Ubuntu/Debian: sudo apt-get install postgresql-client")
        print("     CentOS/RHEL:   sudo yum install postgresql")
        sys.exit(1)
    else:
        print(f"✅ 检测到PostgreSQL客户端: {psql_version}")
    
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
    
    # 解析数据库连接信息
    db_info = parse_database_url(database_url)
    
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sql_dir = os.path.join(project_root, '.scripts', 'postgresql')
    
    print(f"\n📊 数据库连接信息:")
    # 隐藏密码显示
    safe_url = database_url.split('@')[1] if '@' in database_url else database_url
    print(f"   数据库: {safe_url}")
    print(f"   将处理的数据库:")
    for db_name, sql_file in DB_SQL_MAP.items():
        sql_file_path = os.path.join(sql_dir, sql_file)
        exists_mark = "✓" if os.path.exists(sql_file_path) else "✗"
        print(f"     {exists_mark} {db_name} -> {sql_file}")
    print()
    
    # 检查SQL文件目录
    if not os.path.exists(sql_dir):
        print(f"❌ SQL文件目录不存在: {sql_dir}")
        print(f"💡 请确保SQL文件位于项目根目录/.scripts/postgresql/ 目录下")
        sys.exit(1)
    
    # 收集SQL文件信息
    sql_files_map = {}
    for db_name, sql_file in DB_SQL_MAP.items():
        sql_file_path = os.path.join(sql_dir, sql_file)
        if os.path.exists(sql_file_path):
            sql_files_map[db_name] = sql_file_path
        else:
            print(f"⚠️  SQL文件不存在: {sql_file_path}")
    
    if not sql_files_map:
        print("❌ 没有找到任何SQL文件")
        sys.exit(1)
    
    # 检查数据库是否存在
    existing_databases = []
    for db_name in sql_files_map.keys():
        if check_database_exists(db_info, db_name):
            existing_databases.append(db_name)
        else:
            print(f"⚠️  数据库 '{db_name}' 不存在，将跳过")
    
    if not existing_databases:
        print("❌ 没有可用的数据库")
        sys.exit(1)
    
    # 过滤只保留存在的数据库
    sql_files_map = {k: v for k, v in sql_files_map.items() if k in existing_databases}
    
    print("✅ 数据库连接成功\n")
    
    # 如果没有通过命令行确认，则进行交互式确认
    if not args.confirm:
        if not interactive_confirm(sql_files_map):
            sys.exit(0)
    
    # 处理每个数据库
    success_count = 0
    total_count = len(sql_files_map)
    
    for db_name, sql_file_path in sql_files_map.items():
        print(f"\n{'='*50}")
        print(f"处理数据库: {db_name}")
        print(f"{'='*50}")
        
        # 导入SQL文件
        import_success = import_sql_file(db_info, sql_file_path, target_database=db_name)
        if import_success:
            success_count += 1
        else:
            print(f"⚠️  导入数据库 '{db_name}' 的SQL文件时出现问题")
    
    print(f"\n{'='*50}")
    if success_count == total_count:
        print(f"✅ 所有操作完成！成功导入 {success_count}/{total_count} 个数据库")
        sys.exit(0)
    else:
        print(f"⚠️  部分操作完成：成功 {success_count}/{total_count} 个数据库")
        sys.exit(1)

if __name__ == '__main__':
    main()

