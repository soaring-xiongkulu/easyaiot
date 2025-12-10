"""
YOLO模型下载脚本
用于下载常用的YOLOv11模型并导出为ONNX格式
"""

from ultralytics import YOLO
import os

# 模型保存目录
MODEL_DIR = "F:/models"
os.makedirs(MODEL_DIR, exist_ok=True)

# 要下载的模型列表
MODELS = {
    # 检测模型（推荐）
    'yolov11n': '最快，实时流推荐',
    'yolov11s': '平衡性能',
    'yolov11m': '高精度',
    
    # 分割模型
    # 'yolov11n-seg': '实例分割',
    
    # 姿态模型
    # 'yolov11n-pose': '人体姿态',
}

def download_and_export(model_name, description):
    """下载模型并导出为ONNX"""
    print(f"\n{'='*60}")
    print(f"📥 正在处理: {model_name} ({description})")
    print(f"{'='*60}")
    
    try:
        # 1. 加载模型（自动下载）
        print(f"⏬ 下载 {model_name}.pt...")
        model = YOLO(f'{model_name}.pt')
        
        # 2. 导出为ONNX
        print(f"🔄 导出为ONNX格式...")
        onnx_path = model.export(
            format='onnx',
            imgsz=640,
            simplify=True,
            opset=12
        )
        
        # 3. 移动到目标目录
        import shutil
        target_path = os.path.join(MODEL_DIR, f'{model_name}.onnx')
        shutil.move(onnx_path, target_path)
        
        print(f"✅ 成功！模型保存到: {target_path}")
        
        # 4. 显示模型信息
        file_size = os.path.getsize(target_path) / 1024 / 1024
        print(f"📦 文件大小: {file_size:.1f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        return False

def download_coco_names():
    """下载COCO类别文件"""
    print(f"\n{'='*60}")
    print(f"📥 下载COCO类别文件...")
    print(f"{'='*60}")
    
    coco_names = """person
bicycle
car
motorcycle
airplane
bus
train
truck
boat
traffic light
fire hydrant
stop sign
parking meter
bench
bird
cat
dog
horse
sheep
cow
elephant
bear
zebra
giraffe
backpack
umbrella
handbag
tie
suitcase
frisbee
skis
snowboard
sports ball
kite
baseball bat
baseball glove
skateboard
surfboard
tennis racket
bottle
wine glass
cup
fork
knife
spoon
bowl
banana
apple
sandwich
orange
broccoli
carrot
hot dog
pizza
donut
cake
chair
couch
potted plant
bed
dining table
toilet
tv
laptop
mouse
remote
keyboard
cell phone
microwave
oven
toaster
sink
refrigerator
book
clock
vase
scissors
teddy bear
hair drier
toothbrush"""
    
    coco_path = os.path.join(MODEL_DIR, 'coco.names')
    with open(coco_path, 'w', encoding='utf-8') as f:
        f.write(coco_names)
    
    print(f"✅ COCO类别文件已保存: {coco_path}")

def main():
    print("╔════════════════════════════════════════════════════════╗")
    print("║         YOLO模型下载和转换工具                        ║")
    print("╚════════════════════════════════════════════════════════╝")
    print(f"\n📁 模型保存目录: {MODEL_DIR}\n")
    
    # 下载COCO类别文件
    download_coco_names()
    
    # 下载并转换模型
    success_count = 0
    total_count = len(MODELS)
    
    for model_name, description in MODELS.items():
        if download_and_export(model_name, description):
            success_count += 1
    
    # 总结
    print(f"\n{'='*60}")
    print(f"📊 下载完成!")
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"📁 保存位置: {MODEL_DIR}")
    print(f"{'='*60}\n")
    
    # 显示配置示例
    print("💡 TASK模块配置示例:")
    print(f"""
[ai]
model_path={MODEL_DIR}/yolov11n.onnx
classes_path={MODEL_DIR}/coco.names
threads=3
""")

if __name__ == '__main__':
    main()
