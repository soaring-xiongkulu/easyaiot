#pragma once
#include "InferenceEngine.h"
#include "ModelDownloader.h"
#include <map>
#include <memory>
#include <mutex>
#include <nlohmann/json.hpp>

class ModelManager {
public:
    static ModelManager& getInstance();
    
    bool loadModel(const std::string& model_id, const std::string& config_path);
    bool unloadModel(const std::string& model_id);
    bool reloadModel(const std::string& model_id);
    
    std::shared_ptr<InferenceEngine> getModel(const std::string& model_id);
    std::vector<std::string> getLoadedModels() const;
    
    bool isModelLoaded(const std::string& model_id) const;
    std::string getModelStatus(const std::string& model_id) const;
    
    void setModelPriority(const std::string& model_id, int priority);
    void setGPUAllocation(const std::string& model_id, float gpu_memory_fraction);

private:
    ModelManager() = default;
    ~ModelManager() = default;
    
    struct ModelInfo {
        std::shared_ptr<InferenceEngine> engine;
        std::string config_path;
        int priority;
        float gpu_memory_fraction;
        std::chrono::steady_clock::time_point load_time;
        uint64_t inference_count;
        bool is_active;
    };
    
    std::map<std::string, ModelInfo> models_;
    mutable std::mutex models_mutex_;
    
    std::shared_ptr<ModelDownloader> model_downloader_;
    
    bool validateModelConfig(const nlohmann::json& config) const;
    bool allocateGPUResources(const std::string& model_id);
    void releaseGPUResources(const std::string& model_id);
    
    void updateModelStatistics(const std::string& model_id, bool success);
    void cleanupInactiveModels();
};