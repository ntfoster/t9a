import sys
from pathlib import Path

import scribus

sys.path.append(str(Path(__file__).parents[1])) # needed to run from subdirectory

from t9a.scribus import ScribusLAB

lab = ScribusLAB()
missing_styles = lab.test_styles()
if missing_styles:
    scribus.messageBox("Missing styles",str(missing_styles))
else:
    scribus.messageBox("OK","No expected styles missing")

