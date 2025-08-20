/*-------------------------------------------
                Includes
-------------------------------------------*/
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/time.h>
#include <opencv2/opencv.hpp>
#include <sys/stat.h>  // For mkdir
#include "im2d.h"
#include "rga.h"
#include "RgaUtils.h"

#include "rknn_api.h"

#include "rkmedia/utils/mpp_decoder.h"
#include "rkmedia/utils/mpp_encoder.h"

#include "mk_mediakit.h"
#include "task/yolov8_engine.h"
#include "draw/cv_draw.h"
#include "task/yolov8_thread_pool.h"

#define OUT_VIDEO_PATH "out.h264"


struct rknn_zl_app_context_t {
    MppDecoder *decoder;                    // MPP解码器
    mk_player player;                       // 播放器
    mk_media media;                         // 媒体服务
    uint64_t pts;                           // 显示时间戳
    uint64_t dts;                           // 解码时间戳
    int test_id;
    std::queue<cv::Mat> frame_buffer;       // 任务队列
    std::mutex buffer_mutex;                // 锁
    std::condition_variable buffer_cv;      // 条件变量
    rknn_zl_app_context_t() : decoder(nullptr), player(0), media(0), pts(0), dts(0), test_id(0) {}
};

static Yolov8ThreadPool *yolov8_thread_pool = nullptr; 
std::map<int, rknn_zl_app_context_t*> camera_context_map;
std::mutex context_map_mutex;
std::map<int, int> job_cnt_map;
std::mutex job_cnt_mutex;                  

void release_media(mk_media *ptr)
{
    if (ptr && *ptr)
    {
        mk_media_release(*ptr);
        *ptr = NULL;
    }
}

void release_pusher(mk_pusher *ptr)
{
    if (ptr && *ptr)
    {
        mk_pusher_release(*ptr);
        *ptr = NULL;
    }
}

// 解码后的数据回调函数
void mpp_decoder_frame_callback(void *userdata, int width_stride, int height_stride, int width, int height, int format, int fd, void *data, int input_id)
{
    rknn_zl_app_context_t *ctx = (rknn_zl_app_context_t *)userdata;  
    rga_buffer_t origin;
    
    origin = wrapbuffer_fd(fd, width, height, RK_FORMAT_YCbCr_420_SP, width_stride, height_stride);
    cv::Mat origin_mat = cv::Mat::zeros(height, width, CV_8UC3);
    rga_buffer_t rgb_img = wrapbuffer_virtualaddr((void *)origin_mat.data, width, height, RK_FORMAT_RGB_888);
    imcopy(origin, rgb_img);
    {
        std::lock_guard<std::mutex> lock(ctx->buffer_mutex);
        if (ctx->frame_buffer.size() >= 30) 
        {       
            ctx->frame_buffer.pop();                              // 丢弃旧帧
        }
        ctx->frame_buffer.emplace(origin_mat);                    // 存储新帧
    }
    // std::cout << "===frame_buffer ctx: " << ctx << "===frame_buffer size: " << ctx->frame_buffer.size() << std::endl;
}

void API_CALL on_track_frame_out(void *user_data, mk_frame frame) 
{
    rknn_zl_app_context_t *ctx = (rknn_zl_app_context_t *) user_data;
    const char *data = mk_frame_get_data(frame);    
    ctx->dts = mk_frame_get_dts(frame);             
    ctx->pts = mk_frame_get_pts(frame);           
    size_t size = mk_frame_get_data_size(frame);    
    ctx->decoder->Decode((uint8_t *)data, size, 0); // 调用decoder解码器进行解码
}


void API_CALL on_mk_play_event_func(void *user_data, int err_code, const char *err_msg, mk_track tracks[], int track_count) 
{
    rknn_zl_app_context_t *ctx = (rknn_zl_app_context_t *) user_data;
    
    if (err_code == 0) 
    {
        log_debug("play success!");
        int i;
        for (i = 0; i < track_count; ++i) 
        {
            if (mk_track_is_video(tracks[i]))
            {
                mk_track_add_delegate(tracks[i], on_track_frame_out, user_data);
            }
        }
    } 
    else 
    {
        log_warn("play failed: %d %s", err_code, err_msg);
    }
}

void start_processing_async(int camera_id, const char *url, int video_type)
{
    rknn_zl_app_context_t app_ctx;
    {
        std::lock_guard<std::mutex> lock(context_map_mutex);
        camera_context_map[camera_id] = &app_ctx;
    }

    MppDecoder* decoder = new MppDecoder();
    decoder->Init(video_type, 30, &app_ctx, camera_id);
    decoder->SetCallback(mpp_decoder_frame_callback);
    app_ctx.decoder = decoder;
    mk_player player = mk_player_create(); 

    
    mk_player_set_on_result(player, on_mk_play_event_func, &app_ctx);       // 设置播放器正常播放/播放中断的回调函数
    mk_player_set_on_shutdown(player, on_mk_play_event_func, &app_ctx);
    mk_player_play(player, url);                                            // 开始播放 url

    while(true)
    {
        std::this_thread::sleep_for(std::chrono::seconds(10));   
    }
}


rknn_zl_app_context_t* get_context_by_camera_id(int camera_id)
{
    std::lock_guard<std::mutex> lock(context_map_mutex);
    auto it = camera_context_map.find(camera_id);
    if (it != camera_context_map.end())
    {
        return it->second;
    }
    return nullptr;
}

void inference(int camera_id)
{
    while (true)
    {
        cv::Mat frame;
        rknn_zl_app_context_t *ctx = get_context_by_camera_id(camera_id);
        {
            std::unique_lock<std::mutex> lock(ctx->buffer_mutex);
            
            if (ctx->buffer_cv.wait_for(lock, std::chrono::milliseconds(1), [ctx] {
                return !ctx->frame_buffer.empty();
            }))
            {
                frame = ctx->frame_buffer.front();
                ctx->frame_buffer.pop();       
            }
            else
            {
                if (ctx->frame_buffer.empty())
                {
                    continue;
                }
            }
        }
        yolov8_thread_pool->submitTask(frame, ctx->decoder->input_id, job_cnt_map[ctx->decoder->input_id]++);   
    }
}

int main()
{
    std::string model_path = "./weights/yolov8n_detect_float.rknn"; // 模型名称
    const char *stream_urls[] = {
        "rtsp://admin:bjfl123456785.@192.168.1.2:554/h264/ch33/main/av_stream",
        "rtsp://admin:bjfl123456785.@192.168.1.2:554/h264/ch33/main/av_stream",
        "rtsp://admin:bjfl123456785.@192.168.1.2:554/h264/ch33/main/av_stream",
        "rtsp://admin:bjfl123456785.@192.168.1.2:554/h264/ch33/main/av_stream"        
    };

    int video_type = 264;                                       // 视频流类型：264/265

    yolov8_thread_pool = new Yolov8ThreadPool();                // 创建线程池
    yolov8_thread_pool->setUp(model_path, 15);                  // 初始化线程池

    mk_config config;
    memset(&config, 0, sizeof(mk_config));
    config.log_mask = LOG_CONSOLE;
    mk_env_init(&config);

    
    // 一个流启动一个地址
    std::thread decode_threads[2];
    for (int i = 0; i < 2; i++)
    {
        decode_threads[i] = std::thread(start_processing_async, i, stream_urls[i], video_type);
        std::this_thread::sleep_for(std::chrono::milliseconds(10));   
    }

    std::thread infer_threads[2];
    for (int i = 0; i < 2; i++)
    {
        infer_threads[i] = std::thread(inference, i);
    }
    
    // 测试需要
    std::this_thread::sleep_for(std::chrono::seconds(10));

    for (int i = 0; i < 2; i++)
    {
        std::cout << "======input_id: " << i << "====== img_result_length: " << yolov8_thread_pool->results[i].size() << std::endl;   
    }
    
    return 0;        
}