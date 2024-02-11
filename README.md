# wrapwine

A simple (and very early alpha) WINE wrapper with a per-file based configuration system.

With primary focus on _running_ and _getting_ WINE "setups" - not installing (for now).

The project might change scope or goal, and as such, this README is not necessarily up to date. Please open an issue if you find something missing or incorrect.

Please keep in mind that given the age of the project, many things that you would expect in a WINE runner is not present, such as managing log files, killing the prefix' wineserver, or easily doing built-in WINE things like regedit, joy.cpl, etc.

License TBA

## Features and goals

- [rofi-script](https://davatorium.github.io/rofi/current/rofi-script.5/) compatible
    - Currently, only uses the `nonselectable` feature to prevent invalid WINE "units" from being called. PR's are welcome to add better integration.
- Minimal assumptions on existing WINE configuration; if you don't actively set it, it doesn't happen
    - Except for `WINEDEBUG` which should be set to `-all` while running in "release" as per WINE documentation. Set it manually if you don't want this to happen.
    - There is currently ONE exception to this to better handle breaking WINE patchsets (setting `STAGING_AUDIO_PERIOD` when not set, only used with wine-osu patchset)
- Python API (unstable and undocumented)
    - Running the program associated with the WINE unit and blocking until the program closes
    - Launching a shell with the relevant environment variables set (useful for debugging WINE patchsets etc)
    - `unit.get_fancy_title()` adds informational text to the title (e.g. is the PREFIX remote, is the config bad, etc)
- Configuration similar to BASH/SH variable syntax 
    - Supports inline assignment of environment variables, like `WINEPREFIX=${HOME}/mypath` (see example)
    - Supports start-of-line comments (`#`)
- Runner "blocks" as long as the `wineserver` for the prefix is still running

## Dependencies

Optionally:

- WINE (for launching)
- rofi (for listing and selecting options)

## Handled environment variables

See [examples](#examples) for a simple bare-bones example. This section explains the additional features currently available

### Custom WINE version support

Set `W` to the path of your alternative WINE install. The program will (internally) prepend this path+`/bin` to your current PATH.

### Custom prepend and append arguments

Set `PREPENDS` to prepend this to the WINE command

Set `ARGS` to append this to your game exe. E.g:
```sh
FILENAME="myfile.exe"
PREPENDS="gamescope"
ARGS="--nosound"
```

### Feral Interactive game mode support

Set `GAMEMODE` to any value, e.g. `GAMEMODE=y`
This prepends `gamemoderun` to the very front of the command, before your provided prepends. If you want to place it elsewhere, set `PREPENDS` manually.

### Force-skipping the unit

Set `IGNORE` to any value, e.g. `IGNORE=y`

## Examples

### Simple example with rofi

wrapwine file, e.g. `~/.wrapwines/my-game`:

```conf
# This line starts with a # and as such is a comment
# TITLE is the title used for the environment
TITLE="My Game"
# The location of the WINEPREFIX. See WINE documentation on WINEPREFIX
WINEPREFIX="${HOME}/.wineprefixes/my-game"
# or:
#WINEPREFIX="~/.wineprefixes/my-game"
# The relative path of the application/game dir in relation to your WINEPREFIX
GAMEDIR="drive_c/my-game"
# The relative file name of the application/game filename in relation to the GAMEDIR
FILENAME="mygame.exe"
```

then run `rofi-wrapper.sh` as rofi script:

```sh
rofi -modi wrapwine:/path/to/git/root/rofi-wrapper.sh -show wrapwine
```

This should result in "My Game" showing up as a clickable entry, assuming you defined everything else correctly.

### osu! stable

Wrapwine configuration `~/.wrapwines/osu-stable`:
```conf
TITLE="osu! Stable"
WINEPREFIX="${HOME}/.wineprefixes/osu"
GAMEDIR="${WINEPREFIX}/drive_c/osu/"
FILENAME="osu!.exe"

# use custom WINE version
W="/opt/wine-osu"
# set a custom arg (export is optional)
export STAGING_AUDIO_PERIOD=6666
```

### Python example

```py
import wrapwine

my_file = "/path/to/wrapwine/file"

# load your wrapwine unit
ww = wrapwine.unit(my_file)

# launch wine on unit
ww.launch()
```

Alternatively, see `rofi.py` for usage

## Troubleshooting

If things aren't working, pay attention to STDERR (the output going into your terminal) as this will tell you about any eventual errors.

Optionally, make sure `DEBUG` is set to `True` in `/conf.py`

I won't provide direct support on the project yet, but developers are welcome to open issues.
