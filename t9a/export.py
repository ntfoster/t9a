"""Contains methods and values for exporting T9A LAB files from Scribus"""
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

import argparse
import datetime
import os
import re
import shutil
import sys
from pathlib import Path

from t9a import EXPECTED_FRAMES
from t9a.scribus import test_frames, ScribusLAB

QUALITY_TYPES = ["high","low","print"]
FORMAT_TYPES = ["full","nopoints","norules"]

QUALITY_HIGH = {
    "quality":1, # 0:Max, 1:High, 2:Medium, 3:Low, 4:Minimum,
    "fontEmbedding":0,
    "version":15,
    "embedPDF":True,
    "downsample":300,
    "resolution":300,
    "compress":True,
    "compressmtd":1, # 0:Automatic; 1:JPEG,
    "outdst":0, # screen,
    "displayBookmarks":True,
    "useDocBleeds":False,
    "cropMarks":False
}

QUALITY_LOW = {
    "quality":3, # 0= Max, 1 = High, 2 = Medium, 3 = Low, 4 = Minimum,
    "fontEmbedding":0,
    "version":15,
    "embedPDF":True,
    "downsample":100,
    "resolution":100,
    "compress":True,
    "compressmtd":1,  # 0 = Automatic; 1 = JPEG
    "outdst":0, # screen,
    "displayBookmarks":True,
    "useDocBleeds":False,
    "cropMarks":False
}

QUALITY_PRINT = {
    "quality":0, # Max,
    "fontEmbedding":0,
    "version":13,
    "embedPDF":True,
    "downsample":300,
    "resolution":300,
    "compress":True,
    "compressmtd":0, # Automatic compression,
    "outdst":1, # print,
    "useDocBleeds":True,
    "cropMarks":False
}


# globals
quit = False
num_files = 0
progress_step = 0
interactive = True
no_export = False


def create_norules(page_range):
    """Removes rules pages from the LAB and adjust ToC etc.
    """
    try:
        scribus.selectObject("rules_links")
    except: 
        scribus.messageBox("Missing group 'rules_links'", str(err), scribus.ICON_CRITICAL)
        sys.exit(1)

    # page_range = get_rules_pages()

    scribus.deselectAll()
   
    # Create backup of file first
    now = datetime.datetime.now()
    timestamp = now.strftime('%Y-%m-%dT%H-%M-%S')
    filename = scribus.getDocName()
    backup_filename = os.path.splitext(filename)[0]+'_backup_'+timestamp+'.sla'
    shutil.copy(filename,backup_filename) # don't use scribus built-in savceDocAs(), otherwise it will switch focus to the new file, which we don't want.

    # set version string

    # version = scribus.getAllText("version_name")
    # version = version.replace('Rules and Points version 2020', 'Background Book')
    # version = version.replace('Rules Only version 2020', 'Background Book')
    version = scribus.getAllText("edition") + ', ' + scribus.getAllText("norules_title")
    scribus.setText(version,"version_name")
    scribus.setTextAlignment(scribus.ALIGN_CENTERED, "version_name")

    # unlock and delete background, rules toc headers
    frames = ["toc_header_background","toc_header_rules","TOC_Rules"]
    # for frame in frames:
    #     if scribus.isLocked(frame):
    #         scribus.lockObject(frame)
    #         scribus.deleteObject(frame)
    scribus.deleteObject("toc_header_background")
    scribus.deleteObject("toc_header_rules")
    scribus.deleteObject("TOC_Rules")
    # delete rules hyperlinks
    scribus.deleteObject("rules_links")

    # check for alternate contents master page (e.g. smaller background)
    master = scribus.getMasterPage(7) # 7 should (hopefully) always be contents page
    if master.startswith('T -'):
        masters = scribus.masterPageNames()
        new_master = master
        for m in masters:
            print(m)
            if m.startswith('T0'):
                new_master = m
        scribus.applyMasterPage(new_master,7)    
    
    # delete pages
    pages = []
    scribus.statusMessage("Deleting Pages")
    scribus.setRedraw(False)
    for i in range(page_range[1],page_range[0]-1,-1): # need to start from last page as page count changes as pages are deleted
        scribus.deletePage(i)
        pages.append(i)
    scribus.docChanged(True)
    scribus.setRedraw(True)
    
    # set Epilogue hyperlink to correct page (same as rules_start)
    num_pages = page_range[1]-page_range[0] + 1
    original_epilogue = int(scribus.getAllText("epilogue_page"))
    new_epilogue = original_epilogue - num_pages
    scribus.setText(str(new_epilogue),"epilogue_page")
    scribus.setLinkAnnotation(new_epilogue,0,0,"bh_epilogue")
    
    # save _norules version of file
    
    new_filename = os.path.splitext(filename)[0].replace('_nopoints', '')+'_norules.sla'
    scribus.saveDocAs(new_filename)
    # shutil.copy(filename,backup_filename)

def export_pdf(filename,quality):
    pdf = scribus.PDFfile()
    pdf.file = filename
    if quality == "high":
        preset = QUALITY_HIGH
    elif quality == "low":
        preset = QUALITY_LOW
    elif quality == "print":
        preset = QUALITY_PRINT
    for p in preset.items():
        setattr(pdf,p[0],p[1])
    pdf.save()
            

def verify_quality(quality):
    if quality in QUALITY_TYPES:
        return quality
    else:
        raise argparse.ArgumentTypeError("%s is not a valid quality. Valid qualities are: %s" % (quality, str(QUALITY_TYPES)))


def verify_format(format):
    if format in FORMAT_TYPES:
        return format
    else:
        raise argparse.ArgumentTypeError("%s is not a valid format. Valid formats are: %s" % (format, str(FORMAT_TYPES))) 


def set_filename(filename,format,quality,version=""):
    # t9a_pattern = r't9a-fb_lab_(\w+)_(\w+)_v\d+.sla'
    # t9a_re = re.compile(t9a_pattern)
    # sla = os.path.basename(filename)
    # result = t9a_re.match(sla.lower())
    # if result:
    #     army = result.group(1)
    #     lang = result.group(2)

    # if quality =="print":
    #     quality = "press"
    # if quality == "low":
    #     quality = "online"
    # if quality == "high":
    #     quality = "print"
    # if format == "norules":
    #     format = "background"
    #     new_filename = f"{os.path.split(filename)[0]}/t9a-fb_lab_{quality}_{army}_{format}_{lang}.pdf" # no version string needed for background book
    # else:
    #     new_filename = f"{os.path.split(filename)[0]}/t9a-fb_lab_{quality}_{army}_{format}_{version}_{lang}.pdf"
    return f'{os.path.splitext(filename)[0]}_{format}_{quality}.pdf'

def prepare_format(format):
    pass

def export_pdfs(formats,qualities):
    global progress_step
    global num_files
    global interactive
    global no_export

    lab = ScribusLAB
    filename = scribus.getDocName()
    version_number = scribus.getAllText("version_number")

    # set version name from variables
    version = scribus.getAllText("edition") + ', ' + scribus.getAllText("full_title") + ' ' + scribus.getAllText("version_number")
    scribus.setText(version,"version_name")
    scribus.setTextAlignment(scribus.ALIGN_CENTERED, "version_name")

    scribus.setLayerBlendmode("Rules", 3) # Set Multiply for Rules Layer, as this is often set to normal for performance reasons

    num_files = len(formats)*len(qualities)
    scribus.progressTotal(num_files)

    def export_format(format, qualities):
        global progress_step
        global num_files
        for o in qualities:
            output_file = set_filename(filename,format,o,version_number)
            progress_step += 1
            scribus.statusMessage("Exporting %i of %i: %s" % (progress_step, num_files, output_file))
            export_pdf(output_file,o)
            scribus.progressSet(progress_step)

    if "full" in formats:
        export_format("full",qualities)
    if "nopoints" in formats:
        lab.replace_with_nopoints()
        
        version = scribus.getAllText("edition") + ', ' + scribus.getAllText("nopoints_title") + ' version ' + scribus.getAllText("version_number")
        scribus.setText(version,"version_name")
        scribus.setTextAlignment(scribus.ALIGN_CENTERED, "version_name")

        export_format("nopoints",qualities)

    if "norules" in formats:
        # remove rules
        scribus.statusMessage("Removing Rules")
        create_norules()
        export_format("norules",qualities)


def main(argv):
    global no_export
    global interactive
    if len(argv)==1: # if called from within Scribus or with no arguments
        new_args = scribus.valueDialog('Set Arguments', 'Set Arguments:\nOptions for --quality: high, low, print\nOptions for --format: full, nopoints, norules', '--quality high low --formats full')
        if new_args == '':
            scribus.messageBox("Script Cancelled","Script was cancelled or no arguments were provided")
            return
        else:
            arg_list = new_args.split(' ')
            # scribus.messageBox("Arguments",str(argv))
            # return
    else:
        arg_list = argv[1:]
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--quality', nargs='+', help='Which quality types do you want? Available: "high", "low" (RGB) and "print" (CMYK). Defaults to "high".', default="high")
    parser.add_argument('--formats', '-f', nargs='+', help='Options: "full", "nopoints", and "norules". Default is "full".', default="full")
    parser.add_argument('--quit', help='Quit Scribus after export (e.g. when called as part of external script)', action="store_true")
    parser.add_argument('--noexport', help="Don't export PDFs, just make the changes to the file and save", action="store_true")

    try:
        args = parser.parse_args(arg_list)
    except argparse.ArgumentTypeError as e:
        raise e

    if args.noexport:
        no_export = True
    if args.quit:
        interactive = False

    export_pdfs(args.formats,args.quality)

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
        if not interactive:
            scribus.closeDoc()
            scribus.fileQuit()

# This code detects if the script is being run as a script, or imported as a module.
# It only runs main() if being run as a script. This permits you to import your script
# and control it manually for debugging.
if __name__ == '__main__':
    if scribus.haveDoc():
        main_wrapper(sys.argv)
    else:
        scribus.messageBox("No file open","You need to have a suitable file open to use this script")

