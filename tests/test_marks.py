import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1])) # needed to run from subdirectory
import t9a
from t9a.sla import SLAFile

filename = Path(sys.argv[1])

lab = SLAFile(filename)

result = lab.lookup_variable_text("Kuulima's Deceiver")

print(result)
