import sys

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

from t9a_export_pdfs import export_pdfs
from t9a.scribus import ScribusLAB


options = {}


def export_menu():
    # TODO: replace tk with ttk for better looking widgets

    lab = ScribusLAB()

    # create root window
    root = tk.Tk()
    root.eval('tk::PlaceWindow . center')

    # root window title and dimension
    root.title("T9A LAB Tools")

    w = root.winfo_reqwidth()
    h = root.winfo_reqheight()
    # get screen width and height
    ws = root.winfo_screenwidth()  # width of the screen
    hs = root.winfo_screenheight()  # height of the screen

    # calculate x and y coordinates for the Tk root window
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 2)

    # set the dimensions of the screen
    # and where it is placed
    # root.geometry("%dx%d+%d+%d" % (w, h, x, y))
    # root.geometry("+%d+%d" % (x, y))
    # frame = Frame(root)
    # frame.grid(column=0,row=0)

    helpers = tk.LabelFrame(
        root, text="Helpers", bd=2, relief=tk.GROOVE, padx=10, pady=10
    )
    helpers.grid(padx=5,pady=5, sticky="EW")

    def set_rules_headers():
        rules_pdf = Path(lab.get_embedded_rules())
        # json_file = rules.parents[1] / Path(rules.name).with_suffix(".json")
        json_file = rules_pdf.with_suffix(".json")
        if not Path(json_file).is_file():
            # print("Not found; Generating")
            # script_path = Path(__file__).parents[0] / GET_JSON_SCRIPT
            # python_exe = get_python_path()
            # current_env = os.environ.copy()
            # current_env['PYTHONPATH'] = ""  # need to clear out Scribus' pythonpath before calling subprocess to avoid import errors
            # print(f'running command: "{python_exe}" "{script_path}" "{rules}')
            # p = subprocess.run(f'"{python_exe}" "{script_path}" "{rules}"', shell=True, env=current_env)
            # print("Finished running command")
            # if p.returncode > 0: # if error
            #     print(p.stderr)
            scribus.messageBox("Couldn't find JSON file",f"Couldn't fine {json_file}. Please run get_rules_json.py externally and try again")
            raise FileNotFoundError(f"Couldn't fine {json_file}. Please run get_rules_json.py externally and try again")
        try:
            titles = lab.load_titles_from_json(json_file)
        except Exception as err:
            scribus.messageBox("Error loading JSON file", err)
            return
            
        lab.remove_rules_headers()
        lab.add_rules_headers(titles)
        scribus.saveDoc()
        root.destroy()

    def run_script(method,status):
        try:
            method()
            status.set("Done")
        except Exception as err:
            status.set("Error")
            scribus.messageBox("Error",err)

    def run_h1():
        try:
            lab.create_toc_from_text()
            h1_var.set("Done")
        except Exception as err:
            h1_var.set("Error")
            scribus.messageBox("Error",err)

    def run_h2():
        try:
            lab.create_toc_hyperlinks()
            h2_var.set("Done")
        except Exception as err:
            h2_var.set("Error")
            scribus.messageBox("Error", err)

    def run_h3():
        try:
            lab.remove_footers()
            h3_var.set("Done")
        except Exception as err:
            h3_var.set("Error")
            scribus.messageBox("Error", err)

    def run_h4():
        try:
            lab.set_footers()
            h4_var.set("Done")
        except Exception as err:
            h4_var.set("Error")
            scribus.messageBox("Error", err)

    def run_h5():
        try:
            set_rules_headers()
            h5_var.set("Done")
        except Exception as err:
            h5_var.set("Error")
            scribus.messageBox("Error", err)

    def run_h6():
        try:
            new_pdf = scribus.fileDialog(
                "Select slim rules PDF", "PDF Files (*.pdf)", "", haspreview=True)
            if new_pdf:
                lab.replace_pdf(new_pdf)
                h6_var.set("Done")
        except Exception as err:
            h6_var.set("Error")
            scribus.messageBox("Error", err)


    # helpers.pack(side=tk.TOP)
    tk.Button(
        helpers, text="Create Table of Contents", width=20, command=run_h1
    ).grid(column=0, row=0, sticky="EW")

    tk.Button(
        helpers,
        text="Create ToC Hyperlinks",
        width=20,
        command=run_h2,
    ).grid(column=0, row=1, sticky="EW")
    tk.Button(
        helpers, text="Remove Footers", width=20, command=run_h3
    ).grid(column=0, row=2, sticky="EW")
    tk.Button(helpers, text="Set Footers", width=20,
              command=run_h4).grid(column=0, row=3, sticky="EW")
    tk.Button(helpers, text="Set rules headers", width=20,
              command=run_h5).grid(column=0, row=4, sticky="EW")
    tk.Button(helpers, text="Replace rules PDF", width=20,
              command=run_h6).grid(column=0, row=5, sticky="EW")


    h1_var = tk.StringVar()
    h1_var.set("")
    h2_var = tk.StringVar()
    h2_var.set("")
    h3_var = tk.StringVar()
    h3_var.set("")
    h4_var = tk.StringVar()
    h4_var.set("")
    h5_var = tk.StringVar()
    h5_var.set("")
    h6_var = tk.StringVar()
    h6_var.set("")



    h1_status = tk.Label(helpers, textvariable=h1_var).grid(
        column=1, row=0, padx=5, sticky="E")
    h2_status = tk.Label(helpers, textvariable=h2_var).grid(
        column=1, row=1, padx=5, sticky="E")
    h3_status = tk.Label(helpers, textvariable=h3_var).grid(
        column=1, row=2, padx=5, sticky="E")
    h4_status = tk.Label(helpers, textvariable=h4_var).grid(
        column=1, row=3, padx=5, sticky="E")
    h5_status = tk.Label(helpers, textvariable=h5_var).grid(
        column=1, row=4, padx=5, sticky="E")
    h6_status = tk.Label(helpers, textvariable=h6_var).grid(
        column=1, row=5, padx=5, sticky="E")


    export_options = tk.LabelFrame(
        root, text="Export", bd=2, relief=tk.GROOVE, padx=10, pady=10
    )
    export_options.grid(column=0,row=1,padx=5,pady=5)

    quality = tk.LabelFrame(
        export_options, text="Quality", bd=2, relief=tk.GROOVE, padx=10, pady=10
    )
    quality.grid(column=0,row=0)

    high = tk.BooleanVar()
    low = tk.BooleanVar()
    # printq = BooleanVar()

    high.set(True)
    low.set(True)
    # printq.set(False)

    # tk.Checkbutton(quality, text="High", variable=high).grid(column=0,row=0)
    # tk.Checkbutton(quality, text="Low", variable=low).grid(column=0,row=1)
    # tk.Checkbutton(quality, text="Print", state=tk.DISABLED).grid(column=0,row=2)

    tk.Checkbutton(quality, text="High", variable=high, ).pack(anchor="w")
    tk.Checkbutton(quality, text="Low", variable=low,).pack(anchor="w")
    tk.Checkbutton(quality, text="Print", state=tk.DISABLED).pack(anchor="w")

    formats = tk.LabelFrame(
        export_options, text="Format", bd=2, relief=tk.GROOVE, padx=10, pady=10
    )
    formats.grid(column=1, row=0)

    full = tk.BooleanVar()
    nopoints = tk.BooleanVar()
    norules = tk.BooleanVar()

    full.set(True)
    nopoints.set(True)
    norules.set(False)

    tk.Checkbutton(formats, text="Full", variable=full).pack(anchor="w")
    tk.Checkbutton(formats, text="No Points",
                   variable=nopoints).pack(anchor="w")
    tk.Checkbutton(formats, text="Background Only",
                   variable=norules).pack(anchor="w")

    buttons = tk.Frame(root)
    buttons.grid(column=0, row=2, sticky="EW",padx=10,pady=10)

    def export():
        global options

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

    # export_buttons = tk.Frame(export_options)
    # export_buttons.grid(column=0,row=1,columnspan=2,sticky="EW",pady=5)

    tk.Button(buttons, text="Export", fg="Red",
              command=export).pack(side=tk.RIGHT)

    tk.Button(buttons, text="Done", command=root.destroy).pack(side=tk.LEFT)

    root.mainloop()


def main():
    doc_name = Path(scribus.getDocName())
    
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
