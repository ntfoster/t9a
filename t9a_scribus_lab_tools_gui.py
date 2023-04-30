import sys
import logging
try:
    # Please do not use 'from scribus import *' . If you must use a 'from import',
    # Do so _after_ the 'import scribus' and only import the names you need, such
    # as commonly used constants.
    import scribus
except ImportError as err:
    print("This Python script is written for the Scribus scripting interface.")
    print("It can only be run from within Scribus.")
    sys.exit(1)

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from t9a_export_pdfs import export_pdfs # TODO: move export to package
from t9a.scribus import ScribusLAB


options = {}

logging.basicConfig(level=logging.INFO)

def export_menu():
    # create root window
    root = tk.Tk()
    root.eval('tk::PlaceWindow . center')
    root.title("T9A LAB Tools")

    style = ttk.Style(root)
    style.configure("OK.TLabel", background="pale green", foreground="dark green", padding=2, relief="solid", borderwidth=1)
    style.configure("Default.TLabel", padding=2, relief="solid", borderwidth=1)
    style.configure("Error.TLabel", background="pink1", foreground="maroon", padding=2, relief="solid", borderwidth=1)
    style.configure("Warn.TButton", background="red", foreground="red")

    lab = ScribusLAB()

    def set_rules_headers():
        rules_pdf = Path(lab.get_embedded_rules())
        json_file = rules_pdf.with_suffix(".json")
        if not Path(json_file).is_file():
            scribus.messageBox("Couldn't find JSON file",f"Couldn't find {json_file}. Please run get_rules_json.py externally and try again")
            raise FileNotFoundError(f"Couldn't find {json_file}. Please run get_rules_json.py externally and try again")
        try:
            titles = lab.load_titles_from_json(json_file)
        except Exception as err:
            scribus.messageBox("Error loading JSON file", err)
            return

        lab.remove_rules_headers()
        lab.add_rules_headers(titles)
        scribus.saveDoc()

    def create_toc():
        lab.create_toc_from_sla(toc_background.get(),toc_rules.get())

    def run_script(method,status):
        try:
            method()
            status.configure(text="OK")
            status.configure(style="OK.TLabel")
        except Exception as err:
            status.configure(text="Error")
            status.configure(style="Error.TLabel")
            scribus.messageBox("Error",err)

    def replace_rules():
        try:
            new_pdf = scribus.fileDialog(
                "Select slim rules PDF", "PDF Files (*.pdf)", "", haspreview=True)
            if new_pdf:
                lab.replace_pdf(new_pdf)
        except Exception as err:
            raise err

    def export():
        global options

        if nopoints.get() and not lab.check_nopoints():
            scribus.messageBox("Nopoints file missing","Couldn't find nopoints version of the rules. Make sure _nopoints PDF is in the images folder before trying again.")
            return
        
        qualities = []
        if high.get():
            qualities.append("high")
        if low.get():
            qualities.append("low")
        # if printq:
        #     qualities.append("print")

        formats = []
        if full.get():
            formats.append("full")
        if nopoints.get():
            formats.append("nopoints")
        if norules.get():
            formats.append("norules")

        if formats and qualities:
            options = {"formats": formats, "qualities": qualities}
            root.destroy()
        else:
            tk.messagebox.showerror(
                title="No options selected",
                message="You must select at least one option from both Quality and Format",
            )

    ##############
    ### LAYOUT ###
    ##############
    helpers = ttk.LabelFrame(
        root, text="Helpers", padding=5)
    helpers.grid(padx=10,pady=10, sticky="EW")

    toc_background = tk.BooleanVar(value=False)
    toc_rules = tk.BooleanVar(value=True)

    buttons = [ # List of button name and functions
        ("Create Table of Contents", create_toc),
        ("Create ToC Hyperlinks", lab.create_toc_hyperlinks),
        ("Set Footers", lab.set_footers),
        ("Add rules headers", set_rules_headers),
        ("Replace rules PDF", replace_rules),
    ]

    tocs = ttk.Frame(helpers)
    tocs.grid(column=0,row=0,sticky="EW")

    ttk.Checkbutton(tocs, text="BG", variable=toc_background, ).pack(side=tk.LEFT)
    ttk.Checkbutton(tocs, text="Rules", variable=toc_rules, ).pack(side=tk.LEFT)

    button_frame = ttk.Frame(helpers,padx=5)
    labels = []
    for i, button in enumerate(buttons):
        label = ttk.Label(helpers, text="Ready", width=10, style="Default.TLabel", anchor="center")
        labels.append(label)
        command = lambda script=button[1], i=i: run_script(script,labels[i])
        ttk.Button(helpers, text=button[0], width=30,
                   command=command
                   ).grid(column=0, row=i+1, sticky="EW")
        label.grid(column=1, row=i+1, padx=5, sticky="E")

    export_options = ttk.LabelFrame(
        root, text="Export", padding=10
    )
    export_options.grid(column=0,row=1,padx=10,sticky="EW")

    quality = ttk.LabelFrame(
        export_options, text="Quality", padding=5
    )
    quality.grid(column=0,row=0, sticky="EW")

    high = tk.BooleanVar(value=True)
    low = tk.BooleanVar(value=True)
    printq = tk.BooleanVar(value=False)
    ttk.Checkbutton(quality, text="High", variable=high, 
                    ).pack(anchor="w")
    ttk.Checkbutton(quality, text="Low", variable=low,
                    ).pack(anchor="w")
    ttk.Checkbutton(quality, text="Print", variable=printq, state=tk.DISABLED
                    ).pack(anchor="w")

    formats = ttk.LabelFrame(export_options, text="Format", padding=5)
    formats.grid(column=1, row=0, padx=10, sticky="EW")

    full = tk.BooleanVar(value=True)
    nopoints = tk.BooleanVar(value=True)
    norules = tk.BooleanVar(value=False)
    ttk.Checkbutton(formats, text="Full", variable=full
                    ).pack(anchor="w")
    ttk.Checkbutton(formats, text="No Points", variable=nopoints
                    ).pack(anchor="w")
    ttk.Checkbutton(formats, text="Background Only", variable=norules
                    ).pack(anchor="w")

    ttk.Button(export_options, text="Export", style="Warn.TButton", command=export
               ).grid(column=0, row=1, pady=5, sticky = tk.W)

    buttons = ttk.Frame(root)
    buttons.grid(column=0, row=2, sticky="EW", padx=10, pady=10)

    ttk.Button(buttons, text="OK", command=root.destroy
               ).pack()

    root.mainloop()


def main():
    doc_name = Path(scribus.getDocName())
    logging.debug("\n\n*******************************\nn)")
    if doc_name.suffix != ".sla":
        scribus.messageBox("File not found", f"{doc_name} is not a valid .sla file. This script should only be run with an open T9A LAB file.")
        return
    
    export_menu()
    
    if options:
        args = ["scribus", "--quality"] + list(options["qualities"]) + ["--formats"] + list(options["formats"])
        export_pdfs(options["formats"], options["qualities"])
    else:
        sys.exit()

# This code detects if the script is being run as a script, or imported as a module.
# It only runs main() if being run as a script. This permits you to import your script
# and control it manually for debugging.
if __name__ == "__main__":
    if scribus.haveDoc():
        main()
    else:
        scribus.messageBox(
            "No file open", "You need to have a suitable file open to use this script"
        )
