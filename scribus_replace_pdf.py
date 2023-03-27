#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

try:
    import scribus
except ImportError:
    print("Unable to import the 'scribus' module. This script will only run within")
    print("the Python interpreter embedded in Scribus. Try Script->Execute Script.")
    sys.exit(1)

from t9a_scribus import ScribusLAB
from pathlib import Path

def main(argv):
    if len(argv)==1: # if called from within Scribus or with no arguments
        new_args = scribus.valueDialog('New PDF', 'Full path to new rules PDF').strip('"')
        if new_args == '':
            scribus.messageBox("Script Cancelled","Script was cancelled or no arguments were provided")
            return
        else:
            if Path(new_args).is_file():
                new_pdf = new_args
            else:
                scribus.messageBox(f"Invalid file path: {new_args}")
                return
            # scribus.messageBox("Arguments",str(argv))
            # return
    
    lab = ScribusLAB()
    lab.replace_pdf(new_pdf)

def main_wrapper(argv):
    global interactive
    """The main_wrapper() function disables redrawing, sets a sensible generic
    status bar message, and optionally sets up the progress bar. It then runs
    the main() function. Once everything finishes it cleans up after the main()
    function, making sure everything is sane before the script terminates."""
    try:
        # scribus.setRedraw(False) # setRedraw(False) causes shadows not to export properly, somehow.
        scribus.statusMessage("Running script...")
        scribus.progressReset()
        main(argv)
    finally:
        # Exit neatly even if the script terminated with an exception,
        # so we leave the progress bar and status bar blank and make sure
        # drawing is enabled.
        if scribus.haveDoc():
            scribus.setRedraw(True)
        scribus.statusMessage("")
        scribus.progressReset()

# This code detects if the script is being run as a script, or imported as a module.
# It only runs main() if being run as a script. This permits you to import your script
# and control it manually for debugging.
if __name__ == '__main__':
    if scribus.haveDoc():
        main_wrapper(sys.argv)
    else:
        scribus.messageBox("No file open","You need to have a suitable file open to use this script")
