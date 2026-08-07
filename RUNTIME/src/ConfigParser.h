/*
 * Configuration File Parser
 * Parse INI format config files
 */

#ifndef CONFIG_PARSER_H
#define CONFIG_PARSER_H

#include <string>
#include <map>
#include <vector>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <glog/logging.h>
#include "Config.h"

class ConfigParser {
public:
    ConfigParser() {}
    ~ConfigParser() {}
    
    /**
     * Parse configuration file
     * @param filename Config file path
     * @param config Config struct reference
     * @return true if successful, false if failed
     */
    bool parse(const std::string& filename, Config& config);

private:
    /**
     * Trim leading and trailing whitespace
     */
    std::string trim(const std::string& str);
    
    /**
     * Parse boolean value
     */
    bool parseBool(const std::string& value);
    
    /**
     * Parse integer value
     */
    int parseInt(const std::string& value);
    
    /**
     * Parse float value
     */
    float parseFloat(const std::string& value);
    
    /**
     * Parse alarm region (JSON format)
     */
    bool parseRegion(const std::string& regionJson, std::vector<cv::Point>& points);
};

#endif // CONFIG_PARSER_H
