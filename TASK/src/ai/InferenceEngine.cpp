#include "InferenceEngine.h"
#include <fstream>
#include <filesystem>
#include <opencv2/dnn/dnn.hpp>

InferenceEngine::InferenceEngine(const std::string& model_path,
                               const std::vector<std::string>& class_names,
                               float confidence_threshold)
    : class_names(class_names), confidence_threshold(confidence_threshold)
{
    loadModel(model_path);
}

bool InferenceEngine::loadModel(const std::string& model_path)
{
    try
    {
        // 检查模型文件是否存在
        if (!std::filesystem::exists(model_path))
        {
            std::cerr << "Model file not found: " << model_path << std::endl;
            return false;
        }

        // 根据文件扩展名选择加载方式
        std::string extension = std::filesystem::path(model_path).extension().string();

        if (extension == ".onnx")
        {
            net = cv::dnn::readNetFromONNX(model_path);
        }
        else if (extension == ".pb")
        {
            net = cv::dnn::readNetFromTensorflow(model_path);
        }
        else if (extension == ".pt" || extension == ".pth")
        {
            // 需要OpenCV的DNN模块支持PyTorch
            net = cv::dnn::readNetFromTorch(model_path);
        }
        else
        {
            std::cerr << "Unsupported model format: " << extension << std::endl;
            return false;
        }

        if (net.empty())
        {
            std::cerr << "Failed to load model: " << model_path << std::endl;
            return false;
        }

        // 设置计算后端和目标
        net.setPreferableBackend(cv::dnn::DNN_BACKEND_CUDA);
        net.setPreferableTarget(cv::dnn::DNN_TARGET_CUDA);

        // 获取输入层信息 - 使用正确的方法
        std::vector<cv::String> layer_names = net.getLayerNames();
        if (layer_names.empty())
        {
            std::cerr << "No layers found in the model" << std::endl;
            return false;
        }

        // 获取第一个输入层（通常是第0层）
        cv::Ptr<cv::dnn::Layer> first_layer = net.getLayer(0);

        // 获取输入层的形状
        std::vector<cv::dnn::MatShape> input_shapes;
        std::vector<cv::dnn::MatShape> output_shapes;

        // 创建一个虚拟的输入形状（NCHW格式）
        cv::dnn::MatShape dummy_shape = {1, 3, 224, 224};

        // 获取输入层的形状信息
        net.getLayerShapes(dummy_shape, 0, input_shapes, output_shapes);

        if (!input_shapes.empty() && !input_shapes[0].empty())
        {
            const auto& shape = input_shapes[0];  // 输入层的输入形状
            // 形状格式通常是 [batch_size, channels, height, width]
            if (shape.size() >= 4)
            {
                input_size.height = shape[2];
                input_size.width = shape[3];
                std::cout << "Input size: " << input_size.width << "x" << input_size.height << std::endl;
            }
            else if (shape.size() >= 2)
            {
                // 某些模型可能使用不同的维度顺序
                input_size.height = shape[0];
                input_size.width = shape[1];
                std::cout << "Input size: " << input_size.width << "x" << input_size.height << std::endl;
            }
            else
            {
                std::cerr << "Unexpected input shape format" << std::endl;
                return false;
            }
        }
        else
        {
            std::cerr << "Failed to get input shape" << std::endl;
            return false;
        }

        std::cout << "Model loaded successfully: " << model_path << std::endl;
        return true;
    }
    catch (const std::exception& e)
    {
        std::cerr << "Error loading model: " << e.what() << std::endl;
        return false;
    }
}

std::vector<Detection> InferenceEngine::processFrame(const cv::Mat& frame)
{
    std::vector<Detection> detections;

    if (net.empty())
    {
        std::cerr << "Model not loaded" << std::endl;
        return detections;
    }

    try
    {
        // 预处理图像
        cv::Mat blob;
        cv::dnn::blobFromImage(frame, blob, 1.0/255.0,
                             cv::Size(input_size.width, input_size.height),
                             cv::Scalar(), true, false);

        // 设置网络输入
        net.setInput(blob);

        // 前向传播 - 使用输出层名称
        std::vector<cv::String> output_names = net.getUnconnectedOutLayersNames();
        std::vector<cv::Mat> outputs;
        net.forward(outputs, output_names);

        // 后处理
        detections = postProcess(outputs, frame.size());

        return detections;
    }
    catch (const std::exception& e)
    {
        std::cerr << "Error processing frame: " << e.what() << std::endl;
        return detections;
    }
}

std::vector<Detection> InferenceEngine::postProcess(const std::vector<cv::Mat>& outputs,
                                                   const cv::Size& frame_size)
{
    std::vector<Detection> detections;

    for (const auto& output : outputs)
    {
        // 根据不同的模型输出格式进行解析
        if (output.dims == 2) // YOLO格式
        {
            parseYOLOOutput(output, frame_size, detections);
        }
        else if (output.dims == 3) // SSD格式
        {
            parseSSDOutput(output, frame_size, detections);
        }
    }

    // 应用非极大值抑制
    applyNMS(detections);

    return detections;
}

void InferenceEngine::parseYOLOOutput(const cv::Mat& output, const cv::Size& frame_size,
                                     std::vector<Detection>& detections)
{
    const int rows = output.rows;
    const int dimensions = output.cols;

    for (int i = 0; i < rows; ++i)
    {
        const float* data = output.ptr<float>(i);

        // 获取类别置信度
        cv::Mat scores(1, dimensions - 4, CV_32FC1, const_cast<float*>(data + 4));
        cv::Point class_id_point;
        double confidence;
        cv::minMaxLoc(scores, nullptr, &confidence, nullptr, &class_id_point);

        if (confidence > confidence_threshold)
        {
            int center_x = static_cast<int>(data[0] * frame_size.width);
            int center_y = static_cast<int>(data[1] * frame_size.height);
            int width = static_cast<int>(data[2] * frame_size.width);
            int height = static_cast<int>(data[3] * frame_size.height);

            int left = center_x - width / 2;
            int top = center_y - height / 2;

            Detection det;
            det.class_id = class_id_point.x;
            det.confidence = static_cast<float>(confidence);
            det.bbox = cv::Rect(left, top, width, height);
            det.label = class_names[det.class_id];

            detections.push_back(det);
        }
    }
}

void InferenceEngine::applyNMS(std::vector<Detection>& detections)
{
    std::vector<int> indices;
    std::vector<float> confidences;
    std::vector<cv::Rect> boxes;

    for (const auto& det : detections)
    {
        confidences.push_back(det.confidence);
        boxes.push_back(det.bbox);
    }

    cv::dnn::NMSBoxes(boxes, confidences, confidence_threshold, 0.4f, indices);

    std::vector<Detection> filtered_detections;
    for (int idx : indices)
    {
        filtered_detections.push_back(detections[idx]);
    }

    detections = filtered_detections;
}

void InferenceEngine::setConfidenceThreshold(float threshold)
{
    confidence_threshold = threshold;
}

std::vector<std::string> InferenceEngine::getClassNames() const
{
    return class_names;
}

bool InferenceEngine::isModelLoaded() const
{
    return !net.empty();
}