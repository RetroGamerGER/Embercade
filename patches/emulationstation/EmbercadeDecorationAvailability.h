#pragma once

#include <limits>
#include <map>
#include <string>

namespace EmbercadeDecorations
{
    inline std::string selectionName(const std::string& value)
    {
        return value == "consoles" ? "default_unglazed" : value;
    }

    template <typename Exists>
    std::string preview(const std::string& folder, const std::string& system,
                        bool systemSpecific, Exists exists)
    {
        if (!system.empty())
        {
            auto stem = folder + "/systems/" + system;
            if (exists(stem + ".png") && exists(stem + ".info"))
                return stem + ".png";
        }
        if (systemSpecific)
            return {};
        auto generic = folder + "/default.png";
        return exists(generic) ? generic : std::string{};
    }

    // Several official sets link to exactly the same system image/layout.
    // Offer that source once, preferring its own set name over an alias name.
    class Sources
    {
        struct Entry { size_t index; bool direct; };
        std::map<std::string, Entry> entries;
    public:
        static constexpr size_t skip = std::numeric_limits<size_t>::max();
        size_t select(const std::string& identity, bool direct, size_t next)
        {
            auto found = entries.find(identity);
            if (found == entries.end())
            {
                entries.emplace(identity, Entry{next, direct});
                return next;
            }
            if (direct && !found->second.direct)
            {
                found->second.direct = true;
                return found->second.index;
            }
            return skip;
        }
    };
}
