#include <random>
#include <glog/logging.h>

#include "Yolov11Engine.h"

std::vector<std::string> g_classes = {
    "person", "bicycle", "car", "motorbike ", "aeroplane ", "bus ", "train", "truck ", "boat", "traffic light",
    "fire hydrant", "stop sign ", "parking meter", "bench", "bird", "cat", "dog ", "horse ", "sheep", "cow", "elephant",
    "bear", "zebra ", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork", "knife ",
    "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza ", "donut", "cake", "chair", "sofa",
    "pottedplant", "bed", "diningtable", "toilet ", "tvmonitor", "laptop	", "mouse	", "remote ", "keyboard ", "cell phone", "microwave ",
    "oven ", "toaster", "sink", "refrigerator ", "book", "clock", "vase", "scissors ", "teddy bear ", "hair drier", "toothbrush "};

Yolov11Engine::Yolov11Engine()
{
    ready_ = false;
}

Yolov11Engine::~Yolov11Engine()
{
    onnxEnv.release();
    onnxSessionOptions.release();
    onnxSession.release();
}

int Yolov11Engine::LoadModel(std::string model_path, std::vector<std::string> model_class)
{
    try {
        LOG(INFO) << "[YOLO] Creating ONNX Runtime environment...";
        onnxEnv = Ort::Env(ORT_LOGGING_LEVEL_VERBOSE, "YOLOV11");
        
        LOG(INFO) << "[YOLO] Setting up session options...";
        onnxSessionOptions = Ort::SessionOptions();
        onnxSessionOptions.SetGraphOptimizationLevel(ORT_ENABLE_EXTENDED);  // Enable optimizations for DirectML
        onnxSessionOptions.SetExecutionMode(ExecutionMode::ORT_SEQUENTIAL);
        onnxSessionOptions.DisableMemPattern();  // DirectML requires this
        
        // Temporarily using CPU mode - DirectML provider DLL not available
        #ifdef _WIN32
        LOG(INFO) << "[YOLO] Using CPU mode (async inference enabled)";
        LOG(INFO) << "[YOLO] DirectML disabled - onnxruntime_providers_dml.dll not found";
        // TODO: Enable DirectML GPU once provider DLL is obtained
        #else
        LOG(INFO) << "[YOLO] Using CPU execution (Linux)";
        #endif
        
        LOG(INFO) << "[YOLO] Loading model: " << model_path;
        
        // ONNX Runtime on Windows requires wide string path
        #ifdef _WIN32
            std::wstring wModelPath(model_path.begin(), model_path.end());
            onnxSession = Ort::Session(onnxEnv, wModelPath.c_str(), onnxSessionOptions);
        #else
            onnxSession = Ort::Session(onnxEnv, model_path.c_str(), onnxSessionOptions);
        #endif
        
        LOG(INFO) << "[YOLO] Model loaded successfully";
        
        if (!model_class.empty()) {
            g_classes = model_class;
            LOG(INFO) << "[YOLO] Using " << model_class.size() << " custom classes";
        } else {
            LOG(INFO) << "[YOLO] Using default COCO classes (" << g_classes.size() << " classes)";
        }
        
        ready_ = true;
        return 0;
        
    } catch (const Ort::Exception& e) {
        LOG(ERROR) << "[YOLO] ONNX Runtime exception: " << e.what();
        return -1;
    } catch (const std::exception& e) {
        LOG(ERROR) << "[YOLO] Exception loading model: " << e.what();
        return -2;
    }
}

int Yolov11Engine::Inference(const cv::Mat& image, std::vector<DetectObject> &detections)
{
    int image_w = image.cols;
    int image_h = image.rows;
    float score_threshold = 0.25;  // Lower threshold for better detection
    float nms_threshold = 0.45;
    std::vector<std::string> input_node_names;
    std::vector<std::string> output_node_names;
    size_t numInputNodes = onnxSession.GetInputCount();
    size_t numOutputNodes = onnxSession.GetOutputCount();
    Ort::AllocatorWithDefaultOptions allocator;
    input_node_names.reserve(numInputNodes);
    int input_w = 0;
    int input_h = 0;
    for (int i = 0; i < numInputNodes; i++) {
        auto input_name = onnxSession.GetInputNameAllocated(i, allocator);
        input_node_names.push_back(input_name.get());
        Ort::TypeInfo input_type_info = onnxSession.GetInputTypeInfo(i);
        auto input_tensor_info = input_type_info.GetTensorTypeAndShapeInfo();
        auto input_dims = input_tensor_info.GetShape();
        input_w = input_dims[3];
        input_h = input_dims[2];

    }
    Ort::TypeInfo output_type_info = onnxSession.GetOutputTypeInfo(0);
    auto output_tensor_info = output_type_info.GetTensorTypeAndShapeInfo();
    auto output_dims = output_tensor_info.GetShape();
    int output_dim = output_dims[1];
    int output_row = output_dims[2];

    for (int i = 0; i < numOutputNodes; i++) {
        auto out_name = onnxSession.GetOutputNameAllocated(i, allocator);
        output_node_names.push_back(out_name.get());
    }

    int image_size_max = std::max(image_h, image_w);
    cv::Mat mask = cv::Mat::zeros(cv::Size(image_size_max, image_size_max), CV_8UC3);
    cv::Rect roi(0, 0, image_w, image_h);
    image.copyTo(mask(roi));

    float x_factor = mask.cols / static_cast<float>(input_w);
    float y_factor = mask.rows / static_cast<float>(input_h);

    cv::Mat blob = cv::dnn::blobFromImage(mask, 1 / 255.0, cv::Size(input_w, input_h), cv::Scalar(0, 0, 0), true, false);
    size_t tpixels = input_h * input_w * 3;
    std::array<int64_t, 4> input_shape_info{ 1, 3, input_h, input_w };

    auto allocator_info = Ort::MemoryInfo::CreateCpu(OrtDeviceAllocator, OrtMemTypeCPU);
    Ort::Value input_tensor = Ort::Value::CreateTensor<float>(allocator_info, blob.ptr<float>(), tpixels, input_shape_info.data(), input_shape_info.size());

    std::vector<const char*> inputNames{ input_node_names[0].c_str() };
    std::vector<const char*> outNames{ output_node_names[0].c_str() };

    std::vector<Ort::Value> ort_outputs;
    try {
        ort_outputs = onnxSession.Run(Ort::RunOptions{ nullptr }, inputNames.data(), &input_tensor, 1, outNames.data(), outNames.size());
    }
    catch (std::exception e) {
        std::cout << e.what() << std::endl;
    }

    const float* pdata = ort_outputs[0].GetTensorMutableData<float>();
    cv::Mat dout(output_dim, output_row, CV_32F, (float*)pdata);
    cv::Mat det_output = dout.t();

    std::vector<cv::Rect> boxes;
    std::vector<int> classIds;
    std::vector<float> confidences;
    for (int i = 0; i < det_output.rows; i++) {
        cv::Mat classes_scores = det_output.row(i).colRange(4, output_dim);
        cv::Point classIdPoint;
        double score;
        cv::minMaxLoc(classes_scores, 0, &score, 0, &classIdPoint);

        if (score > score_threshold)
        {
            float cx = det_output.at<float>(i, 0);
            float cy = det_output.at<float>(i, 1);
            float ow = det_output.at<float>(i, 2);
            float oh = det_output.at<float>(i, 3);
            int x = static_cast<int>((cx - 0.5 * ow) * x_factor);
            int y = static_cast<int>((cy - 0.5 * oh) * y_factor);
            int width = static_cast<int>(ow * x_factor);
            int height = static_cast<int>(oh * y_factor);
            cv::Rect box;
            box.x = x;
            box.y = y;
            box.width = width;
            box.height = height;

            boxes.push_back(box);
            classIds.push_back(classIdPoint.x);
            confidences.push_back(score);
        }
    }
    std::vector<int> indexes;
    cv::dnn::NMSBoxes(boxes, confidences, score_threshold, nms_threshold, indexes);
    detections.clear();
    
    // Debug logging (first detection only to avoid spam)
    static int debug_count = 0;
    if (debug_count < 3) {
        LOG(INFO) << "[YOLO] Raw detections: " << boxes.size() << ", After NMS: " << indexes.size();
        debug_count++;
    }
    
    for (size_t i = 0; i < indexes.size(); i++) {
        DetectObject detection;
        int index = indexes[i];
        int idx = classIds[index];
        cv::Rect box = boxes[index];
        detection.x1 = box.x;
        detection.y1 = box.y;
        detection.x2 = box.x + box.width;
        detection.y2 = box.y + box.height;
        detection.class_id = idx;
        detection.class_name = g_classes[idx];
        detection.class_score = confidences[index];
        detections.push_back(detection);
        
        // Debug: print first few detections
        if (debug_count < 3 && i < 3) {
            LOG(INFO) << "[YOLO] Detected: " << g_classes[idx] 
                      << " (" << (int)(confidences[index]*100) << "%)";
        }
    }
    return 0;
}

int Yolov11Engine::Run(cv::Mat& image, std::vector<DetectObject>& detections)
{
    return Inference(image, detections);
}
