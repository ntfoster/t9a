import scribus
from t9a.scribus import ScribusLAB

lab = ScribusLAB()
rules = lab.get_embedded_rules()
scribus.messageBox("Rules",rules)
