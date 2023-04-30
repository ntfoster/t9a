import sys

try:
    # Please do not use 'from scribus import *' . If you must use a 'from
    # import', do so _after_ the 'import scribus' and only import the names you
    # need, such as commonly used constants.
    import scribus
except ImportError:
    print("This Python script is written for the Scribus scripting interface.")
    print("It can only be run from within Scribus.")
    sys.exit(1)

import logging
import tkinter as tk
from tkinter import ttk
from pathlib import Path

from t9a.scribus import ScribusLAB

logging.basicConfig(level=logging.INFO)


class HelperMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("T9A Army Book Tools")

        self.lab = ScribusLAB()

        self.toc_background = tk.BooleanVar(value=False)
        self.toc_rules = tk.BooleanVar(value=True)

        helpers = ttk.LabelFrame(root, text="Helpers", padding=5)
        helpers.grid(padx=10, pady=10, sticky="EW")

        toc_options = ttk.Frame(helpers)
        toc_options.grid(column=0, row=0, sticky="EW")
        ttk.Checkbutton(
            toc_options,
            text="BG",
            variable=self.toc_background,
        ).pack(side=tk.LEFT)
        ttk.Checkbutton(
            toc_options,
            text="Rules",
            variable=self.toc_rules,
        ).pack(side=tk.LEFT)

        buttons = [  # List of button names and corresponding functions
            ("Create Table of Contents", self.create_toc),
            ("Create ToC Hyperlinks", self.lab.create_toc_hyperlinks),
            ("Set Footers", self.lab.set_footers),
            ("Add rules headers", self.set_rules_headers),
            ("Replace rules PDF", self.replace_rules),
        ]
        status_labels = []
        for i, button in enumerate(buttons):
            label = ttk.Label(
                helpers, text="Ready", width=10,
                style="Default.TLabel", anchor="center"
            )
            status_labels.append(label)
            def command(script=button[1], i=i):
                return self.run_script(script, status_labels[i])
            ttk.Button(helpers, text=button[0], width=30, command=command
                       ).grid(column=0, row=i + 1, sticky="EW")
            label.grid(column=1, row=i + 1, padx=5, sticky="E")

        buttons = ttk.Frame(root)
        buttons.grid(column=0, row=2, sticky="EW", padx=10, pady=10)

        ttk.Button(buttons, text="OK", command=root.destroy).pack()

    def run_script(self, function, label):
        try:
            function()
            label.configure(text="OK")
            label.configure(style="OK.TLabel")
        except Exception as err:
            label.configure(text="Error")
            label.configure(style="Error.TLabel")
            scribus.messageBox("Error", err)

    def set_rules_headers(self):
        rules_pdf = Path(self.lab.get_embedded_rules())
        json_file = rules_pdf.with_suffix(".json")
        if not Path(json_file).is_file():
            scribus.messageBox(
                "Couldn't find JSON file",
                f"Couldn't find {json_file}. Please run \
                                get_rules_json.py externally and try again",
            )
            raise FileNotFoundError(
                f"Couldn't find {json_file}. Please run get_rules_json.py \
                    externally and try again"
            )
        try:
            titles = self.lab.load_titles_from_json(json_file)
        except Exception as err:
            scribus.messageBox("Error loading JSON file", err)
            return

        self.lab.remove_rules_headers()
        self.lab.add_rules_headers(titles)
        scribus.saveDoc()

    def create_toc(self):
        self.lab.create_toc_from_sla(self.toc_background.get(),
                                     self.toc_rules.get())

    def replace_rules(self):
        try:
            new_pdf = scribus.fileDialog(
                caption="Select slim rules PDF",
                filter="PDF Files (*.pdf)",
                defaultname="",
                haspreview=True
            )
            if new_pdf:
                self.lab.replace_pdf(new_pdf)
        except Exception as err:
            raise err


def main():
    doc_name = Path(scribus.getDocName())
    logging.debug("\n\n*******************************\nn)")
    if doc_name.suffix != ".sla":
        scribus.messageBox(
            "File not found",
            f"{doc_name} is not a valid .sla file. \
            This script should only be run with an open T9A LAB file.",
        )
        return

    root = tk.Tk()
    root.eval("tk::PlaceWindow . center")

    style = ttk.Style(root)
    style.configure(
        "OK.TLabel",
        background="pale green",
        foreground="dark green",
        padding=2,
        relief="solid",
        borderwidth=1,
    )
    style.configure("Default.TLabel", padding=2, relief="solid", borderwidth=1)
    style.configure(
        "Error.TLabel",
        background="pink1",
        foreground="maroon",
        padding=2,
        relief="solid",
        borderwidth=1,
    )
    style.configure("Warn.TButton", background="red", foreground="red")

    HelperMenu(root)
    root.mainloop()


# This code detects if the script is being run as a script, or imported as a
# module. It only runs main() if being run as a script. This permits you to
# import your script and control it manually for debugging.
if __name__ == "__main__":
    if scribus.haveDoc():
        main()
    else:
        scribus.messageBox(
            "No file open", "You need to have a suitable file open to \
                use this script"
        )
