# $language = "Python3"
# $interface = "1.0"

from runners.cisco.cisco_runner import CiscoRunner


class ASA(CiscoRunner):
    def __init__(self, crt, current_tab):
        CiscoRunner.__init__(self, crt, current_tab)
        self.line_matches = ["\r\n", '\r', '\n', '<--- More --->']

    def __str__(self):
        return '<Class: ASA>'

    def show_intf_brief(self):
        self.priv_exec()
        return self.get_command_output("sh int ip br")

    def save_changes(self):
        self.send("copy run start \r", "running-config")
        self.send("\r")