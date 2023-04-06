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

from t9a.scribus import ScribusLAB

lab = ScribusLAB()
missing_styles = lab.test_styles()
if missing_styles:
    scribus.messageBox("Missing styles",str(missing_styles))
else:
    scribus.messageBox("OK","No expected styles missing")

