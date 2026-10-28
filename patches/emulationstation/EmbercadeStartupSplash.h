#pragma once

#include <cstdint>

// Only startup uses this deadline. Loading consumes the same interval; it is
// never followed by an additional fixed sleep. SDL's unsigned ticks wrap safely.
namespace Embercade
{
class StartupSplashDeadline
{
public:
    static constexpr std::uint32_t minimumMs = 2750;
    explicit StartupSplashDeadline(std::uint32_t firstPresented) : started(firstPresented) {}

    std::uint32_t elapsed(std::uint32_t now) const { return now - started; }

    std::uint32_t remaining(std::uint32_t now, bool failed = false) const
    {
        const auto visible = elapsed(now);
        return failed || visible >= minimumMs ? 0 : minimumMs - visible;
    }

private:
    std::uint32_t started;
};
}
