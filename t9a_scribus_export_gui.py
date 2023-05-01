import logging
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

import tkinter as tk
from tkinter import ttk

from t9a.scribus import ScribusLAB
from t9a_export_pdfs import export_pdfs  # TODO: move export to package

logging.basicConfig(level=logging.INFO)


class ExportMenu:
    def __init__(self, root, options):
        self.root = root
        self.root.title("Export T9A Army Book")

        self.lab = ScribusLAB()
        export_options = ttk.LabelFrame(root, text="Export", padding=10)
        export_options.grid(column=0, row=1, padx=10, sticky="EW")

        quality = ttk.LabelFrame(export_options, text="Quality", padding=5)
        quality.grid(column=0, row=0, sticky="EW")

        self.high = tk.BooleanVar(value=True)
        self.low = tk.BooleanVar(value=True)
        self.printq = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            quality,
            text="High",
            variable=self.high,
        ).pack(anchor="w")
        ttk.Checkbutton(
            quality,
            text="Low",
            variable=self.low,
        ).pack(anchor="w")
        ttk.Checkbutton(
            quality, text="Print", variable=self.printq, state=tk.DISABLED
        ).pack(anchor="w")

        formats = ttk.LabelFrame(export_options, text="Format", padding=5)
        formats.grid(column=1, row=0, padx=10, sticky="EW")

        self.full = tk.BooleanVar(value=True)
        self.nopoints = tk.BooleanVar(value=True)
        self.norules = tk.BooleanVar(value=False)
        ttk.Checkbutton(formats, text="Full", variable=self.full
                        ).pack(anchor="w")
        ttk.Checkbutton(formats, text="No Points", variable=self.nopoints
                        ).pack(anchor="w")
        ttk.Checkbutton(formats, text="Background Only", variable=self.norules
                        ).pack(anchor="w")

        ttk.Button(
            export_options,
            text="Export",
            style="Warn.TButton",
            command=lambda: self.export(options),
        ).grid(column=0, row=1, pady=5, sticky=tk.W)

        buttons = ttk.Frame(root)
        buttons.grid(column=0, row=2, sticky="EW", padx=10, pady=10)

    def export(self, options):
        if self.nopoints.get() and not self.lab.check_nopoints():
            scribus.messageBox(
                "Nopoints file missing",
                "Couldn't find nopoints version of the rules. Make sure \
                    _nopoints PDF is in the images folder before trying again."
            )
            return

        qualities = []
        if self.high.get():
            qualities.append("high")
        if self.low.get():
            qualities.append("low")
        # if printq:
        #     qualities.append("print")

        formats = []
        if self.full.get():
            formats.append("full")
        if self.nopoints.get():
            formats.append("nopoints")
        if self.norules.get():
            formats.append("norules")

        if formats and qualities:
            options = {"formats": formats, "qualities": qualities}
            # return options
            self.root.destroy()
            export_pdfs(options["formats"], options["qualities"])
        else:
            tk.messagebox.showerror(
                title="Not enough options selected",
                message="You must select at least one option from both \
                    Quality and Format",
            )

def main():
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
    style.configure("Warn.TButton", background="pink1", foreground="red")

    options = {}
    ExportMenu(root, options)
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
