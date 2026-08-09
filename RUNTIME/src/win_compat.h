#pragma once

// Phase 1 MSVC scaffolding: minimal POSIX shims for RUNTIME on Windows.
// Review each branch when behavior must match Linux exactly (e.g. mkdir mode bits).

#ifdef _WIN32

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <direct.h>   // _mkdir
#include <process.h>  // _getpid

#include <ctime>

// Windows ignores POSIX mode; sufficient for alert image dirs (0755 intent on Linux).
inline int runtime_mkdir(const char* path, int /*mode*/) {
    return _mkdir(path);
}

inline int runtime_getpid() {
    return static_cast<int>(_getpid());
}

// MSVC thread-safe time helpers (POSIX gmtime_r / localtime_r names kept for call sites).
inline int gmtime_r(const std::time_t* timep, std::tm* result) {
    return gmtime_s(result, timep) == 0 ? 0 : -1;
}

inline int localtime_r(const std::time_t* timep, std::tm* result) {
    return localtime_s(result, timep) == 0 ? 0 : -1;
}

#else  // !_WIN32

#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

inline int runtime_mkdir(const char* path, int mode) {
    return ::mkdir(path, mode);
}

inline int runtime_getpid() {
    return static_cast<int>(::getpid());
}

#endif  // _WIN32
