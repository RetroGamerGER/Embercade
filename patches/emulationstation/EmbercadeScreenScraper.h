#pragma once

// Optional development override and separate personal-account storage.
// Production application authorization is supplied by the private build header.
#include <string>
#include <map>
#include <cstdlib>
#include <algorithm>
#include <cctype>
#include <cerrno>
#include <cstdio>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

namespace EmbercadeScreenScraper
{
struct Credentials
{
    std::string developerId;
    std::string developerPassword;
    std::string debugPassword;
    bool valid() const { return !developerId.empty() && !developerPassword.empty(); }
};

inline Credentials load()
{
    const char* path = std::getenv("EMBERCADE_SCREENSCRAPER_SECRET_FILE");
    if (!path || path[0] != '/') return {};
    std::string filename(path);
    auto split = filename.find_last_of('/');
    int directory = open(filename.substr(0, split).c_str(), O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_DIRECTORY);
    if (directory < 0) return {};
    struct stat parent;
    if (fstat(directory, &parent) || parent.st_uid != getuid() || (parent.st_mode & 0077))
    {
        close(directory);
        return {};
    }
    int fd = openat(directory, filename.substr(split + 1).c_str(), O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK);
    close(directory);
    if (fd < 0) return {};
    struct stat st;
    if (fstat(fd, &st) || !S_ISREG(st.st_mode) || st.st_uid != getuid()
        || (st.st_mode & 0077) || st.st_size > 16384)
    {
        close(fd);
        return {};
    }
    std::string data;
    char buffer[1024];
    ssize_t count;
    while ((count = read(fd, buffer, sizeof(buffer))) > 0)
    {
        data.append(buffer, count);
        if (data.size() > 16384) { close(fd); return {}; }
    }
    close(fd);
    if (count < 0 || data.find('\0') != std::string::npos) return {};
    std::map<std::string, std::string> fields;
    size_t begin = 0;
    while (begin < data.size())
    {
        auto end = data.find('\n', begin);
        auto line = data.substr(begin, end == std::string::npos ? end : end - begin);
        begin = end == std::string::npos ? data.size() : end + 1;
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty() || line[0] == '#') continue;
        auto equal = line.find('=');
        if (equal == std::string::npos) return {};
        auto key = line.substr(0, equal);
        if (key != "SCREENSCRAPER_DEV_ID" && key != "SCREENSCRAPER_DEV_PASSWORD"
            && key != "SCREENSCRAPER_DEV_DEBUG_PASSWORD") return {};
        if (fields.count(key)) return {};
        fields[key] = line.substr(equal + 1);
    }
    return {fields["SCREENSCRAPER_DEV_ID"], fields["SCREENSCRAPER_DEV_PASSWORD"],
            fields["SCREENSCRAPER_DEV_DEBUG_PASSWORD"]};
}

struct UserCredentials
{
    std::string name;
    std::string password;
};

inline std::string userSecretDirectory()
{
    const char* base = std::getenv("XDG_CONFIG_HOME");
    if (!base || base[0] != '/') return {};
    return std::string(base) + "/embercade/secrets";
}

inline bool openUserSecretDirectory(int& directory, bool create)
{
    auto path = userSecretDirectory();
    if (path.empty()) return false;
    if (create && mkdir(path.c_str(), 0700) != 0 && errno != EEXIST) return false;
    directory = open(path.c_str(), O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_DIRECTORY);
    if (directory < 0) return false;
    struct stat info;
    if (fstat(directory, &info) != 0 || info.st_uid != getuid() || (info.st_mode & 0077))
    {
        close(directory);
        directory = -1;
        return false;
    }
    return true;
}

inline bool loadUser(UserCredentials& credentials)
{
    int directory = -1;
    if (!openUserSecretDirectory(directory, false)) return false;
    int fd = openat(directory, "screenscraper-user.conf", O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK);
    close(directory);
    if (fd < 0) return false;
    struct stat info;
    if (fstat(fd, &info) != 0 || !S_ISREG(info.st_mode) || info.st_uid != getuid()
        || (info.st_mode & 0077) || info.st_size > 16384)
    {
        close(fd);
        return false;
    }
    std::string data;
    char buffer[1024];
    ssize_t count;
    while ((count = read(fd, buffer, sizeof(buffer))) > 0)
    {
        data.append(buffer, count);
        if (data.size() > 16384) { close(fd); return false; }
    }
    close(fd);
    if (count < 0 || data.find('\0') != std::string::npos) return false;
    bool hasName = false, hasPassword = false;
    UserCredentials parsed;
    size_t begin = 0;
    while (begin < data.size())
    {
        auto end = data.find('\n', begin);
        auto line = data.substr(begin, end == std::string::npos ? end : end - begin);
        begin = end == std::string::npos ? data.size() : end + 1;
        if (!line.empty() && line.back() == '\r') line.pop_back();
        auto equal = line.find('=');
        if (equal == std::string::npos) return false;
        auto key = line.substr(0, equal);
        if (key == "SCREENSCRAPER_USER" && !hasName)
        {
            parsed.name = line.substr(equal + 1);
            hasName = true;
        }
        else if (key == "SCREENSCRAPER_PASSWORD" && !hasPassword)
        {
            parsed.password = line.substr(equal + 1);
            hasPassword = true;
        }
        else return false;
    }
    if (!hasName || !hasPassword) return false;
    credentials = parsed;
    return true;
}

inline bool saveUser(const UserCredentials& credentials)
{
    if (credentials.name.find_first_of("\r\n\0", 0, 3) != std::string::npos
        || credentials.password.find_first_of("\r\n\0", 0, 3) != std::string::npos)
        return false;
    int directory = -1;
    if (!openUserSecretDirectory(directory, true)) return false;
    struct stat existing;
    if (fstatat(directory, "screenscraper-user.conf", &existing, AT_SYMLINK_NOFOLLOW) == 0)
    {
        if (!S_ISREG(existing.st_mode) || existing.st_uid != getuid() || (existing.st_mode & 0077))
        { close(directory); return false; }
        UserCredentials previous;
        if (!loadUser(previous)) { close(directory); return false; }
        if (previous.name == credentials.name && previous.password == credentials.password)
        { close(directory); return true; }
    }
    else if (errno != ENOENT) { close(directory); return false; }

    auto path = userSecretDirectory() + "/.screenscraper-user.conf.XXXXXX";
    std::vector<char> temporary(path.begin(), path.end());
    temporary.push_back('\0');
    int fd = mkstemp(temporary.data());
    if (fd < 0) { close(directory); return false; }
    const std::string data = "SCREENSCRAPER_USER=" + credentials.name + "\n"
        + "SCREENSCRAPER_PASSWORD=" + credentials.password + "\n";
    if (data.size() > 16384)
    {
        close(fd);
        unlink(temporary.data());
        close(directory);
        return false;
    }
    size_t written = 0;
    while (written < data.size())
    {
        ssize_t count = write(fd, data.data() + written, data.size() - written);
        if (count <= 0) break;
        written += static_cast<size_t>(count);
    }
    bool ok = written == data.size() && fsync(fd) == 0;
    close(fd);
    if (ok) ok = rename(temporary.data(), (userSecretDirectory() + "/screenscraper-user.conf").c_str()) == 0;
    if (ok) ok = fsync(directory) == 0;
    if (!ok) unlink(temporary.data());
    close(directory);
    return ok;
}

inline bool isService(const std::string& url)
{
    if (url.find("https://") != 0) return false;
    auto end = url.find_first_of("/?#", 8);
    auto host = url.substr(8, end == std::string::npos ? end : end - 8);
    // The API also returns credential-bearing media URLs on service shards
    // such as neoclone.screenscraper.fr. Accept its DNS namespace, not arbitrary
    // API-provided hosts. Refuse userinfo, ports, escapes and malformed names.
    if (host.empty() || host.front() == '.' || host.back() == '.'
        || host.find("..") != std::string::npos) return false;
    for (unsigned char character : host)
        if (!std::isalnum(character) && character != '-' && character != '.') return false;
    std::transform(host.begin(), host.end(), host.begin(),
        [](unsigned char c) { return std::tolower(c); });
    const std::string domain = "screenscraper.fr";
    const std::string suffix = "." + domain;
    return host == domain || (host.size() > suffix.size()
        && host.compare(host.size() - suffix.size(), suffix.size(), suffix) == 0);
}

inline bool isSensitive(const std::string& url)
{
    return isService(url) || url.find("devid=") != std::string::npos
        || url.find("devpassword=") != std::string::npos
        || url.find("devdebugpassword=") != std::string::npos
        || url.find("sspassword=") != std::string::npos;
}

inline std::string safeError(int status)
{
    switch (status)
    {
    case 401: return "ScreenScraper: service temporarily restricted to active members. Check your user account and try later.";
    case 403: return "ScreenScraper: access was refused. Check your account in the scraper settings or try again later.";
    case 404: return "ScreenScraper: game or resource not found.";
    case 423: return "ScreenScraper: service temporarily closed. Please try later.";
    case 426: return "ScreenScraper: this application version cannot access the service. Please check for an update.";
    case 429: return "ScreenScraper: request limit reached. Please try again later.";
    case 430: return "ScreenScraper: daily scrape limit reached. Please try again later.";
    case 431: return "ScreenScraper: failed-request limit reached. Please try again later.";
    default: return "ScreenScraper: request failed. Check access, network and service availability.";
    }
}
}
