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

from tkinter import *
from tkinter import messagebox
import t9a_export_pdfs

options = {}

def export_menu():

    # create root window
    root = Tk()

    # root window title and dimension
    root.title("LAB export options")
    # Set geometry(widthxheight)
    root.geometry('300x200')

    w = 300 # width for the Tk root
    h = 200 # height for the Tk root

    # get screen width and height
    ws = root.winfo_screenwidth() # width of the screen
    hs = root.winfo_screenheight() # height of the screen

    # calculate x and y coordinates for the Tk root window
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)

    # set the dimensions of the screen 
    # and where it is placed
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))

    # frame = Frame(root)
    # frame.grid(column=0,row=0)

    quality = LabelFrame(root, text='Quality', bd=2, relief=GROOVE, padx=10, pady=10)
    quality.place(x=10,y=10)

    high = BooleanVar()
    low = BooleanVar()
    # printq = BooleanVar()

    high.set(True)
    low.set(True)
    # printq.set(False)

    Checkbutton(quality, text = "High", variable = high).pack(anchor=W)
    Checkbutton(quality, text = "Low", variable = low).pack(anchor=W)
    Checkbutton(quality, text = "Print", state=DISABLED).pack(anchor=W)

    formats = LabelFrame(root,text="Format",bd =2, relief=GROOVE, padx=10, pady=10)
    formats.place(x=100,y=10)

    full = BooleanVar()
    nopoints = BooleanVar()
    norules = BooleanVar()

    full.set(True)
    nopoints.set(True)
    norules.set(False)

    Checkbutton(formats, text = "Full", variable = full).pack(anchor=W)
    Checkbutton(formats, text = "No Points", variable = nopoints).pack(anchor=W)
    Checkbutton(formats, text = "Background Only", variable = norules).pack(anchor=W)

    buttons = Frame(root)
    buttons.place(x=10,y=150)

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
            options = {"formats":formats,"qualities":qualities}
            root.destroy()
        else:
            messagebox.showerror(title="No options selected", message="You must select at least one option from both Quality and Format")

    Button(buttons,text="Export",fg="Red",command=export).pack(side=RIGHT,padx=150)
    Button(buttons,text="Cancel",command=root.destroy).pack(side=LEFT)

    root.mainloop()

def main():
    export_menu()

    if options:
        args = ["scribus","--quality"]
        args.extend(iter(options['qualities']))
        args.append("--formats")
        args.extend(iter(options['formats']))
        print(args)
        # t9a_export_pdfs.main_wrapper(args)
        t9a_export_pdfs.export_pdfs(options['formats'], options['qualities'])

                # scribus.messageBox("Options",f"Selected options: {str(options)}")

    else:
        sys.exit()

# This code detects if the script is being run as a script, or imported as a module.
# It only runs main() if being run as a script. This permits you to import your script
# and control it manually for debugging.
if __name__ == '__main__':
    if scribus.haveDoc():
        main()
    else:
        scribus.messageBox("No file open","You need to have a suitable file open to use this script")


