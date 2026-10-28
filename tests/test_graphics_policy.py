from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import subprocess
import unittest

from embercade.runtime import ProjectRuntime


class GraphicsPolicyTests(unittest.TestCase):
    def test_native_psp_and_3ds_defaults_preserve_manual_and_raw_choices(self):
        project = Path(__file__).resolve().parents[1]
        code = '''
import asyncio,configparser,json,os,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
from batocera_launch.config.config import Config
from batocera_launch.emulators.ppsspp import PPSSPP
from batocera_launch.emulators.azahar import Azahar
class Values(Config):
    @property
    def show_fps(self): return False
async def main():
    count=0
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        for desktop in ('1','0'):
            for available in (True,False):
                gpu=SimpleNamespace(active_discrete_gpu=None) if available else None
                for name,cls,key,manuals,section,option,filename in (
                    ('psp',PPSSPP,'gfxbackend',(None,'OPENGL','VULKAN'),'Graphics','GraphicsBackend','ppsspp.ini'),
                    ('3ds',Azahar,'azahar_graphics_api',(None,'0','1','2'),'Renderer','graphics_api','qt-config.ini')):
                    for manual in manuals:
                        values=Values({key:manual} if manual else {})
                        case=root/str(count)
                        instance=SimpleNamespace(config=values,psp_system_dir=case,config_dir=case,controllers=[])
                        with patch.dict(os.environ,{'EMBERCADE_DESKTOP':desktop}),patch('batocera_launch.emulators.'+('ppsspp' if name=='psp' else 'azahar')+'.get_vulkan_info',AsyncMock(return_value=gpu)):
                            await cls._write_config(instance)
                        result=configparser.RawConfigParser();result.read(case/filename)
                        if name=='psp':
                            expected=manual or ('VULKAN' if desktop=='1' else 'OPENGL')
                            if expected=='VULKAN' and not available:expected='OPENGL'
                        else:
                            expected=manual or ('2' if desktop=='1' else '1')
                            if desktop=='1' and expected=='2' and not available:expected='1'
                        assert result[section][option]==expected,(desktop,available,name,manual,result[section][option],expected)
                        count+=1
        for manual in ('','auto','default'):
            for name,cls,key,section,option,filename,expected in (
                ('ppsspp',PPSSPP,'gfxbackend','Graphics','GraphicsBackend','ppsspp.ini','VULKAN'),
                ('azahar',Azahar,'azahar_graphics_api','Renderer','graphics_api','qt-config.ini','2')):
                case=root/str(count)
                values=Values({key:manual})
                instance=SimpleNamespace(config=values,psp_system_dir=case,config_dir=case,controllers=[])
                with patch.dict(os.environ,{'EMBERCADE_DESKTOP':'1'}),patch('batocera_launch.emulators.'+name+'.get_vulkan_info',AsyncMock(return_value=SimpleNamespace(active_discrete_gpu=None))):
                    await cls._write_config(instance)
                result=configparser.RawConfigParser();result.read(case/filename)
                assert result[section][option]==expected
                count+=1
        # The upstream PPSSPP raw INI override remains the final authority.
        case=root/'raw'
        values=Values({'ppsspp.Graphics.GraphicsBackend':'OPENGL'})
        with patch.dict(os.environ,{'EMBERCADE_DESKTOP':'1'}),patch('batocera_launch.emulators.ppsspp.get_vulkan_info',AsyncMock(return_value=SimpleNamespace(active_discrete_gpu=None))):
            await PPSSPP._write_config(SimpleNamespace(config=values,psp_system_dir=case))
        result=configparser.RawConfigParser();result.read(case/'ppsspp.ini')
        assert result['Graphics']['GraphicsBackend']=='OPENGL'
        print(json.dumps({'validated':count+1}))
asyncio.run(main())
'''
        completed = subprocess.run([str(ProjectRuntime(project).python), "-B", "-c", code],
                                   text=True, capture_output=True, check=False, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), {"validated": 35})

    def test_pinned_backend_policy_preserves_overrides_and_core_constraints(self):
        project = Path(__file__).resolve().parents[1]
        code = '''
import json,os
from types import SimpleNamespace
from unittest.mock import patch
from configgen.generators.libretro.libretroGenerator import getGFXBackend
class Config(dict):
    @property
    def core(self): return self['core']
cases=[]
for available in (True,False):
    for core in ('opera','gambatte','snes9x','kronos','mupen64plus-next','melonds','beetle-psx-hw','parallel_n64','yabasanshiro','boom3'):
        for manual in (None,'gl','glcore','vulkan','auto'):
            values=Config(core=core)
            if manual is not None: values['gfxbackend']=manual
            with patch.dict(os.environ,{'EMBERCADE_DESKTOP':'1'}), patch('configgen.utils.vulkan.is_available',return_value=available), patch('configgen.utils.videoMode.getGLVendor',return_value='intel'), patch('configgen.utils.videoMode.getGLVersion',return_value=4.6):
                cases.append([available,core,manual,getGFXBackend(SimpleNamespace(config=values))])
for vendor in ('intel','nvidia'):
    with patch.dict(os.environ,{'EMBERCADE_DESKTOP':'0'}), patch('configgen.utils.vulkan.is_available') as probe, patch('configgen.utils.videoMode.getGLVendor',return_value=vendor), patch('configgen.utils.videoMode.getGLVersion',return_value=4.6):
        result=getGFXBackend(SimpleNamespace(config=Config(core='opera')))
        assert result==('gl' if vendor=='intel' else 'glcore')
        probe.assert_not_called()
with patch.dict(os.environ,{'EMBERCADE_DESKTOP':'1'}), patch('configgen.utils.vulkan.is_available',return_value=False), patch('configgen.utils.videoMode.getGLVersion',return_value=2.1):
    assert getGFXBackend(SimpleNamespace(config=Config(core='opera'))) == 'gl'
with patch.dict(os.environ,{'EMBERCADE_DESKTOP':'1'}), patch('configgen.utils.vulkan.is_available') as probe:
    assert getGFXBackend(SimpleNamespace(config=Config(core='opera',gfxbackend='vulkan',**{'retroarch.video_driver':'gl'})))=='gl'
    probe.assert_not_called()
print(json.dumps(cases))
'''
        completed = subprocess.run([str(ProjectRuntime(project).python), "-B", "-c", code],
                                   text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        for available, core, manual, backend in json.loads(completed.stdout):
            with self.subTest(available=available, core=core, manual=manual):
                if manual not in (None, "auto"):
                    expected = manual
                elif core in ("kronos", "mupen64plus-next", "melonds", "beetle-psx-hw"):
                    expected = "glcore"
                elif core in ("parallel_n64", "yabasanshiro", "boom3"):
                    expected = "gl"
                else:
                    expected = "vulkan" if available else "glcore"
                self.assertEqual(backend, expected)

    def test_native_notice_consumes_only_known_bounded_messages(self):
        project = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "notice.cpp"
            source.write_text('''#include "EmbercadeLaunchNotice.h"
#include <iostream>
int main(int argc,char **argv) { std::cout << int(EmbercadeLaunchNotice::consume(argv[1])); }
''')
            binary = root / "notice"
            subprocess.run(["c++", "-std=c++17", "-I", str(project / "patches/emulationstation"),
                            str(source), "-o", str(binary)], check=True, capture_output=True)
            notice = root / "notice.txt"
            for text, expected in (("shader-incompatible\n", "1"), ("shader-unavailable\n", "2"),
                                   ("unknown\n", "0"), ("x" * 4096, "0")):
                notice.write_text(text)
                result = subprocess.run([str(binary), str(notice)], capture_output=True, text=True, check=True)
                self.assertEqual(result.stdout, expected)
                self.assertFalse(notice.exists())
            result = subprocess.run([str(binary), str(notice)], capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout, "0")
