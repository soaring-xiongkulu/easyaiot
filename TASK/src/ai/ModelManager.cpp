#include "ModelManager.h"
#include "ServiceLocator.h"

ModelManager& ModelManager::getInstance() {
    static ModelManager instance;
    return instance;
}

bool ModelManager::loadModel(const std::string& model_id, const std::string& config_path) {
    std::lock_guard<std::mutex> lock(models_mutex_);
    
    // Check if model is already loaded
    if (models_.find(model_id) != models_.end()) {
        std::cout << "Model " << model_id << " is already loaded" << std::endl;
        return true;
    }
    
    try {
        // Load model configuration
        std::ifstream config_file(config_path);
        if (!config_file.is_open()) {
            std::cerr << "Failed to open model config: " << config_path << std::endl;
            return false;
        }
        
        nlohmann::json config_data;
        config_file >> config_data;
        config_file.close();
        
        if (!validateModelConfig(config_data)) {
            std::cerr << "Invalid model configuration: " << config_path << std::endl;
            return false;
        }
        
        // Check if model file exists locally
        std::string model_path = config_data["local_path"];
        if (!std::filesystem::exists(model_path)) {
            // Try to download from MinIO
            auto minio_client = ServiceLocator::getInstance().getMinIOClient();
            if (minio_client && config_data.contains("minio_download_url")) {
                std::string minio_url = config_data["minio_download_url"];
                if (!downloadModelFromMinIO(minio_url, model_path)) {
                    std::cerr << "Failed to download model from MinIO: " << minio_url << std::endl;
                    return false;
                }
            } else {
                std::cerr << "Model file not found and no download source available: " 
                          << model_path << std::endl;
                return false;
            }
        }
        
        // Create inference engine
        std::vector<std::string> class_names;
        for (const auto& class_name : config_data["class_names"]) {
            class_names.push_back(class_name);
        }
        
        float confidence_threshold = config_data.value("confidence_threshold", 0.5f);
        
        auto inference_engine = std::make_shared<InferenceEngine>(
            model_path, class_names, confidence_threshold
        );
        
        if (!inference_engine->isModelLoaded()) {
            std::cerr << "Failed to load model: " << model_path << std::endl;
            return false;
        }
        
        // Store model information
        ModelInfo model_info;
        model_info.engine = inference_engine;
        model_info.config_path = config_path;
        model_info.priority = config_data.value("priority", 5);
        model_info.gpu_memory_fraction = config_data.value("gpu_memory_fraction", 0.1f);
        model_info.load_time = std::chrono::steady_clock::now();
        model_info.inference_count = 0;
        model_info.is_active = true;
        
        models_[model_id] = model_info;
        
        // Allocate GPU resources
        if (!allocateGPUResources(model_id)) {
            std::cerr << "Failed to allocate GPU resources for model: " << model_id << std::endl;
            models_.erase(model_id);
            return false;
        }
        
        std::cout << "Model loaded successfully: " << model_id << std::endl;
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "Error loading model " << model_id << ": " << e.what() << std::endl;
        return false;
    }
}

bool ModelManager::downloadModelFromMinIO(const std::string& minio_url, 
                                        const std::string& local_path) {
    try {
        auto minio_client = ServiceLocator::getInstance().getMinIOClient();
        if (!minio_client) {
            return false;
        }
        
        // Extract bucket and object from MinIO URL
        // Format: minio://bucket-name/path/to/model
        size_t pos = minio_url.find("://");
        if (pos == std::string::npos) {
            return false;
        }
        
        std::string path_part = minio_url.substr(pos + 3);
        size_t slash_pos = path_part.find('/');
        if (slash_pos == std::string::npos) {
            return false;
        }
        
        std::string bucket_name = path_part.substr(0, slash_pos);
        std::string object_name = path_part.substr(slash_pos + 1);
        
        // Create directory for local file
        std::filesystem::path local_path_obj(local_path);
        std::filesystem::create_directories(local_path_obj.parent_path());
        
        // Download file
        return minio_client->downloadFile(bucket_name, object_name, local_path);
        
    } catch (const std::exception& e) {
        std::cerr << "Error downloading model from MinIO: " << e.what() << std::endl;
        return false;
    }
}

std::shared_ptr<InferenceEngine> ModelManager::getModel(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(models_mutex_);
    
    auto it = models_.find(model_id);
    if (it != models_.end() && it->second.is_active) {
        it->second.inference_count++;
        return it->second.engine;
    }
    
    return nullptr;
}

void ModelManager::cleanupInactiveModels() {
    std::lock_guard<std::mutex> lock(models_mutex_);
    
    auto now = std::chrono::steady_clock::now();
    std::vector<std::string> models_to_remove;
    
    for (auto& [model_id, model_info] : models_) {
        // Remove models that haven't been used for a long time
        auto last_used = model_info.load_time;
        auto inactive_time = std::chrono::duration_cast<std::chrono::minutes>(
            now - last_used).count();
        
        if (inactive_time > 30 && model_info.inference_count == 0) {
            models_to_remove.push_back(model_id);
        }
    }
    
    for (const auto& model_id : models_to_remove) {
        releaseGPUResources(model_id);
        models_.erase(model_id);
        std::cout << "Removed inactive model: " << model_id << std::endl;
    }
}