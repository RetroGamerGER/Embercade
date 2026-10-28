from dataclasses import replace
from pathlib import Path


def with_graphics_probe(plan, available=True):
    """Control only the host capability probe; run the real pinned launcher."""
    code = f'''
import runpy,sys
from types import SimpleNamespace
from unittest.mock import patch,AsyncMock
gpu=SimpleNamespace(active_discrete_gpu=None) if {available!r} else None
with patch('configgen.utils.vulkan.is_available',return_value={available!r}), \
     patch('configgen.utils.vulkan.has_discrete_gpu',return_value=False), \
     patch('configgen.utils.videoMode.getGLVersion',return_value=4.6), \
     patch('batocera_launch_dolphin.emulator.get_vulkan_info',AsyncMock(return_value=gpu)), \
     patch('batocera_launch_pcsx2.emulator.get_vulkan_info',AsyncMock(return_value=gpu)):
    sys.argv=sys.argv[1:]
    runpy.run_path(sys.argv[0],run_name='__main__')
'''
    return replace(plan, command=(str(Path(plan.command[0]).parent / "python"), "-c", code, *plan.command))
