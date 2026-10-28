from dataclasses import replace
from array import array
import ctypes
import json
import os
from pathlib import Path
import socket
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from embercade.backend import backend_command
from embercade.launcher import LaunchPlan, run_launch
from embercade.decoration_window import GamescopeWindows, configure_layer
from embercade.drm_output import active_output_size, gamescope_drm_nodes, gamescope_device_hint, decoration_drm_nodes, single_output, Resources, Crtc, U32
from embercade.standalone_decoration import (
    Decoration, belongs_to_launch, decoration_backend,
    hyprland_socket_dir, protected_ratio, safe_margins, standalone_decoration,
    validate_decoration, visible_on_monitor,
)


class StandaloneDecorationTests(unittest.TestCase):
    def test_layer_covers_full_output_without_reserving_space_or_input(self):
        layer, window = Mock(), Mock()
        configure_layer(window, layer)
        layer.set_exclusive_zone.assert_called_once_with(window, -1)
        layer.set_keyboard_mode.assert_called_once_with(window, layer.KeyboardMode.NONE)
        for edge in (layer.Edge.TOP, layer.Edge.BOTTOM, layer.Edge.LEFT, layer.Edge.RIGHT):
            layer.set_anchor.assert_any_call(window, edge, True)
            layer.set_margin.assert_any_call(window, edge, 0)

    def test_logical_scaled_and_offset_outputs_keep_centered_safe_apertures(self):
        for system in ('gamecube', 'wii', 'xbox'):
            ratio = protected_ratio(system, {'xemu_aspect': '4x3'})
            for x, y, width, height in ((0, 0, 2560, 1440), (0, 0, 1920, 1080),
                                       (0, 0, 1280, 800), (-1280, 200, 1280, 720),
                                       (1920, -120, 2048, 1152)):
                with self.subTest(system=system, geometry=(x, y, width, height)):
                    decoration = self.decoration(ratio=ratio)
                    left, right = safe_margins(decoration, width, height)
                    self.assertAlmostEqual(left, right)
                    self.assertLessEqual(left, (width - height * ratio) / 2)
                    scale = min(width / decoration.width, height / decoration.height)
                    self.assertLessEqual(decoration.height * scale, height)
                    self.assertLessEqual(decoration.width * scale, width)
                    active = dict(mapped=True, fullscreen=2, at=[x,y], size=[width,height])
                    self.assertTrue(visible_on_monitor(active, (x,y,width,height), True))
                    self.assertFalse(visible_on_monitor(active | {'at':[x,y+32]}, (x,y,width,height), True))

    def test_gamescope_overlay_uses_physical_surface_not_logical_screen(self):
        backend = GamescopeWindows.__new__(GamescopeWindows)
        backend.root_display = Mock()
        window = backend.root_display.create_resource_object.return_value
        window.get_geometry.return_value = Mock(x=0, y=0, width=1920, height=1080)
        backend.size_overlay(42, (3840, 2160))
        backend.root_display.create_resource_object.assert_called_with('window', 42)
        window.configure.assert_called_once_with(x=0, y=0, width=3840, height=2160)
        window.configure.reset_mock()
        window.get_geometry.return_value = Mock(x=0, y=0, width=3840, height=2160)
        backend.size_overlay(42, (3840, 2160))
        window.configure.assert_not_called()

    def test_host_discovery_does_not_require_xlib_in_launcher_venv(self):
        result = Mock(stdout='{"pid": 123, "nodes": ["/dev/dri/card1"]}')
        with patch('embercade.drm_output.subprocess.run', return_value=result) as run:
            self.assertEqual(json.loads(gamescope_device_hint({'DISPLAY': ':1'}))['pid'], 123)
        self.assertEqual(run.call_args.args[0][:3], ['/usr/bin/python', '-I', '-B'])
        self.assertEqual(run.call_args.kwargs['timeout'], 3)
        self.assertEqual(run.call_args.kwargs['env'], {'DISPLAY': ':1'})

    def plan(self, system='ps2', **kwargs):
        return LaunchPlan(('launcher', '-system', system, '-rom', 'game with spaces.iso'),
                          {}, Path('/usr/bin/emulator'), None, Path('game with spaces.iso'),
                          system=system, emulator={'ps2': 'pcsx2', 'xbox': 'xemu',
                                                   'gamecube': 'dolphin', 'wii': 'dolphin'}.get(system),
                          **kwargs)

    def decoration(self, **kwargs):
        return replace(Decoration(Path('/image.png'), 1920, 1080, 240, 0, 240, 0, 1, 4/3), **kwargs)

    def test_geometry_protects_game_and_preserves_aperture(self):
        self.assertEqual(safe_margins(self.decoration(), 2560, 1440), (319, 319))
        self.assertEqual(safe_margins(self.decoration(), 1920, 1080), (239, 239))
        self.assertEqual(safe_margins(self.decoration(), 1440, 1080), (0, 0))
        xbox = self.decoration(left=250, right=265)
        self.assertEqual(safe_margins(xbox, 1920, 1080), (239, 239))
        self.assertEqual(safe_margins(self.decoration(ratio=16/9), 1920, 1080), (0, 0))

    def test_ambiguous_viewports_are_conservative(self):
        self.assertEqual(protected_ratio('ps2', {}), 1.5)
        self.assertEqual(protected_ratio('ps2', {'pcsx2_ratio': '4:3', 'pcsx2_fmv_ratio': None}), 1.5)
        self.assertEqual(protected_ratio('ps2', {'pcsx2_ratio': '4:3', 'pcsx2_fmv_ratio': 'off'}), 4/3)
        self.assertEqual(protected_ratio('ps2', {'pcsx2_ratio': '4:3', 'pcsx2_fmv_ratio': '4:3'}), 4/3)
        self.assertEqual(protected_ratio('ps2', {'pcsx2_ratio': '4:3', 'pcsx2_fmv_ratio': '16:9'}), 16/9)
        self.assertIsNone(protected_ratio('ps2', {'pcsx2_ratio': 'Stretch'}))
        self.assertEqual(protected_ratio('xbox', {'xemu_aspect': '4x3'}), 4/3)
        self.assertEqual(protected_ratio('xbox', {}), 16/9)
        self.assertIsNone(protected_ratio('xbox', {'xemu_scaling': 'stretch'}))
        for system in ('gamecube', 'wii'):
            self.assertEqual(protected_ratio(system, {}), 4/3)
            self.assertEqual(protected_ratio(system, {'dolphin_aspect_ratio': '2'}), 4/3)
            self.assertEqual(protected_ratio(system, {'dolphin_aspect_ratio': '1'}), 16/9)
            self.assertEqual(protected_ratio(system, {'tv_mode': '1'}), 16/9)
            self.assertIsNone(protected_ratio(system, {'dolphin_aspect_ratio': '3'}))
            self.assertIsNone(protected_ratio(system, {'dolphin_aspect_ratio': 'unknown'}))

    def test_visibility_requires_matching_fullscreen_on_exact_monitor(self):
        active = {'mapped': True, 'hidden': False, 'fullscreen': 2, 'at': [0, 0], 'size': [1920, 1080]}
        monitor = (0, 0, 1920, 1080)
        self.assertTrue(visible_on_monitor(active, monitor, True))
        self.assertFalse(visible_on_monitor(active, monitor, False))  # other workspace/window
        for mutation in ({'hidden': True}, {'mapped': False}, {'fullscreen': 0}, {'size': [900, 600]}, {'at': [1920, 0]}):
            self.assertFalse(visible_on_monitor(active | mutation, monitor, True))

    def test_gamescope_focus_is_read_from_the_published_server_not_display_zero(self):
        backend = GamescopeWindows.__new__(GamescopeWindows)
        backend.X = Mock(IsViewable=2)
        backend.root_display = Mock()
        backend.root = Mock()
        backend.root.get_geometry.return_value = Mock(width=1920, height=1080)
        connection = Mock()
        connection.intern_atom.return_value = 73
        backend.connections = {':8': connection}
        window = connection.create_resource_object.return_value
        window.get_geometry.return_value = Mock(x=1, y=1, width=1920, height=1080)
        window.get_attributes.return_value = Mock(map_state=2)
        values = {
            'GAMESCOPE_FOCUSED_WINDOW': [123],
            'GAMESCOPE_FOCUS_DISPLAY': array('I', [int.from_bytes(b':8\0\0', 'little')]),
            '_NET_WM_PID': [4321], '_NET_WM_STATE': [73],
        }
        backend.property = lambda _connection, _window, name: values.get(name)
        active = backend.active()
        self.assertEqual(active['pid'], 4321)
        self.assertEqual(active['at'], [0, 0])
        self.assertTrue(visible_on_monitor(active, active['monitor'], True))
        connection.create_resource_object.assert_called_once_with('window', 123)
        # Xemu's SDL window has no EWMH fullscreen atom in Gamescope.
        values['_NET_WM_STATE'] = None
        active = backend.active()
        self.assertTrue(visible_on_monitor(active, active['monitor'], True))
        # Neither a smaller nor an offset window qualifies without that atom.
        for geometry in (Mock(x=1, y=1, width=1280, height=720),
                         Mock(x=50, y=50, width=1920, height=1080)):
            window.get_geometry.return_value = geometry
            active = backend.active()
            self.assertFalse(visible_on_monitor(active, active['monitor'], True))
        values['GAMESCOPE_FOCUSED_WINDOW'] = None
        self.assertEqual(backend.active(), {})

    def test_gamescope_never_grabs_input_or_marks_overlay_as_game(self):
        source = (Path(__file__).resolve().parents[1] / 'src/embercade/decoration_window.py').read_text()
        self.assertIn("intern_atom('GAMESCOPE_EXTERNAL_OVERLAY')", source)
        self.assertNotIn("intern_atom('STEAM_GAME')", source)
        self.assertNotIn('set_input_focus(', source)
        self.assertIn('input_shape_combine_region(cairo.Region()', source)
        self.assertIn('GLib.IO_HUP | GLib.IO_ERR, stop', source)

    def test_gamescope_4k_scanout_is_not_1080p_xwayland_size(self):
        resources = Resources()
        resources.count_crtcs = 1
        resources.crtcs = (U32 * 1)(12)
        crtc = Crtc()
        crtc.mode_valid = 1
        crtc.mode.hdisplay, crtc.mode.vdisplay = 3840, 2160
        library = Mock()
        library.drmModeGetResources.return_value = ctypes.pointer(resources)
        library.drmModeGetCrtc.return_value = ctypes.pointer(crtc)
        with patch('embercade.drm_output.C.CDLL', return_value=library), patch('embercade.drm_output.os.open', return_value=123) as opened, patch('embercade.drm_output.os.close') as closed:
            self.assertEqual(active_output_size((Path('/dev/dri/card7'),)), (3840, 2160))
            opened.assert_called_once_with(Path('/dev/dri/card7'), os.O_RDONLY | os.O_CLOEXEC)
            closed.assert_called_once_with(123)
            library.drmModeFreeCrtc.assert_called_once()
            library.drmModeFreeResources.assert_called_once()
            self.assertEqual(safe_margins(self.decoration(), 3840, 2160), (479, 479))
        for modes in ([], [(0, 0)], [(1920, 1080), (3840, 2160)]):
            with self.assertRaises(ValueError):
                single_output(modes)

    def test_drm_query_failure_closes_descriptor_without_modeset(self):
        library = Mock()
        library.drmModeGetResources.return_value = None
        with patch('embercade.drm_output.C.CDLL', return_value=library), patch('embercade.drm_output.os.open', return_value=123), patch('embercade.drm_output.os.close') as closed:
            with self.assertRaises(OSError):
                active_output_size((Path('/dev/dri/card7'),))
            closed.assert_called_once_with(123)
            library.drmModeSetCrtc.assert_not_called()
            library.drmSetMaster.assert_not_called()

    def test_gamescope_thread_name_is_not_binary_identity(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            process = root / '77'
            process.mkdir()
            executable = root / 'gamescope'
            executable.touch()
            (process / 'exe').symlink_to(executable)
            (process / 'comm').write_text('gamescope-wl\n')
            (process / 'environ').write_text('DISPLAY=:1\0')
            (process / 'cmdline').write_bytes(b'gamescope\0')
            with self.assertRaisesRegex(ValueError, 'Nested/rotated'):
                gamescope_drm_nodes(77, root)

    def test_sandbox_device_hint_is_pid_scoped_and_rejects_arbitrary_paths(self):
        hint = {'pid': 77, 'nodes': ['/dev/dri/card3']}
        with patch('embercade.drm_output.Path.is_char_device', return_value=True), patch('embercade.drm_output.gamescope_drm_nodes') as discovery:
            self.assertEqual(decoration_drm_nodes(77, {'EMBERCADE_DECORATION_DRM_DEVICES': json.dumps(hint)}), (Path('/dev/dri/card3'),))
            discovery.assert_not_called()
            for value in (hint | {'pid': 88}, hint | {'nodes': ['/etc/shadow']}, hint | {'nodes': ['/dev/dri/../card3']}):
                with self.assertRaises(ValueError):
                    decoration_drm_nodes(77, {'EMBERCADE_DECORATION_DRM_DEVICES': json.dumps(value)})

    def test_pid_matching_never_accepts_unrelated_emulator(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / 'emulator'
            binary.touch()
            for pid, parent in ((100, 50), (50, 10), (200, 1)):
                process = root / str(pid)
                process.mkdir()
                (process / 'stat').write_text(f'{pid} (game (with spaces)) S {parent} 0')
                (process / 'exe').symlink_to(binary)
            self.assertTrue(belongs_to_launch(100, 50, binary, root))
            self.assertFalse(belongs_to_launch(200, 50, binary, root))
            self.assertFalse(belongs_to_launch(100, 50, root / 'different', root))
            self.assertFalse(belongs_to_launch(300, 50, binary, root))

    def test_kwin_backend_preserves_gamescope_priority(self):
        env = dict(WAYLAND_DISPLAY="wayland-0", XDG_CURRENT_DESKTOP="KDE", DISPLAY=":1")
        self.assertEqual(decoration_backend(env), "kwin")
        self.assertEqual(decoration_backend(env | {"GAMESCOPE_WAYLAND_DISPLAY": "gamescope"}), "gamescope")
        self.assertIsNone(decoration_backend(dict(WAYLAND_DISPLAY="w", XDG_CURRENT_DESKTOP="GNOME")))

    def test_kwin_observer_only_reads_active_metadata_and_unloads_its_own_script(self):
        from embercade.kwin_decoration import observer_script
        script = observer_script(":1.999", "embercade-decoration-fixture").decode()
        self.assertIn("NameHasOwner", script)
        self.assertIn('"unloadScript", plugin', script)
        self.assertNotIn("caption", script)
        self.assertNotIn("activeWindow =", script)
        self.assertNotIn("fullScreen =", script)
        self.assertNotIn("writeConfig", script)

    def test_backend_uses_real_sockets_and_gamescope_has_priority(self):
        with TemporaryDirectory() as directory:
            ipc = Path(directory) / 'hypr/test'
            ipc.mkdir(parents=True)
            env = {'WAYLAND_DISPLAY': 'wayland-1', 'XDG_RUNTIME_DIR': directory,
                   'HYPRLAND_INSTANCE_SIGNATURE': 'test'}
            self.assertIsNone(decoration_backend(env))
            with socket.socket(socket.AF_UNIX) as control, socket.socket(socket.AF_UNIX) as events:
                control.bind(str(ipc / '.socket.sock'))
                events.bind(str(ipc / '.socket2.sock'))
                self.assertEqual(decoration_backend(env), 'hyprland')
                self.assertEqual(hyprland_socket_dir(env), ipc)
                self.assertEqual(decoration_backend(env | {'DISPLAY': ':7', 'GAMESCOPE_WAYLAND_DISPLAY': 'gamescope-4'}), 'gamescope')
                self.assertIsNone(hyprland_socket_dir(env | {'HYPRLAND_INSTANCE_SIGNATURE': '../bad'}))

    def test_xemu_desktop_launch_uses_hyprland_helper_and_reaps_it(self):
        with TemporaryDirectory() as directory:
            ipc = Path(directory) / 'hypr/test'
            ipc.mkdir(parents=True)
            with socket.socket(socket.AF_UNIX) as control, socket.socket(socket.AF_UNIX) as events:
                control.bind(str(ipc / '.socket.sock'))
                events.bind(str(ipc / '.socket2.sock'))
                plan = replace(self.plan('xbox'), environment={
                    'WAYLAND_DISPLAY': 'wayland-1',
                    'XDG_RUNTIME_DIR': directory,
                    'HYPRLAND_INSTANCE_SIGNATURE': 'test',
                })
                helper = Mock(returncode=0)
                with patch('embercade.standalone_decoration.resolve_decoration', return_value=self.decoration()) as resolve, \
                     patch('embercade.standalone_decoration.subprocess.Popen', return_value=helper) as popen, \
                     patch('embercade.launcher.subprocess.run', return_value=subprocess.CompletedProcess([], 0)) as launch:
                    self.assertEqual(run_launch(plan), 0)
                resolve.assert_called_once_with(plan)
                self.assertEqual(popen.call_args.args[0][3], 'hyprland')
                launch.assert_called_once_with(plan.command, env=plan.environment, check=False)
                helper.stdin.close.assert_called_once()
                helper.wait.assert_called_once_with(timeout=2)

    def test_resource_validation_no_writes_and_missing_fallback(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            png = root / 'ps2.png'
            png.write_bytes(b'\x89PNG\r\n\x1a\n\0\0\0\rIHDR' + (1920).to_bytes(4) + (1080).to_bytes(4))
            info = root / 'ps2.info'
            info.write_text(json.dumps({'width': 1920, 'height': 1080, 'left': 240, 'right': 240}))
            data = {'emulator': 'pcsx2', 'png': str(png), 'info': str(info), 'options': {'pcsx2_ratio': '4:3', 'pcsx2_fmv_ratio': '4:3'}}
            before = {p: p.read_bytes() for p in root.iterdir()}
            self.assertEqual(validate_decoration(data, 'ps2', (root,)).png, png)
            self.assertEqual(before, {p: p.read_bytes() for p in root.iterdir()})
            self.assertIsNone(validate_decoration(data | {'png': None}, 'ps2', (root,)))
            self.assertIsNone(validate_decoration(data, 'xbox', (root,)))
            with self.assertRaises(ValueError):
                validate_decoration(data, 'ps2', (root / 'other',))
            info.write_text('{}')
            with self.assertRaises(ValueError):
                validate_decoration(data, 'ps2', (root,))
            info.unlink()
            with self.assertRaises(FileNotFoundError):
                validate_decoration(data, 'ps2', (root,))

    def test_none_and_dry_run_never_spawn_overlay(self):
        with patch('embercade.standalone_decoration.resolve_decoration', return_value=None) as resolve, patch('embercade.standalone_decoration.subprocess.Popen') as popen:
            with standalone_decoration(self.plan()):
                pass
            resolve.assert_called_once()
            popen.assert_not_called()
            resolve.reset_mock()
            for plan in (self.plan(dry_run=True), self.plan('ps3'), self.plan('xbox360'), self.plan('nes')):
                with standalone_decoration(plan):
                    pass
            resolve.assert_not_called()

    def test_failure_preserves_standalone_command_and_exit(self):
        for system in ('ps2', 'xbox', 'gamecube', 'wii'):
            with self.subTest(system=system), patch('embercade.standalone_decoration.resolve_decoration', side_effect=ValueError('missing art')), patch('embercade.launcher.subprocess.run', return_value=subprocess.CompletedProcess([], 7)) as run:
                plan = self.plan(system)
                self.assertEqual(run_launch(plan), 7)
                run.assert_called_once_with(plan.command, env={}, check=False)

    def test_helper_cleanup_on_success_and_launcher_exception(self):
        for system in ('ps2', 'xbox', 'gamecube', 'wii'):
            for failing in (False, True):
                with self.subTest(system=system, failing=failing):
                    helper = Mock(returncode=0)
                    with patch('embercade.standalone_decoration.resolve_decoration', return_value=self.decoration()), patch('embercade.standalone_decoration.decoration_backend', return_value='gamescope'), patch('embercade.standalone_decoration.subprocess.Popen', return_value=helper) as popen:
                        try:
                            with standalone_decoration(self.plan(system)):
                                if failing:
                                    raise RuntimeError('emulator failure')
                        except RuntimeError:
                            self.assertTrue(failing)
                        helper.stdin.close.assert_called_once()
                        helper.wait.assert_called_once_with(timeout=2)
                        helper.terminate.assert_not_called()
                        self.assertEqual(popen.call_args.args[0][3], 'gamescope')

    def test_helper_start_failure_does_not_block(self):
        with patch('embercade.standalone_decoration.resolve_decoration', return_value=self.decoration()), patch('embercade.standalone_decoration.decoration_backend', return_value='gamescope'), patch('embercade.standalone_decoration.subprocess.Popen', side_effect=OSError('missing GTK')):
            with standalone_decoration(self.plan()):
                reached = True
            self.assertTrue(reached)

    def test_unresponsive_helper_is_terminated_not_emulator(self):
        helper = Mock(returncode=0)
        helper.wait.side_effect = [subprocess.TimeoutExpired('helper', 2), 0]
        with patch('embercade.standalone_decoration.resolve_decoration', return_value=self.decoration()), patch('embercade.standalone_decoration.decoration_backend', return_value='gamescope'), patch('embercade.standalone_decoration.subprocess.Popen', return_value=helper):
            with standalone_decoration(self.plan()):
                pass
            helper.terminate.assert_called_once()
            self.assertEqual(helper.wait.call_count, 2)

    def test_wedged_renderer_cannot_survive_synchronous_cleanup(self):
        helper = Mock(returncode=-9)
        helper.wait.side_effect = [subprocess.TimeoutExpired('helper', 2), subprocess.TimeoutExpired('helper', 2), -9]
        with patch('embercade.standalone_decoration.resolve_decoration', return_value=self.decoration()), patch('embercade.standalone_decoration.decoration_backend', return_value='gamescope'), patch('embercade.standalone_decoration.subprocess.Popen', return_value=helper):
            with standalone_decoration(self.plan()):
                pass
            helper.kill.assert_called_once()
            self.assertEqual(helper.wait.call_count, 3)

    def test_upstream_selection_honors_none_game_and_user_overrides(self):
        project = Path(__file__).resolve().parents[1]
        runtime = project / '.work/runtime'
        python = runtime / 'venv/bin/python'
        if not python.exists():
            self.skipTest('prepared pinned runtime required')
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / 'batocera.conf'
            es_settings = root / 'user/system/configs/emulationstation/es_settings.cfg'
            es_settings.parent.mkdir(parents=True)
            es_settings.write_text('<config/>')
            env = os.environ | {
                'EMBERCADE_BATOCERA_SHARE_DIR': str(runtime / 'share/batocera'),
                'EMBERCADE_BATOCERA_CONF': str(config),
                'EMBERCADE_SYSTEM_DECORATIONS': str(root / 'resources'),
                'EMBERCADE_DESKTOP': '1',
                'EMBERCADE_USERDATA': str(root / 'user'),
            }
            def probe(text):
                config.write_text(text)
                result = subprocess.run(backend_command(python, 'resolve-decoration', 'ps2', '/roms/Test Game.iso'), env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            system_png = root / 'resources/default_unglazed/systems/ps2.png'
            system_png.parent.mkdir(parents=True)
            system_png.touch()
            self.assertIsNone(probe('ps2.bezel=none\n')['png'])
            self.assertEqual(probe('ps2.bezel=none\n')['options']['pcsx2_fmv_ratio'], '')
            self.assertEqual(probe('global.bezel=consoles\n')['png'], str(system_png))
            user_game = root / 'user/decorations/default_unglazed/games/ps2/Test Game.png'
            user_game.parent.mkdir(parents=True)
            user_game.touch()
            self.assertEqual(probe('global.bezel=consoles\n')['png'], str(user_game))
            self.assertIsNone(probe('global.bezel=consoles\nps2["Test Game.iso"].bezel=none\n')['png'])
            for system in ('gamecube', 'wii'):
                system_png = root / f'resources/default_unglazed/systems/{system}.png'
                system_png.touch()
                def dolphin_probe(text):
                    config.write_text(text)
                    result = subprocess.run(backend_command(python, 'resolve-decoration', system, '/roms/Test Game.iso'), env=env,
                                            text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    return json.loads(result.stdout)
                self.assertIsNone(dolphin_probe(f'{system}.bezel=none\n')['png'])
                selected = dolphin_probe(f'{system}.bezel=consoles\n')
                self.assertEqual(selected['emulator'], 'dolphin')
                self.assertEqual(selected['png'], str(system_png))
                self.assertEqual(selected['options']['dolphin_aspect_ratio'], '')


if __name__ == '__main__':
    unittest.main()
