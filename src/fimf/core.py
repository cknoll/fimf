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

        self.button_search = Button("Search", id="btn_search", variant="primary")
        self.button_replace = Button("Replace All", id="btn_replace", variant="warning")
        self.button_cancel = Button("Cancel", id="btn_cancel", variant="error")
        self.results = TextLog(markup=True, classes="results")

        yield self.intro
        yield self.input_files
        yield self.input_search
        yield self.input_replace

        with Vertical():
            with Horizontal(id="cntn_buttons"):
                yield self.button_search
                yield self.button_replace
                yield self.button_cancel

            yield self.results
        yield Footer()

    def on_mount(self) -> None:
        self.input_files.focus()
        self.results.write("**test1**")
        self.results.write("[#9944aa]test2[/#9944aa]" + "\nxy" * 23)

    def on_input_changed(self, message: Input.Changed) -> None:
        print(message.input)
        self.results.write(message.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:

        if event.button.id == "btn_search":
            self.do_search()
        elif event.button.id == "btn_cancel":
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

    def do_search(self):
        file_pattern = self.input_files.value
        search_pattern = self.input_search.value
        replace_pattern = self.input_replace.value

        results = find_pattern("./", search_pattern, file_pattern)
        indent = " " * 4
        for path, matches in results.items():
            self.results.write(f"{path} ({len(matches)})")
            for line_number, match in matches:
                self.results.write(f"{indent}{line_number:03d} {match}")
            self.results.write("\n")


class HelpScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Grid(
            Static("This modal dialog will be the help screen in the future", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()


def find_matches(filename, pattern):
    matches = {}
    with open(filename, "r") as f:
        for i, line in enumerate(f, start=1):
            for match in re.finditer(pattern, line):
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
