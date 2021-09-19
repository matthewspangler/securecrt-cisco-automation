# $language = "Python3"
# $interface = "1.0"

from runners.cisco.cisco_runner import CiscoRunner


class XE(CiscoRunner):
    def __init__(self, crt, current_tab):
        CiscoRunner.__init__(self, crt, current_tab)
        self.line_matches = ["\r\n", '\r', '\n', '--More--']

    def __str__(self):
        return '<Class: XE>'

    def get_hostname(self):
        """
        Method to get the value of the hostname variable
        :return:
            Hostname set in running-config of Cisco device
        """
        return self.get_command_output("sh run | i hostname")[0].split("hostname ")[1]
