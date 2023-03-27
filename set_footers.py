#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


from t9a_sla import LABfile

FOOTER_X_POS = 20
FOOTER_Y_POS = 285.5
FOOTER_WIDTH = 70
FOOTER_HEIGHT = 7

# Unique mesasurements for certain books
UD_FOOTER_X_POS_ODD = 115.5
UD_FOOTER_X_POS_EVEN = 23
UD_FOOTER_Y_POS = 282.58

SE_FOOTER_X_POS = 20
SE_FOOTER_Y_POS = 280.84

def create_footer(page, footer):
    scribus.gotoPage(page)
    label = scribus.createText(FOOTER_X_POS,FOOTER_Y_POS,FOOTER_WIDTH,FOOTER_HEIGHT)
    scribus.setText(footer,label)
    
    try:
        scribus.setStyle("Footer Left", label)
    except scribus.NotFoundError:
        try:
            scribus.setStyle("FOOTER left", label)
        except scribus.NotFoundError:
            try:
                scribus.setStyle("FOOTER Left", label)
            except scribus.NotFoundError:
                scribus.messageBox("Style Error","Couldn't find appropriate Footer style: 'Footer Left', 'FOOTER left' or 'FOOTER Left'")
                return

def create_footer_UD(page, footer):
    scribus.gotoPage(page)
    if page % 2 == 0:  # even, left-hand page
        label = scribus.createText(UD_FOOTER_X_POS_EVEN,UD_FOOTER_Y_POS,FOOTER_WIDTH,FOOTER_HEIGHT)
        scribus.setText(footer,label)
        try:
            scribus.setStyle("FOOTER left", label)
        except scribus.NotFoundError:
            scribus.messageBox("Style Error","Couldn't find appropriate Footer style: 'FOOTER left'")
            return
    else: # odd, right-hand page
        label = scribus.createText(UD_FOOTER_X_POS_ODD,UD_FOOTER_Y_POS,FOOTER_WIDTH,FOOTER_HEIGHT)
        scribus.setText(footer,label)
        try:
            scribus.setStyle("FOOTER right", label)
        except scribus.NotFoundError:
            scribus.messageBox("Style Error","Couldn't find appropriate Footer style: 'FOOTER right'")
            return

def create_footer_SE(page, footer):
    scribus.gotoPage(page)
    label = scribus.createText(SE_FOOTER_X_POS,SE_FOOTER_Y_POS,FOOTER_WIDTH,FOOTER_HEIGHT)
    scribus.setText(footer,label)
    try:
        scribus.setStyle("FOOTER left", label)
    except scribus.NotFoundError:
        scribus.messageBox("Style Error","Couldn't find appropriate Footer style: 'FOOTER left'")
        return

def main(argv):
    lab = LABfile(scribus.getDocName())
    background_headers = lab.parse_headers("HEADER Level 1")
    rules_headers = lab.parse_headers("HEADER Rules")
    headers = background_headers + rules_headers
    pages = range(8,scribus.pageCount())

    scribus.setUnit(scribus.UNIT_MM)

    current_layer = scribus.getActiveLayer()
    current_header = ""
    for page in pages:
        # don't create footer on page with "blank" master
        if scribus.getMasterPage(page).startswith("X"): continue

        for x in headers:
            if x["page"] == page:
                current_header = x["text"]
        scribus.setActiveLayer("Hyperlinks")
        if "_UD_" in scribus.getDocName():
            create_footer_UD(page, current_header)
        elif "_SE_" in scribus.getDocName():
            create_footer_SE(page, current_header)
        else:
            create_footer(page,current_header)
    scribus.setActiveLayer(current_layer)

def main_wrapper(argv):
    """The main_wrapper() function disables redrawing, sets a sensible generic
    status bar message, and optionally sets up the progress bar. It then runs
    the main() function. Once everything finishes it cleans up after the main()
    function, making sure everything is sane before the script terminates."""
    try:
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
    main_wrapper(sys.argv)
