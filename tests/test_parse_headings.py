import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1])) # needed to run from subdirectory
import t9a
from t9a.sla import SLAFile

filename = Path(sys.argv[1])

lab = SLAFile(filename)

headings = lab.parse_headers_from_text_sla([t9a.HEADER1,t9a.HEADER2])

print(headings)

