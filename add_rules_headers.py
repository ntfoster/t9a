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


import json
# from get_rules_toc import get_titles
from t9a.sla import LABfile
from pathlib import Path
import os
import subprocess



def remove_rules_headers(rules_start,rules_end):
    scribus.setActiveLayer('Notes')
    page = rules_start-1
    scribus.setRedraw(False)
    while page < rules_end:
        scribus.gotoPage(page)
        items = scribus.getAllObjects(4,page,'Notes')
        if len(items) > 0:
            for item in items:
                if scribus.isLocked(item):
                    scribus.lockObject(item)
                scribus.deleteObject(item)
        page +=1

    scribus.setRedraw(True)

def add_rules_headers(titles,rules_start):
    scribus.setActiveLayer('Notes')
    for title in titles:
        page_number = title['page']+rules_start-2
        scribus.gotoPage(page_number)
        frame_name = title['title']+' Header'
        scribus.createText(56.58,841.89-title['ypos'],482,45,frame_name)
        scribus.setText(title['title'],frame_name)
        scribus.setParagraphStyle("HEADER Rules", frame_name)
    scribus.docChanged(True)

def load_titles_from_json(filename):
    with open(filename) as json_file:
        titles = json.load(json_file)
        return titles
        
def set_rules_headers():

    rules_start = int(scribus.getText('rules_start'))
    rules_end = int(scribus.getText("rules_end"))
    scribus.setActiveLayer('Notes')
    scribus.setUnit(scribus.UNIT_POINTS)

    # f = open(r"C:\Users\pusht\OneDrive\9th Age\scripts\titles.json")
    # titles = json.load(f)
    lab = LABfile(scribus.getDocName())
    pdf_file = Path(lab.get_embedded_rules())
    json_file = pdf_file.parent.parent / Path(pdf_file.name).with_suffix('.json')
    if not Path(json_file).is_file():
        script_name = "t9a_pdf.py"
        script_path = Path(__file__).parents[0] / script_name
        print(script_path)
        current_env = os.environ.copy()
        current_env['PYTHONPATH'] = "" # need to clear out Scribus' pythonpath before calling subprocess to avoid import errors
        p = subprocess.run(f'python3 "{script_path}" "{pdf_file}"',shell=True,env=current_env)
        # os.system(f'python3 "{script_path}" "{pdf_file}"')
        # subprocess.run(["python3","--version"],shell=True)
    try:
        print("trying to load titles")
        titles = load_titles_from_json(json_file)
        # scribus.saveDoc()
    except:
        scribus.messageBox("Titles not found",f"The file {json_file} could not be found. Please make sure you have the py_pdf_parser module installed and can run t9a_pdf.py manually.")
        return
    remove_rules_headers(rules_start, rules_end)
    add_rules_headers(titles,rules_start)

def main_wrapper(argv):
    """The main_wrapper() function disables redrawing, sets a sensible generic
    status bar message, and optionally sets up the progress bar. It then runs
    the main() function. Once everything finishes it cleans up after the main()
    function, making sure everything is sane before the script terminates."""
    try:
        scribus.statusMessage("Running script...")
        scribus.progressReset()
        # main(argv)
        set_rules_headers()
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
