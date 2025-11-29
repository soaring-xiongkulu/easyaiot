"""
YOLO11n 模型推理测试脚本
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025

使用方法:
    python test_yolo11n.py [图片路径]
    
示例:
    python test_yolo11n.py test_image.jpg
    python test_yolo11n.py  # 使用默认测试图片
"""
import os
import sys
import argparse
from pathlib import Path

try:
    from ultralytics import YOLO
    import cv2
    import numpy as np
except ImportError as e:
    print(f"❌ 缺少必要的依赖库: {e}")
    print("💡 请运行: pip install ultralytics opencv-python")
    sys.exit(1)


def create_test_image(output_path='test_image.jpg', width=640, height=480):
    """创建一个简单的测试图片（如果没有提供图片）"""
    # 创建一个彩色测试图片
    img = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    # 添加一些几何图形
    cv2.rectangle(img, (100, 100), (300, 200), (0, 255, 0), 3)
    cv2.circle(img, (450, 250), 80, (255, 0, 0), 3)
    cv2.putText(img, 'Test Image', (200, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imwrite(output_path, img)
    print(f"✅ 已创建测试图片: {output_path}")
    return output_path


def test_yolo11n_inference(model_path='yolo11n.pt', image_path=None, conf_thres=0.25, iou_thres=0.45, save_result=True):
    """
    测试 YOLO11n 模型推理
    
    Args:
        model_path: 模型文件路径
        image_path: 测试图片路径（如果为None，会创建一个测试图片）
        conf_thres: 置信度阈值
        iou_thres: IoU阈值
        save_result: 是否保存结果图片
    """
    print("=" * 60)
    print("🚀 YOLO11n 模型推理测试")
    print("=" * 60)
    
    # 1. 检查模型文件是否存在
    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        print(f"💡 请确保模型文件位于当前目录或提供正确的路径")
        return False
    
    print(f"✅ 找到模型文件: {model_path}")
    file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
    print(f"   文件大小: {file_size:.2f} MB")
    
    # 2. 加载模型
    print(f"\n📦 正在加载模型...")
    try:
        model = YOLO(model_path)
        print(f"✅ 模型加载成功")
        print(f"   模型类型: {type(model).__name__}")
    except Exception as e:
        print(f"❌ 模型加载失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 准备测试图片
    if image_path is None:
        print(f"\n📸 未提供测试图片，创建默认测试图片...")
        image_path = create_test_image()
    else:
        if not os.path.exists(image_path):
            print(f"❌ 图片文件不存在: {image_path}")
            return False
        print(f"✅ 使用测试图片: {image_path}")
    
    # 读取图片信息
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ 无法读取图片: {image_path}")
        return False
    height, width = img.shape[:2]
    print(f"   图片尺寸: {width}x{height}")
    
    # 4. 执行推理
    print(f"\n🔍 开始推理...")
    print(f"   置信度阈值: {conf_thres}")
    print(f"   IoU阈值: {iou_thres}")
    
    import time
    start_time = time.time()
    
    try:
        # 执行推理
        results = model.predict(
            image_path,
            conf=conf_thres,
            iou=iou_thres,
            verbose=False  # 减少输出
        )
        inference_time = time.time() - start_time
        
        print(f"✅ 推理完成 (耗时: {inference_time:.3f}秒)")
        
        # 5. 处理结果
        if not results or len(results) == 0:
            print("⚠️  未检测到任何目标")
            return True
        
        result = results[0]
        
        # 显示检测结果
        print(f"\n📊 检测结果:")
        print(f"   检测到的目标数量: {len(result.boxes)}")
        
        if len(result.boxes) > 0:
            # 显示每个检测框的详细信息
            print(f"\n   详细信息:")
            for i, box in enumerate(result.boxes):
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                cls_name = result.names[cls_id]
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = xyxy
                
                print(f"      [{i+1}] {cls_name}: 置信度={conf:.3f}, 位置=({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")
        
        # 6. 保存结果图片
        if save_result:
            output_dir = 'data/inference_results'
            os.makedirs(output_dir, exist_ok=True)
            
            # 绘制结果
            annotated_img = result.plot()
            
            # 生成输出文件名
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            input_name = Path(image_path).stem
            output_path = os.path.join(output_dir, f'yolo11n_test_{input_name}_{timestamp}.jpg')
            
            cv2.imwrite(output_path, annotated_img)
            print(f"\n💾 结果已保存: {output_path}")
        
        # 7. 显示性能信息
        print(f"\n⚡ 性能统计:")
        print(f"   推理时间: {inference_time:.3f}秒")
        print(f"   FPS: {1.0/inference_time:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 推理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='YOLO11n 模型推理测试脚本')
    parser.add_argument('image', nargs='?', default=None, help='测试图片路径（可选，如果不提供会创建默认测试图片）')
    parser.add_argument('--model', type=str, default='yolo11n.pt', help='模型文件路径（默认: yolo11n.pt）')
    parser.add_argument('--conf', type=float, default=0.25, help='置信度阈值（默认: 0.25）')
    parser.add_argument('--iou', type=float, default=0.45, help='IoU阈值（默认: 0.45）')
    parser.add_argument('--no-save', action='store_true', help='不保存结果图片')
    
    args = parser.parse_args()
    
    # 执行测试
    success = test_yolo11n_inference(
        model_path=args.model,
        image_path=args.image,
        conf_thres=args.conf,
        iou_thres=args.iou,
        save_result=not args.no_save
    )
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 测试完成")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()

