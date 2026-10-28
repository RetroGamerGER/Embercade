"""Read-only verification of libVLC's dynamically loaded video decoder.

libvlc's ELF closure alone cannot detect an omitted VLC codec plugin. Keep
host libVLC and its matching distro plugins together; do not bundle a plugin
built against a different host FFmpeg/VLC ABI.
"""
from pathlib import Path
from embercade.elf_runtime import inspect_elf_runtime

VIDEO_PLUGINS = ("codec/libavcodec_plugin.so", "video_chroma/libswscale_plugin.so",
                 "video_output/libvmem_plugin.so")


def video_runtime_failures(plugin_root: Path = Path("/usr/lib/vlc/plugins"), *,
                           runner=None) -> tuple[str, ...]:
    failures = []
    for relative in VIDEO_PLUGINS:
        plugin = plugin_root / relative
        if not plugin.is_file():
            failures.append("Missing VLC video module: " + relative)
            continue
        closure = inspect_elf_runtime(plugin, **({"runner": runner} if runner else {}))
        if not closure.healthy:
            failures.append("VLC module unavailable: " + relative +
                            (" (" + ", ".join(closure.missing) + ")" if closure.missing else ""))
    return tuple(failures)
