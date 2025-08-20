// 定义数据类型

#ifndef RK3588_DEMO_DATATYPE_H
#define RK3588_DEMO_DATATYPE_H

#include <iostream>
#include <stdint.h>
#include <stdlib.h>
#include <opencv2/opencv.hpp>

typedef enum _tensor_layout
{
    NN_TENSORT_LAYOUT_UNKNOWN = 0,
    NN_TENSOR_NCHW = 1,
    NN_TENSOR_NHWC = 2,
    NN_TENSOR_OTHER = 3,
} tensor_layout_e;

typedef enum _tensor_datatype
{
    NN_TENSOR_INT8 = 1,
    NN_TENSOR_UINT8 = 2,
    NN_TENSOR_FLOAT = 3,
    NN_TENSOR_FLOAT16 = 4,
} tensor_datatype_e;

static const int g_max_num_dims = 4;


typedef struct
{
    uint32_t index;
    uint32_t n_dims;
    uint32_t dims[g_max_num_dims];
    uint32_t n_elems;
    uint32_t size;
    tensor_datatype_e type;
    tensor_layout_e layout;
    int32_t zp;
    float scale;
} tensor_attr_s;

typedef struct
{
    tensor_attr_s attr;     // 属性，来源于rknn_tensor_attr_s
    void *data;             // 数据指针
} tensor_data_s;


typedef struct _nn_object_s {
    float x;
    float y;
    float w;
    float h;
    float score;
    int class_id;
} nn_object_s;

struct Detection
{
    int class_id{0};
    std::string className{};
    float confidence{0.0};
    cv::Scalar color{};
    cv::Rect box{};
};


static size_t nn_tensor_type_to_size(tensor_datatype_e type)
{
    switch (type)
    {
    case NN_TENSOR_INT8:
        return sizeof(int8_t);
    case NN_TENSOR_UINT8:
        return sizeof(uint8_t);
    case NN_TENSOR_FLOAT:
        return sizeof(float);
    case NN_TENSOR_FLOAT16:
        return sizeof(uint16_t);
    default:
        printf("unsupported tensor type\n");
        exit(-1);
    }
}

static void nn_tensor_attr_to_cvimg_input_data(const tensor_attr_s &attr, tensor_data_s &data)
{
    if (attr.n_dims != 4)
    {
        printf("unsupported input dims\n");
        exit(-1);
    }
    data.attr.n_dims = attr.n_dims;
    data.attr.index = 0;
    data.attr.type = NN_TENSOR_UINT8;
    data.attr.layout = NN_TENSOR_NHWC;
    if (attr.layout == NN_TENSOR_NCHW)
    {
        data.attr.dims[0] = attr.dims[0];
        data.attr.dims[1] = attr.dims[2];
        data.attr.dims[2] = attr.dims[3];
        data.attr.dims[3] = attr.dims[1];
    }
    else if (attr.layout == NN_TENSOR_NHWC)
    {
        data.attr.dims[0] = attr.dims[0];
        data.attr.dims[1] = attr.dims[1];
        data.attr.dims[2] = attr.dims[2];
        data.attr.dims[3] = attr.dims[3];
    }
    else
    {
        printf("unsupported input layout\n");
        exit(-1);
    }202420
    // multiply all dims
    data.attr.n_elems = data.attr.dims[0] * data.attr.dims[1] *
                        data.attr.dims[2] * data.attr.dims[3];
    data.attr.size = data.attr.n_elems * sizeof(uint8_t);
}

#endif // RK3588_DEMO_DATATYPE_H
