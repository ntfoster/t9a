import sys
from pathlib import Path

import scribus

sys.path.append(str(Path(__file__).parents[1])) # needed to run from subdirectory
from t9a.scribus import ScribusLAB

lab = ScribusLAB()

scribus.deleteText("TOC_Background")
scribus.deleteText("TOC_Rules")
lab.delete_toc_hyperlinks()
lab.remove_footers()
lab.remove_rules_headers()
