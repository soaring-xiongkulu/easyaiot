#include "YoloEngine.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <glog/logging.h>
#include <sstream>

namespace {

std::vector<std::string> g_classes = {
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush"};

std::string toLower(std::string s) {
    for (char& c : s) {
        c = static_cast<char>(::tolower(static_cast<unsigned char>(c)));
    }
    return s;
}

std::string replaceExt(const std::string& path, const std::string& newExt) {
    const auto slash = path.find_last_of("/\\");
    const auto dot = path.find_last_of('.');
    if (dot == std::string::npos || (slash != std::string::npos && dot < slash)) {
        return path + newExt;
    }
    return path.substr(0, dot) + newExt;
}

bool fileExists(const std::string& path) {
    std::ifstream f(path);
    return f.good();
}

std::string findEnsureScript() {
    if (const char* env = std::getenv("RUNTIME_ENSURE_ONNX_SCRIPT")) {
        if (fileExists(env)) {
            return env;
        }
    }
    // Common layouts: next to binary via RUNTIME_ROOT / repo
    const char* roots[] = {
        std::getenv("EASYAIOT_RUNTIME_INSTALL_DIR"),
        std::getenv("RUNTIME_ROOT"),
        std::getenv("EASYAIOT_ROOT"),
        nullptr,
    };
    for (int i = 0; roots[i]; ++i) {
        std::string p = std::string(roots[i]) + "/scripts/ensure_onnx_model.py";
        if (fileExists(p)) {
            return p;
        }
        p = std::string(roots[i]) + "/RUNTIME/scripts/ensure_onnx_model.py";
        if (fileExists(p)) {
            return p;
        }
    }
    // Relative to cwd / source tree
    const char* candidates[] = {
        "RUNTIME/scripts/ensure_onnx_model.py",
        "scripts/ensure_onnx_model.py",
        "/opt/easyaiot/RUNTIME/scripts/ensure_onnx_model.py",
        nullptr,
    };
    for (int i = 0; candidates[i]; ++i) {
        if (fileExists(candidates[i])) {
            return candidates[i];
        }
    }
    return "";
}

}  // namespace

YoloEngine::YoloEngine() = default;

YoloEngine::~YoloEngine() {
    onnxEnv.release();
    onnxSessionOptions.release();
    onnxSession.release();
}

std::string YoloEngine::ensureOnnxPath(const std::string& model_path) {
    const std::string lower = toLower(model_path);
    if (lower.size() >= 5 && lower.substr(lower.size() - 5) == ".onnx") {
        return model_path;
    }
    if (!(lower.size() >= 3 && lower.substr(lower.size() - 3) == ".pt")) {
        LOG(WARNING) << "[YOLO] Unexpected model suffix (expect .onnx/.pt): " << model_path;
        // Still try sibling .onnx
    }

    const std::string sibling = replaceExt(model_path, ".onnx");
    if (fileExists(sibling)) {
        LOG(INFO) << "[YOLO] Using existing ONNX beside weights: " << sibling;
        return sibling;
    }

    const std::string script = findEnsureScript();
    if (script.empty()) {
        LOG(ERROR) << "[YOLO] .pt given but no ONNX and ensure_onnx_model.py not found: " << model_path;
        return "";
    }

    std::ostringstream cmd;
    // Prefer RUNTIME_PYTHON (ultralytics-capable) over bare python3
    const char* py = std::getenv("RUNTIME_PYTHON");
    if (!py || !*py) {
        py = std::getenv("EASYAIOT_PYTHON");
    }
    if (!py || !*py) {
        py = "python3";
    }
    cmd << "\"" << py << "\" \"" << script << "\" --input \"" << model_path
        << "\" --output \"" << sibling << "\" 2>&1";
    LOG(INFO) << "[YOLO] Exporting .pt → ONNX: " << cmd.str();
    FILE* pipe = popen(cmd.str().c_str(), "r");
    if (!pipe) {
        LOG(ERROR) << "[YOLO] Failed to spawn ensure_onnx_model.py";
        return "";
    }
    char buf[512];
    while (fgets(buf, sizeof(buf), pipe)) {
        // Trim trailing newline for glog
        std::string line(buf);
        while (!line.empty() && (line.back() == '\n' || line.back() == '\r')) {
            line.pop_back();
        }
        if (!line.empty()) {
            LOG(INFO) << "[YOLO-EXPORT] " << line;
        }
    }
    const int rc = pclose(pipe);
    if (rc != 0 || !fileExists(sibling)) {
        LOG(ERROR) << "[YOLO] .pt → ONNX export failed rc=" << rc << " out=" << sibling;
        return "";
    }
    LOG(INFO) << "[YOLO] Export OK: " << sibling;
    return sibling;
}

void YoloEngine::loadNamesFromOnnxMetadata() {
    try {
        Ort::AllocatorWithDefaultOptions allocator;
        Ort::ModelMetadata meta = onnxSession.GetModelMetadata();
        Ort::AllocatedStringPtr raw = meta.LookupCustomMetadataMapAllocated("names", allocator);
        if (!raw) {
            return;
        }
        std::string text = raw.get();
        // Accept JSON {"0":"person",...} or Python dict / list-ish: strip braces
        // Minimal parser: find quoted strings in order
        std::vector<std::string> parsed;
        std::string cur;
        bool inQuote = false;
        for (size_t i = 0; i < text.size(); ++i) {
            char c = text[i];
            if (c == '\'' || c == '"') {
                if (inQuote) {
                    parsed.push_back(cur);
                    cur.clear();
                    inQuote = false;
                } else {
                    inQuote = true;
                }
                continue;
            }
            if (inQuote) {
                cur.push_back(c);
            }
        }
        // Heuristic: metadata often mixes keys and values; keep odd/even by filtering numeric keys
        std::vector<std::string> values;
        for (const auto& s : parsed) {
            bool allDigit = !s.empty();
            for (char ch : s) {
                if (!std::isdigit(static_cast<unsigned char>(ch))) {
                    allDigit = false;
                    break;
                }
            }
            if (!allDigit) {
                values.push_back(s);
            }
        }
        if (values.size() >= 2) {
            g_classes = values;
            LOG(INFO) << "[YOLO] Loaded " << g_classes.size() << " class names from ONNX metadata";
        }
    } catch (const std::exception& e) {
        LOG(WARNING) << "[YOLO] ONNX names metadata parse skipped: " << e.what();
    }
}

void YoloEngine::detectLayoutFromOutputShape(const std::vector<int64_t>& dims) {
    // Expect [1, A, B] or [A, B]
    if (dims.empty()) {
        end2end_ = false;
        modelLayout_ = "detect";
        return;
    }
    const int64_t last = dims.back();
    if (last == 6) {
        end2end_ = true;
        modelLayout_ = "end2end";
        return;
    }
    end2end_ = false;
    modelLayout_ = "detect";
}

int YoloEngine::createSession(const std::string& model_path, bool use_cuda, int gpu_device_id) {
    onnxSessionOptions = Ort::SessionOptions();
    onnxSessionOptions.SetGraphOptimizationLevel(ORT_ENABLE_EXTENDED);
    onnxSessionOptions.SetExecutionMode(ExecutionMode::ORT_SEQUENTIAL);

    if (use_cuda) {
        OrtCUDAProviderOptions cuda_options{};
        cuda_options.device_id = gpu_device_id;
        cuda_options.arena_extend_strategy = 0;
        cuda_options.gpu_mem_limit = SIZE_MAX;
        cuda_options.cudnn_conv_algo_search = OrtCudnnConvAlgoSearchExhaustive;
        cuda_options.do_copy_in_default_stream = 1;
        onnxSessionOptions.AppendExecutionProvider_CUDA(cuda_options);
        LOG(INFO) << "[YOLO] Appending CUDA EP device_id=" << gpu_device_id;
    } else {
        LOG(INFO) << "[YOLO] Using CPU execution";
    }

    onnxSession = Ort::Session(onnxEnv, model_path.c_str(), onnxSessionOptions);
    inferEp_ = use_cuda ? "cuda" : "cpu";
    return 0;
}

int YoloEngine::LoadModel(std::string model_path,
                          std::vector<std::string> model_class,
                          bool prefer_gpu,
                          bool force_cpu,
                          int gpu_device_id) {
    try {
        const std::string onnx_path = ensureOnnxPath(model_path);
        if (onnx_path.empty() || !fileExists(onnx_path)) {
            LOG(ERROR) << "[YOLO] No loadable ONNX for: " << model_path;
            inferEp_ = "none";
            return -3;
        }
        loadedOnnxPath_ = onnx_path;

        LOG(INFO) << "[YOLO] Creating ONNX Runtime environment... path=" << onnx_path;
        onnxEnv = Ort::Env(ORT_LOGGING_LEVEL_WARNING, "YOLO");

        const bool try_cuda = prefer_gpu && !force_cpu;
        bool loaded = false;

        if (try_cuda) {
            try {
                createSession(onnx_path, true, gpu_device_id);
                loaded = true;
                LOG(INFO) << "[YOLO] Using CUDA EP";
            } catch (const Ort::Exception& e) {
                LOG(WARNING) << "[YOLO] CUDA EP failed, falling back to CPU: " << e.what();
                onnxSession.release();
                onnxSessionOptions.release();
            } catch (const std::exception& e) {
                LOG(WARNING) << "[YOLO] CUDA EP failed, falling back to CPU: " << e.what();
                onnxSession.release();
                onnxSessionOptions.release();
            }
        }

        if (!loaded) {
            createSession(onnx_path, false, gpu_device_id);
            LOG(INFO) << "[YOLO] Using CPU execution" << (try_cuda ? " (fallback)" : "");
        }

        // Peek output shape for layout
        {
            Ort::TypeInfo output_type_info = onnxSession.GetOutputTypeInfo(0);
            auto output_tensor_info = output_type_info.GetTensorTypeAndShapeInfo();
            detectLayoutFromOutputShape(output_tensor_info.GetShape());
        }

        if (!model_class.empty()) {
            g_classes = model_class;
            LOG(INFO) << "[YOLO] Using " << model_class.size() << " classes from names file";
        } else {
            loadNamesFromOnnxMetadata();
            if (g_classes.empty()) {
                LOG(WARNING) << "[YOLO] No class names; detections will use class_N";
            } else {
                LOG(INFO) << "[YOLO] Using " << g_classes.size() << " class names";
            }
        }

        // YOLO26 end2end: keep slightly lower floor unless setScoreThreshold() raised it
        if (end2end_ && scoreThreshold_ < 0.20f) {
            scoreThreshold_ = 0.20f;
        }

        ready_ = true;
        LOG(INFO) << "[YOLO] Model loaded infer_ep=" << inferEp_
                  << " layout=" << modelLayout_
                  << " onnx=" << loadedOnnxPath_;
        return 0;
    } catch (const Ort::Exception& e) {
        LOG(ERROR) << "[YOLO] ONNX Runtime exception: " << e.what();
        inferEp_ = "none";
        return -1;
    } catch (const std::exception& e) {
        LOG(ERROR) << "[YOLO] Exception loading model: " << e.what();
        inferEp_ = "none";
        return -2;
    }
}

void YoloEngine::setScoreThreshold(float threshold) {
    if (threshold > 0.0f && threshold <= 1.0f) {
        scoreThreshold_ = threshold;
    }
}

int YoloEngine::Inference(const cv::Mat& image, std::vector<DetectObject>& detections) {
    detections.clear();
    const int image_w = image.cols;
    const int image_h = image.rows;

    std::vector<std::string> input_node_names;
    std::vector<std::string> output_node_names;
    const size_t numInputNodes = onnxSession.GetInputCount();
    const size_t numOutputNodes = onnxSession.GetOutputCount();
    Ort::AllocatorWithDefaultOptions allocator;
    input_node_names.reserve(numInputNodes);

    int input_w = 0;
    int input_h = 0;
    for (size_t i = 0; i < numInputNodes; i++) {
        auto input_name = onnxSession.GetInputNameAllocated(i, allocator);
        input_node_names.push_back(input_name.get());
        Ort::TypeInfo input_type_info = onnxSession.GetInputTypeInfo(i);
        auto input_dims = input_type_info.GetTensorTypeAndShapeInfo().GetShape();
        // NCHW
        if (input_dims.size() >= 4) {
            input_h = static_cast<int>(input_dims[2]);
            input_w = static_cast<int>(input_dims[3]);
        }
    }
    if (input_w <= 0 || input_h <= 0) {
        LOG(ERROR) << "[YOLO] Invalid input shape";
        return -1;
    }

    for (size_t i = 0; i < numOutputNodes; i++) {
        auto out_name = onnxSession.GetOutputNameAllocated(i, allocator);
        output_node_names.push_back(out_name.get());
    }

    // Letterbox-style square pad (keep existing RUNTIME behavior)
    const int image_size_max = std::max(image_h, image_w);
    cv::Mat mask = cv::Mat::zeros(cv::Size(image_size_max, image_size_max), CV_8UC3);
    cv::Rect roi(0, 0, image_w, image_h);
    image.copyTo(mask(roi));

    const float x_factor = mask.cols / static_cast<float>(input_w);
    const float y_factor = mask.rows / static_cast<float>(input_h);

    cv::Mat blob = cv::dnn::blobFromImage(mask, 1 / 255.0, cv::Size(input_w, input_h),
                                          cv::Scalar(0, 0, 0), true, false);
    const size_t tpixels = static_cast<size_t>(input_h) * static_cast<size_t>(input_w) * 3;
    std::array<int64_t, 4> input_shape_info{1, 3, input_h, input_w};

    auto allocator_info = Ort::MemoryInfo::CreateCpu(OrtDeviceAllocator, OrtMemTypeCPU);
    Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
        allocator_info, blob.ptr<float>(), tpixels, input_shape_info.data(), input_shape_info.size());

    std::vector<const char*> inputNames{input_node_names[0].c_str()};
    std::vector<const char*> outNames{output_node_names[0].c_str()};

    std::vector<Ort::Value> ort_outputs;
    try {
        ort_outputs = onnxSession.Run(Ort::RunOptions{nullptr}, inputNames.data(), &input_tensor, 1,
                                      outNames.data(), outNames.size());
    } catch (const std::exception& e) {
        LOG(ERROR) << "[YOLO] Inference exception: " << e.what();
        return -1;
    }

    auto out_info = ort_outputs[0].GetTensorTypeAndShapeInfo();
    auto out_dims = out_info.GetShape();
    detectLayoutFromOutputShape(out_dims);
    const float* pdata = ort_outputs[0].GetTensorData<float>();

    auto classNameOf = [](int idx) -> std::string {
        if (idx >= 0 && idx < static_cast<int>(g_classes.size())) {
            return g_classes[static_cast<size_t>(idx)];
        }
        return "class_" + std::to_string(idx);
    };

    if (end2end_) {
        // [1, N, 6] or [N, 6]
        int64_t rows = 0;
        if (out_dims.size() == 3) {
            rows = out_dims[1];
        } else if (out_dims.size() == 2) {
            rows = out_dims[0];
        } else {
            LOG(ERROR) << "[YOLO] Unexpected end2end rank=" << out_dims.size();
            return -1;
        }
        for (int64_t i = 0; i < rows; ++i) {
            const float* row = pdata + i * 6;
            const float score = row[4];
            if (score < scoreThreshold_) {
                continue;
            }
            const int cls = static_cast<int>(row[5]);
            DetectObject det;
            det.x1 = row[0] * x_factor;
            det.y1 = row[1] * y_factor;
            det.x2 = row[2] * x_factor;
            det.y2 = row[3] * y_factor;
            det.class_id = cls;
            det.class_name = classNameOf(cls);
            det.class_score = score;
            detections.push_back(det);
        }
    } else {
        // Ultralytics detect: usually [1, 4+C, N] → treat as (4+C) x N then transpose to N x (4+C)
        // Also accept [1, N, 4+C]
        int64_t d1 = 0;
        int64_t d2 = 0;
        if (out_dims.size() == 3) {
            d1 = out_dims[1];
            d2 = out_dims[2];
        } else if (out_dims.size() == 2) {
            d1 = out_dims[0];
            d2 = out_dims[1];
        } else {
            LOG(ERROR) << "[YOLO] Unexpected detect rank=" << out_dims.size();
            return -1;
        }

        cv::Mat det_output;
        if (d1 < d2) {
            // [4+C, N]
            cv::Mat dout(static_cast<int>(d1), static_cast<int>(d2), CV_32F,
                         const_cast<float*>(pdata));
            det_output = dout.t();
        } else {
            // [N, 4+C]
            det_output = cv::Mat(static_cast<int>(d1), static_cast<int>(d2), CV_32F,
                                 const_cast<float*>(pdata));
        }

        const int output_dim = det_output.cols;
        std::vector<cv::Rect> boxes;
        std::vector<int> classIds;
        std::vector<float> confidences;
        for (int i = 0; i < det_output.rows; i++) {
            if (output_dim <= 4) {
                break;
            }
            cv::Mat classes_scores = det_output.row(i).colRange(4, output_dim);
            cv::Point classIdPoint;
            double score = 0.0;
            cv::minMaxLoc(classes_scores, nullptr, &score, nullptr, &classIdPoint);
            if (score > scoreThreshold_) {
                const float cx = det_output.at<float>(i, 0);
                const float cy = det_output.at<float>(i, 1);
                const float ow = det_output.at<float>(i, 2);
                const float oh = det_output.at<float>(i, 3);
                cv::Rect box;
                box.x = static_cast<int>((cx - 0.5f * ow) * x_factor);
                box.y = static_cast<int>((cy - 0.5f * oh) * y_factor);
                box.width = static_cast<int>(ow * x_factor);
                box.height = static_cast<int>(oh * y_factor);
                boxes.push_back(box);
                classIds.push_back(classIdPoint.x);
                confidences.push_back(static_cast<float>(score));
            }
        }
        std::vector<int> indexes;
        cv::dnn::NMSBoxes(boxes, confidences, scoreThreshold_, nmsThreshold_, indexes);
        for (int index : indexes) {
            DetectObject detection;
            const int idx = classIds[static_cast<size_t>(index)];
            const cv::Rect& box = boxes[static_cast<size_t>(index)];
            detection.x1 = box.x;
            detection.y1 = box.y;
            detection.x2 = box.x + box.width;
            detection.y2 = box.y + box.height;
            detection.class_id = idx;
            detection.class_name = classNameOf(idx);
            detection.class_score = confidences[static_cast<size_t>(index)];
            detections.push_back(detection);
        }
    }

    static int debug_count = 0;
    if (debug_count < 3) {
        LOG(INFO) << "[YOLO] layout=" << modelLayout_ << " detections=" << detections.size();
        debug_count++;
    }
    return 0;
}

int YoloEngine::Run(cv::Mat& image, std::vector<DetectObject>& detections) {
    if (!ready_) {
        return -1;
    }
    return Inference(image, detections);
}
