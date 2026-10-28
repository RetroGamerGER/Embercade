#pragma once

#include <cstdio>
#include <fstream>
#include <string>

namespace EmbercadeLaunchNotice
{
enum class Reason { None, ShaderIncompatible, ShaderUnavailable };

inline void clear(const char* path)
{
    if (path && *path)
        std::remove(path);
}

inline Reason consume(const char* path)
{
    if (!path || !*path)
        return Reason::None;
    char message[64] = {};
    bool valid = false;
    {
        std::ifstream input(path);
        valid = bool(input.getline(message, sizeof(message)));
    }
    clear(path);
    if (!valid)
        return Reason::None;
    if (std::string(message) == "shader-incompatible")
        return Reason::ShaderIncompatible;
    if (std::string(message) == "shader-unavailable")
        return Reason::ShaderUnavailable;
    return Reason::None;
}
}
