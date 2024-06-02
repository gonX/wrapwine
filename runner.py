# wine runner
import os, subprocess
import conf, unit
from util import *

# TODO:
#   - ISOLOC/ISODIR support
#     - Must fallback to 'isomount' folder if no ISODIR specified
#   - gamemode support
class Runner:
    DEFAULT_WINE_AUDIO_PERIOD_SIZE = 100000
    GAMEMODE_COMMAND = "gamemoderun"
    ENV_DEFAULTS = { # don't set anything too crazy here, it will affect ALL programs
            "WINEDEBUG": "-all"
        }

    def __init__(self, unit):
        if unit.skip or not unit.is_usable():
            raise Exception("Only runnable units are supported")
        self._unit = unit
        self._env = None
        self._wd = self._unit.gamedir
        self._initial_env = os.environ

    # FIXME: move to util class
    @staticmethod
    def _find_wine(wine_path):
        paths_to_try = [
            "usr/bin",
            "bin"
        ]
        for path in paths_to_try:
            new_path = os.path.join(wine_path, path)
            wine_file = os.path.join(new_path, "wine")
            if os.path.isfile(wine_file):
                debug(f"found wine in {new_path}")
                return new_path

        debug(f"could not find wine")
        return None

    # returns True/False on whether start_shell will work
    def is_interactive(self):
        if not sys.stdout.isatty():
            return False
        if not sys.stdout or not sys.stdin or not sys.stderr:
            return False
        return True

    def init_env(self):
        if self._env:
            debug("Runner: Reinitializing env")
        self._env = self._initial_env

        unit_vars = self._unit.get_vars()
        # import everything
        for var in unit_vars:
            debug(f"var: {var.key}")
            self._env[var.key] = var.value

        # handle W
        wine = unit_vars.get_by_key("W")
        if wine:
            wine.expand(unit_vars)
            wine = wine.value
            if not os.path.isdir(wine):
                stderr(f"Runner: W path is not a dir: '{wine}'")
                return False

            if "PATH" in self._initial_env:
                orig_path = self._initial_env["PATH"]
                new_wine_path = self._find_wine(wine)
                new_path = f"{new_wine_path}:{orig_path}"
                self._env["PATH"] = new_path
                debug(f"new path: {new_path}")

            if not "STAGING_AUDIO_PERIOD" in unit_vars:
                debug(f"custom wine versions gets STAGING_AUDIO_PERIOD set to {self.DEFAULT_WINE_AUDIO_PERIOD_SIZE}")
                self._env["STAGING_AUDIO_PERIOD"] = str(self.DEFAULT_WINE_AUDIO_PERIOD_SIZE)

        for env_default in self.ENV_DEFAULTS:
            val = self.ENV_DEFAULTS[env_default]
            if env_default not in self._env:
                debug(f"adding {env_default}={val} to env")
                self._env[env_default] = val

        return True

    # launch subshell attached to stdout/stdin
    # relevant env args are set
    def start_shell(self):
        if not self._env:
            raise Exception("Env must be initialized before running this")
        if not self.is_interactive():
            debug("Cannot start shell in non-interactive mode")
            return False
        shell = self._initial_env["SHELL"]
        if not os.path.exists(shell):
            raise Exception("invalid shell {shell}")
        stderr("Subshell is now active!")
        command = self._unit.get_run_command()
        stderr(f"Run command: {' '.join(command)}")
        # TODO: display more stuff? prepends? gamemode? args?
        subprocess.run(shell, env=self._env, cwd=self._wd)

    # launches wine
    def start_unit(self):
        if not self._env:
            raise Exception("Env must be initialized before running this")

        command = self._unit.get_run_command()
        if "GAMEMODE" in self._env:
            stderr("Using gamemode")
            command.insert(0, self.GAMEMODE_COMMAND)

        subprocess.run(command, env=self._env, cwd=self._wd)

    def wait_command(self, command = [ "wineserver", "-w" ]):
        if not self._env:
            raise Exception("Env must be initialized before running this")
        stderr("Waiting for background processes to clean up")
        return subprocess.run(command, env=self._env)

    def run(self):
        if not self.init_env():
            stderr("Could not initialize env")
            return False
        if self.is_interactive():
            self.start_shell()
        rv = self.start_unit()
        if rv:
            stderr("return value: {rv}")
        return self.wait_command()
