# $language = "Python3"
# $interface = "1.0"

from runners.common_runner import CommonRunner
import re


class LinuxRunner(CommonRunner):
    def __init__(self, crt, current_tab):
        CommonRunner.__init__(self, crt, current_tab)
        self.prompt_regex = re.compile(r'^.*#|^.*$')
