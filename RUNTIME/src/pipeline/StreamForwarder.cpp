#include "pipeline/StreamForwarder.h"

#include <cerrno>
#include <chrono>
#include <cstdlib>
#include <string>
#include <thread>
#include <vector>

#include <fcntl.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#include <glog/logging.h>

namespace runtime {
namespace {

constexpr int kReconnectDelayMs = 2000;

void logAvError(const char* tag, int ret) {
    char errbuf[AV_ERROR_MAX_STRING_SIZE];
    av_strerror(ret, errbuf, sizeof(errbuf));
    LOG(ERROR) << tag << ": " << errbuf;
}

bool isRtspUrl(const std::string& url) {
    return url.rfind("rtsp://", 0) == 0 || url.rfind("rtsps://", 0) == 0;
}

bool isRtmpUrl(const std::string& url) {
    return url.rfind("rtmp://", 0) == 0 || url.rfind("rtmps://", 0) == 0;
}

std::string findFfmpegBinary() {
    if (const char* explicitPath = std::getenv("STREAM_FORWARD_FFMPEG")) {
        if (explicitPath[0] != '\0' && access(explicitPath, X_OK) == 0) {
            return explicitPath;
        }
    }
    if (const char* conda = std::getenv("CONDA_PREFIX")) {
        std::string cand = std::string(conda) + "/bin/ffmpeg";
        if (access(cand.c_str(), X_OK) == 0) {
            return cand;
        }
    }
    if (access("/usr/bin/ffmpeg", X_OK) == 0) {
        return "/usr/bin/ffmpeg";
    }
    return "ffmpeg";
}

bool preferFfmpegRelay(const std::string& rtmpUrl) {
    // Local file remux via libav is fine; RTMP publish to SRS for some NVR
    // bitstreams is more reliable through the same ffmpeg CLI path VIDEO uses.
    if (!isRtmpUrl(rtmpUrl)) {
        return false;
    }
    const char* mode = std::getenv("STREAM_FORWARD_RELAY_MODE");
    if (mode && mode[0] != '\0') {
        std::string m(mode);
        if (m == "libav" || m == "api" || m == "remux") {
            return false;
        }
        if (m == "ffmpeg" || m == "cli" || m == "native") {
            return true;
        }
    }
    return true;
}

std::string findFfprobeBinary() {
    const std::string ffmpeg = findFfmpegBinary();
    if (ffmpeg.size() >= 6 && ffmpeg.compare(ffmpeg.size() - 6, 6, "ffmpeg") == 0) {
        std::string probe = ffmpeg.substr(0, ffmpeg.size() - 6) + "ffprobe";
        if (access(probe.c_str(), X_OK) == 0) {
            return probe;
        }
    }
    if (access("/usr/bin/ffprobe", X_OK) == 0) {
        return "/usr/bin/ffprobe";
    }
    return "ffprobe";
}

bool envTruthy(const char* name, bool defaultValue) {
    const char* v = std::getenv(name);
    if (!v || v[0] == '\0') {
        return defaultValue;
    }
    std::string s(v);
    for (char& c : s) {
        if (c >= 'A' && c <= 'Z') {
            c = static_cast<char>(c - 'A' + 'a');
        }
    }
    if (s == "0" || s == "false" || s == "no" || s == "off") {
        return false;
    }
    if (s == "1" || s == "true" || s == "yes" || s == "on") {
        return true;
    }
    return defaultValue;
}

bool isH264CodecName(const std::string& codec) {
    return codec == "h264" || codec == "avc" || codec == "avc1";
}

std::string probeInputVideoCodec(const std::string& inputUrl) {
    const std::string ffprobe = findFfprobeBinary();
    const char* probeEnv = std::getenv("STREAM_FORWARD_PROBESIZE");
    const char* analyzeEnv = std::getenv("STREAM_FORWARD_ANALYZEDURATION");
    const char* probesize = (probeEnv && *probeEnv) ? probeEnv : "3000000";
    const char* analyzeduration = (analyzeEnv && *analyzeEnv) ? analyzeEnv : "3000000";

    int pipefd[2];
    if (pipe(pipefd) != 0) {
        return {};
    }
    pid_t pid = fork();
    if (pid < 0) {
        close(pipefd[0]);
        close(pipefd[1]);
        return {};
    }
    if (pid == 0) {
        close(pipefd[0]);
        dup2(pipefd[1], STDOUT_FILENO);
        close(pipefd[1]);
        int devnull = open("/dev/null", O_WRONLY);
        if (devnull >= 0) {
            dup2(devnull, STDERR_FILENO);
            close(devnull);
        }
        clearenv();
        setenv("PATH", "/usr/bin:/bin", 1);
        execlp(
            ffprobe.c_str(),
            ffprobe.c_str(),
            "-hide_banner",
            "-loglevel", "error",
            "-rtsp_transport", "tcp",
            "-analyzeduration", analyzeduration,
            "-probesize", probesize,
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            inputUrl.c_str(),
            static_cast<char*>(nullptr));
        _exit(127);
    }
    close(pipefd[1]);
    char buf[128];
    std::string out;
    ssize_t n = 0;
    while ((n = read(pipefd[0], buf, sizeof(buf))) > 0) {
        out.append(buf, static_cast<size_t>(n));
        if (out.size() > 64) {
            break;
        }
    }
    close(pipefd[0]);
    int status = 0;
    waitpid(pid, &status, 0);
    // trim
    while (!out.empty() && (out.back() == '\n' || out.back() == '\r' || out.back() == ' ')) {
        out.pop_back();
    }
    for (char& c : out) {
        if (c >= 'A' && c <= 'Z') {
            c = static_cast<char>(c - 'A' + 'a');
        }
    }
    return out;
}

bool shouldTranscodeToH264(const std::string& inputUrl) {
    if (!envTruthy("STREAM_FORWARD_VIDEO_COPY", true)) {
        return true;
    }
    const std::string codec = probeInputVideoCodec(inputUrl);
    if (codec.empty()) {
        LOG(WARNING) << "[FORWARD] codec probe failed, try copy first";
        return false;
    }
    if (isH264CodecName(codec)) {
        LOG(INFO) << "[FORWARD] source codec=" << codec << " use copy";
        return false;
    }
    LOG(INFO) << "[FORWARD] source codec=" << codec << " auto-transcode to H.264 for Web FLV";
    return true;
}

}  // namespace

StreamForwarder::StreamForwarder(const Config& config, PipelineMetrics* metrics)
    : config_(config), metrics_(metrics) {}

StreamForwarder::~StreamForwarder() {
    stop();
    join();
    closeAll();
}

void StreamForwarder::start() {
    if (running_.exchange(true)) {
        return;
    }
    thread_ = std::thread(&StreamForwarder::forwardLoop, this);
}

void StreamForwarder::stop() {
    running_.store(false);
}

void StreamForwarder::join() {
    if (thread_.joinable()) {
        thread_.join();
    }
}

void StreamForwarder::closeAll() {
    if (outCtx_) {
        if (outCtx_->pb) {
            av_write_trailer(outCtx_);
        }
        if (!(outCtx_->oformat->flags & AVFMT_NOFILE) && outCtx_->pb) {
            avio_closep(&outCtx_->pb);
        }
        avformat_free_context(outCtx_);
        outCtx_ = nullptr;
    }
    if (inCtx_) {
        avformat_close_input(&inCtx_);
        inCtx_ = nullptr;
    }
    videoInIndex_ = -1;
    videoOutIndex_ = -1;
}

bool StreamForwarder::openInput() {
    if (inCtx_) {
        avformat_close_input(&inCtx_);
        inCtx_ = nullptr;
    }

    inCtx_ = avformat_alloc_context();
    if (!inCtx_) {
        LOG(ERROR) << "[FORWARD] Failed to allocate input context";
        return false;
    }

    // Align with VIDEO stream_forward defaults (STREAM_FORWARD_PROBESIZE /
    // ANALYZEDURATION). Tiny probesize + analyzeduration=0 often leaves
    // incomplete H.264 extradata; FLV/RTMP then fails SRS demux ("not annexb").
    const char* probeEnv = std::getenv("STREAM_FORWARD_PROBESIZE");
    const char* analyzeEnv = std::getenv("STREAM_FORWARD_ANALYZEDURATION");
    const char* probesize = (probeEnv && *probeEnv) ? probeEnv : "2000000";
    const char* analyzeduration = (analyzeEnv && *analyzeEnv) ? analyzeEnv : "2000000";

    AVDictionary* fmtOptions = nullptr;
    const std::string& openUrl = config_.rtspUrl;
    if (isRtspUrl(openUrl)) {
        // Keep RTSP options conservative: nobuffer/low_delay can drop SPS/PPS
        // packets and make FLV/RTMP copy fail SRS demux ("not annexb").
        av_dict_set(&fmtOptions, "rtsp_transport", "tcp", 0);
        av_dict_set(&fmtOptions, "stimeout", "5000000", 0);
        av_dict_set(&fmtOptions, "rw_timeout", "5000000", 0);
        av_dict_set(&fmtOptions, "max_delay", "500000", 0);
        av_dict_set(&fmtOptions, "probesize", probesize, 0);
        av_dict_set(&fmtOptions, "analyzeduration", analyzeduration, 0);
    } else if (isRtmpUrl(openUrl)) {
        av_dict_set(&fmtOptions, "rtmp_live", "live", 0);
    }

    int ret = avformat_open_input(&inCtx_, openUrl.c_str(), nullptr, &fmtOptions);
    av_dict_free(&fmtOptions);
    if (ret < 0) {
        logAvError("[FORWARD] avformat_open_input failed", ret);
        return false;
    }

    AVDictionary* probeOptions = nullptr;
    if (isRtspUrl(openUrl)) {
        av_dict_set(&probeOptions, "probesize", probesize, 0);
        av_dict_set(&probeOptions, "analyzeduration", analyzeduration, 0);
    }
    ret = avformat_find_stream_info(inCtx_, &probeOptions);
    av_dict_free(&probeOptions);
    if (ret < 0) {
        logAvError("[FORWARD] avformat_find_stream_info failed", ret);
        return false;
    }

    videoInIndex_ = av_find_best_stream(inCtx_, AVMEDIA_TYPE_VIDEO, -1, -1, nullptr, 0);
    if (videoInIndex_ < 0) {
        LOG(ERROR) << "[FORWARD] No video stream found in " << openUrl;
        return false;
    }

    AVStream* inStream = inCtx_->streams[videoInIndex_];
    const char* codecName = avcodec_get_name(inStream->codecpar->codec_id);
    LOG(INFO) << "[FORWARD] Input ready: " << openUrl
              << " video=" << inStream->codecpar->width << "x" << inStream->codecpar->height
              << " codec=" << (codecName ? codecName : "unknown")
              << " extradata=" << inStream->codecpar->extradata_size << "B";
    return true;
}

bool StreamForwarder::openOutput() {
    if (outCtx_) {
        if (outCtx_->pb) {
            av_write_trailer(outCtx_);
        }
        if (!(outCtx_->oformat->flags & AVFMT_NOFILE) && outCtx_->pb) {
            avio_closep(&outCtx_->pb);
        }
        avformat_free_context(outCtx_);
        outCtx_ = nullptr;
    }

    int ret = avformat_alloc_output_context2(&outCtx_, nullptr, "flv", config_.rtmpUrl.c_str());
    if (ret < 0 || !outCtx_) {
        logAvError("[FORWARD] avformat_alloc_output_context2 failed", ret);
        return false;
    }

    AVStream* inStream = inCtx_->streams[videoInIndex_];
    AVStream* outStream = avformat_new_stream(outCtx_, nullptr);
    if (!outStream) {
        LOG(ERROR) << "[FORWARD] avformat_new_stream failed";
        return false;
    }

    ret = avcodec_parameters_copy(outStream->codecpar, inStream->codecpar);
    if (ret < 0) {
        logAvError("[FORWARD] avcodec_parameters_copy failed", ret);
        return false;
    }
    outStream->codecpar->codec_tag = 0;
    // FLV/RTMP expects a stable 1kHz time base for live publish.
    outStream->time_base = AVRational{1, 1000};
    videoOutIndex_ = outStream->index;

#ifdef AVFMT_FLAG_AUTO_BSF
    outCtx_->flags |= AVFMT_FLAG_AUTO_BSF;
#endif

    if (!(outCtx_->oformat->flags & AVFMT_NOFILE)) {
        // Let FFmpeg open the URL (matches CLI remux). Custom rtmp_* options
        // via avio_open2 have been observed to break SRS publish for some NVR
        // bitstreams while local .flv remux still succeeds.
        ret = avio_open(&outCtx_->pb, config_.rtmpUrl.c_str(), AVIO_FLAG_WRITE);
        if (ret < 0) {
            logAvError("[FORWARD] avio_open failed", ret);
            return false;
        }
    }

    ret = avformat_write_header(outCtx_, nullptr);
    if (ret < 0) {
        logAvError("[FORWARD] avformat_write_header failed", ret);
        return false;
    }

    LOG(INFO) << "[FORWARD] Output ready: " << config_.rtmpUrl
              << " mode=copy extradata=" << outStream->codecpar->extradata_size << "B";
    return true;
}

bool StreamForwarder::remuxSession() {
    if (!openInput()) {
        return false;
    }
    if (!openOutput()) {
        closeAll();
        return false;
    }

    AVPacket* pkt = av_packet_alloc();
    if (!pkt) {
        LOG(ERROR) << "[FORWARD] av_packet_alloc failed";
        closeAll();
        return false;
    }

    bool startedOnKey = false;
    while (running_.load()) {
        int ret = av_read_frame(inCtx_, pkt);
        if (ret < 0) {
            if (ret == AVERROR_EOF) {
                LOG(INFO) << "[FORWARD] Input EOF";
            } else {
                logAvError("[FORWARD] av_read_frame failed", ret);
            }
            break;
        }

        if (pkt->stream_index != videoInIndex_) {
            av_packet_unref(pkt);
            continue;
        }

        // Start on IDR so FLV sequence header + first NALU are consistent.
        if (!startedOnKey) {
            if (!(pkt->flags & AV_PKT_FLAG_KEY)) {
                av_packet_unref(pkt);
                continue;
            }
            startedOnKey = true;
            LOG(INFO) << "[FORWARD] First keyframe size=" << pkt->size;
        }

        if (metrics_) {
            metrics_->packetsIn.fetch_add(1, std::memory_order_relaxed);
        }
        packetsRemuxed_.fetch_add(1, std::memory_order_relaxed);

        AVStream* inStream = inCtx_->streams[videoInIndex_];
        AVStream* outStream = outCtx_->streams[videoOutIndex_];
        if (pkt->dts == AV_NOPTS_VALUE && pkt->pts != AV_NOPTS_VALUE) {
            pkt->dts = pkt->pts;
        }
        av_packet_rescale_ts(pkt, inStream->time_base, outStream->time_base);
        pkt->stream_index = videoOutIndex_;
        pkt->pos = -1;

        ret = av_interleaved_write_frame(outCtx_, pkt);
        av_packet_unref(pkt);
        if (ret < 0) {
            logAvError("[FORWARD] av_interleaved_write_frame failed", ret);
            break;
        }
    }

    av_packet_free(&pkt);
    closeAll();
    return true;
}

bool StreamForwarder::ffmpegRelaySession() {
    const std::string ffmpegBin = findFfmpegBinary();
    const char* probeEnv = std::getenv("STREAM_FORWARD_PROBESIZE");
    const char* analyzeEnv = std::getenv("STREAM_FORWARD_ANALYZEDURATION");
    const char* probesize = (probeEnv && *probeEnv) ? probeEnv : "2000000";
    const char* analyzeduration = (analyzeEnv && *analyzeEnv) ? analyzeEnv : "2000000";
    const bool transcode = shouldTranscodeToH264(config_.rtspUrl);

    std::vector<std::string> args = {
        ffmpegBin,
        "-hide_banner",
        "-nostdin",
        "-loglevel", "warning",
        "-rtsp_transport", "tcp",
        "-analyzeduration", analyzeduration,
        "-probesize", probesize,
        "-i", config_.rtspUrl,
        "-an",
    };
    if (transcode) {
        const char* bitrate = std::getenv("STREAM_FORWARD_TRANSCODE_BITRATE");
        if (!bitrate || !*bitrate) {
            bitrate = std::getenv("FFMPEG_VIDEO_BITRATE");
        }
        if (!bitrate || !*bitrate) {
            bitrate = "2000k";
        }
        const char* preset = std::getenv("FFMPEG_PRESET");
        if (!preset || !*preset) {
            preset = "veryfast";
        }
        const char* gop = std::getenv("FFMPEG_GOP_SIZE");
        if (!gop || !*gop) {
            gop = "50";
        }
        const char* fps = std::getenv("VIEW_OUTPUT_FPS");
        if (!fps || !*fps) {
            fps = std::getenv("VIEW_SOURCE_FPS");
        }
        if (!fps || !*fps) {
            fps = "25";
        }
        args.insert(args.end(), {
            "-c:v", "libx264",
            "-b:v", bitrate,
            "-preset", preset,
            "-tune", "zerolatency",
            "-profile:v", "main",
            "-g", gop,
            "-bf", "0",
            "-pix_fmt", "yuv420p",
            "-r", fps,
        });
    } else {
        args.insert(args.end(), {"-c:v", "copy"});
    }
    args.insert(args.end(), {
        "-avoid_negative_ts", "make_zero",
        "-muxdelay", "0",
        "-muxpreload", "0",
        "-f", "flv",
        config_.rtmpUrl,
    });

    std::vector<char*> argv;
    argv.reserve(args.size() + 1);
    for (auto& a : args) {
        argv.push_back(a.data());
    }
    argv.push_back(nullptr);

    LOG(INFO) << "[FORWARD] Starting ffmpeg CLI "
              << (transcode ? "transcode(H.264)" : "copy") << " relay "
              << config_.rtspUrl << " -> " << config_.rtmpUrl
              << " via " << ffmpegBin;

    pid_t pid = fork();
    if (pid < 0) {
        LOG(ERROR) << "[FORWARD] fork failed errno=" << errno;
        return false;
    }
    if (pid == 0) {
        // Capture ffmpeg stderr before clearing env.
        const char* logPath = std::getenv("STREAM_FORWARD_FFMPEG_LOG");
        if (logPath && logPath[0] != '\0') {
            int fd = open(logPath, O_WRONLY | O_CREAT | O_APPEND, 0644);
            if (fd >= 0) {
                dup2(fd, STDERR_FILENO);
                close(fd);
            }
        }
        // Give system ffmpeg a clean environment. Inheriting RUNTIME's conda
        // LD_LIBRARY_PATH makes /usr/bin/ffmpeg fail when publishing to SRS.
        const bool systemFfmpeg = (ffmpegBin == "/usr/bin/ffmpeg" ||
                                   ffmpegBin == "ffmpeg");
        if (systemFfmpeg) {
            clearenv();
            setenv("PATH", "/usr/bin:/bin", 1);
            setenv("HOME", "/tmp", 1);
        }
        execvp(argv[0], argv.data());
        _exit(127);
    }

    // Parent: wait until stop requested or ffmpeg exits
    int status = 0;
    while (running_.load()) {
        pid_t waited = waitpid(pid, &status, WNOHANG);
        if (waited == pid) {
            if (WIFEXITED(status)) {
                LOG(WARNING) << "[FORWARD] ffmpeg exited code=" << WEXITSTATUS(status);
            } else if (WIFSIGNALED(status)) {
                LOG(WARNING) << "[FORWARD] ffmpeg killed by signal=" << WTERMSIG(status);
            }
            return WIFEXITED(status) && WEXITSTATUS(status) == 0;
        }
        if (waited < 0) {
            LOG(ERROR) << "[FORWARD] waitpid failed errno=" << errno;
            return false;
        }
        if (metrics_) {
            // Heartbeat-style activity so monitors know relay is alive.
            metrics_->packetsIn.fetch_add(1, std::memory_order_relaxed);
        }
        packetsRemuxed_.fetch_add(1, std::memory_order_relaxed);
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }

    // Stop requested: terminate ffmpeg
    kill(pid, SIGTERM);
    for (int i = 0; i < 25; ++i) {
        pid_t waited = waitpid(pid, &status, WNOHANG);
        if (waited == pid) {
            break;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    if (waitpid(pid, &status, WNOHANG) == 0) {
        kill(pid, SIGKILL);
        waitpid(pid, &status, 0);
    }
    LOG(INFO) << "[FORWARD] ffmpeg relay stopped";
    return true;
}

void StreamForwarder::forwardLoop() {
    const bool useFfmpeg = preferFfmpegRelay(config_.rtmpUrl);
    LOG(INFO) << "[FORWARD] Starting copy relay "
              << config_.rtspUrl << " -> " << config_.rtmpUrl
              << (useFfmpeg ? " (ffmpeg CLI)" : " (libav remux)");

    while (running_.load()) {
        const bool ok = useFfmpeg ? ffmpegRelaySession() : remuxSession();
        if (!ok) {
            LOG(WARNING) << "[FORWARD] Session failed, retry in "
                         << kReconnectDelayMs << "ms";
        } else if (!running_.load()) {
            break;
        } else {
            LOG(WARNING) << "[FORWARD] Session ended, reconnect in "
                         << kReconnectDelayMs << "ms";
        }

        for (int i = 0; i < kReconnectDelayMs / 100 && running_.load(); ++i) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }

    closeAll();
    LOG(INFO) << "[FORWARD] Relay stopped, packets=" << packetsRemuxed_.load();
}

}  // namespace runtime
