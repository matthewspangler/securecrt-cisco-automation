# $language = "Python3"
# $interface = "1.0"

import os
import sys

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
import runners.cisco


# Main function and script logic here:
def main():

    # TODO: maybe add code to reload if device is found in mode higher than priv exec?

    net_os = runners.cisco.ROMMON(crt)
    # Reload in case not yet in boot process:
    net_os.crt.Dialog.MessageBox("Please reload the switch from IOS.")
    net_os.current_tab.Screen.WaitForStrings(["Proceed with", "confirm"], 1000)
    net_os.current_tab.Screen.Send("\r")

    result = None
    while not result:
        # send all break keys and check for possible prompts
        net_os.current_tab.Screen.Send('\003')  # Ctrl+c
        net_os.current_tab.Screen.Send('\035')  # Ctrl+]
        net_os.current_tab.Screen.Send('\014')  # Ctrl+l
        net_os.current_tab.Screen.Send('\020')  # Ctrl+p
        net_os.current_tab.Screen.SendSpecial('TN_BREAK')  # Break key

        # Check for ROMMON prompts
        result = net_os.crt.Screen.WaitForStrings(net_os.rommon_prompts, 1)

    return net_os


main()
