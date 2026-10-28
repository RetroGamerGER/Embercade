"""Structural validation of the pinned PS4 generator, without booting content."""

from pathlib import Path
import json
import shlex
import subprocess

from embercade.launcher import LaunchPlan, LaunchError
from embercade.paths import EmbercadePaths


def execute_dry_run(plan: LaunchPlan, paths: EmbercadePaths) -> dict:
    if plan.system != "ps4" or not plan.dry_run:
        raise LaunchError("PS4 structural verification requires a dry-run plan")
    result = subprocess.run(plan.command, env=dict(plan.environment),
                            cwd=plan.working_directory, capture_output=True,
                            text=True, timeout=60, check=False)
    if result.returncode:
        raise LaunchError(result.stderr.strip() or result.stdout.strip())
    marker = "EMBERCADE_FINAL_COMMAND="
    commands = [shlex.split(line[len(marker):]) for line in result.stdout.splitlines()
                if line.startswith(marker)]
    eboot = plan.rom / "eboot.bin" if plan.rom.is_dir() else plan.rom
    executable = plan.environment.get("EMBERCADE_SHADPS4_BIN", str(plan.executable))
    expected = [executable, "-g", str(eboot), "--fullscreen", "true"]
    if commands != [expected]:
        raise LaunchError("PS4 generator did not emit the exact resolved command/content arguments")
    settings_file = paths.emulator_configs / "shadPS4/config.json"
    settings = json.loads(settings_file.read_text())
    for field, variable in (("home_dir", "EMBERCADE_SHADPS4_SAVES"),
                            ("addon_install_dir", "EMBERCADE_SHADPS4_ADDONS")):
        if settings["General"][field] != plan.environment[variable]:
            raise LaunchError(f"PS4 {field} is not isolated")
    if not (settings_file.parent / "input_config").is_dir():
        raise LaunchError("PS4 input configuration directory is missing")
    return {"command": commands[0], "config": str(settings_file), "settings": settings}
