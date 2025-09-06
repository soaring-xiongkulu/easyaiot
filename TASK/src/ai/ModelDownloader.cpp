#include "ModelDownloader.h"
#include <curl/curl.h>
#include <fstream>
#include <iostream>

namespace {
size_t writeData(void* ptr, size_t size, size_t nmemb, FILE* stream) {
    size_t written = fwrite(ptr, size, nmemb, stream);
    return written;
}
} // namespace

ModelDownloader::ModelDownloader() {
    curl_global_init(CURL_GLOBAL_DEFAULT);
}

ModelDownloader::~ModelDownloader() {
    curl_global_cleanup();
}

bool ModelDownloader::downloadFile(const std::string& url, const std::string& local_path) {
    CURL* curl;
    FILE* fp;
    CURLcode res;

    curl = curl_easy_init();
    if (!curl) {
        std::cerr << "Failed to initialize CURL" << std::endl;
        return false;
    }

    fp = fopen(local_path.c_str(), "wb");
    if (!fp) {
        std::cerr << "Failed to open file for writing: " << local_path << std::endl;
        curl_easy_cleanup(curl);
        return false;
    }

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeData);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, fp);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);

    res = curl_easy_perform(curl);
    fclose(fp);

    if (res != CURLE_OK) {
        std::cerr << "Download failed: " << curl_easy_strerror(res) << std::endl;
        curl_easy_cleanup(curl);
        return false;
    }

    long response_code;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
    curl_easy_cleanup(curl);

    if (response_code != 200) {
        std::cerr << "HTTP response code: " << response_code << std::endl;
        return false;
    }

    std::cout << "Download completed: " << url << " -> " << local_path << std::endl;
    return true;
}

bool ModelDownloader::downloadModel(const std::string& model_id,
                                  const std::string& model_url,
                                  const std::string& local_path) {
    // Create directory if it doesn't exist
    std::filesystem::path path_obj(local_path);
    std::filesystem::create_directories(path_obj.parent_path());

    return downloadFile(model_url, local_path);
}