// @author 翱翔的雄库鲁
// @email andywebjava@163.com
// @wechat EasyAIoT2025

#include <random>

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
    onnxEnv = Ort::Env(ORT_LOGGING_LEVEL_WARNING, "YOLOV11");
    onnxSessionOptions = Ort::SessionOptions();
    onnxSessionOptions.SetGraphOptimizationLevel(ORT_ENABLE_BASIC);
    std::vector<std::string> providers = Ort::GetAvailableProviders();
    auto f = std::find(providers.begin(), providers.end(), "CUDAExecutionProvider");
    if (f != providers.end()) {
        OrtCUDAProviderOptions cudaOption;
        cudaOption.device_id = 0;
        onnxSessionOptions.AppendExecutionProvider_CUDA(cudaOption);
    }
    onnxSession = Ort::Session(onnxEnv, model_path.c_str(), onnxSessionOptions);
    if (model_class.empty()) {
        g_classes = model_class;
    }
    ready_ = true;
    return 0;
}

int Yolov11Engine::Inference(const cv::Mat& image, std::vector<DetectObject> &detections)
{
    int image_w = image.cols;
    int image_h = image.rows;
    float score_threshold = 0.5;
    float nms_threshold = 0.5;
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
    Ort::Value input_tensor_ = Ort::Value::CreateTensor<float>(allocator_info, blob.ptr<float>(), tpixels, input_shape_info.data(), input_shape_info.size());
    const std::array<const char*, 1> inputNames = { input_node_names[0].c_str() };
    const std::array<const char*, 1> outNames = { output_node_names[0].c_str() };

    std::vector<Ort::Value> ort_outputs = onnxSession.Run(Ort::RunOptions{ nullptr }, inputNames.data(), &input_tensor_, 1, outNames.data(), outNames.size());
    const float* pdata = ort_outputs[0].GetTensorMutableData<float>();
    cv::Mat dout(output_dim, output_row, CV_32F, (float*)pdata);
    cv::Mat det_output = dout.t(); // 8400x84
    std::vector<cv::Rect> boxes;
    std::vector<int> classIds;
    std::vector<float> confidences;

    for (int i = 0; i < det_output.rows; i++) {
        cv::Mat classes_scores = det_output.row(i).colRange(4, 84);
        cv::Point classIdPoint;
        double score;
        minMaxLoc(classes_scores, 0, &score, 0, &classIdPoint);
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
    for (size_t i = 0; i < indexes.size(); i++) {

        int index = indexes[i];
        int class_id = classIds[index];
        float class_score = confidences[index];
        cv::Rect box = boxes[index];
        DetectObject detect;
        detect.x1 = box.x;
        detect.y1 = box.y;
        detect.x2 = box.x + box.width;
        detect.y2 = box.y + box.height;
        detect.class_id = class_id;
        detect.class_name = g_classes[class_id];
        detect.class_score = class_score;
        detections.push_back(detect);
    }
    return true;
}

int Yolov11Engine::Run(cv::Mat& image, std::vector<DetectObject>& detections)
{
    Inference(image, detections);
    return 0;
}