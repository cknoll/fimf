import os
import re
from collections import defaultdict
import fnmatch

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.screen import Screen
from textual.widgets import Static, Input, Footer, Button, TextLog, Label


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
        self.input_files = Input(placeholder="file pattern", id="in_files")
        self.input_search = Input(placeholder="search pattern", id="in_search")
        self.input_replace = Input(placeholder="replace pattern", id="in_replace")

        self.button_search = Button("Search (F3)", id="btn_search", variant="primary")
        self.button_replace = Button("Replace All", id="btn_replace", variant="warning")
        self.button_quit = Button("Quit (CTRL+C)", id="btn_quit", variant="error")
        self.label_results = Label("Results", id="lb_results")
        self.results = TextLog(markup=True, classes="results")

        yield self.intro
        yield self.input_files
        yield self.input_search
        yield self.input_replace

        with Vertical():
            with Horizontal(id="cntn_buttons"):
                yield self.button_search
                yield self.button_replace
                yield self.button_quit

            yield self.results
            yield self.results
        yield Footer()

    def on_mount(self) -> None:
        # self.input_files.focus()
        self.input_search.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:

        if event.button.id == "btn_search":
            self.action_do_search()
        elif event.button.id == "btn_quit":
            self.exit(str(event.button))
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
            file_pattern = "*.njk"

        self.results.clear()
        if not search_pattern:
            self.results.write("error: empty search pattern")
            return

        try:
            search_pattern = re.compile(search_pattern)
        except re.error as ex:
            self.results.write(f"regex error: {ex}")
            return


        results = find_pattern("./", search_pattern, file_pattern)
        indent = " " * 4
        for path, matches in results.items():
            if not matches:
                continue
            self.results.write(f"{path} ({len(matches)})")
            for line_number, match in matches.items():
                self.results.write(f"{indent}{line_number:03d}: {match[0]}")
            self.results.write("\n"*2)


class HelpScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Grid(
            Static("This modal dialog will be the help screen in the future", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="quit"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()


def find_matches(filename, compiled_pattern):
    matches = {}
    with open(filename, "r") as f:
        for i, line in enumerate(f, start=1):
            for match in re.finditer(compiled_pattern, line):
                if i not in matches:
                    matches[i] = [match.group()]
                else:
                    matches[i].append(match.group())
    return matches


def find_pattern(directory, search_pattern, file_pattern):
    results = {}
    for path, dirs, files in os.walk(os.path.abspath(directory)):
        for filename in fnmatch.filter(files, file_pattern):
            filepath = os.path.join(path, filename)
            matches = find_matches(filepath, search_pattern)
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
