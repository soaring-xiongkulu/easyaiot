
#ifndef POSTPROCESS_H
#define POSTPROCESS_H

#include <stdint.h>
#include <vector>

namespace yolo
{
    int GetConvDetectionResult(float **pBlob, std::vector<float> &DetectiontRects);                                                               // 浮点数版本
    int GetConvDetectionResultInt8(int8_t **pBlob, std::vector<int> &qnt_zp, std::vector<float> &qnt_scale, std::vector<float> &DetectiontRects); // int8版本
}

#endif
