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

#########################
# YOUR IMPORTS GO HERE  #
#########################

import xml.etree.ElementTree as ET

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
                if mark.get("type") == "3" and mark.get("label") == entry["label"]:
                    entry["text"] = mark.get("str")

            
    return labels

def main(argv):
    """This is a documentation string. Write a description of what your code
    does here. You should generally put documentation strings ("docstrings")
    on all your Python functions."""
    #########################
    #  YOUR CODE GOES HERE  #
    #########################
    global root
    file = scribus.getDocName()
    tree = ET.parse(file)
    root = tree.getroot()

    background_headers = parse_headers("HEADER Level 1")

    background_labels = lookup_labels(background_headers)

    newlist = sorted(background_labels, key=lambda k: k['page'])
    text = newlist

    toc_background = ""
    for entry in text:
        line = f'{entry["text"]}\t{entry["page"]}\n'
        toc_background += line
    scribus.setText(toc_background,"TOC_Background")
    try:
        scribus.setParagraphStyle("TOC1","TOC_Background")
    except scribus.NotFoundError:
        scribus.setParagraphStyle("TOC level 1", "TOC_Background")


    rules_headers = parse_headers("HEADER Rules")
    rules_labels = lookup_labels(rules_headers)

    newlist = sorted(rules_labels, key=lambda k: k['page'])
    text = newlist

    toc_rules = ""
    for entry in text:
        line = f'{entry["text"]}\t{entry["page"]}\n'
        toc_rules += line
    scribus.setText(toc_rules,"TOC_Rules")
    scribus.setParagraphStyle("TOC Rules","TOC_Rules")

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
