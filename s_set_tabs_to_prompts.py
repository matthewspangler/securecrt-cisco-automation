# $language = "Python3"
# $interface = "1.0"

import os
import sys
from ciscoconfparse import CiscoConfParse

# Avoids errors in IDE's that can't detect the crt variable:
global crt

# Adds script directory to PYTHONPATH,
# so we can import local modules when running common_tasks from SecureCRT
script_dir = None
if 'crt' in globals():
    script_dir, script_name = os.path.split(crt.ScriptFullName)
if script_dir not in sys.path:
    sys.path.append(script_dir)
else:
    script_dir, script_name = os.path.split(os.path.realpath(__file__))

# Local import
import runners
from crt_automation.sessions import CrtSession


# Main function and script logic here:
def main():
    scrt = CrtSession(crt)
    # Discover OS:
    scrt.active_session.start_cisco_session()
    # Validate script is compatible with OS:
    scrt.active_session.validate_os(["IOS", "XE", "NXOS", "ASA", "WAAS"])
    # Make runner easier to type:
    nos = scrt.active_session.runner

    nos.response_timeout = 5  # 5 seconds

    # Get a reference to the tab that was active when this script was launched.
    initial_tab = crt.GetScriptTab()

    # Activate each tab in order from left to right, and issue the command in
    # each "connected" tab...
    skipped_tabs = ""
    for i in range(1, crt.GetTabCount() + 1):
        tab = crt.GetTab(i)
        tab.Activate()
        # Skip tabs that aren't connected
        if tab.Session.Connected == True:
            nos.current_tab = tab
            nos.set_prompt()
        else:
            if skipped_tabs == "":
                skipped_tabs = str(i)
            else:
                skipped_tabs = skipped_tabs + "," + str(i)

        # Now, activate the original tab on which the script was started
        initial_tab.Activate()

        # Determine if there were any skipped tabs, and prepare a message for
        # displaying at the end.
        if skipped_tabs != "":
            skipped_tabs = "\n\n\The following tabs did not receive the command because\n\
    they were not connected at the time:\n\t" + skipped_tabs

    return


main()
