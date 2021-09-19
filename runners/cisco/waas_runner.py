# $language = "Python3"
# $interface = "1.0"

from runners.cisco.cisco_runner import CiscoRunner


class WAAS(CiscoRunner):
    def __init__(self, crt, current_tab):
        CiscoRunner.__init__(self, crt, current_tab)
        self.line_matches = ["\r\n", '\r', '\n', '--More--']

    def __str__(self):
        return '<Class: WAAS>'