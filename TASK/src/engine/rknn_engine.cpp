#include "rknn_engine.h"

#include <string.h>
#include <iostream>
#include "utils/engine_helper.h"

static const int g_max_io_num = 10; // 最大输入输出张量的数量

int RKEngine::LoadModelFile(const char *model_file)
{
    int model_len = 0;                               
    auto model = load_model(model_file, &model_len); 
    if (model == nullptr)
    {
        printf("load model file %s fail!\n", model_file);
        return -1;
    }
    int ret = rknn_init(&rknn_ctx_, model, model_len, 0, NULL);
    if (ret < 0)
    {
        printf("rknn_init fail! ret=%d\n", ret);
        return -1;
    }

    ctx_created_ = true;

    // 获取输入输出个数
    rknn_input_output_num io_num;
    ret = rknn_query(rknn_ctx_, RKNN_QUERY_IN_OUT_NUM, &io_num, sizeof(io_num));
    if (ret != RKNN_SUCC)
    {
        printf("rknn_query fail! ret=%d", ret);
        return -1;
    }
    printf("model input num: %d, output num: %d\n", io_num.n_input, io_num.n_output);

    // 保存输入输出个数
    input_num_ = io_num.n_input;
    output_num_ = io_num.n_output;

    // 输入属性
    printf("input tensors:\n");
    rknn_tensor_attr input_attrs[io_num.n_input];
    memset(input_attrs, 0, sizeof(input_attrs));
    for (int i = 0; i < io_num.n_input; i++)
    {
        input_attrs[i].index = i;
        ret = rknn_query(rknn_ctx_, RKNN_QUERY_INPUT_ATTR, &(input_attrs[i]), sizeof(rknn_tensor_attr));
        if (ret != RKNN_SUCC)
        {
            printf("rknn_query fail! ret=%d\n", ret);
            return -1;
        }
        print_tensor_attr(&(input_attrs[i]));
        in_shapes_.push_back(rknn_tensor_attr_convert(input_attrs[i]));
    }

    // 输出属性
    printf("output tensors:\n");
    rknn_tensor_attr output_attrs[io_num.n_output];
    memset(output_attrs, 0, sizeof(output_attrs));
    for (int i = 0; i < io_num.n_output; i++)
    {
        output_attrs[i].index = i;
        ret = rknn_query(rknn_ctx_, RKNN_QUERY_OUTPUT_ATTR, &(output_attrs[i]), sizeof(rknn_tensor_attr));
        if (ret != RKNN_SUCC)
        {
            printf("rknn_query fail! ret=%d\n", ret);
            return -1;
        }
        print_tensor_attr(&(output_attrs[i]));
        out_shapes_.push_back(rknn_tensor_attr_convert(output_attrs[i]));
    }

    return 0;
}

// 获取输入张量的形状
const std::vector<tensor_attr_s> &RKEngine::GetInputShapes()
{
    return in_shapes_;
}

// 获取输出张量的形状
const std::vector<tensor_attr_s> &RKEngine::GetOutputShapes()
{
    return out_shapes_;
}

int RKEngine::Run(std::vector<tensor_data_s> &inputs, std::vector<tensor_data_s> &outputs, bool want_float)
{
    // 检查输入输出张量的数量是否匹配
    if (inputs.size() != input_num_)
    {
        printf("inputs num not match! inputs.size()=%ld, input_num_=%d\n", inputs.size(), input_num_);
        return -1;
    }
    if (outputs.size() != output_num_)
    {
        printf("outputs num not match! outputs.size()=%ld, output_num_=%d\n", outputs.size(), output_num_);
        return -1;
    }

    // 设置rknn inputs
    rknn_input rknn_inputs[g_max_io_num];
    for (int i = 0; i < inputs.size(); i++)
    {
        rknn_inputs[i] = tensor_data_to_rknn_input(inputs[i]);
    }
    int ret = rknn_inputs_set(rknn_ctx_, (uint32_t)inputs.size(), rknn_inputs);
    if (ret < 0)
    {
        printf("rknn_inputs_set fail! ret=%d\n", ret);
        return -1;
    }

    // 推理
    // printf("rknn running...\n");
    ret = rknn_run(rknn_ctx_, nullptr);
    if (ret < 0)
    {
        printf("rknn_run fail! ret=%d\n", ret);
        return -1;
    }

    // 获得输出
    rknn_output rknn_outputs[g_max_io_num];
    memset(rknn_outputs, 0, sizeof(rknn_outputs));
    for (int i = 0; i < output_num_; ++i)
    {
        rknn_outputs[i].want_float = want_float ? 1 : 0;
    }
    ret = rknn_outputs_get(rknn_ctx_, output_num_, rknn_outputs, NULL);
    if (ret < 0)
    {
        printf("rknn_outputs_get fail! ret=%d\n", ret);
        return -1;
    }
    // printf("output num: %d\n", output_num_);
    // copy rknn outputs to tensor_data_s
    for (int i = 0; i < output_num_; ++i)
    {
        rknn_output_to_tensor_data(rknn_outputs[i], outputs[i]);
        free(rknn_outputs[i].buf);                                  // 释放缓存
    }
    return 0;
}

// 析构函数
RKEngine::~RKEngine()
{
    if (ctx_created_)
    {
        rknn_destroy(rknn_ctx_);
        printf("rknn context destroyed!\n");
    }
}

// 创建RKNN引擎
std::shared_ptr<NNEngine> CreateRKNNEngine()
{
    return std::make_shared<RKEngine>();
}
