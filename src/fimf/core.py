import os
import re
from collections import defaultdict
import fnmatch
from collections import UserDict

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.screen import Screen
from textual.widgets import Static, Input, Footer, Button, TextLog, Label
from textual import log


# note: log-output is visible if this application is stated with `textual run --dev <script.py>`
# and `textual console` in another window


class PartneredTextLog(TextLog):
    """
    This class implements scrolling such that any scrolling event also triggers the scrolling of a partner widget.
    """

    # Down
    def scroll_down(self, *args, **kwargs):
        self.pure_scroll_down(*args, **kwargs)
        self.partner.pure_scroll_down(*args, **kwargs)

    def pure_scroll_down(self, *args, **kwargs):
        super().scroll_down(*args, **kwargs)

    # Up
    def scroll_up(self, *args, **kwargs):
        self.pure_scroll_up(*args, **kwargs)
        self.partner.pure_scroll_up(*args, **kwargs)

    def pure_scroll_up(self, *args, **kwargs):
        super().scroll_up(*args, **kwargs)


class CustomApp(App):
    CSS_PATH = "fimf.css"
    BINDINGS = [
        ("f1", "help", "show help"),
        ("f3", "do_search", "search"),
        ("escape", "cmd_select", "command mode"),
        ("p", "plain_text_select", "mode: plain text"),
        ("e", "escape_seq_select", "mode: escape-sequences"),
        ("t", "regex_select", "mode: regex"),
    ]

    def compose(self) -> ComposeResult:

        self.intro = Label("fimf – find and replace in multiple files", id="lb_intro")
        self.input_files = Input(placeholder="file pattern", id="in_files", classes="input_field")
        self.input_search = Input(placeholder="search pattern", id="in_search", classes="input_field")
        self.input_replace = Input(placeholder="replace pattern", id="in_replace", classes="input_field")

        self.button_search = Button("Search (F3)", id="btn_search", variant="primary")
        self.button_replace = Button("Replace All", id="btn_replace", variant="warning")
        self.button_quit = Button("Quit (CTRL+C)", id="btn_quit", variant="error")
        self.label_results = Label("Results", id="lb_results")
        self.search_results = PartneredTextLog(markup=True, id="tl_search_res", classes="results")
        self.replace_results = PartneredTextLog(markup=True, id="tl_replace_res", classes="results")

        self.search_results.partner = self.replace_results
        self.replace_results.partner = self.search_results

        self.statusbar = Label("no search results yet", id="statusbar", classes="")

        self.search_result = None

        yield self.intro
        with Horizontal(id="cntn_input_fields"):
            yield self.input_files
            yield self.input_search
            yield self.input_replace

        with Horizontal(id="cntn_buttons"):
            yield self.button_search
            yield self.button_replace
            yield self.button_quit

        with Horizontal(id="cntn_results"):
            yield self.search_results
            yield self.replace_results

        yield self.statusbar
        yield Footer()

    def on_mount(self) -> None:
        # self.input_files.focus()
        self.input_search.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:

        if event.button.id == "btn_search":
            self.action_do_search()
        elif event.button.id == "btn_quit":
            self.exit()
        elif event.button.id == "btn_replace":
            self.action_do_replace()
        else:
            # !! unexpected -> raise exception
            pass

    def on_input_submitted(self, message: Input.Submitted) -> None:
        print("xxx", dir(message), message.sender, message.value)
        self.screen.focus_next()

    def action_help(self) -> None:
        """toogle help"""
        self.push_screen(HelpScreen())

    def action_cmd_select(self) -> None:
        self.screen.set_focus(None)

    def action_do_search(self):
        file_pattern = self.input_files.value
        search_pattern = self.input_search.value
        replace_pattern = self.input_replace.value

        # for testing
        if not file_pattern:
            file_pattern = "*"
        if not search_pattern:
            search_pattern = "abcde"
            self.input_search.insert_text_at_cursor(search_pattern)
        if not replace_pattern:
            replace_pattern = "ABC"
            self.input_replace.insert_text_at_cursor(replace_pattern)

        self.search_results.clear()
        self.replace_results.clear()
        if not search_pattern:
            self.search_results.write("error: empty search pattern")
            return

        try:
            search_pattern = re.compile(search_pattern)
        except re.error as ex:
            self.search_results.write(f"regex error: {ex}")
            return


        startpath = os.path.abspath("./")
        results = find_pattern(startpath, search_pattern, file_pattern, replace_pattern)
        indent = " " * 0

        file_count = 0
        match_count = 0

        for path, matches in results.items():
            if not matches:
                continue

            localpath = path.replace(startpath, "./")
            lm = len(matches)
            file_count += 1
            match_count += lm
            self.search_results.write(f"[#ffcc00 on #6f94dc]{localpath} ({lm})")
            self.replace_results.write(f"[#ffcc00 on #6f94dc]{localpath} ({lm})")
            for match_obj in matches:
                lnbr = f"[white on blue]{match_obj.line_number:03d}:[/] "
                self.search_results.write(f"{indent}{lnbr}{match_obj.context_str}")
                self.replace_results.write(f"{indent}{lnbr}{match_obj.context_rpl_str}")

            # add an empty line after each file
            self.search_results.write(" ")
            self.replace_results.write(" ")

        # improve visual presentation of the result
        self.search_results.focus()
        self.statusbar.update(f"found {match_count} matches in {file_count} files (of {results.total_files} files)")
        self.statusbar.add_class("sb_active")

    def action_do_replace(self):
        if self.search_result is None:
            log("Cannot replace: no search result available.")


class HelpScreen(Screen):
    def compose(self) -> ComposeResult:

        self.btn_cancel = Button("Cancel (go back)", variant="primary", id="cancel")
        self.btn_quit = Button("Quit", variant="error", id="quit")

        yield Grid(
            Static("This modal dialog will be the help screen in the future", id="question"),
            self.btn_cancel,
            self.btn_quit,
            id="dialog",
        )

    def on_mount(self):
        self.btn_cancel.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()

class Match():

    def __init__(self, line_number, line, match, rplmt=None):
        self.line_number = line_number
        self.line = line.rstrip("\n")
        self.re_match = match

        i_start, i_end = match.span(0)

        full_match = match.group(0)
        l_max = 50
        l_match = i_end - i_start
        diff = l_max - l_match
        l_line = len(line)
        if diff < 10:
            # there is no space for context
            hl_txt = full_match[:l_max]
            txt0 = ""
            txt1 = ""
        else:
            l0 = (diff//2)
            l1 = diff - l0
            # padding of the line

            i0 = i_start - l0
            if i0 < 0:
                i0 = 0

            i1 = i_end + l1
            if i1 > l_line:
                i1 = l_line
            hl_txt = full_match
            txt0 = line[i0:i_start]
            txt1 = line[i_end:i1]

        self.context_str = f"…{txt0}[#F0A0F0 on #305030]{hl_txt}[/]{txt1.rstrip()}…"

        if rplmt is not None:
            self.context_rpl_str = f"…{txt0}[#F0A0F0 on #303050]{rplmt}[/]{txt1.rstrip()}…"
        else:
            self.context_rpl_str = self.context_str


def find_matches(filename, compiled_pattern, replace_pattern):
    matches = []
    with open(filename, "r") as f:
        for i, line in enumerate(f, start=1):
            for match in re.finditer(compiled_pattern, line):
                matches.append(Match(i, line, match, replace_pattern))
    return matches


def find_pattern(directory, search_pattern, file_pattern, replace_pattern):
    results = UserDict()
    results.total_files = 0
    for path, dirs, files in os.walk(os.path.abspath(directory)):
        for filename in fnmatch.filter(files, file_pattern):
            results.total_files += 1
            filepath = os.path.join(path, filename)
            matches = find_matches(filepath, search_pattern, replace_pattern)
            results[filepath] = matches

    return results


def findReplace(directory, find, replace, filePattern):
    for path, dirs, files in os.walk(os.path.abspath(directory)):
        for filename in fnmatch.filter(files, filePattern):
            filepath = os.path.join(path, filename)
            with open(filepath) as f:
                s = f.read()
            s = s.replace(find, replace)
            with open(filepath, "w") as f:
                f.write(s)


def main():

    app = CustomApp()
    app.run()


if __name__ == "__main__":
    main()
