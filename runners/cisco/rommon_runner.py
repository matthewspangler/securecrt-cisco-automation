# $language = "Python3"
# $interface = "1.0"

from runners.common_runner import CommonRunner
import re


class ROMMON(CommonRunner):
    def __init__(self, crt, current_tab=None):
        CommonRunner.__init__(self, crt, current_tab)
        # Regex catches the following prompts: 'loader >', 'loader>', 'switch:', 'rommon # >', '>', '?'
        # (test on https://regex101.com/)
        self.prompt_regex = re.compile(r'^.*>|^.*\?|switch:')
        self.rommon_prompts = ['loader >', 'loader>', 'switch:', '>', '?']
        # TODO: make regular expression that looks for any of the ROMMON prompts
        self.line_matches = ["\r\n", '\r', '\n']

    def set_prompt(self):
        """
        Method to set the self.prompt variable, which contains the entire ROMMON prompt.
        """
        screen_row = self.current_tab.Screen.CurrentRow + 0
        read_line = self.current_tab.Screen.Get(screen_row, 1, screen_row, 120)
        try:
            prompt = re.search(self.prompt_regex, read_line).group(0)
        except AttributeError:
            prompt = 'UNKNOWN'

        self.current_tab.Caption = prompt

        self.prompt = prompt