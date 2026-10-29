from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
import os, subprocess, unittest
from embercade.video_runtime import VIDEO_PLUGINS, video_runtime_failures
from embercade.elf_runtime import ElfRuntimeClosure
from embercade.host_requirements import HOST_REQUIREMENTS, _probe_requirement, create_bootstrap_plan, HostAssessment, DistroInfo

ROOT=Path(__file__).resolve().parents[1]

class VideoRuntimeTests(unittest.TestCase):
    def test_audio_only_install_is_not_reported_as_video_ready(self):
        with TemporaryDirectory() as d:
            root=Path(d);p=root/'video_output/libvmem_plugin.so';p.parent.mkdir();p.touch()
            with patch('embercade.video_runtime.inspect_elf_runtime',return_value=ElfRuntimeClosure((),())):
                failures=video_runtime_failures(root)
            self.assertEqual(len(failures),2)
            self.assertIn('libavcodec_plugin.so',failures[0])

    def test_decoder_presence_with_broken_ffmpeg_abi_is_unavailable(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            for f in VIDEO_PLUGINS:
                p=root/f;p.parent.mkdir(parents=True,exist_ok=True);p.touch()
            with patch('embercade.video_runtime.inspect_elf_runtime',return_value=ElfRuntimeClosure((),('libavcodec.so.99',))):
                self.assertEqual(len(video_runtime_failures(root)),3)
            with patch('embercade.video_runtime.inspect_elf_runtime',return_value=ElfRuntimeClosure((),())):
                self.assertEqual(video_runtime_failures(root),())

    def test_missing_decoder_enters_existing_confirmed_host_install_plan(self):
        req=next(r for r in HOST_REQUIREMENTS if r.key=='vlc-video')
        with patch('embercade.video_runtime.video_runtime_failures',return_value=('Missing decoder',)):
            status=_probe_requirement(req,Mock(),{})
        self.assertFalse(status.installed)
        plan=create_bootstrap_plan(HostAssessment(DistroInfo('garuda','Garuda',('arch',)),(status,),(),()),Mock(available=lambda _:True))
        self.assertEqual(plan.packages,('vlc-plugin-ffmpeg',))
        self.assertTrue(req.required)

class PolishPackagingTests(unittest.TestCase):
    def test_profile_matches_only_tested_name_ids_and_sdl_backend(self):
        from embercade.launcher import prepare_launch_layout
        from embercade.paths import EmbercadePaths
        with TemporaryDirectory() as d:
            base=Path(d);env={'HOME':str(base),'EMBERCADE_CONFIG_HOME':str(base/'config'),'EMBERCADE_DATA_HOME':str(base/'data'),'EMBERCADE_STATE_HOME':str(base/'state'),'EMBERCADE_CACHE_HOME':str(base/'cache'),'EMBERCADE_RUNTIME_HOME':str(base/'runtime')}
            paths=EmbercadePaths.from_environment(env)
            prepare_launch_layout(paths,ROOT)
            p=paths.emulator_configs/'retroarch/inputs/sdl2/Embercade GameSir G7 Pro.cfg'
            s=p.read_text();self.assertIn('input_device = "GameSir G7 Pro"',s);self.assertIn('input_vendor_id = "13623"',s);self.assertIn('input_driver = "sdl2"',s)
            self.assertIn('input_l2_axis = "+4"',s);self.assertIn('input_r2_axis = "+5"',s)
            p.write_text('# custom profile retained\n');prepare_launch_layout(paths,ROOT);self.assertEqual(p.read_text(),'# custom profile retained\n')

class NotificationPolicyTests(unittest.TestCase):
    def test_saved_custom_values_and_explicit_overrides_survive_default_migration(self):
        from embercade.runtime import ProjectRuntime
        code=r'''
import configparser,json
from types import SimpleNamespace
from configgen.generators.libretro.libretroConfig import applyDesktopWidgetDefaults
keys=('menu_widget_scale_auto','menu_widget_scale_factor','menu_widget_scale_factor_windowed')
cases=0
for old in ({},dict(zip(keys,('true','1.000000','1.000000'))),dict(zip(keys,('false','0.8','0.7'))),dict(zip(keys,('true','1.2','0.9')))):
 for override in (False,True):
  parser=configparser.ConfigParser();parser['DEFAULT']=old
  cfg={'menu_enable_widgets':'true','notification_show_autoconfig_fails':'true','video_shader_enable':'false','video_driver':'vulkan'}
  explicit={'retroarch.menu_widget_scale_factor':'1.4'} if override else {}
  if override:cfg['menu_widget_scale_factor']='1.4'
  applyDesktopWidgetDefaults(SimpleNamespace(config=parser),explicit,cfg)
  defaults=not old or old.get(keys[1])=='1.000000'
  assert cfg[keys[0]]==('false' if defaults else old[keys[0]])
  assert cfg[keys[1]]==('1.4' if override else '0.6' if defaults else old[keys[1]])
  assert cfg['menu_enable_widgets']=='true' and cfg['notification_show_autoconfig_fails']=='true'
  assert cfg['video_driver']=='vulkan' and cfg['video_shader_enable']=='false'
  cases+=1
# Exercise the actual config writer's resolution gate without running games.
from unittest.mock import patch
from configgen.generators.libretro.libretroConfig import writeLibretroConfig
for width,height in ((1920,1080),(2560,1440),(3840,2160)):
 parser=configparser.ConfigParser();parser['DEFAULT']={}
 result={}
 with patch('configgen.generators.libretro.libretroConfig.createLibretroConfig',return_value={'menu_enable_widgets':'true'}),patch('configgen.generators.libretro.libretroConfig.writeLibretroConfigToFile',side_effect=lambda _,c:result.update(c)),patch.dict('os.environ',{'EMBERCADE_DESKTOP':'1'}):
  writeLibretroConfig(None,SimpleNamespace(config=parser),SimpleNamespace(config={}),[],{},[],{},None,None,False,{'width':width,'height':height},'vulkan')
 assert result['menu_widget_scale_auto']=='false' and result['menu_widget_scale_factor']=='0.6'
 assert result['menu_enable_widgets']=='true'
 cases+=1
print(json.dumps({'cases':cases}))
'''
        completed=subprocess.run([str(ProjectRuntime(ROOT).python),'-B','-c',code],capture_output=True,text=True,timeout=20)
        self.assertEqual(completed.returncode,0,completed.stderr)
        self.assertEqual(completed.stdout.strip(),'{"cases": 11}')
