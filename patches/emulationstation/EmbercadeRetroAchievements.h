#pragma once
// SPDX-License-Identifier: MIT
// Embercade-owned frontend helper. No application/shared Web API credential.
#include <string>
#include <cstdlib>
#include <cerrno>
#include <cstdio>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/random.h>
#include <unistd.h>

namespace EmbercadeRetroAchievements
{
__attribute__((used)) static const char userWebApiBuild[] =
    "EMBERCADE_RETROACHIEVEMENTS_USER_WEB_API_V1";
static const char* const filename = "retroachievements-user.conf";

struct Credentials { std::string user; std::string key; };

inline bool validField(const std::string& value)
{
    if (value.empty() || value.size() > 2048) return false;
    for (unsigned char c : value) if (c < 32 || c == 127) return false;
    return true;
}

inline int ownedDirectory(int parent, const char* name, bool create, bool privateMode)
{
    if (create && mkdirat(parent, name, 0700) != 0 && errno != EEXIST) return -1;
    int fd = openat(parent, name, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0) return -1;
    struct stat st;
    if (fstat(fd, &st) != 0 || st.st_uid != getuid()
        || (st.st_mode & (privateMode ? 0077 : 0022)))
    { close(fd); errno = EACCES; return -1; }
    return fd;
}

inline int directory(bool create)
{
    const char* base = std::getenv("XDG_CONFIG_HOME");
    if (!base || base[0] != '/') { errno = EINVAL; return -1; }
    int config = ownedDirectory(AT_FDCWD, base, create, false);
    if (config < 0) return -1;
    int app = ownedDirectory(config, "embercade", create, false);
    close(config);
    if (app < 0) return -1;
    int secrets = ownedDirectory(app, "secrets", create, true);
    close(app);
    return secrets;
}

inline bool safeFile(int dir)
{
    struct stat st;
    return fstatat(dir, filename, &st, AT_SYMLINK_NOFOLLOW) == 0
        && S_ISREG(st.st_mode) && st.st_uid == getuid()
        && !(st.st_mode & 0077) && st.st_nlink == 1;
}

inline bool load(Credentials& result)
{
    int dir = directory(false);
    if (dir < 0) return false;
    int fd = openat(dir, filename, O_RDONLY | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC);
    close(dir);
    if (fd < 0) return false;
    struct stat st;
    if (fstat(fd, &st) != 0 || !S_ISREG(st.st_mode) || st.st_uid != getuid()
        || st.st_mode & 0077 || st.st_nlink != 1 || st.st_size > 8192)
    { close(fd); return false; }
    std::string data;
    char buffer[1024];
    ssize_t count;
    while ((count = read(fd, buffer, sizeof(buffer))) > 0)
    {
        data.append(buffer, count);
        if (data.size() > 8192) { close(fd); return false; }
    }
    close(fd);
    if (count < 0) return false;
    Credentials parsed;
    bool user = false, key = false;
    size_t begin = 0;
    while (begin < data.size())
    {
        auto end = data.find('\n', begin);
        auto line = data.substr(begin, end == std::string::npos ? end : end - begin);
        begin = end == std::string::npos ? data.size() : end + 1;
        const std::string u = "RETROACHIEVEMENTS_WEB_USERNAME=";
        const std::string k = "RETROACHIEVEMENTS_WEB_API_KEY=";
        if (!user && line.compare(0, u.size(), u) == 0)
        { parsed.user = line.substr(u.size()); user = true; }
        else if (!key && line.compare(0, k.size(), k) == 0)
        { parsed.key = line.substr(k.size()); key = true; }
        else return false;
    }
    if (!user || !key || !validField(parsed.user) || !validField(parsed.key)) return false;
    result = parsed;
    return true;
}

inline std::string keyFor(const std::string& user)
{
    Credentials credentials;
    return load(credentials) && credentials.user == user ? credentials.key : "";
}

inline bool save(const std::string& user, const std::string& key)
{
    if (!key.empty() && (!validField(user) || !validField(key))) return false;
    int dir = directory(!key.empty());
    if (dir < 0) return key.empty() && errno == ENOENT;
    struct stat st;
    bool exists = fstatat(dir, filename, &st, AT_SYMLINK_NOFOLLOW) == 0;
    if ((exists && !safeFile(dir)) || (!exists && errno != ENOENT))
    { close(dir); return false; }
    if (key.empty())
    {
        bool ok = !exists || (unlinkat(dir, filename, 0) == 0 && fsync(dir) == 0);
        close(dir);
        return ok;
    }

    unsigned char random[16];
    if (getrandom(random, sizeof(random), 0) != sizeof(random))
    { close(dir); return false; }
    std::string temporary = ".retroachievements-user-";
    const char* digits = "0123456789abcdef";
    for (auto byte : random) { temporary += digits[byte >> 4]; temporary += digits[byte & 15]; }
    int fd = openat(dir, temporary.c_str(), O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0) { close(dir); return false; }
    const std::string data = "RETROACHIEVEMENTS_WEB_USERNAME=" + user + "\n"
        + "RETROACHIEVEMENTS_WEB_API_KEY=" + key + "\n";
    size_t written = 0;
    while (written < data.size())
    {
        ssize_t count = write(fd, data.data() + written, data.size() - written);
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) break;
        written += static_cast<size_t>(count);
    }
    bool ok = written == data.size() && fsync(fd) == 0;
    if (close(fd) != 0) ok = false;
    if (ok) ok = renameat(dir, temporary.c_str(), dir, filename) == 0;
    if (ok) ok = fsync(dir) == 0;
    if (!ok) unlinkat(dir, temporary.c_str(), 0);
    close(dir);
    return ok;
}

// Equal UTF-8 byte positions keep the existing editor's cursor offsets valid.
// This mode is opt-in; normal username/password widgets retain their behavior.
inline std::string displayText(const std::string& text, bool masked)
{ return masked ? std::string(text.size(), '*') : text; }
}
