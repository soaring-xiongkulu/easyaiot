#!/usr/bin/env python3
"""
配置 QwenVL3 API Key
从环境变量 DASHSCOPE_API_KEY 读取 API Key 并配置到数据库

使用方法:
1. 设置环境变量:
   export DASHSCOPE_API_KEY="your-api-key-here"

2. 运行脚本:
   python configure_qwenvl3_api_key.py

或者直接在命令行指定:
   python configure_qwenvl3_api_key.py --api-key "your-api-key-here"

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import argparse
from dotenv import load_dotenv

# 添加AI模块路径
ai_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ai_root)

# 加载环境变量
env_file = os.path.join(ai_root, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"✅ 已加载环境变量文件: {env_file}")
else:
    print(f"⚠️  环境变量文件 {env_file} 不存在，使用系统环境变量")

# 导入 Flask 应用和模型
from run import create_app
from db_models import LLMModel, db


def configure_qwenvl3_api_key(api_key: str, model_name: str = None, auto_create: bool = False):
    """
    配置 QwenVL3 API Key
    
    Args:
        api_key: API Key
        model_name: 模型名称（可选，如果不指定则查找现有的 QwenVL3 模型）
        auto_create: 如果模型不存在，是否自动创建
    """
    if not api_key:
        raise ValueError("API Key 不能为空")
    
    app = create_app()
    
    with app.app_context():
        # 查找现有的 QwenVL3 模型
        if model_name:
            model = LLMModel.query.filter_by(name=model_name).first()
        else:
            # 优先查找激活的模型
            model = LLMModel.query.filter_by(
                vendor='aliyun',
                model_type='vision',
                is_active=True
            ).first()
            
            if not model:
                # 查找所有阿里云视觉模型
                model = LLMModel.query.filter_by(
                    vendor='aliyun',
                    model_type='vision'
                ).first()
        
        if model:
            print(f"✅ 找到模型: {model.name}")
            print(f"   当前 API Key: {model.api_key[:10] + '***' if model.api_key else '未配置'}")
            
            # 更新 API Key
            model.api_key = api_key
            db.session.commit()
            
            print(f"✅ API Key 已更新")
            print(f"   模型名称: {model.name}")
            print(f"   模型标识: {model.model_name}")
            print(f"   API URL: {model.base_url}")
            print(f"   服务类型: {model.service_type}")
            print(f"   是否激活: {model.is_active}")
            
            return model
        else:
            if auto_create:
                print("⚠️  未找到现有模型，正在创建新的 QwenVL3 模型配置...")
                
                # 创建默认的 QwenVL3 模型配置
                default_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/"
                default_model_name = "qwen-vl-max"
                
                model = LLMModel(
                    name="QwenVL3视觉模型",
                    service_type='online',
                    vendor='aliyun',
                    model_type='vision',
                    model_name=default_model_name,
                    base_url=default_base_url,
                    api_key=api_key,
                    temperature=0.7,
                    max_tokens=2000,
                    timeout=60,
                    description="阿里云 QwenVL3 视觉推理大模型",
                    is_active=False,
                    status='inactive'
                )
                
                db.session.add(model)
                db.session.commit()
                
                print(f"✅ 已创建新的 QwenVL3 模型配置")
                print(f"   模型名称: {model.name}")
                print(f"   模型标识: {model.model_name}")
                print(f"   API URL: {model.base_url}")
                print(f"   注意: 模型尚未激活，请通过管理界面激活模型")
                
                return model
            else:
                raise ValueError(
                    "未找到 QwenVL3 模型配置。\n"
                    "请先通过管理界面创建模型配置，或使用 --auto-create 参数自动创建。\n"
                    "自动创建的参数:\n"
                    "  - 模型名称: QwenVL3视觉模型\n"
                    "  - 模型标识: qwen-vl-max\n"
                    "  - API URL: https://dashscope.aliyuncs.com/compatible-mode/v1/"
                )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='配置 QwenVL3 API Key',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从环境变量读取 API Key
  export DASHSCOPE_API_KEY="your-api-key-here"
  python configure_qwenvl3_api_key.py

  # 直接在命令行指定 API Key
  python configure_qwenvl3_api_key.py --api-key "your-api-key-here"

  # 指定模型名称
  python configure_qwenvl3_api_key.py --api-key "your-api-key" --model-name "我的QwenVL3模型"

  # 如果模型不存在，自动创建
  python configure_qwenvl3_api_key.py --api-key "your-api-key" --auto-create
        """
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='API Key（如果不指定，将从环境变量 DASHSCOPE_API_KEY 读取）'
    )
    
    parser.add_argument(
        '--model-name',
        type=str,
        default=None,
        help='模型名称（可选，如果不指定则查找现有的 QwenVL3 模型）'
    )
    
    parser.add_argument(
        '--auto-create',
        action='store_true',
        help='如果模型不存在，自动创建新的模型配置'
    )
    
    args = parser.parse_args()
    
    # 获取 API Key
    api_key = args.api_key or os.getenv('DASHSCOPE_API_KEY')
    
    if not api_key:
        print("❌ 错误: 未提供 API Key")
        print("\n请使用以下方式之一提供 API Key:")
        print("  1. 设置环境变量: export DASHSCOPE_API_KEY='your-api-key'")
        print("  2. 使用命令行参数: --api-key 'your-api-key'")
        print("  3. 在 .env 文件中添加: DASHSCOPE_API_KEY=your-api-key")
        sys.exit(1)
    
    print("=" * 60)
    print("配置 QwenVL3 API Key")
    print("=" * 60)
    print(f"\n🔑 API Key: {api_key[:10]}***{api_key[-4:] if len(api_key) > 14 else '***'}")
    
    try:
        configure_qwenvl3_api_key(
            api_key=api_key,
            model_name=args.model_name,
            auto_create=args.auto_create
        )
        print("\n" + "=" * 60)
        print("✅ 配置完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
