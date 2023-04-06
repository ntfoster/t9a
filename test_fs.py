from t9a import EXPECTED_FRAMES, EXPECTED_STYLES
from t9a.sla import LABfile

lab = LABfile(r"C:\Users\pusht\OneDrive\9th Age\Templates\LAB Template v2\army-book-template.sla")
print(lab.test_frames(EXPECTED_FRAMES))
print(lab.test_styles(EXPECTED_STYLES))
