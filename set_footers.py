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


import xml.etree.ElementTree as ET

FOOTER_X_POS = 20
FOOTER_Y_POS = 285.5
FOOTER_WIDTH = 70
FOOTER_HEIGHT = 7

UD_FOOTER_X_POS_ODD = 115.5
UD_FOOTER_X_POS_EVEN = 23
UD_FOOTER_Y_POS = 282.58

SE_FOOTER_X_POS = 20
SE_FOOTER_Y_POS = 280.84

def parse_headers(style): # scans for 'HEADER Level 1' text to build bookmarks
    header_labels = []
    # for object in root.findall("./DOCUMENT/PAGEOBJECT/StoryText/DefaultStyle[@PARENT='HEADER Level 1']"):
    for element in root.findall(f"./DOCUMENT/PAGEOBJECT[@PTYPE='4']"):
        page = int(element.get("OwnPage"))+1 # Scribus interal page numbers start at 0, so are 1 less than 'real' page numbers 
        for storytext in element:
            if page > 7:
                is_header = False
                for child in storytext:
                    if child.tag == "DefaultStyle":
                        if str(child.get("PARENT")).lower() == style.lower():
                            is_header = True
                    if is_header:
                        if child.tag == "MARK":
                            label = child.get("label")
                            entry = {"label":label, "text":"", "page":page}
                            header_labels.append(entry)
                        if child.tag == "ITEXT":
                            text = child.get("CH")
                            entry = {"label":"", "text":text, "page":page}
                            header_labels.append(entry)
    # print(header_labels)
    return header_labels

def lookup_labels(labels):
    marks = root.find("./DOCUMENT/Marks")
    for entry in labels:
        if entry["label"] != "":
            entry["text"] = entry["label"]
            for mark in marks:
                if mark.get("label") == entry["label"]:
                    entry["text"] = mark.get("str")

            
    return labels

def get_rules_pages():
    rules_start = scribus.getAllText("rules_start")
    rules_end = scribus.getAllText("rules_end")
    return (int(rules_start),int(rules_end))

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
    """This is a documentation string. Write a description of what your code
    does here. You should generally put documentation strings ("docstrings")
    on all your Python functions."""

    global root
    file = scribus.getDocName()
    tree = ET.parse(file)
    root = tree.getroot()

    background_headers = parse_headers("HEADER Level 1")
    rules_headers = parse_headers("HEADER Rules")
    headers = background_headers + rules_headers
    labels = lookup_labels(headers)

    newlist = sorted(labels, key=lambda k: k['page'])


    pages = range(8,scribus.pageCount())
    # rules_pages = get_rules_pages()
    # pages = range(rules_pages[0],rules_pages[1])

    footer = ""
    # scribus.messageBox("Results",str(newlist))
    
    scribus.setUnit(scribus.UNIT_MM)
    for page in pages:
        # don't create footer on page with "blank" master
        if scribus.getMasterPage(page).startswith("X"): continue

        # header = next((item for item in newlist if item["page"] == page), None)
        header = None
        for x in newlist:
            if x["page"] == page:
                header = x
        if header:
            footer = header["text"]
        scribus.setActiveLayer("Hyperlinks")
        if "_UD_" in scribus.getDocName():
            create_footer_UD(page, footer)
        elif "_SE_" in scribus.getDocName():
            create_footer_SE(page, footer)
        else:
            create_footer(page,footer)

    # pages = range(rules_pages[0],rules_pages[1]+1)
    # header = ''
    # # pages = [rules_pages[0]]
    # for page in pages:
    #     scribus.gotoPage(page)
    #     items = scribus.getPageItems()
    #     for item in items:
    #             if item[1] == 4:
    #                 if scribus.getParagraphStyle(item[0]) == 'HEADER Rules':
    #                     header = scribus.getAllText(item[0])
    #     scribus.setActiveLayer("Hyperlinks")
    #     label = scribus.createText(20,288,70,7)
    #     scribus.setText(header,label)
    #     scribus.setStyle("FOOTER - Left", label)

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
