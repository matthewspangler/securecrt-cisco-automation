# $language = "Python3"
# $interface = "1.0"

from runners.cisco.cisco_runner import CiscoRunner


class AireOS(CiscoRunner):
    def __init__(self, crt, current_tab):
        CiscoRunner.__init__(self, crt, current_tab)
        self.line_matches = ["\r\n", '\r', '\n',
                             'Press Enter to continue...',
                             'Press Enter to continue or <[Cc]trl-[Zz]> to abort',
                             '--More or (q)uit current module or <[Cc]trl-[Zz]> to abort', '--More-- or (q)uit']

    def __str__(self):
        return '<Class: AireOS>'