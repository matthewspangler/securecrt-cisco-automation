# $language = "Python3"
# $interface = "1.0"

from runners.cisco.cisco_runner import CiscoRunner


class XR(CiscoRunner):
    def __init__(self, crt, current_tab):
        CiscoRunner.__init__(self, crt, current_tab)
        # TODO: create line matches for the XR class!
        self.line_matches = None

    def __str__(self):
        return '<Class: XR>'

    def enable_cdp_global(self):
        self.global_config()
        self.send("cdp \r")

    def enable_cdp_intf(self, interface):
        self.goto_intf_config(interface)
        self.send("cdp \r")
        self.send("no shut \r")