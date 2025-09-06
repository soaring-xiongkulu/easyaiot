/** 
 * 
 * Copyright©2021 Guangdong LeapFive Technology Limited. All rights reserved. 
 * 
 * This information embodies materials and concepts, which are proprietary and 
 * confidential to Guangdong LeapFive Technology Limited, and is made available 
 * solely pursuant to the terms of a written license agreement, or NDA, or another 
 * written agreement, as applicable, with Guangdong LeapFive Technology Limited 
 * or any of its subsidiaries. 
 * 
 * This information can be used only with the written permission from LeapFive, in 
 * accordance with the terms and conditions stipulated in applicable agreement with 
 * LeapFive, under which the information has been supplied and solely as expressly 
 * permitted for the purpose specified in applicable agreement with LeapFive. 
 * This information is made available exclusively to licensees or parties that have 
 * received express written authorization from LeapFive to download or receive 
 * the information and have agreed to the terms and conditions of applicable 
 * agreement with LeapFive. 
 * IF YOU HAVE NOT RECEIVED SUCH EXPRESS AUTHORIZATION AND AGREED TO APPLICABLE 
 * AGREEMENT WITH LEAPFIVE, YOU MAY NOT DOWNLOAD, INSTALL OR USE THIS INFORMATION. 
 * 
 * The information contained in this file is subject to change without notice and 
 * does not represent a commitment on any part of LeapFive. Unless specifically 
 * agreed otherwise in applicable agreement with LeapFive, LeapFive make no 
 * warranty of any kind with regard to this material, including, but not limited to 
 * implied warranties of merchantability and fitness for a particular purpose 
 * whether arising out of law, custom, conduct or otherwise. 
 * 
 * While the information contained herein is assumed to be accurate, LeapFive 
 * assumes no responsibility for any errors or omissions contained herein, 
 * and assumes no liability for special, direct, indirect or consequential damage, 
 * losses, costs, charges, claims, demands, fees or expenses, of any nature 
 * or kind, which are incurred in connection with the furnishing, performance or 
 * use of this material. 
 * 
 * This file contains proprietary information, which is protected by international 
 * copyright laws. All rights reserved. No part of this file may be reproduced, 
 * photocopied, or translated into another language without the prior written 
 * consent of LeapFive. 
 * 
 */  


#ifndef __AISS_APP_H__
#define __AISS_APP_H__


#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/opencv.hpp>
#include "stdint.h"
#include "stdlib.h"

using namespace cv;
using namespace std;

typedef struct sglib_detection{
	int x; //起点x坐标
    int y; //起点y坐标
	int w; //宽度
	int h; //高度
	int classes; //类别编号
	float prob; //识别精度
} sglib_detection;

typedef struct identify_array{
	int identify_num;
	sglib_detection identify_arr[100];
}identify_array;

typedef struct 
{
	void 	*pUserdata;
	uint32_t userdataSize;
}inferenceUsrParam;


typedef int (*AI_Inference_completeCb)(identify_array *inferenceResult,inferenceUsrParam *pResUsrInfo,void *userdata);

int AI_Init_carInner(uint32_t width,uint32_t height,AI_Inference_completeCb cb, void *contex);
// int AI_AsyncInference_carInner(dma_buffer_t *pYuvDmaBuf,inferenceUsrParam *pInfUsrParam);
int AI_DeInit_carInner();






#endif







