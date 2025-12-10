# 下载YOLOv11n模型并准备类别文件

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "下载YOLOv11n ONNX模型" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 创建模型目录
$modelsDir = "F:\EASYLOT\easyaiot-main\TASK\models"
if (!(Test-Path $modelsDir)) {
    Write-Host "创建模型目录: $modelsDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $modelsDir -Force | Out-Null
}

# 下载YOLOv11n模型
$modelUrl = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov11n.onnx"
$modelPath = "$modelsDir\yolov11n.onnx"

if (Test-Path $modelPath) {
    Write-Host "✅ 模型文件已存在: $modelPath" -ForegroundColor Green
} else {
    Write-Host "⏬ 正在下载模型（约6MB）..." -ForegroundColor Yellow
    Write-Host "URL: $modelUrl" -ForegroundColor Gray
    
    try {
        Invoke-WebRequest -Uri $modelUrl -OutFile $modelPath -UseBasicParsing
        Write-Host "✅ 模型下载成功!" -ForegroundColor Green
    } catch {
        Write-Host "❌ 下载失败: $_" -ForegroundColor Red
        Write-Host "请手动下载:" -ForegroundColor Yellow
        Write-Host "  1. 访问: $modelUrl" -ForegroundColor Yellow
        Write-Host "  2. 保存到: $modelPath" -ForegroundColor Yellow
        exit 1
    }
}

# 创建COCO类别文件
$cocoClasses = @"
person
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
toothbrush
"@

$classesPath = "$modelsDir\coco.names"
$cocoClasses | Out-File -FilePath $classesPath -Encoding ASCII
Write-Host "✅ COCO类别文件已创建: $classesPath" -ForegroundColor Green

# 更新配置文件
$configPath = "F:\EASYLOT\easyaiot-main\TASK\config\test.ini"
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "请手动更新配置文件:" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "文件: $configPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "[ai]" -ForegroundColor White
Write-Host "enable=true" -ForegroundColor White
Write-Host "model_path=$modelPath" -ForegroundColor Green
Write-Host "classes_path=$classesPath" -ForegroundColor Green
Write-Host "threads=3" -ForegroundColor White
Write-Host ""
Write-Host "完成后运行:" -ForegroundColor Cyan
Write-Host "  cd F:\EASYLOT\easyaiot-main\TASK\build\Release" -ForegroundColor Yellow
Write-Host "  .\TASK.exe ..\..\config\test.ini" -ForegroundColor Yellow
Write-Host ""
