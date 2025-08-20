#ifndef RK3588_DEMO_RKNN_ENGINE_H
#define RK3588_DEMO_RKNN_ENGINE_H

#include <vector>
#include "engine.h"
#include <rknn_api.h>


class RKEngine : public NNEngine
{
public:
    RKEngine() : rknn_ctx_(0), ctx_created_(false), input_num_(0), output_num_(0){}; 
    ~RKEngine() override;                                                           

    int LoadModelFile(const char *model_file) override;                                                        
    const std::vector<tensor_attr_s> &GetInputShapes() override;                                                       
    const std::vector<tensor_attr_s> &GetOutputShapes() override;                                                      
    int Run(std::vector<tensor_data_s> &inputs, std::vector<tensor_data_s> &outputs, bool want_float) override; 

private:
    rknn_context rknn_ctx_;
    bool ctx_created_;

    uint32_t input_num_;
    uint32_t output_num_;

    std::vector<tensor_attr_s> in_shapes_;
    std::vector<tensor_attr_s> out_shapes_;
};

#endif // RK3588_DEMO_RKNN_ENGINE_H
