#!/usr/bin/env python3
"""
Export YOLOv11 model optimized for DirectML GPU acceleration
Simplifies the model to ensure all operators are DirectML-compatible
"""

from ultralytics import YOLO
import onnx
from onnx import version_converter
import sys

def export_yolo_for_directml():
    print("=" * 60)
    print(" Exporting YOLOv11 for DirectML GPU")
    print("=" * 60)
    print()
    
    model_path = "yolov11n.pt"
    output_path = "../models/yolov11n.onnx"
    
    try:
        # Load YOLOv11 model
        print(f"[1/4] Loading model: {model_path}")
        model = YOLO(model_path)
        print("  ✓ Model loaded")
        
        # Export with DirectML-compatible settings
        print()
        print("[2/4] Exporting to ONNX (DirectML-compatible)...")
        print("  - Opset: 13 (better DirectML support)")
        print("  - Simplify: Yes")
        print("  - Dynamic: No (static shapes for DirectML)")
        
        model.export(
            format="onnx",
            opset=13,  # Lower opset for better DirectML compatibility
            simplify=True,  # Simplify graph
            dynamic=False,  # Static shapes
            imgsz=640
        )
        
        print("  ✓ ONNX export completed")
        
        # Load and verify the exported model
        print()
        print("[3/4] Verifying exported model...")
        onnx_model = onnx.load("yolov11n.onnx")
        onnx.checker.check_model(onnx_model)
        print(f"  ✓ Model valid (Opset: {onnx_model.opset_import[0].version})")
        
        # Move to models directory
        print()
        print("[4/4] Moving model to models directory...")
        import shutil
        shutil.move("yolov11n.onnx", output_path)
        print(f"  ✓ Model saved: {output_path}")
        
        print()
        print("=" * 60)
        print(" ✓ Export completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. cd F:\\EASYLOT\\easyaiot-main\\TASK\\build\\Release")
        print("  2. .\\TASK.exe ..\\..\\config\\test.ini")
        print()
        
    except Exception as e:
        print()
        print(f"✗ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  - Make sure yolov11n.pt is in the current directory")
        print("  - Install: pip install ultralytics onnx")
        sys.exit(1)

if __name__ == "__main__":
    export_yolo_for_directml()

"""
Export YOLOv11 model optimized for DirectML GPU acceleration
Simplifies the model to ensure all operators are DirectML-compatible
"""

from ultralytics import YOLO
import onnx
from onnx import version_converter
import sys

def export_yolo_for_directml():
    print("=" * 60)
    print(" Exporting YOLOv11 for DirectML GPU")
    print("=" * 60)
    print()
    
    model_path = "yolov11n.pt"
    output_path = "../models/yolov11n.onnx"
    
    try:
        # Load YOLOv11 model
        print(f"[1/4] Loading model: {model_path}")
        model = YOLO(model_path)
        print("  ✓ Model loaded")
        
        # Export with DirectML-compatible settings
        print()
        print("[2/4] Exporting to ONNX (DirectML-compatible)...")
        print("  - Opset: 13 (better DirectML support)")
        print("  - Simplify: Yes")
        print("  - Dynamic: No (static shapes for DirectML)")
        
        model.export(
            format="onnx",
            opset=13,  # Lower opset for better DirectML compatibility
            simplify=True,  # Simplify graph
            dynamic=False,  # Static shapes
            imgsz=640
        )
        
        print("  ✓ ONNX export completed")
        
        # Load and verify the exported model
        print()
        print("[3/4] Verifying exported model...")
        onnx_model = onnx.load("yolov11n.onnx")
        onnx.checker.check_model(onnx_model)
        print(f"  ✓ Model valid (Opset: {onnx_model.opset_import[0].version})")
        
        # Move to models directory
        print()
        print("[4/4] Moving model to models directory...")
        import shutil
        shutil.move("yolov11n.onnx", output_path)
        print(f"  ✓ Model saved: {output_path}")
        
        print()
        print("=" * 60)
        print(" ✓ Export completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. cd F:\\EASYLOT\\easyaiot-main\\TASK\\build\\Release")
        print("  2. .\\TASK.exe ..\\..\\config\\test.ini")
        print()
        
    except Exception as e:
        print()
        print(f"✗ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  - Make sure yolov11n.pt is in the current directory")
        print("  - Install: pip install ultralytics onnx")
        sys.exit(1)

if __name__ == "__main__":
    export_yolo_for_directml()

 
"""
Export YOLOv11 model optimized for DirectML GPU acceleration
Simplifies the model to ensure all operators are DirectML-compatible
"""

from ultralytics import YOLO
import onnx
from onnx import version_converter
import sys

def export_yolo_for_directml():
    print("=" * 60)
    print(" Exporting YOLOv11 for DirectML GPU")
    print("=" * 60)
    print()
    
    model_path = "yolov11n.pt"
    output_path = "../models/yolov11n.onnx"
    
    try:
        # Load YOLOv11 model
        print(f"[1/4] Loading model: {model_path}")
        model = YOLO(model_path)
        print("  ✓ Model loaded")
        
        # Export with DirectML-compatible settings
        print()
        print("[2/4] Exporting to ONNX (DirectML-compatible)...")
        print("  - Opset: 13 (better DirectML support)")
        print("  - Simplify: Yes")
        print("  - Dynamic: No (static shapes for DirectML)")
        
        model.export(
            format="onnx",
            opset=13,  # Lower opset for better DirectML compatibility
            simplify=True,  # Simplify graph
            dynamic=False,  # Static shapes
            imgsz=640
        )
        
        print("  ✓ ONNX export completed")
        
        # Load and verify the exported model
        print()
        print("[3/4] Verifying exported model...")
        onnx_model = onnx.load("yolov11n.onnx")
        onnx.checker.check_model(onnx_model)
        print(f"  ✓ Model valid (Opset: {onnx_model.opset_import[0].version})")
        
        # Move to models directory
        print()
        print("[4/4] Moving model to models directory...")
        import shutil
        shutil.move("yolov11n.onnx", output_path)
        print(f"  ✓ Model saved: {output_path}")
        
        print()
        print("=" * 60)
        print(" ✓ Export completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. cd F:\\EASYLOT\\easyaiot-main\\TASK\\build\\Release")
        print("  2. .\\TASK.exe ..\\..\\config\\test.ini")
        print()
        
    except Exception as e:
        print()
        print(f"✗ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  - Make sure yolov11n.pt is in the current directory")
        print("  - Install: pip install ultralytics onnx")
        sys.exit(1)

if __name__ == "__main__":
    export_yolo_for_directml()

"""
Export YOLOv11 model optimized for DirectML GPU acceleration
Simplifies the model to ensure all operators are DirectML-compatible
"""

from ultralytics import YOLO
import onnx
from onnx import version_converter
import sys

def export_yolo_for_directml():
    print("=" * 60)
    print(" Exporting YOLOv11 for DirectML GPU")
    print("=" * 60)
    print()
    
    model_path = "yolov11n.pt"
    output_path = "../models/yolov11n.onnx"
    
    try:
        # Load YOLOv11 model
        print(f"[1/4] Loading model: {model_path}")
        model = YOLO(model_path)
        print("  ✓ Model loaded")
        
        # Export with DirectML-compatible settings
        print()
        print("[2/4] Exporting to ONNX (DirectML-compatible)...")
        print("  - Opset: 13 (better DirectML support)")
        print("  - Simplify: Yes")
        print("  - Dynamic: No (static shapes for DirectML)")
        
        model.export(
            format="onnx",
            opset=13,  # Lower opset for better DirectML compatibility
            simplify=True,  # Simplify graph
            dynamic=False,  # Static shapes
            imgsz=640
        )
        
        print("  ✓ ONNX export completed")
        
        # Load and verify the exported model
        print()
        print("[3/4] Verifying exported model...")
        onnx_model = onnx.load("yolov11n.onnx")
        onnx.checker.check_model(onnx_model)
        print(f"  ✓ Model valid (Opset: {onnx_model.opset_import[0].version})")
        
        # Move to models directory
        print()
        print("[4/4] Moving model to models directory...")
        import shutil
        shutil.move("yolov11n.onnx", output_path)
        print(f"  ✓ Model saved: {output_path}")
        
        print()
        print("=" * 60)
        print(" ✓ Export completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. cd F:\\EASYLOT\\easyaiot-main\\TASK\\build\\Release")
        print("  2. .\\TASK.exe ..\\..\\config\\test.ini")
        print()
        
    except Exception as e:
        print()
        print(f"✗ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  - Make sure yolov11n.pt is in the current directory")
        print("  - Install: pip install ultralytics onnx")
        sys.exit(1)

if __name__ == "__main__":
    export_yolo_for_directml()

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 