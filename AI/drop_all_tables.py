#!/usr/bin/env python3
"""
删除AI服务所有数据库表的脚本

使用方法:
    python drop_all_tables.py [--env=环境名] [--confirm]

参数:
    --env: 指定环境配置文件，例如: --env=prod 会加载 .env.prod，默认加载 .env
    --confirm: 确认删除操作（必须提供此参数才会真正执行删除）

示例:
    python drop_all_tables.py --confirm
    python drop_all_tables.py --env=prod --confirm

警告: 此操作会永久删除所有数据，请谨慎使用！
"""
import argparse
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='删除AI服务所有数据库表')
    parser.add_argument('--env', type=str, default='', 
                       help='指定环境配置文件，例如: --env=prod 会加载 .env.prod，默认加载 .env')
    parser.add_argument('--confirm', action='store_true',
                       help='确认删除操作（必须提供此参数才会真正执行删除）')
    return parser.parse_args()

# 加载环境变量配置文件
def load_env_file(env_name=''):
    """
    加载环境变量配置文件
    使用 override=True 确保配置文件中的值能够覆盖系统环境变量
    """
    if env_name:
        env_file = f'.env.{env_name}'
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            print(f"✅ 已加载配置文件: {env_file} (覆盖模式)")
        else:
            print(f"⚠️  配置文件 {env_file} 不存在，尝试加载默认 .env 文件")
            if os.path.exists('.env'):
                load_dotenv('.env', override=True)
                print(f"✅ 已加载默认配置文件: .env (覆盖模式)")
            else:
                print(f"❌ 默认配置文件 .env 也不存在")
                sys.exit(1)
    else:
        if os.path.exists('.env'):
            load_dotenv('.env', override=True)
            print(f"✅ 已加载默认配置文件: .env (覆盖模式)")
        else:
            print(f"⚠️  默认配置文件 .env 不存在，尝试使用环境变量")

# 获取所有表名
def get_all_tables(engine):
    """获取数据库中所有表名"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return tables

# 删除所有表
def drop_all_tables(engine, confirm=False):
    """删除所有数据库表"""
    if not confirm:
        print("❌ 错误: 必须使用 --confirm 参数来确认删除操作")
        print("💡 使用方法: python drop_all_tables.py --confirm")
        return False
    
    try:
        # 获取所有表名
        tables = get_all_tables(engine)
        
        if not tables:
            print("ℹ️  数据库中没有表需要删除")
            return True
        
        print(f"\n⚠️  警告: 即将删除以下 {len(tables)} 个表:")
        for i, table in enumerate(tables, 1):
            print(f"   {i}. {table}")
        
        print("\n⚠️  此操作会永久删除所有数据，无法恢复！")
        print("正在执行删除操作...\n")
        
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
                print(f"\n✅ 成功删除所有表！")
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

def main():
    # 解析命令行参数
    args = parse_args()
    
    # 加载环境变量
    load_env_file(args.env)
    
    # 获取数据库URL
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ 错误: DATABASE_URL环境变量未设置")
        print("💡 请检查.env文件或环境变量配置")
        sys.exit(1)
    
    # 转换postgres://为postgresql://（SQLAlchemy要求）
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"\n📊 数据库连接信息:")
    # 隐藏密码显示
    safe_url = database_url
    if '@' in database_url:
        parts = database_url.split('@')
        if len(parts) == 2:
            user_pass = parts[0].split('://')[-1]
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                safe_url = database_url.replace(user_pass, f"{user}:***")
    print(f"   数据库: {safe_url}")
    print()
    
    # 创建数据库引擎
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        
        # 测试连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ 数据库连接成功\n")
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        if "Connection refused" in str(e):
            print(f"💡 提示: 请检查数据库服务是否运行，以及 DATABASE_URL 配置是否正确")
        elif "No module named" in str(e):
            print(f"💡 提示: 缺少数据库驱动，请运行: pip install psycopg2-binary")
        sys.exit(1)
    
    # 执行删除操作
    success = drop_all_tables(engine, confirm=args.confirm)
    
    if success:
        print("\n✅ 操作完成")
        sys.exit(0)
    else:
        print("\n❌ 操作失败")
        sys.exit(1)

if __name__ == '__main__':
    main()

