import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1])) # needed to run from subdirectory
from t9a.sla import SLAFile

def test(filename):
    lab = SLAFile(filename)
    missing_styles = lab.test_styles()
    missing_frames = lab.test_frames()

    print(f"Testing: {filename}")
    print(f"Missing styles: {', '.join(missing_styles) or None}")
    print(f"Missing frames: {', '.join(missing_frames) or None}")

if __name__ == "__main__":
    test(sys.argv[1])

