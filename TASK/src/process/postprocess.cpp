#include <algorithm>
#include <iostream>

#include "postprocess.h"
#include <string.h>
#include <stdlib.h>

namespace yolo
{
    typedef struct
    {
        float xmin;
        float ymin;
        float xmax;
        float ymax;
        float score;
        int classId;
    } DetectRect;
    static int input_w = 640;
    static int input_h = 640;
    static float objectThreshold = 0.4;
    static float nmsThreshold = 0.25;
    static int headNum = 3;
    static int class_num = 80;
    static int strides[3] = {8, 16, 32};
    static int mapSize[3][2] = {{80, 80}, {40, 40}, {20, 20}};
#define ZQ_MAX(a, b) ((a) > (b) ? (a) : (b))
#define ZQ_MIN(a, b) ((a) < (b) ? (a) : (b))
    static inline float fast_exp(float x)
    {
        // return exp(x);
        union
        {
            uint32_t i;
            float f;
        } v;
        v.i = (12102203.1616540672 * x + 1064807160.56887296);
        return v.f;
    }

    float sigmoid(float x)
    {
        return 1 / (1 + fast_exp(-x));
    }

    static inline float IOU(float XMin1, float YMin1, float XMax1, float YMax1, float XMin2, float YMin2, float XMax2, float YMax2)
    {
        float Inter = 0;
        float Total = 0;
        float XMin = 0;
        float YMin = 0;
        float XMax = 0;
        float YMax = 0;
        float Area1 = 0;
        float Area2 = 0;
        float InterWidth = 0;
        float InterHeight = 0;

        XMin = ZQ_MAX(XMin1, XMin2);
        YMin = ZQ_MAX(YMin1, YMin2);
        XMax = ZQ_MIN(XMax1, XMax2);
        YMax = ZQ_MIN(YMax1, YMax2);

        InterWidth = XMax - XMin;
        InterHeight = YMax - YMin;

        InterWidth = (InterWidth >= 0) ? InterWidth : 0;
        InterHeight = (InterHeight >= 0) ? InterHeight : 0;

        Inter = InterWidth * InterHeight;

        Area1 = (XMax1 - XMin1) * (YMax1 - YMin1);
        Area2 = (XMax2 - XMin2) * (YMax2 - YMin2);

        Total = Area1 + Area2 - Inter;

        return float(Inter) / float(Total);
    }

    static float DeQnt2F32(int8_t qnt, int zp, float scale)
    {
        return ((float)qnt - (float)zp) * scale;
    }

    std::vector<float> GenerateMeshgrid()
    {
        std::vector<float> meshgrid;
        if (headNum == 0)
        {
            printf("=== yolov8 Meshgrid  Generate failed! \n");
            exit(-1);
        }

        for (int index = 0; index < headNum; index++)
        {
            for (int i = 0; i < mapSize[index][0]; i++)
            {
                for (int j = 0; j < mapSize[index][1]; j++)
                {
                    meshgrid.push_back(float(j + 0.5));
                    meshgrid.push_back(float(i + 0.5));
                }
            }
        }    
        return meshgrid;
    }
    // int8版本
    int GetConvDetectionResultInt8(int8_t **pBlob, std::vector<int> &qnt_zp, std::vector<float> &qnt_scale,
                                   std::vector<float> &DetectiontRects)
    {
        
        static auto meshgrid = GenerateMeshgrid();
        int ret = 0;
        
        int gridIndex = -2;
        float xmin = 0, ymin = 0, xmax = 0, ymax = 0;
        float cls_val = 0;
        float cls_max = 0;
        int cls_index = 0;

        int quant_zp_cls = 0, quant_zp_reg = 0;
        float quant_scale_cls = 0, quant_scale_reg = 0;

        DetectRect temp;
        std::vector<DetectRect> detectRects;

        for (int index = 0; index < headNum; index++)
        {
            int8_t *reg = (int8_t *)pBlob[index * 2 + 0];
            int8_t *cls = (int8_t *)pBlob[index * 2 + 1];

            quant_zp_reg = qnt_zp[index * 2 + 0];
            quant_zp_cls = qnt_zp[index * 2 + 1];

            quant_scale_reg = qnt_scale[index * 2 + 0];
            quant_scale_cls = qnt_scale[index * 2 + 1];

            for (int h = 0; h < mapSize[index][0]; h++)
            {
                for (int w = 0; w < mapSize[index][1]; w++)
                {
                    gridIndex += 2;

                    for (int cl = 0; cl < class_num; cl++)
                    {
                        cls_val = sigmoid(
                            DeQnt2F32(cls[cl * mapSize[index][0] * mapSize[index][1] + h * mapSize[index][1] + w],
                                      quant_zp_cls, quant_scale_cls));

                        if (0 == cl)
                        {
                            cls_max = cls_val;
                            cls_index = cl;
                        }
                        else
                        {
                            if (cls_val > cls_max)
                            {
                                cls_max = cls_val;
                                cls_index = cl;
                            }
                        }
                    }

                    if (cls_max > objectThreshold)
                    {
                        xmin = (meshgrid[gridIndex + 0] -
                                DeQnt2F32(reg[0 * mapSize[index][0] * mapSize[index][1] + h * mapSize[index][1] + w],
                                          quant_zp_reg, quant_scale_reg)) *
                               strides[index];
                        ymin = (meshgrid[gridIndex + 1] -
                                DeQnt2F32(reg[1 * mapSize[index][0] * mapSize[index][1] + h * mapSize[index][1] + w],
                                          quant_zp_reg, quant_scale_reg)) *
                               strides[index];
                        xmax = (meshgrid[gridIndex + 0] +
                                DeQnt2F32(reg[2 * mapSize[index][0] * mapSize[index][1] + h * mapSize[index][1] + w],
                                          quant_zp_reg, quant_scale_reg)) *
                               strides[index];
                        ymax = (meshgrid[gridIndex + 1] +
                                DeQnt2F32(reg[3 * mapSize[index][0] * mapSize[index][1] + h * mapSize[index][1] + w],
                                          quant_zp_reg, quant_scale_reg)) *
                               strides[index];

                        xmin = xmin > 0 ? xmin : 0;
                        ymin = ymin > 0 ? ymin : 0;
                        xmax = xmax < input_w ? xmax : input_w;
                        ymax = ymax < input_h ? ymax : input_h;

                        if (xmin >= 0 && ymin >= 0 && xmax <= input_w && ymax <= input_h)
                        {
                            temp.xmin = xmin / input_w;
                            temp.ymin = ymin / input_h;
                            temp.xmax = xmax / input_w;
                            temp.ymax = ymax / input_h;
                            temp.classId = cls_index;
                            temp.score = cls_max;
                            detectRects.push_back(temp);
                        }
                    }
                }
            }
        }

        std::sort(detectRects.begin(), detectRects.end(),
                  [](DetectRect &Rect1, DetectRect &Rect2) -> bool
                  { return (Rect1.score > Rect2.score); });

        // printf("NMS Before num :%ld\n", detectRects.size());
        for (int i = 0; i < detectRects.size(); ++i)
        {
            float xmin1 = detectRects[i].xmin;
            float ymin1 = detectRects[i].ymin;
            float xmax1 = detectRects[i].xmax;
            float ymax1 = detectRects[i].ymax;
            int classId = detectRects[i].classId;
            float score = detectRects[i].score;

            if (classId != -1)
            {
                // 将检测结果按照classId、score、xmin1、ymin1、xmax1、ymax1 的格式存放在vector<float>中
                DetectiontRects.push_back(float(classId));
                DetectiontRects.push_back(float(score));
                DetectiontRects.push_back(float(xmin1));
                DetectiontRects.push_back(float(ymin1));
                DetectiontRects.push_back(float(xmax1));
                DetectiontRects.push_back(float(ymax1));

                for (int j = i + 1; j < detectRects.size(); ++j)
                {
                    float xmin2 = detectRects[j].xmin;
                    float ymin2 = detectRects[j].ymin;
                    float xmax2 = detectRects[j].xmax;
                    float ymax2 = detectRects[j].ymax;
                    float iou = IOU(xmin1, ymin1, xmax1, ymax1, xmin2, ymin2, xmax2, ymax2);
                    if (iou > nmsThreshold)
                    {
                        detectRects[j].classId = -1;
                    }
                }
            }
        }

        return ret;
    }
    // 浮点数版本
    int GetConvDetectionResult(float **pBlob, std::vector<float> &DetectiontRects)
    {
        static auto meshgrid = GenerateMeshgrid();
        int ret = 0;

        int gridIndex = -2;
        float xmin = 0, ymin = 0, xmax = 0, ymax = 0;
        float cls_val = 0;
        float cls_max = 0;
        int cls_index = 0;

        DetectRect temp;
        std::vector<DetectRect> detectRects;
        for (int index = 0; index < headNum; index++)
        {
            float *reg = (float *)pBlob[index * 2 + 0];
            float *cls = (float *)pBlob[index * 2 + 1];

            for (int h = 0; h < mapSize[index][0]; h++)
            {
                for (int w = 0; w < mapSize[index][1]; w++)
                {
                    gridIndex += 2;

                    for (int cl = 0; cl < class_num; cl++)
                    {
                        // 获取第 h * w 个网格上得分最高的index
                        cls_val = sigmoid(
                            cls[cl * mapSize[index][0] * mapSize[index][1] + h * mapSize[index][1] + w]);

                        if (0 == cl)
                        {
                            cls_max = cls_val;
                            cls_index = cl;
                        }
                        else
                        {
                            if (cls_val > cls_max)
                            {
                                cls_max = cls_val;
                                cls_index = cl;
                            }
                        }
                    }
                    // 如果第 h * w 个网格上的最高得分大于设定阈值，则计算bbox
                    if (cls_max > objectThreshold)
                    {
                        xmin = (meshgrid[gridIndex + 0] -
                                reg[0 * mapSize[index][0] * mapSize[index][1] + h * mapSize[index][1] + w]) *
                               strides[index];
                        ymin = (meshgrid[gridIndex + 1] -
                                reg[1 * mapSize[index][0] * mapSize[index][1] + h * mapSize[index][1] + w]) *
                               strides[index];
                        xmax = (meshgrid[gridIndex + 0] +
                                reg[2 * mapSize[index][0] * mapSize[index][1] + h * mapSize[index][1] + w]) *
                               strides[index];
                        ymax = (meshgrid[gridIndex + 1] +
                                reg[3 * mapSize[index][0] * mapSize[index][1] + h * mapSize[index][1] + w]) *
                               strides[index];

                        xmin = xmin > 0 ? xmin : 0;
                        ymin = ymin > 0 ? ymin : 0;
                        xmax = xmax < input_w ? xmax : input_w;
                        ymax = ymax < input_h ? ymax : input_h;

                        if (xmin >= 0 && ymin >= 0 && xmax <= input_w && ymax <= input_h)
                        {
                            temp.xmin = xmin / input_w;
                            temp.ymin = ymin / input_h;
                            temp.xmax = xmax / input_w;
                            temp.ymax = ymax / input_h;
                            temp.classId = cls_index;
                            temp.score = cls_max;
                            detectRects.push_back(temp);
                        }
                    }
                }
            }
        }

        std::sort(detectRects.begin(), detectRects.end(),
                  [](DetectRect &Rect1, DetectRect &Rect2) -> bool
                  { return (Rect1.score > Rect2.score); });

        // printf("NMS Before num :%ld\n", detectRects.size());
        for (int i = 0; i < detectRects.size(); ++i)
        {
            float xmin1 = detectRects[i].xmin;
            float ymin1 = detectRects[i].ymin;
            float xmax1 = detectRects[i].xmax;
            float ymax1 = detectRects[i].ymax;
            int classId = detectRects[i].classId;
            float score = detectRects[i].score;

            if (classId != -1)
            {
                // 将检测结果按照classId、score、xmin1、ymin1、xmax1、ymax1 的格式存放在vector<float>中
                DetectiontRects.push_back(float(classId));
                DetectiontRects.push_back(float(score));
                DetectiontRects.push_back(float(xmin1));
                DetectiontRects.push_back(float(ymin1));
                DetectiontRects.push_back(float(xmax1));
                DetectiontRects.push_back(float(ymax1));

                for (int j = i + 1; j < detectRects.size(); ++j)
                {
                    float xmin2 = detectRects[j].xmin;
                    float ymin2 = detectRects[j].ymin;
                    float xmax2 = detectRects[j].xmax;
                    float ymax2 = detectRects[j].ymax;
                    float iou = IOU(xmin1, ymin1, xmax1, ymax1, xmin2, ymin2, xmax2, ymax2);
                    if (iou > nmsThreshold)
                    {
                        detectRects[j].classId = -1;
                    }
                }
            }
        }
        return ret;
    }

}