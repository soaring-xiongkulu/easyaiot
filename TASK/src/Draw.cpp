// @author 翱翔的雄库鲁
// @email andywebjava@163.com
// @wechat EasyAIoT2025

#include <iostream>
#include <sstream>
#include <iomanip>
#include "Draw.h"

void DrawDetections(cv::Mat &img, const std::vector<DetectObject> &objects)
{
    const cv::Scalar color(0, 0, 255);
    const int thickness = 2;
    const auto font = cv::FONT_HERSHEY_SIMPLEX;
    const double font_scale = 0.6;

    for (const auto &object : objects)
    {
        const int x1 = object.x1;
        const int y1 = object.y1;
        const int width = object.x2 - x1;
        const int height = object.y2 - y1;

        cv::rectangle(img, cv::Rect(x1, y1, width, height), color, thickness);
        std::ostringstream label_stream;
        label_stream << object.class_name << ":" << std::fixed << std::setprecision(1) << object.class_score;
        const std::string label = label_stream.str();

        int baseline = 0;
        cv::Size text_size = cv::getTextSize(label, font, font_scale, thickness, &baseline);

        const int text_y = std::max(y1, text_size.height + 2);
        const cv::Point text_pos(x1, text_y);

        cv::rectangle(img,
                     cv::Point(x1, text_y - text_size.height - 2),
                     cv::Point(x1 + text_size.width, text_y + baseline),
                     color, cv::FILLED);

        cv::putText(img, label, text_pos, font, font_scale, cv::Scalar(255, 255, 255), thickness);
    }
}