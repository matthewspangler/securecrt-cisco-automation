import os


def run_script(script_full_path):
    exec(open(script_full_path).read(), globals(), locals())


def do_script_all_tabs(crt, script_full_path):
    initialTab = crt.GetScriptTab()

    # Activate each tab in order from left to right, and issue the command in
    # each "connected" tab...
    skippedTabs = ""
    for i in range(1, crt.GetTabCount() + 1):
        tab = crt.GetTab(i)
        tab.Activate()
        # Skip tabs that aren't connected
        if tab.Session.Connected == True:
            run_script(script_full_path)
        else:
            if skippedTabs == "":
                skippedTabs = str(i)
            else:
                skippedTabs = skippedTabs + "," + str(i)

    # Now, activate the original tab on which the script was started
    initialTab.Activate()

    # Determine if there were any skipped tabs, and prepare a message for
    # displaying at the end.
    if skippedTabs != "":
        skippedTabs = "\n\n\The following tabs did not receive the command because\n\
    they were not connected at the time:\n\t" + skippedTabs


def get_script_full_path(self, script_name):
    script_dir, script_name = os.path.split(self.crt.ScriptFullName)
    return os.path.join(script_dir, script_name)