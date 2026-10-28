from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import unittest


PROJECT = Path(__file__).resolve().parents[1]


class StartupSplashTests(unittest.TestCase):
    def test_actual_native_deadline_fast_slow_error_and_tick_wrap(self):
        compiler = shutil.which("c++")
        if not compiler:
            self.skipTest("C++ compiler needed for native timing contract")
        with TemporaryDirectory() as directory:
            binary = Path(directory) / "timing-test"
            source = '''
#include "EmbercadeStartupSplash.h"
#include <cassert>
int main() {
    using Embercade::StartupSplashDeadline;
    StartupSplashDeadline fast(100);
    assert(fast.remaining(200) == 2650);
    assert(fast.elapsed(200) == 100);
    assert(fast.remaining(2849) == 1);
    assert(fast.remaining(2850) == 0);
    assert(fast.remaining(10100) == 0); // slow load: no extra wait
    assert(fast.remaining(200, true) == 0); // error: immediate cleanup
    StartupSplashDeadline wrap(0xfffffff0u);
    assert(wrap.remaining(0x54u) == 2650);
}
'''
            subprocess.run([compiler, "-std=c++11", "-x", "c++", "-",
                            "-I", str(PROJECT / "patches/emulationstation"),
                            "-o", str(binary)], input=source, text=True, check=True,
                           capture_output=True)
            subprocess.run([str(binary)], check=True, timeout=5)

    def test_only_native_startup_is_gated_and_failures_close_without_wait(self):
        patch = (PROJECT / "patches/emulationstation/0003-embercade-startup-splash.patch").read_text()
        self.assertIn('splashScreen && embercadePolicy', patch)
        self.assertIn('StartupSplashDeadline splashDeadline(SDL_GetTicks())', patch)
        self.assertIn('errorMsg != nullptr', patch)
        self.assertIn('SDL_QUIT, SDL_QUIT', patch)
        self.assertIn('window.closeSplashScreen()', patch)
        self.assertIn('Renderer::deinit()', patch)
        self.assertNotIn('renderSplashScreen', patch)  # no second splash or blank swap
        self.assertNotIn('sleep(', patch)
        text = (PROJECT / "scripts/ui-build").read_text()
        self.assertIn('0003-embercade-startup-splash.patch', text)
        self.assertIn('EmbercadeStartupSplash.h', text)
        self.assertIn('"$project_root/scripts/ui-build" "$@"', (PROJECT / "scripts/stage-build").read_text())
