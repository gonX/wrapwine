# wine runner
import os, subprocess
import conf, unit
from util import *

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
        self._cleanup_commands = []
        self._iso_mounted = False

    # FIXME: doesn't work great in case of exceptions, maybe use a context manager around the run call instead?
    def __del__(self):
        while self._cleanup_commands:
            self._cleanup_commands.pop()()

    # FIXME: move to util class
    @staticmethod
    def _find_wine(wine_path):
        paths_to_try = [
            "usr/bin",
            "bin-wow64",
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

    def needs_iso_mount(self):
        if not self._env:
            raise Exception("Env must be initialized before running this")

        return all(x in self._env for x in ["ISOLOC", "ISO_DRIVE_LETTER"])

    def get_iso_mount_path(self):
        if not self.needs_iso_mount():
            return None

        return os.path.join(self._unit.wineprefix, self._env["ISODIR"])

    def unmount_iso(self, force_run=False):
        if not force_run and not self._iso_mounted:
            raise ValueError("Tried to unmount iso without mount_iso() having been run")

        subprocess.run(["fusermount", "-u", self.get_iso_mount_path()], check=~force_run)
        stderr("Successfully unmounted iso")
        self._iso_mounted = False

    def _configure_driveletter(self, drive_letter):
        if not "ISODIR" in self._env:
            raise ValueError("need ISODIR to configure a drive letter")

        basedir = self._unit.wineprefix
        relative_path_driveletter = f"dosdevices/{drive_letter}:"
        wine_path = os.path.join(basedir, relative_path_driveletter)
        if os.path.islink(wine_path):
            print(f"remove {wine_path}")
            os.remove(wine_path)

        if not os.path.isfile(wine_path):
            isodir = self._env["ISODIR"]
            os.symlink(f"../{isodir}", wine_path)
        else:
            raise ValueError("This does not seem like a proper WINE dosdevices dir")

    def mount_iso(self):
        if not "ISODIR" in self._env:
            self._env["ISODIR"] = "isomount"
        mountpath = self.get_iso_mount_path()
        if not os.path.isdir(mountpath):
            stderr(f"Creating dir {mountpath}")
            os.mkdir(mountpath)
        elif os.path.ismount(mountpath):
            stderr("Mountpath seems already mounted, trying to unmount it first..")
            self.unmount_iso(force_run=True)

        subprocess.run(["fuseiso", self._env["ISOLOC"], mountpath], check=True)
        self._iso_mounted = True
        self._cleanup_commands.append(self.unmount_iso)
        self._configure_driveletter(self._env["ISO_DRIVE_LETTER"])

    def init_env(self):
        if self._env:
            debug("Runner: Reinitializing env")
        self._env = self._initial_env

        unit_vars = self._unit.get_vars()
        # import everything
        for var in unit_vars:
            debug(f"var: {var.key}: {var.value}")
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

            if not "STAGING_AUDIO_PERIOD" in self._initial_env:
                debug(f"custom wine versions gets STAGING_AUDIO_PERIOD set to {self.DEFAULT_WINE_AUDIO_PERIOD_SIZE}")
                self._env["STAGING_AUDIO_PERIOD"] = str(self.DEFAULT_WINE_AUDIO_PERIOD_SIZE)

        for env_default in self.ENV_DEFAULTS:
            val = self.ENV_DEFAULTS[env_default]
            if env_default not in self._env:
                debug(f"adding {env_default}={val} to env")
                self._env[env_default] = val

        if self.needs_iso_mount():
            self.mount_iso()

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
