#!/usr/bin/env python3
"""
MinIO配置诊断脚本
用于检查MinIO连接配置是否正确
"""
import os
import sys
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

def check_minio_config():
    """检查MinIO配置"""
    print("=" * 60)
    print("MinIO配置诊断")
    print("=" * 60)
    
    # 读取配置
    minio_endpoint = os.getenv('MINIO_ENDPOINT', 'MinIO:9000')
    access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
    
    print(f"\n1. 环境变量配置:")
    print(f"   MINIO_ENDPOINT: {minio_endpoint}")
    print(f"   MINIO_ACCESS_KEY: {access_key[:4] + '***' if len(access_key) > 4 else '***'} (长度: {len(access_key)})")
    print(f"   MINIO_SECRET_KEY: {'已设置' if secret_key else '未设置'} (长度: {len(secret_key) if secret_key else 0})")
    print(f"   MINIO_SECURE: {secure}")
    
    # 检查环境变量是否从文件加载
    env_file = os.path.exists('.env')
    env_docker_file = os.path.exists('.env.docker')
    print(f"\n2. 环境变量文件:")
    print(f"   .env 文件存在: {env_file}")
    print(f"   .env.docker 文件存在: {env_docker_file}")
    
    # 尝试连接MinIO
    print(f"\n3. MinIO连接测试:")
    try:
        from minio import Minio
        from minio.error import S3Error
        
        client = Minio(
            minio_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        # 尝试列出存储桶
        try:
            buckets = client.list_buckets()
            print(f"   ✓ 连接成功！")
            print(f"   ✓ 找到 {len(list(buckets))} 个存储桶")
            
            # 列出所有存储桶
            buckets_list = list(buckets)
            if buckets_list:
                print(f"\n   存储桶列表:")
                for bucket in buckets_list:
                    print(f"     - {bucket.name} (创建时间: {bucket.creation_date})")
            
            # 检查 inference-inputs 存储桶
            bucket_name = 'inference-inputs'
            bucket_exists = client.bucket_exists(bucket_name)
            print(f"\n4. 存储桶检查:")
            print(f"   {bucket_name}: {'存在' if bucket_exists else '不存在'}")
            
            if bucket_exists:
                # 尝试列出对象（最多5个）
                try:
                    objects = client.list_objects(bucket_name, recursive=False)
                    objects_list = list(objects)
                    print(f"   ✓ 可以访问存储桶")
                    if objects_list:
                        print(f"   ✓ 存储桶中有 {len(objects_list)} 个对象（显示前5个）:")
                        for i, obj in enumerate(objects_list[:5]):
                            print(f"     {i+1}. {obj.object_name} ({obj.size} 字节)")
                    else:
                        print(f"   ℹ 存储桶为空")
                except S3Error as e:
                    print(f"   ✗ 无法列出对象: {e}")
            else:
                print(f"   ℹ 存储桶不存在，将在首次使用时自动创建")
            
            return True
            
        except S3Error as e:
            error_code = getattr(e, 'code', 'Unknown')
            print(f"   ✗ 连接失败: {error_code}")
            print(f"   错误信息: {str(e)}")
            
            if error_code == 'InvalidAccessKeyId':
                print(f"\n   ⚠ 诊断:")
                print(f"      - Access Key ID不存在于MinIO服务器")
                print(f"      - 请检查MINIO_ACCESS_KEY是否正确")
                print(f"      - 如果MinIO服务已重新部署，可能需要更新访问密钥")
            elif error_code == 'SignatureDoesNotMatch':
                print(f"\n   ⚠ 诊断:")
                print(f"      - Secret Key签名不匹配")
                print(f"      - 请检查MINIO_SECRET_KEY是否正确")
            elif error_code == 'ConnectionRefused' or 'ConnectionError' in str(type(e)):
                print(f"\n   ⚠ 诊断:")
                print(f"      - 无法连接到MinIO服务器")
                print(f"      - 请检查MINIO_ENDPOINT是否正确: {minio_endpoint}")
                print(f"      - 确认MinIO服务是否正在运行")
            
            return False
            
    except ImportError:
        print(f"   ✗ 无法导入minio库，请确认已安装: pip install minio")
        return False
    except Exception as e:
        print(f"   ✗ 未知错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = check_minio_config()
    
    print("\n" + "=" * 60)
    if success:
        print("诊断完成：MinIO配置正常")
    else:
        print("诊断完成：发现配置问题，请根据上述提示修复")
        print("\n常见解决方案:")
        print("1. 检查 .env.docker 文件中的MinIO配置")
        print("2. 检查 docker-compose.yaml 中的环境变量")
        print("3. 确认MinIO服务正在运行且可访问")
        print("4. 验证MinIO服务器的访问密钥是否与配置一致")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

