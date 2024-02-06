## User configurables:
DEBUG = True # spam stderr with useless stuff
TITLE = "Wrapwine Scanner (python)" # title used for dmenu

## Change with care:
# COMMAND is used when outputting the command list
# Arguments:
#   {File} -- the path to the wrapwine unit
COMMAND = "wrapwine '{File}' --nobash"
