import os
import re
import fnmatch
from collections import UserDict

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static, Input, Footer, Button, TextLog, Label, ListView, ListItem
from textual import log


# note: log-output is visible if this application is stated with `textual run --dev main.py`
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


class MainScreen(Screen):
    BINDINGS = [
        ("f1", "help", "help"),
        ("f3", "do_search", "search"),
        ("f4", "do_replace", "replace"),
        ("f9", "screenshot", "screenshot"),
        ("f10", "open_menu", "menu"),
    ]

    def compose(self) -> ComposeResult:

        self.intro = Label("fimf – find and replace in multiple files", id="lb_intro")
        self.intro_hint = Label("(use TAB or Shift+TAB to navigate)", id="lb_intro_hint")
        self.input_files = Input(placeholder="file pattern", id="in_files", classes="input_field")
        self.input_search = Input(placeholder="search pattern", id="in_search", classes="input_field")
        self.input_replace = Input(placeholder="replace pattern", id="in_replace", classes="input_field")

        self.button_search = Button("search (F3)", id="btn_search", variant="primary")
        self.button_replace = Button("replace all (F4)", id="btn_replace", variant="warning")
        self.button_menu = Button("Menu (F10)", id="btn_menu")
        self.label_results = Label("Results", id="lb_results")
        self.search_results = PartneredTextLog(markup=True, id="tl_search_res", classes="results")
        self.replace_results = PartneredTextLog(markup=True, id="tl_replace_res", classes="results")

        self.search_results.partner = self.replace_results
        self.replace_results.partner = self.search_results

        self.statusbar = Label("no search results yet", id="statusbar")

        self.startpath = os.path.abspath("./")
        self.workdirbar = Label(f"workdir: {self.startpath}", id="workdirbar")

        self.search_result_store = None

        with Vertical(id="cntn_intro"):
            yield self.intro
            yield self.intro_hint

        with Horizontal(id="cntn_input_fields2", classes="cntn_input_fields"):
            yield self.button_menu
            yield self.input_files

        with Horizontal(id="cntn_input_fields1", classes="cntn_input_fields"):
            yield self.input_search
            yield self.input_replace

        with Horizontal(id="cntn_buttons"):
            yield self.button_search
            yield self.button_replace

        with Horizontal(id="cntn_results"):
            yield self.search_results
            yield self.replace_results

        yield self.statusbar
        yield self.workdirbar
        yield self.app.modebar
        yield Footer()

    def on_mount(self) -> None:
        # self.input_files.focus()
        self.input_search.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:

        if event.button.id == "btn_search":
            self.action_do_search()
        elif event.button.id == "btn_menu":
            self.app.push_screen(MenuScreen())
        elif event.button.id == "btn_replace":
            self.action_do_replace()
        else:
            # !! unexpected -> raise exception
            pass

    def on_input_submitted(self, message: Input.Submitted) -> None:
        self.screen.focus_next()

    def action_help(self) -> None:
        """toogle help"""
        self.app.push_screen(HelpScreen())

    def action_screenshot(self):
        self.app.save_screenshot()

    def action_open_menu(self) -> None:
        """toogle menu"""
        self.app.push_screen(MenuScreen())

    def action_cmd_select(self) -> None:
        self.set_focus(None)

    def action_do_search(self):
        file_pattern = self.input_files.value
        search_pattern = self.input_search.value

        self.replace_pattern = self.input_replace.value

        # for testing
        if not file_pattern:
            file_pattern = "*"
        if not search_pattern:
            search_pattern = "abcde"
            self.input_search.insert_text_at_cursor(search_pattern)
        if not self.replace_pattern:
            self.replace_pattern = "ABC"
            self.input_replace.insert_text_at_cursor(self.replace_pattern)

        mode = self.app.settings["mode"]
        if mode == "plain-text":
            search_pattern = re.escape(search_pattern)
            self.replace_pattern = self.replace_pattern.replace("\\", r"\\")
        elif mode == "escape-sequences":
            search_pattern = re.escape(search_pattern)
            for esc_seq in [r"\n", r"\r", r"\t"]:
                # undo escaping for some sequences
                search_pattern = search_pattern.replace(f"\\{esc_seq}", esc_seq)

        self.search_results.clear()
        self.replace_results.clear()
        if not search_pattern:
            self.search_results.write("error: empty search pattern")
            return

        try:
            self.compiled_search_pattern = re.compile(search_pattern)
        except re.error as ex:
            self.search_results.write(f"regex error: {ex}")
            return

        results = find_pattern(self.startpath, file_pattern, self.compiled_search_pattern, self.replace_pattern)
        self._preview_search_results(results)

    def _preview_search_results(self, results):
        indent = " " * 0

        file_count = 0
        match_count = 0

        for path, matches in results.items():
            if not matches:
                continue

            localpath = path.replace(self.startpath, ".")
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

        self.statusbar.remove_class(*self.statusbar.classes)
        self.statusbar.add_class("sb_active")

        # seve the search result for late usage
        self.search_result_store = results

    def action_do_replace(self):
        if self.search_result_store is None:
            self.statusbar.update("Cannot replace: no search result available.")
            self.statusbar.remove_class(*self.statusbar.classes)
            self.statusbar.add_class("sb_warning")
            return

        file_count = 0
        for filepath, matches in self.search_result_store.items():
            log("p", filepath, len(matches))
            if len(matches) == 0:
                continue
            with open(filepath) as fp:
                s = fp.read()

                s = self.compiled_search_pattern.sub(self.replace_pattern, s)
            with open(filepath, "w") as fp:
                fp.write(s)
            file_count += 1

        self.statusbar.remove_class(*self.statusbar.classes)
        self.statusbar.add_class("sb_success")

        if file_count == 1:
            file_word = "file"
        else:
            file_word = "files"
        self.statusbar.update(f"replacements performed in {file_count} {file_word}")


class MenuScreen(Screen):

    BINDINGS = [
        ("escape", "esc_pressed", "cancel"),
    ]
    def compose(self) -> ComposeResult:

        self.button_cancel = Button("Cancel (go back)", variant="primary", id="cancel")
        self.button_quit = Button("Quit (CTRL+C)", id="quit", variant="error")

        yield Static("fimf - settings", id="screen-heading")

        with Vertical(id="ctn-menu"):
            yield Label("search mode:")
            with ListView(id="mode-selector"):
                yield ListItem(Label("plain-text"), id="li_plain-text")
                yield ListItem(Label("escape-sequences"), id="li_escape-sequences")
                yield ListItem(Label("regex"), id="li_regex")

        with Horizontal(id="cntn_buttons"):
            yield self.button_cancel
            yield self.button_quit

        # TODO: this is preferrable but does not work
        # yield self.app.modebar

        self.footer = Footer()
        self.footer.styles.dock = ""
        with Vertical(id="ctn-footer"):
            yield Label(f"mode: {self.app.settings['mode']}", id="modebar")
            yield self.footer

    def on_mount(self):
        self.query_one("#mode-selector").focus()
        log("xxx\n"*5)
        log(self.button_quit.styles.dock)


    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()

    def on_list_view_selected(self, message) -> None:
        # log(dir(message.item))
        log(message.item.id)
        self.app.update_mode(message.item.id[3:])
        self.app.pop_screen()


class HelpScreen(Screen):
    def compose(self) -> ComposeResult:

        self.button_cancel = Button("Cancel (go back)", variant="primary", id="cancel")
        self.button_quit = Button("Quit", variant="error", id="quit")

        yield Static("This modal dialog will be the help screen in the future", id="screen-heading")

        with Horizontal(id="cntn_buttons"):
            yield self.button_cancel
            yield self.button_quit

    def on_mount(self):
        self.button_cancel.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()


class FimfApp(App):
    CSS_PATH = "fimf.css"
    # SCREENS = {"main": MainScreen()}
    settings = {"mode": "plain-text"}

    def compose(self) -> ComposeResult:
        self.modebar = Label("", id="modebar")
        self.update_mode()
        return []

    def on_mount(self) -> None:
        self.push_screen(MainScreen())

    def update_mode(self, mode: str = None):
        if mode is None:
            mode = self.settings["mode"]
        else:

            self.settings["mode"] = mode

        self.modebar.update(f"mode: {self.settings['mode']}")

    def action_esc_pressed(self) -> None:

        if self.screen_stack[-1].id != "_default":
            self.pop_screen()



class Match:
    def __init__(self, line_number, line, match, rplmt=None):
        self.line_number = line_number
        self.line = line.rstrip("\n")
        self.re_match = match

        start_end_template = r"[#A0A0A0]{}[/]"

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
            start_char = start_end_template.format("…")
            end_char = start_end_template.format("…")

        else:
            l0 = diff // 2
            l1 = diff - l0
            # padding of the line

            i0 = i_start - l0
            if i0 < 0:
                # prefix part is shorter than what would be possible
                i0 = 0
                start_char = start_end_template.format("↦")
            else:
                start_char = start_end_template.format("…")

            i1 = i_end + l1
            if i1 > l_line:
                i1 = l_line
                end_char = start_end_template.format("⏎")
            else:
                end_char = start_end_template.format("…")

            hl_txt = full_match
            txt0 = line[i0:i_start]
            txt1 = line[i_end:i1]

        self.context_str = f"{start_char}{txt0}[#F0A0F0 on #305030]{hl_txt}[/]{txt1.rstrip()}{end_char}"

        if rplmt is not None:
            self.context_rpl_str = f"{start_char}{txt0}[#F0A0F0 on #303050]{rplmt}[/]{txt1.rstrip()}{end_char}"
        else:
            self.context_rpl_str = self.context_str


def find_matches(filename, compiled_pattern, replace_pattern):
    matches = []
    with open(filename, "r") as f:
        for i, line in enumerate(f, start=1):
            for match in re.finditer(compiled_pattern, line):
                rplmt = compiled_pattern.sub(replace_pattern, match.group(0))
                matches.append(Match(i, line, match, rplmt))
    return matches


def find_pattern(directory, file_pattern, search_pattern, replace_pattern):
    """
    :param directory:
    :param file_pattern:
    :param compiled_search_pattern:
    :param replace_pattern:

    Note: replace_pattern is used here for the sake of preview only
    """
    results = {}
    total_files = 0
    for path, dirs, files in os.walk(os.path.abspath(directory)):
        for filename in fnmatch.filter(files, file_pattern):
            total_files += 1
            filepath = os.path.join(path, filename)
            matches = find_matches(filepath, search_pattern, replace_pattern)
            results[filepath] = matches

    # construct the final return value (with desired ordering and custom attribute)
    results = UserDict(sorted(results.items()))
    results.total_files = total_files
    return results


def main():

    app = FimfApp()
    app.run()


if __name__ == "__main__":
    main()
