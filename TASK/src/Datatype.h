// @author 翱翔的雄库鲁
// @email andywebjava@163.com
// @wechat EasyAIoT2025

#ifndef DATATYPE_H
#define DATATYPE_H

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

struct DetectObject
{
    int x1;
    int y1;
    int x2;
    int y2;
    float class_score;
    int class_id;
    std::string class_name;
    bool happen = false;
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
#endif // DATATYPE_H
