# $language = "Python3"
# $interface = "1.0"

from runners.cisco.cisco_runner import CiscoRunner


class NXOS(CiscoRunner):
    def __init__(self, crt, current_tab):
        CiscoRunner.__init__(self, crt, current_tab)
        self.line_matches = ["\r\n", '\r', '\n', '--More--']

    def __str__(self):
        return '<Class: NXOS>'

    def show_intf_brief(self):
        self.priv_exec()
        return self.get_command_output("sh int br")

    def save_changes(self):
        """
        Sends "copy run start" or equivalents with boilerplate code for different OS's like XE, XR, etc.
        :return:
        """
        # TODO - write a version of this function for the XR class
        # NXOS shows lots of '#' when saving the running-config, which screws with set_prompt.
        # Thus, we need to avoid self.send() which calls set_prompt()
        self.current_tab.Screen.Send("copy run start \r")
        self.current_tab.Screen.WaitForString("Copy complete.", 10)
        self.send("\r")
        self.send("\r")